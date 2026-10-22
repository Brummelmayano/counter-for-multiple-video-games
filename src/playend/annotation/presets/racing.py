"""Beach Buggy Racing 2. Conventions: docs/conventions/course.md.

In split screen the position stays empty and each view's place goes into the note (user decision of
2026-10-04); the central "TOUR n" label is the lap."""

from .base import PRESETS

BBR = {
    "title": "Beach Buggy Racing 2",
    "type": "racing",
    "mode": "race",
    "mode_duration": "bounded",
    "confidence": 0.93,
}


PRESETS["bbr_race"] = {
    "game": BBR,
    "state": {"phase": "active", "screen_type": "gameplay", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.88,
    "secondary_timers": [],
    "secondary_counters": [],
}


PRESETS["bbr_menu"] = {
    "game": {**BBR, "mode": None, "mode_duration": "unknown"},
    "state": {"phase": "menu", "screen_type": "menu", "confidence": 0.9},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": False},
    "observation_confidence": 0.9,
    "secondary_timers": [],
    "secondary_counters": [],
}


PRESETS["bbr_result"] = {
    "game": BBR,
    "state": {"phase": "post_game", "screen_type": "result", "confidence": 0.95},
    "clock": {"visible": False},
    "period": {"type": "none"},
    "result": {"visible": True, "outcome_type": "other"},
    "observation_confidence": 0.92,
    "secondary_timers": [],
    "secondary_counters": [],
}


BBR_VIEWS = {
    3: ("vue du haut", "vue en bas à gauche", "vue en bas à droite"),
    4: ("vue en haut à gauche", "vue en haut à droite", "vue en bas à gauche", "vue en bas à droite"),
    2: ("vue du haut", "vue du bas"),
    1: ("vue unique",),
}


def _fin(disp):
    return {
        "kind": "other",
        "label": "Fin de la course !",
        "display": disp,
        "value_seconds": None,
        "direction": "unknown",
    }


def bbr(i, places, lap, obs="", fin=(), total=8, pre=None):
    """Race frame. places: one 'N/8 PLACE' value per view, first view first (None = unreadable);
    lap: central 'TOUR n' (None = hidden/unreadable); fin: displays of the 'Fin de la course ! NN' countdowns
    (one per view showing it); pre: start countdown digit shown in the views (pre_match timer, seconds null)."""
    n = len(places)
    views = BBR_VIEWS[n]
    pl = "; ".join(f"{v} {p}/{total} PLACE" if p is not None else f"{v} place illisible" for v, p in zip(views, places))
    lp = (
        f"libellé central « TOUR {lap} » (sans total affiché)"
        if lap is not None
        else "libellé central « TOUR » dont le chiffre est masqué ou illisible"
    )
    split = f"écran partagé à {n} vues" if n > 1 else "vue unique"
    rule = (
        "Convention (décision de l'utilisateur, 2026-10-04) : plusieurs coureurs contrôlés, aucun coureur unique "
        "identifiable "
        "→ position vide; la place de chaque vue reste en note. "
        if n > 1
        else "Position = place de la vue unique. "
    )
    base = (
        f"Course Beach Buggy Racing 2 en {split}. Places lues dans chaque vue : {pl}. {lp}. "
        + rule
        + "Aucun chrono de course affiché, aucune période; noms des pilotes contrôlés non écrits dans leur vue → "
        "participants non nommés, "
        f"{n} pilote(s) contrôlé(s) (une vue chacun). Icônes de bonus (bombes, boucliers…) : pas des compteurs."
    )
    timers = [_fin(d) for d in fin]
    if fin:
        base += (
            f" Compte à rebours « Fin de la course ! {fin[0]} » dans {len(fin)} vue(s) (délai avant la fin forcée de "
            "la course) "
            "→ minuteur(s) secondaire(s) kind other, secondes non converties."
        )
    single = places[0] if n == 1 else None  # contract: the controlled racer's place, only when there is a single one
    st = {
        "position.current": single,
        "position.total": total if single is not None else None,
        "progress.type": "lap" if lap is not None else None,
        "progress.current": lap,
        "participants.count_visible": n,
        "secondary_timers": timers,
    }
    if pre is not None:
        timers.append(
            {"kind": "pre_match", "label": None, "display": pre, "value_seconds": None, "direction": "unknown"}
        )
        base += f" Compte à rebours de départ « {pre} » au centre des vues (avant le départ) → minuteur pre_match."
        st["state.phase"] = "pre_game"
    return {"id": i, "p": "bbr_race", "s": None, "parts": [], "obs": (base + " " + obs).strip(), "set": st}


def bbrres(i, rows, event=None, of=8, obs="", st=None):
    """Event classification board ('Mystère 8'): rows = racer names in displayed order (1st first)."""
    names = ", ".join(f"{k + 1}. {r}" for k, r in enumerate(rows))
    ev = f"« ÉVÉNEMENT {event} sur {of} »" if event else "numéro d'événement non lisible"
    base = (
        f"Tableau de résultats de l'épreuve (championnat « Mystère 8 », 1000 CV | Règles de la ligue), {ev} : {names}, "
        "avec temps de course et points de l'épreuve (10, 8, 6…). Résultat explicite : classement de la course; "
        "vainqueur écrit « 1er "
        f"{rows[0]} ». Temps et points : pas un score A/B ni un chrono courant. Participants = noms écrits dans le "
        "tableau, dans l'ordre affiché."
    )
    s = {
        "result.winner": rows[0],
        "progress.type": "stage" if event else None,
        "progress.current": event,
        "progress.total": of if event else None,
    }
    s.update(st or {})
    return {"id": i, "p": "bbr_result", "s": None, "parts": list(rows), "obs": (base + " " + obs).strip(), "set": s}


def bbrm(i, obs, st=None, parts=None, ents=()):
    d = {"id": i, "p": "bbr_menu", "s": None, "obs": obs, "set": {"visible_entities": list(ents), **(st or {})}}
    if parts is not None:
        d["parts"] = list(parts)
    return d
