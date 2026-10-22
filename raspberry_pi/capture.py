#!/usr/bin/env python3
"""Collecteur de gameplay. Aucun OCR/VLM/GRU. Python 3.11 + OpenCV système."""
import argparse
import csv
import datetime as dt
import fcntl
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import math
import multiprocessing as mp
import os
from pathlib import Path
import random
import secrets
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parent
LOG = logging.getLogger("capture_dataset")
FIELDS = ["frame_id", "filename", "received_monotonic_ns", "elapsed_s",
          "delta_t_s", "requested_interval_s", "scheduled_monotonic_ns",
          "lateness_s", "received_wall_utc", "timestamp_source", "encode_ms",
          "write_ms", "width", "height", "size_bytes", "sha256", "device"]


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_bytes(path, data):
    path = Path(path)
    tmp = path.with_name(path.name + ".partial")
    with tmp.open("xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    sync_directory(path.parent)


def atomic_json(path, data):
    path = Path(path)
    # Un nom temporaire unique permet aussi une mise à jour après une coupure.
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    with tmp.open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    sync_directory(path.parent)


def load_config(path):
    cfg = json.loads(Path(path).read_text())
    for key in ("interval_min_s", "interval_max_s", "reserve_free_gib",
                "request_timeout_s", "retry_s"):
        value = cfg[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"Valeur invalide : {key}")
    if cfg["interval_min_s"] > cfg["interval_max_s"]:
        raise ValueError("interval_min_s > interval_max_s")
    for key in ("width", "height", "jpeg_quality"):
        if type(cfg[key]) is not int or cfg[key] <= 0:
            raise ValueError(f"Valeur invalide : {key}")
    if cfg["jpeg_quality"] > 100 or cfg["width"] > 7680 or cfg["height"] > 4320:
        raise ValueError("Qualité JPEG ou résolution hors limites")
    if not isinstance(cfg["device"], str) or not (cfg["device"] == "auto" or cfg["device"].startswith("/dev/")):
        raise ValueError("device doit être auto ou un chemin /dev/")
    directory = Path(cfg["dataset_directory"])
    if directory.is_absolute() or ".." in directory.parts or not directory.parts:
        raise ValueError("dataset_directory doit être un sous-répertoire du projet")
    return cfg


def choose_device(configured):
    if configured != "auto":
        if not Path(configured).exists():
            raise RuntimeError("Périphérique configuré absent")
        return configured
    # Ignorer les codecs et caméras internes : cette collecte concerne une carte USB.
    devices = []
    aliases = sorted(Path("/dev/v4l/by-id").glob("*")) if Path("/dev/v4l/by-id").exists() else []
    for node in sorted(Path("/sys/class/video4linux").glob("video*")):
        if "usb" not in str((node / "device").resolve()).lower():
            continue
        path = Path("/dev") / node.name
        check = subprocess.run(["/usr/bin/v4l2-ctl", "--device", str(path), "--list-formats"],
                               capture_output=True, text=True, timeout=5)
        if check.returncode != 0 or "Video Capture" not in check.stdout:
            continue
        # Les nœuds de métadonnées n'ont pas de format vidéo exploitable.
        if "[0]" not in check.stdout:
            continue
        devices.append(str(next((p for p in aliases if p.resolve() == path.resolve()), path)))
    if len(devices) != 1:
        raise RuntimeError(f"Attente d'une unique source USB vidéo ; {len(devices)} trouvée(s). "
                           "Si plusieurs cartes sont branchées, préciser device dans config.json.")
    return devices[0]


def video_worker(conn, cfg):
    """Draine la vidéo ; ne décode/enregistre une image que sur demande du parent."""
    import cv2
    cv2.setNumThreads(1)
    cap = None
    device = None
    pending = False
    try:
        while True:
            if cap is None and not pending:
                command = conn.recv()
                if command != "capture":
                    return
                pending = True
            elif conn.poll():
                command = conn.recv()
                if command != "capture":
                    return
                pending = True
            try:
                if cap is None:
                    device = choose_device(cfg["device"])
                    cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
                    if not cap.isOpened():
                        raise RuntimeError("Ouverture vidéo impossible")
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg["width"])
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg["height"])
                    # Purger les premières images ; aucune classification de leur contenu.
                    warm_until = time.monotonic() + 0.5
                    while time.monotonic() < warm_until:
                        if not cap.grab():
                            raise RuntimeError("Échec pendant l'ouverture du flux")
                if not cap.grab():
                    raise RuntimeError("Lecture du flux interrompue")
                received_ns = time.monotonic_ns()
                received_utc = utc_now()
                if not pending:
                    continue
                ok, frame = cap.retrieve()
                if not ok or frame is None or frame.size == 0:
                    raise RuntimeError("Image reçue inexploitable")
                started = time.monotonic_ns()
                ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, cfg["jpeg_quality"]])
                if not ok:
                    raise RuntimeError("Compression JPEG échouée")
                conn.send({"ok": True, "jpeg": jpg.tobytes(), "received_monotonic_ns": received_ns,
                           "received_wall_utc": received_utc, "width": int(frame.shape[1]),
                           "height": int(frame.shape[0]), "device": device,
                           "encode_ms": (time.monotonic_ns() - started) / 1e6,
                           "reported_fps": cap.get(cv2.CAP_PROP_FPS),
                           "reported_buffers": cap.get(cv2.CAP_PROP_BUFFERSIZE)})
                pending = False
            except Exception as exc:
                if cap is not None:
                    cap.release()
                    cap = None
                if pending:
                    conn.send({"ok": False, "error": str(exc)})
                    pending = False
    except (EOFError, BrokenPipeError):
        pass
    finally:
        if cap is not None:
            cap.release()
        conn.close()


class VideoClient:
    def __init__(self, cfg):
        self.cfg = cfg
        self.process = None
        self.conn = None

    def close(self):
        if self.process is not None:
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(2)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(2)
            self.process.close()
            self.process = None
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def capture(self, stop):
        if self.process is None or not self.process.is_alive():
            self.close()
            ctx = mp.get_context("spawn")
            self.conn, child = ctx.Pipe()
            self.process = ctx.Process(target=video_worker, args=(child, self.cfg), daemon=True)
            self.process.start()
            child.close()
        try:
            self.conn.send("capture")
            deadline = time.monotonic() + self.cfg["request_timeout_s"]
            while not stop.is_set() and time.monotonic() < deadline:
                if self.conn.poll(0.2):
                    return self.conn.recv()
                if not self.process.is_alive():
                    raise RuntimeError("Processus vidéo arrêté")
            raise RuntimeError("Arrêt demandé" if stop.is_set() else "Délai de réponse vidéo dépassé")
        except (OSError, EOFError, RuntimeError) as exc:
            self.close()
            return {"ok": False, "error": str(exc)}


class Store:
    def __init__(self, dataset, cfg, seed):
        self.cfg = cfg
        self.reserve = int(cfg["reserve_free_gib"] * 1024 ** 3)
        self.start_ns = time.monotonic_ns()
        self.path = Path(dataset) / ("session_" + uuid.uuid4().hex)
        self.path.mkdir(parents=True, exist_ok=False)
        sync_directory(self.path.parent)
        self.csv_file = (self.path / "captures.csv").open("x", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.csv_file, fieldnames=FIELDS)
        self.writer.writeheader()
        self.flush_csv()
        self.count = 0
        self.last_ns = None
        boot = Path("/proc/sys/kernel/random/boot_id")
        try:
            synced = subprocess.run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
                                    capture_output=True, text=True, timeout=2).stdout.strip() == "yes"
        except (OSError, subprocess.TimeoutExpired):
            synced = None
        atomic_json(self.path / "metadata.json", {"schema_version": 1, "session_id": self.path.name,
                    "started_wall_utc": utc_now(), "started_monotonic_ns": self.start_ns,
                    "boot_id": boot.read_text().strip() if boot.exists() else None,
                    "ntp_synchronized_at_start": synced, "random_seed": seed,
                    "profile": "uniform_10_45_configurable_simulation_not_measured_VLM",
                    "timestamp_source": "software_after_v4l2_grab_not_console_timestamp",
                    "config": cfg, "program_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
        self.event_logger = logging.getLogger(self.path.name)
        self.event_logger.setLevel(logging.INFO)
        self.event_logger.propagate = False
        self.handler = RotatingFileHandler(self.path / "events.jsonl", maxBytes=2*1024*1024,
                                          backupCount=2, encoding="utf-8")
        self.event_logger.addHandler(self.handler)
        self.status("waiting_video")

    def flush_csv(self):
        self.csv_file.flush()
        os.fsync(self.csv_file.fileno())

    def space_ok(self, additional=0):
        return shutil.disk_usage(self.path).free >= self.reserve + additional + 1024*1024

    def event(self, name, **extra):
        self.event_logger.info(json.dumps({"event": name, "wall_utc": utc_now(),
                                          "monotonic_ns": time.monotonic_ns(), **extra}, ensure_ascii=False))

    def status(self, state, **extra):
        atomic_json(self.path / "status.json", {"state": state, "saved_images": self.count,
                    "updated_wall_utc": utc_now(), **extra})

    def save(self, frame, interval, scheduled):
        jpg = frame["jpeg"]
        if not self.space_ok(len(jpg)):
            return False
        received = frame["received_monotonic_ns"]
        if self.last_ns is not None and received <= self.last_ns:
            raise RuntimeError("Horodatage non croissant : image refusée")
        number = self.count + 1
        folder = self.path / "images" / f"bloc_{(number - 1)//1000:04d}"
        if not folder.exists():
            folder.mkdir(parents=True)
            sync_directory(self.path)
            sync_directory(folder.parent)
        file = folder / f"frame_{number:08d}.jpg"
        started = time.monotonic_ns()
        atomic_bytes(file, jpg)
        row = {"frame_id": number, "filename": str(file.relative_to(self.path)),
               "received_monotonic_ns": received, "elapsed_s": (received-self.start_ns)/1e9,
               "delta_t_s": "" if self.last_ns is None else (received-self.last_ns)/1e9,
               "requested_interval_s": interval, "scheduled_monotonic_ns": scheduled,
               "lateness_s": max(0, (received-scheduled)/1e9),
               "received_wall_utc": frame["received_wall_utc"],
               "timestamp_source": "software_after_v4l2_grab", "encode_ms": frame["encode_ms"],
               "write_ms": (time.monotonic_ns()-started)/1e6,
               "width": frame["width"], "height": frame["height"],
               "size_bytes": len(jpg), "sha256": hashlib.sha256(jpg).hexdigest(), "device": frame["device"]}
        self.writer.writerow(row)
        self.flush_csv()
        self.count = number
        self.last_ns = received
        self.status("recording", last_file=row["filename"], actual_delta_s=row["delta_t_s"])
        LOG.info("Image %s ; intervalle réel=%s s", number, row["delta_t_s"])
        return True

    def close(self):
        self.csv_file.close()
        self.event_logger.removeHandler(self.handler)
        self.handler.close()


def collect(cfg, store, client, stop, rng, max_images=None, now_ns=time.monotonic_ns):
    interval = 0.0
    scheduled = now_ns()
    previous_error = None
    store.event("session_started")
    while not stop.is_set():
        if not store.space_ok():
            store.event("storage_full")
            store.status("storage_full")
            return
        if stop.wait(max(0, (scheduled-now_ns())/1e9)):
            break
        frame = client.capture(stop)
        if stop.is_set():
            break
        if not frame["ok"]:
            if previous_error != frame["error"]:
                store.event("video_unavailable", error=frame["error"])
                LOG.warning("Vidéo indisponible : %s", frame["error"])
            previous_error = frame["error"]
            store.status("waiting_video", error=frame["error"])
            if stop.wait(cfg["retry_s"]):
                break
            # Conserver l'échéance initiale pour mesurer toute l'interruption.
            continue
        if previous_error is not None:
            store.event("video_recovered")
            previous_error = None
        if not store.save(frame, interval, scheduled):
            store.event("storage_full")
            store.status("storage_full")
            return
        if max_images is not None and store.count >= max_images:
            break
        interval = rng.uniform(cfg["interval_min_s"], cfg["interval_max_s"])
        scheduled = frame["received_monotonic_ns"] + round(interval*1e9)
        store.status("waiting_next_capture", next_interval_s=interval, next_due_monotonic_ns=scheduled)
    store.event("session_stopped")
    store.status("stopped")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--check", action="store_true", help="Vérifier configuration et dépendances sans ouvrir la vidéo")
    parser.add_argument("--max-images", type=int, help="Limiter un essai manuel")
    args = parser.parse_args()
    cfg = load_config(args.config)
    if args.max_images is not None and args.max_images < 1:
        parser.error("--max-images doit être positif")
    if args.check:
        import cv2
        if not shutil.which("v4l2-ctl"):
            raise RuntimeError("v4l2-ctl absent")
        print(json.dumps({"configuration": "ok", "opencv": cv2.__version__, "v4l2_ctl": shutil.which("v4l2-ctl")}))
        return 0
    lock = (ROOT / ".capture.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Un collecteur fonctionne déjà.", file=sys.stderr)
        return 0
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    seed = secrets.randbits(64)
    store = Store(ROOT / cfg["dataset_directory"], cfg, seed)
    for previous in store.path.parent.glob("session_*/status.json"):
        if previous.parent == store.path:
            continue
        try:
            state = json.loads(previous.read_text())["state"]
            if state not in ("stopped", "storage_full", "error"):
                store.event("previous_session_unclosed", session=previous.parent.name,
                            instruction="Exécuter verify_dataset.py avant exploitation ; aucun fichier supprimé")
        except (OSError, ValueError, KeyError):
            store.event("previous_session_status_unreadable", session=previous.parent.name)
    client = VideoClient(cfg)
    LOG.info("Session : %s", store.path)
    try:
        collect(cfg, store, client, stop, random.Random(seed), args.max_images)
    except Exception as exc:
        LOG.exception("Collecte interrompue")
        try:
            store.event("fatal_error", error=str(exc))
            store.status("error", error=str(exc))
        except OSError:
            pass
        return 1
    finally:
        client.close()
        store.close()
        lock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
