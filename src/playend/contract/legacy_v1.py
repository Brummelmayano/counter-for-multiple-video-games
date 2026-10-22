"""The observation format used before contract 2.0, and its strict validator (no repair of a faulty output).

Contract 2.x reuses this validator for the fields it shares with the old format. Only the standard library is used.
Validating a schema never checks that the values match the image.
"""

from __future__ import annotations

import copy
import json
import math
import re

TEMPLATE = {
    "game": {"title": None, "type": "unknown", "mode": None, "mode_duration": "unknown", "confidence": None},
    "state": {"phase": "unknown", "screen_type": "unknown", "confidence": None},
    "participants": {"primary": [], "count_visible": None},
    "score": {"a": None, "b": None, "type": None, "additional_scores": None},
    "clock": {"visible": None, "display": None, "value_seconds": None, "direction": None},
    "period": {"type": "unknown", "number": None, "total": None},
    "progress": {"type": None, "current": None, "total": None},
    "position": {"current": None, "total": None},
    "result": {"visible": None, "winner": None, "outcome_type": None},
    "visible_entities": [],
    "observation_confidence": None,
}

ENUMS = {
    "game.type": {
        "football",
        "basketball",
        "combat",
        "combat_sport",
        "tennis",
        "racing",
        "mission_adventure",
        "other",
        "unknown",
    },
    "game.mode_duration": {"bounded", "continuous", "unknown"},
    "state.phase": {"pre_game", "active", "intermediate", "post_game", "menu", "loading", "paused", "unknown"},
    "state.screen_type": {
        "gameplay",
        "scoreboard",
        "result",
        "character_select",
        "team_select",
        "race_grid",
        "podium",
        "menu",
        "loading",
        "pause",
        "cutscene",
        "other",
        "unknown",
    },
    "score.type": {"goals", "points", "games", "sets", "rounds_won", "other", None},
    "clock.direction": {"countdown", "countup", "unknown", None},
    "period.type": {"half", "quarter", "round", "set", "game", "stage", "overtime", "other", "none", "unknown"},
    "progress.type": {"lap", "checkpoint", "stage", "percentage", "objective", "other", None},
    "result.outcome_type": {
        "win",
        "draw",
        "ko",
        "tko",
        "decision",
        "finish",
        "disqualification",
        "timeout",
        "other",
        None,
    },
}

CRITICAL_FIELDS = [
    "game.type",
    "game.mode_duration",
    "state.phase",
    "state.screen_type",
    "participants.primary",
    "participants.count_visible",
    "score.a",
    "score.b",
    "score.type",
    "clock.visible",
    "clock.display",
    "clock.value_seconds",
    "clock.direction",
    "period.type",
    "period.number",
    "period.total",
    "progress.type",
    "progress.current",
    "progress.total",
    "position.current",
    "position.total",
    "result.visible",
    "result.winner",
    "result.outcome_type",
]
CONFIDENCE_FIELDS = {"game.confidence", "state.confidence", "observation_confidence"}
FORBIDDEN = {
    "boundary",
    "unit_end",
    "unit_end_boundary",
    "match_finished",
    "fight_finished",
    "race_finished",
    "new_match",
    "new_fight",
    "new_race",
    "new_game",
    "game_over",
    "score_reset",
    "clock_reset",
    "period_reset",
    "progress_reset",
    "ended_unit_count",
}


def empty_observation():
    return copy.deepcopy(TEMPLATE)


def get_field(obj, path, default=None):
    for key in path.split("."):
        if not isinstance(obj, dict) or key not in obj:
            return default
        obj = obj[key]
    return obj


def is_number(value):
    # bool is a subclass of int: True must never count as a score of 1.
    return type(value) in (int, float) and math.isfinite(value)


def _no_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def _reject_constant(value):
    raise ValueError(f"not a JSON constant: {value}")


def parse_strict_json(raw_text):
    """Return (object, errors), without extracting or repairing a fragment of the text."""
    if not isinstance(raw_text, str):
        return None, ["raw_text must be a string"]
    try:
        obj = json.loads(raw_text, object_pairs_hook=_no_duplicates, parse_constant=_reject_constant)
    except (ValueError, TypeError) as exc:
        return None, [f"invalid JSON: {exc}"]
    if not isinstance(obj, dict):
        return None, ["the JSON root must be an object"]
    return obj, []


def _nullable_text(value):
    return value is None or (isinstance(value, str) and bool(value.strip()))


def _score_tree(value):
    if value is None or isinstance(value, str) or is_number(value):
        return True
    if isinstance(value, list):
        return all(_score_tree(v) for v in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and _score_tree(v) for k, v in value.items())
    return False


def _temporal_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            full = f"{path}.{key}" if path else key
            if key in FORBIDDEN:
                found.append(f"{full}: temporal field not allowed")
            found.extend(_temporal_keys(value, full))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            found.extend(_temporal_keys(value, f"{path}[{i}]"))
    return found


def validate_markers(obj):
    errors = []
    if not isinstance(obj, dict) or set(obj) != {"left", "right"}:
        return ["markers: exactly the keys left and right are required"]
    for key, value in obj.items():
        if value is not None and (type(value) is not int or value < 0):
            errors.append(f"{key}: nonnegative integer or null required")
    return errors


def validate_observation(obj):
    errors = []
    if not isinstance(obj, dict):
        return ["the root must be an object"]
    if set(obj) != set(TEMPLATE):
        errors.append(
            f"wrong root keys: missing={sorted(set(TEMPLATE) - set(obj))}, extra={sorted(set(obj) - set(TEMPLATE))}"
        )
    for key, template in TEMPLATE.items():
        if isinstance(template, dict):
            value = obj.get(key)
            if not isinstance(value, dict) or set(value) != set(template):
                errors.append(f"{key}: object with the exact subkeys required")
    errors.extend(_temporal_keys(obj))
    # Stop here: going on would read values from keys that are missing.
    if errors:
        return errors
    for path, allowed in ENUMS.items():
        value = get_field(obj, path)
        if (value is not None and not isinstance(value, str)) or value not in allowed:
            errors.append(f"{path}: value not in the enumeration")
    for path in ["game.title", "game.mode", "clock.display", "result.winner"]:
        if not _nullable_text(get_field(obj, path)):
            errors.append(f"{path}: nonempty text or null required")
    for path in ["participants.primary", "visible_entities"]:
        value = get_field(obj, path)
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            errors.append(f"{path}: list of nonempty texts required")
        elif len(value) != len(set(value)):
            errors.append(f"{path}: duplicate names")
    for path in CONFIDENCE_FIELDS:
        value = get_field(obj, path)
        if value is not None and (not is_number(value) or not 0 <= value <= 1):
            errors.append(f"{path}: number in [0, 1] or null required")
    for path in ["clock.visible", "result.visible"]:
        value = get_field(obj, path)
        if value is not None and type(value) is not bool:
            errors.append(f"{path}: boolean or null required")
    for path in ["score.a", "score.b", "clock.value_seconds", "progress.current", "progress.total"]:
        value = get_field(obj, path)
        if value is not None and (not is_number(value) or value < 0):
            errors.append(f"{path}: finite nonnegative number or null required")
    for path in ["participants.count_visible", "period.number", "period.total", "position.current", "position.total"]:
        value = get_field(obj, path)
        minimum = 0 if path == "participants.count_visible" else 1
        if value is not None and (type(value) is not int or value < minimum):
            errors.append(f"{path}: integer >= {minimum} or null required")
    additional = get_field(obj, "score.additional_scores")
    if additional is not None and (not isinstance(additional, dict) or not _score_tree(additional)):
        errors.append("score.additional_scores: object of scores or null required")
    if isinstance(additional, dict):
        for key in ["games", "sets", "tiebreak", "point_labels"]:
            if key in additional and (not isinstance(additional[key], list) or len(additional[key]) != 2):
                errors.append(f"score.additional_scores.{key}: A/B pair required")
    clock = obj["clock"]
    if clock["visible"] is not True and any(clock[k] is not None for k in ["display", "value_seconds"]):
        errors.append("clock: display or value_seconds requires visible=true")
    if clock["visible"] is False and clock["direction"] is not None:
        errors.append("clock: an absent clock requires direction=null")
    display = clock["display"]
    if isinstance(display, str) and is_number(clock["value_seconds"]):
        # Only unambiguous clock formats are compared; nothing is repaired.
        text = display.strip()
        if re.fullmatch(r"\d+:[0-5]\d(?:\.\d+)?", text):
            minutes, seconds = text.split(":")
            expected = int(minutes) * 60 + float(seconds)
            if not math.isclose(clock["value_seconds"], expected, abs_tol=0.001):
                errors.append("clock: display and value_seconds disagree")
        elif re.fullmatch(r"\d+(?:\.\d+)?", text):
            if not math.isclose(clock["value_seconds"], float(text), abs_tol=0.001):
                errors.append("clock: display and value_seconds disagree")
    result = obj["result"]
    if result["visible"] is not True and (result["winner"] is not None or result["outcome_type"] is not None):
        errors.append("result: winner or outcome_type requires visible=true")
    if result["outcome_type"] == "draw" and result["winner"] is not None:
        errors.append("result: a draw cannot name a winner")
    for name, current_name in [("period", "number"), ("progress", "current"), ("position", "current")]:
        current, total = obj[name][current_name], obj[name]["total"]
        if is_number(current) and is_number(total) and current > total:
            errors.append(f"{name}: current value above the total")
    if obj["period"]["type"] == "none" and any(obj["period"][k] is not None for k in ["number", "total"]):
        errors.append("period.type=none requires number=total=null")
    if obj["score"]["type"] == "rounds_won":
        for side in ["a", "b"]:
            value = obj["score"][side]
            if value is not None and (type(value) is not int or value < 0):
                errors.append(f"score.{side}: a round count must be an integer")
    return errors
