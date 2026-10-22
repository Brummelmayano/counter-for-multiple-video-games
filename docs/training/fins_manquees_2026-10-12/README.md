# Les fins manquées, cas par cas : analyses et relectures (11 et 12 octobre 2026)

Synthèse : `../FINS_MANQUEES_CAS_PAR_CAS_2026-10-12.md`. Ce dossier garde le travail qui la fonde.

- `BRIEFING.md` et `REVUE_BRIEFING.md` : les consignes données aux huit analystes et aux trois relecteurs.
- `lots.json` : la répartition des 211 fins en huit lots, par jeu.
- `analyses/lot*.jsonl` et `.md` : une analyse par fin, faite sur les captures (cause, ce qui prouve la fin, problème
  d'observation, pourquoi chaque détecteur l'a manquée, méthode qui l'aurait trouvée), puis la synthèse de chaque lot.
- `analyses/revue_apprentissage.*`, `revue_annotation.*`, `revue_terrain.*` : les trois relectures contradictoires
  (chercheur en apprentissage automatique, spécialiste des annotations, gérant de salle), un avis par fin.
- `causes_par_fin.csv` : les quatre avis fusionnés, la cause de consensus, le coût pour la salle et la durée de la
  partie, une ligne par fin.
- `scripts/dossiers.py` : construit un dossier et une planche de captures par fin manquée, à partir de
  `build/training/v1/ends.csv` (`python -m playend.training.missed`) ; `scripts/merge.py` : fusionne les analyses.
  Les deux écrivent dans `build/observations/fins_manquees/` (hors de git : les planches montrent des pseudos),
  avec `CAUSES_PAR_FIN.md`, la version lisible de la fusion, qui renvoie vers chaque planche.

Aucun pseudo de joueur n'apparaît dans ces fichiers (vérifié avec la liste privée).
