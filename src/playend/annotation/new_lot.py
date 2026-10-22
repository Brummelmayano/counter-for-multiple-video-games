"""Create a lot: a copy of a range of capture frames, ready to be annotated.

Each original image is copied unchanged with its source path, capture time and SHA-256, together with the teacher
prompt the observations will follow. The annotator recorded in the manifest is the --annotator option, or
$ANNOTATOR_MODEL when the option is left out.

usage: python -m playend.annotation.new_lot session_<id> --start 199 --end 264 --suffix <teacher family>
"""

from __future__ import annotations

import argparse
import csv
import shutil

from playend.common.files import sha256, write_jsonl
from playend.common.paths import CAPTURES, LOTS, relative
from playend.common.provenance import annotator_model
from playend.contract.build_assets import PROMPT as PROMPT_SOURCE
from playend.contract.contract import SCHEMA_VERSION


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a lot: a copy of a range of capture frames, ready to annotate."
    )
    parser.add_argument("session_id")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    parser.add_argument("--annotator", help="model that will read the frames (default: $ANNOTATOR_MODEL)")
    parser.add_argument("--suffix", required=True, help="end of the lot folder name, the teacher family: luna, claude…")
    args = parser.parse_args()
    annotator = args.annotator or annotator_model()

    source_root = CAPTURES / args.session_id
    if not source_root.is_dir():
        raise SystemExit(f"missing session: {source_root}")
    capture_rows = {
        int(row["frame_id"]): row
        for row in csv.DictReader((source_root / "captures.csv").open(encoding="utf-8", newline=""))
    }
    image_by_id = {}
    for path in (source_root / "images").rglob("*"):
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            try:
                frame_id = int(path.stem.split("_")[-1])
            except ValueError:
                continue
            image_by_id[frame_id] = path
    if not image_by_id:
        raise SystemExit(f"no images in session: {args.session_id}")
    end = args.end if args.end is not None else max(image_by_id)
    frame_ids = sorted(fid for fid in image_by_id if args.start <= fid <= end)
    if frame_ids != list(range(args.start, end + 1)):
        raise SystemExit(f"non-contiguous/missing frames in requested range {args.start}-{end}: {frame_ids}")
    if set(frame_ids) - set(capture_rows):
        raise SystemExit("captures.csv is missing one or more requested frame IDs")

    lot_name = f"{args.session_id}_frames_{args.start:06d}_{end:06d}_observation_v2_{args.suffix}"
    lot = LOTS / lot_name
    if lot.exists():
        raise SystemExit(f"refusing to overwrite existing lot: {lot}")
    prompt_hash = sha256(PROMPT_SOURCE)
    prompt_copy = lot / "prompt_v4_final_universal.txt"
    (lot / "images").mkdir(parents=True)
    (lot / "annotations").mkdir()
    (lot / "decisions").mkdir()
    shutil.copyfile(PROMPT_SOURCE, prompt_copy)

    manifest = []
    for frame_id in frame_ids:
        source = image_by_id[frame_id]
        destination = lot / "images" / f"frame_{frame_id:08d}{source.suffix.lower()}"
        shutil.copyfile(source, destination)
        capture = capture_rows[frame_id]
        row = {
            "session_id": args.session_id,
            "frame_id": frame_id,
            "source_path": relative(source),
            "image_path": relative(destination),
            "sha256": sha256(source),
            "width": int(capture["width"]),
            "height": int(capture["height"]),
            "received_monotonic_ns": int(capture["received_monotonic_ns"]),
            "elapsed_s": float(capture["elapsed_s"]),
            "delta_t_s": float(capture["delta_t_s"]) if capture["delta_t_s"] else None,
            "received_wall_utc": capture["received_wall_utc"],
            "requested_interval_s": float(capture["requested_interval_s"]) if capture["requested_interval_s"] else 0.0,
            "timestamp_source": capture["timestamp_source"],
            "prompt_version": f"universal_contract_{SCHEMA_VERSION}",
            "prompt_sha256": prompt_hash,
            "schema_version": SCHEMA_VERSION,
            "requested_annotator": annotator,
            "review_status": "proposed_pending_human_review",
            "prompt_source": relative(PROMPT_SOURCE),
            "prompt_path": relative(prompt_copy),
        }
        manifest.append(row)
    write_jsonl(lot / "manifest.jsonl", manifest)
    write_jsonl(lot / "annotation_manifest.jsonl", [])
    readme = (
        f"# Full-frame annotations by {annotator} — {args.session_id}, frames {args.start}–{end}\n\n"
        "This lot copies each original image unchanged and records its source path, capture time, and SHA-256 in "
        "`manifest.jsonl`. "
        f"It uses the shared observation contract {SCHEMA_VERSION} prompt (`prompt_v4_final_universal.txt`, SHA-256 "
        f"`{prompt_hash}`). "
        "Every JSON remains `proposed_pending_human_review`; schema and file hashes do not establish visual "
        "ground-truth correctness.\n"
    )
    (lot / "README.md").write_text(readme, encoding="utf-8")
    print(f"Created {relative(lot)} with {len(manifest)} source frames ({args.start}–{end}).")


if __name__ == "__main__":
    main()
