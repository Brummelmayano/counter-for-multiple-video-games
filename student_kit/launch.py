"""Install and run the student's computations on this machine, then pack the results to bring back.

  python launch.py install   environment (PyTorch for this graphics card), llama.cpp, the models to download
  python launch.py check     every step in small, to see that everything works (about 15 minutes)
  python launch.py gru       end detectors retrained on the student's observations (the protocol of 2026-10-06)
  python launch.py lora      LoRA adapter for the VLM, merged and converted for llama.cpp
  python launch.py vlm       the VLM on the test frames, with and without LoRA, with and without the grammar
  python launch.py all       lora, vlm, gru (each goes on if another stops), then pack
  python launch.py pack      pack the results, finished or not

An interrupted step is resumed by running it again.
"""

from __future__ import annotations

# Standard library only: this file runs before anything is installed.
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent
VENV = KIT / ".venv"
SETTINGS = json.loads((KIT / "kit.json").read_text(encoding="utf-8"))
RESULTS = KIT / "results"
MODELS = KIT / "models"
STUDENT_PACKAGE = KIT / "data" / "playend_student"
EXAMPLES = KIT / "data" / "lora"
TORCH_INDEX = "https://download.pytorch.org/whl/"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def call(*command, log: Path | None = None) -> int:
    """Run a command, showing its messages and keeping them in `log`."""
    command = [str(part) for part in command]
    print("\n$", " ".join(command), flush=True)
    environment = {**os.environ, "PYTHONUTF8": "1"}
    if log is None:
        return subprocess.run(command, cwd=KIT, env=environment).returncode
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(command)}\n")
        process = subprocess.Popen(command, cwd=KIT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace")  # fmt: skip
        for line in process.stdout:
            print(line, end="", flush=True)
            handle.write(line)
        code = process.wait()
        handle.write(f"=== exit code {code}\n")
    return code


def output_of(*command) -> str:
    try:
        result = subprocess.run([str(part) for part in command], capture_output=True, text=True, errors="replace")
    except OSError:
        return ""
    return result.stdout + result.stderr


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, target: Path, expected: str | None = None) -> None:
    """Download with resume, then check the SHA-256 published with the file."""
    if target.exists() and (expected is None or sha256(target) == expected):
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    done = partial.stat().st_size if partial.exists() else 0
    request = urllib.request.Request(url, headers={"Range": f"bytes={done}-"} if done else {})
    print(f"download {target.name}", flush=True)
    with urllib.request.urlopen(request, timeout=60) as response, partial.open("ab" if done else "wb") as handle:
        if done and response.status != 206:
            handle.truncate(0)
            done = 0
        total = done + int(response.headers.get("Content-Length", 0))
        shown = 0
        while block := response.read(1 << 20):
            handle.write(block)
            done += len(block)
            if total and done * 20 // total > shown:
                shown = done * 20 // total
                print(f"  {done / 1e6:.0f} / {total / 1e6:.0f} MB", flush=True)
    if expected and sha256(partial) != expected:
        partial.unlink()
        raise SystemExit(f"{target.name}: damaged download (wrong SHA-256); run the same command again")
    partial.replace(target)


def system() -> str:
    if os.name == "nt":
        return "windows"
    if platform.system() == "Linux":
        return "linux"
    raise SystemExit(f"This kit runs on Windows or Linux, not {platform.system()}")


def graphics_cards() -> list[str]:
    if os.name == "nt":
        names = output_of("powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_VideoController).Name")
        return [name.strip() for name in names.splitlines() if name.strip()]
    lines = output_of("lspci").splitlines() if shutil.which("lspci") else []
    return [line.split(": ", 1)[-1] for line in lines if re.search(r"VGA|3D controller|Display", line)]


def binary(name: str) -> Path | None:
    suffix = ".exe" if os.name == "nt" else ""
    return next(iter(sorted((KIT / "llama.cpp" / "bin").rglob(name + suffix))), None)


def device() -> str:
    found = KIT / ".device"
    return found.read_text(encoding="utf-8").strip() if found.exists() else "cpu"


def install_torch() -> None:
    """PyTorch for the graphics card: Intel (XPU), NVIDIA (CUDA), or the processor."""
    pip = [venv_python(), "-m", "pip"]
    cards = " ".join(graphics_cards()).lower()
    print(f"\nGraphics cards: {cards or 'none found'}", flush=True)
    builds = (["xpu"] if "intel" in cards and "arc" in cards else []) + (
        ["cu128", "cu126"] if "nvidia" in cards else []
    )
    for build in [*builds, "cpu"]:
        if call(*pip, "install", "--upgrade", "torch", "--index-url", TORCH_INDEX + build) != 0:
            continue
        test = (
            "import sys, torch\n"
            "xpu = hasattr(torch, 'xpu') and torch.xpu.is_available()\n"
            "kind = 'xpu' if xpu else 'cuda' if torch.cuda.is_available() else 'cpu'\n"
            "print(torch.__version__, kind)\n"
            "sys.exit(0 if kind != 'cpu' else 4)\n"
        )
        result = subprocess.run([str(venv_python()), "-c", test], capture_output=True, text=True)
        print(result.stdout.strip(), result.stderr.strip()[-300:], flush=True)
        if build == "cpu" or result.returncode == 0:
            (KIT / ".device").write_text(result.stdout.split()[-1] if result.stdout else "cpu", encoding="utf-8")
            return
    raise SystemExit("PyTorch could not be installed: see the messages above")


def install() -> None:
    if sys.version_info < (3, 10):  # noqa: UP036 - this file runs with whatever Python the machine has
        raise SystemExit(f"Python 3.10 or newer is needed, this is {platform.python_version()}")
    if platform.machine().lower() not in ("amd64", "x86_64"):
        raise SystemExit(f"This kit is for 64-bit Intel or AMD processors, not {platform.machine()}")
    if not venv_python().exists() and call(sys.executable, "-m", "venv", VENV):
        raise SystemExit("Could not create the environment")
    call(venv_python(), "-m", "pip", "install", "--upgrade", "pip")
    install_torch()
    if call(venv_python(), "-m", "pip", "install", "-e", KIT):
        raise SystemExit("The installation failed: see the messages above")
    info = SETTINGS["llama_cpp"]
    name, expected = info["builds"][system()]["vulkan"]
    archive = KIT / "downloads" / name
    download(info["url"].format(name), archive, expected)
    if not binary("llama-mtmd-cli"):
        (KIT / "llama.cpp" / "bin").mkdir(parents=True, exist_ok=True)
        if name.endswith(".zip"):
            zipfile.ZipFile(archive).extractall(KIT / "llama.cpp" / "bin")
        else:
            import tarfile

            with tarfile.open(archive) as bundle:
                bundle.extractall(KIT / "llama.cpp" / "bin")
    source = KIT / "downloads" / f"llama.cpp-{info['release']}-source.zip"
    download(info["source"], source)
    if not (KIT / "llama.cpp" / "source").exists():
        zipfile.ZipFile(source).extractall(KIT / "llama.cpp" / "source")
    gguf_py = next((KIT / "llama.cpp" / "source").rglob("gguf-py"))
    if call(venv_python(), "-m", "pip", "install", gguf_py, "sentencepiece", "protobuf"):
        raise SystemExit("The conversion tools of llama.cpp could not be installed")
    for file, expected in SETTINGS["gguf"]["files"].items():
        url = f"https://huggingface.co/{SETTINGS['gguf']['repo']}/resolve/{SETTINGS['gguf']['revision']}/{file}"
        download(url, MODELS / "official" / file, expected)
    hub = SETTINGS["model"]
    code = call(venv_python(), "-c", "from huggingface_hub import snapshot_download; "
                f"print(snapshot_download('{hub['repo']}', revision='{hub['revision']}', "
                f"local_dir=r'{MODELS / 'hf_base'}'))")  # fmt: skip
    if code:
        raise SystemExit("The model could not be downloaded from Hugging Face: run the same command again")
    RESULTS.mkdir(exist_ok=True)
    call(venv_python(), "-c", "from huggingface_hub import model_info; import pathlib; "
         f"pathlib.Path(r'{RESULTS / 'model_revision.txt'}').write_text(model_info('{hub['repo']}').sha)")  # fmt: skip
    print(output_of(binary("llama-mtmd-cli"), "--list-devices"))
    print(f"\nInstallation done (PyTorch on {device()}). Next: python launch.py check")


def convert(model_dir: Path, name: str) -> Path:
    """The language model of `model_dir` as GGUF Q4_0, by the same scripts for the base and the adapted model."""
    f16, q4 = MODELS / f"{name}-F16.gguf", MODELS / f"{name}-Q4_0.gguf"
    script = next((KIT / "llama.cpp" / "source").rglob("convert_hf_to_gguf.py"))
    log = RESULTS / "lora" / "convert.log"
    partial = q4.with_name(q4.stem + ".part.gguf")  # renamed once whole: a cut never leaves a half file under q4
    if not q4.exists():
        if call(venv_python(), script, model_dir, "--outfile", f16, "--outtype", "f16", log=log):
            raise SystemExit(f"Conversion of {name} failed: see {log}")
        if call(binary("llama-quantize"), f16, partial, "Q4_0", log=log):
            raise SystemExit(f"Quantization of {name} failed: see {log}")
        partial.replace(q4)
        f16.unlink()
    return q4


def adapt(name: str, options: list, module: list) -> None:
    """Train one adapter into results/<name>, merge it into the model, convert it to models/<name>-Q4_0.gguf."""
    adapter, merged = RESULTS / name, MODELS / f"hf_{name}"
    train = [*module, "train", "--examples", EXAMPLES, "--model", MODELS / "hf_base", "--out", adapter, *options]
    if not (adapter / "adapter").exists() and call(*train, log=adapter / "train.log"):
        raise SystemExit(f"LoRA training failed: see {adapter / 'train.log'}")
    merge = [*module, "merge", "--model", MODELS / "hf_base", "--adapter", adapter / "adapter", "--out", merged]
    if not (merged / "config.json").exists() and call(*merge, log=adapter / "merge.log"):
        raise SystemExit(f"Merging failed: see {adapter / 'merge.log'}")
    convert(merged, name)


def lora(limit: int | None = None, epochs: int = 2) -> None:
    """The adapter measured on the test frames, then, in the full run, the one trained on every frame for the Pi."""
    module = [venv_python(), "-m", "playend.student.lora"]
    convert(MODELS / "hf_base", "base")
    if limit:
        adapt("lora_check", ["--limit", limit, "--epochs", 1], module)
        return
    adapt("lora", ["--epochs", epochs], module)
    adapt("lora_final", ["--epochs", epochs, "--split", "all"], module)


VARIANTS = {  # name -> (model file, grammar)
    "official_free": ("official", False),
    "official_grammar": ("official", True),
    "base_grammar": ("base", True),
    "lora_free": ("lora", False),
    "lora_grammar": ("lora", True),
}


def vlm(limit: int | None = None) -> None:
    official = MODELS / "official"
    mmproj = next(official.glob("mmproj*.gguf"))
    for name, (model, use_grammar) in VARIANTS.items():
        tag = "_check" if limit else ""
        if model == "official":
            weights = next(path for path in official.glob("*.gguf") if not path.name.startswith("mmproj"))
        else:
            weights = MODELS / f"{model}{tag if model == 'lora' else ''}-Q4_0.gguf"
        out = RESULTS / f"vlm{tag}" / name
        options = ["--grammar"] if use_grammar else []
        if limit:
            options += ["--limit", limit]
        layers = "99" if "Vulkan" in output_of(binary("llama-mtmd-cli"), "--list-devices") else "0"
        module = [venv_python(), "-m", "playend.student.vlm_eval"]
        run = [*module, "run", "--examples", EXAMPLES, "--out", out, "--llama", binary("llama-mtmd-cli"), "--model",
               weights, "--mmproj", mmproj, "--layers", layers, *options]  # fmt: skip
        call(*run, log=RESULTS / f"vlm{tag}" / "run.log")
        call(*module, "score", out, log=RESULTS / f"vlm{tag}" / "score.log")


def gru(quick: bool = False) -> None:
    out = RESULTS / ("gru_check" if quick else "gru")
    options = ["--quick"] if quick else ["--deploy"]
    if call(venv_python(), "-m", "playend.training.run", "--package", STUDENT_PACKAGE, "--out", out, "--device", "cpu",
            *options, log=out / "log.txt"):  # fmt: skip
        raise SystemExit(f"The detector training stopped: run the same command again (messages in {out / 'log.txt'})")


def describe_machine() -> str:
    lines = [f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"system: {platform.platform()}",
             f"processor: {platform.processor() or platform.machine()}, {os.cpu_count()} logical cores",
             f"graphics cards: {', '.join(graphics_cards())}", f"torch device: {device()}"]  # fmt: skip
    if binary("llama-mtmd-cli"):
        lines.append(output_of(binary("llama-mtmd-cli"), "--list-devices"))
    lines.append(output_of(venv_python(), "-m", "pip", "freeze"))
    return "\n".join(lines)


def pack() -> Path:
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "machine.txt").write_text(describe_machine(), encoding="utf-8")
    archive = KIT / f"playend_eleve_resultats_{time.strftime('%Y%m%d-%H%M')}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(KIT / "kit.json", "results/kit.json")
        for path in sorted(RESULTS.rglob("*")):
            if path.is_file() and not path.name.endswith(".gbnf"):
                bundle.write(path, (Path("results") / path.relative_to(RESULTS)).as_posix())
    print(f"\nFile to bring back: {archive} ({archive.stat().st_size / 1e6:.0f} MB)")
    lora_model = MODELS / "lora_final-Q4_0.gguf"
    if lora_model.exists():
        print(f"Also bring back, on the USB key: {lora_model} ({lora_model.stat().st_size / 1e6:.0f} MB)")
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=["install", "check", "gru", "lora", "vlm", "all", "pack"])
    args = parser.parse_args()
    if args.step != "install" and not venv_python().exists():
        raise SystemExit("Run python launch.py install first")
    if args.step == "install":
        install()
    elif args.step == "check":
        gru(quick=True)
        lora(limit=16)
        vlm(limit=3)
        print("\nCheck passed. Next: python launch.py all")
    elif args.step == "gru":
        gru()
    elif args.step == "lora":
        lora()
    elif args.step == "vlm":
        vlm()
    elif args.step == "all":
        # each part goes on even if another stops, so one failure never costs the others' hours
        failed = []
        for name, step in (("lora", lora), ("vlm", vlm), ("gru", gru)):
            try:
                step()
            except SystemExit as error:
                print(f"\n{name} stopped: {error}", flush=True)
                failed.append(name)
        if failed:
            print(f"\nStopped: {', '.join(failed)}. Run python launch.py all again: finished parts are not redone.")
    if args.step in ("all", "pack"):
        pack()


if __name__ == "__main__":
    main()
