# Jeux de combat

Règles communes (participants, compteurs secondaires, écrans hors jeu) : [README.md](README.md). Les marqueurs de
rounds gagnés vont dans le score (`rounds_won`) ; le nombre d'emplacements par côté va dans `secondary_counters`
(`target`/`field`). Les modes sans fin (entraînement avec `∞`) sont facturés au temps : aucune frontière.

## Règles communes aux jeux de combat (décision de l'utilisateur du 2026-10-13, tour `data/validation/conventions_2026-10-13`)

- Écran d'après-combat avec un menu « Revanche / Choix du personnage… » (MK1, Tekken et les autres) :
  `post_game / menu`. Un résultat seulement si un texte de victoire est écrit ; le nom du combattant écrit en grand
  n'est pas un vainqueur écrit.
- « K.O. » ou « X GAGNE » pendant le combat, HUD visible : fin d'une manche, phase `active`, aucun résultat de match.
  Le résultat de match se lit sur l'écran d'après-combat, ou quand le score atteint le nombre de manches gagnantes.
- Gros plan ou pose sans HUD ni texte : `cutscene`, phase `unknown`. Jamais `active / gameplay`, jamais une phase
  devinée d'après l'image voisine.
- Barres de vie ou chrono du combat affichés → `gameplay`, phase `active`, même pendant une attaque spéciale ou un
  coup fatal (décision de l'utilisateur du 2026-10-14, tour `data/validation/cinematiques_2026-10-14`). Les valeurs
  cachées par la scène restent `null`.
- Bannière « ROUND n » écrite : `period round`, numéro n ; « FINAL ROUND » : `period round`, numéro `null`.
- Écran de sélection : les noms des combattants ne sont pas des participants, car les joueurs peuvent encore en
  changer (refus de l'utilisateur du 2026-10-13).
- Écran de choix du décor (vignettes d'arènes et nom du décor, ou grille des niveaux) : `pre_game / character_select`,
  comme un écran de sélection ; il sépare deux combats (décision de l'utilisateur du 2026-10-13).

## Mortal Kombat 1

- Deux marqueurs de rounds de chaque côté du chrono → `rounds_won` ; `target` 2 (mis par le préréglage `mk`).
- En entraînement, le `∞` donne `clock = "∞"`, `mode_duration = "continuous"` et un score `null` (aucun emplacement).
- « FATAL BLOW » et « KONTRE » ne sont pas des résultats.
- Écran « FIGHT » sans emplacements de manches dessinés : score `null`, pas 0–0 (2026-10-13).
- En combat miroir, distinguer les participants par le Kaméo (`"Johnny Cage (Kaméo Tremor)"`).
- Zoom : `zoom mortal-kombat`.

## Naruto Storm Connections

- Deux emplacements sous le chrono de chaque côté : pastille orange = round gagné, grise = vide ; `target` 2 (mis
  par le préréglage `na`).

## Dragon Ball Sparking! ZERO

- Aucun marqueur de round → score `null`. Les nombres sous les portraits sont des points de compétence.
- `∞` seulement en début de combat. « Victoire » → `result win`, `winner null`.
- Barres de vie restantes (décision de l'utilisateur du 2026-10-04) : une rangée de 7 petits blocs près de chaque
  portrait, au-dessus de la barre de vie. Selon le guide officiel de Bandai Namco, « le nombre de barres de vie
  restantes est indiqué dans le coin gauche ». Les blocs allumés (verts, jaunes quand la vie est basse) sont les
  barres restantes. Sur chaque image de combat : `cnt("lives", "a", n)` (gauche) et `cnt("lives", "b", n)` (droite),
  `total` `null` (les emplacements vides sont la capacité de l'écran). Avec `dbf(i, hp=(a, b))` ; blocs cachés
  → `hp=None` (compteurs `null`). Zoom : `zoom dragon-ball`. C'est l'indice le plus proche du KO, donc de la fin du
  combat.
- Frontières : une hausse des barres ne prouve pas une relance. En combat en équipe, le combattant suivant entre avec
  ses barres pleines, et un combattant revenu de la réserve peut avoir rechargé. Seuls l'écran noir, l'introduction,
  le `∞` ou le menu « Réessayer » établissent un nouveau combat (f8c284 U17, 2026-10-04).

## Dragon Ball FighterZ

- Préréglage `dbfz`. Combat 3 contre 3, `∞` à la place du chrono, aucun marqueur de manche → score `null`.
- Fin = écran « RÉSULTAT — VICTOIRE Équipe … ».

## Demon Slayer – Hinokami Chronicles

- Préréglage `kny`. Deux losanges sous la barre de chaque côté du chrono (jaune = manche gagnée) → `rounds_won`,
  `target` 2. Chrono de 99.

## Tekken 8

- Deux ou trois points de rounds gagnés près des barres de vie → `rounds_won`, et le nombre d'emplacements →
  `target`. Chrono de 60 s.
- « WINS n » en bas = victoires consécutives → `series` du côté concerné (label « WINS »), jamais dans le score.
- Frontières : « WINS n », sous le vainqueur de la série, change à chaque fin de match. C'est l'indice le plus fiable,
  plus que les pastilles (session 078643). Zoom : `zoom tekken`.

## UFC 5

- Aucun marqueur de rounds gagnés → score `null`. Le chrono du round descend de 5:00 à 0:00 et repart à chaque round :
  ce n'est pas une fin.
- Participants : les noms en haut à gauche et à droite, au-dessus des barres d'endurance (gauche = A, droite = B),
  jamais les couleurs du short (bandeau du bas « COULEUR DU SHORT », par exemple « VERT | UFC 4:48 R1 | NOIR »). Les
  lire sur chaque image de combat, zoom `zoom ufc`.
- En haut au centre, selon le manuel officiel d'EA (UFC 4, même disposition dans UFC 5) : « The Grapple Advantage meter
  appears at the top center of the screen, as well as the time left in the round and the current and remaining
  rounds ». La barre rouge et bleue à graduations est l'avantage de grappling : ni un score ni un chrono.
- Round en cours et rounds restants : la rangée de segments sous cette barre (segments allumés = round en cours et
  rounds passés, éteints = rounds restants ; 5 segments pour un combat en 5 rounds) → `period.type = "round"`,
  `number` = segments allumés, `total` = nombre de segments, seulement s'ils sont clairement comptables. Zoom :
  `zoom crop session_<id> A-B --box 540 25 740 100 --scale 2.5`. Sur l'autre habillage, le badge « R1 » donne
  `number`.
- Bandeau du bas « NOM | UFC 4:27 R1 | NOM » au début de chaque round ; « COULEUR DU SHORT » avec un chrono à
  4:3x–4:4x en R1 = combat lancé ou relancé.
- Écran d'après-combat : « KO / TKO / SOUMISSION / DÉCISION » avec « R3 01:54 », carte des juges et menu
  *Revanche / Statistiques combat / Changer de combattants / Voir rediffusion / Quitter* → `post_game`,
  `result.visible = true` et `outcome_type` selon le texte (vainqueur seulement s'il est écrit). La carte des juges
  (10–9…) n'est pas `score.a/b`.
- Frontières : la fin d'un combat est établie par ce menu ou cet écran, ou par un changement de combattants, jamais
  par un chrono à 0:00 seul (le round suivant peut commencer).

## Brawlhalla

- Stocks restants sur les portraits → `lives` `a` et `b`, jamais dans le score. Participants `[]` en combat
  (portraits seuls).
- Podium « 1st / 2nd » avec SCORE → résultat.
- L'arène d'attente pendant « Recherche de joueurs… » n'est pas un match.

## J-Stars Victory VS+

Préréglages `js` et `jsm` ; zoom `zoom jstars`. Combat en arène, 1 contre 1 (avec soutien) ou 2 contre 2.

- Jauge de victoire en haut : 3 segments par côté (rouge à gauche = A, bleu à droite = B), allumés depuis le centre
  → `score points` ; `target`/`field` 3.
- Minuteur « Temps 279 » en bas à droite → chrono (secondes) ; « 01.63 » en fin de combat → affiché, non converti.
- Participants : le nom du combattant contrôlé écrit en bas à gauche (A) et celui de l'adversaire verrouillé, écrit
  au-dessus de sa barre (B) quand il est à l'écran ; les noms d'alliés flottants (barre rouge) vont dans
  `visible_entities`.
- « KO ! » d'un personnage = un segment, pas un résultat ; « Terminé » → `post_game`, résultat `other` ;
  « Résultats — Victoire ! » → `win`, `winner null`.
- Le mode histoire « Aventure-J » (carte du monde en bateau, dialogues, quêtes) est facturé au temps ; ses combats
  sont des parties, comme ceux du « Combat libre » (décision de l'utilisateur du 2026-10-13, qui remplace la règle
  « à confirmer » du 2026-10-04).
