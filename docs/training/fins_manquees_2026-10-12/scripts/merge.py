"""Merge the analyst and the three reviews into one record per missed end, with a consensus cause and the real cost."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from playend.common.paths import REPO

ROOT = REPO
HERE = ROOT / "build" / "observations" / "fins_manquees"
SYNONYMS = {"AVANCE": "ANNONCE_EN_AVANCE", "ANNONCE_PRECOCE": "ANNONCE_EN_AVANCE", "FIN_NON_CAPTUREE": "FIN_ENTRE_CAPTURES",
            "DECALAGE_ECHELLE": "SEUIL", "ETIQUETTE_INCOHERENTE": "ETIQUETTE_DOUTEUSE", "CIBLE_INCOHERENTE": "ETIQUETTE_DOUTEUSE"}
norm = lambda code: SYNONYMS.get((code or "").strip(), (code or "").strip())
load = lambda path: {r["case_id"]: r for r in map(json.loads, filter(str.strip, open(path, encoding="utf-8")))}
analyst = {}
for path in sorted((HERE / "analyses").glob("lot*.jsonl")):
    analyst.update(load(path))
reviews = {name: load(HERE / "analyses" / f"revue_{name}.jsonl") for name in ("apprentissage", "annotation", "terrain")}
ends = {}
for row in csv.DictReader(open(ROOT / "build/training/v1/ends.csv", encoding="utf-8")):
    case = f"{row['family'].split(':')[0].replace(' ', '_').replace('!', '')}_{row['session'][8:16]}_{row['unit']}"
    ends[case] = row
units = defaultdict(list)
for unit in csv.DictReader(open(ROOT / "build/playend_v1.0/data/units.csv", encoding="utf-8")):
    units[unit["session_id"]].append(unit)
times, types = defaultdict(dict), {}
for row in csv.DictReader(open(ROOT / "build/playend_v1.0/data/observations.csv", encoding="utf-8")):
    times[row["session_id"]][int(row["frame_id"])] = float(row["t_s"])
    types[(row["session_id"], int(row["frame_id"]))] = json.loads(row["observation_json"])["game"]["type"]
t = lambda v: v == "True"


def duration(session, unit):
    return times[session][int(unit["last_frame"])] - times[session][int(unit["first_frame"])]


def threshold(session, unit):
    return 15 if types[(session, int(unit["last_frame"]))] in ("combat", "combat_sport") else 60


records = []
for case, a in analyst.items():
    end = ends[case]
    session = end["session"]
    unit = next(u for u in units[session] if u["unit_id"] == end["unit"])
    following = sorted((u for u in units[session] if int(u["first_frame"]) >= int(end["end_frame"])), key=lambda u: int(u["first_frame"]))
    d, limit = duration(session, unit), threshold(session, unit)
    if not following:
        cost = "aucun : dernière partie de l'enregistrement, comptée au départ du client"
    elif d < limit or duration(session, following[0]) < threshold(session, following[0]):
        cost = "aucun : une des deux parties est sous le seuil de relance rapide"
    else:
        cost = "une partie perdue par la salle"
    votes = [norm(a["cause_principale"])] + [norm(reviews[n][case]["cause_principale_selon_moi"]) for n in reviews]
    count = Counter(votes)
    top, n = count.most_common(1)[0]
    consensus = top if n >= 2 else votes[0]
    records.append({
        "case_id": case, "jeu": end["family"], "session": session[8:16], "partie": end["unit"],
        "derniere_capture": end["last_frame"], "capture_qui_prouve_la_fin": end["end_frame"],
        "trouvee_par": ", ".join(m for m in ("gru", "boosting", "logistic", "rules") if t(end[m])) or "aucun",
        "cause_analyste": norm(a["cause_principale"]), "causes_secondaires": ", ".join(map(norm, a["causes_secondaires"] or [])),
        "cause_apprentissage": votes[1], "cause_annotation": votes[2], "cause_terrain": votes[3],
        "cause_consensus": consensus, "accord_consensus": f"{n}/4",
        "etiquette_analyste": a["etiquette"], "accord_annotation": reviews["annotation"][case]["accord"],
        "cout": cost, "duree_partie_s": round(d), "ce_qui_prouve_la_fin": a["ce_qui_prouve_la_fin"],
        "probleme_observation": a["probleme_observation"], "pourquoi_gru": a["pourquoi_gru"],
        "pourquoi_gradient_boosting": a["pourquoi_gradient_boosting"], "pourquoi_regles": a["pourquoi_regles"],
        "methode": a["methode_qui_la_trouverait"],
        "avis_apprentissage": reviews["apprentissage"][case]["commentaire"],
        "avis_annotation": reviews["annotation"][case]["commentaire"], "avis_terrain": reviews["terrain"][case]["commentaire"],
    })
records.sort(key=lambda r: (r["jeu"], r["session"], int(r["capture_qui_prouve_la_fin"])))
with open(HERE / "causes_par_fin.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
lines = ["# Les 211 fins manquées, une par une", "",
         "Pour chaque fin manquée par le gradient boosting ou le GRU (calcul du 6 octobre, budget d'une fausse fin pour 100",
         "parties) : ce qui la prouve, ce que l'observation a noté, pourquoi chaque détecteur l'a manquée, la cause selon",
         "l'analyste et selon les trois relecteurs, la cause de consensus, le coût pour la salle et la méthode qui l'aurait",
         "trouvée. Planche des captures et dossier complet : liens de chaque titre. Synthèse :",
         "`docs/training/FINS_MANQUEES_CAS_PAR_CAS_2026-10-12.md`. Hors de git : les planches montrent des pseudos.", ""]
for r in records:
    lines += [f"## [{r['case_id']}](cas/{r['case_id']}.jpg) ([dossier](cas/{r['case_id']}.json))", "",
              f"{r['jeu']}, enregistrement {r['session']}, partie {r['partie']} ; dernière capture {r['derniere_capture']}, "
              f"fin prouvée en {r['capture_qui_prouve_la_fin']} ; trouvée par : {r['trouvee_par']}.", "",
              f"- **Cause de consensus : {r['cause_consensus']}** ({r['accord_consensus']}) ; analyste {r['cause_analyste']}, "
              f"apprentissage {r['cause_apprentissage']}, annotation {r['cause_annotation']}, terrain {r['cause_terrain']}. "
              f"Secondaires : {r['causes_secondaires'] or 'aucune'}.",
              f"- **Étiquette :** {r['etiquette_analyste']} (relecture annotation : accord {r['accord_annotation']}). **Coût :** {r['cout']}.",
              f"- **Ce qui prouve la fin :** {r['ce_qui_prouve_la_fin']}",
              f"- **Observation :** {r['probleme_observation']}",
              f"- **GRU :** {r['pourquoi_gru']}", f"- **Gradient boosting :** {r['pourquoi_gradient_boosting']}",
              f"- **Règles :** {r['pourquoi_regles']}", f"- **Méthode :** {r['methode']}",
              f"- **Avis apprentissage :** {r['avis_apprentissage']}", f"- **Avis annotation :** {r['avis_annotation']}",
              f"- **Avis terrain :** {r['avis_terrain']}", ""]
(HERE / "CAUSES_PAR_FIN.md").write_text("\n".join(lines), encoding="utf-8")
both = [r for r in records if r["trouvee_par"] in ("aucun", "logistic", "rules", "logistic, rules")]
print(len(records), "records")
print("consensus:", Counter(r["cause_consensus"] for r in records).most_common())
print("agreement:", Counter(r["accord_consensus"] for r in records))
print("cost:", Counter(r["cout"].split(" :")[0] for r in records))
gb_missed = [r for r in records if "boosting" not in r["trouvee_par"]]; gru_missed = [r for r in records if "gru" not in r["trouvee_par"]]
print("cost with GB:", sum(r["cout"].startswith("une partie") for r in gb_missed), "of", len(gb_missed), "| with GRU:", sum(r["cout"].startswith("une partie") for r in gru_missed), "of", len(gru_missed))
print("consensus among the 133 missed by both:", Counter(r["cause_consensus"] for r in records if "boosting" not in r["trouvee_par"] and "gru" not in r["trouvee_par"]).most_common(9))
