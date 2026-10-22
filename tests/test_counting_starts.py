import unittest

import numpy as np

from playend.counting.starts import detect


def screen(title, screen_type="gameplay", phase="active", score=(None, None), clock=None, seconds=None,
           period=("none", None), lap=None, players=None, lives=None):  # fmt: skip
    counters = []
    if players is not None:
        counters.append({"kind": "players_remaining", "side": "field", "value": players})
    for side, value in zip("ab", lives or ()):
        counters.append({"kind": "lives", "side": side, "value": value})
    return {
        "game": {"title": title},
        "state": {"phase": phase, "screen_type": screen_type},
        "score": {"a": score[0], "b": score[1]},
        "clock": {"display": clock, "value_seconds": seconds},
        "period": {"type": period[0], "number": period[1]},
        "progress": {"type": "lap" if lap is not None else None, "current": lap},
        "secondary_counters": counters,
    }


def football(home, away, minute):
    return screen("EA Sports FC 26", score=(home, away), clock=f"{minute}:00", seconds=minute * 60)


def starts(*screens):
    return [start.frame for start in detect(dict(enumerate(screens, 1)), generic=False, confirm=True)]


class StartsTest(unittest.TestCase):
    def test_a_kickoff_confirmed_by_the_next_reading(self):
        self.assertEqual(starts(football(0, 0, 2), football(0, 0, 9), football(1, 0, 30)), [1])

    def test_a_pause_does_not_open_a_new_game(self):
        pause = screen("EA Sports FC 26", screen_type="pause", phase="paused")
        self.assertEqual(starts(football(0, 0, 3), football(1, 0, 20), pause, football(1, 0, 25)), [1])

    def test_a_new_match_seen_after_its_kickoff(self):
        # the clock goes back from minute 90 to minute 12: another match, already 1-0
        self.assertEqual(starts(football(0, 0, 3), football(2, 1, 90), football(1, 0, 12), football(1, 0, 20)), [1, 3])

    def test_a_single_misread_score_does_not_open_a_game(self):
        self.assertEqual(starts(football(0, 0, 3), football(2, 2, 40), football(0, 2, 45), football(2, 2, 50)), [1])

    def test_a_penalty_shoot_out_is_not_a_new_match(self):
        shootout = screen("EA Sports FC 26", score=(0, 0), period=("other", None))
        self.assertEqual(starts(football(0, 0, 3), football(3, 3, 120), shootout, football(3, 3, 120)), [1])

    def test_a_new_fight_after_the_previous_one_ended_unseen(self):
        fight = [screen("Mortal Kombat 1", score=score, clock="80") for score in ((0, 0), (1, 1), (0, 0), (1, 0))]
        self.assertEqual(starts(*fight), [1, 3])

    def test_mortal_kombat_training_is_never_a_game(self):
        training = screen("Mortal Kombat 1", clock="∞")
        self.assertEqual(starts(training, training, training), [])

    def test_an_island_left_before_the_bus_is_not_a_game(self):
        island = screen("Fortnite", phase="pre_game", players=96)
        menu = screen("Fortnite", screen_type="menu", phase="menu")
        match = screen("Fortnite", players=98)
        self.assertEqual(starts(island, island, menu, island, match), [4])

    def test_an_island_read_as_play_counts_only_once_players_drop(self):
        island_as_play = screen("Fortnite", players=96)
        menu = screen("Fortnite", screen_type="menu", phase="menu")
        self.assertEqual(starts(island_as_play, island_as_play, menu), [])
        self.assertEqual(starts(island_as_play, screen("Fortnite", players=90)), [1])

    def test_a_lone_misread_score_does_not_make_the_next_ones_look_lower(self):
        self.assertEqual(
            starts(football(0, 0, 3), football(1, 1, 15), football(2, 2, 20), football(1, 1, 25), football(1, 2, 30)),
            [1],
        )

    def test_a_lone_selection_screen_in_a_match_does_not_open_a_game(self):
        selection = screen("EA Sports FC 26", screen_type="team_select", phase="pre_game")
        self.assertEqual(starts(football(0, 0, 3), football(1, 0, 20), selection, football(1, 0, 25)), [1])

    def test_a_selection_screen_that_lasts_opens_a_fight_seen_under_way(self):
        selection = screen("Mortal Kombat 1", screen_type="character_select", phase="pre_game")
        fight = [screen("Mortal Kombat 1", score=score, clock="80") for score in ((0, 0), (1, 0), (1, 0))]
        self.assertEqual(starts(*fight[:2], selection, selection, fight[2]), [1])
        self.assertEqual(starts(*fight[:2], selection, selection, selection, fight[2]), [1, 6])

    def test_a_match_seen_under_way_after_a_result_screen(self):
        result = screen("EA Sports FC 26", screen_type="result", phase="post_game")
        self.assertEqual(starts(football(0, 0, 3), football(3, 1, 88), result, football(0, 1, 30)), [1, 4])

    def test_a_dragon_ball_fight_after_the_selection_screen(self):
        selection = screen("Dragon Ball Sparking! ZERO", screen_type="character_select", phase="pre_game")
        fight = [screen("Dragon Ball Sparking! ZERO", lives=lives) for lives in ((3, 3), (3, 1))]
        self.assertEqual(starts(*fight, selection, *fight), [1, 4])

    def test_a_race_after_its_result_table(self):
        result = screen("Beach Buggy Racing 2", screen_type="result", phase="post_game")
        race = [screen("Beach Buggy Racing 2", lap=lap) for lap in (1, 1)]
        self.assertEqual(starts(*race, result, *race), [1, 4])

    def test_the_endless_clock_opens_a_fight_quit_at_once(self):
        fight = screen("Dragon Ball Sparking! ZERO", lives=(4, 4))
        opening = screen("Dragon Ball Sparking! ZERO", clock="∞", lives=(4, 4))
        menu = screen("Dragon Ball Sparking! ZERO", screen_type="menu", phase="menu")
        self.assertEqual(starts(fight, fight, opening, menu), [1, 3])

    def test_the_same_fighter_with_more_health_bars_was_started_again(self):
        fight = [screen("Dragon Ball Sparking! ZERO", lives=lives) for lives in ((3, 3), (3, 1), (3, 4))]
        same_face = lambda frame, family, side: np.zeros((26, 24))  # noqa: E731
        other_face = lambda frame, family, side: np.full((26, 24), 40.0 * frame)  # noqa: E731
        self.assertEqual([s.frame for s in detect(dict(enumerate(fight, 1)), False, True, same_face)], [1, 3])
        self.assertEqual([s.frame for s in detect(dict(enumerate(fight, 1)), False, True, other_face)], [1])

    def test_a_dragon_ball_fighter_coming_in_with_full_lives_is_the_same_fight(self):
        fight = [screen("Dragon Ball Sparking! ZERO", lives=lives) for lives in ((7, 7), (2, 5), (7, 5))]
        opening = screen("Dragon Ball Sparking! ZERO", clock="∞", lives=(7, 7))
        self.assertEqual(starts(opening, *fight), [1])


if __name__ == "__main__":
    unittest.main()
