"""Replay the sessions of a PlayEnd package through the counter with the verified ends.

The count is compared with a reference taken straight from units.csv and time_segments.csv, under the same rules.

usage: python -m playend.counting.replay [--package build/playend_v1.0] [--out build/counting/truth]
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from playend.common.files import write_jsonl
from playend.common.paths import REPO
from playend.counting import rules as counting_rules
from playend.counting.engine import PER_GAME, Capture, Engine, Game, TimePlayed, count, game_type
from playend.dataset.csvfiles import read_csv, write_csv


def captures(rows: list[dict]) -> list[Capture]:
    return [
        Capture(
            frame=int(row["frame_id"]),
            t=float(row["t_s"]),
            end=row["unit_end_boundary"] == "1",
            mode=row["billing_mode"],
            game_type=row["game_type"] or None,
            game=row["game_family"] or None,
        )
        for row in rows
    ]


def replay(session: list[Capture], rules: counting_rules.Rules) -> list[Game | TimePlayed]:
    engine = Engine(rules)
    events = [event for capture in session for event in engine.observe(capture)]
    return events + engine.close()


def reference(
    session: list[Capture], units: list[dict], segments: list[dict], rules: counting_rules.Rules
) -> list[Game | TimePlayed]:
    by_frame = {capture.frame: capture for capture in session}
    events = []
    for unit in units:
        first, last = int(unit["first_frame"]), int(unit["last_frame"])
        types = Counter(
            by_frame[frame].game_type
            for frame in range(first, last + 1)
            if by_frame[frame].mode == PER_GAME and by_frame[frame].game_type not in (None, "unknown")
        )
        kind = game_type(types, rules)
        duration = int(by_frame[last].t - by_frame[first].t)
        end = int(unit["end_established_at"]) if unit["end_established_at"] else None
        threshold = rules.threshold(kind)
        events.append(Game(first, last, end, duration, unit["game_family"], kind, threshold, duration >= threshold))
    for segment in segments:
        first, last = int(segment["first_frame"]), int(segment["last_frame"])
        events.append(TimePlayed(first, last, int(by_frame[last].t - by_frame[first].t), segment["game_family"]))
    return events


def differences(session_id: str, engine: list, expected: list) -> list[dict]:
    """Games cut or counted differently, matched by the capture that ended them (None for a game open at the end)."""
    mine = {event.end_frame: event for event in engine if isinstance(event, Game)}
    theirs = {event.end_frame: event for event in expected if isinstance(event, Game)}
    found = []
    for end in sorted(set(mine) | set(theirs), key=lambda frame: -1 if frame is None else frame):
        a, b = mine.get(end), theirs.get(end)
        if a is None or b is None:
            difference = "missing"
        elif a.counted != b.counted:
            difference = "counted"
        elif (a.first_frame, a.last_frame) != (b.first_frame, b.last_frame):
            difference = "cut"
        else:
            continue
        found.append(
            {
                "session_id": session_id,
                "end_frame": end,
                "difference": difference,
                "engine": a and asdict(a),
                "reference": b and asdict(b),
            }
        )
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a PlayEnd package through the counter.")
    parser.add_argument("--package", type=Path, default=REPO / "build" / "playend_v1.0", help="PlayEnd package folder")
    parser.add_argument("--out", type=Path, default=REPO / "build" / "counting" / "truth", help="results folder")
    args = parser.parse_args()
    rules = counting_rules.load()
    rows, units, segments = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in read_csv(args.package / "data" / "observations.csv")[1]:
        rows[row["session_id"]].append(row)
    for unit in read_csv(args.package / "data" / "units.csv")[1]:
        units[unit["session_id"]].append(unit)
    for segment in read_csv(args.package / "data" / "time_segments.csv")[1]:
        segments[segment["session_id"]].append(segment)

    table, ledger, changed = [], [], []
    for session_id in sorted(rows):
        session = captures(sorted(rows[session_id], key=lambda row: int(row["frame_id"])))
        events = replay(session, rules)
        expected = reference(session, units[session_id], segments[session_id], rules)
        mine, theirs = count(events), count(expected)
        table.append(
            {"session_id": session_id}
            | {f"{key}_reference": value for key, value in asdict(theirs).items() if key != "unseen_s"}
            | asdict(mine)
        )
        ledger += [{"session_id": session_id, **event.as_dict()} for event in events]
        changed += differences(session_id, events, expected)

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "sessions.csv", list(table[0]), table)
    write_jsonl(args.out / "events.jsonl", ledger)
    write_jsonl(args.out / "differences.jsonl", changed)

    total = {key: sum(row[key] for row in table) for key in table[0] if key != "session_id"}
    print(f"rules {rules.version}, {len(table)} sessions")
    for key in ("games", "quick_restarts", "time_s"):
        print(f"  {key:15} reference {total[key + '_reference']:>7}   counter {total[key]:>7}")
    print(f"  games differing: {dict(Counter(item['difference'] for item in changed))}")
    unseen = [line for line in ledger if line["unseen_s"] and (line["kind"] == "time" or line["counted"])]
    print(f"  lines with time without an image (over {rules.gap_s} s between captures): {len(unseen)}")
    for line in unseen:
        session = line["session_id"].removeprefix("session_")[:8]
        print(f"    {session} {line['kind']} {line['game']}: {line['unseen_s']} s of {line['duration_s']} s")
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()
