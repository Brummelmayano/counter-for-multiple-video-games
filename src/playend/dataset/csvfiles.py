"""CSV as published: RFC 4180 (comma, double quotes, CRLF), UTF-8 without BOM, empty cell for a missing value,
booleans written true / false."""

from __future__ import annotations

import csv
from pathlib import Path


def cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\r\n")
        writer.writerow(columns)
        for row in rows:
            if list(row) != columns:
                raise SystemExit(f"{path.name}: row columns differ from {columns}")
            writer.writerow(cell(row[name]) for name in columns)


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)
