# Le compteur

Le VLM décrit chaque capture ; le GRU dit quand une partie finit et si le moment se compte à la partie, au temps ou
pas du tout (`billing_mode` dans PlayEnd). Le compteur, dans `src/playend/counting/`, en tire ce qui a été joué : les
parties qui comptent, les relances rapides qui ne comptent pas, et le temps de jeu des jeux sans fin de partie. Il
applique les règles décidées par l'utilisateur ([regles_facturation.json](../decisions/regles_facturation.json),
détail daté dans [regles-de-comptage.md](../decisions/regles-de-comptage.md)).

Depuis le 13 octobre, les parties se comptent aussi à leur début, avec des règles et sans entraînement
(`src/playend/counting/starts.py`) : résultats et limites dans [DEBUTS_2026-10-13.md](DEBUTS_2026-10-13.md).

Ce dépôt s'arrête au comptage. Les prix, les montants et la facture du client sont l'affaire du produit
(`compteur-intelligent-matchs`), qui recevra ce compte (voir « Laissé au produit » plus bas).

Le compteur ne connaît ni écran, ni base de données, ni horloge système. Le même code rejoue une session enregistrée
pour l'évaluer et tournera sur le Pi, branché sur le produit à la place du pipeline football (`NewMatchTracker`, puis
`commit_new_match`).

## Ce qu'il reçoit : une capture à la fois

| Champ | Sens |
|---|---|
| `frame` | numéro de la capture, gardé comme preuve dans chaque ligne |
| `t` | secondes sur une horloge monotone (`received_monotonic_ns` sur le Pi), jamais l'heure civile |
| `end` | une partie s'est terminée sur cette capture (décision du GRU) |
| `mode` | `per_game`, `time_based` ou `not_billed` (décision du GRU) |
| `game_type` | type de jeu lu par le VLM (`combat`, `football`, `racing`…), qui fixe le seuil de relance rapide |
| `game` | jeu lu par le VLM, pour la ligne |

## Ce qu'il produit

Deux sortes de lignes, écrites en JSON dans le journal (exemples réels du rejeu sur PlayEnd) :

```json
{"kind": "game", "first_frame": 9, "last_frame": 12, "end_frame": 13, "duration_s": 77,
 "game": "Dragon Ball Sparking! ZERO", "game_type": "combat", "threshold_s": 15, "counted": true, "unseen_s": 0}
{"kind": "time", "first_frame": 50, "last_frame": 200, "duration_s": 4071, "game": "Red Dead Redemption 2",
 "unseen_s": 0}
{"kind": "game", "first_frame": 646, "last_frame": 655, "end_frame": null, "duration_s": 308,
 "game": "Fortnite", "game_type": "other", "threshold_s": 60, "counted": true, "unseen_s": 68}
```

`end_frame` vaut `null` pour une partie encore ouverte quand le client part. `unseen_s` est la part de la durée passée
sans aucune image (convention 7). `count` résume les lignes d'un client : parties comptées, relances rapides, secondes
de jeu au temps et temps sans image.

## Les conventions

1. **Une partie est ouverte de sa première capture `per_game` jusqu'à une fin.** Les captures d'un autre mode entre
   les deux (pause, menu) ne la ferment pas.
2. **La capture qui porte la fin.** Elle peut être la dernière image de la partie qui finit ou la première de la
   suivante ; en direct, rien ne permet de trancher (6 parties de PlayEnd finissent sur leur propre dernière capture,
   121 sur la première de la suivante). Elle n'ouvre donc la partie suivante que si la capture d'après est encore en
   jeu ; sinon elle ne compte pour aucune des deux. Sans cette règle, les menus s'ajoutaient à la partie suivante :
   dans la session fdb79549, un combat de Dragon Ball passait de 425 s à 734 s.
3. **Une fin sans partie ouverte ne compte rien.** Une fausse fin hors d'une partie ne coûte rien au client.
4. **Relance rapide.** Une partie se mesure de sa première à sa dernière capture `per_game`, en secondes entières
   arrondies vers le bas. En dessous de son seuil (15 s pour `combat`, 60 s sinon), elle ne compte pas. Le type d'une
   partie est celui que le VLM a lu le plus souvent sur ses captures ; en cas d'égalité, et pour un type absent du
   tableau, c'est le seuil le plus long qui s'applique : le doute profite au client. L'ancien compteur faisait de même
   à sa façon : il ne comptait un match de FC qu'à partir de la 5e minute affichée, ce qui plaçait l'incrément entre
   la 7e et la 10e minute (Mayano, 2024, § 4.1.3).
5. **Le client part en pleine partie** : elle compte si elle a déjà dépassé son seuil, sinon non (décision du
   2026-10-05).
6. **Le temps** se mesure passage par passage, de la première à la dernière capture `time_based` (décision du
   2026-10-05).
7. **Le temps sans image** (décision du 2026-10-05). Un intervalle de plus de 60 s entre deux captures (le plus long
   intervalle normal est de 45 s) est du temps sans image : câble débranché, console éteinte, Pi bloqué. Il reste
   compté avec la partie ou le passage au temps qui l'entoure, et la ligne l'indique (`unseen_s`) pour que
   l'opérateur tranche avec le client. Ne pas le compter reviendrait à payer moins en débranchant le boîtier ; le
   compter sans le dire ferait payer un temps sans preuve. Un trou après la dernière image en jeu d'une partie n'est
   pas compté : il n'est pas dans sa durée. Le seuil est dans `regles_facturation.json` ; il faudra le revoir quand le
   VLM fixera le vrai rythme des captures sur le Pi.

## Vérification sur PlayEnd

```bash
python -m playend.counting.replay        # écrit build/counting/truth/
```

Le rejeu fait passer les 25 sessions dans le compteur avec les fins vérifiées par l'utilisateur ; le client part à
l'arrêt de la capture. Il compare le compte à une référence tirée directement de `units.csv` et `time_segments.csv`,
avec les mêmes règles. Résultat du 2026-10-05 :

| | Référence | Compteur |
|---|---:|---:|
| Parties comptées | 296 | 296 |
| Relances rapides non comptées | 6 | 4 |
| Temps de jeu au temps | 38 674 s (645 min) | 38 674 s |
| Lignes avec du temps sans image | | 1 (Fortnite, 68 s sur 308 s) |

Les 296 parties comptent les 7 parties encore en cours à l'arrêt de la capture : toutes avaient dépassé leur seuil.
Aucune partie n'est comptée différemment. Les écarts restants viennent de la convention 2 :

- 6 parties finissent une capture plus tôt que dans la référence (en faveur du client) et 3 revanches de Mortal
  Kombat 1 commencent une capture plus tôt ; toutes restent comptées ;
- 2 relances vues sur une seule capture (Tekken 8, Dragon Ball) n'apparaissent pas dans le journal ; elles ne sont
  comptées ni d'un côté ni de l'autre.

Les fichiers écrits : `sessions.csv` (référence et compteur côte à côte, par session), `events.jsonl` (toutes les
lignes) et `differences.jsonl`.

## Avec les fins prédites (2026-10-08)

```bash
python -m playend.counting.predicted [--package build/student/packages/student] [--model boosting] [--modes reference]
```

Le même compteur reçoit cette fois les décisions d'un détecteur du calcul du 6 octobre, sur chacune des 25 sessions
qu'il n'a pas vues à l'entraînement (cinq graines, résultat moyen). Une fin est la première capture d'une suite
au-dessus du seuil que le calcul a choisi pour le budget, la règle de l'évaluation, sans les masques des intervalles
incertains, que le Pi n'aura pas. Le mode de facturation est celui que prédit la seconde tête du GRU, ou le vrai mode
(`--modes reference`) pour séparer les deux sources d'erreur ; le gradient boosting ne prédit pas de mode. Le jeu et
son type viennent des observations lues par le détecteur : celles du professeur, ou celles de l'élève
(`docs/student/RESULTATS.md`).

Chaque partie comptée est appariée à au plus une partie comptée de la référence, les paires qui partagent le plus de
temps d'abord, comme les métriques par événement de la détection d'événements sonores (Mesaros et al., 2016). Une
partie du compteur sans paire est une partie **en trop** (le client la paie), une partie de la référence sans paire
est une partie **manquée** (la salle la perd). Le comptage de répétitions dans les vidéos s'évalue aussi par l'écart
absolu entre le compte prédit et le vrai, et par la part des vidéos comptées juste à une unité près (Dwibedi et al.,
2020) : on les donne par session. Le temps de jeu au temps se compare seconde par seconde.

Vérification : avec les vraies fins et les vrais modes, ce rejeu redonne exactement la référence (296 parties, 0 en
trop, 0 manquée, 38 674 s).

Budget d'une fausse fin pour 100 parties, sur 296 parties de référence et 645 minutes au temps :

| Détecteur | Observations | Mode | Parties comptées | En trop pour 100 | Manquées pour 100 | Sessions au compte exact | à une près | Minutes au temps en trop / manquées |
|---|---|---|---:|---:|---:|---:|---:|---:|
| GRU | professeur | prédit | 134,4 | 1,4 | 56,0 | 35 % | 54 % | 104 / 50 |
| GRU | élève | prédit | 131,4 | 2,6 | 58,2 | 27 % | 48 % | 129 / 97 |
| GRU | professeur | vrai | 131,6 | 0,3 | 55,9 | 38 % | 56 % | 0 / 0 |
| GRU | élève | vrai | 131,4 | 1,4 | 57,0 | 35 % | 49 % | 0 / 0 |
| Gradient boosting | professeur | vrai | 141,0 | 0,0 | 52,4 | 40 % | 52 % | 0 / 0 |
| Gradient boosting | élève | vrai | 100,0 | 0,0 | 66,2 | 36 % | 40 % | 0 / 0 |

Budget de cinq fausses fins pour 100 parties :

| Détecteur | Observations | Mode | Parties comptées | En trop pour 100 | Manquées pour 100 | Sessions au compte exact | à une près |
|---|---|---|---:|---:|---:|---:|---:|
| GRU | professeur | prédit | 174,2 | 2,7 | 43,9 | 44 % | 57 % |
| GRU | élève | prédit | 174,0 | 4,5 | 45,7 | 34 % | 63 % |
| Gradient boosting | professeur | vrai | 196,0 | 0,7 | 34,5 | 56 % | 72 % |
| Gradient boosting | élève | vrai | 161,0 | 1,7 | 47,3 | 44 % | 56 % |

Ce que le rejeu montre :

- **Le client paie rarement une partie de trop.** Une fausse fin ne lui coûte que si elle ajoute une partie au compte.
  Avec les observations de l'élève et les vrais modes, le GRU fait 27,4 fausses fins par graine : 12,2 sont de
  vraies fins vues en retard, qui ferment la bonne partie ; 9,8 coupent une partie dont la vraie fin suivante est
  ratée, et le nombre de parties reste juste ; 1,0 tombe hors d'une partie ouverte (convention 3). Seules 4,4
  ajoutent une partie, soit les 1,4 parties en trop pour 100. Avec les observations du professeur : 10,8 fausses
  fins, dont 1,0 seulement ajoute une partie.
- **La salle perd plus de la moitié des parties** au budget 1, avec les observations du professeur comme avec
  celles de l'élève : une fin ratée fusionne deux parties en une. La limite du comptage est le rappel des
  détecteurs (37 à 43 % des fins trouvées le 6 octobre), pas la lecture de l'élève.
- **Le mode prédit par le GRU** ajoute peu de parties en trop, mais déplace le temps facturé : 104 minutes comptées au
  temps en trop et 50 manquées sur 645 avec les observations du professeur, 129 et 97 avec celles de l'élève.
- **Le budget se juge mieux au niveau du comptage.** Au budget 5, le gradient boosting sur les observations du
  professeur ne compte que 0,7 partie de trop pour 100 et en manque 34,5 au lieu de 52,4. Le budget retenu pour le
  produit reste à décider avec l'utilisateur.

### Avec les détecteurs réentraînés sur l'élève (2026-10-11)

```bash
python -m playend.counting.predicted --package build/student/packages/student \
    --run build/student/kit_resultats_20261010/results/gru --model boosting --modes reference
```

Le kit de l'élève a réentraîné les détecteurs sur les observations de l'élève, avec le même protocole
(`docs/student/RESULTATS.md`, section 8). `--run` rejoue leurs prédictions enregistrées, sans rien réentraîner. C'est
le compte du système qui tournerait sur le Pi : l'élève lit l'écran, un détecteur entraîné sur ses lectures trouve les
fins. Sur 296 parties de référence :

| Détecteur | Entraîné sur | Mode | Budget | Parties comptées | En trop pour 100 | Manquées pour 100 | Sessions au compte exact | à une près |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Gradient boosting | professeur | vrai | 1 | 100,0 | 0,0 | 66,2 | 36 % | 40 % |
| Gradient boosting | élève | vrai | 1 | 98,0 | 0,3 | 67,2 | 32 % | 40 % |
| GRU | professeur | prédit | 1 | 131,4 | 2,6 | 58,2 | 27 % | 48 % |
| GRU | élève | prédit | 1 | 47,4 | 1,0 | 85,0 | 24 % | 41 % |
| Gradient boosting | professeur | vrai | 5 | 161,0 | 1,7 | 47,3 | 44 % | 56 % |
| Gradient boosting | élève | vrai | 5 | 151,0 | 0,7 | 49,7 | 32 % | 48 % |

Réentraîner sur l'élève divisait par trois les fausses fins de la détection, mais ne change presque rien au compte :
avec les détecteurs entraînés sur le professeur, ces fausses fins n'ajoutaient déjà presque aucune partie. Le GRU
réentraîné, qui ne trouve plus que 6,1 % des fins, fait perdre 85 parties sur 100 à la salle. Avec ce qui tournerait
sur le Pi, le client ne paie presque jamais une partie de trop (0,3 pour 100 avec le gradient boosting), mais la salle
perd environ deux parties sur trois au budget 1, et une sur deux au budget 5. Avec le GRU réentraîné et ses modes
prédits, le temps au temps compte 112 minutes en trop et 70 manquées sur 645 (fichier
`student_gru_predicted_modes_retrained.json`, et `student_gru_reference_modes_retrained.json` avec les vrais modes).

Les résultats sont écrits dans `build/counting/predicted/` (un fichier JSON par détecteur, paquet et mode, avec le
détail de chaque graine).

## La suite

- **Dans le produit** : le compteur remplacera le pipeline football ; ses lignes deviendront des enregistrements
  `games` et un événement de cluster `game`.

## Laissé au produit

Décisions de l'utilisateur du 2026-10-05, qui ne relèvent pas du comptage et ne sont pas appliquées ici :

- les prix se règlent par genre de jeu, avec un prix par bloc de temps, par l'employé ou l'employeur dans le produit ;
- le temps de jeu au temps s'arrondit au bloc supérieur une seule fois par client, pour qu'un passage coupé en deux
  ne soit pas arrondi deux fois ;
- le temps sans image apparaît sur la ligne de facture (« dont … sans image »).

## Points à confirmer

1. **Une capture `time_based` pendant une partie ouverte** est comptée au temps en plus. Cela n'arrive pas avec les
   fins vérifiées ; à surveiller dans le rejeu avec le GRU.
2. **Les relances vues sur une seule capture** ne sont pas listées (convention 2). Les lister ferait apparaître, dans
   les cas inverses, des lignes de parties qui n'existent pas.

## Pourquoi ce découpage

- Le cœur se teste sans matériel : c'est le but de l'architecture hexagonale de Cockburn (2005), une application
  « developed and tested in isolation from its eventual run-time devices and databases ».
- Le modèle, les règles de comptage et les prix restent séparés : changer un seuil ou un prix ne demande pas de
  réentraîner, ce qui évite la dette technique décrite par Sculley et al. (2015).
- Le même code sert à l'évaluation et en service : règle n° 32 des *Rules of Machine Learning* de Google (« Re-use
  code between your training pipeline and your serving pipeline whenever possible »).
- Le journal des lignes ne s'efface jamais : les totaux du jour se recalculent en le rejouant (Fowler, 2005). L'ancien
  cluster fait déjà ainsi, avec sa clé unique (borne, type, enregistrement).

## Sources

- Cockburn, A. (2005). *Hexagonal Architecture* (ports and adapters). Résumé et citation :
  en.wikipedia.org/wiki/Hexagonal_architecture_(software) ; AWS Prescriptive Guidance, *Hexagonal architecture
  pattern*.
- Dwibedi, D., Aytar, Y., Tompson, J., Sermanet, P., Zisserman, A. (2020). *Counting Out Time: Class Agnostic Video
  Repetition Counting in the Wild*. CVPR 2020, § 6.1 (erreur « off-by-one » et erreur absolue moyenne du compte).
  arxiv.org/abs/2006.15418
- Fowler, M. (2005, 12 décembre). *Event Sourcing*. martinfowler.com/eaaDev/EventSourcing.html
- Google. *Rules of Machine Learning: Best Practices for ML Engineering* (Zinkevich), règles 32 et 37.
  developers.google.com/machine-learning/guides/rules-of-ml
- Mayano, B. D. (2024). *Compteur intelligent des matchs dans une salle de jeux vidéo*. Mémoire de licence en
  informatique, Université de Kinshasa (dir. J. F. Masakuna).
- Mayano, B. D., Yan-Mol, L. L., Masakuna, J. F. (2025). *Intelligent Match Counter in a Video Game Arena*. IEEE
  Access 13, 32320–32328. doi:10.1109/ACCESS.2025.3542425
- Mesaros, A., Heittola, T., Virtanen, T. (2016). *Metrics for Polyphonic Sound Event Detection*. Applied Sciences
  6(6), 162. doi:10.3390/app6060162
- Sculley, D. et al. (2015). *Hidden Technical Debt in Machine Learning Systems*. NeurIPS 28, 2503–2511.
