"""Replace real player names with stable pseudonyms (player_001, player_002...) before anything is published.

The names come from a private list kept beside the data, never from the code. A name is matched case-insensitively
as a whole token, longest name first, so a clan-tagged name wins over a shorter name inside it. Spellings that differ
only by case (a name written in capitals in a kill feed) get the same pseudonym. Pseudonyms are numbered in order of
first appearance, so the same data always gives the same pseudonyms.
"""

from __future__ import annotations

import re
from pathlib import Path

from playend.common.paths import DATASET

NAMES = DATASET / "real_player_names.txt"
PSEUDONYM = re.compile(r"player_\d{3}")


def read_names(path: Path = NAMES) -> list[str]:
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def name_pattern(names: list[str]) -> re.Pattern:
    alternatives = sorted(names, key=len, reverse=True)
    return re.compile("|".join(rf"(?<!\w){re.escape(name)}(?!\w)" for name in alternatives), re.IGNORECASE)


class Pseudonyms:
    def __init__(self, names: list[str]):
        self.pattern = name_pattern(names)
        self.assigned: dict[str, str] = {}

    def _replace(self, match: re.Match) -> str:
        key = match.group(0).casefold()
        if key not in self.assigned:
            self.assigned[key] = f"player_{len(self.assigned) + 1:03d}"
        return self.assigned[key]

    def text(self, value: str) -> str:
        return self.pattern.sub(self._replace, value)

    def value(self, obj):
        """The same JSON value with every string pseudonymized, at any depth."""
        if isinstance(obj, str):
            return self.text(obj)
        if isinstance(obj, list):
            return [self.value(item) for item in obj]
        if isinstance(obj, dict):
            return {key: self.value(item) for key, item in obj.items()}
        return obj
