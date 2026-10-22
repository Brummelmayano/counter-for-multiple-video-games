import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from playend.training import baselines, columns, events, figures, protocol, run, search
from playend.training.data import Corpus, Sequence
from playend.training.store import Store


def sequence(name="s1", fold=1, ends=(), masked=(), rows=12, features=None):
    end = np.zeros(rows, dtype=np.int8)
    end[list(ends) + list(masked)] = 1
    usable = np.ones(rows, dtype=bool)
    usable[0] = False
    usable[list(masked)] = False
    return Sequence(
        session=name,
        fold=fold,
        t=np.arange(rows, dtype=float) * 30,
        x=features if features is not None else np.zeros((rows, 3), dtype=np.float32),
        end=end,
        usable=usable,
        billing=np.zeros(rows, dtype=np.int64),
        family=["EA Sports FC"] * rows,
        readable={},
    )


class MatchTest(unittest.TestCase):
    def test_on_time_late_and_false(self):
        s = sequence(ends=(3, 7))
        prob = np.zeros(12, dtype=np.float32)
        prob[[4, 7, 10]] = 0.9  # one capture late, on time, and an end that did not happen
        found, missed, false = events.match(s, prob, 0.5)
        self.assertEqual((found, missed, false), ([3, 7], [], [10]))

    def test_consecutive_rows_are_one_prediction(self):
        s = sequence(ends=(3,))
        prob = np.zeros(12, dtype=np.float32)
        prob[3:6] = 0.9
        self.assertEqual(events.match(s, prob, 0.5), ([3], [], []))

    def test_two_captures_late_is_missed_and_false(self):
        s = sequence(ends=(3,))
        prob = np.zeros(12, dtype=np.float32)
        prob[5] = 0.9
        self.assertEqual(events.match(s, prob, 0.5), ([], [3], [5]))

    def test_masked_end_creates_no_false_end(self):
        s = sequence(masked=(5,))
        prob = np.zeros(12, dtype=np.float32)
        prob[6] = 0.9
        self.assertEqual(events.match(s, prob, 0.5), ([], [], []))

    def test_lowest_threshold_within_budget(self):
        s = sequence(ends=(3,))
        prob = np.full(12, 0.1, dtype=np.float32)
        prob[3], prob[9] = 0.9, 0.6
        threshold, result = events.pick_thresholds([s], {"s1": prob}, (0.0,))[0.0]
        self.assertGreater(threshold, 0.6)
        self.assertEqual((result.found, result.false), (1, 0))


class ColumnsTest(unittest.TestCase):
    def test_constant_copy_and_complement_are_dropped(self):
        a = np.array([0, 1, 0, 1], dtype=np.float32)
        b = np.array([0.5, 2.0, 3.0, 1.0], dtype=np.float32)
        x = np.stack([a, np.ones(4, dtype=np.float32), a.copy(), 1 - a, b], axis=1)
        self.assertEqual(columns.informative(x), [0, 4])

    def test_groups_do_not_overlap(self):
        self.assertEqual(columns.group_of("counter.lives.a.delta_candidate"), "counters")
        self.assertEqual(columns.group_of("score.a.delta_candidate"), "changes")
        self.assertEqual(columns.group_of("secondary.respawn.count"), "timers")
        self.assertIsNone(columns.group_of("score.a"))


class BaselinesTest(unittest.TestCase):
    def test_window_adds_previous_rows(self):
        x = np.arange(6, dtype=np.float32).reshape(3, 2)
        windowed = baselines.window(x, 2)
        self.assertEqual(windowed.shape, (3, 6))
        self.assertEqual(windowed[2].tolist(), [4, 5, 2, 3, 0, 1])
        self.assertEqual(windowed[0].tolist(), [0, 1, 0, 0, 0, 0])


class FiguresTest(unittest.TestCase):
    def test_spans_of_masked_rows(self):
        mask = np.array([True, True, False, True, False, False, True])
        self.assertEqual(figures.spans(mask), [(0, 1), (3, 3), (6, 6)])


class SearchTest(unittest.TestCase):
    def test_trials_are_fixed_and_in_range(self):
        first, again = search.trials("gru"), search.trials("gru")
        self.assertEqual(first, again)
        self.assertEqual(len(first), search.TRIALS["gru"])
        for config in first:
            self.assertIn(config["hidden"], (16, 32, 64))
            self.assertTrue(3e-4 <= config["learning_rate"] <= 3e-3)


class StoreTest(unittest.TestCase):
    def test_a_job_is_done_once_its_record_exists(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder))
            self.assertFalse(store.done("job"))
            store.save("job", {"seconds": 1.0}, {"s1": np.ones(3, dtype=np.float32)})
            self.assertTrue(store.done("job"))
            self.assertEqual(store.arrays("job")["s1"].tolist(), [1, 1, 1])
            self.assertEqual(list(Path(folder, "jobs").glob(".*.tmp")), [])

    def test_leftovers_of_a_killed_job_are_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder))
            Path(folder, "jobs", ".job.json.123.tmp").write_text("{")
            store.remove_leftovers()
            self.assertEqual(list(Path(folder, "jobs").iterdir()), [])


class RoundTest(unittest.TestCase):
    def setUp(self):
        sequences = {f"s{i}": sequence(f"s{i}", fold=(i % 5) + 1) for i in range(10)}
        self.corpus = Corpus(sequences, ["a", "b", "c"], "sha", {})

    def test_held_out_fold_is_not_a_validation_fold(self):
        self.assertEqual(protocol.inner_folds(self.corpus, "s0"), [2, 3, 4, 5])
        self.assertEqual(protocol.inner_folds(self.corpus, protocol.ALL), [1, 2, 3, 4, 5])

    def test_held_out_session_never_trains_nor_validates(self):
        for fold in protocol.inner_folds(self.corpus, "s0"):
            train, valid = protocol.split(self.corpus, "s0", fold)
            names = {s.session for s in train + valid}
            self.assertNotIn("s0", names)
            self.assertEqual(len(names), 9)
            self.assertTrue(all(s.fold == fold for s in valid))

    def test_a_group_that_costs_nothing_goes(self):
        full = {"recall": 0.5, "average_precision": 0.6}
        alone = dict.fromkeys(protocol.GROUPS, {"recall": 0.4, "average_precision": 0.9})
        alone["timers"] = {"recall": 0.5, "average_precision": 0.6}
        self.assertEqual(protocol.groups_to_drop(full, alone), ("timers",))

    def test_job_ids_are_stable(self):
        job = protocol.Job("search", "gru", "session_abcdef123456", 2, 3, ("timers",))
        self.assertEqual(job.id, "search-gru-abcdef12-f2-t3-dtimers-r7")


class WorkersTest(unittest.TestCase):
    def test_workers_fit_in_the_free_memory(self):
        with mock.patch.object(run, "free_memory_gb", return_value=4.2), mock.patch("os.cpu_count", return_value=10):
            self.assertEqual(run.default_workers("cpu"), 3)  # not 9: 1 GB a worker, 1 GB left free

    def test_free_memory_is_read_on_this_machine(self):
        memory = run.free_memory_gb()
        self.assertTrue(memory is None or memory > 0)


if __name__ == "__main__":
    unittest.main()
