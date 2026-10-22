"""Evaluation by events: consecutive rows over the threshold make one predicted end, right if it falls on a true end or
up to TOLERANCE rows later. Ends on masked rows are neither counted nor allowed to create false ends."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from sklearn.metrics import average_precision_score

from playend.training.data import Sequence

TOLERANCE = 1
CANDIDATES = 200


@dataclass
class Tally:
    ends: int = 0
    found: int = 0
    false: int = 0
    hours: float = 0.0

    def __add__(self, other: Tally) -> Tally:
        return Tally(
            self.ends + other.ends, self.found + other.found, self.false + other.false, self.hours + other.hours
        )

    @property
    def precision(self) -> float | None:
        predicted = self.found + self.false
        return self.found / predicted if predicted else None

    @property
    def recall(self) -> float | None:
        return self.found / self.ends if self.ends else None

    @property
    def false_per_100(self) -> float | None:
        return 100 * self.false / self.ends if self.ends else None

    @property
    def false_per_hour(self) -> float | None:
        return self.false / self.hours if self.hours else None

    def as_dict(self) -> dict:
        return {
            "ends": self.ends,
            "found": self.found,
            "false": self.false,
            "hours": round(self.hours, 3),
            "precision": self.precision,
            "recall": self.recall,
            "false_per_100": self.false_per_100,
            "false_per_hour": self.false_per_hour,
        }


def match(sequence: Sequence, prob: np.ndarray, threshold: float) -> tuple[list[int], list[int], list[int]]:
    """Rows of the true ends found, of the true ends missed, and of the false ends."""
    above = (prob >= threshold) & sequence.usable
    start = above & ~np.concatenate(([False], above[:-1]))
    used = np.zeros(len(prob), dtype=bool)
    found, missed = [], []
    ends = sequence.end == 1
    for row in np.flatnonzero(ends & sequence.usable):
        hit = next((r for r in range(row, min(row + TOLERANCE + 1, len(prob))) if start[r] and not used[r]), None)
        if hit is None:
            missed.append(int(row))
        else:
            used[hit] = True
            found.append(int(row))
    for row in np.flatnonzero(ends & ~sequence.usable):
        used[row : row + TOLERANCE + 1] |= start[row : row + TOLERANCE + 1]
    return found, missed, [int(row) for row in np.flatnonzero(start & ~used)]


def matches(sequences: list[Sequence], probs: dict, thresholds):
    """match() on every session; thresholds is one value, or a value per session (the threshold of its round)."""
    for sequence in sequences:
        threshold = thresholds[sequence.session] if isinstance(thresholds, dict) else thresholds
        yield sequence, *match(sequence, probs[sequence.session], threshold)


def tally(sequences: list[Sequence], probs: dict, thresholds) -> Tally:
    total = Tally()
    for sequence, found, missed, false in matches(sequences, probs, thresholds):
        total += Tally(len(found) + len(missed), len(found), len(false), sequence.hours)
    return total


def by_family(sequences: list[Sequence], probs: dict, thresholds) -> dict[str, Tally]:
    """True ends belong to the game that ended; a false end to the game read just before it."""
    tallies: dict[str, Tally] = defaultdict(Tally)
    for sequence, found, missed, false in matches(sequences, probs, thresholds):
        for row in found:
            tallies[sequence.ended_family.get(row, "")] += Tally(1, 1, 0)
        for row in missed:
            tallies[sequence.ended_family.get(row, "")] += Tally(1, 0, 0)
        for row in false:
            tallies[sequence.family[max(row - 1, 0)]] += Tally(0, 0, 1)
    return dict(tallies)


def candidates(sequences: list[Sequence], probs: dict) -> np.ndarray:
    pooled = np.concatenate([probs[s.session][s.usable] for s in sequences])
    if len(pooled) == 0:
        return np.array([0.5])
    # Ends are a few percent of the rows: the useful thresholds are in the upper tail.
    levels = np.concatenate((np.linspace(0, 0.9, CANDIDATES // 4), np.linspace(0.9, 1, CANDIDATES - CANDIDATES // 4)))
    return np.unique(np.concatenate((np.quantile(pooled, levels), [pooled.max() + 1e-9])))


def pick_thresholds(sequences: list[Sequence], probs: dict, budgets) -> dict[float, tuple[float, Tally]]:
    """For each budget, the lowest threshold keeping at most that many false ends per 100 true ends.

    When no threshold meets a budget, the one with the fewest false ends (then the most ends found) is kept.
    """
    chosen, fallback = {}, None
    for threshold in candidates(sequences, probs):
        result = tally(sequences, probs, float(threshold))
        for budget in budgets:
            if budget not in chosen and result.false_per_100 is not None and result.false_per_100 <= budget:
                chosen[budget] = (float(threshold), result)
        key = (result.false, -result.found)
        if fallback is None or key < fallback[0]:
            fallback = (key, float(threshold), result)
        if len(chosen) == len(budgets):
            break
    return {budget: chosen.get(budget, (fallback[1], fallback[2])) for budget in budgets}


def curve(sequences: list[Sequence], probs: dict) -> list[dict]:
    points = []
    for threshold in candidates(sequences, probs):
        result = tally(sequences, probs, float(threshold))
        points.append({"threshold": float(threshold), "precision": result.precision, "recall": result.recall})
    return points


def average_precision(sequences: list[Sequence], probs: dict) -> float | None:
    target = np.concatenate([s.end[s.usable] for s in sequences])
    if target.sum() == 0:
        return None
    return float(average_precision_score(target, np.concatenate([probs[s.session][s.usable] for s in sequences])))
