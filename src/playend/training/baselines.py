"""The models the GRU has to beat: hand-written rules fixed in advance, and two models without memory that see a
screenshot and the few before it."""

from __future__ import annotations

import warnings

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from playend.training.data import Sequence

IN_PLAY = {"active", "post_game", "intermediate"}
OUT_OF_PLAY = {"menu", "loading", "pre_game"}
NEW_ROUND_PLAYERS = 10
BOOSTING_WINDOW = 2
BOOSTING_PATIENCE = 20
MAX_TREES = 1000


def previous(values: np.ndarray, fill) -> np.ndarray:
    return np.concatenate(([fill], values[:-1]))


def rules(sequence: Sequence) -> np.ndarray:
    """1.0 on a row when one of four plain signs of a new game appears, else 0.0."""
    readable = sequence.readable
    total = readable["score_a"] + readable["score_b"]
    family = np.array(sequence.family)
    same_game = family == previous(family, "")
    with np.errstate(invalid="ignore"):
        score_reset = (
            (previous(total, np.nan) > 0) & (readable["score_a"] == 0) & (readable["score_b"] == 0) & same_game
        )
        players_back = readable["players"] > previous(readable["players"], np.nan) + NEW_ROUND_PLAYERS
    phase = readable["phase"]
    left_play = np.isin(previous(phase, ""), list(IN_PLAY)) & np.isin(phase, list(OUT_OF_PLAY))
    game_changed = (family != "") & (previous(family, "") != "") & ~same_game
    signal = score_reset | players_back | left_play | game_changed
    signal[0] = False
    return signal.astype(np.float32)


def window(x: np.ndarray, size: int) -> np.ndarray:
    """Each row followed by the `size` rows before it, zeros before the start of the session."""
    shifted = [x]
    for lag in range(1, size + 1):
        shifted.append(np.vstack((np.zeros((min(lag, len(x)), x.shape[1]), x.dtype), x[:-lag])))
    return np.hstack(shifted)


def table(sequences: list[Sequence], columns: list[int], size: int):
    """Windowed rows and targets of the usable rows only."""
    rows = [window(s.x[:, columns], size)[s.usable] for s in sequences]
    return np.vstack(rows), np.concatenate([s.end[s.usable] for s in sequences])


def fit_logistic(train: list[Sequence], columns: list[int], config: dict, seed: int):
    x, y = table(train, columns, config["window"])
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=config["C"], class_weight=config["class_weight"], max_iter=2000, random_state=seed),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x, y)
    return model


def fit_boosting(
    train: list[Sequence], valid: list[Sequence] | None, columns: list[int], config: dict, seed: int, trees=None
):
    """With `valid`, early stopping on its loss; otherwise exactly `trees` iterations."""
    x, y = table(train, columns, BOOSTING_WINDOW)
    model = HistGradientBoostingClassifier(
        learning_rate=config["learning_rate"],
        max_leaf_nodes=config["max_leaf_nodes"],
        l2_regularization=config["l2_regularization"],
        class_weight=config["class_weight"],
        max_iter=trees or MAX_TREES,
        early_stopping=valid is not None,
        n_iter_no_change=BOOSTING_PATIENCE,
        scoring="loss",
        random_state=seed,
    )
    if valid is None:
        model.fit(x, y)
    else:
        x_valid, y_valid = table(valid, columns, BOOSTING_WINDOW)
        model.fit(x, y, X_val=x_valid, y_val=y_valid)
    return model


def predict(model, sequences: list[Sequence], columns: list[int], size: int) -> dict:
    return {s.session: model.predict_proba(window(s.x[:, columns], size))[:, 1].astype(np.float32) for s in sequences}
