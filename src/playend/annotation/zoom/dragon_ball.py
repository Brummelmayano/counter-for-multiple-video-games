"""Dragon Ball Sparking! ZERO: the remaining-HP-bars row of the left fighter (A), then of the right fighter (B), x4.

Official guide (Bandai Namco): "the amount of remaining HP bars is indicated in the left corner". Lit blocks are
the bars left; it is the closest clue to the knockout, hence to the end of the fight.
"""

from .layout import Crop, Layout

LAYOUTS = {"hp": Layout((Crop((88, 44, 188, 74), 4), Crop((1092, 44, 1192, 74), 4)), cols=4, rows=12)}
