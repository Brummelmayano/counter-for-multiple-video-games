"""Fighting games: Mortal Kombat 1, Naruto Storm Connections, Dragon Ball Sparking! ZERO and FighterZ,
Demon Slayer, J-Stars Victory VS+. Conventions: docs/conventions/combat.md."""

from .base import PRESETS, cnt

MK = {"title": "Mortal Kombat 1", "type": "combat", "mode": "versus", "mode_duration": "bounded", "confidence": 0.95}


PRESETS["mk_fight"] = {
    "game": MK,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.95},
    "score": {"type": "rounds_won"},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.93,
    "secondary_timers": [],
}


PRESETS["mk_pause"] = {
    "game": {**MK, "mode": None, "mode_duration": "unknown", "confidence": 0.85},
    "state": {"phase": "paused", "screen_type": "pause", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
}


def mk(i, a, b, t, left, right, kameos, obs="", **kw):
    """Fighting frame: a/b = filled round markers left/right of the timer, t = bare round timer (seconds)."""
    base = (
        f"Combat MK1 {left} (gauche) contre {right} (droite), Kaméos {kameos[0]} / {kameos[1]}. "
        "Contrôle prioritaire des marqueurs de rounds (deux ronds de chaque côté du chrono) : "
        f"gauche {a} rempli(s), droite {b} rempli(s) → score {a}–{b}. Chrono de round {t}."
    )
    d = {
        "id": i,
        "p": "mk_fight",
        "s": [a, b],
        "c": str(t),
        "parts": [left, right],
        "obs": (base + " " + obs).strip(),
        **kw,
    }
    d.setdefault("set", {})["visible_entities"] = list(kameos)
    d["set"]["secondary_counters"] = [cnt("target", "field", 2)]  # 2 marker slots per side
    return d


PRESETS["mk_training"] = {
    "game": {
        "title": "Mortal Kombat 1",
        "type": "combat",
        "mode": "other",
        "mode_duration": "continuous",
        "confidence": 0.9,
    },
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.9},
    "clock": {"visible": True, "display": "∞", "value_seconds": None, "direction": "unknown"},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
}


def mkt(i, left, lk, right, rk, obs=""):
    base = (
        f"MK1 en mode entraînement : {left} (Kaméo {lk}) à gauche contre {right} (Kaméo {rk}) à droite; symbole ∞ à "
        "la place du chrono "
        "(preuve positive d'une durée illimitée → clock display « ∞ », secondes nulles, mode_duration continuous). "
        "Contrôle prioritaire des marqueurs : "
        "aucun emplacement de marqueur de round de part et d'autre du ∞ → score null. Nombres rouges à gauche "
        "(dégâts du combo) et barres de vie X/1000 ou X/1050 : pas des scores."
    )
    return {
        "id": i,
        "p": "mk_training",
        "s": None,
        "parts": [left, right],
        "obs": (base + " " + obs).strip(),
        "set": {"visible_entities": [lk, rk]},
    }


NA = {
    "title": "Naruto x Boruto Ultimate Ninja Storm Connections",
    "type": "combat",
    "mode": "versus",
    "mode_duration": "bounded",
    "confidence": 0.95,
}


PRESETS["na_menu"] = {
    "game": {**NA, "mode": None, "mode_duration": "unknown"},
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
}


PRESETS["na_fight"] = {
    "game": NA,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.93},
    "score": {"type": "rounds_won"},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
}


def na(i, a, b, t, left, right, obs=""):
    base = (
        f"Combat Naruto Storm Connections : {left} (gauche) contre {right} (droite). Contrôle prioritaire des "
        "marqueurs de rounds "
        "(deux emplacements de chaque côté sous le chrono; rempli = pastille orange, vide = icône grise) : gauche "
        f"{a} rempli(s), "
        f"droite {b} rempli(s) → score {a}–{b}. Chrono de round {t} (secondes). Chiffres de combo « COUPS » : pas un "
        "score."
    )
    return {
        "id": i,
        "p": "na_fight",
        "s": [a, b],
        "c": str(t),
        "parts": [left, right],
        "obs": (base + " " + obs).strip(),
        "set": {"secondary_counters": [cnt("target", "field", 2)]},
    }


def nasel(i, left, right, obs=""):
    return {
        "id": i,
        "p": "na_menu",
        "parts": [left, right],
        "s": None,
        "obs": (
            f"Écran de sélection des personnages Naruto Storm Connections : J1 {left} contre J2 {right} (techniques, "
            f"soutiens, grille de portraits). Aucun HUD de combat. " + obs
        ).strip(),
        "set": {"state.phase": "pre_game", "state.screen_type": "character_select"},
    }


DB = {
    "title": "Dragon Ball Sparking! ZERO",
    "type": "combat",
    "mode": "versus",
    "mode_duration": "unknown",
    "confidence": 0.93,
}


PRESETS["db_fight"] = {
    "game": DB,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.9},
    "participants": {"primary": [], "count_visible": 2},
    "clock": {"visible": False},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
}


PRESETS["db_menu"] = {
    "game": {**DB, "mode": None},
    "state": {"phase": "pre_game", "screen_type": "character_select", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
}


PRESETS["db_cut"] = {
    "game": DB,
    "state": {"phase": "active", "screen_type": "cutscene", "confidence": 0.8},
    "participants": {"primary": [], "count_visible": None},
    "clock": {"visible": False},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.8,
    "secondary_timers": [],
}


DBNOTE = (
    "Écran partagé deux joueurs (vue J1 à gauche, vue J2 à droite), barres de vie/ki segmentées et portraits. Les "
    "nombres sous les portraits "
    "sont des points de compétence, les « Hits » et nombres sous ceux-ci sont combo/dégâts : aucun marqueur de round "
    "gagné identifié → score null. "
    "Noms des combattants non écrits dans le HUD → participants non nommés."
)


def dbf(i, obs="", inf=False, hp=None):
    """hp=(a, b): lit boxes of the remaining-HP-bars rows (zoom tool dragon-ball), None for an unreadable side;
    hp=None when the boxes are hidden → secondary_counters null (decision of the user, 2026-10-04)."""
    d = {"id": i, "p": "db_fight", "s": None, "obs": (DBNOTE + " " + obs).strip()}
    if hp is None:
        d["cnt"] = None
        d["obs"] += " Rangées de barres de vie restantes non visibles → compteurs non inventoriés."
    else:
        d["cnt"] = [cnt("lives", side, v) for side, v in zip("ab", hp)]
        d["obs"] += (
            f" Barres de vie restantes (petits blocs allumés près de chaque portrait, guide officiel) : gauche "
            f"{'illisible' if hp[0] is None else hp[0]}, droite {'illisible' if hp[1] is None else hp[1]} → compteurs "
            "lives a/b, "
            "total null (les emplacements vides sont la capacité de l'écran)."
        )
    if inf:
        d["c"] = "∞"
        d["obs"] += (
            " Symbole ∞ en haut au centre à l'emplacement du chrono (durée illimitée) → clock ∞, mode_duration "
            "continuous."
        )
        d["set"] = {"clock.value_seconds": None, "game.mode_duration": "continuous"}
    return d


def dbcut(i, obs, ents=()):
    return {
        "id": i,
        "p": "db_cut",
        "s": None,
        "obs": obs + " Aucun HUD de combat.",
        "set": {"visible_entities": list(ents)},
    }


def dbsel(i, obs):
    return {"id": i, "p": "db_menu", "s": None, "obs": obs + " Aucun HUD de combat."}


def dbwin(i):
    return {
        "id": i,
        "p": "db_cut",
        "s": None,
        "obs": "Écran de fin avec texte explicite « Victoire » et portrait d'un personnage (Goku Super Saiyan 4 "
        "d'après l'apparence), « Niveau de joueur 20 » en haut à gauche (niveau de profil, pas un score), "
        "bouton Suivant. "
        "Résultat visible : victoire; aucun nom de joueur ou de personnage écrit → winner null.",
        "set": {
            "state.phase": "post_game",
            "state.screen_type": "result",
            "state.confidence": 0.95,
            "result.visible": True,
            "result.outcome_type": "win",
        },
    }


KNY = {
    "title": "Demon Slayer: Kimetsu no Yaiba – The Hinokami Chronicles",
    "type": "combat",
    "mode": "versus",
    "mode_duration": "bounded",
    "confidence": 0.9,
}


PRESETS["kny_fight"] = {
    "game": KNY,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.9},
    "participants": {"primary": [], "count_visible": 2},
    "score": {"type": "rounds_won"},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.88,
    "secondary_timers": [],
}


PRESETS["kny_menu"] = {
    "game": {**KNY, "mode": None, "mode_duration": "unknown"},
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.88,
    "secondary_timers": [],
    "secondary_counters": [],
}


def kny(i, a, b, t, obs=""):
    """Round markers: two diamonds under each side of the timer (inner one lights first; yellow = round won)."""
    base = (
        f"Combat Demon Slayer (Hinokami Chronicles) en duo J1 (gauche) contre IA (droite); noms non écrits dans le "
        "HUD. "
        "Contrôle prioritaire des marqueurs de manches (deux losanges sous la barre de chaque côté du chrono; jaune "
        "= manche gagnée) : "
        f"gauche {a}, droite {b} → score {a}–{b}. Chrono {t} (secondes). Chiffres en bas (0 à 2) = jauge "
        "d'Éveil/Pouvoir ultime, compteur « Coups » = combo : pas des scores."
    )
    return {
        "id": i,
        "p": "kny_fight",
        "s": [a, b],
        "c": str(t),
        "obs": (base + " " + obs).strip(),
        "set": {"secondary_counters": [cnt("target", "field", 2)]},
    }


DBFZ = {
    "title": "Dragon Ball FighterZ",
    "type": "combat",
    "mode": "versus",
    "mode_duration": "unknown",
    "confidence": 0.93,
}


PRESETS["dbfz_fight"] = {
    "game": DBFZ,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.9},
    "clock": {"visible": True, "display": "∞", "value_seconds": None, "direction": "unknown"},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.88,
    "secondary_timers": [],
    "secondary_counters": [],
}


PRESETS["dbfz_menu"] = {
    "game": {**DBFZ, "mode": None},
    "state": {"phase": "pre_game", "screen_type": "character_select", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
    "secondary_counters": [],
}


PRESETS["dbfz_cut"] = {
    "game": DBFZ,
    "state": {"phase": "active", "screen_type": "cutscene", "confidence": 0.8},
    "clock": {"visible": False},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.8,
    "secondary_timers": [],
    "secondary_counters": [],
}


def dbfz(i, left, right, obs="", pause=False):
    base = (
        f"Combat Dragon Ball FighterZ 3 contre 3 : {left} (gauche, actif) contre {right} (droite, actif), noms écrits "
        "dans le HUD. "
        "Symbole ∞ à la place du chrono (pas de limite de temps) → clock « ∞ », secondes nulles. Aucun marqueur de "
        "manche : score null. "
        "Chiffres en bas (0 à 7) = barres de ki; portraits des coéquipiers (croix = K.O.) : pas des scores."
    )
    d = {"id": i, "p": "dbfz_fight", "s": None, "parts": [left, right], "obs": (base + " " + obs).strip()}
    if pause:
        d["set"] = {"state.phase": "paused", "state.screen_type": "pause"}
    return d


JS = {"title": "J-Stars Victory VS+", "type": "combat", "mode": "versus", "mode_duration": "bounded", "confidence": 0.9}


PRESETS["js_fight"] = {
    "game": JS,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.9},
    "score": {"type": "points"},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.85,
    "secondary_timers": [],
    "secondary_counters": [],
}


PRESETS["js_menu"] = {
    "game": {**JS, "mode": None, "mode_duration": "unknown"},
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.88,
    "secondary_timers": [],
    "secondary_counters": [],
}


PRESETS["js_cut"] = {
    "game": JS,
    "state": {"phase": "active", "screen_type": "cutscene", "confidence": 0.8},
    "clock": {"visible": False},
    "period": {"type": "unknown"},
    "result": {"visible": False},
    "observation_confidence": 0.8,
    "secondary_timers": [],
    "secondary_counters": None,
}


def js(i, a, b, t, me, target=None, obs="", st=None):
    """J-Stars fight frame. a/b = lit victory-gauge segments left (red) / right (blue) (None = unreadable);
    t = 'Temps' display (bare seconds or mm:ss); me = controlled fighter name written bottom left; target = locked-on
    opponent name written above its bar (None if not on screen)."""
    sa = "illisible" if a is None else str(a)
    sb = "illisible" if b is None else str(b)
    tgt = (
        f"nom de l'adversaire verrouillé « {target} » écrit au-dessus de sa barre (équipe bleue, B)"
        if target
        else "aucun nom d'adversaire écrit sur cette image"
    )
    base = (
        f"Combat J-Stars Victory VS+ : combattant contrôlé « {me} » écrit en bas à gauche (équipe rouge, A); {tgt}. "
        "Contrôle prioritaire des marqueurs : jauge de victoire en haut, 3 segments de chaque côté (rouge à gauche, "
        "bleu à droite), "
        f"segments allumés : gauche {sa}, droite {sb}"
        + (f" → score {a}–{b} (points de victoire)" if a is not None and b is not None else " → score non renseigné")
        + f". Minuteur « Temps {t} » en bas à droite = chrono du combat. "
        "Jauge centrale rouge/bleue à flèches, compteurs « coups » (combo) et barres de vie : pas des scores."
    )
    return {
        "id": i,
        "p": "js_fight",
        "s": None if a is None or b is None else [a, b],
        "c": t,
        "parts": [me] + ([target] if target else []),
        "obs": (base + " " + obs).strip(),
        "set": {"participants.count_visible": 2, "secondary_counters": [cnt("target", "field", 3)], **(st or {})},
    }


def jsm(i, obs, st=None, parts=None, ents=(), p="js_menu"):
    d = {"id": i, "p": p, "s": None, "obs": obs, "set": {"visible_entities": list(ents), **(st or {})}}
    if parts is not None:
        d["parts"] = list(parts)
    return d
