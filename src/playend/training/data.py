"""Read a PlayEnd package, the folder published on Zenodo, into one sequence per capture session."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from playend.common.files import sha256
from playend.dataset.csvfiles import read_csv

BILLING_MODES = ("per_game", "time_based", "not_billed")
PACKAGE_FILES = ("data/observations.csv", "data/units.csv", "data/splits.csv")
# Version 1.0 on Zenodo names the feature files with their encoding version; later exports do not.
FEATURES = ("data/features.csv", "data/features_v4.csv")
SPECS = ("dictionary/feature_spec.json", "dictionary/feature_spec_v4.json")


@dataclass
class Sequence:
    session: str
    fold: int
    t: np.ndarray
    x: np.ndarray
    end: np.ndarray  # 1 when a game ended in the interval (previous screenshot, this one]
    usable: np.ndarray  # False on the first screenshot and on the intervals masked as uncertain
    billing: np.ndarray
    family: list[str]
    ended_family: dict[int, str] = field(default_factory=dict)  # row of an end -> family of the game that ended
    readable: dict[str, np.ndarray] = field(default_factory=dict)  # a few plain columns, for the hand-written rules

    def __len__(self) -> int:
        return len(self.t)

    @property
    def hours(self) -> float:
        return float(self.t[-1] - self.t[0]) / 3600


@dataclass
class Corpus:
    sequences: dict[str, Sequence]
    feature_names: list[str]
    feature_sha256: str
    digest: dict[str, str]

    def select(self, sessions) -> list[Sequence]:
        return [self.sequences[session] for session in sessions]


def number(value: str) -> float:
    return float(value) if value != "" else np.nan


def first_existing(package: Path, names: tuple[str, ...]) -> str | None:
    return next((name for name in names if (package / name).exists()), None)


def load(package: Path) -> Corpus:
    package = Path(package)
    features_file, spec_file = first_existing(package, FEATURES), first_existing(package, SPECS)
    missing = [name for name in PACKAGE_FILES if not (package / name).exists()]
    if missing or features_file is None or spec_file is None:
        raise SystemExit(f"{package} is not a PlayEnd package: features, specification or {missing} missing")
    spec = json.loads((package / spec_file).read_text(encoding="utf-8"))
    names = spec["feature_names"]
    folds = {row["session_id"]: int(row["fold"]) for row in read_csv(package / "data" / "splits.csv")[1]}
    unit_family = {
        (row["session_id"], row["unit_id"]): row["game_family"] for row in read_csv(package / "data" / "units.csv")[1]
    }

    features: dict[str, list[list[float]]] = {}
    with (package / features_file).open(newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream)
        if next(reader)[2:] != names:
            raise SystemExit(f"{features_file} columns differ from {spec_file}")
        for row in reader:
            features.setdefault(row[0], []).append([float(value) for value in row[2:]])

    observations: dict[str, list[dict]] = {}
    for row in read_csv(package / "data" / "observations.csv")[1]:
        observations.setdefault(row["session_id"], []).append(row)

    sequences = {}
    for session, rows in sorted(observations.items()):
        if [int(row["frame_id"]) for row in rows] != list(range(1, len(rows) + 1)):
            raise SystemExit(f"{session}: rows are not frames 1..N in order")
        ended = {
            index: unit_family.get((session, row["ended_unit_id"]), row["game_family"])
            for index, row in enumerate(rows)
            if row["ended_unit_id"]
        }
        sequences[session] = Sequence(
            session=session,
            fold=folds[session],
            t=np.array([float(row["t_s"]) for row in rows]),
            x=np.array(features[session], dtype=np.float32),
            end=np.array([row["unit_end_boundary"] == "1" for row in rows], dtype=np.int8),
            usable=np.array([row["boundary_applicable"] == "true" for row in rows]),
            billing=np.array([BILLING_MODES.index(row["billing_mode"]) for row in rows], dtype=np.int64),
            family=[row["game_family"] for row in rows],
            ended_family=ended,
            readable={
                "score_a": np.array([number(row["score_a"]) for row in rows]),
                "score_b": np.array([number(row["score_b"]) for row in rows]),
                "players": np.array([number(row["players_remaining"]) for row in rows]),
                "phase": np.array([row["phase"] for row in rows]),
            },
        )
        if len(sequences[session].x) != len(rows):
            raise SystemExit(f"{session}: features.csv and observations.csv have different rows")
    # Keyed by role, not by file name, so that both namings of the same data give the same digest.
    digest = {name: sha256(package / name) for name in PACKAGE_FILES} | {"features": sha256(package / features_file)}
    return Corpus(sequences=sequences, feature_names=names, feature_sha256=spec["feature_sha256"], digest=digest)
