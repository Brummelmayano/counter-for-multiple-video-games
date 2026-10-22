"""The pipelines the Raspberry Pi could run, compared on the held-out sessions: what each counts and how long it takes.

  A  classifier + OCR, then the start rules (playend.counting.heldout)
  B  classifier + OCR, then the gradient boosting or the GRU of playend.training.starts.final, run with NumPy
  C  classifier + VLM adapted by LoRA on every gameplay capture, then the start rules
  D  classifier + OCR, the VLM rereading only the captures where the rules hesitate, then the start rules

On the Pi, after A: `check` reads a few captures with llama-mtmd-cli, as the VLM was measured on 2026-10-10 and 11;
`vlm` reads C's captures through llama-server, which keeps the model loaded, and `check` compares the two answers;
`together` reads captures with the OCR while the VLM works, to see whether both fit in memory; `detectors` times B
capture by capture. On the PC, `compare` scores every pipeline against the validated references, once, and gathers
the times measured on the Pi. A cascade where a light model handles everything and a heavy one only the hard cases
is the idea of Viola and Jones (2001) and of FrugalGPT (Chen, Zaharia and Zou, 2023).

usage: python -m playend.counting.pipelines {check,vlm,together,detectors,compare} [--out DIR] ...
"""

from __future__ import annotations

import argparse
import base64
import copy
import csv
import io
import json
import statistics
import subprocess
import threading
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from playend.common.games import game_family
from playend.common.paths import REPO
from playend.contract.temporal import FeatureStream, feature_spec
from playend.counting import heldout
from playend.counting.starts import Detector, Start, detect
from playend.student.apply import Classifier, Marks
from playend.student.collect import frame_paths
from playend.student.features import ImageFeatures
from playend.student.ocr import TextReader
from playend.student.package import profiles
from playend.student.run import read_hud, save, saved, temperature
from playend.student.vlm import parse, prompt, vlm_mosaic
from playend.student.zones import LAYOUTS
from playend.training.starts.events import peaks
from playend.training.starts.sources import readability
from playend.training.starts.trace import Tracing

OUT = REPO / "build" / "evaluation" / "pipelines"
FINAL = REPO / "build" / "training" / "starts_final"
SERVER = "http://127.0.0.1:8080"
CHECKED = 8  # captures read by both llama-mtmd-cli and llama-server
TOGETHER = 20  # captures read by the OCR while the VLM works


def references() -> list[dict]:
    return heldout.references()


def readers(light: bool = False) -> dict:
    found = {"classifier": Classifier(heldout.CLASSIFIER)}
    if not light:
        found |= {"features": ImageFeatures(), "text": TextReader(), "marks": Marks()}
    return found


def views(session: str, ocr: Path, game_profiles: dict, replace=None):
    """Observations and (game, screen) of every capture, from A's records (the classifier is not run again)."""
    return heldout.read_session(session, ocr, readers(light=True), game_profiles, replace)


def vlm_captures(session: str, ocr: Path, game_profiles: dict) -> list[tuple[int, str]]:
    """The captures C gives the VLM: those the student sees as gameplay of a game with zones, as the OCR reads."""
    _, seen = views(session, ocr, game_profiles)
    return [(frame, game) for frame, (game, screen) in sorted(seen.items()) if screen == "gameplay" and game in LAYOUTS]


def mosaic_png(session: str, frame: int, game: str) -> bytes:
    buffer = io.BytesIO()
    vlm_mosaic(Image.open(frame_paths(session)[frame]).convert("RGB"), game).save(buffer, format="PNG")
    return buffer.getvalue()


def ask_server(png: bytes, game: str) -> str:
    image = "data:image/png;base64," + base64.b64encode(png).decode()
    body = {"messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": image}},
                                                      {"type": "text", "text": prompt(game)}]}],
            "temperature": 0, "max_tokens": 96, "seed": 42}  # fmt: skip
    request = urllib.request.Request(f"{SERVER}/v1/chat/completions", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})  # fmt: skip
    with urllib.request.urlopen(request, timeout=1800) as response:
        return json.loads(response.read())["choices"][0]["message"]["content"]


def rss_mb(pid: int | None) -> float | None:
    if not pid:
        return None
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024
    return None


def memory() -> dict:
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        name, value = line.split(":")
        if name in ("MemAvailable", "SwapTotal", "SwapFree"):
            values[name] = int(value.split()[0]) / 1024
    return values


def run_vlm(out: Path, ocr: Path, server_pid: int | None) -> None:
    game_profiles = profiles()
    for reference in references():
        session = reference["session_id"]
        folder = out / "vlm" / session[8:16]
        folder.mkdir(parents=True, exist_ok=True)
        for frame, game in vlm_captures(session, ocr, game_profiles):
            target = folder / f"{frame:05d}.json"
            if saved(target) is not None:
                continue
            started = time.perf_counter()
            answer = ask_server(mosaic_png(session, frame, game), game)
            record = {"frame_id": frame, "game": game, "answer": answer, "fields": parse(game, answer),
                      "seconds": time.perf_counter() - started, "temp_c": temperature(),
                      "server_rss_mb": rss_mb(server_pid), **memory()}  # fmt: skip
            save(record, target)


def run_check(out: Path, ocr: Path, llama: Path, model: Path, mmproj: Path) -> None:
    """The first captures of C read by llama-mtmd-cli; `vlm` later reads the same ones through the server."""
    game_profiles = profiles()
    folder = out / "check"
    folder.mkdir(parents=True, exist_ok=True)
    reference = references()[0]
    session = reference["session_id"]
    for frame, game in vlm_captures(session, ocr, game_profiles)[:CHECKED]:
        target = folder / f"{session[8:16]}_{frame:05d}.json"
        if saved(target) is not None:
            continue
        image = folder / f"{session[8:16]}_{frame:05d}.png"
        image.write_bytes(mosaic_png(session, frame, game))
        command = [str(llama), "-m", str(model), "--mmproj", str(mmproj), "--image", str(image), "-p", prompt(game),
                   "-n", "96", "-c", "4096", "-t", "4", "--temp", "0", "--seed", "42"]  # fmt: skip
        started = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, timeout=1800)
        record = {"frame_id": frame, "game": game, "answer": result.stdout, "exit_code": result.returncode,
                  "seconds_with_loading": time.perf_counter() - started}  # fmt: skip
        save(record, target)


def run_together(out: Path, ocr: Path, server_pid: int | None) -> None:
    """OCR reading of a few captures while the server answers VLM requests without pause: time and memory."""
    game_profiles = profiles()
    reference = references()[-1]
    session = reference["session_id"]
    targets = vlm_captures(session, ocr, game_profiles)
    busy, samples = threading.Event(), []
    busy.set()

    def keep_vlm_busy():
        frame, game = targets[0]
        png = mosaic_png(session, frame, game)
        while busy.is_set():
            ask_server(png, game)

    worker = threading.Thread(target=keep_vlm_busy, daemon=True)
    worker.start()
    time.sleep(20)  # the first request is under way
    scratch = out / "together" / "ocr"
    reading = readers()
    for frame, game in targets[1 : TOGETHER + 1]:
        started = time.perf_counter()
        image = Image.open(frame_paths(session)[frame]).convert("RGB")
        features = reading["features"](image)
        reading["classifier"].label("game", features)
        reading["classifier"].label("screen", features)
        read_hud(reading["text"], reading["marks"], image, game, {})
        samples.append({"frame_id": frame, "seconds": time.perf_counter() - started, "temp_c": temperature(),
                        "server_rss_mb": rss_mb(server_pid), **memory()})  # fmt: skip
    busy.clear()
    scratch.parent.mkdir(parents=True, exist_ok=True)
    save(samples, out / "together" / "samples.json")


class Boosting:
    """The exported trees of playend.training.starts.final, evaluated with NumPy."""

    def __init__(self, path: Path):
        self.arrays = dict(np.load(path))

    def probability(self, row: np.ndarray) -> float:
        a = self.arrays
        row, raw = row[a["kept"]], float(a["baseline"])
        for root in a["roots"]:
            node = root
            while not a["leaf"][node]:
                value = row[a["feature"][node]]
                left = a["missing_left"][node] if np.isnan(value) else value <= a["threshold"][node]
                node = root + (a["left"][node] if left else a["right"][node])
            raw += a["value"][node]
        return float(1 / (1 + np.exp(-raw)))


class StartGRU:
    """The exported GRU of playend.training.starts.final, one informative capture at a time."""

    def __init__(self, path: Path):
        self.a = dict(np.load(path))
        self.state = np.zeros(self.a["weight_hh"].shape[1], np.float32)
        self.previous_t: float | None = None

    def step(self, row: np.ndarray, t: float) -> float:
        a = self.a
        flags = np.isnan(row[a["missing"]]).astype(np.float32)
        scaled = np.nan_to_num((row - a["mean"]) / a["std"], nan=0.0).astype(np.float32)
        gap = np.log1p(0.0 if self.previous_t is None else t - self.previous_t)
        self.previous_t = t
        x = np.concatenate((scaled, flags, [np.float32(gap)])).astype(np.float32)
        reset_x, update_x, new_x = np.split(a["weight_ih"] @ x + a["bias_ih"], 3)
        reset_h, update_h, new_h = np.split(a["weight_hh"] @ self.state + a["bias_hh"], 3)
        reset, update = 1 / (1 + np.exp(-(reset_x + reset_h))), 1 / (1 + np.exp(-(update_x + update_h)))
        new = np.tanh(new_x + reset * new_h)
        self.state = ((1 - update) * new + update * self.state).astype(np.float32)
        return float(1 / (1 + np.exp(-(a["head_weight"][0] @ self.state + a["head_bias"][0]))))


def capture_times(session: str) -> dict[int, float]:
    """Seconds since the first capture of the session, from the monotonic clock."""
    path = next(iter(frame_paths(session).values())).parents[2] / "captures.csv"
    with path.open(encoding="utf-8") as stream:
        rows = {int(row["frame_id"]): int(row["received_monotonic_ns"]) for row in csv.DictReader(stream)}
    first = min(rows.values())
    return {frame: (value - first) / 1e9 for frame, value in rows.items()}


def run_detectors(out: Path, ocr: Path, final: Path) -> dict:
    """B, capture by capture as on the Pi: features, game state, gradient boosting and GRU; probabilities and times."""
    meta = json.loads((final / "meta.json").read_text(encoding="utf-8"))
    names = meta["state_names"]
    families = [name.split("=", 1)[1] for name in names if name.startswith("family=")]
    without_rules = [i for i, name in enumerate(names) if not name.startswith("rules_")]
    feature_names = feature_spec()["feature_names"]
    boosting = Boosting(final / "gb_rules.npz")
    game_profiles = profiles()
    results = {}
    for reference in references():
        session = reference["session_id"]
        observations, _ = views(session, ocr, game_profiles)
        times = capture_times(session)
        readable, informative = readability([observations[f] for f in sorted(observations)])
        grus = [StartGRU(path) for path in sorted(final.glob("gru_seed*.npz"))]
        stream, tracing = FeatureStream(), Tracing(families, heldout.CapturePortraits(frame_paths(session)))
        rows = []
        for index, frame in enumerate(sorted(observations)):
            started = time.perf_counter()
            features = stream.step({"session_id": session, "frame_id": frame, "observation": observations[frame],
                                    "received_monotonic_ns": int(round(times[frame] * 1e9))})  # fmt: skip
            x = np.array([float(features[name]) for name in feature_names], np.float32)
            features_s = time.perf_counter() - started
            step = time.perf_counter()
            tracing.observe_at(frame, times[frame], observations[frame])
            state = np.array([tracing.rows[-1][name] for name in names], np.float32)
            rules_s = time.perf_counter() - step
            step = time.perf_counter()
            gb = boosting.probability(np.concatenate((state, x)).astype(np.float64)) if readable[index] else 0.0
            gb_s = time.perf_counter() - step
            step = time.perf_counter()
            gru = 0.0
            if informative[index] and grus:  # the GRU files may be missing: then only the boosting is timed
                row = np.concatenate((state[without_rules], x))
                gru = float(np.mean([model.step(row, times[frame]) for model in grus]))
            gru_s = time.perf_counter() - step
            rows.append({"frame_id": frame, "gb": gb, "gru": gru if readable[index] else 0.0, "features_s": features_s,
                         "rules_s": rules_s, "gb_s": gb_s, "gru_s": gru_s})  # fmt: skip
        results[session] = rows
    folder = out / "detectors"
    folder.mkdir(parents=True, exist_ok=True)
    save(results, folder / "probabilities.json")
    return results


def hesitates(detector: Detector, frame: int, observation: dict) -> bool:
    """The OCR reading would make the rules open a game, hold a candidate, or confirm one: the VLM rereads it."""
    portraits, detector.portraits = detector.portraits, None  # the thumbnails it keeps are not copied
    trial = copy.deepcopy(detector)
    detector.portraits = trial.portraits = portraits
    before = (len(trial.starts), trial.candidate is not None)
    trial.observe(frame, observation)
    return len(trial.starts) > before[0] or trial.candidate is not None or before[1]


def cascade(session: str, ocr: Path, vlm: dict[int, dict], game_profiles: dict) -> tuple[list[Start], int]:
    """D: the OCR reads everything, the VLM rereads the captures where the rules hesitate."""
    observations, _ = views(session, ocr, game_profiles)
    replaced, _ = views(session, ocr, game_profiles, replace=vlm)
    detector = Detector(generic=False, confirm=True, portraits=heldout.CapturePortraits(frame_paths(session)))
    asked = 0
    for frame in sorted(observations):
        chosen = observations[frame]
        if frame in vlm and hesitates(detector, frame, observations[frame]):
            chosen, asked = replaced[frame], asked + 1
        detector.observe(frame, chosen)
    return detector.starts, asked


def spread(values: list[float]) -> dict | None:
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    return {"n": len(values), "median": statistics.median(values), "p90": values[int(0.9 * (len(values) - 1))],
            "max": values[-1]}  # fmt: skip


def compare(out: Path, ocr: Path, final: Path) -> dict:
    meta = json.loads((final / "meta.json").read_text(encoding="utf-8"))
    probabilities = json.loads((out / "detectors" / "probabilities.json").read_text(encoding="utf-8"))
    game_profiles = profiles()
    tallies = {name: ({}, defaultdict(Counter)) for name in ("A", "B_gb", "B_gru", "C", "D")}
    asked_total, captures_total, ocr_seconds, hud_seconds = 0, 0, [], []
    for reference in references():
        session, units = reference["session_id"], reference["units"]
        short = session[8:16]
        observations, _ = views(session, ocr, game_profiles)
        frames = sorted(observations)
        portraits = heldout.CapturePortraits(frame_paths(session))
        vlm = {int(p.stem): json.loads(p.read_text(encoding="utf-8"))["fields"]
               for p in (out / "vlm" / short).glob("*.json")}  # fmt: skip
        readable, _ = readability([observations[f] for f in frames])
        runs = {"A": detect(observations, False, True, portraits)}
        for name, key, threshold in (("B_gb", "gb", meta["gb_rules"]["threshold"]),
                                     ("B_gru", "gru", meta["gru"]["threshold"])):  # fmt: skip
            prob = np.array([row[key] for row in probabilities[session]], np.float32)
            runs[name] = [Start(f, d, "", False) for f, d in peaks(prob, readable, threshold)]
        replaced, _ = views(session, ocr, game_profiles, replace=vlm)
        runs["C"] = detect(replaced, False, True, portraits)
        runs["D"], asked = cascade(session, ocr, vlm, game_profiles)
        asked_total += asked
        captures_total += len(frames)
        for name, starts in runs.items():
            results, families = tallies[name]
            for start in starts:
                start.family = start.family or game_family(observations[start.frame]["game"]["title"])
            results[session] = heldout.score(units, starts, frames, families)
        for path in sorted((ocr / short).glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            ocr_seconds.append(record.get("seconds"))
            hud_seconds.append(record.get("hud_seconds"))
    vlm_seconds = [json.loads(p.read_text())["seconds"] for p in (out / "vlm").glob("*/*.json")]
    detector_rows = [row for rows in probabilities.values() for row in rows]
    summary = {name: heldout.summarise(results, families) for name, (results, families) in tallies.items()}
    summary["times"] = {
        "ocr_capture": spread(ocr_seconds), "ocr_hud": spread(hud_seconds), "vlm_capture": spread(vlm_seconds),
        "vlm_reads": {"C": len(vlm_seconds), "D": asked_total, "captures": captures_total},
        **{key: spread([row[key] for row in detector_rows]) for key in ("features_s", "rules_s", "gb_s", "gru_s")},
    }  # fmt: skip
    check = sorted((out / "check").glob("*.json"))
    same = 0
    for path in check:
        cli = json.loads(path.read_text(encoding="utf-8"))
        short, frame = path.stem.split("_")
        served = out / "vlm" / short / f"{frame}.json"
        same += served.exists() and parse(cli["game"], cli["answer"]) == json.loads(served.read_text())["fields"]
    summary["server_like_cli"] = {"checked": len(check), "same_values": same}
    together = out / "together" / "samples.json"
    if together.exists():
        samples = json.loads(together.read_text(encoding="utf-8"))
        summary["together"] = {"ocr_capture": spread([s["seconds"] for s in samples]),
                               "lowest_available_mb": min(s["MemAvailable"] for s in samples),
                               "most_swap_used_mb": max(s["SwapTotal"] - s["SwapFree"] for s in samples)}  # fmt: skip
    (out / "comparison.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=["check", "vlm", "together", "detectors", "compare"])
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--ocr", type=Path, default=REPO / "build" / "evaluation" / "sessions_inedites",
                        help="A's records (playend.counting.heldout)")  # fmt: skip
    parser.add_argument("--final", type=Path, default=FINAL)
    parser.add_argument("--server-pid", type=int)
    parser.add_argument("--llama", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--mmproj", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    heldout.check_frozen()
    if args.step == "check":
        run_check(args.out, args.ocr, args.llama, args.model, args.mmproj)
    elif args.step == "vlm":
        run_vlm(args.out, args.ocr, args.server_pid)
    elif args.step == "together":
        run_together(args.out, args.ocr, args.server_pid)
    elif args.step == "detectors":
        run_detectors(args.out, args.ocr, args.final)
    else:
        summary = compare(args.out, args.ocr, args.final)
        for name in ("A", "B_gb", "B_gru", "C", "D"):
            s = summary[name]
            print(f"{name:6s} {s['found']}/{s['games']} found, {s['extra']} too many "
                  f"({s['extra_per_100']:.1f} per 100), exact {s['exact']}")  # fmt: skip
        print(json.dumps(summary["times"], indent=1))


if __name__ == "__main__":
    main()
