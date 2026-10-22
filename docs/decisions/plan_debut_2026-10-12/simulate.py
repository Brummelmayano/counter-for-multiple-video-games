"""Simulate a start-of-game counter on PlayEnd teacher observations: informative captures only, comparison with the
last readable value, a new game counted when start values come back after the game had progressed (or after a game
change or an out-of-game screen), confirmed by a second start reading. No training: rules only, upper bound."""
import csv, json, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3] / "build" / "playend_v1.0" / "data"
TRUE_BILLING = "--true-billing" in sys.argv
obs, meta = defaultdict(dict), defaultdict(dict)
for r in csv.DictReader(open(ROOT / "observations.csv", encoding="utf-8")):
    obs[r["session_id"]][int(r["frame_id"])] = json.loads(r["observation_json"]); meta[r["session_id"]][int(r["frame_id"])] = r
units = defaultdict(list)
for u in csv.DictReader(open(ROOT / "units.csv", encoding="utf-8")):
    units[u["session_id"]].append(u)
FIGHT = {"Mortal Kombat 1", "Tekken 8", "Naruto Storm Connections", "J-Stars Victory VS+", "Demon Slayer", "Dragon Ball FighterZ", "Brawlhalla"}
OUT_OF_GAME = {"result", "scoreboard", "podium", "menu", "loading", "character_select", "team_select", "race_grid"}

def reading(o, family):
    """('start' | 'progressed' | None) for a gameplay capture."""
    if o["state"]["screen_type"] != "gameplay":
        return None
    a, b = o["score"]["a"], o["score"]["b"]
    total = None if a is None and b is None else (a or 0) + (b or 0)
    sec, disp = o["clock"]["value_seconds"], (o["clock"]["display"] or "")
    cnt = defaultdict(list)
    for c in (o.get("secondary_counters") or []):
        if c.get("value") is not None:
            cnt[c["kind"]].append(c["value"])
    if family in ("Fortnite", "Call of Duty: Warzone"):
        p = cnt.get("players_remaining")
        return None if not p else ("start", p[0]) if False else ("players", p[0])
    if family == "Beach Buggy Racing 2":
        lap = o["progress"]["current"]
        return None if lap is None else "start" if lap == 1 else "progressed"
    if family == "EA Sports UFC 5":
        rnd = o["period"]["number"]
        if rnd is None or sec is None: return None
        return "start" if rnd == 1 and sec >= 240 else "progressed"
    if family == "Dragon Ball Sparking! ZERO":
        if disp.strip() == "∞": return "start"
        lives = cnt.get("lives")
        return None if not lives else "start" if min(lives) >= 4 else "progressed"
    if total is None: return None
    if total > 0: return "progressed"
    if family == "EA Sports FC" and sec is not None and sec > 20 * 60: return "progressed"
    return "start"

starts_pred = defaultdict(list)
for s in obs:
    frames = sorted(obs[s])
    game = None   # dict(family, progressed, start_frame, last_players)
    out_seen = True
    pending = None
    for f in frames:
        o, m = obs[s][f], meta[s][f]
        family = m["game_family"]
        if TRUE_BILLING and m["billing_mode"] == "time_based":
            continue
        if o["state"]["screen_type"] in OUT_OF_GAME or o["state"]["phase"] in ("post_game", "pre_game", "menu", "loading"):
            out_seen = True
            continue
        if not family:
            continue
        r = reading(o, family)
        if r is None:
            continue  # uninformative capture: ignored, never a break
        if isinstance(r, tuple):  # battle royale: players remaining
            players = r[1]
            if game and game["family"] == family and game.get("last_players") is not None:
                r = "start" if players > game["last_players"] + 10 else "progressed"
            else:
                r = "start"
        new_context = game is None or game["family"] != family or out_seen or game["progressed"]
        if r == "start" and new_context and (game is None or game["family"] != family or game["progressed"] or out_seen):
            if pending is None:
                pending = f
            else:
                starts_pred[s].append(pending)
                game = {"family": family, "progressed": False, "start_frame": pending}
                pending = None
                out_seen = False
        elif r == "start" and pending is not None:
            starts_pred[s].append(pending); game = {"family": family, "progressed": False, "start_frame": pending}; pending = None; out_seen = False
        else:
            if pending is not None and r == "progressed" and game is not None and game["family"] == family and not game["progressed"] and not out_seen:
                pending = None
            if r == "progressed":
                if pending is not None:  # a single start reading then progress: accept when it followed an out-of-game screen
                    starts_pred[s].append(pending); game = {"family": family, "progressed": True, "start_frame": pending}; pending = None
                elif game is None or game["family"] != family:
                    game = {"family": family, "progressed": True, "start_frame": f}
                    starts_pred[s].append(f)  # game seen already in progress: still a game
                else:
                    game["progressed"] = True
                out_seen = False
        if game is not None and family in ("Fortnite", "Call of Duty: Warzone"):
            game["last_players"] = players
    if pending is not None:
        starts_pred[s].append(pending)

# evaluation: each reference game (unit) matched to at most one predicted start in its first captures
found, missed, false = 0, 0, 0
by_family = defaultdict(Counter)
for s in obs:
    frames = sorted(obs[s]); index = {f: i for i, f in enumerate(frames)}
    preds = sorted(starts_pred[s]); used = set()
    for u in sorted(units[s], key=lambda u: int(u["first_frame"])):
        first, last = int(u["first_frame"]), int(u["last_frame"])
        window = [f for f in frames if first <= f <= last][:5]
        hit = next((p for p in preds if p in window and p not in used), None)
        by_family[u["game_family"]]["games"] += 1
        if hit is None:
            missed += 1; by_family[u["game_family"]]["missed"] += 1
        else:
            used.add(hit); found += 1; by_family[u["game_family"]]["found"] += 1
    for p in preds:
        if p not in used:
            false += 1; by_family[meta[s][p]["game_family"] or "(none)"]["false"] += 1
n = found + missed
print(f"{'true billing modes' if TRUE_BILLING else 'all captures'}: games {n}, starts found {found} ({found/n:.1%}), missed {missed}, false starts {false} ({100*false/n:.1f} per 100 games)")
for fam, c in sorted(by_family.items(), key=lambda kv: -kv[1]['games']):
    print(f"  {fam[:26]:26s} games {c['games']:3d} found {c['found']:3d} missed {c['missed']:3d} false {c['false']:3d}")
