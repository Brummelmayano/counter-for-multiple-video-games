# Lot lot3_eafc_a : fins manquées d'EA Sports FC (26 cas)

## EA_Sports_FC_11029423_U03

Paris SG – Manchester City est recommencé vers la 80e minute. En 76, le tableau donne 4–2 à 79:59 ; 77 et 78 montrent un coup d'envoi sans tableau de score, ce qui ne prouve rien seul (un coup d'envoi suit aussi un but). En 79, le menu « Match classique » affiche « 0:00 Paris SG 0 - 0 Manchester City » : le match est reparti de zéro, ce que confirme 81 (0–0 à 02:51). L'étiquette est juste et l'observation aussi.

Les variables ne voient rien : la précédente (78) n'a pas de score, donc la variation du score n'est pas calculée, et la période unknown interdit de toute façon la variation du chrono (79:59 → 0:00). Le gradient boosting ne voit que 77, 78 et 79, sans aucun score non nul ; le GRU, qui a 4–2 en mémoire, reste à 0,03. Les règles ne se déclenchent pas : pas de score sur la précédente, et la phase « paused » n'est pas dans la liste de la règle (c).

Cause principale : `LECTURE_COUPEE` (les deux captures sans tableau effacent la comparaison 4–2 → 0–0) ; secondaires : `REPRISE`, `CONTEXTE_SANS_VARIATION`, `MENU_AMBIGU`. Ce qui l'aurait trouvée : comparer le score et le chrono à la dernière valeur lisible du même contexte (76), et accepter pour EA FC une baisse du chrono de match même quand la période est unknown.

## EA_Sports_FC_11029423_U04

PSG – Manchester City finit à 3–5 (107 : 91:35, +1). Le coup de sifflet final et l'écran de résultat tombent entre 107 et 108. En 108, l'écran « Équipe » d'avant-match montre l'effectif du PSG contre celui du Bayern (Kane, Musiala) : un autre match se prépare, puis 110 « Choix des équipes » Getafe contre Bayern. L'étiquette est juste. Aucun nom d'équipe n'est écrit sur l'écran Équipe : les participants vides sont conformes, mais le changement d'adversaire est ainsi invisible pour les variables.

Les règles la trouvent (règle (c), passage de active à menu). Le GRU monte nettement de 0,01 à 0,34, sous son seuil de 0,57 ; le gradient boosting reste à 0,16 (seuil 0,71). Dans EA FC, les écrans d'équipe apparaissent aussi en cours de match, ce qui rend ce menu ambigu pour les modèles ; la période unknown les prive aussi d'un indicateur « fin du temps réglementaire » alors que le chrono était à 91:35.

Cause principale : `MENU_AMBIGU` ; secondaires : `SEUIL`, `CONTEXTE_SANS_VARIATION`. Ce qui l'aurait trouvée : une variable « dernier chrono lu ≥ 90:00 » ou une période déduite du chrono pour le football, gardée jusqu'au menu suivant.

## EA_Sports_FC_11029423_U06

Real Madrid – Bayern finit à 4–1 (167 : 92:21, +3). En 168, le menu « Match classique » commence par « Quitter le match », propose « Recommencer ce match », « Détails du match » et « Highlighter », n'a pas de « Reprendre match » et montre en fond les supporters qui quittent le stade, avec le chrono figé à 90:00 : c'est le menu d'après-match. L'étiquette est juste.

Le professeur l'a noté comme une pause (pause, paused, aucun résultat) : l'écran de fin est perdu. Les variables voient une pause à score inchangé, ce qui arrive sans cesse en cours de match ; le recul du chrono (92:21 → 90:00), qui aurait trahi l'écran, n'est pas calculé à cause de la période unknown. GRU 0,006 puis 0,23 deux captures plus tard, gradient boosting 0,015 ; aucune règle ne couvre le passage active → paused.

Cause principale : `ECRAN_NON_MARQUE` ; secondaires : `MENU_AMBIGU`, `CONTEXTE_SANS_VARIATION`. Ce qui l'aurait trouvée : une convention FC 26 qui note ce menu sans « Reprendre » comme écran de résultat (post_game, result.visible), et une variation du chrono calculée pour le football même sans période.

## EA_Sports_FC_11029423_U07

Paris SG – FC Barcelone : 2–2 à 90:57 en 199 (égalisation dans le temps additionnel), puis en 200–202 un menu de pause figé à 90:00 avec des ralentis en fond, et en 203 l'écran « Classique / But en or / Tirs au but / Finir sur un match nul » qu'EA FC propose après un nul ; 204 est un nouveau match à 0–0 à 02:32. La fin est donc juste, entre 199 et 200, mais 200 seul est moins parlant que le menu d'après-match de U06 : il garde « Reprendre match ».

Le professeur note 200 comme une pause, ce qui se défend sur une image seule. Le vrai problème est ailleurs : le titre alterne entre « EA Sports FC » et « EA Sports FC 26 », les équipes entre « PSG/BAR » et « Paris SG/FC Barcelone » ; les variations de score et de chrono ne sont plus calculées (« même contexte » rompu) et les drapeaux de changement de titre et de participants se lèvent pour rien. Le recul du chrono 90:57 → 90:00 reste invisible. 203 est noté comme un écran de console sans jeu. GRU 0,15 puis 0,05, gradient boosting 0,03, aucune règle.

Cause principale : `MENU_AMBIGU` ; secondaires : `CONTEXTE_SANS_VARIATION`, `ERREUR_OBSERVATION`, `SIGNE_PROPRE_AU_JEU`. Ce qui l'aurait trouvée : normaliser titres et noms d'équipe, calculer le recul du chrono du football sans période connue, et une convention pour l'écran de départage d'un nul.

## EA_Sports_FC_11029423_U08

PSG – FC Barcelone finit à 1–4 (229 : 91:07, +1). En 230 et 231, le menu de pause affiche 90:00 pile et un ralenti en fond : c'est le résumé d'après-match mis en pause. En 232, le bandeau de coup d'envoi « PSG 0 · 0 BAR » ouvre le match suivant. L'étiquette est juste ; la pause en cours de match de la capture 206 a exactement le même menu, donc le professeur ne peut pas la distinguer sur une seule image, sauf par le 90:00.

Ce cas n'est pas vraiment une fin ratée : le GRU (0,88), le gradient boosting (0,96) et la règle (a) se déclenchent tous sur 232, au retour à 0–0, mais c'est deux captures après la preuve, une de trop pour la tolérance. Le seul signal à l'heure, le recul du chrono 91:07 → 90:00, n'est pas calculé à cause de la période unknown ; à la place, participants.primary.changed se lève pour une simple différence d'écriture.

Cause principale : `RETARD` (code ajouté : fin annoncée nettement après la tolérance, au début de la partie suivante) ; secondaires : `MENU_AMBIGU`, `CONTEXTE_SANS_VARIATION`. Ce qui l'aurait trouvée : calculer le recul du chrono pour le football sans période connue, ou accepter un retard de deux captures quand celles du milieu sont des menus de la même partie.

## EA_Sports_FC_11029423_U10

PSG – FC Barcelone finit à 5–2 (298 : 90:17, +1). En 299, le menu d'avant-coup d'envoi affiche « 0:00 Paris SG 0 - 0 FC Barcelone », avec « Options pour recommencer » actif et « Fin du match » grisé : le match suivant (ou le même relancé) va commencer. L'étiquette est juste et les valeurs sont bien lues.

La règle (a) la trouve (7 buts puis 0–0 dans le même jeu). Les modèles, eux, n'ont pas la variation du score : le titre est écrit « EA Sports FC 26 » en 298 et « EA Sports FC » en 299, donc le « même contexte » est rompu et la variation −5/−2 n'est pas calculée. Il ne leur reste qu'une pause à 0–0 et des drapeaux de changement de titre et de participants qui se lèvent souvent pour rien : GRU 0,25, gradient boosting 0,045.

Cause principale : `CONTEXTE_SANS_VARIATION` ; secondaires : `REPRISE`, `MENU_AMBIGU`. Ce qui l'aurait trouvée : calculer le contexte sur la famille de jeu normalisée, comme les règles, et non sur le titre écrit.

## EA_Sports_FC_11029423_U11

PSG – FC Barcelone est en prolongation (4–4 à 94:35 et 96:32, sans « PR » lisible), le PSG marque à 97:35 (5–4), puis 339 montre le bandeau de coup d'envoi « PSG 0 · 0 BAR » d'un nouveau match ; 340 est à 0–0 à 05:01. Le match a été relancé avant la fin de la prolongation ; l'étiquette est juste.

La règle (a) la trouve. Les modèles non : le titre est écrit « EA Sports FC 26 » en 338 et « EA Sports FC » en 339, ce qui rompt le contexte et supprime la variation du score (5–4 → 0–0). Il reste un coup d'envoi après une célébration de but, situation banale : GRU 0,185, gradient boosting 0,05.

Cause principale : `CONTEXTE_SANS_VARIATION` ; secondaire : `REPRISE`. Même remède que U10 : un contexte calculé sur la famille de jeu normalisée.

## EA_Sports_FC_11029423_U12

En prolongation, Barça mène 3–4 ; en 381, le menu de pause (« 115:20 PR ») est déroulé sur « Recommencer ce match / Recommencer avec d'autres équipes » et « Fin du match », puis 382 est l'écran « Choix des équipes » Paris SG contre FC Barcelone. Le match est abandonné en pleine prolongation et compte comme une partie ; l'étiquette est juste, et les observations aussi (le « PR » du menu donne une période overtime, alors que le HUD en jeu reste unknown).

Le GRU monte à 0,42 sur 382 (une graine sur cinq la trouve), sous le seuil de 0,57 ; le gradient boosting reste à 0,08 parce que sa fenêtre de trois captures ne contient aucune capture de jeu lisible. La règle (c) ne joue pas car la précédente est une pause, que la règle ne compte pas comme une phase de jeu.

Cause principale : `SEUIL` ; secondaires : `MENU_AMBIGU`, `REPRISE`. Ce qui l'aurait trouvée : traiter la pause comme une phase de partie dans la règle (c), et une variable « choix des équipes après un score lu dans le même jeu ».

## EA_Sports_FC_11029423_U13

PSG – FC Barcelone va aux tirs au but : en 420, PSG mène 4–3 après cinq tirs contre quatre, et le 5e tir du Barça (421, sans HUD) décide. En 422, un nouveau match est déjà en pause à 2:26, 0–0. L'étiquette est juste ; le résultat de la séance n'est pas capturé. Les valeurs sont bien lues ; les pastilles de tirs restants ne sont pas notées, par convention du football.

La capture 421 sans HUD coupe la comparaison : pas de variation 4–3 → 0–0 sur 422, pas de règle (a), et la période passe de other à unknown. GRU 0,03, gradient boosting 0,05 : une pause à 0–0 en début de match est banale, et les tirs au but sont rares dans les données.

Cause principale : `LECTURE_COUPEE` ; secondaires : `REPRISE`, `MENU_AMBIGU`, `SIGNE_PROPRE_AU_JEU`. Ce qui l'aurait trouvée : comparer à la dernière valeur lisible (4–3 en 420), et noter les pastilles des tirs au but comme compteur de ce qui reste.

## EA_Sports_FC_11029423_U15

Barça – Arsenal est relancé à la 35e minute : 467 donne 0–3 à 35:08, 468–470 montrent les écrans d'équipe et « Prêt(e) ! », 471 un coup d'envoi sans tableau, et 472 donne 0–1 à 04:07. Le nouveau match a déjà un but au moment de la preuve. L'étiquette est juste : les écrans d'équipe annoncent sans doute la relance, mais avec les mêmes équipes ils peuvent aussi apparaître en cours de match (la session en montre aux captures 348–352), donc 472 est la première preuve sûre.

Rien ne passe dans les variables : la précédente (471) n'a pas de score, la baisse du score d'Arsenal (3 → 1) et le recul du chrono (35:08 → 04:07) ne sont pas calculés. GRU 0,004, gradient boosting 0,001. La règle (a) ne peut pas jouer (0–1, pas 0–0) ; la règle (c) a vu la sortie vers les menus en 468, quatre captures trop tôt.

Cause principale : `LECTURE_COUPEE` ; secondaires : `REPRISE`, `CONTEXTE_SANS_VARIATION`. Ce qui l'aurait trouvée : un invariant « le score ne baisse jamais, le chrono ne recule jamais » mesuré contre la dernière valeur lisible du même jeu, au lieu d'exiger un retour exact à 0–0.

## EA_Sports_FC_11029423_U16

Barça – Arsenal est relancé vers la 79e minute : 6–3 à 78:42 en 497, un plan rapproché sans tableau en 498, puis 0–0 à 04:46 en 499 avec les mêmes équipes. La relance tient tout entière dans les 44 s entre 498 et 499. L'étiquette et les observations sont justes.

La capture 498 sans tableau efface la comparaison : pas de variation 6–3 → 0–0, pas de règle (a). Le gradient boosting monte un peu (0,18) parce que 6–3 est encore dans sa fenêtre ; le GRU reste à 0,06.

Cause principale : `LECTURE_COUPEE` ; secondaires : `REPRISE`, `CONTEXTE_SANS_VARIATION`. Ce qui l'aurait trouvée : la règle (a) et les variations calculées contre le dernier score lisible du même jeu.

## EA_Sports_FC_11029423_U17

Barça – Arsenal est relancé à la 73e minute (3–1) : 526–528 montrent les écrans d'équipe et « Prêt(e) ! », puis 529 donne 0–0 à 02:16 avec l'encart des commentateurs de début de match. L'étiquette sur 529 suit la règle de la première preuve sûre, car l'écran Équipe partagé existe aussi en cours de match (378c621d, capture 332).

Ce n'est pas une fin ignorée : le GRU l'annonce sur 526 (0,667, au-dessus du seuil), et la règle (c) aussi, dès la sortie vers les menus, trois captures avant la fin étiquetée. L'annonce n'est donc pas comptée. Sur 529, plus rien, parce que 528 n'a pas de score.

Cause principale : `AVANCE` (code ajouté : annonce faite avant la capture qui prouve la fin, sur la sortie vers des menus ambigus, hors tolérance) ; secondaires : `MENU_AMBIGU`, `LECTURE_COUPEE`, `REPRISE`. Remède : rapprocher l'annonce de sortie et la preuve dans l'évaluation, ou comparer au dernier score lisible.

## EA_Sports_FC_11029423_U20

Barça – Arsenal arrive au bout du temps réglementaire à 4–5 (618 : 88:14 ; 619 : fondu sans tableau, panneaux « Tiempo añadido 1 »), puis 620 montre un nouveau match à 0–0 à 04:14 avec les mêmes équipes. L'étiquette et les observations sont justes.

La capture 619 sans tableau efface la variation 4–5 → 0–0 et empêche la règle (a). Le gradient boosting monte à 0,42 grâce au 4–5 encore dans sa fenêtre, sous le seuil de 0,71 ; le GRU reste à 0,09.

Cause principale : `LECTURE_COUPEE` ; secondaires : `REPRISE`, `SEUIL`, `CONTEXTE_SANS_VARIATION`. Remède : comparer au dernier score lisible du même jeu.

## EA_Sports_FC_11029423_U21

Barça – Arsenal se termine à 1–7 vers 89:37 ; 644 montre les supporters d'Arsenal sans HUD, puis 645 l'écran de chargement de Mortal Kombat 1 : la console change de jeu. L'étiquette et les observations sont justes (pas de titre écrit sur le chargement).

Le gradient boosting la trouve (0,94). Le GRU monte à 0,48, sous son seuil de 0,57 (deux graines sur cinq). Les règles la manquent parce que les captures intermédiaires n'ont ni phase de jeu (644 unknown) ni titre (645) : ni la règle (c) ni la règle (d) ne voient deux captures consécutives qui se comparent.

Cause principale : `SEUIL` ; secondaires : `ABANDON`, `LECTURE_COUPEE`. Remède : des règles qui comparent au dernier titre et à la dernière phase connus.

## EA_Sports_FC_378c621d_U04

Barça – PSG se termine vers 88:41 à 0–6 ; après une transition violette (238), 239 est l'écran « Choix des maillots » d'un nouveau match Real Madrid – Bayern. L'étiquette est juste ; le titre passe de « EA Sports FC » à « EA Sports FC 27 » sur les menus, simple variation de notation.

Les deux modèles la voient : GRU 0,93 sur 238 et 0,69 sur 239, gradient boosting 0,97 sur 239. Mais les seuils de ce tour sont 0,988 et 0,989. La règle (c) ne joue pas à cause de la transition de phase unknown entre le jeu et le menu.

Cause principale : `SEUIL` ; secondaires : `FIN_ENTRE_CAPTURES`, `LECTURE_COUPEE`. Remède : un seuil moins extrême ou calibré par famille, et une règle (c) qui saute les captures unknown.

## EA_Sports_FC_378c621d_U06

Real Madrid – Barça (habillage LaLiga) est à 0–5 à 84:12, puis à 89:12 un encart de carton jaune cache le score, et 341 montre le menu principal d'EA FC 27 : le match a été quitté ou terminé sans que l'écran de résultat soit capturé. L'étiquette et les observations sont justes.

La règle (c) la trouve, et les deux modèles la voient presque : GRU 0,962 et gradient boosting 0,909, contre des seuils de 0,988 et 0,989 dans ce tour.

Cause principale : `SEUIL` ; secondaires : `ABANDON`, `FIN_ENTRE_CAPTURES`. Remède : un seuil moins extrême ou calibré par famille.

## EA_Sports_FC_42dcc5f5_U01

PSG – Bayern (habillage Ligue des champions) finit à 3–3 d'après le grand bandeau de 148, et 149 est l'écran « Finale UCL — Choix des équipes » d'un autre match (CFR Cluj contre Angers en défilement). L'étiquette et les observations sont justes.

Le GRU (0,92, cinq graines) et la règle (c) la trouvent. Seul le gradient boosting la manque, à 0,977 contre un seuil de 0,987.

Cause principale : `SEUIL`. Remède : un seuil moins strict pour le gradient boosting.

## EA_Sports_FC_42dcc5f5_U02

Bayern – Real Madrid se termine à 3–2 à 90:00 (178), puis 179 affiche dans le vestiaire « VAINQUEUR — Joueur 2 », et 180 le choix des équipes du match suivant. L'étiquette et l'observation sont parfaites : l'écran de fin est noté comme résultat.

Le GRU (0,93) et la règle (c) la trouvent. Le gradient boosting la manque à 0,985 pour un seuil de 0,987, malgré un écran de résultat explicite.

Cause principale : `SEUIL`. Remède : un seuil moins serré, ou une règle sur result.visible combinée au modèle.

## EA_Sports_FC_42dcc5f5_U03

Barça – Real Madrid se termine vers 1–2 (211 : 86:58) ; 212–213 montrent les tribunes et la célébration du Real sans HUD, 214 un message de connexion de la console au retour dans les menus, et 215 l'aperçu du match suivant avec le face-à-face « 1 victoire — 0 nul — 1 victoire ». L'étiquette est juste.

Le GRU la trouve (0,79, cinq graines) grâce à sa mémoire. Le gradient boosting (0,13) ne voit que deux cinématiques et un message dans sa fenêtre de trois captures, et la règle (c) ne joue pas parce que la précédente a une phase unknown.

Cause principale : `LECTURE_COUPEE` ; secondaires : `MENU_AMBIGU`, `SIGNE_PROPRE_AU_JEU`. Remède : des variables d'état porté (dernière phase connue) pour les modèles sans mémoire, et noter le face-à-face comme compteur series.

## EA_Sports_FC_42dcc5f5_U05

Real Madrid – Barça est à 3–4 à 89:55 (291) ; 292 montre une célébration du Barça sans tableau, 293 un écran noir de chargement, puis 295 le logo de Naruto Storm Connections : la console a quitté EA FC. L'étiquette et les observations sont justes.

Le GRU la trouve (0,77). Le gradient boosting monte à 0,97, sous son seuil de 0,987. Les règles la manquent : la cinématique de phase unknown et les chargements sans titre empêchent toute comparaison entre deux captures consécutives.

Cause principale : `SEUIL` ; secondaires : `ABANDON`, `LECTURE_COUPEE`. Remède : un seuil moins strict, et des règles qui comparent à la dernière phase et au dernier titre connus.

## EA_Sports_FC_7616a3a5_U08

Real Madrid – Lombardia se termine à 2–3 (355 : 90:51, +1), puis 356 est l'écran « Choix des équipes » Real Madrid contre Torino ; 358 montre le face-à-face avec une victoire de Lombardia. L'étiquette est juste. L'observation de 356 laisse les participants vides alors que les deux équipes sont écrites, et la note l'écran comme menu plutôt que team_select.

Le gradient boosting (0,998) et la règle (c) la trouvent ; le GRU reste à 0,40 sous son seuil de 0,635 (une graine sur cinq). Avec les équipes notées, participants.primary.changed aurait signalé le changement d'adversaire.

Cause principale : `SEUIL` ; secondaire : `ERREUR_OBSERVATION`. Remède : noter les équipes écrites des écrans de choix et le face-à-face comme compteur series.

## EA_Sports_FC_7616a3a5_U09

Real Madrid – Lombardia est à 4–2 à 86:55 (384) ; 385 est un fondu sans HUD sur un coup d'envoi, et 386 un nouveau match à 0–0 à 03:55 avec les mêmes équipes et le bandeau de composition de début de match. L'étiquette et les observations sont justes (la minute de but 85′ n'est pas prise pour le chrono).

La capture 385 sans HUD empêche la variation 4–2 → 0–0 et la règle (a). Le gradient boosting monte quand même à 0,973 grâce au 4–2 de sa fenêtre, sous un seuil de 0,994 ; le GRU reste à 0,13.

Cause principale : `LECTURE_COUPEE` ; secondaires : `SEUIL`, `REPRISE`, `CONTEXTE_SANS_VARIATION`. Remède : comparer au dernier score lisible.

## EA_Sports_FC_7616a3a5_U10

Real Madrid – Lombardia est relancé vers la 84e minute : 3–1 à 84:17 en 407, 0–0 à 00:52 en 408, sans écran entre les deux. L'étiquette et les observations sont justes, et la notation stable permet aux variations d'être calculées (−3 et −1).

Le GRU (0,91) et la règle (a) la trouvent ; le gradient boosting est à 0,990 pour un seuil de 0,994.

Cause principale : `SEUIL` ; secondaire : `REPRISE`. Remède : un seuil moins extrême ou une combinaison avec la règle (a).

## EA_Sports_FC_9e0e6a4f_U01

France – Espagne va aux tirs au but après 4–4 ; en 33, la France mène 4–2 avec quatre tirs sur quatre et l'Espagne tire son 4e penalty, décisif. En 35, un nouveau match commence à 0–0 (03:57). L'étiquette est juste ; le premier professeur a noté la période unknown malgré le libellé « PÉNALTYS », contre la convention.

La capture 34 sans HUD coupe la comparaison 4–2 → 0–0 et la règle (a) ; GRU 0,03, gradient boosting 0,15.

Cause principale : `LECTURE_COUPEE` ; secondaires : `ERREUR_OBSERVATION`, `SIGNE_PROPRE_AU_JEU`, `REPRISE`. Remède : comparer au dernier score lisible, corriger la période par une trace et noter les pastilles des tirs au but.

## EA_Sports_FC_9e0e6a4f_U03

France – Espagne est recommencé à la 57e minute : 2–7 à 57:28 en 80, puis en 81 le menu de pause affiche « 0:55 France 0 - 0 Espagne ». L'étiquette et les observations sont justes, et la notation stable laisse calculer la remise à zéro (−2 et −7).

Le GRU (0,88), la règle (a) et la régression logistique la trouvent. Le gradient boosting reste à 0,30 (seuil 0,80) : la remise à zéro tombe sur une capture de pause, combinaison rare dans ses données.

Cause principale : `MENU_AMBIGU` ; secondaire : `REPRISE`. Remède : une variable de remise à zéro indépendante de la phase, ou une combinaison avec la règle (a).

## EA_Sports_FC_9e0e6a4f_U04

France – Espagne se termine sur un 11–1 : en 112, le bandeau « FIN MATCH » affiche « FRA 11 1 ESP », puis 113–114 l'écran « RÉSULTATS ». L'étiquette et l'observation sont parfaites (écran de résultat, vainqueur France).

Le GRU la trouve de justesse (0,654, trois graines) ainsi que la régression logistique. Le gradient boosting reste à 0,698 sous son seuil de 0,804, et les règles n'ont aucune condition sur l'écran de résultat : active → post_game ne compte pas pour la règle (c).

Cause principale : `SEUIL`. Remède : une règle « résultat affiché » et un seuil moins strict pour le gradient boosting.

## Synthèse du lot

26 fins d'EA Sports FC (dix-huit de la session `11029423`), toutes manquées par le gradient boosting ou par le GRU ; 13 sont manquées par les quatre détecteurs. Les 26 étiquettes sont justes. Deux placements se discutent (U15, U17) : la fin est posée sur la première capture du match suivant, alors que la sortie vers les écrans d'équipe avait lieu trois ou quatre captures plus tôt. Le choix se défend, parce que le même écran Équipe partagé existe en cours de match (session `378c621d`, capture 332).

Causes principales : `SEUIL` 10, `LECTURE_COUPEE` 8, `MENU_AMBIGU` 3, `CONTEXTE_SANS_VARIATION` 2, `ECRAN_NON_MARQUE` 1, `RETARD` 1, `AVANCE` 1. Causes secondaires les plus fréquentes : `REPRISE` (13), `CONTEXTE_SANS_VARIATION` (9), `MENU_AMBIGU` (8). Deux codes ajoutés : `RETARD`, une fin vue par les détecteurs mais deux captures ou plus après la preuve, au début de la partie suivante ; `AVANCE`, une fin annoncée avant la capture qui la prouve, au moment où le jeu part vers des menus ambigus.

### Les familles de causes

1. **Une capture sans tableau de score entre deux matchs** (8 cas principaux, 4 secondaires). Un fondu, un plan rapproché, un coup d'envoi sans HUD ou des écrans d'équipe se glissent entre le dernier score (4–2, 6–3, 4–5…) et le 0–0 du match suivant. La variation du score et la règle (a) comparent à la capture juste avant, donc rien ne se passe. Le gradient boosting monte parfois (0,42, 0,97) quand l'ancien score reste dans sa fenêtre de trois captures, sans passer le seuil. En comparant au dernier score lisible du même jeu, la règle (a) aurait trouvé six des treize fins manquées par les quatre (U03, U13, U16, U20, `7616a3a5` U09, `9e0e6a4f` U01). Deux autres (U15, U17) demandent un invariant plus large : un score qui baisse (0–3 → 0–1), pas seulement un retour exact à 0–0.
2. **La période unknown supprime toute variation du chrono.** Dans les 26 cas, la variation du chrono n'est jamais calculée, alors que le chrono d'EA FC ne fait que monter. Elle aurait donné trois signes nets : le recul vers 90:00 du menu d'après-match (U06 : 92:21 → 90:00 ; U08 : 91:07 → 90:00 ; U07 : 90:57 → 90:00), la relance en cours de match (79:59 → 0:00, 57:28 → 0:55, 84:17 → 00:52) et le nouveau match (78:42 → 04:46, 88:14 → 04:14). Pour U06 et U08, c'est le seul obstacle : les deux captures se suivent et les chronos sont lus. La période est même incohérente dans une partie : unknown en jeu, overtime dans le menu qui affiche « PR » (U12).
3. **La notation instable casse le « même contexte ».** Le même professeur écrit tour à tour « EA Sports FC » et « EA Sports FC 26 » (ou « FC 27 » sur les menus), « PSG/BAR » d'après le HUD et « Paris SG/FC Barcelone » d'après le menu. Dans U10 et U11, la remise à zéro (5–2 → 0–0, 5–4 → 0–0) disparaît des variables, alors que les règles, qui comparent la famille de jeu, la trouvent. Partout ailleurs, `game.title.changed` et `participants.primary.changed` se lèvent pour rien, ce qui apprend aux modèles à ne pas s'y fier.
4. **Des seuils presque à 1.** Dans les tours de `42dcc5f5`, `7616a3a5` et `378c621d`, le seuil du gradient boosting vaut 0,987 à 0,994 (0,988 pour le GRU dans `378c621d`). Des fins vues à 0,97–0,99 sont rejetées, dont `42dcc5f5` U02 avec un écran « VAINQUEUR — Joueur 2 » bien noté comme résultat (0,985 pour 0,987). Dans huit des dix cas `SEUIL`, un autre détecteur trouve déjà la fin.
5. **Les menus d'EA FC 26 se ressemblent.** La pause en cours de match, la pause du résumé d'après-match (U07, U08) et la pause d'avant-coup d'envoi ont le même menu. Seuls la valeur du chrono et quelques détails les distinguent : 0:00 avec « Options pour recommencer » actif et « Fin du match » grisé avant le coup d'envoi ; 90:00 pile avec un ralenti en fond après le coup de sifflet. Le vrai menu d'après-match (U06 : « Quitter le match » en tête, plus de « Reprendre », supporters qui sortent du stade) est un écran de fin que le professeur a noté comme une pause.

### Ce qui m'a surpris

- Trois cas ne sont pas des fins ignorées mais des fins vues au mauvais moment : U08 (les trois détecteurs à 0,88–0,96 deux captures après la preuve), U17 (le GRU à 0,667, au-dessus du seuil, trois captures avant), U15 (la règle (c) quatre captures avant). Pour compter les parties, ces trois fins sont bonnes ; seule la tolérance d'une capture les rejette.
- Les règles ont des angles morts simples : la pause n'est pas une phase de jeu pour la règle (c) (U12 : pause → choix des équipes), une capture de phase unknown ou sans titre entre le jeu et le chargement suffit à les aveugler (U21, `42dcc5f5` U03, U05), et aucune règle ne lit `result.visible` (`9e0e6a4f` U04 : écran « FIN MATCH » puis « RÉSULTATS »).
- EA FC affiche des signes de début ou de fin de match que le contrat ne capte pas : l'écran de départage d'un nul (« Classique / But en or / Tirs au but / Finir sur un match nul », noté comme un écran de console en U07), le face-à-face de l'aperçu de Coup d'envoi (« 1 victoire — 0 nul — 1 victoire », un compteur entre parties comme les « WINS » de Tekken), les pastilles des tirs au but, l'encart « COMMENTAIRES » et le bandeau de composition d'équipe de début de match, les panneaux « Tiempo añadido ».
- Le professeur fait peu d'erreurs de lecture : un écran de fin noté comme une pause (U06), une période unknown malgré « PÉNALTYS » (premier professeur, `9e0e6a4f` U01), des équipes écrites mais non notées sur un écran de choix (`7616a3a5` U08), l'écran de départage d'un nul pris pour un écran de console (U07). Les fins se perdent surtout dans le calcul des variables.

### Les méthodes qui reviennent

1. Calculer les variations contre la **dernière valeur lisible du même jeu** (score, chrono, phase, titre), et pas contre la capture juste avant ; appliquer la même chose aux règles (a), (c) et (d). C'est la mesure qui rapporte le plus dans ce lot.
2. Pour le football, **calculer la variation du chrono même quand la période est unknown** : un chrono de match qui recule dans le même jeu est une relance, un nouveau match ou le coup de sifflet final (recul vers 90:00 ou 120:00).
3. **Normaliser le titre (famille de jeu) et les noms d'équipe** avant de tester le « même contexte » et `participants.primary.changed`.
4. **Conventions EA FC à ajouter** : le menu sans « Reprendre » noté comme écran de résultat ; l'écran de départage d'un nul noté comme écran d'EA FC ; le face-à-face et les pastilles des tirs au but notés comme `secondary_counters` (`series`, `target`) ; les équipes écrites des écrans de choix toujours notées. Les lots déjà enregistrés se corrigent par des traces.
5. **Seuils et évaluation** : un seuil calibré par famille ou moins extrême ; une règle « résultat affiché » combinée aux modèles ; une tolérance qui accepte une annonce entre la sortie du jeu et la preuve (`AVANCE`) ou deux captures après la preuve quand celles du milieu sont des menus de la même partie (`RETARD`), à condition qu'il n'y ait qu'une annonce par partie.
