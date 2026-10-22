import unittest

from playend.dataset.croissant import field, slug
from playend.dataset.features import nanoseconds
from playend.dataset.pseudonyms import Pseudonyms
from playend.dataset.tables import seconds, split_rows

# Invented names: the real list never appears in the code or the tests.
NAMES = ["Rex_77", "Rex_77X", "[AB]Big Cat", "zed"]


class PseudonymsTest(unittest.TestCase):
    def test_same_name_any_case_gets_the_same_pseudonym(self):
        pseudonyms = Pseudonyms(NAMES)
        self.assertEqual(pseudonyms.text("Rex_77"), "player_001")
        self.assertEqual(pseudonyms.text("REX_77 A ÉLIMINÉ zed"), "player_001 A ÉLIMINÉ player_002")

    def test_longest_name_wins(self):
        pseudonyms = Pseudonyms(NAMES)
        self.assertEqual(pseudonyms.text("Rex_77X"), "player_001")
        self.assertEqual(pseudonyms.text("Rex_77"), "player_002")
        self.assertEqual(pseudonyms.text("[AB]Big Cat"), "player_003")

    def test_only_whole_tokens_are_replaced(self):
        pseudonyms = Pseudonyms(NAMES)
        self.assertEqual(pseudonyms.text("zedonk Rex_771"), "zedonk Rex_771")

    def test_every_string_of_an_observation_is_replaced(self):
        pseudonyms = Pseudonyms(NAMES)
        obs = {
            "participants": {"primary": ["zed", "Mileena"], "count_visible": 2},
            "visible_entities": ["VOUS REGARDEZ : ZED"],
        }
        self.assertEqual(
            pseudonyms.value(obs),
            {
                "participants": {"primary": ["player_001", "Mileena"], "count_visible": 2},
                "visible_entities": ["VOUS REGARDEZ : player_001"],
            },
        )


class TimeTest(unittest.TestCase):
    def test_seconds_are_exact(self):
        self.assertEqual(seconds(0), "0.000000000")
        self.assertEqual(seconds(28_686_481_396), "28.686481396")
        for value in (0, 1, 999_999_999, 1_000_000_000, 31_937_215_000_123):
            self.assertEqual(nanoseconds(seconds(value)), value)


class SplitTest(unittest.TestCase):
    def test_each_session_lies_in_one_fold_and_the_split_is_stable(self):
        sessions = [
            {"session_id": f"session_{index:02d}", "boundary_count": index % 7, "frame_count": 50 + 30 * index}
            for index in range(12)
        ]
        rows = split_rows(sessions)
        self.assertEqual(sorted(row["session_id"] for row in rows), [row["session_id"] for row in sessions])
        self.assertTrue(all(1 <= row["fold"] <= 5 for row in rows))
        self.assertEqual(rows, split_rows(list(reversed(sessions))))


class CroissantTest(unittest.TestCase):
    def test_labels_and_references(self):
        target = field("observations", "unit_end_boundary", "sc:Integer", "end of a game")
        self.assertEqual(target["dataType"], ["sc:Integer", "cr:Label"])
        session = field("units", "session_id", "sc:Text", "session")
        self.assertEqual(session["references"], {"field": {"@id": "sessions/session_id"}})
        self.assertNotIn("references", field("sessions", "session_id", "sc:Text", "session"))
        self.assertEqual(session["source"]["fileObject"], {"@id": "data/units.csv"})

    def test_agent_ids(self):
        self.assertEqual(slug("Claude Opus 5.5"), "claude-opus-5-5")


if __name__ == "__main__":
    unittest.main()
