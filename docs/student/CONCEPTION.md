# L'élève : lire l'écran sur le Raspberry Pi

Note de conception du 2026-10-07. Les mesures qui l'ont précédée sont dans
`archive/student-measurements-2026-10/` : sur le Pi Zero 2 W, aucun petit VLM ne lit une capture entière en moins de
45 s, mais LFM2.5-VL-450M lit les zones du HUD en 37 s par image, et PP-OCRv6 tiny en 1 s. Ces deux lecteurs sortent
du texte libre. Cette note décrit ce qui manque pour que l'élève produise, seul et sur le Pi, une observation que les
modèles de fin de partie peuvent lire, et comment on le mesurera.

## 1. Ce que l'élève doit produire

Pour chaque capture, une observation au format du contrat 2.1 (`src/playend/contract/`), réduite aux champs que le
HUD permet de lire : le jeu, le type d'écran, le score, le chrono, la période, la progression, les compteurs et les
noms affichés. Les autres champs restent à `null` ou `unknown`, comme chez le professeur quand une valeur n'est pas
lisible. L'observation passe par `validate_observation` du contrat avant d'être gardée. Les variables du GRU
(`playend.dataset.features`) se calculent ensuite exactement comme pour les observations du professeur.

## 2. La chaîne

1. **Classifieur** : l'image entière, réduite, donne le jeu et le type d'écran (jeu, menu, résultat, chargement…).
2. **Disposition et zones** : pour un jeu à plusieurs dispositions (écran partagé à deux, trois ou quatre joueurs),
   la disposition retenue est celle dont les zones se lisent le mieux (le plus de champs acceptés par les règles du
   §4). Les zones de la disposition sont découpées, agrandies et empilées en une mosaïque.
3. **Lecteur**, au choix :
   - OCR (PP-OCRv6 tiny) : chaque texte lu garde sa position, donc on sait de quelle zone il vient ;
   - VLM (LFM2.5-VL-450M), sans ou avec adaptateur LoRA : une grammaire GBNF, tirée du schéma des zones, l'oblige à
     répondre une ligne par zone, au format du rôle de la zone ou `null` [1, 2].
4. **Règles de lecture** : chaque rôle a sa règle (§4), qui transforme le texte en valeur du contrat ou le rejette.
5. **Marques** : les pastilles de manche, les barres de vie restantes et les jauges ne sont pas du texte. Une règle
   d'image compte les cases allumées à des positions connues (luminosité et couleur), là où l'OCR ne voit rien.
6. **Bandeaux et conventions** (ajoutés le 2026-10-08, `RESULTATS.md` §4) : hors du jeu, l'OCR lit la capture
   entière et cherche le bandeau de résultat ; les champs que le HUD ne montre pas (genre, période, type de score)
   viennent d'un profil par jeu tiré des observations du professeur ; un passage isolé entre le jeu et un autre
   écran attend la capture suivante.
7. **Observation**, puis variables, puis modèle de fin (gradient boosting ou GRU), puis comptage
   (`playend.counting`).

Le classifieur n'utilise aucune étiquette quand il travaille. Les étiquettes de PlayEnd servent seulement à
l'entraîner, puis à mesurer ses erreurs sur des sessions qu'il n'a pas vues.

## 3. Le schéma des zones

Les cadres viennent des préréglages de zoom du professeur (`src/playend/annotation/zoom/`) et des cadres posés le
2026-10-06 pour les autres jeux (`archive/student-measurements-2026-10/comparaison/roi.json`). Le schéma leur ajoute un
rôle. Rôles tirés des conventions par genre (`docs/conventions/`) et des champs que le professeur remplit vraiment sur
les images de jeu (part des images où le champ a une valeur) :

| Jeu | Images de jeu | Zones et rôles | Champs du professeur |
|---|---:|---|---|
| EA Sports FC | 2 053 | tableau de score : équipe A, buts A, buts B, équipe B, chrono | score 92 %, chrono 89 %, noms 94 % |
| Mortal Kombat 1 | 1 023 | pastilles gauche (marques), chrono, pastilles droite (marques) | chrono 99 %, manches 40 % |
| Fortnite | 876 | selon la disposition : joueurs restants, minuteur de tempête | joueurs restants 94 % |
| Call of Duty: Warzone | 288 | équipes restantes, joueurs restants ; numéro et minuteur du cercle | équipes et joueurs 98 %, cercle 73 % |
| Dragon Ball Sparking! ZERO | 284 | barres de vie restantes A et B (marques) | vies 95 % |
| Beach Buggy Racing 2 | 170 | « N/8 PLACE » de chaque vue, barre « TOUR n » | tour 81 % |
| Tekken 8 | 125 | « WINS n » A ; pastilles de manche et chrono ; « WINS n » B | manches 92 %, chrono 94 %, séries 38 % |
| EA Sports UFC 5 | 91 | nom A ; badge de round et chrono ; nom B | chrono 95 %, round 75 % |
| Naruto Storm Connections | 57 | chrono, manches (marques), noms | score et chrono 100 % |
| J-Stars Victory VS+ | 29 | jauges de victoire A et B (marques), nom du combattant, minuteur « Temps » | score et chrono 97–100 % |
| Dragon Ball FighterZ, Demon Slayer, Brawlhalla | 8 chacun | chrono, manches | chrono 100 % |

Les jeux de mission (Genshin Impact, Red Dead Redemption 2, Assassin's Creed Origins, God of War) n'ont aucun
compteur qui termine une partie : ils sont facturés au temps et n'ont pas de zone. Pour eux, l'élève donne seulement
le jeu et le type d'écran.

## 4. Les règles de lecture

Une règle par rôle, écrite comme une expression régulière suivie de contrôles de vraisemblance. Ce sont les règles
que le professeur applique déjà (contrat et conventions), rendues mécaniques :

- chrono : `m:ss` ou `mm:ss` (aussi `90+2:13` en football), secondes inférieures à 60, converti en secondes ;
- score : entier de 0 à 20 de chaque côté ;
- position : `k/n` avec k ≤ n ; l'OCR perd parfois la barre (« 618 » pour « 6/8 ») : on la rétablit quand le
  total du jeu est connu (8 dans Beach Buggy Racing 2) ;
- tour, round, cercle : le nombre qui suit le mot du jeu (« TOUR 2 », « ROUND 3 ») ;
- compteurs (joueurs, équipes restantes) : entier positif, au plus la taille connue de la partie ;
- noms : texte gardé tel quel ; jamais un nom déduit d'autre chose que le texte écrit (règle des participants).

Ce qu'aucune règle n'accepte reste à `null`.

## 5. Le classifieur

MobileNetV2 (le modèle ONNX déjà mesuré sur le Pi) reste figé ; on garde ses caractéristiques d'image et on entraîne
dessus un classifieur linéaire. Le modèle ONNX ne donne pas l'avant-dernière couche : ce sont ses 1 000 scores
ImageNet qui servent, réduits par une analyse en composantes principales. Les caractéristiques d'un réseau entraîné sur ImageNet se
transfèrent bien quand on les garde fixes [3] ; nos classes, des jeux d'apparence très différente, sont faciles.
Classes : la famille du jeu (aucun jeu pour l'accueil de la console et les menus du système) et le type d'écran
(jeu, menu, résultat, chargement, cinématique, pause, sélection). Deux évaluations, parce qu'un jeu vu dans une seule
session ne peut pas être reconnu dans une session qu'on retire :

- session par session (une session retirée à chaque tour) : mesure ce qui arrive face à un jeu jamais vu, qui doit
  donner une confiance basse et être traité comme inconnu ;
- par blocs de temps dans chaque session : le jeu est connu, la suite de la session est retirée [4].

## 6. LoRA, et la comparaison avec et sans

Exemples d'entraînement : la mosaïque des zones d'une capture et la réponse attendue, ligne par ligne, tirée de
l'observation du professeur par le schéma des zones (chaque rôle renvoie à un champ). L'adaptateur porte sur les
couches d'attention du modèle de langue (rang 8), selon le guide de Liquid pour LFM2-VL-450M [5] ; l'encodeur d'image
reste figé. L'entraînement se fait sur le PC de l'ami (GPU Intel Arc, PyTorch XPU [6]) ; les sessions de test ne
servent jamais à l'entraînement. L'adaptateur est converti au format de llama.cpp et appliqué au modèle déjà présent
sur le Pi : seuls quelques Mo reviennent. Comparaison sur les mêmes images de test : VLM sans LoRA et sans grammaire,
avec grammaire, avec grammaire et LoRA ; OCR avec règles. Pour chacun : champs justes, temps par image sur le Pi.

## 7. Ce qu'on mesure

1. Champ par champ, sur des sessions de test : part des valeurs justes, des valeurs fausses et des valeurs
   manquantes, pour chaque lecteur ; erreurs du classifieur.
2. L'effet sur la détection des fins : les modèles gardés du calcul du 2026-10-06 (GRU, 25 sessions × 5 graines) et
   le gradient boosting, réentraîné pour chaque session avec ses réglages retenus, lisent les observations de
   l'élève au lieu de celles du professeur. Une simulation complète la mesure : des valeurs retirées au hasard à un
   taux choisi donnent une courbe ; les erreurs réelles, groupées (animations), placent un point dessus. Une cascade
   transmet les erreurs du premier étage au second [7].
3. L'effet sur le comptage : parties facturées en trop et parties perdues pour cent parties, avec chaque lecteur.
4. La boucle complète sur le Pi, en direct : temps par capture et mémoire, modèle chargé une seule fois.

## Sources

1. Geng, S., Josifoski, M., Peyrard, M., West, R. (2023). *Grammar-Constrained Decoding for Structured NLP Tasks
   without Finetuning*. EMNLP 2023. https://aclanthology.org/2023.emnlp-main.674
2. llama.cpp, *GBNF Guide*. https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md ; sur les limites des
   formats imposés (raisonnement, pas extraction) : Tam, Z. R. et al. (2024). *Let Me Speak Freely?* EMNLP 2024.
   https://arxiv.org/abs/2408.02442
3. Kornblith, S., Shlens, J., Le, Q. V. (2019). *Do Better ImageNet Models Transfer Better?* CVPR 2019.
   https://openaccess.thecvf.com/content_CVPR_2019/html/Kornblith_Do_Better_ImageNet_Models_Transfer_Better_CVPR_2019_paper.html
4. Roberts, D. R. et al. (2017). *Cross-validation strategies for data with temporal, spatial, hierarchical, or
   phylogenetic structure*. Ecography 40(8), 913–929. https://doi.org/10.1111/ecog.02881
5. Liquid AI, *Fine-tuning with TRL*. https://docs.liquid.ai/lfm/fine-tuning/trl.md
6. PyTorch, *Getting Started on Intel GPU*. https://docs.pytorch.org/docs/stable/notes/get_start_xpu.html
7. Indurthi, S., Chollampatt, S., Agrawal, R., Turchi, M. (2023). *CLAD-ST: Contrastive Learning with Adversarial
   Data for Robust Speech Translation*. EMNLP 2023 (dans une cascade, le modèle de traduction entraîné sur du texte
   propre résiste mal aux erreurs de la reconnaissance vocale). https://aclanthology.org/2023.emnlp-main.560
