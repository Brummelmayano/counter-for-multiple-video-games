"""Run a VLM reader of the student on the test examples with llama.cpp, then score its fields against the teacher's.

run: one llama-mtmd-cli call per test example (model loaded each time; the time of one image is the time after the
image is encoded, read from the log), with or without the grammar of the game. One JSON file per example, so the
command resumes after an interruption. score: the fields of each answer against those of the expected answer (the
teacher's), as correct, wrong or missed, per game and field; on screens without a HUD, how often a value is invented.
compare: every setting of a results folder (one subfolder each, as the kit writes them) and the OCR student, scored
the same way on the same examples, the OCR readings written in the format of the VLM's answers.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

from playend.common.paths import STUDENT_OUTPUT, relative
from playend.student.lora import answer, read_examples
from playend.student.vlm import grammar, parse

SUMMARIES = {"score.json", "compare.json"}
NAMES = {"participant_a", "participant_b"}


def run(examples: Path, out: Path, llama: Path, model: Path, mmproj: Path, use_grammar: bool, layers: int,
        limit: int | None):  # fmt: skip
    out.mkdir(parents=True, exist_ok=True)
    tests = read_examples(examples, "test")[:limit]
    for count, example in enumerate(tests, start=1):
        name = Path(example["image"]).stem
        target = out / f"{name}.json"
        if target.exists():
            continue
        command = [str(llama), "-m", str(model), "--mmproj", str(mmproj), "--image", str(examples / example["image"]),
                   "-p", example["prompt"], "-n", "96", "-c", "4096", "--temp", "0", "--seed", "42",
                   "-ngl", str(layers), "--perf"]  # fmt: skip
        if use_grammar:
            grammar_file = out / f"{name}.gbnf"
            grammar_file.write_text(grammar(example["family"]), encoding="utf-8")
            command += ["--grammar-file", str(grammar_file)]
        start = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        wall = time.perf_counter() - start
        (out / f"{name}.log").write_text(result.stderr, encoding="utf-8")
        record = {**example, "output": result.stdout, "exit_code": result.returncode, "wall_s": round(wall, 3)}
        partial = target.with_suffix(".part")  # renamed once whole: a cut never leaves a half record
        partial.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        partial.replace(target)
        if count % 50 == 0:
            print(f"{out.name}: {count}/{len(tests)}", flush=True)


def records(results: Path) -> dict[str, dict]:
    """The records of one setting by example name, without the summaries written next to them."""
    return {path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(results.glob("*.json")) if path.name not in SUMMARIES}  # fmt: skip


def field_outcomes(family: str, expected_answer: str, output: str) -> dict[str, str]:
    """correct, wrong or missed for each field the teacher has; extra for a field read where the teacher has none."""
    expected, read = parse(family, expected_answer), parse(family, output)
    outcomes = {}
    for field in set(expected) | set(read):
        want, got = expected.get(field), read.get(field)
        outcomes[field] = ("extra" if want is None else "missed" if got is None
                           else "correct" if str(got).casefold() == str(want).casefold() else "wrong")  # fmt: skip
    return outcomes


def shares(counts: dict, skip: set[str] = frozenset()) -> dict:
    total = Counter()
    for (_, field), count in counts.items():
        if field not in skip:
            total.update(count)
    expected = total["correct"] + total["wrong"] + total["missed"]
    return {
        "values": expected,
        "correct": total["correct"] / expected if expected else None,
        "wrong": total["wrong"] / expected if expected else None,
        "missed": total["missed"] / expected if expected else None,
        "extra": total["extra"],
    }


def score(results: Path) -> dict:
    counts = defaultdict(Counter)
    walls, empty_screens, invented = [], 0, 0
    for record in records(results).values():
        if record.get("exit_code"):
            counts[("failed", "")]["runs"] += 1
            continue
        walls.append(record["wall_s"])
        if record.get("screen", "gameplay") != "gameplay":
            empty_screens += 1
            invented += bool(parse(record["family"], record["output"]))
            continue
        for field, outcome in field_outcomes(record["family"], record["answer"], record["output"]).items():
            counts[(record["family"], field)][outcome] += 1
    total = shares(counts)
    walls.sort()
    return {
        "examples": len(walls),
        "correct": total["correct"],
        "wrong": total["wrong"],
        "missed": total["missed"],
        "extra": total["extra"],
        "screens_without_hud": empty_screens,
        "screens_without_hud_with_invented_values": invented,
        "median_wall_s": walls[len(walls) // 2] if walls else None,
        "by_field": {f"{family} / {field}": dict(count) for (family, field), count in sorted(counts.items())},
    }


def compare(results: Path, ocr_readings: Path) -> dict:
    settings = {folder.name: records(folder) for folder in sorted(results.iterdir()) if folder.is_dir()}
    readings = json.loads(ocr_readings.read_text(encoding="utf-8"))
    examples = next(iter(settings.values()))
    readers = [*settings, "ocr"]
    counts = {reader: defaultdict(Counter) for reader in readers}
    invented = Counter()
    for name, example in examples.items():
        family = example["family"]
        for reader in readers:
            if reader == "ocr":
                if example["screen"] != "gameplay":  # the classifier keeps these screens away from the OCR
                    continue
                output = answer(family, readings.get(f"{example['session']}:{example['frame_id']}", {}))
            else:
                record = settings[reader][name]
                if record["answer"] != example["answer"]:
                    raise SystemExit(f"{reader}/{name}: not the same expected answer as {next(iter(settings))}")
                output = record["output"]
            if example["screen"] != "gameplay":
                invented[reader] += bool(parse(family, output))
                continue
            for field, outcome in field_outcomes(family, example["answer"], output).items():
                counts[reader][(family, field)][outcome] += 1
    without_hud = sum(example["screen"] != "gameplay" for example in examples.values())
    return {
        "examples": len(examples),
        "screens_without_hud": without_hud,
        "ocr_readings": relative(ocr_readings),
        "readers": {
            reader: {
                "all_fields": shares(counts[reader]),
                "names_excluded": shares(counts[reader], NAMES),
                "screens_without_hud_with_invented_values": None if reader == "ocr" else invented[reader],
                "by_field": {
                    f"{family} / {field}": dict(count) for (family, field), count in sorted(counts[reader].items())
                },
            }
            for reader in readers
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    step = sub.add_parser("run")
    step.add_argument("--examples", type=Path, required=True)
    step.add_argument("--out", type=Path, required=True)
    step.add_argument("--llama", type=Path, required=True)
    step.add_argument("--model", type=Path, required=True)
    step.add_argument("--mmproj", type=Path, required=True)
    step.add_argument("--grammar", action="store_true")
    step.add_argument("--layers", type=int, default=99, help="layers on the graphics card (0: processor only)")
    step.add_argument("--limit", type=int)
    step = sub.add_parser("score")
    step.add_argument("results", type=Path)
    step = sub.add_parser("compare")
    step.add_argument("results", type=Path, help="folder with one subfolder of records per setting (results/vlm)")
    step.add_argument(
        "--ocr", type=Path, default=STUDENT_OUTPUT / "readings_ocr.json", help="the OCR student's readings"
    )
    args = parser.parse_args()
    if args.step == "run":
        run(args.examples, args.out, args.llama, args.model, args.mmproj, args.grammar, args.layers, args.limit)
    elif args.step == "compare":
        summary = compare(args.results, args.ocr)
        (args.results / "compare.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{summary['examples']} examples, {summary['screens_without_hud']} of them without a HUD")
        for reader, found in summary["readers"].items():
            total, invented = found["all_fields"], found["screens_without_hud_with_invented_values"]
            invented = "-" if invented is None else invented
            print(
                f"{reader:17} correct {total['correct']:.1%}, wrong {total['wrong']:.1%}, missed {total['missed']:.1%}"
                f" of {total['values']} values; invented on {invented} screens without a HUD"
            )
    else:
        summary = score(args.results)
        (args.results / "score.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
        parts = ", ".join(f"{key} {summary[key]:.1%}" for key in ("correct", "wrong", "missed"))
        print(f"{args.results.name}: {summary['examples']} examples, {parts}, median {summary['median_wall_s']} s")


if __name__ == "__main__":
    main()
