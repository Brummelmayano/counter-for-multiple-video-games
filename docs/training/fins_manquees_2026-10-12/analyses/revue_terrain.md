# Relecture « terrain » des 211 fins manquées

Je relis les huit lots avec l'œil d'un gérant de salle qui fait payer à la partie, et d'un joueur de football, de
combat, de battle royale et de course. Ma question n'est pas seulement « pourquoi le détecteur a raté cette fin »,
mais « combien cette fin ratée coûte à la salle, et qu'est-ce que le client a fait pour en arriver là ».

J'ai lu les huit fichiers `lot*.md` en entier. J'ai ouvert les dossiers `cas/*.json` pour les rôles des captures et
les probabilités, et les images originales deux fois, pour vérifier deux affirmations qui changent le compte :
la fin manquée à l'étiquetage dans `f0067594` U37 (captures 415 à 421, confirmée) et l'écran de départage d'un nul
dans `11029423` U07 (capture 203, confirmé, mais il change le placement de la fin). Je n'ai fait aucune recherche
en ligne.

## Comment je mesure le coût d'une fin manquée

Le compteur (`docs/counting/README.md`) ouvre une partie à sa première capture à la partie et la ferme à la fin
suivante. Une fin manquée fond donc la partie N et la partie N+1 en une seule ligne. La salle perd une partie quand
les deux auraient été facturées, c'est-à-dire quand chacune dépasse son seuil de relance rapide (15 s pour les jeux
de combat, 60 s pour l'UFC, le football, la course et le battle royale), mesuré de la première à la dernière capture
en jeu. J'ai tiré ces durées de `build/playend_v1.0/data/units.csv` et `observations.csv`, avec le type de jeu le
plus lu sur la partie, comme le compteur.

Une fin manquée ne coûte rien dans trois cas :

- c'est la dernière partie de l'enregistrement : la partie reste ouverte et elle est comptée au départ du client,
  puisqu'elle dépasse son seuil (8 cas) ;
- la partie elle-même ou la suivante est une relance trop courte pour être facturée (8 cas : Tekken U22 et U23,
  Dragon Ball `f8c2843d` U16, U16b et U17, `fe69758b` U03, UFC `f8c2843d` U18, Naruto `fdb79549` U01) ;
- le détecteur a annoncé la fin ailleurs que là où l'évaluation l'attend, mais à un endroit où le compteur ferme
  quand même la bonne partie : sur une capture entre la dernière capture de jeu et la preuve, ou au début de la
  partie suivante (EA FC `11029423` U08 pour les deux modèles ; U17, `f8c2843d` U31, UFC `11029423` U01, Dragon
  Ball `fdb79549` U04 et MK1 U53 pour le GRU).

J'ajoute un cas où le règlement compte une partie que je ne facturerais pas : MK1 `f0067594` U54, un combat de 17 s
coupé par une deuxième déconnexion de manette.

| | Fins manquées | Avec un coût réel |
|---|---:|---:|
| Manquées par le gradient boosting | 164 | 147 |
| Manquées par le GRU | 180 | 159 |
| Manquées par les deux | 133 | 113 |
| Au moins un des deux (les 211 cas) | 211 | 193 |

Le contrôle tient : le rejeu du compteur avec le gradient boosting au budget 1 perd 155 parties sur 296
(`docs/counting/README.md`), et je trouve 147 fins ratées qui coûtent une partie. L'écart vient des fins qui se
suivent et des fausses fins qui en compensent d'autres. Autrement dit, presque toutes ces fins ratées sont de
l'argent perdu : 18 seulement sur 211 ne coûtent rien.

Répartition par cause, selon mon codage (coût réel en parties perdues) :

| Cause principale | Cas | Gradient boosting | GRU | Les deux |
|---|---:|---:|---:|---:|
| REPRISE | 40 | 19 | 37 | 18 |
| SEUIL | 33 | 23 | 15 | 9 |
| LECTURE_COUPEE | 31 | 26 | 27 | 24 |
| ABANDON | 28 | 21 | 17 | 15 |
| ECRAN_NON_MARQUE | 18 | 16 | 16 | 14 |
| SIGNE_PROPRE_AU_JEU | 17 | 17 | 15 | 15 |
| JEU_RARE | 10 | 0 | 10 | 0 |
| ERREUR_OBSERVATION | 5 | 4 | 4 | 3 |
| CONTEXTE_SANS_VARIATION | 4 | 4 | 4 | 4 |
| ETIQUETTE_DOUTEUSE | 4 | 2 | 2 | 2 |
| ANNONCE_EN_AVANCE | 4 | 4 | 0 | 0 |
| CIBLE_INCOHERENTE | 3 | 2 | 3 | 2 |
| FIN_NON_CAPTUREE | 3 | 3 | 3 | 3 |
| autres (8 codes) | 11 | 6 | 6 | 4 |

Par jeu, avec le gradient boosting en service, les parties perdues sont surtout des matchs d'EA FC (39), de Mortal
Kombat 1 (34), de Tekken 8 (20) et de Beach Buggy Racing 2 (17). Avec le GRU, Mortal Kombat 1 passe en tête (44).

Bilan : 178 accords, 32 accords partiels, 1 désaccord. Les analystes ont fait un travail solide et vérifié ; mes
réserves portent sur le placement de deux fins, sur l'usage de SEUIL comme cause, sur l'élargissement de la
tolérance et sur ce qui coûte ou ne coûte pas.

Codes que j'ajoute : `CIBLE_INCOHERENTE` (le même signe visuel est étiqueté fin dans une session et non-fin dans une
autre, ce qui aplatit les probabilités) et `MANETTE_DECONNECTEE` (partie interrompue par la boîte « reconnecter la
manette »). Je reprends les codes des analystes `ASYMETRIE_COTES`, `MEMOIRE_GRU`, `RETARD`, `FIN_NON_CAPTUREE`,
`FINS_CONSECUTIVES`, `DEBUT_DE_SESSION`, et je range `AVANCE` et `ANNONCE_PRECOCE` sous `ANNONCE_EN_AVANCE`, qui
désignent la même chose.

## (a) Où je conteste les analystes

### Une fin posée sur un nul au coup de sifflet

EA FC `11029423` U07 est mon seul désaccord. À 2–2 à 90:57, la fin est posée sur la pause figée à 90:00 (200). Or la
capture 203, que j'ai ouverte, montre l'écran qu'EA FC propose après un nul : « Classique / But en or / Tirs au but /
Finir sur un match nul », avec « Classique » en surbrillance. Si les joueurs choisissent Classique ou But en or, la
prolongation se joue dans le même match. La première capture qui prouve la fin est le nouveau match à 0–0 (204).

Pour la facture, la place ne change rien. Pour l'apprentissage, c'est dangereux : une étiquette sur 200 apprend
« pause à 90:00 après un nul = fin ». Cette salle joue souvent la prolongation (`11029423` U11 à 97:35, U12 à 115:20,
`7616a3a5` U11 à 120:44). Un détecteur qui coupe avant la prolongation fait payer la prolongation comme une partie de
plus, le pire cas du projet. Même réserve, plus légère, pour `f0067594` U31 : à 4–4 en finale, le menu « Finale UCL »
avec « Reprendre » précède la prolongation, et seule la sélection d'équipes de 329 prouve la fin. Je propose deux
traces : U07 sur 204, U31 sur 329.

### SEUIL n'est pas une cause

Toute fin manquée a, par définition, une probabilité sous le seuil. Le code n'apprend quelque chose que quand le
signal est clair et que le seuil est absurde (0,985 pour 0,987 sur « VAINQUEUR — Joueur 2 » dans `42dcc5f5` U02,
0,988 pour 0,994 sur « 3e place » dans Warzone `7616a3a5` U03). Quand le modèle plafonne à 0,4 ou 0,7, la cause est
ailleurs. J'ai recodé une quinzaine de cas : en ABANDON quand le client quitte vers un autre jeu ou un autre combat
(`11029423` U12, U21, `42dcc5f5` U05, MK1 U45, UFC U24, Demon Slayer U01, Dragon Ball `020621e7` U01 et `fe69758b`
U03, Fortnite `27921669` U01), en FIN_NON_CAPTUREE (Fortnite `ff1c7245` U04), en DEBUT_DE_SESSION ou en
SIGNE_PROPRE_AU_JEU (Naruto `fdb79549` U01 et U02), en JEU_RARE pour le GRU devant une course qu'il n'a jamais vue
(Beach Buggy Racing 2 U10).

### Les deux manches de Mortal Kombat 1

Pour `8e58b139` U09, `f0067594` U09 et U19, les analystes parlent de seuil. Deux marqueurs allumés et le perdant à
0,00, c'est le match fini, aucun joueur n'en doute. Mais la même image porte la fin dans `f0067594` et pas dans
`8e58b139` : l'entraînement voit des cibles opposées sur le même signe, et les probabilités restent tièdes. Le lot 1
l'a bien vu dans sa synthèse ; je le mets en cause principale (`CIBLE_INCOHERENTE`). Même chose pour Tekken U25 : même
posée sur le K.O. de 154, la fin restait à 0,93 pour 0,97. Ce n'est pas l'étiquette qui manque, c'est une variable
« un côté a atteint le nombre de manches ».

### Élargir la tolérance vers l'avant

Les lots 3, 4, 7 et 8 proposent d'accepter une annonce faite avant la preuve. Pour le compte, ils ont raison : dans
EA FC `11029423` U17, `f8c2843d` U31, UFC U01 et Dragon Ball `fdb79549` U04, le GRU ferme la bonne partie. Mais
regardons sur quoi il réagit : un écran « Équipe » d'EA FC, une fenêtre réseau de la PS5, une transition. Les joueurs
ouvrent l'écran Équipe en plein match pour changer de tactique ou faire un remplacement, surtout à la mi-temps, et
les fenêtres de la console (notification, manette, réseau) arrivent à tout moment. Un détecteur récompensé pour avoir
tiré sur ces écrans finira par tirer en plein match. Je préfère juger le détecteur au niveau du compte, comme le fait
déjà `playend.counting.predicted`, que d'élargir la tolérance.

### Les fins qui ne coûtent rien

Les analystes traitent les 211 cas comme des échecs du même poids. Pour la salle, 18 ne coûtent rien (liste plus
haut). Ce sont souvent des relances quittées aussitôt (Tekken U23, Dragon Ball U16b), un essai d'UFC de 56 s sous le
seuil de 60 s (`f8c2843d` U18), ou la dernière partie avant le départ du client. Elles ne méritent pas d'effort de
modèle : le seuil de relance rapide et le départ du client les règlent déjà.

### La manette qui lâche

MK1 `f0067594` U53 et U54 : les analystes y voient une lecture coupée et une étiquette en retard, à juste titre.
Mais le fait de terrain, c'est la manette déconnectée. Le plus souvent, c'est le matériel de la salle (pile vide,
câble usé). Un gérant ne fait pas payer le combat coupé que les joueurs recommencent, sinon il s'expose à la
contestation. Le règlement actuel compte ces parties ; je propose que le compteur les signale à l'opérateur au lieu de
trancher seul. Ce serait une règle nouvelle, à décider par l'auteur.

## (b) Ce que mon métier voit et que les analyses ne disent pas

### Les clients relancent quand ils vont perdre

Sur les 211 cas, je compte 40 reprises directes, et une bonne part des 31 lectures coupées sont les mêmes reprises
passées par une pause. Les captures montrent toujours le même moment : le joueur mené d'une manche, avec peu de vie
(« FATAL BLOW » disponible, donc moins de 30 % de vie, dans MK1 U38, U39, U44), ou mené de deux buts à dix minutes de la
fin (EA FC 4–2 à 79:59, 0–3 à 35:08, 2–7 à 57:28), met en pause et choisit « Recommencer ». En UFC, c'est juste après
un knockdown (`f8c2843d` U20, U23) ; en Dragon Ball, « Réessayer » deux fois de suite sur le même combat (`fe69758b`
U07, U08). Dans les salles où le perdant paie le match, la relance avant le K.O. est la façon de ne pas payer. Si le
compteur ne la voit pas, les habitués l'apprennent en une semaine. C'est le premier trou à boucher.

La règle du 2026-09-29 (une partie recommencée compte comme une partie complète) est donc la bonne. Le problème est
qu'elle ne sert à rien si la relance passe sous les détecteurs, et c'est le cas dès qu'une pause s'intercale, donc
presque toujours.

### Le gagnant reste, le challenger paie

Le compteur « WIN / WINS n » de Tekken suit la manette, pas le personnage (lot 5). C'est le tableau du « roi de la
manette » : le gagnant garde sa place, le challenger change et paie son match. Chaque changement de ce compteur (il
monte, ou il passe de l'autre côté) est un match fini qu'aucun client ne peut contester. EA FC a l'équivalent avec le
« Face-à-face » des écrans de coup d'envoi (« 1 victoire — 0 nul — 1 victoire », 4 / 0 / 3 dans `f8c2843d` U36) :
c'est la console qui compte les matchs finis entre deux profils. Ces compteurs ne voient pas les relances, mais ils
sont un témoin indépendant du compteur en cas de contestation. À vérifier sur d'autres sessions.

### Les invariants qu'un joueur connaît

Un joueur sait sans réfléchir qu'un score de football ne baisse jamais, que le chrono d'un match ne revient pas de la
91e à la 5e minute (EA FC `fdb79549` U08, le cas le plus net), que le chrono d'un round de MK1 ou d'UFC ne remonte pas
dans la même manche, qu'un « TOUR 1 » après un « TOUR 3 » est une autre course, que la bannière « ROUND 1 » ou
l'introduction avec le Kaméo n'existent qu'en début de match, que le « ∞ » de Dragon Ball réapparaît à chaque début de
combat. Les analyses montrent que presque tous ces signes sont soit jetés par le calcul (période inconnue, capture
intermédiaire), soit jamais vus à l'entraînement. Ce sont pourtant les signes les plus sûrs, ceux qui ne demandent
aucun apprentissage.

### Ce qu'il ne faut pas prendre pour une fin

Mon métier sert aussi à éviter les fausses fins, qui font payer le client. Quatre pièges ressortent des captures :
la prolongation et les tirs au but font partie du match (EA FC U07, U13, `f0067594` U31) ; « X GAGNE » seul annonce
une manche dans MK1, pas le match (U57) ; la bannière « K.O. » d'une simple manche de Tekken a été notée comme un
résultat et fait monter le gradient boosting à 0,86 en plein match (U31) ; un passage par l'accueil de la PS5 suivi
d'un retour en jeu n'est pas une sortie (Fortnite `a4e41f30` capture 86, Dragon Ball `fdb79549` capture 46).

### Le rythme des captures et la durée des écrans de fin

Un écran visible d secondes est capturé avec une probabilité d'environ d/T quand les captures tombent toutes les T
secondes. Avec T = 28 s en moyenne, un bandeau « FIN DU MATCH » ou un écran « KITANA GAGNE » de quelques secondes est
capturé une fois sur quatre ou cinq. C'est pour cela que 14 courses sur 27 ne se voient qu'au départ de la course suivante, et
que la plupart des fins de combat se prouvent par le match suivant. Or la boucle de l'élève sur le Pi lit une capture
de jeu en 2,3 s en médiane (`docs/student/RESULTATS.md`, § 7). Capturer toutes les 5 à 10 s en jeu ferait voir la
plupart de ces écrans. Les détecteurs actuels sont entraînés au rythme de 28 s ; changer de rythme demande de
nouvelles captures et un nouvel entraînement, donc l'accord de l'auteur.

### Les comportements qui doivent guider le compteur

- Les longues pauses sont normales en salle : on regarde la liste des coups, on paie, on change de manette, on se
  dispute. MK1 `f0067594` reste cinq minutes sur la liste des coups (142 à 152), après quoi le GRU ne réagit plus à
  rien pendant trente captures (U22 à U24). Un compteur qui s'endort après une pause rate justement les relances, qui
  suivent une pause.
- Le changement de jeu clôt la partie, sans discussion. 16 fins manquées sont suivies d'un autre titre (MK1 vers
  Genshin Impact, Fortnite ou EA FC, UFC vers EA FC, EA FC vers MK1 ou Beach Buggy Racing 2, Tekken vers Warzone, Demon Slayer vers Dragon Ball
  FighterZ…). Le compteur lui-même peut fermer la partie ouverte au premier titre différent lu ou au passage d'un jeu
  facturé au temps, sans attendre le détecteur.
- L'extinction de la console (EA FC `fdb79549` U09, après dix captures de pause à la mi-temps) n'est pas un client qui
  change de jeu : c'est la fin de la session, une fermeture, ou une coupure de courant annoncée. Dans ce dernier cas, un
  gérant ne facture d'habitude pas le match coupé. Le compteur doit fermer la partie et signaler la ligne.
- Le changement d'utilisateur de la PS5 (MK1 U65) et le passage par les paramètres de la manette (EA FC `f8c2843d`
  U35, U37) annoncent souvent un autre client. C'est utile à l'opérateur pour séparer les comptes.
- En battle royale, la partie la plus courante est la plus courte : on meurt, on relance. Une sortie à 99 ou 87
  joueurs restants (Fortnite `27921669` U01, `ff1c7245` U03) est une partie facturable, et un modèle qui a appris
  « une fin a peu de joueurs restants » se trompe sur la caisse. Il n'y a pas de « recommencer » en battle royale :
  tout retour au salon du même jeu ferme la partie.
- Le réglage du jeu compte autant que le compteur. Un combat de Dragon Ball Sparking! ZERO en chrono infini dure
  25 minutes (`f8c2843d` U17, 1 519 s), le prix de deux matchs d'EA FC pour une partie. Les salles qui facturent à la
  partie imposent un chrono et une durée de mi-temps ; cela rend aussi les durées prévisibles pour le garde-fou décrit
  plus bas.
- Le biais de côté du gradient boosting (MK1 U38 trouvé à 0,981, U39 identique mais côté gauche à 0,289) n'est pas
  qu'un défaut technique : les deux joueurs paient pareil, et un compteur qui compte les relances d'un côté et pas de
  l'autre finit par se remarquer.
- La preuve doit rester. Quand un client conteste, je lui montre l'écran « VAINQUEUR », « VOTRE PLACE : #7 » ou le
  dialogue « Voulez-vous quitter ? — Oui, quitter » (EA FC `f8c2843d` U37). Le compteur devrait garder, pour chaque
  partie comptée, la capture qui prouve sa fin.

## (c) Méthode par famille, pourquoi, et ce qu'elle coûte

Je donne pour chaque famille le coût réel mesuré plus haut (gradient boosting / GRU), la méthode, et ce qu'elle
demande.

**Reprises et lectures coupées (71 cas ; 45 parties perdues avec le gradient boosting, 64 avec le GRU).** Comparer le
score, le chrono de match ou de round, le tour, les compteurs et les participants à la dernière observation lisible du
même jeu, en enjambant noir, pause, cinématique et bannière ; en tirer des variables d'invariant rompu : le score
baisse, le chrono recule (football, même avec une période inconnue), le chrono de round remonte, le tour diminue,
« ROUND 1 » ou « ∞ » réapparaît. Les mêmes invariants servent de règles écrites, combinées au détecteur par un « ou ».
Pourquoi : c'est le geste de triche principal des clients, et ces signes n'ont pas besoin d'être appris. Coût : du code
dans `src/playend/contract/temporal.py` et `src/playend/training/baselines.py`, puis une nouvelle évaluation, à faire
avec l'accord de l'auteur. Risque : une seule valeur mal lue (une minute de but prise pour le chrono) crée une fausse
fin ; il faut un second indice (score et chrono ensemble, ou deux captures de suite), et mesurer les parties en trop
sur tout PlayEnd avant de garder la règle.

**Abandons et changements de jeu (28 cas ; 21 / 17).** Fermer la partie ouverte, dans le compteur, au premier titre
différent lu, au passage à un jeu au temps, à l'extinction de la console ; pour le battle royale, au retour au salon
ou au chargement du même jeu. Pourquoi : aucun client ne conteste qu'il a fini une partie quand il change de jeu. Coût :
quelques lignes dans `src/playend/counting/`, sans réentraînement. Risque : un titre mal lu (UFC `11029423` U02 montre
l'erreur inverse) ; exiger deux captures du nouveau titre ou l'écran de lancement de la console.

**Écrans de fin non marqués et erreurs de lecture (23 cas ; 20 / 20).** Conventions et traces : le menu d'après-match
d'EA FC à encart « 90:00 A x-y B », l'écran « Revanche » de Tekken, le classement cumulé de Beach Buggy Racing 2
(« Suivant : ÉVÉNEMENT n »), qui prouve la fin d'une course depuis la règle du 2026-10-04, le résumé avec la place
dans Warzone, l'escouade éliminée dans Fortnite ; corriger `f0067594` capture 254 (bandeau « FIN DU MATCH » perdu par
une erreur de saisie) et les écrans d'équipe lus comme noirs dans `f8c2843d`. Ajouter dans le compteur une fermeture
sur « résultat affiché avec un vainqueur ou une place ». Pourquoi : un écran de victoire bien noté et rejeté (Dragon
Ball FighterZ U03, raté par les quatre détecteurs) suffit à décrédibiliser le compteur devant un client. Coût : temps
d'annotation pour les traces, puis régénération des étiquettes. Risque : le lot 6 mesure 6 passages du jeu à un écran
de résultat hors d'une fin sur tout PlayEnd, contre 40 sur une fin : il faut regarder ces 6 avant de fermer sans seuil.

**Signes propres au jeu (17 cas ; 17 / 15).** Variables génériques : « le compteur de séries change de valeur ou de
côté », « la progression revient en arrière », « un côté atteint le nombre de manches », et une étiquette unifiée pour
la capture où le dernier marqueur s'allume. Pourquoi : ce sont les signes du « gagnant reste » et des manches, que tout
joueur lit. Coût : du code, et surtout des sessions de Tekken et de Beach Buggy Racing 2 en plus : avec un seul
enregistrement, chaque tour d'évaluation se fait sans aucun exemple du jeu.

**Seuils (33 cas ; 23 / 15).** Décider le budget au niveau du compte. Le rejeu le montre : au budget 5, le gradient
boosting ne fait payer que 0,7 partie de trop pour 100 et en perd 34,5 au lieu de 52,4. Pour un gérant, perdre une
partie sur trois reste trop, mais environ une partie de trop pour 150, avec la capture de preuve à montrer, se règle au
comptoir. Coût : aucun calcul nouveau, une décision de l'auteur. Un plancher de seuil vers 0,95 éviterait les tours où
le seuil à 0,99 éteint le détecteur.

**Jeux rares et mémoire du GRU (12 cas ; 0 / 12).** Le GRU perd seul ces parties : Beach Buggy Racing 2 en entier,
les longues pauses de MK1. Des pauses longues à l'entraînement et l'échange des côtés A et B corrigeraient une partie
du problème. En attendant, le gradient boosting avec les règles est le meilleur choix pour la salle : il perd 147
parties sur ces cas, le GRU 159.

**Fins tombées entre deux captures (4 cas, et toutes les fins prouvées par la partie suivante).** Capturer plus
souvent en jeu, ou en rafale quand le match approche de sa fin (balle de match en combat, 85e minute en football,
moins de dix joueurs en battle royale). Coût : nouvelles captures et nouvel entraînement, donc une nouvelle phase.

**Artefacts de l'évaluation (annonces en avance, retard, fins consécutives, dernière partie).** Rien à corriger dans
les modèles : juger au niveau du compte. Coût nul.

**Garde-fou de durée, pour toutes les familles.** Une fin manquée laisse une trace que le compteur peut voir seul :
une partie anormalement longue. D'après `units.csv`, une partie de MK1 dépasse rarement 212 s en jeu (90e centile,
maximum 534 s), Tekken et Beach Buggy Racing 2 ne dépassent jamais 222 s et 196 s, et un match d'EA FC dépasse
rarement 16 minutes (964 s au 90e centile). Une ligne de MK1 à 15 minutes de jeu actif cache presque sûrement plusieurs matchs. Le compteur peut la
signaler à l'opérateur avec une estimation du nombre de matchs. Il faut compter le temps de jeu actif, pas le temps
écoulé : le match d'EA FC `7616a3a5` U11 reste quarante minutes figé sur « CHOIX DES TIREURS DE PÉNALTY ». Coût :
quelques lignes, aucun réentraînement ; c'est une alerte, pas une facture.

## (d) Mes trois priorités pour l'auteur

1. **Voir les relances.** Comparer chaque valeur à la dernière observation lisible du même jeu et en tirer les
   invariants que connaît un joueur (score qui baisse, chrono qui recule ou remonte, tour qui diminue, série qui
   change, « ROUND 1 » ou « ∞ » qui revient), en variables pour les modèles et en règles combinées au détecteur. C'est
   la plus grosse perte (71 cas de reprises et de lectures coupées, 45 parties perdues avec le gradient boosting) et le
   comportement de triche principal des clients. À mesurer sur les parties en trop avant de la garder.
2. **Fermer sans seuil ce qui ne se discute pas, et garder la preuve.** Dans le compteur : changement de titre,
   passage au temps, extinction de la console, résultat affiché avec un vainqueur ou une place, retour au salon en
   battle royale ; une capture de preuve gardée pour chaque partie ; le garde-fou de durée qui signale les lignes trop
   longues ; le budget décidé au niveau du compte. Rien de tout cela ne demande de réentraîner, et c'est ce qui rend le
   compteur défendable au comptoir.
3. **Corriger ce qui apprend le contraire.** Par des traces : les fins posées avant une prolongation possible
   (`11029423` U07 sur 204, `f0067594` U31 sur 329), la frontière manquante de `f0067594` vers 418, la fin de U54 sur
   549, une place unique pour la capture où le dernier marqueur s'allume, le « K.O. » de manche de Tekken qui n'est pas
   un résultat, les titres et noms d'équipes d'EA FC écrits d'une seule façon. Puis, avec l'accord de l'auteur, des
   sessions de plus pour Tekken, Beach Buggy Racing 2 et MK1 hors de `f0067594`, si possible capturées à un rythme plus
   serré en jeu.

## Fichiers et sources

- Mes lignes : `analyses/revue_terrain.jsonl` (211 cas).
- Règles de comptage et compteur : `docs/decisions/regles-de-comptage.md`, `docs/decisions/regles_facturation.json`,
  `docs/counting/README.md`.
- Durées des parties : `build/playend_v1.0/data/units.csv` et `observations.csv`.
- Temps de lecture sur le Pi : `docs/student/RESULTATS.md`, § 7.
- Images vérifiées : `data/captures/session_f0067594…/images/bloc_0000/frame_00000415.jpg` à `…421.jpg` (marqueurs
  de manche), `data/captures/session_11029423…/images/bloc_0000/frame_00000203.jpg` (départage d'un nul).
- Aucune source en ligne.
