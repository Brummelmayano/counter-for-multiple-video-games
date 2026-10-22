"""The observations a start detector reads: the teacher's (a PlayEnd package) or the student's (a package written by
playend.student.package), each capture with its 262 features, the folds of the package and the reference games."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from playend.common.games import game_family
from playend.counting.starts import package_observations, read, reference_units
from playend.training.data import Sequence, load

# Screens that say something even without a value: where a game ends or a new one is being set up.
DECISIVE = {
    "result",
    "scoreboard",
    "podium",
    "menu",
    "loading",
    "character_select",
    "team_select",
    "race_grid",
    "pause",
}


@dataclass
class Session:
    sequence: Sequence  # features, end labels, folds and times, as the end detectors read them
    observations: list[dict]  # contract 2.1, frame 1 first
    units: list[dict]  # reference games of data/boundaries, or of the units table of the package
    readable: np.ndarray  # a gameplay capture whose values decide something: where a start can be read
    informative: np.ndarray  # readable, or a decisive screen

    @property
    def name(self) -> str:
        return self.sequence.session

    @property
    def fold(self) -> int:
        return self.sequence.fold

    @property
    def frames(self) -> list[int]:
        return list(range(1, len(self.observations) + 1))


@dataclass
class Prepared:
    """A source ready for the protocol: its sessions, the rule state of each capture and the rule starts."""

    sessions: dict[str, Session]
    state: dict[str, np.ndarray]
    names: list[str]
    rule_starts: dict[str, list]


def readability(observations: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    readable, informative = [], []
    for obs in observations:
        state = obs["state"]
        gameplay = state["screen_type"] == "gameplay" and state["phase"] != "post_game"
        kind = read(obs, game_family(obs["game"]["title"])).kind if gameplay else None
        readable.append(kind is not None)
        informative.append(kind is not None or state["screen_type"] in DECISIVE or state["phase"] == "post_game")
    return np.array(readable), np.array(informative)


def load_source(package: Path) -> dict[str, Session]:
    corpus = load(package)
    observations = package_observations(package)
    sessions = {}
    for name, sequence in corpus.sequences.items():
        frames = observations[name]
        ordered = [frames[frame] for frame in range(1, len(frames) + 1)]
        readable, informative = readability(ordered)
        sessions[name] = Session(sequence, ordered, reference_units(name, package), readable, informative)
    return sessions


def start_labels(session: Session, dilation: int) -> np.ndarray:
    """1 on the first `dilation` readable captures of each game, from its reference start (label dilation)."""
    target = np.zeros(len(session.observations), dtype=np.int8)
    for unit in session.units:
        rows = [frame - 1 for frame in range(unit["start_established_at"], unit["last_frame"] + 1)]
        rows = [row for row in rows if session.readable[row]][:dilation]
        target[rows] = 1
    return target
