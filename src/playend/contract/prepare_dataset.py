"""Build versioned GRU inputs from observations + actual capture timestamps.

Example: python -m playend.contract.prepare_dataset
 --manifest PATH --out NEW_DIRECTORY [--allow-legacy] [--labels LABELS_JSONL]

Manifest paths are relative to --project-root (not the current working directory); paths written with the
folder names used before the data moved to data/ are translated.
No VLM execution, image upload or training is performed by this command.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..common.files import sha256, write_jsonl
from ..common.paths import REPO, resolve
from .contract import parse_strict_json, upgrade_legacy, validate_any
from .temporal import FEATURE_VERSION, FeatureStream, feature_spec

PROJECT_ROOT = REPO


def read_strict_json(path):
    obj, errors = parse_strict_json(path.read_text(encoding="utf-8"))
    if errors:
        raise ValueError(f"{path}: {errors}")
    return obj


def read_strict_jsonl(path):
    result = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj, errors = parse_strict_json(line)
        if errors:
            raise ValueError(f"{path}:{number}: {errors}")
        result.append(obj)
    return result


def load_records(manifest, project_root=PROJECT_ROOT, allow_legacy=False):
    records = []
    seen = set()
    for row in read_strict_jsonl(manifest):
        key = (row["session_id"], row["frame_id"])
        if key in seen:
            raise ValueError(f"duplicate frame in manifest: {key}")
        seen.add(key)
        if row.get("observation_missing"):
            # VLM failure/timeout on the device: keep the row (realism), no observation file.
            if row.get("observation_path"):
                raise ValueError(f"{key}: observation_missing rows must not reference an observation file")
            records.append(dict(row, observation=None, legacy_clock_masked=False, observation_sha256=None))
            continue
        path = resolve(row["observation_path"], project_root).resolve()
        obj = read_strict_json(path)
        errors = validate_any(obj)
        if errors:
            raise ValueError(f"{path}: {errors}")
        migrated = "schema_version" not in obj
        if migrated and not allow_legacy:
            raise ValueError("legacy observation: reannotate with v2 or explicitly use --allow-legacy (clock masked)")
        record = dict(
            row,
            observation=upgrade_legacy(obj) if migrated else obj,
            legacy_clock_masked=migrated,
            observation_sha256=sha256(path),
        )
        records.append(record)
    if not records:
        raise ValueError("empty manifest")
    return sorted(records, key=lambda r: (r["session_id"], r["frame_id"]))


def labels_by_frame(path):
    labels = {}
    for label in read_strict_jsonl(path) if path else []:
        key = (label["session_id"], label["frame_id"])
        if key in labels:
            raise ValueError(f"duplicate label: {key}")
        if label.get("review_status") != "human_verified":
            raise ValueError("labels require explicit human_verified review_status")
        for field in ("frame_id", "previous_frame_id"):
            if type(label.get(field)) is not int or label[field] < 1:
                raise ValueError("labels must identify both endpoint frames")
        if type(label.get("boundary_applicable")) is not bool:
            raise ValueError("boundary_applicable must be boolean")
        target, count = label.get("unit_end_boundary"), label.get("ended_unit_count")
        if type(target) is not int or target not in (0, 1):
            raise ValueError("unit_end_boundary must be 0 or 1")
        if type(count) is not int or count < 0 or target != int(count > 0):
            raise ValueError("ended_unit_count and boundary target disagree")
        labels[key] = label
    return labels


def build_rows(records, labels=None):
    labels = labels or {}
    available = {(r["session_id"], r["frame_id"]) for r in records}
    if set(labels) - available:
        raise ValueError("labels refer to missing frames")
    stream, previous, rows = FeatureStream(), None, []
    spec = feature_spec()
    for record in records:
        features = stream.step(record)
        if list(features) != spec["feature_names"]:
            raise ValueError("feature order drift")
        label = labels.get((record["session_id"], record["frame_id"]))
        target, mask, count = None, 0, None
        if label:
            if (
                previous is None
                or previous["session_id"] != record["session_id"]
                or label["previous_frame_id"] != previous["frame_id"]
            ):
                raise ValueError("boundary label does not match the selected interval endpoints")
            target, count = label["unit_end_boundary"], label["ended_unit_count"]
            # Binary counting pilot cannot represent 2+ ends in one interval.
            mask = int(
                label["boundary_applicable"]
                and count <= 1
                and all(
                    (r.get("review_status") == "human_verified" or r.get("observation_missing"))
                    and not r.get("legacy_clock_masked", False)
                    for r in (record, previous)
                )
            )
        rows.append(
            {
                "session_id": record["session_id"],
                "frame_id": record["frame_id"],
                "received_monotonic_ns": record["received_monotonic_ns"],
                "delta_t_s": None
                if previous is None or previous["session_id"] != record["session_id"]
                else (record["received_monotonic_ns"] - previous["received_monotonic_ns"]) / 1e9,
                "review_status": record.get("review_status", "unknown"),
                "observation_path": record.get("observation_path"),
                "observation_sha256": record.get("observation_sha256"),
                "legacy_clock_masked": record.get("legacy_clock_masked", False),
                "observation_missing": bool(record.get("observation_missing")),
                "features": list(features.values()),
                "target_unit_end_boundary": target,
                "ended_unit_count_audit": count,
                "loss_mask_boundary": mask,
            }
        )
        previous = record
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--allow-legacy", action="store_true")
    args = parser.parse_args()
    records = load_records(args.manifest, args.project_root, args.allow_legacy)
    rows = build_rows(records, labels_by_frame(args.labels))
    # Refuse to replace datasets or annotations. Validate everything first.
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "feature_spec.json").write_text(json.dumps(feature_spec(), indent=2) + "\n")
    write_jsonl(args.out / "rows.jsonl", rows)
    report = {
        "rows": len(rows),
        "sessions": len({r["session_id"] for r in rows}),
        "eligible_labelled_intervals": sum(r["loss_mask_boundary"] for r in rows),
        "legacy_clocks_masked": sum(r["legacy_clock_masked"] for r in rows),
        "manifest_sha256": sha256(args.manifest),
        "labels_sha256": sha256(args.labels) if args.labels else None,
        "status": "features_only_no_training",
        "feature_version": FEATURE_VERSION,
        "observation_missing_rows": sum(bool(r.get("observation_missing")) for r in rows),
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
