# Lot 4 — EA Sports FC (b) : analyse des fins manquées

## EA_Sports_FC_a80bda9c_U01

Real Madrid – Liverpool (FC 27, Match classique), 0–0 après prolongation puis tirs au but. Sur le HUD zoomé de la capture 45, le Real a tiré cinq fois (3 réussis, le 5e manqué) et Liverpool quatre fois (4 réussis) : la séance est jouée, Liverpool gagne 4–3, mais aucun écran de résultat n'est capturé. La capture 46 est une transition sans HUD, la 47 l'écran « Équipe » d'un nouveau match entre les mêmes équipes (0–0 à 01:42 en 48). L'étiquette est juste.

Le professeur a bien lu la séance (PÉNALTYS, période other) ; il a seulement mal décrit la scène de 45 (« joueur du Real célébrant ») et noté le titre « EA Sports FC 27 » sur l'écran d'équipe seulement, ce qui fabrique un changement de titre à 47 et à 48. Le gradient boosting trouve la fin (0,997). Le GRU monte à 0,72 pour un seuil de 0,778 (2 graines sur 5) : c'est un problème de seuil. Les règles échouent à cause de la transition 46 : la capture « précédente » de 47 n'est pas une phase de jeu, et le 0–0 de 48 suit un écran sans score. Comparer à la dernière capture lisible suffirait aux règles ; noter les tirs tentés de la séance permettrait de décider la fin dès 45.

## EA_Sports_FC_c93ed313_U02

Real Madrid – FC Barcelone en habillage LaLiga, 1–0 à 24:46 (capture 62), puis l'écran « Match classique — Choix des maillots » (63) et un nouveau 0–0 (66) : match quitté vers la 25e minute et relancé, compté comme une partie complète. L'étiquette est juste.

Le professeur a noté RMA et BAR comme participants alors que les captures 60 à 62 ne montrent que les écussons : un nom déduit d'un logo, sans effet ici. Seul le GRU manque la fin, de peu (0,488 pour un seuil de 0,538) ; le gradient boosting la trouve de justesse (0,982 contre 0,98) et les règles la trouvent par le passage active → pre_game. Le chrono qui repart de 24:46 à 02:56 n'aide personne : la période est unknown, donc sa variation n'est pas calculée, et une capture de menu sépare de toute façon les deux matchs.

## EA_Sports_FC_d8b709c4_U02

Brentford – Newcastle en carrière (habillage Premier League). Le HUD zoomé montre 0–1 à 16:31 (capture 214), puis 0–0 à 03:16 (215) 38 s plus tard : le match a été recommencé, sans menu capturé entre les deux. L'étiquette est juste et l'observation exacte.

Les variables ne voient qu'un but en moins : le recul du chrono de plus de 13 minutes n'est pas calculé parce que la période est unknown, comme presque toujours en EA FC. Un but de moins avec les mêmes équipes ressemble aussi à un but annulé, et le GRU reste à 0,024. Le gradient boosting monte à 0,959, sous un seuil de 0,982. La règle (a) (score total > 0 puis 0–0) la trouve. Une variation du chrono calculée pour le football même sans période connue aurait donné un signal net : −795 s.

## EA_Sports_FC_d8b709c4_U03

Brentford – Newcastle, deuxième tentative, 2–0. La capture 236 montre le bandeau « Remplacement » à 90:27 « +1′ », la 237 l'accueil de la carrière qui annonce le match de Ligue des champions suivant : le match est fini, l'écran de fin n'a pas été capturé. L'étiquette est juste. Le professeur a gardé « BRE » dans les participants de 236 alors que le bandeau le cache (détail sans effet).

Le gradient boosting (0,998) et la règle (c) (active → pre_game) trouvent la fin. Le GRU monte à 0,545 mais le seuil de ce tour est de 0,813 : cause de seuil. Le temps additionnel « +1′ » est lu dans la note mais n'est pas une variable ; un indicateur de chrono au-delà de 90 aiderait tous les modèles.

## EA_Sports_FC_d8b709c4_U04

Lombardia FC – Brentford en Ligue des champions (carrière). À 264, 1–2 à 90:00 avec le temps additionnel ; à 265, le menu d'après-match de la carrière affiche « 90:00 Lombardia FC 1-2 Brentford » avec « Interview d'après-match » et « Recommencer ce match ». C'est un écran de fin explicite et l'étiquette est juste.

Le professeur a noté la phase post_game mais pas le résultat (result.visible = false), et il a écrit les noms longs des équipes au lieu des sigles, ce qui fabrique un changement de participants. Le gradient boosting trouve la fin (0,998). Le GRU reste à 0,388 pour un seuil de 0,813. Les règles ne la voient pas : post_game compte pour elles comme une phase de jeu, et la sortie vers le menu (267) arrive deux captures trop tard. Marquer le résultat sur ce menu et faire de l'entrée en post_game un signal de fin dans les règles corrigerait ce cas.

## EA_Sports_FC_f0067594_U29

Finale de Ligue des champions Arsenal – Real Madrid. La capture 254 montre clairement le bandeau « FIN DU MATCH — ARSENAL 7 | 4 REAL MADRID » avec les buteurs ; suivent la célébration (255) et le trophée (256). L'étiquette est juste.

C'est une erreur de saisie du professeur : dans la lecture du lot, la capture 254 a reçu "parts": ["state.screen_type"] au lieu du bloc qui devait la marquer comme écran de résultat. L'observation enregistrée dit donc « jeu en cours », sans résultat, avec « state.screen_type » comme seul participant (cas unique dans PlayEnd). Pour les variables, 254 n'est qu'un but de plus (6–4 → 7–4) ; la célébration post_game de 255 fait monter le GRU à 0,376 et le gradient boosting à 0,479, loin des seuils. Les règles ne regardent pas l'entrée en post_game. Une trace de correction et un contrôle des participants dans build_lot régleraient ce cas.

## EA_Sports_FC_f0067594_U31

Deuxième finale Arsenal – Real Madrid : 4–4 à 90:00 (327), puis le menu « Finale UCL » figé à 90:00 avec « Reprendre », « Recommencer ce match » et « Fin du match » (328), puis le choix des équipes d'un autre match (329). Un nul en finale aurait dû mener à la prolongation : le joueur a quitté au coup de sifflet, ce qui compte comme une partie complète. L'étiquette est juste ; la preuve stricte est 329, mais la fin placée sur 328 reste dans la tolérance d'une capture.

Le professeur a noté 328 en post_game sans résultat, ce qui est raisonnable pour un nul qui n'est pas terminé ; il a par contre écrit les noms longs de l'encart, ce qui fabrique un changement de participants. Le gradient boosting monte à 0,776 (seuil 0,884), le GRU à 0,33. Les règles trouvent la fin par le passage post_game → pre_game de 329. Le menu figé à 90:00 est ambigu tant qu'on ne sait pas si le score est décisif.

## EA_Sports_FC_f0067594_U32

Finale Manchester City – Real Madrid, 2–5 à 90:00 (361). La capture 362 est un plan sans HUD : joueurs du Real qui marchent, un joueur de City abattu, des photographes sur la pelouse. C'est l'après-match, suivi de la cérémonie du trophée (363–365) puis de l'écran « RÉSULTATS » 2–5 (366). L'étiquette est juste et l'observation exacte (cinématique post_game).

Le seul indice à 362 est le passage du jeu actif à une cinématique post_game, qui ressemble aux célébrations de but. Le gradient boosting monte à 0,628 (seuil 0,884), le GRU à 0,141. L'écran RÉSULTATS arrive quatre captures trop tard pour la tolérance, et les modèles ont appris à se taire à cet endroit (0,011 et 0,004). Les règles ne regardent pas l'entrée en post_game. Ce cas est propre aux finales UCL d'EA FC, dont la cérémonie dure environ deux minutes.

## EA_Sports_FC_f8c2843d_U02

Égypte – Sénégal : 4–6 à 90:58 avec deux minutes de temps additionnel (57), puis le menu « Match classique — Choix des équipes » d'un autre match (58). L'étiquette est juste ; l'écran de fin n'a pas été capturé.

Le professeur a lu la capture 56 comme un écran noir alors que c'est l'écran « Équipe » du match en cours (remplacements) ; cette erreur revient sur 12 captures de la session, toutes des écrans d'équipe. Ici elle casse le contexte entre 55 et 57 et appauvrit la fenêtre du gradient boosting (0,322 pour un seuil de 0,758). Le GRU monte à 0,622 pour un seuil de 0,77. La règle (c) trouve la fin (active → pre_game).

## EA_Sports_FC_f8c2843d_U03

Lens – Montpellier : 5–3 à 91:20 (90), un bandeau de but « 90′ » (91), puis à 92 l'écran « RÉSULTATS — Match classique, VAINQUEUR Joueur 1 » sur un fond sombre, enfin l'écran « Équipe » du match suivant (93). La fin est vraie, mais la première capture qui la prouve est 92 et non 93 : l'étiquette est douteuse d'une capture.

Le professeur a lu cet écran de résultat comme un « écran noir ». L'erreur est fréquente dans cette session : 15 des 29 captures notées noires ne le sont pas (écrans d'équipe, transitions « Prêt(e) ! », ce résultat, un menu de format de fin). Sans le résultat, le GRU monte à 0,753 pour un seuil de 0,77 et le gradient boosting passe de justesse (0,765 contre 0,758). La règle (c) échoue parce que la capture juste avant le menu est cette fausse capture noire, en phase unknown. Un contrôle de luminosité sur les captures notées « noir », puis une trace de correction, retrouveraient l'écran de résultat.

## EA_Sports_FC_f8c2843d_U05

Bayern – Arsenal, 8–3 à 91:58 (165), un fondu au noir (166), puis le menu d'après-match « Match classique » avec l'encart « 90:00 FC Bayern München 8-3 Arsenal » et les statistiques finales (167). L'étiquette est juste.

Le professeur a noté la phase post_game mais pas le résultat, et il a écrit les noms longs des équipes. Le GRU trouve la fin (0,845, 5 graines sur 5) grâce à sa mémoire du match. Le gradient boosting la manque (0,33 pour 0,758) : sa fenêtre de trois captures contient la capture noire, qui efface toutes les variations, et un menu sans résultat qui ressemble à une pause. Les règles la trouvent à 168. Marquer le résultat sur ce menu et donner au gradient boosting les dernières valeurs lisibles corrigeraient ce cas.

## EA_Sports_FC_f8c2843d_U06

Real Madrid – Paris SG se termine aux tirs au but : 4–3 à la capture 203, le 5e tireur du Real au point de penalty, puis un tir filmé de loin (204) et le choix des équipes d'un autre match (205). L'étiquette est juste. Le GRU (0,925) et la règle (c) trouvent la fin ; le gradient boosting la manque d'un centième (0,748 pour 0,758). Hors de la preuve, le menu de format en cas d'égalité (200) est noté « écran noir », une erreur de plus de cette session.

## EA_Sports_FC_f8c2843d_U07

Côte d'Ivoire – Japon : 8–5 à 88:06, un but confirmé (239), puis le menu d'après-match « 90:00 Côte d'Ivoire 9-5 Japon » (240) et le choix des équipes d'un autre match (241). L'étiquette est juste. Comme pour U05, le professeur note post_game sans résultat et écrit les noms longs. Le GRU monte à 0,72 pour un seuil de 0,77, le gradient boosting à 0,283, gêné par la capture de célébration sans score ; la règle (c) trouve la fin à 241.

## EA_Sports_FC_f8c2843d_U27

Paris SG – Monaco : 0–4 à 90:00 dans le temps additionnel (746), puis le menu d'après-match « 90:00 Paris SG 0-4 AS Monaco » (747). L'étiquette est juste. Le professeur a noté ce menu comme un menu d'avant-match, sans score ni résultat. Le GRU (0,741 pour 0,77) et le gradient boosting (0,717 pour 0,758) passent tout près du seuil ; la règle (c) trouve la fin, aidée justement par la phase pre_game notée à tort.

## EA_Sports_FC_f8c2843d_U28

Real Madrid – Villarreal : 2–6 à 90:28 (777), puis le choix des maillots d'un nouveau match contre le Rayo Vallecano (778). L'étiquette est juste et la preuve bien lue. Le gradient boosting (0,931) et la règle (c) trouvent la fin ; le GRU reste à 0,734 pour un seuil de 0,77. Les participants de 775 et 780 sont déduits des écussons, sans effet ici.

## EA_Sports_FC_f8c2843d_U30

Finale Barcelone – Real Madrid : 11–4 à 90:00 (850), puis 0–0 à 01:49 entre les mêmes équipes (851). L'étiquette est juste. Le GRU (0,999) et la règle (a) trouvent la fin. Le gradient boosting la manque de peu (0,731 pour 0,758) malgré deux baisses de score dans sa fenêtre. Le recul du chrono de 88 minutes, qui la rendrait évidente, n'est pas calculé faute de période connue.

## EA_Sports_FC_f8c2843d_U31

Deuxième finale Barcelone – Real Madrid : 7–2 à 90:00 (889), les paramètres réseau de la PS5 ouverts par-dessus le jeu (890), puis le menu « Finale UCL » figé à 90:00 avec l'encart 7–2 (891). L'étiquette est juste. Le GRU annonce bien la fin, mais sur le menu PS5 de 890 (0,895 pour un seuil de 0,77), une capture avant la preuve : l'évaluation compte alors une fausse fin et une fin manquée. Je propose un code nouveau, ANNONCE_PRECOCE, pour ce cas. Le menu d'après-match 891, noté sans résultat, ne déclenche rien ; les règles trouvent la fin à 892.

## EA_Sports_FC_f8c2843d_U34

Finale Manchester City – Paris SG : 9–6 à 90:00 en fin de temps additionnel (1003), puis le choix des maillots d'un match Liverpool – Barcelone (1004). L'étiquette est juste. Le GRU (0,847) et la règle (c) trouvent la fin ; le gradient boosting la manque de peu (0,733 pour 0,758). Le bandeau de but noté en noms longs à 1002 fabrique un changement de participants sur la dernière capture du match.

## EA_Sports_FC_f8c2843d_U35

Finale Liverpool – Barcelone : menu pause à 88:03 avec 7–4 (1049), paramètres de la manette (1050), puis le choix des équipes d'un autre match (1051). Le match a été quitté à la 88e, ce qui compte comme une partie complète ; l'étiquette est juste et l'observation exacte. Aucun détecteur ne la voit : la sortie du match est étalée sur trois captures de menus, la fenêtre du gradient boosting ne contient plus de jeu actif, et la règle (c) ne compte pas la pause comme une phase de jeu. Une règle qui remonte à la dernière phase de jeu connue en traversant les menus la trouverait.

## EA_Sports_FC_f8c2843d_U36

Finale Atlético – Bayern : 9–3 à 71:53 (1087), menu pause (1088), puis l'écran « Coup d'envoi » d'un match Athletic Club – Barcelone (1089). Le match a été quitté à la 72e ; l'étiquette est juste. Le GRU trouve la fin grâce à sa mémoire (0,894) ; le gradient boosting (0,243) et les règles la manquent, parce que la pause n'est pas une phase de jeu pour la règle (c) et que la fenêtre ne montre ni résultat ni chrono à 90. L'écran de coup d'envoi affiche un compteur « Face-à-face général » (4 / 0 / 3) qui n'est noté que dans la note.

## EA_Sports_FC_f8c2843d_U37

Finale Athletic Club – Barcelone quittée vers la 10e minute : 0–2 à 10:06 (1102), puis à 1103 la boîte « Voulez-vous quitter ? — Oui, quitter » sur un gros plan du filet, les paramètres de la manette (1104) et la présentation d'un match Paris SG – Barcelone (1105). L'étiquette est juste. Le professeur a noté 1103 comme une capture de jeu avec un « message à l'écran », sans le texte du dialogue. Le changement d'adversaire et le retour à 0–0 ne sont jamais calculés, parce que le menu de 1104 rompt le contexte et n'a ni score ni participants. Seule la règle (c) réagit, sur 1104, une capture trop tôt pour l'évaluation.

## EA_Sports_FC_f8c2843d_U39

Finale Atlético – Barcelone : 2–5 à 90:00 (1167), puis le bandeau « FIN DU MATCH — ATLÉTICO DE MADRID 2 5 FC BARCELONE » (1168). L'étiquette est juste. C'est le seul cas du lot où le professeur a marqué l'écran de fin comme résultat. Le gradient boosting trouve la fin (0,962), mais le GRU reste à 0,56 pour un seuil de 0,77. Aucune règle ne regarde le résultat visible : une règle « résultat visible » trouverait ce cas.

## EA_Sports_FC_fdb79549_U05

Barcelone – Paris SG : 2–1 à 87:01 (86), puis le bandeau de coup d'envoi « BAR 0 0 PSG » d'un nouveau match entre les mêmes équipes (87). L'étiquette est juste et l'observation exacte. La règle (a) trouve la fin. Le gradient boosting monte à 0,956 pour un seuil de 0,981 et le GRU reste à 0,265 : une revanche sans menu ni écran de fin, avec les mêmes noms, est le cas que le GRU apprend le moins bien.

## EA_Sports_FC_fdb79549_U08

Barcelone – Paris SG : 0–2 à 91:20 (162), puis 1–0 à 04:55 (163) : un nouveau match entre les mêmes équipes a commencé et compte déjà un but. L'étiquette est juste et l'observation exacte. La règle (a) ne voit pas de 0–0 et le GRU reste à 0,014. Le gradient boosting monte à 0,961 pour un seuil de 0,981. Le signal évident, le chrono qui repart de 91:20 à 04:55, n'est pas calculé parce que la période est unknown : c'est le cas le plus net du lot de ce que coûte cette règle de calcul.

## EA_Sports_FC_fdb79549_U09

Barcelone – Paris SG reste dix captures sur le menu pause à 44:36 (3–1), puis la PS5 est mise hors tension (184) : le match est abandonné à la mi-temps et compte comme une partie complète. L'étiquette est juste et l'observation exacte. Aucun détecteur ne réagit : la pause n'est pas une phase de jeu pour les règles, et l'écran de mise hors tension, sans titre de jeu, ressemble aux variables d'une capture illisible. Un état « écran système » dans le contrat et une règle « pause puis arrêt de la console » trouveraient cette fin.

## Synthèse du lot

25 fins d'EA Sports FC, toutes regardées sur leur planche et, quand un détail comptait, sur l'image originale. 24 étiquettes sont justes ; une est douteuse d'une capture (f8c2843d U03 : l'écran « RÉSULTATS — VAINQUEUR Joueur 1 » de la capture 92 prouvait la fin avant le menu de 93). Le GRU trouve 5 de ces fins, le gradient boosting 7, les règles 14. Aucun détecteur n'en trouve 6 : f0067594 U29 et U32, f8c2843d U35 et U37, fdb79549 U08 et U09.

Causes principales : SEUIL 9, ECRAN_NON_MARQUE 6, MENU_AMBIGU 3, REPRISE 2, et une fois chacune SIGNE_PROPRE_AU_JEU, CONTEXTE_SANS_VARIATION, FIN_ENTRE_CAPTURES, ABANDON et ANNONCE_PRECOCE (code nouveau, défini plus bas).

### Les familles de causes

- **Le menu d'après-match d'EA FC n'est pas marqué comme résultat.** Après le coup de sifflet, EA FC affiche un menu figé sur le temps réglementaire, avec l'encart « 90:00 Équipe A x-y Équipe B » (Quitter le match ou Reprendre match, Options pour recommencer, Détails du match, Performance, Highlighter). Le professeur le note post_game sans résultat (d8b709c4 U04, f8c2843d U05, U07, U31), ou même comme un menu d'avant-match sans score (f8c2843d U27). Il écrit aussi les noms longs de l'encart au lieu des sigles du HUD, ce qui fabrique un changement de participants. Le seul cas où le résultat est marqué (f8c2843d U39, bandeau « FIN DU MATCH ») est trouvé par le gradient boosting.
- **Des écrans de fin perdus par erreur de lecture.** En f0067594 U29, la lecture du lot a reçu `"parts": ["state.screen_type"]` à la place du bloc qui marquait l'écran de résultat : la capture « FIN DU MATCH ARSENAL 7 | 4 REAL MADRID » est notée « jeu en cours » et a pour seul participant la chaîne « state.screen_type ». C'est un cas unique dans PlayEnd, vérifié sur toutes les sessions. En f8c2843d, 15 des 29 captures notées « écran noir » ne le sont pas : des écrans d'équipe, des transitions « Prêt(e) ! », le menu de format en cas d'égalité et l'écran « RÉSULTATS » de U03. En f8c2843d U37, une boîte « Voulez-vous quitter ? — Oui, quitter » est notée « message à l'écran » sur une capture de jeu.
- **Les seuils.** Neuf fins sont manquées de peu par le modèle qui les rate : le GRU entre 0,72 et 0,75 pour des seuils de 0,77 à 0,78, et une fois à 0,488 pour 0,538 ; le gradient boosting entre 0,73 et 0,96 pour des seuils de 0,758 à 0,982. Dans la plupart de ces cas, l'autre modèle ou la règle (c) trouve la fin. Les seuils changent beaucoup d'un tour à l'autre (GRU de 0,487 à 0,813).
- **Les revanches et les recommencements entre les mêmes équipes** (d8b709c4 U02, f8c2843d U30, fdb79549 U05 et U08). Le score revient à 0–0, ou repart à 1–0, sans menu entre les deux.
- **Les sorties de match étalées sur plusieurs menus** (f8c2843d U35 et U36, fdb79549 U09) : une pause, puis des réglages, puis un choix des équipes ou l'arrêt de la console. La règle (c) ne compte pas la pause comme une phase de jeu. La fenêtre de trois captures du gradient boosting ne contient alors plus aucune capture de jeu.

### Ce que coûte la période `unknown`

Le professeur note la période `unknown` sur toutes les captures de jeu d'EA FC du lot (633 captures de jeu sur 636 en f8c2843d, toutes en d8b709c4 et fdb79549). La convention le veut, puisque le HUD n'affiche pas la mi-temps. Mais `clock.value_seconds.delta_candidate` exige une période connue : le chrono qui repart à zéro n'est donc jamais une variable. C'est le signal le plus net d'un recommencement, et il est perdu dans quatre cas : 16:31 → 03:16 (d8b709c4 U02), 90:00 → 01:49 (f8c2843d U30), 87:01 puis 06:15 (fdb79549 U05) et surtout 91:20 → 04:55 (fdb79549 U08). Dans ce dernier, le score passe de 0–2 à 1–0 sans retour à 0–0 : le chrono était le seul indice, et aucun détecteur ne trouve la fin. Le chrono figé à 90:00 sur un menu, ou au-delà de 90 avec « +n », n'est pas non plus encodé ; sur les menus d'après-match, il dit pourtant que le match est fini dès que le score n'est pas nul.

### Ce qui m'a surpris

- Le GRU a bien vu la fin de f8c2843d U31, mais une capture trop tôt : 0,895 sur le menu réseau de la PS5 qui précède le menu d'après-match. L'évaluation n'accepte qu'une annonce sur la capture de preuve ou sur la suivante. Elle compte donc une fausse fin et une fin manquée, alors que la facturation serait juste. Les règles font la même chose en f8c2843d U37. Je propose le code **ANNONCE_PRECOCE** : le détecteur annonce la fin sur une capture intermédiaire, entre la dernière capture de la partie et la capture qui prouve la fin, et l'évaluation le compte comme une fausse fin plus une fin manquée.
- Même avec le résultat bien marqué (f8c2843d U39), le GRU reste à 0,56. Dans les finales UCL (f0067594 U32), l'écran « RÉSULTATS » arrive quatre captures après la première cinématique d'après-match ; les modèles ont appris à se taire à cet endroit (0,011 et 0,004).
- Les noms d'équipes changent de forme d'une capture à l'autre (sigles du HUD, noms longs des bandeaux et des encarts, noms déduits des écussons). participants.primary.changed vaut donc 1 sans changement d'affiche, souvent sur la dernière capture d'un match, et reste inconnu quand l'adversaire change vraiment derrière un menu (f8c2843d U37).
- Dans les sessions FC 27 (a80bda9c, c93ed313), le titre vaut « EA Sports FC » en jeu et « EA Sports FC 27 » dans les menus : game.title.changed passe à 1 à chaque entrée dans un menu.

### Les méthodes qui reviennent

1. **Convention et traces de correction** : marquer comme résultat visible le menu d'après-match à encart « 90:00 A x-y B » quand le score n'est pas nul, ainsi que tout bandeau « FIN DU MATCH ». Corriger f0067594 U29 et les captures de f8c2843d notées noires à tort (contrôle automatique : luminosité moyenne au-dessus d'environ 10 sur une capture notée « noir »). Noter les boîtes « Voulez-vous quitter ? » comme des pauses, avec leur texte. Garder une seule forme des noms (le sigle du HUD) et un seul titre de jeu par session. Ajouter dans build_lot un contrôle qui refuse un participant égal à un nom de champ du contrat.
2. **Variables** : calculer la variation du chrono pour un chrono de match croissant même quand la période est unknown, si le titre, le mode et les participants sont les mêmes ; ajouter les indicateurs « chrono ≥ 90:00 ou temps additionnel affiché », « score revenu à 0–0 après un score non nul » et « captures depuis la dernière capture de jeu actif ». Comparer score et participants à la dernière valeur lisible, pas à la capture juste avant.
3. **Règles** : annoncer une fin quand le résultat devient visible ou quand la phase passe à post_game ; compter paused comme une phase de jeu, ou remonter à la dernière phase de jeu connue en traversant les menus ; ajouter « chrono qui recule de plus de 5 minutes » et « un score qui baisse ». Les règles trouvent déjà 14 des 25 fins : les associer aux modèles en récupérerait beaucoup.
4. **Évaluation et seuils** : accepter une annonce sur les captures intermédiaires entre la fin du jeu et la preuve ; regarder des seuils moins stricts ou fixés par famille de jeux, puisque neuf fins sont manquées de peu.
5. **Contrat** (à discuter, sans décision ici) : un état « écran système » (accueil, réglages, mise hors tension de la PS5) distinct d'une capture illisible ; les tirs tentés pendant une séance de tirs au but ; peut-être le compteur « Face-à-face général » des écrans de coup d'envoi, à vérifier sur d'autres sessions.
