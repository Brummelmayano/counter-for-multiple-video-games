# Football : EA Sports FC

Règles communes (participants, compteurs secondaires, écrans hors jeu) : [README.md](README.md). Pour le foot,
`secondary_counters = []`.

Les participants s'écrivent comme l'écran les écrit : le bloc du score de FC 26 donne des sigles (`PSG`, `MCI`, `FRA`),
qu'on ne développe jamais en nom complet ; le nom entier vient seulement d'un bandeau ou d'un menu qui l'écrit (encart
du menu de pause, bandeau des habillages Ligue 1, LaLiga et Ligue des champions). Sur l'écran « RÉSULTATS », « Joueur 1 »
et « Joueur 2 » ne sont pas des participants. Relecture du 2026-10-15, trace `20261015_56`.

## Jeu ou cinématique

Décision de l'utilisateur du 2026-10-14, tour `data/validation/cinematiques_2026-10-14`. Ces règles valent pour tous
les habillages.

- Bandeau du score affiché → `gameplay`, phase `active`, quel que soit le cadrage : gros plan, célébration,
  changement de joueur. Le score et le chrono s'y lisent comme sur une vue de jeu.
- Sans bandeau, une vue de match qui montre le radar, le nom ou le marqueur du joueur contrôlé, ou les consignes
  « TACT. COUP DE PIED ARRÊTÉ » d'un coup de pied arrêté → `gameplay`, phase `active`, score et chrono `null`.
- Ni bandeau, ni radar, ni texte de jeu (gros plan, célébration, ralenti, présentation des équipes) → `cutscene`.
  Les icônes « R2 » qui servent à passer la scène ne sont pas un HUD de jeu. L'encart du buteur (tirs et buts du
  joueur) n'est pas un score. Phase `unknown` quand rien sur l'image ne la donne ; `pre_game` quand un texte
  d'introduction est écrit (« Maintenir pour l'intro complète »), `post_game` pour la remise du trophée.
- L'écran géant du stade n'est pas le HUD : son score et son chrono ne sont pas notés.
- Fenêtre « Choix du camp », « Voulez-vous quitter ? » ou fenêtre de la PS5 par-dessus un match → surcouche :
  `paused / pause` (règle commune du [README.md](README.md)).
- Vue large du coup d'envoi, joueurs en place, sans bandeau, radar ni marqueur de joueur → `cutscene`, phase
  `unknown`. Le logo « LIVE » de la diffusion n'est pas un HUD de jeu.

## Bandeau du score en bas de l'écran

Décision de l'utilisateur du 2026-10-14. Le bandeau qui s'affiche en bas au coup d'envoi et après un but (FC 26 :
sigles, logos et photo du buteur ; Ligue 1, LaLiga et Ligue des champions dans leurs habillages) donne le score : on
le lit comme le bloc du haut, avec les noms d'équipes quand ils sont écrits en entier. La minute du buteur (`80′`)
n'est jamais le chrono, et ce bandeau n'a pas de chrono. Chiffres en train d'apparaître et coupés au point d'être
ambigus (un 0 dont on ne voit que le haut peut être un 3 ou un 8) → score `null`.

## EA Sports FC 26, habillage standard

Préréglages `play` et `pause` de `playend.annotation.presets`.

- Score et chrono dans le bloc en haut à gauche.
- `+1` ou `+2` = temps additionnel annoncé, non converti en secondes.
- Un compteur `+1:03` sous un chrono figé va dans `secondary_timers` (kind `other`, secondes `null`).
- Les minutes de but (`74′`) ne sont jamais le chrono.
- `PR` après le chrono → `period.type = "overtime"`.
- Le libellé `PÉNALTYS` → `period.type = "other"`, et le score compte les tirs au but réussis.
- `(1 | 3)` = agrégat d'un aller-retour : en note seulement, ni score ni compteur `series` (confirmé par l'utilisateur le
  2026-10-05).
- Les notes de joueurs et les statistiques ne sont pas des scores.
- Un match simulé (Carrière : « Simuler match ») n'est pas joué, donc pas compté.
- Menus de match (décision de l'utilisateur du 2026-10-13, tour `data/validation/conventions_2026-10-13`) : première ligne « REPRENDRE MATCH » → `paused / pause`, chrono et score de l'encart notés,
  même à 90:00 ; première ligne « QUITTER LE MATCH », ou « Interview d'après-match » → `post_game / menu`, sans
  résultat. « Choix des équipes » → `pre_game / team_select`, participants vides tant que les équipes défilent.

## EA Sports FC 27 et habillages de diffusion de FC 26

Préréglages `fc27`, `laliga`, `fcload` et `fcm27`.

- Bloc vertical en haut à gauche : l'équipe du haut est A.
- Habillages de diffusion : LaLiga (logo, chrono dessous, scores à droite), Ligue 1 (logo L1) et Ligue des champions
  (barre « chrono | A a | b B »).
- Un encart « COMMENTAIRES », « POSSESSION » ou « BUTEUR » qui cache les chiffres → score `null`.
- Chrono au-delà de 90 sans « PR » lisible → `period unknown`.
- Écran « Choix des tireurs de pénalty » → `period other`, score `null`, participants `[]` (écussons seuls).
