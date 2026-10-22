"""Column dictionary of the PlayEnd tables, in file order: name, type, unit, allowed values, English and French
definitions. The export writes the columns in this order and refuses a table whose columns differ from it.

Types follow the Frictionless Table Schema ("object" is a JSON text); an empty cell is a missing value.
"""

from playend.contract.contract import TIMER_KINDS
from playend.contract.legacy_v1 import ENUMS


def choices(path: str) -> str:
    return "|".join(sorted(str(value) for value in ENUMS[path] if value is not None))


STATUS = "present|none|unknown"

KEYS = [
    (
        "session_id",
        "string",
        "",
        "",
        "Capture session: one boot of the capture device, recorded without interruption.",
        "Session de capture : un démarrage du boîtier de capture, enregistré sans interruption.",
    ),
    (
        "frame_id",
        "integer",
        "",
        "",
        "Rank of the screenshot in its session, from 1, without gaps.",
        "Rang de la capture d'écran dans sa session, à partir de 1, sans trou.",
    ),
]

OBSERVATIONS = KEYS + [
    (
        "t_s",
        "number",
        "s",
        "",
        "Seconds since the first screenshot of the session, from the device's monotonic clock (nanosecond "
        "precision). No wall-clock time is given: the device clock was wrong.",
        "Secondes depuis la première capture de la session, selon l'horloge monotone du boîtier (précision à la "
        "nanoseconde). Aucune heure civile : l'horloge du boîtier était fausse.",
    ),
    (
        "delta_t_s",
        "number",
        "s",
        "",
        "Seconds since the previous screenshot of the same session; empty on the first one. Screenshots are "
        "taken at random intervals of 10 to 45 s, plus the processing delay.",
        "Secondes depuis la capture précédente de la même session ; vide pour la première. Les captures sont "
        "prises à intervalles aléatoires de 10 à 45 s, plus le temps de traitement.",
    ),
    (
        "game_title",
        "string",
        "",
        "",
        "Game title as read by the annotator (several spellings for one game are possible).",
        "Titre du jeu tel que lu par l'annotateur (plusieurs graphies possibles pour un même jeu).",
    ),
    (
        "game_family",
        "string",
        "",
        "",
        "Stable game name grouping the titles of one game (for example EA Sports FC 26 and 27 give EA Sports "
        "FC); empty when no game is identified (console home screen, black screen).",
        "Nom stable qui regroupe les titres d'un même jeu (par exemple EA Sports FC 26 et 27 donnent EA Sports "
        "FC) ; vide quand aucun jeu n'est identifié (accueil de la console, écran noir).",
    ),
    (
        "game_type",
        "string",
        "",
        choices("game.type"),
        "Genre of the game.",
        "Genre du jeu.",
    ),
    (
        "game_mode",
        "string",
        "",
        "match|versus|bout|race|grand_prix|street_race|mission|free_roam|other, or free text",
        "Game mode, preferably one of the listed values; free text read on screen otherwise.",
        "Mode de jeu, de préférence une des valeurs listées ; sinon le texte lu à l'écran.",
    ),
    (
        "mode_duration",
        "string",
        "",
        choices("game.mode_duration"),
        "Whether the mode has an end of game (bounded) or not (continuous: missions, open worlds, training).",
        "Le mode a-t-il une fin de partie (bounded) ou non (continuous : missions, mondes ouverts, entraînement).",
    ),
    (
        "phase",
        "string",
        "",
        choices("state.phase"),
        "Phase of play shown by the screenshot.",
        "Phase de jeu montrée par la capture.",
    ),
    (
        "screen_type",
        "string",
        "",
        choices("state.screen_type"),
        "Kind of screen.",
        "Type d'écran.",
    ),
    (
        "score_a",
        "integer",
        "",
        "",
        "Score of side a (left or home side) read on the HUD; empty when not shown or not readable.",
        "Score du côté a (à gauche ou à domicile) lu sur le HUD ; vide s'il n'est pas affiché ou pas lisible.",
    ),
    (
        "score_b",
        "integer",
        "",
        "",
        "Score of side b, read like score_a.",
        "Score du côté b, lu comme score_a.",
    ),
    (
        "score_type",
        "string",
        "",
        choices("score.type"),
        "What the score counts.",
        "Ce que compte le score.",
    ),
    (
        "clock_visible",
        "boolean",
        "",
        "",
        "Whether the main game clock is on screen.",
        "Le chronomètre principal du jeu est-il à l'écran.",
    ),
    (
        "clock_display",
        "string",
        "",
        "",
        "Main clock text exactly as displayed (for example 74:12 or ∞).",
        "Texte du chronomètre principal tel qu'affiché (par exemple 74:12 ou ∞).",
    ),
    (
        "clock_seconds",
        "integer",
        "s",
        "",
        "Main clock converted to seconds; empty when it is not a time (∞) or not readable.",
        "Chronomètre principal converti en secondes ; vide si ce n'est pas un temps (∞) ou s'il est illisible.",
    ),
    (
        "clock_direction",
        "string",
        "",
        choices("clock.direction"),
        "Whether the main clock counts down or up.",
        "Le chronomètre principal descend-il ou monte-t-il.",
    ),
    (
        "period_type",
        "string",
        "",
        choices("period.type"),
        "Kind of period (half, round...); none when the game has no periods.",
        "Type de période (mi-temps, round...) ; none quand le jeu n'a pas de périodes.",
    ),
    (
        "period_number",
        "integer",
        "",
        "",
        "Number of the current period.",
        "Numéro de la période en cours.",
    ),
    (
        "period_total",
        "integer",
        "",
        "",
        "Number of periods when shown on screen.",
        "Nombre de périodes, quand il est affiché.",
    ),
    (
        "progress_type",
        "string",
        "",
        choices("progress.type"),
        "Kind of progress shown (lap, checkpoint...).",
        "Type de progression affichée (tour, point de passage...).",
    ),
    (
        "progress_current",
        "integer",
        "",
        "",
        "Current progress value (for example the current lap).",
        "Valeur de la progression (par exemple le tour en cours).",
    ),
    (
        "progress_total",
        "integer",
        "",
        "",
        "Total of the progress when shown (for example the number of laps).",
        "Total de la progression, quand il est affiché (par exemple le nombre de tours).",
    ),
    (
        "position_current",
        "integer",
        "",
        "",
        "Place of the player in a race; empty in split screen, where several racers are controlled.",
        "Place du joueur dans une course ; vide en écran partagé, où plusieurs coureurs sont contrôlés.",
    ),
    (
        "position_total",
        "integer",
        "",
        "",
        "Number of competitors when shown next to the place.",
        "Nombre de concurrents, quand il est affiché à côté de la place.",
    ),
    (
        "result_visible",
        "boolean",
        "",
        "",
        "Whether a result of the game (winner, final score, victory screen) is shown.",
        "Un résultat de partie (vainqueur, score final, écran de victoire) est-il affiché.",
    ),
    (
        "result_outcome_type",
        "string",
        "",
        choices("result.outcome_type"),
        "How the shown result was reached.",
        "Comment le résultat affiché a été obtenu.",
    ),
    (
        "result_winner",
        "string",
        "",
        "",
        "Winner as written on screen; player_team when the screen says the player's side won. Real player "
        "names are replaced by pseudonyms.",
        "Vainqueur tel qu'écrit à l'écran ; player_team quand l'écran dit que le camp du joueur a gagné. Les "
        "vrais noms de joueurs sont remplacés par des pseudonymes.",
    ),
    (
        "players_remaining",
        "integer",
        "",
        "",
        "Players still in the game (battle royale).",
        "Joueurs encore en jeu (battle royale).",
    ),
    (
        "teams_remaining",
        "integer",
        "",
        "",
        "Teams or squads still in the game.",
        "Équipes ou escouades encore en jeu.",
    ),
    (
        "lives_a",
        "integer",
        "",
        "",
        "Lives, stocks or health bars left to side a.",
        "Vies, stocks ou barres de vie restants du côté a.",
    ),
    (
        "lives_b",
        "integer",
        "",
        "",
        "Lives, stocks or health bars left to side b.",
        "Vies, stocks ou barres de vie restants du côté b.",
    ),
    (
        "target",
        "integer",
        "",
        "",
        "Value that ends the game when reached, common to both sides and only when the HUD shows it (for "
        "example two round slots per fighter, a score limit of 100).",
        "Valeur qui finit la partie quand elle est atteinte, commune aux deux côtés et seulement si le HUD "
        "l'affiche (par exemple deux emplacements de rounds par combattant, une limite de score de 100).",
    ),
    (
        "target_a",
        "integer",
        "",
        "",
        "Value that ends the game when side a reaches it, when it differs between the sides.",
        "Valeur qui finit la partie quand le côté a l'atteint, quand elle diffère entre les côtés.",
    ),
    (
        "target_b",
        "integer",
        "",
        "",
        "Value that ends the game when side b reaches it, when it differs between the sides.",
        "Valeur qui finit la partie quand le côté b l'atteint, quand elle diffère entre les côtés.",
    ),
    (
        "series_a",
        "integer",
        "",
        "",
        "Counter of side a that runs across consecutive games (for example WINS 2 under a fighter in Tekken).",
        "Compteur du côté a qui court sur plusieurs parties de suite (par exemple WINS 2 sous un combattant dans "
        "Tekken).",
    ),
    (
        "series_b",
        "integer",
        "",
        "",
        "Counter of side b that runs across consecutive games.",
        "Compteur du côté b qui court sur plusieurs parties de suite.",
    ),
    (
        "series",
        "integer",
        "",
        "",
        "Counter across consecutive games shown for both sides together (for example a series score).",
        "Compteur sur plusieurs parties de suite affiché pour les deux côtés ensemble (par exemple un score de série).",
    ),
    (
        "counters_status",
        "string",
        "",
        STATUS,
        "Counters that measure what is left before the end: present (at least one listed), none (HUD inspected, "
        "no such counter), unknown (HUD hidden, or observation in contract 2.0, which had no counters).",
        "Compteurs de ce qui reste avant la fin : present (au moins un listé), none (HUD inspecté, aucun "
        "compteur), unknown (HUD caché, ou observation du contrat 2.0, qui n'avait pas de compteurs).",
    ),
    (
        "secondary_timers_status",
        "string",
        "",
        STATUS,
        "Secondary timers (storm phase, respawn, cooldown...): present, none or unknown, as for counters.",
        "Minuteurs secondaires (phase de tempête, réapparition, recharge...) : present, none ou unknown, comme "
        "pour les compteurs.",
    ),
    (
        "secondary_timer_kinds",
        "string",
        "",
        "|".join(TIMER_KINDS) + ", separated by |",
        "Kinds of the secondary timers on screen, separated by |, in screen order; details in observation_json.",
        "Types des minuteurs secondaires à l'écran, séparés par |, dans l'ordre de l'écran ; détail dans "
        "observation_json.",
    ),
    (
        "secondary_timer_min_seconds",
        "number",
        "s",
        "",
        "Smallest readable value among the secondary timers.",
        "Plus petite valeur lisible parmi les minuteurs secondaires.",
    ),
    (
        "participants_count_visible",
        "integer",
        "",
        "",
        "Number of participants visible on screen, as estimated by the annotator.",
        "Nombre de participants visibles à l'écran, selon l'annotateur.",
    ),
    (
        "participants_listed",
        "integer",
        "",
        "",
        "Number of participant names written on screen (only written text is recorded, never a name guessed "
        "from a logo or a face).",
        "Nombre de noms de participants écrits à l'écran (seul le texte écrit est relevé, jamais un nom deviné "
        "d'après un logo ou un visage).",
    ),
    (
        "participant_a",
        "string",
        "",
        "",
        "First participant name written on screen: side a in two-sided games. Real player names are replaced "
        "by pseudonyms; character and team names are kept. The other names are in observation_json.",
        "Premier nom de participant écrit à l'écran : le côté a dans les jeux à deux camps. Les vrais noms de "
        "joueurs sont remplacés par des pseudonymes ; les noms de personnages et d'équipes restent. Les autres "
        "noms sont dans observation_json.",
    ),
    (
        "participant_b",
        "string",
        "",
        "",
        "Second participant name written on screen: side b in two-sided games.",
        "Deuxième nom de participant écrit à l'écran : le côté b dans les jeux à deux camps.",
    ),
    (
        "observation_json",
        "object",
        "",
        "",
        "Complete observation of the screenshot in the observation contract (version in "
        "observation_schema_version), as JSON text, with real player names replaced by pseudonyms.",
        "Observation complète de la capture selon le contrat d'observation (version dans "
        "observation_schema_version), en texte JSON, avec les vrais noms de joueurs remplacés par des pseudonymes.",
    ),
    (
        "observation_schema_version",
        "string",
        "",
        "2.0|2.1",
        "Version of the observation contract. 2.1 added the counters; a 2.0 observation has unknown counters.",
        "Version du contrat d'observation. La 2.1 a ajouté les compteurs ; une observation 2.0 a des compteurs "
        "inconnus.",
    ),
    (
        "annotator",
        "string",
        "",
        "",
        "Name of the vision-language model that read the screenshot first (the tool used is given in the "
        "documentation).",
        "Nom du modèle de vision et de langage qui a lu la capture en premier (l'outil utilisé est donné dans la "
        "documentation).",
    ),
    (
        "corrected_by",
        "string",
        "",
        "",
        "Correction trace that replaced the first reading, when there is one; the original reading is kept apart.",
        "Trace de correction qui a remplacé la première lecture, s'il y en a une ; la lecture d'origine est "
        "conservée à part.",
    ),
    (
        "corrector",
        "string",
        "",
        "",
        "Name of the model that wrote the correction named in corrected_by.",
        "Nom du modèle qui a écrit la correction nommée dans corrected_by.",
    ),
    (
        "observation_review_status",
        "string",
        "",
        "proposed_pending_human_review",
        "Review status of the observation: a sample was checked by hand (see the documentation), not each one.",
        "Statut de relecture de l'observation : un échantillon a été vérifié à la main (voir la documentation), "
        "pas chaque observation.",
    ),
    (
        "unit_end_boundary",
        "integer",
        "",
        "0|1",
        "Target of the end-of-game detector: 1 when a game ended between the previous screenshot and this one, "
        "placed on the first screenshot that proves the end. Empty on the first screenshot of a session.",
        "Cible du détecteur de fin de partie : 1 quand une partie s'est terminée entre la capture précédente et "
        "celle-ci, placée sur la première capture qui prouve la fin. Vide pour la première capture d'une session.",
    ),
    (
        "boundary_applicable",
        "boolean",
        "",
        "",
        "Whether unit_end_boundary may be learnt and scored here: false on the first screenshot of a session and "
        "on the intervals judged uncertain (see uncertain_reason).",
        "unit_end_boundary peut-il être appris et évalué ici : false pour la première capture d'une session et "
        "pour les intervalles jugés incertains (voir uncertain_reason).",
    ),
    (
        "uncertain_reason",
        "string",
        "",
        "",
        "Why the interval is masked, when boundary_applicable is false for that reason (text in French).",
        "Pourquoi l'intervalle est masqué, quand boundary_applicable est false pour cette raison (texte en français).",
    ),
    (
        "current_unit_id",
        "string",
        "",
        "",
        "Game (unit) this screenshot belongs to, key of units.csv with session_id; empty outside a game.",
        "Partie (unit) à laquelle appartient la capture, clé de units.csv avec session_id ; vide hors partie.",
    ),
    (
        "ended_unit_id",
        "string",
        "",
        "",
        "Game whose end this screenshot establishes, when unit_end_boundary is 1.",
        "Partie dont cette capture établit la fin, quand unit_end_boundary vaut 1.",
    ),
    (
        "unit_start_boundary",
        "integer",
        "",
        "0|1",
        "Target of the start-of-game detector: 1 on the first gameplay screenshot of a game whose HUD is readable "
        "(score, clock, lap, place, lives, players left). A game already running on the first screenshot of a "
        "session starts there.",
        "Cible du détecteur de début de partie : 1 sur la première capture de jeu d'une partie dont le HUD est "
        "lisible (score, chrono, tour, place, vies, joueurs restants). Une partie déjà en cours sur la première "
        "capture d'une session commence sur cette capture.",
    ),
    (
        "started_unit_id",
        "string",
        "",
        "",
        "Game that starts on this screenshot, when unit_start_boundary is 1.",
        "Partie qui commence sur cette capture, quand unit_start_boundary vaut 1.",
    ),
    (
        "billing_mode",
        "string",
        "",
        "per_game|time_based|not_billed",
        "Second target: per_game (inside a game billed per game), time_based (game or mode without an end of "
        "game, billed by time), not_billed (menus, loading, home screen, idle).",
        "Seconde cible : per_game (dans une partie facturée à la partie, « partie » dans les étiquettes), "
        "time_based (jeu ou mode sans fin de partie, facturé au temps, « temps »), not_billed (menus, chargements, "
        "accueil, temps mort, « hors_jeu »).",
    ),
    (
        "label_review_status",
        "string",
        "",
        "human_verified",
        "Review status of the labels: every game end and every time-billed segment was checked by hand.",
        "Statut de relecture des étiquettes : chaque fin de partie et chaque passage au temps ont été vérifiés à "
        "la main.",
    ),
    (
        "label_confidence",
        "number",
        "",
        "0 to 1",
        "Confidence given to the end of game when unit_end_boundary is 1; 1 elsewhere; empty on the first "
        "screenshot of a session.",
        "Confiance donnée à la fin de partie quand unit_end_boundary vaut 1 ; 1 ailleurs ; vide pour la première "
        "capture d'une session.",
    ),
]

SESSIONS = KEYS[:1] + [
    (
        "frame_count",
        "integer",
        "",
        "",
        "Number of screenshots in the session.",
        "Nombre de captures dans la session.",
    ),
    (
        "duration_s",
        "number",
        "s",
        "",
        "Time from the first to the last screenshot of the session (monotonic clock).",
        "Temps entre la première et la dernière capture de la session (horloge monotone).",
    ),
    (
        "capture_interval_min_s",
        "number",
        "s",
        "",
        "Shortest interval requested between two screenshots (random intervals).",
        "Plus court intervalle demandé entre deux captures (intervalles aléatoires).",
    ),
    (
        "capture_interval_max_s",
        "number",
        "s",
        "",
        "Longest interval requested between two screenshots.",
        "Plus long intervalle demandé entre deux captures.",
    ),
    (
        "image_width",
        "integer",
        "px",
        "",
        "Width of the captured images.",
        "Largeur des images capturées.",
    ),
    (
        "image_height",
        "integer",
        "px",
        "",
        "Height of the captured images.",
        "Hauteur des images capturées.",
    ),
    (
        "jpeg_quality",
        "integer",
        "",
        "1 to 100",
        "JPEG quality setting of the captured images.",
        "Réglage de qualité JPEG des images capturées.",
    ),
    (
        "games",
        "string",
        "",
        "",
        "Game families seen in the session, separated by |, in order of first appearance.",
        "Familles de jeux vues dans la session, séparées par |, dans l'ordre de première apparition.",
    ),
    (
        "unit_count",
        "integer",
        "",
        "",
        "Number of games (units) in the session, including one still running when the capture stopped.",
        "Nombre de parties (units) dans la session, y compris une partie encore en cours à l'arrêt de la capture.",
    ),
    (
        "boundary_count",
        "integer",
        "",
        "",
        "Number of game ends (unit_end_boundary = 1) in the session.",
        "Nombre de fins de partie (unit_end_boundary = 1) dans la session.",
    ),
    (
        "start_count",
        "integer",
        "",
        "",
        "Number of game starts (unit_start_boundary = 1) in the session.",
        "Nombre de débuts de partie (unit_start_boundary = 1) dans la session.",
    ),
    (
        "time_segment_count",
        "integer",
        "",
        "",
        "Number of time-billed segments in the session.",
        "Nombre de passages facturés au temps dans la session.",
    ),
    (
        "annotators",
        "string",
        "",
        "",
        "Models that wrote the observations of the session (first readings and corrections), separated by |.",
        "Modèles qui ont écrit les observations de la session (premières lectures et corrections), séparés par |.",
    ),
    (
        "validation_status",
        "string",
        "",
        "human_verified",
        "Review status of the session's boundaries and time segments.",
        "Statut de relecture des frontières et des passages au temps de la session.",
    ),
    (
        "capture_program_sha256",
        "string",
        "",
        "",
        "SHA-256 of the capture program that ran on the device.",
        "Empreinte SHA-256 du programme de capture qui tournait sur le boîtier.",
    ),
]

UNITS = KEYS[:1] + [
    (
        "unit_id",
        "string",
        "",
        "",
        "Game (unit) identifier, unique within its session (U01, U02...).",
        "Identifiant de la partie (unit), unique dans sa session (U01, U02...).",
    ),
    (
        "game",
        "string",
        "",
        "",
        "Game played, as written by the annotator who placed the boundaries.",
        "Jeu joué, tel qu'écrit par l'annotateur qui a placé les frontières.",
    ),
    (
        "game_family",
        "string",
        "",
        "",
        "Stable game name, as in observations.csv.",
        "Nom stable du jeu, comme dans observations.csv.",
    ),
    (
        "description",
        "string",
        "",
        "",
        "Short description of the game (text in French).",
        "Courte description de la partie (texte en français).",
    ),
    (
        "first_frame",
        "integer",
        "",
        "",
        "First screenshot of the game.",
        "Première capture de la partie.",
    ),
    (
        "last_frame",
        "integer",
        "",
        "",
        "Last screenshot of the game still in play or on its result.",
        "Dernière capture de la partie encore en jeu ou sur son résultat.",
    ),
    (
        "start_established_at",
        "integer",
        "",
        "",
        "Start of the game: its first gameplay screenshot whose HUD is readable (first_frame or a later one).",
        "Début de la partie : sa première capture de jeu dont le HUD est lisible (first_frame ou une capture "
        "suivante).",
    ),
    (
        "start_status",
        "string",
        "",
        "rule|author",
        "Who placed the start: the written rule, or the author when they corrected it.",
        "Qui a placé le début : la règle écrite, ou l'auteur quand il l'a corrigé.",
    ),
    (
        "start_evidence",
        "string",
        "",
        "",
        "What proves the start: the HUD values read, or the decision of the author (text in French).",
        "Ce qui prouve le début : les valeurs du HUD lues, ou la décision de l'auteur (texte en français).",
    ),
    (
        "end_established_at",
        "integer",
        "",
        "",
        "First screenshot that proves the end (last_frame or a later one); empty for a game still running when "
        "the capture stopped.",
        "Première capture qui prouve la fin (last_frame ou une capture suivante) ; vide pour une partie encore en "
        "cours à l'arrêt de la capture.",
    ),
    (
        "termination",
        "string",
        "",
        "completed|incomplete_at_capture_end",
        "How the game ended. A restarted or abandoned game counts as completed.",
        "Comment la partie s'est terminée. Une partie recommencée ou abandonnée compte comme terminée.",
    ),
    (
        "counted",
        "boolean",
        "",
        "",
        "Whether the game counts as a game played; empty for a game still running when the capture stopped.",
        "La partie compte-t-elle comme partie jouée ; vide pour une partie encore en cours à l'arrêt de la capture.",
    ),
    (
        "final_score_seen",
        "string",
        "",
        "",
        "Final score or result seen on screen (text in French).",
        "Score final ou résultat vu à l'écran (texte en français).",
    ),
    (
        "label_confidence",
        "number",
        "",
        "0 to 1",
        "Confidence given to the end of the game.",
        "Confiance donnée à la fin de la partie.",
    ),
    (
        "evidence",
        "string",
        "",
        "",
        "Screenshots that prove the start and the end of the game, and why (text in French).",
        "Captures qui prouvent le début et la fin de la partie, et pourquoi (texte en français).",
    ),
]

TIME_SEGMENTS = KEYS[:1] + [
    (
        "first_frame",
        "integer",
        "",
        "",
        "First screenshot of the time-billed segment.",
        "Première capture du passage facturé au temps.",
    ),
    (
        "last_frame",
        "integer",
        "",
        "",
        "Last screenshot of the segment.",
        "Dernière capture du passage.",
    ),
    (
        "game",
        "string",
        "",
        "",
        "Game played during the segment.",
        "Jeu joué pendant le passage.",
    ),
    (
        "game_family",
        "string",
        "",
        "",
        "Stable game name, as in observations.csv.",
        "Nom stable du jeu, comme dans observations.csv.",
    ),
    (
        "reason",
        "string",
        "",
        "",
        "Why the segment is billed by time: game or mode without an end of game (text in French).",
        "Pourquoi le passage est facturé au temps : jeu ou mode sans fin de partie (texte en français).",
    ),
]

SPLITS = KEYS[:1] + [
    (
        "fold",
        "integer",
        "",
        "1 to 5",
        "Cross-validation fold of the session. A session lies entirely in one fold.",
        "Pli de validation croisée de la session. Une session est entière dans un seul pli.",
    ),
]

TABLES = {
    "observations": OBSERVATIONS,
    "sessions": SESSIONS,
    "units": UNITS,
    "time_segments": TIME_SEGMENTS,
    "splits": SPLITS,
}


def names(table: str) -> list[str]:
    return [column[0] for column in TABLES[table]]
