"""Shared by every preset module: the preset registry, the secondary-counter helper and run_lot."""

import json

from playend.annotation.build_lot import build_batch
from playend.annotation.record_lot import record
from playend.common.paths import LOTS
from playend.common.provenance import annotator_model

__all__ = ["CUT", "METHOD", "METHOD_TEXT", "PRESETS", "cnt", "run_lot"]

METHOD = "contact_sheet_plus_zoomed_hud_plus_full_frame_when_ambiguous"
METHOD_TEXT = (
    "3x3 or 2x2 contact sheets for scene/screen type + zoomed crop of the score/clock HUD for every frame "
    "+ full-resolution frame for banners, menus, overlays and any ambiguous case"
)

# Partial observations that a frame merges by name ("p" in the reading spec); each genre module adds its own.
PRESETS = {}
CUT = {"state.screen_type": "cutscene", "state.confidence": 0.8}


def cnt(kind, side, value, total=None, label=None):
    """One secondary counter (kind: players_remaining, teams_remaining, lives, target, series, other, unknown;
    side: a, b or field)."""
    return {"kind": kind, "side": side, "value": value, "total": total, "label": label}


def run_lot(lot, first, last, frames, presets=None):
    """Write the reading spec of frames first to last in the lot, then build and record the batch."""
    if presets is None:
        # Module presets all describe an inspected HUD: no counter unless a helper adds one. A preset dict passed by
        # the caller is left as it is, so a missing key stays null (not inventoried).
        for preset in PRESETS.values():
            preset.setdefault("secondary_counters", [])
    spec = {
        "run": lot,
        "annotator": annotator_model(),
        "method": METHOD_TEXT,
        "presets": presets or PRESETS,
        "frames": frames,
    }
    path = LOTS / lot / "decisions" / f"reading_spec_{first:06d}_{last:06d}.json"
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    batch = build_batch(path)
    record(LOTS / lot, batch, METHOD)
