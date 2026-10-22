"""Print one compact line per annotated observation of a session, in chronological order, to place boundaries.

usage: python -m playend.boundaries.timeline session_<id> [FIRST-LAST] [--note N]
Columns: frame, Δt (s), title, phase/screen, participants, score, clock, period, result, position, counters, timers,
then the first N characters of the per-image note (default 90; 0 = none).
"""

from __future__ import annotations

import argparse
import json

from playend.annotation.lots import source_rows
from playend.annotation.notes import CORRECTION_MARKERS, READING_MARKERS, strip_markers
from playend.common.paths import resolve
from playend.corrections.traces import effective


def observations(session: str) -> dict[int, tuple[dict, dict, str]]:
    """Per frame: its source manifest row, its effective observation and its note.

    The effective observation is the corrected one when a correction trace replaces the lot's file.
    """
    sources = source_rows(session)
    result = {}
    for fid, entry in effective(session).items():
        obs = json.loads(resolve(entry["annotation_path"]).read_text(encoding="utf-8"))
        meta = json.loads(resolve(entry["metadata_path"]).read_text(encoding="utf-8"))
        note = meta.get("annotation_note") or meta.get("note") or ""
        if entry["corrected_by"]:
            note = "[corrigé] " + strip_markers(note, CORRECTION_MARKERS)
        result[fid] = (sources[fid], obs, note)
    return result


def format_line(fid, previous_ns, source, obs, note, width):
    """Frame, seconds since the previous frame, then the fields that matter for placing boundaries."""
    state, score, clock, period, result = obs["state"], obs["score"], obs["clock"], obs["period"], obs["result"]
    gap = "" if previous_ns is None else f"{(source['received_monotonic_ns'] - previous_ns) / 1e9:.0f}"
    score_text = "" if score["a"] is None and score["b"] is None else f"{score['a']}-{score['b']}"
    clock_text = clock["display"] if clock["visible"] else ""
    period_text = ""
    if period["type"] not in ("none", "unknown"):
        period_text = period["type"]
        if period["number"] is not None:
            period_text += f"{period['number']}"
        if period["total"] is not None:
            period_text += f"/{period['total']}"
    result_text = f"RES:{result['outcome_type']}:{result['winner']}" if result["visible"] else ""
    position = obs["position"]["current"]
    position_text = "" if position is None else f"#{position}"
    counters = obs.get("secondary_counters")
    counters_text = ",".join(f"{c['kind'][:4]}.{c['side']}={c['value']}" for c in counters) if counters else ""
    timers = obs.get("secondary_timers") or []
    timers_text = ",".join(f"{t['kind'][:5]}:{t['display']}" for t in timers[:2])
    title = (obs["game"]["title"] or "-")[:10]
    participants = "/".join(name[:12] for name in obs["participants"]["primary"][:2])
    reading = strip_markers(note, READING_MARKERS).split(" || ")[0] if width else ""
    fields = [str(fid), gap, title, f"{state['phase'][:5]}/{state['screen_type'][:6]}"]
    optional = (
        participants,
        score_text and f"S{score_text}",
        clock_text and f"C{clock_text}",
        period_text and f"P:{period_text}",
        result_text,
        position_text,
        counters_text,
        timers_text and f"T:{timers_text}",
    )
    fields += [field for field in optional if field]
    return " ".join(fields) + (f" | {reading[:width]}" if reading[:width] else "")


def main():
    parser = argparse.ArgumentParser(description="One line per observation of a session, in chronological order.")
    parser.add_argument("session")
    parser.add_argument("range", nargs="?", help="FIRST-LAST, or a single frame")
    parser.add_argument("--note", type=int, default=90, help="characters of the note to show (0 = none)")
    args = parser.parse_args()
    data = observations(args.session)
    first, last = 0, float("inf")
    if args.range:
        start, _, end = args.range.partition("-")
        first, last = int(start), int(end or start)
    previous_ns = None
    for fid in sorted(data):
        if first <= fid <= last:
            print(format_line(fid, previous_ns, *data[fid], args.note))
        previous_ns = data[fid][0]["received_monotonic_ns"]


if __name__ == "__main__":
    main()
