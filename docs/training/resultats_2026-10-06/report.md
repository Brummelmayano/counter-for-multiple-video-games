# Résultats de l'entraînement

Sessions tenues à l'écart : 25. Chaque session est évaluée par des modèles qui ne l'ont jamais vue, au seuil choisi sur la validation de son propre tour. Une fin trouvée une capture en retard compte comme juste. Les intervalles entre crochets viennent du rééchantillonnage des sessions (95 %).

## Seuil choisi pour au plus 1 fausse(s) fin(s) pour 100 parties (validation)

| Modèle | Précision | Rappel | Fausses fins pour 100 parties | Fausses fins par heure |
|---|---:|---:|---:|---:|
| GRU | 90.8 % | 37.3 % [25.2 %; 52.3 %] | 3.8 | 0.16 |
| régression logistique | 70.6 % | 8.4 % [4.8 %; 14.5 %] | 3.5 | 0.15 |
| gradient boosting | 96.8 % | 42.5 % [36.7 %; 50.0 %] | 1.4 | 0.06 |
| règles | 63.3 % | 55.8 % [47.7 %; 63.4 %] | 32.3 | 1.35 |

## Seuil choisi pour au plus 2 fausse(s) fin(s) pour 100 parties (validation)

| Modèle | Précision | Rappel | Fausses fins pour 100 parties | Fausses fins par heure |
|---|---:|---:|---:|---:|
| GRU | 89.8 % | 40.2 % [27.4 %; 56.0 %] | 4.6 | 0.19 |
| régression logistique | 68.4 % | 9.1 % [5.2 %; 15.5 %] | 4.2 | 0.18 |
| gradient boosting | 97.2 % | 49.5 % [43.5 %; 56.9 %] | 1.4 | 0.06 |
| règles | 63.3 % | 55.8 % [47.7 %; 63.4 %] | 32.3 | 1.35 |

## Seuil choisi pour au plus 5 fausse(s) fin(s) pour 100 parties (validation)

| Modèle | Précision | Rappel | Fausses fins pour 100 parties | Fausses fins par heure |
|---|---:|---:|---:|---:|
| GRU | 86.3 % | 47.7 % [34.1 %; 64.9 %] | 7.6 | 0.32 |
| régression logistique | 82.1 % | 27.4 % [19.9 %; 36.0 %] | 6.0 | 0.25 |
| gradient boosting | 93.5 % | 60.4 % [54.9 %; 69.0 %] | 4.2 | 0.18 |
| règles | 63.3 % | 55.8 % [47.7 %; 63.4 %] | 32.3 | 1.35 |

Écart entre graines du GRU : rappel ± 1.0 %, précision ± 1.0 %.

GRU contre chaque autre modèle (Wilcoxon par session, premier seuil) :

- régression logistique : p = 0.000 pour le rappel, p = 0.596 pour les fausses fins
- gradient boosting : p = 0.906 pour le rappel, p = 0.121 pour les fausses fins
- règles : p = 0.205 pour le rappel, p = 0.001 pour les fausses fins

## Par famille de jeu (premier seuil)

Rappel, puis fausses fins par entraînement entre parenthèses (le GRU est la moyenne de ses graines).

| Famille | Fins | GRU | régression logistique | gradient boosting | règles |
|---|---:|---:|---:|---:|---:|
| (aucun jeu) | 0 | - | - | - (1) | - |
| Assassin's Creed Origins | 0 | - | - | - | - (3) |
| Beach Buggy Racing 2 | 27 | 1.5 % (0) | 0.0 % (0) | 37.0 % (0) | 22.2 % (0) |
| Brawlhalla | 1 | 100.0 % (0) | 0.0 % (0) | 100.0 % (0) | 100.0 % (0) |
| Call of Duty: Warzone | 12 | 60.0 % (0) | 25.0 % (0) | 41.7 % (0) | 33.3 % (5) |
| Demon Slayer | 1 | 80.0 % (0) | 0.0 % (0) | 0.0 % (0) | 100.0 % (0) |
| Dragon Ball FighterZ | 2 | 0.0 % (0) | 0.0 % (0) | 0.0 % (0) | 0.0 % (1) |
| Dragon Ball Sparking! ZERO | 21 | 59.0 % (1) | 14.3 % (0) | 52.4 % (0) | 33.3 % (4) |
| EA Sports FC | 77 | 48.8 % (4.8) | 9.1 % (1) | 45.5 % (2) | 57.1 % (16) |
| EA Sports UFC 5 | 11 | 34.5 % (0) | 9.1 % (0) | 18.2 % (0) | 36.4 % (2) |
| Fortnite | 27 | 55.6 % (2.8) | 29.6 % (0) | 48.1 % (0) | 88.9 % (9) |
| Genshin Impact | 0 | - | - | - | - (27) |
| God of War | 0 | - | - | - | - (2) |
| J-Stars Victory VS+ | 2 | 50.0 % (1) | 0.0 % (8) | 0.0 % (0) | 100.0 % (2) |
| Mortal Kombat 1 | 67 | 32.5 % (1.2) | 0.0 % (0) | 47.8 % (0) | 64.2 % (10) |
| Naruto Storm Connections | 6 | 66.7 % (0) | 33.3 % (0) | 50.0 % (0) | 66.7 % (1) |
| Red Dead Redemption 2 | 0 | - | - | - | - (9) |
| Tekken 8 | 31 | 3.9 % (0) | 0.0 % (1) | 29.0 % (1) | 61.3 % (1) |

Jeux joués dans une seule session (Beach Buggy Racing 2, Brawlhalla, Demon Slayer, Dragon Ball FighterZ, J-Stars Victory VS+, Tekken 8) : quand cette session est tenue à l'écart, le modèle n'a jamais vu le jeu.

| Modèle | Jeux vus dans d'autres sessions | Jeux d'une seule session |
|---|---:|---:|
| GRU | 46.1 % | 6.9 % |
| régression logistique | 10.9 % | 0.0 % |
| gradient boosting | 45.7 % | 31.2 % |
| règles | 58.8 % | 45.3 % |

## Mode de facturation (GRU) : exactitude 93.9 %

- rappel `per_game` : 93.9 %
- rappel `time_based` : 92.4 %
- rappel `not_billed` : 94.7 %

## Effet des réglages (meilleur rappel de validation pour chaque valeur)

- GRU, `hidden` : 16 : 27.1 %, 32 : 25.1 %, 64 : 30.0 %
- GRU, `pos_weight` : False : 31.1 %, True : 22.5 %
- régression logistique, `class_weight` : None : 6.3 %, balanced : 6.5 %
- régression logistique, `window` : 0 : 4.7 %, 2 : 7.4 %
- gradient boosting, `class_weight` : None : 36.4 %, balanced : 40.5 %

## Tous les essais de réglages (rappel de validation sur les 25 tours)

### GRU

| Essai | `hidden` | `dropout` | `weight_decay` | `learning_rate` | `pos_weight` | Rappel moyen (min ; max) | Précision moyenne | Retenu |
|---:|---|---|---|---|---|---:|---:|---:|
| 1 | 64 | 0.3418 | 1.39e-05 | 0.00126 | False | 27.9 % (19.7 % ; 35.8 %) | 0.594 | 7 |
| 6 | 64 | 0.2437 | 7.08e-05 | 0.00132 | False | 26.8 % (12.3 % ; 37.9 %) | 0.594 | 5 |
| 2 | 64 | 0.0555 | 0.000246 | 0.000468 | False | 25.0 % (13.6 % ; 34.5 %) | 0.542 | 4 |
| 11 | 16 | 0.3557 | 0.000517 | 0.00163 | False | 24.1 % (15.8 % ; 34.1 %) | 0.647 | 3 |
| 12 | 16 | 0.1989 | 0.000198 | 0.00102 | False | 24.1 % (15.8 % ; 37.5 %) | 0.648 | 3 |
| 15 | 32 | 0.4194 | 1.12e-05 | 0.000437 | False | 23.4 % (9.6 % ; 35.8 %) | 0.547 | 1 |
| 8 | 32 | 0.0107 | 8.81e-05 | 0.000353 | False | 20.3 % (5.7 % ; 31.9 %) | 0.510 | 1 |
| 5 | 32 | 0.4055 | 0.000418 | 0.00033 | False | 20.3 % (7.5 % ; 30.9 %) | 0.474 | 0 |
| 9 | 64 | 0.4727 | 0.000124 | 0.00276 | True | 18.0 % (4.6 % ; 30.5 %) | 0.606 | 0 |
| 0 | 16 | 0.1728 | 0.000576 | 0.000914 | True | 17.8 % (3.9 % ; 27.9 %) | 0.614 | 0 |
| 14 | 64 | 0.066 | 0.000827 | 0.0019 | True | 17.5 % (6.1 % ; 30.1 %) | 0.582 | 1 |
| 4 | 16 | 0.111 | 2.97e-05 | 0.00255 | True | 17.0 % (5.7 % ; 30.5 %) | 0.624 | 0 |
| 13 | 64 | 0.2864 | 4.77e-05 | 0.000734 | True | 16.7 % (7.5 % ; 25.0 %) | 0.554 | 0 |
| 3 | 16 | 0.4591 | 3.34e-05 | 0.00205 | True | 16.4 % (1.8 % ; 28.4 %) | 0.620 | 0 |
| 7 | 32 | 0.2728 | 0.000177 | 0.000534 | True | 14.5 % (3.5 % ; 24.0 %) | 0.580 | 0 |
| 10 | 32 | 0.1278 | 2.07e-05 | 0.000665 | True | 14.3 % (5.2 % ; 26.7 %) | 0.584 | 0 |

### régression logistique

| Essai | `C` | `window` | `class_weight` | Rappel moyen (min ; max) | Précision moyenne | Retenu |
|---:|---|---|---|---:|---:|---:|
| 3 | 0.00842 | 2 | None | 5.9 % (2.9 % ; 17.0 %) | 0.619 | 12 |
| 5 | 0.228 | 2 | balanced | 5.6 % (0.4 % ; 12.5 %) | 0.454 | 6 |
| 4 | 0.00201 | 0 | None | 4.0 % (1.3 % ; 7.4 %) | 0.282 | 1 |
| 6 | 4.46 | 0 | None | 3.5 % (0.4 % ; 9.6 %) | 0.299 | 2 |
| 1 | 1.07 | 2 | None | 3.5 % (0.4 % ; 13.5 %) | 0.469 | 2 |
| 7 | 0.0488 | 2 | balanced | 2.8 % (0.0 % ; 17.5 %) | 0.499 | 1 |
| 2 | 0.956 | 0 | balanced | 2.0 % (0.0 % ; 5.7 %) | 0.257 | 1 |
| 0 | 0.0117 | 0 | balanced | 1.2 % (0.0 % ; 6.5 %) | 0.292 | 0 |

### gradient boosting

| Essai | `learning_rate` | `max_leaf_nodes` | `l2_regularization` | `class_weight` | Rappel moyen (min ; max) | Précision moyenne | Retenu |
|---:|---|---|---|---|---:|---:|---:|
| 6 | 0.1 | 15 | 0.0296 | balanced | 37.9 % (20.4 % ; 50.4 %) | 0.748 | 13 |
| 4 | 0.05 | 15 | 0.4366 | balanced | 36.3 % (15.7 % ; 48.6 %) | 0.745 | 4 |
| 3 | 0.05 | 31 | 0.1896 | balanced | 33.6 % (7.4 % ; 46.0 %) | 0.730 | 0 |
| 1 | 0.1 | 31 | 0.3469 | balanced | 33.2 % (13.9 % ; 50.4 %) | 0.731 | 3 |
| 5 | 0.1 | 31 | 0.837 | None | 31.0 % (13.5 % ; 50.4 %) | 0.718 | 2 |
| 7 | 0.05 | 31 | 0.7425 | None | 30.8 % (13.5 % ; 50.2 %) | 0.715 | 1 |
| 2 | 0.1 | 15 | 0.5352 | None | 30.6 % (13.5 % ; 51.9 %) | 0.728 | 2 |
| 0 | 0.05 | 15 | 0.8802 | None | 28.7 % (14.0 % ; 48.1 %) | 0.727 | 0 |


## Groupes de variables retirés (GRU)

- `counters` : retiré dans 4 tours sur 25, rappel de validation sans lui -6.9 points en moyenne
- `timers` : retiré dans 2 tours sur 25, rappel de validation sans lui -8.0 points en moyenne
- `changes` : retiré dans 1 tours sur 25, rappel de validation sans lui -13.9 points en moyenne
- `mode` : retiré dans 1 tours sur 25, rappel de validation sans lui -9.8 points en moyenne

Courbes d'apprentissage du GRU retenu : meilleure époque médiane 95.0, 50 courbes sur 100 où la perte de validation remonte de plus de 10 %.

Calcul total : 68.8 heures-processus. Machine : Windows-11-10.0.26200-SP0, 16 cœurs logiques, processeur seul, PyTorch 2.14.1+cpu.

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
