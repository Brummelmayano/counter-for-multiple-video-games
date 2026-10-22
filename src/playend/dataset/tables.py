"""Rows of the PlayEnd tables, read from the human-verified boundaries and the effective observations.

Each row of observations.csv is one screenshot; its labels describe the interval (previous screenshot, this
screenshot], as in labels_human_verified.jsonl, so the first screenshot of a session has no end-of-game target.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from playend.boundaries.build_labels import billing_mode
from playend.common.files import read_jsonl, sha256
from playend.common.games import game_family
from playend.common.paths import BOUNDARIES, CAPTURES, REPO, resolve
from playend.contract import upgrade_v20
from playend.contract.temporal import COUNTER_SLOTS
from playend.corrections.traces import effective, lot_entries
from playend.dataset.pseudonyms import Pseudonyms

FOLDS = 5
FOLDS_FILE = REPO / "docs" / "dataset" / "folds.json"
# Billing modes are recorded in French in the labels; the published values are English.
BILLING_MODES = {"partie": "per_game", "temps": "time_based", "hors_jeu": "not_billed"}


@dataclass
class Session:
    session_id: str
    frames: list[dict]
    labels: dict[int, dict]
    units: list[dict]
    segments: list[dict]
    metadata: dict


def exported_sessions() -> list[str]:
    """Sessions whose boundaries were verified by hand: the only ones published."""
    return sorted(path.parent.name for path in BOUNDARIES.glob("session_*/labels_human_verified.jsonl"))


def annotator_model(entry: dict) -> str:
    """Model name alone ("GPT-6 Luna"): the id and the tool recorded after it stay in the repository's metadata."""
    recorded = json.loads(resolve(entry["metadata_path"]).read_text(encoding="utf-8"))["annotator_model"]
    return recorded.split(" (")[0]


def load_session(session: str) -> Session:
    folder = BOUNDARIES / session
    labels = read_jsonl(folder / "labels_human_verified.jsonl")
    if any(label["review_status"] != "human_verified" for label in labels):
        raise SystemExit(f"{session}: labels not all human_verified")
    if labels[0]["proposed_labels_sha256"] != sha256(folder / "labels_proposed.jsonl"):
        raise SystemExit(f"{session}: units.json changed after the labels were verified")
    first_readings, current = lot_entries(session), effective(session)
    frames = []
    for row in read_jsonl(folder / "observation_manifest.jsonl"):
        fid, entry = row["frame_id"], current[row["frame_id"]]
        if entry["annotation_path"] != row["observation_path"]:
            raise SystemExit(f"{session} frame {fid}: observation manifest is stale, rerun build_labels")
        path = resolve(entry["annotation_path"])
        if sha256(path) != entry["annotation_sha256"]:
            raise SystemExit(f"{session} frame {fid}: observation changed since it was recorded")
        frames.append(
            {
                "frame_id": fid,
                "received_monotonic_ns": row["received_monotonic_ns"],
                "observation": json.loads(path.read_text(encoding="utf-8")),
                "review_status": entry["review_status"],
                "annotator": annotator_model(first_readings[fid]),
                "corrected_by": entry["corrected_by"],
                "corrector": annotator_model(entry) if entry["corrected_by"] else None,
            }
        )
    spec = json.loads((folder / "units.json").read_text(encoding="utf-8"))
    return Session(
        session_id=session,
        frames=frames,
        labels={label["frame_id"]: label for label in labels},
        units=spec["units"],
        segments=spec.get("time_segments", []),
        metadata=json.loads((CAPTURES / session / "metadata.json").read_text(encoding="utf-8")),
    )


def seconds(nanoseconds: int) -> str:
    """Exact decimal seconds: no float rounding, so differences between rows stay exact."""
    return f"{nanoseconds // 1_000_000_000}.{nanoseconds % 1_000_000_000:09d}"


def counter_column(kind: str, side: str) -> str:
    return kind if side == "field" else f"{kind}_{side}"


def list_status(items: list | None) -> str:
    if items is None:
        return "unknown"
    return "present" if items else "none"


def observation_columns(obs: dict) -> dict:
    view = upgrade_v20(obs) if obs["schema_version"] == "2.0" else obs
    game, state, score, clock = view["game"], view["state"], view["score"], view["clock"]
    period, progress, position, result = view["period"], view["progress"], view["position"], view["result"]
    timers, counters = view["secondary_timers"], view["secondary_counters"]
    names = view["participants"]["primary"]
    readable = [timer["value_seconds"] for timer in timers or [] if timer["value_seconds"] is not None]
    row = {
        "game_title": game["title"],
        "game_family": game_family(game["title"]) if game["title"] else None,
        "game_type": game["type"],
        "game_mode": game["mode"],
        "mode_duration": game["mode_duration"],
        "phase": state["phase"],
        "screen_type": state["screen_type"],
        "score_a": score["a"],
        "score_b": score["b"],
        "score_type": score["type"],
        "clock_visible": clock["visible"],
        "clock_display": clock["display"],
        "clock_seconds": clock["value_seconds"],
        "clock_direction": clock["direction"],
        "period_type": period["type"],
        "period_number": period["number"],
        "period_total": period["total"],
        "progress_type": progress["type"],
        "progress_current": progress["current"],
        "progress_total": progress["total"],
        "position_current": position["current"],
        "position_total": position["total"],
        "result_visible": result["visible"],
        "result_outcome_type": result["outcome_type"],
        "result_winner": result["winner"],
    }
    for kind, side in COUNTER_SLOTS:
        values = [item["value"] for item in counters or [] if item["kind"] == kind and item["side"] == side]
        row[counter_column(kind, side)] = values[0] if values else None
    row |= {
        "counters_status": list_status(counters),
        "secondary_timers_status": list_status(timers),
        "secondary_timer_kinds": "|".join(dict.fromkeys(timer["kind"] for timer in timers or [])) or None,
        "secondary_timer_min_seconds": min(readable, default=None),
        "participants_count_visible": view["participants"]["count_visible"],
        "participants_listed": len(names),
        "participant_a": names[0] if names else None,
        "participant_b": names[1] if len(names) > 1 else None,
    }
    return row


def label_columns(session: Session, fid: int, pseudonyms: Pseudonyms) -> dict:
    label = session.labels.get(fid)
    if label is None:  # first screenshot: no interval before it, so no end-of-game target
        current = [unit["unit_id"] for unit in session.units if unit["first_frame"] <= fid <= unit["last_frame"]]
        # a game already running on the first screenshot starts there (decision of the author, 2026-10-13)
        started = [unit["unit_id"] for unit in session.units if unit.get("start_established_at") == fid]
        return {
            "unit_end_boundary": None,
            "boundary_applicable": False,
            "uncertain_reason": None,
            "current_unit_id": current[0] if current else None,
            "ended_unit_id": None,
            "unit_start_boundary": int(bool(started)),
            "started_unit_id": started[0] if started else None,
            "billing_mode": BILLING_MODES[billing_mode(fid, session.units, session.segments)],
            "label_review_status": "human_verified",
            "label_confidence": None,
        }
    if label["ended_unit_count"] > 1:
        raise SystemExit(f"{session.session_id} frame {fid}: several games end in one interval")
    reason = label["uncertain_reason"]
    return {
        "unit_end_boundary": label["unit_end_boundary"],
        "boundary_applicable": label["boundary_applicable"],
        "uncertain_reason": pseudonyms.text(reason) if reason else None,
        "current_unit_id": label["current_unit_id"],
        "ended_unit_id": label["ended_unit_ids"][0] if label["ended_unit_ids"] else None,
        "unit_start_boundary": label["unit_start_boundary"],
        "started_unit_id": label["started_unit_ids"][0] if label["started_unit_ids"] else None,
        "billing_mode": BILLING_MODES[label["billing_mode"]],
        "label_review_status": label["review_status"],
        "label_confidence": label["label_confidence"],
    }


def observation_rows(session: Session, pseudonyms: Pseudonyms) -> list[dict]:
    start = session.frames[0]["received_monotonic_ns"]
    rows, previous = [], None
    for frame in session.frames:
        stamp, fid = frame["received_monotonic_ns"], frame["frame_id"]
        obs = pseudonyms.value(frame["observation"])
        rows.append(
            {
                "session_id": session.session_id,
                "frame_id": fid,
                "t_s": seconds(stamp - start),
                "delta_t_s": seconds(stamp - previous) if previous is not None else None,
                **observation_columns(obs),
                "observation_json": json.dumps(obs, ensure_ascii=False, separators=(",", ":")),
                "observation_schema_version": obs["schema_version"],
                "annotator": frame["annotator"],
                "corrected_by": frame["corrected_by"],
                "corrector": frame["corrector"],
                "observation_review_status": frame["review_status"],
                **label_columns(session, fid, pseudonyms),
            }
        )
        previous = stamp
    return rows


def unit_rows(session: Session, pseudonyms: Pseudonyms) -> list[dict]:
    return [
        {
            "session_id": session.session_id,
            "unit_id": unit["unit_id"],
            "game": unit["game"],
            "game_family": game_family(unit["game"]),
            "description": pseudonyms.text(unit["description"]),
            "first_frame": unit["first_frame"],
            "last_frame": unit["last_frame"],
            "start_established_at": unit["start_established_at"],
            "start_status": unit["start_status"],
            "start_evidence": pseudonyms.text(unit["start_evidence"]),
            "end_established_at": unit["end_established_at"],
            "termination": unit["termination"],
            "counted": unit["counted"],
            "final_score_seen": pseudonyms.text(unit["final_score_seen"]),
            "label_confidence": unit["label_confidence"],
            "evidence": pseudonyms.text(unit["evidence"]),
        }
        for unit in session.units
    ]


def time_segment_rows(session: Session, pseudonyms: Pseudonyms) -> list[dict]:
    return [
        {
            "session_id": session.session_id,
            "first_frame": segment["first_frame"],
            "last_frame": segment["last_frame"],
            "game": segment["game"],
            "game_family": game_family(segment["game"]),
            "reason": pseudonyms.text(segment["reason"]),
        }
        for segment in sorted(session.segments, key=lambda segment: segment["first_frame"])
    ]


def session_row(session: Session, observations: list[dict]) -> dict:
    config = session.metadata["config"]
    frames = session.frames
    models = {frame["annotator"] for frame in frames} | {frame["corrector"] for frame in frames if frame["corrector"]}
    families = (row["game_family"] for row in observations if row["game_family"])
    return {
        "session_id": session.session_id,
        "frame_count": len(frames),
        "duration_s": seconds(frames[-1]["received_monotonic_ns"] - frames[0]["received_monotonic_ns"]),
        "capture_interval_min_s": config["interval_min_s"],
        "capture_interval_max_s": config["interval_max_s"],
        "image_width": config["width"],
        "image_height": config["height"],
        "jpeg_quality": config["jpeg_quality"],
        "games": "|".join(dict.fromkeys(families)),
        "unit_count": len(session.units),
        "boundary_count": sum(label["unit_end_boundary"] for label in session.labels.values()),
        "start_count": sum(unit.get("start_established_at") is not None for unit in session.units),
        "time_segment_count": len(session.segments),
        "annotators": "|".join(sorted(models)),
        "validation_status": "human_verified",
        "capture_program_sha256": session.metadata["program_sha256"],
    }


def split_rows(sessions: list[dict]) -> list[dict]:
    """Whole sessions in FOLDS folds, balanced on game ends and on screenshots.

    The folds of version 1.0 are kept (docs/dataset/folds.json) so that results stay comparable across versions;
    the balancing below only runs for sessions that file does not list.

    A session weighs its share of all the ends plus its share of all the screenshots. The heaviest session goes
    first into the lightest fold, as GroupKFold does with sample counts alone; the ends are added because they are
    the rare class that the evaluation depends on.
    """
    frozen = json.loads(FOLDS_FILE.read_text(encoding="utf-8"))
    if {row["session_id"] for row in sessions} <= frozen.keys():
        return [{"session_id": row["session_id"], "fold": frozen[row["session_id"]]} for row in sessions]
    total_ends = sum(row["boundary_count"] for row in sessions)
    total_frames = sum(row["frame_count"] for row in sessions)
    weight = {
        row["session_id"]: row["boundary_count"] / total_ends + row["frame_count"] / total_frames for row in sessions
    }
    load = [0.0] * FOLDS
    rows = []
    for row in sorted(sessions, key=lambda row: (-weight[row["session_id"]], row["session_id"])):
        fold = min(range(FOLDS), key=lambda f: (load[f], f))
        load[fold] += weight[row["session_id"]]
        rows.append({"session_id": row["session_id"], "fold": fold + 1})
    return sorted(rows, key=lambda row: row["session_id"])
