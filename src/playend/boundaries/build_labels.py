"""Turn a session's units.json into one boundary label per observation interval.

A label describes the interval (previous observation, current observation]; its format is the one read by
playend.contract.prepare_dataset, plus audit keys (current unit, ended units, evidence). Every observation stays in
the sequence, menus and black frames included, and the end of a unit is learnt as 0 everywhere else: only the
intervals listed in uncertain_frames are masked. The second output, billing_mode, says whether the current
observation is billed per partie, by time, or not at all. When units.json gives the starts (playend.boundaries.starts),
unit_start_boundary marks the first gameplay observation of each partie whose HUD is readable. A start on the first
observation of the session has no interval: it is counted from units.json. The files are described in
data/boundaries/README.md.

usage: python -m playend.boundaries.build_labels session_<id>
       (reads session_<id>/units.json; writes the labels, units.csv and the observation manifest)
"""

from __future__ import annotations

import argparse
import csv
import json

from playend.annotation.lots import session_lots, source_rows
from playend.common.files import read_jsonl, write_jsonl
from playend.common.paths import BOUNDARIES
from playend.corrections.traces import effective

TERMINATIONS = {"completed", "incomplete_at_capture_end"}
START_STATUSES = {"rule", "author"}


def session_frames(session: str) -> list[dict]:
    sources = source_rows(session)
    rows = {}
    for lot in session_lots(session):
        for entry in read_jsonl(lot / "annotation_manifest.jsonl"):
            fid = entry["frame_id"]
            if fid in rows:
                raise SystemExit(f"frame {fid} annotated twice")
            rows[fid] = {
                "frame_id": fid,
                "received_monotonic_ns": sources[fid]["received_monotonic_ns"],
                "elapsed_s": sources[fid]["elapsed_s"],
                "observation_path": entry["annotation_path"],
                "observation_review_status": entry["review_status"],
            }
    for fid, entry in effective(session).items():  # a corrected observation replaces the lot's file
        if entry["corrected_by"]:
            rows[fid].update(
                observation_path=entry["annotation_path"],
                observation_review_status=entry["review_status"],
                corrected_by=entry["corrected_by"],
            )
    frames = [rows[k] for k in sorted(rows)]
    if [f["frame_id"] for f in frames] != list(range(1, len(frames) + 1)):
        raise SystemExit("session is not fully annotated from frame 1: label only complete sessions")
    return frames


def check_time_segments(segments: list[dict], units: list[dict], last_frame: int) -> None:
    taken = {f for u in units for f in range(u["first_frame"], u["last_frame"] + 1)}
    seen = set()
    for seg in segments:
        if not (1 <= seg["first_frame"] <= seg["last_frame"] <= last_frame):
            raise SystemExit(f"time segment {seg}: bad frame range")
        frames = set(range(seg["first_frame"], seg["last_frame"] + 1))
        if frames & taken or frames & seen:
            raise SystemExit(
                f"time segment {seg['first_frame']}-{seg['last_frame']} overlaps a unit or another segment"
            )
        if not seg.get("reason"):
            raise SystemExit("time segment: reason required (game/mode without an end of partie)")
        seen |= frames


def check_units(units: list[dict], last_frame: int) -> None:
    previous_end, previous_in_unit = 0, False
    ids = set()
    for u in units:
        if u["unit_id"] in ids:
            raise SystemExit(f"duplicate unit id {u['unit_id']}")
        ids.add(u["unit_id"])
        if u["termination"] not in TERMINATIONS:
            raise SystemExit(f"{u['unit_id']}: termination must be one of {sorted(TERMINATIONS)}")
        if not (1 <= u["first_frame"] <= u["last_frame"] <= last_frame):
            raise SystemExit(f"{u['unit_id']}: bad frame range")
        if u["first_frame"] < previous_end or (u["first_frame"] == previous_end and previous_in_unit):
            raise SystemExit(f"{u['unit_id']}: starts before the previous unit's end was established")
        end = u.get("end_established_at")
        if u["termination"] == "incomplete_at_capture_end":
            if end is not None or u["last_frame"] != last_frame:
                raise SystemExit(f"{u['unit_id']}: an unfinished unit must run to the last frame with no end")
            previous_end = last_frame + 1
        else:
            if end is None or not (u["last_frame"] <= end <= last_frame):
                raise SystemExit(f"{u['unit_id']}: end_established_at must be last_frame or follow it")
            previous_end, previous_in_unit = end, end == u["last_frame"]
        if not u.get("evidence"):
            raise SystemExit(f"{u['unit_id']}: evidence required")
        start = u.get("start_established_at")
        if start is not None:
            if not (u["first_frame"] <= start <= u["last_frame"]):
                raise SystemExit(f"{u['unit_id']}: start_established_at must lie between first_frame and last_frame")
            if u.get("start_status") not in START_STATUSES or not u.get("start_evidence"):
                raise SystemExit(
                    f"{u['unit_id']}: start_status in {sorted(START_STATUSES)} and start_evidence required"
                )
    starts = [u.get("start_established_at") is not None for u in units]
    if any(starts) and not all(starts):
        raise SystemExit("place the start of every unit, or of none (python -m playend.boundaries.starts)")


def billing_mode(fid: int, units: list[dict], segments: list[dict]) -> str:
    if any(u["first_frame"] <= fid <= u["last_frame"] for u in units):
        return "partie"
    if any(s["first_frame"] <= fid <= s["last_frame"] for s in segments):
        return "temps"
    return "hors_jeu"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Turn units.json into boundary labels, units.csv and the observation manifest."
    )
    parser.add_argument("session", help="session_<id>")
    session = parser.parse_args().session
    folder = BOUNDARIES / session
    spec = json.loads((folder / "units.json").read_text(encoding="utf-8"))
    if spec["session_id"] != session:
        raise SystemExit("units.json session_id mismatch")
    frames = session_frames(session)
    units = spec["units"]
    segments = spec.get("time_segments", [])
    check_units(units, frames[-1]["frame_id"])
    check_time_segments(segments, units, frames[-1]["frame_id"])

    uncertain = {}
    for item in spec.get("uncertain_frames", []):
        if not item.get("reason"):
            raise SystemExit("uncertain_frames: reason required")
        for fid in range(item["first_frame"], item.get("last_frame", item["first_frame"]) + 1):
            uncertain[fid] = item["reason"]

    labels = []
    for prev, cur in zip(frames, frames[1:]):
        fid = cur["frame_id"]
        current = [u for u in units if u["first_frame"] <= fid <= u["last_frame"]]
        ended = [u for u in units if u.get("end_established_at") == fid]
        started = [u for u in units if u.get("start_established_at") == fid]
        if len(current) > 1:
            raise SystemExit(f"frame {fid} belongs to several units")
        labels.append(
            {
                "session_id": session,
                "frame_id": fid,
                "previous_frame_id": prev["frame_id"],
                "unit_end_boundary": int(bool(ended)),
                "ended_unit_count": len(ended),
                "boundary_applicable": fid not in uncertain,
                "uncertain_reason": uncertain.get(fid),
                "review_status": "proposed_pending_human_review",
                "current_unit_id": current[0]["unit_id"] if current else None,
                "ended_unit_ids": [u["unit_id"] for u in ended],
                "unit_start_boundary": int(bool(started)),
                "started_unit_ids": [u["unit_id"] for u in started],
                "termination_types": [u["termination"] for u in ended],
                "label_confidence": min([u.get("label_confidence", 1.0) for u in ended] or [1.0]),
                "evidence": "; ".join(u["evidence"] for u in ended) or None,
                "delta_t_s": (cur["received_monotonic_ns"] - prev["received_monotonic_ns"]) / 1e9,
                "billing_mode": billing_mode(fid, units, segments),
            }
        )
    write_jsonl(folder / "labels_proposed.jsonl", labels)
    with (folder / "units.csv").open("w", newline="", encoding="utf-8") as stream:
        cols = [
            "unit_id",
            "game",
            "description",
            "first_frame",
            "last_frame",
            "start_established_at",
            "start_status",
            "end_established_at",
            "termination",
            "counted",
            "final_score_seen",
            "label_confidence",
            "evidence",
        ]
        writer = csv.DictWriter(stream, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(units)
    manifest = [
        {
            "session_id": session,
            "frame_id": f["frame_id"],
            "received_monotonic_ns": f["received_monotonic_ns"],
            "observation_path": f["observation_path"],
            "review_status": f["observation_review_status"],
            "corrected_by": f.get("corrected_by"),
        }
        for f in frames
    ]
    write_jsonl(folder / "observation_manifest.jsonl", manifest)
    ends = sum(label["unit_end_boundary"] for label in labels)
    starts = sum(label["unit_start_boundary"] for label in labels)
    applicable = sum(label["boundary_applicable"] for label in labels)
    modes = {mode: sum(label["billing_mode"] == mode for label in labels) for mode in ("partie", "temps", "hors_jeu")}
    corrected = sum(bool(f.get("corrected_by")) for f in frames)
    print(
        f"{session}: {len(frames)} observations ({corrected} from correction traces), {len(labels)} intervals, "
        f"{len(units)} units, {len(segments)} time segments, {ends} boundaries, {starts} starts, "
        f"{applicable} applicable intervals, "
        f"billing_mode {modes}"
    )


if __name__ == "__main__":
    main()
