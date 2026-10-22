# Relecture des fins manquées : regard « annotation »

Relecture des 211 cas des huit lots, du point de vue de la qualité des étiquettes et des observations : la fin
est-elle juste et placée comme ailleurs, l'observation du professeur est-elle fausse ou seulement incomplète, et
quelle convention ou quelle correction réglerait le problème. Les lignes cas par cas sont dans
`revue_annotation.jsonl`.

Bilan : 176 accords, 35 accords partiels, aucun désaccord complet. Je n'ai contesté aucune conclusion sur une fin
réelle. Les accords partiels portent sur trois points : la cause principale (5 cas où je la remplace), le partage
entre erreur du professeur et convention qui manque (une vingtaine de cas), et des corrections proposées qui
introduiraient des déductions dans les observations. J'ai vérifié 68 cas sur les images originales : les 8
étiquettes jugées douteuses, tous les cas `ECRAN_NON_MARQUE` et `ERREUR_OBSERVATION` que j'ai jugés décisifs, les
cas à confiance moyenne, et les deux constats demandés. J'ai aussi fait des mesures sur toute la base, à partir des
observations effectives (traces de correction appliquées, `playend.corrections.traces.effective`) et des
étiquettes validées (`labels_human_verified.jsonl`).

Codes que j'ajoute :

- `ETIQUETTE_INCOHERENTE` : la fin est juste, mais le même signe à l'écran reçoit la fin sur des captures
  différentes selon la partie. La fin respecte une des deux pratiques et contredit l'autre.
- `FIN_MARQUEE_NON_EXPLOITEE` : l'observation marque correctement l'écran de fin (phase `post_game`), et ce sont
  les détecteurs qui ne s'en servent pas. Je l'emploie à la place de `ECRAN_NON_MARQUE` quand l'écran est déjà noté
  `post_game` et qu'aucun vainqueur n'est écrit.

## 1. Les deux constats demandés

### 1.1 La capture où un combattant atteint l'objectif de manches

Les analystes des lots 1, 2 et 5 l'ont vu, et j'ai vérifié sur toute la base : c'est une vraie incohérence
d'étiquetage, pas un effet de lecture.

J'ai cherché toutes les parties dont une capture montre un score `rounds_won` égal à l'objectif
(`counter.target.field`). Il y en a 16, et sur chacune, cette capture est la dernière de la partie :

| Fin posée sur la capture qui atteint l'objectif | Fin posée sur la capture suivante |
|---|---|
| f0067594 U09 (58), U19 (123), U22 (156), U23 (160), U42 (459) | 8e58b139 U03 (46→47), U05 (52→53), U07 (82→83), U08 (92→93), U09 (99→100) |
| Naruto fdb79549 U02 (8) | f0067594 U34 (397→398), U47 (495→496), U48 (506→507) |
| | Tekken 078643a4 U25 (154→155), U30 (183→184) |

Soit 6 contre 10. J'ai lu au zoom les marqueurs et les barres de vie des 13 captures de Mortal Kombat 1 et des deux
de Tekken. Sur toutes, le second marqueur du vainqueur est allumé (parfois encore orange, en cours d'attribution) et
le perdant est à 0,00 point de vie, avec en plus « FINISH HIM » (f0067594 160, 495, 506) ou « K.O. » (Tekken 154).
La règle du double indice est donc satisfaite sur l'image elle-même.

**Laquelle suit la règle ?** La première, sans ambiguïté. `data/boundaries/README.md` (l. 20–21) écrit :
« `unit_end_boundary = 1` sur la première observation qui établit la fin […]. Si cette observation montre encore la
partie en train de se jouer (MK1 : le dernier marqueur de round s'allume en plein combat), elle est aussi la dernière
image de la partie : `end_established_at = last_frame` (validation humaine du 2026-10-03) ». Les 10 fins posées sur
la capture suivante s'écartent donc de la règle écrite. Le plus curieux est que 8e58b139 a été validée le même jour
(2026-10-03) que f0067594 : la décision a été appliquée à cinq parties d'une session, pas à ses trois autres
(U34, U47, U48), ni aux autres sessions.

**Ce que cela coûte.**

- À l'évaluation, une annonce est acceptée sur la fin ou sur la capture suivante. Avec la fin sur la capture N qui
  atteint l'objectif, une annonce en N+1 reste acceptée ; avec la fin sur N+1, une annonce en N compte comme fausse
  fin et la fin comme manquée. Harmoniser sur N ne pénalise donc aucun détecteur en retard.
- À l'entraînement, quand f0067594 est tenue à l'écart, les seuls exemples de « cible atteinte » sont ceux de
  8e58b139 et de Tekken, et ils disent tous « 0 ». Une variable « score = objectif », proposée par trois analystes,
  apprendrait le contraire de ce qu'on veut tant que les étiquettes ne sont pas harmonisées.

**Correction recommandée**, à décider par l'auteur : déplacer les 10 fins sur la capture qui atteint l'objectif, et
leur donner `billing_mode = partie` comme pour les 6 autres. La prudence face aux erreurs de lecture de l'élève
(un marqueur orange mal lu) a sa place dans les détecteurs, pas dans la vérité terrain : un détecteur peut attendre
la capture suivante pour confirmer, puisqu'elle est tolérée.

### 1.2 Le participant « state.screen_type » (f0067594 U29)

J'ai parcouru tous les champs texte des 8 871 observations effectives et des entrées brutes des lots (17 742
fichiers lus), à la recherche d'une valeur qui ressemble à un nom de champ du contrat (`state.…`, `score.…`,
`participants.…`, etc.). **C'est le seul cas de PlayEnd** : f0067594, capture 254, `participants.primary =
["state.screen_type"]`.

La cause se lit dans la lecture du lot (`decisions/reading_spec_000199_000264.json`). La ligne de 254 porte
`"parts": ["state.screen_type"]` et aucun bloc `set`. Les lignes 255 et 256, juste après, portent
`"set": {"state.phase": "post_game", "state.screen_type": "cutscene"}`. La clé destinée au bloc `set` est tombée
dans `parts`. Résultat : le préréglage `fc_play` a laissé 254 en `active / gameplay` sans résultat, alors que l'image
montre le bandeau « FIN DU MATCH — ARSENAL 7 | 4 REAL MADRID ». **Une seule faute de saisie produit les deux défauts**,
l'écran de fin non marqué et le faux participant. Ce n'est pas une erreur de perception : la note libre décrit bien
« Bandeau récapitulatif ».

`build_lot` l'a acceptée parce que `parts` n'est pas contrôlé, et parce que l'accord entre note et JSON, que
l'outil garantit, ne protège pas contre une faute dans la lecture elle-même. Corrections : une trace sur 254
(`post_game / result`, gagnant Arsenal, participants ARSENAL et REAL MADRID), et un contrôle dans `build_lot` ou
`record_lot` qui refuse un participant de la forme `mot.mot`.

## 2. Ce que je conteste chez les analystes

**Écrans d'après-match déjà notés `post_game`** (d8b709c4 U04, f8c2843d U05, U07 et U31, f0067594 U23, en partie
11029423 U06). Les analystes les classent en `ECRAN_NON_MARQUE` et proposent de mettre `result.visible = true` sur le
menu à encart « 90:00 A x-y B ». Je m'y oppose. Le contrat ne met un résultat que lorsqu'il est explicitement écrit,
et la pratique est constante sur ces menus : a80bda9c 71, f0067594 328, f8c2843d 167 et 240 sont notés `post_game`,
résultat non visible, « aucun libellé de vainqueur ». L'écran de fin est donc marqué ; c'est son exploitation qui
manque. La mesure le confirme : dans EA FC, 16 des 17 entrées en `post_game` de la base tombent à une capture près
d'une vraie fin. Pour 11029423 U06, la trace doit passer 168 de `pause` à `post_game`, sans résultat.

**Erreurs du professeur qui sont des conventions manquantes.** Ne pas noter la bannière « ROUND 1 » (f0067594 U46,
U57) n'est pas une erreur : aucune convention de MK1 ne demande la période. Les noms écrits sur la pause et la
sélection laissés vides (f0067594 U10, U16) viennent des préréglages de menu. Les équipes vides sur « Choix des
équipes » (7616a3a5 U08) sont la pratique constante des 30 écrans de ce type, où les équipes défilent. Le titre ou le
mode null sur un gros plan sans aucun texte (Tekken U07, U09, U11), ou sur l'écran « Classique / But en or / Tirs au
but » (11029423 U07, capture 203), est une lecture prudente. Dans tous ces cas, il faut une règle écrite, pas une
correction isolée.

**Étiquettes que je ne trouve pas douteuses.** f0067594 U25 et U65 : la fin posée sur le premier accueil de la
console suit la pratique de toutes les sessions. f0067594 U36 : 412 prouve déjà le nouveau match, parce que dans MK1
les emplacements de manches restent dessinés entre deux manches (420 : « ROUND 2 » avec le marqueur allumé) et ne
manquent qu'au début d'un match.

**Étiquettes qui ne sont pas « justes »** alors que l'analyste les jugeait telles. Dragon Ball fdb79549 U04 : la
fin devrait être sur 54, le premier accueil sans reprise, et non sur 55. L'analyste y voyait une annonce trop
précoce ; je vois une étiquette qui s'écarte de la pratique. Tekken U25 et U30, que l'analyste traitait comme des
cas isolés, relèvent de l'incohérence du § 1.1.

**Propositions qui introduiraient des déductions dans les observations.** Je les déconseille, parce qu'elles
violeraient la règle « une image, une lecture » et apprendraient à l'élève à inventer. Cela vaut pour une période
déduite pour EA FC (mieux vaut calculer la variation du chrono sans période), pour « stage n−1 » sur le classement
de Beach Buggy, pour le tour lu d'après la position du drapeau à damier (constatée sur une session, sans source),
pour `pre_game` sur une pose sans texte et pour l'option en surbrillance du menu de pause comme champ. Le
« face-à-face » d'EA FC en `series` irait aussi contre la décision de l'auteur du 2026-10-05 sur l'agrégat
aller-retour.

## 3. Ce que mon métier voit et que les analyses ne disent pas

**La vérité terrain a des erreurs qui faussent la mesure elle-même.** Sur les 211 cas, je compte 9 fins mal
placées : 8e58b139 U09, f0067594 U33 et U54, f8c2843d U03, Tekken U25 et U30, Fortnite 27921669 U02, Dragon Ball
fdb79549 U04, et UFC f8c2843d U21, à confirmer. S'y ajoutent les 7 autres parties du § 1.1 et **une frontière
manquante** : f0067594, capture 418, dans l'unité U37. J'ai vérifié 415–421 au zoom. 416–417 sont la 2e manche à
1–0 ; 418 est à 0–0, chrono 88, Kitana à 1000/1000 ; 420 affiche « ROUND 2 » à 90 avec Kitana à 1–0. Une 2e manche
ne recommence pas dans le même match : une partie manque, et une annonce sur 418 aurait été comptée comme fausse fin.
Dans plusieurs de ces cas, les détecteurs avaient raison : le GRU à 0,723 sur 549 (U54), les trois détecteurs sur
75 (27921669 U02) et sur 54 (fdb79549 U04). Northcutt et al. (2021) ont montré que de faibles taux d'erreur dans les
étiquettes de test suffisent à changer le classement des modèles. Ici, il s'agit justement de comparer le GRU, le
gradient boosting et les règles.

**Pourquoi la validation humaine ne les a pas vues.** La fiche de validation (`build_items.py`) montre le début, la
dernière image, la fin établie et l'image suivante de chaque partie. Elle laisse donc passer ce qui se passe *à
l'intérieur* d'une partie (la frontière manquante de 418, notée « lecture isolée »), et tout ce que l'observation a
mal lu avant le placement (f8c2843d 92, écran « RÉSULTATS — VAINQUEUR Joueur 1 » lu comme un écran noir, d'où une fin
posée sur 93). Les fins ont été placées à partir des observations : une erreur du professeur devient une erreur
d'étiquette sans que rien ne le signale.

**Le même professeur lit différemment le même écran d'une session à l'autre.** C'est la dérive la plus nette, et
elle vient des écrans hors jeu, pas du HUD :

- le menu d'après-match d'EA FC est noté `pause` (11029423 168), `post_game` (f8c2843d 167, 240) ou `pre_game`
  (f8c2843d 747) ;
- le menu « REPRENDRE MATCH » à 90:00 est noté `pause` en 11029423 et `post_game` en f8c2843d 891 et f0067594 328 ;
- l'écran d'après-match de Tekken est noté `intermediate` (32, 45) ou `menu` (91, 103, 114, 164, 187), jamais
  `post_game`, alors que l'écran équivalent de MK1 est `post_game` partout, comme le menu de l'UFC selon sa
  convention ;
- les gros plans sans HUD de Tekken sont notés de quatre façons : `cutscene / unknown`, titre null, `intermediate`,
  et même `active / gameplay` (139, 160) ;
- en Fortnite, les captures de spectateur sont notées `active` (47), `intermediate` (10), `post_game` (7) ou
  `pre_game` (5), et le mode prend 9 valeurs (None 1 051, « Battle Royale » 234, « other » 147, puis cinq graphies
  libres de « Zéro construction ») ;
- dans MK1, l'écran « FIGHT » à 90 sans emplacements dessinés est noté 0–0 en 40 et null en 108.

**La notation fidèle mais instable casse le calcul.** Le titre d'EA FC change 61 fois entre deux captures voisines,
dont 51 au milieu d'une partie (32 dans 11029423). Les participants changent 103 fois entre deux captures qui en ont
tous les deux, dont 92 au milieu d'une partie, presque toujours entre le sigle du HUD et le nom long d'un menu
(« PSG / BAR » contre « Paris SG / FC Barcelone »). Chaque graphie respecte la règle du texte écrit : il ne faut pas
réannoter, il faut normaliser dans le calcul (famille de jeu, table d'alias des équipes). De même, le mode passe à
null sur les pauses et les menus par les préréglages (120 changements None ↔ match en EA FC), ce qui rompt le
« même contexte » à chaque pause.

**Les traces de correction générales héritent des erreurs du premier professeur.** Plusieurs erreurs vérifiées sont
sur des captures dont la note commence par « [Correction] ». C'est le cas de l'UFC 11029423 31 (carte des juges
recopiée comme score 20–18, « TKO » noté `other`), de 11029423 42 (logo FC26 noté « EA Sports UFC 5 »), de 11029423
168, de 9e0e6a4f 33 (« PÉNALTYS » avec une période `unknown`) et de Dragon Ball 020621e7 13 (accueil de la PS5 avec
le titre du jeu). Ces traces ont repris les compteurs secondaires sans relire les autres champs.

**Les infractions à la règle des participants existent encore.** Noms déduits des écussons : c93ed313 58–62
(habillage LaLiga, la note du professeur dit elle-même « écussons ») et f8c2843d 775. Noms reportés de la voisine
sous un encart : f8c2843d 780, d8b709c4 236 (« BRE » sous le bandeau « Remplacement »). C'est peu, mais c'est la
règle non négociable de l'auteur.

**Les vraies erreurs de lecture du professeur**, vérifiées sur les images, en plus des cas cités plus haut :
f0067594 404, « KITANA GAGNE » écrit en petit et raté alors que « LI MEI GAGNE » est noté résultat en 8e58b139 53 ;
13 des 29 captures notées noires en f8c2843d, qui ne le sont pas (luminosité moyenne nettement au-dessus du noir :
56, 60, 92, 94, 130, 131, 171, 200, 209, 243, 749, 750, 1132) ; Warzone 078643a4 266, « 9e place » sans résultat ni
place, contre la convention ; 311, « VICTOIRE » de l'« ESCOUADE ENNEMIE » notée `winner = player_team` ; 309,
`screen_type result` avec `result.visible` null ; Fortnite ccfc6589 64–65, joueurs restants (6 puis 5) visibles au
zoom et notés « non affichés » ; a4e41f30 87–96, phase `intermediate` alors que le joueur joue ; Tekken 185, « K.O. »
d'une première manche noté résultat de match, la plus dangereuse puisqu'elle fabrique un faux écran de fin en plein
match (gradient boosting à 0,86).

## 4. Méthode recommandée par famille de causes

**Revanches, lectures coupées, contexte sans variation** (`REPRISE`, `LECTURE_COUPEE`, `CONTEXTE_SANS_VARIATION`,
environ 80 cas). Ce ne sont pas des défauts d'annotation, et il ne faut pas les corriger dans les observations en
recopiant le score sur l'écran noir ou la pause : ce serait une lecture d'image voisine, et l'élève apprendrait à
inventer. La correction va dans `temporal.py` : dernière valeur lisible avec son âge, contexte calculé sur la
famille de jeu normalisée, enjambement des captures sans titre, alias d'équipes. Coût : du code et un nouveau
calcul des variables, aucune réannotation.

**Écrans de fin** (`ECRAN_NON_MARQUE`, 13 cas en cause principale selon moi, plus `FIN_MARQUEE_NON_EXPLOITEE`). Il
faut séparer trois situations.

- Les vraies erreurs, à corriger par des traces : f0067594 254 et 404, f8c2843d 92 et 747, 11029423 168, Warzone
  266 et 311. Une demi-journée.
- Les conventions qui manquent, à écrire puis appliquer par des traces. L'écran d'après-match de Tekken passe en
  `post_game` (7 captures). Le classement cumulé de Beach Buggy passe en `post_game / scoreboard`, sans résultat (la
  convention actuelle `intermediate` contredit la règle « une course = une partie » décidée le même jour). Pour
  Warzone, « ÉLIMINATION FINALE » passe en `post_game`, résultat non visible.
- L'exploitation : une règle et une variable « entrée en `post_game` hors des jeux facturés au temps ». Les entrées
  en `post_game` hors de ces fins tombent presque toutes dans Genshin, God of War et des écrans de Warzone : le
  filtre par mode de facturation est indispensable.

**Erreurs d'observation** (`ERREUR_OBSERVATION`). Des contrôles automatiques, à ajouter à `build_lot` ou à
`record_lot` et à passer une fois sur toute la base, dans la ligne des méthodes de détection d'erreurs comparées par
Klie, Webber et Gurevych (2023) :

1. un participant de la forme `mot.mot` ou égal à un nom de champ ;
2. une capture notée noire dont la luminosité moyenne dépasse environ 12 sur 255 ;
3. une note qui contient « VAINQUEUR », « GAGNE », « FIN DU MATCH », « RÉSULTATS » ou « place » avec un résultat
   non visible ;
4. des participants non vides alors que la note parle d'écussons ;
5. un titre non nul sur un accueil de console ;
6. `screen_type = result` avec `result.visible` null ;
7. un « K.O. » noté résultat alors qu'aucun côté n'atteint l'objectif.

Chaque alerte se relit à la main et se corrige par une trace. Coût : quelques dizaines de lignes de code et une ou
deux journées de relecture ; le gain est surtout sur la vérité terrain, puisque les fins sont placées à partir de ces
observations.

**Étiquettes** (`ETIQUETTE_DOUTEUSE`, `ETIQUETTE_INCOHERENTE`). Une vingtaine de frontières à revoir dans les
`units.json` : les 10 parties du § 1.1, la frontière manquante de f0067594 418, f0067594 U54 → 549, U33 → 390,
f8c2843d U03 → 92, 27921669 U02 → 75, fdb79549 U04 → 54, et UFC f8c2843d U21 → 637, à confirmer (le texte de sortie
n'apparaît qu'après un rehaussement du contraste). Il faut ensuite régénérer les étiquettes, ajouter les cas aux
« Points à confirmer », obtenir la validation de l'auteur avant toute promotion (règle 7), puis refaire
l'évaluation. Je déconseille d'élargir d'abord la tolérance aux annonces en avance, comme le proposent trois
analystes. Plusieurs de ces « annonces en avance » sont en fait des étiquettes en retard ; accepter l'avance
partout ferait aussi passer des annonces vraiment prématurées (écrans d'équipe d'EA FC en cours de match, accueil
de la console suivi d'une reprise en fdb79549 46). Il faut une règle écrite pour les sorties vers la console :
« accueil de la console sans reprise du même jeu : fin sur le premier accueil ». Elle est appliquée partout sauf en
fdb79549 U04, mais elle n'est écrite nulle part.

**Seuils, jeux rares, signes propres à un jeu** (`SEUIL`, `JEU_RARE`, `SIGNE_PROPRE_AU_JEU`). Ce n'est pas mon
domaine, sauf sur un point : l'annotation peut rendre les signes transférables d'un jeu à l'autre. Le même écran
d'après-match noté `post_game` dans tous les jeux de combat, la bannière « ROUND n » notée `period round n` quand le
numéro est écrit (MK1, Tekken) : un modèle peut alors apprendre sur MK1 ce qui servira à Tekken. Une convention
uniforme coûte moins qu'une session de plus.

## 5. Conventions à écrire

Chacune avec un critère lisible sur l'image seule, une date et une décision de l'auteur.

1. **Écrans d'après-match des jeux de combat** (Tekken surtout) : `post_game`. Un résultat seulement si un texte de
   victoire est écrit (« X GAGNE », « VICTOIRE », réplique de victoire). Le nom en grand sans autre texte : à
   trancher par l'auteur, de façon cohérente avec MK1.
2. **« K.O. » et « X GAGNE » avec le HUD visible** : fin de manche, jamais un résultat de match, sauf si le score
   atteint l'objectif.
3. **Gros plans et poses sans HUD ni texte** (Tekken, Dragon Ball, intro de MK1) : `cutscene`, phase `unknown`.
   Jamais `active / gameplay`, jamais `pre_game` déduit.
4. **Bannières « ROUND n » / « FINAL ROUND »** : `period round`, numéro n.
5. **Écran « FIGHT » de MK1 sans emplacements dessinés** : score null.
6. **Pause et sélection d'un jeu de combat** : noter les deux combattants principaux écrits, sans les Kaméos.
7. **EA FC** : le menu à « QUITTER LE MATCH » en tête, ou avec « Interview d'après-match » : `post_game`, sans
   résultat. Le menu « REPRENDRE MATCH » : `pause`, chrono noté. « Choix des équipes » : `team_select`,
   participants vides tant que les équipes défilent.
8. **Fortnite** : un codage unique du spectateur, et un vocabulaire fermé pour `game.mode`, le libellé affiché
   allant dans la note (règle déjà écrite pour les autres jeux).
9. **Surcouches système** (centre de contrôle de la PS5, « Voulez-vous quitter ? », manette déconnectée) : `paused`
   ou `menu`, texte recopié dans la note.
10. **Beach Buggy** : classement cumulé « Suivant : ÉVÉNEMENT n » en `post_game / scoreboard`, sans résultat.
11. **Warzone** : « ÉLIMINATION FINALE / DERNIÈRE KILLCAM » en `post_game`, résultat non visible ; écrans de
    progression et de récompenses de fin de partie en `post_game`.
12. **Étiquettes de manette** (« Joueur 1 », « J1 ») : décider si elles sont des participants.
13. **Sortie vers la console** : fin sur le premier accueil sans reprise (règle de placement, dans
    `ANALYSE_FIN_DE_PARTIE_PAR_JEU.md`).

## 6. Mes trois priorités pour l'auteur

1. **Réparer la vérité terrain avant toute nouvelle mesure.** Harmoniser les 10 fins « objectif de manches
   atteint » sur la capture qui l'atteint (la règle est déjà écrite), ajouter la frontière manquante de f0067594
   418, et déplacer les fins en retard (f0067594 U54 → 549, U33 → 390, f8c2843d U03 → 92, 27921669 U02 → 75,
   fdb79549 U04 → 54 ; UFC f8c2843d U21 → 637 à confirmer). Tout cela avec ta validation, puis refaire
   l'évaluation : ces étiquettes décident aujourd'hui si un détecteur a raison.
2. **Corriger les vraies erreurs du professeur par des traces, et installer les sept contrôles automatiques** du
   § 4 dans `build_lot` ou `record_lot`. Les plus coûteuses : la faute de saisie de f0067594 254, les 13 fausses
   captures noires de f8c2843d (dont un écran de résultat), les menus d'après-match mal typés, la carte des juges de
   l'UFC, le titre FC26 noté UFC 5, la place et le vainqueur de Warzone, les participants déduits des écussons.
3. **Écrire les conventions qui manquent (§ 5) et normaliser la notation dans le calcul**, pas dans les
   observations : famille de jeu, alias d'équipes, mode fermé. La plupart des incohérences vues ici viennent d'écrans
   hors jeu sans règle écrite, sur lesquels le même professeur a varié d'une session à l'autre.

## Sources

- C. G. Northcutt, A. Athalye, J. Mueller, « Pervasive Label Errors in Test Sets Destabilize Machine Learning
  Benchmarks », NeurIPS Datasets and Benchmarks, 2021 : https://arxiv.org/abs/2103.14749
- J.-C. Klie, B. Webber, I. Gurevych, « Annotation Error Detection: Analyzing the Past and Present for a More
  Coherent Future », *Computational Linguistics* 49(1), 2023 : https://aclanthology.org/2023.cl-1.4 (arXiv
  2206.02280)
- G. J. J. van den Burg, C. K. I. Williams, « An Evaluation of Change Point Detection Algorithms », 2020–2022
  (annotation des points de rupture par plusieurs annotateurs et accord entre eux) : https://arxiv.org/abs/2003.06222
- Règles internes citées : `data/boundaries/README.md` (l. 20–21), `docs/conventions/README.md`, `combat.md`,
  `football.md`, `battle-royale.md`, `course.md`, `ANALYSE_FIN_DE_PARTIE_PAR_JEU.md`.
