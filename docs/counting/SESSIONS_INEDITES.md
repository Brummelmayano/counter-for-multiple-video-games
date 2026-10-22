# Évaluation sur deux sessions jamais lues (protocole, 15 octobre 2026)

Tous les chiffres du compteur de débuts sont mesurés sur les 25 sessions de PlayEnd, qui ont servi à écrire ses
règles : ils sont optimistes (`docs/training/PROTOCOLE_DEBUTS.md`). Deux sessions capturées le 2026-10-03 n'ont jamais
été lues, ni par le professeur ni pour écrire une règle : 2e4eea20 (251 captures) et a4ad74e6 (620 captures). Elles
avaient été laissées de côté pour équilibrer les jeux de PlayEnd (surtout EA FC et Fortnite). Elles servent ici de
test, une seule fois.

## Ce qui est gelé avant de regarder une seule image

Le système évalué est celui qui tournera sur le Pi : l'élève (classifieur d'écran et de jeu, lecteur OCR) suivi du
compteur de débuts par règles. Il est gelé au commit `96d77ad2` (2026-10-15), avec :

| Fichier | SHA-256 |
|---|---|
| `src/playend/counting/starts.py` | `077bcb67c3a28af9875c2309a4e835670130588a1414810223bd70ebb587f466` |
| `src/playend/counting/portraits.py` | `03f2c5f695f1699b21925f535a8979c3bf3825402a8b594a3ba4f66902384ce5` |
| `src/playend/student/read.py` | `e2f8242e2687d9680fc345e0e6dccf3ae881245ab45736b0c402d4ed2e0b7550` |
| `src/playend/student/rules.py` | `c0b3abcc1741937be892cb6702462ab46c0da6370943236dbe4a30bb264b605d` |
| `src/playend/student/zones.py` | `8122a010822a54431b3ee5c1e46fed51ad7a955e92cfeb0bcb24d70be2b7d191` |
| `src/playend/student/ocr.py` | `8e11f8baa1c2c84bd81d1adaa956642ec5f2297a2f254ff92ea1186e6b7119a2` |
| `src/playend/student/package.py` | `ebc935ea96b2bf60dcd0e7b12554a2d46f19795a9376437e55fd11d269e043c9` |
| `src/playend/student/classify.py` | `a4f6c1810a7a9e8f7894b23e06611d93f1c144cc6aea88dd034ff3b26c5e0a8b` |
| `build/student/classifier_v1.1_cine.npz` (classifieur entraîné sur les 25 sessions) | `d267c9fd15bde23cc9f490872e8efe8a9ed52896f2276290aed3b11e379dce92` |

Aucune règle, aucun seuil, aucun modèle de ce système ne change avant la mesure, quoi que montrent l'étape 3 ou ces
sessions. Une erreur trouvée sur ces sessions est un résultat ; sa correction ira dans une version suivante, mesurée
sur d'autres données.

## L'ordre des opérations

1. **La référence, sans le système.** Les parties de chaque session sont repérées sur les captures elles-mêmes
   (planches, puis HUD agrandi autour de chaque début et de chaque fin), selon les règles de comptage et la règle des
   débuts de l'auteur (`docs/decisions/regles-de-comptage.md`) : le début sur la première capture de jeu de la partie
   dont le score ou le HUD est lisible, la fin sur la première capture qui la prouve, les modes sans fin au temps. Le
   système ne tourne pas sur ces sessions avant que la référence soit faite.
2. **La validation par l'auteur**, partie par partie, dans l'outil local.
3. **La mesure, une seule fois** : l'élève lit les captures brutes, le compteur compte ; parties trouvées, parties en
   trop, compte exact par session, avec la même règle d'appariement que pour PlayEnd (un début dans la partie, ou
   jusqu'à deux captures avant sa première capture).

La référence est écrite dans `data/evaluation/sessions_inedites/` ; les réponses de l'auteur dans
`data/validation/inedites_2026-10-15/`.

## Résultat de la mesure unique (15 octobre 2026)

`python -m playend.counting.heldout`, lancé une fois, système gelé vérifié par ses empreintes ; lectures de chaque
capture dans `build/evaluation/sessions_inedites/`.

| Référence | Parties | Trouvées | En trop | Précision | Compte exact |
|---|---:|---:|---:|---:|---:|
| Validée avant la mesure | 25 | 23 (92,0 %) | 8 (32 pour 100) | 74 % | 0 sur 2 |
| Avec les deux relances trouvées après (validées) | 27 | 25 (92,6 %) | 6 (22 pour 100) | 81 % | 1 sur 2 |

**Deux erreurs de la référence**, trouvées parce que le compteur y plaçait un début : deux matchs d'EA FC recommencés
pris pour un seul. En 2e4eea20, le chrono passe de 90:02 à 82:31 au même score (capture 185) ; en
a4ad74e6, de 23:48 (menu de pause, 210) à 07:30 (212). Seul U18 avait été vérifié ainsi, à la demande de l'auteur ;
les autres matchs ne l'avaient été qu'à leurs bords. Après la mesure, le chrono des 302 captures d'EA FC de la référence a été
relu : ces deux cas sont les seuls. L'auteur a validé la correction (`data/validation/inedites_relances_2026-10-15`) ; la
référence d'avant la mesure est gardée dans `data/evaluation/sessions_inedites/avant_mesure/`, et le second chiffre
vient des mêmes lectures, notées de nouveau sans relancer le système (`results_reference_avant_mesure.json` et
`results.json`).
Corriger une référence après avoir vu les sorties d'un système peut l'avantager ; c'est pourquoi les deux chiffres
sont donnés. Northcutt, Athalye et Mueller (2021) procèdent de même pour les erreurs d'étiquettes des jeux de test :
les candidats viennent des modèles, la décision d'un humain.

**Les parties manquées.** 2e4eea20, U02 (Fortnite) : le nombre de joueurs n'est lu sur aucune capture de la partie ;
la colonne de compteurs de cette vue est quelques pixels à gauche de la zone que lit l'élève. a4ad74e6, U17 : le
compteur a bien compté une partie de plus, décidée en 536, mais avec un début placé en 512, dans le match d'avant ; la
règle d'appariement la compte comme une partie manquée et une en trop.

**Les parties en trop (référence corrigée).** Cinq viennent de scores mal lus dans l'habillage LaLiga d'EA FC 27 :
l'OCR lit comme un « 4 » le logo rouge de LaLiga, à gauche du tableau, avec ou sans les sigles des équipes (4–0 au lieu
de 0–0 en 2e4eea20, 226 ; 4–3 au lieu de 0–3 en a4ad74e6, 297 ; 4–4 au lieu de 0–4), et le score qui retombe ensuite
passe pour une rupture (2e4eea20 : 237 ; a4ad74e6 : 297, 304, 512, 547). En a4ad74e6, 295, un bandeau de remplacement
couvre le tableau et le numéro du joueur qui entre (14) est lu comme un score (4–14). *Corrigé le 2026-10-16 : la
première version attribuait le « 4 » à l'écusson du club ; les captures 226 et 297 montrent que c'est le logo.* Une vient de la vidéo de présentation d'UFC 5 (467) : le classifieur y voit du jeu et
l'OCR lit les noms des combattants et un chrono.

**Ce que cela dit.** Sur des sessions jamais vues, le compteur trouve presque autant de parties que sur PlayEnd
(92 % contre 86 % pour l'élève), mais en compte bien plus de trop (22 pour 100 contre 2,3). L'écart vient d'un
habillage rare dans PlayEnd et fréquent ici, et non des règles de comptage : le tableau LaLiga (logo rouge reconnu par
sa couleur) est sur 107 des 2 049 captures de jeu d'EA FC de PlayEnd, une sur vingt, et sur 156 des 301 captures des
21 matchs d'EA FC de ces deux sessions (11 matchs). Sur les 97 captures LaLiga de PlayEnd où le professeur lit un
score, l'élève n'en lit aucun juste (76 non lus, 21 faux dont 18 avec ce « 4 »). *Précisé le 2026-10-16.* C'est la limite attendue de règles et d'un lecteur réglés sur 25 sessions. Deux sessions ne suffisent pas à
donner un intervalle de confiance : ce chiffre se lit comme un ordre de grandeur.
