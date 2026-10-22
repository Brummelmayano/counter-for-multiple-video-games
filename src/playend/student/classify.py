"""Train and evaluate the student's classifier: the game and the type of screen, from MobileNetV2 features.

The 1000 ImageNet scores of each capture (build/student/features.npz) are standardised and reduced to 128 principal
components, then a logistic regression learns the teacher's labels. Two evaluations, because a game seen in a single
session cannot be recognised once that session is held out:

- by session: each session in turn is held out; frames of a game no other session shows are counted apart;
- by blocks of time: every session is cut into five consecutive blocks, and block k of every session is held out
  in turn (blocked cross-validation for dependent data, Roberts et al. 2017).

The model trained on every frame is written as plain arrays (build/student/classifier.npz), so the Pi needs only
NumPy to apply it.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from playend.common.games import NO_GAME
from playend.common.paths import STUDENT_OUTPUT
from playend.student.collect import OBSERVATIONS

BLOCKS = 5
COMPONENTS = 128


def load(features_path: Path):
    data = np.load(features_path)
    labels = {}
    with open(OBSERVATIONS, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            labels[(row["session_id"], int(row["frame_id"]))] = (row["game_family"] or NO_GAME, row["screen_type"])
    keys = list(zip(data["session"].tolist(), data["frame"].tolist()))
    games = np.array([labels[key][0] for key in keys])
    screens = np.array([labels[key][1] for key in keys])
    return data["features"], data["session"], games, screens


def fit(features: np.ndarray, labels: np.ndarray):
    scaler = StandardScaler().fit(features)
    pca = PCA(COMPONENTS, random_state=0).fit(scaler.transform(features))
    model = LogisticRegression(C=1.0, max_iter=1000).fit(pca.transform(scaler.transform(features)), labels)
    return scaler, pca, model


def predict(fitted, features):
    scaler, pca, model = fitted
    probabilities = model.predict_proba(pca.transform(scaler.transform(features)))
    return model.classes_[probabilities.argmax(axis=1)], probabilities.max(axis=1)


def blocks(sessions: np.ndarray) -> np.ndarray:
    """Block number of each frame: frames are in time order within a session."""
    numbers = np.zeros(len(sessions), dtype=int)
    for session in np.unique(sessions):
        where = np.flatnonzero(sessions == session)
        numbers[where] = np.arange(len(where)) * BLOCKS // len(where)
    return numbers


def evaluate(name: str, folds: np.ndarray, features, labels, sessions=None):
    predicted = np.empty(len(labels), dtype=object)
    confidence = np.zeros(len(labels))
    unseen = np.zeros(len(labels), dtype=bool)
    for fold in np.unique(folds):
        test = folds == fold
        predicted[test], confidence[test] = predict(fit(features[~test], labels[~test]), features[test])
        unseen[test] = ~np.isin(labels[test], labels[~test])
    seen = ~unseen
    right = predicted == labels
    print(f"{name}: {right[seen].mean():.1%} correct on {seen.sum()} frames of classes seen in training", end="")
    if unseen.any():
        print(f"; {unseen.sum()} frames of classes never seen (median confidence {np.median(confidence[unseen]):.2f}"
              f", against {np.median(confidence[seen & right]):.2f} when right)", end="")  # fmt: skip
    print()
    errors = Counter(
        (label, guess) for label, guess, ok, known in zip(labels, predicted, right, seen) if known and not ok
    )
    for (label, guess), count in errors.most_common(5):
        print(f"    {count:4} {label} -> {guess}")
    return predicted, confidence


def smoothed(predicted, confidence, sessions, window: int) -> np.ndarray:
    """Causal vote: each frame takes the label with the largest summed confidence over its last `window` frames."""
    out = np.empty(len(predicted), dtype=object)
    for session in np.unique(sessions):
        where = np.flatnonzero(sessions == session)
        for position, index in enumerate(where):
            votes = Counter()
            for earlier in where[max(0, position - window + 1) : position + 1]:
                votes[predicted[earlier]] += confidence[earlier]
            out[index] = votes.most_common(1)[0][0]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--features", type=Path, default=STUDENT_OUTPUT / "features.npz")
    parser.add_argument("--out", type=Path, default=STUDENT_OUTPUT / "classifier.npz")
    parser.add_argument("--oof", type=Path, help="only write, for every frame, the game (with the vote) and the screen "
                        "predicted by models that did not see its block of time")  # fmt: skip
    args = parser.parse_args()
    features, sessions, games, screens = load(args.features)
    gameplay = screens == "gameplay"
    print(f"{len(games)} frames, {len(np.unique(games))} games (with '{NO_GAME}'), {len(np.unique(screens))} screens")
    if args.oof:
        game, confidence = evaluate("game, by block of time", blocks(sessions), features, games)
        screen, _ = evaluate("screen, by block of time", blocks(sessions), features, screens)
        game = smoothed(game, confidence, sessions, 5)
        frames = np.load(args.features)["frame"].tolist()
        out = {f"{s}:{f}": {"game": g, "screen": c} for s, f, g, c in zip(sessions.tolist(), frames, game, screen)}
        args.oof.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        return
    session_folds = np.unique(sessions, return_inverse=True)[1]
    evaluate("game, by session", session_folds, features, games)
    predicted, confidence = evaluate("game, by block of time", blocks(sessions), features, games)
    for window in (3, 5, 9):
        print(f"    with a vote over the last {window} captures: "
              f"{(smoothed(predicted, confidence, sessions, window) == games).mean():.1%} correct")  # fmt: skip
    evaluate("screen, by block of time", blocks(sessions), features, screens)
    evaluate("gameplay or not, by block of time", blocks(sessions), features, gameplay.astype(str))
    arrays = {}
    for target, labels in (("game", games), ("screen", screens)):
        scaler, pca, model = fit(features, labels)
        # standardise, project, then score: three matrix products the Pi does with NumPy
        arrays |= {
            f"{target}_mean": scaler.mean_, f"{target}_scale": scaler.scale_, f"{target}_pca_mean": pca.mean_,
            f"{target}_pca": pca.components_, f"{target}_weights": model.coef_, f"{target}_bias": model.intercept_,
            f"{target}_classes": model.classes_,
        }  # fmt: skip
    np.savez(args.out, **arrays)
    print(f"model trained on all frames -> {args.out}")


if __name__ == "__main__":
    main()
