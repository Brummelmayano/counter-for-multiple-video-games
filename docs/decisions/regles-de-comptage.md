# Règles de comptage et de facturation

Décisions de l'utilisateur, avec leur date. Le VLM décrit l'image et le GRU trouve les fins de partie et le mode de
facturation ; ces règles disent ce qui compte comme une partie. La version que lit la couche de facturation est
[regles_facturation.json](regles_facturation.json).

## Ce qui est une partie

- Un match recommencé ou quitté avant la fin compte comme une partie complète : sa fin est une frontière
  (2026-09-29).
- Une partie encore en cours à la fin de la capture n'a pas de frontière (`incomplete_at_capture_end`).
- Un match simulé (Carrière FC : « Simuler match ») n'est pas joué, donc pas compté.
- Fortnite en écran partagé = une seule partie, même si les deux joueurs n'ont pas le même sort (2026-09-29).
- Île d'attente Fortnite quittée avant le bus : pas une partie (2026-10-02).
- Beach Buggy Racing 2 : une course = une partie, et non le championnat de 8 épreuves (2026-10-04).
- Le système signale le début d'une partie, pas sa fin (2026-10-12, plan dans
  [PLAN_COMPTAGE_PAR_DEBUT.md](PLAN_COMPTAGE_PAR_DEBUT.md)). Le début se place sur la première capture de jeu de la
  nouvelle partie dont le HUD est lisible (score, chrono, tour, vies, joueurs restants) (2026-10-13). Sans HUD lu, pas
  de début : dans PlayEnd, toutes les parties montrent un HUD lisible. Un HUD lisible ne suffit pas : les modes au
  temps et les écrans de résultat en montrent aussi ; il faut aussi les valeurs de départ (0–0, tour 1…) et un mode
  qui a une fin de partie.
- Une partie déjà en cours sur la première capture d'un enregistrement commence sur cette capture et compte, même si
  le score montre qu'elle a commencé avant (2026-10-13). En écran partagé de Beach Buggy Racing 2, les places de
  chaque vue, écrites en note, suffisent comme HUD lisible : la course commence sur sa première image de jeu
  (2026-10-13).

## Ce qui est facturé au temps

- Les jeux et modes sans fin de partie sont facturés au temps, jamais comptés (2026-09-29) : tous les jeux de mission
  et de monde ouvert qui n'ont presque pas de fin (The Last of Us, GTA, Assassin's Creed, Red Dead Redemption 2,
  Genshin Impact avec ses défis et tests DPS, et tout nouveau jeu du même genre), et les modes sans fin des jeux de
  combat (Mortal Kombat 1 entraînement avec `∞`). Aucune frontière n'y est placée et aucun signal d'incrément n'est
  produit. Ces passages sont déclarés en `time_segments` dans `units.json` ; `billing_mode` vaut alors `"temps"`, et
  un système externe au modèle facture la durée.
- Red Dead Redemption 2 au temps : confirmé le 2026-09-29.
- Îles créatives Fortnite (Super Pit, Scrims…) : au temps (2026-10-02).
- J-Stars Victory VS+, mode histoire « Aventure-J » : la carte, les dialogues et les quêtes au temps ; ses combats
  sont des parties (2026-10-13, qui tranche la règle « à confirmer » du 2026-10-04).

## Ce qui n'est pas facturé

- Les écrans hors jeu (accueil PS5, menus, chargements, sélections, entre deux parties) ont
  `billing_mode = "hors_jeu"`.
- Relance ou abandon très rapide (2026-10-02) : non facturé en dessous de 60 s de jeu, 15 s pour les jeux de combat.
  La durée se mesure de la première à la dernière observation en jeu de la partie ; une partie vue sur une seule
  capture compte 0 s, en faveur du client (2026-10-03). Les annotations ne changent pas et la frontière reste placée :
  c'est la couche de facturation qui applique ce seuil.
- Le temps mort n'est jamais facturé (2026-10-04) : quand personne ne joue (écran de mort, pause ou menu laissé
  longtemps sans reprise, comme God of War « VOUS ÊTES MORT » pendant 11 min dans fdb79549), ces images sortent du
  `time_segment` et passent en `hors_jeu`. Cela ne vise que le temps mort sans reprise, quand l'écran reste figé
  jusqu'à l'abandon du jeu : une pause, un menu ou un écran de mort suivi d'une reprise reste facturé, même s'il dure
  quelques minutes.

## Le comptage après le GRU

Appliqué par le compteur (`src/playend/counting/`, voir `docs/counting/README.md`). Ce dépôt s'arrête au comptage :
les prix et la facture sont l'affaire du produit (2026-10-05).

- Le temps se mesure passage par passage, de la première à la dernière capture au temps (2026-10-05).
- Une partie encore en cours quand le client part compte si son temps de jeu dépasse déjà le seuil de relance rapide,
  sinon non (2026-10-05).
- Le temps sans image (plus de 60 s entre deux captures : câble débranché, console éteinte…) reste compté avec la
  partie ou le passage au temps qui l'entoure, et la ligne l'indique ; l'opérateur tranche avec le client
  (2026-10-05).
- Laissé au produit (2026-10-05) : prix par genre de jeu et prix du bloc de temps, réglés par l'employé ou
  l'employeur ; arrondi du temps au bloc supérieur une seule fois par client ; mention « dont … sans image » sur la
  facture.

## Annotation

- Tout annoter d'abord (images et frontières de chaque session), valider à la fin pour tout le jeu de données. En cas
  de doute, choisir la valeur la plus prudente (`null` ou `unknown`), l'expliquer dans la note de l'image et ajouter le
  cas aux « Points à confirmer » du `REVIEW.md` de la session.
- Participants = seulement le texte écrit sur l'image (2026-10-03).
- Libellé du mode en texte libre, sans champ `mode_label` pour le premier entraînement du GRU (2026-10-02).
- Dragon Ball Sparking! ZERO : barres de vie restantes notées en `lives` (2026-10-04).
- Beach Buggy Racing 2 en écran partagé : position vide, place de chaque vue en note (2026-10-04).

Le détail de chaque convention est dans [docs/conventions/](../conventions/README.md).
