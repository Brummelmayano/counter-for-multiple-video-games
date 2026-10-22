"""The whole student on capture sessions, one capture at a time, as on the Pi: from the image to the count.

For each capture, in order: the classifier gives the game (with its vote) and the screen; on a screen it does not
take for gameplay, the OCR reads the whole capture for a banner; a lone switch between gameplay and the other screens
waits for the next capture (SteadyScreen); on a gameplay screen the HUD is read (reading boxes, zones, marks); the
observation follows the teacher's conventions (student_view) and the contract; FeatureStream gives the causal
features; the GRU, in NumPy, gives the probability of an end and the billing mode; the counter turns them into games
and time.

prepare (PC): the captures of the chosen sessions, the student's models, the game profiles and, for each session, the
final GRU of the training run that did not see it, with the threshold of the budget, in one folder for the Pi.
run (Pi or PC): one JSON record per capture, so a power cut loses only the capture in progress. On a restart the
records give back what was read, and the rest (screen, observation, features, GRU, counter) is computed again.
compare (PC): two runs of the same captures, capture by capture, and their times.
"""

from __future__ import annotations

import argparse
import json
import resource
import shutil
import statistics
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image

from playend.common.paths import COUNTING_RULES, STUDENT_MODELS, STUDENT_OUTPUT
from playend.contract.contract import validate_observation
from playend.contract.temporal import FeatureStream
from playend.counting import rules as counting_rules
from playend.counting.engine import Capture, Engine, count
from playend.dataset.csvfiles import read_csv
from playend.dataset.features import nanoseconds
from playend.student.apply import Classifier, EndDetector, Marks
from playend.student.collect import frame_paths
from playend.student.features import ImageFeatures
from playend.student.ocr import TextReader
from playend.student.package import PACKAGE, SteadyScreen, profiles, student_view
from playend.student.rules import INFINITY_AS_EIGHT
from playend.student.run import read_hud, save, saved, temperature
from playend.student.zones import LAYOUTS
from playend.training.data import BILLING_MODES

RULES_FILE = "regles_facturation.json"


def short(session: str) -> str:
    return session.removeprefix("session_")[:8]


def prepare(sessions: list[str], out: Path, budget: float) -> None:
    from playend.student.endings import RUN
    from playend.training.protocol import final_jobs
    from playend.training.report import load_run, thresholds
    from playend.training.store import Store

    if out.exists():
        raise SystemExit(f"{out} already exists")
    models = out / "models"
    shutil.copytree(STUDENT_MODELS, models)
    for name in ("classifier.npz", "marks.npz"):
        shutil.copy2(STUDENT_OUTPUT / name, models / name)
    shutil.copy2(COUNTING_RULES, models / RULES_FILE)
    game_profiles = [{"game": game, "infinite_clock": infinite, "profile": profile}
                     for (game, infinite), profile in profiles().items()]  # fmt: skip
    (models / "profiles.json").write_text(json.dumps(game_profiles, ensure_ascii=False, indent=1), encoding="utf-8")

    settings, choices = load_run(RUN)
    store, limits = Store(RUN), thresholds(settings, choices, "gru", budget)
    for session in sessions:
        job = next(job for job in final_jobs(choices[session], session, settings["seeds"]) if job.model == "gru")
        state = store.model(job.id)
        weights = {name: tensor.numpy().astype(np.float32) for name, tensor in state["weights"].items()}
        np.savez(
            models / f"detector_{short(session)}.npz",
            weight_ih=weights["gru.weight_ih_l0"], weight_hh=weights["gru.weight_hh_l0"],
            bias_ih=weights["gru.bias_ih_l0"], bias_hh=weights["gru.bias_hh_l0"],
            end_weight=weights["end.weight"], end_bias=weights["end.bias"],
            billing_weight=weights["billing.weight"], billing_bias=weights["billing.bias"],
            columns=np.array(state["columns"]), threshold=np.float64(limits[session]), seed=np.int64(job.seed),
        )  # fmt: skip

    rows = [row for row in read_csv(PACKAGE / "data" / "observations.csv")[1] if row["session_id"] in sessions]
    paths = {session: frame_paths(session) for session in sessions}
    frames = []
    for row in sorted(rows, key=lambda row: (sessions.index(row["session_id"]), int(row["frame_id"]))):
        image = Path("frames") / short(row["session_id"]) / f"{int(row['frame_id']):05d}.jpg"
        (out / image).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(paths[row["session_id"]][int(row["frame_id"])], out / image)
        frames.append({"session": row["session_id"], "frame_id": int(row["frame_id"]), "t_s": row["t_s"],
                       "image": str(image)})  # fmt: skip
    (out / "frames.json").write_text(json.dumps(frames, indent=1), encoding="utf-8")
    print(f"{len(frames)} captures of {len(sessions)} sessions in {out}")


def read_capture(item: dict, folder: Path, readers: dict) -> dict:
    """What the student reads on one capture: game, screen, banner and HUD, with the time of each step."""
    times = {}
    start = time.perf_counter()
    frame = Image.open(folder / item["image"]).convert("RGB")
    times["load_s"] = time.perf_counter() - start
    step = time.perf_counter()
    features = readers["features"](frame)
    game_label = readers["classifier"].label("game", features)
    screen, _ = readers["classifier"].label("screen", features)
    times["classify_s"] = time.perf_counter() - step
    banner = None
    if screen != "gameplay":
        step = time.perf_counter()
        banner = [[line.text, line.score, *line.box] for line in readers["text"].read(frame)]
        times["banner_s"] = time.perf_counter() - step
    return {"game_label": [game_label[0], float(game_label[1])], "screen_raw": screen, "banner": banner,
            "times": times, "frame": frame}  # fmt: skip


def run(folder: Path, out: Path) -> None:
    frames = json.loads((folder / "frames.json").read_text(encoding="utf-8"))
    models = folder / "models"
    readers = {"features": ImageFeatures(models / "mobilenetv2-12.onnx"), "text": TextReader(models),
               "classifier": Classifier(models / "classifier.npz"), "marks": Marks(models / "marks.npz")}  # fmt: skip
    game_profiles = {(item["game"], item["infinite_clock"]): item["profile"]
                     for item in json.loads((models / "profiles.json").read_text(encoding="utf-8"))}  # fmt: skip
    rules = counting_rules.load(models / RULES_FILE)
    sessions = defaultdict(list)
    for item in frames:
        sessions[item["session"]].append(item)

    for session, items in sessions.items():
        records = out / short(session)
        records.mkdir(parents=True, exist_ok=True)
        detector = EndDetector(models / f"detector_{short(session)}.npz")
        classifier, screens, stream, engine = readers["classifier"], SteadyScreen(), FeatureStream(), Engine(rules)
        classifier.recent.clear()
        above, events, decisions = False, [], []
        for item in items:
            target = records / f"{item['frame_id']:05d}.json"
            done = saved(target)
            read = done or read_capture(item, folder, readers)
            classifier.recent.append(tuple(read["game_label"]))
            game = classifier.vote()
            texts = [line[0] for line in read["banner"]] if read["banner"] is not None else None
            screen = screens.step(read["screen_raw"], texts)
            if done is None:
                fields = {}
                if screen == "gameplay" and game in LAYOUTS:
                    fields = read_hud(readers["text"], readers["marks"], read["frame"], game, read["times"])
                read["fields"] = fields
                read["times"]["read_s"] = sum(read["times"].values())
            step = time.perf_counter()
            fields = read["fields"]
            profile = game_profiles.get((game, fields.get("clock_display") == INFINITY_AS_EIGHT)) or game_profiles.get(
                (game, False), {}
            )
            observation = student_view(game, screen, fields, texts, profile)
            missing = bool(validate_observation(observation))
            record = {"session_id": session, "frame_id": item["frame_id"],
                      "received_monotonic_ns": nanoseconds(item["t_s"]), "observation": observation,
                      "observation_missing": missing}  # fmt: skip
            features = stream.step(record)
            probability, billing = detector.step(np.array([features[name] for name in detector.columns], np.float32))
            end = probability >= detector.threshold and not above
            above = probability >= detector.threshold
            capture = Capture(item["frame_id"], float(item["t_s"]), end, BILLING_MODES[billing],
                              observation["game"]["type"], observation["game"]["title"])  # fmt: skip
            events += engine.observe(capture)
            decide_s = time.perf_counter() - step
            decisions.append({"frame_id": item["frame_id"], "game": game, "screen": screen, "observation": observation,
                              "observation_missing": missing, "probability": probability, "end": end,
                              "billing_mode": BILLING_MODES[billing]})  # fmt: skip
            if done is None:
                read.pop("frame")
                read["times"]["decide_s"] = decide_s
                read["times"]["total_s"] = read["times"]["read_s"] + decide_s
                save({**item, **read, "game": game, "screen": screen, "temp_c": temperature(),
                      "max_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}, target)  # fmt: skip
        events += engine.close()
        summary = {"session": session, "captures": len(items), "threshold": detector.threshold,
                   "count": asdict(count(events)), "events": [event.as_dict() for event in events],
                   "decisions": decisions}  # fmt: skip
        save(summary, out / f"{short(session)}.json")
        print(f"{short(session)}: {len(items)} captures, {summary['count']}")


def records_of(out: Path) -> dict[str, list[dict]]:
    """The capture records of a run, by session."""
    return {folder.name: [json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("*.json"))]
            for folder in sorted(out.iterdir()) if folder.is_dir()}  # fmt: skip


def timing(records: list[dict]) -> str:
    def spread(values: list[float]) -> str:
        if not values:
            return "-"
        values = sorted(values)
        p90 = values[int(0.9 * (len(values) - 1))]
        return f"median {statistics.median(values):.2f} s, p90 {p90:.2f}, max {values[-1]:.2f}"

    gameplay = [record["times"]["total_s"] for record in records if record["screen"] == "gameplay"]
    other = [record["times"]["total_s"] for record in records if record["screen"] != "gameplay"]
    lines = [
        f"  every capture: {spread([record['times']['total_s'] for record in records])}",
        f"  gameplay: {spread(gameplay)} ({len(gameplay)})",
        f"  other screens: {spread(other)} ({len(other)})",
    ]
    for step in ("classify_s", "banner_s", "boxes_s", "zones_s", "marks_s", "decide_s"):
        lines.append(f"  {step}: {spread([record['times'][step] for record in records if step in record['times']])}")
    temperatures = [record["temp_c"] for record in records if record.get("temp_c") is not None]
    if temperatures:
        lines.append(f"  temperature at most {max(temperatures):.0f} °C")
    lines.append(f"  memory at most {max(record['max_rss_mb'] for record in records):.0f} MB")
    return "\n".join(lines)


def compare(first: Path, second: Path) -> None:
    runs = records_of(first), records_of(second)
    for session in sorted(set(runs[0]) & set(runs[1])):
        pairs = list(zip(runs[0][session], runs[1][session]))
        differing = defaultdict(int)
        for a, b in pairs:
            for key in ("game", "screen", "banner", "fields"):
                differing[key] += (
                    a[key] != b[key]
                    if key != "banner"
                    else ([line[0] for line in a[key] or []] != [line[0] for line in b[key] or []])
                )
        summaries = [json.loads((run / f"{session}.json").read_text(encoding="utf-8"))
                     for run in (first, second) if (run / f"{session}.json").exists()]  # fmt: skip
        print(f"{session}: {len(pairs)} captures in both, differing {dict(differing)}")
        if len(summaries) == 2:
            probabilities = [abs(a["probability"] - b["probability"])
                             for a, b in zip(summaries[0]["decisions"], summaries[1]["decisions"])]  # fmt: skip
            same_ends = [a["end"] for a in summaries[0]["decisions"]] == [b["end"] for b in summaries[1]["decisions"]]
            print(f"  largest gap in end probability {max(probabilities):.2e}, same ends {same_ends}, "
                  f"counts {summaries[0]['count']} / {summaries[1]['count']}")  # fmt: skip
        for name, run in zip((first, second), runs):
            print(f" {name}\n{timing(run[session])}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    making = commands.add_parser("prepare", help="the folder to copy on the Pi")
    making.add_argument("sessions", nargs="+", help="session ids, in the order the Pi reads them")
    making.add_argument("--out", type=Path, default=STUDENT_OUTPUT / "pi_loop")
    making.add_argument("--budget", type=float, default=1.0, help="false ends per 100 games of the threshold")
    running = commands.add_parser("run", help="read every capture of the folder, in order")
    running.add_argument("folder", type=Path)
    running.add_argument("--out", type=Path, required=True)
    comparing = commands.add_parser("compare", help="two runs of the same captures")
    comparing.add_argument("first", type=Path)
    comparing.add_argument("second", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        known = {row["session_id"] for row in read_csv(PACKAGE / "data" / "splits.csv")[1]}
        sessions = [next(name for name in known if short(name).startswith(prefix)) for prefix in args.sessions]
        prepare(sessions, args.out, args.budget)
    elif args.command == "run":
        run(args.folder, args.out)
    else:
        compare(args.first, args.second)


if __name__ == "__main__":
    main()
