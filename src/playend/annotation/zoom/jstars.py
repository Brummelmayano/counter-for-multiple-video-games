"""J-Stars Victory VS+: the left and right victory gauges, the support-call circle (its number is the recharge),
the controlled fighter's name (bottom left) and the "Temps" timer (bottom right).
"""

from .layout import Crop, Layout

BOXES = [(115, 45, 540, 105), (740, 45, 1165, 105), (90, 585, 175, 665), (280, 630, 560, 665), (900, 620, 1215, 675)]
LAYOUTS = {"hud": Layout(tuple(Crop(box, 0.9) for box in BOXES), rows=18)}
