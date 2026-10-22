# Les fins manquées par les détecteurs (analyse du 11 octobre 2026)

> **Remplacée par `FINS_MANQUEES_CAS_PAR_CAS_2026-10-12.md`**, l'analyse cas par cas des 211 fins manquées, faite sur
> les images par huit analystes et trois relecteurs. Ce premier classement venait des observations et des textes de
> preuve, avec cinq planches regardées. Deux affirmations y sont fausses : le bandeau « Fin de la course ! » de Beach
> Buggy Racing 2 n'est pas un écran de fin oublié (un autre joueur roule encore ; c'est un signe que la fin approche),
> et la famille 6 (seuils) est en partie un problème d'échelle des probabilités entre modèles, pas seulement de
> budget.

Demandée par l'auteur : répertorier toutes les fins manquées, pour tous les jeux et tous les détecteurs, puis les
regarder une par une. Rien n'est réentraîné : l'analyse relit les prédictions du calcul complet du 6 octobre
(`build/training/v1/`), au budget d'une fausse fin pour 100 parties, sur les 285 fins évaluées des 25 sessions tenues
à l'écart.

```bash
python -m playend.training.missed      # écrit build/training/v1/ends.csv (copie : resultats_2026-10-06/fins.csv)
```

Le tableau donne, pour chaque fin : le résultat de chaque détecteur (le GRU compte comme ayant trouvé la fin si au
moins 3 de ses 5 graines la trouvent), la probabilité la plus haute du GRU et du gradient boosting à côté du seuil de
leur tour, et ce que montrent les observations autour de la fin : écran de fin sur la capture qui la prouve (résultat
affiché ou phase d'après-partie, la règle qui redonne les 229 fins sans écran de fin), type de cet écran, captures
intermédiaires, participants et score avant et après, mots de relance ou d'abandon dans la preuve. Pour chacune des
76 fins manquées par les quatre détecteurs, une planche des captures (dernière capture de la partie, captures
intermédiaires, capture qui prouve la fin, capture suivante) est dans `build/observations/fins_manquees/`, hors de git
parce que les captures montrent des pseudos.

## Vue d'ensemble

Sur 285 fins : le gradient boosting en trouve 121, le GRU 105, la régression logistique 24, les règles 159. 133 fins
sont manquées à la fois par le gradient boosting et par le GRU, 76 par les quatre détecteurs.

| Ce qui entoure la fin | Fins | GRU | Gradient boosting | Régression logistique | Règles | Manquées par les quatre |
|---|---:|---:|---:|---:|---:|---:|
| Écran de fin sur la capture qui prouve la fin | 66 | 68 % | 76 % | 26 % | 45 % | 3 |
| Pas d'écran de fin | 219 | 27 % | 32 % | 3 % | 59 % | 73 |
| La fin se prouve par une capture de jeu (partie suivante déjà commencée) | 114 | 17 % | 35 % | 4 % | 50 % | 49 |
| La fin se prouve par un menu de pause | 10 | 20 % | 10 % | 10 % | 40 % | 6 |
| Mêmes participants avant et après | 108 | 22 % | 43 % | 6 % | 56 % | 36 |
| Participants différents | 177 | 46 % | 42 % | 10 % | 55 % | 40 |
| Partie relancée ou abandonnée (d'après la preuve) | 69 | 17 % | 22 % | 1 % | 52 % | 29 |
| Jeu d'une seule session | 64 | 6 % | 31 % | 0 % | 45 % | 24 |

Le détail par type d'écran et par jeu s'affiche avec la commande.

## Les familles de fins manquées

### 1. Les revanches et les parties recommencées

Quand les mêmes participants rejouent, le GRU ne trouve plus que 22 % des fins, contre 46 % quand les participants
changent ; le gradient boosting n'est pas touché (43 % et 42 %). Quand la partie est relancée ou abandonnée, les deux
tombent sous 25 %. Rien n'annonce alors la fin : pas d'écran de résultat, les mêmes noms ; seul le retour aux valeurs
de départ la trahit.

- Mortal Kombat 1, `f0067594` U49 : capture 514, menu de pause avec « RECOMMENCER » en surbrillance ; 515, le combat
  repart à 0–0 avec les mêmes combattants. Dans cette session, 28 fins sont prouvées ainsi (« retour à 0–0 avec les
  mêmes combattants et un chrono de début de round ») ; 11 sont manquées par les quatre détecteurs.
- EA Sports UFC 5, `f8c2843d` U18, U20, U22, U23 : le chrono du premier round remonte (2:54 puis 4:48) avec le bandeau
  « COULEUR DU SHORT » du début d'un combat : le combat a été relancé.
- EA Sports FC, `11029423` U15, U16, U17, U20 ; `7616a3a5` U09 ; `9e0e6a4f` U01 ; `fdb79549` U08 : un nouveau match
  entre les mêmes équipes, souvent après un écran d'équipe ou une capture sans tableau de score. Pour U20 (4–5 à 88:14,
  capture sans tableau de score, 0–0 à 04:14), le GRU monte à 0,09 pour un seuil de 0,57. La fin de la figure 3.2,
  passage direct de 6–5 à 0–0, est trouvée (0,98) : la capture sans tableau de score entre les deux matchs efface la
  rupture dans les variables qui comparent une capture à la précédente.

### 2. Le menu de fin de match d'EA FC noté « pause »

Dans `11029423`, après le coup de sifflet final, EA FC affiche un menu « Quitter le match / Recommencer ce match » avec
le score final et le chrono à 90:00. Le professeur l'a noté comme une pause (`pause`, phase `paused`, aucun résultat),
comme un arrêt au milieu d'un match. Les fins U03, U06, U07, U08 et U13 de cette session, prouvées par ce menu, sont
manquées par les quatre détecteurs ; sur les 10 fins prouvées par un menu de pause, le gradient boosting en trouve 1.
Hors du chrono à 90:00, rien ne distingue ce menu d'une pause en cours de match.

### 3. Des écrans de fin que l'observation ne marque pas

- EA FC, `f0067594` U29 : la capture 254 affiche « FIN DU MATCH — Arsenal 7–4 Real Madrid », mais l'observation la
  note comme une capture de jeu en cours, sans résultat. Manquée par les quatre.
- Beach Buggy Racing 2 : le bandeau « Fin de la course ! » est visible sur la dernière capture de cinq courses (U15,
  U19, U29, U32, U35) sans être noté comme un résultat ; la fin est placée sur la capture suivante, au « TOUR 1 » de la
  course d'après.
- Les menus de la famille 2 montrent eux aussi le score final.

Les 229 fins « sans écran de fin » sont donc celles dont la capture de preuve n'est pas notée comme un écran de fin
dans l'observation ; quelques-unes montrent pourtant un écran de fin. Les compter exactement demande de regarder
chaque capture de preuve. L'écran de fin est l'indice le plus utile (76 % des fins trouvées par le gradient boosting
avec lui, 32 % sans) : chaque écran de fin non marqué est un indice perdu.

### 4. Beach Buggy Racing 2 : le tour qui revient à 1

14 des 27 fins sont manquées par les quatre détecteurs ; le GRU n'en trouve aucune. D'une course à la suivante, rien ne
change sauf le compteur de tours, qui revient de 3 à 1 (« TOUR 1 »). C'est le seul jeu de course de PlayEnd, et aucune
règle écrite ne regarde ce retour.

### 5. Tekken 8 : le compteur de victoires

8 fins manquées par les quatre, prouvées par le compteur de victoires consécutives qui change (« WIN 1 » puis
« WINS 2 ») ou par le menu de revanche. Le gradient boosting monte à 0,95 et 0,94 sur U02 et U22, sous le seuil de son
tour (0,97).

### 6. Des seuils très hauts pour le gradient boosting

Le seuil du gradient boosting dépasse 0,95 dans 15 des 20 tours qui ont des fins (médiane 0,97). 76 de ses 164 fins
manquées ont une probabilité d'au moins 0,5 : il voit beaucoup de fins que le budget strict l'empêche d'annoncer. Pour
le GRU (seuil médian 0,64), c'est le cas de 22 fins manquées sur 180 seulement : ses fins manquées ont presque toujours
une probabilité basse. Le budget de cinq fausses fins pour 100 parties montre ce que coûte de relâcher le seuil
(60,4 % des fins pour 4,2 fausses fins avec le gradient boosting).

### 7. Les autres cas

Des parties abandonnées pour l'accueil de la console ou un autre jeu (Dragon Ball Sparking! ZERO `fdb79549` U04, qui
finit au lancement d'EA SPORTS FC 26 ; Mortal Kombat 1 `11029423` U31, manette déconnectée puis accueil de la PS5 ; EA
FC `fdb79549` U09, mise hors tension de la PS5), des fins de Dragon Ball FighterZ dans un tour au seuil de 0,99, et une
partie de Fortnite quittée.

## Pistes, non faites

- Conventions du professeur : noter le résultat sur les menus de fin de match (score final, chrono au temps
  réglementaire) et sur les bandeaux « FIN DU MATCH » ou « Fin de la course ! ».
- Variables : le chrono de round qui revient à sa valeur de départ, le tour qui revient à 1, le compteur de séries qui
  change ; elles existent en partie mais ont peu d'exemples.
- Associer au gradient boosting les indices de retour aux valeurs de départ, qui font trouver aux règles 59 % des fins
  sans écran de fin.
- Plus de jeux de course et plus de revanches dans les données.

## Limites

Le classement vient des observations et du texte de preuve de chaque partie, pas d'une relecture de toutes les
captures. Les planches de cinq cas ont été regardées (EA FC `11029423` U06 et U20, `f0067594` U29 ; Mortal Kombat 1
`f0067594` U49 ; UFC 5 `f8c2843d` U18). « Mêmes participants » compare les noms tels qu'ils sont écrits dans les
observations : les noms longs d'EA FC notés par le premier professeur peuvent fausser quelques cas.
