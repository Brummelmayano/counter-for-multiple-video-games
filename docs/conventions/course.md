# Course

Règles communes (participants, compteurs secondaires, écrans hors jeu) : [README.md](README.md).

## Beach Buggy Racing 2

Préréglages `bbr`, `bbrres` et `bbrm` ; zoom `zoom beach-buggy session_<id> A-B --layout 3|4|2`. Premier jeu de
course, vu dans la session fdb79549 : karts en écran partagé, jusqu'à 4 vues (3 dans fdb79549 : une vue en haut, deux
en bas).

- `game.type = "racing"`, `mode = "race"`, `period = "none"`, aucun chrono de course affiché (`clock` non visible),
  score `null`.
- Position : le contrat n'a qu'un champ `position`, pour « le coureur contrôlé quand il est identifiable ». En écran
  partagé (plusieurs joueurs), la position reste vide et la place « N/8 PLACE » de chaque vue va en note (décision de
  l'utilisateur du 2026-10-04, trace `20261004_22`). En vue unique, position = sa place, `total` 8.
- Tour : le libellé central « TOUR n » → `progress lap`, `total` `null` (aucun « /3 » affiché) ; chiffre caché par
  les icônes de pilotes → `progress` `null`.
- Les places et les tours ne vont jamais dans `secondary_counters` (`[]`).
- « Fin de la course ! 16 » (délai avant la fin forcée) → `secondary_timers` kind `other`, un par vue qui l'affiche.
  Gros chiffre de départ « 3 / 1 » → `pre_match`, phase `pre_game`.
- Pilotes dont le nom n'est pas écrit dans leur vue → `participants = []`, `count_visible` = nombre de vues.
- Tableau « ÉVÉNEMENT n sur 8 » → `post_game/result`, `result other`, vainqueur = le premier écrit, participants =
  les noms du tableau, `progress stage n/8`. Classement cumulé (« Suivant : ÉVÉNEMENT n ») →
  `post_game/scoreboard`, sans résultat : la course est finie (décision de l'utilisateur du 2026-10-13, qui
  remplace `intermediate`). Podium final → `podium`, résultat. Le bandeau d'arrivée « 2e place »
  dans une vue n'est pas un résultat.

### Comptage et fin de partie

- Une course = une partie, et non le championnat de 8 épreuves (décision de l'utilisateur du 2026-10-04).
- Fin : le tableau, le classement ou le menu ; à défaut, « TOUR 1 » après un tour 3, confirmé par l'image suivante.
- Une course relancée compte comme une partie complète.

## Autres jeux de course

Pas encore rencontrés. Piste : tour « 2/3 » → `progress lap`, place « 3/16 » → `position`, temps de course →
`clock`, `period = none` (voir [README.md](README.md)).
