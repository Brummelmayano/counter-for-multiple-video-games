"""One dossier and one capture sheet per end missed by gradient boosting or by the GRU (6 October run, budget 1)."""
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from playend.common.paths import REPO
from playend.student.collect import frame_paths
from playend.training import data, report
from playend.training.protocol import BUDGETS
from playend.training.store import Store

OUT = REPO / "build" / "observations" / "fins_manquees" / "cas"
package, run = REPO / "build" / "playend_v1.0", REPO / "build" / "training" / "v1"
settings, choices = report.load_run(run)
store, corpus = Store(run), data.load(package)
names = corpus.feature_names
probs = {m: report.predictions(store, corpus, settings, choices, m) for m in ("gru", "boosting")}
rules = report.predictions(store, corpus, settings, choices, "rules")[0]
limits = {m: report.thresholds(settings, choices, m, BUDGETS[0]) for m in ("gru", "boosting")}
obs, meta = defaultdict(dict), defaultdict(dict)
with open(package / "data" / "observations.csv", newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        obs[row["session_id"]][int(row["frame_id"])] = json.loads(row["observation_json"])
        meta[row["session_id"]][int(row["frame_id"])] = row
ends = list(csv.DictReader(open(run / "ends.csv", encoding="utf-8")))
units = {(u["session_id"], u["unit_id"]): u for u in csv.DictReader(open(package / "data" / "units.csv", encoding="utf-8"))}
KEY_FEATURES = [n for n in names if n.endswith((".changed", ".changed.known", ".delta_candidate", ".delta_candidate.known"))
                or n in ("result.visible", "result.visible.known", "clock.seconds_since_previous_readable", "delta_t_s")]
t = lambda v: v == "True"


def compact(o):
    counters = [f"{c['kind']}:{c['side']}={c['value']}" for c in (o.get("secondary_counters") or [])]
    timers = [f"{c['kind']}={c['display']}" for c in (o.get("secondary_timers") or [])]
    return {
        "game": f"{o['game']['title']} | {o['game']['type']} | mode={o['game']['mode']}",
        "screen": f"{o['state']['screen_type']} / phase={o['state']['phase']}",
        "score": f"{o['score']['a']}-{o['score']['b']} ({o['score']['type']})",
        "clock": o["clock"]["display"], "period": f"{o['period']['type']} {o['period']['number']}/{o['period']['total']}",
        "progress": f"{o['progress']['type']} {o['progress']['current']}/{o['progress']['total']}",
        "position": f"{o['position']['current']}/{o['position']['total']}",
        "participants": o["participants"]["primary"], "result": o["result"],
        "counters": counters if o.get("secondary_counters") is not None else None,
        "timers": timers if o.get("secondary_timers") is not None else None,
    }


made = []
for end in ends:
    if t(end["boosting"]) and t(end["gru"]):
        continue
    session, unit_id = end["session"], end["unit"]
    unit = units[(session, unit_id)]
    order = sorted(obs[session])
    seq = corpus.sequences[session]
    row_of = {frame: index for index, frame in enumerate(order)}
    first, last, proof = int(unit["first_frame"]), int(end["last_frame"]), int(end["end_frame"])
    window = [f for f in order if max(first, last - 2) <= f <= proof + 2]
    gru = np.mean([p[session] for p in probs["gru"]], axis=0)
    gb = probs["boosting"][0][session]
    case_id = f"{end['family'].split(':')[0].replace(' ', '_').replace('!', '')}_{session[8:16]}_{unit_id}"
    frames = []
    for frame in window:
        row = row_of[frame]
        role = ("capture qui prouve la fin" if frame == proof else "dernière capture de la partie" if frame == last
                else "entre les deux" if last < frame < proof else "avant" if frame < last else "après")
        frames.append({"frame": frame, "role": role, "image": str(frame_paths(session)[frame]),
                       "t_s": float(meta[session][frame]["t_s"]), "gru_p": round(float(gru[row]), 3),
                       "boosting_p": round(float(gb[row]), 3), "rules_p": round(float(rules[session][row]), 3),
                       "observation": compact(obs[session][frame]), "annotator": meta[session][frame].get("annotator", "")[:18]})
    features = {}
    for frame in (proof - 1, proof, proof + 1):
        if frame in row_of:
            x = seq.x[row_of[frame]]
            features[str(frame)] = {n: round(float(x[names.index(n)]), 3) for n in KEY_FEATURES if float(x[names.index(n)]) != 0.0}
    dossier = {
        "case_id": case_id, "session": session, "unit": unit_id, "family": end["family"],
        "single_session_game": t(end["single_session_game"]), "game_description": unit["description"],
        "first_frame": first, "last_frame": last, "end_frame": proof, "final_score_seen": unit["final_score_seen"],
        "label_confidence": unit["label_confidence"], "evidence_of_the_end": unit["evidence"],
        "found": {"gru_seeds_of_5": int(end["gru_seeds_found"]), "gru": t(end["gru"]), "boosting": t(end["boosting"]),
                  "logistic": t(end["logistic"]), "rules": t(end["rules"])},
        "thresholds": {"gru": float(end["gru_threshold"]), "boosting": float(end["boosting_threshold"])},
        "peaks_at_end": {"gru": float(end["gru_peak"]), "boosting": float(end["boosting_peak"])},
        "frames": frames, "nonzero_change_features": features,
    }
    (OUT / f"{case_id}.json").write_text(json.dumps(dossier, ensure_ascii=False, indent=1), encoding="utf-8")
    tiles = []
    for item in frames:
        image = Image.open(item["image"]).convert("RGB").resize((640, 360))
        canvas = Image.new("RGB", (640, 384), "white")
        canvas.paste(image, (0, 24))
        label = f"{item['frame']} {item['role']}  GRU {item['gru_p']:.2f}  GB {item['boosting_p']:.2f}"
        ImageDraw.Draw(canvas).text((4, 6), label, fill="black")
        tiles.append(canvas)
    columns = 3
    rows_count = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 646, rows_count * 390), "#888888")
    for index, tile in enumerate(tiles):
        sheet.paste(tile, ((index % columns) * 646, (index // columns) * 390))
    sheet.save(OUT / f"{case_id}.jpg", quality=88)
    made.append((case_id, end["family"], session[8:16]))
(OUT.parent / "cas_index.json").write_text(json.dumps(made, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(made), "dossiers")
