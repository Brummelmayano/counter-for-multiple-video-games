# Battle royale

Règles communes (participants, compteurs secondaires, écrans hors jeu) : [README.md](README.md). Les joueurs et
équipes restants vont dans `secondary_counters` ; les éliminations restent en note.

## Fortnite

- `game.type = "other"`, `period = "none"`, score `null`.
- Minuteurs : icône de tempête ou de chronomètre → `storm_phase` ; icône de coche → `unknown`.
- Comptes à rebours `pre_match`, avec des secondes `null` quand le format est « 16 s » : « EN ATTENTE DE JOUEURS
  16 s », « BUS DE COMBAT LANCEMENT DANS 0 s », « OUVERTURE DES PORTES DANS 1 s », « Recherche de serveur 0:25 ».
- « EXPIRATION DE LA CARTE DE RÉTABLISSEMENT DANS 250 s » → `respawn`.
- « MODE SPECTATEUR — joueur » (décision de l'utilisateur du 2026-10-13, tour `data/validation/conventions_2026-10-13`) : si l'escouade joue encore (un coéquipier en vie), phase `active`, écran
  `gameplay` ; si toute l'escouade est éliminée, `post_game`. Le joueur regardé est noté.
- Mode de jeu : le libellé affiché reste tel quel ; il est normalisé dans le calcul des variables (Battle Royale,
  Zéro construction, île créative), pas dans les observations (2026-10-13).
- « Victoire Royale » → `result win`, et `position.current = 1` si « #1 » est visible. « VOTRE PLACE : #N » →
  `result other` et `position.current = N`, comme dans les lots de Luna.
- Écran partagé : un minuteur par vue (préréglage `fnsplit`), zoom `zoom fortnite --layout split`. En mode
  spectateur, noter le joueur regardé.
- Fortnite OG en écran partagé (session ff1c72) : les compteurs sont sur une ligne sous chaque minicarte (minuteur,
  joueurs restants, éliminations), zoom `zoom fortnite --layout og`. Une disposition qui change dans la session :
  `--layout multi`.
- Vue unique (préréglage `fnsolo`, zoom `zoom fortnite --layout solo`) et îles créatives (`fncrea`) : le classement
  individuel et « 2/12 en attente » ne sont pas des compteurs de fin.

### Comptage

- Écran partagé = une seule partie, même si les deux joueurs n'ont pas le même sort.
- Îles créatives d'arène à réapparition (Super Pit, Scrims…) : facturées au temps (`time_segment`, décision du
  2026-10-02).
- Île d'attente quittée avant le bus : pas une partie (décision du 2026-10-02).

### Fin d'une partie (au niveau de l'équipe)

- C'est une fin : « #1 VICTOIRE ROYALE », « VOTRE PLACE : #N » sur toutes les vues, le récapitulatif de la partie,
  le salon, la recherche de serveur, ou l'île d'attente avec 95 à 100 joueurs après une partie.
- Ce n'est pas une fin : un joueur éliminé qui regarde un coéquipier (il peut être rétabli), une tempête à 0:00, peu
  de joueurs restants.
- La partie commence à l'île d'attente.

## Call of Duty: Warzone

Préréglage `wz` ; zoom `zoom warzone`.

- En haut à droite : icône d'escouade → `teams_remaining`, icône de personne → `players_remaining` ; le compteur à
  l'icône d'avion n'est pas enregistré. Éliminations : en note seulement.
- Badge du cercle → `period stage`. Minuteur du cercle, contrats et redéploiement → `secondary_timers`.
- « Xe place / RÉSUMÉ PARTIE » → `result other` et `position.current`.
- Fin de partie (décision de l'utilisateur du 2026-10-13, tour `data/validation/conventions_2026-10-13`) : « ÉLIMINATION FINALE » ou « DERNIÈRE KILLCAM » → `post_game / other`, résultat non visible ;
  « KILLCAM » avec « RÉAPPARITION DANS n » → la partie continue, `active` ; écrans de progression et de récompenses
  après la partie → `post_game`.
