# La chaîne de traitement

De l'écran de la console au compte des parties, en sept étapes. Les cinq premières produisent et vérifient les
données ; la sixième publie le jeu de données PlayEnd et entraîne les détecteurs de fin de partie ; la septième prépare
l'élève, le petit lecteur de l'écran qui remplacera le professeur sur le Pi.

```text
Console ──HDMI──> Raspberry Pi ──> data/captures/                1. capture
                                        │
                                        v
                 professeur (grand VLM) : une observation JSON    2. annotation
                 par image ──> data/annotations/lots/
                                        │
                                        v
                 erreurs relevées ──> data/annotations/corrections/   3. corrections
                                        │
                                        v
                 relecture chronologique ──> data/boundaries/     4. fins de partie
                 (units.json, étiquettes par intervalle)
                                        │
                                        v
                 relecture humaine ──> data/validation/            5. validation
                 puis labels_human_verified.jsonl
                                        │
                                        v
                 jeu de données PlayEnd ──> détecteurs de fin       6. jeu de données
                 (GRU, gradient boosting…)                             et détecteurs
                                        │
                                        v
                 élève (OCR, ou VLM + LoRA) ──> boucle sur le Pi   7. élève
```

## 1. Capture

Le Raspberry Pi Zero 2 W reçoit le flux HDMI par une carte de capture USB et enregistre une image JPEG toutes les 10 à
45 secondes, avec son temps de réception (`raspberry_pi/capture.py`). Chaque démarrage ouvre une session
(`data/captures/session_<id>/`). Les intervalles simulent la lenteur du futur modèle embarqué. Seul le temps monotone
d'une session est fiable : l'horloge civile du Pi était fausse. Installation et preuves : `docs/capture/`.

## 2. Annotation

Un grand modèle de vision, le professeur, décrit chaque image selon le contrat d'observation 2.1 : jeu, phase, écran,
participants, score, chrono, période, résultat, compteurs et minuteurs secondaires (`docs/contract/README.md`). Il
décrit seulement ce qui est visible et ne décide jamais qu'une partie est finie. Les images sont lues par lots de 66,
avec les conventions de `docs/conventions/`.

```bash
python -m playend.annotation.new_lot session_<id> --start 1 --end 66 --suffix <professeur>
python -m playend.annotation.zoom grid session_<id> 1-66     # puis la lecture, enregistrée par presets.run_lot
python -m playend.annotation.coverage session_<id>
```

## 3. Corrections

Un lot enregistré ne change plus. Une erreur trouvée plus tard se corrige par une trace séparée, qui garde l'empreinte
de l'observation remplacée (`data/annotations/corrections/README.md`). Toutes les étapes suivantes lisent
l'observation effective : celle du lot, ou sa dernière correction.

```bash
python -m playend.corrections.build SPEC.json --dry-run
```

## 4. Fins de partie

Ici, et seulement ici, on raisonne dans le temps : on relit les observations d'une session dans l'ordre pour placer
les parties et leurs fins (`units.json`), selon `docs/conventions/ANALYSE_FIN_DE_PARTIE_PAR_JEU.md` et les règles de
`docs/decisions/regles-de-comptage.md`. Chaque intervalle entre deux observations reçoit deux étiquettes : la fin de
partie (`unit_end_boundary`) et le mode de facturation (`partie`, `temps` ou `hors_jeu`). Depuis le 2026-10-13, le
début de chaque partie est aussi étiqueté (`unit_start_boundary`), après avoir été placé dans `units.json`.

```bash
python -m playend.boundaries.timeline session_<id>
python -m playend.boundaries.starts session_<id> --write   # début = première capture de jeu au HUD lisible
python -m playend.boundaries.build_labels session_<id>
python -m playend.boundaries.review session_<id>
```

## 5. Validation

L'utilisateur relit dans un outil local toutes les fins de partie, tous les passages au temps et un échantillon
d'observations par jeu. Les erreurs relevées deviennent des traces de correction ; une fois la session validée, ses
étiquettes sont promues en `labels_human_verified.jsonl`, sur son accord explicite.

```bash
python -m playend.validation.server
python -m playend.boundaries.promote session_<id> --reviewer "Nom"
```

## 6. Jeu de données et modèles

Les observations et les étiquettes validées forment le jeu de données PlayEnd, en CSV, publié sur Zenodo
([doi:10.5281/zenodo.23159322](https://doi.org/10.5281/zenodo.23159322), version 1.0 du 2026-10-05), avec sa fiche
descriptive en anglais (`docs/dataset/DATA_CARD.md`). L'export lit les 25 sessions validées, remplace les vrais pseudos
par `player_001`… (liste privée `data/dataset/real_player_names.txt`), n'écrit aucune heure civile, puis relit et
vérifie le paquet produit :

```bash
python -m playend.dataset.export            # écrit build/playend_v1.0/ (data/, dictionary/, README.md, croissant.json)
```

Les détecteurs de fin de partie (GRU, régression logistique, gradient boosting, et des règles pour comparer) sont
entraînés sur PlayEnd, chaque session étant jugée par des modèles qui ne l'ont jamais vue (`docs/training/README.md`,
choix dans `docs/decisions/PLAN_ENTRAINEMENT_GRU.md`). Le calcul complet a tourné le 2026-10-06 sur le PC d'un ami,
avec le kit de `python -m playend.training.kit` ; ses résultats sont dans `docs/training/RESULTATS_2026-10-06.md`.

```bash
python -m playend.training.run --out build/training/v1 --deploy   # le protocole complet
python -m playend.training.report                                 # rapport et figures d'un calcul, sans réentraîner
```

Pour une seule session, la préparation des entrées du GRU existe aussi :

```bash
python -m playend.contract.prepare_dataset --manifest data/boundaries/session_<id>/observation_manifest.jsonl \
    --labels data/boundaries/session_<id>/labels_human_verified.jsonl --out NOUVEAU_DOSSIER
```

## 7. L'élève

Sur le Pi, il n'y a pas de professeur : c'est l'élève qui lit l'écran (`src/playend/student/`, conception dans
`docs/student/CONCEPTION.md`). Un classifieur reconnaît le jeu et le type d'écran, puis l'OCR lit les zones du HUD
selon les règles de chaque jeu, et les bandeaux de résultat sur la capture entière. Une autre piste lit les mêmes zones
avec LFM2.5-VL-450M adapté par LoRA, entraîné avec le kit de `python -m playend.student.kit` sur une machine à carte
graphique. La boucle complète, de la capture au compte, a tourné sur le Pi avec l'élève OCR, identique au PC. Les
mesures et les résultats sont dans `docs/student/RESULTATS.md`.

```bash
python -m playend.student.loop prepare|run|compare               # la boucle du Pi, sur des sessions de PlayEnd
python -m playend.student.vlm_eval compare <résultats du kit>/vlm  # VLM et élève OCR notés sur les mêmes images
```

## Le système final, sur le Pi

Le Pi capture une image, l'élève la décrit, un détecteur lit la suite des descriptions et signale une fin de partie
et le mode de facturation. Le choix du lecteur et du détecteur reste à faire (`docs/student/RESULTATS.md`). Le compteur, hors du modèle, décide alors de ce qui compte
(`docs/decisions/regles_facturation.json`) : une partie, du temps de jeu, ou rien. C'est `src/playend/counting/`
(contrat et conventions dans `docs/counting/README.md`), vérifié sur PlayEnd avec les fins validées. Les prix et la
facture restent au produit.

```bash
python -m playend.counting.replay      # écrit build/counting/truth/
python -m playend.counting.predicted   # le même compte avec les fins prédites par un détecteur
```
