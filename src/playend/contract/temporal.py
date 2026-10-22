"""Causal GRU features 4.0. No inferred labels, no fitting on validation data.

Secondary timers are aggregated per role; their sequence is left to the GRU.
No fabricated identity/delta across multiple contracts or cooldowns.

4.0 (contract 2.1) adds: secondary counters per (kind, side) slot, game.mode categories,
clock.infinite ("∞"), period.is_last (number == total) and observation_missing (VLM failure on
the device: the row is kept, all observation fields unknown). 2.0 observations are read through
upgrade_v20 (counters unknown).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math

from .contract import SCHEMA_VERSION, TIMER_KINDS, empty_observation, upgrade_v20, validate_observation
from .legacy_v1 import ENUMS, get_field, is_number

FEATURE_VERSION = "4.0"
GAME_MODES = ("match", "versus", "bout", "race", "grand_prix", "street_race", "mission", "free_roam", "other")
# Fixed, order-stable counter slots; "other"/"unknown" are only counted.
COUNTER_SLOTS = (
    ("players_remaining", "field"),
    ("teams_remaining", "field"),
    ("lives", "a"),
    ("lives", "b"),
    ("target", "field"),
    ("target", "a"),
    ("target", "b"),
    ("series", "a"),
    ("series", "b"),
    ("series", "field"),
)
INFINITE_DISPLAYS = ("∞", "INF", "INFINITE")
NUMERIC = (
    "participants.count_visible",
    "score.a",
    "score.b",
    "clock.value_seconds",
    "period.number",
    "period.total",
    "progress.current",
    "progress.total",
    "position.current",
    "position.total",
)
CATEGORICAL = tuple(k for k in ENUMS if k != "clock.direction")


def _scaled(number):
    # Fixed transform: no fitted statistics, no leakage from held-out sessions.
    return math.copysign(math.log1p(abs(number)), number)


def _number(out, name, value):
    known = is_number(value)
    out[name] = _scaled(value) if known else 0.0
    out[name + ".known"] = float(known)


def _boolean(out, name, value):
    out[name] = float(value is True)
    out[name + ".known"] = float(type(value) is bool)


def _same_context(a, b):
    return (
        a is not None
        and a["game"]["title"] is not None
        and a["game"]["title"] == b["game"]["title"]
        and a["game"]["type"] != "unknown"
        and a["game"]["type"] == b["game"]["type"]
        and a["game"]["mode"] == b["game"]["mode"]
    )


class FeatureStream:
    """One ordered capture session at a time. Reusing a closed session is an error.

    The caller must also reset the actual GRU hidden state when sequence_start=1.
    No features refer to future rows, training targets, filenames or result labels.
    """

    def __init__(self):
        self.session = None
        self.closed = set()
        self.previous = None
        self.previous_ns = None
        self.previous_frame = None
        self.last_main_ns = None

    def step(self, record):
        missing = bool(record.get("observation_missing"))
        obj = empty_observation() if missing else record["observation"]
        errors = validate_observation(obj)
        if errors:
            raise ValueError(errors)
        if obj["schema_version"] == "2.0":
            obj = upgrade_v20(obj)
        session, frame, stamp = (record[k] for k in ("session_id", "frame_id", "received_monotonic_ns"))
        if not isinstance(session, str) or not session.strip():
            raise ValueError("nonempty session_id required")
        if type(frame) is not int or frame < 1 or type(stamp) is not int or stamp < 0:
            raise ValueError("positive integer frame_id and nonnegative integer monotonic timestamp required")
        start = session != self.session
        if start:
            if session in self.closed:
                raise ValueError("interleaved/reopened session; group rows by session")
            if self.session is not None:
                self.closed.add(self.session)
            self.session = session
            self.previous = self.previous_ns = self.previous_frame = self.last_main_ns = None
        if self.previous_ns is not None and (stamp <= self.previous_ns or frame <= self.previous_frame):
            raise ValueError("frames/timestamps must increase strictly within a session")
        delta = None if start else (stamp - self.previous_ns) / 1e9
        prev = self.previous
        out = {"sequence_start": float(start), "observation_missing": float(missing)}
        _number(out, "delta_t_s", delta)
        for path in NUMERIC:
            _number(out, path, get_field(obj, path))
        for path in CATEGORICAL:
            value = get_field(obj, path)
            for category in sorted(ENUMS[path], key=str):
                out[f"{path}={category}"] = float(value == category)
        for path in ("clock.visible", "result.visible"):
            _boolean(out, path, get_field(obj, path))
        mode = obj["game"]["mode"]
        normalized_mode = (
            "MISSING"
            if mode is None
            else mode.strip().lower()
            if isinstance(mode, str) and mode.strip().lower() in GAME_MODES
            else "OTHER_TEXT"
        )
        for category in GAME_MODES + ("OTHER_TEXT", "MISSING"):
            out[f"game.mode={category}"] = float(normalized_mode == category)
        display = obj["clock"]["display"]
        readable_clock = obj["clock"]["visible"] is True and isinstance(display, str)
        _boolean(out, "clock.infinite", display.strip().upper() in INFINITE_DISPLAYS if readable_clock else None)
        number, total = obj["period"]["number"], obj["period"]["total"]
        _boolean(out, "period.is_last", number == total if is_number(number) and is_number(total) else None)
        for field in ("game.title", "game.mode", "participants.primary", "result.winner"):
            a, b = get_field(prev, field), get_field(obj, field)
            known = a not in (None, [], "unknown") and b not in (None, [], "unknown")
            _boolean(out, field + ".changed", (a != b) if known else None)
        # Tennis additional score pairs: numerical values only; point labels
        # have a fixed vocabulary, never a fitted identifier embedding.
        for group in ("games", "sets", "tiebreak"):
            pair = get_field(obj, "score.additional_scores." + group)
            for i in range(2):
                _number(out, f"score.{group}.{i}", pair[i] if isinstance(pair, list) and len(pair) == 2 else None)
        pair = get_field(obj, "score.additional_scores.point_labels")
        for i in range(2):
            value = str(pair[i]).upper() if isinstance(pair, list) and len(pair) == 2 and pair[i] is not None else None
            for category in ("0", "15", "30", "40", "AD", "A", "ADV", "OTHER", "MISSING"):
                normalized = (
                    value
                    if value in ("0", "15", "30", "40", "AD", "A", "ADV")
                    else ("MISSING" if value is None else "OTHER")
                )
                out[f"score.point_labels.{i}={category}"] = float(normalized == category)
        context = _same_context(prev, obj)
        # Main-clock delta is merely a candidate difference, not a reset label.
        # Require explicit same sporting period (or explicit period.type=none).
        period = obj["period"]
        same_period = (
            context
            and prev["period"] == period
            and period["type"] != "unknown"
            and (period["type"] == "none" or period["number"] is not None)
        )
        for path in ("score.a", "score.b", "clock.value_seconds", "progress.current", "position.current"):
            a, b = get_field(prev, path), get_field(obj, path)
            comparable = context
            if path.startswith("clock"):
                comparable = same_period
            elif path.startswith("score"):
                comparable = (
                    context and obj["score"]["type"] is not None and prev["score"]["type"] == obj["score"]["type"]
                )
            elif path.startswith("progress"):
                comparable = (
                    context
                    and obj["progress"]["type"] is not None
                    and prev["progress"]["type"] == obj["progress"]["type"]
                )
            _number(out, path + ".delta_candidate", b - a if comparable and is_number(a) and is_number(b) else None)
        if prev and not context and not missing:
            self.last_main_ns = None
        _number(
            out,
            "clock.seconds_since_previous_readable",
            (stamp - self.last_main_ns) / 1e9 if self.last_main_ns is not None else None,
        )
        if obj["clock"]["value_seconds"] is not None:
            self.last_main_ns = stamp
        timers = obj["secondary_timers"]
        out["secondary.inventory_known"] = float(timers is not None)
        for kind in TIMER_KINDS:
            selected = [t for t in (timers or []) if t["kind"] == kind]
            values = [t["value_seconds"] for t in selected if t["value_seconds"] is not None]
            prefix = "secondary." + kind
            _number(out, prefix + ".count", len(selected) if timers is not None else None)
            _number(out, prefix + ".readable_count", len(values) if timers is not None else None)
            _number(out, prefix + ".minimum_seconds", min(values) if values else None)
            _number(out, prefix + ".maximum_seconds", max(values) if values else None)
        counters = obj["secondary_counters"]
        prev_counters = prev["secondary_counters"] if prev else None
        out["counter.inventory_known"] = float(counters is not None)

        def slot_value(items, kind, side):
            for item in items or []:
                if item["kind"] == kind and item["side"] == side:
                    return item["value"]
            return None

        for kind, side in COUNTER_SLOTS:
            name = f"counter.{kind}.{side}"
            value = slot_value(counters, kind, side)
            _number(out, name, value)
            before = slot_value(prev_counters, kind, side)
            _number(
                out,
                name + ".delta_candidate",
                value - before if context and is_number(value) and is_number(before) else None,
            )
        for kind in ("other", "unknown"):
            _number(
                out,
                f"counter.{kind}.count",
                sum(item["kind"] == kind for item in counters) if counters is not None else None,
            )
        if not missing:
            # A missing observation carries no evidence: keep the last real observation as context.
            self.previous = copy.deepcopy(obj)
        self.previous_ns, self.previous_frame = stamp, frame
        return out


def feature_spec():
    names = list(
        FeatureStream().step(
            {"session_id": "spec", "frame_id": 1, "received_monotonic_ns": 0, "observation": empty_observation()}
        )
    )
    spec = {
        "feature_version": FEATURE_VERSION,
        "observation_version": SCHEMA_VERSION,
        "accepted_observation_versions": ["2.0 (read with counters unknown)", SCHEMA_VERSION],
        "feature_names": names,
        "input_dim": len(names),
        "numeric_transform": "sign(x)*log1p(abs(x)); missing=0 plus known mask",
        "time_source": "received_monotonic_ns, subtraction before conversion to seconds",
        "secondary_aggregation": "count/readable_count/min/max per role; no identity or boundary inference",
        "counter_slots": [f"{k}.{s}" for k, s in COUNTER_SLOTS] + ["other.count", "unknown.count"],
        "counter_encoding": "value + known + delta_candidate (same game context only); other/unknown counted",
        "extra_flags": [
            "observation_missing",
            "game.mode=<canonical|OTHER_TEXT|MISSING>",
            "clock.infinite",
            "period.is_last",
        ],
        "hidden_state": "reset at every sequence_start; never cross capture sessions",
    }
    spec["feature_sha256"] = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    return spec


def assert_checkpoint_compatible(checkpoint):
    expected = feature_spec()
    for key in ("feature_version", "feature_sha256", "feature_names", "input_dim"):
        if checkpoint.get(key) != expected[key]:
            raise ValueError(f"incompatible GRU checkpoint ({key}); retrain for features {FEATURE_VERSION}")
