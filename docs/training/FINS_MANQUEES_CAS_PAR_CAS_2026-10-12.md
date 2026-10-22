# Les fins manquées, cas par cas (11 et 12 octobre 2026)

Demandée par l'auteur après une première analyse trop rapide (`FINS_MANQUEES_2026-10-11.md`, classement automatique,
cinq planches regardées) : regarder **toutes** les fins manquées une par une, image par image avec leurs voisines,
comprendre pourquoi nos détecteurs ne les trouvent pas, et chercher la méthode adaptée à chaque cause. Rien n'est
réentraîné : tout part des prédictions du calcul complet du 6 octobre (`build/training/v1/`), au budget d'une fausse fin
pour 100 parties. Le travail détaillé est dans `fins_manquees_2026-10-12/` (voir son README).

## Méthode

- **Les cas.** Les 211 fins manquées par le gradient boosting ou par le GRU, dont 133 par les deux (sur 285 fins
  évaluées). Pour chacune, un dossier : les captures de deux avant la fin de la partie à deux après la preuve, avec
  l'observation du professeur, les probabilités du GRU, du gradient boosting et des règles, et les variables de
  changement réellement calculées ; et une planche des captures.
- **Huit analystes**, chacun spécialiste d'un genre (Mortal Kombat 1 en deux lots, EA FC en deux lots, Tekken 8, Beach
  Buggy Racing 2, battle royale, autres combats), ont étudié chaque fin sur sa planche, en ouvrant les images en taille
  réelle dès qu'un détail comptait. Pour chacune : ce qui prouve la fin à l'écran, la justesse de l'étiquette,
  l'erreur éventuelle du professeur, ce que montraient les variables, pourquoi chaque détecteur l'a manquée, une cause
  principale et des causes secondaires (codes définis dans `BRIEFING.md`), la méthode qui l'aurait trouvée.
- **Trois relecteurs** ont repris les 211 cas, chacun avec son métier, pour confirmer ou contester : un chercheur en
  apprentissage automatique (qui a vérifié les explications dans le code et rejoué des prédictions, sans entraîner), un
  spécialiste de la qualité des annotations (68 cas vérifiés sur les images, dont toutes les étiquettes douteuses et
  tous les écrans de fin dits non marqués), un gérant de salle et joueur (coût réel de chaque fin manquée).
- **Consensus.** La cause retenue est celle que donnent au moins deux des quatre regards : unanime pour 151 fins,
  trois sur quatre pour 47, deux sur quatre pour 13. Accords des relecteurs avec les analystes : apprentissage 164
  accords, 42 partiels, 5 désaccords ; annotation 176 et 35, aucun désaccord ; terrain 178, 32 et 1.

## Les causes

| Cause de consensus | Fins | Manquées par les deux | Parties perdues avec le gradient boosting | avec le GRU |
|---|---:|---:|---:|---:|
| `SEUIL` : la fin est vue mais le seuil du tour la rejette | 50 | 20 | 34 | 24 |
| `REPRISE` : partie recommencée ou revanche, mêmes participants, retour au départ | 40 | 21 | 20 | 39 |
| `LECTURE_COUPEE` : une capture illisible entre les deux efface la variation | 34 | 28 | 29 | 29 |
| `ECRAN_NON_MARQUE` : un écran de fin visible n'est pas noté comme résultat | 20 | 15 | 17 | 18 |
| `SIGNE_PROPRE_AU_JEU` : tour qui revient à 1, compteur de victoires, manches | 15 | 14 | 15 | 14 |
| `ABANDON` : sortie vers le salon, la console, un autre jeu | 14 | 12 | 11 | 11 |
| `JEU_RARE` : jeu d'un seul enregistrement, manqué par le seul GRU | 9 | 0 | 0 | 9 |
| `MENU_AMBIGU` : pause ou menu pris pour une interruption | 6 | 3 | 6 | 3 |
| Évaluation et étiquettes (annonce en avance, retard, étiquette douteuse, fins consécutives) | 10 | 10 | 8 | 8 |
| Autres (fin entre deux captures, contexte sans variation, asymétrie des côtés, mémoire du GRU, erreur d'observation) | 13 | 10 | 11 | 12 |

Les étiquettes sont justes pour 203 fins sur 211 ; 8 sont placées une capture trop tôt ou trop tard (voir plus bas).

**Coût réel.** Une fin manquée fait perdre une partie quand la partie et la suivante dépassent toutes deux le seuil de
relance rapide (15 s en combat, 60 s ailleurs) : c'est le cas de 197 fins sur 211 (151 des 164 manquées par le
gradient boosting, 167 des 180 manquées par le GRU). Le relecteur terrain, qui écarte aussi quelques cas particuliers,
en compte 193. C'est cohérent avec le rejeu du compteur (155 parties perdues sur 296 avec le gradient boosting).

## Ce que l'analyse a découvert

Les causes de consensus disent ce qui se voit dans un cas. Derrière elles, l'analyse cas par cas a mis au jour des
défauts de fond, communs à plusieurs familles.

1. **Tout se compare à la capture juste avant.** Les variables de changement et les règles écrites comparent chaque
   capture à la précédente, même noire, sans tableau de score, en pause ou sur une bannière. Le retour à 0–0, le
   changement de jeu ou le chrono qui remonte disparaissent alors. Comparer à la dernière valeur lisible du même jeu
   aurait trouvé, selon les lots, 6 des 13 fins d'EA FC manquées par tous, 6 des 8 de Tekken, 4 des 6 d'un lot de
   Mortal Kombat 1. Exemple : EA FC `11029423` U20, 4–5 à 88:14, capture sans tableau de score, 0–0 à 04:14 ; sur la
   capture qui prouve la fin, aucune variation de score n'est calculée et le GRU reste à 0,09.
2. **Un « même contexte » trop strict, et une notation instable.** La variation du chrono n'est calculée que si la
   période est connue ; le professeur la note `unknown` pour EA FC et la plupart des jeux de combat, donc le chrono qui
   repart à zéro, le signe le plus net d'un nouveau match, n'est jamais une variable. Le titre d'EA FC change
   d'écriture 61 fois entre deux captures voisines, dont 51 au milieu d'une partie ; les noms d'équipe 92 fois au
   milieu d'une partie (sigle du tableau de score contre nom long d'un menu). Chaque changement d'écriture rompt le
   calcul des variations et lève à tort les drapeaux de changement, ce qui apprend aux modèles à ne pas s'y fier.
3. **Une variable par case, et des cases mal remplies.** Le même événement (« une quantité qui ne fait que monter a
   reculé ») est éclaté entre le score A, le score B, le chrono, le tour et une case par compteur, chacune comparée dans
   son seul contexte : chaque colonne voit trop peu d'exemples. Le compteur de victoires de Tekken change de case quand
   la série passe à l'autre joueur, et sa variation n'est plus calculée. Le gradient boosting a appris le côté :
   toutes les revanches d'entraînement du tour de `f0067594` retombent du côté B, et il trouve 0,98 pour la même
   situation côté B contre 0,29 côté A (Mortal Kombat 1 U38 et U39). Le « ∞ » de Dragon Ball Sparking! ZERO, qui
   marque le début d'un combat, vient presque toujours de l'entraînement de Mortal Kombat 1, où il n'y a aucune fin :
   les modèles l'ont appris à l'envers.
4. **Le GRU s'endort.** Après une longue pause (Mortal Kombat 1, captures 142 à 152) ou sur une longue suite de courses
   d'un jeu jamais vu, son état s'enferme. Expérience du relecteur, sans entraînement : sans les captures de pause, sa
   probabilité remonte de 0,02–0,05 à 0,45–0,89 sur les deux fins suivantes.
5. **Un seuil qui ne se transpose pas.** Le seuil de chaque tour est fixé par deux fausses annonces sur les 216 à 243
   fins de validation, et choisi sur les modèles de validation (une graine, arrêt précoce) avant d'être appliqué aux
   modèles finaux (cinq graines, durée fixée). Les échelles de probabilité diffèrent : le GRU fait 3,8 fausses fins pour
   100 parties en test pour un budget de 1, et ailleurs le seuil est 5 à 7 fois plus haut que la plus forte capture
   ordinaire. 57 des 164 fins manquées par le gradient boosting (39 des 180 pour le GRU) sont plus hautes que toute
   capture ordinaire de leur enregistrement. Baisser le seuil ne suffit pas : plafonné à 0,95, le gradient boosting
   passe à 48,4 % des fins mais à 2,11 fausses fins pour 100 parties.
6. **Une évaluation qui pénalise des annonces justes.** La tolérance n'accepte que le retard, sur la preuve ou la
   capture suivante. Une annonce faite sur une capture de transition juste avant la preuve compte comme une fausse fin
   et une fin manquée. Avec une marge de deux captures dans les deux sens, un appariement un à un et une capture masquée
   autorisée à porter l'annonce, le GRU passe de 37,3 % à 39,6 % des fins et de 3,79 à 2,46 fausses fins pour 100
   parties ; le gradient boosting bouge peu (42,5 % à 42,8 %, 1,40 à 1,05).
7. **Une vérité terrain à réparer.**
   - Dans les jeux de combat, la capture où un combattant atteint l'objectif de manches porte la fin dans 6 parties
     (`f0067594` U09, U19, U22, U23, U42 ; Naruto `fdb79549` U02) et la capture suivante dans 10 (`8e58b139` U03, U05,
     U07, U08, U09 ; `f0067594` U34, U47, U48 ; Tekken U25, U30). La règle écrite (`data/boundaries/README.md`, fin
     sur la première observation qui l'établit) donne raison aux 6 premières : la décision du 3 octobre n'a été
     appliquée qu'à moitié. Les modèles reçoivent la même entrée avec deux cibles.
   - Huit fins sont placées une capture trop tard ou trop tôt : `8e58b139` U09, `f0067594` U33 et U54, `f8c2843d` U03,
     Tekken U25 et U30, Fortnite `27921669` U02, UFC `f8c2843d` U21 (à confirmer) ; le relecteur annotation ajoute
     Dragon Ball `fdb79549` U04. Dans plusieurs cas, les détecteurs avaient raison et sont comptés faux.
   - En `f0067594` U37, la bannière « ROUND 2 » revient alors que la deuxième manche a déjà été jouée : un match
     recommencé que la référence ne compte pas (l'intervalle est masqué comme incertain).
   - Le relecteur terrain conteste EA FC `11029423` U07 : après un nul au coup de sifflet, EA FC propose une
     prolongation ; la fin devrait être sur le match suivant (capture 204), sinon le détecteur apprend à couper les
     matchs avec prolongation.
8. **Des observations à corriger.** Une seule faute de saisie dans une lecture du professeur (`f0067594`, capture 254 :
   la clé destinée à noter l'écran de résultat est tombée dans la liste des participants) donne à la fois un faux
   participant « state.screen_type » et un écran « FIN DU MATCH — Arsenal 7–4 Real Madrid » noté comme du jeu en cours ;
   c'est le seul cas dans PlayEnd. 13 des 29 captures notées noires en `f8c2843d` ne le sont pas, dont un écran
   « RÉSULTATS — VAINQUEUR ». Le même écran est noté différemment d'une session à l'autre : le menu d'après-match d'EA FC
   en `pause`, `post_game` ou `pre_game` ; l'écran d'après-match de Tekken en `intermediate` ou `menu`, jamais
   `post_game` ; le spectateur de Fortnite de quatre façons, et son mode avec neuf valeurs. Un « K.O. » de simple manche
   de Tekken est noté comme un résultat de match, ce qui fabrique un faux écran de fin en plein match.
9. **Le rythme des captures.** Un écran de fin visible quelques secondes n'est saisi, avec une capture toutes les 28 s,
   qu'une fois sur quatre ou cinq : 14 courses sur 27 ne se voient qu'au départ de la course suivante. Or la boucle de
   l'élève lit une capture de jeu en 2,3 s sur le Pi : capturer toutes les 5 à 10 s en jeu deviendrait possible.
10. **Deux corrections de la première analyse.** Le bandeau « Fin de la course ! » de Beach Buggy Racing 2 n'est pas un
    écran de fin oublié : un autre joueur roule encore, le classement n'est pas arrêté ; c'est un signe que la fin
    approche (elle suit 5 fois sur 5). Et le tri des colonnes par pli, qui retire les colonnes d'un jeu tenu à l'écart,
    n'est pas une cause : une colonne constante à l'entraînement n'apprend rien de toute façon ; le vrai défaut est
    l'encodage par case (point 3).

## La méthode adaptée à chaque cause

Toutes ces méthodes coûtent moins d'une milliseconde par capture sur le Pi (un pas du GRU ou des arbres, contre 3,6 s
pour lire l'écran) ; leur coût est du code, un réentraînement sur PC ou des corrections d'annotation. Aucune n'est
faite : chacune demande l'accord de l'auteur.

| Cause | Méthode | Pourquoi |
|---|---|---|
| `LECTURE_COUPEE`, `CONTEXTE_SANS_VARIATION` | Variations calculées contre la **dernière valeur lisible** du même jeu, avec son âge ; titre, mode et noms d'équipe normalisés (famille de jeu, table d'alias) ; chrono du football comparé sans période connue | Reporter la dernière observation avec un masque et l'intervalle de temps est la méthode reconnue pour les séries à trous (GRU-D [1] ; [2]) ; cela donne aussi au gradient boosting, sans mémoire, ce que le GRU devrait retenir |
| `REPRISE`, `SIGNE_PROPRE_AU_JEU`, `JEU_RARE` | **Invariants communs à tous les jeux**, en variables et en règles : une quantité qui ne fait que monter recule (score, manche, tour, chrono de match), le chrono de round remonte, l'objectif de manches est atteint, un compteur apparaît ou change de côté, « ROUND 1 » ou « ∞ » revient ; détecter aussi le **début** d'une partie, pas seulement la fin ; plus d'enregistrements de Tekken, de Beach Buggy et de Mortal Kombat 1 hors de `f0067594` | Les reprises de Mortal Kombat 1 servent alors d'exemples aux courses et aux relances d'UFC. Détecter une remise à zéro, c'est ce que font les outils de surveillance pour un compteur qui ne fait que monter [3]. Beaucoup de fins ne se prouvent que par le départ de la partie suivante : BSN estime séparément une probabilité de début et une de fin [4] |
| `ASYMETRIE_COTES` | Variables symétriques entre les deux camps (total, plus petit, plus grand) ou échange aléatoire des camps à l'entraînement | Augmentation par une symétrie connue du problème [5] |
| `MEMOIRE_GRU` | Ne pas faire avancer le GRU sur une observation identique à la précédente (en cumulant seulement le temps), ou un modèle à mémoire bornée | Idée des Skip RNN [6] ; un réseau convolutif temporel a un champ réceptif fini [7] |
| `SEUIL` | Seuil choisi sur des prédictions hors pli de modèles construits comme le modèle final, appliqué à la moyenne des graines [8] ; règle de Neyman-Pearson qui borne le taux de fausses fins [9] ou contrôle du risque par conformité [10] ; validation interne qui laisse un jeu de côté [11] ; étalonnage des probabilités du gradient boosting [12] ; budget choisi au niveau du compte, d'après le coût des erreurs [13] | Le seuil actuel tient à deux annonces extrêmes et change d'échelle entre modèles ; les arbres boostés déforment leurs probabilités, et un étalonnage monotone rend les seuils transférables sans changer le classement |
| `ECRAN_NON_MARQUE`, `ERREUR_OBSERVATION` | Traces de correction, treize conventions à écrire (écran d'après-match des jeux de combat en `post_game`, « K.O. » de manche jamais un résultat, menus d'après-match d'EA FC, spectateur et mode de Fortnite, classement cumulé de Beach Buggy, sorties vers la console…) et sept contrôles automatiques dans `build_lot` (participant égal à un nom de champ, capture « noire » trop lumineuse, note qui parle de « VAINQUEUR » sans résultat…) | Les fins ont été placées à partir des observations : une erreur du professeur devient une erreur d'étiquette sans que rien ne le signale. Détection systématique des erreurs d'annotation [14] ; de faibles taux d'erreur dans les étiquettes de test suffisent à changer le classement des modèles [15] |
| `ABANDON`, `MENU_AMBIGU` | Fermer la partie **dans le compteur, sans seuil** : titre différent, passage à un jeu facturé au temps, extinction de la console, résultat affiché avec un vainqueur ou une place, retour au salon d'un battle royale ; variables portées « dernière phase de jeu connue », « captures depuis le dernier jeu actif » ; associer le GRU et le gradient boosting | Aucun client ne conteste la fin d'une partie quand il change de jeu ; le GRU gagne sur les sorties étalées sur plusieurs menus, le gradient boosting sur les signes en une capture : ils se complètent. Combiner des règles bruitées et un modèle appris est l'idée de la supervision faible [16] |
| `FIN_ENTRE_CAPTURES` | Capturer plus souvent en jeu (5 à 10 s), ou en rafale quand la fin approche ; signaler à l'opérateur une partie anormalement longue (temps de jeu actif au-delà de la durée habituelle du jeu) | Un écran de d secondes est saisi avec une probabilité d'environ d/T ; une durée attendue par jeu est l'idée des modèles semi-markoviens [17] |
| Évaluation et étiquettes | Appariement un à un avec une marge dans les deux sens [18], une capture masquée autorisée à porter l'annonce, erreur sur le nombre de parties par session ; cible étalée autour de la fin à l'entraînement [19] ; mesures par plage [20] ; étiquettes unifiées par traces après validation de l'auteur | La tolérance actuelle compte une annonce juste comme une fin manquée plus une fausse fin, et la comparaison GRU contre gradient boosting en dépend |

## Les priorités, d'après les trois relecteurs

Les trois relecteurs convergent sur le même ordre.

1. **Réparer la vérité terrain et la mesure avant de comparer quoi que ce soit** : unifier la capture qui porte la fin
   d'un combat, déplacer les fins mal placées, ajouter le match recommencé de `f0067594`, trancher le nul suivi d'une
   prolongation, corriger la capture 254 et les fausses captures noires par des traces, puis refaire l'évaluation avec
   un appariement symétrique. Cela demande la validation de l'auteur (règle 7).
2. **Refaire les variables de changement** (nouvelle version des variables) : dernière valeur lisible, contexte
   normalisé, invariants communs, symétrie entre les camps, GRU qui n'avance pas sur les observations identiques. Cela
   touche environ 100 des 211 cas et ne coûte rien sur le Pi, mais demande un nouvel entraînement.
3. **Fermer sans seuil ce qui ne se discute pas, dans le compteur, garder la capture qui prouve chaque fin, et décider
   le budget au niveau du compte** (au budget 5, le rejeu donne 0,7 partie en trop et 34,5 perdues pour 100, au lieu de
   0,0 et 52,4). Rien de cela ne demande de réentraîner.

Viennent ensuite le seuil transférable, les conventions et contrôles d'annotation, des enregistrements de plus pour
les jeux rares, et un rythme de capture plus serré en jeu.

## Pour le mémoire

- 3.2 : les familles de fins manquées et leurs nombres, le défaut « tout se compare à la capture juste avant », le
  coût réel (197 sur 211) ; la réponse sur les fins sans écran de fin (déjà notée pour la revue finale).
- 3.6 (discussion et limites) : le seuil qui ne se transpose pas, l'effet de la tolérance sur la comparaison GRU
  contre gradient boosting, l'incohérence d'étiquetage des fins de combat, les erreurs du professeur et les conventions
  manquantes, les pistes classées par coût.
- 3.1 : la phrase « 229 fins n'ont aucun écran de fin » compte les captures de preuve non notées comme écran de fin
  dans les observations ; quelques-unes en montrent un (capture 254, écran « RÉSULTATS » de `f8c2843d`).

## Sources

1. Che, Z., Purushotham, S., Cho, K., Sontag, D., Liu, Y. (2018). *Recurrent Neural Networks for Multivariate Time
   Series with Missing Values*. Scientific Reports 8, 6085. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5904216/
2. Lipton, Z. C., Kale, D., Wetzel, R. (2016). *Directly Modeling Missing Data in Sequences with RNNs*. MLHC, PMLR 56.
   https://proceedings.mlr.press/v56/Lipton16.html
3. Mécanisme de remise à zéro des compteurs dans Prometheus (une baisse entre deux valeurs successives est une remise
   à zéro), description secondaire : https://oneuptime.com/blog/post/2026-07-31-detect-counter-resets-wraparound/view
4. Lin, T., Zhao, X., Su, H., Wang, C., Yang, M. (2018). *BSN: Boundary Sensitive Network for Temporal Action Proposal
   Generation*. ECCV. https://arxiv.org/abs/1806.02964
5. Wen, Q. et al. (2021). *Time Series Data Augmentation for Deep Learning: A Survey*. IJCAI.
   https://www.ijcai.org/proceedings/2021/631
6. Campos, V. et al. (2018). *Skip RNN: Learning to Skip State Updates in Recurrent Neural Networks*. ICLR.
   https://arxiv.org/abs/1708.06834
7. Bai, S., Kolter, J. Z., Koltun, V. (2018). *An Empirical Evaluation of Generic Convolutional and Recurrent Networks
   for Sequence Modeling*. https://arxiv.org/abs/1803.01271
8. Lakshminarayanan, B., Pritzel, A., Blundell, C. (2017). *Simple and Scalable Predictive Uncertainty Estimation
   using Deep Ensembles*. NeurIPS. https://arxiv.org/abs/1612.01474
9. Tong, X., Feng, Y., Li, J. J. (2018). *Neyman-Pearson classification algorithms and NP receiver operating
   characteristics*. Science Advances 4, eaao1659. https://pmc.ncbi.nlm.nih.gov/articles/PMC5804623
10. Angelopoulos, A. N. et al. (2024). *Conformal Risk Control*. ICLR.
    https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html
11. Gulrajani, I., Lopez-Paz, D. (2021). *In Search of Lost Domain Generalization*. ICLR. https://arxiv.org/abs/2007.01434
12. Niculescu-Mizil, A., Caruana, R. (2005). *Predicting Good Probabilities with Supervised Learning*. ICML, 625–632.
    https://mlanthology.org/icml/2005/niculescumizil2005icml-predicting
13. Elkan, C. (2001). *The Foundations of Cost-Sensitive Learning*. IJCAI.
    https://mlanthology.org/ijcai/2001/elkan2001ijcai-foundations
14. Klie, J.-C., Webber, B., Gurevych, I. (2023). *Annotation Error Detection: Analyzing the Past and Present for a More
    Coherent Future*. Computational Linguistics 49(1). https://aclanthology.org/2023.cl-1.4
15. Northcutt, C. G., Athalye, A., Mueller, J. (2021). *Pervasive Label Errors in Test Sets Destabilize Machine
    Learning Benchmarks*. NeurIPS Datasets and Benchmarks. https://arxiv.org/abs/2103.14749
16. Ratner, A. et al. (2017). *Snorkel: Rapid Training Data Creation with Weak Supervision*. VLDB.
    https://arxiv.org/abs/1711.10160
17. Yu, S.-Z. (2010). *Hidden semi-Markov models*. Artificial Intelligence 174(2), 215–243.
    https://www.cs.ubc.ca/~murphyk/Teaching/CS540-Spring10/projects/Yu-hsmm09.pdf
18. van den Burg, G. J. J., Williams, C. K. I. (2020). *An Evaluation of Change Point Detection Algorithms*.
    https://arxiv.org/abs/2003.06222
19. Cioppa, A. et al. (2020). *A Context-Aware Loss Function for Action Spotting in Soccer Videos*. CVPR.
    https://openaccess.thecvf.com/content_CVPR_2020/html/Cioppa_A_Context-Aware_Loss_Function_for_Action_Spotting_in_Soccer_Videos_CVPR_2020_paper.html
20. Tatbul, N. et al. (2018). *Precision and Recall for Time Series*. NeurIPS.
    https://proceedings.neurips.cc/paper/2018/hash/8f468c873a32bb0619eaeb2050ba45d1-Abstract.html
