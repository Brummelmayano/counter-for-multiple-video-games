# Décisions pour l'entraînement du GRU v4 (discutées avec l'utilisateur le 2026-09-29)

À appliquer quand toutes les images et frontières seront annotées et validées. Rien n'est encore entraîné en v4.

## Données
- **Toutes les observations restent dans la séquence**, dans l'ordre, avec les vrais `delta_t` : écrans noirs, fondus, menus, missions, accueil PS5, et `observation_missing` quand le VLM échoue sur le Pi.
- **Deux sorties** : `unit_end_boundary` (fin de partie) et `billing_mode` (`partie` / `temps` / `hors_jeu`). Les jeux sans fin de partie sont facturés au temps par un système externe ; le compteur n'incrémente que si `billing_mode = "partie"`.
- La fin de partie est **apprise à 0** hors des parties (menus, missions, noir). On ne masque qu'avec `uncertain_frames`.
- Les annotations 2.0 sont lues avec `secondary_counters` inconnu. **Avant l'entraînement**, compléter les compteurs de Fortnite, Warzone et Tekken (joueurs restants, WINS) par des traces séparées.
  *Fait le 2026-10-05 : les 3 049 observations 2.0 sont converties en 2.1 avec leurs compteurs (traces `20261004_24_compteurs_v21_*`, voir `data/annotations/README.md`).*

## Déséquilibre des classes (environ 1 fin pour 50 à 150 non-fins)
Mesuré le 2026-10-04 sur les 25 sessions validées, corrigé le 2026-10-05 : sur les 8 794 intervalles appris, 285
contiennent une fin, soit environ 1 fin pour 30 non-fins. Les 10 autres fins tombent sur des intervalles masqués comme
incertains. L'estimation du titre datait d'avant la fin de l'annotation.

1. **Pondérer la perte** : `pos_weight = non-fins / fins`, calculé **uniquement** sur les sessions d'entraînement (déjà dans le pilote `train_gru_variants.py`). Passer à √w si le modèle déclenche trop de fausses fins.
2. **Ne jamais dupliquer des images isolées** : cela casserait la temporalité, dont le GRU a besoin.
3. Si nécessaire, **suréchantillonner des fenêtres entières et continues** contenant une fin, qui commencent plusieurs minutes avant, avec un **préchauffage sans perte** (le contexte est lu, la perte n'est calculée qu'autour de la fin). **Recalculer `pos_weight` ensuite**, pour ne pas corriger deux fois.
4. Augmentations qui préservent l'ordre : **sous-échantillonner** des observations (captures plus espacées, `delta_t` recalculés) et assembler des sessions réelles.
5. `billing_mode` : entropie croisée pondérée par l'inverse de la fréquence des classes.

## Décision et évaluation
- **Ne pas garder le seuil fixe de 0,5.** Le choisir sur des sessions de validation : le seuil le plus bas qui garde **au plus 1 fausse fin pour 100 parties**. Une fausse fin, c'est un client facturé en trop.
- Mesures, **par famille de jeu** et par jeu tenu à l'écart :
  - **précision** (protection du client) ;
  - **rappel** (chiffre d'affaires) ;
  - **fausses fins par heure de jeu**.
  - Accepter qu'une fin détectée avec **une observation de retard** (environ 28 s) compte comme juste.
  - Jamais l'exactitude seule : « jamais de fin » donne 98,6 % d'exactitude et 0 partie comptée.
- Refaire l'évaluation avec les sorties du **VLM élève** distillé, et pas seulement celles du professeur.

## Couche de facturation (après le GRU)
- Les règles commerciales sont dans `regles_facturation.json` : facturation à la partie / au temps / hors jeu, relance rapide non facturée (60 s de jeu, 15 s pour les jeux de combat), île d'attente quittée = pas une partie.
- L'évaluation finale doit compter les **parties facturées** (après ces règles), et pas seulement les fins détectées.
