# Collecte d’images de gameplay sur Raspberry Pi Zero 2 W

Statut actualisé le 21 septembre 2026 : projet installé sur la carte et service
activé hors ligne après demande explicite de l’utilisateur. Profil choisi par
l’utilisateur : intervalles uniformes de 10 à 45 secondes, simulés. Les tests
logiciels et l’audit d’installation passent ; le boot réel et la capture HDMI sur
le Raspberry restent à vérifier. Voir RAPPORT_INSTALLATION.md et projet/README.md.
Les sections ci-dessous conservent le raisonnement de conception initial.

## État constaté

- Carte `/dev/mmcblk0`, environ 64 Go commerciaux. Partition système ext4 UUID
  `4aa56689-dcb4-4759-90e6-179beae559ac`, montée sur `/media/mayano/rootfs`.
- Partition de démarrage `bootfs`, UUID `EF6E-C078`.
- Debian 12 Bookworm ARM64 ; utilisateur `brummel`, UID/GID 1000, membre de `video`.
- Le Bureau configuré est `/home/brummel/Desktop` sur le Raspberry.
- Environ 25 Gio disponibles sur la partition système au moment de l’inspection.
- Python 3.11, OpenCV 4.6, NumPy, FFmpeg et v4l-utils sont installés selon dpkg.
  Le module OpenCV ARM64 est présent. Leur fonctionnement sera vérifié sur le Pi ;
  lire la carte depuis un PC x86 ne constitue pas un test d’exécution ARM.
- `compteur-boot.service` et `compteur-cluster.service` sont activés au démarrage.
  Le premier lance `auto_launcher.sh`, puis `boot_launcher.py`, qui ouvre le flux
  vidéo avant de lancer `main.py`. Une compétition avec le collecteur est possible.
- Le projet existant demande une image 1280 × 720 et utilise OpenCV/V4L2.

## Sens de « refléter la réalité »

Correction après précision de l’utilisateur : le compteur final est séquentiel.
Il capture une image, attend le VLM, le GRU et le comptage, puis capture la suivante.
Une cadence de 0,5 seconde ne représente donc PAS son fonctionnement prévu.

L’intervalle entre débuts de captures est la somme des durées de capture,
prétraitement, VLM, préparation des observations, GRU, comptage/persistance et
éventuelle pause supplémentaire. Une pause de boucle n’est pas cet intervalle.
Les latences peuvent varier d’une image à l’autre et avec les ressources disponibles.
La durée exacte du cycle n’est pas connue tant que le pipeline retenu n’a pas été
mesuré sur le Raspberry cible, avec sa configuration de mémoire et de swap.

Le collecteur actuel reste sans VLM, OCR ni GRU. Deux usages sont à distinguer :

- Dataset représentatif du compteur : rejouer un profil de durées de cycles mesurées
  sur le Pi, sans additionner par erreur le temps d’écriture du collecteur à un délai
  qui l’inclut déjà. Conserver les échéances demandées et les instants réels ; tout
  dépassement est enregistré sans rafale de rattrapage. Le profil rejoué reste une
  approximation, notamment si la latence dépend du contenu de l’image.
- Archive source plus dense, facultative : conserver davantage d’images pour former
  ensuite des sous-séquences selon les latences mesurées. Une telle archive n’est
  pas directement une séquence représentative à fournir au GRU. Une cadence dense
  ne sera choisie qu’en fonction du budget de stockage et des essais matériels.

Sans profil mesuré, on peut préparer le collecteur et recueillir une archive source,
mais on ne peut pas prétendre avoir fixé une cadence représentative. Ni 0,5 seconde,
ni 30 secondes, ni un intervalle aléatoire ne sont établis comme durée réelle.
La sélection ultérieure doit être causale : prochaine image disponible après la fin
du cycle précédent, sans consulter les événements futurs. Documenter aussi l’erreur
temporelle due à la résolution de l’archive. Les simulations ne remplacent pas un
test embarqué ; on ne peut pas recréer des événements absents des captures.

## Projet et données prévus

```text
/home/brummel/Desktop/Capture-dataset-jeux/
  capture.py
  config.json
  README.md
  systemd/capture-dataset-jeux.service
  tools/                  # contrôle, vérification et retour au mode compteur
  dataset/
    session_<identifiant_unique>/
      metadata.json
      captures.csv
      events.jsonl
      status.json
      images/
        bloc_0001/
          frame_00000001.jpg
```

Un lancement crée une nouvelle session sans écraser les précédentes. Conserver
le boot_id et un identifiant de lancement distinct : un redémarrage du service
pendant le même boot ne doit pas confondre deux séquences. L’identifiant unique
ne dépend pas seulement de la date, potentiellement incorrecte hors réseau.
Les blocs limitent le nombre de fichiers dans un même répertoire.

Les captures couvrent les sessions complètes : menus, pauses, chargements,
gameplay, résultats, revanches et changements de jeu. Pas de filtre de similarité
qui éliminerait les images répétées. Une image noire réellement reçue peut être
une transition ; elle ne doit pas être assimilée automatiquement à une panne.
Le nom du jeu et les limites des parties seront annotés séparément, après collecte.

## Horodatage et acquisition

1. Ouvrir la carte HDMI/USB avec une identité persistante si disponible ; vérifier
   ses capacités de capture. Ne pas choisir arbitrairement le premier `/dev/video*`.
2. Négocier le format et la résolution, consigner les valeurs réellement obtenues.
   Commencer par vérifier 1280 × 720, JPEG qualité 90 ; vérifier la lisibilité des
   petits textes et marqueurs sur les fichiers enregistrés, ajuster si nécessaire.
3. Recevoir le flux dans une tâche dédiée qui entretient une image récente, avec
   numéro de réception et horodatage. Garder une mémoire bornée ; ne pas accumuler
   le flux complet pendant une écriture lente. Mesurer le coût réel sur le Pi.
4. Programmer les prélèvements sur des échéances monotones, calculées selon le
   profil de cycles pour le mode représentatif, ou l’intervalle explicitement choisi
   pour une archive dense. Si une échéance est
   dépassée, enregistrer le retard et les échéances sautées, puis continuer sans
   rafale de rattrapage. Ne pas réenregistrer une même réception comme image neuve.
   Deux réceptions réellement distinctes peuvent contenir des pixels identiques.
5. Horodater la réception avant compression/écriture, et mesurer ces deux durées.
   Si disponible via le backend choisi, conserver aussi le timestamp du pilote
   et son domaine d’horloge. Avec OpenCV seul, annoncer honnêtement un timestamp
   de réception logiciel : il ne prouve pas l’heure exacte de l’image sur la console.
6. Vérifier expérimentalement la fraîcheur du flux (horloge visible filmée/capturée)
   pour détecter un retard de buffers. Une propriété de buffer demandée ne suffit
   pas à démontrer que le matériel l’applique.

Champs prévus par capture : `session_id`, `frame_id`, `filename`, `receive_seq`,
`received_monotonic_ns`, `elapsed_s`, `delta_t_s`, `received_wall_utc`,
`timestamp_source`, `scheduled_elapsed_s`, `lateness_s`, `frame_age_at_selection_s`,
`encode_ms`, `write_ms`, `width`, `height`, `size_bytes`, `sha256`.
Le hash peut être calculé sur les octets JPEG déjà en mémoire.

`delta_t_s` correspond aux réceptions des images effectivement sauvegardées.
Les échecs et pertes sont dans `events.jsonl`, jamais comblés par des timestamps
inventés. L’heure civile et son état de synchronisation sont complémentaires.
Une correction de l’heure système ne doit pas altérer les intervalles monotones.
Ne pas calculer un intervalle monotone à travers deux redémarrages.

## Démarrage autonome et coexistence

Prévoir un service système exécuté sous `User=brummel`, sans bureau graphique ni
connexion Internet nécessaires, avec accès au groupe `video`. Utiliser Python
système déjà installé ; vérifier les imports sur le Pi avant activation.
Le service attend/recherche la carte de capture lorsqu’elle n’est pas présente,
consigne les interruptions et réessaie à intervalle borné. Prévoir un verrou
anti-double lancement et une reprise après erreur avec temporisation.

L’installation devra proposer un mode collecte exclusif : relever et sauvegarder
l’état des anciens services, empêcher temporairement `compteur-boot.service`
d’ouvrir la vidéo, puis activer le nouveau collecteur. Conserver les fichiers et
données de l’ancien projet. Auditer les autres lanceurs avant activation ; traiter
`compteur-cluster.service` seulement s’il relance ou commande le pipeline en conflit.
Préparer la procédure inverse qui restaure exactement l’état précédent.
Ne pas simplement ajouter les deux programmes au démarrage en espérant partager
la carte vidéo. Cette bascule fait partie de la future installation, pas de cet audit.

## Conservation de l’OS et des données

- Ajout du projet et d’un service dédié ; aucune réinstallation, aucun formatage,
  aucune modification des partitions, du boot, du réseau ou du swap nécessaire.
- Prévoir par défaut au moins 5 Gio libres sur la partition système ; au seuil,
  arrêter les captures et afficher/consigner `storage_full`, sans effacer le dataset
  ni relancer indéfiniment le service en erreur. Journaux eux aussi bornés.
- Dimensionner le stockage selon le profil choisi : nombre d’images par heure
  multiplié par taille JPEG moyenne mesurée. À titre d’exemple uniquement, une
  archive à 0,5 s produit 7 200 images/heure, environ 1,44 Go à 200 ko/image ;
  cet exemple n’est pas une estimation de la cadence du compteur.
- Écrire chaque JPEG dans un fichier temporaire puis le renommer ; définir une
  politique de synchronisation fichiers/répertoires et index adaptée au débit.
  Une coupure brutale peut encore perdre les dernières écritures : aucun mécanisme
  applicatif ne garantit à lui seul la survie de toute la carte à une coupure.
- Prévoir arrêt propre, contrôle au redémarrage des fichiers incomplets et images
  orphelines, récupération documentée sans supprimer silencieusement des preuves.
- Éjecter proprement la carte du PC avant de la remettre dans le Raspberry.

## Validation avant collecte longue

1. Sur PC : tests de l’ordonnanceur avec retards, horloge civile corrigée, perte de
   source, stockage plein simulé et redémarrage ; vérifier l’absence de duplication
   artificielle, de réécriture de session et de suppression automatique.
2. Sur le Pi : vérifier les imports et capacités vidéo, essai manuel de dix minutes,
   inspecter la lisibilité, les deltas réels, retards, trous, fraîcheur, mémoire,
   consommation de stockage et erreurs d’écriture. Pour le mode représentatif,
   confronter les intervalles obtenus au profil de cycles mesuré sur le Pi.
3. Tester source branchée après démarrage et reconnexion HDMI/USB ; distinguer les
   images « aucun signal » produites par la carte des échecs de lecture.
4. Activer ensuite le service et vérifier un démarrage réel sans écran ni réseau,
   absence de compétition avec le compteur et création d’une nouvelle session.
5. Faire une collecte prolongée et produire un bilan des intervalles et pertes.
   Ne pas présenter des tests sur PC comme une validation sur Zero 2 W.
6. Pour le futur GRU, répartir les sessions complètes entre entraînement et test,
   avant toute création de sous-séquences, afin d’éviter les fuites entre ensembles.

## Référence technique

Python 3.11 définit une horloge monotone indépendante des mises à jour de l’heure
système : https://docs.python.org/3.11/library/time.html#time.monotonic_ns

Le fonctionnement séquentiel est confirmé par l’utilisateur. Le profil uniforme
10–45 secondes a ensuite été choisi explicitement pour cette collecte. Il est
installé et reste identifié comme simulation ; les durées réelles des cycles VLM
restent à mesurer sur le matériel cible.
