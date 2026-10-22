"""The learned start detectors: gradient boosting on one capture (with the two before it), and a GRU over the
informative captures with a head for starts and one for ends, as BSN scores starts and ends apart (Lin et al., 2018).

Gradient boosting is tried first: on tables of this size, trees are usually ahead of neural networks (Grinsztajn et
al., 2022). Label dilation marks the first readable captures of a game rather than one (Hong et al., 2022), a simple
form of the context-aware labels of Cioppa et al. (2020)."""

from __future__ import annotations

import math
import warnings

import numpy as np
import torch
from sklearn.ensemble import HistGradientBoostingClassifier
from torch import nn
from torch.nn.utils.rnn import pad_sequence

from playend.training.baselines import window
from playend.training.search import value

PATIENCE = {"boosting": 20, "gru": 20}
MAX_TREES = 1000
MAX_EPOCHS = 150
SESSIONS_PER_STEP = 4
END_SUPPORT = 3  # captures over which the end probability is looked at, the current one included
SPACES = {
    "boosting": {
        "learning_rate": ("choice", (0.05, 0.1)),
        "max_leaf_nodes": ("choice", (15, 31)),
        "l2_regularization": ("uniform", (0.0, 1.0)),
        "class_weight": ("choice", (None, "balanced")),
        "dilation": ("choice", (1, 2, 3)),
    },
    "gru": {
        "hidden": ("choice", (16, 32, 64)),
        "dropout": ("uniform", (0.0, 0.5)),
        "weight_decay": ("log", (1e-5, 1e-3)),
        "learning_rate": ("log", (3e-4, 3e-3)),
        "pos_weight": ("choice", (False, True)),
        "dilation": ("choice", (1, 2)),
    },
}
SEED = 20261014


def trials(space: str, count: int, fixed: dict | None = None) -> list[dict]:
    from torch.quasirandom import SobolEngine

    names = SPACES[space]
    points = SobolEngine(len(names), scramble=True, seed=SEED).draw(count).tolist()
    configs = [{name: value(kind, bounds, draw) for (name, (kind, bounds)), draw in zip(names.items(), point)}
               for point in points]  # fmt: skip
    return [config | (fixed or {}) for config in configs]


def boosting(config: dict, seed: int, trees: int | None, early: bool) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        learning_rate=config["learning_rate"],
        max_leaf_nodes=config["max_leaf_nodes"],
        l2_regularization=config["l2_regularization"],
        class_weight=config["class_weight"],
        max_iter=trees or MAX_TREES,
        early_stopping=early,
        n_iter_no_change=PATIENCE["boosting"],
        scoring="loss",
        random_state=seed,
    )


class Boosting:
    """Gradient boosting on the columns that vary in its training rows (a column with no value there is dropped)."""

    def __init__(self, config: dict, seed: int, trees: int | None, early: bool):
        self.model = boosting(config, seed, trees, early)
        self.kept = None

    def fit(self, x, y, x_valid=None, y_valid=None):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            low, high = np.nanmin(x, axis=0), np.nanmax(x, axis=0)
        self.kept = np.flatnonzero(np.isfinite(low) & (high > low))
        if x_valid is None:
            self.model.fit(x[:, self.kept], y)
        else:
            self.model.fit(x[:, self.kept], y, X_val=x_valid[:, self.kept], y_val=y_valid)
        return self

    @property
    def n_iter_(self) -> int:
        return self.model.n_iter_

    def predict_proba(self, x):
        return self.model.predict_proba(x[:, self.kept])


def fit_boosting(x, y, x_valid, y_valid, config: dict, seed: int, trees: int | None = None) -> Boosting:
    """Early stopping on the validation loss when validation rows are given, else exactly `trees` trees."""
    return Boosting(config, seed, trees, early=x_valid is not None).fit(x, y, x_valid, y_valid)


def raw_window(session) -> np.ndarray:
    return window(session.sequence.x, 2)


def end_support(prob_end: np.ndarray) -> np.ndarray:
    """Highest end probability over the last END_SUPPORT captures."""
    padded = np.concatenate((np.zeros(END_SUPPORT - 1, np.float32), prob_end))
    return np.max(np.lib.stride_tricks.sliding_window_view(padded, END_SUPPORT), axis=1)


def transition(prob_start: np.ndarray, prob_end: np.ndarray, readable: np.ndarray) -> np.ndarray:
    """On each readable capture, the mean of its start probability and of the highest end probability since the
    previous readable capture: what came between two readings of a game (nothing, the after-game screen, menus,
    loading...) and may hold the end of the previous one (the sum rule of Kittler et al., 1998). The first game of a
    session has no end before it and keeps its start probability."""
    out = np.zeros(len(prob_start), np.float32)
    previous = None
    for row in np.flatnonzero(readable):
        if previous is None:
            out[row] = prob_start[row]
        else:
            out[row] = (prob_start[row] + prob_end[previous + 1 : row + 1].max()) / 2
        previous = row
    return out


class StartEndGRU(nn.Module):
    def __init__(self, inputs: int, hidden: int, dropout: float):
        super().__init__()
        self.gru = nn.GRU(inputs, hidden, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.heads = nn.Linear(hidden, 2)  # start, end

    def forward(self, x):
        out, _ = self.gru(x)
        return self.heads(self.dropout(out))


class Scaler:
    """Standardisation fitted on training rows; a missing value becomes 0 and gets its own flag."""

    def __init__(self, x: np.ndarray):
        self.missing = np.flatnonzero(np.isnan(x).any(axis=0))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # a column with no value in the training rows
            self.mean = np.nanmean(x, axis=0)
            self.std = np.nanstd(x, axis=0)
        self.mean[np.isnan(self.mean)] = 0.0
        self.std[~(self.std > 0)] = 1.0

    def __call__(self, x: np.ndarray) -> np.ndarray:
        flags = np.isnan(x[:, self.missing]).astype(np.float32)
        scaled = np.nan_to_num((x - self.mean) / self.std, nan=0.0).astype(np.float32)
        return np.hstack((scaled, flags))


def gru_item(x: np.ndarray, session, start: np.ndarray, scaler: Scaler) -> dict:
    """Informative captures only, with the time since the previous one (log seconds); start and end targets."""
    rows = np.flatnonzero(session.informative)
    t = session.sequence.t[rows]
    gap = np.log1p(np.diff(np.concatenate(([t[0]], t)))).astype(np.float32)[:, None]
    end = np.zeros(len(rows), np.float32)
    end_usable = np.ones(len(rows), np.float32)
    position = np.searchsorted(rows, np.flatnonzero(session.sequence.end))
    for index, frame_row in zip(position, np.flatnonzero(session.sequence.end)):
        if index < len(rows) and rows[index] - frame_row <= END_SUPPORT:
            end[index] = 1.0  # the end proved on a capture that says nothing goes to the next informative one
    return {"rows": rows, "x": torch.from_numpy(np.hstack((scaler(x[rows]), gap))),
            "start": torch.from_numpy(start[rows].astype(np.float32)), "end": torch.from_numpy(end),
            "readable": torch.from_numpy(session.readable[rows].astype(np.float32)),
            "end_usable": torch.from_numpy(end_usable)}  # fmt: skip


def gru_loss(model, items: list[dict], pos_weight: tuple | None) -> torch.Tensor:
    x = pad_sequence([item["x"] for item in items], batch_first=True)
    logits = model(x)
    total = 0.0
    for head, key, mask_key in ((0, "start", "readable"), (1, "end", "end_usable")):
        target = pad_sequence([item[key] for item in items], batch_first=True)
        mask = pad_sequence([item[mask_key] for item in items], batch_first=True)
        weight = None if pos_weight is None else torch.tensor(pos_weight[head])
        loss = nn.functional.binary_cross_entropy_with_logits(logits[..., head], target, pos_weight=weight,
                                                              reduction="none")  # fmt: skip
        total = total + (loss * mask).sum() / mask.sum().clamp(min=1)
    return total


def fit_gru(train: list[dict], valid: list[dict] | None, config: dict, seed: int, epochs: int | None = None):
    """Early stopping on the validation loss when validation sessions are given, else exactly `epochs` epochs."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = StartEndGRU(train[0]["x"].shape[1], config["hidden"], config["dropout"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"])
    pos_weight = None
    if config["pos_weight"]:
        starts = sum(float(item["start"].sum()) for item in train)
        readable = sum(float(item["readable"].sum()) for item in train)
        ends = sum(float(item["end"].sum()) for item in train)
        rows = sum(len(item["end"]) for item in train)
        pos_weight = ((readable - starts) / max(starts, 1.0), (rows - ends) / max(ends, 1.0))
    best, best_state, best_epoch, waited = math.inf, None, 0, 0
    for epoch in range(1, (epochs or MAX_EPOCHS) + 1):
        model.train()
        order = rng.permutation(len(train))
        for begin in range(0, len(order), SESSIONS_PER_STEP):
            optimizer.zero_grad()
            loss = gru_loss(model, [train[i] for i in order[begin : begin + SESSIONS_PER_STEP]], pos_weight)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        if valid is None:
            continue
        model.eval()
        with torch.no_grad():
            valid_loss = gru_loss(model, valid, pos_weight).item()
        if valid_loss < best - 1e-5:
            best, best_epoch, waited = valid_loss, epoch, 0
            best_state = {key: tensor.detach().clone() for key, tensor in model.state_dict().items()}
        else:
            waited += 1
            if waited >= PATIENCE["gru"]:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, (best_epoch or epochs or MAX_EPOCHS)


def predict_gru(model, item: dict, length: int) -> np.ndarray:
    """Start probability on every capture of the session (0 on the captures the GRU does not read)."""
    model.eval()
    with torch.no_grad():
        prob = torch.sigmoid(model(item["x"][None])[0, :, 0]).numpy()
    out = np.zeros(length, np.float32)
    out[item["rows"]] = prob
    return out
