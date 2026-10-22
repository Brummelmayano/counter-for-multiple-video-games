"""Install and run the PlayEnd training on this machine, then pack the results to send back.

  python launch.py install    environment, PyTorch for this machine's graphics card, libraries, tests
  python launch.py check      the whole protocol in small, to see that everything works
  python launch.py train      the whole protocol, then playend_results_<date>.zip to send back
  python launch.py pack       pack the results again, finished or not

An interrupted command is resumed by running it again. Options after check or train go to the training command.
"""

from __future__ import annotations

# Standard library only: this file runs before anything is installed.
import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent
VENV = KIT / ".venv"
PACKAGE = KIT / "data" / "playend_v1.0"
RESULTS = KIT / "results"
DEVICE = KIT / ".device"  # written by install when the GPU is there but does not work with PyTorch
TORCH_INDEX = "https://download.pytorch.org/whl/"
# PyTorch builds for NVIDIA cards, newest first, with the CUDA version the driver must accept to run them.
CUDA_BUILDS = [((13, 2), "cu132"), ((13, 0), "cu130"), ((12, 8), "cu128"), ((12, 6), "cu126"), ((11, 8), "cu118")]
# Where the NVIDIA drivers put nvidia-smi on Windows, in case it is not on the PATH.
NVIDIA_SMI = [
    Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32" / "nvidia-smi.exe",
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe",
]

GPU_TEST = """
import sys
import torch
print("PyTorch", torch.__version__)
if not torch.cuda.is_available():
    print("No usable GPU: the training will run on the processor, much more slowly")
    sys.exit()
try:
    for index in range(torch.cuda.device_count()):
        print("GPU", index, torch.cuda.get_device_name(index))
    gru = torch.nn.GRU(8, 16, batch_first=True).cuda()
    gru(torch.zeros(2, 50, 8, device="cuda"))[0].sum().backward()
except Exception as error:
    print("The GPU does not work with this PyTorch:", error)
    sys.exit(3)
print("GPU test passed: the training will use the GPU")
"""
GPU_BROKEN = 3


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def call(*command) -> int:
    print("\n$", " ".join(str(part) for part in command), flush=True)
    return subprocess.run([str(part) for part in command], cwd=KIT).returncode


def output_of(*command) -> str:
    try:
        return subprocess.run([str(part) for part in command], capture_output=True, text=True).stdout
    except OSError:
        return ""


def nvidia_smi() -> str | None:
    return shutil.which("nvidia-smi") or next((str(path) for path in NVIDIA_SMI if path.exists()), None)


def graphics_cards() -> list[str]:
    """Names of the graphics cards the system sees, whatever their maker."""
    if os.name == "nt":
        names = output_of("powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_VideoController).Name")
        return [name.strip() for name in names.splitlines() if name.strip()]
    lines = output_of("lspci").splitlines() if shutil.which("lspci") else []
    return [line.split(": ", 1)[-1] for line in lines if re.search(r"VGA|3D controller|Display", line)]


def driver_cuda() -> tuple[int, int] | None:
    """Newest CUDA version the NVIDIA driver accepts, as printed by nvidia-smi; None when it does not answer."""
    smi = nvidia_smi()
    found = re.search(r"CUDA Version:\s*(\d+)\.(\d+)", output_of(smi)) if smi else None
    return (int(found[1]), int(found[2])) if found else None


def installed_torch() -> str | None:
    """The CUDA version of the PyTorch in the environment, "cpu" for a build without CUDA, None without PyTorch."""
    return output_of(venv_python(), "-c", "import torch; print(torch.version.cuda or 'cpu')").strip() or None


def install() -> None:
    if sys.version_info < (3, 10):  # noqa: UP036 - this file runs with whatever Python the machine has
        raise SystemExit(f"Python 3.10 or newer is needed, this is {platform.python_version()}")
    if not venv_python().exists() and call(sys.executable, "-m", "venv", VENV):
        raise SystemExit("Could not create the environment (on Debian or Ubuntu: sudo apt install python3-venv)")
    pip = [venv_python(), "-m", "pip"]
    call(*pip, "install", "--upgrade", "pip")
    cuda, cards = driver_cuda(), graphics_cards()
    print(f"\nGraphics cards: {', '.join(cards) or 'none found'}", flush=True)
    if cuda:
        print(f"The NVIDIA driver accepts CUDA {cuda[0]}.{cuda[1]}")
    elif any("nvidia" in card.lower() for card in cards):
        print(
            "WARNING: there is an NVIDIA card, but its driver does not answer (nvidia-smi). Install or update the "
            "driver from https://www.nvidia.com/drivers, restart the computer, then run python launch.py install again"
        )
    else:
        print("No NVIDIA card: PyTorch can only use an NVIDIA card here, so the training will run on the processor")
    if cuda and installed_torch() == "cpu":
        # pip would keep the build for processors in place, since "torch" is already installed.
        call(*pip, "uninstall", "--yes", "torch")
    builds = [name for version, name in CUDA_BUILDS if cuda and version <= cuda]
    for build in [*builds, "cpu"]:
        if call(*pip, "install", "torch", "--index-url", TORCH_INDEX + build) == 0:
            break
    else:
        raise SystemExit("PyTorch could not be installed: see the messages above")
    if cuda and build == "cpu":
        print(
            f"\nWARNING: no PyTorch build for this NVIDIA driver and Python {platform.python_version()}: update the "
            "driver or use Python 3.12, then run python launch.py install again"
        )
    if call(*pip, "install", "-e", KIT):
        raise SystemExit("The installation failed: see the messages above")
    gpu = call(venv_python(), "-c", GPU_TEST)
    if gpu == GPU_BROKEN:
        DEVICE.write_text("cpu", encoding="utf-8")
        print("WARNING: the training will run on the processor (check and train remember it)")
    elif gpu:
        raise SystemExit("The installation failed: see the messages above")
    else:
        DEVICE.unlink(missing_ok=True)
    if call(venv_python(), "-m", "unittest", "discover", "-s", "tests", "-t", "."):
        raise SystemExit("The tests failed: send the messages above")
    print("\nInstallation done. Next: python launch.py check")


def describe_machine() -> None:
    lines = [
        f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"system: {platform.platform()}",
        f"processor: {platform.processor() or platform.machine()}, {os.cpu_count()} logical cores",
        f"python: {platform.python_version()}",
    ]
    lines += [f"graphics cards: {', '.join(graphics_cards()) or 'none found'}"]
    if nvidia_smi():
        lines += ["", output_of(nvidia_smi())]
    freeze = subprocess.run([venv_python(), "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    lines += ["", "libraries:", freeze]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "machine.txt").write_text("\n".join(lines), encoding="utf-8")


def run_training(name: str, options: list[str]) -> int:
    """Run the training into results/<name>, showing its messages and keeping them in results/<name>/log.txt."""
    if not venv_python().exists():
        raise SystemExit("Run python launch.py install first")
    if DEVICE.exists() and "--device" not in options:
        options = ["--device", DEVICE.read_text(encoding="utf-8").strip(), *options]
    folder = RESULTS / name
    folder.mkdir(parents=True, exist_ok=True)
    describe_machine()
    command = [venv_python(), "-m", "playend.training.run", "--package", PACKAGE, "--out", folder, *options]
    command = [str(part) for part in command]
    started = time.time()
    with (folder / "log.txt").open("a", encoding="utf-8") as log:
        log.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(command[1:])}\n")
        process = subprocess.Popen(
            command,
            cwd=KIT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        while True:
            try:
                for line in process.stdout:
                    print(line, end="", flush=True)
                    log.write(line)
                    log.flush()
                break
            except KeyboardInterrupt:
                continue  # the training received the Ctrl-C too: keep its last messages while it stops
        code = process.wait()
        log.write(f"=== exit code {code} after {(time.time() - started) / 60:.0f} min\n")
    return code


def pack(suffix: str = "") -> Path:
    archive = KIT / f"playend_results_{time.strftime('%Y%m%d-%H%M')}{suffix}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        if (KIT / "kit.json").exists():
            bundle.write(KIT / "kit.json", "results/kit.json")
        for path in sorted(RESULTS.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                bundle.write(path, (Path("results") / path.relative_to(RESULTS)).as_posix())
    print(f"\nFile to send back: {archive} ({archive.stat().st_size / 1e6:.0f} MB)", flush=True)
    return archive


def check(options: list[str]) -> None:
    if run_training("check", ["--quick", *options]):
        raise SystemExit("\nThe check failed: see the messages above, they are also in results/check/log.txt")
    print("\nCheck passed (its figures mean nothing: 3 sessions, 10 epochs). Next: python launch.py train")


def train(options: list[str]) -> None:
    if run_training("full", ["--deploy", *options]) == 0:
        print("\nTraining finished.")
        pack()
        return
    print("\nThe training stopped before the end. Run python launch.py train again: it resumes where it stopped.")
    print("If it keeps stopping on an error, send the partial results packed here:")
    pack("_unfinished")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install and run the PlayEnd training, then pack the results.",
        epilog="Other options after check or train are passed to the training (for example --workers 2).",
    )
    parser.add_argument("step", choices=["install", "check", "train", "pack"])
    args, options = parser.parse_known_args()
    if options and args.step in ("install", "pack"):
        parser.error(f"{args.step} takes no options")
    if args.step == "install":
        install()
    elif args.step == "check":
        check(options)
    elif args.step == "train":
        train(options)
    else:
        pack()


if __name__ == "__main__":
    main()
