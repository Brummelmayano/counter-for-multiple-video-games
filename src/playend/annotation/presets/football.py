"""EA Sports FC 26 and 27. Conventions: docs/conventions/football.md."""

from .base import PRESETS

FC = {"title": "EA Sports FC", "type": "football", "mode": "match", "mode_duration": "bounded", "confidence": 0.95}


PRESETS["fc_play"] = {
    "game": FC,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.95},
    "participants": {"primary": ["PSG", "BAR"], "count_visible": 2},
    "score": {"type": "goals"},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.95,
    "secondary_timers": [],
}


PRESETS["fc_pause"] = {
    "game": FC,
    "state": {"phase": "paused", "screen_type": "pause", "confidence": 0.95},
    "participants": {"primary": ["Paris SG", "FC Barcelone"], "count_visible": 2},
    "score": {"type": "goals"},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.95,
    "secondary_timers": [],
}


PRESETS["fc_nohud"] = {
    "game": {**FC, "confidence": 0.85},
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.85},
    "clock": {"visible": False},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.8,
    "secondary_timers": [],
}


PRESETS["fc_menu"] = {
    "game": {**FC, "mode": None, "mode_duration": "unknown", "confidence": 0.75},
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
}


F26 = {"t": "EA Sports FC 26"}


def play(i, a, b, c, obs="", parts=("PSG", "BAR"), **kw):
    base = f"Jeu en cours, bloc HUD haut gauche {parts[0]}/{parts[1]} : score {a}–{b}, chrono {c}."
    d = {"id": i, "p": "fc_play", "s": [a, b], "c": c, "obs": (base + " " + obs).strip(), **kw}
    if tuple(parts) != ("PSG", "BAR"):
        d["parts"] = list(parts)
    return d


def pause(i, a, b, c, obs="", parts=("Paris SG", "FC Barcelone"), **kw):
    base = (
        f"Menu pause « Match classique » (Reprendre match, Gestion d'équipe…); encart haut droit : "
        f"{c} {parts[0]} {a}–{b} {parts[1]}."
    )
    d = {"id": i, "p": "fc_pause", "s": [a, b], "c": c, "obs": (base + " " + obs).strip(), **kw}
    if tuple(parts) != ("Paris SG", "FC Barcelone"):
        d["parts"] = list(parts)
    return d


def nohud(i, obs, **kw):
    return {"id": i, "p": "fc_nohud", "s": None, "obs": obs, **kw}


PRESETS["fc_loading"] = {
    "game": {
        "title": "EA Sports FC 26",
        "type": "football",
        "mode": None,
        "mode_duration": "unknown",
        "confidence": 0.9,
    },
    "state": {"phase": "loading", "screen_type": "loading", "confidence": 0.85},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
}


def fcm(i, obs, extra_set=None, **kw):
    """EA FC menu frame; extra_set is merged into the dotted overrides."""
    s = dict(extra_set or {})
    return {"id": i, "p": "fc_menu", "s": None, "obs": obs, "t": "EA Sports FC 26", "set": s, **kw}


def lobby(i, obs, extra_set=None):
    s = {"state.phase": "pre_game"}
    s.update(extra_set or {})
    return fcm(i, obs + " Notes de joueurs, pas des scores.", s)


F27T = "EA Sports FC 27"


def fc27(i, a, b, c, parts, obs="", **kw):
    """FC 27 default skin: vertical block top-left, upper team = A, lower team = B, clock underneath."""
    v = (
        f"Habillage FC 27 : bloc vertical en haut à gauche, {parts[0]} en haut (A), {parts[1]} en bas (B), "
        "chrono dessous."
    )
    return play(i, a, b, c, (v + " " + obs).strip(), parts=parts, **kw)


def laliga(i, a, b, c, parts=("RMA", "BAR"), crest=False, obs=""):
    """FC 27 LaLiga broadcast skin: LaLiga logo, clock under it, teams stacked (upper = A), scores on the right."""
    who = "écussons à la place des sigles" if crest else f"sigles {parts[0]} (haut) et {parts[1]} (bas)"
    return {
        "id": i,
        "p": "fc_play",
        "s": [a, b],
        "c": c,
        "parts": list(parts),
        "obs": (
            f"Jeu en cours, habillage de diffusion LaLiga en haut à gauche : logo LaLiga, chrono {c} dessous, {who}, "
            f"scores à droite : {parts[0]} {a}, {parts[1]} {b} → score {a}–{b}, chrono {c}. " + obs
        ).strip(),
    }


def fcload(i, obs, st=None):
    """FC 27 loading / intro / non-interactive screen; st = dotted overrides."""
    d = {"id": i, "p": "fc_loading", "s": None, "t": F27T, "obs": obs}
    if st:
        d["set"] = dict(st)
    return d


def fcm27(i, obs, st=None):
    d = fcm(i, obs, st)
    d["t"] = F27T
    return d
