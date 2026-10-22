# Relecture `apprentissage` : les 211 fins manquées vues par l'apprentissage automatique

J'ai relu les 211 cas des huit lots en me demandant chaque fois si l'explication de l'échec par les variables et par
les modèles tenait. Les huit synthèses ont servi de texte principal. J'ai vérifié les affirmations de mon métier dans
le code (`src/playend/contract/temporal.py`, `src/playend/training/`) et dans les prédictions stockées du calcul du
6 octobre (`build/training/v1`), en lecture seule. Je n'ai lancé aucun entraînement. Trois sortes de vérifications :

- pour chaque cas, le pic de chaque détecteur comparé au seuil de son tour, graine par graine pour le GRU, le moment
  où l'annonce commence, et le nombre de captures « ordinaires » de l'enregistrement (à plus d'une capture d'une fin)
  qui atteignent ce pic. Ce dernier nombre dit si l'échec vient du classement (beaucoup de captures ordinaires plus
  hautes) ou du seuil (aucune) ;
- deux expériences d'inférence sur les GRU finaux, sans réentraînement : rejouer l'enregistrement en retirant des
  captures, ou en repartant d'un état neuf ;
- l'évaluation refaite sur les prédictions stockées avec d'autres règles d'appariement et d'autres seuils.

Je n'ai pas rouvert les images : les analystes les avaient lues au zoom, et mes désaccords portent sur les modèles,
pas sur la lecture des écrans.

**Bilan : 164 accords, 42 accords partiels, 5 désaccords.** La lecture des écrans et des étiquettes par les analystes
est solide. Mes réserves portent presque toutes sur l'explication côté modèle, surtout sur l'usage du code `SEUIL`.

## Codes ajoutés

- `DECALAGE_ECHELLE` : sur l'enregistrement tenu à l'écart, toutes les probabilités du modèle sont plus basses qu'en
  validation. La fin est classée au-dessus de toutes (ou presque toutes) les captures ordinaires de l'enregistrement,
  mais sous le seuil choisi sur d'autres enregistrements. Le classement est bon, l'échelle ne l'est pas.
- J'ai repris les codes des analystes : `ASYMETRIE_COTES` et `MEMOIRE_GRU` (lot 2), `RETARD` et `AVANCE` (lot 3),
  `ANNONCE_PRECOCE` (lot 4), `ANNONCE_EN_AVANCE`, `FINS_CONSECUTIVES` et `DEBUT_DE_SESSION` (lot 8).

Répartition de mes causes principales : `SEUIL` 48, `LECTURE_COUPEE` 39, `REPRISE` 27, `SIGNE_PROPRE_AU_JEU` 17,
`ECRAN_NON_MARQUE` 16, `DECALAGE_ECHELLE` 15, `JEU_RARE` 9, `ABANDON` 8, `MENU_AMBIGU` 7, `ASYMETRIE_COTES` 4,
`CONTEXTE_SANS_VARIATION` 4, `ETIQUETTE_DOUTEUSE` 4, `ANNONCE_EN_AVANCE` 3, `MEMOIRE_GRU` 2, `FIN_ENTRE_CAPTURES` 2,
puis une fois chacun `RETARD`, `AVANCE`, `ANNONCE_PRECOCE`, `ERREUR_OBSERVATION`, `FINS_CONSECUTIVES` et
`DEBUT_DE_SESSION`.

## (a) Ce que je conteste chez les analystes

### 1. `SEUIL` est employé trop largement, et pas toujours là où il faudrait

Un cas relève du seuil seulement si l'abaisser jusqu'au pic coûte peu : peu ou pas de captures ordinaires aussi
hautes. Quand des dizaines de captures ordinaires dépassent le pic, le modèle ne sépare pas la fin du reste, et
parler de seuil masque un défaut de représentation.

- **Le GRU sur les reprises de Mortal Kombat 1** (lot 1, presque tous les cas). Les analystes notent `SEUIL` en
  secondaire pour des pics de 0,18 à 0,44 face à des seuils de 0,555 à 0,57. Abaisser le seuil jusque-là ajouterait
  3 à 39 fausses fins par graine sur l'enregistrement (`f0067594` U10 : 31 à 39 ; U17 : 22 à 28 ; `11029423` U27 :
  6 à 10). Le GRU ne classe pas une baisse de score d'une seule capture au-dessus des captures ordinaires, alors que le
  gradient boosting la voit en une coupure d'arbre.
- **Désaccords** : Beach Buggy Racing 2 U19 et U22 (gradient boosting à 0,487 et 0,484 pour 0,981, avec 6 captures
  ordinaires plus hautes : c'est un autre détecteur qu'il faudrait, pas un autre seuil) ; Naruto `fdb79549` U01
  (6 captures ordinaires plus hautes pour le gradient boosting, 4 pour le GRU ; la vraie cause est le début
  d'enregistrement, avec une fenêtre remplie de zéros).
- **À l'inverse, le seuil est sous-estimé là où les analystes voient une faiblesse du modèle.** Dans `ff1c7245`, la
  capture ordinaire la plus haute vaut 0,11 pour le GRU (moyenne des graines) et 0,13 pour le gradient boosting, face
  à des seuils de 0,628 et 0,973. Toutes les fins manquées de Fortnite et de Warzone de cet enregistrement sont
  au-dessus de toute capture ordinaire, pour les deux modèles. L'explication « une fin à 87 joueurs restants ne
  ressemble à aucune fin apprise » (U03, désaccord) ne tient donc pas. Même constat dans `f8c2843d` : la capture
  ordinaire la plus haute vaut 0,21 pour le GRU et 0,19 pour le gradient boosting, pour des seuils de 0,77 et 0,758
  (U02, U05, U07, U27, U36).
- **Tekken 8 : le GRU n'est pas aveugle, il est tassé.** Les analystes parlent d'« aveuglement aux revanches » (U20,
  désaccord ; U04, U06, U24, U28, U30, partiels). Avec la moyenne de ses graines, il trouve 2 fins sur 34 à son seuil de
  0,481, 9 à 0,2 et 17 à 0,12, avec seulement 2 fausses fins dans l'enregistrement. Le gradient boosting passe de 11 à
  19 fins sur 34 en descendant de 0,97 à 0,9, pour une fausse fin de plus. Sur un jeu jamais vu, les probabilités du
  GRU baissent toutes ensemble, et un seuil choisi sur des jeux vus ne convient plus.

Mise en garde : ces comptes sont faits à l'intérieur de chaque enregistrement, avec ses étiquettes. Ils ne disent
pas qu'un seuil global plus bas serait gratuit. Je l'ai mesuré sur toutes les sessions tenues à l'écart (prédictions
stockées, seuil de chaque tour plafonné) :

| Gradient boosting, seuil du tour | Rappel | Fausses fins pour 100 parties |
|---|---:|---:|
| tel que choisi (rapport) | 42,5 % | 1,40 |
| plafonné à 0,95 | 48,4 % | 2,11 |
| plafonné à 0,90 | 53,0 % | 3,51 |
| médiane des 25 seuils partout | 26,7 % | 0,70 |

Le plafond est choisi ici après avoir vu les résultats : ces chiffres montrent l'arbitrage, ils ne valent pas
évaluation. Pour le GRU, les plafonds ne changent presque rien (37,3 % à 38,2 %), et la moyenne des graines au lieu
du vote non plus (36,5 %). Une fin parfaitement séparée dans son enregistrement peut donc rester sous le seuil sans
qu'un seuil global plus bas soit la solution : **les échelles de probabilité diffèrent d'un enregistrement à
l'autre**, et c'est cela qu'il faut corriger (section c).

### 2. Les captures masquées changent le mécanisme décrit

Dans `events.match`, `above` est multiplié par `usable` : une annonce sur une capture masquée est ignorée, elle ne
compte ni comme fin trouvée ni comme fausse fin.

- UFC `11029423` U01 : 29 et 30 sont masquées, l'annonce du GRU sur 30 (0,58 à 0,80) ne compte pas comme fausse fin,
  contrairement à ce qu'écrit l'analyste ; la fin est manquée parce que 4 graines retombent sous 0,57 sur 31.
- `f8c2843d` U31 (Warzone, « ANNONCE_PRECOCE ») : 890 est masquée, même correction.
- `f0067594` U37 : la « frontière manquante » de 418 n'est pas oubliée, 418 est masquée comme incertaine. La question
  de facturation reste ouverte pour l'auteur.
- `f8c2843d` U03 (EA FC) : 91 et 92 sont masquées, donc l'étiquette « douteuse d'une capture » ne pèse pas sur le
  compte.

En revanche, l'analyste du lot 8 décrit exactement `fdb79549` U04 (Dragon Ball : annonce sur l'accueil masqué, rien
sur la preuve).

### 3. `MEMOIRE_GRU` : confirmé là où il est affirmé, sauf un cas

J'ai rejoué les 5 GRU finaux du tour de `f0067594` sur l'enregistrement privé des captures de pause 144 à 152.
Sur 157 (fin U22), la probabilité passe de 0,02–0,05 à 0,45–0,81 (4 graines sur 5 au-dessus de 0,555). Sur
l'écran de victoire 161 (fin U23), elle passe de 0,06–0,48 à 0,76–0,89 (5 graines sur 5). L'hypothèse de l'analyste
est donc juste pour U22 et U23. Pour U24 en revanche, sans la pause, le GRU ne dépasse pas 0,07–0,21 sur 168 : c'est
la pause courte de 167 qui coupe la variation, pas la longue pause.

Même mécanisme dans Beach Buggy Racing 2 (le lot 6 l'appelait `AUTRE`, « dérive »). En repartant d'un état neuf
8 captures avant chaque tableau de résultats, les tableaux tardifs (311, 328, 360) passent de 0,00–0,06 à 0,13–0,34
pour 4 graines sur 5. La dérive est réelle, mais même avec un état neuf le GRU reste sous son seuil de 0,487 : la
cause principale reste le jeu jamais vu.

### 4. Le tri des colonnes par pli : constat exact, conséquence surestimée

C'est vérifié avec `kept_columns`. Dans le tour de Tekken, les 8 colonnes `counter.series.*` et
`result.outcome_type=ko` sont retirées. Dans celui de Beach Buggy Racing 2, ce sont `game.type=racing`,
`game.mode=race`, `progress.type=lap`, `progress.type=stage` et `state.screen_type=podium`. Mais les garder n'aurait
rien apporté : une colonne constante dans les données d'entraînement ne peut produire aucune coupure d'arbre, et dans
le GRU les poids d'une entrée toujours nulle ne reçoivent aucun gradient. Ils resteraient à leur valeur initiale
aléatoire et ajouteraient du bruit le jour où la colonne s'allume. Le vrai défaut est double : aucun exemple de ce
jeu à l'entraînement, et un encodage par case (type, côté) qui enferme un signal rare dans des colonnes qu'un seul jeu
remplit. Même remarque pour la variation du tour dans les courses : `progress.current.delta_candidate` n'est connue
que sur 2 lignes d'entraînement de ce tour, jamais négative.

### 5. `ASYMETRIE_COTES` : confirmé, avec une précision

Dans l'entraînement du tour qui tient `f0067594` à l'écart, les fins avec baisse de score se répartissent ainsi :
2 « A seul », 15 « B seul », 18 « les deux ». Les deux fins « A seul » sont des baisses 2→0 (Tekken `078643a4`
capture 155, Mortal Kombat 1 `8e58b139` capture 100). Avec `sign·log1p`, une baisse 1→0 vaut −0,693 et une baisse
2→0 −1,099 : aucune baisse 1→0 du seul côté A n'a été vue comme fin. La paire U38/U39 (0,981 contre 0,289) suffit à
le prouver.

### 6. « La variation n'est pas calculée parce que… » : ce que dit le code

Toutes les explications de ce type que j'ai contrôlées sont justes. Je rappelle les conditions exactes, parce que
plusieurs sont plus strictes que ce qu'on imagine :

- `_same_context` compare le titre **tel qu'il est écrit**, le type et le mode écrit. « EA Sports FC » contre
  « EA Sports FC 26 » (EA FC `11029423` U10, U11), un mode null sur une pause (`f0067594` U10) ou un mode en texte libre
  (Fortnite `ff1c7245` U09) rompent le contexte ;
- le chrono exige un dictionnaire de période identique **et** un type connu (`same_period`) : jamais vrai pour EA FC,
  Mortal Kombat 1 et Tekken, vrai seulement pour UFC ;
- les compteurs se comparent case par case : une série qui passe de B à A ne produit aucune variation (Tekken U06,
  U11, U18, U21) ;
- la « précédente » est la dernière observation qui n'est pas `observation_missing`. Une capture noire, masquée ou
  sans HUD reste donc la précédente (Beach Buggy Racing 2 U35 : la capture floutée masquée coupe quand même la
  variation).

Un point que les analystes n'ont pas pu voir : **plusieurs GRU ont retiré un groupe entier de variables par
ablation.** `changes` dans le tour de `27921669`, `counters` dans ceux de `11029423`, `ccfc6589`, `d8b709c4` et
`f8c2843d`, `timers` dans ceux de `fdb79549` et `ff1c7245`, `mode` dans celui de `fe69758b`. Pour ces tours,
expliquer un échec du GRU par une variation ou un compteur absents n'a pas de sens : il ne les voyait pas du tout.

## (b) Ce que mon métier voit que les analyses ne disent pas

1. **Le seuil est une statistique d'ordre extrême.** Dans les 25 tours, le seuil retenu à une fausse fin pour 100
   parties correspond à exactement 2 fausses annonces (une seule dans quatre cas sur 50) sur 216 à 243 fins de validation. Il est
   donc fixé par la deuxième ou la troisième fausse annonce la plus forte d'enregistrements qui ne sont pas celui
   qu'on évalue. D'où des seuils de 0,678 à 0,994 pour le gradient boosting et de 0,377 à 0,988 pour le GRU. Un seul
   cas difficile dans un pli de validation suffit à bloquer tout un enregistrement.
2. **Le seuil est choisi sur d'autres modèles que ceux qu'on évalue.** Il vient des modèles de validation interne
   (graine 7, arrêt précoce, entraînés sur une partie des sessions). Il est appliqué aux modèles finaux (graines 0 à 4,
   nombre d'époques ou d'arbres fixé à la médiane, toutes les sessions d'entraînement). Les échelles de probabilité ne
   sont pas les mêmes. Résultat visible dans le rapport : le GRU fait 3,8 fausses fins pour 100 parties en test pour
   un budget de 1 (0,4 à 0,9 en validation). Pour certains enregistrements, au contraire, le seuil est 5 à 7 fois
   plus haut que la plus forte capture ordinaire (`ff1c7245`). Au total, 57 des 164 fins manquées par le gradient
   boosting et 39 des 180 manquées par le GRU n'ont aucune capture ordinaire de leur enregistrement aussi haute
   qu'elles.
3. **Le GRU sature sur les longues suites identiques ou inconnues.** Je l'ai démontré par les deux expériences de
   la section a.3 : une pause de neuf captures dans Mortal Kombat 1, une longue suite de courses dans Beach Buggy
   Racing 2. Un GRU d'une couche, entraîné sur 25 enregistrements avec environ six pas de gradient par époque, n'a
   jamais rencontré ces régimes : son état s'y enferme.
4. **L'appariement d'évaluation coûte surtout au GRU.** Il ne reconnaît que le début d'un dépassement, sur la preuve
   ou la capture suivante. J'ai refait l'évaluation avec une tolérance de ±2 captures, appariement un à un au plus
   proche, en autorisant une capture masquée à porter l'annonce de la fin qui suit. Le GRU passe de 37,3 % à 39,6 % de
   rappel et de 3,79 à 2,46 fausses fins pour 100 parties : un tiers de ses « fausses fins » sont des annonces
   précoces de vraies fins. Le gradient boosting ne bouge presque pas (42,5 % → 42,8 %, 1,40 → 1,05). Fins récupérées par
   la majorité des graines : Fortnite `27921669` U02, EA FC `11029423` U08, `f8c2843d` U31, UFC `11029423` U01, Dragon
   Ball `fdb79549` U04 ; par une ou deux graines seulement : EA FC `11029423` U17, J-Stars U38, Mortal Kombat 1
   `11029423` U25. Attention : un appariement glouton à ±2 crée aussi des
   échanges entre fins voisines (l'annonce de 549 attribuée à U53 au lieu de U54 ; Tekken U07 et U08). Il faut un
   appariement optimal un à un, ou une mesure par nombre de parties.
5. **Les deux modèles se complètent.** Le gradient boosting gagne quand le signe tient en une capture explicite
   (reprises directes, écrans de résultat). Le GRU gagne quand la sortie s'étale sur plusieurs menus (abandons vers
   l'accueil, Warzone `7616a3a5` U04 et U06, EA FC `42dcc5f5` U03, `f8c2843d` U36). Les combiner (empilement, ou
   donner au gradient boosting les valeurs portées dans le temps) récupère les deux familles.
6. **Le même événement est éclaté entre six familles de colonnes.** « Une quantité qui ne devrait que monter a
   reculé » s'écrit `score.a`, `score.b`, `clock`, `progress`, et une case par compteur, chacune comparée seulement
   dans son contexte. Chaque colonne voit donc trop peu d'exemples pour être apprise, alors que l'invariant est
   commun à Mortal Kombat 1, EA FC, Tekken, UFC et Beach Buggy Racing 2.
7. **Les cibles sont incohérentes d'une session à l'autre.** La capture où le second marqueur s'allume est la fin dans
   `f0067594` (U09, U19, U22, U23, U42) et la capture d'avant la fin dans `8e58b139`, Tekken et une partie de
   `f0067594`. Pour un modèle, c'est la même entrée avec deux cibles. Avec une tolérance qui n'accepte que le retard,
   l'une des deux conventions est toujours pénalisée.

## (c) Méthode recommandée pour chaque famille de causes, et son coût

Repère de coût sur le Raspberry Pi Zero 2 W (Cortex-A53 quadricœur à 1 GHz, 512 Mo). Un pas du GRU retenu (cachés
16 à 64, environ 150 entrées) coûte au plus 3·(150·64 + 64·64) ≈ 41 000 multiplications-additions, et le gradient
boosting au plus 1 000 arbres à parcourir. Les deux restent bien sous la milliseconde par capture, à comparer aux
3,6 s médianes du VLM sur le Pi. Toutes les méthodes ci-dessous sont donc gratuites à l'exécution ; leur coût est un
réentraînement sur PC, une nouvelle version des variables (`FEATURE_VERSION`) et, pour certaines, des traces
d'annotation.

| Famille (cas, mes codes) | Méthode | Pourquoi | Coût |
|---|---|---|---|
| Comparaisons coupées ou mal faites : `LECTURE_COUPEE` 39, `CONTEXTE_SANS_VARIATION` 4 | Variations calculées contre la **dernière valeur lisible** du même jeu (score, chrono, phase, titre, compteurs), avec l'âge de cette valeur en secondes ; titre, mode et noms d'équipe normalisés avant `_same_context` ; chrono du football comparé sans période connue | Le report de la dernière observation, avec un masque et un intervalle de temps, est la méthode reconnue pour les séries à trous (GRU-D, Che et al., 2018 ; Lipton et al., 2016). Il donne aussi au gradient boosting, sans mémoire, ce que le GRU devrait retenir | Quelques dizaines de nombres d'état, calcul négligeable ; réentraînement |
| Signe non appris : `REPRISE` 27, `SIGNE_PROPRE_AU_JEU` 17, `JEU_RARE` 9 | **Variables communes à tous les jeux** : « une quantité croissante a reculé » (score, manche, tour, chrono de match), « score = objectif de manches », « un compteur de fin apparaît, disparaît ou change de côté », « ∞ qui apparaît » (variation plutôt qu'état) | Les reprises de Mortal Kombat 1 servent alors d'exemples aux nouvelles courses et aux relances d'UFC. C'est la seule façon de rendre un jeu nouveau un peu moins nouveau | Nul sur le Pi |
| `ASYMETRIE_COTES` 4 | Variables symétriques (total, minimum et maximum des deux côtés) ou **échange aléatoire A/B** à l'entraînement | Augmentation par une symétrie connue du problème (Wen et al., 2021, pour une revue des augmentations de séries temporelles) | Nul sur le Pi ; données d'entraînement doublées |
| `MEMOIRE_GRU` 2 (et la dérive de Beach Buggy Racing 2) | **Ne pas faire avancer le GRU** sur une observation identique à la précédente (en cumulant seulement le temps écoulé), ou plafonner la longueur des suites identiques ; à défaut, ajouter des pauses longues à l'entraînement ou passer à un modèle à mémoire bornée | L'idée de sauter des mises à jour d'état est celle des Skip RNN (Campos et al., 2018). Un réseau convolutif temporel à champ réceptif fini (Bai et al., 2018) ne peut pas s'enfermer dans un état | Diminue le calcul |
| Seuil et échelle : `SEUIL` 48, `DECALAGE_ECHELLE` 15 | (1) Choisir le seuil sur des prédictions **hors pli de modèles entraînés exactement comme le modèle final** (mêmes graines, même nombre d'époques), puis l'appliquer à la **moyenne des graines** ; (2) remplacer le point empirique « 2 fausses annonces sur 243 » par une règle de Neyman-Pearson qui borne le taux de fausses fins avec une probabilité donnée (algorithme parapluie, Tong et al., 2018) ; (3) faire la validation interne en **laissant un jeu de côté** pour le choix du seuil et des ablations ; (4) étalonner les sorties (Platt ou isotonique) pour comparer les seuils entre configurations | (1) supprime le décalage entre modèles de validation et modèles finaux ; la moyenne des probabilités est la combinaison d'un ensemble (Lakshminarayanan et al., 2017). (2) rend le seuil moins dépendant de deux annonces extrêmes. (3) La sélection de modèle sous changement de domaine se fait sur un domaine tenu à l'écart (Gulrajani et Lopez-Paz, 2021). (4) Le gradient boosting déforme ses probabilités (Niculescu-Mizil et Caruana, 2005) ; l'étalonnage est monotone, il ne change pas le classement d'un modèle, mais il rend les seuils transférables | Une comparaison sur le Pi, une table de correspondance pour l'isotonique ; plus de tâches d'entraînement sur PC |
| Évaluation et étiquettes : `ETIQUETTE_DOUTEUSE` 4, `ANNONCE_EN_AVANCE` 3, `RETARD`, `AVANCE`, `ANNONCE_PRECOCE`, `FINS_CONSECUTIVES`, `DEBUT_DE_SESSION` (1 chacun) | Appariement **un à un avec marge symétrique** (van den Burg et Williams, 2020 : marge de 5 points, une seule détection retenue par vraie rupture), une capture masquée autorisée à porter l'annonce de la fin suivante, et une mesure par **nombre de parties par session**, la grandeur facturée. À l'entraînement, une cible étalée autour de la fin plutôt qu'une seule ligne (fonction de perte sensible au contexte de Cioppa et al., 2020). Conventions d'étiquetage unifiées par traces (capture du second marqueur, abandon vers l'accueil) | La tolérance actuelle (0 à +1, sur le seul début du dépassement) compte une annonce juste comme une fin manquée plus une fausse fin. Les mesures par plage (Tatbul et al., 2018) vont dans le même sens | Nul sur le Pi |
| Écrans de fin non marqués et erreurs du professeur : `ECRAN_NON_MARQUE` 16, `ERREUR_OBSERVATION` 1 | Traces de correction, contrôle dans `build_lot` (un participant égal à un nom de champ, EA FC `f0067594` U29) ; côté modèle, garder `result.visible` comme variable commune, encodée faux plutôt qu'inconnu quand l'écran est lu | Ce n'est pas un problème d'apprentissage, mais `result.visible` est la variable qui transfère le mieux d'un jeu à l'autre (seule fin de Tekken trouvée par le GRU : U08) | Annotation |
| Sorties de partie : `ABANDON` 8, `MENU_AMBIGU` 7, `FIN_ENTRE_CAPTURES` 2 | Variables portées : « dernière phase de jeu connue », « captures depuis la dernière capture de jeu actif », « dernier titre connu » ; empilement GRU + gradient boosting | Ce sont les cas où le GRU l'emporte par sa mémoire et où la fenêtre de trois captures du gradient boosting est vide | Négligeable |

## (d) Les trois priorités que je donnerais à l'auteur

1. **Refaire les variables de changement (version 5.0) avant tout nouvel entraînement.** Valeurs portées depuis la
   dernière observation lisible avec leur âge, titre, mode et noms normalisés, invariants communs à tous les jeux
   (quantité croissante qui recule, objectif atteint, compteur qui change de côté), variables symétriques entre A et
   B, et un GRU qui n'avance pas sur les observations identiques. Cela touche directement environ 100 des 211 cas
   (`LECTURE_COUPEE`, `REPRISE`, `CONTEXTE_SANS_VARIATION`, `ASYMETRIE_COTES`, une partie de `SIGNE_PROPRE_AU_JEU`,
   `ABANDON`, `MENU_AMBIGU`, `MEMOIRE_GRU`), sans rien coûter sur le Pi.
2. **Rendre le seuil transférable.** Seuils choisis sur des prédictions hors pli de modèles construits comme le
   modèle final, moyenne des graines, borne de Neyman-Pearson au lieu de deux annonces extrêmes, validation interne
   qui laisse un jeu de côté. Publier la courbe rappel / fausses fins plutôt qu'un seul point. C'est la famille la plus
   nombreuse (63 cas), mais j'insiste : un seuil global plus bas n'est pas la réponse (+5,9 points de rappel au prix de
   +0,7 fausse fin pour 100 parties pour le gradient boosting plafonné à 0,95). Il faut des échelles comparables d'un
   enregistrement à l'autre.
3. **Corriger la mesure avant de comparer les modèles.** Appariement optimal un à un avec marge symétrique, captures
   masquées autorisées à porter une annonce, erreur sur le nombre de parties par session, conventions d'étiquetage
   unifiées par traces (après validation de l'auteur). Sur les prédictions actuelles, cela ramène déjà les fausses
   fins du GRU de 3,79 à 2,46 pour 100 parties et lui rend 2 points de rappel : la comparaison GRU contre gradient
   boosting du mémoire en dépend.

## Sources vérifiées en ligne

- Che, Purushotham, Cho, Sontag, Liu (2018), « Recurrent Neural Networks for Multivariate Time Series with Missing
  Values », *Scientific Reports* 8:6085 — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5904216/
- Lipton, Kale, Wetzel (2016), « Directly Modeling Missing Data in Sequences with RNNs », MLHC, PMLR 56 —
  https://proceedings.mlr.press/v56/Lipton16.html
- Tong, Feng, Li (2018), « Neyman-Pearson classification algorithms and NP receiver operating characteristics »,
  *Science Advances* 4:eaao1659 — https://pmc.ncbi.nlm.nih.gov/articles/PMC5804623
- Niculescu-Mizil, Caruana (2005), « Predicting Good Probabilities with Supervised Learning », ICML —
  https://mlanthology.org/icml/2005/niculescumizil2005icml-predicting
- Lakshminarayanan, Pritzel, Blundell (2017), « Simple and Scalable Predictive Uncertainty Estimation using Deep
  Ensembles », NeurIPS (§2.4 : « averaging the predicted probabilities ») — https://arxiv.org/abs/1612.01474
- Gulrajani, Lopez-Paz (2021), « In Search of Lost Domain Generalization », ICLR — https://arxiv.org/abs/2007.01434
- van den Burg, Williams (2020), « An Evaluation of Change Point Detection Algorithms » (marge M = 5, une seule
  détection retenue par rupture) — https://arxiv.org/abs/2003.06222
- Tatbul, Lee, Zdonik, Alam, Gottschlich (2018), « Precision and Recall for Time Series », NeurIPS —
  https://proceedings.neurips.cc/paper/2018/hash/8f468c873a32bb0619eaeb2050ba45d1-Abstract.html
- Cioppa et al. (2020), « A Context-Aware Loss Function for Action Spotting in Soccer Videos », CVPR —
  https://openaccess.thecvf.com/content_CVPR_2020/html/Cioppa_A_Context-Aware_Loss_Function_for_Action_Spotting_in_Soccer_Videos_CVPR_2020_paper.html
- Campos, Jou, Giró-i-Nieto, Torres, Chang (2018), « Skip RNN: Learning to Skip State Updates in Recurrent Neural
  Networks », ICLR — https://arxiv.org/abs/1708.06834
- Bai, Kolter, Koltun (2018), « An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence
  Modeling » — https://arxiv.org/abs/1803.01271
- Wen et al. (2021), « Time Series Data Augmentation for Deep Learning: A Survey », IJCAI —
  https://www.ijcai.org/proceedings/2021/631
- Raspberry Pi Zero 2 W, fiche officielle (Cortex-A53 quadricœur 64 bits à 1 GHz, 512 Mo) —
  https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/
