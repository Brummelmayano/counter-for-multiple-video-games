# Lancer l'entraînement

Le code est dans `src/playend/training/`. Il suit le protocole de `docs/decisions/PLAN_ENTRAINEMENT_GRU.md` : validation
croisée imbriquée (une session tenue à l'écart à chaque tour, 4 plis de validation à l'intérieur), recherche des
réglages, retrait des groupes de variables, modèles finaux avec plusieurs graines, puis rapport et figures. Il lit le
paquet PlayEnd publié, pas les dossiers `data/` du dépôt : n'importe quelle machine qui a le paquet et ce code peut le
faire tourner.

## Sur une autre machine : le kit

```bash
python -m playend.training.kit
```

La commande vérifie le paquet `build/playend_v1.0` avec les contrôles de l'export (pseudonymes compris), puis écrit
`build/playend_training.zip` (moins de 1 Mo) : le paquet, le code d'entraînement, les tests, le plan, le lanceur
`launch.py` et un mode d'emploi. `kit.json` y garde le commit du code. Les fichiers propres au kit sont dans
`training_kit/` : lanceur, mode d'emploi pour la personne qui lance le calcul, `pyproject.toml` réduit à
l'entraînement.

Sur l'autre machine, trois commandes suffisent (détail dans `training_kit/README.md`) :

```bash
python launch.py install    # environnement, PyTorch adapté à la carte NVIDIA (d'après nvidia-smi), tests
python launch.py check      # le protocole en petit
python launch.py train      # le protocole complet avec --deploy, puis playend_results_<date>.zip
```

`install` choisit la version de PyTorch d'après la version de CUDA que le pilote accepte (affichée par `nvidia-smi`),
en essayant de la plus récente (`cu132`) à la plus ancienne (`cu118`), puis la version pour processeur. Les paquets de
PyTorch contiennent déjà CUDA : seul le pilote NVIDIA doit être installé. Elle affiche aussi les cartes graphiques que
voit le système (Windows : `Win32_VideoController` ; Linux : `lspci`), cherche `nvidia-smi` hors du PATH aux
emplacements des pilotes Windows, et remplace un PyTorch « processeur » déjà installé quand une carte NVIDIA répond
(sinon pip le garderait, puisque « torch » est déjà là). Une carte qui ne passe pas le test du GPU (trop ancienne pour
cette version de PyTorch) fait écrire `.device`, et `check` et `train` passent alors `--device cpu`. Sous Windows, le
nombre de processus suit la mémoire libre (1 Go par processus sur processeur) et les variables `OPENBLAS_NUM_THREADS`,
`OMP_NUM_THREADS` et `MKL_NUM_THREADS` sont fixées avant le démarrage des processus : sinon OpenBLAS réserve dès
l'import de numpy la mémoire de tous les threads possibles, et 9 processus ont épuisé une machine de 7 Go.

## Analyser les résultats rapportés

Un calcul fait sur une autre machine se range comme s'il avait tourné ici, pour que les commandes le trouvent sans
option :

| Dans `playend_results_<date>.zip` | Ici |
|---|---|
| `results/full/` | `build/training/v1/` (dossier par défaut de `run`, `report` et `figures`) |
| `results/machine.txt`, `results/kit.json` | dans `build/training/v1/` : la machine et le commit du code |
| `results/check/` | `build/training/quick_<machine>/`, à côté de l'essai local `build/training/quick/` |
| le zip lui-même | `build/training/archives/` |

Ne jamais écraser un dossier existant : un nouveau calcul complet prend un autre nom (`v2`...) et se lit avec `--out`.
Le rapport et les figures se refont sans rien réentraîner :

```bash
python -m playend.training.report
python -m playend.training.figures
```

Premier calcul complet (2026-10-06, PC d'un ami) : il est dans `build/training/v1/`, analysé dans
`RESULTATS_2026-10-06.md`. Comme `build/` n'est pas suivi par git, le rapport, les figures, les choix de chaque tour
et le GRU à déployer sont aussi copiés dans `resultats_2026-10-06/`.

## Sur ce dépôt

Après `pip install -e ".[train]"` (PyTorch installé d'abord, dans la version qui convient à la machine) :

```bash
python -m playend.training.run --quick --out build/training/quick   # le protocole en petit, une dizaine de minutes
python -m playend.training.run --out build/training/v1 --deploy     # le protocole complet
```

| Option | Rôle |
|---|---|
| `--device` | `auto` (par défaut : le GPU s'il y en a un, sinon le processeur), `cpu`, `cuda` ou `cuda:1`. La régression logistique et le gradient boosting tournent toujours sur le processeur. |
| `--workers` | nombre d'entraînements menés en même temps (par défaut : nombre de cœurs moins un, et au plus 4 par GPU, car chacun occupe quelques centaines de Mo de mémoire sur la carte). |
| `--threads` | threads par entraînement (par défaut : cœurs divisés par `--workers`). |
| `--until` | s'arrêter après `search`, `ablation`, `final` ou `report`. |
| `--deploy` | entraîner aussi le modèle à déployer sur les 25 sessions. À décider au premier lancement : il change les réglages du dossier. |
| `--package` | dossier du paquet (par défaut `build/playend_v1.0`). |

Le GRU est petit (16 à 64 unités) : un seul entraînement n'occupe qu'une partie d'un GPU, d'où plusieurs
entraînements à la fois sur la même carte. Avec plusieurs cartes, les processus sont répartis entre elles.

## Reprendre après une coupure

Relancer exactement la même commande. Chaque entraînement terminé est enregistré à part, dans `jobs/`, et n'est pas
refait ; ceux qui étaient en cours sont refaits depuis le début. Cela vaut pour un Ctrl-C, une coupure de courant ou un
entraînement qui a échoué. Testé le 2026-10-05 avec un Ctrl-C et avec un arrêt brutal (`kill -9`) en pleine recherche.

Un processus tué pendant le calcul, le plus souvent par le système quand la mémoire vive manque, rend tout le pool de
processus inutilisable (`BrokenProcessPool`) : c'est arrivé au premier lancement sur la machine à GPU, en pleine
recherche des réglages. Le programme recrée alors le pool pour les entraînements restants, avec deux fois moins de processus ;
seul, si un entraînement tue encore son processus, il est sauté et signalé. Les jobs passent aussi par lots d'au plus
100 par processus, chaque lot dans un pool neuf, pour que la mémoire laissée par un job ne s'accumule pas
(`max_tasks_per_child` ferait la même chose, mais il peut bloquer le pool avant Python 3.14.7 : cpython #115634).
Le nombre de processus par défaut tient compte de la mémoire vive : environ 0,45 Go mesuré par processus sur
processeur, et jusqu'à 2 Go de plus pour les bibliothèques CUDA d'un processus qui utilise le GPU.

Les réglages d'un dossier (paquet, essais tirés, tours, graines) sont figés dans `run.json` au premier lancement. Si
le paquet ou le code des réglages a changé, la commande refuse de continuer dans ce dossier : prendre un autre
`--out`.

## Ce qui sort

```text
build/training/v1/
  run.json        réglages figés, versions des bibliothèques, machine
  jobs/           un .json (réglage, époques, courbe, durée) et un .npz (probabilités) par entraînement
  models/         les poids des modèles finaux du GRU
  choices/        pour chaque tour : réglage retenu, groupes retirés, seuils, scores de tous les essais
  report.md       les résultats, en français, avec la liste des figures
  report.json     les mêmes, en entier
  figures/        modèles, précision-rappel, courbes d'apprentissage, essais, réglages, groupes de variables,
                  familles de jeux, mode de facturation, et une figure par session tenue à l'écart
```

## Reproductibilité

Les tirages des réglages, l'ordre des lots et l'initialisation des poids dépendent de graines fixes, et le GRU est
réglé pour être déterministe sur GPU (`CUBLAS_WORKSPACE_CONFIG=:16:8`, `cudnn.deterministic`). Une même commande sur
la même machine redonne donc les mêmes résultats. Entre le processeur et le GPU, ou entre deux versions de PyTorch,
les chiffres peuvent varier un peu : PyTorch ne garantit pas des résultats identiques « between CPU and GPU executions,
even when using identical seeds » (documentation *Reproducibility* de PyTorch 2.14). C'est pourquoi `run.json` garde
les versions et la machine, et chaque modèle final du GRU est entraîné avec 5 graines.
