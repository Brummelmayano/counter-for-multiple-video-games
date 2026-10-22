"""Read the HUD zones of every gameplay frame of PlayEnd with the student's OCR, for every layout of the game.

The game comes from the teacher's observation here (a perfect classifier): this pass records where each text
stands on screen, to place the reading boxes of the zone schema and to measure the readers. One JSON line per frame
and layout in build/student/ocr/<session>.jsonl, with each text's box in capture pixels.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import defaultdict
from pathlib import Path

from PIL import Image

from playend.annotation.zoom.layout import session_dir
from playend.common.paths import REPO, STUDENT_OUTPUT
from playend.student.ocr import TextReader
from playend.student.zones import LAYOUTS, mosaic

# The teacher's observations the student learns from and is measured against. Results before 2026-10-14 used version
# 1.0 (build/playend_v1.0).
OBSERVATIONS = REPO / "build" / "playend_v1.1" / "data" / "observations.csv"


def gameplay_frames(observations: Path = OBSERVATIONS) -> dict[str, list[tuple[int, str]]]:
    frames = defaultdict(list)
    with open(observations, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["screen_type"] == "gameplay" and row["game_family"] in LAYOUTS:
                frames[row["session_id"]].append((int(row["frame_id"]), row["game_family"]))
    return frames


def frame_paths(session: str) -> dict[int, Path]:
    return {int(path.stem.split("_")[-1]): path for path in (session_dir(session) / "images").rglob("frame_*.jpg")}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=STUDENT_OUTPUT / "ocr")
    parser.add_argument("--limit", type=int, help="frames per session, to check the command")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    reader = TextReader()
    start, done = time.time(), 0
    for session, frames in sorted(gameplay_frames().items()):
        target = args.out / f"{session}.jsonl"
        if target.exists():
            continue
        paths = frame_paths(session)
        records = []
        for frame_id, family in frames[: args.limit]:
            frame = Image.open(paths[frame_id]).convert("RGB")
            for layout, layout_zones in LAYOUTS[family].items():
                built = mosaic(frame, layout_zones)
                lines = []
                for line in reader.read(built.image):
                    zone, box = built.to_frame(line.box)
                    lines.append([line.text, round(line.score, 3), zone, *(round(value) for value in box)])
                records.append({"frame_id": frame_id, "family": family, "layout": layout, "lines": lines})
            done += 1
        partial = target.with_suffix(".part")
        partial.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
        partial.replace(target)
        print(f"{session}: {len(frames[: args.limit])} frames, {done / (time.time() - start):.1f} frames/s", flush=True)


if __name__ == "__main__":
    main()
