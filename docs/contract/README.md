# Contrat d'observation 2.1 et entrées GRU 4.0

Mise à jour du 29 septembre 2026. Images entières uniquement.

## Nouveautés 2.1 (29 septembre 2026) : compteurs secondaires universels

Le contrat 2.1 ajoute **une seule clé racine**, `secondary_counters`. Elle recense les compteurs visibles qui mesurent **ce qui reste avant la fin** d'une partie, avec la même forme pour tous les jeux :

```json
{"kind": "players_remaining | teams_remaining | lives | target | series | other | unknown",
 "side": "a | b | field", "value": 46, "total": null, "label": null}
```

| `kind` | `side` | Exemples |
|---|---|---|
| `players_remaining` | `field` | Fortnite, Warzone : joueurs en vie |
| `teams_remaining` | `field` | Warzone : escouades en vie |
| `lives` | `a` / `b` | Brawlhalla : stocks de chaque camp |
| `target` | `field` (ou `a` / `b`) | 2 emplacements de rounds (MK1, Tekken), limite de score « 100 » (Call of Duty), **seulement si le HUD l'affiche** |
| `series` | `a` / `b` / `field` | Tekken « WINS 2 », série de Rocket League |
| `other` / `unknown` | tous | autre compteur de fin, ou rôle ambigu |

- `null` = inventaire non fait ou impossible ; `[]` = HUD inspecté, aucun compteur de ce type.
- Il y a au plus un élément par couple (`kind`, `side`), sauf pour `other` et `unknown`.
- Ne sont **pas** des compteurs de fin : éliminations, dégâts, combos, vie, munitions, argent, XP, niveaux.
- Règles complètes dans [counter_rules.txt](../../src/playend/contract/counter_rules.txt), insérées dans les prompts générés par `build_assets.py`.

**Compatibilité** : les observations 2.0 restent valides (`validate_observation` accepte 2.0 et 2.1). `upgrade_v20()` les lit en mémoire avec `secondary_counters=null` (inconnu), sans rien deviner et sans modifier le fichier. Les valeurs notées en texte dans les annotations existantes (par exemple les joueurs restants de Fortnite) pourront être ajoutées plus tard par des traces séparées.

**Entrées GRU 4.0** ([gru_feature_spec_v4.json](../../src/playend/contract/gru_feature_spec_v4.json), 262 variables au lieu de 201) :
- compteurs par emplacement fixe (valeur, `known`, variation dans le même contexte de jeu) ;
- `game.mode` en catégories fixes, indice pour la sortie `billing_mode` ;
- `clock.infinite` (« ∞ »), pour ne plus le confondre avec un chrono illisible ;
- `period.is_last` (round, quart-temps ou set = total) ;
- `observation_missing` : ligne gardée quand le VLM échoue sur le Pi. On la déclare dans le manifeste avec `"observation_missing": true` et sans `observation_path`.

`gru_feature_spec_v3.json` est conservé comme trace historique : les checkpoints v3 sont incompatibles avec la v4.


`clock` décrit le chrono principal courant du match, de sa période sportive,
de la course ou de la mission. `secondary_timers` conserve séparément les
compteurs secondaires. Une minute de but, un replay ou l'heure système ne
renseignent aucun de ces deux champs.

Exemple **illustratif**, sans prétendre annoter une capture réelle :

```json
{
  "clock": {"visible": false, "display": null, "value_seconds": null, "direction": null},
  "secondary_timers": [
    {"kind": "storm_phase", "label": null, "display": "0:44", "value_seconds": 44, "direction": "unknown"}
  ]
}
```

Ce fragment doit être complété avec les autres champs du [modèle JSON](../../src/playend/contract/observation_v2.template.json).
Les rôles autorisés sont `storm_phase`, `contract`, `respawn`, `ability_cooldown`,
`pre_match`, `other`, `unknown`. Chaque élément représente un compteur visible ;
il n'a donc pas de champ `visible` redondant. Son libellé reste le texte réellement
lu, ou null ; plusieurs compteurs du même rôle sont conservés.

| Cas observé | Représentation |
| --- | --- |
| Aucun compteur secondaire après inspection | `secondary_timers=[]` |
| Inventaire incertain/non revu | `secondary_timers=null` |
| Compteur visible mais chiffres illisibles | élément avec `display=null`, `value_seconds=null` |
| Compteur identifié, rôle ambigu | `kind="unknown"` ; si potentiellement principal, `clock.visible=null` |
| Compteur de tempête à zéro | `value_seconds=0`, sans conclusion de fin de partie |
| Minute courante affichée `8'` | texte conservé dans `clock`, secondes null |
| Minute `8'` à côté du buteur | exclue des chronomètres |

La direction reste `unknown` sur une image isolée. Les conversions exactes
acceptent secondes identifiées, mm:ss et h:mm:ss, éventuellement fractionnaires.
Un format incertain garde son texte avec des secondes null.

## Fichiers actifs et compatibilité

- [contract.py](../../src/playend/contract/contract.py) : contrat et validation sémantique/type ; [schéma JSON](../../src/playend/contract/observation_v2.schema.json) pour génération structurée.
- [timer_rules.txt](../../src/playend/contract/timer_rules.txt) : source commune des nouvelles règles de temps.
- [prompt API v4](../../archive/codex-luna-phase/openai_teacher/prompts/full_frame_v4_final_universal.txt) (archivé).
- [prompt universel demandé](../../src/playend/contract/prompts/06_prompt_VLM_universel_COMPACT_STABLE_v1.txt), le seul prompt actif, régénéré par `build_assets.py` : nom historique conservé, contenu et modèle JSON explicitement versionnés 2.0 ; ancienne révision archivée à côté.
- [prompt local universel v6](../../archive/vlm-evaluations-2026-09/evaluation_2026_09_08_heavy/prompts/universal_v6_final_v2.txt) (archivé).
- [temporal.py](../../src/playend/contract/temporal.py) et [prepare_dataset.py](../../src/playend/contract/prepare_dataset.py) : préparation causale indépendante des anciennes expériences.

Le profil 2.0 fixe aussi `score.additional_scores` : null, ou les quatre paires
A/B `games`, `sets`, `tiebreak`, `point_labels`. Une paire non lue vaut
`[null,null]`. Cela garde le même contrat pour la génération structurée et la validation.

Les anciennes observations sans `schema_version` restent validables par
`validate_any`. `legacy_v1.py` est une copie figée du validateur historique
`archive/vlm-evaluations-2026-09/evaluation_2026_09_08_heavy/scripts/schema.py` au moment de cette évolution.
Les anciennes prédictions et le package de reproductibilité GRU n'ont pas été
réécrits. Une conversion ne prouve jamais qu'une image a été relue.

La préparation refuse les anciennes observations par défaut. Avec
`--allow-legacy`, elle les adapte **en mémoire** : ancien chrono masqué, compteurs
secondaires inconnus, statut de revue conservé. Le JSON original et son empreinte
restent référencés. Les paires de scores absentes sont complétées par null ; des
clés de score historiques incompatibles exigent une revue explicite. Il faut
réinspecter l'image entière pour renseigner les nouveaux chronomètres.

## Entrées du GRU

La spécification [gru_feature_spec_v3.json](../../src/playend/contract/gru_feature_spec_v3.json) fixe l'ordre,
la dimension et l'empreinte des nouvelles variables. Elle comprend les scores,
participants, état, période, progression, position, résultat explicite, chrono
principal et compteurs secondaires. Les noms libres ne sont pas encodés comme
identifiants de jeu/joueur ; leurs changements observables sont représentés.

Les nombres utilisent `sign(x)*log1p(abs(x))`, une transformation fixe sans
statistiques apprises sur le test. Toute valeur numérique manquante a un masque
`known=0`. Un zéro réellement lu a `known=1`. Les catégories utilisent des
vocabulaires fixes ; les confiances subjectives du VLM ne sont pas des entrées.

Pour chaque rôle secondaire : nombre de compteurs, nombre de valeurs lisibles,
minimum et maximum des secondes. L'ordre de ces compteurs ne change pas le
vecteur. Les JSON originaux conservent les libellés et chaque valeur ; le vecteur
est une agrégation, pas une représentation sans perte. Aucun identifiant de
contrat ou changement de phase n'est inventé pour associer les compteurs entre images.
Le GRU pourra apprendre à partir de leur succession ; aucun reset secondaire
n'est converti en fin de partie par le préparateur.

`delta_t_s` est la différence **réelle** des `received_monotonic_ns`, calculée
avant conversion en secondes. Il n'est jamais fixé à 0,5 s ou au délai demandé.
Les sessions restent séparées ; les timestamps/frames doivent croître dans une
session. Le modèle entraîné avec ces données devra remettre son état caché à zéro
à chaque `sequence_start=1`. Les deltas du chrono principal exigent un contexte
comparable et une même période explicitement identifiable ; ils restent de simples
différences candidates, pas des labels de frontière.

Les anciens checkpoints à 132/136 entrées sont incompatibles : **réentraînement
nécessaire**. `assert_checkpoint_compatible` contrôle version, ordre, dimension et
empreinte pour un futur chargeur v3. Les anciens scripts d'entraînement/inférence
ne sont pas modifiés ni rendus compatibles par cette mise à jour. Le code ajouté
prépare les données ; il ne livre pas un nouveau GRU entraîné.

## Utilisation depuis la racine du mémoire

Validation de sortie (hors ligne) :

```bash
python -m playend.contract.validate observation.json --require-v2
```

Un manifeste JSONL associe chaque sortie à sa capture :

```json
{"session_id":"session_example","frame_id":1,"received_monotonic_ns":1000000000,"observation_path":"chemin/observation.json","review_status":"proposed_pending_human_review"}
```

Les chemins sont relatifs à la racine du projet (modifiable avec `--project-root`).
Pour une session, ce manifeste est produit par `python -m playend.boundaries.build_labels`
(`data/boundaries/session_<id>/observation_manifest.jsonl`) :

```bash
python -m playend.contract.prepare_dataset --manifest data/boundaries/session_<id>/observation_manifest.jsonl \
    --labels data/boundaries/session_<id>/labels_human_verified.jsonl --out NOUVEAU_DOSSIER
```

La sortie contient `rows.jsonl`, `feature_spec.json` et `report.json`. Le dossier
de sortie doit être nouveau. Les vecteurs `features` sont ordonnés par la
spécification et convertibles en tenseurs float32, session par session.
Sans labels, les cibles sont null et tous les masques de perte sont zéro.

Les labels temporels sont un **fichier séparé**, après vérification de l'intervalle,
avec cette structure :

```json
{"session_id":"session_example","frame_id":2,"previous_frame_id":1,"unit_end_boundary":0,"ended_unit_count":0,"boundary_applicable":true,"review_status":"human_verified"}
```

Ajouter `--labels labels_verifies.jsonl` à la préparation. Les deux bornes de
l'intervalle doivent correspondre aux observations sélectionnées. Le masque vaut
1 uniquement si les labels et les deux observations portent la revue humaine,
sans migration legacy, avec une frontière applicable et au plus une fin dans
l'intervalle. Une proposition de modèle n'est jamais promue automatiquement en
vérité terrain. L'indicateur `human_verified` doit correspondre à une revue
réellement faite ; le script ne peut pas l'attester.

Au-delà d'une fin entre captures, le compte reste en audit et le masque binaire
vaut zéro : il faudra un modèle de comptage adapté. La rareté de captures ne
permet pas de reconstruire avec certitude un événement entièrement invisible.
Pour le futur entraînement, séparer les sessions complètes entre train/validation/test,
réinitialiser les états cachés et évaluer le comptage, pas seulement la loss.

## Vérification et limites

```bash
python -m unittest discover -s tests -t . -v
python -m playend.contract.build_assets
```

La dernière commande régénère les prompts et spécifications depuis leurs sources.
Les tests vérifient aussi qu'ils correspondent aux sources. `jsonschema` est
nécessaire aux tests du schéma ; le contrat et le préparateur n'utilisent que
la bibliothèque standard. Aucun poids de modèle à télécharger.

La [revue technique](VALIDATION.md) distingue les contrôles logiciels des mesures
visuelles encore nécessaires. Aucun appel API payant, nouveau benchmark VLM ou
entraînement réel n'est présenté comme effectué par cette mise à jour.
La génération structurée utilise les objets à clés fixes décrits dans la
[documentation officielle OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs).
Un JSON conforme ne prouve pas l'exactitude de son contenu visuel.

## Alignement du prompt pour la distillation et les comparaisons

Le prompt final complet 06 est la référence. Les variantes actives API v4 et locale v6 sont des copies exactes du même texte généré ; le lot Luna des frames 1–66 contient également ce texte. Les anciens prompts courts restent des variantes historiques explicitement nommées. Le schéma commun ne suffisait pas à rendre leurs consignes identiques.

Pour la comparaison initiale professeur/élève, utiliser le même prompt final et les mêmes images entières. La distillation n'impose pas en général des textes identiques : un élève pourrait ensuite être entraîné avec une instruction plus courte. Ce serait une expérience distincte, avec une nouvelle version et une évaluation dédiée. Aucune instruction courte n'est actuellement adoptée pour l'élève.
