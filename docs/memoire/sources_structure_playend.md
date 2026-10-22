# Sources : structure du jeu de données PlayEnd

À citer dans le mémoire pour justifier la structure des fichiers de PlayEnd (plusieurs tables CSV reliées par des
identifiants, découpage d'évaluation par session). Citations relevées dans les textes originaux le 2026-10-04 ;
références vérifiées sur Crossref quand un DOI existe. La liste complète des sources du jeu de données est dans
`docs/dataset/PROPOSITION_JEU_DE_DONNEES_GRU.md`.

## Une table par type d'élément observé

**Wickham, H. (2014). Tidy Data. *Journal of Statistical Software*, 59(10), 1–23.
<https://doi.org/10.18637/jss.v059.i10>**

C'est la source principale de la structure.

- Section 2.3, p. 4 : « In tidy data: 1. Each variable forms a column. 2. Each observation forms a row. 3. Each type
  of observational unit forms a table. This is Codd's 3rd normal form (Codd 1990), but with the constraints framed in
  statistical language. »
- Section 3.4, « Multiple types in one table », p. 11 : « Datasets often involve values collected at multiple levels,
  on different types of observational units. During tidying, each type of observational unit should be stored in its
  own table. This is closely related to the idea of database normalization, where each fact is expressed in only one
  place. If this is not done, it is possible for inconsistencies to occur. »
- Même page, l'exemple du classement Billboard : le jeu de données mêle la chanson et son rang chaque semaine, d'où
  « the duplication of facts about the song » ; il est découpé en une table des chansons et une table des rangs.
- Même page, la nuance : « Normalization is useful for tidying and eliminating inconsistencies. However, there are
  few data analysis tools that work directly with relational data, so analysis usually also requires denormalization
  or merging the datasets back into one table. »

Application à PlayEnd : une table par type d'élément, soit l'image (`observations.csv`), la session
(`sessions.csv`), la partie (`units.csv`) et le passage facturé au temps (`time_segments.csv`). Suivant la nuance de
Wickham, `observations.csv` porte aussi, sur chaque image, la partie en cours et les étiquettes du GRU, pour qu'il
suffise à l'entraînement. Le choix de ces quatre tables est une application de ce principe à nos données, pas une
liste prescrite par l'article.

**Codd, E. F. (1990). *The Relational Model for Database Management: Version 2*. Addison-Wesley.**
Référence de Wickham pour la troisième forme normale ; à citer avec lui si l'on parle de normalisation.

## Des tables reliées par des clés, et les découpages décrits à part

**Akhtar, M. et al. (2024). Croissant: A Metadata Format for ML-Ready Datasets. arXiv:2403.19546.
<https://arxiv.org/abs/2403.19546>** — et la spécification : <https://docs.mlcommons.org/croissant/docs/croissant-spec.html>

- Tables reliées : « Croissant provides a simple mechanism to create a "foreign key" reference between fields of
  recordsets. »
- Découpages : « The Croissant format allows for the data to be split arbitrarily into one or multiple splits, which
  for example allows dataset consumers to load a specific split », au moyen du type `cr:Split`.

Application : `session_id` et `unit_id` relient les tables, déclarés comme clés dans `croissant.json` ; le
découpage en plis est une table à part (`splits.csv`).

## Découper par session : éviter la fuite d'information

**Kaufman, S., Rosset, S., Perlich, C. (2011). Leakage in Data Mining: Formulation, Detection, and Avoidance.
*Proceedings of the 17th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (KDD '11),
556–563. <https://doi.org/10.1145/2020408.2020496>**

Résumé, p. 556 : « Deemed "one of the top ten data mining mistakes", leakage is essentially the introduction of
information about the data mining target, which should not be legitimately available to mine from. »

Version longue, avec un quatrième auteur : **Kaufman, S., Rosset, S., Perlich, C., Stitelman, O. (2012).
*ACM Transactions on Knowledge Discovery from Data*, 6(4), 1–21. <https://doi.org/10.1145/2382577.2382579>**

Application : des images voisines d'une même session, presque identiques, à la fois en entraînement et en test,
donneraient au modèle une information sur sa cible qu'il n'aurait pas sur le Pi.

**scikit-learn. GroupKFold.**
<https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html> — « Each group will appear
exactly once in the test set across all folds. »

Application : le groupe est la session ; une session est entière dans un seul pli.

## Le précédent pour le fichier principal

**Reiss, A., Stricker, D. (2012). PAMAP2 Physical Activity Monitoring. UCI Machine Learning Repository.
<https://archive.ics.uci.edu/dataset/231/pamap2+physical+activity+monitoring>**

Un jeu de données de séries temporelles où chaque ligne est un instant horodaté avec son étiquette vraie, comme
chaque ligne de `observations.csv` est une image avec ses étiquettes.

## Notation de la figure du schéma

**Object Management Group (2017). *OMG Unified Modeling Language (OMG UML), Version 2.5.1*. Spécification formelle.
<https://www.omg.org/spec/UML/2.5.1>**

Les multiplicités de `docs/memoire/figures/schema_playend.png` suivent cette notation : un intervalle
`borne-inférieure..borne-supérieure`, `*` pour une borne supérieure illimitée, et « 1 » équivaut à « 1..1 ».

Légende proposée pour le document : « Figure X — Schéma relationnel du jeu de données PlayEnd. PK : clé primaire ;
FK : clé étrangère ; multiplicités en notation UML (Object Management Group, 2017). Seules les principales colonnes
sont représentées. »

## Le format temporel et le découpage (relevé le 2026-10-05)

**Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or
phylogenetic structure. *Ecography*, 40(8), 913–929. <https://doi.org/10.1111/ecog.02881>**

- Résumé : « We recommend that block cross-validation be used wherever dependence structures exist in a dataset, even
  if no correlation structure is visible in the fitted model residuals, or if the fitted models account for such
  correlations. »
- p. 919 : « To include as much data for model training as possible in each cross-validation iteration, each block
  should be its own fold. »
- p. 918–919, pour limiter l'extrapolation : « representing predictors equally across blocks or folds ».

Application : la session est le bloc ; une session tenue à l'écart à chaque fois pour l'évaluation finale, et des
plis équilibrés (`splits.csv`) pour le choix du seuil.

**Gholamiangonabadi, D., Kiselov, N., Grolinger, K. (2020). Deep Neural Networks for Human Activity Recognition With
Wearable Sensors: Leave-One-Subject-Out Cross-Validation for Model Selection. *IEEE Access*, 8, 133982–133994.
<https://doi.org/10.1109/ACCESS.2020.3010715>** — le précédent le plus proche : séries de capteurs, un sujet tenu à
l'écart à chaque fois.

**Aminikhanghahi, S., Cook, D. J. (2017). A survey of methods for time series change point detection. *Knowledge and
Information Systems*, 51(2), 339–367. <https://doi.org/10.1007/s10115-016-0987-z>**

« In practice, no change point detection algorithm operates in perfect real time because it must inspect new data
before determining if a change point occurred between the old and new data points. »

Application : l'étiquette d'une ligne décrit l'intervalle (image précédente, image] ; la fin est placée sur la
première image qui la prouve.

**Reyna, M. A. et al. (2020). Early Prediction of Sepsis From Clinical Data: The PhysioNet/Computing in Cardiology
Challenge 2019. *Critical Care Medicine*, 48(2), 210–217.** Données : « Each row of the table provides a collection of
measurements at the same time » ; `ICULOS` = « ICU length-of-stay (hours since ICU admit) ». Application : une ligne
par image et `t_s` compté depuis le début de chaque session.

**Che, Z. et al. (2018). Recurrent Neural Networks for Multivariate Time Series with Missing Values. *Scientific
Reports*, 8, 6085. <https://doi.org/10.1038/s41598-018-24271-9>** — GRU-D : le masque des valeurs absentes et
l'intervalle de temps entrent dans le réseau. Application : masques `.known` et `delta_t_s` des variables v4.
