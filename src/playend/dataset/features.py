"""GRU input features 4.0 of every screenshot, computed from the published rows alone.

features.csv is rebuilt from observations.csv (observation_json and t_s), so anyone can recompute it from the
package. It is compared with the features of the private observations, to show that the pseudonyms and the
relative time leave the model inputs unchanged.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Iterator

from playend.contract.temporal import FeatureStream
from playend.dataset.tables import Session


def nanoseconds(seconds: str) -> int:
    whole, _, fraction = seconds.partition(".")
    return int(whole) * 1_000_000_000 + int(fraction.ljust(9, "0"))


def feature_rows(observations: list[dict]) -> list[dict]:
    stream = FeatureStream()
    rows = []
    for row in observations:
        record = {
            "session_id": row["session_id"],
            "frame_id": row["frame_id"],
            "received_monotonic_ns": nanoseconds(row["t_s"]),
            "observation": json.loads(row["observation_json"]),
        }
        rows.append({"session_id": row["session_id"], "frame_id": row["frame_id"], **stream.step(record)})
    return rows


def private_features(sessions: list[Session]) -> Iterator[dict]:
    stream = FeatureStream()
    for session in sessions:
        for frame in session.frames:
            yield stream.step(
                {
                    "session_id": session.session_id,
                    "frame_id": frame["frame_id"],
                    "received_monotonic_ns": frame["received_monotonic_ns"],
                    "observation": frame["observation"],
                }
            )


def differences(published: list[dict], private: Iterable[dict]) -> Counter:
    """Number of screenshots on which each feature differs between the two computations."""
    changed = Counter()
    for row, features in zip(published, private, strict=True):
        changed.update(name for name, value in features.items() if row[name] != value)
    return changed
