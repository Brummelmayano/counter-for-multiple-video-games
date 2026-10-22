"""Build the zip that runs the training on another machine: package, code, tests, and the launcher and guide of
training_kit/. The package goes through the export checks first, so the zip carries nothing private.

usage: python -m playend.training.kit [--package build/playend_v1.0] [--out build/playend_training.zip]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import zipfile
from pathlib import Path

from playend.common.files import sha256
from playend.common.paths import REPO
from playend.dataset.checks import check_package
from playend.dataset.pseudonyms import NAMES, read_names
from playend.dataset.tables import exported_sessions, load_session

FOLDER = "playend_training"
SHARED = ["src/playend/__init__.py", "src/playend/common/__init__.py", "src/playend/common/files.py"]
SHARED += ["src/playend/common/paths.py", "src/playend/dataset/__init__.py", "src/playend/dataset/csvfiles.py"]
SHARED += ["tests/__init__.py", "tests/test_training.py"]


def contents(package: Path) -> dict[str, Path]:
    """Path inside the kit -> file in the repository."""
    files = {name: REPO / "training_kit" / name for name in ("launch.py", "README.md", "pyproject.toml")}
    files |= {name: REPO / name for name in SHARED}
    for path in sorted((REPO / "src" / "playend" / "training").glob("*.py")):
        if path.name != "kit.py":  # needs the repository's private data, useless on the other machine
            files[f"src/playend/training/{path.name}"] = path
    files["docs/PLAN_ENTRAINEMENT_GRU.md"] = REPO / "docs" / "decisions" / "PLAN_ENTRAINEMENT_GRU.md"
    for path in sorted(package.rglob("*")):
        if path.is_file():
            files[f"data/{package.name}/{path.relative_to(package).as_posix()}"] = path
    return files


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the zip that runs the training on another machine.")
    parser.add_argument("--package", type=Path, default=REPO / "build" / "playend_v1.0", help="PlayEnd package folder")
    parser.add_argument("--out", type=Path, default=REPO / "build" / "playend_training.zip", help="zip to write")
    args = parser.parse_args()
    if args.package.name != "playend_v1.0":
        raise SystemExit("the launcher expects data/playend_v1.0: build the kit from that package")
    print(f"checking {args.package} ...", flush=True)
    problems = check_package(args.package, read_names(NAMES), [load_session(s) for s in exported_sessions()])
    if problems:
        raise SystemExit("the package has problems, no kit built:\n" + "\n".join(problems))
    files = contents(args.package)
    shipped = [str(path.relative_to(REPO)) for name, path in files.items() if not name.startswith("data/")]
    changed = git("status", "--porcelain", "--", *shipped).splitlines()
    kit = {
        "built": time.strftime("%Y-%m-%d %H:%M:%S"),
        "commit": git("rev-parse", "HEAD"),
        "uncommitted_changes": changed,
        "package": args.package.name,
        "package_sha256": {name: sha256(path) for name, path in files.items() if name.startswith("data/")},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, path in files.items():
            bundle.write(path, f"{FOLDER}/{name}")
        bundle.writestr(f"{FOLDER}/kit.json", json.dumps(kit, indent=1) + "\n")
    if changed:
        print("warning: files with uncommitted changes went into the kit:\n" + "\n".join(changed))
    print(f"{args.out}: {len(files) + 1} files, {args.out.stat().st_size / 1e6:.1f} MB, commit {kit['commit'][:8]}")


if __name__ == "__main__":
    main()
