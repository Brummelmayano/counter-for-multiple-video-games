"""The counting rules decided by the user, read from docs/decisions/regles_facturation.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from playend.common.paths import COUNTING_RULES


@dataclass(frozen=True)
class Rules:
    version: str
    quick_restart_s: dict[str, int]  # by game type as the VLM reads it; a shorter game does not count
    gap_s: int  # a longer interval between two captures is time without an image, shown on its line

    def threshold(self, game_type: str | None) -> int:
        # A type missing from the table gets the longest threshold: a doubt goes to the client.
        return self.quick_restart_s.get(game_type, max(self.quick_restart_s.values()))


def load(path: Path = COUNTING_RULES) -> Rules:
    data = json.loads(path.read_text(encoding="utf-8"))
    thresholds = data["relance_rapide_non_facturee"]["seuil_secondes_par_genre"]
    return Rules(
        version=data["version"],
        quick_restart_s={kind: int(seconds) for kind, seconds in thresholds.items()},
        gap_s=int(data["trou_de_capture"]["seuil_secondes"]),
    )
