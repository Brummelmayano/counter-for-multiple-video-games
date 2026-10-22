"""Apply the student's trained classifier, mark readers and end detector with NumPy alone, as the Raspberry Pi does.

classify.py and marks.py train with scikit-learn, the GRU with PyTorch (playend.training); all are saved as plain
arrays, which this module only multiplies.
"""

from __future__ import annotations

from collections import Counter, deque
from pathlib import Path

import numpy as np
from PIL import Image

from playend.common.paths import STUDENT_OUTPUT
from playend.student.zones import MARKS, NONE, pixels

VOTE = 5  # captures in the causal vote on the game


def softmax_label(scores: np.ndarray, classes: np.ndarray) -> tuple[str, float]:
    if scores.shape[-1] == 1:  # a two-class logistic regression keeps one column
        probability = 1 / (1 + np.exp(-scores[0]))
        return (classes[1], probability) if probability >= 0.5 else (classes[0], 1 - probability)
    exp = np.exp(scores - scores.max())
    probabilities = exp / exp.sum()
    return classes[probabilities.argmax()], float(probabilities.max())


class Classifier:
    def __init__(self, path: Path = STUDENT_OUTPUT / "classifier.npz"):
        self.arrays = dict(np.load(path, allow_pickle=True))
        self.recent: deque = deque(maxlen=VOTE)

    def label(self, target: str, features: np.ndarray) -> tuple[str, float]:
        a = self.arrays
        projected = ((features - a[f"{target}_mean"]) / a[f"{target}_scale"] - a[f"{target}_pca_mean"]) @ a[
            f"{target}_pca"
        ].T
        return softmax_label(projected @ a[f"{target}_weights"].T + a[f"{target}_bias"], a[f"{target}_classes"])

    def game(self, features: np.ndarray, new_session: bool = False) -> str:
        """The game, by a vote over the last captures weighted by confidence."""
        if new_session:
            self.recent.clear()
        self.recent.append(self.label("game", features))
        return self.vote()

    def vote(self) -> str:
        votes = Counter()
        for name, confidence in self.recent:
            votes[name] += confidence
        return votes.most_common(1)[0][0]


class Marks:
    def __init__(self, path: Path = STUDENT_OUTPUT / "marks.npz"):
        self.arrays = dict(np.load(path, allow_pickle=True))

    def read(self, family: str, frame: Image.Image) -> dict:
        if family not in MARKS:
            return {}
        field_a, field_b, box_a, box_b = MARKS[family]
        key = family.split()[0].lower()
        a = self.arrays
        fields = {}
        for field, box in ((field_a, box_a), (field_b, box_b)):
            scaled = (pixels(frame, box) - a[f"{key}_mean"]) / a[f"{key}_scale"]
            value, _ = softmax_label(scaled @ a[f"{key}_weights"].T + a[f"{key}_bias"], a[f"{key}_classes"])
            if value != NONE:
                fields[field] = int(value)
        return fields


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-values))


class EndDetector:
    """The GRU of playend.training.gru, one capture at a time: the probability of an end and the billing mode.

    Same equations as torch.nn.GRU (gates in the order reset, update, new), in float32. The arrays are written by
    playend.student.loop prepare.
    """

    def __init__(self, path: Path):
        arrays = dict(np.load(path, allow_pickle=False))
        self.input_weights, self.input_bias = arrays["weight_ih"], arrays["bias_ih"]
        self.state_weights, self.state_bias = arrays["weight_hh"], arrays["bias_hh"]
        self.end_weights, self.end_bias = arrays["end_weight"], arrays["end_bias"]
        self.billing_weights, self.billing_bias = arrays["billing_weight"], arrays["billing_bias"]
        self.columns = [str(name) for name in arrays["columns"]]
        self.threshold = float(arrays["threshold"])
        self.state = np.zeros(self.state_weights.shape[1], dtype=np.float32)

    def step(self, features: np.ndarray) -> tuple[float, int]:
        reset_x, update_x, new_x = np.split(self.input_weights @ features + self.input_bias, 3)
        reset_h, update_h, new_h = np.split(self.state_weights @ self.state + self.state_bias, 3)
        reset, update = sigmoid(reset_x + reset_h), sigmoid(update_x + update_h)
        new = np.tanh(new_x + reset * new_h)
        self.state = (1 - update) * new + update * self.state
        end = sigmoid(self.end_weights @ self.state + self.end_bias)[0]
        return float(end), int(np.argmax(self.billing_weights @ self.state + self.billing_bias))
