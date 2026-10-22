"""The lots of a capture session and their source manifests."""

from pathlib import Path

from playend.common.files import read_jsonl
from playend.common.paths import LOTS


def session_lots(session: str) -> list[Path]:
    return sorted(LOTS.glob(f"{session}_frames_*"))


def source_rows(session: str) -> dict[int, dict]:
    """Manifest row of every frame copied into a lot of the session (image paths, hashes, capture times)."""
    return {row["frame_id"]: row for lot in session_lots(session) for row in read_jsonl(lot / "manifest.jsonl")}
