# Conventions d'annotation

Comment remplir le contrat d'observation 2.1 pour chaque jeu déjà rencontré. Ces conventions ont été appliquées à
tous les lots existants : une nouvelle annotation doit rester cohérente avec elles. Le contrat lui-même (champs et
valeurs permises) est décrit dans [`docs/contract/README.md`](../contract/README.md) ; le prompt du professeur est
dans `src/playend/contract/prompts/`.

| Genre | Jeux | Fichier |
|---|---|---|
| Football | EA Sports FC 26 et 27 | [football.md](football.md) |
| Combat | Mortal Kombat 1, Naruto Storm Connections, Dragon Ball Sparking! ZERO, Dragon Ball FighterZ, Demon Slayer, Tekken 8, UFC 5, Brawlhalla, J-Stars Victory VS+ | [combat.md](combat.md) |
| Battle royale | Fortnite, Call of Duty: Warzone | [battle-royale.md](battle-royale.md) |
| Course | Beach Buggy Racing 2 | [course.md](course.md) |
| Mission et monde ouvert | Genshin Impact, Red Dead Redemption 2, God of War, Assassin's Creed Origins | [mission.md](mission.md) |

Pour placer les fins de partie, lire d'abord [ANALYSE_FIN_DE_PARTIE_PAR_JEU.md](ANALYSE_FIN_DE_PARTIE_PAR_JEU.md) :
principes généraux, puis une fiche par jeu.

## Règles communes

### Participants : seulement le texte écrit sur l'image

Règle de l'utilisateur, fixée à la validation du 2026-10-03. Un participant n'est jamais un nom déduit d'un logo, d'un
écusson, d'un maillot, d'un visage, d'une liste de joueurs, d'un nom de tactique (« FRANCE DÉFAUT ») ou d'une image
voisine (écran de chargement, bandeau vu plus tôt). Si aucun nom n'est écrit : `participants.primary = []` et
`count_visible` = nombre de participants visibles (`null` si on ne peut pas les compter). Exemples : Brawlhalla en
combat (portraits seuls), FC « Choix des tireurs de pénalty » et écrans de tactique (écussons seuls).

Étiquettes de manette (décision de l'utilisateur du 2026-10-13, tour `data/validation/conventions_2026-10-13`) : « Joueur 1 », « J2 », « P1 » ne sont pas des participants ; elles restent
dans la note. Elles ne changent pas d'un match à l'autre et alternent avec les noms d'équipe.

### Compteurs secondaires (`secondary_counters`)

À remplir sur chaque nouvelle image, avec `cnt(kind, side, value, total=None, label=None)` de
`playend.annotation.presets` (règles complètes : `src/playend/contract/counter_rules.txt`). `[]` veut dire « HUD
inspecté, aucun compteur » ; `null` veut dire « inventaire impossible » (HUD caché). On n'y met que ce qui mesure ce
qui reste avant la fin :

- battle royale : `players_remaining`/`field` (Fortnite, Warzone ; `fnsplit` le fait) et `teams_remaining`/`field`
  (Warzone) ;
- Brawlhalla : `lives`/`a` et `lives`/`b` (stocks sur les portraits) ; Dragon Ball Sparking! ZERO : barres de vie
  restantes, en `lives` ;
- combat : `target`/`field` = nombre d'emplacements de rounds par côté (MK1 et Naruto : 2, déjà mis par `mk` et
  `na`) ; Tekken : `series` du côté du « WINS n » (label « WINS ») ;
- Call of Duty multijoueur : `target`/`field` = limite de score affichée ; Rocket League : `series` ;
- foot, UFC, menus, PS5, noir, missions : `[]` (déjà mis par les préréglages).

Jamais : éliminations, dégâts, combos, vie, argent, XP, niveaux.

### Libellé du mode

Toujours écrire dans la lecture libre (`obs`) le libellé du mode ou du format affiché (« Combat principal », « Durée
5 min par période », « 3 tours »). Il n'y a pas de champ `mode_label` pour le premier entraînement du GRU (décision du
2026-10-02).

### Écrans hors jeu

Accueil PS5 et PS4 (préréglage `ps5_home`), menus, écran noir : l'heure système affichée n'est pas un chrono.
`period = "none"` pour les menus, `"unknown"` pour l'écran noir.

- Accueil de la PS5 (décision de l'utilisateur du 2026-10-13, tour `data/validation/conventions_2026-10-13`) : titre du jeu `null`, même quand une vignette de jeu est mise en avant ; le nom du jeu
  va dans la note. Aucun jeu n'est en cours.
- Surcouche pendant une partie (« Manette déconnectée », centre de contrôle de la PS5, « Voulez-vous quitter ? ») :
  `paused / pause`, texte recopié dans la note. Hors partie : `menu` (2026-10-13).

## Nouveau jeu

1. Ajouter un préréglage et une fonction dans le module de son genre (`src/playend/annotation/presets/`), en suivant
   le prompt du contrat.
2. Écrire ses conventions dans le fichier de son genre (ou en créer un), avec les décisions de l'utilisateur datées.
3. Si un zoom particulier aide, ajouter un module dans `src/playend/annotation/zoom/`.

Pistes déjà réfléchies pour les genres pas encore rencontrés (voir le §4 de l'analyse des fins de partie) :

- course : tour « 2/3 » → `progress lap`, place « 3/16 » → `position`, temps de course → `clock`, `period = none` ;
- tennis : points, jeux, sets et tie-break → `score points` et `additional_scores` ;
- basket : Q1 à Q4 et prolongation → `period quarter`, chronomètre des tirs → `secondary_timers` ;
- Rocket League : prolongation « +0:23 » → `period overtime` ;
- boxe : comme l'UFC ; Street Fighter 6 : comme Mortal Kombat 1 ;
- missions (The Last of Us, GTA, tout jeu de mission presque sans fin) : voir [mission.md](mission.md).

## Outils de lecture

`python -m playend.annotation.zoom OUTIL session_<id> A-B` (liste complète avec `--help`, planches dans
`build/zoom/`) :

- `grid` et `mini` : planches 3×3 et 6×6, pour reconnaître le jeu et le type d'écran ;
- `crop` : le même recadrage pour beaucoup d'images (`--box X0 Y0 X1 Y1 --scale 2`) ;
- `names` : noms des deux combattants ;
- un outil par jeu, dont les zones sont décrites dans son module `src/playend/annotation/zoom/<jeu>.py` :
  `mortal-kombat`, `tekken`, `fortnite` (`--layout split`, `solo`, `multi`, `og`), `ufc`, `beach-buggy`, `jstars`,
  `dragon-ball`, `warzone`.

Pour les frontières : `python -m playend.boundaries.timeline` (une ligne par observation) et
`python -m playend.boundaries.condense` (une ligne par suite d'observations semblables).
