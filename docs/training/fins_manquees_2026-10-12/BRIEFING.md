# Consignes : analyse cas par cas des fins manquées

Tu es analyste dans une équipe qui étudie pourquoi nos détecteurs de fin de partie ont manqué certaines fins. Travaille
cas par cas, image par image, sans généraliser avant d'avoir regardé le cas. Écris en français.

## Le projet en bref

Un Raspberry Pi capture l'écran d'une console de salle de jeux à Kinshasa, une capture toutes les 10 à 45 s (28 s en
moyenne). Un grand modèle de vision, le « professeur », a décrit chaque capture en JSON (l'« observation » : jeu,
type d'écran, phase, score, chrono, période, participants, compteurs de fin, minuteurs, résultat), une capture à la
fois, sans voir les voisines. Les fins de partie ont ensuite été placées en lisant les observations dans l'ordre :
chaque fin est posée sur la **première capture qui la prouve** (la « capture qui prouve la fin »), puis vérifiée à la
main par l'auteur (282 fins justes sur 295 ; 5 fausses ont été corrigées). Une partie recommencée ou quittée compte
comme une partie complète. Le jeu de données s'appelle PlayEnd.

Conventions du professeur utiles ici (détail : `docs/conventions/README.md` et un fichier par genre dans
`docs/conventions/`, analyse des fins par jeu : `docs/conventions/ANALYSE_FIN_DE_PARTIE_PAR_JEU.md`) :
- participants = seulement le texte écrit à l'écran ; aucun nom écrit : liste vide ;
- `null` quand une valeur n'est pas lisible ; chaque capture est lue seule ;
- `result.visible` seulement quand un résultat est explicitement affiché ;
- compteurs de fin (`secondary_counters`) : ce qui reste avant la fin (joueurs restants, vies, emplacements de
  manches, séries « WINS ») ;
- le professeur ne décide jamais qu'une partie est finie.

## Les détecteurs et ce qu'ils voient

Ils ne voient pas les images : seulement 262 variables calculées à partir de chaque observation, dans l'ordre, sans
l'avenir. Chaque enregistrement est jugé par des modèles qui ne l'ont jamais vu. Une fin est trouvée si une annonce
tombe sur l'intervalle de la vraie fin ou sur le suivant (une capture de retard tolérée).

- **GRU** : réseau récurrent qui garde en mémoire tout l'enregistrement lu jusque-là ; 5 graines (trouvée si au moins
  3 graines la trouvent).
- **Gradient boosting** et **régression logistique** : voient seulement la capture et les deux précédentes (leurs
  variables brutes côte à côte).
- **Règles écrites à la main** (`src/playend/training/baselines.py`, fonction `rules`) : une fin quand (a) la capture
  précédente avait un score total > 0 et celle-ci un score 0–0, dans le même jeu ; (b) le nombre de joueurs restants
  remonte de plus de 10 ; (c) la phase passe du jeu (active, post_game, intermediate) à menu, chargement ou
  avant-partie ; (d) le jeu change. « Précédente » veut dire la capture juste avant, lisible ou non.
- **Seuil** : choisi sur la validation de chaque tour pour garder au plus une fausse fin pour 100 parties. Il varie
  beaucoup d'un tour à l'autre (gradient boosting : souvent 0,97 à 0,99).

Comment les variables de changement sont calculées (`src/playend/contract/temporal.py`), point essentiel pour
comprendre les échecs :
- « même contexte » = même titre de jeu, même type et même mode que l'observation précédente ;
- variation du score (`score.a.delta_candidate`, `score.b...`) : seulement en même contexte, avec le même type de
  score, et si les deux scores sont lisibles. La « précédente » est la dernière observation, même illisible : une
  capture sans tableau de score entre deux matchs efface la variation ;
- variation du chrono (`clock.value_seconds.delta_candidate`) : seulement dans la même période, avec un type de
  période connu et un numéro connu (ou type `none`). Pour EA FC, la période est presque toujours `unknown` : la
  variation du chrono n'est jamais calculée ;
- `participants.primary.changed` : seulement si les deux listes sont non vides ; `game.title.changed`,
  `game.mode.changed`, `result.winner.changed` ;
- variations des compteurs (joueurs restants, vies, manches, séries), du tour (`progress.current`) et de la place,
  en même contexte seulement ;
- les nombres sont transformés par `sign(x)·log1p(|x|)` ; chaque valeur a une colonne `.known` (1 = calculée).

## Ton travail, pour chaque cas de ton lot

Le dossier `build/observations/fins_manquees/cas/<case_id>.json` donne : la partie, la capture qui prouve la fin, le
texte de preuve écrit au moment du placement, quels détecteurs l'ont trouvée, les seuils et les pics de probabilité,
puis pour chaque capture de la fenêtre (deux avant la fin de la partie jusqu'à deux après la preuve) : le chemin de
l'image originale (1280×720), le rôle de la capture, les probabilités du GRU, du gradient boosting et des règles, et
l'observation résumée. `nonzero_change_features` liste les variables de changement non nulles sur la capture avant
la preuve, la preuve et la suivante. La planche `cas/<case_id>.jpg` montre toutes ces captures avec leurs
probabilités.

1. Lis le dossier, puis **regarde la planche** (outil Read sur le .jpg). Ouvre les images originales dès qu'un détail
   compte (tableau de score, bandeau, menu, compteur) : ne conclus jamais sur une vignette illisible.
2. Dis ce qu'un humain voit qui prouve la fin, et si l'étiquette est juste (fin bien placée, vraie fin).
3. Compare avec ce que l'observation a noté : une erreur ou un oubli du professeur (écran de fin non marqué comme
   résultat, mauvais type d'écran, valeur mal lue, nom déduit) ?
4. Dis ce que les variables montraient au moment de la fin (en t'appuyant sur `nonzero_change_features` et sur les
   règles de calcul ci-dessus) et explique pourquoi le GRU l'a manquée, pourquoi le gradient boosting l'a manquée ou
   trouvée, pourquoi les règles l'ont trouvée ou non.
5. Donne la cause principale et les causes secondaires avec les codes ci-dessous, et la méthode qui aurait trouvé
   cette fin (convention d'annotation, variable, règle, modèle, données, seuil…), le plus concrètement possible.
6. Tu peux chercher en ligne pour comprendre l'interface d'un jeu (ce que signifie un bandeau, un compteur, le
   déroulé d'un championnat ou d'un menu de fin de match). Cite le lien si une recherche t'a servi.

Codes de cause (ajoute un code nouveau si aucun ne convient, en le définissant) :
- `REPRISE` : partie recommencée ou revanche avec les mêmes participants ; retour aux valeurs de départ, sans écran
  de fin ;
- `ECRAN_NON_MARQUE` : un écran ou un bandeau de fin (score final, « FIN DU MATCH », « VICTOIRE »…) est visible mais
  l'observation ne le marque pas comme résultat ;
- `FIN_ENTRE_CAPTURES` : la fin s'est produite entre deux captures ; la preuve est la partie suivante déjà commencée,
  avec d'autres participants ;
- `MENU_AMBIGU` : la preuve est une pause, un menu, un chargement ou l'accueil de la console, qui ressemble à une
  interruption en cours de partie ;
- `SIGNE_PROPRE_AU_JEU` : le signe de fin est propre au jeu (tour qui revient à 1, compteur de victoires, emplacements
  de manches…) et peu représenté ;
- `LECTURE_COUPEE` : une capture illisible ou sans tableau de score entre les deux casse les variations ;
- `CONTEXTE_SANS_VARIATION` : la variation existe à l'écran mais les règles de calcul ne la produisent pas (période
  inconnue, type de score différent, titre ou mode noté autrement) ;
- `SEUIL` : la probabilité monte nettement mais reste sous le seuil du tour ;
- `ERREUR_OBSERVATION` : le professeur a mal lu une valeur utile (score, chrono, écran, participants, jeu) ;
- `ETIQUETTE_DOUTEUSE` : la fin est mal placée ou n'en est pas une ;
- `ABANDON` : partie quittée pour l'accueil de la console, un autre jeu, une manette déconnectée ;
- `JEU_RARE` : jeu joué dans un seul enregistrement ;
- `AUTRE`.

## Règles

- N'écris jamais le pseudo d'un vrai joueur lu sur une image (escouades, fil des éliminations) : écris « un pseudo ».
  Les noms d'équipes, de combattants et les textes du jeu sont permis.
- Ne modifie aucun fichier du dépôt en dehors de `build/observations/fins_manquees/analyses/`.
- Ne lance aucun entraînement.

## Ce que tu rends

Dans `build/observations/fins_manquees/analyses/` :

1. `<lot>.jsonl` : une ligne JSON par cas, avec exactement ces clés :
   `case_id`, `etiquette` (`juste`, `douteuse` ou `fausse`), `ce_qui_prouve_la_fin` (ce qu'on voit à l'écran),
   `probleme_observation` (`aucun` ou la description), `signal_des_variables`, `pourquoi_gru`,
   `pourquoi_gradient_boosting`, `pourquoi_regles`, `cause_principale` (un code), `causes_secondaires` (liste de
   codes), `methode_qui_la_trouverait`, `confiance` (`haute`, `moyenne` ou `basse`), `images_ouvertes` (liste des
   numéros de captures ouvertes en taille réelle), `sources` (liens, ou liste vide).
2. `<lot>.md` : une section par cas (titre : le `case_id`), quelques phrases claires qui reprennent l'analyse, puis à
   la fin une synthèse du lot : les familles de causes vues, ce qui t'a surpris, et les méthodes qui reviennent.

**Écris au fur et à mesure.** Dès qu'un cas est fait, ajoute tout de suite sa ligne au `.jsonl` (et sa section au
`.md` s'il y en a une), en mode ajout, avant de passer au suivant ; avant de commencer un cas, regarde s'il est déjà
dans le `.jsonl` et passe-le si oui. Une coupure de connexion ne doit faire perdre qu'un cas.

Ta réponse finale (à l'équipe) : le nombre de cas analysés, la répartition des causes principales, et les trois
constats les plus importants de ton lot.
