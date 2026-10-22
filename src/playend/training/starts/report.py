"""Pool the outer folds, compare the methods and write <out>/results.json and <out>/RAPPORT.md.

Every session is predicted once, by a model that never saw its fold. The 95 % intervals come from resampling whole
sessions (cluster bootstrap, Field and Welsh, 2007); each method is compared with the rules session by session with
the Wilcoxon signed-rank test on the errors (games missed plus games in excess), as Demšar (2006) recommends."""

from __future__ import annotations

import json
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

from playend.common.games import game_family
from playend.counting.starts import Start, match
from playend.training.starts import events

RESAMPLES = 2000
LEARNED = ("gb_raw", "gb_state", "gb_state_dilated", "gb_end_support", "gb_rules", "gb_transition", "hybrid", "gru")
LABELS = {
    "rules": "Règles (écrites sur toutes les sessions)",
    "rules_tuned": "Règles, seuils choisis par validation croisée",
    "gb_raw": "Gradient boosting, 262 variables de l'image et des 2 précédentes",
    "gb_state": "Gradient boosting, état de la partie + variables de l'image",
    "gb_state_dilated": "Gradient boosting, état + étiquette étalée",
    "gb_end_support": "Gradient boosting, état + probabilité de fin en appui",
    "gb_rules": "Gradient boosting, état + décisions des règles (empilement)",
    "gb_transition": "Fin depuis la dernière lecture de jeu, puis début (somme)",
    "hybrid": "Règles proposent, gradient boosting vérifie et complète",
    "gru": "GRU début + fin, captures porteuses",
}


def load_predictions(out: Path, source: str, folds) -> dict[str, dict]:
    """method -> budget -> session -> starts, for the methods whose outer folds are all done."""
    results = out / "results"
    methods = {}
    rules = results / f"{source}-rules.json"
    if rules.exists():
        data = json.loads(rules.read_text(encoding="utf-8"))
        methods["rules"], methods["rules_tuned"] = data["fixed"], data["predicted"]
    for method in LEARNED:
        paths = [results / f"{source}-{method}-o{outer}.json" for outer in folds]
        if not all(path.exists() for path in paths):
            continue
        merged = defaultdict(dict)
        for path in paths:
            for budget, sessions in json.loads(path.read_text(encoding="utf-8"))["predicted"].items():
                merged[budget] |= sessions
        methods[method] = dict(merged)
    return methods


def per_session(prepared, predicted: dict, names: list[str]) -> dict[str, events.Tally]:
    return {name: events.score(prepared.sessions[name], [tuple(pair) for pair in predicted.get(name, [])])
            for name in names}  # fmt: skip


def bootstrap(names: list[str], tallies: dict, reference: dict | None, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    games = np.array([tallies[n].games for n in names], float)
    found = np.array([tallies[n].found for n in names], float)
    extra = np.array([tallies[n].extra for n in names], float)
    ref_found = np.array([reference[n].found for n in names], float) if reference else None
    ref_extra = np.array([reference[n].extra for n in names], float) if reference else None
    draws = defaultdict(list)
    for _ in range(RESAMPLES):
        pick = rng.integers(0, len(names), len(names))
        g = games[pick].sum()
        draws["recall"].append(100 * found[pick].sum() / g)
        draws["extra_per_100"].append(100 * extra[pick].sum() / g)
        if reference:
            draws["recall_gain"].append(100 * (found[pick].sum() - ref_found[pick].sum()) / g)
            draws["extra_change"].append(100 * (extra[pick].sum() - ref_extra[pick].sum()) / g)
    return {key: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for key, v in draws.items()}


def compare(names, tallies, reference) -> dict:
    errors = np.array([tallies[n].games - tallies[n].found + tallies[n].extra for n in names])
    ref = np.array([reference[n].games - reference[n].found + reference[n].extra for n in names])
    if np.all(errors == ref):
        return {"wilcoxon_p": 1.0, "sessions_better": 0, "sessions_worse": 0}
    return {"wilcoxon_p": float(wilcoxon(errors, ref, zero_method="wilcox").pvalue),
            "sessions_better": int((errors < ref).sum()), "sessions_worse": int((errors > ref).sum())}  # fmt: skip


def by_family(prepared, predicted) -> dict[str, dict]:
    """Games found per family of the reference game; a start in excess counts for the game read on its capture."""
    out = defaultdict(lambda: {"games": 0, "found": 0, "extra": 0})
    for name, session in prepared.sessions.items():
        if name not in predicted:
            continue
        starts = [tuple(pair) for pair in predicted[name]]
        objects = [Start(f, d, "", False) for f, d in starts]
        found = match(session.units, objects, session.frames)
        used = {id(start) for start in found.values()}
        for unit in session.units:
            family = game_family(unit["game"])
            out[family]["games"] += 1
            out[family]["found"] += unit["unit_id"] in found
        for start in objects:
            if id(start) not in used:
                out[game_family(session.observations[start.frame - 1]["game"]["title"])]["extra"] += 1
    return dict(out)


def summarise(prepared, methods: dict, folds) -> dict:
    names = sorted(name for name, session in prepared.sessions.items() if session.fold in folds)
    summary = {}
    reference = {budget: per_session(prepared, methods["rules"][budget], names) for budget in methods["rules"]} if (
        "rules" in methods) else {}  # fmt: skip
    for method, budgets in methods.items():
        summary[method] = {}
        for budget, predicted in budgets.items():
            tallies = per_session(prepared, predicted, names)
            total = sum(tallies.values(), events.Tally())
            ref = reference.get(budget) if method != "rules" else None
            summary[method][budget] = {
                **total.as_dict(),
                "interval": bootstrap(names, tallies, ref),
                "against_rules": compare(names, tallies, ref) if ref else None,
                "families": by_family(prepared, {n: predicted.get(n, []) for n in names})
                if float(budget) == events.MAIN_BUDGET
                else None,
            }
    return summary


def percent(value) -> str:
    return f"{value:.1f}".replace(".", ",")


def interval(bounds) -> str:
    return f"[{percent(bounds[0])} ; {percent(bounds[1])}]"


def markdown(summaries: dict, folds) -> str:
    lines = [
        "# Détecteurs de débuts : règles et modèles appris (validation croisée imbriquée)",
        "",
        "Rapport écrit par `python -m playend.training.starts.run`. Protocole et sources :",
        "`docs/training/PROTOCOLE_DEBUTS.md`. Chaque session est prédite une seule fois, par un modèle",
        f"qui n'a jamais vu son pli (plis extérieurs {', '.join(map(str, folds))}). Les règles ont été",
        "écrites en lisant toutes les sessions : leurs chiffres sont optimistes, ceux des modèles appris",
        "ne le sont pas. Intervalles à 95 % par rééchantillonnage des sessions ; p : test des rangs",
        "signés de Wilcoxon contre les règles, sur les erreurs par session (+ sessions meilleures,",
        "− sessions moins bonnes).",
        "",
    ]
    for source, summary in summaries.items():
        lines += [f"## Source : {'professeur' if source == 'teacher' else 'élève'}", ""]
        for budget in (str(b) for b in events.BUDGETS):
            lines += [f"### Budget : {percent(float(budget))} partie en trop pour 100 (seuil choisi en validation)", "",
                      "| Méthode | Trouvées % | En trop /100 | Précision % | Compte exact | p contre règles |",
                      "|---|---|---|---|---|---|"]  # fmt: skip
            for method, by_budget in summary.items():
                if budget not in by_budget:
                    continue
                r = by_budget[budget]
                against = r["against_rules"]
                p = (
                    "—"
                    if not against
                    else f"{against['wilcoxon_p']:.3f} (+{against['sessions_better']}/−{against['sessions_worse']})"
                )
                found = f"{percent(100 * r['recall'])} {interval(r['interval']['recall'])}"
                extra = f"{percent(r['extra_per_100'])} {interval(r['interval']['extra_per_100'])}"
                exact = f"{r['exact']} sur {r['sessions']}"
                lines.append(f"| {LABELS.get(method, method)} | {found} | {extra} | {percent(100 * r['precision'])} "
                             f"| {exact} | {p} |")  # fmt: skip
            lines.append("")
        main = str(events.MAIN_BUDGET)
        learned = {m: s[main] for m, s in summary.items() if m in LEARNED and main in s}
        if learned and "rules" in summary:
            best = max(learned, key=lambda m: (learned[m]["recall"], -learned[m]["extra_per_100"]))
            lines += [f"### Par jeu, budget {percent(events.MAIN_BUDGET)} : règles et {LABELS[best]}", "",
                      "| Jeu | Parties | Règles : trouvées / en trop | Modèle : trouvées / en trop |",
                      "|---|---|---|---|"]  # fmt: skip
            rules_families = summary["rules"][main]["families"] or {}
            for family, counts in sorted(rules_families.items(), key=lambda item: -item[1]["games"]):
                other = learned[best]["families"].get(family, {"found": 0, "extra": 0})
                lines.append(f"| {family or '(aucun jeu)'} | {counts['games']} | {counts['found']} / {counts['extra']} "
                             f"| {other['found']} / {other['extra']} |")  # fmt: skip
            lines.append("")
    return "\n".join(lines) + "\n"


def write(out: Path, sources, folds) -> None:
    summaries = {}
    for source in sources:
        path = out / "prepared" / f"{source}.pkl"
        if not path.exists():
            continue
        with path.open("rb") as stream:
            prepared = pickle.load(stream)
        methods = load_predictions(out, source, folds)
        if methods:
            summaries[source] = summarise(prepared, methods, folds)
    (out / "results.json").write_text(json.dumps(summaries, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "RAPPORT.md").write_text(markdown(summaries, folds), encoding="utf-8")
