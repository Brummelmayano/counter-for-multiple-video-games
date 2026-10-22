# Détecteurs de débuts appris : protocole de comparaison (étape 3, 15 octobre 2026)

Étape 3 de `docs/decisions/PLAN_COMPTAGE_PAR_DEBUT.md`, lancée sur accord de l'auteur le 2026-10-14. Le code est dans
`src/playend/training/starts/` ; le rapport s'écrit dans `build/training/starts_2026-10-15/RAPPORT.md`.

## La question

Le compteur par règles (`src/playend/counting/starts.py`) trouve 307 des 308 parties avec les observations du
professeur et 86,0 % avec celles de l'élève, pour 2,3 parties en trop sur 100. Ces chiffres sont mesurés sur les 25
sessions qui ont servi à écrire les règles : ils sont optimistes. La question est double : un modèle appris fait-il
mieux que les règles, et combien valent les uns et les autres sur des sessions qu'ils n'ont pas vues ?

## Pourquoi une validation croisée imbriquée, par session

Le 6 octobre, les détecteurs de fins ont été évalués de la même façon (`docs/decisions/PLAN_ENTRAINEMENT_GRU.md`, §3),
pour deux raisons qui valent encore ici.

- Les captures d'une même session ne sont pas indépendantes : mêmes joueurs, mêmes jeux, mêmes écrans à quelques
  secondes d'écart. Couper au hasard entre les captures mettrait des morceaux de la même partie dans l'entraînement et
  dans le test, et la mesure serait trop belle. On coupe donc par sessions entières (Roberts et al., 2017).
- Choisir les réglages et le seuil sur les données qui servent aussi à la mesure donne des scores trop optimistes
  (Cawley et Talbot, 2010 ; Varma et Simon, 2006). Avec peu de données, l'écart est grand même à 1 000 exemples,
  alors qu'une validation croisée imbriquée reste juste (Vabalas et al., 2019). Nous avons 308 débuts.

Boucle extérieure : les 5 plis figés de PlayEnd (`docs/dataset/folds.json`). Chaque session est prédite une seule
fois, par un modèle entraîné sans son pli. Boucle intérieure : sur les 4 autres plis, chacun mis de côté à son tour,
on essaie 8 réglages tirés par une suite de Sobol, on choisit le seuil et le meilleur réglage ; le modèle final est
entraîné sur les 4 plis et prédit le pli extérieur une fois. Le pli extérieur ne sert à aucun choix.

## Ce qui est comparé

| Méthode | Ce qu'elle voit | Pourquoi |
|---|---|---|
| Règles | l'observation, avec les règles écrites à la main | la référence |
| Règles, seuils choisis par validation croisée | idem ; 81 réglages de 4 seuils, choisis sur la boucle intérieure | le témoin : un modèle appris doit faire mieux que des règles mieux réglées |
| Gradient boosting, image | les 262 variables de l'image et des 2 précédentes | un modèle sans connaissance du jeu |
| Gradient boosting, état | l'état de la partie que tiennent les règles (valeurs lues, ruptures, écrans de fin vus, âge de la dernière lecture) et les 262 variables | les « variables portées » du plan |
| … avec étiquette étalée | les 1 à 3 premières captures lisibles de la partie marquées comme début | dilatation des étiquettes (Hong et al., 2022), forme simple de la perte de Cioppa et al. (2020) |
| … avec la fin en appui | la probabilité de fin des 3 dernières captures, donnée par un second modèle | début et fin estimés à part, comme BSN (Lin et al., 2018) ; empilement hors pli (Wolpert, 1992 ; Ting et Witten, 1999) |
| … avec les décisions des règles | l'état et ce que les règles ont décidé | empilement sur les règles |
| Fin depuis la dernière lecture, puis début | la probabilité de début et la plus haute probabilité de fin depuis la capture lisible précédente, moyennées | l'idée de l'auteur du 2026-10-15 : une fin suivie d'un début forme un signal plus fort ; règle de la somme (Kittler et al., 1998) ; apparier les bords comme BMN (Lin et al., 2019) |
| Règles + modèle | les règles proposent, le modèle « état, étiquette étalée » garde ou écarte, et ajoute ce que les règles ratent | une cascade : des propositions à haut rappel, puis un tri |
| GRU | les captures porteuses seulement, une sortie pour le début et une pour la fin | le modèle de séquence du plan |

Le gradient boosting passe d'abord : sur des tableaux de cette taille, les arbres font en général mieux que les
réseaux (Grinsztajn et al., 2022). Le GRU ne lit que les captures porteuses, avec le temps écoulé depuis la
précédente, comme le prévoit le plan (GRU-D, Che et al., 2018).

Une précaution : seule la variante « décisions des règles » reçoit ce que les règles ont décidé. Les règles ont été
écrites en lisant toutes les sessions ; un modèle nourri de leurs décisions hérite de ce regard sur son pli de test.
Les variables d'état viennent aussi de la logique des règles (profils de jeux, grandeurs qui ne font que monter) :
c'est une connaissance du domaine, écrite en lisant les mêmes sessions, et la mesure sur des sessions jamais vues
(prévue après cette étape) est la seule qui la juge vraiment.

## L'idée « une fin, puis un début » (15 octobre)

L'auteur propose de lire ensemble les deux courbes : sauf pour la première partie d'une session, une partie commence
après qu'une autre a fini, et la fin suivie du début forme un signal plus fort que chacun seul. L'écart entre les deux
varie : dans PlayEnd 1.1, sur 286 enchaînements, la fin et le début suivant tombent sur la même capture 114 fois (le
nouveau match apparaît directement, sans écran de fin), à 1 ou 2 captures 59 fois, à 3 à 10 captures 79 fois et à
plus de 10 captures 34 fois (médiane 39 s, 90 % sous 5 min). Entre les deux viennent, selon les cas, rien du tout,
l'écran d'après-match, les menus, la sélection, le chargement ou un long temps mort. La fenêtre de trois captures de la
variante « fin en appui » ne voit donc pas 40 % de ces entre-deux ; la nouvelle variante prend tout l'entre-deux, de la
capture qui suit la dernière lecture de jeu jusqu'au début possible, comme on traite l'intervalle entre deux phases de
jeu dans le découpage « jeu / arrêt » des vidéos de sport (Ekin et Tekalp, 2003).

Un essai hors pli, avec des réglages fixes (`build/training/starts_2026-10-15/` n'en dépend pas), a donné :

- au niveau de la capture, la fin dans l'entre-deux désigne beaucoup mieux la première capture d'une partie : précision
  moyenne de 0,55 à 0,93 avec le professeur, de 0,65 à 0,87 avec l'élève ;
- au niveau du compte, le gain est faible : avec l'élève et 2 parties en trop pour 100, 70,5 % trouvées au lieu de
  69,5 % ; avec 5, 79,5 % au lieu de 76,0 % ;
- ajoutée aux règles pour retrouver des parties et écarter des débuts douteux, elle ne fait pas mieux que les règles
  seules (86,0 % et 2,3 en trop pour 100).

Deux raisons. Les règles font déjà ce raisonnement : un écran de fin vu depuis la dernière lecture fait compter
l'ouverture suivante, et l'état de la partie le donne aux modèles. Et dans 40 % des enchaînements, la fin n'est
prouvée que par le début du match suivant : fin et début sont alors le même indice, l'un ne peut pas confirmer l'autre.
Avec l'élève, 6 des 7 parties comptées en trop par les règles n'ont aucun indice de fin dans l'entre-deux qui les précède,
mais 49 vrais débuts non plus. La variante est mesurée dans le protocole complet pour que le mémoire en ait le chiffre.

## Comment on compte

- **Les débuts.** Un modèle donne une probabilité sur chaque capture lisible. Un début est une capture au-dessus du
  seuil, plus haute que la capture lisible d'avant et que celle d'après, une suppression des non-maxima sur une
  capture comme dans E2E-Spot (Hong et al., 2022). Le début est décidé à la capture lisible suivante.
- **L'appariement.** Une partie de référence est trouvée par le premier début libre qui tombe dedans, ou jusqu'à deux
  captures avant sa première capture, la règle déjà utilisée pour le compteur. Les autres débuts sont des parties en
  trop, les plus coûteuses pour le client.
- **Le seuil.** Le plus bas qui garde au plus 1, 2 ou 5 parties en trop pour 100 sur les sessions de validation : on
  borne l'erreur coûteuse et on réduit l'autre, comme en classification de Neyman-Pearson (Tong et al., 2018). Tong
  et al. montrent qu'une borne respectée sur la validation peut être dépassée au test ; le rapport donne donc la
  valeur mesurée au test, pas celle visée.
- **Les mesures.** Parties trouvées, parties en trop pour 100, précision, sessions au compte exact, retard de
  décision. Intervalles à 95 % par rééchantillonnage des sessions entières (bootstrap par grappes, Field et Welsh,
  2007). Chaque méthode est comparée aux règles session par session par le test des rangs signés de Wilcoxon sur les
  erreurs (parties manquées et en trop), comme le recommande Demšar (2006).

## Exécution

```bash
python -m playend.training.starts.run --out build/training/starts_2026-10-15             # tout, environ 3 h
python -m playend.training.starts.run --out build/training/starts_quick --quick           # vérification, 6 min
```

Deux sources : le professeur (`build/playend_v1.1`) et l'élève (`build/student/packages/student_v1.1_final`).
Chaque morceau de travail (une méthode, un pli extérieur, une source) écrit son résultat dans `results/` quand il est
fini ; relancer la même commande reprend là où le calcul s'est arrêté. Le rapport est réécrit après chaque étape
(règles, gradient boosting, cascade, GRU) : un calcul interrompu laisse les résultats des étapes finies.

## Sources

- Cawley, G. C., Talbot, N. L. C. (2010). *On Over-fitting in Model Selection and Subsequent Selection Bias in
  Performance Evaluation*. JMLR 11, 2079–2107.
- Che, Z. et al. (2018). *Recurrent Neural Networks for Multivariate Time Series with Missing Values*. Scientific
  Reports 8, 6085.
- Cioppa, A. et al. (2020). *A Context-Aware Loss Function for Action Spotting in Soccer Videos*. CVPR.
- Demšar, J. (2006). *Statistical Comparisons of Classifiers over Multiple Data Sets*. JMLR 7, 1–30.
- Field, C. A., Welsh, A. H. (2007). *Bootstrapping clustered data*. Journal of the Royal Statistical Society B 69(3),
  369–390. doi:10.1111/j.1467-9868.2007.00593.x
- Ekin, A., Tekalp, A. M. (2003). *Generic play-break event detection for summarization and hierarchical sports video
  analysis*. ICME 2003. doi:10.1109/ICME.2003.1220881
- Grinsztajn, L., Oyallon, E., Varoquaux, G. (2022). *Why do tree-based models still outperform deep learning on
  typical tabular data?* NeurIPS 2022. arXiv:2207.08815.
- Hong, J., Zhang, H., Gharbi, M., Fisher, M., Fatahalian, K. (2022). *Spotting Temporally Precise, Fine-Grained
  Events in Video*. ECCV 2022. arXiv:2207.10213.
- Kittler, J., Hatef, M., Duin, R. P. W., Matas, J. (1998). *On combining classifiers*. IEEE TPAMI 20(3), 226–239.
- Lin, T. et al. (2018). *BSN: Boundary Sensitive Network for Temporal Action Proposal Generation*. ECCV.
- Lin, T., Liu, X., Li, X., Ding, E., Wen, S. (2019). *BMN: Boundary-Matching Network for Temporal Action Proposal
  Generation*. ICCV 2019, 3889–3898. arXiv:1907.09702.
- Roberts, D. R. et al. (2017). *Cross-validation strategies for data with temporal, spatial, hierarchical, or
  phylogenetic structure*. Ecography 40(8), 913–929.
- Ting, K. M., Witten, I. H. (1999). *Issues in Stacked Generalization*. Journal of Artificial Intelligence Research
  10, 271–289.
- Tong, X., Feng, Y., Li, J. J. (2018). *Neyman-Pearson classification algorithms and NP receiver operating
  characteristics*. Science Advances 4(2), eaao1659. doi:10.1126/sciadv.aao1659
- Vabalas, A., Gowen, E., Poliakoff, E., Casson, A. J. (2019). *Machine learning algorithm validation with a limited
  sample size*. PLoS ONE 14(11), e0224365. doi:10.1371/journal.pone.0224365
- Varma, S., Simon, R. (2006). *Bias in error estimation when using cross-validation for model selection*. BMC
  Bioinformatics 7, 91.
- Wolpert, D. H. (1992). *Stacked generalization*. Neural Networks 5(2), 241–259.
