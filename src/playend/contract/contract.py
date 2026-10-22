"""Observation 2.1: main clock, secondary HUD timers and universal secondary counters.

2.0 → 2.1 adds one root key, secondary_counters (players/teams remaining, lives, displayed target,
series). 2.0 observations remain valid; upgrade_v20() converts them in memory with
secondary_counters=null (unknown), never by guessing.

legacy_v1.py keeps the validator of the format used before 2.0, unchanged. Validating a schema cannot check that the
values match the image, nor tell which timer is which.
"""

from __future__ import annotations

import copy
import math
import re

from . import legacy_v1 as legacy
from .legacy_v1 import parse_strict_json as parse_strict_json

SCHEMA_VERSION = "2.1"
SUPPORTED_VERSIONS = ("2.0", "2.1")
TIMER_KINDS = ("storm_phase", "contract", "respawn", "ability_cooldown", "pre_match", "other", "unknown")
TIMER_KEYS = {"kind", "label", "display", "value_seconds", "direction"}
COUNTER_KINDS = ("players_remaining", "teams_remaining", "lives", "target", "series", "other", "unknown")
COUNTER_SIDES = ("a", "b", "field")
COUNTER_KEYS = {"kind", "side", "value", "total", "label"}
# Allowed sides per kind; "other"/"unknown" accept any side and may repeat.
COUNTER_SIDE_RULES = {
    "players_remaining": ("field",),
    "teams_remaining": ("field",),
    "lives": ("a", "b"),
    "target": COUNTER_SIDES,
    "series": COUNTER_SIDES,
}
TEMPLATE_V20 = {"schema_version": "2.0", **legacy.empty_observation(), "secondary_timers": None}
TEMPLATE = {
    "schema_version": SCHEMA_VERSION,
    **legacy.empty_observation(),
    "secondary_timers": None,
    "secondary_counters": None,
}


def empty_observation():
    return copy.deepcopy(TEMPLATE)


def upgrade_v20(obj):
    """In-memory 2.0 → 2.1 view: counters unknown (null). The source JSON is left untouched."""
    if obj.get("schema_version") != "2.0":
        raise ValueError("upgrade_v20 expects a 2.0 observation")
    upgraded = copy.deepcopy(obj)
    upgraded["schema_version"] = SCHEMA_VERSION
    upgraded["secondary_counters"] = None
    return upgraded


def _counter_errors(counters):
    if counters is None:
        return []
    if not isinstance(counters, list):
        return ["secondary_counters: array or null required"]
    errors = legacy._temporal_keys(counters, "secondary_counters")
    seen = set()
    for index, item in enumerate(counters):
        path = f"secondary_counters[{index}]"
        if not isinstance(item, dict) or set(item) != COUNTER_KEYS:
            errors.append(f"{path}: exact counter keys required (kind, side, value, total, label)")
            continue
        kind, side = item["kind"], item["side"]
        if kind not in COUNTER_KINDS:
            errors.append(f"{path}.kind: invalid role")
            continue
        if side not in COUNTER_SIDE_RULES.get(kind, COUNTER_SIDES):
            errors.append(f"{path}.side: {side!r} not allowed for {kind}")
        if kind not in ("other", "unknown"):
            if (kind, side) in seen:
                errors.append(f"{path}: duplicate ({kind}, {side})")
            seen.add((kind, side))
        for key in ("value", "total"):
            value = item[key]
            if value is not None and (not legacy.is_number(value) or value < 0):
                errors.append(f"{path}.{key}: finite nonnegative number or null required")
        if legacy.is_number(item["value"]) and legacy.is_number(item["total"]) and item["value"] > item["total"]:
            errors.append(f"{path}: value exceeds displayed total")
        if not legacy._nullable_text(item["label"]):
            errors.append(f"{path}.label: visible nonempty label or null required")
    return errors


def _time_errors(timer, path, main=False):
    errors = []
    visible = timer.get("visible") if main else True
    if main and visible is not True:
        if any(timer.get(k) is not None for k in ("display", "value_seconds", "direction")):
            errors.append(f"{path}: absent/uncertain main clock requires null values")
        return errors
    if timer.get("direction") != "unknown":
        errors.append(f"{path}.direction: use unknown for a single image")
    display, seconds = timer.get("display"), timer.get("value_seconds")
    if display is not None and (not isinstance(display, str) or not display.strip()):
        errors.append(f"{path}.display: nonempty text or null required")
    if seconds is None:
        return errors
    if not legacy.is_number(seconds) or seconds < 0:
        return errors + [f"{path}.value_seconds: finite nonnegative number or null required"]
    if not isinstance(display, str):
        return errors + [f"{path}: seconds require a readable display"]
    text = display.strip()
    expected = None
    if re.fullmatch(r"\d+:[0-5]\d:[0-5]\d(?:\.\d+)?", text):
        hours, minutes, secs = text.split(":")
        expected = int(hours) * 3600 + int(minutes) * 60 + float(secs)
    elif re.fullmatch(r"\d+:[0-5]\d(?:\.\d+)?", text):
        minutes, secs = text.split(":")
        expected = int(minutes) * 60 + float(secs)
    elif re.fullmatch(r"\d+(?:\.\d+)?", text):
        expected = float(text)
    if expected is None:
        errors.append(f"{path}: unsupported/approximate time format; keep seconds null")
    elif not math.isclose(seconds, expected, rel_tol=0, abs_tol=0.001):
        errors.append(f"{path}: display and seconds disagree")
    return errors


def validate_observation(obj):
    """Validate a 2.1 observation (current) or a 2.0 one (existing annotations)."""
    version = obj.get("schema_version") if isinstance(obj, dict) else None
    if version not in SUPPORTED_VERSIONS:
        return ["unsupported schema_version (2.0 or 2.1 expected)"]
    template = TEMPLATE if version == "2.1" else TEMPLATE_V20
    if set(obj) != set(template):
        return [
            f"observation {version} requires exact root keys including schema_version and secondary_timers"
            + (" and secondary_counters" if version == "2.1" else "")
        ]
    errors = []
    if version == "2.1":
        errors.extend(_counter_errors(obj["secondary_counters"]))
    base = {key: obj[key] for key in legacy.TEMPLATE}
    errors.extend(legacy.validate_observation(base))
    if errors:
        return errors
    additional = obj["score"]["additional_scores"]
    if additional is not None:
        if set(additional) != {"games", "sets", "tiebreak", "point_labels"}:
            errors.append("score.additional_scores: v2 requires the four explicit pairs or null")
        else:
            for pair in additional.values():
                if any(v is not None and not isinstance(v, str) and not legacy.is_number(v) for v in pair):
                    errors.append("score.additional_scores: pair values must be scalar numbers/text/null")
    errors.extend(_time_errors(obj["clock"], "clock", main=True))
    timers = obj["secondary_timers"]
    if timers is None:
        return errors
    if not isinstance(timers, list):
        return errors + ["secondary_timers: array or null required"]
    errors.extend(legacy._temporal_keys(timers, "secondary_timers"))
    for index, timer in enumerate(timers):
        path = f"secondary_timers[{index}]"
        if not isinstance(timer, dict) or set(timer) != TIMER_KEYS:
            errors.append(f"{path}: exact timer keys required")
            continue
        if timer["kind"] not in TIMER_KINDS:
            errors.append(f"{path}.kind: invalid role")
        if not legacy._nullable_text(timer["label"]):
            errors.append(f"{path}.label: visible nonempty label or null required")
        errors.extend(_time_errors(timer, path))
    return errors


def validate_any(obj):
    if isinstance(obj, dict) and "schema_version" not in obj:
        return legacy.validate_observation(obj)
    return validate_observation(obj)


def upgrade_legacy(obj):
    """Convert an observation of the format before 2.0, in memory.

    This is not a visual review: the clock read under the old format may be the wrong one, so it is masked until the
    image is read again. The caller keeps the original JSON and its provenance.
    """
    errors = legacy.validate_observation(obj)
    if errors:
        raise ValueError(errors)
    upgraded = {
        "schema_version": SCHEMA_VERSION,
        **copy.deepcopy(obj),
        "secondary_timers": None,
        "secondary_counters": None,
    }
    upgraded["clock"] = copy.deepcopy(legacy.TEMPLATE["clock"])
    additional = upgraded["score"]["additional_scores"]
    if isinstance(additional, dict):
        keys = ("games", "sets", "tiebreak", "point_labels")
        if set(additional) - set(keys):
            raise ValueError("legacy additional_scores has unsupported keys; explicit review required")
        upgraded["score"]["additional_scores"] = {key: additional.get(key, [None, None]) for key in keys}
    errors = validate_observation(upgraded)
    if errors:
        raise ValueError(f"legacy observation needs explicit review before v2 conversion: {errors}")
    return upgraded


def _object(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def output_schema():
    """JSON schema of an observation, for structured generation; score pairs are checked again afterwards."""

    def leaf(path):
        if path in legacy.ENUMS:
            return {"enum": sorted(legacy.ENUMS[path], key=str)}
        if path in legacy.CONFIDENCE_FIELDS:
            return {"type": ["number", "null"], "minimum": 0, "maximum": 1}
        if path in ("clock.visible", "result.visible"):
            return {"type": ["boolean", "null"]}
        if path in ("participants.primary", "visible_entities"):
            return {"type": "array", "items": {"type": "string"}}
        if path in (
            "participants.count_visible",
            "period.number",
            "period.total",
            "position.current",
            "position.total",
        ):
            return {"type": ["integer", "null"], "minimum": 0 if path == "participants.count_visible" else 1}
        if path in ("score.a", "score.b", "clock.value_seconds", "progress.current", "progress.total"):
            return {"type": ["number", "null"], "minimum": 0}
        if path == "score.additional_scores":
            pair = {"type": "array", "items": {"type": ["number", "string", "null"]}, "minItems": 2, "maxItems": 2}
            return {
                "anyOf": [
                    _object({k: copy.deepcopy(pair) for k in ("games", "sets", "tiebreak", "point_labels")}),
                    {"type": "null"},
                ]
            }
        return {"type": ["string", "null"]}

    props = {"schema_version": {"type": "string", "enum": [SCHEMA_VERSION]}}
    for key, value in legacy.TEMPLATE.items():
        props[key] = (
            _object({child: leaf(f"{key}.{child}") for child in value}) if isinstance(value, dict) else leaf(key)
        )
    props["clock"]["properties"]["direction"] = {"enum": ["unknown", None]}
    props["secondary_timers"] = {
        "anyOf": [
            {
                "type": "array",
                "items": _object(
                    {
                        "kind": {"type": "string", "enum": list(TIMER_KINDS)},
                        "label": {"type": ["string", "null"]},
                        "display": {"type": ["string", "null"]},
                        "value_seconds": {"type": ["number", "null"], "minimum": 0},
                        "direction": {"type": "string", "enum": ["unknown"]},
                    }
                ),
            },
            {"type": "null"},
        ]
    }
    props["secondary_counters"] = {
        "anyOf": [
            {
                "type": "array",
                "items": _object(
                    {
                        "kind": {"type": "string", "enum": list(COUNTER_KINDS)},
                        "side": {"type": "string", "enum": list(COUNTER_SIDES)},
                        "value": {"type": ["number", "null"], "minimum": 0},
                        "total": {"type": ["number", "null"], "minimum": 0},
                        "label": {"type": ["string", "null"]},
                    }
                ),
            },
            {"type": "null"},
        ]
    }
    return _object(props)
