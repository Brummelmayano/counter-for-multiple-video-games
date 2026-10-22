# Proposition : jeu de données publiable pour le GRU (format, schéma, Data Card)

**Statut : proposition à valider par l'utilisateur (2026-10-04). Rien n'est converti ni publié.** Les fichiers d'essai
(`datasets/v4_20261004/`, JSON Lines, et `runs/v4_20261004/`) sont gardés en local, non commités, en attendant.

Ce document s'appuie sur une recherche documentaire (sources numérotées [1]–[19] en fin de document, réutilisables
dans le mémoire). Chaque choix renvoie à ses sources.

---

## 1. Ce que dit la littérature, et ce que nous en retenons

| Question | Ce que disent les sources | Décision proposée |
|---|---|---|
| Quel format de fichier ? | Le CSV est un format *préféré* pour la conservation des jeux de données [13], normalisé par la RFC 4180 [11]. Les bonnes pratiques recommandent des formats ouverts, une colonne par variable et une ligne par observation [9, 10]. Hugging Face lit le CSV directement et ne recommande Parquet que pour plusieurs Go [18]. | **CSV** (RFC 4180, UTF-8, séparateur virgule, point décimal, une ligne d'en-tête). Nos fichiers font quelques Mo. |
| Quelle forme de tableau ? | « Données ordonnées » : une ligne par observation, une colonne par variable, une table par type d'unité observée [10]. Précédent proche : PAMAP2, une ligne horodatée par instant avec l'étiquette vraie et les mesures, un fichier par sujet, une notice des colonnes, valeurs manquantes signalées [14]. | **Une ligne par image capturée**, avec la session, le temps, les valeurs lues et les étiquettes. **Une table par type d'unité** : images, sessions, parties, passages au temps. |
| Publier les variables encodées ? | Publier seulement des variables pré-calculées empêche d'en construire d'autres et réduit la recherche à des comparaisons de modèles [17]. Il faut garder les données brutes, les résultats intermédiaires en format standard, et le code qui relie les deux [8, 16]. | **Fichier principal = valeurs lisibles** (score, chrono, période…). Les **262 variables v4** sont un fichier secondaire, avec le code qui les recrée. |
| Comment documenter ? | Toute base de données doit avoir sa fiche descriptive [3]. Les Data Cards résument les faits essentiels pour toutes les parties prenantes, organisés selon le cycle de vie (OFTEn) et 31 thèmes, avec des questions à trois niveaux de détail [1, 2]. Une étude de 7 433 fiches sur Hugging Face montre que la section « précautions d'usage » est la plus négligée (2,1 % du texte, même pour les jeux les plus téléchargés) [19]. | Une **Data Card** complète, selon le modèle officiel du Playbook [2], en **soignant particulièrement les limites, les risques et les usages déconseillés**. |
| Documentation lisible par les logiciels ? | Croissant décrit fichiers, colonnes, types et découpages, et est lu par Hugging Face, Kaggle et OpenML [4]. Son extension « IA responsable » documente collecte, annotation, données personnelles et limites [5]. NeurIPS 2026 l'**exige** pour toute soumission de jeu de données [6]. Le W3C propose aussi des métadonnées pour les CSV [12]. | Un fichier **`croissant.json` avec les champs RAI** et un **dictionnaire des colonnes** en CSV. |
| Où publier ? | Principes FAIR : identifiant pérenne, métadonnées riches, licence claire [7]. Dépôt avec DOI [9]. | **Zenodo** (DOI), plus éventuellement un miroir **Hugging Face**. |

---

## 2. Les fichiers proposés (paquet « v1.0 »)

```
<nom_du_jeu_de_donnees>_v1.0/
  README.md                      ← la Data Card (section 4)
  croissant.json                 ← métadonnées lisibles par les logiciels + champs IA responsable
  LICENSE
  data/
    observations.csv             ← FICHIER PRINCIPAL : 1 ligne par image capturée (valeurs lues + étiquettes)
    sessions.csv                 ← 1 ligne par session de capture
    units.csv                    ← 1 ligne par partie (début, fin, preuve, score final)
    time_segments.csv            ← 1 ligne par passage facturé au temps (avec sa raison)
    splits.csv                   ← session → pli d'évaluation (découpage par session, sans fuite)
    features.csv                 ← secondaire : les 262 variables encodées (clés + variables)
  dictionary/
    observations_columns.csv     ← dictionnaire : colonne, type, unité, valeurs permises, définition, exemple
    units_columns.csv, sessions_columns.csv, time_segments_columns.csv
    feature_spec.json            ← ordre et définition des 262 variables (encodage 4.0)
  code/                          ← scripts qui produisent tout le paquet depuis les observations JSON
```

### 2.1 `observations.csv` : une ligne par image

Les observations du contrat 2.1 contiennent des listes (participants, minuteurs, compteurs). Le CSV ne gère pas bien
les champs à valeurs multiples [15]. Je propose donc des **colonnes fixes** pour tout ce qui sert au comptage, et une
colonne texte JSON documentée seulement pour le détail.

| Groupe | Colonnes proposées | Remarques |
|---|---|---|
| Clés et temps | `session_id`, `frame_id`, `t_s` (secondes depuis la **première image de la session**, horloge monotone), `delta_t_s` (depuis l'image précédente de la même session) | Aucune heure réelle : elle est fausse (5.2). |
| Jeu | `game_title`, `game_family`, `game_type`, `game_mode`, `mode_duration` | `game_family` = famille stable (« EA Sports FC », « Mortal Kombat 1 »…). |
| Écran | `phase` (active, pre_game, post_game, menu, paused, loading, unknown…), `screen_type` | |
| Score | `score_a`, `score_b`, `score_type` (goals, rounds_won, points…) | Vide = illisible ou absent. |
| Chrono | `clock_visible`, `clock_display` (texte tel qu'affiché, ex. « 74:12 », « ∞ »), `clock_seconds`, `clock_direction` | |
| Période | `period_type`, `period_number`, `period_total` | |
| Progression et place | `progress_type`, `progress_current`, `progress_total`, `position_current`, `position_total` | Course : tour, place. |
| Résultat | `result_visible`, `result_outcome_type`, `result_winner` | |
| Compteurs de fin | `players_remaining`, `teams_remaining`, `lives_a`, `lives_b`, `target`, `series_a`, `series_b`, `counters_status` (inspecté / aucun / inconnu) | Mêmes emplacements que le contrat 2.1. |
| Minuteurs secondaires | `secondary_timer_kinds` (ex. « storm_phase », séparés par « \| »), `secondary_timer_min_seconds` | Détail complet dans `observation_json`. |
| Participants | `participants_count_visible`, `participant_a`, `participant_b` | Seulement les noms **écrits** sur l'image. Pseudos réels : voir D2. |
| Détail complet | `observation_json` | L'observation 2.1 entière, en texte JSON. |
| Provenance | `annotator` (GPT-6 Luna / Claude Opus 5.5), `corrected_by` (trace), `observation_review_status` | Transparence sur l'origine de chaque valeur. |
| **Étiquettes** | `unit_end_boundary` (0/1), `boundary_applicable` (vrai/faux), `uncertain_reason`, `current_unit_id`, `ended_unit_id`, `billing_mode` (partie / temps / hors_jeu), `label_review_status`, `label_confidence` | Ce que le GRU apprend. |

Conventions : cellule vide = valeur absente ou illisible (déclaré dans `croissant.json`) ; booléens `true`/`false` ;
noms de colonnes en anglais `snake_case` pour la réutilisation internationale. Les définitions sont en français et en
anglais dans le dictionnaire (voir D7).

### 2.2 Les autres tables

- `sessions.csv` : identifiant, durée, nombre d'images, intervalle de capture (aléatoire de 10 à 45 s),
  console (PS5, PS4), jeux présents, statut de validation.
- `units.csv` : reprend le `units.csv` existant de chaque session (début, dernière image, image qui établit la fin,
  type de fin, score final vu, confiance, preuve), avec le jeu et la famille.
- `time_segments.csv` : début, fin, jeu, raison (jeu de mission, île créative, entraînement ∞…).
- `splits.csv` : affectation de chaque session à un pli. Le découpage se fait **par session** pour éviter qu'un même
  match se retrouve à la fois en entraînement et en test. Croissant documente ce découpage [4].

---

## 3. Ce qui est déjà connu (chiffres actuels, régénérés automatiquement à la construction)

- Collecte : Raspberry Pi Zero 2 W + boîtier de capture USB (MacroSilicon MS2109), JPEG 1280×720, capture à
  intervalles aléatoires de 10 à 45 s, consoles PS5 et PS4, salle de jeux à Kinshasa, **septembre 2026** (selon
  l'utilisateur). Les dates « avril 2026 » des fichiers sont **fausses** : le Raspberry Pi n'avait ni pile d'horloge ni
  connexion internet (voir 5.2).
- 25 sessions avec frontières, 8 871 images : les 24 premières (7 952 images) et `fdb79549` (919 images). 23 sessions
  vérifiées par l'utilisateur : 7 413 intervalles, 239 fins de partie, environ 57 h de capture.
- Jeux : EA Sports FC, Fortnite, Mortal Kombat 1, Call of Duty: Warzone, Dragon Ball Sparking! ZERO, Genshin Impact,
  Red Dead Redemption 2, Tekken 8, EA Sports UFC 5, Naruto Storm Connections, Brawlhalla, Dragon Ball FighterZ,
  Demon Slayer, et dans `fdb79549` : Beach Buggy Racing 2, J-Stars Victory VS+, God of War, Assassin's Creed Origins.
- Annotateurs : GPT-6 Luna (premier « professeur ») puis Claude Opus 5.5, tous deux signés dans chaque observation.
- Validation humaine (2026-10-03) : toutes les fins et tous les passages au temps, et un échantillon de 463
  observations. Environ 1 % d'erreurs d'observation, aucune sur le score ou le chrono. 3 erreurs de frontière sur 257,
  toutes corrigées par des traces séparées.

---

## 4. Plan de la Data Card (modèle officiel du Playbook [2], organisé selon OFTEn [1])

Pour chaque section : ce que j'écrirai, et **ce qui manque**, c'est-à-dire ce qui vous revient.

### Origines (*Origins*)
1. **Résumé et auteurs** : nom, auteurs et affiliation (UNIKIN), contact, financement. Manque : D1 (nom), D8 (auteurs, contact).
2. **Motivations et usages prévus** : compter les parties pour facturer à la partie dans une salle de jeux, à partir
   d'observations d'un VLM, avec un GRU unique pour tous les jeux. Usages adaptés : recherche en détection de fins
   d'épisodes et en segmentation temporelle d'événements. **Usages déconseillés** : surveiller ou profiler des
   joueurs, facturer sans validation humaine, extrapoler à d'autres salles sans réévaluation.
3. **Accès, licence, conservation** : licence (D4), conditions d'usage, plan de maintenance et de versions.
4. **Provenance et collecte** : dispositif, intervalle aléatoire, dates, critères d'inclusion et d'exclusion (les
   nouvelles sessions écartées et pourquoi), consentement (D5).

### Faits (*Factuals*)
5. **Aperçu et statistiques** : nombre de sessions, d'images, de parties ; répartition par jeu et par famille ;
   proportion de fins (environ 1 pour 30) ; durées des parties ; valeurs manquantes par colonne.
6. **Exemples de données** : une ligne typique (un match FC en cours) et des cas atypiques (écran noir, île
   d'attente Fortnite, partie d'une seule capture, « ∞ » de MK1).
7. **Attributs sensibles** : pseudos de joueurs, noms d'utilisateur PSN sur l'accueil, horaires de présence dans la salle (D2, D3).

### Transformations
8. **Annotation et étiquetage** : observations produites par deux VLM « professeurs » (*machine-generated*), selon
   un contrat écrit (règles par jeu) ; frontières de parties placées par Claude et **vérifiées par l'utilisateur**
   (*expert*) ; règles de comptage fixées par l'utilisateur ; corrections par traces séparées, jamais par écrasement.
9. **Validation** : méthode et résultats de la validation humaine (taux d'erreur par jeu, erreurs trouvées et corrigées).
10. **Encodage des variables v4** : transformation logarithmique fixe, sans statistique apprise, donc sans fuite d'information.

### Expérience (*Experience*)
11. **Applications connues et références** : résultats d'un modèle de référence quand l'entraînement sera autorisé,
    avec la référence triviale (« jamais de fin » : 96,8 % d'exactitude mais 0 partie comptée).
12. **Limites et risques**, la section la plus négligée en pratique [19] :
    - une seule salle et 4 jours, des jeux très inégalement représentés (FC et Fortnite dominent) ;
    - observations non vérifiées une à une ;
    - des fins sans écran de fin, établies par le retour à 0–0 ;
    - l'intervalle de capture limite la mesure des durées courtes ;
    - le risque commercial de facturer une partie de trop.

### Exemples (*n = 1*)
13. Liens vers des exemples commentés et vers le code de reproduction.

### Questions du modèle de cours (Data Cards, Google Skills)
Je les reprends telles quelles dans la Data Card, avec nos réponses :
- **Entrée et sortie** : observations structurées extraites d'images de jeu ; sorties = fin de partie (0/1) et mode de facturation.
- **Problème de classification** : binaire déséquilibré (fin / pas de fin) et à 3 classes (partie, temps, hors jeu).
- **Étiquetage** : utilisateur expert de la salle, avec un échantillon pour mesurer la cohérence.
- **Création des données** : capture directe sur console, sans données synthétiques.
- **Collecte sur le web** : aucune (point à préciser pour les images des jeux, voir D6).
- **Biais et représentation** : une salle de Kinshasa, des jeux populaires localement ; c'est une contribution sur
  un contexte africain peu représenté, mais pas une représentation de tous les joueurs.
- **Valeurs et communauté** : protection du client (jamais de facture en trop) et transparence de la facturation.

---

## 5. Décisions qui vous reviennent avant la construction

| N° | Décision | Pourquoi c'est important |
|---|---|---|
| D1 | Nom du jeu de données | Il sera cité dans le mémoire et via le DOI. |
| D2 | Pseudos de joueurs réels (escouades Warzone/Fortnite, PSN) : **remplacer par des identifiants anonymes** (`joueur_01`…) ou retirer ? Les noms de personnages et d'équipes du jeu (« Mileena », « Real Madrid ») ne sont pas des données personnelles. | Données personnelles ; question explicite des Data Cards et des fiches descriptives [1, 3]. |
| D3 | Heure réelle de capture : garder la date et l'heure, garder seulement la date, ou seulement le temps relatif (`elapsed_s`) ? | Les horaires révèlent la présence des clients dans la salle. |
| D4 | Licence : CC BY 4.0 (réutilisation libre) ou CC BY-NC 4.0 (pas d'usage commercial) ? | Elle conditionne la réutilisation ; obligatoire pour FAIR [7]. |
| D5 | Les clients de la salle ont-ils été informés de la capture d'écran ? Faut-il un affichage ou un consentement pour les captures futures ? | Section « consentement » de la Data Card [1, 2]. |
| D6 | Les **images** (jeu de données de distillation) feront-elles partie de la publication ? Leur droit d'auteur appartient aux éditeurs. Des publications récentes d'images de jeux ne licencient que leurs propres annotations, réservent l'accès à la recherche non commerciale et laissent les droits sur le contenu aux éditeurs. **À vérifier en détail** avant de décider. | Le CSV du GRU ne contient pas d'images, donc ce risque est faible pour lui. |
| D7 | Langue de la Data Card : français, anglais, ou les deux ? | Mémoire en français, réutilisation internationale en anglais. |
| D8 | Auteurs, affiliation, contact, financement. | Section « Authorship ». |
| D9 | Contenu de la v1.0 : les 23 sessions vérifiées seulement, ou attendre la validation de 8e58b1 et `fdb79549` (25 sessions) ? | Toutes les étiquettes publiées doivent être vérifiées. |
| D10 | Dépôt : Zenodo seul, ou Zenodo et Hugging Face ? | DOI et visibilité. |

---

### 5.1 Décisions prises par l'utilisateur (2026-10-04)

| N° | Décision |
|---|---|
| D2 | Les **vrais pseudos de joueurs** sont remplacés par des identifiants anonymes stables (`player_001`…) : 25 pseudos distincts dans Fortnite et 30 dans Warzone (escouades, spectateur, panneau Social), et les noms d'utilisateur PSN sur l'accueil de la console. Les noms de personnages (« Scorpion ») et d'équipes (« PSG ») restent : ce sont des contenus du jeu. Le remplacement vaut dans `observations.csv`, dans `observation_json` et dans les autres tables. |
| D4 | **CC BY-NC 4.0** (pas d'usage commercial). Un guide universitaire de choix de licence la recommande justement quand les participants ont été informés qu'il n'y aurait pas d'usage commercial [29]. La licence ne couvre que **notre travail** (observations, étiquettes, documentation) : le contenu des jeux reste la propriété des éditeurs, comme l'écrit OGameData [21]. |
| D1 | **Nom : PlayEnd.** |
| D5 | **Les clients étaient informés et ont donné leur accord oral.** Certains ont accepté de jouer à des jeux sous-représentés pour qu'ils soient capturés. À écrire dans la Data Card : c'est un consentement oral, et aussi une **sélection volontaire des jeux** à documenter dans « méthode d'échantillonnage », car elle influence la répartition des jeux. |
| D6 | **Publication en deux temps** (5.3) : d'abord le CSV du GRU, ensuite les images floutées, en accès contrôlé. |
| D7 | **Data Card finale en anglais.** Ce document reste en français pour le travail. |
| D8 | **Auteurs** : **Brummel D. Mayano** (ORCID 0009-0008-5433-5259) et **Jordan F. Masakuna** (ORCID 0000-0001-6165-8402) — ORCID repris de l'article IEEE Access 2025 (doi:10.1109/ACCESS.2025.3542425) via Crossref [30]. **Affiliation (en anglais, décision de l'utilisateur) : Department of Mathematics, Statistics and Computer Science, University of Kinshasa, Kinshasa, Democratic Republic of the Congo.** Aucun laboratoire ni financement mentionné (décision de l'utilisateur). Contact : brummelmayano@gmail.com. |
| D9 | **Attendre la validation** de 8e58b1 et `fdb79549` : la v1.0 contiendra les 25 sessions. Serveur de validation lancé le 2026-10-04 avec les 155 éléments de `fdb79549`. |
| D10 | **Zenodo + Hugging Face** : Zenodo pour la version officielle citée (DOI, conservation par le CERN), Hugging Face en miroir pour les chercheurs en IA. |

### 5.1 bis Décisions issues de la validation de `fdb79549` (2026-10-04)

- **Beach Buggy Racing 2** : position vide en écran partagé (plusieurs coureurs contrôlés), places de chaque vue en
  note. Trace `20261004_22`, 170 images.
- **Dragon Ball Sparking! ZERO** : les barres de vie restantes (blocs près du portrait, « le nombre de barres de vie
  restantes est indiqué dans le coin gauche » selon le guide officiel [39]) deviennent un compteur `lives` a/b, sur les
  337 images de combat (relecture par un agent, traces `20261004_23_*`).
- **J-Stars Victory VS+** : la jauge de victoire est bien la condition de fin (première équipe à 3 cases ; 2 ou 1 case
  dans certains combats d'histoire ; au temps écoulé, l'équipe avec le plus de cases gagne) [40, 41]. Convention
  actuelle confirmée.
- **Titre du jeu sur les images sans indice** (ex. cinématique de nuages de God of War, image 538) : l'utilisateur
  choisit de **laisser tel quel**. À écrire dans la Data Card comme **limite connue** : sur certaines cinématiques,
  chargements ou écrans noirs, le titre du jeu vient du contexte (images voisines) et non de l'image seule.

### 5.2 D3, le temps : l'heure réelle est fausse, le temps relatif est fiable

**Ce que l'utilisateur a observé, et que les données confirment.**
- Le Raspberry Pi n'avait **ni pile d'horloge (RTC) ni internet**. Sous Linux, l'outil `fake-hwclock` enregistre l'heure
  toutes les heures et à l'arrêt, puis la **recharge au démarrage** : l'horloge repart de l'heure d'arrêt, quel que soit
  le temps réellement écoulé [31].
- Dans nos 29 sessions, chacune commence par un **nouveau démarrage** (`boot_id` différent), et la première image d'une
  session arrive toujours **2 à 3,5 minutes** (selon l'horloge) après la dernière de la précédente, soit le temps de
  démarrage. L'écart réel pouvait être de plusieurs jours. Aucune session n'a été synchronisée sur l'heure réelle
  (`ntp_synchronized_at_start = false` partout). Les dates « 17–20 avril 2026 » sont donc fictives ; la capture a eu
  lieu en **septembre 2026**.

**Ce qui reste fiable.** À l'intérieur d'une session, les temps viennent de l'horloge **monotone** du système
(`received_monotonic_ns`, `elapsed_s`). Sous Linux, elle compte les secondes depuis le démarrage et **n'est pas affectée
par les sauts de l'heure système** [32]. Comme chaque session correspond à un démarrage, les écarts entre images d'une
même session sont justes.

**Décision proposée (conforme à la remarque de l'utilisateur).**
- `t_s` = **0 à la première image de chaque session**, puis les secondes écoulées selon l'horloge monotone ;
  `delta_t_s` = écart avec l'image précédente de la même session (vide pour la première).
- **Aucune heure réelle** dans les fichiers publiés : elle est fausse, et la retirer protège aussi les clients.
  Dans la Data Card : « septembre 2026, Kinshasa », avec l'explication de l'horloge.
- Aucun écart entre sessions n'est publié : il est inconnu.
- L'outil de validation affiche désormais le temps depuis le début de la session, et non plus la fausse date (2026-10-04).

### 5.5 Les sessions : un seul fichier, mais des séquences séparées

Question de l'utilisateur : faut-il garder les données en plusieurs sessions, ou les rassembler en respectant le temps ?

- **Rassembler dans un seul fichier : oui.** C'est la forme « longue » recommandée pour les séries temporelles multiples :
  une colonne identifie la séquence (`session_id`) et une colonne donne l'ordre (`frame_id`, `t_s`) [33]. C'est aussi
  la règle des données ordonnées : une seule table par type d'unité observée [10].
- **Mettre les sessions bout à bout en une seule chronologie : non.**
  1. L'écart réel entre deux sessions est inconnu (5.2), et une chronologie continue serait fausse.
  2. Les sessions sont indépendantes (console éteinte, autres clients, autre jour). Si on les enchaîne, le GRU verrait un
     faux passage « fin de session → début de session » : il pourrait y apprendre une fausse fin de partie ou une fausse
     continuité. Avec des séquences indépendantes, l'état caché du réseau doit repartir de zéro au début de chacune [34].
     C'est déjà le cas dans le préparateur v4 (variable `sequence_start`).
  3. Pour évaluer honnêtement, il faut découper **par session** : une même session ne doit pas être à la fois dans
     l'entraînement et le test. C'est ce qu'évite la « fuite d'information » [35], et que fait la validation croisée
     par groupes [36]. D'où le fichier `splits.csv`.
- En pratique : **un seul `observations.csv`** trié par `session_id` puis `frame_id`, avec `t_s` remis à 0 à chaque
  session. On garde à la fois la simplicité d'un fichier unique et l'intégrité temporelle de chaque séquence.

### 5.6 D10, où publier : Zenodo, Hugging Face ou Kaggle ?

| | **Zenodo** | **Hugging Face** | **Kaggle** |
|---|---|---|---|
| Qui | Dépôt de recherche du CERN, financé par l'Union européenne | Plateforme de l'apprentissage automatique (entreprise) | Plateforme de Google (concours, carnets) |
| DOI | Oui, pour chaque dépôt et chaque version [37] | Oui, via DataCite, sur demande [38] | Possible pour les jeux de données (mentionné par ses utilisateurs, à vérifier) |
| Conservation | Garantie pour la durée de vie du CERN (programme d'au moins 20 ans), sauvegardes chaque nuit, deux centres [37] | Pas de garantie formelle équivalente ; un jeu avec DOI ne peut plus être supprimé sans demande [38] | Pas de garantie de conservation publiée |
| Accès contrôlé | Oui : fichiers en accès restreint, accordés par le déposant [37] | Oui : jeu « à accès contrôlé », l'utilisateur accepte les conditions [28] | Partage privé avec des utilisateurs choisis |
| Points forts | Citation dans le mémoire, conservation, versions | Visionneuse, chargement direct (`datasets`), Croissant, communauté IA [18] | Visibilité, carnets d'analyse, concours |

**Recommandation.** **Zenodo comme dépôt de référence** : c'est son DOI qui sera cité dans le mémoire et les
articles. **Hugging Face en miroir** pour les chercheurs en IA, et plus tard pour les images en accès contrôlé.
Kaggle n'est pas nécessaire : un troisième dépôt ajouterait de la maintenance sans apporter de garantie
supplémentaire. On pourra l'ajouter plus tard pour la visibilité.

### 5.3 D6, publier les images : analyse

**Droit d'auteur.** Les images de jeux appartiennent aux éditeurs (EA, Epic, Activision, Bandai Namco…).
- Le droit de la RDC (ordonnance-loi n° 86-033) autorise les **citations et extraits** d'œuvres à des fins
  scientifiques ou d'enseignement, avec la source et l'auteur (art. 24), et les photographies dans les ouvrages
  scientifiques (art. 25). Il n'a pas d'exception générale de type *fair use* [20]. Publier des milliers d'images
  complètes dépasse probablement la simple « citation ». Le risque juridique n'est donc pas nul.
  *Ce n'est pas un avis juridique : à faire confirmer par le service juridique de l'université si possible.*
- Les éditeurs tolèrent l'usage non commercial : la politique « Fan Content » d'Epic autorise l'usage personnel non
  commercial des images de Fortnite dans un cadre défini [25], et EA dit ne pas s'opposer aux usages loyaux de ses
  captures, avec un formulaire de demande d'autorisation pour l'usage éducatif [26].

**Ce que font les travaux publiés.**
- OGameData (GameGen-X, 2024) : « le droit d'auteur reste aux propriétaires », usage réservé à la recherche, aucun
  usage commercial, et seulement des identifiants de vidéos YouTube, pas les vidéos [21].
- VideoGameBunny (WACV 2025) publie 185 259 images de 413 jeux sur Hugging Face, sans discuter du droit d'auteur [22].
  La pratique existe donc, mais elle est mal documentée.
- GlitchBench (CVPR 2024) a retiré les images montrant le visage de streamers, pour protéger leur vie privée [23].
- *Playing for Data* (ECCV 2016) a publié 25 000 images de GTA V, très utilisées depuis [24].

**Vie privée.** Les images montrent les pseudos de joueurs, ce qui contredirait D2. En vision par ordinateur, on
floute ce qui identifie les personnes : flouter les visages dans ImageNet ne fait perdre que 1 % de précision au
plus [27]. Ici, il faudrait **flouter les pseudos** dans les images (listes d'escouade, spectateur, accueil PSN).

**Recommandation pour D6.**
1. Publier d'abord le **jeu de données du GRU** (CSV, sans images), en accès libre sous CC BY-NC 4.0 : risque faible.
2. Publier les **images** (jeu de données de distillation) à part, avec quatre conditions :
   - les pseudos floutés ;
   - CC BY-NC 4.0 pour nos annotations seulement, avec la mention « le contenu des jeux reste la propriété de leurs éditeurs » ;
   - un **accès contrôlé** sur Hugging Face, où l'utilisateur accepte les conditions (recherche, pas d'usage commercial) avant de télécharger [28] ;
   - éventuellement une demande d'autorisation aux principaux éditeurs.

### 5.4 D1, propositions de noms (aucun jeu de données existant trouvé sous ces noms)

| Nom | Idée |
|---|---|
| **KinPlay** | *Kin*shasa + *play* : court, facile à citer, rappelle l'origine du jeu de données. |
| **ArenaCount** | Fait le lien avec votre article IEEE Access sur le compteur de parties en salle de jeux. |
| **PlayEnd** | Insiste sur la tâche : détecter la fin d'une partie. |
| **GameRoom-KIN** | Très descriptif : une salle de jeux à Kinshasa. |

Exemple de titre complet : *« KinPlay: Console Gameplay Sessions from a Kinshasa Gaming Room for End-of-Match
Detection and Billing »*.

### 5.7 Choix de l'export confirmés (2026-10-05)

Export : `python -m playend.dataset.export` écrit `build/playend_v1.0/`. Chaque choix a été revu au regard de notre
but (un GRU qui trouve les fins de partie sans en inventer) et de la littérature.

| Choix | Pourquoi | Sources |
|---|---|---|
| Une ligne par image, `session_id` pour la séquence, `t_s` remis à 0 à chaque session | C'est la forme des séries temporelles médicales de référence : une ligne par pas de temps, temps compté depuis le début du séjour (`ICULOS`), une étiquette par ligne. | [33, 43] |
| `t_s` et `delta_t_s` exacts à la nanoseconde | Les intervalles de capture sont irréguliers (10 à 45 s) ; le GRU reçoit Δt en entrée, comme GRU-D, et les 262 variables se recalculent exactement depuis le CSV. | [42] |
| Cellule vide = valeur absente, avec les masques `.known` dans `features.csv` | Convention par défaut de Table Schema (`missingValues = [""]`) ; GRU-D montre que l'absence elle-même renseigne sur la cible. | [42, 49] |
| La fin est placée sur la première image qui la prouve ; l'étiquette d'une ligne décrit l'intervalle (image précédente, image] | Un détecteur en ligne doit voir la nouvelle donnée avant de dire qu'un changement a eu lieu entre l'ancienne et la nouvelle. | [44] |
| Première image d'une session : pas de cible de fin, `boundary_applicable = false` | Aucun intervalle ne la précède ; la perte se masque, comme pour tout pas sans cible. | [42] |
| Masque d'apprentissage = `boundary_applicable` des étiquettes validées | Les fins et les passages au temps sont vérifiés à la main ; les observations, elles, sont des sorties du professeur, comme le seront sur le Pi celles du VLM élève. Exiger des observations vérifiées une à une masquerait tout. | — |
| Évaluation avec une tolérance d'une observation | Déjà décidé pour le GRU ; l'évaluation des détecteurs de changement compte juste une détection proche de la vraie position. | [45] |
| `splits.csv` : 5 plis, chaque session entière dans un pli, équilibrés sur les fins et les images | Découper par groupe évite la fuite ; il faut aussi représenter les données de façon équilibrée entre les plis. La session `f00675` porte 23 % des fins : un équilibre parfait est impossible. | [35, 36, 46, 48] |
| Recommandation pour l'évaluation finale : une session tenue à l'écart à chaque fois (25 plis), les 5 plis servant au choix du seuil | Avec des groupes, « chaque bloc devrait être son propre pli » pour garder le plus de données d'entraînement ; c'est la pratique en reconnaissance d'activité (un sujet tenu à l'écart). À décider avec l'entraînement. | [46, 47] |
| `billing_mode` publié en anglais : `per_game`, `time_based`, `not_billed` | Décision de l'utilisateur ; « time-based » est le terme des logiciels de salles de jeux. Les étiquettes internes gardent `partie`, `temps`, `hors_jeu`. | [51] |
| Pseudos : un par nom (sans tenir compte des majuscules), liste privée jamais publiée | Des données pseudonymisées restent personnelles tant que la correspondance existe : la liste doit rester à part. | [50] |
| Toutes les observations en contrat 2.1 | Les 3 049 observations 2.0 ont reçu leurs compteurs (traces `20261004_24_*`) : plus aucun compteur « inconnu » par défaut de contrat, seulement quand le HUD est caché. | — |

### 5.8 Rédaction de la Data Card (2026-10-05)

La Data Card (`docs/dataset/DATA_CARD.md`) suit les sections du modèle officiel du Playbook [2], en gardant celles qui
concernent PlayEnd, avec l'en-tête YAML que lit Hugging Face (licence, sous-ensembles `configs`) [56]. À la demande de
l'utilisateur, elle évite ce que la littérature associe aux textes écrits par un grand modèle de langue :

- le vocabulaire en excès depuis 2023 dans 15 millions de résumés PubMed (*delves*, *underscores*, *showcasing*,
  *pivotal*, *intricate*, *crucial*…, 291 mots de la liste de Kobak et al.) [52] ;
- les tournures relevées par Wikipedia : « serves as » au lieu de « is », parallélismes négatifs (« not just X, but
  Y »), règle de trois, incises en « -ing » qui commentent la phrase, tirets cadratins, gras, listes à petits titres,
  titres en majuscules, conclusions générales sur « les défis et les perspectives » [54] ;
- le style dense en noms des modèles réglés par instruction : deux à cinq fois plus de propositions participiales
  présentes, 1,5 à 2 fois plus de nominalisations, deux fois moins de passifs sans agent que les textes humains [53].

Un script de vérification (hors du dépôt) compte ces marques ; la version finale ne contient aucun mot de ces
listes, aucun tiret cadratin, aucun gras ni aucune liste à petits titres, et la longueur
des phrases varie comme dans un texte humain (21 mots en moyenne, écart type 13). La fiche donne des chiffres précis,
des exemples réels et des limites propres à PlayEnd plutôt que des formules générales [55].

## 6. Étapes après votre accord (une à la fois, chacune sur votre feu vert)

1. Écrire le script d'export CSV et le dictionnaire des colonnes, puis vous montrer quelques lignes réelles.
2. Rédiger la Data Card complète. *Fait le 2026-10-05 : `docs/dataset/DATA_CARD.md`, copiée en `README.md` du paquet par l'export, qui vérifie ses chiffres.*
3. Produire `croissant.json` (avec les champs RAI) et le valider avec l'outil officiel. *Fait le 2026-10-05 : généré par l'export à partir du dictionnaire et de `docs/dataset/croissant_metadata.json` (Croissant 1.1 et RAI 1.0, champs minimaux de NeurIPS 2026), validé sans erreur ni avertissement par `mlcroissant` 1.1.0, et les 7 tables se chargent avec lui. Reste l'adresse `url`, à remplir au dépôt [57–59].*
4. Relecture finale par vous, puis dépôt. *Fait le 2026-10-05 : publié sur Zenodo, [doi:10.5281/zenodo.23159322](https://doi.org/10.5281/zenodo.23159322), dépôt n° 23159322 (archive `playend_v1.0.zip`, empreinte md5 4dd8f529a8f90d63b70255bc85dd209e), avec `python -m playend.dataset.zenodo`. Une correction se publiera comme nouvelle version de ce dépôt. Le miroir Hugging Face reste à faire.*

---

## Sources

1. Pushkarna, M., Zaldivar, A., Kjartansson, O. (2022). *Data Cards: Purposeful and Transparent Dataset Documentation for Responsible AI*. FAccT '22. https://doi.org/10.1145/3531146.3533231
2. Google PAIR. *Data Cards Playbook* et modèle `DataCardsExtendedTemplate.md`. https://sites.research.google/datacardsplaybook/ ; https://github.com/PAIR-code/datacardsplaybook/tree/main/templates
3. Gebru, T. et al. (2021). *Datasheets for Datasets*. Communications of the ACM 64(12), 86–92. https://arxiv.org/abs/1803.09010
4. Akhtar, M. et al. (2024). *Croissant: A Metadata Format for ML-Ready Datasets*. https://arxiv.org/abs/2403.19546
5. Jain, N. et al. (2024). *A Standardized Machine-readable Dataset Documentation Format for Responsible AI* (Croissant-RAI). https://arxiv.org/abs/2407.16883
6. NeurIPS (2026). *Responsible AI metadata requirements for the Evaluations and Datasets Track*. https://blog.neurips.cc/2026/05/04/responsible-ai-metadata-requirements-for-the-evaluations-and-datasets-track-neurips-2026/
7. Wilkinson, M. D. et al. (2016). *The FAIR Guiding Principles for scientific data management and stewardship*. Scientific Data 3, 160018. https://doi.org/10.1038/sdata.2016.18
8. Sandve, G. K. et al. (2013). *Ten Simple Rules for Reproducible Computational Research*. PLOS Comput. Biol. 9(10). https://pmc.ncbi.nlm.nih.gov/articles/PMC3812051/
9. Wilson, G. et al. (2017). *Good enough practices in scientific computing*. PLOS Comput. Biol. 13(6), e1005510. https://doi.org/10.1371/journal.pcbi.1005510
10. Wickham, H. (2014). *Tidy Data*. Journal of Statistical Software 59(10). https://vita.had.co.nz/papers/tidy-data.html
11. Shafranovich, Y. (2005). *RFC 4180: Common Format and MIME Type for CSV Files*. https://datatracker.ietf.org/doc/html/rfc4180
12. W3C (2015). *Metadata Vocabulary for Tabular Data* (CSV on the Web). https://www.w3.org/TR/tabular-metadata/
13. Library of Congress. *Recommended Formats Statement — Datasets*. https://loc.gov/preservation/resources/rfs/data.html
14. Reiss, A., Stricker, D. (2012). PAMAP2 Physical Activity Monitoring (UCI). https://archive.ics.uci.edu/dataset/231/pamap2+physical+activity+monitoring
15. Hugging Face. *LLM Dataset Formats 101* (CSV et champs à valeurs multiples). https://huggingface.co/blog/tegridydev/llm-dataset-formats-101-hugging-face
16. Tierney, N. J., Ram, K. (2020). *A Realistic Guide to Making Data Available Alongside Code to Improve Reproducibility*. https://arxiv.org/abs/2002.11626
17. Holland, J. et al. (2022). *Towards Reproducible Network Traffic Analysis*. https://arxiv.org/abs/2203.12410
18. Hugging Face. *Adding datasets / Dataset viewer* (formats acceptés, recommandations). https://huggingface.co/docs/hub/datasets-adding
19. Yang, X., Liang, W., Zou, J. (2024). *Navigating Dataset Documentations in AI: A Large-Scale Analysis of Dataset Cards on Hugging Face*. ICLR 2024. https://arxiv.org/abs/2401.13822
20. République démocratique du Congo. *Ordonnance-loi n° 86-033 du 5 avril 1986 portant protection des droits d'auteur et des droits voisins*, art. 24–32 (WIPO Lex). https://www.wipo.int/wipolex/en/legislation/details/7511 ; texte : https://wipolex-res.wipo.int/edocs/lexdocs/laws/fr/cd/cd005fr.pdf
21. Che, H. et al. (2024). *GameGen-X: Interactive Open-world Game Video Generation* (jeu de données OGameData). https://arxiv.org/abs/2411.00769
22. Taesiri, M. R., Bezemer, C.-P. (2025). *VideoGameBunny: Towards vision assistants for video games*. WACV 2025. https://arxiv.org/abs/2407.15295 ; jeu de données : https://huggingface.co/datasets/asgaardlab/VideoGameBunny-Dataset
23. Taesiri, M. R. et al. (2024). *GlitchBench: Can Large Multimodal Models Detect Video Game Glitches?* CVPR 2024. https://arxiv.org/abs/2312.05291
24. Richter, S. R., Vineet, V., Roth, S., Koltun, V. (2016). *Playing for Data: Ground Truth from Computer Games*. ECCV 2016. https://arxiv.org/abs/1608.02192
25. Epic Games. *Fan Content Policy*. https://legal.epicgames.com/epicgames/fan-art-policy
26. Electronic Arts. Position publique sur les vidéos et captures d'écran (forum officiel EA Answers) et formulaire d'autorisation permissionrequests@ea.com. https://answers.ea.com/t5/STAR-WARS-Battlefront/Monetizing-Star-Wars-Battlefront-II-gameplay-videos-on-Youtube/m-p/7895111 *(source de forum : à remplacer par la politique officielle si elle est trouvée)*
27. Yang, K., Yau, J., Fei-Fei, L., Deng, J., Russakovsky, O. (2022). *A Study of Face Obfuscation in ImageNet*. ICML 2022. https://arxiv.org/abs/2103.06191
28. Hugging Face. *Gated datasets*. https://huggingface.co/docs/hub/datasets-gated
29. Université de Groningue. *Choosing a licence for your dataset*. https://www.rug.nl/digital-competence-centre/research-data/archive-and-publish/how-to-work-with-dataversenl/choosing-a-licence-for-your-dataset
30. Mayano, B. D., Yan-Mol, L. L., Masakuna, J. F. (2025). *Intelligent Match Counter in a Video Game Arena*. IEEE Access 13, 32320–32328. https://doi.org/10.1109/ACCESS.2025.3542425 (métadonnées et ORCID : https://api.crossref.org/works/10.1109/ACCESS.2025.3542425)
31. Debian. *fake-hwclock(8)* : sauvegarde et restauration de l'heure sur les machines sans horloge matérielle. https://manpages.debian.org/unstable/fake-hwclock/fake-hwclock.8.en.html
32. Linux man-pages. *clock_gettime(3)* : CLOCK_MONOTONIC n'est pas affecté par les sauts de l'heure système. https://man7.org/linux/man-pages/man3/clock_gettime.3.html
33. tsfresh. *Data Formats* (format long : colonne d'identifiant et colonne de tri, pas de temps non équidistants admis). https://tsfresh.readthedocs.io/en/main/text/data_formats.html
34. Forum PyTorch. *Beneficial to call detach vs zero-initialize between batches* (ne pas transmettre l'état caché entre séquences indépendantes). https://discuss.pytorch.org/t/beneficial-to-call-detach-vs-zero-initialize-between-batches/6135
35. Kaufman, S., Rosset, S., Perlich, C., Stitelman, O. (2012). *Leakage in Data Mining: Formulation, Detection, and Avoidance*. ACM TKDD 6(4). https://doi.org/10.1145/2382577.2382579
36. scikit-learn. *GroupKFold* (un même groupe n'est jamais à la fois en entraînement et en test). https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html
37. Zenodo. *Policies* (CERN, conservation, DOI, versions, accès restreint, 50 Go par dépôt). https://about.zenodo.org/policies/
38. Hugging Face. *Digital Object Identifier (DOI)*. https://huggingface.co/docs/hub/doi
39. Bandai Namco Entertainment Europe. *DRAGON BALL: Sparking! ZERO — The Beginner's Guide* (« the amount of remaining HP bars is indicated in the left corner »). https://en.bandainamcoent.eu/dragon-ball/news/dragon-ball-sparking-zero-the-beginners-guide ; voir aussi NoobFeed, *Understanding the HUD*. https://www.noobfeed.com/articles/dragon-ball-sparking!-zero-understanding-the-hud
40. Dustloop. *J-Stars Victory VS+ players guide* (jauge de victoire : un point par KO, première équipe à 3 points). https://www.forums.dustloop.com/topic/8519-j-stars-victory-vs-players-guide-discussion/
41. JoJo Wiki. *J-Stars Victory VS+* (cases de la jauge, combats d'histoire à 2 ou 1 case, minuteur de 300 s, départage au temps). https://jojowiki.com/J-Stars_Victory_VS%2B

42. Che, Z., Purushotham, S., Cho, K., Sontag, D., Liu, Y. (2018). *Recurrent Neural Networks for Multivariate Time Series with Missing Values*. Scientific Reports 8, 6085. https://doi.org/10.1038/s41598-018-24271-9
43. Reyna, M. A. et al. (2020). *Early Prediction of Sepsis From Clinical Data: The PhysioNet/Computing in Cardiology Challenge 2019*. Critical Care Medicine 48(2), 210–217 (PMID 31939789) ; données : une ligne par heure, `ICULOS` = « hours since ICU admit ». https://physionet.org/content/challenge-2019/1.0.0/
44. Aminikhanghahi, S., Cook, D. J. (2017). *A survey of methods for time series change point detection*. Knowledge and Information Systems 51(2), 339–367 (« no change point detection algorithm operates in perfect real time because it must inspect new data before determining if a change point occurred between the old and new data points »). https://doi.org/10.1007/s10115-016-0987-z
45. van den Burg, G. J. J., Williams, C. K. I. (2020). *An Evaluation of Change Point Detection Algorithms*. arXiv:2003.06222 (détection juste si elle tombe à moins de M points de la vraie position). https://arxiv.org/abs/2003.06222
46. Roberts, D. R. et al. (2017). *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*. Ecography 40(8), 913–929 (« We recommend that block cross-validation be used wherever dependence structures exist » ; p. 919 : « each block should be its own fold » ; « representing predictors equally across blocks or folds »). https://doi.org/10.1111/ecog.02881
47. Gholamiangonabadi, D., Kiselov, N., Grolinger, K. (2020). *Deep Neural Networks for Human Activity Recognition With Wearable Sensors: Leave-One-Subject-Out Cross-Validation for Model Selection*. IEEE Access 8, 133982–133994. https://doi.org/10.1109/ACCESS.2020.3010715
48. scikit-learn. *StratifiedGroupKFold* (« avoid building folds with imbalanced class proportions »). https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html
49. Frictionless Data. *Table Schema* (« The default value `[ "" ]` means that empty strings will be converted to null » ; booléens `true` / `false`). https://specs.frictionlessdata.io/table-schema/
50. European Data Protection Board (2025). *Guidelines 01/2025 on Pseudonymisation* (les données pseudonymisées restent des données personnelles). https://www.edpb.europa.eu/
51. izi.is. *Time-Based Pricing for Gaming Clubs* (vocabulaire des logiciels de salles de jeux). https://izi.is/wiki/en/tariffs/pricing-by-time/
52. Kobak, D., González-Márquez, R., Horvát, E.-Á., Lause, J. (2025). *Delving into LLM-assisted writing in biomedical publications through excess vocabulary*. Science Advances 11(27), eadt3813. https://doi.org/10.1126/sciadv.adt3813
53. Reinhart, A., Markey, B., Laudenbach, M., Pantusen, K., Yurko, R., Weinberg, G., Brown, D. W. (2025). *Do LLMs write like humans? Variation in grammatical and rhetorical styles*. PNAS 122(8), e2422455122. https://doi.org/10.1073/pnas.2422455122
54. Wikipedia, WikiProject AI Cleanup. *Signs of AI writing*. https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
55. Liang, W. et al. (2024). *Mapping the Increasing Use of LLMs in Scientific Papers*. arXiv:2404.01268. https://arxiv.org/abs/2404.01268
56. Hugging Face. *Dataset Cards* et *Manual Configuration* (en-tête YAML, `configs`). https://huggingface.co/docs/hub/datasets-cards ; https://huggingface.co/docs/hub/datasets-manual-configuration
57. MLCommons. *Croissant Format Specification, version 1.1* et exemples officiels. https://docs.mlcommons.org/croissant/docs/croissant-spec-1.1.html ; https://github.com/mlcommons/croissant/tree/main/datasets/1.1
58. MLCommons. *Croissant RAI Specification, version 1.0* et vocabulaire `croissant_rai.ttl`. https://docs.mlcommons.org/croissant/docs/croissant-rai-spec.html
59. NeurIPS 2026. *Evaluations & Datasets: hosting and Croissant requirements* (Croissant 1.1, champs RAI minimaux, `rai:hasSyntheticData`, `prov:wasDerivedFrom`, `prov:wasGeneratedBy`). https://neurips.cc/Conferences/2026/EvaluationsDatasetsHosting
