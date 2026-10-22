# Entraînement PlayEnd

Ce dossier contient tout ce qu'il faut pour lancer l'entraînement : les données (jeu de données PlayEnd 1.0), le code et
un script, `launch.py`, qui installe et lance tout. Il n'y a rien à modifier : trois commandes suffisent, et à la fin
un fichier zip est à renvoyer.

## Avant de commencer

- **Python 3.10 ou plus récent** (3.12 conseillé).
  - Windows : installer Python depuis <https://www.python.org/downloads/> en cochant « Add python.exe to PATH ».
  - Linux : `python3` et le paquet `python3-venv` (Debian, Ubuntu : `sudo apt install python3-venv`).
- **Une carte graphique NVIDIA avec son pilote à jour** : la commande `nvidia-smi` doit afficher la carte. PyTorch ne
  sait utiliser ici qu'une carte NVIDIA : une carte Intel ou AMD, même intégrée au processeur, ne sert pas, et
  l'entraînement tourne alors sur le processeur, plus lentement. `install` affiche les cartes graphiques qu'elle trouve
  et dit laquelle elle utilise.
- **Internet** pendant l'installation, et environ **6 Go d'espace disque** (PyTorch pour GPU est gros).
- **Désactiver la mise en veille** de l'ordinateur pendant l'entraînement, qui dure plusieurs heures.

## Les trois commandes

Ouvrir un terminal dans ce dossier (Windows : clic droit dans le dossier, « Ouvrir dans le terminal »). Sous Linux,
écrire `python3` au lieu de `python` ; sous Windows, `py` marche aussi.

```text
python launch.py install
python launch.py check
python launch.py train
```

1. **`install`** crée un environnement Python dans `.venv/`, installe la version de PyTorch qui correspond à la carte
   graphique, puis le reste, et lance les tests. Avec une carte NVIDIA, elle doit finir par `GPU test passed` puis
   `Installation done`. Compter 5 à 20 minutes selon la connexion. Ce qu'elle peut aussi écrire :
   - `there is an NVIDIA card, but its driver does not answer` : installer ou mettre à jour le pilote NVIDIA
     (<https://www.nvidia.com/drivers>), redémarrer, puis relancer `python launch.py install`. Elle remplace alors
     d'elle-même le PyTorch « processeur » installé avant par celui du GPU ;
   - `No NVIDIA card` : la carte n'est pas une NVIDIA, l'entraînement se fera sur le processeur ;
   - `The GPU does not work with this PyTorch` : carte trop ancienne pour cette version de PyTorch ; `check` et
     `train` utiliseront le processeur sans qu'il faille rien faire.
2. **`check`** fait tout le travail en petit (3 sessions, 10 époques) pour vérifier que tout marche jusqu'au rapport.
   Quelques minutes. Elle doit finir par `Check passed`. Ses chiffres ne veulent rien dire, c'est normal.
3. **`train`** fait l'entraînement complet. Pendant le calcul, chaque étape affiche le temps qui lui reste
   (`about N min left`). À la fin, la commande crée **`playend_results_<date>.zip`** dans ce dossier : c'est le seul
   fichier à renvoyer.

## Si l'entraînement s'arrête

Ctrl-C, coupure de courant, redémarrage, erreur : relancer **la même commande**, `python launch.py train`. Tout ce qui
était terminé est gardé ; seul ce qui était en cours est refait.

Si le système tue un des processus d'entraînement (le plus souvent parce que la mémoire vive manque), le programme
continue seul avec deux fois moins de processus et l'écrit : `a worker process was killed … going on with 2`. Rien
n'est perdu. Le nombre de processus par défaut tient déjà compte de la mémoire de l'ordinateur.

Message `CUDA out of memory` : la carte manque de mémoire pour tous les entraînements menés en parallèle. Relancer
avec moins de processus : `python launch.py train --workers 2`.

Si une erreur revient à chaque fois, la commande crée quand même un zip `playend_results_<date>_unfinished.zip` :
l'envoyer tel quel, avec une capture des messages. `python launch.py pack` refait ce zip à tout moment.

## Passer à une nouvelle version du kit sans perdre le travail fait

Décompresser le nouveau zip au même endroit que l'ancien, en acceptant de remplacer les fichiers : les dossiers
`.venv/` et `results/` restent en place. Relancer ensuite `python launch.py install` (rapide : seul ce qui manque
est installé), puis `python launch.py train` : les entraînements déjà terminés ne sont pas refaits.

## Réglages facultatifs

Les options écrites après `check` ou `train` sont transmises au programme d'entraînement :

| Option | Effet |
|---|---|
| `--workers 6` | nombre d'entraînements menés en même temps. Par défaut : cœurs du processeur moins un, au plus 4 par carte graphique, et pas plus que la mémoire vive ne le permet (environ 2,5 Go par processus avec une carte graphique). |
| `--device cpu` | ne pas utiliser la carte graphique. |
| `--device cuda:1` | n'utiliser que la deuxième carte. Par défaut, toutes les cartes sont utilisées. |

Ces options peuvent changer d'un lancement à l'autre sans rien perdre.

## Contenu

```text
launch.py            installation, lancement, zip des résultats
README.md            ce fichier
kit.json             version du code qui a servi à faire ce dossier
data/playend_v1.0/   le jeu de données (CSV, dictionnaire des colonnes, fiche descriptive, licence)
src/playend/         le code d'entraînement
tests/               tests du code, lancés par install
docs/                le protocole d'entraînement complet (PLAN_ENTRAINEMENT_GRU.md)
pyproject.toml       liste des bibliothèques
```

Après les commandes apparaissent `.venv/` (l'environnement Python, qui n'est pas à renvoyer) et `results/` :

```text
results/
  machine.txt        système, processeur, carte graphique, versions des bibliothèques
  check/             le petit essai
  full/              l'entraînement complet
    log.txt          tous les messages affichés
    run.json         réglages figés au premier lancement
    jobs/            un fichier par entraînement (réglages, courbe d'apprentissage, prédictions)
    choices/         ce qui a été choisi dans chaque tour
    models/          les poids des modèles finaux
    report.md        le rapport des résultats
    figures/         les graphiques (modèles, courbes, familles de jeux, une figure par session)
```

Le zip contient tout `results/`.

## À propos des données

PlayEnd 1.0 décrit, image par image, des captures d'écran de consoles dans une salle de jeux vidéo, avec les fins de
partie vérifiées à la main ; les images elles-mêmes n'y sont pas. Les noms des joueurs sont remplacés par des
pseudonymes. Licence CC BY-NC 4.0 (voir `data/playend_v1.0/LICENSE`), DOI 10.5281/zenodo.23159322.
