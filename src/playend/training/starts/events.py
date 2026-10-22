"""Starts as events: a readable capture whose probability passes the threshold and is the highest of its neighbours
(the readable capture before and the one after, a non-maximum suppression over one capture as in Hong et al., 2022)
is a start, decided at the next readable capture. Lowering the threshold only adds starts. A reference game is found
by the first unused start inside it, or up to two captures before its first capture, as for the rules
(playend.counting.starts.match); the other starts are games counted in excess.

The threshold is the lowest one that keeps the starts in excess under a budget per 100 games on the validation
sessions, the Neyman-Pearson way of bounding the costly error and minimising the other (Tong, Feng and Li, 2018)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from playend.counting.starts import Start, match

BUDGETS = (1.0, 2.0, 5.0)  # games counted in excess per 100 games
MAIN_BUDGET = 2.0
LEVELS = 200


@dataclass
class Tally:
    games: int = 0
    found: int = 0
    extra: int = 0
    sessions: int = 0
    exact: int = 0
    count_error: int = 0  # sum over sessions of |starts - games|
    lags: list = field(default_factory=list)  # captures between the reference start and the decision

    def __add__(self, other: Tally) -> Tally:
        return Tally(self.games + other.games, self.found + other.found, self.extra + other.extra,
                     self.sessions + other.sessions, self.exact + other.exact,
                     self.count_error + other.count_error, self.lags + other.lags)  # fmt: skip

    @property
    def recall(self) -> float:
        return self.found / self.games if self.games else 0.0

    @property
    def extra_per_100(self) -> float:
        return 100 * self.extra / self.games if self.games else 0.0

    @property
    def precision(self) -> float:
        counted = self.found + self.extra
        return self.found / counted if counted else 1.0

    def as_dict(self) -> dict:
        return {"games": self.games, "found": self.found, "extra": self.extra, "recall": self.recall,
                "extra_per_100": self.extra_per_100, "precision": self.precision, "sessions": self.sessions,
                "exact": self.exact, "count_error": self.count_error,
                "lag_median": float(np.median(self.lags)) if self.lags else None}  # fmt: skip


def peaks(prob: np.ndarray, readable: np.ndarray, threshold: float) -> list[tuple[int, int]]:
    """(frame, frame where it is decided) of each start; frames count from 1. On a plateau the first capture wins."""
    rows = np.flatnonzero(readable)
    values = prob[rows]
    starts = []
    for i, row in enumerate(rows):
        if values[i] < threshold:
            continue
        if (i == 0 or values[i] > values[i - 1]) and (i == len(rows) - 1 or values[i] >= values[i + 1]):
            decided = rows[i + 1] if i + 1 < len(rows) else row
            starts.append((int(row) + 1, int(decided) + 1))
    return starts


def score(session, frames_decided: list[tuple[int, int]]) -> Tally:
    """Tally of one session for starts given as (start frame, frame where it was decided)."""
    predicted = [Start(frame, decided, "", False) for frame, decided in frames_decided]
    frames = session.frames
    found = match(session.units, predicted, frames)
    lags = [frames.index(found[u["unit_id"]].decided_at) - frames.index(u["start_established_at"])
            for u in session.units if u["unit_id"] in found]  # fmt: skip
    games, count = len(session.units), len(predicted)
    return Tally(games, len(found), count - len(found), 1, int(count == games), abs(count - games), lags)


def tally(sessions: list, probs: dict, threshold: float) -> Tally:
    total = Tally()
    for session in sessions:
        total += score(session, peaks(probs[session.name], session.readable, threshold))
    return total


def candidates(sessions: list, probs: dict) -> np.ndarray:
    pooled = np.concatenate([probs[s.name][s.readable] for s in sessions])
    levels = np.concatenate((np.linspace(0, 0.9, LEVELS // 4), np.linspace(0.9, 1, LEVELS - LEVELS // 4)))
    return np.unique(np.concatenate((np.quantile(pooled, levels), [pooled.max() + 1e-9])))


def pick(sessions: list, probs: dict, budgets=BUDGETS) -> dict[float, tuple[float, Tally]]:
    """For each budget, the lowest threshold within it; when none is, the one with the fewest excess starts."""
    chosen, fallback = {}, None
    for threshold in candidates(sessions, probs):
        result = tally(sessions, probs, float(threshold))
        for budget in budgets:
            if budget not in chosen and result.extra_per_100 <= budget:
                chosen[budget] = (float(threshold), result)
        key = (result.extra, -result.found)
        if fallback is None or key < fallback[0]:
            fallback = (key, float(threshold), result)
        if len(chosen) == len(budgets):
            break
    return {budget: chosen.get(budget, (fallback[1], fallback[2])) for budget in budgets}


def average_precision(sessions: list, probs: dict, targets: dict) -> float:
    """Capture by capture, on readable captures: a ranking measure that does not depend on the threshold."""
    from sklearn.metrics import average_precision_score  # imported here: the Pi, which has no scikit-learn, uses peaks

    target = np.concatenate([targets[s.name][s.readable] for s in sessions])
    if target.sum() == 0:
        return 0.0
    return float(average_precision_score(target, np.concatenate([probs[s.name][s.readable] for s in sessions])))
