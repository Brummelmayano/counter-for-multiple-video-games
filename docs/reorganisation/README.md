# Réorganisation du dépôt

Réorganisation décrite dans [PLAN_REORGANISATION.md](PLAN_REORGANISATION.md), menée le 2026-10-04. Le bilan et
toutes les vérifications sont dans [RAPPORT_FINAL.md](RAPPORT_FINAL.md).

- `mesures-avant.json` : état de référence au commit marqué par l'étiquette git `avant-reorganisation`. Il contient
  la couverture de chaque session (alors `verify_session_coverage.py --all`, aujourd'hui
  `python -m playend.annotation.coverage --all`), les empreintes SHA-256 des fichiers de frontières et de
  validation, celles du prompt et du schéma du contrat, et le résultat des tests.
- `mesures-apres.json` : les mêmes mesures à la fin de la réorganisation.
- `mesurer.py` : le script qui produit ces mesures.

Pour revenir à l'état d'avant : `git checkout avant-reorganisation`.

Les fichiers d'essai d'entraînement du GRU v4 (non autorisé) sont gardés sur la branche locale
`essai/gru-v4-20261004`, à ne pas fusionner sans décision.

## Avancement

| Phase | Commit |
|---|---|
| 0. Mesures de référence | `96ad4412` |
| 1. Archives et doublons | `923202e7` |
| 2. Paquet `src/playend` (2a à 2f) | `5abaad25` à `665c04d5` |
| 3. Données dans `data/` | `3ed7973a`, revue `34d75311` |
| 4. Documentation (`README.md`, `AGENTS.md`, `docs/`) | `fcf1e13a`, nom du projet `08dac4d9` |
| 5. Nettoyage du code | `ec4736d2`, `bc12008d`, `d9d0fa2b`, `aac7cc84` |
| 6. Vérification finale | [RAPPORT_FINAL.md](RAPPORT_FINAL.md) |

Pour refaire la comparaison : `python docs/reorganisation/mesurer.py > nouvelles-mesures.json`, puis comparer avec
`mesures-apres.json`. Par rapport à `mesures-avant.json`, seules les fiches `REVIEW.md` diffèrent (liens vers les
images et phrase d'introduction), et le prompt et le schéma y sont repérés par leur ancien chemin plutôt que par leur
nom, avec les mêmes empreintes.
