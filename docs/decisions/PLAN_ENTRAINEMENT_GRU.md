# Plan d'entraînement et d'évaluation du GRU (proposition du 2026-10-05)

Proposition soumise à l'utilisateur avant tout calcul. Elle complète les décisions déjà prises
(`DECISIONS_ENTRAINEMENT_GRU.md`) et s'appuie sur la littérature citée en fin de document.

## 1. Ce que le modèle doit faire

Le GRU lit, session par session et dans l'ordre, les 262 variables de chaque image (`features.csv` du jeu de données
publié) et donne deux sorties à chaque image :

- `unit_end_boundary` : une partie s'est-elle terminée entre l'image précédente et celle-ci ?
- `billing_mode` : l'image est-elle facturée à la partie, au temps, ou pas du tout ?

Le modèle ne voit que le passé, comme sur le Raspberry Pi : un GRU à sens unique, remis à zéro au début de chaque
session.

Les données : 25 sessions, 8 871 images, 285 fins sur les 8 794 intervalles appris (environ 1 pour 30). Tout
l'entraînement part du paquet publié (`build/playend_v1.0`, identique au dépôt Zenodo à part les noms de fichiers),
pour que les résultats du mémoire se refassent à partir des données publiques.

## 2. Ce que l'essai du 4 octobre a appris

L'essai mis de côté (branche `essai/gru-v4-20261004`, 23 sessions, compteurs encore incomplets) n'est pas réutilisé,
mais il montre où se trouvent les difficultés :

- avec la règle « au plus une fausse fin pour 100 parties », le seuil est monté à 0,97–0,98 et le rappel est tombé à
  29 % (précision 78 %) ;
- Mortal Kombat 1 a donné 17 des 20 fausses fins : la fin d'un round ressemble à la fin d'un match ;
- aucune fin de Tekken n'a été trouvée ; les compteurs de rounds et de victoires, absents à l'époque, sont maintenant
  dans toutes les observations.

## 3. Protocole d'évaluation

Validation croisée imbriquée, par session :

- **boucle extérieure** : une session tenue à l'écart à chaque fois (25 tours). Chaque session est prédite une fois
  par un modèle qui ne l'a jamais vue. C'est ce que recommandent Roberts et al. (2017) quand les données sont
  groupées, et la pratique en reconnaissance d'activité (Gholamiangonabadi et al., 2020) ;
- **boucle intérieure** : sur les 24 sessions restantes, les plis de `splits.csv` servent à choisir le nombre d'époques
  (arrêt précoce), le seuil de décision et les hyperparamètres. Rien de ce qui est choisi ne voit la session tenue à
  l'écart : choisir sur les mêmes données que l'évaluation donne des scores trop optimistes (Cawley et Talbot,
  2010).

Les résultats publiés sont ceux des 25 sessions tenues à l'écart, mis en commun.

Ordre des opérations dans chaque tour, une session étant tenue à l'écart :

1. retirer les colonnes sans information, d'après les 24 sessions d'entraînement (section 7, niveau 1) ;
2. tirer les essais de réglages et les évaluer sur la boucle intérieure (section 9) ;
3. avec la configuration retenue, retirer un groupe de variables à la fois, toujours sur la boucle intérieure (section
   7, niveau 3) ;
4. réentraîner le modèle final sur les 24 sessions, avec les groupes gardés, 5 graines et le seuil choisi ;
5. prédire la session tenue à l'écart, une seule fois.

## 4. Comment on compte les fins

L'évaluation se fait par événements, pas image par image :

- des intervalles consécutifs au-dessus du seuil forment une seule fin prédite, placée sur le premier ;
- une fin prédite est juste si elle tombe sur l'intervalle de la vraie fin ou sur le suivant (une capture de retard,
  environ 28 s), comme les marges de tolérance utilisées pour la détection d'événements sonores (Mesaros et al.,
  2016) et de points de rupture (van den Burg et Williams, 2020) ;
- une fin prédite sans vraie fin correspondante est une fausse fin ; les intervalles masqués sont ignorés.

Mesures, au total et par famille de jeu :

- la précision (protection du client) et le rappel (recette de la salle) ;
- les fausses fins pour 100 parties et par heure de jeu ;
- la courbe précision-rappel complète, plus parlante que la courbe ROC quand les classes sont aussi déséquilibrées
  (Saito et Rehmsmeier, 2015) ;
- pour `billing_mode` : la matrice de confusion et le rappel de chaque classe ;
- enfin, le nombre de parties **facturées** par session, après les règles de facturation (relance de moins de 60 s,
  15 s pour les combats), comparé au vrai nombre.

L'exactitude seule n'est jamais donnée : « ne jamais détecter de fin » atteint 96,8 % et ne compte aucune partie.

## 5. Le seuil de décision

Le seuil retenu est le plus bas qui garde au plus une fausse fin pour 100 parties sur les sessions de validation
(décision du 2026-09-29). Comme cette règle a fait tomber le rappel de l'essai, les résultats montreront aussi ce que
donneraient 2 et 5 fausses fins pour 100 parties, pour que le choix commercial se fasse en connaissant le coût en
parties manquées.

## 6. Les modèles comparés

Un GRU ne vaut que par comparaison avec des méthodes plus simples :

1. la référence triviale (jamais de fin) ;
2. des règles écrites à la main sur les observations : score revenu à 0–0 après un score non nul, écran de résultat
   suivi d'un menu, nombre de joueurs restants qui remonte, changement de jeu ;
3. une régression logistique sur les variables de l'image et des deux précédentes ;
4. un gradient boosting sur les mêmes fenêtres : sur des données tabulaires de cette taille (environ 10 000 lignes),
   les arbres restent souvent devant les réseaux de neurones (Grinsztajn et al., 2022) ;
5. le GRU, modèle principal.

Le LSTM n'est pas ajouté : il fait jeu égal avec le GRU sur les tâches de séquences (Chung et al., 2014), et le GRU
est plus léger pour le Raspberry Pi. Les réseaux convolutifs temporels (Bai et al., 2018) restent une piste pour plus
tard.

## 7. Les variables d'entrée : ce qu'on garde

`features.csv` a 262 variables, calculées pour n'importe quel jeu prévu par le contrat d'observation. Sur PlayEnd,
beaucoup ne servent à rien. Analyse faite le 2026-10-05 sur les 8 871 images, sans regarder les étiquettes :

- **76 colonnes sont constantes** : scores du tennis (30), catégories jamais rencontrées (basket, tennis, mi-temps,
  sets, nul, KO technique…), minuteurs de recharge, emplacements de rounds par côté, série commune aux deux côtés ;
- **28 colonnes sont des copies exactes** d'une autre (par exemple les colonnes « connu » des minuteurs, toutes égales
  à `secondary.inventory_known`), et une est le complément exact d'une autre (`sequence_start` = 1 − `delta_t_s.known`) ;
- il reste **157 colonnes distinctes**. 18 d'entre elles ne s'écartent de leur valeur habituelle que sur 9 images ou
  moins (par exemple `result.outcome_type=ko`, 4 images).

Ce qu'on en fait, en trois niveaux :

1. **Retirer ce qui ne porte aucune information.** Les colonnes constantes, les copies et les compléments sont
   retirés dans chaque pli, d'après les seules sessions d'entraînement (quand une session est tenue à l'écart, 0 à 9
   colonnes de plus deviennent constantes). Ce tri n'utilise pas les étiquettes, donc il ne fausse pas l'évaluation.
   Il est utile pour un réseau de neurones, que les entrées sans information gênent davantage qu'un modèle à arbres
   (Grinsztajn et al., 2022). Le même tri s'applique à la régression logistique et au gradient boosting, pour que la
   comparaison reste juste. Le fichier publié reste entier ; la liste des colonnes gardées est enregistrée avec chaque
   modèle.
2. **Ne pas trier avec les étiquettes sur toutes les données.** Garder les colonnes les plus liées aux fins d'après un
   test statistique fait sur l'ensemble des données rend l'évaluation trop optimiste, même si l'on fait ensuite une
   validation croisée : le tri doit être refait dans chaque pli (Ambroise et McLachlan, 2002 ; Hastie et al., 2009,
   §7.10.2). On ne retire pas non plus une colonne parce qu'elle est très corrélée à une autre : deux variables très
   corrélées peuvent se compléter (Guyon et Elisseeff, 2003). `score.a.known` et `score.b.known`, par exemple,
   diffèrent justement quand un seul côté du score est lisible. Enfin, on garde les colonnes rares : les fins aussi
   sont rares, et un écran « KO », vu sur 4 images seulement, est précisément un indice de fin. La pénalité des poids
   et le dropout limitent ce que le modèle tire de ces colonnes.
3. **Mesurer l'utilité par groupe, pas colonne par colonne.** Dans la boucle intérieure, le GRU retenu est réentraîné
   sans un groupe de variables à la fois : minuteurs secondaires, compteurs de fin, variations et changements depuis
   l'image précédente, mode de jeu. Retirer un groupe et réentraîner est plus fiable que de mélanger ses valeurs, ce
   qui trompe quand les variables sont corrélées (Hooker et al., 2021). Un groupe qui n'améliore pas la validation est
   retiré, et le résultat est rapporté dans le mémoire.

Le bruit, lui, ne vient pas des colonnes : elles sont calculées sans hasard à partir des observations. Il viendrait
des erreurs de lecture des modèles professeurs, qu'aucun tri de colonnes n'enlève. La validation humaine de 576
observations tirées au hasard en donne la mesure. Sur les 36 réponses qui n'étaient pas « correct », il y avait :

- 14 noms de participants déduits (d'un logo, d'un visage) au lieu d'être écrits à l'écran, et 2 noms douteux dans
  Warzone : un écart à la règle « seulement le texte écrit », fixée pendant cette validation. 302 images ont ensuite
  été relues et 185 corrigées ;
- 12 places de course en écran partagé, marquées douteuses : la convention a été changée (place laissée vide) ;
- 2 périodes fausses dans UFC, corrigées ;
- 6 questions sans valeur fausse : sur les barres de vie de Dragon Ball, la jauge de J-Stars, le titre de God of War
  déduit des images voisines (laissé tel quel, et signalé comme limite), ou sans précision.

Les vraies erreurs de lecture d'une valeur affichée sont donc rares, et aucune ne touchait le score ou le chrono. Seules
185 observations de l'échantillon montrent un score et 232 un chrono (compté le 2026-10-08) : zéro erreur borne le taux
d'erreur, avec une confiance de 95 %, à environ 1,6 % pour le score et 1,3 % pour le chrono (règle de trois de Hanley
et Lippman-Hand, 1983 : 3/185 et 3/232 ; la première version de ce plan divisait à tort par les 576 observations). Les
étiquettes, elles, ont toutes été vérifiées à la main.

## 8. L'entraînement du GRU

- **Architecture** : une couche GRU à sens unique, puis deux têtes linéaires (fin de partie, mode de facturation).
  Les entrées sont les 262 variables publiées : transformation fixe et colonnes « valeur connue », que les réseaux
  récurrents savent exploiter (Lipton et al., 2016 ; Che et al., 2018).
- **Perte** : entropie croisée binaire pour la fin, limitée aux intervalles où `boundary_applicable` est vrai ;
  entropie croisée à trois classes pour le mode de facturation.
- **Déséquilibre** : deux variantes, départagées sur la boucle intérieure. La première n'applique aucune correction
  et ne fait que déplacer le seuil. La seconde pondère la perte des fins (`pos_weight` calculé sur les sessions
  d'entraînement seulement). Des corrections du déséquilibre peuvent dégrader les probabilités sans mieux séparer
  les classes, et déplacer le seuil donne souvent le même résultat (van den Goorbergh et al., 2022). Aucune image
  isolée n'est dupliquée.
- **Réglages** : taille de la couche, dropout, pénalité des poids, taux d'apprentissage, détaillés à la section 9.
  Arrêt précoce sur la validation (Prechelt, 1998).
- **Variabilité** : chaque modèle final est entraîné avec 5 graines différentes ; les résultats donnent la moyenne et
  l'écart.

## 9. Hyperparamètres et espace de recherche

Chaque modèle a ses réglages. Ceux qui sont fixés le sont pour une raison donnée ; les autres sont tirés au hasard
dans les plages ci-dessous et choisis sur la boucle intérieure seulement, jamais sur la session tenue à l'écart.

GRU :

| Réglage | Valeur ou plage | Pourquoi |
|---|---|---|
| Nombre de couches | 1 (fixé) | 285 fins seulement : un modèle plus profond surapprendrait ; un seul niveau tourne aussi plus vite sur le Pi |
| Sens | vers l'avant seulement (fixé) | le Pi ne connaît pas l'avenir |
| Taille de la couche cachée | 16, 32 ou 64 | du plus léger au plus expressif |
| Dropout en sortie du GRU | de 0 à 0,5 | régularisation |
| Pénalité des poids (weight decay) | de 10⁻⁵ à 10⁻³, échelle logarithmique | régularisation |
| Taux d'apprentissage (Adam) | de 3 × 10⁻⁴ à 3 × 10⁻³, échelle logarithmique | vitesse et stabilité de l'apprentissage |
| Pondération des fins | aucune, ou non-fins / fins des sessions d'entraînement | voir le déséquilibre ci-dessus |
| Lots | 4 sessions entières par pas, de longueurs proches (fixé) | l'état repart de zéro à chaque session ; voir ci-dessous |
| Époques | 300 au plus, arrêt après 30 époques sans progrès (fixé) | arrêt précoce sur la validation |
| Écrêtage du gradient | norme 1,0 (fixé) | évite les sauts du gradient dans les longues sessions |

Modèles de référence :

| Modèle | Réglage | Valeur ou plage |
|---|---|---|
| Régression logistique | régularisation C | de 10⁻³ à 10, échelle logarithmique |
| Régression logistique | fenêtre | image seule, ou image et 2 précédentes |
| Régression logistique | pondération des classes | aucune, ou inverse de la fréquence (`balanced`) |
| Gradient boosting | taux d'apprentissage | 0,05 ou 0,1 |
| Gradient boosting | feuilles par arbre | 15 ou 31 |
| Gradient boosting | régularisation L2 | de 0 à 1 |
| Gradient boosting | nombre d'arbres | arrêt précoce sur la validation |
| Gradient boosting | pondération des classes | aucune, ou inverse de la fréquence (`balanced`) |
| Règles écrites à la main | aucun réglage appris | fixées à l'avance, pour ne rien ajuster sur les données de test |

Les modèles de référence ont, comme le GRU, le choix entre pondérer les fins ou non : sans cela, la comparaison du
traitement du déséquilibre ne vaudrait que pour le GRU.

Une session est toujours lue en entier, mais le GRU en voit 4 à la fois à chaque pas d'apprentissage. Les sessions vont
de 3 à 1 184 images : mettre ensemble des sessions de longueur proche évite de calculer sur le rembourrage qui égalise
leurs longueurs, ce qui accélère l'entraînement sans changer ce que le modèle apprend (Khomenko et al., 2016 ; Doetsch
et al., 2017). Les longueurs sont légèrement brouillées et l'ordre des lots change à chaque époque, pour que les mêmes
sessions ne soient pas toujours ensemble. Mesuré sur cette machine : 0,80 s par époque, contre 1,07 s avec des lots
tirés au hasard. Le rembourrage est placé en fin de session : un GRU qui ne lit que vers l'avant n'en est pas influencé
sur les vraies images, et il est exclu des deux pertes.

Le seuil de décision n'est pas un hyperparamètre du modèle, mais il est choisi de la même façon, sur la boucle
intérieure (section 5).

### Rôle de chaque réglage

Suivant le Deep Learning Tuning Playbook de Google Research (Godbole et al., 2023), chaque réglage a un rôle :

- **réglages étudiés** : ceux dont on veut mesurer l'effet et rapporter le résultat dans le mémoire. Ce sont la
  famille de modèle (règles, régression logistique, gradient boosting, GRU), le traitement du déséquilibre
  (pondération ou non), la taille de la couche cachée et les groupes de variables gardés (section 7) ;
- **réglages de nuisance** : ceux qu'il faut optimiser pour que la comparaison des réglages étudiés soit juste. Ce sont
  le taux d'apprentissage, la pénalité des poids, le dropout, et la régularisation des modèles de référence ;
- **réglages fixés** : une couche, sens unique, sessions entières, plafond d'époques, patience, écrêtage. Les
  conclusions ne valent que pour ces valeurs, ce que le mémoire dira.

### Comment les essais sont tirés

Tous les réglages varient ensemble, tirés de façon quasi aléatoire dans leurs plages : 16 essais pour le GRU, 8 pour
chaque modèle de référence. On ne fait pas varier un réglage à la fois autour d'une configuration de départ : cette
méthode ne voit pas les interactions entre réglages (Czitrom, 1999), et la recherche aléatoire trouve aussi bien
qu'une grille pour beaucoup moins de calcul (Bergstra et Bengio, 2012). L'effet de chaque réglage est montré après
coup, à partir des mêmes essais (section 10).

### Comment le meilleur essai est choisi

Sur la boucle intérieure seulement, par le rappel des fins obtenu sous la contrainte d'au plus une fausse fin pour
100 parties ; à égalité, par la précision moyenne. L'arrêt précoce, lui, suit la perte de validation, plus régulière.
La configuration retenue est ensuite réentraînée avec 5 graines différentes, parce qu'une même configuration donne
des résultats différents d'une graine à l'autre (Bouthillier et al., 2021).

## 10. Journal des essais et analyses

Chaque entraînement est enregistré, qu'il soit retenu ou non, comme dans le « journal d'expériences » des laboratoires
de Google DeepMind (cours AI Research Foundations, lab 3.6) :

- la configuration complète, la graine, la session tenue à l'écart, le pli de validation et la liste des colonnes
  gardées (groupes retirés compris) ;
- les courbes d'apprentissage, c'est-à-dire la perte d'entraînement et de validation à chaque époque, et l'époque
  retenue par l'arrêt précoce ;
- les mesures de validation : précision moyenne, et seuil, rappel et fausses fins sous la contrainte ;
- la durée de l'entraînement.

Ce journal sert à trois choses, qu'un essai unique ne permettrait pas :

1. **Voir le surapprentissage.** Les courbes des meilleurs essais montrent si la perte de validation remonte, comme
   dans le laboratoire de DeepMind. Si c'est le cas, la régularisation est revue avant de comparer quoi que ce soit.
2. **Montrer l'effet de chaque réglage.** Pour chaque valeur d'un réglage étudié, on garde le meilleur essai sur les
   autres réglages (graphique d'isolement du Playbook). C'est une comparaison juste entre valeurs, sans refaire
   d'entraînement.
3. **Rendre compte honnêtement.** Le mémoire donne toutes les plages, le nombre d'essais, la façon de choisir, et les
   résultats de validation de tous les essais, et non le seul meilleur. C'est ce que demandent la liste de contrôle
   de reproductibilité de NeurIPS (Pineau et al., 2021) et Dodge et al. (2019).

Les poids des modèles ne sont gardés que pour les modèles retenus. Les essais de la boucle intérieure ne voient
jamais la session tenue à l'écart : le journal peut donc être analysé librement sans fausser l'évaluation finale.

## 11. Comparer honnêtement

Les mesures sont aussi calculées session par session. Le GRU et le meilleur modèle de référence sont comparés par le
test des rangs signés de Wilcoxon sur les sessions (Demšar, 2006), et les intervalles de confiance sont obtenus par
rééchantillonnage des sessions entières.

## 12. Ce qui sera produit

- un module `src/playend/training/` (lecture du paquet, modèles, évaluation par événements, protocole), lancé par
  `python -m playend.training…`. Il est dans le paquet `playend`, comme les autres étapes, pour en réutiliser le code
  (`playend.common`, `playend.dataset`) ;
- les résultats dans `build/` et un rapport de synthèse pour le mémoire ;
- le modèle final, avec l'empreinte de `feature_spec.json` et la liste des colonnes gardées, pour refuser des entrées
  d'une autre version ou dans un autre ordre.

Dépendances : l'option `train` du paquet (`pip install -e ".[train]"`), après avoir installé PyTorch dans la version qui
convient à la machine. Le mode d'emploi, pour une autre machine aussi, est dans `docs/training/README.md`.

Temps de calcul : le modèle est petit (quelques dizaines de milliers de paramètres) et la machine a 4 cœurs sans
carte graphique. Le protocole complet représente environ 2 200 entraînements du GRU : 25 sessions × 4 plis × 16
essais pour les réglages, 25 × 4 × 4 groupes pour le retrait des variables (plus les groupes retirés ensemble), et
5 graines pour chaque modèle retenu. Mesuré avec l'essai `--quick` (3 entraînements en parallèle) : 1,5 s par
époque et par entraînement. Avec une centaine d'époques par entraînement en moyenne (arrêt précoce), cela fait
environ 30 heures sur cette machine ; sur une machine avec GPU, la durée se mesure avec le même essai. Si elle est
trop longue, la boucle extérieure passera aux 5 plis de `splits.csv`, ce qui reste une validation croisée imbriquée
par session.

## 13. Limite à garder en tête

Les observations d'entrée viennent des modèles professeurs. Sur le Pi, elles viendront du petit modèle distillé, qui
fera plus d'erreurs de lecture : ces résultats sont une borne haute. L'évaluation sera refaite avec ses sorties
(décision du 2026-09-29).

## Sources

- Ambroise, C., McLachlan, G. J. (2002). *Selection bias in gene extraction on the basis of microarray
  gene-expression data*. PNAS 99(10), 6562–6566. doi:10.1073/pnas.102102699
- Bai, S., Kolter, J. Z., Koltun, V. (2018). *An Empirical Evaluation of Generic Convolutional and Recurrent Networks
  for Sequence Modeling*. arXiv:1803.01271.
- Bergstra, J., Bengio, Y. (2012). *Random Search for Hyper-Parameter Optimization*. JMLR 13, 281–305.
- Cawley, G. C., Talbot, N. L. C. (2010). *On Over-fitting in Model Selection and Subsequent Selection Bias in
  Performance Evaluation*. JMLR 11, 2079–2107.
- Bouthillier, X. et al. (2021). *Accounting for Variance in Machine Learning Benchmarks*. Proceedings of Machine
  Learning and Systems 3 (MLSys 2021). arXiv:2103.03098.
- Che, Z. et al. (2018). *Recurrent Neural Networks for Multivariate Time Series with Missing Values*. Scientific
  Reports 8, 6085. doi:10.1038/s41598-018-24271-9
- Chung, J., Gulcehre, C., Cho, K., Bengio, Y. (2014). *Empirical Evaluation of Gated Recurrent Neural Networks on
  Sequence Modeling*. arXiv:1412.3555.
- Czitrom, V. (1999). *One-Factor-at-a-Time Versus Designed Experiments*. The American Statistician 53(2), 126–131.
- Demšar, J. (2006). *Statistical Comparisons of Classifiers over Multiple Data Sets*. JMLR 7, 1–30.
- Dodge, J., Gururangan, S., Card, D., Schwartz, R., Smith, N. A. (2019). *Show Your Work: Improved Reporting of
  Experimental Results*. EMNLP-IJCNLP 2019. aclanthology.org/D19-1224
- Doetsch, P., Golik, P., Ney, H. (2017). *A Comprehensive Study of Batch Construction Strategies for Recurrent
  Neural Networks in MXNet*. arXiv:1705.02414.
- Gholamiangonabadi, D., Kiselov, N., Grolinger, K. (2020). *Deep Neural Networks for Human Activity Recognition
  With Wearable Sensors: Leave-One-Subject-Out Cross-Validation for Model Selection*. IEEE Access 8, 133982–133994.
  doi:10.1109/ACCESS.2020.3010715
- Godbole, V., Dahl, G. E., Gilmer, J., Shallue, C. J., Nado, Z. (2023). *Deep Learning Tuning Playbook*, version
  1.0. Google Research. github.com/google-research/tuning_playbook
- Google DeepMind. *AI Research Foundations*, cours 3, laboratoire 3.6 « Mitigate Overfitting » (journal
  d'expériences, dropout, pénalité des poids, arrêt précoce). github.com/google-deepmind/ai-foundations
- Grinsztajn, L., Oyallon, E., Varoquaux, G. (2022). *Why do tree-based models still outperform deep learning on
  typical tabular data?* NeurIPS 2022. arXiv:2207.08815.
- Guyon, I., Elisseeff, A. (2003). *An Introduction to Variable and Feature Selection*. JMLR 3, 1157–1182.
- Hanley, J. A., Lippman-Hand, A. (1983). *If Nothing Goes Wrong, Is Everything All Right? Interpreting Zero
  Numerators*. JAMA 249(13), 1743–1745.
- Hastie, T., Tibshirani, R., Friedman, J. (2009). *The Elements of Statistical Learning*, 2e éd., Springer,
  §7.10.2 « The Wrong and Right Way to Do Cross-validation ».
- Hooker, G., Mentch, L., Zhou, S. (2021). *Unrestricted permutation forces extrapolation: variable importance
  requires at least one more model, or there is no free variable importance*. Statistics and Computing 31, 82.
  doi:10.1007/s11222-021-10057-z
- Khomenko, V., Shyshkov, O., Radyvonenko, O., Bokhan, K. (2016). *Accelerating Recurrent Neural Network Training
  Using Sequence Bucketing and Multi-GPU Data Parallelization*. IEEE First International Conference on Data Stream
  Mining & Processing (DSMP). arXiv:1708.05604.
- Lipton, Z. C., Kale, D., Wetzel, R. (2016). *Directly Modeling Missing Data in Sequences with RNNs: Improved
  Classification of Clinical Time Series*. Proceedings of the 1st Machine Learning for Healthcare Conference (PMLR 56).
- Mesaros, A., Heittola, T., Virtanen, T. (2016). *Metrics for Polyphonic Sound Event Detection*. Applied Sciences
  6(6), 162. doi:10.3390/app6060162
- Pineau, J. et al. (2021). *Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019
  Reproducibility Program)*. JMLR 22(164), 1–20.
- Prechelt, L. (1998). *Early Stopping, But When?* In *Neural Networks: Tricks of the Trade*, Springer.
- Roberts, D. R. et al. (2017). *Cross-validation strategies for data with temporal, spatial, hierarchical, or
  phylogenetic structure*. Ecography 40(8), 913–929. doi:10.1111/ecog.02881
- Saito, T., Rehmsmeier, M. (2015). *The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating
  Binary Classifiers on Imbalanced Datasets*. PLoS ONE 10(3), e0118432.
- van den Burg, G. J. J., Williams, C. K. I. (2020). *An Evaluation of Change Point Detection Algorithms*.
  arXiv:2003.06222.
- van den Goorbergh, R., van Smeden, M., Timmerman, D., Van Calster, B. (2022). *The harm of class imbalance
  corrections for risk prediction models: illustration and simulation using logistic regression*. JAMIA 29(9),
  1525–1534. doi:10.1093/jamia/ocac093
