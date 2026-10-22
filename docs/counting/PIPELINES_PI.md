# Quelle chaîne faire tourner sur le Raspberry Pi ? (protocole, 15 octobre 2026)

Demande de l'auteur du 2026-10-15 : mesurer sur le Pi Zero 2 W le temps de chaque chaîne qu'on pourrait adopter, et
son résultat sur les deux sessions jamais lues (`docs/counting/SESSIONS_INEDITES.md`), pour choisir la chaîne qui
offre le meilleur compromis entre justesse et durée. Code : `src/playend/counting/pipelines.py` ; détecteurs appris :
`src/playend/training/starts/final.py` ; programme du Pi : `docs/student/pi/debuts_2026-10-15.sh`.

## Les chaînes

| | Lecture | Décision |
|---|---|---|
| A | Classifieur (jeu, écran) et OCR sur les zones du HUD | Compteur de débuts par règles |
| B | Comme A | Gradient boosting (état de la partie et décisions des règles) ou GRU début et fin, entraînés sur les 25 sessions |
| C | Classifieur, et le VLM adapté par LoRA sur chaque capture de jeu, à la place de l'OCR | Règles |
| D | Comme A, mais le VLM relit les captures où les règles hésitent | Règles |

Une capture fait hésiter les règles quand la lecture de l'OCR leur ferait ouvrir une partie, garder une partie en
attente de confirmation, ou en confirmer une. D est une cascade : un modèle léger lit tout, un modèle lourd ne relit
que les cas difficiles, comme la cascade de détecteurs de Viola et Jones (2001) ou FrugalGPT, qui n'appelle un grand
modèle que quand un petit ne suffit pas (Chen, Zaharia et Zou, 2023).

## Ce qui reste fixé

Le classifieur, le lecteur OCR et les règles sont ceux gelés pour les sessions jamais lues (commit `96d77ad2`,
`frozen.json`, vérifié à chaque étape). Le VLM est l'adaptateur LoRA final du 10 octobre, entraîné sur PlayEnd ; il
n'a jamais vu ces deux sessions : c'est la première mesure de sa justesse sur des captures inconnues. Les détecteurs
de B sont choisis et entraînés sur les 25 sessions de PlayEnd par la validation croisée de l'étape 3 (réglage, nombre
d'arbres ou d'époques, seuil au budget de 2 parties en trop pour 100), sans regarder les sessions jamais lues, puis
exportés en tableaux pour tourner avec NumPy seul (le Pi n'a ni scikit-learn ni PyTorch ; les arbres exportés
redonnent exactement les probabilités de scikit-learn).

## Ce que le Pi mesure, dans l'ordre

1. A sur toutes les captures : lectures, débuts, temps, température, mémoire.
2. Huit captures de C lues par `llama-mtmd-cli`, l'outil avec lequel le VLM a été mesuré le 10 et le 11 octobre.
3. C par `llama-server`, qui garde le modèle chargé, comme le ferait le produit ; les huit premières réponses sont
   comparées à celles de l'outil en ligne de commande.
4. L'OCR qui lit 20 captures pendant que le serveur répond sans arrêt au VLM : temps de l'OCR, mémoire libre et
   échange sur la carte. C'est la condition de D sur un Pi de 512 Mo.
5. B capture par capture : variables, état de la partie, gradient boosting, GRU.

Le PC compte ensuite les parties de chaque chaîne contre la référence validée, une seule fois, avec la règle
d'appariement de PlayEnd, et rassemble les temps mesurés sur le Pi. Les lectures du VLM faites aussi sur le PC, avec
une autre version de llama.cpp, servent à vérifier le code avant la nuit ; les chiffres retenus sont ceux du Pi.

## Les détecteurs de B, entraînés le 15 octobre

`python -m playend.training.starts.final`, sur les lectures de l'élève des 25 sessions (1 h 35 sur un cœur du PC).
Réglage choisi par les 5 plis, seuil au budget de 2 parties en trop pour 100 sur leurs prédictions :

| | Réglage | Seuil | Sur les 5 plis de PlayEnd |
|---|---|---|---|
| Gradient boosting (`gb_rules`) | 113 arbres, 31 feuilles, pas 0,05, L2 0,61, dilatation 2 | 0,881 | 218/308 trouvées, 4 en trop |
| GRU début et fin | 16 unités, abandon 0,46, 138 époques, 3 graines, dilatation 2 | 0,907 | 213/308 trouvées, 5 en trop |

Le GRU exporté donne avec NumPy les probabilités de PyTorch à 3·10⁻⁷ près (4 sessions, 1 180 captures).

## Aperçu sur le PC, avant la nuit du Pi

Mêmes lectures de l'OCR que sur le PC (`build/evaluation/sessions_inedites`), VLM lu par llama.cpp b10840 :

| | Trouvées | En trop | Compte exact |
|---|---|---|---|
| A | 25/27 | 6 | 1 session sur 2 |
| B, gradient boosting | 18/27 | 0 | 0 |
| B, GRU | 18/27 | 1 | 0 |
| C | 22/27 | 6 | 1 |
| D (48 relectures du VLM) | 24/27 | 2 | 1 |

Sur 8 captures, `llama-server` et `llama-mtmd-cli` rendent les mêmes réponses. Les chiffres retenus seront ceux du Pi.

## Résultats sur le Raspberry Pi (nuit du 15 au 16 octobre)

Programme lancé le 15 au soir, coupé une fois (le Pi débranché pendant le VLM), repris sans perte le 16 au matin ; fini
après 10 h 12 de marche sur les 14 h du budget, 1 391 fiches, aucune vide. Résultats copiés dans
`build/evaluation/pi_2026-10-16/`, comptés sur le PC par `python -m playend.counting.pipelines compare`.

| Chaîne | Trouvées | En trop | Pour 100 | Temps sur le Pi |
|---|---|---|---|---|
| A, OCR et règles | 25/27 | 6 | 22,2 | 3,7 s par capture en médiane (90e centile 8,4 s, max 18,5 s) |
| B, gradient boosting | 18/27 | 0 | 0 | celui de A, plus 3 ms |
| B, GRU | 18/27 | 1 | 3,7 | celui de A, plus 3 ms |
| C, VLM sur chaque capture de jeu | 22/27 | 5 | 18,5 | 69,4 s par capture de jeu (90e centile 76,3 s, max 88,9 s) |
| D, VLM là où les règles hésitent | 25/27 | 2 | 7,4 | celui de A, plus 49 relectures du VLM sur 871 captures |

Ce que disent les temps :

- C ne suit pas le jeu : ses 509 lectures, à 69,4 s en médiane, ont demandé en tout 3,0 h de VLM pour 2,0 h
  d'enregistrement (2e4eea20, 170 lectures) et 6,6 h pour 4,7 h (a4ad74e6, 339 lectures).
- D le suit : 13 et 36 relectures, le VLM occupé 12 et 15 % du temps ; en servant les relectures une à une, dans leur
  ordre d'arrivée et avec le temps mesuré de chacune, la réponse arrive 76 s après la capture en médiane, 190 s au
  plus, soit une à six captures plus tard. *Recalculé le 2026-10-16 : la première version donnait 3,3 h, 13 %, 69 s
  et 183 s, tirés du temps médian au lieu des temps mesurés.* Pendant que le serveur
  répond, l'OCR lit une capture en 1,7 s en médiane (5,7 s au plus), avec 108 Mo de mémoire libre au plus bas et
  environ 470 Mo dans la mémoire d'échange, à 63–67 °C.
- Le serveur seul : jusqu'à 312 Mo, mémoire libre descendue à 208 Mo, jusqu'à 1,5 Go dans la mémoire d'échange,
  83 °C. Le traitement de la question y prend environ 64 s (196 jetons à 329 ms), contre une trentaine de secondes
  mesurées le 11 octobre avec l'outil en ligne de commande : le serveur réserve quatre emplacements de 4 096 jetons et
  déborde dans la mémoire d'échange. À confirmer par une mesure avec un seul emplacement, si l'auteur le veut.

Le Pi et le PC : A donne exactement le même compte ; le VLM rend les mêmes champs sur 497 captures sur 509 (llama.cpp
0.6.0 sur le Pi, b10840 sur le PC) ; le serveur et l'outil en ligne de commande rendent les mêmes champs sur 8 sur 8.
D trouve une partie de plus sur le Pi que sur le PC (25 contre 24), à cause de ces lectures qui diffèrent.

Lecture : D est le meilleur compromis mesuré. Il garde les parties trouvées de A (25 sur 27) et ramène les parties en
trop de 6 à 2, pour un VLM qui ne relit qu'une capture sur dix-huit. Les détecteurs appris de B n'inventent presque
rien mais ratent une partie sur trois ; C lit mieux certaines captures mais ne tient pas le rythme et invente autant
que A.

Limites : deux enregistrements et 27 parties, un ordre de grandeur sans intervalle. La règle qui décide quand le VLM
relit (D) a été écrite le 15 octobre, après la mesure de A sur ces mêmes sessions, en sachant que les parties en trop
venaient de scores mal lus : son résultat est moins neutre que celui de A, gelé avant de regarder les sessions. Le
« compte exact » de C (2 sessions sur 2) est un hasard : 5 parties manquées et 5 en trop qui se compensent.
