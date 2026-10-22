"""Compare a fighter's portrait between two captures of a fighting game that shows no score.

In Dragon Ball Sparking! ZERO, the health bars of a fighter never come back within a fight. When they go up, either a
teammate came in, with another portrait, or the fight was restarted with "Réessayer", with the same portrait. The
portrait is compared on the capture itself, in a fixed zone of the HUD, as the student's OCR reads its own zones: no
name is read. On PlayEnd's 103 rises of the bars, the two restarts differ by 8 and 16, every teammate by 29 or more
(decision of the author, 2026-10-14, data/validation/explication_dbz_2026-10-14).
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from playend.annotation.lots import source_rows
from playend.common.paths import resolve

WIDTH, HEIGHT = 1280, 720  # the zones are given for a capture of this size
ZONES = {"Dragon Ball Sparking! ZERO": {"a": (30, 5, 120, 105), "b": (1160, 5, 1250, 105)}}
THUMBNAIL = (24, 26)
SAME_PORTRAIT = 22  # mean absolute grey difference between two thumbnails


def thumbnail(image: Image.Image, zone: tuple[int, int, int, int]) -> np.ndarray:
    scale_x, scale_y = image.width / WIDTH, image.height / HEIGHT
    left, top, right, bottom = zone
    box = (round(left * scale_x), round(top * scale_y), round(right * scale_x), round(bottom * scale_y))
    return np.asarray(image.crop(box).convert("L").resize(THUMBNAIL), dtype=float)


def same(first: np.ndarray, second: np.ndarray) -> bool:
    return float(np.abs(first - second).mean()) < SAME_PORTRAIT


class SessionPortraits:
    """The portrait thumbnails of one recorded session, read from its captures when first asked for."""

    def __init__(self, session: str):
        self.rows = source_rows(session)
        self.cache: dict[tuple[int, str], np.ndarray] = {}

    def __call__(self, frame: int, family: str, side: str) -> np.ndarray | None:
        zone = ZONES.get(family, {}).get(side)
        if zone is None or frame not in self.rows:
            return None
        if (frame, side) not in self.cache:
            with Image.open(resolve(self.rows[frame]["source_path"])) as image:
                self.cache[(frame, side)] = thumbnail(image, zone)
        return self.cache[(frame, side)]
