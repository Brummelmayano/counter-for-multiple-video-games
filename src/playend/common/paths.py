"""Where the data lives in the repository.

Every module asks this file for a location instead of computing it from its own position. When the data moves,
only this file changes.

Many stored records (lot manifests, correction manifests, observation manifests, validation items) contain paths
written as text, relative to the repository root. Those records are never rewritten, so `resolve` is the one place
that turns a stored path into a file on disk, including paths written before the data moved to data/.
"""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

DATA = REPO / "data"
CAPTURES = DATA / "captures"
LOTS = DATA / "annotations" / "lots"
CORRECTIONS = DATA / "annotations" / "corrections"
BOUNDARIES = DATA / "boundaries"
VALIDATION = DATA / "validation"
# Private inputs of the PlayEnd export, such as the real player names to replace; never published.
DATASET = DATA / "dataset"

# The counting rules decided by the user, in the form the counter reads.
COUNTING_RULES = REPO / "docs" / "decisions" / "regles_facturation.json"

# Contact sheets and zoomed strips made while reading frames: rebuilt on demand, never committed.
ZOOM_OUTPUT = REPO / "build" / "zoom"

# The student that reads the screen on the Raspberry Pi: downloaded model files (listed with their sources and
# hashes in docs/student/), and everything it writes. Never committed.
STUDENT_OUTPUT = REPO / "build" / "student"
STUDENT_MODELS = STUDENT_OUTPUT / "models"

# Folder names used by records written before 2026-10-04, when the data moved to data/.
OLD_PREFIXES = {
    "Capture-dataset-jeux/dataset/": "data/captures/",
    "dossier_partie_VLM/codex_luna_eval/runs/": "data/annotations/lots/",
    "dossier_partie_VLM/codex_luna_eval/corrections/": "data/annotations/corrections/",
}


def translate(stored: str) -> str:
    """Return the current repository-relative form of a stored path."""
    for old, new in OLD_PREFIXES.items():
        if stored.startswith(old):
            return new + stored[len(old) :]
    return stored


def resolve(stored: str, root: Path = REPO) -> Path:
    """Return the file a stored repository-relative path points to."""
    path = root / translate(stored)
    if path.is_symlink() and not path.exists():
        # Two early lots of session 078643 hold their images as symlinks to an absolute path of the capture folder
        # on the computer that made them. Lots are never modified, so follow them to the current capture folder.
        target = os.readlink(path)
        marker = "/Capture-dataset-jeux/dataset/"
        if marker in target:
            return root / translate(marker[1:] + target.split(marker, 1)[1])
    return path


def relative(path: Path) -> str:
    """Return the repository-relative text form used in new records."""
    return path.resolve().relative_to(REPO).as_posix()
