"""The results folder of a run. A job is done once its record is written, after its arrays and model: a job killed
half-way leaves nothing that looks finished and is simply run again."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import torch


def replace_atomically(path: Path, write) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as stream:
        write(stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    if os.name == "posix":  # so that the rename itself survives a power cut; Windows cannot open a folder
        folder = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(folder)
        finally:
            os.close(folder)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    replace_atomically(path, lambda stream: stream.write((json.dumps(data, indent=1) + "\n").encode()))


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.jobs = self.root / "jobs"
        self.models = self.root / "models"
        self.jobs.mkdir(parents=True, exist_ok=True)
        self.models.mkdir(exist_ok=True)

    def remove_leftovers(self) -> None:
        """Temporary files of jobs killed while writing; only safe while no job runs."""
        for path in [*self.jobs.glob(".*.tmp"), *self.models.glob(".*.tmp")]:
            path.unlink()

    def done(self, job_id: str) -> bool:
        return (self.jobs / f"{job_id}.json").exists()

    def save(self, job_id: str, record: dict, arrays: dict, state: dict | None = None) -> None:
        replace_atomically(self.jobs / f"{job_id}.npz", lambda stream: np.savez_compressed(stream, **arrays))
        if state is not None:
            replace_atomically(self.models / f"{job_id}.pt", lambda stream: torch.save(state, stream))
        write_json(self.jobs / f"{job_id}.json", record)

    def record(self, job_id: str) -> dict:
        return read_json(self.jobs / f"{job_id}.json")

    def arrays(self, job_id: str) -> dict:
        with np.load(self.jobs / f"{job_id}.npz") as data:
            return {key: data[key] for key in data.files}

    def model(self, job_id: str) -> dict:
        return torch.load(self.models / f"{job_id}.pt", map_location="cpu")
