# Plan de réorganisation du dépôt

Statut : proposition à valider (2026-10-04). Aucun fichier n'a été déplacé. Chaque phase de la section 6 ne sera
lancée qu'avec l'accord de l'utilisateur, et vérifiée avant de passer à la suivante.

## 1. État actuel

Inventaire fait sur la branche `main` (commit `fbef740e`).

| Zone | Fichiers suivis | Rôle réel |
|---|---|---|
| `Capture-dataset-jeux/` | 8 985 | Code du Raspberry Pi **et** images capturées (2,0 Go). |
| `dossier_capture_dataset/` | 25 | Notes d'installation du Pi et une **copie exacte** du code de capture (`projet/`). |
| `dossier_partie_VLM/codex_luna_eval/` | 30 629 | Lots d'annotation (`runs/`), traces de correction, outils de lecture, plus des audits datés du 25 septembre. |
| `dossier_partie_VLM/gru_boundaries/` | 160 | Fins de partie et étiquettes du GRU (données et scripts mélangés). |
| `dossier_partie_VLM/observation_contract/` | 20 | Contrat d'observation 2.1 et préparation des variables du GRU. |
| `dossier_partie_VLM/validation/` | 7 | Outil de validation humaine. |
| `dossier_partie_VLM/evaluation_2026_09_*` (4 dossiers) | 676 | Essais de VLM de début septembre ; scripts recopiés d'un dossier à l'autre. |
| `dossier_partie_VLM/VLM_Handoff_Codex/`, `openai_teacher/`, `annotations_codex_full_frames_v1/`, `images_vlm/` | 85 | Travaux de la phase Codex/Luna, terminés. |
| `Memoire_GRU_Reproduction_COMPLETE/` | 68 | Paquet du GRU pilote (7 septembre). |
| Racine | 6 | `CLAUDE.md`, un PDF (aussi présent ailleurs), `fichier_des_idees.md`. |

Problèmes constatés :

1. **Noms qui ne disent pas le métier.** `dossier_partie_VLM`, `codex_luna_eval` (nom d'un outil et d'un modèle),
   `claude_tools` : on ne devine pas ce qu'ils contiennent.
2. **Données et code mélangés** dans les mêmes dossiers (`gru_boundaries/` contient à la fois les étiquettes et
   les scripts qui les produisent).
3. **Doublons** : le code de capture en deux exemplaires, deux PDF en double, le même prompt dans quatre dossiers,
   `gru_audit.md` et `AUDIT_ANNOTATIONS.md` en trois exemplaires, `evaluate.py` et `schema.py` recopiés dans
   trois dossiers d'évaluation.
4. **Code actif et code historique côte à côte.** Sur 132 scripts hors lots, 44 servent encore ; les autres
   appartiennent à des essais terminés (scripts datés `*_20260925.py`, évaluations de septembre).
5. **Import par bricolage** : 20 scripts modifient `sys.path` pour trouver leurs voisins.
6. **Même fonction écrite trois fois** : la lecture des observations effectives d'une session existe dans
   `corrections_lib.effective`, `build_boundary_labels.session_frames` et `build_validation_set.load_sessions`.
7. **Chemins codés en dur** dans une trentaine de scripts.
8. **Langues mélangées** : docstrings en anglais, messages et documents en français, sans règle.
9. **`CLAUDE.md` de 31 Ko** qui sert à la fois de consignes, de conventions par jeu, de journal des décisions et de
   mode d'emploi.

Contrainte qui pèse sur tout le reste : **10 889 fichiers de données versionnés contiennent plus de 56 000 chemins
écrits en toutes lettres** (`annotation_path`, `image_path`, `base_annotation_path`…). Ils commencent par
`dossier_partie_VLM/codex_luna_eval/…` ou `Capture-dataset-jeux/dataset/…`. Les observations elles-mêmes
(`*.observation.json`) n'en contiennent aucun : seuls les manifestes et les métadonnées en ont. Les empreintes
SHA-256 vérifiées portent sur le contenu des observations et des images, pas sur les manifestes.

## 2. Principes retenus, et leurs sources

| Principe | Source |
|---|---|
| Les données brutes ne se modifient jamais sur place ; on les lit et on produit de nouveaux fichiers. | Cookiecutter Data Science, *Opinions* [1] |
| Séparer clairement données, code, documentation et résultats, avec un README à la racine. | Wilson et al. 2017 [2] ; Noble 2009 [3] |
| Le code réutilisable devient un vrai paquet installable, au lieu de scripts qui se cherchent entre eux. | Cookiecutter Data Science [1] ; guide officiel de l'empaquetage Python, disposition `src/` [4] |
| Ranger le code par métier (capture, annotation, fins de partie…), pas par type technique. | « Package by feature » [5] |
| Style : PEP 8 pour les noms, PEP 257 pour les docstrings, et des commentaires qui expliquent le *pourquoi*, pas le *quoi*. | PEP 8 [6], PEP 257 [7], guide Google [8] |
| Déplacer avec `git mv`, pour que `git log --follow` retrouve l'historique de chaque fichier. | Documentation de Git [9] |
| Une seule implémentation par fonction : on factorise ce qui est recopié. | Cookiecutter Data Science [1] |

Un point s'écarte volontairement de Cookiecutter Data Science : il conseille de ne pas mettre les données dans
git [1]. Ici, elles y sont, et c'est voulu, car les sessions cloud en ont besoin et chaque image a son empreinte.
Les sortir de git obligerait à réécrire tout l'historique. Ce n'est pas proposé dans ce plan.

## 3. Structure cible

```
intelligent-counter-for-multiple-video-games/   (memoire-master-vlm jusqu'au 2026-10-04)
├── README.md              présentation, installation, la chaîne en cinq commandes
├── AGENTS.md              consignes pour les agents de code (standard ouvert), moins de 200 lignes
├── pyproject.toml         dépendances et commandes du projet
├── CITATION.cff           comment citer le dépôt
├── src/playend/           le code, rangé par métier
│   ├── common/            chemins du dépôt, lecture des observations effectives (une seule fois), JSON
│   ├── capture/           Raspberry Pi : capture, vérification du jeu d'images, services systemd
│   ├── contract/          contrat d'observation 2.1 : schéma, validation, migration 2.0 → 2.1, règles
│   ├── annotation/        lots du professeur : création, préréglages par jeu, construction, enregistrement,
│   │   └── zoom/          couverture ; outils de lecture d'images (planches, zooms par jeu)
│   ├── corrections/       traces de correction
│   ├── boundaries/        fins de partie : units → étiquettes, fiche REVIEW, promotion, chronologie
│   ├── validation/        outil de validation humaine (serveur et page web)
│   ├── dataset/           export PlayEnd (CSV, Data Card), à venir
│   └── training/          GRU v4, à venir et seulement sur autorisation
├── data/                  les données (voir 4)
│   ├── captures/          images et captures.csv par session
│   ├── annotations/       lots/ et corrections/
│   ├── boundaries/        units.json, étiquettes et REVIEW.md par session
│   └── validation/        items.json et validation_results.jsonl
├── docs/
│   ├── pipeline.md        la chaîne de bout en bout, schéma compris
│   ├── conventions/       conventions d'annotation par jeu (sorties de CLAUDE.md)
│   ├── decisions/         décisions datées de l'utilisateur (comptage, facturation, validation…)
│   ├── reports/           rapports et analyses, une seule copie de chacun
│   └── memoire/           notes et sources pour la rédaction
├── archive/               travaux terminés, en lecture seule, avec un README qui dit ce qu'ils étaient
│   ├── vlm-evaluations-2026-09/
│   ├── codex-luna-phase/
│   └── gru-pilot-2026-09/
└── tests/                 tests par module (pytest)
```

Chaque module garde ses commandes, appelées avec `python -m` (par exemple
`python -m playend.boundaries build session_<id>`). On n'a plus à se placer dans un dossier précis, et plus aucun
`sys.path` n'est modifié.

## 4. Les données : trois options

| Option | Ce qu'on fait | Avantage | Inconvénient |
|---|---|---|---|
| **A. Ne pas bouger les données** | Seuls le code, la documentation et les archives sont réorganisés. | Aucun risque pour les données. | Les noms `dossier_partie_VLM/codex_luna_eval/runs` restent ; le dépôt reste à moitié en désordre. |
| **B. Déplacer et réécrire les chemins** | `git mv` vers `data/`, puis remplacement mécanique du début des chemins dans les 10 889 manifestes et métadonnées. | Dépôt propre, chemins à jour partout. | Modifie les fichiers des lots, contre la règle « ne jamais modifier un lot » ; 10 889 fichiers changent dans l'historique. |
| **C. Déplacer sans réécrire (recommandée)** | `git mv` vers `data/` ; les fichiers enregistrés gardent leurs anciens chemins ; une seule fonction de `playend.common` traduit un ancien chemin en nouveau (« `dossier_partie_VLM/codex_luna_eval/runs/` → `data/annotations/lots/` »). | Dépôt propre ; aucun lot n'est modifié ; empreintes intactes. | Les fichiers anciens mentionnent les anciens noms ; c'est documenté dans `data/README.md`. |

## 5. Règles d'écriture du code et des textes

Ce qui fait « généré » dans le code actuel, et ce qu'on applique à la place :

- **Docstrings** : une ligne qui dit ce que fait la fonction, puis des détails seulement s'ils sont utiles (PEP 257).
  Fini les longs paragraphes qui répètent le code.
- **Commentaires** : seulement pour expliquer un choix non évident, comme le temps monotone parce que l'horloge du Pi
  est fausse (guide Google). Pas de commentaire qui paraphrase la ligne suivante.
- **Noms** : des mots du métier (`lot`, `trace`, `unit`, `boundary`), en `snake_case` (PEP 8). On retire les
  suffixes datés et les noms d'outils ou de modèles (`claude_tools`, `codex_luna_eval`, `luna_batch`,
  `CLAUDE_ANNOTATOR`). Seule exception : la provenance enregistrée dans les données (champ `annotator_model`,
  suffixe `_claude` ou `_luna` des dossiers de lots), qui doit dire honnêtement qui a annoté, et qui est figée
  dans les fichiers enregistrés.
- **Une seule implémentation** pour la lecture des observations effectives, les chemins et l'écriture JSON.
- **Pas de texte promotionnel** dans les README : ce que fait le module, comment le lancer, ce qu'il produit.
- **Formatage automatique** avec Ruff, pour que tout le code ait la même forme.
- **Tests** regroupés dans `tests/`, lancés avant chaque phase et après.

## 6. Phases (chacune validée, commitée et vérifiée séparément)

| Phase | Contenu | Vérification |
|---|---|---|
| 0. Sécurité | Étiquette git `avant-reorganisation` ; mesures de référence : `verify_session_coverage.py --all`, tests, empreintes de toutes les étiquettes et de tous les `units.json`. Les fichiers d'essai du GRU (non commités) vont sur une branche à part. | Tout est enregistré avant de toucher à quoi que ce soit. |
| 1. Archives et doublons | Les travaux terminés vont dans `archive/` avec un README d'index. On supprime les copies exactes, en gardant une copie de chaque. | Aucun script actif ne référence un fichier archivé. |
| 2. Paquet `src/playend` | Déplacement du code actif par `git mv` dans les modules métier ; module `common` (chemins, lecture des observations) ; plus de `sys.path`. | Tests ; les commandes régénèrent des étiquettes **identiques à l'octet près**. |
| 3. Données | Selon l'option choisie (A, B ou C). | `verify --all` : 0 problème ; mêmes empreintes. |
| 4. Documentation | `README.md`, `docs/` ; `CLAUDE.md` devient `AGENTS.md` (moins de 200 lignes), avec les conventions par jeu dans `docs/conventions/` et un `.claude/CLAUDE.md` caché qui l'importe seulement. | Relecture par l'utilisateur. |
| 5. Nettoyage du code | Module par module : noms, docstrings, commentaires, code mort, Ruff. | Tests et étiquettes identiques après chaque module. |
| 6. Vérification finale | Toute la chaîne relancée, comparaison avec les mesures de la phase 0. | Rapport de comparaison. |

## 7. Décisions de l'utilisateur (2026-10-04)

1. Données : **option C**. Déplacement vers `data/` par `git mv`, sans réécrire les chemins enregistrés ; une
   fonction de `playend.common` traduit les anciens chemins.
2. Langue : **code, docstrings et commentaires en anglais ; README et documentation en français.**
3. Nom du paquet : **`playend`**.
4. Travaux terminés : **gardés dans `archive/`**, avec un README d'index.
5. Pas de nom d'outil ou de modèle dans les noms du code et des documents. `CLAUDE.md` devient **`AGENTS.md`**,
   le standard ouvert lu par Claude Code (version 2.1.277 et suivantes), Codex, Cursor, Copilot, Gemini CLI…
   Un `.claude/CLAUDE.md` caché, qui contient seulement `@../AGENTS.md`, couvre les sessions qui ne lisent que
   `CLAUDE.md` [10]. La documentation conseille de rester sous 200 lignes [10] : les conventions par jeu passent
   dans `docs/conventions/`. Confirmé par l'utilisateur.

## Sources

1. DrivenData. *Cookiecutter Data Science — Opinions*. https://cookiecutter-data-science.drivendata.org/opinions/
2. Wilson, G. et al. (2017). *Good enough practices in scientific computing*. PLOS Comput. Biol. 13(6), e1005510. https://doi.org/10.1371/journal.pcbi.1005510
3. Noble, W. S. (2009). *A Quick Guide to Organizing Computational Biology Projects*. PLOS Comput. Biol. 5(7), e1000424. https://noble.gs.washington.edu/papers/noble2009quick.html
4. Python Packaging Authority. *src layout vs flat layout*. https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
5. Madisoft Labs. *Folder structure for big projects: package by type, layer or feature*. https://labs.madisoft.it/folder-structure-for-big-projects-package-by-type-layer-or-feature/
6. van Rossum, G., Warsaw, B., Coghlan, A. *PEP 8 — Style Guide for Python Code*. https://peps.python.org/pep-0008/
7. Goodger, D., van Rossum, G. *PEP 257 — Docstring Conventions*. https://peps.python.org/pep-0257/
8. Google. *Google Python Style Guide*. https://google.github.io/styleguide/pyguide.html
9. Git. *git-log, option --follow*. https://git-scm.com/docs/git-log
10. Anthropic. *Claude Code — How Claude remembers your project* (AGENTS.md, `.claude/CLAUDE.md`, imports `@path`, moins de 200 lignes). https://code.claude.com/docs/en/memory ; InfoQ (2025). *AGENTS.md*. https://infoq.com/news/2025/08/agents-md/
