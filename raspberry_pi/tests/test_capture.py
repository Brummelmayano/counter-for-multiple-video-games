import csv
import importlib.util
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("capture", ROOT / "capture.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class Clock:
    def __init__(self):
        self.ns = 1_000_000_000
        self.stopped = False
    def now(self):
        return self.ns
    def is_set(self):
        return self.stopped
    def wait(self, seconds):
        self.ns += round(seconds * 1e9)
        return self.stopped


class MemoryStore:
    def __init__(self, clock, write_s=0):
        self.clock = clock
        self.write_s = write_s
        self.count = 0
        self.rows = []
        self.events = []
        self.state = None
        self.free = True
    def space_ok(self):
        return self.free
    def event(self, name, **kwargs):
        self.events.append(name)
    def status(self, state, **kwargs):
        self.state = state
    def save(self, frame, interval, scheduled):
        self.rows.append((frame["received_monotonic_ns"], interval, scheduled))
        self.count += 1
        self.clock.wait(self.write_s)
        return True


class Client:
    def __init__(self, clock, failures=0):
        self.clock = clock
        self.failures = failures
    def capture(self, stop):
        if self.failures:
            self.failures -= 1
            return {"ok": False, "error": "absent"}
        return {"ok": True, "received_monotonic_ns": self.clock.now()}


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.cfg = c.load_config(ROOT / "config.json")
        self.clock = Clock()

    def run_case(self, store, client, count=5):
        c.collect(self.cfg, store, client, self.clock, random.Random(123), count, self.clock.now)

    def test_interval_includes_writing(self):
        store = MemoryStore(self.clock, write_s=3)
        self.run_case(store, Client(self.clock))
        for previous, current in zip(store.rows, store.rows[1:]):
            self.assertAlmostEqual((current[0]-previous[0])/1e9, current[1], places=7)
            self.assertGreaterEqual(current[1], 10)
            self.assertLessEqual(current[1], 45)

    def test_slow_storage_does_not_invent_missing_frames(self):
        store = MemoryStore(self.clock, write_s=60)
        self.run_case(store, Client(self.clock))
        self.assertEqual(store.count, 5)
        for previous, current in zip(store.rows, store.rows[1:]):
            self.assertEqual((current[0]-previous[0])/1e9, 60)
            self.assertGreater(current[0], current[2])

    def test_reconnect_no_fake_images(self):
        store = MemoryStore(self.clock)
        self.run_case(store, Client(self.clock, failures=3), 2)
        self.assertEqual(store.rows[0][0], 16_000_000_000)
        self.assertEqual(store.events.count("video_unavailable"), 1)
        self.assertIn("video_recovered", store.events)
        self.assertEqual(store.count, 2)

    def test_full_storage_stops_without_capture(self):
        store = MemoryStore(self.clock)
        store.free = False
        self.run_case(store, Client(self.clock))
        self.assertEqual(store.count, 0)
        self.assertEqual(store.state, "storage_full")

    def test_stop_while_waiting(self):
        store = MemoryStore(self.clock)
        self.clock.stopped = True
        self.run_case(store, Client(self.clock))
        self.assertEqual(store.count, 0)
        self.assertEqual(store.state, "stopped")

    def test_seed_reproducible(self):
        s1 = MemoryStore(self.clock)
        self.run_case(s1, Client(self.clock))
        self.clock = Clock()
        s2 = MemoryStore(self.clock)
        self.run_case(s2, Client(self.clock))
        self.assertEqual(s1.rows, s2.rows)

    def test_mid_session_disconnect_preserves_gap(self):
        store = MemoryStore(self.clock)
        client = Client(self.clock)
        original = client.capture
        calls = 0
        def response(stop):
            nonlocal calls
            calls += 1
            if calls in (2, 3):
                return {"ok": False, "error": "cable unplugged"}
            return original(stop)
        client.capture = response
        self.run_case(store, client, 2)
        self.assertAlmostEqual((store.rows[1][0]-store.rows[0][0])/1e9, store.rows[1][1]+10, places=7)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cfg = c.load_config(ROOT / "config.json")
        self.cfg["reserve_free_gib"] = 0.001
        self.store = c.Store(Path(self.temp.name), self.cfg, 123)
    def tearDown(self):
        self.store.close()
        self.temp.cleanup()
    def frame(self, ns):
        return {"jpeg": b"\xff\xd8test\xff\xd9", "received_monotonic_ns": ns,
                "received_wall_utc": "2026-01-01T00:00:00+00:00", "encode_ms": 1,
                "width": 1280, "height": 720, "device": "FAKE_TEST_ONLY"}
    def test_saved_image_matches_index_and_hash(self):
        frame = self.frame(self.store.start_ns+10)
        self.assertTrue(self.store.save(frame, 0, self.store.start_ns))
        rows = list(csv.DictReader((self.store.path / "captures.csv").read_text().splitlines()))
        data = (self.store.path / rows[0]["filename"]).read_bytes()
        self.assertEqual(data, frame["jpeg"])
        self.assertEqual(rows[0]["sha256"], c.hashlib.sha256(data).hexdigest())
        self.assertEqual(rows[0]["delta_t_s"], "")
    def test_wall_clock_change_does_not_change_delta(self):
        ns = self.store.start_ns
        first, second = self.frame(ns), self.frame(ns+27_000_000_000)
        second["received_wall_utc"] = "2020-01-01T00:00:00+00:00"
        self.store.save(first, 0, ns)
        self.store.save(second, 27, ns+27_000_000_000)
        rows = list(csv.DictReader((self.store.path / "captures.csv").read_text().splitlines()))
        self.assertEqual(float(rows[1]["delta_t_s"]), 27)
    def test_identical_pixels_are_kept_if_distinct_receptions(self):
        self.store.save(self.frame(self.store.start_ns), 0, self.store.start_ns)
        self.store.save(self.frame(self.store.start_ns+10_000_000_000), 10, self.store.start_ns+10_000_000_000)
        self.assertEqual(len(list(self.store.path.rglob("*.jpg"))), 2)
    def test_same_reception_rejected(self):
        frame = self.frame(self.store.start_ns)
        self.store.save(frame, 0, self.store.start_ns)
        with self.assertRaises(RuntimeError):
            self.store.save(frame, 10, self.store.start_ns)
    def test_low_space_no_image_deleted_or_created(self):
        with patch.object(self.store, "space_ok", return_value=False):
            self.assertFalse(self.store.save(self.frame(self.store.start_ns), 0, self.store.start_ns))
        self.assertEqual(list(self.store.path.rglob("*.jpg")), [])
    def test_sessions_never_overwritten(self):
        other = c.Store(Path(self.temp.name), self.cfg, 123)
        try:
            self.assertNotEqual(self.store.path, other.path)
            self.assertTrue((self.store.path / "metadata.json").exists())
        finally:
            other.close()
    def test_crash_between_image_and_index_leaves_orphan_not_false_index(self):
        with patch.object(self.store, "writer") as writer:
            writer.writerow.side_effect = OSError("simulated card error")
            with self.assertRaises(OSError):
                self.store.save(self.frame(self.store.start_ns), 0, self.store.start_ns)
        self.assertEqual(len(list(self.store.path.rglob("*.jpg"))), 1)
        self.assertEqual(len(list(csv.DictReader((self.store.path / "captures.csv").read_text().splitlines()))), 0)


class ConfigurationTests(unittest.TestCase):
    def test_bad_intervals(self):
        cfg = c.load_config(ROOT / "config.json")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            for lo, hi in [(0,45), (50,45), (float('nan'),45), (10,float('inf'))]:
                cfg.update(interval_min_s=lo, interval_max_s=hi)
                path.write_text(json.dumps(cfg))
                with self.assertRaises(ValueError):
                    c.load_config(path)


if __name__ == "__main__":
    unittest.main()
