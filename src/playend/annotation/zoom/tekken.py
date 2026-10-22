"""Tekken 8: the "WINS n" corner bottom left, the round markers with the top of the timer (x2), the "WINS n" corner
bottom right.

"WINS n" changes at every end of match: it is the most reliable end clue, more than the round markers (078643).
"""

from .layout import Crop, Layout

LAYOUTS = {
    "rounds": Layout(
        (Crop((30, 596, 290, 666), 0.8), Crop((480, 14, 850, 58), 2.0), Crop((990, 596, 1250, 666), 0.8)),
        cols=2,
        rows=14,
    )
}
