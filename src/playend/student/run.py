"""Run the student on a list of captures and time it: the full OCR student, or the VLM, held by its grammar or not.

The list is a JSON file of {"session", "frame_id", "image"} (image path relative to the list). One JSON file per
capture is written in the output folder, so the command can be started again after a power cut and skips what is
done. The OCR student finds the game itself (classifier with its vote), so its times are those of the real loop.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

from PIL import Image

from playend.student.apply import Classifier, Marks
from playend.student.features import ImageFeatures
from playend.student.ocr import TextReader
from playend.student.read import merge, read_boxes
from playend.student.rules import read_fields
from playend.student.vlm import grammar, parse, prompt, vlm_mosaic
from playend.student.zones import LAYOUTS, mosaic


def temperature() -> float | None:
    """CPU temperature of the Pi in °C; None elsewhere."""
    sensor = Path("/sys/class/thermal/thermal_zone0/temp")
    return int(sensor.read_text()) / 1000 if sensor.exists() else None


def save(record: dict, path: Path):
    partial = path.with_suffix(".part")
    with open(partial, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, indent=1))
        handle.flush()
        # Without it, a power cut on the Pi can keep the renamed file with its content never written: zero bytes.
        os.fsync(handle.fileno())
    partial.replace(path)


def saved(path: Path) -> dict | None:
    """A record written earlier, or None when it is missing or was cut short by a power cut."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def read_hud(reader: TextReader, marks: Marks, frame: Image.Image, game: str, times: dict) -> dict:
    """The HUD values of a gameplay capture of a game with zones; the time of each step is added to `times`."""
    step = time.perf_counter()
    boxes = read_boxes(reader, frame, game)
    times["boxes_s"] = time.perf_counter() - step
    step = time.perf_counter()
    readings = {}
    for layout, zones in LAYOUTS[game].items():
        built = mosaic(frame, zones)
        readings[layout] = []
        for line in reader.read(built.image):
            zone, box = built.to_frame(line.box)
            readings[layout].append([line.text, line.score, zone, *box])
    detected = read_fields(game, readings, {layout: len(z) for layout, z in LAYOUTS[game].items()})
    times["zones_s"] = time.perf_counter() - step
    step = time.perf_counter()
    fields = merge(boxes, detected, marks.read(game, frame))
    times["marks_s"] = time.perf_counter() - step
    return fields


def read_with_ocr(frames: list[dict], root: Path, out: Path):
    extractor, classifier, marks, reader = ImageFeatures(), Classifier(), Marks(), TextReader()
    session = None
    for item in frames:
        target = out / f"{item['session'][8:14]}_{item['frame_id']:05d}.json"
        new_session = item["session"] != session
        session = item["session"]
        if saved(target) is not None:
            continue
        times = {}
        start = time.perf_counter()
        frame = Image.open(root / item["image"]).convert("RGB")
        times["load_s"] = time.perf_counter() - start
        features = extractor(frame)
        game = classifier.game(features, new_session)
        screen, _ = classifier.label("screen", features)
        times["classify_s"] = time.perf_counter() - start - times["load_s"]
        fields = {}
        if screen == "gameplay" and game in LAYOUTS:
            fields = read_hud(reader, marks, frame, game, times)
        times["total_s"] = time.perf_counter() - start
        record = {**item, "game": game, "screen": screen, "fields": fields, "times": times, "temp_c": temperature()}
        save(record, target)


def read_with_vlm(
    frames: list[dict], root: Path, out: Path, binary: Path, model: Path, mmproj: Path, threads: int, use_grammar: bool
):
    work = out / "inputs"
    work.mkdir(parents=True, exist_ok=True)
    for item in frames:
        family = item.get("family")
        name = f"{item['session'][8:14]}_{item['frame_id']:05d}"
        target = out / f"{name}.json"
        if saved(target) is not None or not family:
            continue
        image = work / f"{name}.png"
        vlm_mosaic(Image.open(root / item["image"]).convert("RGB"), family).save(image)
        command = [str(binary), "-m", str(model), "--mmproj", str(mmproj), "--image", str(image), "-p", prompt(family),
                   "-n", "96", "-c", "4096", "-t", str(threads), "--temp", "0", "--seed", "42", "--perf"]  # fmt: skip
        if use_grammar:
            grammar_file = work / f"{name}.gbnf"
            grammar_file.write_text(grammar(family), encoding="utf-8")
            command += ["--grammar-file", str(grammar_file)]
        start = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, timeout=1800)
        grammar_used = use_grammar and result.returncode == 0
        if use_grammar and not grammar_used:  # a llama.cpp build that refuses the grammar still gives a free answer
            command = command[: command.index("--grammar-file")] + command[command.index("--grammar-file") + 2 :]
            start = time.perf_counter()
            result = subprocess.run(command, capture_output=True, text=True, timeout=1800)
        wall = time.perf_counter() - start
        (out / f"{name}.log").write_text(result.stderr, encoding="utf-8")
        save({**item, "answer": result.stdout, "fields": parse(family, result.stdout), "wall_s": wall,
              "grammar": grammar_used, "exit_code": result.returncode, "temp_c": temperature()}, target)  # fmt: skip


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("reader", choices=["ocr", "vlm"])
    parser.add_argument("frames", type=Path, help="JSON list of captures")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--llama", type=Path, help="llama-mtmd-cli, for the VLM")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--mmproj", type=Path)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--no-grammar", action="store_true", help="let the VLM answer freely, without the grammar")
    args = parser.parse_args()
    frames = json.loads(args.frames.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    if args.reader == "ocr":
        read_with_ocr(frames, args.frames.parent, args.out)
    else:
        read_with_vlm(
            frames, args.frames.parent, args.out, args.llama, args.model, args.mmproj, args.threads, not args.no_grammar
        )


if __name__ == "__main__":
    main()
