"""Which feature columns a model receives, and the groups removed one at a time to measure what they bring."""

from __future__ import annotations

import numpy as np

GROUPS = ("counters", "timers", "changes", "mode")


def group_of(name: str) -> str | None:
    # A counter's change belongs to the counters: the groups must not overlap.
    if name.startswith("counter."):
        return "counters"
    if name.startswith("secondary."):
        return "timers"
    if ".delta_candidate" in name or ".changed" in name or name.startswith("clock.seconds_since"):
        return "changes"
    if name.startswith("game.mode="):
        return "mode"
    return None


def informative(x: np.ndarray) -> list[int]:
    """Columns that vary, minus exact copies and complements. Labels are never read: it runs inside each round."""
    kept, seen = [], set()
    for index in range(x.shape[1]):
        column = x[:, index]
        if column.min() == column.max():
            continue
        if column.tobytes() in seen or (1 - column).tobytes() in seen:
            continue
        seen.add(column.tobytes())
        kept.append(index)
    return kept


def without(names: list[str], kept: list[int], dropped: tuple[str, ...]) -> list[int]:
    return [index for index in kept if group_of(names[index]) not in dropped]
