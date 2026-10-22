"""Configurations tried for each model: one scrambled Sobol draw, reused in every round (Tuning Playbook)."""

from __future__ import annotations

import math

from torch.quasirandom import SobolEngine

SEED = 20261005
TRIALS = {"gru": 16, "logistic": 8, "boosting": 8}

SPACES = {
    "gru": {
        "hidden": ("choice", (16, 32, 64)),
        "dropout": ("uniform", (0.0, 0.5)),
        "weight_decay": ("log", (1e-5, 1e-3)),
        "learning_rate": ("log", (3e-4, 3e-3)),
        "pos_weight": ("choice", (False, True)),
    },
    "logistic": {
        "C": ("log", (1e-3, 10.0)),
        "window": ("choice", (0, 2)),
        "class_weight": ("choice", (None, "balanced")),
    },
    "boosting": {
        "learning_rate": ("choice", (0.05, 0.1)),
        "max_leaf_nodes": ("choice", (15, 31)),
        "l2_regularization": ("uniform", (0.0, 1.0)),
        "class_weight": ("choice", (None, "balanced")),
    },
}


def value(kind: str, bounds: tuple, draw: float):
    if kind == "choice":
        return bounds[min(int(draw * len(bounds)), len(bounds) - 1)]
    if kind == "uniform":
        return round(bounds[0] + draw * (bounds[1] - bounds[0]), 4)
    low, high = math.log(bounds[0]), math.log(bounds[1])
    return float(f"{math.exp(low + draw * (high - low)):.3g}")


def trials(model: str, count: int | None = None) -> list[dict]:
    space = SPACES[model]
    points = SobolEngine(len(space), scramble=True, seed=SEED).draw(count or TRIALS[model]).tolist()
    return [
        {name: value(kind, bounds, draw) for (name, (kind, bounds)), draw in zip(space.items(), point)}
        for point in points
    ]
