"""Build the student's kit for a machine with a graphics card: launcher, code, the student's package, LoRA examples.

The folder build/student/playend_student_kit/ is zipped next to it (images stored as they are). Before anything is
written, the package and the examples are searched for the real player names of the private list: none may leave.

usage: python -m playend.student.kit
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

from playend.common.paths import REPO, STUDENT_OUTPUT
from playend.dataset.pseudonyms import name_pattern, read_names

KIT = STUDENT_OUTPUT / "playend_student_kit"
CODE = ["src/playend/__init__.py", "src/playend/common/__init__.py", "src/playend/common/files.py",
        "src/playend/common/paths.py", "src/playend/common/games.py", "src/playend/dataset/__init__.py",
        "src/playend/dataset/csvfiles.py", "src/playend/student/__init__.py", "src/playend/student/lora.py",
        "src/playend/student/vlm.py", "src/playend/student/vlm_eval.py", "src/playend/student/rules.py",
        "src/playend/student/zones.py"]  # fmt: skip
LLAMA_CPP = {
    "release": "b11429",
    "commit": "d81235049384534c167caea52b85a694f6103d14",
    "note": "same commit as the llama.cpp v0.6.0 compiled on the Raspberry Pi",
    "url": "https://github.com/ggml-org/llama.cpp/releases/download/b11429/{}",
    "source": "https://github.com/ggml-org/llama.cpp/archive/refs/tags/b11429.zip",
    "builds": {
        "windows": {"vulkan": ["llama-b11429-bin-win-vulkan-x64.zip",
                               "1bfe78ad9168b79fa02bf67f6af9f5e17a966d824d77238517f7bef12ac73b36"]},
        "linux": {"vulkan": ["llama-b11429-bin-ubuntu-vulkan-x64.tar.gz",
                             "632c4e98feba2b94407a2130e3133e0c3aefb0ea1ab41337e926d8bfafdd0b74"]},
    },
}  # fmt: skip
GGUF = {
    "repo": "LiquidAI/LFM2.5-VL-450M-GGUF",
    "revision": "1abed04b6fe71314d8c446a1371c03d7c332266d",
    "files": {
        "LFM2.5-VL-450M-Q4_0.gguf": "6d2757dd0f0b98aea7dc90477bb5b3a0df1089be85ef92943f8cecb05121ccbf",
        "mmproj-LFM2.5-VL-450m-Q8_0.gguf": "ebfc428baa37efad8bae93864f914b2634a09009f91ad59f974fe1a1565d8561",
    },
}


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True).stdout.strip()


def real_names_in(folders: list[Path]) -> list[str]:
    pattern = name_pattern(read_names())
    found = []
    for folder in folders:
        for path in folder.rglob("*"):
            # features hold only numbers; the text that could carry a name is in the other tables and the examples
            if path.is_file() and path.suffix in (".csv", ".json", ".jsonl") and not path.name.startswith("features"):
                found += [f"{path.name}: {match.group(0)}" for match in pattern.finditer(path.read_text("utf-8"))]
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--package", type=Path, default=STUDENT_OUTPUT / "packages" / "student")
    parser.add_argument("--examples", type=Path, default=STUDENT_OUTPUT / "kit_data" / "lora")
    args = parser.parse_args()
    leaks = real_names_in([args.package, args.examples])
    if leaks:
        raise SystemExit("real player names found, no kit built:\n" + "\n".join(leaks[:20]))
    if KIT.exists():
        shutil.rmtree(KIT)
    for name in ("launch.py", "README.md", "pyproject.toml"):
        (KIT / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / "student_kit" / name, KIT / name)
    for name in CODE:
        (KIT / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / name, KIT / name)
    (KIT / "src/playend/training").mkdir(parents=True)
    for path in sorted((REPO / "src" / "playend" / "training").glob("*.py")):
        if path.name != "kit.py":  # needs the repository's private data
            shutil.copy(path, KIT / "src/playend/training" / path.name)
    shutil.copytree(args.package, KIT / "data" / "playend_student")
    shutil.copytree(args.examples, KIT / "data" / "lora")
    examples = [json.loads(line) for line in (KIT / "data/lora/examples.jsonl").read_text("utf-8").splitlines()]
    kit = {
        "built": time.strftime("%Y-%m-%d %H:%M:%S"),
        "commit": git("rev-parse", "HEAD"),
        "uncommitted_code": git("status", "--porcelain", "--", "src/playend", "student_kit").splitlines(),
        "llama_cpp": LLAMA_CPP,
        "gguf": GGUF,
        # the revision published on 2026-04-08, checked on the Hugging Face API on 2026-10-08 (not gated)
        "model": {"repo": "LiquidAI/LFM2.5-VL-450M", "revision": "fc6221ca597f3315e4f82fc2df606783267b34ba"},
        "examples": {split: sum(e["split"] == split for e in examples) for split in ("train", "test")},
    }
    (KIT / "kit.json").write_text(json.dumps(kit, indent=1), encoding="utf-8")
    archive = KIT.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w") as bundle:
        for path in sorted(KIT.rglob("*")):
            if path.is_file():
                compression = zipfile.ZIP_STORED if path.suffix == ".png" else zipfile.ZIP_DEFLATED
                bundle.write(path, (Path(KIT.name) / path.relative_to(KIT)).as_posix(), compress_type=compression)
    print(f"{archive} ({archive.stat().st_size / 1e6:.0f} MB), examples {kit['examples']}")


if __name__ == "__main__":
    main()
