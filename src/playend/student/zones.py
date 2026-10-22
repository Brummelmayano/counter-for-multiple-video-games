"""Where the student looks: the HUD zones of each game, cut from the 1280x720 capture and stacked in one mosaic.

Boxes are [x0, y0, x1, y1] in pixels of the capture, with the enlargement applied in the mosaic. They come from the
measurements of 2026-10-06 (archive/student-measurements-2026-10/comparaison/roi.json); Beach Buggy Racing 2 adds the
two- and four-player layouts of the teacher's zoom presets. Mission games have no zone: nothing on their screen ends
a game.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

GAP = 8  # grey band between two zones of a mosaic
BACKGROUND = (40, 40, 40)


@dataclass(frozen=True)
class Zone:
    box: tuple[int, int, int, int]
    zoom: float


def zones(*boxes: tuple[int, int, int, int, float]) -> tuple[Zone, ...]:
    return tuple(Zone((x0, y0, x1, y1), zoom) for x0, y0, x1, y1, zoom in boxes)


BEACH_BUGGY_LAP = (500, 335, 780, 392, 1.2)
LAYOUTS: dict[str, dict[str, tuple[Zone, ...]]] = {
    "Beach Buggy Racing 2": {
        "3": zones((140, 30, 290, 112, 1.2), (20, 385, 170, 455, 1.2), (660, 385, 810, 455, 1.2), BEACH_BUGGY_LAP),
        "4": zones(
            (20, 25, 170, 95, 1.2),
            (660, 25, 810, 95, 1.2),
            (20, 385, 170, 455, 1.2),
            (660, 385, 810, 455, 1.2),
            BEACH_BUGGY_LAP,
        ),  # fmt: skip
        "2": zones((140, 30, 290, 112, 1.2), (140, 390, 290, 472, 1.2), BEACH_BUGGY_LAP),
    },
    "Brawlhalla": {"default": zones((1000, 15, 1280, 100, 1.5))},
    "Call of Duty: Warzone": {"counters": zones((1095, 10, 1278, 54, 1.8), (20, 195, 130, 230, 1.8))},
    "Demon Slayer": {"default": zones((500, 30, 780, 115, 1.0))},
    "Dragon Ball FighterZ": {
        "default": zones((140, 10, 600, 45, 1.0), (570, 15, 710, 105, 1.0), (700, 10, 1140, 45, 1.0)),
    },
    "Dragon Ball Sparking! ZERO": {"split": zones((20, 100, 140, 190, 1.5), (1150, 100, 1270, 190, 1.5))},
    "EA Sports FC": {"default": zones((0, 10, 440, 110, 1.5))},
    "EA Sports UFC 5": {"names": zones((55, 30, 380, 58, 1.3), (560, 28, 720, 98, 1.3), (900, 30, 1225, 58, 1.3))},
    "Fortnite": {
        "split": zones((560, 0, 850, 160, 1.3), (1000, 360, 1290, 520, 1.3)),
        "solo": zones((990, 30, 1110, 150, 1.6)),
        "multi": zones((765, 0, 850, 115, 2.0), (1080, 360, 1165, 475, 2.0), (995, 20, 1105, 145, 1.4)),
        "og": zones((805, 145, 960, 175, 2.2), (1125, 505, 1280, 535, 2.2)),
    },
    "J-Stars Victory VS+": {
        "hud": zones(
            (115, 45, 540, 105, 0.9),
            (740, 45, 1165, 105, 0.9),
            (90, 585, 175, 665, 0.9),
            (280, 630, 560, 665, 0.9),
            (900, 620, 1215, 675, 0.9),
        ),  # fmt: skip
    },
    "Mortal Kombat 1": {"rounds": zones((555, 0, 730, 70, 2.0))},
    "Naruto Storm Connections": {
        "default": zones((150, 30, 560, 80, 1.0), (580, 65, 710, 130, 1.0), (720, 30, 1130, 80, 1.0)),
    },
    "Tekken 8": {"rounds": zones((30, 596, 290, 666, 0.8), (480, 10, 850, 95, 1.2), (990, 596, 1250, 666, 0.8))},
}


@dataclass(frozen=True)
class Mosaic:
    image: Image.Image
    zones: tuple[Zone, ...]
    tops: tuple[int, ...]  # first mosaic row of each zone

    def to_frame(self, box: tuple[float, float, float, float]) -> tuple[int, tuple[float, float, float, float]]:
        """The zone holding the centre of a mosaic box, and the box in capture pixels."""
        centre = (box[1] + box[3]) / 2
        index = max((i for i, top in enumerate(self.tops) if top <= centre), default=0)
        zone, top = self.zones[index], self.tops[index]
        x0, y0 = zone.box[:2]
        return index, (x0 + box[0] / zone.zoom, y0 + (box[1] - top) / zone.zoom,
                       x0 + box[2] / zone.zoom, y0 + (box[3] - top) / zone.zoom)  # fmt: skip


def mosaic(frame: Image.Image, layout: tuple[Zone, ...]) -> Mosaic:
    pieces = []
    for zone in layout:
        x0, y0, x1, y1 = zone.box
        piece = frame.crop((x0, y0, min(x1, frame.width), y1))
        pieces.append(piece.resize((round(piece.width * zone.zoom), round(piece.height * zone.zoom)), Image.LANCZOS))
    canvas = Image.new("RGB", (max(p.width for p in pieces), sum(p.height for p in pieces) + GAP * (len(pieces) - 1)),
                       BACKGROUND)  # fmt: skip
    tops, y = [], 0
    for piece in pieces:
        canvas.paste(piece, (0, y))
        tops.append(y)
        y += piece.height + GAP
    return Mosaic(canvas, layout, tuple(tops))


# Marks that are not text: playend.student.marks learns their values from the pixels of these boxes.
NONE = "none"
SIZE = (16, 6)  # pixels kept from each box, width by height

# game -> (field of side A, field of side B, box of side A, box of side B), in capture pixels
MARKS = {
    "Mortal Kombat 1": ("score_a", "score_b", (574, 4, 616, 24), (690, 4, 732, 24)),
    "Tekken 8": ("score_a", "score_b", (498, 22, 552, 50), (728, 22, 782, 50)),
    "Naruto Storm Connections": ("score_a", "score_b", (562, 118, 632, 146), (658, 118, 714, 146)),
    "Demon Slayer": ("score_a", "score_b", (552, 86, 602, 110), (678, 86, 728, 110)),
    "Dragon Ball Sparking! ZERO": ("lives_a", "lives_b", (84, 40, 192, 78), (1088, 40, 1196, 78)),
}


def pixels(frame: Image.Image, box: tuple[int, int, int, int]) -> np.ndarray:
    return np.asarray(frame.crop(box).resize(SIZE, Image.BOX), dtype=np.float32).ravel() / 255.0
