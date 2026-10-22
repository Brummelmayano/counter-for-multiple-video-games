# Lot 6 : Beach Buggy Racing 2 (session fdb79549)

Les 27 fins de course de PlayEnd, toutes dans le même enregistrement, en écran partagé à trois vues. Convention : une
course = une partie. Le GRU n'en trouve aucune, le gradient boosting 10, les règles 6 ; 14 sont manquées par les quatre
détecteurs. Les sections suivent l'ordre des captures, la synthèse est à la fin.

## Beach_Buggy_Racing_2_fdb79549_U10

Première course du premier championnat « Mystère 8 » (Aquarius). La capture 210 montre le tableau de résultats de l'épreuve (« ÉVÉNEMENT 1 sur 8 », huit pilotes avec temps et points) : la fin est juste et bien placée. L'observation note correctement l'écran (result, post_game, stage 1/8, vainqueur le premier écrit). Le gradient boosting la trouve à 0,997 grâce à result.visible. Le GRU monte à 0,421, sous son seuil de 0,487 (2 graines sur 5) : c'est son meilleur score de toute la session, et ses pics sur les tableaux suivants ne feront que baisser. Les règles la manquent parce qu'aucune ne regarde l'apparition d'un résultat et que la course suivante démarre sans compte à rebours capturé. Cause principale `SEUIL` (pour le GRU), secondaire `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U11

Épreuve 2 du premier championnat. En 214 la course est au « TOUR 3 », les pilotes près du drapeau d'arrivée de la barre ; 18 s plus tard, en 215, « TOUR 1 » sur un autre circuit (le volcan, après la jungle de nuit), juste après la ligne de départ. Le tableau de résultats n'a pas été capturé. L'étiquette est juste (le texte de preuve parle de « fond de grille » alors que les places sont 3/8, 4/8 et 2/8, détail sans effet). L'observation est correcte. La seule trace de la fin dans les variables est progress.current.delta_candidate = −1,099 : une valeur qui n'existe dans aucune autre session de PlayEnd, donc jamais vue à l'entraînement. GRU 0,010, gradient boosting 0,001, règles muettes (aucune ne regarde le tour). Cause principale `SIGNE_PROPRE_AU_JEU`, secondaires `FIN_ENTRE_CAPTURES` et `JEU_RARE`. Une règle « le tour diminue dans le même jeu » la trouverait, sans fausse fin sur tout PlayEnd.

## Beach_Buggy_Racing_2_fdb79549_U12

Épreuve 3 du premier championnat. Le volcan au « TOUR 3 » (220) laisse place, 33 s plus tard, à un circuit de neige de nuit au « TOUR 1 », toutes les icônes de pilotes au départ de la barre (221) ; 222 (grotte de lave du même circuit) et 223 (« TOUR 2 ») confirment la nouvelle course. Étiquette juste, observation correcte. Seule variable non nulle : la variation du tour de −1,099, jamais vue à l'entraînement. GRU 0,010, gradient boosting 0,011, règles muettes. Même mécanisme que U11 : `SIGNE_PROPRE_AU_JEU`, avec `FIN_ENTRE_CAPTURES` et `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U13

Épreuve 4 du premier championnat. En 228, dernier tour sur la neige, les pilotes touchent le drapeau d'arrivée de la barre ; en 229, « TOUR 1 » sur un circuit de pistes orange dans un stade. Étiquette juste, observation correcte. Seule trace dans les variables : la variation du tour de −1,099. GRU 0,010, gradient boosting 0,002, règles muettes. `SIGNE_PROPRE_AU_JEU`, avec `FIN_ENTRE_CAPTURES` et `JEU_RARE`. En regardant ces captures, un détail de l'interface ressort : le drapeau à damier de la barre se place à gauche au premier tour et à droite au dernier, ce qui donnerait le tour même quand son chiffre est caché.

## Beach_Buggy_Racing_2_fdb79549_U14

Épreuve 5 (Looptastic) : le tableau de 234 (« ÉVÉNEMENT 5 sur 8 », boutons « Continuer | Quitter | Recommencer ») prouve la fin et confirme après coup que les « TOUR 1 » de U11 à U13 ouvraient bien de nouvelles épreuves (2, 3, 4). Étiquette juste, observation correcte. Le gradient boosting la trouve (0,996). Le GRU reste à 0,107 : ses pics sur les tableaux de cette session baissent course après course (0,42 puis 0,11, 0,06… 0,014), alors qu'il remonte à 0,5–0,7 sur les fins d'un autre jeu plus tard dans la même session. Les règles ne regardent pas l'apparition d'un résultat. Un détail de l'entraînement compte ici : les colonnes game.type=racing, game.mode=race et progress.type=lap/stage sont retirées dans ce tour, car constantes dans les autres sessions. Cause principale `JEU_RARE`, secondaire `AUTRE` (dérive de l'état du GRU).

## Beach_Buggy_Racing_2_fdb79549_U15

Épreuve 6. En 240, deux joueurs ont franchi la ligne (« 1re place », « 2e place ») et le troisième voit « Fin de la course ! 17 » : la course sera close moins de 17 s plus tard. En 241, « TOUR 1 » sur un autre circuit. La fin est dans l'intervalle (240, 241], la placer sur 241 est juste. Je ne range pas ce cas dans les écrans de fin non marqués : les bandeaux d'arrivée d'une vue ne sont pas un résultat, puisque la course n'est pas close et que le classement peut encore bouger. L'observation note bien le minuteur, mais sans valeur en secondes (value_seconds = null), et le GRU de ce tour a été entraîné sans le groupe des minuteurs. Dans la session, ce minuteur précède une fin 5 fois sur 5 (à une ou deux captures) : c'est un signe avant-coureur presque parfait, que rien n'exploite. Cause principale `SIGNE_PROPRE_AU_JEU` (tour qui revient à 1), secondaires `PRECURSEUR_NON_EXPLOITE` (code ajouté), `FIN_ENTRE_CAPTURES`, `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U16

Épreuve 7. Le tableau de l'épreuve n'a pas été capturé, mais 246 montre le classement cumulé (« Suivant : ÉVÉNEMENT 8 sur 8 — Frostfire Vale »), qui n'apparaît qu'après la fin d'une épreuve. Étiquette juste. L'observation suit la convention de course (intermediate/scoreboard, sans résultat), et c'est là que le bât blesse : avec « une course = une partie », cet écran prouve une fin autant que le tableau de l'épreuve. Le gradient boosting monte à 0,783 (sous 0,981), le GRU reste à 0,007, et les règles ne réagissent pas car intermediate compte comme une phase de jeu. Cause principale `ECRAN_NON_MARQUE` (par convention), secondaires `SEUIL` et `JEU_RARE`. Pour la trouver : noter ce classement comme un écran d'après course, avec le numéro de l'épreuve terminée.

## Beach_Buggy_Racing_2_fdb79549_U17

Dernière épreuve du premier championnat (Frostfire Vale) : tableau « ÉVÉNEMENT 8 sur 8 » en 252, puis en 253 le compte à rebours « 1 » d'une nouvelle course, les trois joueurs en fond de grille (6, 7 et 8/8). Étiquette juste, observation correcte. Gradient boosting (0,997) et règles la trouvent ; les règles grâce au passage post_game → pre_game de 253, dans la capture de retard tolérée. Le GRU reste à 0,062. Cause principale (pour le GRU) `JEU_RARE`, secondaire `AUTRE` (dérive de son état).

## Beach_Buggy_Racing_2_fdb79549_U18

Première course du deuxième championnat, sur le circuit du dôme et des tunnels (grille de départ en 253, « TOUR 3 » en 259). En 260, « TOUR 1 » sur le circuit du port. Le changement de circuit lève le doute du placement (« épreuve 1 ou relance ») : c'est une nouvelle épreuve. Étiquette juste, observation correcte. Seule variable non nulle : la variation du tour de −1,099. GRU 0,005, gradient boosting 0,011, règles muettes. `SIGNE_PROPRE_AU_JEU`, avec `FIN_ENTRE_CAPTURES` et `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U19

En 264, un joueur a fini 3e et les deux autres voient « Fin de la course ! 16 » ; 17 s plus tard, en 265, le compte à rebours « 3 » d'une course sur un autre circuit. Étiquette juste, observation correcte (minuteurs notés sans valeur en secondes). Les règles la trouvent grâce au passage active → pre_game ; le gradient boosting monte à 0,487, sous son seuil de 0,981 ; le GRU, entraîné sans le groupe des minuteurs, reste à 0,008. Cause principale `SEUIL` (gradient boosting), secondaires `PRECURSEUR_NON_EXPLOITE`, `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U20

Le placement hésitait entre relance et nouvelle course, et jugeait la course jamais vue au tour 3. En réalité, 272 montre la fin du libellé « R 3 » et le drapeau à damier à droite de la barre (dernier tour), puis 273 un autre circuit au « TOUR 1 », avec les joueurs en fond de grille : course complète puis nouvelle épreuve, étiquette juste. Le professeur a noté le tour de 272 à null (chiffre en partie caché), ce qui efface la variation du tour sur 273 : aucune variable ne bouge, et les quatre détecteurs restent muets. Cause principale `LECTURE_COUPEE`, secondaires `SIGNE_PROPRE_AU_JEU`, `FIN_ENTRE_CAPTURES`, `JEU_RARE`. Comparer le tour à la dernière valeur lisible, ou lire la position du drapeau, la trouverait.

## Beach_Buggy_Racing_2_fdb79549_U21

Dernier tour sur la plage au coucher du soleil en 279, puis « TOUR 1 » dans une ville de nuit en 280, 22 s plus tard. Étiquette juste, observation correcte, planche assez lisible pour conclure. Seule variable non nulle : la variation du tour de −1,099, que ni le GRU (0,005) ni le gradient boosting (0,004) n'ont appris, et qu'aucune règle ne regarde. `SIGNE_PROPRE_AU_JEU`, avec `FIN_ENTRE_CAPTURES` et `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U22

Dernier tour dans la ville de nuit en 286, puis compte à rebours « 1 » sur la grille d'un circuit de désert en 287. Étiquette juste, observation correcte. Les règles la trouvent (active → pre_game) ; le gradient boosting monte à 0,484, loin sous 0,981 ; le GRU, sans minuteurs, reste à 0,007. Cause principale `SEUIL`, secondaires `SIGNE_PROPRE_AU_JEU`, `FIN_ENTRE_CAPTURES`, `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U23

Tableau « ÉVÉNEMENT 3 sur 8 — Dryptopia » en 294 : étiquette juste, observation correcte, trouvée par le gradient boosting (0,995), manquée par le GRU (0,078) et par les règles. Ce tableau corrige la description du championnat : les épreuves 1 et 2 sont les courses de 273 et 280. Les trois courses de 253 à 272 (tunnel, port, mangrove) appartiennent à un championnat abandonné après la manette déconnectée. Les étiquettes ne changent pas, puisque chaque course compte pour une partie. Cause principale `JEU_RARE`, secondaire `AUTRE` (dérive du GRU).

## Beach_Buggy_Racing_2_fdb79549_U24

Épreuve 4 (Dino Jungle). Les captures 300 à 302 montrent tout l'après-course du jeu : tableau de l'épreuve, puis boutons, puis classement cumulé « Suivant : ÉVÉNEMENT 5 ». Étiquette juste, observation correcte. Le gradient boosting la trouve sur 300 (0,996), puis redescend proprement sur 301–302. Le GRU reste à 0,05 et les règles ne regardent pas l'apparition d'un résultat. Cause principale `JEU_RARE`, secondaire `AUTRE` (dérive du GRU).

## Beach_Buggy_Racing_2_fdb79549_U25

Tableau « ÉVÉNEMENT 5 sur 8 — Raytona Stadium » en 311, puis compte à rebours « 3 » d'une course dans le désert en 312. Étiquette juste, observation correcte. Le gradient boosting (0,994) et les règles (passage post_game → pre_game, une capture de retard) la trouvent ; le GRU reste à 0,02. Cause principale `JEU_RARE`, secondaire `AUTRE` (dérive du GRU).

## Beach_Buggy_Racing_2_fdb79549_U26

Tableau « ÉVÉNEMENT 6 sur 8 — Scorching Sands » en 319, entre le dernier tour dans le temple égyptien (318, drapeau à droite) et le « TOUR 1 » d'un autre désert (320). Étiquette juste, observation correcte. Trouvée par le gradient boosting (0,993) ; le GRU reste à 0,019, et les règles ne voient rien puisque la course suivante démarre sans compte à rebours capturé. Cause principale `JEU_RARE`, secondaire `AUTRE` (dérive du GRU).

## Beach_Buggy_Racing_2_fdb79549_U27

Tableau « ÉVÉNEMENT 7 sur 8 — Gold Rush Ridge » en 328, après le dernier tour dans la ville de l'Ouest (327) et avant une course en bord de mer (329). Étiquette juste, observation correcte. Gradient boosting 0,996 (trouvée), GRU 0,018, règles muettes. Cause principale `JEU_RARE`, secondaire `AUTRE` (dérive du GRU).

## Beach_Buggy_Racing_2_fdb79549_U28

Dernière épreuve du championnat repris en 273. Le tableau de l'épreuve n'est pas capturé, mais 335 montre le classement final et le podium, puis 336 le choix des pilotes de la « Coupe ultime ». Étiquette juste, observation correcte. Le gradient boosting (0,994) et les règles (post_game → pre_game) la trouvent ; le GRU reste à 0,015. Cause principale `JEU_RARE`, secondaire `AUTRE` (dérive du GRU).

## Beach_Buggy_Racing_2_fdb79549_U29

Première course du championnat suivant. En 346, deux joueurs ont fini (7e et 4e) et le troisième voit « Fin de la course ! 18 » ; 17 s plus tard, en 347, « TOUR 1 » sur la ligne de départ d'une jungle de lave. Étiquette juste, observation correcte (les bandeaux d'arrivée ne sont pas un résultat). Seules traces dans les variables : le minuteur « other » de 346, que le GRU ne voit pas, et la variation du tour de −1,099 sur 347. Quatre détecteurs muets. Cause principale `SIGNE_PROPRE_AU_JEU`, secondaires `PRECURSEUR_NON_EXPLOITE`, `FIN_ENTRE_CAPTURES`, `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U30

Comme pour U16, le tableau de l'épreuve n'est pas capturé et la fin est prouvée par le classement cumulé (« Suivant : ÉVÉNEMENT 3 sur 8 — Fiesta Village », 354). Étiquette juste. L'observation suit la convention (intermediate, sans résultat), qui ne marque pas cet écran comme une fin de course. Gradient boosting 0,355, GRU 0,004, règles muettes. Cause principale `ECRAN_NON_MARQUE` (par convention), secondaires `SEUIL` et `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U31

Tableau « ÉVÉNEMENT 3 sur 8 — Fiesta Village » en 360, entre le dernier tour dans le village (359) et une course dans la jungle (361). Étiquette juste, observation correcte. Gradient boosting 0,997 (trouvée), GRU 0,014, son plus bas niveau sur un tableau de la session, règles muettes. Cause principale `JEU_RARE`, secondaire `AUTRE` (dérive du GRU).

## Beach_Buggy_Racing_2_fdb79549_U32

Même schéma que U15 et U29. En 367, un joueur a fini 2e et les deux autres voient « Fin de la course ! 18 ». En 368, « TOUR 1 » au temple de la jungle. Étiquette juste, observation correcte. Seules traces dans les variables : deux minuteurs « other » sur 367 et la variation du tour de −1,099 sur 368, que rien n'exploite. Cause principale `SIGNE_PROPRE_AU_JEU`, secondaires `PRECURSEUR_NON_EXPLOITE`, `FIN_ENTRE_CAPTURES`, `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U33

Trois captures au « TOUR 3 » dans le temple de la jungle (371–373), puis « TOUR 1 » sur la ligne de départ du volcan (374). Étiquette juste, observation correcte. Seule variable non nulle : la variation du tour de −1,099, ignorée par le GRU (0,004), le gradient boosting (0,003) et les règles. `SIGNE_PROPRE_AU_JEU`, avec `FIN_ENTRE_CAPTURES` et `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U34

Dernier tour sur le volcan en 378, puis « TOUR 1 » sur le circuit de glace et de feu en 379, 42 s plus tard. Étiquette juste, observation correcte. Seule variable non nulle : la variation du tour de −1,099. GRU 0,004, gradient boosting 0,017, règles muettes. `SIGNE_PROPRE_AU_JEU`, avec `FIN_ENTRE_CAPTURES` et `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U35

En 386, deux joueurs ont fini (2e et 6e) et le troisième voit « Fin de la course ! 13 » ; 14 s plus tard, 387 montre la même scène floutée, sans interface : très probablement la transition de fin de course. 388 est au « TOUR 1 » dans le stade. Étiquette juste (387 masquée, fin sur 388). Comme la capture floutée n'a pas de tour, la variation 3 → 1 n'est pas calculée sur 388, et aucun détecteur ne voit rien. Cause principale `LECTURE_COUPEE`, secondaires `SIGNE_PROPRE_AU_JEU`, `PRECURSEUR_NON_EXPLOITE`, `FIN_ENTRE_CAPTURES`, `JEU_RARE`.

## Beach_Buggy_Racing_2_fdb79549_U36

Dernier tour dans le stade en 393, puis le menu « Championnats » en 394–396 : la 8e épreuve du championnat commencé en 338 est finie, sans que le tableau ni le podium soient capturés. Étiquette juste, observation correcte. Les règles la trouvent (active → menu). Le gradient boosting monte à 0,896, sous son seuil de 0,981, et le GRU reste à 0,022. Cause principale `SEUIL`, secondaires `MENU_AMBIGU`, `FIN_ENTRE_CAPTURES` et `JEU_RARE`.

## Synthèse du lot

**Étiquettes.** Les 27 fins sont justes et bien placées. Deux descriptions de placement sont à corriger, sans effet sur
les étiquettes. La course de U20 n'était pas « jamais vue au tour 3 » : la capture 272 montre la fin du libellé « R 3 »
et le drapeau d'arrivée à droite de la barre. Et d'après le tableau « ÉVÉNEMENT 3 sur 8 » de 294, les courses de 253 à
272 (tunnel, port, mangrove) appartiennent à un championnat abandonné après la manette déconnectée : le championnat
suivant commence en 273 et va jusqu'au podium de 335.

**Ce qui prouve les fins.** Le tableau de l'épreuve est capturé 9 fois, le podium final une fois, le classement cumulé
2 fois, le menu des championnats une fois ; les 14 autres fins ne se voient qu'au début de la course suivante (12 fois
« TOUR 1 », 2 fois le compte à rebours). Une course dure 2 min 30 à 3 min, et l'après-course passe vite : entre le
dernier tour et le « TOUR 1 » suivant, il s'écoule parfois 17 ou 18 s seulement (U11, U19, U29).

**Causes principales.** `SIGNE_PROPRE_AU_JEU` 10, `JEU_RARE` 9, `SEUIL` 4, `ECRAN_NON_MARQUE` 2, `LECTURE_COUPEE` 2.
Parmi les 14 fins manquées par les quatre détecteurs : 10 `SIGNE_PROPRE_AU_JEU`, 2 `ECRAN_NON_MARQUE`, 2
`LECTURE_COUPEE`. Code ajouté : `PRECURSEUR_NON_EXPLOITE` (secondaire dans 5 cas), un signe noté dans l'observation qui
annonce une fin imminente mais que les détecteurs ne peuvent pas utiliser. `AUTRE` (9 cas) désigne la dérive du GRU
décrite plus bas.

Les familles :

1. *Le tour qui revient à 1* (12 fins, plus 2 où la lecture est coupée). La variable existe :
   progress.current.delta_candidate vaut −1,099 sur chacune de ces 12 captures, et dans tout PlayEnd une variation
   négative du tour n'apparaît que là, toujours sur une fin. Mais dans les 24 sessions d'entraînement du tour, cette
   colonne n'est connue que 2 fois, jamais négative : aucun modèle ne peut apprendre ce signe. Le tri des colonnes,
   fait sur les seules sessions d'entraînement, retire en plus game.type=racing, game.mode=race, progress.type=lap,
   progress.type=stage et state.screen_type=podium, constantes ailleurs.
2. *Les tableaux de résultats* (10 fins). Le gradient boosting les trouve tous (0,993 à 0,997) grâce à result.visible,
   puis redescend proprement sur les captures suivantes du même après-course. Le GRU n'en trouve aucun.
3. *Le classement cumulé noté comme intermédiaire* (U16, U30). La convention range « Suivant : ÉVÉNEMENT n » en
   intermediate/scoreboard, sans résultat. Or, avec « une course = une partie », cet écran prouve la fin autant que le
   tableau. Gradient boosting 0,78 et 0,36.
4. *« Fin de la course ! N »* (U15, U19, U29, U32, U35). Sur les 5 captures qui portent ce minuteur, la fin suit à la
   capture suivante (4 fois) ou deux captures plus loin (1 fois). Je ne les range pas dans les écrans de fin non
   marqués : quand le minuteur s'affiche, un joueur roule encore et le classement n'est pas arrêté. La fin tombe donc
   dans l'intervalle suivant, où elle est placée. Mais ce signe avant-coureur est perdu : value_seconds reste null
   (seul le nombre de minuteurs passe dans les variables), et le GRU retenu pour ce tour a été entraîné sans le groupe
   des minuteurs (dtimers).
5. *Les seuils* (U19, U22, U36, et U10 pour le GRU). Le compte à rebours ou le menu capturé juste après la course
   fait monter le gradient boosting à 0,48, 0,48 et 0,90, sous un seuil de 0,981. Les règles trouvent ces trois fins
   (passage d'une phase de jeu à pre_game ou menu).

**Ce qui m'a surpris.**

- La dérive du GRU : sur les tableaux, sa probabilité passe de 0,421 (U10, 2 graines sur 5) à 0,107, 0,06, puis 0,02
  et moins à partir de U25. Elle remonte à 0,52 et 0,71 sur les fins de J-Stars Victory VS+, plus loin dans la même
  session. Ce n'est donc pas l'écran qui l'éteint, mais la longue suite de captures d'un jeu jamais vu.
- Le signe le plus fiable du lot (le tour qui diminue) est déjà calculé, mais aucun modèle n'a pu l'apprendre.
- Un détail de l'interface : le drapeau à damier de la barre de progression se place à gauche au premier tour et à
  droite au dernier tour. C'est vrai sur toutes les planches du lot où le drapeau est visible. Il donnerait le tour même quand le chiffre
  est caché par les icônes des pilotes (209, 245, 272, 318, 334).
- Au départ d'un championnat, les trois joueurs partent en fond de grille (6, 7 et 8/8, captures 253 et 273) ; aux
  épreuves suivantes, la grille dépend du classement. « Fond de grille » ne vaut donc que pour une première épreuve.

**Méthodes qui reviennent.**

- Règle « dans le même jeu, le tour diminue par rapport au dernier tour lisible, la référence étant remise à zéro sur
  un écran de résultat, de classement, de podium ou de menu ». Sur cette session, elle trouve les 14 fins prouvées par
  la course suivante (U20 et U35 compris), sans fausse fin. La version stricte, qui compare à la seule capture
  précédente, trouve 12 fins et ne fait aucune fausse fin sur tout PlayEnd.
- Règle « une capture de jeu suivie d'un écran result, scoreboard ou podium, dans le même jeu ». Sur tout PlayEnd, ce
  passage tombe 40 fois sur une fin (ou une capture après) et 6 fois ailleurs. Avec la règle du tour, elle couvre
  les 27 fins de la session sans fausse fin. Ajouter le menu ferait trop de fausses fins dans les jeux facturés au
  temps (Genshin Impact, Red Dead Redemption 2).
- Pour les modèles appris : une colonne générique « compteur de progression qui revient en arrière » (tour qui revient
  à 1, round qui revient à 1, chrono de round qui revient à son départ), pour que les revanches des autres jeux
  servent d'exemples. Ne pas retirer d'office le groupe des minuteurs. Et surtout plus de sessions de course : avec une
  seule session, chaque tour d'évaluation de ce jeu se fait sans aucun exemple de course.
- Conventions : noter le classement cumulé « Suivant : ÉVÉNEMENT n sur 8 » comme écran d'après course (post_game,
  stage n−1 sur 8) ; renseigner value_seconds pour « Fin de la course ! N », ou créer un type de minuteur « fin
  forcée » ; lire le premier ou le dernier tour d'après la position du drapeau quand le chiffre est caché.
- Seuil : avec un budget un peu moins strict, le gradient boosting aurait pris U36 (0,90) et peut-être U16 (0,78).

Sources : la page du jeu sur le Microsoft Store confirme les championnats à plusieurs épreuves jouables en écran
partagé (https://www.xbox.com/en-US/games/store/-/9N5W8W1WW9J9). Je n'ai trouvé en
ligne aucune description du minuteur « Fin de la course ! » : sa lecture vient des captures (délai entre 386 et 387).
