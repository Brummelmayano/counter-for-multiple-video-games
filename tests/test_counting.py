import unittest
from collections import Counter

from playend.counting import rules as counting_rules
from playend.counting.engine import (
    NOT_BILLED,
    PER_GAME,
    TIME_BASED,
    Capture,
    Count,
    Engine,
    Game,
    TimePlayed,
    count,
    game_type,
)

RULES = counting_rules.Rules("test", {"football": 60, "combat": 15}, gap_s=60)


def play(t, kind="football", end=False):
    return (t, PER_GAME, end, kind)


def menu(t, end=False):
    return (t, NOT_BILLED, end, None)


def mission(t):
    return (t, TIME_BASED, False, None)


def run(steps: list[tuple]) -> list[Game | TimePlayed]:
    engine = Engine(RULES)
    events = []
    for frame, (t, mode, end, kind) in enumerate(steps):
        events += engine.observe(Capture(frame, t, end, mode, kind, kind))
    return events + engine.close()


class RulesTest(unittest.TestCase):
    def test_rules_of_the_repository(self):
        rules = counting_rules.load()
        self.assertEqual((rules.threshold("combat"), rules.threshold("football")), (15, 60))
        self.assertEqual(rules.threshold("other"), 60)  # a type without its own threshold gets the longest
        self.assertEqual(rules.gap_s, 60)

    def test_a_tie_between_types_goes_to_the_longer_threshold(self):
        self.assertEqual(game_type(Counter(combat=2, football=2), RULES), "football")
        self.assertIsNone(game_type(Counter(), RULES))


class EngineTest(unittest.TestCase):
    def test_a_quick_restart_does_not_count(self):
        combat = run([play(0, "combat"), play(10, "combat"), menu(40, end=True)])
        self.assertEqual([(game.duration_s, game.counted) for game in combat], [(10, False)])
        football = run([play(0), play(59.9), play(90, end=True)])
        self.assertFalse(football[0].counted)

    def test_a_pause_does_not_close_a_game(self):
        events = run([play(0), menu(30), play(60), menu(90, end=True)])
        game = events[0]
        self.assertEqual(
            (len(events), game.first_frame, game.last_frame, game.end_frame, game.counted), (1, 0, 2, 3, True)
        )

    def test_an_end_without_a_game_counts_nothing(self):
        self.assertEqual(run([menu(0, end=True), menu(30, end=True)]), [])

    def test_the_end_capture_opens_the_next_game_only_if_play_goes_on(self):
        start = [play(0, "combat"), play(30, "combat"), play(60, "combat", end=True)]
        rematch = run([*start, play(90, "combat")])
        self.assertEqual([game.first_frame for game in rematch], [0, 2])
        back_to_menus = run([*start, menu(90), play(400, "combat"), play(430, "combat")])
        self.assertEqual([(game.first_frame, game.duration_s) for game in back_to_menus], [(0, 30), (4, 30)])

    def test_a_game_open_when_the_client_leaves(self):
        long_enough = run([play(0), play(100)])
        self.assertEqual((long_enough[0].end_frame, long_enough[0].counted), (None, True))
        self.assertFalse(run([play(0), play(30)])[0].counted)

    def test_time_runs_are_measured_one_by_one(self):
        events = run([mission(0), mission(240), menu(270), mission(300), mission(540)])
        self.assertEqual([(event.first_frame, event.duration_s) for event in events], [(0, 240), (3, 240)])

    def test_time_without_an_image_stays_counted_and_is_shown(self):
        game = run([play(0), play(30), play(130), play(160), menu(190, end=True)])[0]
        self.assertEqual((game.duration_s, game.unseen_s, game.counted), (160, 100, True))
        paused = run([play(0), menu(30), menu(130), play(160), menu(190, end=True)])[0]
        self.assertEqual(paused.unseen_s, 100)  # no image during the pause either
        time = run([mission(0), mission(30), mission(400), menu(430)])[0]
        self.assertEqual((time.duration_s, time.unseen_s), (400, 370))

    def test_a_gap_after_the_last_image_in_play_is_not_shown(self):
        game = run([play(0), play(30), play(60), menu(200), menu(230, end=True)])[0]
        self.assertEqual((game.duration_s, game.unseen_s), (60, 0))

    def test_an_unknown_mode_is_refused(self):
        with self.assertRaises(ValueError):
            Engine(RULES).observe(Capture(0, 0.0, False, "partie"))


class CountTest(unittest.TestCase):
    def test_count_of_a_client(self):
        events = [
            Game(0, 1, 2, 90, "Tekken 8", "combat", 15, True),
            Game(3, 4, 5, 400, "EA Sports FC", "football", 60, True, unseen_s=70),
            Game(6, 6, 7, 0, "EA Sports FC", "football", 60, False, unseen_s=30),  # not counted: its gap neither
            TimePlayed(8, 20, 600, "GTA V", unseen_s=90),
            TimePlayed(22, 30, 240, "GTA V"),
        ]
        self.assertEqual(count(events), Count(games=2, quick_restarts=1, time_s=840, unseen_s=160))


if __name__ == "__main__":
    unittest.main()
