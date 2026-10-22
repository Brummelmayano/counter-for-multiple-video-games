"""Build a batch of contract 2.x observations, each with its note, from one compact reading per frame.

The JSON and the "Valeurs JSON" part of each note are generated from the same values, so the
note can no longer announce a score/period that the saved JSON does not contain. The free-text
reading (`obs`) is also scanned for explicit "a–b" pairs and must agree with score.a/score.b.

Spec file (JSON):
{
  "run": "<lot folder name>",
  "presets": {"<name>": {<partial observation>}, ...},
  "frames": [
    {"id": 199, "p": "<preset>", "s": [2, 2], "c": "90:57", "obs": "...", "set": {"state.phase": "active"}},
    ...
  ]
}
Shortcuts: "s" -> score.a/score.b (null -> both null and score.type null); "c" -> main clock display
(null -> clock not visible); "pd" -> [period.type, number, total]; "t" -> game.title;
"parts" -> participants.primary; "set" -> any dotted-path override.

usage: python -m playend.annotation.build_lot SPEC.json
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

from playend.annotation.notes import READING
from playend.common.files import read_jsonl, write_jsonl
from playend.common.paths import LOTS, relative
from playend.contract.contract import empty_observation, validate_observation

PAIR = re.compile(r"(?<![\d:/–-])(\d{1,2})\s*[–-]\s*(\d{1,2})(?![\d:/'′–-])")  # excludes dates like 2026-09-20


def merge(dst, src):
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            merge(dst[key], value)
        else:
            dst[key] = copy.deepcopy(value)


def set_path(obj, dotted, value):
    *parents, leaf = dotted.split(".")
    for key in parents:
        obj = obj[key]
    if leaf not in obj:
        raise SystemExit(f"unknown field {dotted}")
    obj[leaf] = value


def to_seconds(display):
    if display is None or not re.fullmatch(r"\d{1,3}(:\d{2}){1,2}(\.\d+)?", display):
        return None
    total = 0.0
    for part in display.split(":"):
        total = total * 60 + float(part)
    return int(total) if total.is_integer() else total


def build(frame, presets):
    obs = empty_observation()
    for name in frame.get("p", "").split("+") if frame.get("p") else []:
        merge(obs, presets[name])
    if "t" in frame:
        obs["game"]["title"] = frame["t"]
    if "parts" in frame:
        obs["participants"]["primary"] = frame["parts"]
        obs["participants"]["count_visible"] = len(frame["parts"]) or None
    if "s" in frame:
        if frame["s"] is None:
            obs["score"].update(a=None, b=None, type=None)
        else:
            obs["score"]["a"], obs["score"]["b"] = frame["s"]
    if "c" in frame:
        display = frame["c"]
        if display is None:
            obs["clock"] = {"visible": False, "display": None, "value_seconds": None, "direction": None}
        else:
            obs["clock"] = {
                "visible": True,
                "display": display,
                "value_seconds": to_seconds(display),
                "direction": "unknown",
            }
    if "pd" in frame:
        obs["period"] = dict(zip(("type", "number", "total"), frame["pd"]))
    for dotted, value in frame.get("set", {}).items():
        set_path(obs, dotted, value)
    return obs


def summary(obs):
    """The "Valeurs JSON" sentence that ends every note, written from the saved observation itself."""
    score, clock, period, result = obs["score"], obs["clock"], obs["period"], obs["result"]
    if score["a"] is None and score["b"] is None:
        score_text = "non lisible/absent"
    else:
        score_text = f"{score['a']}–{score['b']} ({score['type']})"
    if clock["visible"]:
        clock_text = clock["display"]
    else:
        clock_text = "rôle incertain" if clock["visible"] is None else "non visible"
    period_text = period["type"]
    if period["number"] is not None:
        period_text += f" {period['number']}"
    if period["total"] is not None:
        period_text += f"/{period['total']}"
    if result["visible"] is False:
        result_text = "aucun"
    elif result["visible"] is None:
        result_text = "incertain"
    else:
        result_text = f"{result['outcome_type']} (vainqueur: {result['winner']})"
    timers = obs["secondary_timers"]
    if timers is None:
        timers_text = "non inventoriés"
    else:
        timers_text = ", ".join(f"{t['kind']} {t['display']}" for t in timers) or "aucun"
    text = (
        f"Valeurs JSON — état: {obs['state']['phase']}/{obs['state']['screen_type']}; score A–B: {score_text}; "
        f"horloge: {clock_text}; période: {period_text}; résultat: {result_text}; minuteurs secondaires: {timers_text}"
    )
    if "secondary_counters" in obs:  # contract 2.1; the notes of 2.0 lots keep their original form
        counters = obs["secondary_counters"]
        if counters is None:
            counters_text = "non inventoriés"
        else:
            counters_text = (
                ", ".join(
                    f"{c['kind']}.{c['side']}={c['value']}" + (f"/{c['total']}" if c["total"] is not None else "")
                    for c in counters
                )
                or "aucun"
            )
        text += f"; compteurs secondaires: {counters_text}"
    return text + "."


def build_batch(spec_path: Path) -> Path:
    """Check a reading spec and write decisions/batch_<lo>_<hi>.jsonl in its lot. Returns the batch path."""
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    lot = LOTS / spec["run"]
    manifest_ids = {row["frame_id"] for row in read_jsonl(lot / "manifest.jsonl")}
    frames = spec["frames"]
    ids = [f["id"] for f in frames]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate frame ids in spec")
    problems, records = [], []
    for frame in frames:
        fid = frame["id"]
        if fid not in manifest_ids:
            problems.append(f"{fid}: not in the lot manifest")
            continue
        obs = build(frame, spec.get("presets", {}))
        errors = validate_observation(obs)
        if errors:
            problems.append(f"{fid}: contract errors {errors}")
        text = frame["obs"].strip()
        if not text:
            problems.append(f"{fid}: empty reading")
        pairs = {(int(x), int(y)) for x, y in PAIR.findall(text)}
        declared = (obs["score"]["a"], obs["score"]["b"])
        if pairs and declared not in pairs:
            problems.append(f"{fid}: reading mentions {sorted(pairs)} but JSON score is {declared}")
        note = f"{READING}{text} || {summary(obs)}"
        records.append({"frame_id": fid, "observation": obs, "annotation_note": note})
    missing = sorted(manifest_ids - set(ids))
    if problems:
        raise SystemExit("\n".join(problems))
    lo, hi = min(ids), max(ids)
    out = lot / "decisions" / f"batch_{lo:06d}_{hi:06d}.jsonl"
    write_jsonl(out, records)
    print(
        f"{len(records)} records -> {relative(out)}"
        + (f"; frames still missing from the lot: {missing}" if missing else "")
    )
    return out


def main():
    parser = argparse.ArgumentParser(description="Build a lot's batch of observations from its reading spec.")
    parser.add_argument("spec", type=Path)
    build_batch(parser.parse_args().spec)


if __name__ == "__main__":
    main()
