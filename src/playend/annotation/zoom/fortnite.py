"""Fortnite: the HUD counters, for the four screen layouts met so far.

- "split": two-player split screen, corner of the top view and of the bottom view (players left, timer, minimap);
- "solo": single view, stats column left of the minimap (eliminations, players left, storm timer);
- "multi": layout changing within one session (ff1c72): top view, bottom view with side portraits, single view;
- "og": Fortnite OG split screen (ff1c72), the counter row under each minimap (timer, players left, eliminations).
"""

from .layout import Crop, Layout

LAYOUTS = {
    "split": Layout((Crop((560, 0, 850, 160), 1.3), Crop((1000, 360, 1290, 520), 1.3)), rows=11),
    "solo": Layout((Crop((990, 30, 1110, 150), 1.6),), cols=4, rows=10),
    "multi": Layout(
        (Crop((765, 0, 850, 115), 1.4), Crop((1080, 360, 1165, 475), 1.4), Crop((995, 20, 1105, 145), 1.4)),
        cols=4,
        rows=7,
    ),
    "og": Layout((Crop((805, 145, 960, 175), 2.2), Crop((1125, 505, 1280, 535), 2.2)), cols=3, rows=10, stacked=True),
}
