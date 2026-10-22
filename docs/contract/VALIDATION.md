# Revue technique — 23 septembre 2026

## Résultat

21 tests automatisés réussis : 16 sur le contrat et la préparation temporelle,
5 sur l'adaptateur API. Le [journal](validation_log.txt) contient les commandes
et sorties. Les appels API sont simulés ; aucun coût d'inférence n'a été engagé.

Le validateur de sortie accepte le modèle JSON 2.0. Le contrôle des fichiers
requis du handoff et le chargement CLI du runner local passent. La consultation
hors ligne de l'état des nouvelles propositions API fonctionne. Elle ne constitue
pas un essai du service distant ou d'un modèle local.

## Points contrôlés

- JSON strict, doublons de clés refusés, valeurs non finies/booléens numériques
  refusés, version inconnue refusée, absence de labels temporels dans l'observation.
- Conversion exacte mm:ss, h:mm:ss et fractions ; refus des secondes inventées
  à partir de minutes approximatives et des nombres sans affichage source.
- Compteur secondaire illisible ou de rôle inconnu conservé ; inventaire absent,
  inconnu et valeur réellement nulle distincts.
- Main clock et compteurs secondaires simultanés, sans mélange des valeurs.
- Suite de tempête 44 → 0 → 180 : aucune valeur ou différence ajoutée au chrono
  principal, aucune fin de partie ni cible d'entraînement fabriquée.
- Plusieurs compteurs du même type : permutation sans effet sur les variables.
- Intervalles réels 10,125 s puis 45,5 s ; remise à zéro de l'historique au changement
  de session ; rejet des retours en arrière et sessions entrelacées.
- Données futures et labels séparés sans effet sur les variables déjà calculées.
- Masque de perte nul pour les propositions non vérifiées et les intervalles non
  étiquetés ; contrôle des bornes des labels.
- Contrôle de compatibilité des checkpoints : anciennes dimensions, empreinte ou
  ordre incorrects refusés par le contrôleur v3.
- Envoi du JPEG entier dans l'adaptateur API simulé ; reprise vérifiée avec
  empreintes, refus des réponses incomplètes ou contenant des clés dupliquées.
- Prompts et schémas générés identiques aux sources communes.

## Essai avec le manifeste existant

Le manifeste `annotations_codex_full_frames_v1/manifest.jsonl` a été parcouru :
4 observations, une session, 4 chronos legacy masqués, zéro intervalle éligible
à l'entraînement. Sortie séparée dans
[examples/legacy_manifest_smoke_v3](../../src/playend/contract/examples/legacy_manifest_smoke_v3/report.json).
Aucune annotation source n'a été corrigée ou promue en référence humaine.
La copie figée `legacy_v1.py` est identique octet pour octet au validateur
historique ; le package GRU de reproductibilité n'a pas été modifié.

Le nouveau vecteur comporte **201 variables**. Aucun ancien checkpoint ne doit
être utilisé avec ces vecteurs. Le préparateur et le contrôleur de compatibilité
sont disponibles ; les anciens entraînements ne sont pas transformés en modèle v3.

## Limites restantes

Cette revue valide le contrat et les transformations logicielles, pas la lecture
visuelle des compteurs. Les nouveaux prompts n'ont pas encore fait l'objet d'une
nouvelle campagne VLM sur les images. Le fichier `storm_timer_illustration.json`
est un exemple de structure, pas une annotation mesurée sur une capture.

Prochaine validation scientifique : réannoter un petit lot d'images entières avec
ce contrat, vérifier manuellement rôles/chiffres/absence, puis annoter séparément
les frontières sur des séquences et entraîner un GRU compatible. Séparer les
sessions entre apprentissage, validation et test. Aucun score de précision ni
gain de comptage réel n'est revendiqué ici.
