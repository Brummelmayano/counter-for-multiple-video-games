# Points à confirmer (validation finale)

Cas relevés pendant l'annotation, à trancher lors de la validation humaine de fin de projet.

- **session_110294…, frames 33–41 (UFC 5, Pereira–Silva, annotation Luna)** : `clock` lu 23:52 → 22:27 → 24:17. Un chrono qui remonte au milieu d'un combat n'est pas un chrono de round : erreur de lecture ou autre mode (entraînement) ? Revoir les images avant de construire les frontières de cette session.
- **session_110294…, frame 31 (UFC 5, après Prates–Brady, annotation Luna)** : l'écran affiche « TKO » et « R3 01:54 » en fond (menu d'après-combat Revanche / Statistiques / Changer de combattants / Voir rediffusion / Quitter + carte des juges 20–18). Luna a noté `outcome_type="other"` : probablement `tko` (vainqueur non écrit). À corriger par une trace séparée après validation.
- **Contrat 2.0, évolution possible (à décider)** : conserver le libellé de mode visible avant le combat (ex. UFC « Combat principal — Défendre ou disputer la ceinture ») au lieu de le réduire à `bout`, pour que le GRU apprenne la durée probable (3 ou 5 rounds) sans déduction par le VLM.
- **session_110294…, frames 9–28 (UFC 5 Prates–Brady, annotation Luna)** : la barre de 5 segments sous la jauge encode le round et le total (1/5 aux frames 13–16, 2/5 aux frames 21–25, 3/5 à la frame 28), mais Luna a laissé `period.number` et `period.total` à null sur ces frames. Compléter par une trace de correction après validation.
- **session_110294…, frames 1144–1149 (UFC 5 Sonnen–Adesanya, annotation Claude)** : badge « R1 » suivi de 4 petites barres. Le total (5 ?) n'a pas été rempli, faute de certitude sur la signification des barres.
- ~~GRU : variable « dernière période »~~ → **fait** (GRU v4 : `period.is_last`).
- ~~Contrat : joueurs restants~~ → **fait** (contrat 2.1 : `secondary_counters`, `players_remaining` / `teams_remaining`). Annotations 2.0 existantes complétées par des traces séparées (`data/annotations/corrections/`, voir plus bas).
- **Fortnite, modes créatifs (à décider)** : carte « Scrims » avec « manches 03/60 », Box PVP… Faut-il compter chaque manche, ou toute la session sur la carte ?
- ~~Contrat : stocks, objectif, série~~ → **fait** (2.1 : `lives`, `target`, `series`). **Encore ouvert** : `mode_label` (libellé du mode ou du format).
- ~~Missions GTA / Assassin's Creed, activités Genshin~~ → **décidé le 2026-09-29** : les jeux et modes sans fin de partie (tous les jeux de mission presque sans fin : The Last of Us, GTA, Assassin's Creed, Red Dead Redemption 2, Genshin Impact ; MK1 entraînement ∞) ne sont pas comptés. Ils sont facturés au temps par un système externe (`billing_mode="temps"`, aucune frontière).
- **Règle commerciale encore ouverte** : les modes créatifs de Fortnite.
- **Réglages à imposer dans la salle** : EA FC « Score Clock : On », UFC « HUD : On », pas de chrono infini dans les combats facturés.
- **Contrat 2.1 mis en œuvre (2026-09-29)** : `secondary_counters` universel (joueurs et équipes restants, vies, objectif, série) et GRU v4. **Fait le 2026-09-29** : compteurs des annotations 2.0 de Luna complétés par des traces séparées, lus au zoom image par image (`data/annotations/corrections/` : Tekken WINS 128 images, Warzone 799ac2 13 et 078643 66, Fortnite 279216 37, a4e41f 17, ff1c72 462 dont 39 Warzone). Restent ouverts : un champ pour le libellé du mode, et l'état par vue en écran partagé.

## Ajouts du 2026-09-29 (fin de l'annotation, Claude)

Toutes les sessions sont annotées et ont leurs frontières. Détails session par session dans `session_<id>/REVIEW.md` (section « Points à confirmer »). Principaux sujets :

- **Parties recommencées ou quittées** (très nombreuses : FC relancé à mi-match, UFC relancé au 1er round, MK1 et Tekken en revanches rapides, finales UCL quittées) : toutes comptées comme parties complètes, selon la règle. À confirmer commercialement pour les relances après moins d'une minute de jeu.
- **Fins établies a posteriori** (retour à 0–0 avec les mêmes combattants, nouveau coup d'envoi, salon) sans écran de fin : sessions `f00675` (55 matchs MK1), `110294` (10 matchs MK1 Ghostface–Johnny Cage) et `8e58b1`. Risque de fausse fin si un marqueur a été mal lu : **à vérifier en priorité**.
- **Tekken (`078643`)** : les frontières reposent sur le compteur « WINS n ». **Fait** : ajouté en `series` (et `target` 2) par la trace séparée `data/annotations/corrections/20260929_02_compteurs_tekken_078643` (128 images) ; les pastilles de Luna, revérifiées au zoom, concordent. Fin de U29 avancée à 177 (pause où WINS 2 est déjà affiché).
- **Modes créatifs Fortnite** (Super Pit UNC dans `fe6975` 278–318, Scrims Palestine dans `a4e41f` 99–127) : déclarés facturés au temps en attendant la règle commerciale.
- ~~Nouveaux jeux facturés au temps : Red Dead Redemption 2~~ → **confirmé par l'utilisateur le 2026-09-29** (`c93ed3`, `378c62`) : tous les jeux de mission qui n'ont presque pas de fin (The Last of Us, GTA, Red Dead Redemption 2, etc.) sont facturés au temps.
- **Nouveaux jeux comptés** : Demon Slayer Hinokami Chronicles, Dragon Ball FighterZ (conventions dans `docs/conventions/combat.md`).
- **Corrections d'annotations existantes** : **faites** par la trace séparée `data/annotations/corrections/20260929_01_observations_signalees` (Luna `279216` frame 55, Luna `078643` frame 77, Claude `fe6975` frame 126). À valider avec les autres observations.
- **UFC Pereira–Silva (`110294` 33–41)** : chrono de 21 à 24 minutes dans une arène à l'ancienne ; mode particulier ? Compté avec une confiance faible.
- **Prolongations FC 27/FC 26** : sans libellé « PR » lisible, la période reste `unknown` (a80bda, 7616a3).
- **Traces de correction (2026-09-29)** : 7 traces, 726 observations corrigées sans toucher aux lots (`data/annotations/corrections/README.md`). Les frontières ont été régénérées sur les observations corrigées ; elles ne changent pas, sauf la fin de U29 dans `078643` (178 → 177, pause où WINS 2 est déjà affiché). Pendant la relecture de `ff1c72`, trois observations Luna (174, 629, 630) portaient le minuteur et le nombre de joueurs d'une autre image : minuteurs corrigés. **À surveiller** : d'autres notes Luna de ce lot pourraient décrire une image voisine.
- **Fortnite `ff1c72` 554–557** : île d'attente jusqu'au lancement du bus (556), puis salon. Non compté faute de jeu visible ; si c'est une partie quittée au lancement du bus, la règle « quittée = partie complète » la compterait. Même cas dans `279216` 29–30 (île puis salon). À trancher.
- **UFC 5 `f8c284` (610–676)** : participants corrigés par la trace séparée `data/annotations/corrections/20260929_08_noms_ufc_f8c284` (44 images; 10 déjà justes). Les observations laissaient les noms vides ou prenaient les couleurs du short pour les participants (613, 623, 628, 650). Convention ajoutée dans `CLAUDE.md` : participants = noms en haut à gauche et à droite, jamais les couleurs du short. Les 8 frontières UFC sont inchangées : chaque relance oppose les mêmes combattants et reste prouvée par le chrono revenu à 4:xx au 1er round et le bandeau de début de combat.

## Décisions de l'utilisateur du 2026-10-02 (les 4 règles ouvertes)

1. **Îles créatives Fortnite** (Super Pit, Scrims…) : **facturées au temps** (`time_segment`, `billing_mode="temps"`). Déjà appliqué (`fe6975` 278–318, `a4e41f` 99–127).
2. **Relances ou abandons très rapides : non facturés** si la relance arrive avant un seuil de temps de jeu. Les annotations ne changent pas : le GRU détecte toujours la fin. C'est la couche de facturation, après le GRU, qui ne facture pas. **Seuil fixé le 2026-10-02 : par genre** : 60 s de jeu pour le foot, l'UFC/la boxe, les battle royale, la course, le tennis et le basket ; **15 s** pour les jeux de combat (MK1, Tekken, Naruto…), dont les vrais combats durent souvent moins d'une minute. Règles lisibles par programme : `regles_facturation.json`.
3. **Île d'attente quittée avant le bus** : **pas une partie** (le joueur n'a pas joué). Déjà appliqué (`ff1c72` 554–557, `279216` 29–30).
4. **Champ `mode_label`** : **pas maintenant**. Le libellé reste dans les notes ; on l'ajoutera après le premier entraînement du GRU si besoin.
