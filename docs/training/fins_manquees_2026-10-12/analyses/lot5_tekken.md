# Lot 5 : Tekken 8 (session 078643a4)

## Tekken_8_078643a4_U01

Le match Reina contre Eddy en est à 0–1 (une pastille allumée côté Eddy, chrono 74) sur la capture 18. La capture 19
montre l'écran « BRYAN VS EDDY » : le joueur de gauche a pris un autre combattant, un nouveau match commence, et la
capture 20 affiche « WIN 1 » sous Eddy, preuve que le joueur de droite a gagné. L'étiquette est juste et
l'observation correcte. Les variables portent un signal net sur 19 (participants changés, phase active → avant-partie) :
la règle (c) la trouve. Le gradient boosting monte à 0,84, sous son seuil de 0,97 ; le GRU, qui n'a jamais vu Tekken,
reste à 0,19. Cause principale : `SEUIL` ; secondaire : `JEU_RARE`. (Recadrages du HUD en taille réelle : 16, 17, 18,
20.)

## Tekken_8_078643a4_U02

Sur la capture 23, Eddy, à droite, a gagné la première manche (0–1) et la deuxième commence (chrono
88), avec « WIN 1 » sous lui. La capture 24 montre Eddy seul, sans HUD (pose de victoire ou présentation, rien ne
permet de trancher). Sur 25, un nouveau match commence à 0–0, les combattants ont changé de côté et « WINS 2 » est
affiché à droite : le joueur de droite a gagné ce match aussi. L'étiquette est juste et l'observation correcte.
Le problème est dans le calcul : la capture 24, sans score ni compteur, sert de « précédente » et efface le retour à
0–0 comme le passage WIN 1 → WINS 2. Les règles et le GRU (0,04) ne voient rien ; le gradient boosting, qui voit les
trois captures côte à côte, monte à 0,95 pour un seuil de 0,97. Cause principale : `LECTURE_COUPEE` ; secondaires :
`SEUIL`, `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Tekken_8_078643a4_U03

Les captures 30 et 31 montrent la manche décisive à 1–1. La capture 32 est l'écran d'après-match de Tekken 8 : Bryan
en pose de victoire, son nom en grandes lettres, et le menu « Revanche / Choisir un personnage / … ». La revanche
commence en 33 avec « WINS 3 » à droite. L'étiquette est juste. Le professeur a noté 32 comme un menu en phase
intermediate, sans résultat, faute de texte « vainqueur » explicite : ce menu n'apparaît pourtant qu'après un match et
devrait être post_game. Comme intermediate compte comme une phase de jeu, la règle (c) ne se déclenche pas, et 32,
sans score ni compteur, efface sur 33 le retour à 0–0 et le passage à WINS 3. GRU 0,17, gradient boosting 0,73.
Cause principale : `ECRAN_NON_MARQUE` ; secondaires : `LECTURE_COUPEE`, `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Tekken_8_078643a4_U04

Bryan prend la première manche par K.O. (capture 35), la deuxième se joue à 0–1 (36–37), puis la revanche commence
à 0–0 en 38 avec « WINS 4 » à droite : Bryan a gagné 2–0. Étiquette juste, observations exactes. Le signal est le plus
net qu'on puisse avoir : sur 38, le score de droite baisse de 1 et le compteur de séries monte de 1, en même contexte.
La règle (a) et le gradient boosting (0,991) la trouvent ; seul le GRU la manque (0,07). C'est une revanche immédiate,
mêmes combattants, sans écran de fin : la famille où le GRU tombe à 22 %. Le compteur series ne lui sert à rien, car
il n'existe dans aucun autre enregistrement. Cause principale : `REPRISE` ; secondaires : `SIGNE_PROPRE_AU_JEU`,
`JEU_RARE`.

## Tekken_8_078643a4_U05

La manche décisive se joue à 1–1 (captures 42 à 44). La capture 45 montre le menu d'après-match, sous-menu
« Sélection rapide » ouvert (Joueur 1 EDDY, Joueur 2 BRYAN), sur un fond où « BRYAN », le vainqueur, est écrit en
grand. En 46, le joueur 2 choisit Reina ; en 48, « WINS 5 » reste à droite : la série suit le joueur, pas le
combattant. L'étiquette est juste. Comme en U03, le professeur note ce menu en phase intermediate sans résultat. Sur
45, aucune variable ne bouge ; le gradient boosting monte à 0,92 (seuil 0,97), le GRU à 0,12. Les règles la
trouvent une capture plus tard, au passage intermediate → pre_game de l'écran de sélection. Cause principale :
`ECRAN_NON_MARQUE` ; secondaires : `SEUIL`, `JEU_RARE`.

## Tekken_8_078643a4_U06

La manche décisive commence à 1–1 (capture 55) ; en 56, le Rage Art de Reina cache la pastille de gauche et le chrono.
En 57, la revanche commence à 0–0 et « WIN 1 » s'affiche sous Shaheen : le joueur de gauche a gagné et coupé la série de
cinq victoires du joueur de droite. Étiquette juste, observation correcte. Seul le score de droite donne une variation
(−1) ; celui de gauche n'est pas comparable, et le passage du compteur de droite à gauche ne produit aucune variation,
car le calcul compare la même case. Le gradient boosting la trouve (0,989). La règle (a) la manque à cause du score
masqué en 56, et le GRU (0,09) ne voit qu'une revanche sans écran de fin. Cause principale : `REPRISE` ; secondaires :
`SIGNE_PROPRE_AU_JEU`, `LECTURE_COUPEE`, `JEU_RARE`.

## Tekken_8_078643a4_U07

La manche décisive commence à 1–1 (capture 61). En 62, Reina apparaît seule, sans HUD : c'est très probablement sa
présentation au début du match suivant, puisque le vainqueur est Shaheen. En 63, la revanche est à 0–0 avec « WINS 2 »
à gauche. Étiquette juste. La capture 62 est notée cinématique, phase unknown et mode null : elle ne porte aucun score,
et son mode manquant rompt le contexte. Aucune variation n'est donc calculée sur 63, et la règle (c) ne joue pas
(phase unknown). Le gradient boosting la trouve de justesse (0,973 pour 0,97), le GRU réagit à la cinématique (0,32)
sans atteindre 0,48. Cause principale : `LECTURE_COUPEE` ; secondaires : `REPRISE`, `ERREUR_OBSERVATION` (mode null),
`JEU_RARE`.

## Tekken_8_078643a4_U08

En 64, les deux barres de vie sont presque vides (0–0, chrono 59). En 65, Shaheen dit « Cette victoire ne me procure
aucune joie » : c'est sa réplique de fin de match. Suivent l'écran « EDDY VS BRYAN » (66) et « WINS 3 » à gauche
(67). Étiquette juste. Le professeur a bien noté 65 comme résultat d'après-partie (vainqueur null, aucun nom écrit),
seul le mode manque. C'est la seule fin de ce lot que le GRU trouve (5 graines sur 5, 0,754), et c'est aussi la seule
dont l'écran de fin est marqué comme un résultat. Les règles la trouvent une capture plus tard (post_game →
pre_game). Le gradient boosting monte à 0,853 pour un seuil de 0,97. Cause principale : `SEUIL` ; secondaire :
`JEU_RARE`.

## Tekken_8_078643a4_U09

La manche décisive est à 1–1 en 72 (chrono 66). Douze secondes plus tard, la capture 73 montre Eddy en gros plan avec
son berimbau, sans HUD : le délai est trop court pour un menu et une revanche, c'est sans doute sa pose de victoire.
En 74, le nouveau match est à 0–0 avec « WINS 4 » à gauche. Étiquette juste (73 ne prouve rien seule, faute de texte).
La capture 73 a un titre de jeu null : le contexte est rompu et aucune variation n'est calculée sur 74, ni par les
règles (a), (c), (d). Le gradient boosting la trouve (0,994), le GRU non (0,32 puis 0,08). Cause principale :
`LECTURE_COUPEE` ; secondaires : `REPRISE`, `ERREUR_OBSERVATION` (titre null), `JEU_RARE`.

## Tekken_8_078643a4_U10

Eddy mène 1–0 dans la deuxième manche (capture 76). La capture 77 montre la bannière « ROUND » d'ouverture, le chrono à
99, les étiquettes P1/P2 et « WINS 5 » à gauche : Eddy a gagné 2–0 et la revanche commence. Étiquette juste,
observation correcte (les pastilles sont masquées par l'animation). Le seul signal calculé est la hausse de 1 du
compteur de séries. Or ce compteur n'existe dans aucun autre enregistrement : aucun modèle n'a appris à s'en servir
(GRU 0,04, gradient boosting 0,33). Le retour à 0–0 n'apparaît jamais d'une capture à la suivante, puisque 77 n'a pas
de score. La remontée du chrono n'est pas calculée non plus, car le numéro de manche de Tekken est toujours inconnu.
Cause principale : `SIGNE_PROPRE_AU_JEU` ; secondaires : `LECTURE_COUPEE`, `CONTEXTE_SANS_VARIATION`, `REPRISE`,
`JEU_RARE`.

## Tekken_8_078643a4_U11

La manche décisive est à 1–1 (80–81). La capture 82 montre Eddy en gros plan, sans HUD : c'est sa présentation au
début du match suivant, puisque Bryan a gagné. En 83, la revanche commence à 0–0 et « WIN 1 » s'affiche sous Bryan : la
série de cinq d'Eddy s'arrête. Étiquette juste. Comme en U09, la capture intermédiaire n'a pas de titre de jeu : le
contexte est rompu et rien n'est calculé sur 83. Même sans cette coupure, le passage du compteur de gauche à droite ne
donnerait aucune variation. Gradient boosting 0,986 (trouvée), GRU 0,32 puis 0,09, règles muettes. Cause principale :
`LECTURE_COUPEE` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `REPRISE`, `ERREUR_OBSERVATION`, `JEU_RARE`.

## Tekken_8_078643a4_U12

Le match commence à 0–0 en 83 ; en 84, la bannière « ROUND 2 » cache les pastilles ; en 85, une cinématique d'attaque
spéciale cache tout le HUD. En 86, le score est 0–0 avec « WINS 2 » à droite : Bryan a gagné 2–0 et la revanche a
commencé. Étiquette juste, observations correctes. Aucune pastille allumée n'a été lue pendant ce match : le seul
indice de la fin dans les observations est la hausse de 1 du compteur de séries. Ni les modèles (GRU 0,04, gradient
boosting 0,57) ni les règles ne savent s'en servir. Cause principale : `SIGNE_PROPRE_AU_JEU` ; secondaires :
`REPRISE`, `LECTURE_COUPEE`, `JEU_RARE`.

## Tekken_8_078643a4_U13

Bryan mène 0–1 dans la deuxième manche (87), puis la revanche commence à 0–0 avec « WINS 3 » à droite (88) : il a
gagné 2–0. Étiquette juste, observations exactes, et le signal est le même que pour U04 : score de droite −1 et
compteur de séries +1, en même contexte. La règle (a) la trouve ; le gradient boosting s'arrête à 0,947 (seuil 0,97)
et le GRU à 0,05, comme pour toutes les revanches sans écran de fin. Cause principale : `REPRISE` ; secondaires :
`SEUIL`, `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Tekken_8_078643a4_U14

Eddy mène 1–0 en 90. La capture 91 montre l'écran d'après-match, avec « BRYAN » en grand et le menu « Revanche… » :
Bryan a renversé le match. Suivent la présentation d'Eddy (92), puis « WINS 4 » à droite (93). Étiquette juste. Cette
fois le professeur a noté l'écran en phase menu, non plus intermediate comme en U03 et U05 : la règle (c) la trouve.
Comme aucun résultat n'est marqué, le GRU (0,20) et le gradient boosting (0,47) n'y voient qu'une pause. Cause
principale : `ECRAN_NON_MARQUE` ; secondaires : `LECTURE_COUPEE`, `JEU_RARE`.

## Tekken_8_078643a4_U15

La manche décisive est à 1–1 (95–96) ; 45 s plus tard, la capture 97 montre la sélection des personnages, et le match
suivant affichera « WIN 1 » à gauche : Eddy a gagné et coupé la série de quatre. L'écran d'après-match n'a pas été
capturé. Étiquette juste, observation correcte : participants changés et passage à l'avant-partie. La règle (c) la
trouve ; le gradient boosting la manque de 0,002 (0,968 pour 0,97) ; le GRU reste à 0,24. Cause principale : `SEUIL` ;
secondaire : `JEU_RARE`.

## Tekken_8_078643a4_U16

Eddy mène 1–0 au début de la deuxième manche (102). En 103, l'écran d'après-match montre son portrait, « EDDY » en
grand et le menu « Revanche… » ; la revanche commence en 104 avec « WINS 2 » à gauche. Étiquette juste. L'écran est noté
menu sans résultat, avec un mode null : la règle (c) le trouve, le GRU monte à 0,41 (une graine sur cinq) et le
gradient boosting à 0,52. Marqué comme résultat, cet écran aurait sans doute suffi, comme en U08. Cause principale :
`ECRAN_NON_MARQUE` ; secondaires : `SEUIL`, `LECTURE_COUPEE`, `JEU_RARE`.

## Tekken_8_078643a4_U17

Eddy mène 1–0 en 106 ; en 107, il apparaît en gros plan avec la réplique « Tu pourrais améliorer ton jeu de jambes ».
En 108, la revanche est à 0–0 avec « WINS 3 » à gauche. Entre 107 et 108, il ne s'écoule que 18 s, dont 14 s de
manche : 107 est donc la présentation du nouveau match, pas une réplique de victoire (confiance moyenne sur ce point).
Le professeur l'a notée intermediate, ce qui empêche la règle (c) de jouer, et cette capture sans score efface sur 108
le retour à 0–0 et la hausse du compteur. GRU 0,06, gradient boosting 0,68. Cause principale : `LECTURE_COUPEE` ;
secondaires : `ERREUR_OBSERVATION`, `REPRISE`, `JEU_RARE`.

## Tekken_8_078643a4_U18

Hwoarang mène 0–1 dans la deuxième manche (110–111) ; en 112, la revanche est à 0–0 et « WIN 1 » est passé sous lui :
il a gagné 2–0 et coupé la série de trois d'Eddy. Étiquette juste. Sur 112, le nom de Hwoarang est en partie caché,
d'où un faux changement de participants, sans conséquence ici. La règle (a) la trouve et le gradient boosting monte à
0,959 (seuil 0,97). Le GRU (0,08) ne voit qu'une revanche, et le passage du compteur à droite ne produit aucune
variation. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Tekken_8_078643a4_U19

Hwoarang mène 0–1 au début de la deuxième manche (113). En 114, l'écran d'après-match affiche son portrait, son nom en
grand et le menu « Revanche… », puis les joueurs quittent vers l'accueil de la PS5. Étiquette juste. L'écran est noté
menu, sans résultat : la règle (c) le trouve, le GRU monte à 0,41 et le gradient boosting à 0,50. Cause principale :
`ECRAN_NON_MARQUE` ; secondaires : `SEUIL`, `JEU_RARE`.

## Tekken_8_078643a4_U20

La manche décisive commence à 1–1 en 130 ; en 131, la revanche est à 0–0 avec « WINS 2 » à droite : Hwoarang a gagné
2–1. Étiquette juste, observations exactes. Le signal est le plus complet du lot : les deux scores baissent de 1 et le
compteur monte de 1, sans capture intermédiaire. La règle (a) et le gradient boosting (0,999) la trouvent. Le GRU
reste à 0,10 : c'est le cas le plus net de son aveuglement aux revanches sans écran de fin. Cause principale :
`REPRISE` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Tekken_8_078643a4_U21

La manche décisive commence à 1–1 en 138. En 139, Bryan apparaît en gros plan sans HUD : c'est sa présentation au
match suivant, puisque 26 s plus tard la manche en est déjà à 19 s de jeu. En 140, « WIN 1 » est passé sous Bryan.
Étiquette juste. La capture 139 est notée en jeu actif, sans score : elle efface le retour à 0–0 et empêche la règle
(c) de jouer. Le compteur change de côté, ce qui ne donne aucune variation. GRU 0,07, gradient boosting 0,64.
Cause principale : `LECTURE_COUPEE` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `ERREUR_OBSERVATION`, `REPRISE`, `JEU_RARE`.

## Tekken_8_078643a4_U22

Hwoarang mène 0–1 dans la deuxième manche (142). Après un écran noir (143), un nouveau match apparaît, assombri, à
0–0 avec « WIN 1 » passé sous Hwoarang (144) : il a gagné 2–0. Étiquette juste, observations correctes. L'écran noir
sert de « précédente » et coupe toutes les variations ; le changement de côté du compteur n'en produirait de toute façon
aucune. Le gradient boosting monte à 0,935 (seuil 0,97), le GRU à 0,25 sur l'écran noir. Cause principale :
`LECTURE_COUPEE` ; secondaires : `SEUIL`, `SIGNE_PROPRE_AU_JEU`, `REPRISE`, `JEU_RARE`.

## Tekken_8_078643a4_U23

La revanche commence en 144 (0–0, image assombrie), puis 145 montre le fond flou de la sélection des personnages et 146
la sélection du décor. En 147, Bryan affronte Victor et la série de droite n'a pas bougé : la revanche a été quittée
sans vainqueur. L'étiquette est juste, même si la capture 145 prouvait déjà la fin. Le professeur a noté 145
« other / intermediate » : la règle (c) ne joue donc qu'en 146, encore dans la tolérance, tandis que GRU (0,14) et
gradient boosting (0,40) restent bas. Cause principale : `ABANDON` ; secondaires : `ERREUR_OBSERVATION`, `JEU_RARE`.

## Tekken_8_078643a4_U24

La manche décisive est à 1–1 (150–151) ; en 152, la revanche est à 0–0 et « WIN 1 » est passé sous Bryan, vainqueur
2–1. Étiquette juste, observations exactes. Les deux scores retombent de 1 en même contexte : la règle (a) et le
gradient boosting (0,999) la trouvent, le GRU non (0,15), comme pour toutes les revanches sans écran de fin. Cause
principale : `REPRISE` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Tekken_8_078643a4_U25

En 154, la bannière « K.O. » s'affiche, la barre de Victor est vide et la deuxième pastille de Bryan s'allume : 2–0,
le match est fini sur cette capture. La fin est pourtant posée en 155 (revanche, « WINS 2 »), une capture trop tard :
étiquette douteuse. Le professeur a bien noté 154 comme résultat K.O. à 2–0. Le gradient boosting monte à 0,93 sur 154
(sous 0,97, et sur l'intervalle qui précède la fin étiquetée) ; la règle (a) la trouve en 155 grâce au placement
tardif ; le GRU ne réagit pas (0,09). Une variable « un score atteint l'objectif de manches » montrerait 154
directement. Cause principale : `ETIQUETTE_DOUTEUSE` ; secondaires : `SEUIL`, `JEU_RARE`.

## Tekken_8_078643a4_U26

La manche décisive est à 1–1 (158–159). En 160, Bryan apparaît en gros plan sans HUD ; en 161, le score est 1–0 au
chrono 73 et « WIN 1 » est passé à droite : le joueur de droite a gagné, et la revanche en est déjà à sa deuxième
manche. Étiquette juste. Le retour à 0–0 n'a jamais été capturé, et 160, notée à tort en jeu actif, n'a aucun score.
Seul le changement de côté du compteur trahit la fin, et rien ne le calcule (GRU 0,06, gradient boosting 0,39, règles
muettes). Cause principale : `SIGNE_PROPRE_AU_JEU` ; secondaires : `LECTURE_COUPEE`, `REPRISE`, `ERREUR_OBSERVATION`,
`JEU_RARE`.

## Tekken_8_078643a4_U27

Bryan prend la première manche par K.O. (161) ; la deuxième se joue à 1–0 (162). En 163, il apparaît en gros plan avec
sa mitrailleuse (pose de victoire probable), puis l'écran d'après-match « BRYAN » s'affiche avec le menu de revanche
(164) : il a gagné 2–0. Étiquette juste. L'écran 164 est noté menu, sans résultat : la règle (c) le trouve, mais le
GRU (0,16) et le gradient boosting (0,77) n'y voient qu'un menu. Cause principale : `ECRAN_NON_MARQUE` ; secondaire :
`JEU_RARE`.

## Tekken_8_078643a4_U28

La manche décisive se joue à 1–1 (170 à 172) ; en 173, la revanche est à 0–0 et « WIN 1 » est passé sous Steve,
vainqueur 2–1. Étiquette juste, observations exactes. Les deux scores retombent en même contexte : la règle (a) et le
gradient boosting (0,999) la trouvent, le GRU reste à 0,13. Cause principale : `REPRISE` ; secondaires :
`SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Tekken_8_078643a4_U29

Steve mène 0–1 dans la deuxième manche (175–176). En 177, un menu de pause couvre un HUD encore lisible : chrono 99,
0–0 et « WINS 2 » à droite. Steve a gagné 2–0 et la revanche, à peine lancée, est en pause. Étiquette juste ; le
professeur a lu le HUD sous le menu, ce qui garde la baisse du score et la hausse du compteur. La règle (a) la trouve,
le gradient boosting s'arrête à 0,93 (seuil 0,97) et le GRU à 0,05 : mêmes combattants, pas d'écran de fin, et une
pause qui ressemble à une interruption. Cause principale : `REPRISE` ; secondaires : `MENU_AMBIGU`, `SEUIL`,
`SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Tekken_8_078643a4_U30

La manche décisive commence à 1–1 (182). En 183, la barre de Steve est vide et les deux pastilles de Bryan sont
allumées : 2–1, le match se termine sur cette capture. La fin est posée en 184 (revanche, « WIN 1 » passé à gauche),
une capture trop tard, ce qui reste dans la tolérance des détecteurs. Le gradient boosting (0,994) et la règle (a) la
trouvent en 184 grâce à la remise à zéro ; sur 183, le gradient boosting n'est qu'à 0,04, car aucune variable ne
compare le score à l'objectif de manches. Le GRU reste à 0,21. Cause principale : `REPRISE` ; secondaires :
`ETIQUETTE_DOUTEUSE`, `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Tekken_8_078643a4_U31

Steve prend la première manche par K.O. (185) et mène 0–1 dans la deuxième (186). En 187–188, l'écran d'après-match
montre Bryan en gros plan avec le menu « Revanche… », sans nom écrit, puis les joueurs reviennent à l'accueil de la PS5.
Étiquette juste. Le menu est noté menu, sans résultat : la règle (c) le trouve, le GRU (0,13) et le gradient boosting
(0,09) non. À l'inverse, la bannière « K.O. » de la première manche a été notée comme un résultat d'après-partie : le
gradient boosting monte à 0,86 en plein match. Cause principale : `ECRAN_NON_MARQUE` ; secondaires :
`ERREUR_OBSERVATION`, `JEU_RARE`.

## Synthèse du lot 5 (Tekken 8, 31 fins, session 078643a4)

**Ce que trouvent les détecteurs.** Sur les 31 fins, le GRU n'en trouve qu'une (U08), le gradient boosting 9, la
régression logistique aucune, les règles 19. Les règles et le gradient boosting réunis en trouvent 23 ; 8 sont manquées
par les quatre (U02, U03, U10, U12, U17, U21, U22, U26). Le gradient boosting monte entre 0,917 et 0,968 sur 7 autres
fins (U02, U05, U13, U15, U18, U22, U29), sous le seuil de 0,97 de son tour. 29 étiquettes sont justes, 2 douteuses
(U25, U30) : le K.O. final, avec deux pastilles allumées, est visible une capture avant la fin posée. L'écart reste dans
la tolérance d'une capture.

**Causes principales.** `REPRISE` 9, `LECTURE_COUPEE` 7, `ECRAN_NON_MARQUE` 7, `SEUIL` 3, `SIGNE_PROPRE_AU_JEU` 3,
`ABANDON` 1, `ETIQUETTE_DOUTEUSE` 1. `JEU_RARE` vaut pour les 31 cas (Tekken n'existe que dans cet enregistrement) ;
`SIGNE_PROPRE_AU_JEU` revient en cause secondaire 14 fois, `ERREUR_OBSERVATION` 8 fois.

**Les familles vues.**
- *Revanches immédiates* (U04, U06, U13, U18, U20, U24, U28, U29, U30) : mêmes combattants, aucun écran de fin, le
  score retombe à 0–0 d'une capture à la suivante. La règle (a) et le gradient boosting en trouvent la plupart. Le GRU
  reste entre 0,05 et 0,21 même quand les deux scores baissent et que le compteur monte (U20 : gradient boosting
  0,999, GRU 0,10).
- *Captures intermédiaires sans HUD* (U02, U07, U09, U11, U17, U21, U22) : présentation d'un combattant, pose de
  victoire, cinématique ou écran noir entre deux matchs. Cette capture, sans score ni compteur, devient la
  « précédente » et efface le retour à 0–0 comme la variation du compteur. Un titre ou un mode null (U07, U09, U11)
  rompt en plus le contexte, et une phase active ou intermediate (U17, U21) empêche la règle (c) de jouer.
- *Écran d'après-match non marqué* (U03, U05, U14, U16, U19, U27, U31) : portrait du vainqueur, son nom en grand et
  menu « Revanche / Choisir un personnage / … ». Il n'est jamais noté comme résultat, et sa phase change d'un cas à
  l'autre : intermediate en U03 et U05 (la règle (c) ne joue pas), menu ailleurs (elle joue). La seule fin dont
  l'écran est marqué comme résultat (U08, réplique de victoire de Shaheen) est la seule que le GRU trouve, avec ses
  5 graines.
- *Compteur de victoires seul* (U10, U12, U26) : rien d'autre ne prouve la fin dans les observations. En U12, aucune
  pastille allumée n'a été lue de tout le match ; en U26, la revanche est déjà à 1–0 quand elle est capturée.

**Ce qui m'a surpris.**
- Le compteur « WIN / WINS n », que la fiche Tekken présente comme l'indice le plus fiable, ne sert à aucun détecteur :
  le compteur `series` n'existe que dans cet enregistrement (traces de correction 078643). Tenu à l'écart, il laisse
  ses colonnes toujours inconnues à l'entraînement. De plus, la variation n'est calculée que pour la même case des deux
  côtés : quand la série change de joueur (U06, U11, U18, U21, U22, U24, U26, U28, U30), ni series.a ni series.b ne
  varie. Aucune règle écrite ne regarde ce compteur.
- Le compteur suit le joueur (le côté), pas le combattant : en U02, les joueurs échangent leurs personnages et
  « WINS 2 » reste à droite ; en U05, le joueur de droite passe de Bryan à Reina et garde « WINS 5 ».
- Pour Tekken, period.number est toujours null : la remontée du chrono à 95–99 au début d'un match n'est jamais
  calculée (CONTEXTE_SANS_VARIATION).
- Le professeur a noté une bannière « K.O. » de simple manche (185, 0–1) comme un résultat d'après-partie, alors que
  l'écran d'après-match, lui, ne l'est jamais : le marquage est inversé par rapport à ce qui prouve la fin.
- L'échantillonnage (une capture toutes les 28 s en moyenne, manches de 20 à 40 s) manque presque toujours le dernier
  coup ; la fin se prouve alors par le début du match suivant.

**Méthodes qui reviennent.**
1. Une règle « le compteur de séries change de valeur ou de côté par rapport à sa dernière valeur lisible, dans le même
   jeu » aurait trouvé les 8 fins manquées par les quatre détecteurs (pour U03, avec la capture de retard tolérée).
   Elle est propre à Tekken et à valider sur un autre enregistrement.
2. Calculer les variations et la règle (a) par rapport à la dernière valeur lisible du même jeu, en sautant les
   captures sans HUD : 6 des 8 fins manquées par tous (U02, U03, U10, U17, U21, U22) auraient été trouvées.
3. Convention : l'écran d'après-match de Tekken 8 noté post_game, result.visible=true, winner = nom écrit ; une
   présentation de combattant notée pre_game ; un « K.O. » noté résultat de match seulement si un côté atteint le
   nombre d'emplacements.
4. Variable « un score atteint target.field » (U25, U30) et variable « compteur de séries changé de côté ».
5. Associer les règles au GRU et au gradient boosting (ensemble « règle ou modèle »), ou relâcher un peu le seuil du
   gradient boosting : 7 fins sont entre 0,917 et 0,968.
6. Données : des revanches sans écran de fin et un second enregistrement de Tekken pour que le compteur de séries ait
   des exemples.

Source consultée : le manuel de Tekken 3 décrit déjà l'affichage « Consecutive Wins » (nombre de victoires d'affilée),
https://secure.cdn.us.playstation.com/manuals/classic/games/tekken-3-manual-en.pdf. Je n'ai trouvé aucune
documentation officielle du mode Versus hors ligne de Tekken 8 ; le comportement du compteur décrit ici vient des
captures elles-mêmes.
