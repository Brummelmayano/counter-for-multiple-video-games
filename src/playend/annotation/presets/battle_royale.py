"""Fortnite (split screen, single view, creative islands) and Call of Duty: Warzone.
Conventions: docs/conventions/battle-royale.md."""

from .base import PRESETS, cnt

FN = {"title": "Fortnite", "type": "other", "mode": None, "mode_duration": "unknown", "confidence": 0.94}


PRESETS["fn_play"] = {
    "game": FN,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
}


PRESETS["fn_menu"] = {
    "game": FN,
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
}


def _t(kind, disp, label=None):
    import re

    secs = None
    if re.fullmatch(r"\d{1,3}:\d{2}", disp):
        m, s = disp.split(":")
        secs = int(m) * 60 + int(s)
    return {"kind": kind, "label": label, "display": disp, "value_seconds": secs, "direction": "unknown"}


def fnsplit(i, players, disp, icon, obs="", halves=2, labels=(None, None), ents=()):
    """Fortnite 2-player split screen; icon: 'storm' (shrinking), 'watch' (waiting), 'check', None."""
    kind = {"storm": "storm_phase", "watch": "storm_phase", "check": "unknown", "pre": "pre_match"}.get(icon)
    role = {
        "storm": "icône de tempête (tempête en cours de rétrécissement)",
        "watch": "icône chronomètre (attente avant le prochain rétrécissement de la tempête)",
        "check": "icône coche verte, rôle incertain → kind unknown",
        "pre": "compte à rebours d'avant-partie",
    }.get(icon, "")
    timers = [] if disp is None else [_t(kind, disp, labels[k]) for k in range(halves)]
    base = (
        "Fortnite en écran partagé deux joueurs (vue haute et vue basse, portraits des skins à droite/gauche). "
        f"HUD : {players} joueurs restants"
        + (
            f"; minuteur {disp} avec {role}, affiché dans {'les deux vues' if halves == 2 else 'une seule vue'} → "
            f"{halves} minuteur(s) secondaire(s)"
            if disp
            else "; aucun minuteur"
        )
        + ". Éliminations, assistances et joueurs restants sont des statistiques, pas un score; aucune période ni "
        "chrono principal."
    )
    counters = [cnt("players_remaining", "field", players)] if players is not None else []
    return {
        "id": i,
        "p": "fn_play",
        "s": None,
        "obs": (base + " " + obs).strip(),
        "set": {"secondary_timers": timers, "visible_entities": list(ents), "secondary_counters": counters},
    }


PRESETS["fn_crea"] = {
    "game": {**FN, "mode": "other"},
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.85},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.82,
    "secondary_timers": [],
    "secondary_counters": [],
}


def fncrea(i, island, obs="", ents=(), timers=(), split=True):
    """Fortnite creative island gameplay: individual leaderboard (points) and player count are arena statistics."""
    view = "en écran partagé deux joueurs" if split else "en vue unique"
    base = (
        f"Fortnite, île créative « {island} » {view}. En haut à droite : nombre de joueurs présents sur l'île et "
        "classement individuel (pseudos et points) : statistiques d'arène à réapparition, ni score A/B, ni joueurs "
        "restants. "
        "Rang « BRONZE I »/« UNRANKED » avec progression X/200 ou X/100 : niveau de classement, pas un compteur de "
        "fin. "
        "Aucun chrono de partie, aucune période."
    )
    return {
        "id": i,
        "p": "fn_crea",
        "s": None,
        "obs": (base + " " + obs).strip(),
        "set": {"visible_entities": list(ents), "secondary_timers": list(timers)},
    }


def fnsolo(i, players, disp, icon, obs="", elim=None, extra_timers=(), ents=()):
    """Fortnite single view.

    icon: 'storm', 'watch', 'bus' or 'pre' (pre_match), 'dive' or 'check' (unknown), None.
    """
    kind = {
        "storm": "storm_phase",
        "watch": "storm_phase",
        "bus": "pre_match",
        "pre": "pre_match",
        "dive": "unknown",
        "check": "unknown",
    }.get(icon)
    role = {
        "storm": "icône de tempête (tempête en cours de rétrécissement)",
        "watch": "icône chronomètre (attente avant le prochain rétrécissement)",
        "bus": "icône de bus (compte à rebours avant l'ouverture des portes du bus)",
        "pre": "compte à rebours d'avant-partie",
        "dive": "icône de parachutiste, rôle incertain → kind unknown",
        "check": "icône coche, rôle incertain → kind unknown",
    }.get(icon, "")
    timers = ([] if disp is None else [_t(kind, disp)]) + list(extra_timers)
    base = (
        "Fortnite en vue unique (un joueur), HUD en haut à droite à gauche de la minicarte : "
        + (f"{elim} élimination(s) (statistique), " if elim is not None else "")
        + (f"{players} joueurs restants" if players is not None else "joueurs restants non affichés")
        + (f"; minuteur {disp} avec {role}" if disp else "; aucun minuteur")
        + ". Éliminations et joueurs restants ne sont pas un score; aucune période ni chrono principal."
    )
    counters = [cnt("players_remaining", "field", players)] if players is not None else []
    return {
        "id": i,
        "p": "fn_play",
        "s": None,
        "obs": (base + " " + obs).strip(),
        "set": {"secondary_timers": timers, "visible_entities": list(ents), "secondary_counters": counters},
    }


def fnm(i, obs, st=None):
    return {"id": i, "p": "fn_menu", "s": None, "obs": obs, "set": dict(st or {})}


def resp(disp):
    return {
        "kind": "respawn",
        "label": "EXPIRATION DE LA CARTE DE RÉTABLISSEMENT DANS",
        "display": disp,
        "value_seconds": None,
        "direction": "unknown",
    }


def pre(disp, label="EN ATTENTE DE JOUEURS"):
    return _t("pre_match", disp, label)


WZ = {
    "title": "Call of Duty: Warzone",
    "type": "other",
    "mode": "other",
    "mode_duration": "unknown",
    "confidence": 0.94,
}


PRESETS["wz_play"] = {
    "game": WZ,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.88,
    "secondary_timers": [],
    "secondary_counters": [],
}


PRESETS["wz_menu"] = {
    "game": {**WZ, "mode": None},
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
    "secondary_counters": [],
}


def wz(i, teams, players, elim=None, badge=None, timer=None, obs="", spect=False):
    """Warzone gameplay: top-right squad icon = teams remaining, person icon = players remaining, skull = eliminations
    (statistic); circle badge under the minimap = period stage, its countdown = storm_phase timer."""
    parts = []
    parts.append(f"{teams} équipes restantes" if teams is not None else "équipes restantes illisibles")
    parts.append(
        f"{players} joueurs restants" if players is not None else "joueurs restants illisibles (chiffre en animation)"
    )
    if elim is not None:
        parts.append(f"{elim} éliminations (statistique)")
    base = (
        "Warzone en jeu, compteurs en haut à droite : "
        + ", ".join(parts)
        + (
            f"; badge de cercle {badge} et minuteur {timer} sous la minicarte → période stage {badge}, minuteur de "
            "cercle"
            if badge
            else "; aucun badge de cercle ni minuteur"
        )
        + ". Argent, niveaux et éliminations ne sont pas des scores."
    )
    if spect:
        base += " Bandeau « SPECTATEUR » (joueur éliminé, en attente de réapparition)."
    counters = []
    if players is not None:
        counters.append(cnt("players_remaining", "field", players))
    if teams is not None:
        counters.append(cnt("teams_remaining", "field", teams))
    d = {
        "id": i,
        "p": "wz_play",
        "s": None,
        "obs": (base + " " + obs).strip(),
        "set": {"secondary_counters": counters, "secondary_timers": [_t("storm_phase", timer)] if timer else []},
    }
    if badge:
        d["pd"] = ["stage", badge, None]
    return d


def wzm(i, obs, st=None):
    return {"id": i, "p": "wz_menu", "s": None, "obs": obs, "set": dict(st or {})}
