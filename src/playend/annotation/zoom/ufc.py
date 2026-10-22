"""UFC 5: the fighter name top left (A), the round badge and clock (top centre), the fighter name top right (B).

The participants are these names, never the trunk colours of the bottom banner.
"""

from .layout import Crop, Layout

LAYOUTS = {
    "names": Layout(
        (Crop((55, 30, 380, 58), 1.3), Crop((560, 28, 720, 98), 1.3), Crop((900, 30, 1225, 58), 1.3)), cols=2, rows=14
    )
}
