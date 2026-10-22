"""The state of the game the start rules keep, written out capture by capture as variables a model can learn from.

The rule detector of playend.counting.starts reads the session; before each capture is observed, the variables
describe what it knows (the open game, what broke, the screens seen since the last reading) and what the capture
shows; after it, whether the rules decided a start there. Only past and present captures are used, as on the Pi.
"""

from __future__ import annotations

import math

import numpy as np

from playend.common.games import game_family
from playend.counting.starts import CLOSING_SCREENS, OPENING, PROGRESS, QUANTITIES, TIME, Detector, Start, read

SCREENS = ("gameplay", "pause", "menu", "loading", "result", "scoreboard", "podium", "character_select",
           "team_select", "race_grid", "cutscene", "other", "unknown")  # fmt: skip
PHASES = ("active", "paused", "pre_game", "post_game", "menu", "loading", "intermediate", "unknown")
BREAKS = ("total", "lap", "round", "football_clock", "ufc_clock", "series", "names", "players")


def nan(value) -> float:
    return math.nan if value is None else float(value)


class Tracing(Detector):
    """The rule detector, which also writes one row of variables per capture."""

    def __init__(self, families: list[str], portraits=None):
        super().__init__(generic=False, confirm=True, portraits=portraits)
        self.families = families
        self.rows: list[dict] = []
        self.last_reading_t: float | None = None
        self.readings_in_game = 0
        self.last_start_t: float | None = None

    def observe_at(self, frame: int, t: float, obs: dict) -> None:
        family = game_family(obs["game"]["title"])
        state = obs["state"]
        gameplay = state["screen_type"] == "gameplay" and state["phase"] != "post_game"
        reading = read(obs, family) if gameplay else None
        row = {f"screen={name}": float(state["screen_type"] == name) for name in SCREENS}
        row |= {f"phase={name}": float(state["phase"] == name) for name in PHASES}
        row |= {f"family={name}": float(family == name) for name in self.families}
        row["closing_screen"] = float(state["screen_type"] in CLOSING_SCREENS)
        for kind in (OPENING, PROGRESS, TIME):
            row[f"kind={kind}"] = float(reading is not None and reading.kind == kind)
        open_game = self.game is not None
        row["game_open"] = float(open_game)
        row["same_game"] = float(open_game and self.game.family == family)
        row["closed"], row["final"] = float(self.closed), float(self.final)
        row["final_run"] = float(self.final_longest)
        row["candidate_waiting"] = float(self.candidate is not None)
        row["candidate_age"] = nan(frame - self.candidate.frame if self.candidate else None)
        row["seconds_since_reading"] = nan(t - self.last_reading_t if self.last_reading_t is not None else None)
        row["seconds_since_start"] = nan(t - self.last_start_t if self.last_start_t is not None else None)
        row["readings_in_game"] = float(self.readings_in_game)
        last = self.game.last if open_game else None
        breaks = self.breaks(reading) if reading is not None and reading.kind is not None else {}
        for name in BREAKS:
            row[f"broke={name}"] = float(breaks.get(name, False))
        row["comparable"] = float(bool(breaks) and self.comparable(reading))
        for name in QUANTITIES:
            now = getattr(reading, name) if reading is not None else None
            before = getattr(last, name) if last is not None else None
            row[f"value={name}"] = nan(now)
            row[f"change={name}"] = nan(now - before if now is not None and before is not None else None)
        lives = (reading.lives or {}) if reading is not None else {}
        row["lives_low"] = nan(min(lives.values()) if lives else None)
        row["lives_high"] = nan(max(lives.values()) if lives else None)
        row["marker"] = float(reading is not None and reading.marker)
        row["series_seen"] = float(reading is not None and reading.series is not None)
        row["names_seen"] = float(reading is not None and reading.names is not None)

        count = len(self.starts)
        self.observe(frame, obs)
        decided = self.starts[count:]
        row["rules_decided_start"] = float(bool(decided))
        row["rules_start_late"] = float(any(start.late for start in decided))
        if reading is not None and reading.kind is not None:
            self.last_reading_t = t
            self.readings_in_game = 0 if decided else self.readings_in_game + 1
        if decided:
            self.last_start_t = t
        self.rows.append(row)


def trace(session, families: list[str], portraits=None) -> tuple[np.ndarray, list[str], list[Start]]:
    """Variables of every capture of a session (rows in frame order) and the starts the rules decide."""
    tracing = Tracing(families, portraits)
    for index, obs in enumerate(session.observations):
        tracing.observe_at(index + 1, float(session.sequence.t[index]), obs)
    names = list(tracing.rows[0])
    table = np.array([[row[name] for name in names] for row in tracing.rows], dtype=np.float32)
    return table, names, tracing.starts
