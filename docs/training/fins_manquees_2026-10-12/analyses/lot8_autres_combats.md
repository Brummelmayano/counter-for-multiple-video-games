# Lot 8 : autres jeux de combat (UFC 5, Dragon Ball, Naruto, J-Stars, Demon Slayer)

## EA_Sports_UFC_5_11029423_U01

Combat Prates contre Brady arrêté par TKO au 3e round. La capture 31 montre le menu d'après-combat (Revanche, Changer de combattants…) devant l'écran « TKO, R3 01:54 » et la carte des juges : l'étiquette est juste. Le professeur marque bien un résultat, mais note `other` au lieu de `tko` et recopie la carte des juges 20–18 comme score, contre la convention UFC.

Le GRU n'a pas raté le signal, il l'a pris une capture trop tôt : 0,66 sur la transition WFA (30), au-dessus de son seuil, puis 0,42 sur la preuve. L'évaluation compte alors une fausse fin et une fin manquée (une graine sur cinq seulement démarre sur 31). Le gradient boosting monte à 0,39, loin de 0,71 : écran d'après-combat UFC rare et mal typé. Les règles la trouvent sur 32 (post_game puis pre_game), mais tirent aussi sur 30.

Cause principale : `ANNONCE_EN_AVANCE` (nouveau code : l'annonce tombe sur une capture de transition juste avant la preuve et compte comme fausse fin). Il suffirait d'accepter les annonces posées entre la dernière capture de jeu et la preuve, et de corriger la convention (`tko`, carte des juges hors du score).

## EA_Sports_UFC_5_11029423_U02

Combat en mode Kumite (Pereira contre Silva, chrono 23:52 puis 21:41) quitté : la capture 42 est l'écran de lancement d'EA SPORTS FC26, puis vient le menu de FC 26. L'étiquette est juste. Le GRU (0,79, cinq graines sur cinq) et les règles (phase active puis menu) la trouvent ; le gradient boosting monte à 0,49 sous son seuil de 0,71.

Le professeur a noté le logo FC26 comme « EA Sports UFC 5 » : le titre de la capture précédente a été repris. Le changement de jeu, signal le plus net d'un abandon, disparaît donc des variables (`game.title.changed` = 0) et la règle (d) ne tire pas. Le gradient boosting ne voit plus qu'un passage au menu, comme une pause.

Cause principale : `ERREUR_OBSERVATION` ; secondaires : `ABANDON`, `SEUIL`. Une trace qui corrige le titre de la capture 42 suffirait.

## EA_Sports_UFC_5_11029423_U32

Combat UFC Sonnen contre Adesanya interrompu au 1er round (0:27), écran noir (1150), puis menu de pause de Mortal Kombat 1 (1151) et entraînement MK1 avec « ∞ ». Fin par abandon, étiquette juste, observations correctes.

Personne ne la trouve (GRU 0,24 sur le noir puis 0,10 ; gradient boosting 0,20). L'écran noir sans titre casse la comparaison de titres : `game.title.changed` n'est pas calculé sur 1151 et vaut 0 sur 1152. La règle (d) a le même défaut (elle compare avec la capture juste avant), et la règle (c) ignore `unknown` et `paused`. Reste un menu de pause, que tout détecteur associe à une interruption en cours de partie.

Cause principale : `LECTURE_COUPEE` ; secondaires : `ABANDON`, `MENU_AMBIGU`. Comparer le titre à la dernière observation qui a un titre connu suffirait à faire apparaître le changement de jeu.

## EA_Sports_UFC_5_f8c2843d_U18

Brown contre Makhachev : R1 2:54 sur 612, puis R1 4:48 avec le bandeau « COULEUR DU SHORT » et l'arbitre au centre sur 613. Le chrono du premier round remonte : le combat a été relancé. L'étiquette est juste et l'observation exacte (seul `period.total` manque, alors que le badge R1 suivi de quatre segments indique 5 rounds).

La variable existe : `clock.value_seconds.delta_candidate` vaut +114 s dans le même round. Mais en comptant sur tout le corpus, une hausse de plus de 20 s du chrono dans un même round n'apparaît que trois fois, toutes sur des fins UFC de cette session. Tenue à l'écart, la session est jugée par des modèles qui n'ont jamais vu cette valeur : GRU 0,03, gradient boosting 0,01. Les règles ne regardent pas le chrono.

Cause principale : `REPRISE` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `JEU_RARE` (UFC : deux sessions, 128 lignes). Une règle « chrono de round qui remonte sans changement de round », doublée du bandeau de lancement comme second indice, la trouverait sans attendre plus de données.

## EA_Sports_UFC_5_f8c2843d_U20

Edwards contre St-Pierre : St-Pierre au tapis à R1 1:52 (626–627), puis R1 4:39 avec le bandeau « COULEUR DU SHORT » sur 628. Trop peu de temps pour un KO, un écran d'après-combat et une revanche : le combat a été recommencé depuis la pause. Étiquette juste, observation exacte (sauf `period.total` absent).

Le seul signal est le chrono du premier round qui remonte de 167 s, une variable que les modèles n'ont jamais vue positive à l'entraînement (trois cas dans tout le corpus, tous dans cette session). GRU 0,06, gradient boosting 0,01, règles muettes.

Cause principale : `REPRISE` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`. Même remède que U18 : une règle sur le chrono qui remonte dans un même round, avec le bandeau de lancement pour confirmer.

## EA_Sports_UFC_5_f8c2843d_U21

Combat Edwards contre St-Pierre quitté au 2e round (R2 4:20 sur 636). La fin est posée sur 638, le choix des combattants. Mais 637, une transition rouge, porte au zoom le texte « … la partie en cours pour accéder au Choix des … » : on quitte déjà le combat. La fin est vraie, son placement est douteux d'une capture.

Ce décalage coûte cher : la règle (c) tire justement sur 637 (`active` puis `pre_game`) et l'évaluation la compte comme fausse fin. Le GRU culmine aussi sur 637 (0,38, seuil 0,77) et redescend sur 638. Le gradient boosting reste bas : pour lui, une scène `pre_game` après un combat ressemble à l'entre-deux-rounds.

Cause principale : `ETIQUETTE_DOUTEUSE` ; secondaires : `ANNONCE_EN_AVANCE`, `ERREUR_OBSERVATION` (texte de sortie non lu sur 637). À corriger par une trace qui avance la fin sur 637.

## EA_Sports_UFC_5_f8c2843d_U22

Adesanya contre Chimaev : R1 0:51 (644), scène sans HUD des combattants dans leur coin (645), puis R1 4:12 avec le bandeau de présentation (646). Le combat a été recommencé ; étiquette juste, observations exactes.

Cette fois la hausse du chrono (+201 s) n'apparaît même pas dans les variables : la scène sans HUD, notée avec un mode null et une période `none`, rompt le « même contexte », et la variation n'est pas calculée sur 646. Les modèles ne voient qu'une coupure comme entre deux rounds (GRU 0,11, gradient boosting 0,03) ; les règles ne lisent pas le chrono.

Cause principale : `LECTURE_COUPEE` ; secondaires : `REPRISE`, `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`. Il faudrait comparer le chrono à la dernière observation lisible, puis appliquer la règle du chrono qui remonte.

## EA_Sports_UFC_5_f8c2843d_U23

Adesanya contre Chimaev, deuxième relance : Chimaev au tapis à R1 2:28 (649), puis R1 4:41 avec « COULEUR DU SHORT » (650). Étiquette juste, observation exacte. Comme dans U20, le joueur en difficulté recommence le combat après un knockdown.

La variable de chrono vaut +133 s dans le même round, mais aucun modèle ne l'a jamais vue à l'entraînement (GRU 0,10, gradient boosting 0,01) et aucune règle ne la lit.

Cause principale : `REPRISE` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `JEU_RARE`. Dans tout le corpus, une hausse du chrono de plus de 20 s dans le même round n'apparaît que cinq fois : trois fins UFC (U18, U20, U23) et deux captures de Genshin Impact, facturé au temps. Une règle écrite sur ce signal serait presque sans fausse fin.

## EA_Sports_UFC_5_f8c2843d_U24

Combat Adesanya contre Chimaev quitté au 1er round (1:23) pour l'écran de choix des combattants (655). Étiquette juste, observation exacte. Le GRU (0,87, quatre graines sur cinq) et la règle (c) la trouvent.

Le gradient boosting monte à 0,68 sous un seuil de 0,76 : il voit la fin, mais le seuil du tour, choisi pour au plus une fausse fin pour 100 parties, l'en empêche. Faute de mode et de participants sur l'écran de sélection, aucune variable de changement ne l'aide.

Cause principale : `SEUIL` ; secondaire : `ABANDON`. Une variable « passage du jeu à la sélection », copie de la règle (c), ou un budget moins strict suffiraient.

## Dragon_Ball_Sparking_ZERO_020621e7_U01

Combat contre Freezer (premier professeur) : pause avec « Réessayer » en 11, reprise en 12, puis accueil de la PS5 en 13 et mise hors tension en 14. Fin par abandon, étiquette juste. La règle (c) la trouve (active puis menu).

Le GRU monte de 0,01 à 0,51, sous son seuil de 0,725 ; le gradient boosting atteint 0,39 pour un seuil de 0,989, inatteignable sans écran de résultat. L'observation brouille le signal : l'accueil est noté avec le titre du jeu (tuile sélectionnée), type combat, écran `other`, comme un menu interne. La convention `ps5_home` du second professeur (titre null) n'a pas été appliquée par le premier. Et le changement de titre détecté ne vient que de deux écritures du même jeu (« Dragon Ball » puis « DRAGON BALL: Sparking! ZERO »).

Cause principale : `SEUIL` ; secondaires : `ABANDON`, `ERREUR_OBSERVATION`. Harmoniser l'accueil de la console et les titres, et revoir le seuil du gradient boosting de ce tour.

## Dragon_Ball_Sparking_ZERO_f8c2843d_U16

Gogeta contre Gogeta en écran partagé (J1 contre J2). Sur 529 réapparaît le « ∞ » du début de combat, les points de compétence reviennent à 0 et les deux combattants sont en position de départ : le combat a été relancé. Étiquette juste ; 528, un gros plan sans HUD, ne suffisait pas à le prouver.

Le seul indice dans les variables est `clock.infinite`. Or dans PlayEnd, « ∞ » veut presque toujours dire entraînement sans fin de Mortal Kombat 1 (596 des 616 captures, aucune fin) : les modèles ont appris le contraire de ce qu'il signifie ici. GRU 0,10, gradient boosting 0,18 sur 529. Les règles « trouvent » U16 grâce au menu de 530, qui est en fait la preuve de la fin suivante (U16b), tombée dans la tolérance d'une capture.

Cause principale : `REPRISE` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `FINS_CONSECUTIVES` (nouveau code, voir U16b), `SEUIL`. Il faudrait une variable « ∞ qui apparaît » propre au début de combat, distincte du ∞ permanent de l'entraînement.

## Dragon_Ball_Sparking_ZERO_f8c2843d_U16b

Le combat relancé en 529 (U16) est quitté dès la capture suivante : 530 montre le menu principal (« Combat », « Hors ligne »), puis viennent la sélection d'équipe et un nouveau combat. La frontière est juste ; le combat a duré moins d'une capture et n'est sans doute pas facturé.

Cette fin est perdue d'avance pour tous les détecteurs. La règle (c) tire bien sur 530, mais l'évaluation donne cette annonce à U16, dont la preuve est 529 et la tolérance va jusqu'à 530. Le GRU (0,63) et le gradient boosting (0,53) restent de plus sous leur seuil. Pour trouver les deux fins, il faudrait annoncer sur 529, retomber sur 530 et annoncer de nouveau sur 531.

Cause principale : `FINS_CONSECUTIVES` (nouveau code : deux fins sur deux captures consécutives, une même annonce n'en valide qu'une) ; secondaires : `SEUIL`, `ABANDON`. C'est un artefact de l'évaluation plus qu'un défaut des détecteurs : regrouper les fins consécutives ou ne pas noter les parties non facturables.

## Dragon_Ball_Sparking_ZERO_f8c2843d_U17

Combat presque fini (barres restantes 1 contre 0), menu « Pause » en 585, écran noir en 586, menu principal en 587 : le combat est quitté. Étiquette juste, observations exactes. Le GRU la trouve sur 587 (0,89, cinq graines). Le gradient boosting (0,12) et les règles la manquent : le noir sépare la pause du menu, et ni la règle (c) ni la fenêtre de trois captures ne voient un passage direct du combat au menu ; `paused` n'est d'ailleurs pas compté comme « dans la partie ». Cause principale : `LECTURE_COUPEE` ; secondaires : `MENU_AMBIGU`, `ABANDON`. Comparer à la dernière phase connue, pause comprise, suffirait.

## Dragon_Ball_Sparking_ZERO_fdb79549_U03

Combat en équipes fini par KO : plus aucune barre de vie à droite (33), attaque ultime de Jiren (34), puis écran d'équipe « Joueur 1 » (35). L'écran « Victoire » n'a pas été capturé. Étiquette juste. Le GRU (0,81), la régression logistique et la règle (c) la trouvent. Le gradient boosting monte à 0,93, mais le seuil de son tour est de 0,981. Cause principale : `SEUIL`. À noter : « Joueur 1 » et « Joueur 2 » notés comme participants sur les écrans d'équipe créent un faux changement de participants.

## Dragon_Ball_Sparking_ZERO_fdb79549_U04

Combat en équipes abandonné : accueil de la PS5 en 54, lancement d'EA SPORTS FC26 en 55. L'accueil seul ne prouvait pas la fin (en 46, le combat avait repris après un passage à l'accueil) : 54 est masqué et la fin posée sur 55. Étiquette juste. Les détecteurs ont réagi au bon endroit (GRU 0,75 au-dessus de son seuil, gradient boosting 0,97, règle (c)), mais sur 54, la capture masquée, où l'évaluation ignore les annonces. Sur 55, plus rien : le changement de jeu n'est pas calculé, car l'accueil sans titre sépare les deux jeux. Cause principale : `ANNONCE_EN_AVANCE` ; secondaires : `LECTURE_COUPEE`, `ABANDON`, `SEUIL`. Il faudrait accepter les annonces sur une capture masquée entre la dernière capture de jeu et la preuve, et comparer les titres en sautant l'accueil.

## Dragon_Ball_Sparking_ZERO_fe69758b_U01

Combat en équipes : à gauche il ne reste plus de barre de vie (26), puis écran noir (27) et grille de sélection (28). Le KO probable s'est joué entre deux captures ; étiquette juste. Le gradient boosting la trouve de justesse (0,986 pour 0,984). Le GRU monte à 0,69, sous son seuil de 0,772. Les règles la manquent, car l'écran noir sépare le combat de la sélection. Cause principale : `SEUIL` ; secondaire : `LECTURE_COUPEE`.

## Dragon_Ball_Sparking_ZERO_fe69758b_U03

Combat Freezer contre Vegetto vu sur une seule capture (89, avec le « ∞ » du début), pose d'équipe sans interface (90), puis écran des règles et du décor (91) : le combat a été quitté pour revenir à la configuration. Étiquette juste. La règle (c) la trouve ; le gradient boosting atteint 0,91 sous un seuil de 0,984 ; le GRU reste à 0,25, car une partie d'une capture ouverte par un « ∞ » ne lui donne aucun combat à voir s'interrompre. Cause principale : `SEUIL` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `ABANDON`.

## Dragon_Ball_Sparking_ZERO_fe69758b_U04

Combat en équipes : l'équipe de droite n'a plus de barre de vie (107–108), Son Goku est au sol sans interface (109), puis un nouveau combat démarre avec le « ∞ » et les points de compétence à 0 (110). Le KO s'est joué entre deux captures et l'écran « Victoire » n'a pas été capturé ; étiquette juste. Les détecteurs ne voient rien (GRU 0,01, gradient boosting 0,36) : le ∞ est appris comme un signe d'entraînement, et la remontée des barres (1 et 0, puis 3 et 4) n'est pas calculée à cause de la capture sans HUD. Cause principale : `FIN_ENTRE_CAPTURES` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `LECTURE_COUPEE`, `REPRISE`. Il faudrait une variable « ∞ qui apparaît » et des variations de compteurs calculées contre la dernière lecture lisible.

## Dragon_Ball_Sparking_ZERO_fe69758b_U07

Son Gohan contre Gogeta SS4 : combat en écran partagé en 147, puis 12 s plus tard un plan d'introduction plein écran sans HUD (148), Gohan revenu en forme de base face à Gogeta au loin. Ensuite une pause, et un combat aux points de compétence remis à zéro. Le combat a été relancé avec « Réessayer », sans écran de résultat ; étiquette juste, avec un léger doute sur la nature de la scène 148. Aucun détecteur ne réagit (GRU 0,07, gradient boosting 0,01) : la scène est notée `cutscene` / `active`, comme les nombreuses attaques ultimes du jeu, et la remontée des barres n'est pas calculée. Cause principale : `REPRISE` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `LECTURE_COUPEE`. Il faudrait noter l'introduction en `pre_game` et garder les points de compétence remis à zéro.

## Dragon_Ball_Sparking_ZERO_fe69758b_U08

Deuxième relance du même combat : pause avec « Réessayer » (149), combat (150), écran noir (151), puis retour à la position de départ de l'introduction, points de compétence à 0 et barres de Gogeta pleines (152). Étiquette juste. Aucun détecteur ne réagit (GRU 0,02, gradient boosting 0,10) : l'écran noir empêche le calcul de la remontée des barres, et les indices propres au jeu (points de compétence à 0, position de départ) ne sont pas dans le contrat. Cause principale : `REPRISE` ; secondaires : `LECTURE_COUPEE`, `SIGNE_PROPRE_AU_JEU`.

## Dragon_Ball_FighterZ_378c621d_U02

Combat 3 contre 3 de Dragon Ball FighterZ (jeu d'une seule session) : super attaque de Gogeta (23), pose de victoire sans interface (24), puis « SÉLECTION DU PERSONNAGE » (25) ; l'écran « RÉSULTAT » n'a pas été capturé. Étiquette juste. Le gradient boosting monte à 0,977 et le GRU à 0,67, mais les seuils de ce tour sont de 0,989 et 0,988. Les règles la manquent parce que la pose de victoire est notée en phase `unknown`, ce qui coupe le passage du jeu à l'avant-partie. Cause principale : `SEUIL` ; secondaires : `JEU_RARE`, `LECTURE_COUPEE`.

## Dragon_Ball_FighterZ_378c621d_U03

Écran « RÉSULTAT — VICTOIRE Équipe rouge » en 40, bien noté comme résultat par le professeur : c'est le cas le plus simple du lot. Pourtant les quatre détecteurs la manquent. Le gradient boosting monte à 0,93 et le GRU à 0,44, avec des seuils de 0,989 et 0,988 dans ce tour (jeu d'une seule session). Les règles n'ont aucune règle sur le résultat affiché, et `post_game` compte pour elles comme « dans le jeu ». Cause principale : `SEUIL` ; secondaire : `JEU_RARE`. Une règle « résultat affiché qui apparaît » et un plancher de seuil suffiraient.

## Naruto_Storm_Connections_f0067594_U27

Combat Neji/Orochimaru contre Sasuke à 0–1, menu de pause avec « Retour à la sélection du personnage » (207), écran noir (210), puis un autre combat dans une autre arène, Koji Kashin contre Tenten à 0–0 (211). Étiquette juste, observations exactes. Le noir efface tout : la règle (a) ne voit pas le retour à 0–0, et ni le changement de noms ni la variation du score ne sont calculés. Le gradient boosting monte à 0,77 (seuil 0,884), le GRU reste à 0,16. Cause principale : `LECTURE_COUPEE` ; secondaires : `FIN_ENTRE_CAPTURES`, `SEUIL`, `CONTEXTE_SANS_VARIATION` (chrono 92 non converti en secondes, période inconnue). Comparer à la dernière observation lisible suffirait.

## Naruto_Storm_Connections_fdb79549_U01

La capture 1, première de l'enregistrement, montre un combat à 0–1 ; la capture 2 un combat à 0–0 avec un chrono de 90 (marqueurs vérifiés au zoom). Les rounds gagnés ne redescendent jamais : un nouveau combat a commencé entre les deux. Étiquette juste ; la règle (a) la trouve. Le GRU (0,22) n'a qu'une capture de mémoire, et le gradient boosting (0,56) une fenêtre à moitié vide sous un seuil de 0,981. Le changement de participants qui l'accompagne ne vaut rien dans ce jeu : les combattants se relaient en plein combat. Cause principale : `SEUIL` ; secondaires : `DEBUT_DE_SESSION` (nouveau code : fin sur les toutes premières captures d'un enregistrement), `FIN_ENTRE_CAPTURES`.

## Naruto_Storm_Connections_fdb79549_U02

Le côté droit allume son deuxième emplacement de round (0–2, vérifié au zoom) sur la capture 8, combat encore affiché. L'objectif de deux rounds est atteint, et 9 est l'écran titre de Dragon Ball Sparking! ZERO. Étiquette juste, observation exacte. Le GRU et les règles la trouvent sur 9 grâce au changement de jeu. Le gradient boosting monte à 0,80 sur 9, sous un seuil de 0,981, et ne voit rien sur 8 : aucune variable ne dit que le score a atteint l'objectif. Cause principale : `SEUIL` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `ABANDON`. Une variable « rounds gagnés = objectif » trouverait la fin dès la capture 8.

## J-Stars_Victory_VS+_fdb79549_U37

Combat libre de J-Stars Victory VS+ (jeu d'une seule session) : Ichigo mène 2–1 à 56 s, réplique d'Ichigo sans texte de résultat (471, masqué), puis « Choix du personnage » pour un nouveau combat avec Kenshirô (472). Étiquette juste. Le GRU (trois graines sur cinq) et la règle (c) la trouvent ; le gradient boosting la manque de trois millièmes (0,978 pour un seuil de 0,981). Cause principale : `SEUIL` ; secondaire : `JEU_RARE`.

## J-Stars_Victory_VS+_fdb79549_U38

Kenshirô contre Akainu à 2–2 dans les dernières secondes (« Temps 01.63 », écran bordé de rouge) en 486, puis menu principal « Combat libre » en 487, et le mode Aventure-J ensuite. Étiquette juste. La règle (c) la trouve. Le gradient boosting monte à 0,89 sous un seuil de 0,981. Le GRU a une moyenne de 0,71, au-dessus de son seuil, mais seules deux graines sur cinq la trouvent : d'autres ont sans doute annoncé dès 486, une capture trop tôt. Cause principale : `SEUIL` ; secondaires : `ANNONCE_EN_AVANCE`, `JEU_RARE`.

## Demon_Slayer_378c621d_U01

Manche décisive à 1–1 (13), puis accueil de la PS4 (14) et lancement de Dragon Ball FighterZ (15) : le combat de Demon Slayer (jeu d'une seule session) a été quitté. Étiquette juste. Le GRU (0,99, quatre graines sur cinq) et la règle (c) la trouvent. Le gradient boosting monte à 0,945, sous le seuil de 0,989 de ce tour. Cause principale : `SEUIL` ; secondaires : `ABANDON`, `JEU_RARE`.

## Synthèse du lot

28 cas : 9 d'UFC 5, 11 de Dragon Ball Sparking! ZERO, 2 de Dragon Ball FighterZ, 3 de Naruto Storm Connections, 2 de
J-Stars Victory VS+ et 1 de Demon Slayer. 14 sont manqués par les quatre détecteurs ; le gradient boosting en manque
27, le GRU 21, les règles 16. Les étiquettes sont justes dans 27 cas. Une seule est douteuse : UFC `f8c2843d` U21,
où la sortie du combat se lit déjà sur 637 (« … la partie en cours pour accéder au Choix des … ») et non sur 638.

### Causes principales

| Cause | Cas |
|---|---:|
| `SEUIL` | 12 |
| `REPRISE` | 6 |
| `LECTURE_COUPEE` | 4 |
| `ANNONCE_EN_AVANCE` | 2 |
| `ERREUR_OBSERVATION` | 1 |
| `ETIQUETTE_DOUTEUSE` | 1 |
| `FINS_CONSECUTIVES` | 1 |
| `FIN_ENTRE_CAPTURES` | 1 |

Causes secondaires les plus citées : `ABANDON` (10), `SIGNE_PROPRE_AU_JEU` (10), `JEU_RARE` (9), `SEUIL` (6),
`LECTURE_COUPEE` (6).

Trois codes nouveaux :
- `ANNONCE_EN_AVANCE` : le détecteur annonce sur une capture située entre la dernière capture de jeu et la preuve
  (transition, capture masquée). L'évaluation n'accepte que la preuve et la capture suivante : l'annonce compte comme
  fausse fin et la fin comme manquée.
- `FINS_CONSECUTIVES` : deux fins sur deux captures consécutives. Une même annonce n'en valide qu'une ; pour trouver
  les deux, il faudrait retomber sous le seuil entre les deux.
- `DEBUT_DE_SESSION` : la fin tombe sur les toutes premières captures d'un enregistrement. Le GRU n'a presque rien en
  mémoire, et la fenêtre du gradient boosting est remplie de zéros.

### Les familles vues

1. **Des seuils qui bloquent des fins bien vues.** Dans 15 des 28 cas, le seuil du gradient boosting dépasse 0,98, et
   il atteint 0,989 dans `378c621d` et `020621e7`. Le gradient boosting passe 0,88 sans annoncer dans 8 cas, dont
   Dragon Ball FighterZ U03, où l'écran « RÉSULTAT — VICTOIRE Équipe rouge » est pourtant bien noté comme résultat.
   Les règles n'ont d'ailleurs aucune règle sur le résultat affiché, et `post_game` compte pour elles comme « dans le
   jeu ».
2. **Des relances dont le signe existe à l'écran mais pas dans les variables.**
   - UFC (U18, U20, U23) : le chrono du 1er round remonte. Une hausse de plus de 20 s dans un même round n'apparaît
     que cinq fois dans tout PlayEnd : ces trois fins de `f8c2843d` et deux captures de Genshin Impact. Tenue à
     l'écart, cette session est donc jugée par des modèles qui n'ont jamais vu la variable positive.
   - Dragon Ball Sparking! ZERO (U16, fe69758b U04) : le « ∞ » marque le début d'un combat. Mais `clock.infinite` vaut
     1 sur 616 captures, dont 596 en entraînement de Mortal Kombat 1, sans aucune fin : les modèles ont appris le
     contraire.
   - Les autres indices de relance, à savoir les points de compétence remis à 0, l'introduction en position de départ
     et le bandeau « COULEUR DU SHORT », n'ont aucune place dans le contrat.
3. **La comparaison avec la seule capture d'avant.** Les règles (a), (c) et (d) comparent avec la capture juste avant,
   et les variables de changement avec la dernière observation, même noire ou sans titre. Un écran noir, l'accueil de
   la console, une scène sans HUD ou une pause effacent donc le changement de jeu (UFC U32), le retour à 0–0 (Naruto
   U27), la remontée du chrono (UFC U22), celle des barres de vie (fe69758b U04, U07, U08) et le passage du combat au
   menu (f8c2843d U17).
4. **Des artefacts de l'évaluation.** Dans UFC U01, le GRU annonce sur la transition qui précède l'écran « TKO ». Dans
   fdb79549 U04, les trois détecteurs annoncent sur l'accueil masqué juste avant le lancement de FC 26. Dans U16 et
   U16b, deux fins consécutives se disputent une seule annonce. Dans ces quatre cas, la détection était bonne, à une
   capture près.
5. **Peu d'erreurs du professeur.** Les erreurs relevées sont les suivantes :
   - le logo EA SPORTS FC26 noté « EA Sports UFC 5 » (UFC U02, titre repris de la capture d'avant) ;
   - l'accueil de la PS5 noté avec le titre du jeu par le premier professeur (020621e7 U01) ;
   - l'écran UFC « TKO » noté `other`, avec la carte des juges recopiée comme score (U01) ;
   - « Joueur 1 » et « Joueur 2 » notés comme participants sur un écran d'équipe ;
   - le texte de sortie de 637 non lu (U21).

### Ce qui m'a surpris

- Un écran de victoire explicite et bien annoté (Dragon Ball FighterZ U03) est manqué par les quatre détecteurs.
- Le « ∞ » a deux sens opposés selon le jeu : début de combat dans Dragon Ball Sparking! ZERO, entraînement sans fin
  dans Mortal Kombat 1.
- Seul l'UFC a un chrono converti en secondes avec un numéro de période : c'est le seul jeu où la variation du chrono
  existe (53 captures dans tout le corpus). Les chronos de Mortal Kombat 1, Naruto, Demon Slayer et J-Stars sont
  gardés en affichage seul, alors que le contrat autorise la conversion d'un chrono de round.
- Dans Naruto Storm Connections, les noms au-dessus des barres changent à chaque relais d'équipe : la variable
  `participants.primary.changed` y est du bruit.
- Deux joueurs d'UFC relancent le combat juste après avoir été mis au tapis (U20, U23).

### Les méthodes qui reviennent

- **Comparer avec la dernière observation lisible** (titre, phase, score, chrono, compteurs), en sautant le noir,
  l'accueil et les scènes sans HUD, et compter `paused` comme encore dans la partie. Cette seule méthode aurait
  donné un signal dans environ dix cas du lot.
- **Règles écrites à ajouter :**
  - le résultat affiché qui apparaît ;
  - le chrono de round décroissant qui remonte sans changement de round, confirmé par le bandeau de lancement (UFC :
    trois fins, aucune fausse dans le corpus) ;
  - le « ∞ qui apparaît » dans Dragon Ball Sparking! ZERO ;
  - le score qui atteint l'objectif (`score` = `counter.target.field`).
- **Seuil** : un plancher, ou un choix de seuil qui n'aille pas au-delà de 0,98, pour ne pas bloquer des fins
  vues à 0,9 et plus.
- **Évaluation** :
  - accepter une annonce posée entre la dernière capture de jeu et la preuve, capture masquée comprise ;
  - regrouper les fins consécutives d'une relance quittée aussitôt.
- **Conventions** :
  - convertir les chronos de round en secondes et noter la période ;
  - appliquer `ps5_home` à tout accueil de console ;
  - écrire `tko` quand « TKO » est affiché, et laisser la carte des juges hors du score ;
  - noter l'introduction d'un combat en `pre_game` ;
  - garder les points de compétence remis à 0 comme indice de début de combat.
