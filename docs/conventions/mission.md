# Mission et monde ouvert

Règles communes (participants, compteurs secondaires, écrans hors jeu) : [README.md](README.md). Pour ces jeux,
`secondary_counters = []`.

Ces jeux n'ont presque pas de fin de partie : ils sont facturés au temps (décision de l'utilisateur du 2026-09-29).
Leurs passages sont déclarés en `time_segments` dans `units.json`, avec `billing_mode = "temps"` ; aucune frontière
n'y est placée. Cela vaut pour The Last of Us, GTA, Assassin's Creed, Red Dead Redemption 2, Genshin Impact (défis et
tests DPS compris) et tout nouveau jeu du même genre. Le temps mort sans reprise n'est pas facturé (voir
[les règles de comptage](../decisions/regles-de-comptage.md)).

Dans l'observation, on décrit quand même ce qui est affiché : « MISSION RÉUSSIE / ÉCHOUÉE » → `result`, objectif →
`progress objective`.

## Genshin Impact

- `mission_adventure`. Recharges sans unité → `ability_cooldown`, non converti.
- Objectifs « 2/6 » → `progress objective`.
- Minuteur « Temps de test » ou de défi → chrono principal.

## Red Dead Redemption 2

- Préréglage `rdr`. `mission_adventure`, mode `free_roam` ou `mission`.
- Prime « RECHERCHÉ », munitions, argent : en note seulement.
- Facturé au temps, confirmé par l'utilisateur le 2026-09-29.

## God of War (PS2) et Assassin's Creed Origins

- Préréglages `gow` et `aco`. `mission_adventure`, `mode = "mission"`, objectif de quête → `progress objective`.
- Vie, magie, orbes, niveau, XP, distances : en note seulement.
- « VOUS ÊTES MORT — RECOMMENCER DERNIER CHECKPOINT » → `post_game/result`, `result other` : c'est la mort du
  personnage, pas une fin de partie.
