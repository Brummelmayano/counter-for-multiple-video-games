"""Run the training protocol on a PlayEnd package, in parallel, on CPU or GPU, resuming where it stopped.

  python -m playend.training.run --package build/playend_v1.0 --out build/training/v1
  python -m playend.training.run --out build/training/quick --quick     # end-to-end check in a few minutes

Running the same command again skips the jobs already done; the settings of a run are fixed in <out>/run.json.
"""

from __future__ import annotations

import argparse
import ctypes
import multiprocessing
import os
import platform
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from playend.common.paths import REPO
from playend.training import data, figures, protocol, report
from playend.training.search import TRIALS, trials
from playend.training.store import Store, read_json, write_json

MODELS = ("gru", "logistic", "boosting")
SEEDS = 5
STAGES = ("search", "ablation", "final", "report")
# Memory one worker needs: 0.45 GB measured on Linux, more on Windows, which commits memory up front (9 workers
# failed on a 7 GB machine), and up to 2 GB more for the CUDA libraries of a GPU process.
WORKER_GB = {"cpu": 1.0, "cuda": 2.5}
MARGIN_GB = 1  # left free for the system
# Each batch of jobs gets a fresh pool: a worker never lives long enough for leftover memory to pile up.
# (max_tasks_per_child would do it, but it can hang the pool before Python 3.14.7: cpython issue 115634.)
JOBS_PER_WORKER = 100

_worker = {}


def resolve_device(requested: str) -> str:
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested.startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit("--device cuda was asked for, but PyTorch sees no CUDA device on this machine")
    return requested


def free_memory_gb() -> float | None:
    """Memory that new processes can take without swapping; None where it cannot be read."""
    try:
        if os.name != "nt":
            meminfo = Path("/proc/meminfo")
            if meminfo.exists():
                available = next(line for line in meminfo.read_text().splitlines() if line.startswith("MemAvailable:"))
                return int(available.split()[1]) / 2**20
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30

        class MemoryStatus(ctypes.Structure):  # MEMORYSTATUSEX of the Windows API
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong)
                for name in ("total", "free", "page_total", "page_free", "virtual", "virtual_free", "extended")
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        return status.free / 2**30
    except (AttributeError, OSError, StopIteration, ValueError):
        return None


def default_workers(device: str) -> int:
    """Cores minus one, at most 4 per GPU, and no more than the free memory can hold."""
    workers = max(1, (os.cpu_count() or 2) - 1)
    kind = "cuda" if device.startswith("cuda") else "cpu"
    if kind == "cuda":
        workers = min(workers, 4 * (torch.cuda.device_count() if device == "cuda" else 1))
    memory = free_memory_gb()
    if memory:
        workers = min(workers, int((memory - MARGIN_GB) // WORKER_GB[kind]))
    return max(1, workers)


def make_settings(args, corpus: data.Corpus) -> dict:
    if args.quick:
        with_ends = [s for s in corpus.sequences.values() if s.end[s.usable].sum() >= 2]
        outers = [s.session for s in sorted(with_ends, key=len)[:3]]
        counts, max_epochs, seeds = dict.fromkeys(MODELS, 2), 10, 2
    else:
        outers, counts, max_epochs, seeds = sorted(corpus.sequences), TRIALS, 300, SEEDS
    if args.deploy:
        outers = [*outers, protocol.ALL]
    return {
        "package": corpus.digest,
        "feature_sha256": corpus.feature_sha256,
        "models": list(MODELS),
        "configs": {model: trials(model, counts[model]) for model in MODELS},
        "outers": outers,
        "seeds": seeds,
        "max_epochs": max_epochs,
    }


def fixed_settings(path: Path, settings: dict) -> dict:
    """The settings of a run never change: a resumed run must use the ones it started with."""
    if path.exists():
        saved = read_json(path)
        if saved["settings"] != settings:
            changed = sorted(key for key in settings if saved["settings"].get(key) != settings[key])
            raise SystemExit(f"{path.parent} was started with other settings ({changed}): use another --out")
        return saved["settings"]
    write_json(
        path,
        {
            "settings": settings,
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "machine": {
                "python": sys.version.split()[0],
                **{name: metadata.version(name) for name in ("torch", "numpy", "scikit-learn", "scipy")},
                "cuda": torch.version.cuda,
                "platform": platform.platform(),
                "cpus": os.cpu_count(),
                "free_memory_gb": round(free_memory_gb() or 0, 1),
            },
        },
    )
    return settings


def setup_worker(package: str, out: str, device: str, threads: int, workers_started=None) -> None:
    # Set before CUDA starts in this process: PyTorch asks for it to make GRUs deterministic on the GPU.
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":16:8")
    torch.set_num_threads(threads)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    threadpool_limits(threads)
    if workers_started is not None and device == "cuda" and torch.cuda.device_count() > 1:
        with workers_started.get_lock():  # each new worker takes the next GPU in turn
            device = f"cuda:{workers_started.value % torch.cuda.device_count()}"
            workers_started.value += 1
    _worker.update(
        corpus=data.load(Path(package)),
        store=Store(Path(out)),
        settings=read_json(Path(out) / "run.json")["settings"],
        device=device,
    )


def run_job(job: protocol.Job) -> None:
    record, arrays, state = protocol.run(job, _worker["corpus"], _worker["settings"], _worker["device"])
    _worker["store"].save(job.id, record, arrays, state)


@dataclass
class Progress:
    name: str
    total: int
    started: float = field(default_factory=time.time)
    finished: int = 0
    failed: list[str] = field(default_factory=list)

    def step(self) -> None:
        self.finished += 1
        if self.finished == self.total or self.finished % max(1, self.total // 50) == 0:
            left = (time.time() - self.started) / self.finished * (self.total - self.finished)
            failures = f", {len(self.failed)} failed" if self.failed else ""
            print(
                f"[{self.name}] {self.finished}/{self.total} done{failures}, about {left / 60:.0f} min left", flush=True
            )


def run_jobs(name: str, jobs: list[protocol.Job], args, store: Store) -> None:
    todo = [job for job in jobs if not store.done(job.id)]
    print(f"[{name}] {len(jobs)} jobs, {len(jobs) - len(todo)} already done, {len(todo)} to run", flush=True)
    if not todo:
        return
    setup = (str(args.package), str(args.out), args.device, args.threads)
    progress = Progress(name, len(todo))
    if args.workers == 1:
        setup_worker(*setup)
        for job in todo:
            run_job(job)
            progress.step()
        return
    workers, fruitless = args.workers, 0
    while todo:
        before = progress.finished
        crashed = run_pool(todo[: workers * JOBS_PER_WORKER], setup, workers, progress)
        todo = [job for job in todo if not store.done(job.id) and job.id not in progress.failed]
        if not crashed:
            fruitless = 0
            continue
        fruitless = fruitless + 1 if progress.finished == before else 0
        if fruitless == 3:
            raise SystemExit(f"[{name}] the worker processes die before finishing any job: see the messages above")
        if workers > 1:
            workers //= 2
            print(
                f"[{name}] a worker process was killed, most often because the machine ran out of memory; "
                f"going on with {workers}",
                flush=True,
            )
        elif todo:
            # Alone in its pool, the first job left is the one that killed the process.
            progress.failed.append(todo.pop(0).id)
            print(f"[{name}] {progress.failed[-1]} kills its process even alone: skipped", flush=True)
    if progress.failed:
        raise SystemExit(f"[{name}] {len(progress.failed)} jobs failed; run the same command again to retry them")


def run_pool(jobs: list[protocol.Job], setup: tuple, workers: int, progress: Progress) -> bool:
    """Run the jobs in a pool of processes; True when a process was killed, which breaks the whole pool."""
    context = multiprocessing.get_context("spawn")  # the only start method that CUDA supports
    workers_started = context.Value("i", 0)
    executor = ProcessPoolExecutor(
        workers, mp_context=context, initializer=setup_worker, initargs=(*setup, workers_started)
    )
    crashed = False
    try:
        futures = {executor.submit(run_job, job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                future.result()
            except BrokenProcessPool:
                crashed = True  # the job is not lost: it goes to the next pool
                continue
            except Exception as error:  # one failed job must not stop the others
                progress.failed.append(job.id)
                print(f"[{progress.name}] {job.id} failed: {error!r}", flush=True)
            progress.step()
    except BrokenProcessPool:  # raised by submit when a process died very early
        crashed = True
    except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        raise SystemExit("stopped: run the same command again to resume") from None
    executor.shutdown()
    return crashed


def choose(corpus: data.Corpus, store: Store, settings: dict, args) -> dict:
    """Best configuration of each model in each round, then the groups of columns the GRU keeps."""
    assessed = {
        outer: {model: protocol.assess_trials(corpus, store, settings, outer, model) for model in settings["models"]}
        for outer in settings["outers"]
    }
    best = {
        outer: {model: max(results, key=protocol.rank) for model, results in by_model.items()}
        for outer, by_model in assessed.items()
    }
    singles = [
        job
        for outer in settings["outers"]
        for job in protocol.ablation_jobs(corpus, outer, best[outer]["gru"]["trial"], [[g] for g in protocol.GROUPS])
    ]
    run_jobs("ablation", singles, args, store)
    alone, dropped = {}, {}
    for outer in settings["outers"]:
        trial = best[outer]["gru"]["trial"]
        alone[outer] = {
            g: protocol.assess(corpus, store, outer, "gru", trial, (g,), "ablation") for g in protocol.GROUPS
        }
        dropped[outer] = protocol.groups_to_drop(best[outer]["gru"], alone[outer])
    together = [
        job
        for outer in settings["outers"]
        if len(dropped[outer]) > 1
        for job in protocol.ablation_jobs(corpus, outer, best[outer]["gru"]["trial"], [list(dropped[outer])])
    ]
    run_jobs("ablation", together, args, store)
    choices = {}
    for outer in settings["outers"]:
        trial = best[outer]["gru"]["trial"]
        # Groups that cost nothing one by one may still matter together: the full model stays a candidate, and on a
        # tie the candidate with fewer columns, listed first, wins.
        candidates = [alone[outer][g] for g in dropped[outer]] + [best[outer]["gru"]]
        if len(dropped[outer]) > 1:
            candidates.insert(0, protocol.assess(corpus, store, outer, "gru", trial, dropped[outer], "ablation"))
        choices[outer] = {
            "outer": outer,
            "models": {**best[outer], "gru": max(candidates, key=protocol.rank)},
            "ablation": {
                g: {key: alone[outer][g][key] for key in ("recall", "average_precision")} for g in protocol.GROUPS
            },
            "trials": {
                model: [{key: a[key] for key in ("trial", "recall", "average_precision")} for a in results]
                for model, results in assessed[outer].items()
            },
        }
        name = outer if outer == protocol.ALL else outer.removeprefix("session_")
        write_json(store.root / "choices" / f"{name}.json", choices[outer])
    return choices


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate the end-of-game detectors on a PlayEnd package.")
    parser.add_argument("--package", type=Path, default=REPO / "build" / "playend_v1.0", help="PlayEnd package folder")
    parser.add_argument("--out", type=Path, default=REPO / "build" / "training" / "v1", help="results folder")
    parser.add_argument(
        "--workers", type=int, help="parallel processes (default: cores - 1, at most 4 per GPU, within free memory)"
    )
    parser.add_argument("--threads", type=int, default=0, help="threads per process (default: cores / workers)")
    parser.add_argument("--device", default="auto", help="auto, cpu, cuda or cuda:N (sklearn models stay on CPU)")
    parser.add_argument("--until", choices=STAGES, default="report", help="stop after this stage")
    parser.add_argument("--deploy", action="store_true", help="also train the models to deploy, on every session")
    parser.add_argument("--quick", action="store_true", help="3 rounds, 2 configurations, 10 epochs: a check")
    args = parser.parse_args()
    args.device = resolve_device(args.device)
    args.workers = args.workers or default_workers(args.device)
    args.threads = args.threads or max(1, (os.cpu_count() or 1) // args.workers)
    # Before any worker starts: as soon as numpy is imported, OpenBLAS reserves memory for every thread it may use.
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = str(args.threads)
    np.seterr(all="ignore")
    corpus = data.load(args.package)
    store = Store(args.out)
    store.remove_leftovers()
    (store.root / "choices").mkdir(exist_ok=True)
    settings = fixed_settings(store.root / "run.json", make_settings(args, corpus))
    memory = f", {free_memory_gb():.1f} GB of free memory" if free_memory_gb() else ""
    print(
        f"device {args.device}{memory}, {args.workers} workers x {args.threads} threads, results in {args.out}",
        flush=True,
    )
    run_jobs("search", protocol.search_jobs(corpus, settings), args, store)
    if args.until == "search":
        return
    choices = choose(corpus, store, settings, args)
    if args.until == "ablation":
        return
    finals = [job for outer, choice in choices.items() for job in protocol.final_jobs(choice, outer, settings["seeds"])]
    run_jobs("final", finals, args, store)
    if args.until == "final":
        return
    try:
        print(f"report: {report.write(store, corpus, settings, choices)}", flush=True)
        print(f"figures: {figures.write(store, corpus, settings, choices)}", flush=True)
    except Exception:  # every trained result is already saved; only its summary failed
        traceback.print_exc()
        raise SystemExit(
            "the report or the figures failed; the results are saved and can be summarised again with "
            "python -m playend.training.report and python -m playend.training.figures"
        ) from None


if __name__ == "__main__":
    main()
