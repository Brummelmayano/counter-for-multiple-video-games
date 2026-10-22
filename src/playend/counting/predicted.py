"""Replay the counter with the ends and billing modes a detector predicts, and count what its errors cost.

The detectors of the training run read each held-out session from a PlayEnd package: the teacher's observations, or a
student package (playend.student.package). GRU: its final models; gradient boosting: refitted as in
playend.student.endings. An end is the first capture of a run at or above the threshold the run chose for the budget,
as in the evaluation but without the masks of uncertain intervals, which the Pi does not have. The billing mode is the
GRU's, or the reference's with --modes reference (gradient boosting has no billing mode). The game and its type come
from the package's observations. With --run, the detectors come from a training run made on the package itself (the
student's kit retrained them on the student's package): their stored predictions are replayed as they are.

Each counted game is paired with at most one counted game of the reference (units.csv, same rules), the pairs that
share the most time first, as in the event-based metrics of sound event detection (Mesaros et al., 2016). A game left
without a pair is counted too many (the client pays for it) or missed (the arcade loses it). Time-based play is
compared second by second.

usage: python -m playend.counting.predicted [--package build/student/packages/student] [--modes reference]
       [--model boosting] [--run RUN_FOLDER]
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np

from playend.common.files import sha256
from playend.common.paths import REPO
from playend.counting import rules as counting_rules
from playend.counting.engine import Capture, Game, TimePlayed, count
from playend.counting.replay import captures, reference, replay
from playend.dataset.csvfiles import read_csv
from playend.student.endings import RUN, probabilities
from playend.training import data
from playend.training.data import BILLING_MODES
from playend.training.protocol import BUDGETS
from playend.training.report import final_arrays, held_out, load_run, thresholds
from playend.training.store import Store

TEACHER = REPO / "build" / "playend_v1.0"
OUT = REPO / "build" / "counting" / "predicted"


def sessions_of(package: Path) -> dict[str, list[dict]]:
    rows = defaultdict(list)
    for row in read_csv(package / "data" / "observations.csv")[1]:
        rows[row["session_id"]].append(row)
    return {session: sorted(items, key=lambda row: int(row["frame_id"])) for session, items in rows.items()}


def predicted_captures(rows: list[dict], prob: np.ndarray, modes: list[str], threshold: float) -> list[Capture]:
    above = prob >= threshold
    starts = above & ~np.concatenate(([False], above[:-1]))
    session = []
    for row, end, mode in zip(rows, starts, modes):
        # the package's own reading: a student package keeps the teacher's columns and replaces observation_json
        game = json.loads(row["observation_json"])["game"]
        session.append(Capture(int(row["frame_id"]), float(row["t_s"]), bool(end), mode, game["type"], game["title"]))
    return session


def span(event: Game | TimePlayed, times: dict[int, float]) -> tuple[float, float]:
    return times[event.first_frame], times[event.last_frame]


def shared(a: tuple[float, float], b: tuple[float, float]) -> float:
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def paired(mine: list[Game], theirs: list[Game], times: dict[int, float]) -> int:
    """How many games of each side can be paired one to one, the pairs that share the most time first."""
    overlaps = sorted(
        ((shared(span(a, times), span(b, times)), i, j) for i, a in enumerate(mine) for j, b in enumerate(theirs)),
        reverse=True,
    )
    used_mine, used_theirs = set(), set()
    for overlap, i, j in overlaps:
        if overlap <= 0:
            break
        if i not in used_mine and j not in used_theirs:
            used_mine.add(i)
            used_theirs.add(j)
    return len(used_mine)


def compare(events: list, expected: list, times: dict[int, float]) -> dict:
    mine = [event for event in events if isinstance(event, Game) and event.counted]
    theirs = [event for event in expected if isinstance(event, Game) and event.counted]
    pairs = paired(mine, theirs, times)
    my_time = [span(event, times) for event in events if isinstance(event, TimePlayed)]
    their_time = [span(event, times) for event in expected if isinstance(event, TimePlayed)]
    common = sum(shared(a, b) for a in my_time for b in their_time)
    return {
        "games_reference": len(theirs),
        "games": len(mine),
        "games_too_many": len(mine) - pairs,
        "games_missed": len(theirs) - pairs,
        "quick_restarts": count(events).quick_restarts,
        "time_reference_s": count(expected).time_s,
        "time_s": count(events).time_s,
        "time_too_much_s": sum(end - start for start, end in my_time) - common,
        "time_missed_s": sum(end - start for start, end in their_time) - common,
    }


def summary(sessions: list[dict]) -> dict:
    total = {key: sum(session[key] for session in sessions) for key in sessions[0]}
    games = total["games_reference"]
    errors = [abs(session["games"] - session["games_reference"]) for session in sessions]
    return total | {
        "too_many_per_100": 100 * total["games_too_many"] / games,
        "missed_per_100": 100 * total["games_missed"] / games,
        "count_error_per_session": statistics.mean(errors),
        "sessions_exact": sum(error == 0 for error in errors) / len(errors),
        "sessions_within_one": sum(error <= 1 for error in errors) / len(errors),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--package", type=Path, default=TEACHER, help="PlayEnd package the detector reads")
    parser.add_argument("--model", choices=("gru", "boosting"), default="gru")
    parser.add_argument("--modes", choices=("predicted", "reference"), default="predicted")
    parser.add_argument("--run", type=Path, help="a training run made on the package: replay its stored predictions")
    args = parser.parse_args()
    if args.model == "boosting" and args.modes == "predicted":
        parser.error("gradient boosting predicts no billing mode: use --modes reference")
    rules = counting_rules.load()
    if args.run:
        settings, choices = load_run(args.run)
        made_on = settings["package"]["data/observations.csv"]
        if made_on != sha256(args.package / "data" / "observations.csv"):
            raise SystemExit(f"{args.run} was not trained on the observations of {args.package}")
        store = Store(args.run)
        runs = final_arrays(store, settings, choices, args.model)
        modes = final_arrays(store, settings, choices, "gru", ":billing") if args.modes == "predicted" else []
    else:
        teacher, package = data.load(TEACHER), data.load(args.package)
        settings, choices = load_run(RUN)
        runs, modes = probabilities(args.model, teacher, package, settings, choices, Store(RUN), False)
    truth, rows = sessions_of(TEACHER), sessions_of(args.package)
    units, segments = defaultdict(list), defaultdict(list)
    for unit in read_csv(TEACHER / "data" / "units.csv")[1]:
        units[unit["session_id"]].append(unit)
    for segment in read_csv(TEACHER / "data" / "time_segments.csv")[1]:
        segments[segment["session_id"]].append(segment)

    expected, times = {}, {}
    for session in held_out(settings):
        truth_captures = captures(truth[session])
        expected[session] = reference(truth_captures, units[session], segments[session], rules)
        times[session] = {capture.frame: capture.t for capture in truth_captures}

    results = {}
    for budget in BUDGETS:
        limits = thresholds(settings, choices, args.model, budget)
        by_seed = []
        for seed, probs in enumerate(runs):
            sessions = []
            for session in held_out(settings):
                if len(rows[session]) != len(probs[session]):
                    raise SystemExit(f"{session}: {len(rows[session])} observations, {len(probs[session])} rows")
                if args.modes == "reference":
                    session_modes = [row["billing_mode"] for row in truth[session]]
                else:
                    session_modes = [BILLING_MODES[mode] for mode in modes[seed][session]]
                events = replay(
                    predicted_captures(rows[session], probs[session], session_modes, limits[session]), rules
                )
                sessions.append(compare(events, expected[session], times[session]))
            by_seed.append(summary(sessions))
        results[str(budget)] = {key: statistics.mean(seed[key] for seed in by_seed) for key in by_seed[0]} | {
            "seeds": by_seed
        }

    OUT.mkdir(parents=True, exist_ok=True)
    name = f"{args.package.name}_{args.model}_{args.modes}_modes" + ("_retrained" if args.run else "")
    (OUT / f"{name}.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    for budget, result in results.items():
        print(
            f"{name} budget {budget}: games {result['games']:.1f} for {result['games_reference']:.0f}, "
            f"too many {result['too_many_per_100']:.1f} and missed {result['missed_per_100']:.1f} per 100, "
            f"sessions exact {result['sessions_exact']:.0%} (within one {result['sessions_within_one']:.0%}), "
            f"time {result['time_s'] / 60:.0f} min for {result['time_reference_s'] / 60:.0f} "
            f"(too much {result['time_too_much_s'] / 60:.0f}, missed {result['time_missed_s'] / 60:.0f})"
        )
    print(f"written to {OUT / name}.json")


if __name__ == "__main__":
    main()
