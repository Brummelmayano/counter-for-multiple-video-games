"""Replay the end detectors of the training run on a student package: what reading errors do to the ends found.

GRU: the final models kept for each held-out session (build/training/v1/models, five seeds) read that session from
the student package. Gradient boosting: refitted for each held-out session with the settings the run chose, either on
the teacher's other sessions (as in the run) or on the student package's other sessions. Thresholds are those the
run chose for each budget of false ends per 100 games. Written to build/student/endings/<package>.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playend.common.paths import REPO, STUDENT_OUTPUT
from playend.student.package import PACKAGE
from playend.training import baselines, data, gru
from playend.training.protocol import BUDGETS, final_jobs, kept_columns, training_sessions
from playend.training.report import held_out, load_run, per_session, summary, thresholds
from playend.training.store import Store

RUN = REPO / "build" / "training" / "v1"


def probabilities(
    model: str, teacher, student, settings, choices, store, refit_on_student: bool
) -> tuple[list[dict], list[dict]]:
    """Per seed, for every held-out session: {session: probability of an end on each row}, and for the GRU
    {session: billing mode on each row}."""
    runs: dict[int, dict] = {}
    modes: dict[int, dict] = {}
    for outer in held_out(settings):
        for job in final_jobs(choices[outer], outer, settings["seeds"]):
            if job.model != model:
                continue
            if model == "gru":
                state = store.model(job.id)
                columns = [student.feature_names.index(name) for name in state["columns"]]
                prob, billing = gru.predict(
                    state["weights"], state["config"], columns, [student.sequences[outer]], "cpu"
                )[outer]
                modes.setdefault(job.seed, {})[outer] = billing
            else:
                names = [teacher.feature_names[i] for i in kept_columns(teacher, outer, job.dropped)]
                source = student if refit_on_student else teacher
                fitted = baselines.fit_boosting(
                    source.select(training_sessions(source, outer)),
                    None,
                    [source.feature_names.index(name) for name in names],
                    settings["configs"][model][job.trial],
                    job.seed,
                    job.length,
                )
                columns = [student.feature_names.index(name) for name in names]
                prob = baselines.predict(fitted, [student.sequences[outer]], columns, baselines.BOOSTING_WINDOW)[outer]
            runs.setdefault(job.seed, {})[outer] = prob
    return [runs[seed] for seed in sorted(runs)], [modes[seed] for seed in sorted(modes)]


def replay(package: Path, models: list[str], refit_on_student: bool) -> dict:
    teacher, student = data.load(PACKAGE), data.load(package)
    settings, choices = load_run(RUN)
    store = Store(RUN)
    sequences = student.select(held_out(settings))
    results = {}
    for model in models:
        runs, _ = probabilities(model, teacher, student, settings, choices, store, refit_on_student)
        results[model] = {
            str(budget): summary(sequences, per_session(sequences, runs, thresholds(settings, choices, model, budget)))
            for budget in BUDGETS
        }
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("package", type=Path, help="a student package (playend.student.package) or the teacher's")
    parser.add_argument("--models", nargs="+", default=["gru", "boosting"])
    parser.add_argument("--refit-on-student", action="store_true", help="gradient boosting learns from the package")
    args = parser.parse_args()
    results = replay(args.package, args.models, args.refit_on_student)
    out = STUDENT_OUTPUT / "endings"
    out.mkdir(parents=True, exist_ok=True)
    name = args.package.name + ("_refit" if args.refit_on_student else "")
    (out / f"{name}.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    for model, budgets in results.items():
        for budget, result in budgets.items():
            print(f"{name} {model} budget {budget}: recall {result['recall']:.1%}, false ends per 100 "
                  f"{result['false_per_100']:.1f}, precision {result['precision']:.1%}")  # fmt: skip


if __name__ == "__main__":
    main()
