# Plan : compter les parties à leur début (proposition du 12 octobre 2026)

Proposition soumise à l'auteur, qui l'a demandée : le système ne doit pas signaler la fin d'une partie mais son
**début**, confirmé par plusieurs captures, et ne lire que les captures qui portent une information. Rien n'est encore
fait : chaque étape demande son accord. Les mesures citées se refont avec les scripts de `plan_debut_2026-10-12/`, sur
les observations du professeur de PlayEnd (`build/playend_v1.0/`).

## 1. Pourquoi changer d'unité

Depuis le début, le détecteur cherche la **fin** d'une partie : un événement bref, qui tombe le plus souvent entre deux
captures (une toutes les 28 s), et dont l'écran ne reste que quelques secondes. L'analyse cas par cas des 211 fins
manquées (`docs/training/FINS_MANQUEES_CAS_PAR_CAS_2026-10-12.md`) le montre : la plupart des fins se prouvent par ce
qui vient après, c'est-à-dire par le début de la partie suivante, que le détecteur ne regarde qu'à travers une
variation calculée contre la capture d'avant.

Le **début** d'une partie a les propriétés inverses :

- **il dure.** Le score reste à 0–0, le chrono dans sa zone de départ, le premier tour ou la première manche pendant
  plusieurs captures : 2 à 2,5 lectures de début de suite en médiane (EA FC, Mortal Kombat 1, Tekken 8, Beach Buggy
  Racing 2), 11 pour Fortnite ;
- **il se voit presque toujours.** Sur la première capture de jeu lisible de chaque partie, les valeurs de départ sont
  visibles pour 75 parties d'EA FC sur 80, 71 de Mortal Kombat 1 sur 77, 29 de Tekken 8 sur 31, 28 de Fortnite sur 28,
  26 de Beach Buggy Racing 2 sur 27, 7 de Naruto sur 8 ;
- **il se confirme.** Plusieurs captures de suite le montrent, ce qui permet de l'exiger deux fois, comme le faisait le
  compteur de 2025 ;
- **c'est le moment où l'on compte.** Une partie commence ; elle est facturée dès qu'elle a duré plus que le seuil de
  relance rapide (60 s, 15 s en combat). La fin ne sert plus qu'à fermer la partie et à arrêter le temps.

Le compteur de football de 2025 (Mayano et al., 2025 ; dépôt `Compteur-intelligent-updated`, `match_tracker.py`)
fonctionnait déjà ainsi. Il était « minutes d'abord » : il n'acceptait que des minutes lues au format `mm:ss`, jetait
les lectures ambiguës, confirmait un match à froid après 3 lectures cohérentes de début, et n'ouvrait un nouveau match
que si 3 nouvelles minutes cohérentes étaient toutes plus basses que les 3 anciennes. Une lecture manquante n'y était
pas une rupture : seule une vraie perte du signal vidéo l'était. C'est un détecteur de **débuts** confirmé par **k
lectures sur n**, le principe de l'intégration binaire des radars (une détection est déclarée quand M tests sur N
dépassent le seuil [1]).

## 2. Ce que les mesures montrent déjà

Une simulation par règles, sans aucun entraînement (`plan_debut_2026-10-12/simulate.py`), lit les 25 enregistrements
capture par capture et compte un début quand les valeurs de départ reviennent après que la partie avait avancé (ou
après un changement de jeu, ou après un écran hors jeu), confirmé par une seconde lecture. Elle ne lit que les captures
porteuses et compare à la dernière valeur lisible.

| | Parties trouvées | Fausses annonces pour 100 parties |
|---|---:|---:|
| Débuts, règles simples, vrais modes de facturation | 274 sur 302 (90,7 %) | 2,0 |
| Débuts, règles simples, toutes les captures | 274 sur 302 (90,7 %) | 2,6 |
| Fins, gradient boosting du 6 octobre (rappel) | 42,5 % des fins | 1,4 |

Sur les 211 fins manquées par le gradient boosting ou le GRU, 203 sont suivies d'une autre partie ; le compteur de
débuts trouve le début de cette partie suivante dans **185 cas**, quelle que soit la cause de l'échec : 37 reprises
sur 40, 31 lectures coupées sur 34, 39 fins rejetées par le seuil sur 50, 18 écrans de fin non marqués sur 20, 13
signes propres à un jeu sur 15, 12 abandons sur 14, les 9 jeux rares.

**Réserves.** Ces règles ont été écrites en regardant ces mêmes données, et elles lisent les observations du
professeur, pas celles de l'élève : c'est une borne haute, qu'il faut confirmer sur des enregistrements tenus à
l'écart et sur les lectures de l'élève.

Les 28 débuts manqués viennent surtout de trois causes (les autres sont des jeux sans score lisible, comme
Dragon Ball FighterZ et Brawlhalla, ou un mode d'UFC particulier) :
- des parties très courtes (23 à 106 s) dont aucune lecture de départ n'est capturée ;
- un nouveau match déjà lu à 0–1 sur sa première capture : il faut aussi la règle « le score a baissé depuis la dernière
  lecture », pas seulement « le score est à zéro » ;
- Dragon Ball Sparking! ZERO (8 sur 21), dont la signature de début est faible dans les observations actuelles.

## 3. Ne lire que les captures porteuses

Le détecteur reçoit aujourd'hui toutes les captures, y compris celles qui ne disent rien : 1 179 sur 8 871 n'ont
aucune valeur déterminante (jeu sans tableau de score, ralenti, gros plan, écran noir), et 3 374 répètent exactement
l'observation précédente (pause, menu, liste des coups). Ce sont elles qui endorment le GRU et qui cassent les
variations. Une capture est **porteuse** si elle a au moins une valeur déterminante lisible (score, chrono, période,
tour, place, compteur de fin, résultat affiché) ou un état décisif (écran de résultat, menu, chargement, sélection,
avant-partie ou après-partie). En ne gardant que les captures porteuses, et une seule capture par suite identique (avec
sa durée), la suite que lit le détecteur passe de 8 871 à 4 756 captures.

Les captures non porteuses ne disparaissent pas : elles comptent toujours pour le temps (facturation au temps, temps
de jeu d'une partie) et pour l'âge de la dernière lecture. C'est la même idée que GRU-D, qui donne au réseau la
dernière valeur observée et le temps écoulé depuis, plutôt qu'une valeur manquante [2], et que les Skip RNN, qui ne
mettent pas à jour l'état sur une entrée sans nouveauté [3].

## 4. La chaîne proposée

```text
capture ──> lecteur (élève) ──> filtre des captures porteuses ──> état de la partie ──> détecteur de débuts ──> compteur
                                   │ (non porteuses : temps seulement)    (dernière valeur      (règles sûres     (compte les débuts confirmés,
                                   v                                       lisible, âge,         + modèle appris,   ferme sur sortie ou nouveau
                                temps de jeu et facturation au temps       invariants)           fin en appui)      début, garde les preuves)
```

**État de la partie.** Pour chaque grandeur, la dernière valeur lisible du même jeu et son âge ; l'identité du jeu
normalisée (famille de jeu, table d'alias des équipes) pour que « EA Sports FC » et « FC 27 », « PSG » et « Paris SG »
ne rompent plus le contexte ; des grandeurs communes à tous les jeux :
- **avancement**, qui ne fait que monter pendant une partie : score total, manches gagnées, tour, numéro de période,
  chrono de match (montant au football, descendant dans un round), joueurs éliminés en battle royale, vies perdues ;
- **signature de début**, vraie quand les valeurs sont celles du départ : score 0–0, chrono dans sa zone de départ,
  première manche, tour 1, joueurs ou vies au maximum, « ∞ » ou bannière « ROUND 1 » quand ils marquent un départ ;
- **invariant rompu** : une grandeur d'avancement a reculé depuis sa dernière valeur lisible (score qui baisse, tour
  qui revient à 1, joueurs restants qui remontent, chrono de match qui recule, compteur de séries qui change de valeur
  ou de côté) ;
- **indices de sortie** depuis la dernière lecture de jeu : écran de résultat, après-partie, menu, salon, sélection,
  accueil de la console, changement de jeu.

La signature de début et les grandeurs d'avancement viennent d'un **profil par jeu** (tiré des parties de PlayEnd :
valeurs de la première capture de chaque partie contre les suivantes) ; un jeu sans profil retombe sur les invariants
communs, qui ne demandent aucun apprentissage.

**Détecteur de débuts, en deux couches.**
1. **Règles sûres**, sans seuil appris, qui suffisent pour la plupart des parties : un début est confirmé quand la
   signature de début est lue deux fois parmi les trois captures porteuses suivantes et que le contexte dit que c'est
   une nouvelle partie (la partie ouverte avait avancé, ou le jeu a changé, ou un indice de sortie est apparu, ou un
   invariant est rompu). C'est la règle de 2025 étendue à tous les jeux et à toutes les grandeurs.
2. **Un modèle appris** pour les cas que les règles laissent ouverts : il donne, sur chaque capture porteuse, une
   probabilité de début et une probabilité de fin, comme BSN estime séparément le début et la fin d'une action [4]. La
   fin sert d'**appui** : un pic de fin suivi d'un pic de début dans une courte fenêtre donne la confirmation la plus
   forte ; un début seul suffit pour une reprise sans écran de fin ; une fin seule ferme la partie quand le client
   s'en va. L'étiquette est étalée sur les premières captures de la partie plutôt que posée sur une seule ligne,
   comme la perte sensible au contexte de Cioppa et al. pour repérer des actions [5]. On commence par le gradient
   boosting, rapide à entraîner sur le PC de l'auteur, sur les variables portées ; le GRU ne revient que s'il fait
   mieux, en n'avançant que sur les captures porteuses.

**Compteur.** Il compte les débuts confirmés ; une partie se ferme au début suivant, à un indice de sortie ou au
départ du client. La règle de relance rapide s'applique au temps de jeu entre le début et la fermeture. Les fermetures
qui ne se discutent pas (changement de jeu, passage à un jeu facturé au temps, extinction de la console, retour au
salon d'un battle royale) se font sans seuil. Pour chaque partie, le compteur garde la capture qui prouve son début et
celle qui prouve sa fin, pour répondre à un client qui conteste. Une partie dont le temps de jeu dépasse nettement la
durée habituelle de son jeu est signalée à l'opérateur, comme une durée attendue dans un modèle semi-markovien [6].

## 5. Les étiquettes et la mesure

- **Une étiquette de début** par partie : la première capture de jeu de la nouvelle partie dont le HUD est lisible
  (règle validée par l'auteur le 2026-10-13), tirée des `units.json` existants et vérifiée par l'auteur. Sur les 302
  parties, une seule n'avait aucun HUD lu (Brawlhalla `da79d420`, captures 10 à 14), et l'image montre bien les vies
  (3 et 3, puis 2 et 1) : une erreur du professeur, à corriger par une trace.
- **Réparer d'abord la vérité terrain**, avec la validation de l'auteur (règle 7) : la capture qui porte la fin d'un
  combat, posée de deux façons ; les 8 fins décalées d'une capture ; le match recommencé de `f0067594` vers la capture
  418 ; le nul suivi d'une prolongation possible (`11029423` U07) ; la capture 254 et les fausses captures noires de
  `f8c2843d`, par des traces. Fait le 2026-10-13 pour les frontières : 17 décisions de l'auteur
  (`data/validation/corrections_2026-10-13/`), étiquettes de 7 sessions promues à nouveau. Fait aussi le 2026-10-13 :
  19 corrections d'observation (8 traces), 15 conventions écrites et appliquées (12 traces), débuts placés par
  `playend.boundaries.starts` dans les 25 `units.json` et étiquetés (`unit_start_boundary`) ; 25 débuts vérifiés par
  l'auteur (`data/validation/debuts_2026-10-13` : 19 acceptés, 6 corrigés).
- **Mesurer au niveau du compte** : nombre de parties comptées par enregistrement comparé à la référence (compte exact,
  à une près, parties en trop et manquées pour 100), puis débuts trouvés et fausses annonces avec une marge dans les
  deux sens et un appariement un à un [7]. Le seuil, s'il en reste un, se choisit sur des prédictions hors pli de
  modèles construits comme le modèle final.
- **Tenir un jeu entier à l'écart** en plus d'un enregistrement, pour mesurer ce qui arrive face à un jeu nouveau [8].

## 6. Viser près de 100 %, et ce qui l'empêche

L'objectif demandé est un compte juste presque toujours : précision et rappel proches de 100 %. Sur les observations
du professeur, les règles simples donnent déjà 90,7 % des parties pour 2 fausses annonces pour 100. Ce qui sépare de
100 % est connu :

| Obstacle | Ce qui le lève |
|---|---|
| Parties très courtes, sans lecture de départ capturée | capturer plus souvent en jeu (l'élève lit une capture de jeu en 2,3 s sur le Pi : une capture toutes les 5 à 10 s devient possible) ; ces parties sont souvent sous le seuil de relance rapide et ne seraient pas facturées |
| Début déjà avancé à la première lecture | invariant « avancement qui recule », pas seulement « valeur de départ » |
| Signatures faibles (Dragon Ball Sparking! ZERO, Brawlhalla) | profil du jeu (vies pleines, « ∞ », bannière de départ) et conventions d'annotation pour ces écrans |
| Erreurs d'étiquetage (3 % des cas étudiés) | réparation de la vérité terrain avant toute mesure |
| Erreurs de lecture de l'élève | confirmation par plusieurs lectures et par plusieurs grandeurs ; le VLM adapté par LoRA lit 91,7 % des champs comme le professeur |
| Jeux jamais vus | invariants communs à tous les jeux ; profil ajouté au premier enregistrement du jeu |

Un 100 % strict n'est pas garanti : une partie de 20 s entre deux captures ne laisse aucune trace. L'objectif
réaliste, à vérifier étape par étape, est un compte exact sur presque tous les enregistrements, avec moins d'une
partie comptée en trop pour 100, d'abord sur les observations du professeur, puis sur celles de l'élève.

## 7. Les étapes proposées, chacune sur accord de l'auteur

1. **Réparer la vérité terrain** (traces, validation des corrections par l'auteur, étiquettes de début).
2. **Construire le filtre, l'état de la partie et le compteur de débuts par règles** (`src/playend/counting/`,
   `src/playend/contract/temporal.py` en version 5), et les mesurer sans entraînement : sur le professeur, sur le
   paquet de l'élève, en tenant des enregistrements et des jeux à l'écart. Si les règles atteignent l'objectif, le
   modèle appris devient un complément. Fait le 2026-10-13 (`docs/counting/DEBUTS_2026-10-13.md`) : 96,4 % des parties
   trouvées pour 1,3 en trop sur 100 avec le professeur, 85,8 % pour 8,3 avec l'élève.
3. **Entraîner le détecteur de débuts** (gradient boosting d'abord, sur le PC de l'auteur) sur les variables portées,
   avec la fin en appui ; GRU seulement s'il apporte quelque chose. Méthodes à comparer, avec les règles de l'étape 2
   comme point de départ (décision de l'auteur du 2026-10-13) :
   - **gradient boosting sur les variables portées** : une probabilité de début, une de fin, la fin en appui ;
   - **estimation séparée du début et de la fin, à la manière de BSN** [4] : deux sorties, une pour chaque frontière,
     apprises ensemble ; seule l'idée est reprise, BSN lisant des descripteurs d'images et non des observations, et
     la génération de propositions « début → fin » n'étant pas nécessaire, puisque nos parties ne se chevauchent pas ;
   - **étiquette étalée sur les premières captures** de la partie, avec une perte sensible au contexte [5] ;
   - **GRU** sur les seules captures porteuses, s'il fait mieux ;
   - **réglage des seuils des règles** par validation croisée : le témoin qui dit si un modèle appris apporte plus que
     des règles mieux réglées.
4. **Rejouer le compteur** avec l'élève, puis faire tourner la boucle complète sur le Pi.
5. **Données** : enregistrements de plus pour les jeux rares, rythme de capture plus serré en jeu (le programme du Pi
   change : refaire son manifeste).

Ce changement touche le mémoire : le chapitre 2 décrit un détecteur de débuts, la section 3.2 garde les résultats du
détecteur de fins comme point de départ, et la discussion explique pourquoi l'unité a changé.

## Sources

1. Intégration binaire (« M-of-N ») : une détection est déclarée quand M tests sur N dépassent le seuil. MathWorks,
   documentation de `binaryintloss`, https://www.mathworks.com/help/radar/ref/binaryintloss.html ; présentation :
   https://rfessentials.com/resources/rf-glossary/binary-integration/
2. Che, Z. et al. (2018). *Recurrent Neural Networks for Multivariate Time Series with Missing Values*. Scientific
   Reports 8, 6085. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5904216/
3. Campos, V. et al. (2018). *Skip RNN: Learning to Skip State Updates in Recurrent Neural Networks*. ICLR.
   https://arxiv.org/abs/1708.06834
4. Lin, T. et al. (2018). *BSN: Boundary Sensitive Network for Temporal Action Proposal Generation*. ECCV.
   https://arxiv.org/abs/1806.02964
5. Cioppa, A. et al. (2020). *A Context-Aware Loss Function for Action Spotting in Soccer Videos*. CVPR.
   https://openaccess.thecvf.com/content_CVPR_2020/html/Cioppa_A_Context-Aware_Loss_Function_for_Action_Spotting_in_Soccer_Videos_CVPR_2020_paper.html
6. Yu, S.-Z. (2010). *Hidden semi-Markov models*. Artificial Intelligence 174(2), 215–243.
   https://www.cs.ubc.ca/~murphyk/Teaching/CS540-Spring10/projects/Yu-hsmm09.pdf
7. van den Burg, G. J. J., Williams, C. K. I. (2020). *An Evaluation of Change Point Detection Algorithms*.
   https://arxiv.org/abs/2003.06222
8. Gulrajani, I., Lopez-Paz, D. (2021). *In Search of Lost Domain Generalization*. ICLR. https://arxiv.org/abs/2007.01434
9. Mayano, B. D., Yan-Mol, L. L., Masakuna, J. F. (2025). *Intelligent Match Counter in a Video Game Arena*. IEEE
   Access 13, 32320–32328. doi:10.1109/ACCESS.2025.3542425
