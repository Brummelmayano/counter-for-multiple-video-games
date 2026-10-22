"""Contact sheets and zoomed crops of capture frames, each labelled with its frame id.

Frames are read straight from the capture dataset: the images of a lot are byte-identical copies, checked by their
hash. Sheets go to build/zoom/, which is rebuilt on demand and never committed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from playend.common.paths import CAPTURES, ZOOM_OUTPUT

BACKGROUND = (40, 40, 40)
LABEL_COLOUR = (255, 0, 255)
LABEL_WIDTH = 48  # room left of each row for the frame id
GAP = 6  # between two crops of the same frame
ROW_GAP = 4  # between two frames


def font(size: int) -> ImageFont.ImageFont:
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def parse_ids(text: str) -> list[int]:
    """'199-230,240' -> [199, 200, ..., 230, 240]"""
    ids = []
    for part in text.split(","):
        first, _, last = part.partition("-")
        ids.extend(range(int(first), int(last or first) + 1))
    return ids


def session_dir(key: str) -> Path:
    """A capture session from its folder name, its id, or a unique start of its id ("fdb795")."""
    key = key.removeprefix("session_")
    hits = [p for p in CAPTURES.glob(f"session_{key}*") if p.is_dir()]
    if len(hits) != 1:
        raise SystemExit(f"{key!r} matches {len(hits)} capture sessions")
    return hits[0]


def load_frames(session_key: str, ids: list[int]) -> tuple[str, dict[int, Path]]:
    """Short session tag used in file names, and the image file of each requested frame."""
    session = session_dir(session_key)
    paths = {int(p.stem.split("_")[-1]): p for p in (session / "images").rglob("frame_*.jpg")}
    missing = [fid for fid in ids if fid not in paths]
    if missing:
        raise SystemExit(f"frames not in {session.name}: {missing[:10]}{'…' if len(missing) > 10 else ''}")
    return session.name.removeprefix("session_")[:6], paths


@dataclass(frozen=True)
class Crop:
    """A region of the 1280x720 frame, drawn enlarged by `scale`, or at exactly `size` when given."""

    box: tuple[int, int, int, int]
    scale: float = 1.0
    size: tuple[int, int] | None = None

    def drawn_size(self) -> tuple[int, int]:
        if self.size:
            return self.size
        x0, y0, x1, y1 = self.box
        return int((x1 - x0) * self.scale), int((y1 - y0) * self.scale)


@dataclass(frozen=True)
class Layout:
    """The crops drawn for every frame, side by side or stacked, and how many frames fit on one sheet."""

    crops: tuple[Crop, ...]
    cols: int = 1
    rows: int = 14
    stacked: bool = False


def crop_sheets(
    name: str,
    session_key: str,
    ids: list[int],
    layout: Layout,
    cols: int | None = None,
    rows: int | None = None,
    suffix: str = "",
) -> list[Path]:
    """Draw the layout's crops for every frame, `cols` x `rows` frames per sheet. Returns the sheet files."""
    tag, paths = load_frames(session_key, ids)
    cols, rows = cols or layout.cols, rows or layout.rows
    sizes = [crop.drawn_size() for crop in layout.crops]
    if layout.stacked:
        body_w, body_h = max(w for w, _ in sizes), sum(h for _, h in sizes) + GAP * (len(sizes) - 1)
    else:
        body_w, body_h = sum(w for w, _ in sizes) + GAP * (len(sizes) - 1), max(h for _, h in sizes)
    cell_w, cell_h = LABEL_WIDTH + body_w + 2 * GAP, body_h + ROW_GAP
    label_font = font(16)
    ZOOM_OUTPUT.mkdir(parents=True, exist_ok=True)

    sheets = []
    for start in range(0, len(ids), cols * rows):
        chunk = ids[start : start + cols * rows]
        sheet = Image.new("RGB", (cols * cell_w, math.ceil(len(chunk) / cols) * cell_h), BACKGROUND)
        draw = ImageDraw.Draw(sheet)
        for n, fid in enumerate(chunk):
            x, y = (n % cols) * cell_w, (n // cols) * cell_h
            frame = Image.open(paths[fid]).convert("RGB")
            draw.text((x + 2, y + body_h // 2 - 8), str(fid), fill=LABEL_COLOUR, font=label_font)
            px, py = x + LABEL_WIDTH, y
            for crop, (w, h) in zip(layout.crops, sizes):
                piece = frame.crop(crop.box).resize((w, h), Image.LANCZOS)
                if layout.stacked:
                    sheet.paste(piece, (px, py))
                    py += h + GAP
                else:
                    sheet.paste(piece, (px, y + (body_h - h) // 2))
                    px += w + GAP
        path = ZOOM_OUTPUT / f"{name}_{tag}_{chunk[0]:05d}{suffix}.png"
        sheet.save(path)
        sheets.append(path)
    return sheets


def contact_sheets(
    name: str, session_key: str, ids: list[int], cols: int, width: int, height: int, quality: int
) -> list[Path]:
    """Whole frames reduced to width x height, `cols` x `cols` per sheet, saved as JPEG."""
    tag, paths = load_frames(session_key, ids)
    label_font = font(20)
    cell_w, cell_h, label_h = width + 4, height + 26, 24
    ZOOM_OUTPUT.mkdir(parents=True, exist_ok=True)

    sheets = []
    for start in range(0, len(ids), cols * cols):
        chunk = ids[start : start + cols * cols]
        sheet = Image.new("RGB", (cols * cell_w, math.ceil(len(chunk) / cols) * cell_h), BACKGROUND)
        draw = ImageDraw.Draw(sheet)
        for n, fid in enumerate(chunk):
            x, y = (n % cols) * cell_w, (n // cols) * cell_h
            draw.text((x + 4, y), f"#{fid}", fill=LABEL_COLOUR, font=label_font)
            frame = Image.open(paths[fid]).convert("RGB").resize((width, height), Image.LANCZOS)
            sheet.paste(frame, (x, y + label_h))
        path = ZOOM_OUTPUT / f"{name}_{tag}_{chunk[0]:05d}.jpg"
        sheet.save(path, quality=quality)
        sheets.append(path)
    return sheets
