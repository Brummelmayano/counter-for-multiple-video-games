"""Read one capture with the student's OCR: fixed reading boxes first, the detected text of the zones second.

A HUD does not move within a game, so most values are read by recognising a known box directly: on the PlayEnd
frames this is more accurate than detecting the text first (the detector misses small digits, such as the stacked
scores of EA Sports FC) and cheaper on the Pi. The detected text of the zone mosaic (playend.student.rules) fills
what the boxes do not cover. Marks that are not text come from playend.student.marks.
"""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path

import numpy as np
from PIL import Image

from playend.student.ocr import TextReader
from playend.student.rules import read_value

ENLARGE = 3  # a reading box is enlarged before recognition: HUD digits are a few pixels high

# game -> (field, kind, box in capture pixels); boxes placed from where the OCR read the teacher's values
BOXES = {
    "Mortal Kombat 1": [("clock_display", "seconds_or_infinity", (612, 4, 668, 48))],
    "Tekken 8": [("clock_display", "seconds", (610, 25, 680, 85))],
    "Naruto Storm Connections": [("clock_display", "seconds", (600, 65, 700, 128))],
    "J-Stars Victory VS+": [("clock_display", "seconds", (1070, 620, 1200, 668))],
    "EA Sports UFC 5": [
        ("clock_display", "clock", (612, 70, 668, 99)),
        ("period_number", "round", (612, 44, 650, 69)),
    ],
}
# Call of Duty: Warzone shows its counters in slots under icons: squads left, players left, then eliminations or
# planes. Without the third counter, everything moves one slot to the right, so the slots are found from the icons.
WARZONE_ICONS = [(1176, 18, 1198, 34), (1209, 18, 1231, 34), (1242, 18, 1264, 34)]
WARZONE_DIGITS = [(1172, 35, 1203, 50), (1205, 35, 1237, 50), (1238, 35, 1272, 50)]
WARZONE_ENLARGE = 5  # its digits are about seven pixels high
TEMPLATES = Path(__file__).parent / "templates"
# EA Sports FC, in its usual scoreboard (team codes stacked, small scores on their right, clock below)
FOOTBALL_TEAMS = [("participant_a", (104, 39, 152, 59)), ("participant_b", (104, 55, 152, 75))]
FOOTBALL_SCORES = [("score_a", (170, 41, 194, 57)), ("score_b", (170, 57, 194, 73))]


def recognise_box(reader: TextReader, frame: Image.Image, box: tuple[int, int, int, int], scale: int = ENLARGE) -> str:
    crop = frame.crop(box)
    text, _ = reader.recognise(crop.resize((crop.width * scale, crop.height * scale), Image.LANCZOS))
    return text


def brightness(image: Image.Image) -> np.ndarray:
    """The strongest channel: a red icon is as bright as a white one."""
    return np.asarray(image.convert("RGB"), dtype=float).max(axis=2)


@cache
def template(name: str) -> np.ndarray:
    return brightness(Image.open(TEMPLATES / f"{name}.png"))


def similarity(first: np.ndarray, second: np.ndarray) -> float:
    first, second = first - first.mean(), second - second.mean()
    norm = np.sqrt((first * first).sum() * (second * second).sum())
    return float((first * second).sum() / norm) if norm else 0.0


def warzone_counters(reader: TextReader, frame: Image.Image) -> dict:
    """Squads and players left, read under their icons; a value that cannot be right is left unread (None)."""
    icons = [brightness(frame.crop(box)) for box in WARZONE_ICONS]
    squad, player = template("warzone_squad"), template("warzone_player")
    shifted = similarity(icons[1], squad) + similarity(icons[2], player) > similarity(icons[0], squad) + similarity(
        icons[1], player
    )
    slot = 1 if shifted else 0
    teams, players = (
        read_value("count", [recognise_box(reader, frame, WARZONE_DIGITS[index], WARZONE_ENLARGE)])
        for index in (slot, slot + 1)
    )
    if teams is not None and players is not None and teams > players:
        players = None  # fewer players than squads: one of the two was misread
    return {"teams_remaining": teams, "players_remaining": players}


def read_boxes(reader: TextReader, frame: Image.Image, family: str) -> dict:
    fields = {}
    for field, kind, box in BOXES.get(family, []):
        value = read_value(kind, [recognise_box(reader, frame, box)])
        if value is not None:
            fields[field] = value
    if family == "Call of Duty: Warzone":
        fields |= warzone_counters(reader, frame)  # an unread value stays None, over what the zone text gave
    if family == "EA Sports FC":
        teams = {field: recognise_box(reader, frame, box) for field, box in FOOTBALL_TEAMS}
        if all(re.fullmatch(r"[A-Z]{3}", text) for text in teams.values()):
            fields |= teams
            for field, box in FOOTBALL_SCORES:
                text = recognise_box(reader, frame, box)
                if re.fullmatch(r"[\dOoIl|SsBZ]{1,2}", text):
                    value = read_value("small_count", [text]) if len(text) == 1 else read_value("count", [text])
                    if value is not None and value <= 20:
                        fields[field] = value
    return fields


def merge(boxes: dict, detected: dict, marks: dict) -> dict:
    """Box readings win over detected text; marks fill the rounds and lives no text gives."""
    return detected | marks | boxes
