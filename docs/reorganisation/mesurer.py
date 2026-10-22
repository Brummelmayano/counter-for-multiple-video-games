"""Reference measurements taken before the repository reorganization (phase 0)."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return (p.stdout + p.stderr).strip().splitlines()


out = {"commit": run(["git", "rev-parse", "HEAD"], ROOT)[0], "tag": "avant-reorganisation"}

coverage = run([sys.executable, "-m", "playend.annotation.coverage", "--all"], ROOT)
out["verify_session_coverage"] = [line for line in coverage if line.startswith("session_")]

files = {}
for session in sorted(p for p in (DATA / "boundaries").glob("session_*") if p.is_dir()):
    for name in (
        "units.json",
        "units.csv",
        "labels_proposed.jsonl",
        "labels_human_verified.jsonl",
        "observation_manifest.jsonl",
        "REVIEW.md",
    ):
        f = session / name
        if f.exists():
            files[f"{session.name}/{name}"] = sha(f)
out["boundary_files_sha256"] = files

out["validation_sha256"] = {n: sha(DATA / "validation" / n) for n in ("items.json", "validation_results.jsonl")}
# Located by name, so the measurement still works after the files move.
ASSETS = (
    "06_prompt_VLM_universel_COMPACT_STABLE_v1.txt",
    "observation_v2.schema.json",
    "observation_v2.template.json",
    "gru_feature_spec_v4.json",
)
out["contract_assets_sha256"] = {}
for name in ASSETS:
    found = [
        p
        for p in ROOT.rglob(name)
        if "archive" not in p.parts
        and "runs" not in p.parts
        and p.relative_to(ROOT).parts[0] not in ("data", "build")
        and not any(part.startswith(".") for part in p.relative_to(ROOT).parts)
    ]
    out["contract_assets_sha256"][name] = sha(found[0]) if len(found) == 1 else f"not unique: {found}"

tests = {}
tests["contract"] = run([sys.executable, "-m", "unittest", "discover", "-s", "tests/contract", "-t", "."], ROOT)[-3:]
tests["capture"] = run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], ROOT / "raspberry_pi")[-3:]
out["tests"] = tests

tracked = run(["git", "ls-files"], ROOT)
out["tracked_files"] = len(tracked)
print(json.dumps(out, ensure_ascii=False, indent=1))
