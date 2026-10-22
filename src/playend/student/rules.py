"""Reading rules of the student: where each value stands in a game's HUD, and how its text becomes a value.

A slot is a part of a zone, in capture pixels, holding one value of a known kind. Positions come from where the OCR
found each kind of text over all gameplay frames (build/student/ocr/); a HUD does not move within a game. What a
rule cannot read stays None, as the teacher writes null when a value is not readable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DIGIT_LOOKALIKES = str.maketrans({"O": "0", "o": "0", "D": "0", "I": "1", "l": "1", "|": "1", "i": "1", "S": "5",
                                  "s": "5", "Z": "2", "z": "2", "B": "8"})  # fmt: skip
CIRCLED = {chr(0x2460 + n): str(n + 1) for n in range(9)}  # ① to ⑨, the Warzone circle number
CLOCK = re.compile(r"(\d{1,3})\s*[:.;]\s*(\d{2})")
INFINITY_AS_EIGHT = "∞"  # the infinity sign of training modes is read as a lone 8


@dataclass(frozen=True)
class Slot:
    field: str
    kind: str
    zone: int
    x: tuple[int, int]
    y: tuple[int, int]


def slot(field, kind, zone, x0, x1, y0, y1):
    return Slot(field, kind, zone, (x0, x1), (y0, y1))


SLOTS: dict[str, tuple[Slot, ...]] = {
    "Beach Buggy Racing 2": (slot("progress_current", "lap", -1, 520, 720, 330, 395),),
    "Call of Duty: Warzone": (
        slot("teams_remaining", "count", 0, 1160, 1203, 22, 58),
        slot("players_remaining", "count", 0, 1203, 1245, 22, 58),
        slot("period_number", "circle", 1, 15, 55, 198, 235),
    ),
    "Demon Slayer": (slot("clock_display", "seconds", 0, 560, 720, 30, 115),),
    "Dragon Ball FighterZ": (
        slot("clock_display", "seconds_or_infinity", 1, 580, 700, 15, 105),
        slot("participant_a", "name", 0, 140, 600, 5, 45),
        slot("participant_b", "name", 2, 700, 1140, 5, 45),
    ),
    "Dragon Ball Sparking! ZERO": (
        slot("lives_a", "small_count", 0, 20, 110, 105, 185),
        slot("lives_b", "small_count", 1, 1160, 1270, 105, 185),
    ),
    "EA Sports FC": (slot("scoreboard", "football", 0, 0, 440, 10, 110),),
    "EA Sports UFC 5": (
        slot("clock_display", "clock", 1, 590, 700, 65, 98),
        slot("period_number", "round", 1, 600, 680, 42, 72),
        slot("participant_a", "name", 0, 55, 380, 28, 60),
        slot("participant_b", "name", 2, 900, 1225, 28, 60),
    ),
    "Fortnite": (slot("players_remaining", "fortnite_players", 0, 0, 1280, 0, 720),),
    "J-Stars Victory VS+": (
        slot("clock_display", "seconds", 4, 1040, 1215, 620, 675),
        slot("participant_a", "name", 3, 280, 520, 625, 670),
    ),
    "Mortal Kombat 1": (slot("clock_display", "seconds_or_infinity", 0, 600, 685, 15, 65),),
    "Naruto Storm Connections": (
        slot("clock_display", "seconds", 1, 580, 710, 65, 130),
        slot("participant_a", "name", 0, 150, 560, 30, 80),
        slot("participant_b", "name", 2, 720, 1130, 30, 80),
    ),
    "Tekken 8": (
        slot("clock_display", "seconds", 1, 600, 730, 20, 100),
        slot("series_a", "wins", 0, 30, 290, 600, 666),
        slot("series_b", "wins", 2, 990, 1250, 600, 666),
    ),
}

# Fortnite: where the players-left number stands in each screen layout (centre of the text, capture pixels).
FORTNITE_PLAYERS = {
    "solo": [(1020, 1062, 70, 96)],
    "multi": [(1020, 1062, 70, 96), (780, 822, 48, 74), (1100, 1142, 408, 434)],
    "split": [(780, 822, 48, 74), (1100, 1142, 408, 434)],
}
# Split screen with a portrait beside each view (layout "og"): the two views show the same count under their maps.
# Elsewhere other numbers stand there, so the count is kept only when both views give it.
FORTNITE_SPLIT_PORTRAITS = [(860, 900, 148, 175), (1180, 1220, 510, 535)]


def similarity(left: str, right: str) -> float:
    """1 - normalised Levenshtein distance."""
    if not left or not right:
        return 0.0
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (a != b)))
        previous = current
    return 1 - previous[-1] / max(len(left), len(right))


def digits(text: str) -> str:
    return re.sub(r"\D", "", text.translate(DIGIT_LOOKALIKES))


def as_int(text: str, low: int, high: int) -> int | None:
    found = digits(text)
    if found and low <= int(found) <= high:
        return int(found)
    return None


def read_value(kind: str, texts: list[str]):
    """The value of one slot from the texts found in it, in reading order; None when nothing fits."""
    joined = " ".join(texts)
    if kind == "clock":
        match = CLOCK.search(joined)
        if match and int(match.group(2)) < 60:
            return f"{int(match.group(1))}:{match.group(2)}"
    elif kind in ("seconds", "seconds_or_infinity"):
        if kind == "seconds_or_infinity" and re.fullmatch(r"[Oo0]?8|∞|[Oo]{2}", joined.strip()):
            return INFINITY_AS_EIGHT
        found = re.findall(r"\d{1,3}", joined.translate(DIGIT_LOOKALIKES).replace("-", ""))
        if found:
            return found[0] if int(found[0]) <= 300 else None
    elif kind == "count":
        for text in texts:
            value = as_int(text, 1, 200) if re.fullmatch(r"[\dOoIl|SsBZ]{1,3}", text) else None
            if value is not None:
                return value
    elif kind == "small_count":
        for text in texts:
            value = as_int(text, 0, 9) if len(digits(text)) == 1 else None
            if value is not None:
                return value
    elif kind == "circle":
        for text in texts:
            text = "".join(CIRCLED.get(character, character) for character in text)
            value = as_int(text.split(":")[0][:1], 1, 9) if text and not CLOCK.fullmatch(text) else None
            if value is not None:
                return value
    elif kind == "round":
        match = re.search(r"R\s*([\dIl|i])", joined)
        if match:
            return as_int(match.group(1), 1, 9)
    elif kind == "lap":
        match = re.search(r"OUR\W*([\dIl|]{1,2})|TOUR\W*([\dIl|]{1,2})", joined)
        if match:
            return as_int(match.group(1) or match.group(2), 1, 9)
    elif kind == "wins":
        match = re.search(r"WINS?\W*([\dIl|]{1,3})", joined)
        if match:
            return as_int(match.group(1), 1, 999)
    elif kind == "name":
        words = [text for text in texts if re.search(r"[A-Za-z]{3}", text)]
        if words:
            return max(words, key=len)
    return None


def football(lines: list[tuple[str, float, float]]) -> dict:
    """Clock, the two scores and the two team codes of an EA Sports FC scoreboard, in either of its two styles.

    lines: (text, x, y) with x, y the centre of the text in capture pixels.
    """
    found = {}
    for text, x, _ in lines:
        match = CLOCK.search(text)
        if match and int(match.group(2)) < 60 and x < 300 and "clock_display" not in found:
            found["clock_display"] = f"{match.group(1).zfill(2)}:{match.group(2)}"
    inline = [re.search(r"([A-Z]{2,4})\s*(\d{1,2})\s*[-|:\s]\s*(\d{1,2})\s*([A-Z]{2,4})", text) for text, _, _ in lines]
    inline = [match for match in inline if match]
    if inline:
        team_a, score_a, score_b, team_b = inline[0].groups()
        found.update(participant_a=team_a, score_a=int(score_a), score_b=int(score_b), participant_b=team_b)
        return found
    teams = sorted((y, x, text) for text, x, y in lines if re.fullmatch(r"[A-Z]{3}", text) and x < 420)
    scores = sorted((y, x, int(text)) for text, x, y in lines if re.fullmatch(r"\d{1,2}", text) and x < 420)
    vertical = teams and max(x for _, x, _ in teams) < 160
    order = (lambda item: (item[0], item[1])) if vertical else (lambda item: (item[1], item[0]))
    teams, scores = sorted(teams, key=order), sorted(scores, key=order)
    if len(teams) == 2:
        found.update(participant_a=teams[0][2], participant_b=teams[1][2])
    if len(scores) == 2 and all(value <= 20 for *_, value in scores):
        found.update(score_a=scores[0][2], score_b=scores[1][2])
    return found


def in_slot(slot: Slot, zone_count: int, line: list) -> bool:
    _, _, zone, x0, y0, x1, y1 = line
    wanted = slot.zone if slot.zone >= 0 else zone_count + slot.zone
    centre_x, centre_y = (x0 + x1) / 2, (y0 + y1) / 2
    return zone == wanted and slot.x[0] <= centre_x <= slot.x[1] and slot.y[0] <= centre_y <= slot.y[1]


# The timer of the storm (Fortnite) and of the circle (Warzone): where the OCR finds it, centre in capture pixels.
STORM_TIMERS = {
    "Fortnite": {"solo": (1010, 1075, 100, 135), "multi": (1010, 1075, 100, 135)},
    "Call of Duty: Warzone": {"counters": (15, 100, 198, 235)},
}
TIMER = re.compile(r"(\d{1,2})[:.](\d{2})(?:[.,](\d))?")


def storm_timer(family: str, readings: dict[str, list[list]]) -> str | None:
    """The storm or circle timer as displayed (m:ss or m:ss.d), from the zones of the game."""
    for layout, (a, b, c, d) in STORM_TIMERS.get(family, {}).items():
        for text, _, _, x0, y0, x1, y1 in readings.get(layout, []):
            match = TIMER.search(text)
            if match and a <= (x0 + x1) / 2 <= b and c <= (y0 + y1) / 2 <= d and int(match.group(2)) < 60:
                tenths = f".{match.group(3)}" if match.group(3) else ""
                return f"{int(match.group(1))}:{match.group(2)}{tenths}"
    return None


def fortnite_players(lines: list[list], boxes: list[tuple[int, int, int, int]]) -> set[int]:
    """The player counts (1 to 100) read alone on a line whose centre falls in one of the boxes."""
    found = set()
    for text, _, _, x0, y0, x1, y1 in lines:
        centre_x, centre_y = (x0 + x1) / 2, (y0 + y1) / 2
        if re.fullmatch(r"\d{1,3}", text) and any(a <= centre_x <= b and c <= centre_y <= d for a, b, c, d in boxes):
            found.add(as_int(text, 1, 100))
    return found - {None}


def read_fields(family: str, readings: dict[str, list[list]], zone_counts: dict[str, int]) -> dict:
    """Fields of the observation for one frame from the OCR lines of each layout of its game.

    readings: layout -> lines [text, score, zone, x0, y0, x1, y1] in capture pixels.
    """
    fields = {}
    timer = storm_timer(family, readings)
    if timer:
        fields["storm_timer"] = timer
    if family == "Fortnite":
        both = [fortnite_players(readings.get("og", []), [box]) for box in FORTNITE_SPLIT_PORTRAITS]
        common = set.intersection(*both)
        if len(common) == 1:
            fields["players_remaining"] = common.pop()
            return fields
        for layout, boxes in FORTNITE_PLAYERS.items():
            for text, _, _, x0, y0, x1, y1 in readings.get(layout, []):
                centre_x, centre_y = (x0 + x1) / 2, (y0 + y1) / 2
                if any(a <= centre_x <= b and c <= centre_y <= d for a, b, c, d in boxes):
                    value = as_int(text, 1, 100) if re.fullmatch(r"\d{1,3}", text) else None
                    if value is not None:
                        fields["players_remaining"] = value
                        return fields
        return fields
    layout, lines = next(iter(readings.items()))
    for slot_ in SLOTS.get(family, ()):
        if slot_.kind == "football":
            fields.update(football([(t, (x0 + x1) / 2, (y0 + y1) / 2) for t, _, _, x0, y0, x1, y1 in lines]))
            continue
        texts = [line[0] for line in lines if in_slot(slot_, zone_counts[layout], line)]
        value = read_value(slot_.kind, texts)
        if value is not None:
            fields[slot_.field] = value
    return fields
