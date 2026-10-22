"""Marks that are not text: round pastilles, round diamonds and remaining-life blocks, read from their pixels.

For each game and side, the box of the marks is reduced to a few pixels, and a logistic regression learns the
teacher's value from them (rounds won, or life bars left), with "none" when the teacher has no value. Evaluated by
blocks of time like the classifier (playend.student.classify); the models trained on every frame are written as
plain arrays to build/student/marks.npz for the Pi.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from playend.common.paths import STUDENT_OUTPUT
from playend.student.classify import blocks
from playend.student.collect import OBSERVATIONS, frame_paths
from playend.student.zones import MARKS, NONE, pixels


def collect():
    """Pixels of both sides and the teacher's values, for every gameplay frame of the games with marks."""
    rows = defaultdict(list)
    with open(OBSERVATIONS, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["screen_type"] == "gameplay" and row["game_family"] in MARKS:
                rows[row["game_family"]].append(row)
    data = {}
    for game, game_rows in rows.items():
        field_a, field_b, box_a, box_b = MARKS[game]
        paths, current, samples = {}, None, []
        for row in game_rows:
            if row["session_id"] != current:
                paths, current = frame_paths(row["session_id"]), row["session_id"]
            frame = Image.open(paths[int(row["frame_id"])]).convert("RGB")
            for side, field, box in (("a", field_a, box_a), ("b", field_b, box_b)):
                samples.append((row["session_id"], int(row["frame_id"]), pixels(frame, box), row[field] or NONE, side))
        data[game] = samples
    return data


def fit(features, labels):
    scaler = StandardScaler().fit(features)
    return scaler, LogisticRegression(C=0.1, max_iter=2000).fit(scaler.transform(features), labels)


def cross_validate(samples):
    """Predictions made by models that never saw the block of time of each sample."""
    sessions = np.array([sample[0] for sample in samples])
    features = np.stack([sample[2] for sample in samples])
    labels = np.array([sample[3] for sample in samples])
    sides = np.array([sample[4] for sample in samples])
    folds = np.zeros(len(samples), dtype=int)
    for side in "ab":
        folds[sides == side] = blocks(sessions[sides == side])
    predicted = np.empty(len(labels), dtype=object)
    for fold in np.unique(folds):
        test = folds == fold
        scaler, model = fit(features[~test], labels[~test])
        predicted[test] = model.predict(scaler.transform(features[test]))
    return features, labels, predicted


def out_of_fold() -> dict[tuple[str, int], dict]:
    """Field values read from the marks of every gameplay frame, each by a model that did not see its block."""
    values = defaultdict(dict)
    for game, samples in collect().items():
        field_a, field_b = MARKS[game][:2]
        _, _, predicted = cross_validate(samples)
        for (session, frame_id, _, _, side), value in zip(samples, predicted):
            if value != NONE:
                values[(session, frame_id)][field_a if side == "a" else field_b] = int(value)
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=STUDENT_OUTPUT / "marks.npz")
    args = parser.parse_args()
    arrays = {}
    for game, samples in collect().items():
        features, labels, predicted = cross_validate(samples)
        valued = labels != NONE
        right = predicted == labels
        errors = Counter(zip(labels[~right], predicted[~right])).most_common(3)
        print(f"{game}: {right[valued].mean():.1%} of {valued.sum()} teacher values read right, "
              f"{(predicted[valued] == NONE).mean():.1%} read as none; {right[~valued].mean():.1%} of "
              f"{(~valued).sum()} frames without a value left empty; errors {errors}")  # fmt: skip
        scaler, model = fit(features, labels)
        key = game.split()[0].lower()
        arrays |= {f"{key}_mean": scaler.mean_, f"{key}_scale": scaler.scale_, f"{key}_weights": model.coef_,
                   f"{key}_bias": model.intercept_, f"{key}_classes": model.classes_}  # fmt: skip
    np.savez(args.out, **arrays)


if __name__ == "__main__":
    main()
