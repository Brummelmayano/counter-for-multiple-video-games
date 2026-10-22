# Résultats du premier entraînement complet (2026-10-06)

Le protocole de `docs/decisions/PLAN_ENTRAINEMENT_GRU.md` a tourné en entier chez un ami, avec le kit
`build/playend_training.zip`. Il est rangé comme s'il avait tourné ici : le dossier complet, avec tous les
entraînements, est `build/training/v1/` (la vérification rapide faite sur la même machine est
`build/training/quick_ami/`, et le zip d'origine `build/training/archives/playend_results_20261006-1844.zip`). Le
rapport, les figures, les choix de chaque tour et le GRU à déployer sont aussi copiés dans `resultats_2026-10-06/`, suivi
par git.

## Le calcul

- Machine : Windows 11, 16 cœurs logiques, Python 3.14.6, PyTorch 2.14.1 pour processeur (aucune carte graphique n'a
  servi), scikit-learn 1.9.1 (`resultats_2026-10-06/machine.txt`).
- Code du commit `54534cc7`. Les commits suivants n'ont touché que la présentation du code d'entraînement (textes,
  lecture des CSV, découpage d'une fonction) et le lanceur ; le rapport refait avec le code actuel donne les mêmes
  tableaux.
- Le calcul s'est arrêté deux fois (code Windows `0xC000013A`, fenêtre fermée ou Ctrl-C), après 50 minutes puis une
  minute. La reprise a gardé les 768 entraînements déjà finis ; le calcul s'est ensuite terminé normalement.
- 3 360 entraînements pour la recherche des réglages, 428 pour le retrait des groupes de variables, 182 finaux (pour
  chacun des 26 tours, dont celui du modèle à déployer sur les 25 sessions : 5 graines du GRU, une régression
  logistique, un gradient boosting), soit 68,8 heures-processus.

## Résultats sur les sessions tenues à l'écart

Chaque session est jugée par des modèles qui ne l'ont jamais vue, au seuil choisi sur la validation de son tour. Une
fin trouvée une capture en retard compte comme juste ; les intervalles viennent du rééchantillonnage des sessions.

| Modèle | Budget de validation | Rappel | Fausses fins pour 100 parties | Précision |
|---|---|---:|---:|---:|
| GRU | 1 pour 100 | 37,3 % [25,2 ; 52,3] | 3,8 | 90,8 % |
| Gradient boosting | 1 pour 100 | 42,5 % [36,7 ; 50,0] | 1,4 | 96,8 % |
| Régression logistique | 1 pour 100 | 8,4 % [4,8 ; 14,5] | 3,5 | 70,6 % |
| Règles écrites à la main | aucun seuil | 55,8 % [47,7 ; 63,4] | 32,3 | 63,3 % |
| GRU | 5 pour 100 | 47,7 % [34,1 ; 64,9] | 7,6 | 86,3 % |
| Gradient boosting | 5 pour 100 | 60,4 % [54,9 ; 69,0] | 4,2 | 93,5 % |

Le gradient boosting trouve plus de fins et en invente moins que le GRU, mais l'écart ne se confirme pas session par
session : test de Wilcoxon sur les 25 sessions (Demšar, 2006), p = 0,91 pour le rappel et p = 0,12 pour les fausses
fins. Le GRU fait en revanche nettement moins de fausses fins que les règles (p = 0,001) et trouve nettement plus de
fins que la régression logistique (p < 0,001). Le seuil choisi en validation ne tient pas pour le GRU : 3,8 fausses
fins pour 100 parties au lieu d'une, contre 1,4 pour le gradient boosting. D'une graine à l'autre, le GRU varie de
± 1 point.

Le mode de facturation (par partie, au temps, hors jeu) prédit par le GRU est juste dans 93,9 % des captures.

## Ce que le GRU rate : les jeux jamais vus

Six jeux ne sont joués que dans une seule session : Tekken 8 (31 parties), Beach Buggy Racing 2 (27 parties, seul jeu
de course du jeu de données), Dragon Ball FighterZ, J-Stars Victory VS+, Demon Slayer et Brawlhalla. Quand leur
session est tenue à l'écart, le modèle ne les a jamais vus.

| Modèle (premier budget) | Jeux joués dans d'autres sessions | Jeux d'une seule session |
|---|---:|---:|
| GRU | 46,1 % | 6,9 % |
| Gradient boosting | 45,7 % | 31,2 % |
| Régression logistique | 10,9 % | 0,0 % |
| Règles écrites à la main | 58,8 % | 45,3 % |

Sur les jeux connus, le GRU et le gradient boosting trouvent autant de fins ; le GRU fait environ cinq fois plus de
fausses fins. Sur les jeux inconnus, le GRU s'effondre. Les deux cas extrêmes n'ont pas la même cause :

- Tekken 8 (`figures/sessions/078643a4.png`) : la probabilité du GRU monte à chaque fin, mais reste entre 0,2 et 0,4,
  sous le seuil de 0,48. Le signal existe, trop faible.
- Beach Buggy Racing 2 (`figures/sessions/fdb79549.png`) : la probabilité reste plate sur toute la série de courses.
  Les variables donnent le genre du jeu, pas son titre ; or aucun autre jeu de course n'est dans les données.

Le détail par jeu et par modèle est dans `resultats_2026-10-06/report.md` et `figures/families.png`.

## Les réglages

Le tableau complet des 16 essais du GRU et des 8 essais de chaque modèle de référence est dans le rapport. Les
rappels qui suivent sont ceux de la validation, moyennés sur les 25 tours.

- GRU : les huit meilleurs essais ne pondèrent pas les fins (22,5 % de meilleur rappel avec la pondération, 31,1 %
  sans). Les trois premiers ont une couche de 64 et un taux d'apprentissage autour de 1,3 × 10⁻³ ; le meilleur
  (27,9 % en moyenne) est aussi celui retenu pour le déploiement (64 unités, dropout 0,34, pénalité 1,4 × 10⁻⁵,
  taux 1,26 × 10⁻³). Le GRU est très sensible à ses réglages : de 6 % à 33 % selon l'essai sur le tour final, et huit
  essais différents ont été retenus selon les tours. Les couches de 16 classent le mieux les captures (précision
  moyenne 0,65) mais trouvent moins de fins au seuil strict.
- Gradient boosting : la pondération des classes aide (les quatre meilleurs essais la prennent), les arbres de 15
  feuilles font un peu mieux que ceux de 31. Un même essai a été retenu dans 13 tours sur 25 (37,9 % en moyenne).
- Régression logistique : régularisation forte et fenêtre de deux captures, sans dépasser 6 % en moyenne.

Avec 16 tirages au hasard, la chance de tomber dans les 10 % meilleurs réglages de l'espace est d'environ 81 %
(1 − 0,9¹⁶) : un GRU mieux réglé gagnerait peut-être quelques points. Le gradient boosting, avec deux fois moins
d'essais, fait pourtant au moins aussi bien.

## L'apprentissage

Meilleure époque médiane : 95 sur 300 au plus. Dans la moitié des courbes du GRU retenu, la perte de validation
remonte de plus de 10 % après son minimum : le modèle surapprend, ce que l'arrêt précoce rattrape. Retirer un groupe
de variables coûte de 7 à 14 points de rappel de validation ; les changements d'une capture à l'autre sont le groupe le
plus utile.

## Ce que cela veut dire pour le comptage

- Les fausses fins restent rares avec les modèles entraînés : 0,06 par heure de jeu pour le gradient boosting, 0,16
  pour le GRU. Le client paierait rarement une partie de trop.
- Les fins ratées sont nombreuses : avec un rappel de 40 à 60 %, la salle perdrait une partie sur deux environ.
  L'effet réel sur la facture dépend de la suite (deux parties fusionnées ne coûtent qu'une partie), ce que le rejeu
  du compteur avec les fins prédites mesurera.
- Les règles écrites à la main ne sont pas utilisables seules : 92 fausses fins pour 285 fins (32,3 pour 100 parties),
  dont 27 dans Genshin Impact, un jeu de mission sans fin de partie.

Pourquoi un modèle sans mémoire fait-il aussi bien qu'un modèle récurrent ? Le gradient boosting voit la capture et
les deux précédentes, et les variables de PlayEnd décrivent déjà ce qui change d'une capture à l'autre (score,
chrono, titre, participants) : c'est la méthode de la fenêtre glissante (Dietterich, 2002). La plupart des signes de
fin sont locaux, dans la minute qui entoure la fin. Sur des données en tableau et en petite quantité (302 parties), les
arbres de décision battent souvent les réseaux de neurones (Grinsztajn et al., 2022 ; Shwartz-Ziv et Armon, 2022).

## Limites

- 25 sessions et 302 parties : les intervalles restent larges, et six jeux n'apparaissent que dans une session.
- Les conclusions valent pour les réglages fixés (une couche, sens unique, 300 époques au plus) et pour une tolérance
  d'une capture.
- Calcul sur processeur : PyTorch ne garantit pas les mêmes chiffres au dernier chiffre sur GPU, ce qui ne change rien
  aux comparaisons.

## Suites possibles, à décider

1. Rejouer le compteur (`src/playend/counting/`) avec les fins prédites par le gradient boosting et le GRU, pour
   mesurer l'erreur de facturation en parties et en minutes.
2. Mesurer la tenue sur un jeu jamais vu en tenant à l'écart un jeu entier plutôt qu'une session.
3. Améliorer la détection : gradient boosting comme détecteur, GRU plus largement réglé ou combiné au gradient
   boosting, variables pour les fins de Tekken (`WINS`) et de Beach Buggy (retour au tour 1, écran de classement).

## Sources

- Demšar, J. (2006). Statistical comparisons of classifiers over multiple data sets. *Journal of Machine Learning
  Research*, 7, 1–30.
- Dietterich, T. G. (2002). Machine learning for sequential data: a review. *Structural, Syntactic, and Statistical
  Pattern Recognition*, LNCS 2396, 15–30.
- Grinsztajn, L., Oyallon, E. et Varoquaux, G. (2022). Why do tree-based models still outperform deep learning on
  tabular data? *NeurIPS, Datasets and Benchmarks Track*. arXiv:2207.08815.
- Shwartz-Ziv, R. et Armon, A. (2022). Tabular data: deep learning is not all you need. *Information Fusion*, 81,
  84–90. arXiv:2106.03253.
- Bergstra, J. et Bengio, Y. (2012). Random search for hyper-parameter optimization. *Journal of Machine Learning
  Research*, 13, 281–305.
