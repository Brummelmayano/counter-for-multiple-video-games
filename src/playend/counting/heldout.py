"""Count the games of the held-out sessions with the frozen student and the start rules, once
(docs/counting/SESSIONS_INEDITES.md).

The student reads each capture as on the Pi (classifier with its vote, banner OCR off gameplay, SteadyScreen, HUD
reading on gameplay, student_view); the start rules count the games; the starts are matched to the reference games
validated by the author (data/evaluation/sessions_inedites/). The run refuses to start if a file of the frozen
system changed or if a reference is not validated. One JSON record per capture is kept, with its reading time, the
temperature and the memory used, so a stopped run resumes; the same command runs on the Raspberry Pi.

usage: python -m playend.counting.heldout [--out build/evaluation/sessions_inedites]
"""

from __future__ import annotations

import argparse
import json
import resource
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

from playend.common.files import sha256
from playend.common.games import game_family
from playend.common.paths import REPO, STUDENT_MODELS, STUDENT_OUTPUT
from playend.counting.portraits import ZONES, thumbnail
from playend.counting.starts import detect, match
from playend.student.apply import Classifier, Marks
from playend.student.collect import frame_paths
from playend.student.features import ImageFeatures
from playend.student.ocr import TextReader
from playend.student.package import SteadyScreen, profiles, student_view
from playend.student.rules import INFINITY_AS_EIGHT
from playend.student.run import read_hud, save, saved, temperature
from playend.student.zones import LAYOUTS

REFERENCE = REPO / "data" / "evaluation" / "sessions_inedites"
CLASSIFIER = STUDENT_OUTPUT / "classifier_v1.1_cine.npz"


def check_frozen() -> None:
    frozen = json.loads((REFERENCE / "frozen.json").read_text(encoding="utf-8"))
    changed = [name for name, digest in frozen["files"].items() if sha256(REPO / name) != digest]
    if changed:
        raise SystemExit(f"the frozen system changed since commit {frozen['commit']}: {changed}")


class CapturePortraits:
    """Portrait thumbnails read from the capture folder, for sessions that have no annotation lot."""

    def __init__(self, paths: dict[int, Path]):
        self.paths, self.cache = paths, {}

    def __call__(self, frame: int, family: str, side: str):
        zone = ZONES.get(family, {}).get(side)
        if zone is None or frame not in self.paths:
            return None
        if (frame, side) not in self.cache:
            with Image.open(self.paths[frame]) as image:
                self.cache[(frame, side)] = thumbnail(image, zone)
        return self.cache[(frame, side)]


def read_session(
    session: str, out: Path, readers: dict, game_profiles: dict, replace: dict[int, dict] | None = None
) -> tuple[dict[int, dict], dict[int, tuple[str, str]]]:
    """The student's observation of every capture, in order, and the game and screen it saw; one record per capture
    under `out`. `replace` gives other HUD values for some captures (another reader), in place of the OCR's."""
    folder = out / session[8:16]
    folder.mkdir(parents=True, exist_ok=True)
    classifier, screens, observations, views = readers["classifier"], SteadyScreen(), {}, {}
    classifier.recent.clear()
    for frame, path in sorted(frame_paths(session).items()):
        target = folder / f"{frame:05d}.json"
        record = saved(target)
        if record is None:
            started = time.perf_counter()
            image = Image.open(path).convert("RGB")
            features = readers["features"](image)
            label = classifier.label("game", features)
            screen_raw, _ = classifier.label("screen", features)
            banner = None
            if screen_raw != "gameplay":
                banner = [[line.text, line.score, *line.box] for line in readers["text"].read(image)]
            record = {"frame_id": frame, "game_label": [label[0], float(label[1])], "screen_raw": screen_raw,
                      "banner": banner, "image": image}  # fmt: skip
        classifier.recent.append(tuple(record["game_label"]))
        game = classifier.vote()
        texts = [line[0] for line in record["banner"]] if record["banner"] is not None else None
        screen = screens.step(record["screen_raw"], texts)
        if "fields" not in record:
            fields, times = {}, {}
            if screen == "gameplay" and game in LAYOUTS:
                fields = read_hud(readers["text"], readers["marks"], record["image"], game, times)
            record["fields"] = fields
            record["hud_seconds"] = sum(times.values())
            record.pop("image")
            record["seconds"] = time.perf_counter() - started
            record["temp_c"] = temperature()
            record["max_rss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            save(record, target)
        fields = record["fields"] if replace is None or frame not in replace else replace[frame]
        views[frame] = (game, screen)
        profile = game_profiles.get((game, fields.get("clock_display") == INFINITY_AS_EIGHT)) or game_profiles.get(
            (game, False), {}
        )
        observations[frame] = student_view(game, screen, fields, texts, profile)
    return observations, views


def score(units: list[dict], starts: list, frames: list[int], families: defaultdict) -> dict:
    """Games of the reference found by the starts, starts in excess, and the tally of each game family."""
    found = match(units, starts, frames)
    used = {id(start) for start in found.values()}
    for unit in units:
        families[game_family(unit["game"])]["games"] += 1
        families[game_family(unit["game"])]["found"] += unit["unit_id"] in found
    extra = [start for start in starts if id(start) not in used]
    for start in extra:
        families[start.family]["extra"] += 1
    return {
        "games": len(units),
        "found": len(found),
        "extra": len(extra),
        "exact": len(starts) == len(units),
        "starts": [[start.frame, start.decided_at, start.family] for start in starts],
        "missed": [unit["unit_id"] for unit in units if unit["unit_id"] not in found],
        "extra_starts": [[start.frame, start.family] for start in extra],
        "matched": {uid: [start.frame, start.decided_at] for uid, start in found.items()},
    }


def summarise(results: dict, families: dict) -> dict:
    games = sum(r["games"] for r in results.values())
    found = sum(r["found"] for r in results.values())
    extra = sum(r["extra"] for r in results.values())
    return {"games": games, "found": found, "extra": extra, "recall": found / games,
            "extra_per_100": 100 * extra / games, "precision": found / (found + extra) if found + extra else 1.0,
            "exact": sum(r["exact"] for r in results.values()),
            "sessions": results, "families": {k: dict(v) for k, v in families.items()}}  # fmt: skip


def references() -> list[dict]:
    """The validated reference of each held-out session."""
    found = []
    for path in sorted(REFERENCE.glob("session_*.json")):
        reference = json.loads(path.read_text(encoding="utf-8"))
        if reference["status"] != "human_verified":
            raise SystemExit(f"{path.name}: the reference is not validated by the author")
        found.append(reference)
    return found


def evaluate(out: Path) -> dict:
    check_frozen()
    readers = {"features": ImageFeatures(STUDENT_MODELS / "mobilenetv2-12.onnx"), "text": TextReader(),
               "classifier": Classifier(CLASSIFIER), "marks": Marks()}  # fmt: skip
    game_profiles = profiles()
    results, families = {}, defaultdict(Counter)
    for reference in references():
        session, units = reference["session_id"], reference["units"]
        observations, _ = read_session(session, out, readers, game_profiles)
        starts = detect(observations, False, True, CapturePortraits(frame_paths(session)))
        results[session] = score(units, starts, sorted(observations), families)
    summary = summarise(results, families)
    seconds = [json.loads(path.read_text(encoding="utf-8")).get("seconds") for path in out.glob("*/*.json")]
    seconds = sorted(value for value in seconds if value is not None)
    if seconds:
        p90 = seconds[int(0.9 * (len(seconds) - 1))]
        summary["seconds_per_capture"] = {"captures": len(seconds), "median": statistics.median(seconds), "p90": p90,
                                          "max": seconds[-1]}  # fmt: skip
    (out / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=REPO / "build" / "evaluation" / "sessions_inedites")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    summary = evaluate(args.out)
    print(f"{summary['found']}/{summary['games']} games found ({100 * summary['recall']:.1f} %), {summary['extra']} "
          f"too many ({summary['extra_per_100']:.1f} per 100), exact count on {summary['exact']} of "
          f"{len(summary['sessions'])} sessions")  # fmt: skip
    for session, result in summary["sessions"].items():
        print(f"  {session[8:16]}: {result['found']}/{result['games']} found, {result['extra']} too many, "
              f"missed {result['missed']}, extra {result['extra_starts']}")  # fmt: skip


if __name__ == "__main__":
    main()
