"""Count games at their start, with rules only (step 2 of docs/decisions/PLAN_COMPTAGE_PAR_DEBUT.md).

Each gameplay capture is read against the profile of its game family. An opening reading shows the values of a game
that has just begun (0-0, lap 1, almost every player left, first round at full clock, the endless clock that opens a
Dragon Ball fight); a progress reading shows a game under way; a capture with no deciding value is skipped and never
breaks a game. A time-billed mode (Mortal Kombat 1 training, Fortnite creative islands) is never a game.

The game state keeps the last values read in the open game. A quantity that only grows during a game and goes back
(score, lap, round, the clock of a football match, players left in a battle royale) breaks the game: another game has
begun; a single reading far above two others is taken for a misread, and so is a jump no game makes between two
captures (more than two goals at once, more than twenty players out), which is not kept. In a fighting game, a change
of the fighters' names or of the series of consecutive wins (Tekken's "WINS n") also breaks the game. A pause or a
menu does not, since play resumes where it stopped; the lobby or the loading of a battle royale does, since a match
never resumes from there, and so does a screen before a fight (the choice of the stage, the "VS" screen).

A new game is decided:
- on an opening reading when no game is open, the game changed, the open game is broken, or a screen that closes a
  game was seen since (result, loading, selection, after the game, console home). The endless clock of Dragon Ball
  Sparking! ZERO, seen only as a fight opens, and a change of Tekken's series of wins decide at once; any other
  opening is confirmed by the next
  gameplay reading of the same game, unless a screen that closes a game comes first. In a battle royale, a reading
  on the waiting island is confirmed only by a reading in the match, and any menu before it drops the reading: an
  island left before the bus is not a game;
- on a progress reading when no game is open, the game changed, or the open game is broken: a game first seen
  already under way, as the 2025 counter did with its old and new minutes. A screen after which the same game cannot
  resume (result, selection, after the game) opens it at once when the values break too. Alone, such a screen shows
  no value of the game and may be a misread one, so values that could show a break and do not go on with the open
  game, as the 2025 counter skipped every capture where it read no minute. When nothing can be compared (Dragon Ball's
  health bars rise with every teammate, FighterZ shows no count), the screen stays the only sign. After a pause, a
  loading screen or the console home, the same game may resume.
The start is placed on the first reading of the new game, where the reference start is
(data/boundaries/*/units.json, start_established_at; without data/, the units table of the PlayEnd package).

In Dragon Ball Sparking! ZERO, a fighter whose health bars go up while the portrait stays the same was started again
with "Réessayer" (playend.counting.portraits, which reads the portrait zone on the capture). Without the captures,
which PlayEnd does not publish, no portrait is compared, as with --no-portraits.

usage: python -m playend.counting.starts [--package build/playend_v1.1] [--generic] [--no-confirm] [--no-portraits]
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from functools import cache
from pathlib import Path

import numpy as np

from playend.common.games import NO_GAME, game_family
from playend.common.paths import BOUNDARIES, REPO
from playend.counting.portraits import SessionPortraits, same

OPENING, PROGRESS, TIME = "opening", "progress", "time"
CLOSING_SCREENS = {"result", "scoreboard", "podium", "loading", "character_select", "team_select", "race_grid"}
FINAL_SCREENS = {"result", "podium", "character_select", "team_select", "race_grid"}  # the same game cannot resume
BATTLE_ROYALE = {"Fortnite", "Call of Duty: Warzone"}
FIGHTING = {
    "Mortal Kombat 1", "Tekken 8", "Naruto Storm Connections", "Dragon Ball Sparking! ZERO", "Dragon Ball FighterZ",
    "Demon Slayer", "J-Stars Victory VS+", "EA Sports UFC 5", "Brawlhalla",
}  # fmt: skip
NAMED_FIGHTERS = {"Mortal Kombat 1", "Tekken 8", "EA Sports UFC 5"}  # the names above the bars are the fighters
FOOTBALL_OPENING_S = 20 * 60  # an EA FC match at 0-0 before minute 20 has just begun
UFC_OPENING_S = 4 * 60  # round 1 with more than 4:00 left
BATTLE_ROYALE_OPENING = 60  # players left
PLAYERS_DROP = 3  # players lost since the opening reading that confirm a battle royale match has begun
PLAYERS_JUMP = 10  # more players left than at the last reading: another match
CLOCK_BACK_S = 60  # a football clock that goes back by more than this: another match
UFC_CLOCK_UP_S = 30  # a UFC round clock that goes up in the same round: another fight
NAME_SIMILARITY = 0.7  # two spellings of a fighter's name read on different screenshots
EARLY_TOLERANCE = 2  # captures: a start read this much before the reference start still finds its game
FINAL_RUN = 3  # captures in a row of a result or selection screen: rarely a misread one (5 of 72 in play)


@dataclass
class Reading:
    kind: str | None
    total: int | None = None  # score or rounds won, both sides read
    lap: int | None = None
    players: int | None = None
    round: int | None = None
    football_clock: int | None = None
    ufc_clock: int | None = None
    marker: bool = False  # a sign that only an opening shows
    series: tuple | None = None  # side and value of the consecutive wins
    lives: dict | None = None  # health bars left, by side (Dragon Ball Sparking! ZERO)
    names: frozenset | None = None  # the two fighters written on screen


def counters(obs: dict) -> dict[str, list[int]]:
    found = defaultdict(list)
    for counter in obs.get("secondary_counters") or []:
        if counter.get("value") is not None:
            found[counter["kind"]].append(counter["value"])
    return found


def read(obs: dict, family: str, generic: bool = False) -> Reading:
    """Opening, progress or time for one gameplay capture; kind None when nothing on it decides."""
    score_a, score_b = obs["score"]["a"], obs["score"]["b"]
    total = score_a + score_b if score_a is not None and score_b is not None else None
    clock, seconds = (obs["clock"]["display"] or "").strip(), obs["clock"]["value_seconds"]
    found = counters(obs)
    progress = obs["progress"]
    # the student writes the lap of Beach Buggy Racing 2 without its kind
    racing_lap = family == "Beach Buggy Racing 2" and progress["type"] is None
    lap = progress["current"] if progress["type"] == "lap" or racing_lap else None
    players = (found.get("players_remaining") or [None])[0]
    period = obs["period"]
    endless = family in ("Dragon Ball Sparking! ZERO", "Dragon Ball FighterZ")  # FighterZ shows ∞ all fight long
    if clock == "∞" and total is None and not endless:
        return Reading(TIME)  # Mortal Kombat 1 training: endless clock and no round marker
    if family == "Fortnite" and players is not None and period["type"] == "round":
        return Reading(TIME)  # creative island: rounds of a respawn arena
    reading = Reading(None, total, lap, players, period["number"] if period["type"] == "round" else None)
    series = [(counter["side"], counter["value"]) for counter in obs.get("secondary_counters") or []
              if counter["kind"] == "series" and counter.get("value") is not None]  # fmt: skip
    reading.series = tuple(sorted(series)) or None
    reading.lives = {side: values[0] for side, values in lives_by_side(obs).items()} or None
    names = [name for name in obs.get("participants", {}).get("primary") or [] if name]
    if family in NAMED_FIGHTERS and len(names) == 2:
        reading.names = frozenset(names)
    if family == "EA Sports FC":
        if period["type"] == "other":
            return reading  # penalty shoot-out: its score starts again at 0-0 inside the same match
        reading.football_clock = seconds
    if family == "EA Sports UFC 5":
        reading.ufc_clock = seconds
    if family == "Dragon Ball Sparking! ZERO" and clock == "∞":
        reading.kind, reading.marker = OPENING, True  # the endless clock shows only as a fight opens
        return reading
    profile = None if generic else PROFILES.get(family)
    reading.kind = profile(obs, reading, seconds, found) if profile else generic_kind(reading)
    return reading


def lives_by_side(obs: dict) -> dict[str, list[int]]:
    found = defaultdict(list)
    for counter in obs.get("secondary_counters") or []:
        if counter["kind"] == "lives" and counter.get("value") is not None:
            found[counter["side"]].append(counter["value"])
    return found


def generic_kind(reading: Reading) -> str | None:
    """What any game shows: a score at zero, the first lap, most players left."""
    if reading.total is not None:
        return OPENING if reading.total == 0 else PROGRESS
    if reading.lap is not None:
        return OPENING if reading.lap == 1 else PROGRESS
    if reading.players is not None:
        return OPENING if reading.players >= BATTLE_ROYALE_OPENING else PROGRESS
    return None


def football(obs, reading, seconds, found):
    if reading.total is None:
        return None
    return OPENING if reading.total == 0 and (seconds is None or seconds <= FOOTBALL_OPENING_S) else PROGRESS


def ufc(obs, reading, seconds, found):
    if seconds is None:
        return None
    if reading.round is None:
        return PROGRESS  # a mode with one long clock and no round number
    return OPENING if reading.round == 1 and seconds >= UFC_OPENING_S else PROGRESS


def lives_left(obs, reading, seconds, found):
    # Dragon Ball: a fighter who comes in has full lives inside the same fight, so lives never open a game there;
    # FighterZ shows ∞ for the whole fight and nothing else, which still says a fight is on.
    return PROGRESS if found.get("lives") or (obs["clock"]["display"] or "").strip() == "∞" else None


def stocks(obs, reading, seconds, found):
    lives = found.get("lives")
    if not lives:
        return None
    return OPENING if min(lives) >= 3 else PROGRESS


def by_generic(obs, reading, seconds, found):
    return generic_kind(reading)


PROFILES = {
    "EA Sports FC": football,
    "EA Sports UFC 5": ufc,
    "Dragon Ball Sparking! ZERO": lives_left,
    "Dragon Ball FighterZ": lives_left,
    "Brawlhalla": stocks,
}


QUANTITIES = ("total", "lap", "players", "round", "football_clock", "ufc_clock")
MEMORY = 3  # readings of each quantity kept
# How far the highest of the kept values may stand above the next one before it is taken for a misread (the lowest
# below the next one, for the players left, which only go down).
MAX_STEP = {"total": 2, "players": 20}  # largest change kept from one reading to the next
OUTLIER_GAP = {"total": 1, "lap": 1, "round": 1, "football_clock": 10 * 60, "players": 15}


def implausible(name: str, value: int, reference: int | None) -> bool:
    """A jump no game makes between two captures (ten goals at once, forty players out): a misreading, not kept."""
    if reference is None:
        return False
    if name == "total":
        return value > reference + MAX_STEP["total"]
    if name == "players":
        return value < reference - MAX_STEP["players"]
    return False


def reference(name: str, seen: deque):
    """The value a new reading is compared with: the furthest the game went, unless a single reading went too far."""
    if not seen:
        return None
    if name == "ufc_clock":
        return seen[-1]  # it runs down in a round and starts again at the next one
    ordered = sorted(seen, reverse=name != "players")
    if len(ordered) >= MEMORY and abs(ordered[0] - ordered[1]) > OUTLIER_GAP[name]:
        return ordered[1]  # one reading alone against two that agree
    return ordered[0]


def same_fighters(first: frozenset, second: frozenset) -> bool:
    """Both fighters match, up to case and a few misread letters."""

    def key(name):
        return "".join(letter for letter in name.casefold() if letter.isalnum())

    def close(a, b):
        return SequenceMatcher(None, key(a), key(b)).ratio() >= NAME_SIMILARITY

    return all(any(close(name, other) for other in second) for name in first)


@dataclass
class OpenGame:
    family: str
    history: dict[str, deque] = field(default_factory=dict)
    series: tuple | None = None
    names: frozenset | None = None

    @classmethod
    def from_reading(cls, family: str, reading: Reading) -> OpenGame:
        game = cls(family, {name: deque(maxlen=MEMORY) for name in QUANTITIES})
        game.remember(reading)
        return game

    def remember(self, reading: Reading) -> None:
        last = self.last
        for name in QUANTITIES:
            value = getattr(reading, name)
            if value is not None and not implausible(name, value, getattr(last, name)):
                self.history[name].append(value)
        self.series = reading.series or self.series
        self.names = reading.names or self.names

    @property
    def last(self) -> Reading:
        values = {name: reference(name, seen) for name, seen in self.history.items()}
        return Reading(None, **values, series=self.series, names=self.names)


@dataclass
class Start:
    frame: int  # the first reading of the new game
    decided_at: int  # the capture that confirmed it
    family: str
    late: bool  # first seen already under way


@dataclass
class Candidate:
    frame: int
    family: str
    late: bool
    island: bool  # read on a battle royale waiting island
    needs_break: bool  # a game seen under way only because a value went back: the next reading must show it too
    reading: Reading


@dataclass
class Detector:
    generic: bool = False
    confirm: bool = True
    game: OpenGame | None = None
    closed: bool = True  # a screen that closes a game was seen since the last gameplay reading
    final: bool = True  # a screen after which the same game cannot resume was seen since
    candidate: Candidate | None = None
    starts: list[Start] = field(default_factory=list)
    portraits: Callable[[int, str, str], np.ndarray | None] | None = None  # frame, game, side -> thumbnail
    fighters: tuple[int, str, dict] | None = None  # last fight reading with health bars: frame, game, bars
    final_run: int = 0  # captures in a row of a final screen, up to this one
    final_longest: int = 0  # longest such run since the last gameplay reading

    def observe(self, frame: int, obs: dict) -> None:
        family = game_family(obs["game"]["title"])
        state = obs["state"]
        ending = state["screen_type"] in FINAL_SCREENS or state["phase"] == "post_game"
        self.final_run = self.final_run + 1 if ending else 0
        self.final_longest = max(self.final_longest, self.final_run)
        if state["screen_type"] != "gameplay" or state["phase"] == "post_game":
            if self.candidate is not None and (self.candidate.island or self.closes(state, family)):
                self.candidate = None  # play stopped before the opening was confirmed
            self.closed |= self.closes(state, family)
            self.final |= ending
            # a battle royale match never resumes from the lobby or a loading screen (the insertion is part of it)
            lobby = state["phase"] in ("pre_game", "loading") and state["screen_type"] in ("menu", "loading")
            self.final |= family in BATTLE_ROYALE and lobby
            # between two fights: the choice of the stage, the "VS" screen
            self.final |= family in FIGHTING and state["phase"] == "pre_game"
            return
        reading = read(obs, family, self.generic)
        if reading.kind == TIME:
            self.game, self.candidate, self.closed, self.final = None, None, True, True
            return
        if reading.kind is None:
            return
        if self.restarted(frame, family, reading):
            self.open(Start(frame, frame, family, late=False), reading)
            return
        island = family in BATTLE_ROYALE and state["phase"] == "pre_game"
        if self.candidate is not None and self.settle(frame, family, reading, island):
            return
        reason = self.reason(family, reading)
        if reading.kind == OPENING and (reason or (self.closed and self.game is not None)):
            if reading.marker or self.series_changed(reading):
                # signs that only an opening shows: no second reading needed (a game quit at once still counts)
                self.open(Start(frame, frame, family, late=False), reading)
            elif self.confirm or island or reason == "broken":
                # in a battle royale, an opening seen only through a jump of the players left needs a second reading
                needs_break = reason == "broken" and family in BATTLE_ROYALE
                self.candidate = Candidate(frame, family, False, island, needs_break, reading)
            else:
                self.open(Start(frame, frame, family, late=False), reading)
            return
        if reading.kind == PROGRESS and (reason == "fresh" or (reason == "broken" and not self.confirm)):
            self.open(Start(frame, frame, family, late=True), reading)
            return
        if reading.kind == PROGRESS and reason == "broken":
            self.candidate = Candidate(frame, family, True, False, True, reading)
            return
        if self.game is not None and self.game.family == family:
            self.game.remember(reading)
        self.closed = self.final = False
        self.final_longest = 0

    def settle(self, frame: int, family: str, reading: Reading, island: bool) -> bool:
        """Confirm or drop the waiting candidate; True when this reading was used up.

        A confirmed game opens on the candidate's reading; the confirming reading is then read like any other, since
        it may already show the next game (a series counter that changed, other fighters)."""
        candidate, self.candidate = self.candidate, None
        if candidate.family != family:
            return False
        if candidate.island and island:
            self.candidate = candidate  # still waiting for the bus
            return True
        if family in BATTLE_ROYALE and not (
            candidate.late or candidate.island or self.players_dropped(candidate, reading)
        ):
            # an opening not known to be on the island: a waiting island left before the bus never loses a player
            self.candidate = candidate
            return True
        if candidate.needs_break and not self.broken(reading):
            return False  # a single misread value: the open game goes on
        self.open(Start(candidate.frame, frame, family, late=candidate.late), candidate.reading)
        return False

    @staticmethod
    def players_dropped(candidate: Candidate, reading: Reading) -> bool:
        first, now = candidate.reading.players, reading.players
        if first is None or now is None:
            return now is not None and now < BATTLE_ROYALE_OPENING
        return now <= first - PLAYERS_DROP

    def restarted(self, frame: int, family: str, reading: Reading) -> bool:
        """The same fighter has more health bars than at the last reading: the fight was started again."""
        if not reading.lives:
            return False
        previous, self.fighters = self.fighters, (frame, family, reading.lives)
        if self.portraits is None or self.game is None or previous is None or previous[1] != family:
            return False
        last_frame, _, last_lives = previous
        for side, value in reading.lives.items():
            # with no bar left the fighter was out, and zero is the commonest misreading: a rise from 0 says nothing
            if 0 < last_lives.get(side, value) < value:
                before, after = self.portraits(last_frame, family, side), self.portraits(frame, family, side)
                if before is not None and after is not None and same(before, after):
                    return True
        return False

    def series_changed(self, reading: Reading) -> bool:
        """Tekken's series of consecutive wins changes only when a match has ended."""
        last = self.game.series if self.game is not None else None
        return None not in (reading.series, last) and reading.series != last

    @staticmethod
    def closes(state: dict, family: str) -> bool:
        return state["screen_type"] in CLOSING_SCREENS or state["phase"] == "post_game" or family == NO_GAME

    def open(self, start: Start, reading: Reading) -> None:
        self.starts.append(start)
        self.game = OpenGame.from_reading(start.family, reading)
        self.candidate, self.closed, self.final, self.final_longest = None, False, False, 0

    def breaks(self, reading: Reading) -> dict[str, bool]:
        """For each quantity that only grows during a game, whether it went back (empty when no game is open)."""
        if self.game is None:
            return {}
        last = self.game.last
        # a football score read without the clock may be a penalty shoot-out, which starts again from 0-0
        total = reading.total if reading.football_clock is not None or last.football_clock is None else None

        def back(now, before) -> bool:
            return now is not None and before is not None and now < before

        football, ufc = (reading.football_clock, last.football_clock), (reading.ufc_clock, last.ufc_clock)
        same_round = reading.round is not None and reading.round == last.round
        return {
            "total": back(total, last.total),
            "lap": back(reading.lap, last.lap),
            "round": back(reading.round, last.round),
            "football_clock": None not in football and football[0] < football[1] - CLOCK_BACK_S,
            "ufc_clock": None not in ufc and same_round and ufc[0] > ufc[1] + UFC_CLOCK_UP_S,
            # the series counter changes only when a match ends
            "series": None not in (reading.series, last.series) and reading.series != last.series,
            "names": None not in (reading.names, last.names) and not same_fighters(reading.names, last.names),
            "players": None not in (reading.players, last.players) and reading.players > last.players + PLAYERS_JUMP,
        }

    def broken(self, reading: Reading) -> bool:
        """A quantity that only grows during a game went back."""
        return any(self.breaks(reading).values())

    def reason(self, family: str, reading: Reading) -> str | None:
        """Why this reading belongs to another game: fresh (nothing to continue) or broken (a quantity went back)."""
        if self.game is None or self.game.family != family or reading.marker:
            return "fresh"
        if self.final:
            # a final screen read by the student can be wrong: values that can show a break must show one, unless the
            # screen lasted, which a misread one seldom does
            lasted = self.final_longest >= FINAL_RUN
            return "fresh" if lasted or self.broken(reading) or not self.comparable(reading) else None
        return "broken" if self.broken(reading) else None

    def comparable(self, reading: Reading) -> bool:
        """The reading has a quantity that broken() can compare with the open game (health bars cannot)."""
        last = self.game.last
        pairs = [(reading.total, last.total), (reading.lap, last.lap), (reading.round, last.round),
                 (reading.football_clock, last.football_clock), (reading.series, last.series),
                 (reading.names, last.names), (reading.players, last.players)]  # fmt: skip
        return any(now is not None and before is not None for now, before in pairs)


def package_observations(package: Path) -> dict[str, dict[int, dict]]:
    sessions = defaultdict(dict)
    with (package / "data" / "observations.csv").open(encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            sessions[row["session_id"]][int(row["frame_id"])] = json.loads(row["observation_json"])
    return sessions


@cache
def package_units(package: Path) -> dict[str, list[dict]]:
    units = defaultdict(list)
    with (package / "data" / "units.csv").open(encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            frames = {key: int(row[key]) for key in ("first_frame", "last_frame", "start_established_at")}
            units[row["session_id"]].append({"unit_id": row["unit_id"], "game": row["game"], **frames})
    return units


def reference_units(session: str, package: Path | None = None) -> list[dict]:
    path = BOUNDARIES / session / "units.json"
    if path.exists() or package is None:
        return json.loads(path.read_text(encoding="utf-8"))["units"]
    # a clone of the public code has no data/: the reference games are those PlayEnd publishes
    return package_units(package)[session]


def detect(observations: dict[int, dict], generic: bool, confirm: bool, portraits=None) -> list[Start]:
    detector = Detector(generic=generic, confirm=confirm, portraits=portraits)
    for frame in sorted(observations):
        detector.observe(frame, observations[frame])
    return detector.starts


def match(units: list[dict], predicted: list[Start], frames: list[int]) -> dict[str, Start]:
    """Each reference game takes the first unused start predicted inside it, or just before its first capture."""
    index = {frame: position for position, frame in enumerate(frames)}
    found, used = {}, set()
    for unit in sorted(units, key=lambda unit: unit["first_frame"]):
        earliest = frames[max(0, index[unit["first_frame"]] - EARLY_TOLERANCE)]
        for start in predicted:
            if id(start) not in used and earliest <= start.frame <= unit["last_frame"]:
                found[unit["unit_id"]] = start
                used.add(id(start))
                break
    return found


def evaluate(package: Path, generic: bool, confirm: bool, portraits: bool = True) -> dict:
    totals, families, lag = Counter(), defaultdict(Counter), []
    for session, observations in sorted(package_observations(package).items()):
        frames, units = sorted(observations), reference_units(session, package)
        predicted = detect(observations, generic, confirm, SessionPortraits(session) if portraits else None)
        found = match(units, predicted, frames)
        for unit in units:
            family = game_family(unit["game"])
            families[family]["games"] += 1
            if unit["unit_id"] in found:
                families[family]["found"] += 1
                lag.append(frames.index(found[unit["unit_id"]].decided_at) - frames.index(unit["start_established_at"]))
        kept = {id(start) for start in found.values()}
        for start in predicted:
            families[start.family]["false"] += id(start) not in kept
        totals["exact"] += len(predicted) == len(units)
        totals["recordings"] += 1
    for counts in families.values():
        totals.update(counts)
    return {"totals": totals, "families": families, "lag": lag}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--package", type=Path, default=REPO / "build" / "playend_v1.1", help="observations to read")
    parser.add_argument("--generic", action="store_true", help="ignore the game profiles, as for an unseen game")
    parser.add_argument("--no-confirm", action="store_true", help="decide on the first opening reading")
    parser.add_argument("--no-portraits", action="store_true", help="do not compare the fighters' portraits")
    args = parser.parse_args()
    result = evaluate(args.package, args.generic, not args.no_confirm, not args.no_portraits)
    totals, lag = result["totals"], sorted(result["lag"])
    games = totals["games"]
    print(
        f"{args.package.name}: {games} games, found {totals['found']} ({totals['found'] / games:.1%}), "
        f"missed {games - totals['found']}, {totals['false']} too many ({100 * totals['false'] / games:.1f} per 100 "
        f"games), exact count on {totals['exact']} of {totals['recordings']} recordings, decision lag median "
        f"{lag[len(lag) // 2]} captures (90 % within {lag[int(0.9 * (len(lag) - 1))]})"
    )
    for family, counts in sorted(result["families"].items(), key=lambda item: -item[1]["games"]):
        print(
            f"  {family[:28]:28s} games {counts['games']:3d}  found {counts['found']:3d}  "
            f"missed {counts['games'] - counts['found']:3d}  too many {counts['false']:3d}"
        )


if __name__ == "__main__":
    main()
