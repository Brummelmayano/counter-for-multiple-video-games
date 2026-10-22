"""Mortal Kombat 1: the two round-marker sockets left of the timer, the timer, and the two sockets right of it."""

from .layout import Crop, Layout

LAYOUTS = {
    "rounds": Layout(
        (Crop((578, 6, 612, 22), 3), Crop((622, 8, 658, 40), size=(36, 48)), Crop((694, 6, 728, 22), 3)),
        cols=6,
        rows=30,
    )
}
