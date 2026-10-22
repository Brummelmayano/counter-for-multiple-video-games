"""Check every lot of a capture session.

Full frame coverage without duplicates, the observation contract, image and annotation hashes, and agreement
between each generated note and its saved JSON. Correction traces are checked too: chain, hashes, contract and
note/JSON agreement.

usage: python -m playend.annotation.coverage session_<id> [session_<id> ...]
       python -m playend.annotation.coverage --all      # every session of the dataset (status table)
"""

from __future__ import annotations

import argparse
import json
import sys

from playend.annotation.build_lot import summary
from playend.annotation.lots import session_lots
from playend.annotation.notes import READING_MARKERS
from playend.common.files import read_jsonl, sha256
from playend.common.paths import CAPTURES, resolve
from playend.contract.contract import validate_observation
from playend.corrections import traces


def check(session: str) -> list[str]:
    problems: list[str] = []
    source_ids = {int(p.stem.split("_")[-1]) for p in (CAPTURES / session / "images").rglob("frame_*.jpg")}
    covered: dict[int, str] = {}
    by_annotator: dict[str, int] = {}
    for lot in session_lots(session):
        manifest = {row["frame_id"]: row for row in read_jsonl(lot / "manifest.jsonl")}
        for entry in read_jsonl(lot / "annotation_manifest.jsonl"):
            fid = entry["frame_id"]
            if fid in covered:
                problems.append(f"frame {fid}: annotated twice ({covered[fid]} and {lot.name})")
            covered[fid] = lot.name
            src = manifest[fid]
            if (
                sha256(resolve(src["image_path"])) != src["sha256"]
                or sha256(resolve(src["source_path"])) != src["sha256"]
            ):
                problems.append(f"frame {fid}: image hash mismatch")
            ann_path = resolve(entry["annotation_path"])
            if sha256(ann_path) != entry["annotation_sha256"]:
                problems.append(f"frame {fid}: annotation file changed since recording")
            obs = json.loads(ann_path.read_text(encoding="utf-8"))
            errors = validate_observation(obs)
            if errors:
                problems.append(f"frame {fid}: contract errors {errors}")
            meta = json.loads(resolve(entry["metadata_path"]).read_text(encoding="utf-8"))
            by_annotator[meta["annotator_model"]] = by_annotator.get(meta["annotator_model"], 0) + 1
            note = meta.get("annotation_note") or ""
            if note.startswith(READING_MARKERS) and not note.endswith(summary(obs)):
                problems.append(f"frame {fid}: note summary disagrees with saved JSON")
    missing = sorted(source_ids - set(covered))
    extra = sorted(set(covered) - source_ids)
    if missing:
        problems.append(
            f"{len(missing)} source frames without annotation: {missing[:10]}{'…' if len(missing) > 10 else ''}"
        )
    if extra:
        problems.append(f"annotations for unknown frames: {extra[:10]}")
    correction_problems, corrected = traces.check(session)
    problems += correction_problems
    print(
        f"{session}: {len(covered)}/{len(source_ids)} frames annotated; by annotator: {by_annotator}"
        + (f"; corrected by separate traces: {corrected}" if corrected else "")
        + f"; problems: {len(problems)}"
    )
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Check every lot and correction trace of capture sessions.")
    parser.add_argument("sessions", nargs="*", metavar="session_<id>")
    parser.add_argument("--all", action="store_true", help="every session of the dataset")
    args = parser.parse_args()
    if args.all == bool(args.sessions):
        parser.error("give session names or --all")
    sessions = sorted(p.name for p in CAPTURES.glob("session_*") if p.is_dir()) if args.all else args.sessions
    all_problems = [p for s in sessions for p in check(s)]
    for p in all_problems:
        print("  -", p)
    sys.exit(1 if all_problems else 0)


if __name__ == "__main__":
    main()
