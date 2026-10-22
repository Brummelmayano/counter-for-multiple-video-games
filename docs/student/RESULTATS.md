# L'élève : premiers résultats (7 au 10 octobre 2026)

Mesures faites sur ce PC avec le code de `src/playend/student/` (conception : `CONCEPTION.md`). Les images sont
celles de PlayEnd ; la référence est l'observation du professeur. Les fichiers produits sont dans `build/student/`
(non versionné). La nuit du 7 au 8 octobre, le Pi mesure le temps de l'élève OCR et le VLM avec grammaire sur 236
captures (`pi/nuit_2026-10-07.sh`).

## 1. Le lecteur OCR

PP-OCRv6 tiny, exécuté par notre propre code (ONNX Runtime, NumPy, Pillow), pour que le Pi et le PC lisent le même
texte. Sur les 26 mosaïques de la comparaison du 6 octobre, il donne le même texte que RapidOCR sur 15 et diffère d'un
caractère ou d'une boîte sur les autres. Il lit une mosaïque en 0,05 s sur ce PC.

Les mosaïques construites par `zones.py` sont identiques, pixel pour pixel, à celles qui ont été mesurées (26 sur 26).

## 2. Des champs lus, comparés au professeur

Sur toutes les images de jeu des 13 jeux qui ont des zones (4 960 images, jeu donné par le professeur), champ par
champ. Trois manières de lire ont été essayées, dans l'ordre :

1. détecter le texte des zones puis le ranger par position : 38,8 % des valeurs justes ;
2. lire directement des cadres fixes avec le seul modèle de reconnaissance, là où le HUD ne bouge pas ;
3. lire les marques (pastilles de manche, losanges, blocs de vie) à partir de leurs pixels, par une régression
   logistique par jeu.

La détection est le maillon faible : elle rate les petits chiffres. Le score d'EA FC, dans son tableau standard,
passe de 21 % à 95 % de valeurs justes quand on lit ses deux cadres directement (300 images tirées au hasard).

Résultat de l'élève OCR complet, sur les 10 674 valeurs de HUD du professeur (noms exclus) : **79,0 % justes, 2,8 %
fausses, 18,2 % manquées**. Ses erreurs sont surtout des absences, qui sont la forme d'erreur la moins risquée pour la
facturation.

| Valeur | Juste |
|---|---:|
| Chrono de Tekken 8 | 98 % |
| Chrono de Naruto, de J-Stars | 96 % |
| Chrono de Mortal Kombat 1 | 90 % (36 % par détection) |
| Chrono d'EA FC | 90 % |
| Manches de Mortal Kombat 1, Tekken 8, Naruto (marques) | 96 à 99 % |
| Vies de Dragon Ball Sparking! ZERO (marques) | 99 % |
| Tours de Beach Buggy Racing 2 | 91 % |
| Joueurs restants de Fortnite | 84 % |
| Joueurs et équipes restants de Warzone | 74 % et 69 % |
| Score d'EA FC, tous styles confondus | 65 % |

Les marques sont évaluées par blocs de temps : chaque image est prédite par un modèle qui n'a pas vu son bloc.

Limite : EA FC change de tableau de score selon la compétition (des centaines de styles). Les cadres fixes ne couvrent
que le tableau standard. Une lecture placée par rapport aux sigles des équipes a été essayée et rejetée : sur les
images où elle trouve les sigles, elle donne plus de scores faux (668) que justes (485), à cause des écussons lus comme
des chiffres. Le VLM, qui n'a pas besoin de cadres, est mesuré sur ce cas.

## 3. Le classifieur de jeu et d'écran

Caractéristiques figées de MobileNetV2 (les 1 000 scores ImageNet), réduites à 128 composantes principales, puis une
régression logistique ; les étiquettes du professeur servent seulement à l'entraîner.

| Évaluation | Juste |
|---|---:|
| Jeu, par blocs de temps | 86,7 % |
| Jeu, avec un vote sur les 5 dernières captures (possible en direct) | 90,7 % |
| Jeu, par session retirée | 78,2 % |
| Type d'écran, par blocs de temps | 85,5 % |
| Écran de jeu ou non | 94,5 % |

Face à un jeu jamais vu, il reste très sûr de lui (confiance médiane 0,97) : sa confiance ne permet pas de repérer un
jeu inconnu.

## 4. L'effet sur la détection des fins

Les détecteurs du calcul du 6 octobre sont rejoués sans réentraînement sur des paquets PlayEnd dont seules les
observations changent (`package.py`, `endings.py`). Le rejeu sur les observations du professeur redonne exactement
les résultats du calcul (GRU : 37,3 % des fins, 3,8 fausses fins pour 100 parties ; gradient boosting : 42,5 % et
1,4). Budget d'une fausse fin pour 100 parties, GRU :

| Observations lues par le GRU | Fins trouvées | Fausses fins pour 100 parties |
|---|---:|---:|
| Professeur (référence) | 37,3 % | 3,8 |
| Champs de l'élève, lus sans erreur | 39,3 % | 4,9 |
| Lectures réelles de l'élève OCR | 37,5 % | 4,4 |
| 10 % des valeurs du HUD vidées au hasard | 37,1 % | 4,5 |
| 30 % vidées | 36,0 % | 3,7 |
| 50 % vidées | 31,2 % | 3,4 |
| 80 % vidées | 27,0 % | 4,0 |

Les erreurs de lecture du HUD touchent peu la détection : même avec la moitié des valeurs vidées, le GRU garde
31 % des fins sans fausse fin de plus.

L'élève complet, en revanche, a d'abord fait chuter le GRU à 9,5 % des fins, avec 18,1 fausses fins pour 100 parties.
Il ne fournissait ni le mode de jeu, ni les bandeaux de résultat, ni les minuteurs secondaires, et il se trompait
d'écran une fois sur sept. Dans le calcul du 6 octobre, retirer le mode faisait perdre 10 points de rappel, les
minuteurs 8, les compteurs 7. Quatre corrections ont suivi, chacune mesurée par le même rejeu :

1. **Les conventions du professeur.** Hors du jeu, le professeur écrit un chrono invisible, des compteurs vides et
   une période « none » ; sur une image de jeu, il donne au jeu son genre, sa période, le type de score et le nombre
   de participants. L'élève reprend ces valeurs d'un profil par jeu, tiré des images de jeu du professeur (séparé
   selon que le chrono est infini ou non, comme les modes d'entraînement). Les bandeaux de résultat sont lus par l'OCR
   sur la capture entière, quand le classifieur ne voit pas un écran de jeu (`banners.py`) ; l'issue lue concorde
   avec celle du professeur sur 186 des 240 écrans de résultat.
2. **Un bandeau doit être sûr.** Un écran que le classifieur prend pour un résultat, sans aucun mot de résultat lu,
   n'est pas cru : ce sont surtout des erreurs du classifieur.
3. **Le maintien de l'écran.** Un passage isolé du jeu à un autre écran, ou l'inverse, est presque toujours une
   erreur du classifieur ; pour le GRU, il ressemble à une partie qui finit. L'élève ne suit ce passage que si la
   capture suivante le confirme, ou tout de suite si un bandeau de résultat est lu (`steady_screens`). Le retard est
   d'une capture au plus, et seules les captures passées servent, comme sur le Pi. Le nombre de changements d'écran
   tombe de 2 101 à 1 298 (le professeur en compte 1 602) ; le type d'écran juste passe de 85,5 % à 81,7 %, parce
   que chaque vrai changement attend une capture.
4. **Un bandeau est une ligne à lui seul.** Les faux résultats venaient de mots pris dans des phrases : « RATIO »
   dans « AMÉLIORATION » (176 écrans), « une couronne de victoire » dans le fil des éliminations de Fortnite,
   « Finir sur un match nul » dans les réglages d'EA FC, « VICTOIRES » dans les statistiques des menus. En exigeant
   un mot entier, et pour la victoire ou le match nul une ligne à elle seule, au singulier, les écrans hors jeu où
   l'élève voit un résultat que le professeur ne voit pas passent de 252 à 32, sans perdre un seul des 208 vrais.

| Élève complet, GRU entraîné sur le professeur, budget 1 | Fins trouvées | Fausses fins pour 100 parties | Précision |
|---|---:|---:|---:|
| Première version | 9,5 % | 18,1 | |
| Conventions, profils, bandeaux | 30,7 % | 28,1 | |
| Bandeaux sûrs, OCR de la capture entière | 34,1 % | 28,0 | 54,9 % |
| Maintien de l'écran | 33,0 % | 12,6 | 72,4 % |
| Bandeaux sur une ligne à eux (élève retenu) | 30,7 % | 9,6 | 76,1 % |

Avec l'élève retenu, le gradient boosting entraîné sur le professeur trouve 22,5 % des fins pour 6,0 fausses fins
(42,5 % et 1,4 sur les observations du professeur).

Les fausses fins qui restent (27,4 par graine sur les 25 sessions retirées) ont trois causes. Près de la moitié
(12,2) sont de vraies fins trouvées deux à six captures trop tard : l'évaluation tolère une capture de retard, et le
maintien de l'écran en consomme déjà une. L'évaluation compte chacune comme une fin ratée et une fausse fin ; le
rejeu du comptage avec les fins prédites dira ce que ces retards coûtent en parties facturées. Viennent ensuite les
erreurs d'écran qui durent deux captures ou plus (8,4), puis les sauts du score ou du chrono mal lus (2,6). Le remède connu est
de réentraîner les détecteurs sur les sorties de l'élève, pour qu'ils apprennent ses retards et ses erreurs : c'est
le calcul `gru` du kit de l'ami, fait avec cet élève.

Six observations sur 8 871 (variante « lecture ») et trois (variante « élève complet ») ne passaient pas le
validateur du contrat ; elles ont gardé l'observation du professeur.

## 5. Sur le Raspberry Pi : l'élève OCR et le VLM avec grammaire (nuit du 7 au 8 octobre)

Le Pi Zero 2 W a lu seul 236 captures tirées de PlayEnd (20 par jeu, 20 écrans hors jeu), sans réseau, avec une
reprise automatique après une coupure de courant (`archive/student-measurements-2026-10/nuit_2026-10-07/`).

**L'élève OCR complet** (classifieur et vote, cadres fixes, OCR des zones, marques) : 1,5 s par capture de jeu en
médiane, 3,7 s au 90e centile, 6,0 s au plus. Classifieur 0,33 s, cadres 0,17 s, OCR des zones 0,9 s (jusqu'à 5,6 s
pour les jeux à plusieurs dispositions, comme Fortnite), marques moins de 0,01 s. Processeur à 78 °C au plus. C'est 30
fois moins que la limite de 45 s.

**LFM2.5-VL-450M avec la grammaire de chaque jeu, sans LoRA** : la grammaire est acceptée par llama.cpp v0.6.0 sur
les 216 captures de jeu, qui répondent toutes au format attendu. Une image prend 46,9 s une fois le modèle chargé
(90e centile 61,5 s), dont 16,9 s pour encoder l'image ; c'est plus que les 37 s du 6 octobre, parce que la question
décrit chaque champ et que la grammaire contraint chaque mot généré.

Sur les mêmes 216 captures, contre le professeur (436 valeurs, noms exclus) :

| Lecteur | Justes | Fausses | Manquées |
|---|---:|---:|---:|
| Élève OCR | 76,1 % | 3,7 % | 20,2 % |
| VLM + grammaire, sans LoRA | 47,7 % | 52,3 % | 0 % |

La grammaire donne la forme, pas le contenu : le modèle ne répond jamais `null` et invente une valeur quand il ne
sait pas. Il fait mieux que l'OCR sur les buts d'EA FC, tous styles de tableau confondus (30 sur 36 contre 17), et sur
les chronos (33 sur 38 contre 26) ; il fait bien moins bien sur les marques (manches : 45 sur 146 contre 133 ; « ∞ » :
4 sur 28 contre 20 ; séries « WINS » : 7 sur 18 contre 17). Apprendre au modèle à répondre `null` et à lire les marques
est le but de l'adaptateur LoRA (kit de l'ami, avec des écrans sans HUD parmi les exemples).

`llama-server` a été compilé sur le Pi cette nuit-là, pour mesurer ensuite la boucle avec le modèle chargé une seule
fois.

## 6. L'effet sur le comptage (8 octobre)

Le compteur (`playend.counting`) reçoit les fins et les modes de facturation que prédit le GRU entraîné sur le
professeur, en lisant soit les observations du professeur, soit celles de l'élève retenu. Chaque partie comptée est
appariée à au plus une partie de la référence ; méthode et tableaux complets dans `docs/counting/README.md`
(« Avec les fins prédites »). Budget d'une fausse fin pour 100 parties, 296 parties de référence :

| Observations lues par le GRU | Parties en trop pour 100 | Parties manquées pour 100 | Minutes au temps en trop / manquées (sur 645) |
|---|---:|---:|---:|
| Professeur | 1,4 | 56,0 | 104 / 50 |
| Élève | 2,6 | 58,2 | 129 / 97 |

Au niveau des fins, l'élève faisait 9,6 fausses fins pour 100 parties ; au niveau du comptage, il fait payer au
client 2,6 parties de trop pour 100. Sur les 27,4 fausses fins par graine (vrais modes), 12,2 sont des fins vues en
retard qui ferment la bonne partie, 9,8 coupent une partie dont la vraie fin suivante est ratée (le nombre reste
juste), 1,0 tombe hors d'une partie ouverte ; 4,4 seulement ajoutent une partie. L'élève coûte donc peu par rapport
au professeur : 1,2 partie de trop et 2,2 parties manquées de plus pour 100. Ce qui limite le comptage, avec l'un comme
avec l'autre, est le rappel du détecteur : plus de la moitié des parties sont perdues pour la salle au budget 1.

## 7. La boucle complète sur le Pi (8 octobre au soir)

Le Pi Zero 2 W a fait seul tout le trajet de l'élève, de la capture au compte (`python -m playend.student.loop run`,
programme `docs/student/pi/nuit_2026-10-08.sh`), sur quatre sessions de PlayEnd lues dans l'ordre : 2 341 captures
et 152 fins. Chaque session a son GRU final (graine 0, seuil du budget 1). Le classifieur avait déjà vu ces images :
la soirée mesure le temps et l'identité avec le PC, pas l'exactitude. Une coupure de courant après 343 captures a
laissé deux fiches remplies de zéros ; depuis, chaque fiche est écrite sur le disque avant d'être renommée, et une
fiche illisible est relue. Après réparation de la carte, la boucle a lu les 2 000 captures restantes en 2 h 20, sans
erreur (`archive/student-measurements-2026-10/nuit_2026-10-08/`).

**Identique au PC.** Sur les 2 341 captures, le jeu, l'écran, le bandeau et les champs lus sont les mêmes que sur le
PC ; la probabilité de fin du GRU en NumPy s'écarte au plus de 1,8 × 10⁻⁷ de celle du PC ; les fins et les comptes
sont les mêmes (9, 30, 6 et 7 parties, et 10 365 s au temps).

**Le temps.** Processeur à 85 °C au plus, sans refroidissement ; 281 Mo de mémoire au plus.

| Captures | Médiane | 90e centile | Maximum |
|---|---:|---:|---:|
| Toutes (2 341) | 3,6 s | 7,6 s | 19,7 s |
| Jeu en cours (1 496) | 2,3 s | 6,3 s | 18,5 s |
| Autres écrans (845) | 6,6 s | 9,6 s | 19,7 s |

Par étape, en médiane : classifieur 0,46 s ; bandeau lu sur la capture entière 6,2 s, jusqu'à 19,2 s sur les menus
d'EA FC, pleins de texte ; cadres fixes 0,20 s ; zones 1,3 s, mais 6,2 s pour Fortnite et 5,0 s pour Beach Buggy
Racing 2, qui ont plusieurs dispositions ; GRU et compteur 0,01 s. Aucune capture ne dépasse 20 s, 96 (4,1 %)
dépassent 10 s et 13 dépassent 15 s : la limite de 45 s est tenue partout. Une capture de jeu prend 2,1 s quand le
bandeau n'est pas lu, contre 1,5 s la nuit précédente : l'OCR tourne maintenant sans réserve de mémoire (14 % plus
lent) et Fortnite et Beach Buggy Racing 2 pèsent plus dans ces quatre sessions. Le bandeau est aussi lu sur les 128
captures de jeu que le classifieur avait d'abord prises pour un autre écran (5,6 s en médiane). C'est la lecture du
bandeau sur la capture entière qu'il faudrait accélérer pour capturer plus souvent.

## 8. Le kit de l'ami : LoRA, VLM et détecteurs réentraînés (9 et 10 octobre)

Le kit construit le 8 octobre (commit 405d67d8, élève retenu de la section 4) a tourné sur le PC d'un ami : Windows 11,
16 cœurs logiques, carte Intel Arc 140T. Résultats rapportés le 10 octobre : le zip
(`playend_eleve_resultats_20261010-1618.zip`) est gardé dans `build/student/archives/` et extrait dans
`build/student/kit_resultats_20261010/`. Comme `build/` n'est pas suivi par git, les rapports, les scores du VLM, le
GRU à déployer et l'adaptateur LoRA final sont aussi copiés dans `resultats_kit_2026-10-10/`. Le modèle fusionné
`models/lora_final-Q4_0.gguf`, qui ira sur le Pi, n'est pas dans le zip : il est revenu à part le 11 octobre
(219 310 496 octets, SHA-256 `3602d815…ff259a`, architecture `lfm2` en Q4_0, nommé `Hf_Lora_Final`), rangé
dans `build/student/models/`. PyTorch n'a pas reconnu la carte : la LoRA a été entraînée sur le
processeur, en float32 (7 h 45 pour l'adaptateur mesuré, 4 339 exemples, 2 époques ; 7 h 24 pour l'adaptateur final,
5 612 exemples). Les lectures du VLM ont tourné sur la carte, par Vulkan. Le lanceur a été corrigé sur place pour
l'encodage de la console Windows (cp1252) et pour torchvision : sa version rapportée fait 410 lignes contre 345, et nous
n'avons pas le fichier modifié.

### Le VLM, avec et sans LoRA

1 273 images de test : le dernier cinquième des images de jeu de chaque session (1 002) et 271 écrans sans HUD. Les
jeux, les équipes et les tableaux de score sont donc déjà vus à l'entraînement, plus tôt dans la même session ; un jeu
ou un HUD nouveau n'est pas mesuré. « Juste » veut dire identique au professeur. L'élève OCR est noté sur les mêmes
images de jeu, avec ses lectures de `readings_ocr.json` mises au format des réponses du VLM. Le tableau se refait
avec `python -m playend.student.vlm_eval compare build/student/kit_resultats_20261010/results/vlm`, qui écrit
`compare.json` (copié dans `resultats_kit_2026-10-10/vlm/`, avec le score de chaque réglage).

| Lecteur | Justes | Fausses | Manquées | Écrans sans HUD où il invente | Médiane sur l'Arc |
|---|---:|---:|---:|---:|---:|
| Modèle publié, sans grammaire | 31,5 % | 19,1 % | 49,4 % | 207 / 271 | 1,09 s |
| Modèle publié, avec grammaire | 65,5 % | 34,2 % | 0,3 % | 271 / 271 | 1,78 s |
| Modèle converti par le kit, avec grammaire | 65,5 % | 34,2 % | 0,3 % | 271 / 271 | 1,18 s |
| LoRA, sans grammaire | 91,6 % | 2,9 % | 5,5 % | 1 / 271 | 1,77 s |
| LoRA, avec grammaire | 91,7 % | 3,1 % | 5,1 % | 6 / 271 | 1,77 s |
| Élève OCR | 75,3 % | 2,9 % | 21,8 % | — | — |

2 689 valeurs attendues ; noms exclus (1 850 valeurs) : LoRA 94,9 % justes, 1,9 % fausses, 3,1 % manquées ; élève OCR
75,0 %, 2,9 % et 22,2 %. Le modèle converti par le kit donne exactement les scores du modèle publié : la conversion
est juste.

La LoRA corrige ce que la grammaire ne corrigeait pas. Le modèle répond `null` quand il ne voit rien (il invente sur
1 écran sans HUD sur 271, contre 271) et il lit les marques et les compteurs :

| Champ | Sans LoRA | Avec LoRA | Élève OCR |
|---|---:|---:|---:|
| Mortal Kombat 1, chrono (secondes ou « ∞ ») | 9 / 248 | 245 / 248 | 216 / 248 |
| Fortnite, joueurs restants | 11 / 143 | 134 / 143 | 119 / 143 |
| Beach Buggy Racing 2, tour | 1 / 33 | 33 / 33 | 27 / 33 |
| Warzone, équipes restantes | 26 / 39 | 39 / 39 | 27 / 39 |
| EA Sports FC, buts (deux équipes) | 698 / 792 | 742 / 792 | 437 / 792 |
| EA Sports FC, chrono | 356 / 379 | 377 / 379 | 362 / 379 |
| Mortal Kombat 1, manches (deux combattants) | 34 / 64 | 60 / 64 | 62 / 64 |
| J-Stars Victory VS+, chrono | 4 / 27 | 12 / 27 | 27 / 27 |

Les points faibles qui restent sont les noms des personnages (Naruto, J-Stars) et le chrono de J-Stars, que l'OCR lit
mieux. Avec la LoRA, la grammaire n'apporte plus rien : sans elle, les champs justes sont les mêmes et le modèle
invente moins. Or la grammaire, avec la question plus longue, faisait passer le temps du Pi de 37 s à 46,9 s par
image (section 5). Sur le Pi, la LoRA sans grammaire prend 44,7 s par image (§9).

### Les détecteurs réentraînés sur les observations de l'élève

Même protocole que le 6 octobre (25 sessions tenues à l'écart, 5 graines pour le GRU), sur le paquet de l'élève
retenu (`observations.csv` a59e7fe3). Budget d'une fausse fin pour 100 parties, choisi sur la validation :

| Détecteur | Entraîné sur | Lit | Fins trouvées | Fausses fins pour 100 parties | Précision |
|---|---|---|---:|---:|---:|
| GRU | professeur | professeur | 37,3 % | 3,8 | |
| Gradient boosting | professeur | professeur | 42,5 % | 1,4 | |
| GRU | professeur | élève | 30,7 % | 9,6 | 76,1 % |
| Gradient boosting | professeur | élève | 22,5 % | 6,0 | |
| GRU | élève | élève | 6,1 % | 3,6 | 63,0 % |
| Régression logistique | élève | élève | 6,0 % | 1,4 | 81,0 % |
| Gradient boosting | élève | élève | 25,3 % | 2,1 | 92,3 % |
| Règles | — | élève | 55,8 % | 32,3 | 63,3 % |

Réentraîner sur les sorties de l'élève divise les fausses fins par trois (gradient boosting : 6,0 à 2,1 ; GRU : 9,6 à
3,6). Le GRU perd en revanche presque tout son rappel : sur des observations plus bruitées, le seuil qui tient le
budget en validation monte, et il ne trouve plus que 6,1 % des fins (14,2 % au budget de 5, pour 11,2 fausses fins).
Le gradient boosting devient le meilleur détecteur sur les observations de l'élève : 25,3 % des fins pour 2,1 fausses
fins pour 100 parties, à comparer à 42,5 % et 1,4 sur celles du professeur. Le mode de facturation prédit par le GRU
est juste dans 88,7 % des captures, contre 93,9 % sur les observations du professeur.

Ces détecteurs lisent l'élève OCR. Le VLM avec LoRA lit le HUD mieux que lui, mais il ne fournit que les champs du
HUD : le classifieur, les bandeaux et le maintien de l'écran restent ceux de l'élève OCR.

Rejoués dans le compteur (`docs/counting/README.md`, « Avec les détecteurs réentraînés sur l'élève »), ces détecteurs
changent peu le compte : au budget 1, le gradient boosting réentraîné compte 0,3 partie en trop et 67,2 manquées pour
100, contre 0,0 et 66,2 pour celui entraîné sur le professeur ; le GRU réentraîné en manque 85,0. Les fausses fins que
le réentraînement retire n'ajoutaient déjà presque aucune partie.

## 9. Le VLM adapté par LoRA sur le Raspberry Pi (nuit du 11 au 12 octobre)

Le Pi Zero 2 W a relu seul les 216 captures de jeu de la nuit du 7 octobre avec l'adaptateur LoRA final du kit,
fusionné et quantifié en Q4_0 (`lora_final-Q4_0.gguf`), d'abord sans grammaire puis avec
(`archive/student-measurements-2026-10/nuit_2026-10-11/`, programme `docs/student/pi/nuit_2026-10-11.sh`). Les
432 lectures se sont terminées sans erreur, processeur à 77 °C au plus. L'adaptateur a été entraîné sur toutes les
captures de PlayEnd, celles-ci comprises : cette nuit mesure le temps, pas la justesse, qui est donnée au §8.

Les temps sont calculés comme le 7 octobre, une fois le modèle chargé (refaire le calcul sur la nuit du 7 donne bien
46,9 s) :

| Modèle | Par image (médiane) | 90e centile | Encodage de l'image | Après l'image | Chargement |
|---|---:|---:|---:|---:|---:|
| Sans LoRA, avec grammaire (7 octobre) | 46,9 s | 61,5 s | 16,8 s | 31,1 s | 29,5 s |
| LoRA, sans grammaire | 44,7 s | 60,1 s | 15,3 s | 29,5 s | 30,3 s |
| LoRA, avec grammaire | 46,7 s | 62,2 s | 16,7 s | 29,9 s | 32,9 s |

La LoRA ne rend pas le modèle plus rapide : une fois fusionnée, elle a la taille du modèle de base, et le temps reste
celui du 7 octobre. Retirer la grammaire ne fait gagner que 2 s. Le temps se partage entre l'encodage de l'image
(15 s) et le traitement de la question puis la réponse (30 s) ; le chargement du modèle (30 s), payé ici à chaque
image, disparaît avec `llama-server`, qui garde le modèle en mémoire.

Avec 44,7 s par image, le VLM lit à peine une capture sur une quand elles arrivent toutes les 10 à 45 s, contre 1,5 s
pour l'élève OCR. Il ne peut donc pas lire chaque capture sur ce Pi. Il peut en revanche lire les captures que l'OCR
laisse douteuses, ou seulement les captures porteuses d'un début de partie ; c'est ce que le comptage par le début
permet de tester (`docs/decisions/PLAN_COMPTAGE_PAR_DEBUT.md`). Raccourcir la question, que la LoRA n'a plus besoin de
détailler, est l'autre piste, puisque le traitement de la question pèse 30 s.

## 10. Le classifieur réentraîné sur PlayEnd 1.1 (14 octobre)

Depuis le 14 octobre, le code de l'élève lit les observations de la version 1.1 (`playend.student.collect.OBSERVATIONS`) ;
les résultats des sections précédentes ont été obtenus sur la 1.0. Entre les deux versions, 403 captures changent de
jeu, surtout l'accueil de la PS5 qui ne porte plus le titre du jeu mis en avant, et 54 de type d'écran. Les réponses
attendues de la LoRA ne changent que sur 7 exemples sur environ 5 000 : elle n'a pas été réentraînée.

Le classifieur a été réentraîné sur les étiquettes de la 1.1 (`build/student/classifier_v1.1.npz` et
`classifier_oof_v1.1.json` ; le modèle du Pi, `classifier.npz`, n'a pas changé). Même évaluation que la section 3 :

| Évaluation | 1.0 | 1.1 |
|---|---:|---:|
| Jeu, par blocs de temps | 86,7 % | 87,4 % |
| Jeu, avec un vote sur les 5 dernières captures | 90,7 % | 90,5 % |
| Jeu, par session retirée | 78,2 % | 82,3 % |
| Type d'écran, par blocs de temps | 85,5 % | 86,1 % |
| Écran de jeu ou non | 94,5 % | 94,5 % |

Rejoué dans le compteur de débuts (`docs/counting/DEBUTS_2026-10-13.md`), avec les paquets de l'élève reconstruits sur
la 1.1 : 88,3 % des 308 parties trouvées pour 8,4 en trop sur 100, contre 87,3 % et 8,1 avec l'ancien classifieur.
Le gain est petit : les erreurs du classifieur qui coûtent des parties (J-Stars, Dragon Ball FighterZ, Demon Slayer,
écrans de jeu pris pour des cinématiques) ne viennent pas des étiquettes changées, mais du peu d'exemples de ces jeux.

## 11. La lecture des compteurs de Warzone (14 octobre)

Le HUD de Warzone range ses compteurs sous des icônes : escouades restantes, joueurs restants, puis éliminations ou
avions. Sans le troisième compteur, tout se décale d'une place vers la droite ; les cadres fixes lisaient alors les
escouades à la place des joueurs, ou un seul des deux chiffres. Le lecteur reconnaît maintenant la disposition par
les icônes (`src/playend/student/read.py`, gabarits dans `src/playend/student/templates/`), lit chaque compteur sous
son icône, agrandi cinq fois, et laisse le nombre de joueurs non lu quand il est plus petit que le nombre d'escouades.

| Joueurs restants de Warzone (281 valeurs du professeur) | Justes | Faux | Non lus |
|---|---:|---:|---:|
| Cadres fixes | 74 % | 62 | 10 |
| Lecture sous les icônes | 83 % | 13 | 34 |

Lectures complètes dans `build/student/readings_ocr_warzone.json`. Dans le compteur de débuts, avec le classifieur
réentraîné : l'élève compte 18 parties de trop pour 100 au lieu de 26 (5,8 au lieu de 8,4 pour 100), sans en
manquer davantage (88,3 %) ; avec les écrans du professeur et les valeurs de l'élève, 8 de trop au lieu de 16
(2,6 pour 100). Il reste 2 parties de trop en Warzone, contre 9. Le Pi lira ainsi après le prochain déploiement.

## 12. Le classifieur réentraîné sur les étiquettes corrigées, et Fortnite en écran partagé (14 octobre, soir)

Après le tour du 14 octobre sur les cinématiques et le bandeau du score (`data/annotations/README.md`), le
classifieur a été réentraîné sur l'export 1.1 refait (`build/student/classifier_v1.1_cine.npz`, vote hors bloc dans
`build/student/classifier_oof_v1.1_cine.json`). Les confusions entre cinématique et jeu passent de 213 à 198 ; le type
d'écran reste juste à 85,9 % par bloc de temps, jeu ou hors jeu à 94,7 %. Sur le compte, l'écart avec l'ancien
classifieur ne dépasse pas une partie dans un sens ou dans l'autre, et se répartit sur sept sessions : c'est du bruit.
Nous gardons le nouveau, entraîné sur les étiquettes publiées.

Fortnite en écran partagé avec un portrait à côté de chaque vue (session ff1c72) affiche le nombre de joueurs sous la
carte de chaque vue, là où d'autres dispositions mettent d'autres nombres. Le lecteur le prend maintenant quand les
deux vues donnent le même nombre (`FORTNITE_SPLIT_PORTRAITS` dans `src/playend/student/rules.py`).

| Joueurs restants de Fortnite (828 valeurs du professeur) | Justes | Faux | Non lus |
|---|---:|---:|---:|
| Avant | 84 % | 29 | 104 |
| Les deux vues d'accord | 86 % | 26 | 90 |

Lectures complètes dans `build/student/readings_ocr_fortnite.json`. Pour Warzone, deux autres façons de trouver les
compteurs ont été essayées sans être retenues : chercher les icônes en glissant leurs gabarits (210 justes au lieu de
234), et ne s'en servir que quand rien n'est lu (3 justes de plus, 2 faux de plus). Les comptes à trois chiffres du
début de partie décalent le HUD, aligné à droite ; ils restent lus juste une fois sur deux.

| Compteur de débuts, élève | Trouvées | En trop pour 100 | Compte exact |
|---|---:|---:|---:|
| Classifieur du 14 après-midi, lecture de Warzone | 85,7 % | 1,9 | 10 sur 25 |
| + lecture de Fortnite | 86,4 % | 1,9 | 10 sur 25 |
| + classifieur réentraîné | 86,0 % | 2,3 | 9 sur 25 |
| Écrans du professeur, valeurs de l'élève | 93,5 % | 1,3 | 15 sur 25 |
