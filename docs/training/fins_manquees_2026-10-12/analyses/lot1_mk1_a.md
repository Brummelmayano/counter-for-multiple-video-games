# Lot lot1_mk1_a : fins manquées de Mortal Kombat 1 (cas par cas)

## Mortal_Kombat_1_11029423_U22

Revanche entre les mêmes combattants (Ghostface contre Johnny Cage). En 650, Johnny Cage mène 0–1 au 2e round (44 s) ; en 651, bannière « FIGHT », chrono à 90, vies pleines et emplacements éteints : un nouveau match commence. L'étiquette est juste et l'observation n'a rien d'erroné. La seule variation produite est la baisse du score de B (−0,693) : le chrono qui remonte de 44 à 90 n'est pas calculé, faute de période connue. Le gradient boosting (0,89, seuil 0,713) et la règle (a) la trouvent ; le GRU monte à 0,35 sous son seuil de 0,57. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_11029423_U23

Même revanche Ghostface contre Johnny Cage. Le marqueur de Johnny Cage, allumé au 2e round (654 « ROUND 2 », 655 à 52 s), a disparu en 656 alors que le chrono est remonté à 67 : un nouveau match a commencé entre les deux captures (44 s d'écart). Étiquette juste, observation correcte. La variation du score de B (−0,693) est la seule produite ; le gradient boosting (0,873) et la règle (a) trouvent la fin, le GRU reste à 0,42 pour un seuil de 0,57. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `FIN_ENTRE_CAPTURES`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_11029423_U24

Troisième match de suite entre Ghostface et Johnny Cage. Johnny Cage mène 0–1 au 2e round (660, 71 s) ; 31 s plus tard (661), les marqueurs sont à 0–0 avec un chrono remonté à 79 et des vies presque pleines : le match a été recommencé, sans doute par la pause (trop peu de temps pour finir le round, voir la victoire et relancer). Étiquette juste, observation correcte. Gradient boosting à 0,746 (seuil 0,713, trouvée de justesse), règle (a) trouvée, GRU à 0,39. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `FIN_ENTRE_CAPTURES`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_11029423_U25

Manche décisive à 1–1 en 667 (Ghostface presque KO), écran noir en 668, puis 0–0 en 669 avec les mêmes combattants : nouveau match. Étiquette juste, observation correcte. La capture noire coupe toutes les variations : sur 669, ni variation de score ni comparaison des participants. Le gradient boosting, qui voit 667 dans sa fenêtre, trouve la fin (0,928) ; la règle (a) la manque parce qu'elle compare au noir ; le GRU monte à 0,44 sur le noir et 0,39 sur 669, sous 0,57. Cause principale : `REPRISE` ; secondaires : `LECTURE_COUPEE`, `SEUIL`, `FIN_ENTRE_CAPTURES`.

## Mortal_Kombat_1_11029423_U26

Johnny Cage mène 0–1 au 2e round (670 à 85, 672 à 50) ; en 673, emplacements à 0–0 et chrono remonté à 69 : nouveau match, confirmé par 674 (0–1 à 71, 1re manche du nouveau match). Étiquette juste, observation correcte. Seule la baisse du score de B est produite. Gradient boosting (0,91) et règle (a) la trouvent, le GRU reste à 0,37. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `FIN_ENTRE_CAPTURES`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_11029423_U27

Match éclair : 673 à 0–0, 674 à 0–1 (2e round), puis 675 en position de départ, chrono 87, vies pleines et 0–0 : nouveau match. Étiquette juste, observation correcte. Le gradient boosting manque la fin de peu (0,688 pour 0,713) : sa fenêtre voit 0–0, 0–1, 0–0, qui ressemble à un marqueur mal lu sur une seule capture. Le GRU reste à 0,24 ; la règle (a) la trouve. Les vies pleines, la preuve la plus claire à l'écran, ne sont pas dans le contrat. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_11029423_U28

Manche décisive à 1–1 en 680 (chrono 89), puis bannière « ROUND 1 » sans HUD en 681, mêmes combattants avec leurs Kaméos : nouveau match, confirmé par 682 (0–0 à 73). Étiquette juste, observation conforme. La capture de bannière n'a ni score ni noms : elle coupe la comparaison 1–1 → 0–0 pour les règles et pour les variations ; seul le gradient boosting la rattrape sur 682 (0,724 pour 0,713). Le GRU reste à 0,30. Une règle « ROUND 1 = nouveau match » propre à Mortal Kombat 1 la trouverait sur 681. Cause principale : `REPRISE` ; secondaires : `LECTURE_COUPEE`, `SIGNE_PROPRE_AU_JEU`, `SEUIL`.

## Mortal_Kombat_1_11029423_U29

Match très court : 0–0 en 682–683, 0–1 au 2e round en 684 (chrono 66), puis 685 à 0–0, chrono 81, Johnny Cage revenu à 1000/1000 : nouveau match. Étiquette juste, observation correcte. Le gradient boosting la manque (0,662 pour 0,713) : sa fenêtre voit 0–0, 0–1, 0–0, motif d'un marqueur mal lu ; il trouve en revanche les revanches où le marqueur était visible sur deux captures. Le GRU reste à 0,26, la règle (a) la trouve. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `FIN_ENTRE_CAPTURES`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_11029423_U30

Johnny Cage mène 0–1 au 2e round et Ghostface est presque KO (687, 135/1000) ; en 688, 0–0, chrono 89, Ghostface à 1000/1000 et bandeau « PREMIER COUP » : nouveau match. Étiquette juste, observation correcte. Gradient boosting à 0,723 (seuil 0,713, trouvée de justesse), règle (a) trouvée, GRU à 0,36. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_11029423_U31

Combat à 0–1 (693), puis quatre captures de manette déconnectée (dialogue du jeu, puis fenêtre « Qui utilise cette manette ? » de la PS5), puis l'accueil de la PS5 (698) et le lancement de Genshin Impact : match abandonné, étiquette juste. Les captures 693–694 ont été regardées à mi-résolution, les dialogues sont lisibles sur la planche. Le GRU passe tout près (0,539 pour 0,57, 2 graines sur 5) ; le gradient boosting reste à 0,04. Les règles échouent pour une raison de calcul : la pause n'est pas « en jeu » pour la règle (c), et l'accueil sans titre empêche la règle (d) de voir le passage de Mortal Kombat 1 à Genshin Impact. Cause principale : `ABANDON` ; secondaires : `MENU_AMBIGU`, `SEUIL`, `LECTURE_COUPEE`.

## Mortal_Kombat_1_8e58b139_U02

Li Mei mène 1–0 au 2e round (36–37), écran noir (38), puis 0–0 au chrono 60 avec les mêmes combattants (39) : match recommencé, confirmé par « SCORPION GAGNE » en 40. Étiquette juste ; le texte de preuve se trompe en parlant de vies pleines (164,64/950 et 428,01/1000), mais les marqueurs, vérifiés au zoom, suffisent. Même schéma que `11029423` U25 : la capture noire coupe toutes les variations, la règle (a) la manque, le gradient boosting (0,885) la trouve grâce à sa fenêtre, le GRU reste à 0,44 pour un seuil de 0,696. Cause principale : `REPRISE` ; secondaires : `LECTURE_COUPEE`, `SEUIL`.

## Mortal_Kombat_1_8e58b139_U09

Raiden gagne 2–0 contre Scorpion : sur 99, le deuxième marqueur s'allume et la vie de Scorpion est à 0,00. Le match suivant commence sur 100 (0–0 à 87, mêmes combattants). La fin est vraie, mais elle est posée sur 100 alors que 99 la prouve déjà, d'où l'étiquette `douteuse`. Surtout, l'étiquetage de ce signe n'est pas cohérent d'une session à l'autre : dans `f0067594`, cinq fins sont posées sur la capture à 2 manches elle-même, ailleurs sur la capture suivante. Les deux modèles montent près de leur seuil sur 100 (GRU 0,625 pour 0,696, une graine sur 5 ; gradient boosting 0,633 pour 0,678), et la règle (a) la trouve. Cause principale : `SEUIL` ; secondaires : `ETIQUETTE_DOUTEUSE`, `REPRISE`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_f0067594_U01

Premier match de l'enregistrement : manche décisive à 1–1 (captures 1–2), puis 0–0 à 83 avec des vies presque pleines et les mêmes combattants (3). Étiquette juste, observation correcte. Les deux scores baissent ensemble ; le gradient boosting (0,992) et la règle (a) trouvent la fin, le GRU reste à 0,39 pour un seuil de 0,555. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `FIN_ENTRE_CAPTURES`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_f0067594_U04

Reptile mène 0–1 au 2e round (24, chrono 19) ; en 25, position de départ, chrono 90, vies pleines et 0–0 : nouveau match, étiquette juste. Seule la baisse du score de B est produite. Le gradient boosting la manque de peu (0,834 pour un seuil de 0,884), le GRU reste à 0,30, la règle (a) la trouve. Petite erreur sans effet : le chrono à moitié caché de 23 est lu « 9 » au lieu de null. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_f0067594_U06

Johnny Cage mène 1–0 au 2e round (37–39) ; « FIGHT » à 90 en 40, puis 0–0 à 75 en 41 : nouveau match, étiquette juste. L'observation de 40 note 0–0 alors que les emplacements ne sont pas encore dessinés : la valeur est juste mais déduite, et c'est elle qui permet à la règle (a) de trouver la fin. Le gradient boosting tombe à 0,068 alors qu'il dépasse 0,83 sur les chutes du côté B : il semble avoir appris le côté, parce que les revanches de l'entraînement font presque toutes retomber le score de B. Nouveau code `SESSION_DOMINANTE` : `f0067594` contient 58 des 77 parties de Mortal Kombat 1 (33 des 43 revanches) ; tenu à l'écart, il en laisse très peu à l'entraînement. Cause principale : `REPRISE`.

## Mortal_Kombat_1_f0067594_U07

Reptile mène 0–1 au 2e round (44–45) ; en 46, 0–0 au chrono 83 avec les mêmes combattants : nouveau match, étiquette juste, observation correcte. Le gradient boosting la trouve nettement (0,974) : la chute porte sur le score de B, comme dans les revanches de l'entraînement. Le GRU reste à 0,37, la règle (a) la trouve. Cause principale : `REPRISE`.

## Mortal_Kombat_1_f0067594_U08

Johnny Cage mène 1–0 au 2e round (48–49) ; en 50, « FIGHT » à 90, vies pleines et 0–0 : nouveau match, étiquette juste, observation correcte. Le gradient boosting reste à 0,353 : c'est encore une chute du score de A, que ses variables, propres à chaque côté, voient rarement dans les revanches de l'entraînement. Le GRU est à 0,32 ; la règle (a) la trouve. Cause principale : `REPRISE` ; secondaires : `SESSION_DOMINANTE`, `SEUIL`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_f0067594_U09

En 58, au ralenti du KO, les deux marqueurs de Reptile sont allumés et Johnny Cage est à 0,00 : la fin y est posée, comme l'a décidé la validation humaine pour cette session. Le GRU ne voit rien sur 58 et monte à 0,522 sur 59 (seuil 0,555, 2 graines sur 5) ; le gradient boosting et la règle (a) la trouvent sur 59, avec le retard toléré. Le signe « objectif de manches atteint » n'est pas exploité, et il est étiqueté différemment dans `8e58b139`. À noter dans ce match : la capture 52 (« FIGHT » à 90 et 0–0 juste après 0–0 à 73) est masquée comme incertaine, sans doute un recommencement rapide. Cause principale : `SEUIL` ; secondaires : `SIGNE_PROPRE_AU_JEU`, `REPRISE`, `SESSION_DOMINANTE`.

## Mortal_Kombat_1_f0067594_U10

Johnny Cage mène 1–0 (61), menu de pause (62), puis 0–0 au chrono 74 (63) : match recommencé depuis la pause, étiquette juste. La capture de pause, notée sans score, sans mode et sans participants alors que les deux noms y sont écrits, coupe toutes les comparaisons : les quatre détecteurs la manquent. Une règle (a) calculée contre la dernière capture lisible la trouverait sur 63. Cause principale : `REPRISE` ; secondaires : `LECTURE_COUPEE`, `MENU_AMBIGU`, `SESSION_DOMINANTE`.

## Mortal_Kombat_1_f0067594_U11

Reptile mène 0–1 au 2e round, puis, 13 s après une attaque cinématique à 12 s du terme (69), une manche neuve commence sans aucun marqueur (70, vies pleines, « PREMIER COUP ») : match recommencé, étiquette juste, vérifiée au zoom. Le gradient boosting monte à 0,823 sous son seuil de 0,884, le GRU reste à 0,27, la règle (a) la trouve. Cause principale : `REPRISE` ; secondaires : `SEUIL`, `SESSION_DOMINANTE`, `CONTEXTE_SANS_VARIATION`.

## Mortal_Kombat_1_f0067594_U12

Reptile mène 0–1 et Johnny Cage est à 0,10 de vie (76) ; 22 s plus tard, 0–0 au chrono 81 avec Reptile à pleine vie (77) : nouveau match, sans doute recommencé au moment de perdre. Étiquette juste, observation correcte. Gradient boosting (0,909) et règle (a) la trouvent, le GRU reste à 0,37. Cause principale : `REPRISE`.

## Mortal_Kombat_1_f0067594_U13

Manche décisive à 1–1 (83–84), cinématique sans HUD (85), puis manche neuve à 0–0 avec vies pleines (86) : nouveau match, étiquette juste. La cinématique, sans score ni noms, coupe la comparaison : les quatre détecteurs la manquent, alors que la même double chute sans coupure (U01) est trouvée à 0,992 par le gradient boosting. Comparer à la dernière capture lisible suffirait. Cause principale : `REPRISE` ; secondaires : `LECTURE_COUPEE`, `SESSION_DOMINANTE`.

## Mortal_Kombat_1_f0067594_U14

Même schéma que U13 : manche décisive à 1–1 (92–93), une capture d'effet sans HUD (94), puis 0–0 au chrono 57 (95) avec les mêmes combattants. Étiquette juste, observation correcte. La capture sans score coupe la règle (a) et les variations ; le gradient boosting monte à 0,761 sous son seuil de 0,884, le GRU reste à 0,23. Cause principale : `REPRISE` ; secondaires : `LECTURE_COUPEE`, `SEUIL`, `FIN_ENTRE_CAPTURES`, `SESSION_DOMINANTE`.

## Mortal_Kombat_1_f0067594_U15

Manche décisive à 1–1 (98–99), attaque cinématique où le côté de Reptile est caché (100), puis manche neuve à 0–0 avec vies pleines (101) : nouveau match, étiquette juste. Le score de 100 est noté null en entier alors que le marqueur de Johnny Cage se lit : la comparaison est perdue, la règle (a) la manque et le gradient boosting tombe à 0,013. Comparer à la dernière capture lisible la trouverait. Cause principale : `REPRISE` ; secondaires : `LECTURE_COUPEE`, `SESSION_DOMINANTE`.

## Mortal_Kombat_1_f0067594_U16

Johnny Cage mène 1–0 contre Reptile (104–105), pause (106), puis écran de choix des Kaméos contre Sub-Zero (107) et « FIGHT » contre Sub-Zero (108) : match quitté par la pause, étiquette juste. Les textes étaient lisibles sur la planche. La pause intermédiaire empêche la règle (c) de voir le passage du jeu à la préparation, et les noms écrits sur l'écran de sélection ne sont pas notés, ce qui retire le changement d'adversaire. Le GRU monte à 0,44 (1 graine sur 5), le gradient boosting à 0,58. Cause principale : `ABANDON` ; secondaires : `MENU_AMBIGU`, `LECTURE_COUPEE`, `SEUIL`, `ERREUR_OBSERVATION`.

## Mortal_Kombat_1_f0067594_U17

Sub-Zero mène 0–1 au 2e round (111–112) ; en 113, position de départ, vies pleines et marqueur disparu : nouveau match, étiquette juste, observation correcte. Gradient boosting (0,978) et règle (a) la trouvent ; le GRU ne monte qu'à 0,18. Cause principale : `REPRISE`.

## Synthèse du lot lot1_mk1_a

26 cas de Mortal Kombat 1 : 10 de `11029423` (U22 à U31), 2 de `8e58b139` (U02, U09), 14 de `f0067594` (U01 à U17). Le GRU les manque tous. Le gradient boosting en trouve 13, les règles 17 ; 6 sont manqués par les quatre détecteurs (`11029423` U31, `f0067594` U10, U13, U14, U15, U16). Les étiquettes sont justes dans 25 cas. La seule douteuse est `8e58b139` U09 : la fin y est posée une capture après celle qui la prouve. Toutes les fins ont été vérifiées sur les marqueurs zoomés des images originales.

Causes principales : `REPRISE` 22, `ABANDON` 2 (`11029423` U31, `f0067594` U16), `SEUIL` 2 (`8e58b139` U09, `f0067594` U09). Causes secondaires les plus fréquentes : `SEUIL` 21, `CONTEXTE_SANS_VARIATION` 16, `SESSION_DOMINANTE` 11, `LECTURE_COUPEE` 9, `FIN_ENTRE_CAPTURES` 9.

Deux précisions sur les codes. Nouveau code `SESSION_DOMINANTE` : l'enregistrement évalué contient l'essentiel des exemples de ce jeu ou de ce type de fin. `f0067594` contient 58 des 77 parties de Mortal Kombat 1 et 33 des 43 fins « retour à 0–0 avec les mêmes combattants » ; quand il est tenu à l'écart, l'entraînement n'en garde que 10. Le code s'applique à tous les cas de `f0067594`, même s'il n'est noté qu'à partir de U06. J'ai aussi employé `FIN_ENTRE_CAPTURES` au sens large : la dernière manche n'est pas capturée et la preuve est le match suivant déjà commencé, même avec les mêmes combattants.

### Les familles vues

1. **Revanche ou recommencement sans écran de fin, comparaison directe possible** (16 cas : `11029423` U22–U24, U26, U27, U29, U30 ; `8e58b139` U09 ; `f0067594` U01, U04, U06, U07, U08, U11, U12, U17). Le match suivant commence à 0–0 avec les mêmes noms ; souvent, seulement 20 à 40 s séparent la dernière capture du match de la première du suivant, ce qui désigne un « RECOMMENCER » depuis la pause. La règle (a) les trouve tous. Le gradient boosting en trouve 9. Le GRU monte entre 0,18 et 0,63 sans jamais franchir son seuil (0,555 à 0,696).
2. **La même rupture, mais une capture sans score au milieu** (7 cas : écran noir `11029423` U25 et `8e58b139` U02 ; bannière « ROUND 1 » `11029423` U28 ; pause `f0067594` U10 ; cinématique ou effet `f0067594` U13, U14 ; score noté null en entier `f0067594` U15). La règle (a) et toutes les variations comparent à la capture juste avant, donc rien n'est produit. Le gradient boosting rattrape parfois la chute grâce à sa fenêtre de trois captures (U25, U02, U28) ; il échoue ailleurs.
3. **Partie quittée** (2 cas). Pour `11029423` U31 (manette déconnectée, accueil de la PS5, Genshin Impact), le GRU passe tout près (0,539 pour 0,57, 2 graines sur 5). Pour `f0067594` U16 (pause puis choix des Kaméos contre un autre adversaire), une pause entre le jeu et la sélection empêche la règle (c) de se déclencher.
4. **Objectif de manches atteint** (`8e58b139` U09, `f0067594` U09) : la capture où le 2e marqueur s'allume, avec le perdant à 0,00, prouve la fin. Les modèles ne réagissent pas sur cette capture (0,01 à 0,12), seulement sur la suivante.

### Ce qui m'a surpris

- **Le chrono ne sert jamais en Mortal Kombat 1.** La période est toujours « unknown », donc `clock.value_seconds.delta_candidate` n'est jamais calculé. Pourtant le chrono qui remonte (44 → 90, 71 → 79) sans marqueur gagné en plus ne peut pas arriver dans un même match.
- **Le gradient boosting semble avoir appris le côté.** Dans le tour de `f0067594`, les chutes du score de B donnent 0,82 à 0,98 (U04, U07, U11, U12, U17) et la double chute 0,992 (U01). Les chutes du score de A seul restent à 0,07 et 0,35 (U06, U08 ; 0,32 pour U10 avec une pause). Explication probable : les revanches de l'entraînement de ce tour viennent surtout de `11029423`, où c'est toujours le score de B qui retombe.
- **Un motif 0–0, 0–1, 0–0 sur trois captures fait chuter le gradient boosting** (`11029423` U27 0,688 et U29 0,662, contre 0,72 à 0,93 quand le marqueur était lu sur deux captures). Le modèle prend le marqueur isolé pour une erreur de lecture, alors que le match a vraiment duré deux captures.
- **L'étiquetage de la capture à 2 manches n'est pas cohérent.** Dans `f0067594`, la validation humaine du 2026-10-03 pose la fin sur cette capture (U09, U19, U22, U23, U42). Dans `8e58b139` (U03, U05, U07, U08, U09) et dans `f0067594` U34, U47 et U48, elle est posée sur la capture suivante. Les mêmes images reçoivent donc des cibles opposées.
- **Les vies sont affichées en chiffres dans cette salle** (« 1000,00 / 1000 », « 950,00 / 950 »). Des vies pleines des deux côtés sans aucun marqueur, c'est la preuve la plus nette d'un début de match. Le contrat ne la note pas.
- Quelques petites erreurs d'observation, sans effet décisif dans ce lot : un 0–0 noté avant que les emplacements soient dessinés (`f0067594` 40), un chrono à moitié caché lu « 9 » (`f0067594` 23), un score mis à null en entier alors qu'un côté se lisait (`f0067594` 100), des noms écrits sur la pause ou la sélection laissés vides (`f0067594` 62, 106, 107). Le texte de preuve de `8e58b139` U02 parle aussi de « vies pleines » à tort.

### Les méthodes qui reviennent

1. **Comparer à la dernière observation lisible du même jeu** pour la règle (a), les variations de score, les participants et le changement de jeu, en enjambant les écrans noirs, bannières, pauses et cinématiques. Cela trouverait 4 des 6 cas manqués par les quatre détecteurs (U10, U13, U14, U15). La version de la règle (c) qui enjambe les pauses et celle de la règle (d) qui regarde le dernier titre connu trouveraient U16 et U31.
2. **Donner au GRU ce que voit la règle (a)** : sa sortie comme variable, ou une combinaison « OU » GRU + règle (a). La règle trouve ici 17 fins que le GRU manque. Le coût en fausses fins reste à mesurer sur l'ensemble des données.
3. **Des variables symétriques entre A et B** (variation du score total, somme des marqueurs) ou un échange aléatoire des côtés à l'entraînement, contre l'asymétrie du gradient boosting.
4. **Le chrono de round en Mortal Kombat 1** : autoriser sa variation quand le jeu est le même malgré une période inconnue, ou déduire le numéro de manche des marqueurs (somme + 1). Une variable « chrono remonté sans manche gagnée » en découle.
5. **Le contrat et les données** : une variable « vies pleines » ou la vie lue en nombre ; une règle « un côté atteint l'objectif de manches » (score = `counter.target.field`), avec un étiquetage unifié de cette capture ; les noms écrits sur les pauses et les sélections ; plus de revanches de Mortal Kombat 1 hors de `f0067594`.
6. **Les seuils** : dans 23 cas (code `SEUIL`, principal ou secondaire), au moins un modèle monte nettement sans atteindre son seuil (le gradient boosting de 0,63 à 0,83 pour des seuils de 0,68 à 0,88 ; le GRU jusqu'à 0,63 pour 0,70). Relâcher le seuil n'est utile que mesuré contre les fausses fins, puisqu'une fausse fin fait payer une partie de trop.
