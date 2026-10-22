"""How informative are the captures, and how visible is the start of each game, in PlayEnd (teacher observations)."""
import csv, json, statistics
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3] / "build" / "playend_v1.0" / "data"
obs = defaultdict(dict); fam = defaultdict(dict); bill = defaultdict(dict); tt = defaultdict(dict)
for r in csv.DictReader(open(ROOT / "observations.csv", encoding="utf-8")):
    s, f = r["session_id"], int(r["frame_id"])
    obs[s][f] = json.loads(r["observation_json"]); fam[s][f] = r["game_family"]; bill[s][f] = r["billing_mode"]; tt[s][f] = float(r["t_s"])
units = [u for u in csv.DictReader(open(ROOT / "units.csv", encoding="utf-8"))]
DECISIVE_STATES = {"result", "scoreboard", "podium", "menu", "loading", "character_select", "team_select", "race_grid"}
def values(o):
    v = {}
    if o["score"]["a"] is not None or o["score"]["b"] is not None: v["score"] = (o["score"]["a"], o["score"]["b"])
    if o["clock"]["display"]: v["clock"] = o["clock"]["display"]
    if o["progress"]["current"] is not None: v["progress"] = o["progress"]["current"]
    if o["position"]["current"] is not None: v["position"] = o["position"]["current"]
    cs = [c for c in (o.get("secondary_counters") or []) if c.get("value") is not None]
    if cs: v["counters"] = tuple(sorted((c["kind"], c["side"], c["value"]) for c in cs))
    if o["result"]["visible"] is True: v["result"] = True
    return v
def informative(o):
    return bool(values(o)) or o["state"]["screen_type"] in DECISIVE_STATES or o["state"]["phase"] in ("post_game", "pre_game", "menu", "loading")
total = Counter()
for s in obs:
    prev = None
    for f in sorted(obs[s]):
        o = obs[s][f]; info = informative(o)
        key = json.dumps({k: o[k] for k in ("game", "state", "score", "clock", "period", "progress", "position", "result", "secondary_counters")}, sort_keys=True)
        total["all"] += 1
        total["informative"] += info
        total[f"uninformative_{bill[s][f]}"] += not info
        total["duplicate_of_previous"] += key == prev
        prev = key
print("captures:", dict(total))
# start visibility per family: first readable gameplay capture of each counted unit
by_family = defaultdict(Counter); persist = defaultdict(list)
def start_like(o, family):
    a, b = o["score"]["a"], o["score"]["b"]
    sc = (a or 0) + (b or 0) if (a is not None or b is not None) else None
    sec = o["clock"]["value_seconds"]; disp = o["clock"]["display"] or ""
    counters = {(c["kind"]): c["value"] for c in (o.get("secondary_counters") or []) if c.get("value") is not None}
    if family in ("Fortnite", "Call of Duty: Warzone"):
        pr = counters.get("players_remaining")
        return None if pr is None else pr >= 60
    if family == "Beach Buggy Racing 2":
        p = o["progress"]["current"]
        return None if p is None else p == 1
    if sc is None: return None
    if sc != 0: return False
    if family == "EA Sports FC":
        return sec is None or sec <= 20 * 60
    return True  # fighting games: rounds 0-0 is the start of a match
for u in units:
    if u["termination"] != "completed" and False: pass
    s = u["session_id"]; first, last = int(u["first_frame"]), int(u["last_frame"])
    family = u["game_family"]
    frames = [f for f in sorted(obs[s]) if first <= f <= last]
    readable = [f for f in frames if start_like(obs[s][f], family) is not None and obs[s][f]["state"]["screen_type"] == "gameplay"]
    if not readable:
        by_family[family]["no readable start value"] += 1; continue
    ok = start_like(obs[s][readable[0]], family)
    by_family[family]["start visible" if ok else "first reading already past the start"] += 1
    n = 0
    for f in readable:
        if start_like(obs[s][f], family): n += 1
        else: break
    persist[family].append(n)
print("\nunits per family: start visible on the first readable gameplay capture?")
for family, c in sorted(by_family.items(), key=lambda kv: -sum(kv[1].values())):
    n = sum(c.values())
    p = persist[family]
    print(f"  {family[:26]:26s} {n:3d} units  {dict(c)}  start-like readings in a row: median {statistics.median(p) if p else '-'}")
