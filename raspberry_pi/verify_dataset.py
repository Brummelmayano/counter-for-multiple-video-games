#!/usr/bin/env python3
"""Audit en lecture seule des fichiers et index ; aucune suppression."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def audit(root):
    report = {"sessions": [], "errors": 0}
    for session in sorted(Path(root).glob("session_*")):
        errors, indexed, count, previous = [], set(), 0, None
        try:
            with (session / "captures.csv").open(newline="") as f:
                for row in csv.DictReader(f):
                    file = (session / row["filename"]).resolve()
                    if not file.is_relative_to(session.resolve()):
                        raise ValueError("Chemin hors session")
                    if file in indexed:
                        errors.append("Fichier référencé plusieurs fois : " + str(file))
                    indexed.add(file)
                    stamp = int(row["received_monotonic_ns"])
                    if previous is not None and stamp <= previous:
                        errors.append("Horodatages non croissants")
                    if previous is not None and abs(float(row["delta_t_s"])-(stamp-previous)/1e9) > 1e-6:
                        errors.append("Intervalle incohérent")
                    previous = stamp
                    data = file.read_bytes()
                    if len(data) != int(row["size_bytes"]) or hashlib.sha256(data).hexdigest() != row["sha256"]:
                        errors.append("Taille ou SHA256 incorrect : " + row["filename"])
                    count += 1
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(str(exc))
        orphans = sorted(str(p.relative_to(session)) for p in session.rglob("*.jpg") if p.resolve() not in indexed)
        partials = sorted(str(p.relative_to(session)) for p in session.rglob("*.partial"))
        errors.extend("Image sans ligne CSV : " + p for p in orphans)
        errors.extend("Écriture incomplète : " + p for p in partials)
        report["sessions"].append({"session": session.name, "indexed_images": count, "errors": errors})
        report["errors"] += len(errors)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", nargs="?", type=Path, default=Path(__file__).resolve().parent / "dataset")
    result = audit(parser.parse_args().dataset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result["errors"]))
