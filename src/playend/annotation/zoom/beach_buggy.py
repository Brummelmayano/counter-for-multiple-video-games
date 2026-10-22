"""Beach Buggy Racing 2 in split screen: the "N/8 PLACE" of every view, then the central "TOUR n" bar.

Layouts: "3" = one view on top and two at the bottom (session fdb795), "4" = four views, "2" = top and bottom.
"""

from .layout import Crop, Layout

LAP_BAR = Crop((500, 335, 780, 392), 1.2)
TOP_CENTRE = Crop((140, 30, 290, 112), 1.2)
TOP_LEFT, TOP_RIGHT = Crop((20, 25, 170, 95), 1.2), Crop((660, 25, 810, 95), 1.2)
BOTTOM_LEFT, BOTTOM_RIGHT = Crop((20, 385, 170, 455), 1.2), Crop((660, 385, 810, 455), 1.2)
BOTTOM_CENTRE = Crop((140, 390, 290, 472), 1.2)

LAYOUTS = {
    "3": Layout((TOP_CENTRE, BOTTOM_LEFT, BOTTOM_RIGHT, LAP_BAR), rows=16),
    "4": Layout((TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT, LAP_BAR), rows=16),
    "2": Layout((TOP_CENTRE, BOTTOM_CENTRE, LAP_BAR), rows=16),
}
