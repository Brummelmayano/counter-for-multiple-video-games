"""Figures of a run, drawn from report.json and the stored predictions into <run>/figures/ (list in report.FIGURES).

usage: python -m playend.training.figures --package PACKAGE --out RUN_FOLDER
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure  # without pyplot, nothing needs a screen

from playend.common.paths import REPO
from playend.training import data, report
from playend.training.data import Corpus
from playend.training.events import match
from playend.training.protocol import BUDGETS
from playend.training.report import FIRST
from playend.training.store import Store, read_json

COLORS = {"gru": "tab:blue", "logistic": "tab:orange", "boosting": "tab:green", "rules": "tab:gray"}


def save(figure: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150, bbox_inches="tight")


def budget_label(budget: float) -> str:
    return f"au plus {budget:g} fausse(s) fin(s) / 100 parties"


def grouped(count: int, slot: int, slots: int, width: float) -> np.ndarray:
    """Positions of the bars of one series among `slots` series drawn side by side."""
    return np.arange(count) + (slot - (slots - 1) / 2) * width


def error_bars(values: np.ndarray, intervals: list) -> np.ndarray:
    """Distances from each value to the ends of its 95 % interval; 0 where no interval could be drawn."""
    low = np.array([interval[0] if interval else value for value, interval in zip(values, intervals)])
    high = np.array([interval[1] if interval else value for value, interval in zip(values, intervals)])
    return np.clip(np.vstack((values - low, high - values)), 0, None)


def models(summary: dict, path: Path) -> None:
    names = list(summary["results"])
    figure = Figure(layout="constrained", figsize=(12, 4.2))
    recall_axes, false_axes = figure.subplots(1, 2)
    width = 0.8 / len(BUDGETS)
    for slot, budget in enumerate(BUDGETS):
        rows = [summary["results"][name][str(budget)] for name in names]
        positions = grouped(len(names), slot, len(BUDGETS), width)
        for axes, key in ((recall_axes, "recall"), (false_axes, "false_per_100")):
            scale = 100 if key == "recall" else 1
            values = np.array([scale * (row[key] or 0) for row in rows])
            intervals = [[scale * bound for bound in row["interval_95"].get(key, [])] for row in rows]
            axes.bar(
                positions, values, width, yerr=error_bars(values, intervals), capsize=3, label=budget_label(budget)
            )
    for axes, title in ((recall_axes, "Rappel (%)"), (false_axes, "Fausses fins pour 100 parties")):
        axes.set_xticks(np.arange(len(names)), [report.NAMES[name] for name in names], rotation=15)
        axes.set_title(title)
        axes.grid(axis="y", alpha=0.3)
    recall_axes.set_ylim(0, 105)
    recall_axes.legend(fontsize=8, loc="upper left")
    figure.suptitle(f"Sessions tenues à l'écart ({summary['sessions']}), intervalles à 95 % par sessions")
    save(figure, path)


def precision_recall(summary: dict, path: Path) -> None:
    figure = Figure(layout="constrained", figsize=(6, 5))
    axes = figure.subplots()
    for name, points in summary["curve"].items():
        kept = [(p["recall"], p["precision"]) for p in points if p["recall"] is not None and p["precision"] is not None]
        if kept:
            recall, precision = 100 * np.array(kept).T
            axes.plot(recall, precision, color=COLORS[name], marker=".", ms=3, lw=0.7, label=report.NAMES[name])
        chosen = summary["results"][name][FIRST]
        if chosen["recall"] is not None and chosen["precision"] is not None:
            axes.scatter(
                100 * chosen["recall"], 100 * chosen["precision"], color=COLORS[name], edgecolor="black", zorder=3
            )
    axes.set_xlabel("Rappel (%)")
    axes.set_ylabel("Précision (%)")
    axes.set_xlim(0, 100)
    axes.set_ylim(0, 102)
    axes.grid(alpha=0.3)
    axes.legend()
    axes.set_title("Par événements, toutes sessions tenues à l'écart\n(point : seuil choisi pour le premier budget)")
    save(figure, path)


def learning_curves(records: list[dict], path: Path) -> None:
    figure = Figure(layout="constrained", figsize=(12, 4.2))
    train_axes, valid_axes = figure.subplots(1, 2, sharey=True)
    for record in records:
        epochs = [point[0] for point in record["curve"]]
        train_axes.plot(epochs, [point[1] for point in record["curve"]], color="tab:blue", alpha=0.25, lw=0.8)
        valid = [point[2] for point in record["curve"]]
        valid_axes.plot(epochs, valid, color="tab:red", alpha=0.25, lw=0.8)
        best = record["best_epoch"]
        if 0 < best <= len(valid) and valid[best - 1] is not None:
            valid_axes.scatter(best, valid[best - 1], color="black", s=8, zorder=3)
    train_axes.set_title("Perte d'entraînement")
    valid_axes.set_title("Perte de validation (point : meilleure époque)")
    for axes in (train_axes, valid_axes):
        axes.set_xlabel("Époque")
        axes.grid(alpha=0.3)
    figure.suptitle(f"GRU retenu, {len(records)} courbes (tours × plis de validation)")
    save(figure, path)


def trials(settings: dict, choices: dict, path: Path) -> None:
    figure = Figure(layout="constrained", figsize=(7, 4.5))
    axes = figure.subplots()
    rng = np.random.default_rng(0)
    names = settings["models"]
    for position, name in enumerate(names):
        recalls = [100 * t["recall"] for o in report.held_out(settings) for t in choices[o]["trials"][name]]
        axes.boxplot([recalls], positions=[position], widths=0.5, showfliers=False)
        jitter = rng.uniform(-0.15, 0.15, len(recalls))
        axes.scatter(position + jitter, recalls, color=COLORS[name], alpha=0.5, s=10)
    axes.set_xticks(range(len(names)), [report.NAMES[name] for name in names])
    axes.set_ylabel(f"Rappel de validation (%), {budget_label(BUDGETS[0])}")
    axes.set_title("Tous les essais de réglages, dans tous les tours")
    axes.grid(axis="y", alpha=0.3)
    save(figure, path)


def settings_effect(summary: dict, path: Path) -> None:
    panels = [
        (model, setting, table) for model, tables in summary["isolation"].items() for setting, table in tables.items()
    ]
    figure = Figure(layout="constrained", figsize=(3 * len(panels), 3.5))
    for axes, (model, setting, table) in zip(np.atleast_1d(figure.subplots(1, len(panels), sharey=True)), panels):
        values = [100 * (recall or 0) for recall in table.values()]
        axes.bar(range(len(table)), values, color=COLORS[model])
        axes.set_xticks(range(len(table)), list(table))
        axes.set_title(f"{report.NAMES[model]}\n{setting}", fontsize=9)
        axes.grid(axis="y", alpha=0.3)
    figure.supylabel("Meilleur rappel de validation (%)", fontsize=9)
    figure.suptitle("Chaque valeur d'un réglage, les autres réglages optimisés (moyenne des tours)")
    save(figure, path)


def ablation(summary: dict, path: Path) -> None:
    groups = list(summary["ablation"])
    changes = [100 * summary["ablation"][g]["mean_recall_change"] for g in groups]
    figure = Figure(layout="constrained", figsize=(7, 4))
    axes = figure.subplots()
    axes.bar(groups, changes, color=["tab:red" if c < 0 else "tab:green" for c in changes])
    for position, group in enumerate(groups):
        axes.annotate(
            f"retiré : {summary['ablation'][group]['dropped_in_rounds']}/{summary['sessions']}",
            (position, changes[position]),
            ha="center",
            va="bottom" if changes[position] >= 0 else "top",
            fontsize=8,
        )
    axes.axhline(0, color="black", lw=0.8)
    axes.set_ylabel("Écart de rappel de validation sans le groupe (points)")
    axes.set_title("GRU : retrait d'un groupe de variables à la fois")
    axes.grid(axis="y", alpha=0.3)
    save(figure, path)


def families(summary: dict, path: Path) -> None:
    shown = list(summary["families"])
    names = sorted({family for model in shown for family in summary["families"][model]})
    figure = Figure(layout="constrained", figsize=(9, 0.5 * len(names) + 1.5))
    axes = figure.subplots()
    height = 0.8 / len(shown)
    for slot, model in enumerate(shown):
        rows = [summary["families"][model].get(family) for family in names]
        positions = grouped(len(names), slot, len(shown), height)
        recalls = [100 * (row["recall"] or 0) if row else 0 for row in rows]
        axes.barh(positions, recalls, height, color=COLORS[model], label=report.NAMES[model])
        for position, recall, row in zip(positions, recalls, rows):
            if row:
                axes.annotate(
                    f" {row['found']}/{row['ends']}, {row['false']} fausse(s)",
                    (recall, position),
                    va="center",
                    fontsize=7,
                )
    axes.set_yticks(np.arange(len(names)), names)
    axes.invert_yaxis()
    axes.set_xlim(0, 125)
    axes.set_xlabel("Rappel (%) : fins trouvées / fins, toutes graines")
    axes.legend(fontsize=8, loc="lower right")
    axes.set_title(f"Par famille de jeu, {budget_label(BUDGETS[0])}")
    save(figure, path)


def billing(summary: dict, path: Path) -> None:
    confusion = np.array(summary["billing"]["confusion"], dtype=float)
    shares = confusion / np.maximum(confusion.sum(axis=1, keepdims=True), 1)
    modes = summary["billing"]["modes"]
    figure = Figure(layout="constrained", figsize=(5.5, 4.5))
    axes = figure.subplots()
    image = axes.imshow(shares, cmap="Blues", vmin=0, vmax=1)
    for true, predicted in np.ndindex(shares.shape):
        share, count = shares[true, predicted], int(confusion[true, predicted])
        color = "white" if share > 0.5 else "black"
        axes.text(predicted, true, f"{100 * share:.0f} %\n({count})", ha="center", va="center", color=color)
    axes.set_xticks(range(len(modes)), modes)
    axes.set_yticks(range(len(modes)), modes)
    axes.set_xlabel("Prédit")
    axes.set_ylabel("Vrai")
    axes.set_title(f"Mode de facturation (GRU), exactitude {100 * summary['billing']['accuracy']:.1f} %")
    figure.colorbar(image, ax=axes, fraction=0.046)
    save(figure, path)


def spans(mask: np.ndarray) -> list[tuple[int, int]]:
    """(first, last) rows of each run of True."""
    edges = np.diff(np.concatenate(([0], mask.astype(int), [0])))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1) - 1))


def sessions(store: Store, corpus: Corpus, settings: dict, choices: dict, summary: dict, folder: Path) -> None:
    """The GRU probability is the mean of the seeds, compared with the threshold of the session's own round."""
    gru_runs = report.predictions(store, corpus, settings, choices, "gru")
    limits = report.thresholds(settings, choices, "gru", BUDGETS[0])
    baseline = summary["best_baseline"]
    baseline_runs = report.predictions(store, corpus, settings, choices, baseline) if baseline != "rules" else []
    for session in report.held_out(settings):
        sequence = corpus.sequences[session]
        prob = np.mean([run[session] for run in gru_runs], axis=0)
        found, missed, false = match(sequence, prob, limits[session])
        minutes = (sequence.t - sequence.t[0]) / 60
        figure = Figure(layout="constrained", figsize=(13, 3.2))
        axes = figure.subplots()
        for first, last in spans(~sequence.usable):
            axes.axvspan(minutes[first], minutes[last], color="0.85", lw=0)
        for row in np.flatnonzero(sequence.end == 1):
            axes.axvline(minutes[row], color="black", lw=0.6, alpha=0.4)
        if baseline_runs:
            axes.plot(
                minutes,
                baseline_runs[0][session],
                color=COLORS[baseline],
                lw=0.6,
                alpha=0.6,
                label=report.NAMES[baseline],
            )
        axes.plot(minutes, prob, color=COLORS["gru"], lw=0.9, label="GRU (moyenne des graines)")
        axes.axhline(limits[session], color=COLORS["gru"], ls="--", lw=0.8, label="seuil du tour")
        axes.scatter(
            minutes[found], np.full(len(found), 1.05), marker="v", color="tab:green", label="fin trouvée", zorder=3
        )
        axes.scatter(
            minutes[missed], np.full(len(missed), 1.05), marker="v", color="tab:orange", label="fin manquée", zorder=3
        )
        axes.scatter(minutes[false], prob[false], marker="x", color="tab:red", label="fausse fin", zorder=3)
        name = session.removeprefix("session_")[:8]
        games = ", ".join(sorted({family for family in sequence.family if family}))
        axes.set_title(
            f"{name} · {games} · {len(found)}/{len(found) + len(missed)} fins trouvées, "
            f"{len(false)} fausse(s) fin(s) (gris : intervalles masqués)",
            fontsize=9,
        )
        axes.set_xlabel("Minutes depuis le début de la session")
        axes.set_ylabel("Probabilité de fin")
        axes.set_ylim(-0.02, 1.12)
        axes.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.0, 1.0))
        save(figure, folder / f"{name}.png")


def write(store: Store, corpus: Corpus, settings: dict, choices: dict) -> Path:
    summary = read_json(store.root / "report.json")
    folder = store.root / "figures"
    models(summary, folder / "models.png")
    precision_recall(summary, folder / "precision_recall.png")
    learning_curves(report.chosen_gru_records(store, settings, choices), folder / "learning_curves.png")
    trials(settings, choices, folder / "trials.png")
    settings_effect(summary, folder / "settings.png")
    ablation(summary, folder / "ablation.png")
    families(summary, folder / "families.png")
    billing(summary, folder / "billing.png")
    sessions(store, corpus, settings, choices, summary, folder / "sessions")
    return folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw the figures of a training run from its report and results.")
    parser.add_argument("--package", type=Path, default=REPO / "build" / "playend_v1.0")
    parser.add_argument("--out", type=Path, default=REPO / "build" / "training" / "v1")
    args = parser.parse_args()
    settings, choices = report.load_run(args.out)
    print(write(Store(args.out), data.load(args.package), settings, choices))


if __name__ == "__main__":
    main()
