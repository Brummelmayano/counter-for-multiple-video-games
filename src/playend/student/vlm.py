"""VLM reader of the student: LFM2.5-VL-450M on the HUD mosaic, its answer held to one line per field by a grammar.

The grammar (GBNF, llama.cpp) is written from the field list of each game, so the model can only answer
`field: value` or `field: null`, in the order asked; parse() turns the lines into the same fields as the OCR student.
Grammar-constrained decoding gives the structure without fine-tuning (Geng et al., EMNLP 2023); the LoRA adapter is
compared with and without it. The mosaic adds the boxes of the marks to the zones of the game, so the model sees what
the OCR student's mark readers see.
"""

from __future__ import annotations

import re

from PIL import Image

from playend.student.zones import LAYOUTS, MARKS, Zone, mosaic

# game -> layout shown, then (field, kind, what to read) in the order of the answer
FIELDS = {
    "EA Sports FC": ("default", [
        ("clock_display", "clock", "match clock"),
        ("participant_a", "code", "first team code"),
        ("score_a", "goals", "goals of the first team"),
        ("score_b", "goals", "goals of the second team"),
        ("participant_b", "code", "second team code"),
    ]),
    "Mortal Kombat 1": ("rounds", [
        ("clock_display", "seconds_or_infinity", "round timer"),
        ("score_a", "rounds", "rounds won by the left fighter (lit round markers)"),
        ("score_b", "rounds", "rounds won by the right fighter (lit round markers)"),
    ]),
    "Tekken 8": ("rounds", [
        ("clock_display", "seconds", "round timer"),
        ("score_a", "rounds", "rounds won by the left fighter (lit round markers)"),
        ("score_b", "rounds", "rounds won by the right fighter (lit round markers)"),
        ("series_a", "wins", "WINS number on the left"),
        ("series_b", "wins", "WINS number on the right"),
    ]),
    "Naruto Storm Connections": ("default", [
        ("clock_display", "seconds", "round timer"),
        ("score_a", "rounds", "rounds won by the left fighter (lit markers)"),
        ("score_b", "rounds", "rounds won by the right fighter (lit markers)"),
        ("participant_a", "name", "left fighter name"),
        ("participant_b", "name", "right fighter name"),
    ]),
    "Demon Slayer": ("default", [
        ("clock_display", "seconds", "round timer"),
        ("score_a", "rounds", "rounds won on the left (lit diamonds)"),
        ("score_b", "rounds", "rounds won on the right (lit diamonds)"),
    ]),
    "J-Stars Victory VS+": ("hud", [
        ("clock_display", "seconds", "timer"),
        ("participant_a", "name", "fighter name"),
    ]),
    "EA Sports UFC 5": ("names", [
        ("clock_display", "clock", "round clock"),
        ("period_number", "round_number", "round number"),
        ("participant_a", "name", "left fighter name"),
        ("participant_b", "name", "right fighter name"),
    ]),
    "Dragon Ball FighterZ": ("default", [
        ("clock_display", "seconds_or_infinity", "timer"),
        ("participant_a", "name", "left fighter name"),
        ("participant_b", "name", "right fighter name"),
    ]),
    "Dragon Ball Sparking! ZERO": ("split", [
        ("lives_a", "rounds", "remaining health bars of the left fighter (lit blocks)"),
        ("lives_b", "rounds", "remaining health bars of the right fighter (lit blocks)"),
    ]),
    "Call of Duty: Warzone": ("counters", [
        ("teams_remaining", "count", "teams left"),
        ("players_remaining", "count", "players left"),
        ("period_number", "round_number", "circle number"),
    ]),
    "Fortnite": ("multi", [("players_remaining", "count", "players left")]),
    "Beach Buggy Racing 2": ("3", [("progress_current", "round_number", "lap number")]),
}  # fmt: skip

# GBNF of each kind of value
VALUES = {
    "clock": '[0-9] [0-9]? [0-9]? ":" [0-9] [0-9]',
    "seconds": "[0-9] [0-9]? [0-9]?",
    "seconds_or_infinity": '[0-9] [0-9]? [0-9]? | "∞"',
    "goals": "[0-9] [0-9]?",
    "rounds": "[0-9]",
    "round_number": "[0-9] [0-9]?",
    "wins": "[0-9] [0-9]? [0-9]?",
    "count": "[0-9] [0-9]? [0-9]?",
    "code": "[A-Z] [A-Z] [A-Z] [A-Z]?",
    "name": "[A-Za-zÀ-ÖØ-öø-ſ] [A-Za-z0-9À-ÖØ-öø-ſ .()'-]{0,30}",
}


def vlm_mosaic(frame: Image.Image, family: str) -> Image.Image:
    layout, _ = FIELDS[family]
    zones = LAYOUTS[family][layout]
    if family in MARKS:
        zones = zones + tuple(Zone(box, 2.0) for box in MARKS[family][2:])
    return mosaic(frame, zones).image


def prompt(family: str) -> str:
    _, fields = FIELDS[family]
    lines = "\n".join(f"{field}: {what}" for field, _, what in fields)
    return (f"This image shows parts of the screen of the video game {family}. Read these values and answer one line "
            f"per value, in this order, with null when a value is not visible:\n{lines}")  # fmt: skip


def grammar(family: str) -> str:
    _, fields = FIELDS[family]
    rules = [f"root ::= {' '.join(f'line{i}' for i in range(len(fields)))}"]
    for i, (field, kind, _) in enumerate(fields):
        rules.append(f'line{i} ::= "{field}: " ( {VALUES[kind]} | "null" ) "\\n"')
    return "\n".join(rules) + "\n"


def parse(family: str, answer: str) -> dict:
    """Field values of an answer; what is null or not in the format of its field is left out."""
    _, fields = FIELDS[family]
    found = {}
    for field, kind, _ in fields:
        match = re.search(rf"^{field}: (.*)$", answer, re.MULTILINE)
        text = match.group(1).strip() if match else ""
        if not text or text == "null":
            continue
        if kind == "clock":
            clock = re.fullmatch(r"(\d{1,3}):(\d{2})", text)
            if clock and int(clock.group(2)) < 60:
                found[field] = f"{int(clock.group(1))}:{clock.group(2)}"
        elif kind in ("seconds", "seconds_or_infinity"):
            if text == "∞" or re.fullmatch(r"\d{1,3}", text):
                found[field] = text
        elif kind == "code":
            if re.fullmatch(r"[A-Z]{3,4}", text):
                found[field] = text
        elif kind == "name":
            found[field] = text
        elif re.fullmatch(r"\d{1,3}", text):
            found[field] = int(text)
    return found
