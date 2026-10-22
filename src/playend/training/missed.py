"""Every end of a training run, whether each detector found it, and how the end is proved, to study the ends missed.

For each end of a held-out session (masked intervals left out, as in the evaluation), at the budget of one false end per
100 games: found or missed by each detector (the GRU by the number of its seeds that found it), the peak probability
of the GRU and of gradient boosting next to the threshold of the round, and what the observations show around the end:
an end screen on the capture that proves it (the result is shown or the phase is after the game, the rule of the
validation tool), the type of that screen, the captures in between, the participants and the score before and after.

usage: python -m playend.training.missed [--package PACKAGE] [--out RUN_FOLDER]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from playend.common.paths import REPO
from playend.dataset.csvfiles import read_csv
from playend.training import data, report
from playend.training.events import match
from playend.training.protocol import BUDGETS
from playend.training.store import Store

DETECTORS = ("gru", "boosting", "logistic", "rules")
RESTART_WORDS = re.compile(r"relanc|recommen|quitt|abandon|réessa", re.I)


def readable(observation: dict) -> bool:
    return any(value is not None for value in (*score(observation), observation["clock"]["display"]))


def score(observation: dict) -> tuple:
    return observation["score"]["a"], observation["score"]["b"]


def end_screen(observation: dict) -> bool:
    return observation["result"]["visible"] is True or observation["state"]["phase"] == "post_game"


def outcomes(store: Store, corpus, settings: dict, choices: dict) -> dict:
    """{(session, row of the end): {detector: [found by each seed], detector_peak, detector_threshold}}."""
    found_by = defaultdict(lambda: defaultdict(list))
    for model in DETECTORS:
        runs = report.predictions(store, corpus, settings, choices, model)
        limits = report.thresholds(settings, choices, model, BUDGETS[0])
        for session in report.held_out(settings):
            sequence = corpus.sequences[session]
            for probs in runs:
                found, missed, _ = match(sequence, probs[session], limits[session])
                for row in found + missed:
                    found_by[(session, row)][model].append(row in found)
            if model in ("gru", "boosting"):
                mean = np.mean([probs[session] for probs in runs], axis=0)
                for row in np.flatnonzero((sequence.end == 1) & sequence.usable):
                    found_by[(session, int(row))][f"{model}_peak"] = float(mean[row : row + 2].max())
                    found_by[(session, int(row))][f"{model}_threshold"] = float(limits[session])
    return found_by


def ends_table(package: Path, run: Path) -> list[dict]:
    settings, choices = report.load_run(run)
    corpus = data.load(package)
    observations, times, families = defaultdict(dict), defaultdict(dict), defaultdict(dict)
    for row in read_csv(package / "data" / "observations.csv")[1]:
        frame = int(row["frame_id"])
        observations[row["session_id"]][frame] = json.loads(row["observation_json"])
        times[row["session_id"]][frame] = float(row["t_s"])
        families[row["session_id"]][frame] = row["game_family"]
    units = {
        (unit["session_id"], int(unit["end_established_at"])): unit
        for unit in read_csv(package / "data" / "units.csv")[1]
        if unit["end_established_at"]
    }
    single = report.single_session_families(corpus.sequences.values())
    table = []
    for (session, row), result in sorted(outcomes(Store(run), corpus, settings, choices).items()):
        seen = observations[session]
        frames = sorted(seen)
        end = frames[row]
        unit = units[(session, end)]
        first, last = int(unit["first_frame"]), int(unit["last_frame"])
        between = [frame for frame in frames if last < frame < end]
        before = next((f for f in reversed(range(first, last + 1)) if f in seen and readable(seen[f])), None)
        after = next(
            (f for f in frames if f >= end and readable(seen[f]) and seen[f]["state"]["screen_type"] == "gameplay"),
            None,
        )
        names_before = seen[before]["participants"]["primary"] if before else []
        names_after = seen[after]["participants"]["primary"] if after else []
        table.append({
            "session": session, "unit": unit["unit_id"], "family": unit["game_family"],
            "single_session_game": unit["game_family"] in single, "last_frame": last, "end_frame": end,
            "captures_after_last": end - last,
            "seconds_after_last": round(times[session][end] - times[session][last], 1),
            "end_screen": end_screen(seen[end]), "proof_screen": seen[end]["state"]["screen_type"],
            "screens_between": "|".join(seen[frame]["state"]["screen_type"] for frame in between),
            "unreadable_between": any(not readable(seen[frame]) for frame in between),
            "score_before": score(seen[before]) if before else None,
            "score_after": score(seen[after]) if after else None,
            "same_participants": bool(names_before) and names_before == names_after,
            "game_after": families[session][after] if after else "",
            "restart_words": bool(RESTART_WORDS.search(unit["evidence"])),
            "gru_seeds_found": sum(result["gru"]), "gru": sum(result["gru"]) * 2 > len(result["gru"]),
            "boosting": result["boosting"][0], "logistic": result["logistic"][0], "rules": result["rules"][0],
            "gru_peak": round(result["gru_peak"], 3), "gru_threshold": round(result["gru_threshold"], 3),
            "boosting_peak": round(result["boosting_peak"], 3),
            "boosting_threshold": round(result["boosting_threshold"], 3),
            "evidence": unit["evidence"],
        })  # fmt: skip
    return table


def recall_by(table: list[dict], key) -> list[str]:
    groups = defaultdict(list)
    for end in table:
        groups[key(end)].append(end)
    lines = []
    for value, ends in sorted(groups.items(), key=lambda item: -len(item[1])):
        shares = "  ".join(f"{model} {sum(end[model] for end in ends) / len(ends):4.0%}" for model in DETECTORS)
        missed = sum(not any(end[model] for model in DETECTORS) for end in ends)
        lines.append(f"  {str(value)[:32]:32} {len(ends):4} ends  {shares}  missed by all {missed}")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--package", type=Path, default=REPO / "build" / "playend_v1.0")
    parser.add_argument("--out", type=Path, default=REPO / "build" / "training" / "v1")
    args = parser.parse_args()
    table = ends_table(args.package, args.out)
    path = args.out / "ends.csv"
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    print(f"{len(table)} ends; found: " + ", ".join(f"{m} {sum(end[m] for end in table)}" for m in DETECTORS))
    for name, key in (
        ("end screen on the capture that proves the end", lambda end: end["end_screen"]),
        ("screen that proves the end", lambda end: end["proof_screen"]),
        ("same participants before and after", lambda end: end["same_participants"]),
        ("restarted or abandoned (words of the evidence)", lambda end: end["restart_words"]),
        ("game played in one session only", lambda end: end["single_session_game"]),
        ("game", lambda end: end["family"]),
    ):
        print(name)
        print("\n".join(recall_by(table, key)))
    near = Counter(end["family"] for end in table if not end["boosting"] and end["boosting_peak"] >= 0.5)
    print(f"gradient boosting: {sum(near.values())} missed ends with a probability of 0.5 or more, under the threshold")
    print(f"written to {path}")


if __name__ == "__main__":
    main()
