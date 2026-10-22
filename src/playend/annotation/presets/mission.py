"""Mission and open-world games, billed by time: Genshin Impact, Red Dead Redemption 2,
Assassin's Creed Origins, God of War. Conventions: docs/conventions/mission.md."""

from .base import PRESETS

GI = {
    "title": "Genshin Impact",
    "type": "mission_adventure",
    "mode": None,
    "mode_duration": "unknown",
    "confidence": 0.95,
}


PRESETS["gi_loading"] = {
    "game": {**GI, "confidence": 0.9},
    "state": {"phase": "loading", "screen_type": "loading", "confidence": 0.95},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
}


PRESETS["gi_menu"] = {
    "game": GI,
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.95},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
}


PRESETS["gi_play"] = {
    "game": GI,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
}


def cd(display, label=None):
    return {
        "kind": "ability_cooldown",
        "label": label,
        "display": display,
        "value_seconds": None,
        "direction": "unknown",
    }


PRESETS["gi_cut"] = {
    "game": GI,
    "state": {"phase": "active", "screen_type": "cutscene", "confidence": 0.85},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
}


PRESETS["gi_black"] = {
    "game": {**GI, "confidence": 0.6},
    "state": {"phase": "unknown", "screen_type": "other", "confidence": 0.5},
    "clock": {"visible": False},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.6,
    "secondary_timers": [],
}


def gmenu(i, obs, **kw):
    return {"id": i, "p": "gi_menu", "s": None, "obs": obs, **kw}


def gtalk(i, speaker, obs="", extra=()):
    ents = [speaker] + list(extra) if speaker and speaker != "???" else list(extra)
    return {
        "id": i,
        "p": "gi_cut",
        "s": None,
        "obs": (
            f"Dialogue de quête Genshin Impact, locuteur affiché « {speaker} » avec sous-titre; boutons Lecture en "
            f"cours / Confirmer. " + obs
        ).strip(),
        "set": {"visible_entities": ents},
    }


def groam(i, obs, timers=(), party=("Columbina", "Linnea", "Ineffa", "Flins")):
    return {
        "id": i,
        "p": "gi_play",
        "s": None,
        "obs": "Exploration Genshin Impact, équipe " + " / ".join(party) + ". " + obs,
        "set": {
            "game.mode": "free_roam",
            "visible_entities": list(party),
            "secondary_timers": [cd(display, label) for display, label in timers],
        },
    }


def gboss(i, obs, timers=()):
    return {
        "id": i,
        "p": "gi_play",
        "s": None,
        "obs": "Combat de boss « Hérétique de la fausse lune — Dottore » (Niv.90, barre de vie en haut), équipe "
        "Columbina / Linnea / Ineffa / Flins. " + obs,
        "set": {
            "game.mode": "mission",
            "visible_entities": ["Dottore", "Columbina", "Linnea", "Ineffa", "Flins"],
            "secondary_timers": [cd(display, label) for display, label in timers],
        },
    }


RDR = {
    "title": "Red Dead Redemption 2",
    "type": "mission_adventure",
    "mode": None,
    "mode_duration": "unknown",
    "confidence": 0.9,
}


PRESETS["rdr_play"] = {
    "game": {**RDR, "mode": "free_roam"},
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.85},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
    "secondary_counters": [],
}


PRESETS["rdr_menu"] = {
    "game": RDR,
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.85},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
    "secondary_counters": [],
}


PRESETS["rdr_load"] = {
    "game": {**RDR, "confidence": 0.7},
    "state": {"phase": "loading", "screen_type": "loading", "confidence": 0.8},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.75,
    "secondary_timers": [],
    "secondary_counters": [],
}


def rdr(i, obs, p="rdr_play", st=None):
    d = {"id": i, "p": p, "s": None, "obs": obs + " Aucun score, chrono de partie ni période (monde ouvert)."}
    if st:
        d["set"] = dict(st)
    return d


ACO = {
    "title": "Assassin's Creed Origins",
    "type": "mission_adventure",
    "mode": "mission",
    "mode_duration": "unknown",
    "confidence": 0.93,
}


GOW = {
    "title": "God of War",
    "type": "mission_adventure",
    "mode": "mission",
    "mode_duration": "unknown",
    "confidence": 0.9,
}


for _k, _g in (("aco", ACO), ("gow", GOW)):
    PRESETS[f"{_k}_play"] = {
        "game": _g,
        "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.88},
        "clock": {"visible": False},
        "period": {"type": "none"},
        "result": {"visible": False},
        "observation_confidence": 0.85,
        "secondary_timers": [],
        "secondary_counters": [],
    }
    PRESETS[f"{_k}_menu"] = {
        "game": {**_g, "mode": None},
        "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.9},
        "clock": {"visible": False},
        "period": {"type": "none"},
        "result": {"visible": False},
        "observation_confidence": 0.88,
        "secondary_timers": [],
        "secondary_counters": [],
    }
    PRESETS[f"{_k}_load"] = {
        "game": {**_g, "mode": None, "confidence": 0.85},
        "state": {"phase": "loading", "screen_type": "loading", "confidence": 0.85},
        "clock": {"visible": False},
        "period": {"type": "none"},
        "result": {"visible": False},
        "observation_confidence": 0.85,
        "secondary_timers": [],
        "secondary_counters": [],
    }


def aco(i, obs, objective=True, p="aco_play", st=None):
    """AC Origins frame; objective=True: quest objective text shown (progress objective, no numeric progress)."""
    d = {
        "id": i,
        "p": p,
        "s": None,
        "obs": obs
        + " Aucun score, chrono de partie ni période (jeu de mission); niveau du joueur et distances : pas des "
        "compteurs.",
    }
    s = {"progress.type": "objective"} if objective else {"game.mode": "free_roam" if p.endswith("_play") else None}
    s.update(st or {})
    d["set"] = s
    return d


def gow(i, obs, objective=False, p="gow_play", st=None):
    d = {"id": i, "p": p, "s": None, "obs": obs + " Aucun score, chrono de partie ni période (jeu de mission)."}
    s = {"progress.type": "objective"} if objective else {}
    s.update(st or {})
    d["set"] = s
    return d
