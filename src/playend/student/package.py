"""Write a PlayEnd package whose observations carry what the student read, to replay the end detectors on it.

The package is a copy of the teacher's (playend.student.collect.OBSERVATIONS) where only observation_json and the
features change; the ends, units and splits stay the teacher's. Variants:

- reading: the HUD values of every observation (score, clock, period, lap, counters, names) are replaced by what the
  OCR student read on that frame (build/student/readings_ocr.json), null when it read nothing or does not read that
  frame; game, screen, banners stay the teacher's. It isolates the effect of reading errors.
- missing:<share>: the teacher's HUD values, each emptied at random with this probability (a fixed seed).
- student: the whole student. The game and the screen come from the classifier, each frame predicted by a model that
  did not see its block of time, with the vote over the last captures (build/student/classifier_oof.json); a lone
  switch between gameplay and the other screens waits for the next capture (steady_screens). The HUD
  is read only where the classifier sees a gameplay screen of the frame's game; on every other screen the banner is
  looked for in the whole capture (playend.student.banners, build/student/screens_ocr.json). Properties of a game that
  the teacher writes the same way on almost every frame (type, usual mode and its duration, kind of period, kind of
  score, number of participant slots, whether there is a main clock) come from its profile, the most frequent value
  over the teacher's gameplay frames. As the teacher does, what was looked for and is not on the screen is written
  absent (false, empty list), and only what could not be read stays null.

Every new observation passes validate_observation of contract 2.1 before the features are computed.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from playend.common.games import NO_GAME
from playend.common.paths import STUDENT_OUTPUT
from playend.contract.contract import empty_observation, upgrade_v20, validate_observation
from playend.contract.temporal import feature_spec
from playend.dataset.features import feature_rows
from playend.student.banners import result
from playend.student.collect import OBSERVATIONS
from playend.student.rules import INFINITY_AS_EIGHT

PACKAGE = OBSERVATIONS.parents[1]
# Whole-capture OCR of every screen the classifier does not take for gameplay, where banners are looked for.
BANNERS = STUDENT_OUTPUT / "screens_ocr.json"
COUNTERS = {
    "players_remaining": ("players_remaining", "field"),
    "teams_remaining": ("teams_remaining", "field"),
    "lives_a": ("lives", "a"),
    "lives_b": ("lives", "b"),
    "series_a": ("series", "a"),
    "series_b": ("series", "b"),
}
# The type of each game and the phase of each screen, as the teacher writes them (a property of the game or screen).
GAME_TYPES = {
    "EA Sports FC": "football", "EA Sports UFC 5": "combat_sport", "Beach Buggy Racing 2": "racing",
    "Fortnite": "other", "Call of Duty: Warzone": "other", "Genshin Impact": "mission_adventure",
    "Red Dead Redemption 2": "mission_adventure", "Assassin's Creed Origins": "mission_adventure",
    "God of War": "mission_adventure",
}  # fmt: skip
# Screens on which the game is not running: no mode, as the teacher mostly leaves it empty there.
OUTSIDE_GAME = {"menu", "loading", "character_select", "team_select", "unknown"}
# Games whose HUD the student reads counters or a storm timer from: elsewhere an empty list is the truth.
COUNTER_GAMES = {"Fortnite", "Call of Duty: Warzone", "Dragon Ball Sparking! ZERO", "Tekken 8"}
TIMER_GAMES = {"Fortnite", "Call of Duty: Warzone"}
PHASES = {"gameplay": "active", "menu": "menu", "team_select": "pre_game", "character_select": "pre_game",
          "pause": "paused", "other": "post_game", "loading": "loading", "cutscene": "active", "result": "post_game",
          "scoreboard": "post_game", "podium": "post_game", "unknown": "unknown"}  # fmt: skip


def seconds(display) -> float | None:
    text = str(display or "")
    if ":" in text:
        minutes, _, rest = text.partition(":")
        try:
            return int(minutes) * 60 + float(rest) if minutes.isdigit() and rest[:2].isdigit() else None
        except ValueError:
            return None
    return float(text) if text.isdigit() else None


def hud_values(observation: dict) -> dict:
    """The HUD values of an observation, in the field names the student uses."""
    fields = {
        "score_a": observation["score"]["a"],
        "score_b": observation["score"]["b"],
        "clock_display": observation["clock"]["display"],
        "period_number": observation["period"]["number"],
        "progress_current": observation["progress"]["current"],
    }
    names = observation["participants"]["primary"]
    fields |= {"participant_a": names[0] if names else None, "participant_b": names[1] if len(names) > 1 else None}
    for counter in observation.get("secondary_counters") or []:
        for field, (kind, side) in COUNTERS.items():
            if counter["kind"] == kind and counter["side"] == side:
                fields[field] = counter["value"]
    return {field: value for field, value in fields.items() if value is not None}


def with_hud(observation: dict, fields: dict) -> dict:
    """The observation with its HUD values replaced by `fields`; everything the student does not read is null."""
    new = copy.deepcopy(observation)
    if new["schema_version"] == "2.0":
        new = upgrade_v20(new)
    new["score"]["a"], new["score"]["b"] = fields.get("score_a"), fields.get("score_b")
    display = fields.get("clock_display")
    new["clock"] = {"visible": True if display is not None else None, "display": None, "value_seconds": None,
                    "direction": "unknown" if display is not None else None}  # fmt: skip
    if display is not None:
        new["clock"]["display"] = str(display)
        new["clock"]["value_seconds"] = seconds(display)
    new["period"]["number"], new["period"]["total"] = fields.get("period_number"), None
    new["progress"]["current"], new["progress"]["total"] = fields.get("progress_current"), None
    new["position"] = {"current": None, "total": None}
    new["participants"]["primary"] = [fields[f] for f in ("participant_a", "participant_b") if fields.get(f)]
    new["secondary_counters"] = [
        {"kind": kind, "side": side, "value": fields[field], "total": None, "label": None}
        for field, (kind, side) in COUNTERS.items()
        if fields.get(field) is not None
    ]
    timer = fields.get("storm_timer")
    new["secondary_timers"] = None
    if timer is not None:
        new["secondary_timers"] = [{"kind": "storm_phase", "label": None, "display": timer,
                                    "value_seconds": seconds(timer), "direction": "unknown"}]  # fmt: skip
    return new


def profiles() -> dict[tuple[str, bool], dict]:
    """Per game, the most frequent value of its fixed properties over the teacher's gameplay frames.

    Kept apart for a clock showing infinity: Mortal Kombat 1 in training (mode other, no end) is not a timed fight.
    """
    counts = defaultdict(lambda: defaultdict(Counter))
    with open(OBSERVATIONS, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["screen_type"] != "gameplay" or not row["game_family"]:
                continue
            observation = json.loads(row["observation_json"])
            game = observation["game"]
            values = {"mode": game["mode"], "mode_duration": game["mode_duration"],
                      "period_type": observation["period"]["type"], "score_type": observation["score"]["type"],
                      "count_visible": observation["participants"]["count_visible"],
                      "clock_visible": observation["clock"]["visible"]}  # fmt: skip
            infinite = observation["clock"]["display"] == INFINITY_AS_EIGHT
            for key, value in values.items():
                if value is not None or key == "clock_visible":
                    counts[(row["game_family"], infinite)][key][value] += 1
    return {game: {key: counter.most_common(1)[0][0] for key, counter in keys.items()} for game, keys in counts.items()}


def student_view(game: str, screen: str, fields: dict, banner: list[str] | None, profile: dict) -> dict:
    observation = empty_observation()
    if game != NO_GAME:
        observation["game"]["title"] = game
        observation["game"]["type"] = GAME_TYPES.get(game, "combat")
        if screen not in OUTSIDE_GAME:
            observation["game"]["mode"] = profile.get("mode")
            observation["game"]["mode_duration"] = profile.get("mode_duration", "unknown")
    observation["state"]["screen_type"] = screen
    observation["state"]["phase"] = PHASES.get(screen, "unknown")
    observation = with_hud(observation, fields)
    if screen != "gameplay":  # no HUD on the screen: no clock, no counter, no timer
        observation["clock"] = {"visible": False, "display": None, "value_seconds": None, "direction": None}
        observation["secondary_counters"], observation["secondary_timers"] = [], []
        observation["period"]["type"] = "none"
    else:
        if fields.get("clock_display") is None and profile.get("clock_visible") is False:
            observation["clock"]["visible"] = False
        observation["period"]["type"] = profile.get("period_type", "unknown")
        if fields.get("score_a") is not None or fields.get("score_b") is not None:
            observation["score"]["type"] = profile.get("score_type")
        observation["participants"]["count_visible"] = profile.get("count_visible")
        if not observation["secondary_counters"] and game in COUNTER_GAMES:
            observation["secondary_counters"] = None  # counters on this HUD, none read
        if observation["secondary_timers"] is None and game not in TIMER_GAMES:
            observation["secondary_timers"] = []
    visible, found = result(screen, banner or [])
    observation["result"] = {"visible": visible, "winner": None, "outcome_type": found}
    return observation


class SteadyScreen:
    """The classifier's screen, one capture at a time, a lone switch between gameplay and the rest held back.

    A capture taken for a menu in the middle of play, or for play in the middle of menus, is most often a classifier
    error, and to the end detector it looks like a game that ends or starts. A switch is kept when the next capture
    agrees, or at once when a result banner is read; it costs at most one capture of delay, the tolerance of the
    evaluation. Only past captures are used, as on the Pi.
    """

    def __init__(self):
        self.steady: str | None = None
        self.previous: str | None = None

    def step(self, screen: str, banner: list[str] | None) -> str:
        """The screen to keep for this capture, given the classifier's screen and the banner read, if any."""
        kept = screen
        if self.steady is not None:
            was_gameplay, is_gameplay = self.steady == "gameplay", screen == "gameplay"
            confirmed = self.previous is not None and (self.previous == "gameplay") == is_gameplay
            if not (was_gameplay == is_gameplay or confirmed or (banner and result(screen, banner)[0])):
                kept = self.steady
        self.previous, self.steady = screen, kept
        return kept


def steady_screens(predicted: list[str], banners: list[list[str] | None]) -> list[str]:
    """SteadyScreen over the screens of one session in order."""
    state = SteadyScreen()
    return [state.step(screen, banner) for screen, banner in zip(predicted, banners)]


def build(variant: str, out: Path, readings: Path | None, seed: int = 0, classifier: Path | None = None) -> dict:
    if out.exists():
        raise SystemExit(f"{out} already exists")
    shutil.copytree(PACKAGE, out, ignore=shutil.ignore_patterns("observations.csv", "features*.csv"))
    read = json.loads(readings.read_text(encoding="utf-8")) if variant in ("reading", "student") else {}
    predicted = json.loads(classifier.read_text(encoding="utf-8")) if variant == "student" else {}
    banners = json.loads(BANNERS.read_text(encoding="utf-8")) if variant == "student" else {}
    game_profiles = profiles()
    share = float(variant.split(":")[1]) if variant.startswith("missing:") else 0.0
    rng = random.Random(seed)
    with open(OBSERVATIONS, newline="", encoding="utf-8") as handle:
        source = csv.DictReader(handle)
        columns, rows = source.fieldnames, list(source)
    counts = {"frames": len(rows), "changed": 0, "invalid": 0}
    screens = {}
    if variant == "student":
        sessions = defaultdict(list)
        for row in rows:
            sessions[row["session_id"]].append(f"{row['session_id']}:{int(row['frame_id'])}")
        for keys in sessions.values():
            raw = [predicted[key]["screen"] for key in keys]
            texts = [[line[0] for line in banners[key]] if key in banners else None for key in keys]
            screens |= dict(zip(keys, steady_screens(raw, texts)))
    for row in rows:
        observation = json.loads(row["observation_json"])
        key = f"{row['session_id']}:{int(row['frame_id'])}"
        if variant == "student":
            game, screen = predicted[key]["game"], screens[key]
            seen = screen == "gameplay" and game == (row["game_family"] or NO_GAME)
            banner = [line[0] for line in banners[key]] if key in banners else None
            fields = read.get(key, {}) if seen else {}
            profile = game_profiles.get((game, fields.get("clock_display") == INFINITY_AS_EIGHT)) or game_profiles.get(
                (game, False), {}
            )
            new = student_view(game, screen, fields, banner, profile)
        else:
            if variant == "reading":
                fields = read.get(key, {})
            else:
                fields = {k: v for k, v in hud_values(observation).items() if rng.random() >= share}
            new = with_hud(observation, fields)
        if validate_observation(new):
            counts["invalid"] += 1
            continue
        counts["changed"] += new != observation
        row["observation_json"] = json.dumps(new, ensure_ascii=False, separators=(",", ":"))
    with open(out / "data" / "observations.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        row["frame_id"] = int(row["frame_id"])
    names = feature_spec()["feature_names"]
    with open(out / "data" / "features.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["session_id", "frame_id", *names])
        for features in feature_rows(rows):
            writer.writerow([features["session_id"], features["frame_id"], *(repr(features[n]) for n in names)])
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("variant", help="reading, student, or missing:<share> such as missing:0.2")
    parser.add_argument("--readings", type=Path, default=STUDENT_OUTPUT / "readings_ocr.json")
    parser.add_argument("--classifier", type=Path, default=STUDENT_OUTPUT / "classifier_oof.json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or STUDENT_OUTPUT / "packages" / args.variant.replace(":", "_")
    print(args.variant, build(args.variant, out, args.readings, classifier=args.classifier))


if __name__ == "__main__":
    main()
