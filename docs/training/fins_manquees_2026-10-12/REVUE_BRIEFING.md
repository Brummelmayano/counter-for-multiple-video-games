# Consignes : relecture contradictoire des analyses de fins manquées

Huit analystes ont étudié, cas par cas et image par image, les 211 fins que le gradient boosting ou le GRU a manquées
(calcul du 6 octobre, budget d'une fausse fin pour 100 parties). Lis d'abord `BRIEFING.md` (même dossier) : il
décrit le projet, les détecteurs, la façon dont les variables de changement sont calculées et les codes de cause.

Leurs analyses sont dans `build/observations/fins_manquees/analyses/` : un fichier `<lot>.jsonl` (une ligne par cas)
et un fichier `<lot>.md` (texte et synthèse du lot) pour chacun des huit lots. Les dossiers et les planches des cas
sont dans `cas/`.

Tu relis **tous les cas**, avec ton propre regard de métier, pour confirmer, nuancer ou contester chaque analyse. Tu
n'es pas là pour approuver : un désaccord argumenté vaut plus qu'un accord poli. Quand tu doutes d'une affirmation
(un écran de fin « non marqué », une erreur du professeur, une étiquette douteuse, une explication de l'échec par les
variables), **vérifie-la toi-même** sur le dossier et sur les images originales.

## Ce que tu rends

Dans `build/observations/fins_manquees/analyses/` :

1. `revue_<ton_regard>.jsonl` : une ligne JSON par cas (les 211), avec exactement ces clés : `case_id`, `accord`
   (`oui`, `partiel` ou `non`), `cause_principale_selon_moi` (un code du briefing ou un nouveau, défini),
   `commentaire` (ce que tu ajoutes ou contestes, concret), `verifie_sur_images` (vrai ou faux).
2. `revue_<ton_regard>.md` : ta synthèse, avec (a) les points où tu contestes les analystes, cas cités ; (b) ce que
   ton métier voit que les autres n'ont pas vu ; (c) pour chaque famille de causes, la méthode que tu recommandes,
   pourquoi, et ce qu'elle coûterait ; (d) les trois priorités que tu donnerais à l'auteur.

**Écris au fur et à mesure.** Dès qu'un cas est fait, ajoute tout de suite sa ligne au `.jsonl` (et sa section au
`.md` s'il y en a une), en mode ajout, avant de passer au suivant ; avant de commencer un cas, regarde s'il est déjà
dans le `.jsonl` et passe-le si oui. Une coupure de connexion ne doit faire perdre qu'un cas.

## Règles

Écris en français. N'écris jamais le pseudo d'un vrai joueur. Ne modifie aucun autre fichier, ne touche pas aux
analyses des autres, ne lance aucun entraînement. Tu peux chercher en ligne ; cite les liens qui t'ont servi.

Ta réponse finale : combien d'accords, d'accords partiels et de désaccords, et tes trois priorités.
