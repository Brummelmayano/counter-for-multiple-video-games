"""Condensed session timeline: one line per run of consecutive observations that share the same title, state,
participants, score, period, result and position, with the clock and players-left range of the run.

usage: python -m playend.boundaries.condense session_<id> [--note N]
"""

import argparse

from playend.annotation.notes import READING_MARKERS, strip_markers
from playend.boundaries.timeline import observations


def run_key(obs: dict) -> tuple[str, ...]:
    score, period, result = obs["score"], obs["period"], obs["result"]
    return (
        (obs["game"]["title"] or "-")[:12],
        obs["state"]["phase"],
        obs["state"]["screen_type"],
        "/".join(name[:10] for name in obs["participants"]["primary"][:2]),
        f"{score['a']}-{score['b']}" if score["a"] is not None or score["b"] is not None else "",
        f"{period['type']}{period['number'] or ''}" if period["type"] not in ("none", "unknown") else "",
        f"RES:{result['outcome_type']}:{result['winner']}" if result["visible"] else "",
        f"#{obs['position']['current']}" if obs["position"]["current"] else "",
    )


def describe(run: list[tuple[int, dict, str]], note_width: int) -> str:
    first, last = run[0][0], run[-1][0]
    clocks = [obs["clock"]["display"] for _, obs, _ in run if obs["clock"]["visible"]]
    players = [
        counter
        for _, obs, _ in run
        for counter in (obs.get("secondary_counters") or [])
        if counter["kind"] in ("players_remaining", "teams_remaining")
    ]
    note = strip_markers(run[0][2], READING_MARKERS).split(" || ")[0][:note_width]
    text = f"{first}-{last} ({len(run)}) " + " ".join(part for part in run_key(run[0][1]) if part)
    if clocks:
        text += f" C:{clocks[0]}→{clocks[-1]}"
    if players:
        text += f" pl:{players[0]['value']}→{players[-1]['value']}"
    if note_width:
        text += f" | {note}"
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("session")
    parser.add_argument("--note", type=int, default=60)
    args = parser.parse_args()
    data = observations(args.session)
    run: list[tuple[int, dict, str]] = []
    for fid in sorted(data):
        _, obs, note = data[fid]
        if run and run_key(obs) != run_key(run[-1][1]):
            print(describe(run, args.note))
            run = []
        run.append((fid, obs, note))
    if run:
        print(describe(run, args.note))


if __name__ == "__main__":
    main()
