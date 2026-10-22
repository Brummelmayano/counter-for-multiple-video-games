"""Build the list of items to validate by hand (items.json), from the boundaries and the effective observations.

Three kinds of items:
- "fin"   : every partie whose end is established (units.json), riskiest first (no end screen, low confidence);
- "temps" : every time-billed segment (time_segments), to confirm the "billed by time" decision;
- "obs"   : a stratified sample of observations per game (5 %, at least 15 per game when available,
            mostly active gameplay), to estimate the reading error rate of each game.

The effective observation of a frame is the one listed in data/boundaries/session_*/observation_manifest.jsonl
(the correction trace when one exists, otherwise the original lot). Fixed seed: reproducible sample.

usage: python -m playend.validation.build_items [--add-new-sessions]   (writes items.json in the validation data folder)
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import random
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

from playend.common.files import read_jsonl
from playend.common.games import NO_GAME, game_family
from playend.common.paths import BOUNDARIES, CAPTURES, VALIDATION, resolve

LOCAL_TZ = ZoneInfo("Africa/Kinshasa")
SEED = 20261002
SAMPLE_RATE = 0.05
SAMPLE_MIN = 15
GAMEPLAY_SHARE = 0.8


def summary(obs: dict) -> dict:
    """Fields that matter for counting, in a flat form for display."""
    score, clock, period, result = obs["score"], obs["clock"], obs["period"], obs["result"]
    progress, position = obs["progress"], obs["position"]
    counters, timers = obs.get("secondary_counters"), obs["secondary_timers"]
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
        result_text = None
    elif result["visible"] is None:
        result_text = "incertain"
    else:
        result_text = f"{result['outcome_type']} (vainqueur : {result['winner']})"
    score_text = None if score["a"] is None and score["b"] is None else f"{score['a']} – {score['b']} ({score['type']})"
    return {
        "jeu": obs["game"]["title"],
        "type": obs["game"]["type"],
        "mode": obs["game"]["mode"],
        "écran": f"{obs['state']['phase']} / {obs['state']['screen_type']}",
        "participants": " / ".join(obs["participants"]["primary"]) or None,
        "score": score_text,
        "chrono": clock_text,
        "période": period_text,
        "progression": None
        if progress["type"] is None
        else f"{progress['type']} {progress['current']}/{progress['total']}",
        "position": None if position["current"] is None else f"{position['current']}/{position['total']}",
        "résultat": result_text,
        "compteurs": None
        if counters is None
        else (", ".join(f"{c['kind']}.{c['side']}={c['value']}" for c in counters) or "aucun"),
        "minuteurs": None if timers is None else (", ".join(f"{t['kind']} {t['display']}" for t in timers) or "aucun"),
    }


def load_sessions():
    sessions = {}
    for folder in sorted(p for p in BOUNDARIES.glob("session_*") if p.is_dir()):
        units = json.loads((folder / "units.json").read_text(encoding="utf-8"))
        frames = {}
        for row in read_jsonl(folder / "observation_manifest.jsonl"):
            path = resolve(row["observation_path"])
            obs = json.loads(path.read_text(encoding="utf-8"))
            meta_path = Path(str(path).replace(".observation.json", ".metadata.json"))
            note = None
            if meta_path.is_file():
                note = json.loads(meta_path.read_text(encoding="utf-8")).get("annotation_note")
            frames[row["frame_id"]] = {
                "obs": obs,
                "note": note,
                "corrected_by": row.get("corrected_by"),
                "observation_path": row["observation_path"],
            }
        captures = {}
        for row in csv.DictReader((CAPTURES / folder.name / "captures.csv").open(encoding="utf-8")):
            wall = datetime.datetime.fromisoformat(row["received_wall_utc"]).astimezone(LOCAL_TZ)
            captures[int(row["frame_id"])] = {
                "heure": wall.strftime("%d/%m %H:%M:%S"),
                "t": float(row["elapsed_s"]),
                "iso": row["received_wall_utc"],
            }
        for fid, item in frames.items():
            item["capture"] = captures[fid]
        sessions[folder.name] = {"units": units, "frames": frames}
    return sessions


def frame_view(session_id, frames, fid, role):
    item = frames.get(fid)
    if item is None:
        return None
    # The Raspberry Pi had no RTC battery and no network: its wall clock resumed from the last shutdown, so the date is
    # not reliable. The reviewer is shown the time since the first capture of the session (monotonic clock) instead.
    t0 = min(f["capture"]["t"] for f in frames.values())
    return {
        "session_id": session_id,
        "frame_id": fid,
        "role": role,
        "valeurs": summary(item["obs"]) if item["obs"] else {},
        "heure_capture": item["capture"]["heure"],
        "t_s": item["capture"]["t"],
        "t_session_s": item["capture"]["t"] - t0,
        "capture_utc": item["capture"]["iso"],
        "note": item["note"],
        "corrigée_par": item["corrected_by"],
    }


def bare_frames(session_id: str) -> dict[int, dict]:
    """The captures of a session that was never annotated: times only, no observation (held-out sessions)."""
    frames = {}
    for row in csv.DictReader((CAPTURES / session_id / "captures.csv").open(encoding="utf-8")):
        wall = datetime.datetime.fromisoformat(row["received_wall_utc"]).astimezone(LOCAL_TZ)
        capture = {
            "heure": wall.strftime("%d/%m %H:%M:%S"),
            "t": float(row["elapsed_s"]),
            "iso": row["received_wall_utc"],
        }
        frames[int(row["frame_id"])] = {"obs": None, "note": None, "corrected_by": None, "capture": capture}
    return frames


def refresh(item, sessions):
    """Same item, same frames and roles; values re-read from the current effective observations (corrections)."""
    item = dict(item)
    item["frames"] = [
        frame_view(f["session_id"], sessions[f["session_id"]]["frames"], f["frame_id"], f["role"])
        for f in item["frames"]
    ]
    return item


def main():
    """Full build, or with --add-new-sessions: keep every existing item (refreshed) and add items only for the sessions
    that have none yet, so that answers already given in validation_results.jsonl keep their meaning."""
    parser = argparse.ArgumentParser(description="Build the list of items to validate by hand (items.json).")
    parser.add_argument(
        "--add-new-sessions",
        action="store_true",
        help="keep every existing item and add items only for sessions that have none",
    )
    args = parser.parse_args()
    sessions = load_sessions()
    existing = None
    if args.add_new_sessions:
        existing = json.loads((VALIDATION / "items.json").read_text(encoding="utf-8"))
        covered = {i["session_id"] for i in existing["items"]}
        new = sorted(s for s in sessions if s not in covered)
        print("sessions ajoutées :", [s[8:14] for s in new] or "aucune")
        build_sessions = {s: sessions[s] for s in new}
    else:
        build_sessions = sessions
    items = []
    for sid, data in build_sessions.items():
        units, frames = data["units"], data["frames"]
        last = max(frames)
        for unit in units["units"]:
            end = unit.get("end_established_at")
            if end is None:
                continue
            end_obs = frames[end]["obs"]
            end_screen = end_obs["result"]["visible"] is True or end_obs["state"]["phase"] == "post_game"
            views = [frame_view(sid, frames, unit["first_frame"], "début de la partie")]
            if end == unit["last_frame"]:  # the proof still shows the partie being played (MK1: last round marker)
                views.append(frame_view(sid, frames, end, "dernière image de la partie, qui prouve la fin"))
            else:
                views += [
                    frame_view(sid, frames, unit["last_frame"], "dernière image de la partie"),
                    frame_view(sid, frames, end, "image qui prouve la fin"),
                ]
            if end + 1 <= last:
                views.append(frame_view(sid, frames, end + 1, "image suivante"))
            risk = (0 if not end_screen else 1, unit.get("label_confidence", 1.0))
            items.append(
                {
                    "id": f"fin:{sid[8:16]}:{unit['unit_id']}",
                    "kind": "fin",
                    "session_id": sid,
                    "jeu": game_family(unit.get("game")),
                    "titre": f"{unit.get('game')} — {unit.get('description')}",
                    "preuve": unit.get("evidence"),
                    "score_final_vu": unit.get("final_score_seen"),
                    "confiance": unit.get("label_confidence"),
                    "écran_de_fin_capturé": end_screen,
                    "frames": [v for v in views if v],
                    "_risk": risk,
                }
            )
        for k, seg in enumerate(units.get("time_segments", [])):
            mid = (seg["first_frame"] + seg["last_frame"]) // 2
            views = [
                frame_view(sid, frames, seg["first_frame"], "début"),
                frame_view(sid, frames, mid, "milieu"),
                frame_view(sid, frames, seg["last_frame"], "fin"),
            ]
            items.append(
                {
                    "id": f"temps:{sid[8:16]}:{k + 1}",
                    "kind": "temps",
                    "session_id": sid,
                    "jeu": game_family(seg.get("game")),
                    "titre": f"{seg.get('game')} — images {seg['first_frame']} à {seg['last_frame']}",
                    "preuve": seg.get("reason"),
                    "frames": [v for v in views if v],
                    "_risk": (0, 0),
                }
            )
    fins = sorted([i for i in items if i["kind"] == "fin"], key=lambda i: i["_risk"])
    temps = [i for i in items if i["kind"] == "temps"]

    by_game = defaultdict(list)
    for sid, data in build_sessions.items():
        for fid, item in data["frames"].items():
            by_game[game_family(item["obs"]["game"]["title"])].append((sid, fid, item))
    rng = random.Random(SEED)
    obs_items = []
    for game in sorted(by_game):
        pool = by_game[game]
        n = min(len(pool), max(SAMPLE_MIN, round(SAMPLE_RATE * len(pool))))
        active = [
            p
            for p in pool
            if p[2]["obs"]["state"]["phase"] == "active" and p[2]["obs"]["state"]["screen_type"] == "gameplay"
        ]
        other = [p for p in pool if p not in active]
        k_active = min(len(active), round(n * GAMEPLAY_SHARE)) if game != NO_GAME else 0
        chosen = rng.sample(active, k_active) + rng.sample(other, min(len(other), n - k_active))
        if len(chosen) < n:
            rest = [p for p in active if p not in chosen]
            chosen += rng.sample(rest, min(len(rest), n - len(chosen)))
        for sid, fid, _ in sorted(chosen, key=lambda p: (p[0], p[1])):
            obs_items.append(
                {
                    "id": f"obs:{sid[8:16]}:{fid}",
                    "kind": "obs",
                    "session_id": sid,
                    "jeu": game,
                    "titre": f"{game} — session {sid[8:14]}, image {fid}",
                    "frames": [frame_view(sid, data_frames(sessions, sid), fid, "image à vérifier")],
                }
            )
    for i in fins + temps:
        i.pop("_risk", None)
    start = 0
    old = []
    if existing is not None:
        old = [refresh(i, sessions) for i in existing["items"]]
        start = max(i["ordre_risque"] for i in old) + 1
    for rank, i in enumerate(fins + temps + obs_items, start):
        i["ordre_risque"] = rank
        # within a session the order is the frame order (the Pi's wall clock is unreliable across sessions)
        i["ordre_chrono"] = f"{i['frames'][0]['t_session_s']:012.3f}"
    for i in old:
        i["ordre_chrono"] = f"{i['frames'][0]['t_session_s']:012.3f}"
    all_items = old + fins + temps + obs_items
    out = {
        "version": 2 if existing is not None else 1,
        "seed": SEED,
        "sample_rate": SAMPLE_RATE,
        "sample_min": SAMPLE_MIN,
        "counts": {k: sum(i["kind"] == k for i in all_items) for k in ("fin", "temps", "obs")},
        "items": all_items,
    }
    (VALIDATION / "items.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    per_game = defaultdict(int)
    for i in obs_items:
        per_game[i["jeu"]] += 1
    print(f"items.json : {len(fins)} fins de partie, {len(temps)} passages au temps, {len(obs_items)} observations")
    for game, n in sorted(per_game.items(), key=lambda x: -x[1]):
        print(f"  {n:4d}  {game}")


def data_frames(sessions, sid):
    return sessions[sid]["frames"]


if __name__ == "__main__":
    main()
