# Lot 7 : battle royale (Fortnite, Call of Duty: Warzone)

Analyse cas par cas des fins manquées. Les pseudos lus sur les images sont remplacés par « un pseudo ».

## Fortnite_27921669_U01

Partie de Battle Royale « Zéro construction » quittée deux minutes après le saut du bus. En 36, le joueur est en jeu à
99 joueurs restants, santé pleine ; en 37, il est au salon avec « PRÊT », et son coéquipier apparaît en hologramme
(encore en partie). L'étiquette est juste et bien placée. L'observation est correcte. Sur 37, aucune variable de
changement ne bouge : seul l'état brut passe de « jeu actif avec compteur » à « menu pre_game sans compteur ». Les règles
la trouvent par la règle (c) (active vers pre_game). Le gradient boosting monte à 0,937 sous un seuil de 0,964, et le
GRU a une moyenne de 0,384 au-dessus du seuil (0,377) mais seulement 2 graines sur 5 au-dessus : c'est un échec de
seuil et de vote. Une fin par abandon à 99 joueurs restants est rare dans les données, d'où l'hésitation. Cause
principale : `SEUIL` ; secondaire : `ABANDON`. Ce qui l'aurait trouvée : le vote sur la moyenne des graines, ou la
règle « jeu actif vers salon » associée au gradient boosting en battle royale.

## Fortnite_27921669_U02

Partie en escouade quittée vers l'accueil de la PS5 à 11 joueurs restants. En 74 le joueur est en jeu ; en 75 il est sur
l'accueil de la console, le menu d'options de Fortnite ouvert sur « Fermer le jeu » ; en 76 l'accueil sans menu ; en 77
la console passe en mode repos. La fin est vraie, mais l'étiquette est posée sur 76, qui n'apporte rien de plus que 75 :
les deux captures ont la même observation. Les détecteurs réagissent tous à 75 (GRU 0,65 au-dessus de son seuil,
gradient boosting 0,935, règle (c)), une capture avant l'étiquette, et l'appariement ne tolère que le retard. C'est
donc un problème de placement plus qu'un échec des détecteurs. Cause principale : `ETIQUETTE_DOUTEUSE` ; secondaires :
`ABANDON`, `MENU_AMBIGU` (l'accueil par-dessus un jeu peut précéder une reprise, d'où la prudence de l'annotateur). Ce
qui la trouverait : placer la fin sur 75, ou tolérer une annonce une capture en avance quand cette capture est déjà hors
jeu.

## Fortnite_a4e41f30_U01

Partie de battle royale en équipe quittée en cours. Le joueur, éliminé tôt puis rétabli (spectateur en 82–85, accueil
PS5 en 86, retour en jeu en 87), est vivant en 96 avec 15 joueurs restants, son coéquipier à terre ; en 97 apparaît
l'écran « BATTLE ROYALE — CONNEXION », puis en 98 le chargement d'une île créative (« SCRIMS », 60 manches). L'étiquette
est juste. Le professeur a laissé la phase intermediate sur 87–96 alors que le joueur joue : la fin arrive donc après
une capture qui ressemble à un spectateur avec un minuteur de rétablissement. Sur 97, aucune variable de changement ne
bouge ; les règles la trouvent par la règle (c), mais cette règle se trompe aussi en 86. Le GRU (0,35, seuil 0,672) et
le gradient boosting (0,068) n'y voient qu'une interruption. Cause principale : `ABANDON` ; secondaires :
`MENU_AMBIGU`, `ERREUR_OBSERVATION`. Ce qui la trouverait : un mode « île créative » noté dès l'écran de chargement de
l'île (changement de mode dans la fenêtre de tolérance), la correction de la phase, et une règle (c) limitée aux
chargements et salons du jeu.

## Fortnite_ccfc6589_U01

Partie en équipe, joueur de la console éliminé à 7 joueurs restants. En 64–65, il est spectateur d'une coéquipière, sa
carte de rétablissement expire dans 224 s ; en 66, chargement « BATTLE ROYALE — CONNEXION » ; en 67, salon avec la
coéquipière en hologramme. Il a quitté la partie : l'étiquette est juste. Le professeur a manqué les joueurs restants
visibles en vue spectateur (6 et 5) et a noté le spectateur en phase active. Sur 66, aucune variable de changement ne
bouge ; la règle (c) la trouve, le GRU monte à 0,539 pour un seuil de 0,641, le gradient boosting à 0,275 : un
minuteur de rétablissement juste avant fait croire à une équipe encore en jeu, et le chargement ressemble à celui qui
mène à l'île d'attente. Cause principale : `ABANDON` ; secondaires : `MENU_AMBIGU`, `SEUIL`, `ERREUR_OBSERVATION`. Ce
qui la trouverait : corriger les compteurs du spectateur, coder le spectateur partout de la même façon, et donner aux
modèles la variable « chargement ou salon juste après une capture de jeu ».

## Fortnite_ccfc6589_U04

Escouade éliminée à 3 joueurs restants. En 190, le joueur de la console est à terre (« SURVIVANT IV — 3 joueurs
restants ») ; en 191, il regarde l'adversaire qui a éliminé l'équipe, avec « EN ATTENTE DE L'ÉQUIPE… 0:37 », puis
« RECHERCHE DE LA PROCHAINE PARTIE ». L'étiquette est juste et bien placée ; l'observation est correcte (pre_game avec
minuteur, sans place affichée). Le GRU (0,788, 5 graines sur 5) et la règle (c) la trouvent ; seul le gradient boosting
la manque, à 0,949 pour un seuil de 0,967. Cause principale : `SEUIL`. Ce qui la trouverait : un seuil un peu plus bas
ou l'association avec la règle (c) ; noter cet écran en post_game aiderait aussi.

## Fortnite_ff1c7245_U03

Partie quittée trois minutes après le bus. En 105 le joueur plane à 87 joueurs restants, en pleine santé ; en 106 il est
seul dans le salon avec « JOUER ». L'étiquette est juste ; l'observation aussi. Sur 106, le changement de participants
vaut 1 et la phase passe au menu : la règle (c) la trouve, mais le GRU (0,33 pour 0,628) et le gradient boosting (0,308
pour 0,973) restent bas, parce qu'une fin à 87 joueurs restants, sans spectateur ni place, ne ressemble à aucune fin de
Fortnite qu'ils ont apprise. Cause principale : `ABANDON`. Ce qui la trouverait : la règle « capture de jeu puis salon »
associée au gradient boosting en battle royale, et plus d'abandons en début de partie dans les données.

## Fortnite_ff1c7245_U04

Partie en écran partagé, équipe parmi les deux dernières. En 150, le joueur du haut vient d'être éliminé (carte
« JOUEURS (SECTIONS) RESTANTS 6 (2) »), celui du bas est vivant à 45 PV ; en 151, 45 s plus tard, menu « PASSE DE
COMBAT » du salon. La place n'a pas été capturée, mais la fin est vraie et bien placée ; l'observation est correcte. Sur
151, aucune variable de changement ne bouge, seul l'état passe au menu : la règle (c) la trouve, le gradient boosting
monte à 0,926 pour un seuil de 0,973, le GRU à 0,439 pour 0,628, freiné par les rétablissements des captures
précédentes. Cause principale : `SEUIL` ; secondaire : `FIN_NON_CAPTUREE` (nouveau code : l'écran de place, de victoire
ou de résumé a duré moins qu'un intervalle de capture, et la preuve est un salon, un menu ou un chargement du jeu sans
résultat). Ce qui la trouverait : un seuil un peu plus bas ou la règle (c) associée au gradient boosting, et une capture
plus serrée en fin de partie.

## Fortnite_ff1c7245_U05

Fin explicite : en 183, « VOTRE PLACE : #7 » sur les deux vues de l'écran partagé, avec le nom de l'équipe adverse et
« Retourner au salon ». L'étiquette est juste et l'observation exemplaire (résultat, post_game, place 7). Le GRU la
trouve de justesse (3 graines, moyenne égale au seuil), les règles une capture plus tard, mais le gradient boosting ne
dépasse pas 0,694 pour un seuil de 0,973, alors que l'écran de fin est marqué : le compteur encore visible et les
minuteurs de rétablissement de la capture d'avant le retiennent. Cause principale : `SEUIL`. Ce qui la trouverait : une
règle « place affichée en battle royale = fin », ou un seuil moins extrême.

## Fortnite_ff1c7245_U07

Fin entre deux captures. En 281, les deux joueurs de l'écran partagé sont vivants à 6 joueurs restants ; 43 s plus tard
(282), un sondage « NOUS AIMERIONS AVOIR VOTRE AVIS ! » s'affiche par-dessus le salon, puis le menu du passe de combat.
Ce sondage ne vient qu'après une partie : l'étiquette est juste, mais l'écran de victoire ou de place n'a pas été
capturé. L'observation note le sondage comme un menu ordinaire. Sur 282, aucune variable de changement ne bouge ; la
règle (c) la trouve, le GRU monte à 0,434 (seuil 0,628) et le gradient boosting à 0,079 puis 0,43 (seuil 0,973). Cause
principale : `FIN_NON_CAPTUREE`. Ce qui la trouverait : noter le sondage en post_game, associer la règle (c) au gradient
boosting, capturer plus souvent en fin de partie.

## Fortnite_ff1c7245_U08

Les deux joueurs de l'écran partagé, éliminés, attendent un rétablissement en spectateurs (315–317, 27 joueurs
restants), puis reviennent au salon « FORTNITE OG » (318) pendant que leur coéquipier en ligne continue (hologramme,
bouton « REGARDER ») ; en 319 ils cherchent déjà une nouvelle partie. L'étiquette est juste. Les spectateurs sont notés
en phase active, alors que le même professeur les note intermediate ailleurs : le contrat ne dit pas comment les coder.
Sur 318, le changement de participants vaut 1 et la phase passe au menu ; la règle (c) la trouve, le GRU (0,321) et le
gradient boosting (0,427 puis 0,54) restent loin de leurs seuils. Cause principale : `ABANDON` ; secondaire :
`CONVENTION_MANQUANTE` (nouveau code : aucune convention ne fixe le codage d'une situation utile pour la fin, ici le
spectateur, et les lots la codent différemment). Ce qui la trouverait : une convention du spectateur appliquée partout
et la règle (c) associée au gradient boosting.

## Fortnite_ff1c7245_U09

En 339, les deux joueurs de l'écran partagé sont à terre à 44 joueurs restants ; en 340, chargement « FORTNITE OG —
CONNEXION », puis récompense et salon. L'étiquette est juste (sortie de la partie, place non capturée). Le mode est noté
en texte libre (« Zero Construction Sections » puis « Battle Royale »), ce qui fait passer game.mode.changed à 1 au
milieu de la partie et rien à la fin. Seule la règle (c) la trouve ; le GRU (0,24) et le gradient boosting (0,43)
restent loin des seuils. Cause principale : `ABANDON` ; secondaires : `CONVENTION_MANQUANTE`, `FIN_NON_CAPTUREE`. Ce
qui la trouverait : un vocabulaire fermé pour le mode, un indicateur « joueur à terre ou éliminé », la règle (c) associée
au gradient boosting.

## Fortnite_ff1c7245_U12

Le joueur, éliminé à 7 joueurs et 3 équipes restants, regarde un coéquipier (467, carte de rétablissement à 156 s), puis
revient au salon où le bouton « REGARDER » montre que ses coéquipiers jouent encore (468). L'étiquette est juste. Le
spectateur est noté en jeu actif, et le mode, noté en texte libre, change quatre fois en cinq captures. Le changement
de participants et la règle (c) donnent un signal sur 468 : les règles la trouvent, le gradient boosting monte à 0,746
(seuil 0,973), le GRU reste à 0,297. Cause principale : `ABANDON` ; secondaires : `CONVENTION_MANQUANTE`, `SEUIL`.

## Fortnite_ff1c7245_U14

L'escouade est éliminée alors qu'il restait deux équipes (547 : « 3 (2) ») ; en 548, le joueur regarde l'adversaire
(« VOUS REGARDEZ ») pendant que l'escouade attend la partie suivante (« EN ATTENTE DE LA PRÉPARATION DES AUTRES
JOUEURS… »). L'étiquette est juste. Le professeur note cet écran comme un menu ordinaire, avec les mêmes pseudos que dans
la partie, alors que l'autre professeur le note pre_game avec un minuteur (ccfc6589 U04, gradient boosting à 0,949) :
ici le gradient boosting reste à 0,292 et le GRU à 0,208, seule la règle (c) la trouve. Cause principale :
`ECRAN_NON_MARQUE` ; secondaires : `CONVENTION_MANQUANTE`, `FIN_NON_CAPTUREE`. Ce qui la trouverait : un codage
post_game fixé pour cet écran d'escouade éliminée.

## Fortnite_ff1c7245_U15

Le joueur, rétabli une fois (595), est de nouveau spectateur en 596 à 10 joueurs restants ; en 597, chargement « BATTLE
ROYALE — CONNEXION », puis salon avec les trois membres de l'escouade qui cherchent déjà une partie. L'équipe a été
éliminée entre deux captures : l'étiquette est juste, la place n'a pas été capturée. Seule la règle (c) la trouve ; le
gradient boosting monte à 0,875 (seuil 0,973), le GRU à 0,312, retenu par le rétablissement qu'il vient de voir. Cause
principale : `FIN_NON_CAPTUREE` ; secondaires : `SEUIL`, `MENU_AMBIGU`, `CONVENTION_MANQUANTE`.

## Call_of_Duty_078643a4_U32

Fin explicite : en 266, l'écran « RÉSUMÉ PARTIE » de Résurgence affiche « 9e place » avec le menu « REJOUER / QUITTER
LA PARTIE », juste après une vue spectateur. L'étiquette est juste. Le professeur a bien noté post_game et scoreboard,
mais pas le résultat ni la place, contrairement à la convention de Warzone. Le gradient boosting (0,999), la régression
logistique et les règles la trouvent ; le GRU reste à 0,393 pour un seuil de 0,481. Cause principale :
`ECRAN_NON_MARQUE` ; secondaire : `SEUIL`. Ce qui la trouverait : une trace qui ajoute le résultat et la place 9.

## Call_of_Duty_078643a4_U33

L'escouade est à terre à 2 équipes restantes (306–308) ; en 309, « ÉLIMINATION FINALE » et la dernière killcam
annoncent la fin ; en 311, le résumé montre « VICTOIRE » pour l'« ESCOUADE ENNEMIE ». L'étiquette est juste. Le
professeur note result / post_game sur 309 mais laisse result.visible à null, et il attribue la victoire de 311 à
l'équipe du joueur. Aucun détecteur ne la trouve : le gradient boosting s'arrête à 0,948 (seuil 0,97), le GRU à 0,313,
et les règles ne regardent pas le passage à post_game. Cause principale : `ECRAN_NON_MARQUE` ; secondaires : `SEUIL`,
`ERREUR_OBSERVATION`. Ce qui la trouverait : une trace qui marque le résultat sur 309, et une règle « passage à
post_game = fin ».

## Call_of_Duty_7616a3a5_U01

En 53, la partie de Résurgence en est au cercle 7 avec 2 équipes restantes ; en 54, l'écran « RÉCOMPENSES »
d'après-partie, puis le salon de Warzone. L'étiquette et l'observation sont justes (post_game, sans place écrite). Le
GRU (0,834, 5 graines) et les règles (une capture plus tard) la trouvent ; le gradient boosting monte à 0,959, sous un
seuil de 0,994. Cause principale : `SEUIL` ; secondaire : `FIN_NON_CAPTUREE` (le résumé avec la place n'a pas été
capturé).

## Call_of_Duty_7616a3a5_U02

Victoire de l'escouade : en 99, « ÉLIMINATION FINALE » avec la dernière killcam du joueur de la console, puis la
cinématique de fin et « VICTOIRE » en 101. L'étiquette est juste ; le professeur note post_game mais pas de résultat sur
99, et la cinématique de 100 en phase active. Le GRU la trouve (0,823) ; le gradient boosting s'arrête à 0,985 pour un
seuil de 0,994, et les règles ne voient pas le passage à post_game. Cause principale : `SEUIL` ; secondaire :
`CONVENTION_MANQUANTE` (« ÉLIMINATION FINALE » sans codage fixé).

## Call_of_Duty_7616a3a5_U03

Fin explicite : en 143, le résumé de Résurgence affiche « 3e place », juste après une vue spectateur à 3 équipes
restantes. L'étiquette est juste et l'observation exemplaire (résultat, place 3). Le GRU (0,99) et la régression
logistique la trouvent ; le gradient boosting monte à 0,988 pour un seuil de 0,994, et les règles ne connaissent pas le
passage à post_game. Cause principale : `SEUIL`. Ce qui la trouverait : un seuil plafonné ou une règle « place affichée
= fin ».

## Call_of_Duty_7616a3a5_U04

Le joueur, seul dans son escouade à 11 équipes restantes, est tué (182, « KILLCAM »), puis vient un écran noir (183) et
le salon de Warzone qui cherche déjà une nouvelle partie (184). L'étiquette est juste : la killcam seule ne prouve rien,
le salon si. Les observations sont correctes, mais la killcam sans HUD et l'écran noir séparent la dernière capture de
jeu du salon : la règle (c), qui compare à la capture juste avant, ne se déclenche pas, et la fenêtre de deux captures
du gradient boosting (0,18) ne voit plus la partie. Le GRU monte à 0,527 (seuil 0,635). Cause principale :
`LECTURE_COUPEE` ; secondaires : `SEUIL`, `FIN_NON_CAPTUREE`. Ce qui la trouverait : comparer à la dernière capture
lisible du même jeu plutôt qu'à la précédente.

## Call_of_Duty_7616a3a5_U06

Le joueur, déjà passé par le Goulag, est tué (261) puis regarde un coéquipier (262–263, 33 équipes restantes) ; après un
trou de capture de 271 s, un écran noir (264) puis le salon de Warzone (265). L'étiquette est juste. Le GRU la trouve
(0,859) ; les règles la manquent parce que l'écran noir s'intercale entre le jeu et le salon, et le gradient boosting
monte à 0,667 sous un seuil de 0,994. Cause principale : `LECTURE_COUPEE` ; secondaires : `SEUIL`,
`FIN_NON_CAPTUREE`. Ce qui la trouverait : comparer à la dernière capture lisible du même jeu.

## Call_of_Duty_ff1c7245_U01

Le joueur, mort, regarde un coéquipier qui peut encore le racheter (47–49, 20 équipes restantes), puis passe par l'écran
de progression du passe de combat (50) et se retrouve seul au salon (51). L'étiquette est juste : il a quitté la partie
(ou son escouade est tombée). Le professeur note cet écran d'après-partie comme un menu, alors que l'autre professeur
note l'écran équivalent post_game. La règle (c) la trouve ; le gradient boosting monte à 0,837 (seuil 0,973), le GRU
reste à 0,352. Cause principale : `ABANDON` ; secondaires : `CONVENTION_MANQUANTE`, `SEUIL`.

## Call_of_Duty_ff1c7245_U02

Le joueur meurt au premier cercle (72, 87 joueurs restants, redéploiement actif), puis viennent un chargement noir (73),
l'écran « PROGRESSION — EXP DE LA PARTIE » (74) et la mise en repos de la PS5 (75). L'étiquette est juste, posée sur
la première preuve nette. Le gradient boosting la trouve sur 74 (0,98) ; le GRU reste à 0,469 ; la règle (c) se
déclenche sur 73, une capture trop tôt pour l'appariement. Cause principale : `ABANDON` ; secondaire :
`ANNONCE_EN_AVANCE` (nouveau code : un détecteur annonce la fin une capture avant la capture qui la prouve, sur un écran
de transition, et l'appariement, qui ne tolère que le retard, la compte comme fausse).

## Synthèse du lot

23 cas regardés (14 Fortnite, 9 Warzone). 22 étiquettes sont justes ; une est douteuse par son placement
(Fortnite `27921669` U02, posée une capture après le premier écran d'abandon). Causes principales : `ABANDON` 8,
`SEUIL` 7, `ECRAN_NON_MARQUE` 3, `FIN_NON_CAPTUREE` 2, `LECTURE_COUPEE` 2, `ETIQUETTE_DOUTEUSE` 1. Trois codes ont été
ajoutés : `FIN_NON_CAPTUREE` (l'écran de place, de victoire ou de résumé tombe entre deux captures, la preuve est un
salon, un menu ou un chargement du jeu sans résultat), `CONVENTION_MANQUANTE` (aucune convention ne fixe le codage d'une
situation utile pour la fin, et les lots la codent différemment) et `ANNONCE_EN_AVANCE` (un détecteur annonce la fin
une capture avant la capture qui la prouve, et l'appariement, qui ne tolère que le retard, la compte comme fausse).

**Familles vues.**

- *La sortie de partie sans résultat* (Fortnite surtout) : le joueur de la console, éliminé et spectateur ou encore
  vivant, quitte la partie ; la preuve est un chargement « BATTLE ROYALE — CONNEXION », le salon (souvent avec le
  coéquipier en hologramme ou le bouton « REGARDER ») ou un menu du jeu. Sur la capture de preuve, aucune variable de
  changement ne bouge : seul l'état brut passe du jeu au menu. La règle (c) trouve 12 de ces fins que le GRU et le
  gradient boosting manquent tous les deux.
- *Le seuil du gradient boosting* : 0,964 à 0,994 selon le tour. Il monte à 0,926–0,988 sur sept fins sans les annoncer,
  y compris deux écrans de place parfaitement notés (« VOTRE PLACE : #7 », 0,694 ; « 3e place », 0,988).
- *Des écrans de fin mal codés* : « 9e place » sans résultat (Warzone `078643a4` U32), « ÉLIMINATION FINALE » avec
  result.visible à null (U33) et une « VICTOIRE » de l'escouade ennemie attribuée au joueur, l'écran Fortnite de
  l'escouade éliminée (« VOUS REGARDEZ » l'adversaire + attente de la partie suivante) noté menu par un professeur et
  pre_game avec minuteur par l'autre.
- *Les écrans noirs et killcams intercalés* (Warzone `7616a3a5` U04, U06) : la règle (c) compare à la capture juste
  avant, notée unknown, et ne se déclenche pas ; la fenêtre de deux captures du gradient boosting perd la partie.

**Ce qui m'a surpris.**

- Le spectateur n'a pas de codage fixé : active chez l'un, intermediate chez l'autre, et le même professeur varie d'une
  session à l'autre. Le compteur de joueurs restants, pourtant visible en vue spectateur, a même été oublié (ccfc6589
  U01). Or un minuteur de rétablissement juste avant la fin fait baisser le GRU : il a appris qu'une équipe avec carte
  de rétablissement revient souvent (a4e41f30 U01, ff1c7245 U15).
- Le mode de Fortnite est noté en texte libre (« Zero Construction Sections », « Battle Royale », « Construction, Solo »…)
  et game.mode.changed se déclenche au milieu des parties ou entre deux écrans du salon, jamais au bon moment.
- Le GRU ne trouve aucune fin de Fortnite prouvée par un simple passage au salon ou au chargement, sauf de justesse ;
  il trouve en revanche presque toutes les fins de Warzone qui passent par post_game (5 sur 5 dans `7616a3a5`).
- Deux fins sont « manquées » alors que les détecteurs réagissent une capture trop tôt (accueil PS5 avec « Fermer le
  jeu », chargement « WZ ») : c'est l'appariement, pas le modèle, qui les perd.
- Aucune règle écrite ne regarde le passage à post_game : les règles manquent ainsi trois fins de Warzone qui ont un
  écran de fin.

**Méthodes qui reviennent.**

1. Une règle de battle royale « capture de jeu (compteur présent) → salon, menu, chargement ou post_game du même jeu =
   fin », calculée par rapport à la dernière capture lisible du même jeu (en sautant noir et killcam), associée au
   gradient boosting ou au GRU pour ce genre. Elle aurait trouvé 21 des 23 fins (toutes sauf les deux annonces en avance).
2. Un seuil du gradient boosting plafonné (0,95 environ) ou fixé par genre : sept fins passent avec lui.
3. Des conventions fixées et appliquées par des traces : spectateur en intermediate avec un indicateur « joueur de la
   console éliminé » ; post_game pour les écrans d'après-partie (récompenses, progression, sondage, escouade éliminée
   qui regarde l'adversaire, « ÉLIMINATION FINALE ») ; result et place dès que « Xe place » est écrit ; vocabulaire
   fermé pour le mode de Fortnite, île créative comprise dès son écran de chargement.
4. Une tolérance d'une capture en avance quand cette capture est déjà hors jeu, ou un placement de la fin sur ce premier
   écran hors jeu.
5. Une capture plus serrée en fin de partie (moins de 10 joueurs restants), pour saisir « VOTRE PLACE » ou « VICTOIRE
   ROYALE », et plus d'abandons en début de partie dans les données, pour que le nombre de joueurs restants élevé ne
   serve plus de contre-indice.
