"""Warzone: the top-right counters (squad icon = teams left, person icon = players left, eliminations), then the
circle badge and its timer under the minimap.
"""

from .layout import Crop, Layout

LAYOUTS = {
    "counters": Layout(
        (Crop((1095, 10, 1278, 54), size=(330, 80)), Crop((20, 195, 130, 230), size=(200, 70))), cols=5, rows=12
    )
}
