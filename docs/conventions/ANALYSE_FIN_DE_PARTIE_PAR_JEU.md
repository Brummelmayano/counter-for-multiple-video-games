# Reconnaître la fin d'une partie malgré des captures espacées : analyse par jeu

Analyse du 2026-09-29 (Claude), fondée sur les 4 051 images annotées du jeu de données, les réglages de capture réels et la documentation officielle ou de référence de chaque jeu (sources en fin de document).

**But :** s'assurer que le comptage des parties, donc la facturation, reste juste alors qu'on ne voit qu'une image toutes les 10 à 45 s.

---

## 1. Ce que les captures réelles permettent de voir

Mesures sur les 7 928 intervalles de toutes les sessions :

| Intervalle entre deux captures | Valeur |
|---|---|
| minimum | 10,1 s |
| médiane | **27,7 s** |
| 90e centile | 41,7 s |
| 99e centile | 44,9 s |
| maximum | 270,9 s (0,6 % des intervalles dépassent 45 s) |

Durée d'affichage observée des écrans de fin (images consécutives avec un résultat ou un état `post_game`) :

| Jeu | Séquences de fin vues | Images consécutives (min / médiane / max) |
|---|---|---|
| Fortnite | 10 | 1 / 1 / 2 |
| Tekken 8 | 5 | 1 / 1 / 1 |
| EA Sports FC | 5 | 1 / 2 / 68 |
| Warzone | 7 | 1 / 2 / 73 |
| Dragon Ball Sparking! ZERO | 3 | 1 / 1 / 25 |
| Genshin Impact | 3 | 1 / 1 / 4 |
| UFC 5, Brawlhalla | 1 chacun | 1 |

**Conclusions :**

1. Les événements brefs (« K.O. », coup de sifflet final, « FINISH HIM », bannière de but) durent quelques secondes : ils sont **le plus souvent ratés**.
2. Même les écrans de fin ne sont souvent vus **qu'une seule fois**, parce que les joueurs les passent vite. On ne peut donc pas compter uniquement sur eux : il faut aussi les preuves qui arrivent **après** la fin (menu, sélection, participants différents, compteurs remis à zéro).
3. Aucune partie observée ne tient entre deux captures : une partie dure au minimum environ 1 minute (combat), et de 6 à 25 minutes pour les autres genres. Le risque de « deux fins dans un même intervalle » est donc très faible, mais pas nul pour les jeux de combat avec revanche immédiate (voir §3).

---

## 2. Principe général, valable pour tous les jeux

Trois familles d'indices, par ordre de fiabilité face aux captures espacées :

| Famille | Exemples | Pourquoi c'est robuste |
|---|---|---|
| **A. État affiché en permanence pendant la partie** | score, chrono, round en cours et total, participants, joueurs restants, tours | Visible sur **presque toutes** les images, donc on suit la partie même en ratant des moments. |
| **B. Écrans de fin qui attendent une action** | tableau de résultats, menu Revanche / Rejouer / Quitter, podium, « Votre place #N » | Ils restent affichés tant que le joueur n'agit pas, mais peuvent être passés en quelques secondes. |
| **C. Début de la partie suivante** | chargement, sélection, île d'attente, compteurs remis à zéro, **autres participants** | Toujours présent après une fin : c'est la preuve **a posteriori**. |

**Règle de décision** (le GRU l'apprend, elle n'est pas codée jeu par jeu) :

> Une partie se termine quand un **invariant de continuité est rompu** (A), quand un **écran de fin** apparaît (B), ou quand **la partie suivante commence** (C).
> Jamais sur un événement bref seul, **jamais sur un chrono à 0:00 seul** (round suivant, prolongation, nouvelle phase).
> La décision peut attendre **une observation** (environ 28 s de retard, sans conséquence sur la facturation).

**Invariants de continuité** (ce qui ne peut **pas** arriver au sein d'une même partie) :

| Grandeur | Pendant une partie | Une rupture signifie |
|---|---|---|
| Participants (équipes, combattants, pilotes) | identiques | autre partie |
| Score cumulé (buts, rounds gagnés, sets, jeux) | ne baisse jamais | nouvelle partie (ou recommencement) |
| Chrono de match croissant (foot) | monte | recommencement |
| Chrono de round décroissant (combat, UFC, basket) | baisse **dans** un round, puis repart au round suivant | round suivant **seulement** si le numéro de round augmente de 1 |
| Numéro de période ou de round | ne baisse jamais | nouvelle partie |
| Joueurs ou équipes restants (battle royale) | baisse (petites remontées possibles avec les réapparitions) | grand saut vers le maximum = nouvelle partie |
| Tour en cours (course) | ne baisse jamais | nouvelle course |

**Protection contre les erreurs de lecture du VLM :** une rupture d'invariant qui ne repose que sur **une seule valeur lue** (un chiffre de score, un chrono) doit être confirmée par une **deuxième observation** ou un **deuxième indice** (nouvel écran, participants différents). Sinon, une erreur de lecture fabrique une fausse fin, donc **une partie facturée en trop**.

**Sortie vers la console** (règle appliquée depuis le début, écrite le 2026-10-13 sur décision de l'utilisateur) :
accueil de la console sans reprise du même jeu → la fin se place sur le premier accueil. Si le même jeu reprend
ensuite au même score, ce n'est pas une fin.

**Réglages à imposer dans la salle :** laisser **toujours affichés** les éléments de HUD qui portent ces invariants (voir chaque fiche). Exemples : EA FC « Score Clock : On », UFC « HUD : On », et pas de chrono infini dans les jeux de combat si la partie doit être facturée.

---

## 3. Fiches des jeux déjà capturés

### EA Sports FC (FC 26) — football, 1 055 images
- **Format :** 2 mi-temps réglables de 3 à 20 min (réglage « Durée d'une mi-temps »). Chrono de match croissant de 0 à 90′, avec du temps additionnel. Prolongation (« PR ») jusqu'à 120′, puis tirs au but (label « PÉNALTYS »).
- **Affiché en permanence :** le bloc score en haut à gauche (équipes abrégées, score, chrono). ⚠️ Il peut être désactivé (« Score Clock Off ») : il faut l'imposer à « On ».
- **Fin établie par :**
  - écran « Scores finaux », « VAINQUEUR — Joueur N », menu d'après-match (« Interview d'après-match / Continuer »), conférence de presse en carrière ;
  - **ou**, a posteriori : menus, sélection des équipes, autres équipes, 0–0 avec un chrono bas.
- **Pièges :**
  - la mi-temps : 45:00, puis 46:00, avec les équipes qui changent de côté ;
  - les pauses, ralentis et bandeaux de but (minute de but ≠ chrono) ;
  - la prolongation et les tirs au but ;
  - l'agrégat aller-retour « (1 | 3) » ;
  - un **match simulé** en carrière, qui n'est pas joué.
- **Échantillonnage :** avec des mi-temps de 5 min, un match dure environ 10 min, soit 15 à 25 captures. Le chrono avance de 3 à 7 minutes de jeu entre deux images.
- **Contrat 2.0 :** suffisant (score `goals`, `clock`, `period` overtime/other).
- **Robustesse : élevée.**

### EA Sports UFC 5 — sport de combat, 47 images
- **Format :** 3 rounds, ou 5 pour un combat principal ou pour la ceinture. Chrono de round décroissant de 5:00 à 0:00, qui repart à chaque round.
- **Affiché en permanence, en haut au centre :** selon le manuel EA, « Grapple Advantage meter […] the time left in the round and the current and remaining rounds ». La rangée de segments donne le **round en cours et le total** (1 sur 5, 2 sur 5, 3 sur 5 observés dans Prates–Brady). Sur un autre habillage, le badge « R1 ».
- **Fin établie par :**
  - KO, TKO, soumission ou décision avec « R3 01:54 », carte des juges, menu *Revanche / Statistiques combat / Changer de combattants / Voir rediffusion / Quitter* ;
  - **ou** round = total et chrono à 0:00 ;
  - **ou** sortie du combat alors que du temps reste (arrêt).
- **Pièges :** 0:00 aux rounds 1 et 2 (le round suivant commence), ralentis de knockdown, écrans entre les rounds. La barre rouge et bleue est l'avantage de grappling, pas un score.
- **Contrat :** `period.number` et `total` sont lisibles sur les segments. Il manque le libellé du mode (« Combat principal »).
- **Robustesse : élevée**, si le HUD reste activé.

### Mortal Kombat 1 — combat, 343 images
- **Format :** par défaut « First to Two » (2 rounds gagnants), chrono de 90 s par round.
- **Affiché en permanence :** le chrono au centre, avec **deux emplacements de marqueurs de rounds gagnés** de chaque côté. Le nombre d'emplacements donne le nombre de rounds à gagner. En entraînement, un « ∞ » remplace le chrono et il n'y a pas d'emplacement.
- **Fin établie par :**
  - un côté atteint 2 rounds ;
  - écran de victoire, menu d'après-match (revanche, choix du personnage) ;
  - **ou**, a posteriori : marqueurs revenus à 0–0 avec des barres de vie pleines, ou combattants différents.
- **Pièges :** « FINISH HIM/HER », « FATAL BLOW », « KONTRE », compteurs de coups et de dégâts, chrono à 0 (fin de round, pas de match), mode entraînement (non comptable).
- **Risque d'échantillonnage :** un round dure 20 à 60 s, un match 1 à 3 min. En cas de revanche immédiate, on peut rater tout le dernier round, mais la fin reste établie par le **retour à 0–0 avec les mêmes combattants**, ce qui exige deux indices (voir §2).
- **Contrat :** `score` `rounds_won`. Il manque l'objectif en rounds (le nombre d'emplacements).
- **Robustesse : élevée.**

### Tekken 8 — combat, 173 images
- **Format :** chrono de 60 s par round par défaut. Le nombre de rounds à gagner est réglable, et le HUD l'indique par ses emplacements (des points qui s'allument à chaque round gagné).
- **Affiché en permanence :** le chrono, les points de rounds près des barres de vie, et « **WINS n** » en bas. Selon la documentation, c'est le compteur de **victoires consécutives** en mode Versus, qui augmente après chaque match gagné et repart à zéro après une défaite. **Ce n'est pas un score de round**, mais c'est un **indice de fin de match** qui persiste d'un match à l'autre.
- **Fin établie par :** comme pour MK1, plus le changement du « WINS n ».
- **Contrat :** `rounds_won`. Le compteur « WINS » n'a pas de champ.
- **Robustesse : élevée.**

### Naruto x Boruto Ultimate Ninja Storm Connections — combat, 62 images
- **Format :** nombre de rounds et chrono réglables (chrono infini possible).
- **Affiché en permanence :** chrono en haut au centre, **deux emplacements** de rounds gagnés de chaque côté sous le chrono (orange = gagné, gris = vide).
- **Fin établie par :** un côté atteint le nombre de rounds, écran de victoire ou de résultats, retour à la sélection des personnages, ou retour des marqueurs à 0–0.
- **Pièges :** les scènes de coup fatal (cinématiques), les invocations et techniques secrètes, les écrans de sélection sans combat lancé.
- **Robustesse : élevée.**

### Dragon Ball Sparking! ZERO — combat, 176 images
- **Format :** combats en équipe **sans rounds**. La victoire revient à qui élimine toute l'équipe adverse ; si le temps est écoulé (180, 360 ou 600 s, ou ∞), elle revient au **pourcentage de vie restant de l'équipe**.
- **Affiché en permanence :** les barres de vie segmentées (une par personnage de l'équipe) et les portraits. Un « ∞ » n'apparaît qu'en début de combat.
- **Fin établie par :** écran « **Victoire** » avec « Niveau de joueur » et récompenses. Il a été vu **25 images d'affilée** : il reste à l'écran tant que le joueur n'agit pas. Ensuite : sélection d'équipe.
- **Piège :** « **Réessayer** » depuis le menu pause relance un combat **sans écran de résultat** et avec les mêmes équipes. Le seul indice est alors le retour des barres de vie au maximum, que le contrat ne capture pas.
- **Contrat :** score toujours `null`. La **vie et la réserve de l'équipe** ne sont pas représentées.
- **Robustesse : moyenne** (élevée tant que l'écran « Victoire » est capturé).

### Brawlhalla — combat de plateforme, 85 images
- **Format :** partie classée en **3 stocks** (vies) et **8 minutes**. Le dernier joueur avec des stocks gagne ; si le temps est écoulé, c'est celui qui a le plus de stocks.
- **Affiché en permanence :** les portraits en haut à droite, avec le **nombre de stocks restants** et un anneau de dégâts coloré.
- **Fin établie par :** podium « 1st / 2nd » avec **SCORE, KO, Chutes**, « Récompenses de match », *Revanche / Revenir / Suivant* ; ou retour à « Recherche de joueurs ».
- **Pièges :** pendant la recherche d'adversaires, le joueur est dans une **arène d'attente** avec d'autres joueurs et des chiffres sur les portraits (frame 8) : ce **n'est pas un match compté**.
- **Contrat :** **les stocks ne sont pas représentés** (ce ne sont pas des scores).
- **Robustesse : moyenne** sans les stocks, **élevée** avec.

### Fortnite — battle royale, 1 105 images
- **Format :** jusqu'à 100 joueurs, en solo, duo, trio ou escouade, avec des phases de tempête. Une partie dure environ 15 à 25 min.
- **Affiché en permanence, en haut à droite :**
  - éliminations et assistances ;
  - **joueurs restants**, un nombre qui inclut le joueur et ses coéquipiers ;
  - minuteur de tempête : une icône **chronomètre gris** indique le temps avant que la tempête bouge, une icône **nuage violet** le temps avant qu'elle se referme.
- **Fin établie par (niveau équipe ; écran partagé = une partie) :**
  - « #1 VICTOIRE ROYALE » ;
  - « VOTRE PLACE : #N » sur toutes les vues, ou spectateur de l'adversaire qui a éliminé l'équipe ;
  - récap de la partie, salon, « Recherche de serveur » ;
  - île d'attente à 95–100 joueurs après une partie.
- **Pièges :** joueur éliminé en **spectateur d'un coéquipier**, carte de rétablissement (il peut **revenir** : frames 221 à 226), tempête à 0:00, joueurs restants qui **remontent légèrement** avec les réapparitions.
- **Contrat :** **joueurs restants absents** (seulement dans les notes).
- **Robustesse : élevée** avec les joueurs restants, **moyenne** sans.
- **À décider :** les modes créatifs (manches « 03/60 », Box PVP).

### Call of Duty: Warzone — battle royale, 317 images
- **Format :** battle royale (Goulag : un seul retour possible) ou Résurgence (réapparitions tant que le compte à rebours de l'équipe le permet). Des contrats, des phases de cercle.
- **Affiché en permanence, en haut à droite :** **équipes restantes**, **joueurs restants**, éliminations. Le minuteur du cercle a un **badge de phase** (numéro), la liste de l'escouade est affichée avec l'argent.
- **Fin établie par :** « **9e place** / RÉSUMÉ PARTIE » avec « REJOUER : 10 s » et « Quitter la partie » (73 images d'affilée observées), victoire, puis retour au salon ou à l'avion.
- **Pièges :** la mort d'un joueur quand l'escouade est vivante (Goulag, redéploiement, spectateur de l'escouade), la killcam, la phase du cercle qui augmente, les contrats et leurs minuteurs.
- **Contrat :** phase du cercle en `period stage` (OK). **Équipes et joueurs restants absents.**
- **Robustesse : élevée** avec ces champs, **moyenne** sans.

### Genshin Impact — aventure, 304 images
- **Structure :** exploration libre, domaines ou défis avec chronomètre, tests « Time Attack » d'1 minute, combats de boss.
- **Décision de l'utilisateur (2026-09-29) :** jeu de mission **facturé au temps** en entier, y compris les défis. Aucune frontière : `billing_mode = "temps"`.
- **Signal utile pour la seconde sortie :** `game.type = mission_adventure`, présent sur toutes les images de jeu.

---

## 4. Fiches des jeux à capturer plus tard

| Jeu / genre | Affiché en permanence | Fin établie par | Pièges | Contrat 2.0 |
|---|---|---|---|---|
| **Course** (Gran Turismo 7, F1 25, Need for Speed, MotoGP) | **Position** « 3/16 », **tour** « 2/3 », temps de course | Dernier tour (tour = total), puis **tableau des résultats** ou podium, menu, ou relance (tour 1, temps à 0) | Contre-la-montre et essais libres (tours sans total), qualifications chronométrées, monde ouvert (NFS) = exploration, retour au garage | `progress lap` et `position` : **OK** ; `period=none` |
| **Tennis** (TopSpin 2K25) | **Tableau de score permanent** (il ne peut pas être désactivé) : points, jeux, sets | Balle de match suivie de l'écran de victoire, ou retour à 0–0 en sets avec d'autres joueurs | Les points repartent à chaque jeu et les jeux à chaque set : ce ne sont pas des fins. « AD », tie-break | `score points` et `additional_scores` jeux / sets / tie-break : **OK**. Le format (2 ou 3 sets gagnants) n'est pas affiché. |
| **Basket** (NBA 2K26) | Score, **quart-temps** (Q1–Q4, prolongation), chrono du quart-temps (décroissant), chronomètre des tirs (24 s) | Q4 à 0:00 avec un score non égal, puis écran final, ou retour au menu. Égalité : prolongation. | Chrono qui repart à chaque quart-temps, chronomètre des tirs (secondaire), temps morts, mi-temps | `period quarter`, `clock`, `score points` : **OK** |
| **Rocket League** | Chrono décroissant de 5:00, buts, **prolongation « +0:23 »** (le chrono monte) | Chrono à 0:00 avec un score non égal, puis écran **WINNER** et MVP (avec le score de la série), ou but en or en prolongation | 0:00 avec égalité : prolongation, pas une fin | `clock`, `goals`, `overtime` : **OK**. Le score de la série n'a pas de champ. |
| **Boxe** (Undisputed) | Numéro de round et chrono au centre (jusqu'à 12 rounds de 3 min) | KO, TKO, décision avec cartes des juges | Comme l'UFC : 0:00 = fin de round | `period round` : **OK** si le numéro est lu |
| **Street Fighter 6** | Chrono de 99 s, icônes de rounds gagnés (2 rounds gagnants) | Un côté à 2 rounds, puis écran de victoire ou revanche, ou retour à 0–0 | Les icônes indiquent **comment** le round a été gagné ; des jauges propres à certains personnages | `rounds_won` : **OK** |
| **Call of Duty multijoueur** | Scores des équipes (par exemple 100 éliminations en match à mort par équipe), chrono décroissant | VICTOIRE ou DÉFAITE, tableau des scores, vote de la carte suivante | Réapparitions, séries d'éliminations | `score points`, `clock` : **OK** |
| **Missions** (The Last of Us, GTA V, Assassin's Creed, Red Dead Redemption 2, tout jeu de mission presque sans fin) | Objectif en cours, minimap | Sans objet : **facturé au temps** (`billing_mode = "temps"`) | Ne pas compter les bandeaux « MISSION RÉUSSIE / ÉCHOUÉE » comme des parties | `game.type = mission_adventure` suffit pour la seconde sortie |
| **eFootball** | Comme EA FC | Comme EA FC | Comme EA FC | **OK** |

**Jeux de mission : décision prise (2026-09-29).** Les jeux et modes **sans fin de partie** (tous les jeux de mission qui n'ont presque pas de fin, comme The Last of Us, GTA, Assassin's Creed ou Red Dead Redemption 2 — confirmé pour ce dernier le 2026-09-29 ; Genshin Impact, y compris ses défis ; MK1 entraînement ∞) **ne sont pas comptés**. Aucune frontière n'y est placée et aucun signal d'incrément n'est produit. Le système les signale par une **seconde sortie `billing_mode = "temps"`**, et **un système externe facture la durée**. Le problème du bandeau « Mission réussie » trop bref disparaît donc.

**Conséquence pour le modèle :** le GRU (ou une petite tête de classification à côté) produit deux sorties :

1. **fin de partie** (`unit_end_boundary`), qui n'a de sens que pour `billing_mode = "partie"` ;
2. **mode de facturation** (`partie`, `temps` ou `hors_jeu`), par observation.

Le type de jeu fourni par le VLM (`mission_adventure`, mode `free_roam` / `mission`, chrono `∞`) est un indice direct pour cette seconde sortie.

**Dans le jeu de données du GRU**, une mission n'est pas retirée : ses observations restent dans la séquence avec `billing_mode = "temps"` **et** une cible de fin de partie à **0, apprise** (et non masquée). Même chose pour les menus et les écrans noirs. Sinon, le GRU n'apprendrait jamais à ignorer « MISSION RÉUSSIE », un fondu au noir ou un chargement, et il fabriquerait des fins, donc des parties facturées en trop. Par sécurité, le système de comptage n'incrémente de toute façon que si `billing_mode = "partie"`.

---

## 5. Ce qui manque au contrat 2.0 (à décider avant la fin de l'annotation)

> **Mis en œuvre le 2026-09-29 : contrat 2.1 et GRU v4.** La solution universelle retenue est une clé unique, `secondary_counters` (voir `docs/contract/README.md`), qui couvre `survivors` (`players_remaining` / `teams_remaining`), `stocks` (`lives`), `score.target` (`target`) et `series`. Les indicateurs GRU `game.mode`, `clock.infinite`, `period.is_last` et `observation_missing` sont ajoutés. Restent non traités : le libellé du mode (texte, en note) et l'état par vue en écran partagé.


| Champ proposé | Jeux concernés | Rôle pour la fin de partie |
|---|---|---|
| `survivors` : joueurs et/ou équipes restants (valeur lue) | Fortnite, Warzone, tout battle royale | Invariant principal : il baisse, puis repart au maximum à la partie suivante. |
| `stocks` : vies restantes A/B | Brawlhalla (et jeux similaires) | La partie finit quand un côté arrive à 0. |
| `score.target` : rounds, sets ou points à atteindre, **quand le HUD l'affiche** (nombre d'emplacements) | MK1, Tekken, Naruto, SF6 | Un côté atteint l'objectif, donc fin de match. |
| `mode_label` : libellé visible du mode ou du format | UFC (« Combat principal »), FC (« Durée 5 min par période »), course (« 3 tours ») | Durée et format probables, sans déduction par le VLM. |
| `series` : compteur entre parties visible | Tekken (« WINS n »), Rocket League (score de série) ; pas l'agrégat aller-retour de FC, laissé en note (décision du 2026-10-05) | Il change après chaque partie gagnée. |
| Variable GRU « dernière période » (`number == total`) | UFC, boxe, basket, tennis, foot | Décision immédiate au dernier round, quart-temps ou set. |

**Manques côté entrées du GRU (`gru_feature_spec_v3`, 201 variables).** Ils se corrigent sans réannoter, car les valeurs sont déjà dans le JSON :

| Information | Présente dans le JSON du VLM | Lue par le GRU v3 ? | À ajouter (spec v4) |
|---|---|---|---|
| `game.mode` (match, versus, bout, race, mission, free_roam…) | ✅ | ❌ (seuls `game.type` et `mode_duration` sont encodés) | encodage one-hot : utile pour `billing_mode` (mission, exploration libre, entraînement) |
| Chrono infini « ∞ » | ✅ (`clock.display`) | ❌ (le GRU voit seulement « chrono visible, valeur inconnue », comme un chrono illisible) | indicateur `clock.infinite` |
| Dernière période | ✅ (`period.number`, `period.total`) | partiel | indicateur `period.is_last` (`number == total`) |
| Observation manquante (échec ou délai du VLM sur le Pi) | — | ❌ | indicateur `observation_missing` et ligne conservée |
| Notes libres (joueurs restants, stocks, WINS…) | seulement en texte | ❌ | passer par les nouveaux champs du contrat ci-dessus |

Le GRU n'est pas encore entraîné en v3 : c'est le bon moment pour passer à une spec v4.

Les valeurs manquantes des annotations déjà faites sont **en grande partie dans les notes** (par exemple les joueurs restants de Fortnite) : elles pourront être complétées par des traces séparées, sans modifier les lots existants.

---

## 6. Risques résiduels

1. **Erreur de lecture du VLM élève** (sur le Pi) : c'est la principale source de fausses fins. Protection : double indice pour toute rupture d'invariant, et entraînement ou évaluation du GRU sur les sorties **de l'élève**.
2. **HUD désactivé** par le joueur : perte des invariants A. Protection : imposer les réglages dans la salle.
3. **Données manquantes** pour la course, le tennis, le basket, la boxe, les missions, et trop peu d'UFC : le GRU ne généralise pas à ce qu'il n'a jamais vu. Il faut capturer ces genres.
4. **Règle commerciale encore ouverte** : les modes créatifs de Fortnite (manches « 03/60 », Box PVP). Les missions et Genshin sont décidés : facturation au temps.

---

## Sources

- EA Sports UFC 4 — manuel officiel (PS4), HUD en haut au centre : https://www.ea.com/able/resources/ufc/ufc-4/ps4/manual
- Fortnite — icônes de tempête, joueurs restants, éliminations et assistances : https://fortnite.fandom.com/wiki/The_Storm , https://fortnite.fandom.com/wiki/Elimination
- Brawlhalla — Ranked (3 stocks, 8:00) : https://brawlhalla.fandom.com/wiki/Ranked , https://brawlhalla.fandom.com/wiki/Stock
- Mortal Kombat 1 — format (2 rounds gagnants, 90 s) : https://mk1.kombatakademy.com/guides/the-match/ , https://help.vanta.gg/article/360-what-are-the-match-rules-for-mortal-kombat-1
- Tekken 8 — compteur WINS (victoires consécutives en Versus) : https://steamcommunity.com/app/1778820/discussions/0/4202489789154902338/ ; modes : https://tk8.tekken-official.jp/en/mode/online.php
- Street Fighter 6 — HUD et règles : https://wiki.supercombo.gg/w/Street_Fighter_6/HUD , https://help.vanta.gg/article/314-what-are-the-match-rules-for-street-fighter-6
- Naruto Storm Connections — réglages de combat : https://psnprofiles.com/guide/18144-naruto-x-boruto-ultimate-ninja-storm-connections-trophy-guide
- Dragon Ball Sparking! ZERO — limites de temps et victoire en équipe : https://steamcommunity.com/app/1790600/discussions/0/830448327606668052/ , https://www.thegamer.com/dragon-ball-sparking-zero-complete-world-tournament-guide/
- Warzone — Goulag et Circle Collapse : https://www.callofduty.com/blog/2022/11/call-of-duty-warzone-2-0-season-01-dmz-battle-royale-overview , https://www.callofduty.com/patchnotes/2025/08/call-of-duty-bo6-warzone-season-05-patch-notes
- EA FC 26 — durée des mi-temps, Score Clock On/Off : https://www.fifplay.com/fc-26-game-settings/
- TopSpin 2K25 — tableau de score non désactivable : https://www.sportskeeda.com/gaming-tech/best-topspin-2k25-xbox-settings
- NBA 2K26 — durée des quart-temps : https://www.magicgameworld.com/nba-2k26-how-to-change-quarter-length/
- Rocket League — 5 min, prolongation, écran de victoire : https://help.playvs.com/en/articles/4919221-rocket-league-rulebook
- Undisputed — HUD (round et chrono au centre) : https://www.sporf.com/first-full-round-of-footage-for-undisputed-boxing-video-game-revealed/
- GTA V — Mission Passed / Failed : https://gta.fandom.com/wiki/Missions ; Assassin's Creed — synchronisation : https://assassinscreed.fandom.com/wiki/Synchronization
- Black Ops 6 — match à mort par équipe (100 éliminations) : https://www.callofduty.com/guides/blackops6/modes/call-of-duty-guides-black-ops-6-multiplayer-mode-team-deathmatch
