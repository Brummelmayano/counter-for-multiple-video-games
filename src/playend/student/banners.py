"""The end-of-game banner: what the whole screen says when the classifier sees a result screen.

The OCR reads the whole capture (playend.student.ocr), and the words of the banner give the outcome as the teacher
writes it. Win: "Victoire", "VICTOIRE ROYALE", "VAINQUEUR", "LI MEI GAGNE", "FIN MATCH", or a final score with a
winner on a results screen. Ko: "KO". Draw: "MATCH NUL" or a level final score. Other: "VOUS ÊTES MORT", "VOTRE
PLACE : #4", a race ranking ("1er", "2e"), match statistics or the judges' scorecards. Damaged readings of "Victoire"
("Pictoire", "VCTOIRE") are accepted by similarity. A banner is a line of its own: the same words inside a sentence
("a fait tomber une couronne de victoire", "Finir sur un match nul") or in a statistic ("35 VICTOIRES") are menus and
kill feeds, not results. A result screen with none of these words has a visible result and no outcome, as in the
teacher's observations.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from playend.common.paths import STUDENT_OUTPUT
from playend.student.collect import OBSERVATIONS
from playend.student.rules import similarity

WIN_WORDS = ("VICTOIRE", "VICTORY", "VAINQUEUR")
# close enough to "VICTOIRE" but not a win: the fighter Victor, the story mode of the menus
NOT_WINS = ("VICTOR", "HISTOIRE")
RESULT_SCREENS = {"result", "scoreboard", "podium"}


def win_word(word: str) -> bool:
    # six letters at least and singular: "VICTOIRES" is a statistic of the menus
    return (
        len(word) >= 6
        and not word.endswith("S")
        and word not in NOT_WINS
        and any(similarity(word, target) >= 0.75 for target in WIN_WORDS)
    )


def outcome(texts: list[str]) -> str | None:
    words = [word for text in texts for word in re.findall(r"[^\W\d_]+", text)]
    lines = [" ".join(re.findall(r"[^\W\d_]+", text.upper())) for text in texts]
    upper = [word.upper() for word in words]
    joined = " ".join(texts).upper()
    if "KO" in upper or any(re.fullmatch(r"K\.?O\.?", text.strip()) for text in texts):
        return "ko"
    if "VICTOIRE ROYALE" in joined or "VICTORY ROYALE" in joined:
        return "win"
    if re.search(r"VOUS ?[ÉE]TES MORT|VOTRE PLACE|\bPLACE\s*:|\b1ER\b.*\b2E\b|\bRATIO\b|JUGES", joined):
        return "other"
    if any(" " not in line and win_word(line) for line in lines):
        return "win"
    if "GAGNE" in words or re.search(r"\bFIN (DU )?MATCH\b", joined):
        return "win"
    if "MATCH NUL" in lines or "DRAW" in lines:
        return "draw"
    final = re.search(r"\bR[ÉE]SULTATS?\b.*?\b(\d{1,2})\s*-\s*(\d{1,2})\b", joined)
    if final:  # a final score on a results screen: a winner, or a draw
        return "win" if final.group(1) != final.group(2) else "draw"
    return None


# Words of a results screen that give no outcome by themselves ("RÉSULTATS", "CLASSEMENT", "RÉSUMÉ PARTIE").
RESULT_WORDS = re.compile(r"R[ÉE]SULTAT|R[ÉE]COMPENSES|CLASSEMENT|R[ÉE]SUM[ÉE]", re.IGNORECASE)


def result(screen: str, texts: list[str]) -> tuple[bool, str | None]:
    """Whether a result is visible, and its outcome: a banner word anywhere, or a results word on a screen the
    classifier takes for a result. A result screen with no word read is not trusted: most are classifier errors."""
    found = outcome(texts)
    if found is not None:
        return True, found
    return screen in RESULT_SCREENS and bool(RESULT_WORDS.search(" ".join(texts))), None


def main():
    parser = argparse.ArgumentParser(description="Score the banner rules on the teacher's result screens.")
    parser.add_argument("--readings", type=Path, default=STUDENT_OUTPUT / "result_screens_ocr.json")
    args = parser.parse_args()
    readings = json.loads(args.readings.read_text(encoding="utf-8"))
    counts = Counter()
    with open(OBSERVATIONS, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = f"{row['session_id']}:{int(row['frame_id'])}"
            if row["screen_type"] in RESULT_SCREENS and key in readings:
                teacher = json.loads(row["observation_json"])["result"]["outcome_type"]
                read = outcome([line[0] for line in readings[key]])
                counts[(str(teacher), str(read))] += 1
    right = sum(count for (teacher, read), count in counts.items() if teacher == read)
    print(f"{right}/{sum(counts.values())} result screens with the teacher's outcome")
    for (teacher, read), count in counts.most_common():
        print(f"  teacher {teacher:6} read {read:6} {count}")


if __name__ == "__main__":
    main()
