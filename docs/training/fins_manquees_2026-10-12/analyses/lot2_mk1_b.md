# Lot lot2_mk1_b : 25 fins de Mortal Kombat 1 (session f0067594)

Chaque cas a été lu sur son dossier, sur sa planche, puis sur les images originales : le HUD de chaque capture de la
fenêtre (chrono, emplacements de manches au-dessus des barres, barres de vie chiffrées) a été lu sur un recadrage
agrandi deux fois de l'image 1280×720, et les captures décisives ont été ouvertes en entier. La liste
`images_ouvertes` du `.jsonl` donne les captures lues ainsi sur l'original (recadrage ou image entière).

Repère utile pour tout le lot : la session f0067594 est tenue à l'écart dans son tour, ses modèles sont entraînés sur
les 24 autres sessions, qui ne contiennent que 17 fins de Mortal Kombat 1 (11029423 et 8e58b139). Le seuil du GRU
est 0,555 et celui du gradient boosting 0,884 pour toute la session.

## Mortal_Kombat_1_f0067594_U18

Fin juste : à 116, Johnny Cage mène 1–0 dans la deuxième manche (chrono 70) ; à 117, mêmes combattants et mêmes Kaméos, 0–0, barres pleines chiffrées 1000/1000 et 1050/1050, chrono 89 : un nouveau match, sans écran de fin entre les deux. L'observation est juste.

Seule variable non nulle : score.a.delta_candidate = −0,693. La remontée du chrono n'est pas calculée (période unknown). Les règles la trouvent par le retour à 0–0. Le gradient boosting reste à 0,06 : dans les 24 sessions d'entraînement, les baisses d'un seul côté étiquetées fin sont toutes du côté B (0–1 → 0–0), jamais du côté A, et la seule baisse du côté A est une non-fin d'EA FC. Le même modèle trouve à 0,82–0,98 les revanches directes 0–1 → 0–0 de cette session. Cause principale : asymétrie des côtés (code nouveau `ASYMETRIE_COTES`) ; une variable symétrique (variation du total, retour à 0–0) ou l'échange A/B à l'entraînement la ferait trouver.

## Mortal_Kombat_1_f0067594_U19

Fin juste : à 123, Johnny Cage est à 0 point de vie, hébété dans un décor passé en noir et blanc (état « Finish Him »), et Sub-Zero a deux marqueurs allumés : le match est gagné 0–2. À 124, un nouveau match commence entre les mêmes combattants (0–0, chrono 83). L'observation est juste.

À 123, le passage de 1 à 2 manches donne la même variable qu'un gain de manche ordinaire (+0,693) ; rien ne dit que la cible est atteinte, et dans l'entraînement les captures « 2 manches » sont presque toutes des non-fins, la fin y ayant été posée sur la capture suivante. À 124, le gradient boosting monte à 0,869 (seuil 0,884) et le GRU à 0,505 (seuil 0,555, deux graines sur cinq) : cas de seuil. Les règles la trouvent à 124. Une variable « score = cible » et une place de fin harmonisée entre sessions la feraient trouver dès 123.

## Mortal_Kombat_1_f0067594_U21

Fin juste : à 135, Sub-Zero mène 0–1 (chrono 37) ; à 136, menu de pause avec « RECOMMENCER » en surbrillance ; à 137, les mêmes combattants repartent de 0–0 (chrono 74). Le match a été recommencé, compté comme une partie complète.

La pause entre les deux efface tout : score null et mode null à 136, donc aucune variation de score à 137, et la règle (a), qui regarde la capture juste avant, ne voit rien. Le gradient boosting a pourtant 0–1 et 0–0 dans sa fenêtre, mais seulement en valeurs brutes (0,18) ; sans la pause, la baisse du côté B est un motif qu'il trouve à 0,98 dans la même session. Cause principale : lecture coupée par la pause. Comparer le score à la dernière capture lisible et noter l'option choisie du menu de pause la feraient trouver.

## Mortal_Kombat_1_f0067594_U22

Fin juste : à 156, Sub-Zero tombe à 0 dans la troisième manche et Johnny Cage a deux marqueurs (2–1) ; à 157, un nouveau match commence entre les mêmes combattants (0–0, chrono 58). L'observation est juste.

Le gradient boosting (0,997 à 157) et les règles la trouvent avec une capture de retard. Le GRU reste à 0,033, alors qu'il trouve à 0,56–0,75 les autres retours directs 1–1 → 0–0 de la session. Juste avant, P2 est resté environ cinq minutes sur la liste des coups du menu de pause (onze captures, 142 à 152) ; à partir de là, toutes les probabilités du GRU restent entre 0,002 et 0,05 jusqu'à la capture 172. Cause principale, code nouveau `MEMOIRE_GRU` : la longue pause éteint l'état du GRU, qui ne réagit plus aux ruptures qui suivent (U22, U23, U24). Résumer les pauses longues ou en mettre à l'entraînement, et une variable « cible atteinte », sont les pistes.

## Mortal_Kombat_1_f0067594_U23

Fin juste : à 160, le chrono est à 0, Sub-Zero à 0 point de vie, Johnny Cage a deux marqueurs et le grand bandeau « FINISH HIM » est affiché ; à 161, écran de victoire avec le menu « REVANCHE / CHOIX DU PERSONNAGE / MENU PRINCIPAL » ; à 162, la revanche commence. En 158–159, les barres et la pose de Sub-Zero sont figées alors que le chrono tourne : un joueur ne jouait plus, la manche s'est finie au temps.

Le professeur n'a pas noté « FINISH HIM », qui n'apparaît qu'à la fin de la manche décisive (une Fatality marque toujours la fin du match). Le gradient boosting la trouve sur l'écran de victoire (0,972). Le GRU reste à 0,23 sur cet écran, contre 0,80–0,84 sur les autres écrans d'après-match de la session : il est encore éteint par la longue pause 142–152 (code `MEMOIRE_GRU`). Les règles la manquent, car la règle (c) traite post_game comme une phase de jeu et la règle (a) bute sur l'écran sans score.

## Mortal_Kombat_1_f0067594_U24

Fin juste : à 166, Sub-Zero mène 0–1 dans la deuxième manche ; à 167, P2 met le jeu en pause sur la liste des coups ; à 168, les mêmes combattants repartent de 0–0 (chrono 68), et Sub-Zero gagne la première manche de ce nouveau match à 170.

Comme en U21, la pause efface la variation de score : la règle (a) et les variables comparent 168 à la pause, sans score. Le gradient boosting a les valeurs brutes dans sa fenêtre mais reste à 0,13. Le GRU est encore éteint par la pause de cinq minutes de 142–152 (0,10 sur cette pause, contre 0,30–0,43 d'habitude). Cause principale : lecture coupée ; une variation calculée sur la dernière capture lisible la ferait trouver.

## Mortal_Kombat_1_f0067594_U25

Fin juste : la manche décisive est en cours à 1–1 (177), puis la console revient à son accueil (178), ouvre ses paramètres (179) et lance Fortnite (180). Le match est abandonné, compté comme partie complète. Posée sur l'accueil, la fin est défendable mais pas prouvée par cette seule capture : un accueil peut n'être qu'une sortie passagère, et pour l'abandon de fdb79549 U04 la fin a été posée sur le lancement du jeu suivant. Les deux sessions ne suivent donc pas la même règle.

Les règles la trouvent (passage d'active à menu). Le gradient boosting reste à 0,02 : dans l'entraînement, une capture sans titre après du jeu actif n'est presque jamais une fin (1 sur 36). Aucune variable de changement n'est calculée, car le titre devient null. Cause principale : abandon vers l'accueil de la console ; un type d'écran « accueil de la console » et une variable « le jeu disparaît » la rendraient lisible.

## Mortal_Kombat_1_f0067594_U33

Fin vraie mais posée une capture trop tard : à 389, Omni-Man mène 1–0 ; à 390, Peacemaker et son Kaméo Stryker posent sans HUD, ce qui est l'introduction d'avant-match de MK1 (il n'y en a pas entre deux manches) ; à 391, 0–0 avec les mêmes combattants. Le professeur a noté cette introduction comme une cinématique en phase active, au lieu de pre_game : la règle (c) et les modèles perdent le signe le plus net. La cinématique coupe aussi la variation de score à 391, et la baisse aurait de toute façon été du côté A. Le gradient boosting monte à 0,52 sur les seules valeurs brutes. Noter l'introduction en pre_game et calculer la variation sur la dernière capture lisible la feraient trouver.

## Mortal_Kombat_1_f0067594_U35

Fin juste : à 404, l'écran affiche « BRUTALITY — KITANA GAGNE » avec le menu « REVANCHE / CHOIX DU PERSONNAGE / MENU PRINCIPAL », puis vient la sélection des personnages (405–406). Le professeur a noté l'écran en menu / post_game, sans résultat, alors que « KITANA GAGNE », écrit avec le menu d'après-match, est un résultat explicite (`ECRAN_NON_MARQUE`). Seul, ce bandeau annonce aussi chaque manche gagnée (U57) : c'est le menu qui en fait une fin de match. Le GRU (0,804, cinq graines) et les règles (passage à pre_game en 405) la trouvent. Le gradient boosting s'arrête à 0,876 pour un seuil de 0,884 : le résultat marqué l'aurait fait passer. Lu sur la planche, où le texte est net.

## Mortal_Kombat_1_f0067594_U36

Fin juste : Kitana mène 1–0 à 411 (deuxième manche, chrono 76), puis la bannière « FIGHT » s'affiche à 90 (412), sans emplacements de manches encore dessinés, et 413–414 montrent 0–0 avec les mêmes combattants. La capture 412 seule pourrait être un début de troisième manche : c'est 413 qui prouve le nouveau match. Le score null de 412 coupe la comparaison, si bien que ni les variables ni la règle (a) ne relient le 1–0 au 0–0, et la baisse serait de toute façon du côté A. Comparer à la dernière capture lisible, et croiser un indicateur « début de manche » avec ce score, la ferait trouver.

## Mortal_Kombat_1_f0067594_U37

La fin de 423 est juste : à 422, la pause a « CHOIX DU PERSONNAGE » en surbrillance, et à 423 vient la sélection d'un autre combat (Cyrax contre Liu Kang). Les détecteurs la manquent à cause de la pause intercalée : la règle (c) ne part pas d'une phase paused, et la suite pause → sélection n'apparaît qu'une fois dans l'entraînement (gradient boosting 0,58, GRU 0,37, contre plus de 0,84 quand la sélection suit un combat). Constat plus grave : l'unité cache une fin manquée. Après le KO de la première manche (415) et une deuxième manche à 1–0 (416–417), la capture 418 montre 0–0 à 88 avec le marqueur de Kitana éteint, puis 420 affiche une nouvelle bannière « ROUND 2 ». Le match a donc été recommencé entre 417 et 418, et la lecture de 418, jugée isolée, était juste : il manque une frontière, soit une partie non comptée.

## Mortal_Kombat_1_f0067594_U38

Fin juste : Liu Kang mène 0–1 et Cyrax, à 205 points avec « FATAL BLOW » disponible, est près de perdre (428) ; à 429, le combat repart de 0–0 avec Cyrax intact. Le gradient boosting (0,981) et les règles la trouvent : la baisse du côté B est le motif de revanche qu'ils connaissent. Le GRU reste à 0,125 : dans cette session, il ne passe jamais le seuil sur un retour à 0–0 d'un seul côté. Il a besoin d'un écran qui change ou d'une double baisse. Lui donner une variable explicite de retour à 0–0 suffirait.

## Mortal_Kombat_1_f0067594_U39

Fin juste : Cyrax mène 1–0 et Liu Kang, à 52 points, peut encore placer son « FATAL BLOW » (433) ; à 434, les mêmes combattants repartent de 0–0. Ce cas forme une paire parfaite avec U38 : même session, mêmes combattants, même situation, mais la baisse est du côté A. Le gradient boosting passe de 0,981 (U38) à 0,289 (U39), le GRU reste bas dans les deux cas, et les règles trouvent les deux. Cause principale : l'asymétrie des côtés, à corriger par des variables symétriques ou par l'échange A/B à l'entraînement.

## Mortal_Kombat_1_f0067594_U42

Fin juste : dans la manche décisive, Sektor tombe à 0 sous le coup final de Kung Lao, dont le second marqueur s'allume (459, 1–2) ; viennent ensuite un écran de transition (460) et la sélection d'un autre combat (461). Le GRU (0,827) et les règles (passage à un menu) la trouvent à 460. Le gradient boosting s'arrête à 0,61, car le paysage de transition est moins net pour lui qu'une sélection. À 459, aucun modèle ne voit que la cible de deux manches est atteinte : une variable « score = cible » aurait annoncé la fin sur la capture même.

## Mortal_Kombat_1_f0067594_U44

Fin juste : Conan mène 0–1 et Li Mei, à 132 points avec « FATAL BLOW » disponible, est près de perdre (474) ; après une pause (475), le combat repart de 0–0, barres pleines (476). C'est le même schéma que U21 et U24 : la pause efface la variation de score, donc ni les modèles (GRU 0,16, gradient boosting 0,11) ni la règle (a) ne voient le retour à 0–0. Cause principale : lecture coupée. Une comparaison avec la dernière capture lisible la trouverait, et la baisse est du côté B, que le gradient boosting connaît.

## Mortal_Kombat_1_f0067594_U45

Fin juste : Conan mène 0–1 et Li Mei est presque à terre (481), puis le jeu passe par le paysage de transition (482) avant le choix des Kaméos d'un autre combat (483–484). Le joueur a quitté le match qu'il allait perdre. Le GRU (0,836) et les règles la trouvent. Le gradient boosting s'arrête à 0,811 pour un seuil de 0,884 : cas de seuil, avec un écran de transition qu'il connaît moins bien qu'une sélection.

## Mortal_Kombat_1_f0067594_U46

Fin juste : la manche décisive est en cours à 1–1 (489), puis la bannière « ROUND 1 » s'affiche avec les combattants et leurs Kaméos en position de départ (490), et le compteur repart de 0–0 (491). Le professeur n'a pas noté « ROUND 1 » (période unknown, score null), alors que c'est une preuve directe de nouveau match. Comme la capture 490 n'a pas de score, ni la règle (a) ni les variables de baisse ne voient le 1–1 → 0–0. Le gradient boosting monte à 0,51 sur les seules valeurs brutes. Noter le numéro des bannières de manche et comparer à la dernière capture lisible la feraient trouver ; la planche suffisait, la bannière y est lisible.

## Mortal_Kombat_1_f0067594_U49

Fin juste : Geras mène 0–1 (513, chrono 59) ; à 514, la pause a « RECOMMENCER » en surbrillance ; à 515, 0–0 à 62. Un chrono qui remonte de 59 à 62 ne peut pas appartenir à la même manche, et le KO de la première manche du nouveau match à 516 (Reiko à 0, premier marqueur de Geras) confirme la lecture. Comme dans U21, U24 et U44, la pause efface la baisse de score : gradient boosting 0,39, GRU 0,17, règle (a) muette. Une variation calculée sur la dernière capture lisible, score et chrono de manche, la trouverait.

## Mortal_Kombat_1_f0067594_U50

Fin juste : Geras mène 0–1 dans la deuxième manche (518–519), P1 met en pause sur la liste des coups (520), puis le combat repart de 0–0 à 82 avec des barres presque pleines (521). C'est le deuxième recommencement de suite entre Reiko et Geras, toujours avec une pause entre les deux. Même mécanisme que U49 : la pause coupe la comparaison, et les modèles (0,14 et 0,44) comme les règles restent muets.

## Mortal_Kombat_1_f0067594_U52

Fin juste : la manche décisive est à 1–1 (534) ; à 535, le décor gris vient du pouvoir du temps de Geras (son sablier en bas à droite), pas d'un « Finish Him », et le combat continue ; à 536, l'écran de transition mène à la sélection d'un autre combat (537–538). Le GRU (0,623) et les règles la trouvent. Le gradient boosting reste à 0,29 sur un écran qu'il note 0,61 ou 0,81 ailleurs : avec seulement deux captures de contexte, une capture sans score et une pause juste avant suffisent à le faire douter. Un type d'écran propre à cette transition, qui n'apparaît qu'en sortie de match, lui éviterait cette confusion.

## Mortal_Kombat_1_f0067594_U53

Fin juste : Li Mei mène 1–0 (545) ; une manette se déconnecte et le jeu s'arrête sur une pause avec la boîte « Veuillez reconnecter la manette… » (546) ; le combat repart de 0–0 avec les mêmes combattants (547–548). La pause efface la variation, et la baisse serait de toute façon du côté A : gradient boosting 0,29, GRU 0,10, règle (a) muette. Cause principale : lecture coupée. Comparer à la dernière capture lisible, avec des variables symétriques, la ferait trouver.

## Mortal_Kombat_1_f0067594_U54

La fin est vraie mais posée deux captures trop tard. Dès 549, la boîte « Veuillez reconnecter la manette… » s'affiche sur l'écran de sélection, assombri mais reconnaissable (noms et grille des portraits) : le combat de 547–548 est déjà quitté. L'étiquette met la fin sur 551, la sélection suivante, après un passage par le menu principal (550). Le GRU (0,723, cinq graines) et les règles l'annoncent sur 549, hors de la tolérance : ils sont comptés comme ayant manqué la fin, alors qu'ils avaient raison. À 551, plus aucun détecteur ne réagit, car une sélection après un menu n'est jamais une fin dans l'entraînement. Il faut corriger l'étiquette par une trace (fin sur 549).

## Mortal_Kombat_1_f0067594_U57

Fin juste : après le bandeau « MILEENA GAGNE » de la première manche (570) et une deuxième manche à 1–0 (571), la bannière « ROUND 1 » s'affiche avec les combattants et leurs Kaméos en position de départ (572) : le match est recommencé. Comme en U46, le professeur n'a pas noté « ROUND 1 », et la capture sans score coupe la comparaison 1–0 → 0–0 (baisse du côté A, de surcroît) ; aucun détecteur ne passe 0,33. Ce cas montre aussi que « X GAGNE » seul annonce une manche, pas un match. Tout est lisible sur la planche.

## Mortal_Kombat_1_f0067594_U64

Fin juste : la manche décisive est à 1–1 (616, chrono 25), puis le même duel repart de 0–0 à 78 (617). La double baisse est directe, le motif que le gradient boosting trouve à 0,98–0,997 ailleurs dans la session ; ici il s'arrête à 0,575 et le GRU à 0,438. La seule différence est la pause de P2 deux captures plus tôt (615), qui entre dans la fenêtre du gradient boosting et dans la mémoire récente du GRU. Les règles la trouvent. Neutraliser les pauses dans le contexte des modèles, ou leur donner la sortie de la règle (a), la ferait passer.

## Mortal_Kombat_1_f0067594_U65

Fin juste : la manche décisive est à 1–1 (626), puis le centre de contrôle de la PS5 s'ouvre par-dessus le combat (627), suivi du changement d'utilisateur (628), de l'accueil (629) et d'autres jeux (Naruto, EA FC). Le match est abandonné. La fin est posée sur le centre de contrôle, qui laisse encore le jeu tourner : la preuve ferme vient une ou deux captures plus tard. Le GRU (0,703) et les règles la trouvent. Le gradient boosting s'arrête à 0,626, car une capture sans titre après du jeu est rarement une fin dans l'entraînement. Les noms d'utilisateurs de 628 ne sont pas repris ici.

## Synthèse du lot

25 fins de Mortal Kombat 1, toutes dans f0067594. Le GRU en trouve 5, le gradient boosting 3, la régression
logistique aucune, les règles 12 ; 12 fins sont manquées par les quatre (U21, U24, U33, U36, U37, U44, U46, U49,
U50, U53, U54, U57). 23 étiquettes sont justes, 2 sont douteuses (U33 posée une capture trop tard, U54 deux captures
trop tard), et l'unité U37 cache une fin manquée à l'étiquetage.

Causes principales : `LECTURE_COUPEE` 11, `SEUIL` 3, `ASYMETRIE_COTES` 2, `MEMOIRE_GRU` 2, `ABANDON` 2,
`ECRAN_NON_MARQUE` 1, `REPRISE` 1, `SIGNE_PROPRE_AU_JEU` 1, `MENU_AMBIGU` 1, `ETIQUETTE_DOUTEUSE` 1. `REPRISE` est
présente comme cause secondaire dans 14 cas : presque toutes ces fins sont des revanches ou des matchs recommencés
entre les mêmes combattants.

Deux codes nouveaux :

- `ASYMETRIE_COTES` : la rupture se lit sur un côté (score.a seul) alors que les exemples d'entraînement de cette
  rupture sont tous de l'autre côté. Les variables par côté ne sont pas symétrisées, et le modèle ne généralise pas
  de B vers A.
- `MEMOIRE_GRU` : après une longue suite de captures identiques (ici une pause de cinq minutes, onze captures), l'état
  du GRU s'éteint, et ses probabilités restent proches de 0 pendant des dizaines de captures, ruptures comprises.

### Les familles de causes vues

1. **La capture du milieu efface la rupture (11 cas).** Le retour 1–0 → 0–0 est visible pour un humain, mais une
   capture sans score s'intercale : une pause (U21, U24, U44, U49, U50, U53, U37), l'introduction d'avant-match
   (U33), la bannière « FIGHT » ou « ROUND 1 » (U36, U46, U57). Les variations ne se calculent que par rapport à la
   capture juste avant, et la règle (a) aussi : tout disparaît. Le gradient boosting a pourtant les deux scores dans
   sa fenêtre en valeurs brutes, et monte à 0,3–0,5 sans jamais passer le seuil.
2. **L'asymétrie A/B.** Dans les 24 sessions d'entraînement de ce tour, toutes les revanches d'un seul côté sont du
   côté B (0–1 → 0–0) ; aucune baisse du côté A seul n'y est une fin. Résultat dans cette session : les revanches
   directes 0–1 → 0–0 sont trouvées par le gradient boosting à 0,82–0,98 (U04, U07, U11, U12, U17, U38), les 1–0 →
   0–0 directes restent à 0,06–0,35 (U06, U08, U18, U39). La paire U38/U39 (mêmes combattants, mêmes conditions,
   0,981 contre 0,289) le montre sans ambiguïté.
3. **La cible atteinte n'est pas une variable.** Sur les captures où le second marqueur s'allume (U19, U22, U23,
   U42), le passage de 1 à 2 manches donne la même variable qu'un gain de manche ordinaire. De plus, f0067594 pose la
   fin sur cette capture, alors que 8e58b139 et Tekken 8 la posent sur la suivante : dans l'entraînement, « 2
   manches » est presque toujours une non-fin.
4. **Le GRU éteint par la longue pause** (U22, U23, U24) : de 144 à 172, toutes ses probabilités restent sous 0,05
   (sauf un 0,23), y compris sur un écran de victoire qu'il note 0,80–0,84 ailleurs. En dehors de cet effet, le GRU
   ne passe jamais le seuil sur un retour à 0–0 d'un seul côté (U18, U38, U39) : il lui faut un écran qui change ou
   une double baisse.
5. **Seuils et contexte du gradient boosting** (U19, U35, U45, U64, U52) : 0,869, 0,876 et 0,811 pour un seuil de
   0,884 ; et la même double baisse directe tombe de 0,98 à 0,575 quand une pause entre dans sa fenêtre (U64). Le même
   écran de transition vers la sélection vaut 0,29, 0,61 ou 0,81 selon les deux captures d'avant.
6. **Abandons vers la console** (U25, U65) : l'accueil ou le centre de contrôle de la PS5 n'ont pas de type d'écran
   propre, et le titre devenu null empêche toute variable de changement de jeu.

### Ce qui m'a surpris

- **Les détecteurs avaient raison et l'étiquette tort (U54).** Dès 549, la boîte « manette déconnectée » s'affiche
  sur l'écran de sélection : le GRU (cinq graines) et les règles annoncent la fin là, mais l'étiquette la pose deux
  captures plus loin. Ils sont comptés comme ayant manqué une fin, et sans doute comme ayant annoncé une fausse fin.
- **Une fin manquée à l'étiquetage (U37).** À 418, le 0–0 jugé « lecture isolée » était juste : le marqueur de Kitana
  est éteint, et la bannière « ROUND 2 » revient à 420 alors que la deuxième manche avait déjà eu lieu (416–417). Le
  match a été recommencé, et il manque une frontière, donc une partie non comptée.
- **Le professeur ne note pas les bannières de manche** (« ROUND 1 » en U46 et U57) ni l'introduction d'avant-match
  (U33, notée en phase active) : ce sont pourtant les preuves les plus directes d'un nouveau match dans MK1. Il ne
  note pas non plus « FINISH HIM » (U23). Il n'a manqué qu'un seul vrai écran de fin (« BRUTALITY — KITANA GAGNE »,
  U35).
- **« X GAGNE » seul ne termine pas le match** : le bandeau s'affiche après chaque manche gagnée (U57, capture 570).
  C'est le menu d'après-match (REVANCHE / CHOIX DU PERSONNAGE) ou la Brutality / Fatality qui en font une fin.
- **Le comportement des joueurs** : presque tous les recommencements viennent du joueur qui va perdre, quand son
  adversaire mène d'une manche et qu'il a lui-même peu de vie (« FATAL BLOW » disponible, donc moins de 30 % de vie :
  U38, U39, U44, U45, U53). Les déconnexions de manette (U53, U54) précèdent aussi des relances et des abandons.
- Le décor gris n'est pas toujours un « Finish Him » : en U52 c'est le pouvoir du temps de Geras.

### Les méthodes qui reviennent

1. **Comparer à la dernière capture lisible** du même jeu et des mêmes combattants (score, chrono de manche, phase),
   avec le nombre de captures sautées comme variable, et appliquer la même base à la règle (a) et à la règle (c)
   (combat → pause → sélection = combat → sélection). C'est la méthode qui toucherait le plus de cas : les 11
   lectures coupées, plus U37.
2. **Symétriser les variables de score** (variation du total, « un côté baisse », « retour à 0–0 depuis un total
   > 0 »), ou doubler l'entraînement en échangeant A et B.
3. **Donner aux modèles la sortie des règles** (a) et (c) comme variables : les règles trouvent 12 des 25 fins, dont
   10 que le gradient boosting manque.
4. **Une variable « cible de manches atteinte »** (score = target), et une place commune pour la fin sur la capture
   où le dernier marqueur s'allume, dans toutes les sessions.
5. **Conventions du professeur pour MK1** : noter le numéro des bannières « ROUND n » (period round n), l'introduction
   d'avant-match en pre_game, « FINISH HIM », l'option en surbrillance du menu de pause (« RECOMMENCER », « CHOIX DU
   PERSONNAGE »), un type d'écran pour l'accueil et le centre de contrôle de la console, et un indicateur « manette
   déconnectée » ; garder le mode et les combattants connus sur les pauses du même jeu.
6. **Pour le GRU** : résumer ou neutraliser les longues pauses, ou en mettre à l'entraînement par augmentation.
7. **Étiquettes à corriger par des traces**, après validation de l'auteur : U54 (fin sur 549), U33 (fin sur 390),
   frontière manquante à 418 (dans U37).
