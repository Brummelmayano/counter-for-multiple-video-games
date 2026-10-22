"""Compare the fields the student reads with the teacher's, field by field, on every gameplay frame.

For each field with a value in the teacher's observation: correct, wrong (another value) or missed (nothing read).
A value read where the teacher has none counts as extra. Names are compared without case. `--method detected` uses
only the detected text of the zones; `full` adds the fixed reading boxes and the marks, the marks predicted by
models that did not see the frame's block of time.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

from playend.common.paths import STUDENT_OUTPUT
from playend.student import marks
from playend.student.collect import OBSERVATIONS, frame_paths
from playend.student.ocr import TextReader
from playend.student.read import merge, read_boxes
from playend.student.rules import read_fields
from playend.student.zones import LAYOUTS

FIELDS = [
    "clock_display", "score_a", "score_b", "period_number", "progress_current", "players_remaining",
    "teams_remaining", "series_a", "series_b", "lives_a", "lives_b", "participant_a", "participant_b",
]  # fmt: skip


def same(field: str, teacher: str, student) -> bool:
    if field.startswith("participant"):
        return str(student).casefold() == teacher.casefold()
    if field == "clock_display" and ":" in teacher and ":" in str(student):
        minutes, seconds = teacher.split(":")[:2]
        read_minutes, read_seconds = str(student).split(":")[:2]
        return int(minutes or 0) == int(read_minutes) and seconds[:2] == read_seconds[:2]
    return str(student) == teacher


def outcomes(readings_dir: Path, method: str = "full") -> tuple[dict, dict]:
    teacher = {}
    with open(OBSERVATIONS, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            teacher[(row["session_id"], int(row["frame_id"]))] = row
    counts = defaultdict(Counter)
    per_frame = {}
    reader = TextReader() if method == "full" else None
    mark_values = marks.out_of_fold() if method == "full" else {}
    for path in sorted(readings_dir.glob("*.jsonl")):
        paths = frame_paths(path.stem) if method == "full" else {}
        frames = defaultdict(dict)
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            frames[(record["frame_id"], record["family"])][record["layout"]] = record["lines"]
        for (frame_id, family), readings in frames.items():
            zone_counts = {layout: len(zones) for layout, zones in LAYOUTS[family].items()}
            fields = read_fields(family, readings, zone_counts)
            if method == "full":
                frame = Image.open(paths[frame_id]).convert("RGB")
                fields = merge(read_boxes(reader, frame, family), fields, mark_values.get((path.stem, frame_id), {}))
            row = teacher[(path.stem, frame_id)]
            per_frame[(path.stem, frame_id)] = fields
            for field in FIELDS:
                expected, read = row.get(field) or "", fields.get(field)
                if expected:
                    outcome = "missed" if read is None else "correct" if same(field, expected, read) else "wrong"
                elif read is not None:
                    outcome = "extra"
                else:
                    continue
                counts[(family, field)][outcome] += 1
    return counts, per_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--readings", type=Path, default=STUDENT_OUTPUT / "ocr")
    parser.add_argument("--method", choices=["detected", "full"], default="full")
    parser.add_argument("--save", type=Path, help="write the fields read on every frame to this JSON file")
    args = parser.parse_args()
    counts, per_frame = outcomes(args.readings, args.method)
    if args.save:
        readings = {f"{session}:{frame_id}": fields for (session, frame_id), fields in per_frame.items()}
        args.save.write_text(json.dumps(readings, ensure_ascii=False), encoding="utf-8")
    total = Counter()
    print(f"{'game':28} {'field':18} {'teacher':>7} {'correct':>8} {'wrong':>6} {'missed':>7} {'extra':>6}")
    for (family, field), count in sorted(counts.items()):
        expected = count["correct"] + count["wrong"] + count["missed"]
        total.update(count)
        share = f"{100 * count['correct'] / expected:.0f} %" if expected else "-"
        print(f"{family[:28]:28} {field:18} {expected:7} {share:>8} {count['wrong']:6} {count['missed']:7} "
              f"{count['extra']:6}")  # fmt: skip
    expected = total["correct"] + total["wrong"] + total["missed"]
    print(f"all fields: {expected} teacher values, {100 * total['correct'] / expected:.1f} % correct, "
          f"{100 * total['wrong'] / expected:.1f} % wrong, {100 * total['missed'] / expected:.1f} % missed, "
          f"{total['extra']} extra")  # fmt: skip


if __name__ == "__main__":
    main()
