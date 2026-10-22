# Rapport final de la réorganisation

Réorganisation du dépôt menée le 2026-10-04, en sept phases, chacune validée par l'utilisateur avant d'être lancée.
Point de départ : l'étiquette git `avant-reorganisation` (commit `39f95ff5`). Le plan et ses sources sont dans
[PLAN_REORGANISATION.md](PLAN_REORGANISATION.md).

## Avant et après

| Avant | Après |
|---|---|
| `CLAUDE.md` à la racine, 191 lignes, conventions par jeu comprises | `AGENTS.md` (167 lignes) et `.claude/CLAUDE.md`, qui l'importe ; conventions dans `docs/conventions/` |
| Scripts dispersés dans `dossier_partie_VLM/` (`build_claude_batch.py`, `claude_tools/`, `corrections_lib.py`…), reliés par des `sys.path` | Paquet installable `src/playend/` rangé par métier : `contract`, `annotation` (et `zoom`, `presets`), `corrections`, `boundaries`, `validation`, `common` |
| Programme du Pi mêlé aux images dans `Capture-dataset-jeux/` | `raspberry_pi/`, à copier tel quel sur la carte SD |
| Données dans `Capture-dataset-jeux/dataset/` et `dossier_partie_VLM/…` | `data/captures`, `data/annotations/lots`, `data/annotations/corrections`, `data/boundaries`, `data/validation` |
| Évaluations et phase Luna au milieu du travail courant | `archive/`, en lecture seule, avec un README par dossier |
| Pas de README à la racine | `README.md`, `docs/pipeline.md`, `docs/decisions/` |
| Dépôt GitHub `memoire-master-vlm` | `intelligent-counter-for-multiple-video-games`, « Compteur intelligent multijeux vidéo » |

## Vérifications

| Vérification | Résultat |
|---|---|
| Lots d'annotation, comparés fichier par fichier à l'étiquette de départ | 27 541 fichiers identiques |
| Images de capture | 8 976 fichiers identiques |
| Liste de validation et réponses de l'utilisateur | identiques |
| Traces de correction | 3 002 fichiers identiques ; seul le README a été mis à jour, et les deux scripts du dossier sont passés dans le paquet |
| Fichiers de frontières (`units.json`, étiquettes, manifestes) | 125 fichiers identiques à l'octet près ; les 25 `REVIEW.md` diffèrent comme prévu (voir plus bas) |
| Couverture des 33 sessions de capture | identique |
| Prompt du professeur, schéma, modèle JSON, spécification des entrées du GRU | identiques |
| Chemins écrits dans les fichiers enregistrés | 67 820 chemins (37 875 distincts), tous retrouvés |
| Liens des documents actifs | 1 075 liens dans 57 documents, aucun cassé |
| Commandes du paquet | les 16 répondent à `--help` |
| Tests | 26 tests du paquet et 17 du programme du Pi réussis |
| Installation à neuf dans un environnement vide | installation, tests et commandes réussis |
| Manifeste d'installation du Pi | 10 fichiers sur 10 avec leur empreinte d'origine |
| Ruff | aucun avertissement |

Pendant la phase 5, 19 sorties du programme ont été comparées après chaque étape : étiquettes et fiches des
25 sessions, couverture (elle recalcule la phrase finale des 8 871 notes enregistrées), chronologies, préréglages,
reconstruction d'un lot et d'une trace, liste de validation, planches de zoom, préparation des entrées du GRU. Elles
sont restées identiques, sauf trois différences voulues lors du dernier changement (marqueurs des notes).

Les mesures elles-mêmes sont dans [mesures-avant.json](mesures-avant.json) et [mesures-apres.json](mesures-apres.json).

## Différences voulues

- **Fiches `REVIEW.md`** : liens vers les images recalculés depuis `data/`. Pour la session 078643, ils mènent aux
  images de capture, parce que deux lots Luna y gardent des liens symboliques absolus qui ne marchaient que sur un PC.
  La phrase d'introduction ne nomme plus le modèle.
- **Chemins enregistrés** : jamais réécrits. `playend.common.paths.resolve` traduit les anciens noms de dossiers et suit
  les 360 liens symboliques des deux lots Luna de 078643 (voir `data/README.md`).
- **Notes à venir** : marqueurs `[Lecture]` et `[Correction]` au lieu de `[Lecture Claude]` et `[Correction Claude]` ;
  le modèle reste nommé dans `annotator_model`. Les anciennes notes sont lues telles quelles.
- **Messages d'erreur de validation** : en anglais, comme le reste du code ; ils sortaient à moitié en français.

## Correspondance des commandes

| Avant | Après |
|---|---|
| `setup_new_session_run.py`, `claude_tools/newlot.sh` | `python -m playend.annotation.new_lot … --suffix …` |
| `claude_tools/view.py`, `tile.py`, `mini.py`, `*strip.py`, `names.py`… | `python -m playend.annotation.zoom OUTIL …` |
| `claude_tools/lotkit.py` | `from playend.annotation.presets import *` |
| `build_claude_batch.py`, `record_luna_batch.py` | `playend.annotation.build_lot`, `playend.annotation.record_lot` |
| `verify_session_coverage.py` | `python -m playend.annotation.coverage` |
| `corrections/build_correction.py` | `python -m playend.corrections.build` |
| `build_boundary_labels.py`, `write_review.py`, `promote_verified_labels.py` | `playend.boundaries.build_labels`, `.review`, `.promote` |
| `session_timeline.py`, `condense.py` | `playend.boundaries.timeline`, `.condense` |
| `lancer_validation.sh`, `build_validation_set.py` | `python -m playend.validation.server`, `playend.validation.build_items` |
| `validate_vlm_output.py` (archivé) | `python -m playend.contract.validate` |

## Ce qui reste à décider ou à faire

- La session `6d48fd` n'a aucun élément dans `data/validation/items.json` : ses observations n'ont pas été
  échantillonnées pour la validation.
- La branche locale `essai/gru-v4-20261004` suit l'ancienne organisation : elle ne se fusionne pas telle quelle.
- Avant toute publication : un fichier `LICENSE` et un `CITATION.cff` (avec le DOI Zenodo une fois attribué).
- Les sept sessions de capture non retenues ne sont protégées que par la prudence ; les ajouter au `.gitignore`
  éviterait qu'un `git add` les embarque.
- Le vérificateur interne du lot Luna Fortnite/Warzone ne se relance plus ; comme le lot est immuable, il reste tel
  quel, et `playend.annotation.coverage` fait les mêmes contrôles.
- Le paquet ne marche qu'installé en mode éditable, puisqu'il trouve les données à partir de son emplacement.

## Commits

| Phase | Commits |
|---|---|
| 0. Mesures de référence | `96ad4412` |
| 1. Archives et doublons | `923202e7` |
| 2. Paquet `src/playend` | `5abaad25`, `da1b2b46`, `155a1911`, `b75acaa1`, `900cad4d`, `665c04d5` |
| 3. Données dans `data/` | `3ed7973a`, revue `34d75311` |
| 4. Documentation | `fcf1e13a`, nom du projet `08dac4d9` |
| 5. Nettoyage du code | `ec4736d2`, `bc12008d`, `d9d0fa2b`, `aac7cc84` |
| 6. Vérification finale | ce rapport |

## Refaire la vérification

```bash
python docs/reorganisation/mesurer.py > nouvelles-mesures.json   # à comparer avec mesures-apres.json
python -m playend.annotation.coverage --all
python -m unittest discover -s tests -t .
cd raspberry_pi && python -m unittest discover -s tests
```
