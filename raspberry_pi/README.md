# Capture d’images de gameplay

Collecteur installé sur le Bureau de brummel. Il crée une session à chaque lancement,
capture le flux HDMI/USB, et enregistre des JPEG complets et leur chronologie.
Pas d’OCR, de VLM ou de GRU. Les intervalles uniformes de 10 à 45 secondes sont une
simulation, pas des mesures de la durée du futur modèle. Moyenne théorique 27,5 s.

Au démarrage, le service attend une carte de capture USB vidéo, puis enregistre une
première image. Les intervalles suivants sont calculés depuis la réception de l’image
précédente, compression et écriture comprises. Un retard reste un retard, sans image
factice ni rafale de rattrapage. Les menus, écrans noirs et images répétées sont conservés.
Une carte qui produit un écran « aucun signal » reste une source vidéo : ces images
seront conservées et devront être annotées plus tard.

Les fichiers sont dans `dataset/session_<uuid>/`. `metadata.json` décrit la configuration,
la graine aléatoire et l’horloge ; `captures.csv` contient les chemins et temps réels ;
`status.json` indique l’état courant ; `events.jsonl` consigne les interruptions.
Les événements sont bornés à trois fichiers de 2 Mio ; les captures et leur index ne
sont jamais supprimés automatiquement. Le temps est celui de réception par le Pi,
pas un timestamp garanti de l’image sur la console. La date civile peut être incorrecte
hors réseau, mais les intervalles utilisent une horloge monotone.

## Commandes sur le Raspberry

```sh
cd /home/brummel/Desktop/Capture-dataset-jeux
systemctl status capture-dataset-jeux.service
journalctl -u capture-dataset-jeux.service -n 40 --no-pager
python3 verify_dataset.py
sudo systemctl stop capture-dataset-jeux.service
sudo systemctl start capture-dataset-jeux.service
```

Pour retrouver l’ancien compteur et son démarrage automatique :

```sh
sudo python3 /home/brummel/Desktop/Capture-dataset-jeux/mode.py compteur
```

Pour revenir à la collecte :

```sh
sudo python3 /home/brummel/Desktop/Capture-dataset-jeux/mode.py collecte
```

La bascule utilise `/etc/capture-dataset-mode`. Des fichiers de complément systemd
empêchent l’ancien compteur de démarrer tant que ce marqueur existe. Ses fichiers
originaux et ses liens d’activation restent conservés. Le service cluster est conservé.
Ne pas lancer manuellement l’ancien `main.py` pendant la collecte : il contournerait
cette protection des services et pourrait monopoliser la vidéo.

## Configuration et stockage

`config.json` : intervalle min/max, résolution demandée 1280×720, JPEG qualité 90,
réserve minimale de 5 Gio. La résolution effectivement reçue figure dans chaque ligne
CSV. Avec plusieurs périphériques vidéo USB, renseigner `device` avec le chemin
approprié, idéalement `/dev/v4l/by-id/...`, puis redémarrer le service. Le programme
refuse de choisir arbitrairement entre plusieurs sources.

À moins de 5 Gio libres, l’enregistrement s’arrête normalement (`storage_full`) et le
service ne redémarre pas tout seul. Transférer/vérifier les données et libérer de
l’espace avant de le relancer. Ne pas diminuer cette réserve sans examiner l’OS.

Avant de retirer l’alimentation, arrêter proprement le Raspberry (`sudo poweroff`).
Les images sont synchronisées puis renommées, avant l’ajout synchronisé au CSV.
Une coupure peut néanmoins laisser des fichiers incomplets ou une image sans ligne
CSV : `verify_dataset.py` les signale en lecture seule, sans effacer ni inventer de données.
Une nouvelle session évite tout écrasement. Les anciens index ne sont pas réparés
automatiquement : conserver les fichiers signalés pour examen.

## Vérification matérielle à faire au premier démarrage

La préparation sur PC ne teste pas le fonctionnement ARM, le boot ni le périphérique.
Après remise de la carte dans le Pi et connexion HDMI/USB, laisser tourner dix minutes.
Vérifier la création des JPEG, leur lisibilité et le fichier `captures.csv`. En dehors
des démarrages, pannes et lenteurs, les intervalles réels doivent suivre le tirage de
10–45 s avec le petit retard de réception. Un dépassement de 45 s est possible et
doit rester visible dans les données. Vérifier ensuite déconnexion/reconnexion et
redémarrage sans écran ni Internet. Une vidéo de référence séparée aidera à annoter
les combats qui se terminent entre deux captures.

Le service borne sa mémoire à 180 Mio pour limiter son impact sur le système ; le
plafond et le coût de la lecture continue devront être évalués sur le matériel réel.
Un périphérique qui bloque provoque une relance du processus vidéo après 20 secondes.
Les erreurs ordinaires de source déclenchent un nouvel essai après 5 secondes.
