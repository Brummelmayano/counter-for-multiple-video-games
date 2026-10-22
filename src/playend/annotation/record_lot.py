"""Validate a batch of observations and record it in its lot.

Each observation is checked against the contract, each source image against the hash taken when the lot was
created, and nothing already recorded is ever overwritten.

usage: python -m playend.annotation.record_lot LOT_DIR BATCH.jsonl [--annotation-method METHOD]
       (relative paths are taken from the repository root)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from playend.common.files import read_jsonl, sha256, write_jsonl
from playend.common.paths import REPO, relative, resolve
from playend.contract.contract import validate_observation


def record(lot: Path, batch_path: Path, annotation_method: str) -> list[dict]:
    """Write the batch's observations and metadata into the lot, then extend its annotation manifest."""
    manifest = {row["frame_id"]: row for row in read_jsonl(lot / "manifest.jsonl")}
    index_path = lot / "annotation_manifest.jsonl"
    existing_rows = read_jsonl(index_path)
    existing = {row["frame_id"] for row in existing_rows}
    records = read_jsonl(batch_path)
    if len({record["frame_id"] for record in records}) != len(records):
        raise SystemExit("duplicate frame IDs in batch")
    if any(record["frame_id"] not in manifest for record in records):
        raise SystemExit("batch contains frame IDs outside the source manifest")
    if any(record["frame_id"] in existing for record in records):
        raise SystemExit("refusing to overwrite an existing annotation")

    added = []
    for record in records:
        fid = record["frame_id"]
        observation = record["observation"]
        errors = validate_observation(observation)
        if errors:
            raise SystemExit(f"frame {fid}: {errors}")
        note = record.get("annotation_note")
        if not isinstance(note, str) or not note.strip():
            raise SystemExit(f"frame {fid}: annotation_note must be nonempty")

        source_row = manifest[fid]
        if sha256(resolve(source_row["image_path"])) != source_row["sha256"]:
            raise SystemExit(f"frame {fid}: copied image hash mismatch")
        stem = f"frame_{fid:08d}"
        ann_path = lot / "annotations" / f"{stem}.observation.json"
        meta_path = lot / "annotations" / f"{stem}.metadata.json"
        payload = (json.dumps(observation, ensure_ascii=False, indent=2) + "\n").encode()
        ann_path.write_bytes(payload)
        metadata = {
            "session_id": source_row["session_id"],
            "frame_id": fid,
            "image_path": source_row["image_path"],
            "image_sha256": source_row["sha256"],
            "prompt_version": source_row["prompt_version"],
            "prompt_sha256": source_row["prompt_sha256"],
            "schema_version": observation["schema_version"],
            "annotator_model": source_row["requested_annotator"],
            "annotation_method": annotation_method,
            "image_input": "complete_original_frame",
            "image_dimensions": [source_row["width"], source_row["height"]],
            "review_status": "proposed_pending_human_review",
            "validation_errors": [],
            "annotation_note": note,
        }
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        added.append(
            {
                "session_id": source_row["session_id"],
                "frame_id": fid,
                "image_sha256": source_row["sha256"],
                "annotation_path": relative(ann_path),
                "annotation_sha256": hashlib.sha256(payload).hexdigest(),
                "metadata_path": relative(meta_path),
                "review_status": metadata["review_status"],
                "prompt_sha256": source_row["prompt_sha256"],
                "schema_version": observation["schema_version"],
                "validation_errors": [],
            }
        )
    write_jsonl(index_path, [*existing_rows, *added])
    first, last = min(r["frame_id"] for r in added), max(r["frame_id"] for r in added)
    print(f"Recorded {len(added)} annotations for frames {first}–{last}.")
    return added


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a batch of observations and record it in its lot.")
    parser.add_argument("lot", type=Path)
    parser.add_argument("batch", type=Path)
    parser.add_argument("--annotation-method", default="single_complete_original_frame_visual_read")
    args = parser.parse_args()
    lot = args.lot if args.lot.is_absolute() else REPO / args.lot
    batch = args.batch if args.batch.is_absolute() else REPO / args.batch
    record(lot, batch, args.annotation_method)


if __name__ == "__main__":
    main()
