"""Checks run on the written package: the files are read back from disk, never trusted from memory.

Each check compares the CSV files with the dictionary, with each other (keys) or with the sources (verified labels,
units, time segments). check_package returns the problems found; an empty list means the package is consistent.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path

from playend.boundaries.build_labels import billing_mode
from playend.common.files import sha256
from playend.contract import validate_observation
from playend.contract.contract import TIMER_KINDS
from playend.contract.temporal import feature_spec
from playend.dataset.columns import TABLES
from playend.dataset.csvfiles import cell, read_csv
from playend.dataset.features import nanoseconds
from playend.dataset.pseudonyms import PSEUDONYM, name_pattern
from playend.dataset.tables import BILLING_MODES, Session, observation_columns

PLAIN_CHOICES = re.compile(r"[\w.]+(\|[\w.]+)*")
# Traces of the capture device or of the repository that must not reach the published files.
# The Responsible AI answers asked for every dataset submission (NeurIPS 2026 Evaluations and Datasets track).
MINIMAL_RAI = [
    "rai:dataLimitations",
    "rai:dataBiases",
    "rai:personalSensitiveInformation",
    "rai:dataUseCases",
    "rai:dataSocialImpact",
    "rai:hasSyntheticData",
    "prov:wasDerivedFrom",
    "prov:wasGeneratedBy",
]
FORBIDDEN = {
    "wall-clock time": re.compile(r"\b20\d\d-\d\d-\d\d[T ]\d\d:\d\d"),
    "repository path": re.compile(r"/home/|dossier_partie_VLM|data/annotations|data/captures"),
    "device field": re.compile(r"received_wall_utc|boot_id|random_seed"),
}


def type_problems(table: str, rows: list[dict]) -> list[str]:
    problems = []
    for name, kind, _, allowed, _, _ in TABLES[table]:
        choices = set(allowed.split("|")) if PLAIN_CHOICES.fullmatch(allowed) else None
        for number, row in enumerate(rows, 2):
            value = row[name]
            if value == "":
                continue
            try:
                if kind == "integer":
                    int(value)
                elif kind == "number" and not math.isfinite(float(value)):
                    raise ValueError("not finite")
                elif kind == "boolean" and value not in ("true", "false"):
                    raise ValueError("not true/false")
                elif kind == "object":
                    json.loads(value)
            except ValueError as error:
                problems.append(f"{table}.csv line {number}: {name}={value!r} is not {kind} ({error})")
                continue
            if choices and value not in choices:
                problems.append(f"{table}.csv line {number}: {name}={value!r} not in {allowed}")
            if name == "secondary_timer_kinds" and not set(value.split("|")) <= set(TIMER_KINDS):
                problems.append(f"{table}.csv line {number}: unknown timer kind in {value!r}")
    return problems


def sequence_problems(observations: list[dict]) -> list[str]:
    problems, by_session = [], defaultdict(list)
    for row in observations:
        by_session[row["session_id"]].append(row)
    if list(by_session) != sorted(by_session):
        problems.append("observations.csv: sessions not sorted")
    for session, rows in by_session.items():
        if [int(row["frame_id"]) for row in rows] != list(range(1, len(rows) + 1)):
            problems.append(f"{session}: frame_id not 1..N in order")
        times = [nanoseconds(row["t_s"]) for row in rows]
        if times[0] != 0 or rows[0]["delta_t_s"] != "":
            problems.append(f"{session}: first screenshot must have t_s = 0 and no delta_t_s")
        for previous, current, row in zip(times, times[1:], rows[1:]):
            if current <= previous or nanoseconds(row["delta_t_s"]) != current - previous:
                problems.append(f"{session} frame {row['frame_id']}: t_s / delta_t_s inconsistent")
    return problems


def label_problems(observations: list[dict], sessions: list[Session]) -> list[str]:
    problems = []
    rows = {(row["session_id"], int(row["frame_id"])): row for row in observations}
    for session in sessions:
        for frame in session.frames:
            fid = frame["frame_id"]
            row = rows[(session.session_id, fid)]
            mode = billing_mode(fid, session.units, session.segments)
            expected = {"billing_mode": BILLING_MODES[mode], "unit_end_boundary": "", "boundary_applicable": "false"}
            label = session.labels.get(fid)
            started = [unit["unit_id"] for unit in session.units if unit.get("start_established_at") == fid]
            expected |= {
                "unit_start_boundary": cell(int(bool(started))),
                "started_unit_id": cell((started or [None])[0]),
            }
            if label is not None:
                if label["started_unit_ids"] != started:
                    problems.append(f"{session.session_id} frame {fid}: verified start differs from units.json")
                if label["billing_mode"] != mode:
                    problems.append(f"{session.session_id} frame {fid}: verified billing_mode differs from units.json")
                expected |= {
                    "unit_end_boundary": cell(label["unit_end_boundary"]),
                    "boundary_applicable": cell(label["boundary_applicable"]),
                    "current_unit_id": cell(label["current_unit_id"]),
                    "ended_unit_id": cell((label["ended_unit_ids"] or [None])[0]),
                }
            for name, value in expected.items():
                if row[name] != value:
                    problems.append(f"{session.session_id} frame {fid}: {name}={row[name]!r}, expected {value!r}")
    return problems


def key_problems(observations: list[dict], units: list[dict], segments: list[dict]) -> list[str]:
    problems = []
    unit_keys = {(unit["session_id"], unit["unit_id"]): unit for unit in units}
    if len(unit_keys) != len(units):
        problems.append("units.csv: (session_id, unit_id) not unique")
    ends, starts = {}, {}
    for row in observations:
        session, fid = row["session_id"], int(row["frame_id"])
        for column in ("current_unit_id", "ended_unit_id", "started_unit_id"):
            if row[column] and (session, row[column]) not in unit_keys:
                problems.append(f"{session} frame {fid}: {column} {row[column]} missing from units.csv")
        if row["current_unit_id"]:
            unit = unit_keys.get((session, row["current_unit_id"]))
            if unit and not int(unit["first_frame"]) <= fid <= int(unit["last_frame"]):
                problems.append(f"{session} frame {fid}: outside the frames of {row['current_unit_id']}")
        if (row["unit_end_boundary"] == "1") != bool(row["ended_unit_id"]):
            problems.append(f"{session} frame {fid}: unit_end_boundary and ended_unit_id disagree")
        if row["ended_unit_id"]:
            ends[(session, row["ended_unit_id"])] = fid
        if (row["unit_start_boundary"] == "1") != bool(row["started_unit_id"]):
            problems.append(f"{session} frame {fid}: unit_start_boundary and started_unit_id disagree")
        if row["started_unit_id"]:
            starts[(session, row["started_unit_id"])] = fid
    for key, unit in unit_keys.items():
        expected = int(unit["end_established_at"]) if unit["end_established_at"] else None
        if ends.get(key) != expected:
            problems.append(f"{key}: end at {ends.get(key)}, units.csv says {expected}")
        if starts.get(key) != int(unit["start_established_at"]):
            problems.append(f"{key}: start at {starts.get(key)}, units.csv says {unit['start_established_at']}")
    in_segment = {
        (segment["session_id"], fid)
        for segment in segments
        for fid in range(int(segment["first_frame"]), int(segment["last_frame"]) + 1)
    }
    for row in observations:
        if (row["billing_mode"] == "time_based") != ((row["session_id"], int(row["frame_id"])) in in_segment):
            problems.append(f"{row['session_id']} frame {row['frame_id']}: billing_mode and time segments disagree")
    return problems


def table_problems(observations, sessions_rows, units, segments, splits) -> list[str]:
    problems = []
    count = defaultdict(lambda: defaultdict(int))
    for row in observations:
        count[row["session_id"]]["frames"] += 1
        count[row["session_id"]]["ends"] += row["unit_end_boundary"] == "1"
        count[row["session_id"]]["starts"] += row["unit_start_boundary"] == "1"
    for unit in units:
        count[unit["session_id"]]["units"] += 1
    for segment in segments:
        count[segment["session_id"]]["segments"] += 1
    for row in sessions_rows:
        found = count[row["session_id"]]
        expected = (
            row["frame_count"],
            row["boundary_count"],
            row["start_count"],
            row["unit_count"],
            row["time_segment_count"],
        )
        if tuple(str(found[key]) for key in ("frames", "ends", "starts", "units", "segments")) != expected:
            problems.append(f"sessions.csv: counts of {row['session_id']} differ from the other tables")
    session_ids = [row["session_id"] for row in sessions_rows]
    if sorted(row["session_id"] for row in splits) != sorted(session_ids) or set(count) != set(session_ids):
        problems.append("splits.csv, sessions.csv and observations.csv do not list the same sessions")
    return problems


def observation_json_problems(observations: list[dict]) -> list[str]:
    problems = []
    for row in observations:
        obs = json.loads(row["observation_json"])
        errors = validate_observation(obs)
        if errors:
            problems.append(f"{row['session_id']} frame {row['frame_id']}: observation_json invalid {errors}")
            continue
        for name, value in observation_columns(obs).items():
            if row[name] != cell(value):
                problems.append(f"{row['session_id']} frame {row['frame_id']}: {name} differs from observation_json")
    return problems


def feature_problems(header: list[str], features: list[dict], observations: list[dict]) -> list[str]:
    problems = []
    if header != ["session_id", "frame_id", *feature_spec()["feature_names"]]:
        problems.append("features.csv: columns differ from feature_spec.json")
    keys = [(row["session_id"], row["frame_id"]) for row in observations]
    if [(row["session_id"], row["frame_id"]) for row in features] != keys:
        problems.append("features.csv: rows do not match observations.csv")
    for row in features:
        if not all(math.isfinite(float(row[name])) for name in header[2:]):
            problems.append(f"features.csv: non-finite value in {row['session_id']} frame {row['frame_id']}")
    return problems


def privacy_problems(folder: Path, names: list[str], sessions: list[Session]) -> list[str]:
    problems = []
    real_names = name_pattern(names)
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        found = {match.group(0) for match in real_names.finditer(text)}
        if found:
            problems.append(f"{path.name}: {len(found)} real player names left")
        for what, pattern in FORBIDDEN.items():
            if pattern.search(text):
                problems.append(f"{path.name}: {what} found")
    for session in sessions:
        for frame in session.frames:
            if PSEUDONYM.search(json.dumps(frame["observation"], ensure_ascii=False)):
                problems.append(
                    f"{session.session_id} frame {frame['frame_id']}: source already looks like a pseudonym"
                )
    return problems


def card_problems(folder: Path, tables: dict[str, list[dict]]) -> list[str]:
    """The figures written in README.md (the data card) must still be those of the tables."""
    card = (folder / "README.md").read_text(encoding="utf-8")
    observations, units = tables["observations"], tables["units"]
    usable = [row for row in observations if row["boundary_applicable"] == "true"]
    completed = sum(row["termination"] == "completed" for row in units)
    hours = sum(float(row["duration_s"]) for row in tables["sessions"]) / 3600
    pseudonyms = set(PSEUDONYM.findall((folder / "data" / "observations.csv").read_text(encoding="utf-8")))
    expected = [
        f"The {len(tables['sessions'])} sessions",
        f"{len(observations):,} screenshots",
        f"{hours:.1f} hours",
        f"{len(units)}: {completed} with an observed end, {len(units) - completed} still running",
        f"| Time-billed segments | {len(tables['time_segments'])} (",
        f"{sum(row['unit_end_boundary'] == '1' for row in usable)} for {len(usable):,}",
        f"replaced {len(pseudonyms)} real names",
        f"{sum(bool(row['corrected_by']) for row in observations):,} rows come from such corrections",
    ]
    families = defaultdict(lambda: [0, 0])
    for row in observations:
        families[row["game_family"]][0] += 1
    for row in units:  # an end belongs to the game that ended, not to the screen that proves it
        families[row["game_family"]][1] += row["termination"] == "completed"
    expected += [f"| {family} | {frames:,} | {ends} |" for family, (frames, ends) in families.items() if family]
    folds = defaultdict(lambda: [0, 0, 0])
    fold_of = {row["session_id"]: row["fold"] for row in tables["splits"]}
    for row in tables["sessions"]:
        fold = folds[fold_of[row["session_id"]]]
        fold[0] += 1
        fold[1] += int(row["frame_count"])
        fold[2] += int(row["boundary_count"])
    expected += [f"| {fold} | {n} | {frames:,} | {ends} |" for fold, (n, frames, ends) in sorted(folds.items())]
    return [f"README.md: expected '{text}'" for text in expected if text not in card]


def croissant_problems(folder: Path, tables: dict[str, list[dict]]) -> list[str]:
    """Hashes and columns named in croissant.json must match the files; the minimal RAI answers must be there."""
    metadata = json.loads((folder / "croissant.json").read_text(encoding="utf-8"))
    problems = []
    screenshots, sessions = len(tables["observations"]), len(tables["sessions"])
    if f"{screenshots:,} screenshots" not in metadata["description"]:
        problems.append("croissant.json: the description does not give the number of screenshots")
    if f"{screenshots:,} JPEG captures of the console output in {sessions} sessions" not in json.dumps(metadata):
        problems.append("croissant.json: prov:wasDerivedFrom does not give the numbers of the package")
    headers = {}
    for item in metadata["distribution"]:
        path = folder / item["contentUrl"]
        if sha256(path) != item["sha256"]:
            problems.append(f"croissant.json: hash of {item['contentUrl']} differs")
        if path.suffix == ".csv":
            headers[item["@id"]] = read_csv(path)[0]
    for record_set in metadata["recordSet"]:
        for field in record_set["field"]:
            source = field.get("source")
            if source and source["extract"]["column"] not in headers[source["fileObject"]["@id"]]:
                problems.append(f"croissant.json: {field['@id']} names a missing column")
    missing = [key for key in MINIMAL_RAI if key not in metadata]
    if missing:
        problems.append(f"croissant.json: missing {missing}")
    return problems


def check_package(folder: Path, names: list[str], sessions: list[Session]) -> list[str]:
    data = folder / "data"
    problems, tables = [], {}
    for table, columns in TABLES.items():
        header, rows = read_csv(data / f"{table}.csv")
        documented = [row["column"] for row in read_csv(folder / "dictionary" / f"{table}_columns.csv")[1]]
        if header != [column[0] for column in columns] or documented != header:
            problems.append(f"{table}.csv: columns differ from the dictionary")
        problems += type_problems(table, rows)
        tables[table] = rows
    observations = tables["observations"]
    problems += sequence_problems(observations)
    problems += label_problems(observations, sessions)
    problems += key_problems(observations, tables["units"], tables["time_segments"])
    problems += table_problems(
        observations, tables["sessions"], tables["units"], tables["time_segments"], tables["splits"]
    )
    problems += observation_json_problems(observations)
    header, features = read_csv(data / "features.csv")
    problems += feature_problems(header, features, observations)
    problems += privacy_problems(folder, names, sessions)
    problems += card_problems(folder, tables)
    problems += croissant_problems(folder, tables)
    return problems
