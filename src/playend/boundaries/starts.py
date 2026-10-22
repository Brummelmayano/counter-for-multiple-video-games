"""Place the start of each unit of units.json: its first gameplay observation with a readable HUD.

Rule of the author (2026-10-13, docs/decisions/regles-de-comptage.md): a partie starts on the first gameplay capture
of the new partie whose HUD is readable (score, clock, lap, place, lives, players left). A partie already under way on
the first capture of the session also starts there and is counted (decision of the author, same day). start_status
says where the start comes from: "rule" when this module placed it, "author" when the author corrected it. A start
already written in units.json is never replaced; a different computed value is only reported.

usage: python -m playend.boundaries.starts session_<id> [--write]
       python -m playend.boundaries.starts --all [--write]
"""

from __future__ import annotations

import argparse
import json

from playend.common.paths import BOUNDARIES, resolve
from playend.corrections.traces import effective

START_FIELDS = ("start_established_at", "start_status", "start_evidence")


def hud_values(obs: dict) -> list[str]:
    values = []
    score = obs["score"]
    if score["a"] is not None or score["b"] is not None:
        values.append(f"score {score['a']}–{score['b']}")
    if obs["clock"]["display"]:
        values.append(f"chrono {obs['clock']['display']}")
    if obs["progress"]["current"] is not None:
        values.append(f"{obs['progress']['type'] or 'progression'} {obs['progress']['current']}")
    if obs["position"]["current"] is not None:
        values.append(f"place {obs['position']['current']}")
    for counter in obs.get("secondary_counters") or []:
        if counter.get("value") is not None:
            values.append(f"{counter['kind']} {counter['side']} {counter['value']}")
    return values


def computed_start(unit: dict, observations: dict[int, dict]) -> dict:
    for fid in range(unit["first_frame"], unit["last_frame"] + 1):
        obs = observations[fid]
        values = hud_values(obs)
        if obs["state"]["screen_type"] == "gameplay" and values:
            return {
                "start_established_at": fid,
                "start_status": "rule",
                "start_evidence": f"première capture de jeu au HUD lisible ({', '.join(values)})",
            }
    raise SystemExit(f"{unit['unit_id']}: no gameplay capture with a readable HUD, place its start by hand")


def with_start(unit: dict, start: dict) -> dict:
    """Insert the start fields right after last_frame, keeping the order of the other keys."""
    out = {}
    for key, value in unit.items():
        if key not in START_FIELDS:
            out[key] = value
        if key == "last_frame":
            out.update(start)
    return out


def place_starts(session: str, write: bool) -> tuple[int, int, list[str]]:
    path = BOUNDARIES / session / "units.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    entries = effective(session)
    observations = {fid: json.loads(resolve(entry["annotation_path"]).read_text()) for fid, entry in entries.items()}
    placed, kept, disagreements = 0, 0, []
    for index, unit in enumerate(spec["units"]):
        start = computed_start(unit, observations)
        if unit.get("start_established_at") is not None:
            kept += 1
            if unit["start_established_at"] != start["start_established_at"]:
                disagreements.append(
                    f"{unit['unit_id']}: written {unit['start_established_at']}, rule {start['start_established_at']}"
                )
            continue
        spec["units"][index] = with_start(unit, start)
        placed += 1
    if write and placed:
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return placed, kept, disagreements


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("session", nargs="?", help="session_<id>")
    parser.add_argument("--all", action="store_true", help="every session that has a units.json")
    parser.add_argument("--write", action="store_true", help="write the starts into units.json (default: report)")
    args = parser.parse_args()
    if args.all == bool(args.session):
        parser.error("give one session or --all")
    sessions = sorted(p.parent.name for p in BOUNDARIES.glob("session_*/units.json")) if args.all else [args.session]
    for session in sessions:
        placed, kept, disagreements = place_starts(session, args.write)
        action = "placed" if args.write else "to place"
        print(f"{session}: {placed} starts {action}, {kept} already written")
        for line in disagreements:
            print(f"  {line}")


if __name__ == "__main__":
    main()
