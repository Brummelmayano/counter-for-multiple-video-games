"""The learned start detectors of the pipeline comparison, trained once on the 25 sessions of PlayEnd (student
readings).

The configuration and the number of trees or epochs are chosen as in the protocol, by the 5 folds of PlayEnd, and the
threshold of the main budget (2 games in excess per 100) on the predictions those folds give; nothing here looks at
the held-out sessions. Two detectors: gradient boosting fed with the game state and the decisions of the rules (the
best of step 3 with the student), and the GRU with a start and an end head. Each is also written as plain arrays, so
the Raspberry Pi runs it with NumPy alone (playend.counting.pipelines).

usage: python -m playend.training.starts.final [--out build/training/starts_final]
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from playend.common.paths import REPO
from playend.training.starts import events, models, protocol
from playend.training.starts.sources import start_labels

PREPARED = REPO / "build" / "training" / "starts_2026-10-15" / "prepared" / "student.pkl"
ALL_SESSIONS = 0  # an outer fold that does not exist: the protocol then chooses on all 5 folds


def boosting_arrays(model: models.Boosting) -> dict:
    """The trees of a fitted HistGradientBoostingClassifier as flat arrays, one row per node, tree after tree."""
    nodes = [predictor.nodes for (predictor,) in model.model._predictors]
    offsets = np.cumsum([0] + [len(tree) for tree in nodes[:-1]])
    stacked = np.concatenate(nodes)
    return {
        "feature": stacked["feature_idx"].astype(np.int32),
        "threshold": stacked["num_threshold"].astype(np.float64),
        "missing_left": stacked["missing_go_to_left"].astype(np.bool_),
        "left": stacked["left"].astype(np.int64),
        "right": stacked["right"].astype(np.int64),
        "leaf": stacked["is_leaf"].astype(np.bool_),
        "value": stacked["value"].astype(np.float64),
        "roots": offsets.astype(np.int64),
        "baseline": np.float64(np.ravel(model.model._baseline_prediction)[0]),
        "kept": model.kept.astype(np.int64),
    }


def gru_arrays(model, scaler: models.Scaler) -> dict:
    state = {key: value.numpy() for key, value in model.state_dict().items()}
    return {
        "weight_ih": state["gru.weight_ih_l0"], "weight_hh": state["gru.weight_hh_l0"],
        "bias_ih": state["gru.bias_ih_l0"], "bias_hh": state["gru.bias_hh_l0"],
        "head_weight": state["heads.weight"], "head_bias": state["heads.bias"],
        "mean": scaler.mean.astype(np.float32), "std": scaler.std.astype(np.float32),
        "missing": scaler.missing.astype(np.int64),
    }  # fmt: skip


def train(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    with PREPARED.open("rb") as stream:
        prepared = pickle.load(stream)
    sessions = list(prepared.sessions.values())
    meta = {"state_names": prepared.names, "budget": events.MAIN_BUDGET}

    with threadpool_limits(1):
        chosen = protocol.boosting_outer(prepared, "gb_rules", ALL_SESSIONS, False)
        config, trees = chosen["config"], chosen["trees"]
        x, y = protocol.readable_rows(prepared, "gb_rules", sessions, config["dilation"])
        boosting = models.fit_boosting(x, y, None, None, config, chosen["trial"], trees)
    with (out / "gb_rules.pkl").open("wb") as stream:
        pickle.dump(boosting, stream)
    np.savez(out / "gb_rules.npz", **boosting_arrays(boosting))
    meta["gb_rules"] = {"config": config, "trees": trees,
                        "threshold": chosen["validation"][str(events.MAIN_BUDGET)]["threshold"],
                        "validation": chosen["validation"][str(events.MAIN_BUDGET)]}  # fmt: skip

    chosen = protocol.gru_outer(prepared, ALL_SESSIONS, False)
    config, epochs = chosen["config"], chosen["epochs"]
    scaler = models.Scaler(np.vstack([protocol.inputs(prepared, "gb_state", s)[s.informative] for s in sessions]))
    items = [models.gru_item(protocol.inputs(prepared, "gb_state", s), s, start_labels(s, config["dilation"]), scaler)
             for s in sessions]  # fmt: skip
    for seed in range(protocol.GRU_SEEDS):
        model, _ = models.fit_gru(items, None, config, seed, epochs)
        np.savez(out / f"gru_seed{seed}.npz", **gru_arrays(model, scaler))
    meta["gru"] = {"config": config, "epochs": epochs, "seeds": protocol.GRU_SEEDS,
                   "threshold": chosen["validation"][str(events.MAIN_BUDGET)]["threshold"],
                   "validation": chosen["validation"][str(events.MAIN_BUDGET)]}  # fmt: skip
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=REPO / "build" / "training" / "starts_final")
    meta = train(parser.parse_args().out)
    for name in ("gb_rules", "gru"):
        print(name, meta[name]["config"], "threshold", meta[name]["threshold"], meta[name]["validation"])


if __name__ == "__main__":
    main()
