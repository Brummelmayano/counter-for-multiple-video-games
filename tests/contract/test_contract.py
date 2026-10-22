import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from playend.contract import (
    empty_observation,
    legacy_v1,
    output_schema,
    parse_strict_json,
    upgrade_legacy,
    upgrade_v20,
    validate_any,
    validate_observation,
)
from playend.contract.build_assets import assets
from playend.contract.prepare_dataset import build_rows, labels_by_frame, load_records
from playend.contract.temporal import FeatureStream, assert_checkpoint_compatible, feature_spec


def timer(value=44, kind="storm_phase"):
    return {
        "kind": kind,
        "label": None,
        "display": f"{value // 60}:{value % 60:02}",
        "value_seconds": value,
        "direction": "unknown",
    }


def counter(kind, side, value, total=None, label=None):
    return {"kind": kind, "side": side, "value": value, "total": total, "label": label}


def observation(timers=None):
    obj = empty_observation()
    obj["game"].update(title="Test game", type="other", mode="test")
    obj["period"]["type"] = "none"
    obj["clock"]["visible"] = False
    obj["secondary_timers"] = timers
    return obj


def record(obj=None, frame=1, seconds=0, session="test", reviewed=False):
    return {
        "session_id": session,
        "frame_id": frame,
        "received_monotonic_ns": 10**18 + int(seconds * 1e9),
        "observation": obj if obj is not None else observation(),
        "review_status": "human_verified" if reviewed else "proposed_pending_human_review",
    }


class ContractTest(unittest.TestCase):
    def test_generated_assets_are_current(self):
        for path, expected in assets().items():
            self.assertEqual(path.read_text(), expected, str(path))

    def test_v2_examples_and_strict_schema(self):
        import jsonschema

        jsonschema.Draft202012Validator.check_schema(output_schema())
        for timers in (None, [], [timer()], [timer(0), timer(15, "respawn")], [timer(), timer(19)]):
            obj = observation(timers)
            self.assertEqual(validate_observation(obj), [])
            jsonschema.validate(obj, output_schema())

    def test_unreadable_timer_and_ambiguous_role(self):
        obj = observation([dict(timer(), kind="unknown", display=None, value_seconds=None)])
        obj["clock"]["visible"] = None
        self.assertEqual(validate_observation(obj), [])

    def test_time_conversion_and_single_image_direction(self):
        for display, seconds, valid in (
            ("0:44", 44, True),
            ("1:02:03", 3723, True),
            ("72", 72, True),
            ("0:44", 45, False),
            ("8'", 480, False),
            ("90+3'", 5580, False),
            ("8'", None, True),
            (None, 44, False),
            ("0:99", 99, False),
            ("00:00.50", 0.5, True),
        ):
            obj = observation()
            obj["clock"].update(visible=True, display=display, value_seconds=seconds, direction="unknown")
            self.assertEqual(not validate_observation(obj), valid, display)
        obj["clock"]["direction"] = "countdown"
        self.assertTrue(validate_observation(obj))

    def test_bad_types_temporal_keys_and_unknown_versions(self):
        changes = [
            ("value_seconds", True),
            ("value_seconds", float("nan")),
            ("value_seconds", -1),
            ("kind", []),
            ("label", 45),
            ("direction", "countdown"),
        ]
        for key, value in changes:
            obj = observation([timer()])
            obj["secondary_timers"][0][key] = value
            self.assertTrue(validate_observation(obj), (key, value))
        obj = observation([timer()])
        obj["secondary_timers"][0]["unit_end_boundary"] = 1
        self.assertTrue(validate_observation(obj))
        obj = observation()
        obj["schema_version"] = "999"
        self.assertTrue(validate_any(obj))
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', "[]"):
            self.assertTrue(parse_strict_json(raw)[1])

    def test_migration_preserves_source_and_masks_unreviewed_clock(self):
        old = legacy_v1.empty_observation()
        old["clock"].update(visible=True, display="0:44", value_seconds=44, direction="unknown")
        before = copy.deepcopy(old)
        self.assertEqual(validate_any(old), [])
        new = upgrade_legacy(old)
        self.assertEqual(old, before)
        self.assertIsNone(new["secondary_timers"])
        self.assertIsNone(new["clock"]["value_seconds"])
        self.assertEqual(validate_observation(new), [])
        self.assertTrue(validate_observation(old))

    def test_legacy_proposals_remain_readable(self):
        paths = sorted((Path(__file__).resolve().parent / "fixtures" / "legacy_v1_observations").rglob("*.json"))
        self.assertGreaterEqual(len(paths), 4)
        for path in paths:
            self.assertEqual(validate_any(json.loads(path.read_text())), [], str(path))

    def test_secondary_reset_never_populates_main_clock_or_target(self):
        stream = FeatureStream()
        for i, seconds in enumerate((44, 0, 180)):
            features = stream.step(record(observation([timer(seconds)]), i + 1, i * 27))
            self.assertEqual(features["clock.value_seconds.known"], 0)
            self.assertEqual(features["clock.value_seconds.delta_candidate.known"], 0)
            self.assertEqual(features["secondary.storm_phase.minimum_seconds.known"], 1)
            self.assertNotIn("unit_end_boundary", features)
        rows = build_rows([record(observation([timer(0)]))])
        self.assertIsNone(rows[0]["target_unit_end_boundary"])
        self.assertEqual(rows[0]["loss_mask_boundary"], 0)

    def test_unknown_absent_and_zero_differ(self):
        unknown, absent, zero = [FeatureStream().step(record(observation(t))) for t in (None, [], [timer(0)])]
        self.assertEqual(unknown["secondary.storm_phase.count.known"], 0)
        self.assertEqual(absent["secondary.storm_phase.count.known"], 1)
        self.assertEqual(absent["secondary.storm_phase.minimum_seconds.known"], 0)
        self.assertEqual(zero["secondary.storm_phase.minimum_seconds.known"], 1)

    def test_multiple_same_kind_timers_order_invariant(self):
        a = FeatureStream().step(record(observation([timer(44), timer(15)])))
        b = FeatureStream().step(record(observation([timer(15), timer(44)])))
        self.assertEqual(a, b)
        self.assertGreater(a["secondary.storm_phase.count"], 1)

    def test_actual_irregular_delta_and_session_reset(self):
        records = [
            record(frame=1, seconds=0),
            record(frame=2, seconds=10.125),
            record(frame=3, seconds=55.625),
            record(session="second"),
        ]
        rows = build_rows(records)
        self.assertEqual([r["delta_t_s"] for r in rows], [None, 10.125, 45.5, None])
        names = feature_spec()["feature_names"]
        i = names.index("sequence_start")
        self.assertEqual([r["features"][i] for r in rows], [1, 0, 0, 1])
        with self.assertRaises(ValueError):
            build_rows([records[0], records[-1], records[1]])
        with self.assertRaises(ValueError):
            build_rows([records[1], records[0]])

    def test_future_does_not_change_earlier_features(self):
        a, b = record(frame=1), record(frame=2, seconds=40)
        self.assertEqual(build_rows([a])[0], build_rows([a, b])[0])

    def test_main_and_secondary_coexist_without_cross_talk(self):
        a = observation([timer(44)])
        a["clock"].update(visible=True, display="1:00", value_seconds=60, direction="unknown")
        b = copy.deepcopy(a)
        b["clock"].update(display="0:45", value_seconds=45)
        b["secondary_timers"] = [timer(180)]
        rows = build_rows([record(a), record(b, 2, 15)])
        f = dict(zip(feature_spec()["feature_names"], rows[-1]["features"]))
        self.assertLess(f["clock.value_seconds.delta_candidate"], 0)
        self.assertEqual(f["clock.value_seconds.delta_candidate.known"], 1)

    def test_checkpoint_contract_rejects_historical_or_wrong_order(self):
        assert_checkpoint_compatible(feature_spec())
        for ckpt in (
            {"input_dim": 136},
            dict(feature_spec(), feature_names=[]),
            dict(feature_spec(), feature_sha256="wrong"),
        ):
            with self.assertRaises(ValueError):
                assert_checkpoint_compatible(ckpt)

    def test_labels_require_correct_interval_and_verified_observations(self):
        a, b = record(reviewed=True), record(frame=2, seconds=10, reviewed=True)
        label = {
            ("test", 2): {
                "previous_frame_id": 1,
                "unit_end_boundary": 1,
                "ended_unit_count": 1,
                "boundary_applicable": True,
            }
        }
        self.assertEqual(build_rows([a, b], label)[1]["loss_mask_boundary"], 1)
        # Changing external labels does not change feature inputs.
        self.assertEqual(build_rows([a, b], label)[1]["features"], build_rows([a, b])[1]["features"])
        b["review_status"] = "proposed_pending_human_review"
        self.assertEqual(build_rows([a, b], label)[1]["loss_mask_boundary"], 0)
        label[("test", 2)]["previous_frame_id"] = 99
        with self.assertRaises(ValueError):
            build_rows([a, b], label)

    # --- contract 2.1: universal secondary counters -------------------------------------------
    def test_v21_counters_valid_examples(self):
        import jsonschema

        br = [counter("players_remaining", "field", 46), counter("teams_remaining", "field", 14)]
        stocks = [counter("lives", "a", 3), counter("lives", "b", 1)]
        fighting = [counter("target", "field", 2), counter("series", "b", 2, label="WINS")]
        for counters in (
            None,
            [],
            br,
            stocks,
            fighting,
            [counter("other", "field", 5), counter("other", "field", 7)],
            [counter("players_remaining", "field", None)],
            [counter("players_remaining", "field", 46, 100)],
        ):
            obj = observation()
            obj["secondary_counters"] = counters
            self.assertEqual(validate_observation(obj), [], counters)
            jsonschema.validate(obj, output_schema())

    def test_v21_counters_invalid(self):
        bad = [
            [counter("lives", "field", 3)],  # lives must belong to a side
            [counter("players_remaining", "a", 46)],  # players remaining is field-wide
            [counter("target", "field", 2), counter("target", "field", 3)],  # duplicate slot
            [counter("players_remaining", "field", 120, 100)],  # value > displayed total
            [counter("players_remaining", "field", -1)],
            [dict(counter("lives", "a", 1), label=3)],
            [dict(counter("lives", "a", 1), kind="kills")],
            [dict(counter("lives", "a", 1), unit_end_boundary=1)],
            "46",
        ]
        for counters in bad:
            obj = observation()
            obj["secondary_counters"] = counters
            self.assertTrue(validate_observation(obj), counters)

    def test_v20_annotations_remain_valid_and_upgrade_in_memory(self):
        obj = observation([timer()])
        v20 = {k: v for k, v in obj.items() if k != "secondary_counters"}
        v20["schema_version"] = "2.0"
        before = copy.deepcopy(v20)
        self.assertEqual(validate_observation(v20), [])
        self.assertEqual(validate_any(v20), [])
        up = upgrade_v20(v20)
        self.assertEqual(v20, before)
        self.assertIsNone(up["secondary_counters"])
        self.assertEqual(validate_observation(up), [])
        wrong = dict(v20, secondary_counters=[])  # 2.0 must not carry the 2.1 key
        self.assertTrue(validate_observation(wrong))
        f = FeatureStream().step(record(v20))
        self.assertEqual(f["counter.inventory_known"], 0)
        self.assertEqual(f["counter.players_remaining.field.known"], 0)

    def test_v4_counter_features_and_deltas(self):
        a, b = observation(), observation()
        a["secondary_counters"] = [counter("players_remaining", "field", 46)]
        b["secondary_counters"] = [counter("players_remaining", "field", 30)]
        rows = build_rows([record(a), record(b, 2, 28)])
        f = dict(zip(feature_spec()["feature_names"], rows[-1]["features"]))
        self.assertEqual(f["counter.inventory_known"], 1)
        self.assertEqual(f["counter.players_remaining.field.known"], 1)
        self.assertLess(f["counter.players_remaining.field.delta_candidate"], 0)
        self.assertEqual(f["counter.lives.a.known"], 0)
        empty = FeatureStream().step(record(dict(observation(), secondary_counters=[])))
        self.assertEqual(empty["counter.inventory_known"], 1)
        self.assertEqual(empty["counter.other.count"], 0)
        self.assertEqual(empty["counter.other.count.known"], 1)

    def test_v4_mode_infinite_clock_last_period(self):
        obj = observation()
        obj["game"]["mode"] = "free_roam"
        obj["clock"].update(visible=True, display="∞", value_seconds=None, direction="unknown")
        obj["period"].update(type="round", number=5, total=5)
        f = FeatureStream().step(record(obj))
        self.assertEqual(f["game.mode=free_roam"], 1)
        self.assertEqual(f["clock.infinite"], 1)
        self.assertEqual(f["clock.infinite.known"], 1)
        self.assertEqual(f["period.is_last"], 1)
        obj["game"]["mode"] = "UFC bout"  # non-canonical text is not an identifier
        obj["clock"].update(display=None)
        obj["period"].update(number=3)
        g = FeatureStream().step(record(obj))
        self.assertEqual(g["game.mode=OTHER_TEXT"], 1)
        self.assertEqual(g["clock.infinite.known"], 0)
        self.assertEqual(g["period.is_last"], 0)
        self.assertEqual(g["period.is_last.known"], 1)

    def test_v4_missing_observation_row_is_kept(self):
        real = record(observation(), 1, 0, reviewed=True)
        missing = {
            "session_id": "test",
            "frame_id": 2,
            "received_monotonic_ns": 10**18 + 30 * 10**9,
            "observation": None,
            "observation_missing": True,
        }
        after = record(observation(), 3, 60, reviewed=True)
        label = {
            ("test", 2): {
                "previous_frame_id": 1,
                "unit_end_boundary": 0,
                "ended_unit_count": 0,
                "boundary_applicable": True,
            }
        }
        rows = build_rows([real, missing, after], label)
        names = feature_spec()["feature_names"]
        self.assertEqual([r["features"][names.index("observation_missing")] for r in rows], [0, 1, 0])
        self.assertEqual(rows[1]["loss_mask_boundary"], 1)  # the GRU learns to stay silent on gaps
        self.assertEqual(rows[2]["delta_t_s"], 30)

    def test_manifest_cli_and_label_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            obj = observation([timer(0)])
            (root / "obs.json").write_text(json.dumps(obj))
            manifest = root / "manifest.jsonl"
            row = dict(record(), observation_path="obs.json")
            row.pop("observation")
            manifest.write_text(json.dumps(row) + "\n")
            loaded = load_records(manifest, root)
            self.assertEqual(loaded[0]["observation"], obj)
            labelpath = root / "labels.jsonl"
            labelpath.write_text(
                json.dumps(
                    {
                        "session_id": "test",
                        "frame_id": 2,
                        "previous_frame_id": 1,
                        "review_status": "proposed",
                        "unit_end_boundary": 0,
                        "ended_unit_count": 0,
                        "boundary_applicable": True,
                    }
                )
            )
            with self.assertRaises(ValueError):
                labels_by_frame(labelpath)
            out = root / "output"
            command = [
                sys.executable,
                "-m",
                "playend.contract.prepare_dataset",
                "--manifest",
                str(manifest),
                "--project-root",
                str(root),
                "--out",
                str(out),
            ]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads((out / "report.json").read_text())["eligible_labelled_intervals"], 0)
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
