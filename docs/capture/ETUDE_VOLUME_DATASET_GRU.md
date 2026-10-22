# Dimensionnement du dataset temporel GRU

Recherche et inspection du projet : 22 septembre 2026.

## Recommandation adaptée au projet

Il n’existe pas de seuil universel de lignes pour entraîner un GRU ni de maximum
universel. Les chiffres ci-dessous sont un budget de collecte proposé pour une
première version couvrant environ trois à cinq titres, et non des seuils prouvés
par les publications. Une courbe d’apprentissage et des tests sur des sessions
indépendantes devront confirmer si ce budget suffit.

Une ligne désigne ici une observation horodatée issue d’une capture, avec ses
caractéristiques extraites et une étiquette temporelle vérifiée. Une fenêtre
construite à partir de ces lignes n’est pas une nouvelle partie indépendante.

| Palier | Observations du corpus complet | Usage proposé | Heures à 27,5 s en moyenne |
|---|---:|---|---:|
| Exploratoire | 2 000–5 000 | Vérifier annotation, extraction, entraînement et premiers échecs | 15–38 |
| Premier budget de collecte | 10 000 | Première comparaison sur un périmètre limité | 76 |
| Objectif principal | 20 000–30 000 | Développer une première version multi-jeux | 153–229 |
| Extension conditionnelle | 50 000 et plus | Couvrir les lacunes ou améliorer une validation encore sensible aux données | 382 et plus |

Les heures sont des ordres de grandeur : N × 27,5 / 3 600. Elles supposent la
réception continue d’images et la cadence uniforme choisie entre 10 et 45 secondes.
Les interruptions, échecs de capture et temps de préparation peuvent augmenter la
durée nécessaire. Ces intervalles sont simulés et ne mesurent pas le futur VLM.

Ces volumes incluent entraînement, validation et test. À titre de planification,
30 000 observations peuvent être réparties approximativement en 21 000 pour
l’entraînement, 4 500 pour la validation et 4 500 pour le test. La séparation doit
respecter les sessions, même si cela empêche d’atteindre exactement ces proportions.

## État effectivement constaté dans le projet

- GRU à une couche, dimension cachée 16, sortie binaire.
- Variante de base : 132 entrées, 7 217 paramètres.
- Variante enrichie : 136 entrées, 7 409 paramètres.
- Pilote d’entraînement : 33 observations d’une session, 27 positions évaluées,
  dont six frontières positives.
- Le rapport d’entraînement annonce explicitement que ses métriques sont calculées
  sur les données d’entraînement et ne mesurent pas la généralisation.
- Le dataset heldout synthétique contient 69 observations et six frontières
  positives. Il ne remplace pas une évaluation sur des sessions filmées réelles.

Sources locales :
`archive/gru-pilot-2026-09/Memoire_GRU_Reproduction/code/train_gru_variants.py`,
`datasets/03_gru_features_v2/gru_feature_spec_v2.json`,
`reproduced/02_training/gru_pilot_results_reproduced.json` dans le même paquet.

Le nombre de paramètres décrit le modèle actuel ; il ne fournit pas une formule
permettant de déduire automatiquement le nombre d’observations nécessaire.

## Pourquoi le nombre de parties compte davantage que le seul nombre de lignes

Un match qui dure dix minutes produit environ 600 / 27,5 = 22 observations de
gameplay. Une partie de trois minutes en produit environ sept. Ce sont des exemples
de durées, pas des mesures des jeux de l’utilisateur. Les menus et transitions
ajoutent aussi des lignes. Une collecte dominée par les matchs longs aura beaucoup
de lignes et relativement peu de fins de partie.

Le budget peut être construit comme suit :

N ≈ nombre de titres × parties annotées par titre × observations moyennes par partie.

Exemple de planification : cinq titres × 300 parties × 20 observations, transitions
comprises en moyenne, donne 30 000 observations et 1 500 fins réelles à annoter.
Les 300 parties par titre constituent un objectif pratique proposé, non un minimum
statistique validé. À 70/15/15, cela donne environ 210 parties d’entraînement et
45 de validation et de test par titre : suffisant pour un premier bilan, mais pas
pour affirmer un très faible taux d’erreur par jeu avec une grande précision.

Il faut suivre séparément le nombre de lignes, de parties, de sessions, de titres
et de scénarios. Il faut aussi diversifier joueurs, adversaires, jours de collecte
et conditions d’affichage. Des milliers d’images corrélées ne remplacent pas cette
diversité. Une session doit contenir des enchaînements de plusieurs parties.

Les cas rares imposent des collectes ciblées : KO précoce, prolongation, abandon,
revanche avec les mêmes participants, changement de jeu, lecture VLM erronée,
interruption du signal. Si un scénario survient dans 1 % des parties, 300 parties
n’en fournissent que trois en moyenne. Ce calcul illustre pourquoi le budget total
ne garantit pas la couverture de toutes les situations.

## Annotation et évaluation

La cible actuelle `unit_end_boundary` indique qu’au moins une unité comptable s’est
terminée depuis l’observation précédente. La spécification suppose au plus une fin
entre deux observations. Si deux parties peuvent finir dans un même intervalle,
la cible binaire ne permet pas de restituer un compte égal à deux : il faudra revoir
la cible ou le protocole, et pas seulement ajouter des données.

Une référence indépendante, idéalement une vidéo complète ou un relevé vérifiable,
est nécessaire pour annoter les fins survenues entre les captures. Le VLM produit
les variables d’entrée ; ses réponses ne doivent pas servir seules de vérité terrain
pour décider qu’une partie s’est terminée. Conserver ses erreurs et valeurs inconnues
dans les entrées permet de tester le système tel qu’il fonctionnera réellement.

Séparer les sessions avant de créer des fenêtres ou des variantes. Conserver l’ordre
temporel à l’intérieur des séquences. Calculer la normalisation uniquement sur
l’entraînement et réinitialiser l’état du GRU aux vraies limites de séquence.
Pour revendiquer une adaptation à des titres nouveaux, prévoir aussi un essai où
un titre entier n’apparaît jamais pendant l’entraînement.

Mesurer le rappel des fins, la précision des détections, les faux comptages, les
parties manquées, le retard de détection et l’erreur de compte par session. Donner
les résultats par jeu et des incertitudes calculées en regroupant par sessions.
Une accuracy globale élevée peut masquer un modèle qui annonce rarement une fin.
Les métriques de précision/rappel sont adaptées à l’examen de la classe rare [4].

## Comment décider d’arrêter la collecte

Conserver un ensemble de validation composé de sessions indépendantes et un test
final séparé. Comparer des entraînements utilisant par exemple 1 000, 2 000, 5 000,
10 000 et 20 000 lignes d’entraînement, ajoutées par sessions entières en préservant
la diversité des jeux. Répéter avec plusieurs initialisations et sous-ensembles
de sessions pour ne pas confondre un gain réel et la variabilité d’un essai.

Observer les courbes de validation et les erreurs par scénario. Si elles s’améliorent
encore nettement avec plus de parties, poursuivre la collecte. Si elles stagnent,
examiner la qualité des labels, les erreurs VLM, les variables manquantes et la cible
avant de collecter davantage de scènes semblables. Un plateau n’est pas une preuve
que le système est assez bon ; il peut révéler une limite des observations ou du modèle.
Les critères de performance souhaités doivent être fixés avec l’usage du compteur.
Le test final reste réservé à l’évaluation du choix arrêté.

Aucune limite à 50 000 lignes : 100 000 ou davantage restent possibles si leur apport
le justifie. À architecture fixée, augmenter le corpus d’entraînement n’augmente pas
le nombre de paramètres du GRU déployé. L’entraînement se fait sur le PC, avec un
chargement par lots/séquences adapté ; le script pilote qui charge tout en une seule
séquence doit évoluer pour les nombreuses sessions réelles.

## Ce que les références soutiennent, et ce qu’elles ne soutiennent pas

Les travaux sur les courbes d’apprentissage justifient de mesurer l’effet du nombre
d’exemples et d’ajuster le budget aux résultats. Ils n’établissent pas les seuils de
10 000 ou 30 000 lignes pour ce compteur [1, 2]. La documentation sur la validation
par groupes soutient la séparation de sessions corrélées [3]. Les résultats de
Dehghani et al. concernent des capteurs de mouvement ; ils illustrent un risque de
validation avec des fenêtres corrélées, pas une taille transférable à notre GRU [5].

1. Hoiem et al., **Learning Curves for Analysis of Deep Networks**, ICML 2021 :
   https://proceedings.mlr.press/v139/hoiem21a.html
2. Hestness et al., **Deep Learning Scaling is Predictable, Empirically**, 2017 :
   https://arxiv.org/abs/1712.00409
3. scikit-learn, **Cross-validation — grouped data** :
   https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data
4. Saito et Rehmsmeier, **The Precision-Recall Plot Is More Informative than the ROC
   Plot When Evaluating Binary Classifiers on Imbalanced Datasets**, PLOS ONE, 2015 :
   https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432
5. Dehghani et al., **A Quantitative Comparison of Overlapping and Non-Overlapping
   Sliding Windows for Human Activity Recognition Using Inertial Sensors**, 2019 :
   https://pmc.ncbi.nlm.nih.gov/articles/PMC6891351/
6. scikit-learn, **Learning curve** :
   https://scikit-learn.org/stable/modules/learning_curve.html#learning-curve
