"""Run the comparison of the start detectors in the background, resuming where it stopped.

  python -m playend.training.starts.run --out build/training/starts_2026-10-15
  python -m playend.training.starts.run --out build/training/starts_quick --quick   # end-to-end check

Each piece of work (a method on one outer fold of one source) writes its result to <out>/results/ when done; running
the same command again skips what is there. The report is rewritten after each stage, so a run stopped half-way still
leaves the results of the stages it finished.
"""

from __future__ import annotations

import argparse
import json
import pickle
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from threadpoolctl import threadpool_limits

from playend.common.games import game_family
from playend.common.paths import REPO
from playend.counting.portraits import SessionPortraits
from playend.training.starts import protocol, report
from playend.training.starts.sources import Prepared, load_source
from playend.training.starts.trace import trace

SOURCES = {
    "teacher": REPO / "build" / "playend_v1.1",
    "student": REPO / "build" / "student" / "packages" / "student_v1.1_final",
}
BOOSTING = ("gb_raw", "gb_state", "gb_state_dilated", "gb_end_support", "gb_rules", "gb_transition")
FOLDS = (1, 2, 3, 4, 5)


def log(out: Path, message: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}"
    print(line, flush=True)
    with (out / "run.log").open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def prepare(out: Path, source: str) -> Path:
    path = out / "prepared" / f"{source}.pkl"
    if path.exists():
        return path
    sessions = load_source(SOURCES[source])
    families = sorted({game_family(obs["game"]["title"]) for s in sessions.values() for obs in s.observations})
    state, rule_starts, names = {}, {}, None
    for name, session in sessions.items():
        state[name], names, rule_starts[name] = trace(session, families, SessionPortraits(name))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        pickle.dump(Prepared(sessions, state, names, rule_starts), stream)
    return path


_CACHE: dict = {}


def prepared(path: Path) -> Prepared:
    if path not in _CACHE:
        with path.open("rb") as stream:
            _CACHE[path] = pickle.load(stream)
    return _CACHE[path]


def work(task: dict) -> str:
    """One piece of work, run in a worker process; its result file is written only when it is complete."""
    target = Path(task["target"])
    with threadpool_limits(1):
        data = prepared(Path(task["prepared"]))
        if task["kind"] == "boosting" and task["method"] == "gb_transition":
            result = protocol.transition_outer(data, task["outer"], task["quick"])
        elif task["kind"] == "boosting":
            result = protocol.boosting_outer(data, task["method"], task["outer"], task["quick"])
        elif task["kind"] == "gru":
            result = protocol.gru_outer(data, task["outer"], task["quick"])
        elif task["kind"] == "hybrid":
            model = json.loads(Path(task["model"]).read_text(encoding="utf-8"))
            result = protocol.hybrid_outer(data, model, task["outer"])
        elif task["kind"] == "rules":
            grid = protocol.rules_grid(data, task["quick"])
            result = {"fixed": protocol.rules_fixed(data), **protocol.rules_tuned(data, grid)}
        else:
            raise ValueError(task["kind"])
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(result), encoding="utf-8")
    temporary.replace(target)
    return target.name


def stage(out: Path, name: str, tasks: list[dict], workers: int) -> None:
    todo = [task for task in tasks if not Path(task["target"]).exists()]
    log(out, f"stage {name}: {len(tasks) - len(todo)} done before, {len(todo)} to run on {workers} workers")
    if not todo:
        return
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, task): task for task in todo}
        for future in as_completed(futures):
            task = futures[future]
            try:
                log(out, f"  done {future.result()}")
            except Exception:  # a failed piece is logged and left for the next run; the others go on
                log(out, f"  FAILED {Path(task['target']).name}\n{traceback.format_exc()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--quick", action="store_true", help="2 configurations, 2 outer folds, a few GRU epochs")
    parser.add_argument("--sources", nargs="+", default=list(SOURCES), choices=list(SOURCES))
    args = parser.parse_args()
    out = args.out
    (out / "results").mkdir(parents=True, exist_ok=True)
    folds = FOLDS[:2] if args.quick else FOLDS
    log(out, f"start: sources {args.sources}, folds {folds}, quick {args.quick}")
    paths = {}
    for source in args.sources:
        paths[source] = prepare(out, source)
        log(out, f"prepared {source}")

    def target(source, method, outer=None):
        suffix = "" if outer is None else f"-o{outer}"
        return str(out / "results" / f"{source}-{method}{suffix}.json")

    def task(kind, source, method, outer=None, **extra):
        return {"kind": kind, "source": source, "method": method, "outer": outer, "quick": args.quick,
                "prepared": str(paths[source]), "target": target(source, method, outer), **extra}  # fmt: skip

    stage(out, "rules", [task("rules", source, "rules") for source in args.sources], args.workers)
    report.write(out, args.sources, folds)
    stage(out, "boosting", [task("boosting", source, method, outer) for source in args.sources for method in BOOSTING
                            for outer in folds], args.workers)  # fmt: skip
    hybrid = [task("hybrid", source, "hybrid", outer, model=target(source, "gb_state_dilated", outer))
              for source in args.sources for outer in folds
              if Path(target(source, "gb_state_dilated", outer)).exists()]  # fmt: skip
    stage(out, "hybrid", hybrid, args.workers)
    report.write(out, args.sources, folds)
    stage(out, "gru", [task("gru", source, "gru", outer) for source in args.sources for outer in folds], args.workers)
    report.write(out, args.sources, folds)
    log(out, "finished")


if __name__ == "__main__":
    main()
