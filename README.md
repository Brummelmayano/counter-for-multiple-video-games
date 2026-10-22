# Compteur intelligent multijeux vidéo

*In English.* Code of a master's thesis (University of Kinshasa, 2026): a Raspberry Pi Zero 2 W plugged into a game
console captures the screen, reads it and counts the games of very different titles at their start, so that a gaming
room can bill its customers per game. The PlayEnd dataset built for this work is published on Zenodo
([doi:10.5281/zenodo.23159321](https://doi.org/10.5281/zenodo.23159321)).

Ce dépôt réunit le code du mémoire de master *Compteur intelligent multijeux vidéo* (Université de Kinshasa, 2026).
Dans une salle de jeux vidéo, les clients paient à la partie. Un Raspberry Pi Zero 2 W, branché sur la console, en
capture l'écran, le lit et compte chaque partie à son début, quel que soit le jeu : match de football, combat, course
ou battle royale. Ce travail prolonge le compteur de matchs de football de Mayano, Yan-Mol et Masakuna (2025),
*Intelligent Match Counter in a Video Game Arena*, IEEE Access 13, 32320–32328
([doi:10.1109/ACCESS.2025.3542425](https://doi.org/10.1109/ACCESS.2025.3542425)).

## Ce qui est publié, et ce qui ne l'est pas

```text
src/playend/        le paquet Python, par étape : contrat d'observation, annotation, frontières, validation, jeu de
                    données, entraînement, comptage, élève (le lecteur du Pi)
raspberry_pi/       le programme de capture du Pi
training_kit/       le lanceur du kit d'entraînement des détecteurs, pour une autre machine
student_kit/        le lanceur du kit de l'élève, pour une machine à carte graphique
docs/               chaîne de traitement, conventions par jeu, décisions, contrat, jeu de données, résultats
tests/              tests du paquet
```

Le jeu de données PlayEnd (308 parties, 25 enregistrements) est publié à part, sur Zenodo, avec sa fiche descriptive
et ses métadonnées Croissant.

Ne sont pas publiés :

- les captures d'écran, qui appartiennent aux éditeurs des jeux et montrent parfois les pseudos de vrais joueurs ;
- nos fichiers de travail (annotations image par image, fiches de validation), pour la même raison ;
- les poids du modèle de vision adapté par LoRA, qui a appris à lire ces pseudos à l'écran.

## Installation

Python 3.10 ou plus récent.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m unittest discover -s tests -t .
```

Le programme du Pi a ses propres tests : `cd raspberry_pi && python -m unittest discover -s tests`.

## Refaire les mesures avec PlayEnd

Téléchargez la version 1.1 de PlayEnd sur Zenodo et placez son contenu dans `build/playend_v1.1`, de sorte que le
fichier `build/playend_v1.1/data/observations.csv` existe. Le compteur par règles se lance alors sur les observations
du professeur, le grand modèle de vision qui a décrit chaque capture :

```bash
python -m playend.counting.starts --package build/playend_v1.1
```

Il trouve 305 des 308 parties de PlayEnd, sans en compter aucune de trop. Le mémoire en annonce 307 : une règle compare
les portraits des combattants de Dragon Ball Sparking! ZERO sur les captures elles-mêmes, et repère ainsi deux combats
recommencés de plus. Sans les captures, cette règle ne peut pas tourner.

Les modèles appris (gradient boosting, GRU) se réentraînent de la même façon sur PlayEnd ; voir
[docs/training/README.md](docs/training/README.md). Les lectures de l'élève et les mesures faites sur le Pi demandent
les captures : elles ne peuvent pas être refaites avec ce dépôt seul.

La chaîne complète, de la capture au compte, est décrite dans [docs/pipeline.md](docs/pipeline.md).

## Citer ce travail

Le fichier [CITATION.cff](CITATION.cff) donne la citation du code. Pour le jeu de données :

> Mayano, B. D. et Masakuna, J. F. (2026). *PlayEnd: Console Play Sessions from a Kinshasa Gaming Room for End-of-Game
> Detection*. Version 1.1. Zenodo. [doi:10.5281/zenodo.23159321](https://doi.org/10.5281/zenodo.23159321).

## Licence

CC BY-NC 4.0, comme PlayEnd (voir [LICENSE](LICENSE)).

## Auteur

DUASENGE MAYANO BRUMMEL ([ORCID 0009-0008-5433-5259](https://orcid.org/0009-0008-5433-5259)), sous la direction du
Professeur MASAKUNA FÉLICIEN JORDAN, Université de Kinshasa.
