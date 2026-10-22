"""Export the PlayEnd dataset from the human-verified boundaries: CSV tables, column dictionary, GRU features and
the data card (docs/dataset/DATA_CARD.md, copied as README.md), croissant.json and the LICENSE.

Only the sessions whose boundaries were verified by hand are exported. Real player names are replaced by pseudonyms
and no wall-clock time is written. The package is read back and checked after writing; nothing in data/ changes.

usage: python -m playend.dataset.export [--out build/playend_v1.0]
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

from playend.common.paths import REPO
from playend.contract.temporal import feature_spec
from playend.dataset.checks import check_package
from playend.dataset.columns import TABLES, names
from playend.dataset.croissant import croissant
from playend.dataset.csvfiles import cell, write_csv
from playend.dataset.features import differences, feature_rows, private_features
from playend.dataset.pseudonyms import NAMES, Pseudonyms, read_names
from playend.dataset.tables import (
    exported_sessions,
    load_session,
    observation_rows,
    session_row,
    split_rows,
    time_segment_rows,
    unit_rows,
)

CARD = REPO / "docs" / "dataset" / "DATA_CARD.md"
# Official legal code of CC BY-NC 4.0, as downloaded from creativecommons.org.
LICENSE = REPO / "LICENSE"
DICTIONARY_COLUMNS = ["column", "type", "unit", "allowed_values", "description_en", "description_fr", "example"]
EXAMPLE_LENGTH = 80


def dictionary_rows(table: str, rows: list[dict]) -> list[dict]:
    out = []
    for name, kind, unit, allowed, english, french in TABLES[table]:
        example = next((cell(row[name]) for row in rows if row[name] is not None), "")
        if len(example) > EXAMPLE_LENGTH:
            example = example[: EXAMPLE_LENGTH - 1] + "…"
        out.append(dict(zip(DICTIONARY_COLUMNS, (name, kind, unit, allowed, english, french, example))))
    return out


def fold_summary(tables: dict) -> list[str]:
    fold_of = {row["session_id"]: row["fold"] for row in tables["splits"]}
    sessions, ends, frames = Counter(), Counter(), Counter()
    for row in tables["sessions"]:
        fold = fold_of[row["session_id"]]
        sessions[fold] += 1
        ends[fold] += row["boundary_count"]
        frames[fold] += row["frame_count"]
    return [
        f"  fold {fold}: {sessions[fold]} sessions, {frames[fold]} screenshots, {ends[fold]} ends"
        for fold in sorted(sessions)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the PlayEnd dataset (CSV tables, column dictionary, GRU features) "
        "from the human-verified boundaries."
    )
    parser.add_argument(
        "--out", type=Path, default=REPO / "build" / "playend_v1.0", help="new folder; an export never overwrites"
    )
    parser.add_argument("--names", type=Path, default=NAMES, help="private list of the real player names to replace")
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit(f"{args.out} already exists: remove it first")
    real_names = read_names(args.names)
    pseudonyms = Pseudonyms(real_names)
    sessions = [load_session(session) for session in exported_sessions()]

    tables = {table: [] for table in TABLES}
    for session in sessions:
        observations = observation_rows(session, pseudonyms)
        tables["observations"] += observations
        tables["units"] += unit_rows(session, pseudonyms)
        tables["time_segments"] += time_segment_rows(session, pseudonyms)
        tables["sessions"].append(session_row(session, observations))
    tables["splits"] = split_rows(tables["sessions"])
    features = feature_rows(tables["observations"])
    changed = differences(features, private_features(sessions))

    data, dictionary = args.out / "data", args.out / "dictionary"
    data.mkdir(parents=True)
    dictionary.mkdir()
    for table, rows in tables.items():
        write_csv(data / f"{table}.csv", names(table), rows)
        write_csv(dictionary / f"{table}_columns.csv", DICTIONARY_COLUMNS, dictionary_rows(table, rows))
    spec = feature_spec()
    write_csv(data / "features.csv", ["session_id", "frame_id", *spec["feature_names"]], features)
    (dictionary / "feature_spec.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(CARD, args.out / "README.md")
    shutil.copyfile(LICENSE, args.out / "LICENSE")
    metadata = croissant(args.out, spec["feature_names"])
    (args.out / "croissant.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    observations = tables["observations"]
    modes = Counter(row["billing_mode"] for row in observations)
    print(f"{args.out}")
    print(
        f"  {len(sessions)} sessions, {len(observations)} screenshots, {len(tables['units'])} units, "
        f"{len(tables['time_segments'])} time segments"
    )
    print(
        f"  {sum(row['unit_end_boundary'] == 1 for row in observations)} ends "
        f"({sum(row['unit_end_boundary'] == 1 and row['boundary_applicable'] for row in observations)} on applicable "
        f"intervals), {sum(row['boundary_applicable'] for row in observations)} applicable intervals, "
        f"billing_mode {dict(modes)}"
    )
    print(f"  {len(pseudonyms.assigned)} pseudonyms for {len(real_names)} listed names")
    print("\n".join(fold_summary(tables)))
    if changed:
        print(f"  features that differ from the private observations: {dict(changed)}")
    else:
        print(f"  {len(spec['feature_names'])} features identical to those of the private observations")
    problems = check_package(args.out, real_names, sessions)
    for problem in problems[:50]:
        print(f"PROBLEM {problem}")
    if problems:
        raise SystemExit(f"{len(problems)} problems in the exported package")
    print("  package checked: no problem")
    if "url" not in metadata:
        print("  croissant.json has no url yet: set it in docs/dataset/croissant_metadata.json at deposit")


if __name__ == "__main__":
    main()
