import unittest

import numpy as np
from PIL import Image

from playend.student.read import TEMPLATES, WARZONE_DIGITS, WARZONE_ICONS, warzone_counters
from playend.student.rules import read_fields


class GreyReader:
    """Reads a box as the number given by its grey level, so a test can write digits as colours."""

    def recognise(self, crop):
        return str(round(float(np.asarray(crop, dtype=float).mean()))), 1.0


def warzone(icons: dict, digits: dict) -> Image.Image:
    frame = Image.new("RGB", (1280, 720))
    for slot, name in icons.items():
        frame.paste(Image.open(TEMPLATES / f"{name}.png"), WARZONE_ICONS[slot][:2])
    for slot, value in digits.items():
        frame.paste((value, value, value), WARZONE_DIGITS[slot])
    return frame


class WarzoneTest(unittest.TestCase):
    def test_three_counters(self):
        frame = warzone({0: "warzone_squad", 1: "warzone_player"}, {0: 10, 1: 31, 2: 4})
        self.assertEqual(warzone_counters(GreyReader(), frame), {"teams_remaining": 10, "players_remaining": 31})

    def test_two_counters_moved_one_slot_to_the_right(self):
        frame = warzone({1: "warzone_squad", 2: "warzone_player"}, {1: 14, 2: 52})
        self.assertEqual(warzone_counters(GreyReader(), frame), {"teams_remaining": 14, "players_remaining": 52})

    def test_fewer_players_than_squads_is_left_unread(self):
        frame = warzone({0: "warzone_squad", 1: "warzone_player"}, {0: 40, 1: 31})
        self.assertIsNone(warzone_counters(GreyReader(), frame)["players_remaining"])


def line(text: str, centre_x: int, centre_y: int, zone: int = 0) -> list:
    return [text, 0.99, zone, centre_x - 10, centre_y - 8, centre_x + 10, centre_y + 8]


class FortniteSplitTest(unittest.TestCase):
    zones = {"split": 2, "solo": 1, "multi": 3, "og": 2}

    def test_both_views_give_the_same_count(self):
        readings = {"og": [line("98", 880, 160), line("98", 1200, 520, zone=1)]}
        self.assertEqual(read_fields("Fortnite", readings, self.zones), {"players_remaining": 98})

    def test_a_number_in_one_view_only_is_not_a_count(self):
        readings = {"og": [line("30", 880, 160)]}
        self.assertEqual(read_fields("Fortnite", readings, self.zones), {})


if __name__ == "__main__":
    unittest.main()
