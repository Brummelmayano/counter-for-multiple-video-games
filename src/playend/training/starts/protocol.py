"""The nested cross-validation, one outer fold at a time (docs/training/PROTOCOLE_DEBUTS.md).

Outer loop: the 5 frozen folds of PlayEnd; each session is predicted once, by a model that never saw its fold. Inner
loop: on the 4 other folds, each held out in turn, the configurations are tried, the threshold is chosen for each
budget, and the best configuration is kept (recall at the main budget, then average precision). The final model is
trained on the 4 folds and predicts the outer fold once. Nothing chosen sees the outer fold (Cawley and Talbot, 2010;
Varma and Simon, 2006)."""

from __future__ import annotations

import contextlib
import itertools
import statistics

import numpy as np

from playend.counting import starts as rules
from playend.counting.portraits import SessionPortraits
from playend.counting.starts import detect
from playend.training.starts import events, models
from playend.training.starts.sources import start_labels

TRIALS = {"boosting": 8, "gru": 8}
GRU_SEEDS = 3
# Rule settings tried by the control: the thresholds written by hand in playend.counting.starts.
RULE_GRID = {
    "FINAL_RUN": (2, 3, 4),
    "PLAYERS_DROP": (2, 3, 5),
    "PLAYERS_JUMP": (6, 10, 15),
    "CLOCK_BACK_S": (30, 60, 120),
}
HYBRID_LEVELS = (0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99)  # quantiles of the probability on readable captures
HYBRID_WINDOW = 3  # readable captures around a rule start where a model start is the same start


def split(sessions: dict, outer: int) -> tuple[list, list]:
    train = [s for s in sessions.values() if s.fold != outer]
    test = [s for s in sessions.values() if s.fold == outer]
    return train, test


def inner_folds(train: list) -> list[int]:
    return sorted({s.fold for s in train})


def inputs(prepared, method: str, session, end_prob: np.ndarray | None = None) -> np.ndarray:
    """Rows of every capture of the session for a method.

    The decisions of the rules are given to gb_rules only: the rules were written while reading every session, so a
    model fed with them inherits that view of its test fold. The other models see the game state the rules keep,
    which is domain knowledge, but not what the rules decided."""
    if method == "gb_raw":
        return models.raw_window(session)
    state = prepared.state[session.name]
    if method != "gb_rules":
        state = state[:, [i for i, name in enumerate(prepared.names) if not name.startswith("rules_")]]
    x = np.hstack((state, session.sequence.x))
    if method == "gb_end_support":
        x = np.hstack((x, models.end_support(end_prob)[:, None]))
    return x


def readable_rows(prepared, method, sessions, dilation, end_probs=None):
    xs, ys = [], []
    for s in sessions:
        x = inputs(prepared, method, s, None if end_probs is None else end_probs[s.name])
        xs.append(x[s.readable])
        ys.append(start_labels(s, dilation)[s.readable])
    return np.vstack(xs), np.concatenate(ys)


def predict_rows(model, prepared, method, session, end_prob=None) -> np.ndarray:
    prob = np.zeros(len(session.observations), np.float32)
    x = inputs(prepared, method, session, end_prob)
    if session.readable.any():
        prob[session.readable] = model.predict_proba(x[session.readable])[:, 1]
    return prob


def end_rows(prepared, sessions):
    xs = [inputs(prepared, "gb_state", s)[s.sequence.usable] for s in sessions]
    ys = [s.sequence.end[s.sequence.usable] for s in sessions]
    return np.vstack(xs), np.concatenate(ys)


END_CONFIG = {"learning_rate": 0.1, "max_leaf_nodes": 15, "l2_regularization": 0.5, "class_weight": None}
END_TREES = 200


def end_model(prepared, sessions):
    x, y = end_rows(prepared, sessions)
    return models.fit_boosting(x, y, None, None, END_CONFIG, 0, END_TREES)


def end_probs(prepared, train: list, scored: list) -> dict:
    """End probabilities: out of fold on the training sessions (by their folds), from all of them on the others.

    A model fed with in-sample predictions learns to trust them more than it should (Wolpert, 1992; Ting and
    Witten, 1999): each training session gets the predictions of an end model that did not see its fold."""
    out = {}
    for fold in sorted({s.fold for s in train}):
        model = end_model(prepared, [s for s in train if s.fold != fold])
        for s in train:
            if s.fold == fold:
                out[s.name] = model.predict_proba(inputs(prepared, "gb_state", s))[:, 1].astype(np.float32)
    model = end_model(prepared, train)
    for s in scored:
        out[s.name] = model.predict_proba(inputs(prepared, "gb_state", s))[:, 1].astype(np.float32)
    return out


def assess(sessions: list, probs: dict, dilation: int) -> dict:
    targets = {s.name: start_labels(s, dilation) for s in sessions}
    thresholds = events.pick(sessions, probs)
    main = thresholds[events.MAIN_BUDGET][1]
    return {
        "recall": main.recall,
        "average_precision": events.average_precision(sessions, probs, targets),
        "thresholds": {str(budget): {"threshold": t, **result.as_dict()} for budget, (t, result) in thresholds.items()},
    }


def rank(assessment: dict) -> tuple:
    return assessment["recall"], assessment["average_precision"]


def boosting_outer(prepared, method: str, outer: int, quick: bool) -> dict:
    train, test = split(prepared.sessions, outer)
    configs = models.trials("boosting", 2 if quick else TRIALS["boosting"],
                            None if method in ("gb_state_dilated", "gb_rules") else {"dilation": 1})  # fmt: skip
    inner = {}
    for fold in inner_folds(train):
        fit_on = [s for s in train if s.fold != fold]
        held = [s for s in train if s.fold == fold]
        stacked = end_probs(prepared, fit_on, held) if method == "gb_end_support" else None
        for trial, config in enumerate(configs):
            x, y = readable_rows(prepared, method, fit_on, config["dilation"], stacked)
            xv, yv = readable_rows(prepared, method, held, config["dilation"], stacked)
            model = models.fit_boosting(x, y, xv, yv, config, trial)
            probs = {s.name: predict_rows(model, prepared, method, s, None if stacked is None else stacked[s.name])
                     for s in held}  # fmt: skip
            inner.setdefault(trial, {"probs": {}, "trees": []})
            inner[trial]["probs"] |= probs
            inner[trial]["trees"].append(int(model.n_iter_))
    assessments = {trial: assess(train, record["probs"], configs[trial]["dilation"]) for trial, record in inner.items()}
    best = max(assessments, key=lambda trial: rank(assessments[trial]))
    config, trees = configs[best], max(1, round(statistics.median(inner[best]["trees"])))
    stacked = end_probs(prepared, train, test) if method == "gb_end_support" else None
    x, y = readable_rows(prepared, method, train, config["dilation"], stacked)
    model = models.fit_boosting(x, y, None, None, config, best, trees)
    test_probs = {s.name: predict_rows(model, prepared, method, s, None if stacked is None else stacked[s.name])
                  for s in test}  # fmt: skip
    return finish(method, outer, config, best, assessments, inner[best]["probs"], test_probs, test, trees=trees)


def transition_outer(prepared, outer: int, quick: bool) -> dict:
    """A start model and an end model trained apart, fused by models.transition: an end in the break, then a start,
    make one strong signal (the author's idea of 2026-10-15). Nothing is learned in the fusion, so neither model ever
    sees predictions made on its own training sessions."""
    train, test = split(prepared.sessions, outer)
    configs = models.trials("boosting", 2 if quick else TRIALS["boosting"])
    inner = {}
    for fold in inner_folds(train):
        fit_on = [s for s in train if s.fold != fold]
        held = [s for s in train if s.fold == fold]
        ends = end_model(prepared, fit_on)
        prob_end = {s.name: ends.predict_proba(inputs(prepared, "gb_state", s))[:, 1] for s in held}
        for trial, config in enumerate(configs):
            x, y = readable_rows(prepared, "gb_state", fit_on, config["dilation"])
            xv, yv = readable_rows(prepared, "gb_state", held, config["dilation"])
            model = models.fit_boosting(x, y, xv, yv, config, trial)
            record = inner.setdefault(trial, {"probs": {}, "trees": []})
            for s in held:
                start = predict_rows(model, prepared, "gb_state", s)
                record["probs"][s.name] = models.transition(start, prob_end[s.name], s.readable)
            record["trees"].append(int(model.n_iter_))
    assessments = {trial: assess(train, record["probs"], configs[trial]["dilation"]) for trial, record in inner.items()}
    best = max(assessments, key=lambda trial: rank(assessments[trial]))
    config, trees = configs[best], max(1, round(statistics.median(inner[best]["trees"])))
    x, y = readable_rows(prepared, "gb_state", train, config["dilation"])
    model = models.fit_boosting(x, y, None, None, config, best, trees)
    ends = end_model(prepared, train)
    test_probs = {}
    for s in test:
        prob_end = ends.predict_proba(inputs(prepared, "gb_state", s))[:, 1]
        test_probs[s.name] = models.transition(predict_rows(model, prepared, "gb_state", s), prob_end, s.readable)
    return finish("gb_transition", outer, config, best, assessments, inner[best]["probs"], test_probs, test,
                  trees=trees)  # fmt: skip


def gru_outer(prepared, outer: int, quick: bool) -> dict:
    import torch

    torch.set_num_threads(1)
    train, test = split(prepared.sessions, outer)
    configs = models.trials("gru", 2 if quick else TRIALS["gru"])
    max_epochs = 3 if quick else models.MAX_EPOCHS
    inner = {}

    def items(sessions, scaler, dilation):
        return [
            models.gru_item(inputs(prepared, "gb_state", s), s, start_labels(s, dilation), scaler) for s in sessions
        ]

    def stacked_x(sessions):
        return np.vstack([inputs(prepared, "gb_state", s)[s.informative] for s in sessions])

    for fold in inner_folds(train):
        fit_on = [s for s in train if s.fold != fold]
        held = [s for s in train if s.fold == fold]
        scaler = models.Scaler(stacked_x(fit_on))
        for trial, config in enumerate(configs):
            fitted, valid = items(fit_on, scaler, config["dilation"]), items(held, scaler, config["dilation"])
            model, epoch = models.fit_gru(fitted, valid, config, trial, max_epochs if quick else None)
            record = inner.setdefault(trial, {"probs": {}, "epochs": []})
            for s, item in zip(held, valid):
                record["probs"][s.name] = models.predict_gru(model, item, len(s.observations))
            record["epochs"].append(epoch)
    assessments = {trial: assess(train, record["probs"], configs[trial]["dilation"]) for trial, record in inner.items()}
    best = max(assessments, key=lambda trial: rank(assessments[trial]))
    config, epochs = configs[best], max(1, round(statistics.median(inner[best]["epochs"])))
    scaler = models.Scaler(stacked_x(train))
    test_items = items(test, scaler, config["dilation"])
    test_probs = {s.name: np.zeros(len(s.observations), np.float32) for s in test}
    for seed in range(1 if quick else GRU_SEEDS):  # the mean of a few seeds, whose spread is not negligible
        model, _ = models.fit_gru(items(train, scaler, config["dilation"]), None, config, seed, epochs)
        for s, item in zip(test, test_items):
            test_probs[s.name] += models.predict_gru(model, item, len(s.observations)) / (1 if quick else GRU_SEEDS)
    return finish("gru", outer, config, best, assessments, inner[best]["probs"], test_probs, test, epochs=epochs)


def finish(method, outer, config, best, assessments, valid_probs, test_probs, test, **length) -> dict:
    chosen = assessments[best]["thresholds"]
    predicted = {}
    for budget, choice in chosen.items():
        predicted[budget] = {s.name: events.peaks(test_probs[s.name], s.readable, choice["threshold"]) for s in test}
    return {
        "method": method,
        "outer": outer,
        "config": config,
        "trial": best,
        "trials": {str(trial): {k: v for k, v in a.items() if k != "thresholds"} for trial, a in assessments.items()},
        "validation": chosen,
        "predicted": predicted,
        "valid_probs": {name: prob.tolist() for name, prob in valid_probs.items()},
        "test_probs": {name: prob.tolist() for name, prob in test_probs.items()},
        **length,
    }


def rules_fixed(prepared) -> dict:
    return {
        str(budget): {
            s.name: [(start.frame, start.decided_at) for start in prepared.rule_starts[s.name]]
            for s in prepared.sessions.values()
        }  # fmt: skip
        for budget in events.BUDGETS
    }


@contextlib.contextmanager
def rule_settings(settings: dict):
    saved = {name: getattr(rules, name) for name in settings}
    try:
        for name, setting in settings.items():
            setattr(rules, name, setting)
        yield
    finally:
        for name, setting in saved.items():
            setattr(rules, name, setting)


def rules_grid(prepared, quick: bool) -> list[dict]:
    names = list(RULE_GRID)
    grid = [dict(zip(names, values)) for values in itertools.product(*RULE_GRID.values())]
    grid = grid[:3] if quick else grid
    portraits = {name: SessionPortraits(name) for name in prepared.sessions}
    results = []
    for settings in grid:
        with rule_settings(settings):
            starts = {name: [(st.frame, st.decided_at) for st in detect(_by_frame(s), False, True, portraits[name])]
                      for name, s in prepared.sessions.items()}  # fmt: skip
        results.append({"settings": settings, "starts": starts})
    return results


def _by_frame(session) -> dict[int, dict]:
    return {index + 1: obs for index, obs in enumerate(session.observations)}


def choose(tallies: list, budget: float) -> int:
    """The setting that finds the most games within the budget; when none is within it, the fewest excess starts."""
    within = [i for i, tally in enumerate(tallies) if tally.extra_per_100 <= budget]
    if within:
        return max(within, key=lambda i: (tallies[i].found, -tallies[i].extra))
    return min(range(len(tallies)), key=lambda i: (tallies[i].extra, -tallies[i].found))


def rules_tuned(prepared, grid: list[dict]) -> dict:
    """Per outer fold and budget, the rule settings that find the most games on the training sessions within the
    budget (fewest excess starts when none is), applied to the outer fold."""
    out = {str(budget): {} for budget in events.BUDGETS}
    choices = {}
    for outer in sorted({s.fold for s in prepared.sessions.values()}):
        train, test = split(prepared.sessions, outer)
        tallies = []
        for entry in grid:
            total = events.Tally()
            for s in train:
                total += events.score(s, entry["starts"][s.name])
            tallies.append(total)
        for budget in events.BUDGETS:
            best = choose(tallies, budget)
            choices.setdefault(str(budget), {})[str(outer)] = grid[best]["settings"]
            for s in test:
                out[str(budget)][s.name] = grid[best]["starts"][s.name]
    return {"predicted": out, "choices": choices}


def hybrid_starts(session, rule_starts, prob, verify: float, add: float) -> list[tuple[int, int]]:
    """Rule starts the model backs (probability at or above `verify` near the start), and model starts above `add`
    far from any rule start: the rules propose, the model checks and fills in (a two-stage cascade)."""
    readable = np.flatnonzero(session.readable)
    position = {int(row) + 1: i for i, row in enumerate(readable)}

    def near(frame):
        i = position.get(frame)
        if i is None:
            i = int(np.searchsorted(readable, frame - 1))
        rows = readable[max(0, i - HYBRID_WINDOW) : i + HYBRID_WINDOW + 1]
        return float(prob[rows].max()) if len(rows) else 0.0

    kept = [(f, d) for f, d in rule_starts if near(f) >= verify]
    proposed = {f for f, _ in rule_starts}
    added = []
    if np.isfinite(add):
        for frame, decided in events.peaks(prob, session.readable, add):
            i = position[frame]
            window_frames = {int(r) + 1 for r in readable[max(0, i - HYBRID_WINDOW) : i + HYBRID_WINDOW + 1]}
            if not window_frames & proposed:
                added.append((frame, decided))
    return sorted(kept + added)


def hybrid_outer(prepared, model_record: dict, outer: int) -> dict:
    train, test = split(prepared.sessions, outer)
    valid = {name: np.array(prob, np.float32) for name, prob in model_record["valid_probs"].items()}
    tested = {name: np.array(prob, np.float32) for name, prob in model_record["test_probs"].items()}
    pooled = np.concatenate([valid[s.name][s.readable] for s in train])
    levels = sorted({float(np.quantile(pooled, q)) if q > 0 else 0.0 for q in HYBRID_LEVELS})
    pairs = [(v, a) for v in levels for a in [*levels[1:], float("inf")]]
    tallies = []
    for verify, add in pairs:
        total = events.Tally()
        for s in train:
            total += events.score(s, hybrid_starts(s, rules_starts_of(prepared, s), valid[s.name], verify, add))
        tallies.append(total)
    predicted, choices = {}, {}
    for budget in events.BUDGETS:
        best = choose(tallies, budget)
        verify, add = pairs[best]
        choices[str(budget)] = {"verify": verify, "add": add, **tallies[best].as_dict()}
        predicted[str(budget)] = {s.name: hybrid_starts(s, rules_starts_of(prepared, s), tested[s.name], verify, add)
                                  for s in test}  # fmt: skip
    return {"method": "hybrid", "outer": outer, "validation": choices, "predicted": predicted}


def rules_starts_of(prepared, session) -> list[tuple[int, int]]:
    return [(start.frame, start.decided_at) for start in prepared.rule_starts[session.name]]
