"""Screens outside any game: console home screens, system menus and black frames."""

from .base import PRESETS

PRESETS["black"] = {
    "game": {"title": None, "type": "unknown", "mode": None, "mode_duration": "unknown", "confidence": 0.3},
    "state": {"phase": "unknown", "screen_type": "unknown", "confidence": 0.4},
    "clock": {"visible": False},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.5,
    "secondary_timers": [],
}


PRESETS["ps5_menu"] = {
    "game": {"title": None, "type": "unknown", "mode": None, "mode_duration": "unknown", "confidence": 0.3},
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
}


PRESETS["ps5_home"] = {
    "game": {"title": None, "type": "unknown", "mode": None, "mode_duration": "unknown", "confidence": 0.3},
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.95},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
}


def ps5(i, obs):
    return {
        "id": i,
        "p": "ps5_home",
        "s": None,
        "obs": obs + " Heure système PS5 exclue du chrono; aucune donnée de partie.",
    }
