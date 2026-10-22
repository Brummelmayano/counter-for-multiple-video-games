"""The nested cross-validation as jobs (docs/decisions/PLAN_ENTRAINEMENT_GRU.md).

Each job trains one model on one split and stores its predictions; every choice is made from the stored validation
predictions only."""

from __future__ import annotations

import statistics
import time
from dataclasses import asdict, dataclass

import numpy as np

from playend.training import baselines, gru
from playend.training.columns import GROUPS, informative, without
from playend.training.data import Corpus
from playend.training.events import average_precision, pick_thresholds

ALL = "all"
BUDGETS = (1.0, 2.0, 5.0)  # false ends allowed per 100 true ends
SEARCH_SEED = 7


@dataclass(frozen=True)
class Job:
    stage: str
    model: str
    outer: str  # held-out session, or ALL
    fold: int | None  # validation fold; None for a final model
    trial: int
    dropped: tuple[str, ...] = ()
    seed: int = SEARCH_SEED
    length: int | None = None  # final models: epochs (GRU) or trees (boosting)

    @property
    def id(self) -> str:
        outer = self.outer if self.outer == ALL else self.outer.removeprefix("session_")[:8]
        dropped = "+".join(self.dropped) or "none"
        return f"{self.stage}-{self.model}-{outer}-f{self.fold}-t{self.trial}-d{dropped}-r{self.seed}"


def training_sessions(corpus: Corpus, outer: str) -> list[str]:
    return [session for session in corpus.sequences if session != outer]


def inner_folds(corpus: Corpus, outer: str) -> list[int]:
    held = corpus.sequences[outer].fold if outer != ALL else None
    return sorted({s.fold for s in corpus.sequences.values()} - {held})


def split(corpus: Corpus, outer: str, fold: int):
    sessions = training_sessions(corpus, outer)
    train = [corpus.sequences[s] for s in sessions if corpus.sequences[s].fold != fold]
    valid = [corpus.sequences[s] for s in sessions if corpus.sequences[s].fold == fold]
    return train, valid


def kept_columns(corpus: Corpus, outer: str, dropped: tuple[str, ...]) -> list[int]:
    stacked = np.vstack([corpus.sequences[s].x for s in training_sessions(corpus, outer)])
    return without(corpus.feature_names, informative(stacked), dropped)


def run(job: Job, corpus: Corpus, settings: dict, device: str) -> tuple[dict, dict, dict | None]:
    """Train the model of a job; return its record, its predictions and, for a final GRU, its weights."""
    started = time.time()
    config = settings["configs"][job.model][job.trial]
    columns = kept_columns(corpus, job.outer, job.dropped)
    if job.fold is None:
        train = corpus.select(training_sessions(corpus, job.outer))
        scored = [] if job.outer == ALL else [corpus.sequences[job.outer]]
        valid = None
    else:
        train, valid = split(corpus, job.outer, job.fold)
        scored = valid
    record = {**asdict(job), "id": job.id, "config": config, "columns": len(columns)}
    arrays, state = {}, None
    if job.model == "gru":
        result = gru.fit(train, valid, columns, config, device, job.seed, job.length, settings["max_epochs"])
        predictions = gru.predict(result.state, config, columns, scored, device)
        for session, (prob, billing) in predictions.items():
            arrays[session] = prob
            arrays[f"{session}:billing"] = billing
        record |= {"best_epoch": result.best_epoch, "curve": result.curve, "device": device}
        if job.fold is None:
            state = {
                "weights": result.state,
                "config": config,
                "columns": [corpus.feature_names[i] for i in columns],
                "feature_sha256": corpus.feature_sha256,  # lets the Pi refuse inputs of another feature version
            }
    elif job.model == "logistic":
        model = baselines.fit_logistic(train, columns, config, job.seed)
        arrays = baselines.predict(model, scored, columns, config["window"])
    else:
        model = baselines.fit_boosting(train, valid, columns, config, job.seed, job.length)
        arrays = baselines.predict(model, scored, columns, baselines.BOOSTING_WINDOW)
        record["best_epoch"] = int(model.n_iter_)
    record["seconds"] = round(time.time() - started, 2)
    return record, arrays, state


def search_jobs(corpus: Corpus, settings: dict) -> list[Job]:
    return [
        Job("search", model, outer, fold, trial)
        for outer in settings["outers"]
        for model in settings["models"]
        for trial in range(len(settings["configs"][model]))
        for fold in inner_folds(corpus, outer)
    ]


def assess(corpus: Corpus, store, outer: str, model: str, trial: int, dropped: tuple[str, ...], stage: str) -> dict:
    """Pool the validation predictions of the inner folds and score them."""
    probs, epochs = {}, []
    folds = inner_folds(corpus, outer)
    for fold in folds:
        job = Job(stage, model, outer, fold, trial, dropped)
        arrays = store.arrays(job.id)
        probs.update({key: value for key, value in arrays.items() if ":" not in key})
        epochs.append(store.record(job.id).get("best_epoch"))
    sequences = [corpus.sequences[s] for s in probs]
    chosen = {
        str(budget): {"threshold": threshold, **result.as_dict()}
        for budget, (threshold, result) in pick_thresholds(sequences, probs, BUDGETS).items()
    }
    main = chosen[str(BUDGETS[0])]
    return {
        "trial": trial,
        "dropped": list(dropped),
        "recall": main["recall"] or 0.0,
        "average_precision": average_precision(sequences, probs) or 0.0,
        "thresholds": chosen,
        "epochs": [e for e in epochs if e is not None],
    }


def rank(assessment: dict) -> tuple:
    return (assessment["recall"], assessment["average_precision"])


def assess_trials(corpus: Corpus, store, settings: dict, outer: str, model: str) -> list[dict]:
    return [assess(corpus, store, outer, model, t, (), "search") for t in range(len(settings["configs"][model]))]


def ablation_jobs(corpus: Corpus, outer: str, trial: int, dropped_sets) -> list[Job]:
    return [
        Job("ablation", "gru", outer, fold, trial, tuple(dropped))
        for dropped in dropped_sets
        for fold in inner_folds(corpus, outer)
    ]


def groups_to_drop(full: dict, alone: dict[str, dict]) -> tuple[str, ...]:
    """A group goes when the GRU without it ranks at least as well on validation (recall, then average precision)."""
    return tuple(g for g in GROUPS if rank(alone[g]) >= rank(full))


def final_jobs(choice: dict, outer: str, seeds: int) -> list[Job]:
    jobs = []
    for model, selected in choice["models"].items():
        length = max(1, round(statistics.median(selected["epochs"]))) if selected["epochs"] else None
        count = seeds if model == "gru" else 1
        for seed in range(count):
            jobs.append(Job("final", model, outer, None, selected["trial"], tuple(selected["dropped"]), seed, length))
    return jobs
