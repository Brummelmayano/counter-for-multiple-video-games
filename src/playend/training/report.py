"""The report of a run, read from the stored results: nothing is trained here.

usage: python -m playend.training.report --package PACKAGE --out RUN_FOLDER
"""

from __future__ import annotations

import argparse
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

from playend.common.paths import REPO
from playend.training import baselines, data
from playend.training.data import BILLING_MODES, Corpus
from playend.training.events import Tally, by_family, curve, match
from playend.training.protocol import ALL, BUDGETS, final_jobs
from playend.training.store import Store, read_json, write_json

BOOTSTRAP = 2000
FIRST = str(BUDGETS[0])
NAMES = {"gru": "GRU", "logistic": "régression logistique", "boosting": "gradient boosting", "rules": "règles"}
# Drawn by playend.training.figures into <run>/figures/.
FIGURES = {
    "models.png": "rappel et fausses fins de chaque modèle sur les sessions tenues à l'écart, pour les trois seuils",
    "precision_recall.png": "précision et rappel par événements selon le seuil, GRU et meilleur modèle de référence",
    "learning_curves.png": "pertes d'entraînement et de validation du GRU retenu, dans chaque tour",
    "trials.png": "rappel de validation de chaque essai de réglages, par modèle",
    "settings.png": "meilleur rappel de validation obtenu avec chaque valeur d'un réglage étudié",
    "ablation.png": "effet sur le rappel de validation du retrait de chaque groupe de variables",
    "families.png": "fins trouvées et fausses fins par famille de jeu",
    "billing.png": "matrice de confusion du mode de facturation prédit par le GRU",
    "sessions/": "une figure par session tenue à l'écart : probabilité de fin, vraies fins, fins prédites",
}


def held_out(settings: dict) -> list[str]:
    return [outer for outer in settings["outers"] if outer != ALL]


def final_arrays(store: Store, settings: dict, choices: dict, model: str, suffix: str = "") -> list[dict]:
    """What the final models stored for their held-out session, one {session: array} per seed."""
    runs: dict[int, dict] = {}
    for outer in held_out(settings):
        for job in final_jobs(choices[outer], outer, settings["seeds"]):
            if job.model == model:
                runs.setdefault(job.seed, {})[outer] = store.arrays(job.id)[outer + suffix]
    return [runs[seed] for seed in sorted(runs)]


def predictions(store: Store, corpus: Corpus, settings: dict, choices: dict, model: str) -> list[dict]:
    if model == "rules":  # one run, nothing trained
        return [{session: baselines.rules(corpus.sequences[session]) for session in held_out(settings)}]
    return final_arrays(store, settings, choices, model)


def thresholds(settings: dict, choices: dict, model: str, budget: float) -> dict:
    if model == "rules":
        return dict.fromkeys(held_out(settings), 0.5)
    return {
        outer: choices[outer]["models"][model]["thresholds"][str(budget)]["threshold"] for outer in held_out(settings)
    }


def per_session(sequences, runs: list[dict], limits: dict) -> dict[str, np.ndarray]:
    """Ends, ends found and false ends of every session, averaged over the seeds."""
    counts = np.zeros((len(runs), len(sequences), 3))
    for seed, probs in enumerate(runs):
        for index, sequence in enumerate(sequences):
            found, missed, false = match(sequence, probs[sequence.session], limits[sequence.session])
            counts[seed, index] = (len(found) + len(missed), len(found), len(false))
    mean = counts.mean(axis=0)
    return {"ends": mean[:, 0], "found": mean[:, 1], "false": mean[:, 2], "runs": counts}


def ratios(ends, found, false, hours) -> dict:
    return {
        "hours": round(hours, 3),
        "ends": float(ends),
        "found": float(found),
        "false": float(false),
        "precision": found / (found + false) if found + false else None,
        "recall": found / ends if ends else None,
        "false_per_100": 100 * false / ends if ends else None,
        "false_per_hour": false / hours if hours else None,
    }


def summary(sequences, counts: dict) -> dict:
    hours = sum(sequence.hours for sequence in sequences)
    by_seed = [ratios(*run.sum(axis=0), hours) for run in counts["runs"]]
    out = ratios(counts["ends"].sum(), counts["found"].sum(), counts["false"].sum(), hours)
    for key in ("precision", "recall", "false_per_100"):
        values = [seed[key] for seed in by_seed if seed[key] is not None]
        out[f"{key}_sd"] = statistics.pstdev(values) if len(values) > 1 else 0.0
    return out


def bootstrap(counts: dict, seed: int = 0) -> dict:
    """95 % intervals by resampling whole sessions."""
    rng = np.random.default_rng(seed)
    sessions = len(counts["ends"])
    samples = {"precision": [], "recall": [], "false_per_100": []}
    for _ in range(BOOTSTRAP):
        pick = rng.integers(0, sessions, sessions)
        ends, found, false = (counts[key][pick].sum() for key in ("ends", "found", "false"))
        if ends and found + false:
            samples["precision"].append(found / (found + false))
            samples["recall"].append(found / ends)
            samples["false_per_100"].append(100 * false / ends)
    return {
        key: [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]
        for key, values in samples.items()
        if values
    }


def compare(gru: dict, other: dict) -> dict:
    """Wilcoxon signed-rank tests over sessions (Demšar 2006): recall on sessions with ends, and false ends."""
    with_ends = gru["ends"] > 0
    pairs = {
        "recall": (
            gru["found"][with_ends] / gru["ends"][with_ends],
            other["found"][with_ends] / other["ends"][with_ends],
        ),
        "false_ends": (gru["false"], other["false"]),
    }
    out = {}
    for name, (gru_values, other_values) in pairs.items():
        try:
            with np.errstate(divide="ignore", invalid="ignore"):
                p_value = float(wilcoxon(gru_values, other_values).pvalue)
        except ValueError:  # every difference is zero
            p_value = float("nan")
        out[name] = {"p_value": None if np.isnan(p_value) else p_value, "sessions": int(len(gru_values))}
    return out


def family_table(sequences, runs: list[dict], limits: dict) -> dict:
    total: dict[str, Tally] = {}
    for probs in runs:
        for family, result in by_family(sequences, probs, limits).items():
            total[family] = total.get(family, Tally()) + result
    return {family or "(aucun jeu)": result.as_dict() for family, result in sorted(total.items())}


def single_session_families(sequences) -> set[str]:
    """Families whose games all come from one session: when it is held out, the model has never seen the game."""
    sessions = defaultdict(set)
    for sequence in sequences:
        for family in sequence.ended_family.values():
            sessions[family].add(sequence.session)
    return {family for family, found in sessions.items() if family and len(found) == 1}


def seen_or_not(table: dict, alone: set[str]) -> dict:
    """Recall on the games also played in other sessions, and on the games of a single session."""
    groups = {"seen_elsewhere": [], "single_session": []}
    for family, row in table.items():
        if family in alone:
            groups["single_session"].append(row)
        elif family != "(aucun jeu)":
            groups["seen_elsewhere"].append(row)
    out = {}
    for name, rows in groups.items():
        ends, found, false = (sum(row[key] for row in rows) for key in ("ends", "found", "false"))
        out[name] = {"ends": ends, "found": found, "false": false, "recall": found / ends if ends else None}
    return out


def billing_table(sequences, runs: list[dict]) -> dict:
    confusion = np.zeros((len(BILLING_MODES), len(BILLING_MODES)), dtype=int)
    for predicted in runs:
        for sequence in sequences:
            np.add.at(confusion, (sequence.billing, predicted[sequence.session].astype(int)), 1)
    recall = {
        mode: float(confusion[index, index] / confusion[index].sum())
        for index, mode in enumerate(BILLING_MODES)
        if confusion[index].sum()
    }
    return {
        "modes": list(BILLING_MODES),
        "confusion": confusion.tolist(),
        "accuracy": float(np.trace(confusion) / confusion.sum()),
        "recall": recall,
    }


def isolation(settings: dict, choices: dict, model: str, setting: str) -> dict:
    """Best validation recall reached with each value of one setting, the others optimised away (Tuning Playbook)."""
    configs = settings["configs"][model]
    table = {}
    for value in sorted({str(config[setting]) for config in configs}):
        best = []
        for outer in held_out(settings):
            recalls = [
                trial["recall"]
                for trial in choices[outer]["trials"][model]
                if str(configs[trial["trial"]][setting]) == value
            ]
            if recalls:
                best.append(max(recalls))
        table[value] = statistics.mean(best) if best else None
    return table


def ablation_table(choices: dict, sessions: list[str]) -> dict:
    table = {}
    for group in next(iter(choices.values()))["ablation"]:
        changes = []
        for outer in sessions:
            gru = choices[outer]["models"]["gru"]
            full = choices[outer]["trials"]["gru"][gru["trial"]]["recall"]
            changes.append(choices[outer]["ablation"][group]["recall"] - full)
        dropped = sum(group in choices[outer]["models"]["gru"]["dropped"] for outer in sessions)
        table[group] = {"dropped_in_rounds": dropped, "mean_recall_change": statistics.mean(changes)}
    return table


def trials_table(settings: dict, choices: dict) -> dict:
    """Every trial of every model: its settings, its validation recall over the rounds, how often it was chosen."""
    sessions = held_out(settings)
    table = {}
    for model, configs in settings["configs"].items():
        rows = []
        for trial, config in enumerate(configs):
            records = [row for outer in sessions for row in choices[outer]["trials"][model] if row["trial"] == trial]
            recalls = [row["recall"] for row in records if row["recall"] is not None]
            precisions = [row["average_precision"] for row in records if row["average_precision"] is not None]
            rows.append(
                {
                    "trial": trial,
                    "config": config,
                    "recall_mean": statistics.mean(recalls) if recalls else None,
                    "recall_min": min(recalls, default=None),
                    "recall_max": max(recalls, default=None),
                    "average_precision_mean": statistics.mean(precisions) if precisions else None,
                    "chosen": sum(choices[outer]["models"][model]["trial"] == trial for outer in sessions),
                }
            )
        table[model] = sorted(rows, key=lambda row: -(row["recall_mean"] or 0))
    return table


def chosen_table(settings: dict, choices: dict) -> dict:
    table = {}
    for outer in settings["outers"]:
        table[outer] = {}
        for model in settings["models"]:
            selected = choices[outer]["models"][model]
            table[outer][model] = {
                "trial": selected["trial"],
                "config": settings["configs"][model][selected["trial"]],
                "dropped": selected["dropped"],
                "threshold": selected["thresholds"][FIRST]["threshold"],
            }
    return table


def chosen_gru_records(store: Store, settings: dict, choices: dict) -> list[dict]:
    """Records of the validation jobs of the GRU chosen in each round, with their learning curves."""
    records = []
    for outer in held_out(settings):
        selected = choices[outer]["models"]["gru"]
        stage = "ablation" if selected["dropped"] else "search"
        dropped = "+".join(selected["dropped"]) or "none"
        for path in store.jobs.glob(f"{stage}-gru-*-t{selected['trial']}-d{dropped}-*.json"):
            record = read_json(path)
            if record["outer"] == outer:
                records.append(record)
    return records


def learning(store: Store, settings: dict, choices: dict) -> dict:
    """Best epochs of the chosen GRU in each round, and how many curves show the validation loss going back up."""
    records = chosen_gru_records(store, settings, choices)
    rising = 0
    for record in records:
        losses = [point[2] for point in record["curve"] if point[2] is not None]
        if losses and losses[-1] > 1.1 * min(losses):
            rising += 1
    epochs = [record["best_epoch"] for record in records]
    return {
        "median_best_epoch": statistics.median(epochs) if epochs else None,
        "rising_curves": rising,
        "curves": len(records),
    }


def write(store: Store, corpus: Corpus, settings: dict, choices: dict) -> Path:
    sessions = held_out(settings)
    sequences = corpus.select(sessions)
    models = [*settings["models"], "rules"]
    results, counts, runs = {}, {}, {}
    for model in models:
        runs[model] = predictions(store, corpus, settings, choices, model)
        results[model] = {}
        for budget in BUDGETS:
            counted = per_session(sequences, runs[model], thresholds(settings, choices, model, budget))
            results[model][str(budget)] = summary(sequences, counted) | {"interval_95": bootstrap(counted)}
            if budget == BUDGETS[0]:
                counts[model] = counted
    others = [model for model in models if model != "gru"]
    # The rules have no threshold to tune and ignore the false-end budget: the baseline is the best trained model.
    baseline = max(settings["models"][1:], key=lambda model: results[model][FIRST]["recall"] or 0)
    shown = ("gru", baseline)
    families = {
        model: family_table(sequences, runs[model], thresholds(settings, choices, model, BUDGETS[0]))
        for model in models
    }
    alone = single_session_families(sequences)
    report = {
        "machine": read_json(store.root / "run.json").get("machine", {}),
        "sessions": len(sessions),
        "results": results,
        "best_baseline": baseline,
        "versus": {model: compare(counts["gru"], counts[model]) for model in others},
        "families": families,
        "family_runs": {model: len(runs[model]) for model in models},
        "single_session_families": sorted(alone),
        "seen_or_not": {model: seen_or_not(families[model], alone) for model in models},
        "billing": billing_table(sequences, final_arrays(store, settings, choices, "gru", ":billing")),
        "curve": {model: curve(sequences, runs[model][0]) for model in shown if model != "rules"},
        "isolation": {
            "gru": {setting: isolation(settings, choices, "gru", setting) for setting in ("hidden", "pos_weight")},
            "logistic": {
                setting: isolation(settings, choices, "logistic", setting) for setting in ("class_weight", "window")
            },
            "boosting": {"class_weight": isolation(settings, choices, "boosting", "class_weight")},
        },
        "ablation": ablation_table(choices, sessions),
        "learning": learning(store, settings, choices),
        "trials": trials_table(settings, choices),
        "chosen": chosen_table(settings, choices),
        "compute_seconds": sum(read_json(path)["seconds"] for path in store.jobs.glob("*.json")),
    }
    write_json(store.root / "report.json", report)
    path = store.root / "report.md"
    path.write_text(markdown(report, models), encoding="utf-8")
    return path


def percent(value) -> str:
    return "-" if value is None else f"{100 * value:.1f} %"


def plain(value, digits: int = 2) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def recall_cell(result: dict) -> str:
    interval = result["interval_95"].get("recall")
    if interval is None:
        return percent(result["recall"])
    return f"{percent(result['recall'])} [{percent(interval[0])}; {percent(interval[1])}]"


def markdown(report: dict, models: list[str]) -> str:
    lines = [
        "# Résultats de l'entraînement",
        "",
        f"Sessions tenues à l'écart : {report['sessions']}. Chaque session est évaluée par des modèles qui ne "
        "l'ont jamais vue, au seuil choisi sur la validation de son propre tour. Une fin trouvée une capture en "
        "retard compte comme juste. Les intervalles entre crochets viennent du rééchantillonnage des sessions (95 %).",
        "",
    ]
    for budget in BUDGETS:
        lines += [
            f"## Seuil choisi pour au plus {budget:g} fausse(s) fin(s) pour 100 parties (validation)",
            "",
            "| Modèle | Précision | Rappel | Fausses fins pour 100 parties | Fausses fins par heure |",
            "|---|---:|---:|---:|---:|",
        ]
        for model in models:
            result = report["results"][model][str(budget)]
            lines.append(
                f"| {NAMES[model]} | {percent(result['precision'])} | {recall_cell(result)} "
                f"| {plain(result['false_per_100'], 1)} | {plain(result['false_per_hour'])} |"
            )
        lines.append("")
    gru = report["results"]["gru"][FIRST]
    lines += [
        f"Écart entre graines du GRU : rappel ± {percent(gru['recall_sd'])}, "
        f"précision ± {percent(gru['precision_sd'])}.",
        "",
        "GRU contre chaque autre modèle (Wilcoxon par session, premier seuil) :",
        "",
    ]
    for model, test in report["versus"].items():
        lines.append(
            f"- {NAMES[model]} : p = {plain(test['recall']['p_value'], 3)} pour le rappel, "
            f"p = {plain(test['false_ends']['p_value'], 3)} pour les fausses fins"
        )
    lines += family_lines(report, models)
    billing = report["billing"]
    lines += ["", f"## Mode de facturation (GRU) : exactitude {percent(billing['accuracy'])}", ""]
    lines += [f"- rappel `{mode}` : {percent(value)}" for mode, value in billing["recall"].items()]
    lines += ["", "## Effet des réglages (meilleur rappel de validation pour chaque valeur)", ""]
    for model, tables in report["isolation"].items():
        for setting, table in tables.items():
            values = ", ".join(f"{value} : {percent(recall)}" for value, recall in table.items())
            lines.append(f"- {NAMES[model]}, `{setting}` : {values}")
    lines += trial_lines(report)
    lines += ["", "## Groupes de variables retirés (GRU)", ""]
    for group, result in report["ablation"].items():
        lines.append(
            f"- `{group}` : retiré dans {result['dropped_in_rounds']} tours sur {report['sessions']}, "
            f"rappel de validation sans lui {100 * result['mean_recall_change']:+.1f} points en moyenne"
        )
    learning = report["learning"]
    lines += [
        "",
        f"Courbes d'apprentissage du GRU retenu : meilleure époque médiane {learning['median_best_epoch']}, "
        f"{learning['rising_curves']} courbes sur {learning['curves']} où la perte de validation remonte "
        "de plus de 10 %.",
        "",
        f"Calcul total : {report['compute_seconds'] / 3600:.1f} heures-processus. Machine : "
        f"{machine_line(report.get('machine', {}))}.",
        "",
        "## Figures",
        "",
    ]
    lines += [f"- [`figures/{name}`](figures/{name}) : {description}" for name, description in FIGURES.items()]
    return "\n".join(lines) + "\n"


def family_lines(report: dict, models: list[str]) -> list[str]:
    """Recall and false ends per game family for every model; false ends are averaged over the seeds."""
    runs = report["family_runs"]
    names = sorted({family for model in models for family in report["families"][model]})
    lines = [
        "",
        "## Par famille de jeu (premier seuil)",
        "",
        "Rappel, puis fausses fins par entraînement entre parenthèses (le GRU est la moyenne de ses graines).",
        "",
        "| Famille | Fins | " + " | ".join(NAMES[model] for model in models) + " |",
        "|---|---:|" + "---:|" * len(models),
    ]
    for family in names:
        rows = [report["families"][model].get(family) for model in models]
        ends = next((row["ends"] / runs[model] for model, row in zip(models, rows) if row), 0)
        cells = [
            f"{percent(row['recall'])} ({row['false'] / runs[model]:g})" if row else "-"
            for model, row in zip(models, rows)
        ]
        lines.append(f"| {family} | {ends:g} | " + " | ".join(cells) + " |")
    alone = report["single_session_families"]
    lines += [
        "",
        f"Jeux joués dans une seule session ({', '.join(alone)}) : quand cette session est tenue à l'écart, le modèle "
        "n'a jamais vu le jeu.",
        "",
        "| Modèle | Jeux vus dans d'autres sessions | Jeux d'une seule session |",
        "|---|---:|---:|",
    ]
    for model in models:
        split = report["seen_or_not"][model]
        lines.append(
            f"| {NAMES[model]} | {percent(split['seen_elsewhere']['recall'])} "
            f"| {percent(split['single_session']['recall'])} |"
        )
    return lines


def trial_lines(report: dict) -> list[str]:
    """Every trial, best first: what the training plan asks the thesis to show, not the best trial alone."""
    lines = ["", "## Tous les essais de réglages (rappel de validation sur les 25 tours)", ""]
    for model, rows in report["trials"].items():
        settings = list(rows[0]["config"])
        lines += [
            f"### {NAMES[model]}",
            "",
            "| Essai | " + " | ".join(f"`{name}`" for name in settings) + " | Rappel moyen (min ; max) | "
            "Précision moyenne | Retenu |",
            "|---:|" + "---|" * len(settings) + "---:|---:|---:|",
        ]
        for row in rows:
            values = " | ".join(f"{row['config'][name]:g}" if isinstance(row["config"][name], float)
                                else str(row["config"][name]) for name in settings)  # fmt: skip
            lines.append(
                f"| {row['trial']} | {values} | {percent(row['recall_mean'])} ({percent(row['recall_min'])} ; "
                f"{percent(row['recall_max'])}) | {plain(row['average_precision_mean'], 3)} | {row['chosen']} |"
            )
        lines.append("")
    return lines


def machine_line(machine: dict) -> str:
    if not machine:
        return "non décrite"
    device = f"GPU CUDA {machine['cuda']}" if machine.get("cuda") else "processeur seul"
    return (
        f"{machine.get('platform', '?')}, {machine.get('cpus', '?')} cœurs logiques, {device}, "
        f"PyTorch {machine.get('torch', '?')}"
    )


def load_run(out: Path) -> tuple[dict, dict]:
    """Settings and choices of a run folder, as written by playend.training.run."""
    choices = {}
    for path in (out / "choices").glob("*.json"):
        choice = read_json(path)
        choices[choice["outer"]] = choice
    return read_json(out / "run.json")["settings"], choices


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the report of a training run from its stored results.")
    parser.add_argument("--package", type=Path, default=REPO / "build" / "playend_v1.0")
    parser.add_argument("--out", type=Path, default=REPO / "build" / "training" / "v1")
    args = parser.parse_args()
    settings, choices = load_run(args.out)
    print(write(Store(args.out), data.load(args.package), settings, choices))


if __name__ == "__main__":
    main()
