# Résultats de l'entraînement

Sessions tenues à l'écart : 25. Chaque session est évaluée par des modèles qui ne l'ont jamais vue, au seuil choisi sur la validation de son propre tour. Une fin trouvée une capture en retard compte comme juste. Les intervalles entre crochets viennent du rééchantillonnage des sessions (95 %).

## Seuil choisi pour au plus 1 fausse(s) fin(s) pour 100 parties (validation)

| Modèle | Précision | Rappel | Fausses fins pour 100 parties | Fausses fins par heure |
|---|---:|---:|---:|---:|
| GRU | 63.0 % | 6.1 % [2.0 %; 10.5 %] | 3.6 | 0.15 |
| régression logistique | 81.0 % | 6.0 % [3.2 %; 9.1 %] | 1.4 | 0.06 |
| gradient boosting | 92.3 % | 25.3 % [20.7 %; 28.8 %] | 2.1 | 0.09 |
| règles | 63.3 % | 55.8 % [47.7 %; 63.4 %] | 32.3 | 1.35 |

## Seuil choisi pour au plus 2 fausse(s) fin(s) pour 100 parties (validation)

| Modèle | Précision | Rappel | Fausses fins pour 100 parties | Fausses fins par heure |
|---|---:|---:|---:|---:|
| GRU | 63.5 % | 6.6 % [2.4 %; 10.9 %] | 3.8 | 0.16 |
| régression logistique | 83.3 % | 7.0 % [3.6 %; 10.7 %] | 1.4 | 0.06 |
| gradient boosting | 90.1 % | 28.8 % [22.2 %; 34.1 %] | 3.2 | 0.13 |
| règles | 63.3 % | 55.8 % [47.7 %; 63.4 %] | 32.3 | 1.35 |

## Seuil choisi pour au plus 5 fausse(s) fin(s) pour 100 parties (validation)

| Modèle | Précision | Rappel | Fausses fins pour 100 parties | Fausses fins par heure |
|---|---:|---:|---:|---:|
| GRU | 55.9 % | 14.2 % [3.6 %; 27.7 %] | 11.2 | 0.47 |
| régression logistique | 89.7 % | 18.2 % [9.2 %; 24.7 %] | 2.1 | 0.09 |
| gradient boosting | 82.9 % | 37.5 % [29.3 %; 44.9 %] | 7.7 | 0.32 |
| règles | 63.3 % | 55.8 % [47.7 %; 63.4 %] | 32.3 | 1.35 |

Écart entre graines du GRU : rappel ± 3.1 %, précision ± 5.8 %.

GRU contre chaque autre modèle (Wilcoxon par session, premier seuil) :

- régression logistique : p = 0.445 pour le rappel, p = 0.684 pour les fausses fins
- gradient boosting : p = 0.001 pour le rappel, p = 1.000 pour les fausses fins
- règles : p = 0.000 pour le rappel, p = 0.003 pour les fausses fins

## Par famille de jeu (premier seuil)

Rappel, puis fausses fins par entraînement entre parenthèses (le GRU est la moyenne de ses graines).

| Famille | Fins | GRU | régression logistique | gradient boosting | règles |
|---|---:|---:|---:|---:|---:|
| Assassin's Creed Origins | 0 | - | - | - | - (3) |
| Beach Buggy Racing 2 | 27 | 0.0 % (0) | 0.0 % (0) | 25.9 % (0) | 22.2 % (0) |
| Brawlhalla | 1 | 0.0 % (0) | 0.0 % (0) | 0.0 % (0) | 100.0 % (0) |
| Call of Duty: Warzone | 12 | 0.0 % (0) | 8.3 % (0) | 16.7 % (0) | 33.3 % (5) |
| Demon Slayer | 1 | 0.0 % (0) | 0.0 % (0) | 0.0 % (0) | 100.0 % (0) |
| Dragon Ball FighterZ | 2 | 0.0 % (0) | 0.0 % (0) | 0.0 % (0) | 0.0 % (1) |
| Dragon Ball Sparking! ZERO | 21 | 1.9 % (0) | 4.8 % (0) | 9.5 % (0) | 33.3 % (4) |
| EA Sports FC | 77 | 5.2 % (0.6) | 5.2 % (2) | 26.0 % (5) | 57.1 % (16) |
| EA Sports UFC 5 | 11 | 0.0 % (0.8) | 9.1 % (2) | 0.0 % (0) | 36.4 % (2) |
| Fortnite | 27 | 16.3 % (0.4) | 11.1 % (0) | 29.6 % (1) | 88.9 % (9) |
| Genshin Impact | 0 | - | - | - | - (27) |
| God of War | 0 | - | - | - | - (2) |
| J-Stars Victory VS+ | 2 | 0.0 % (0) | 0.0 % (0) | 50.0 % (0) | 100.0 % (2) |
| Mortal Kombat 1 | 67 | 10.7 % (8.4) | 6.0 % (0) | 32.8 % (0) | 64.2 % (10) |
| Naruto Storm Connections | 6 | 23.3 % (0) | 0.0 % (0) | 0.0 % (0) | 66.7 % (1) |
| Red Dead Redemption 2 | 0 | - | - | - | - (9) |
| Tekken 8 | 31 | 0.0 % (0) | 9.7 % (0) | 32.3 % (0) | 61.3 % (1) |

Jeux joués dans une seule session (Beach Buggy Racing 2, Brawlhalla, Demon Slayer, Dragon Ball FighterZ, J-Stars Victory VS+, Tekken 8) : quand cette session est tenue à l'écart, le modèle n'a jamais vu le jeu.

| Modèle | Jeux vus dans d'autres sessions | Jeux d'une seule session |
|---|---:|---:|
| GRU | 7.9 % | 0.0 % |
| régression logistique | 6.3 % | 4.7 % |
| gradient boosting | 24.4 % | 28.1 % |
| règles | 58.8 % | 45.3 % |

## Mode de facturation (GRU) : exactitude 88.7 %

- rappel `per_game` : 90.5 %
- rappel `time_based` : 88.9 %
- rappel `not_billed` : 85.5 %

## Effet des réglages (meilleur rappel de validation pour chaque valeur)

- GRU, `hidden` : 16 : 9.2 %, 32 : 7.3 %, 64 : 6.5 %
- GRU, `pos_weight` : False : 9.7 %, True : 7.5 %
- régression logistique, `class_weight` : None : 6.3 %, balanced : 4.9 %
- régression logistique, `window` : 0 : 4.4 %, 2 : 5.9 %
- gradient boosting, `class_weight` : None : 24.2 %, balanced : 25.9 %

## Tous les essais de réglages (rappel de validation sur les 25 tours)

### GRU

| Essai | `hidden` | `dropout` | `weight_decay` | `learning_rate` | `pos_weight` | Rappel moyen (min ; max) | Précision moyenne | Retenu |
|---:|---|---|---|---|---|---:|---:|---:|
| 12 | 16 | 0.1989 | 0.000198 | 0.00102 | False | 7.2 % (1.3 % ; 15.6 %) | 0.337 | 5 |
| 11 | 16 | 0.3557 | 0.000517 | 0.00163 | False | 7.2 % (0.4 % ; 15.8 %) | 0.345 | 7 |
| 10 | 32 | 0.1278 | 2.07e-05 | 0.000665 | True | 5.5 % (0.5 % ; 11.9 %) | 0.338 | 3 |
| 14 | 64 | 0.066 | 0.000827 | 0.0019 | True | 5.3 % (1.3 % ; 8.3 %) | 0.356 | 1 |
| 9 | 64 | 0.4727 | 0.000124 | 0.00276 | True | 5.3 % (1.9 % ; 7.9 %) | 0.371 | 1 |
| 7 | 32 | 0.2728 | 0.000177 | 0.000534 | True | 4.7 % (0.5 % ; 10.3 %) | 0.334 | 0 |
| 8 | 32 | 0.0107 | 8.81e-05 | 0.000353 | False | 4.6 % (0.0 % ; 10.3 %) | 0.171 | 5 |
| 4 | 16 | 0.111 | 2.97e-05 | 0.00255 | True | 4.0 % (0.0 % ; 12.1 %) | 0.365 | 1 |
| 3 | 16 | 0.4591 | 3.34e-05 | 0.00205 | True | 3.9 % (1.3 % ; 8.7 %) | 0.371 | 0 |
| 6 | 64 | 0.2437 | 7.08e-05 | 0.00132 | False | 3.5 % (0.4 % ; 9.6 %) | 0.242 | 1 |
| 15 | 32 | 0.4194 | 1.12e-05 | 0.000437 | False | 3.5 % (0.0 % ; 8.0 %) | 0.167 | 0 |
| 0 | 16 | 0.1728 | 0.000576 | 0.000914 | True | 3.3 % (0.4 % ; 7.0 %) | 0.349 | 0 |
| 1 | 64 | 0.3418 | 1.39e-05 | 0.00126 | False | 3.0 % (0.4 % ; 11.8 %) | 0.239 | 1 |
| 13 | 64 | 0.2864 | 4.77e-05 | 0.000734 | True | 2.5 % (0.4 % ; 5.7 %) | 0.294 | 0 |
| 5 | 32 | 0.4055 | 0.000418 | 0.00033 | False | 2.1 % (0.0 % ; 7.0 %) | 0.130 | 0 |
| 2 | 64 | 0.0555 | 0.000246 | 0.000468 | False | 1.9 % (0.0 % ; 4.5 %) | 0.185 | 0 |

### régression logistique

| Essai | `C` | `window` | `class_weight` | Rappel moyen (min ; max) | Précision moyenne | Retenu |
|---:|---|---|---|---:|---:|---:|
| 3 | 0.00842 | 2 | None | 5.3 % (1.3 % ; 10.3 %) | 0.415 | 14 |
| 6 | 4.46 | 0 | None | 4.0 % (0.5 % ; 10.3 %) | 0.278 | 5 |
| 5 | 0.228 | 2 | balanced | 3.4 % (0.0 % ; 7.9 %) | 0.333 | 2 |
| 2 | 0.956 | 0 | balanced | 3.4 % (0.5 % ; 8.6 %) | 0.204 | 1 |
| 7 | 0.0488 | 2 | balanced | 3.3 % (0.0 % ; 5.7 %) | 0.364 | 2 |
| 1 | 1.07 | 2 | None | 2.6 % (0.0 % ; 9.6 %) | 0.346 | 1 |
| 0 | 0.0117 | 0 | balanced | 1.1 % (0.0 % ; 3.5 %) | 0.227 | 0 |
| 4 | 0.00201 | 0 | None | 0.9 % (0.0 % ; 1.3 %) | 0.223 | 0 |

### gradient boosting

| Essai | `learning_rate` | `max_leaf_nodes` | `l2_regularization` | `class_weight` | Rappel moyen (min ; max) | Précision moyenne | Retenu |
|---:|---|---|---|---|---:|---:|---:|
| 3 | 0.05 | 31 | 0.1896 | balanced | 24.2 % (12.1 % ; 33.3 %) | 0.553 | 7 |
| 4 | 0.05 | 15 | 0.4366 | balanced | 22.2 % (13.5 % ; 33.3 %) | 0.548 | 3 |
| 2 | 0.1 | 15 | 0.5352 | None | 21.5 % (11.1 % ; 32.8 %) | 0.563 | 7 |
| 1 | 0.1 | 31 | 0.3469 | balanced | 21.4 % (10.5 % ; 30.7 %) | 0.548 | 1 |
| 6 | 0.1 | 15 | 0.0296 | balanced | 20.8 % (10.6 % ; 29.4 %) | 0.538 | 3 |
| 0 | 0.05 | 15 | 0.8802 | None | 20.3 % (9.6 % ; 38.3 %) | 0.565 | 4 |
| 5 | 0.1 | 31 | 0.837 | None | 19.2 % (11.1 % ; 31.3 %) | 0.551 | 0 |
| 7 | 0.05 | 31 | 0.7425 | None | 18.4 % (8.8 % ; 30.0 %) | 0.555 | 0 |


## Groupes de variables retirés (GRU)

- `counters` : retiré dans 12 tours sur 25, rappel de validation sans lui -0.9 points en moyenne
- `timers` : retiré dans 0 tours sur 25, rappel de validation sans lui -6.2 points en moyenne
- `changes` : retiré dans 0 tours sur 25, rappel de validation sans lui -7.0 points en moyenne
- `mode` : retiré dans 2 tours sur 25, rappel de validation sans lui -4.7 points en moyenne

Courbes d'apprentissage du GRU retenu : meilleure époque médiane 103.5, 40 courbes sur 100 où la perte de validation remonte de plus de 10 %.

Calcul total : 72.4 heures-processus. Machine : Windows-11-10.0.26300-SP0, 16 cœurs logiques, processeur seul, PyTorch 2.13.0.

## Figures

- [`figures/models.png`](figures/models.png) : rappel et fausses fins de chaque modèle sur les sessions tenues à l'écart, pour les trois seuils
- [`figures/precision_recall.png`](figures/precision_recall.png) : précision et rappel par événements selon le seuil, GRU et meilleur modèle de référence
- [`figures/learning_curves.png`](figures/learning_curves.png) : pertes d'entraînement et de validation du GRU retenu, dans chaque tour
- [`figures/trials.png`](figures/trials.png) : rappel de validation de chaque essai de réglages, par modèle
- [`figures/settings.png`](figures/settings.png) : meilleur rappel de validation obtenu avec chaque valeur d'un réglage étudié
- [`figures/ablation.png`](figures/ablation.png) : effet sur le rappel de validation du retrait de chaque groupe de variables
- [`figures/families.png`](figures/families.png) : fins trouvées et fausses fins par famille de jeu
- [`figures/billing.png`](figures/billing.png) : matrice de confusion du mode de facturation prédit par le GRU
- [`figures/sessions/`](figures/sessions/) : une figure par session tenue à l'écart : probabilité de fin, vraies fins, fins prédites
