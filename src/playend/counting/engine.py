"""The counter: one capture at a time, it turns the detector's decisions into the games and the time played.

It knows nothing of screens, databases, clocks or prices, so the same code replays a recorded session and runs on the
Pi. Conventions: docs/counting/README.md.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field

from playend.counting.rules import Rules

PER_GAME, TIME_BASED, NOT_BILLED = "per_game", "time_based", "not_billed"  # billing_mode in PlayEnd
UNREAD = (None, "", "unknown")


def game_type(types: Counter, rules: Rules) -> str | None:
    """The type read most often on a game's captures."""
    if not types:
        return None
    top = max(types.values())
    # On a tie, the type with the longer threshold: a doubt goes to the client.
    return max((kind for kind, count in types.items() if count == top), key=rules.threshold)


@dataclass(frozen=True)
class Capture:
    """What the counter needs from one capture: the detector's decisions and what the VLM read."""

    frame: int
    t: float  # seconds on a monotonic clock
    end: bool
    mode: str
    game_type: str | None = None
    game: str | None = None


@dataclass(frozen=True)
class Game:
    first_frame: int
    last_frame: int
    end_frame: int | None  # the capture that ended it; None when it was still open as the client left
    duration_s: int
    game: str | None
    game_type: str | None
    threshold_s: int
    counted: bool
    unseen_s: int = 0  # part of the duration without any image

    def as_dict(self) -> dict:
        return {"kind": "game", **asdict(self)}


@dataclass(frozen=True)
class TimePlayed:
    first_frame: int
    last_frame: int
    duration_s: int
    game: str | None
    unseen_s: int = 0

    def as_dict(self) -> dict:
        return {"kind": "time", **asdict(self)}


@dataclass(frozen=True)
class Count:
    games: int
    quick_restarts: int
    time_s: int
    unseen_s: int


def count(events: list[Game | TimePlayed]) -> Count:
    games = [event for event in events if isinstance(event, Game)]
    runs = [event for event in events if isinstance(event, TimePlayed)]
    counted = [game for game in games if game.counted]
    unseen = sum(game.unseen_s for game in counted) + sum(run.unseen_s for run in runs)
    return Count(len(counted), len(games) - len(counted), sum(run.duration_s for run in runs), unseen)


@dataclass
class Span:
    first: Capture
    last: Capture
    games: Counter = field(default_factory=Counter)
    types: Counter = field(default_factory=Counter)

    @classmethod
    def start(cls, capture: Capture) -> Span:
        span = cls(capture, capture)
        span.extend(capture)
        return span

    def extend(self, capture: Capture) -> None:
        self.last = capture
        if capture.game not in UNREAD:
            self.games[capture.game] += 1
        if capture.game_type not in UNREAD:
            self.types[capture.game_type] += 1

    @property
    def duration_s(self) -> int:
        return int(self.last.t - self.first.t)

    @property
    def game(self) -> str | None:
        return self.games.most_common(1)[0][0] if self.games else None


class Engine:
    def __init__(self, rules: Rules):
        self.rules = rules
        self.game: Span | None = None
        self.time: Span | None = None
        self.pending: Capture | None = None  # an in-play capture carrying an end, waiting for the next one
        self.previous_t: float | None = None
        self.gaps: list[tuple[float, float]] = []  # intervals without an image that an open line may still cover

    def observe(self, capture: Capture) -> list[Game | TimePlayed]:
        if capture.mode not in (PER_GAME, TIME_BASED, NOT_BILLED):
            raise ValueError(f"unknown billing_mode {capture.mode!r}")
        if self.previous_t is not None and capture.t - self.previous_t > self.rules.gap_s:
            self.gaps.append((self.previous_t, capture.t))
        self.previous_t = capture.t
        events = []
        if capture.end and self.game is not None:
            events.append(self.close_game(capture.frame))
        if capture.mode != TIME_BASED and self.time is not None:
            events.append(self.close_time())
        pending, self.pending = self.pending, None
        if capture.mode == PER_GAME:
            if self.game is not None:
                self.game.extend(capture)
            elif capture.end:
                # It may be the last image of the game that just ended: it opens the next one only if play goes on.
                self.pending = capture
            else:
                self.game = Span.start(pending or capture)
                if pending is not None:
                    self.game.extend(capture)
        elif capture.mode == TIME_BASED:
            if self.time is None:
                self.time = Span.start(capture)
            else:
                self.time.extend(capture)
        self.forget_gaps()
        return events

    def close(self) -> list[Game | TimePlayed]:
        """The client leaves: a game still open counts if it already passed its quick-restart threshold."""
        events = []
        if self.game is not None:
            events.append(self.close_game(None))
        if self.time is not None:
            events.append(self.close_time())
        return events

    def unseen(self, span: Span) -> int:
        return int(sum(end - start for start, end in self.gaps if span.first.t <= start and end <= span.last.t))

    def forget_gaps(self) -> None:
        starts = [span.first.t for span in (self.game, self.time) if span is not None]
        if self.pending is not None:
            starts.append(self.pending.t)
        self.gaps = [gap for gap in self.gaps if starts and gap[0] >= min(starts)]

    def close_game(self, end_frame: int | None) -> Game:
        span, self.game = self.game, None
        kind = game_type(span.types, self.rules)
        threshold = self.rules.threshold(kind)
        return Game(
            first_frame=span.first.frame,
            last_frame=span.last.frame,
            end_frame=end_frame,
            duration_s=span.duration_s,
            game=span.game,
            game_type=kind,
            threshold_s=threshold,
            counted=span.duration_s >= threshold,
            unseen_s=self.unseen(span),
        )

    def close_time(self) -> TimePlayed:
        span, self.time = self.time, None
        return TimePlayed(span.first.frame, span.last.frame, span.duration_s, span.game, self.unseen(span))
