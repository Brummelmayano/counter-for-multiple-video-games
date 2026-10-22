# Installation du collecteur — 21 septembre 2026

Le collecteur est installé sur la carte système du Raspberry, dans
`/home/brummel/Desktop/Capture-dataset-jeux`. Le service
`capture-dataset-jeux.service` est activé pour le prochain démarrage.
La carte était attachée au PC : aucun démarrage Raspberry ni essai réel HDMI
n’a été effectué pendant cette installation.

## Fonctionnement installé

- Première capture lorsque la source vidéo USB peut être ouverte.
- Tirages uniformes indépendants entre 10 et 45 secondes ; intervalle visé depuis
  la réception précédente, écriture incluse. Profil explicitement simulé.
- Images complètes, menus et transitions conservés, aucune extraction VLM/OCR/GRU.
- Une nouvelle session par lancement, fichiers JPEG et index CSV avec horodatage
  monotone réel, heure civile, intervalle tiré, retard, dimensions et SHA256.
- Réception vidéo dans un processus séparé pour drainer les buffers ; relance si
  une demande bloque plus de 20 secondes. Essai suivant après 5 s en cas d’erreur.
- Pas de remplissage des trous par des images dupliquées. Les pixels identiques
  issus de réceptions distinctes sont conservés.
- Réserve de 5 Gio : arrêt sans suppression du dataset au seuil d’espace libre.
- Écritures synchronisées, sessions uniques, audit en lecture seule des fichiers
  incomplets/orphelins ; aucune garantie absolue contre une coupure électrique.

## Installation et retour arrière

Les fichiers originaux de l’OS et du compteur n’ont pas été réécrits. Les seuls
ajouts de configuration système sont le service, son lien de démarrage,
`/etc/capture-dataset-mode`, et des compléments `90-capture-dataset.conf` pour
`compteur-boot.service` et `compteur.service`. Ces compléments empêchent les anciens
services d’ouvrir la vidéo pendant le mode collecte. Leurs liens de démarrage
originaux restent présents. Le service cluster reste inchangé.

Les copies de sauvegarde et l’inventaire sont dans
`/var/lib/capture-dataset-installation` sur la carte. Une copie de l’inventaire est
dans `validation/installation_record.json` sur le PC.

Pour revenir au compteur sur le Raspberry, sans supprimer les captures :

```sh
sudo python3 /home/brummel/Desktop/Capture-dataset-jeux/mode.py compteur
```

Pour réactiver le collecteur :

```sh
sudo python3 /home/brummel/Desktop/Capture-dataset-jeux/mode.py collecte
```

## Vérifications réalisées

- **17 tests réussis** : calendrier aléatoire reproductible, écriture comprise dans
  l’intervalle, retard de stockage, déconnexion/reconnexion, manque d’espace,
  correction de l’heure civile, écritures cohérentes avec l’index, rejet d’une même
  réception réutilisée, nouvelles sessions, panne entre écriture JPEG et index.
- Deux de ces tests exécutent le programme parent et son processus vidéo avec un
  module OpenCV simulé : collecte complète et blocage suivi d’un arrêt propre.
  Les données simulées sont restées dans des répertoires temporaires sur le PC.
- Compilation syntaxique Python et vérification systemd, y compris avec la racine
  du système cible ; `systemctl --root=... is-enabled` répond `enabled`.
- **47 contrôles d’installation réussis** : SHA256 du projet, fichiers système
  originaux conservés, anciens liens préservés, propriétaire brummel, mode exclusif,
  espace libre, configuration systemd et répertoire dataset initialement vide.
- Aucun paquet ajouté au système : Python, OpenCV et v4l-utils étaient présents.

Preuves : `validation/tests.log`, `validation/installation_audit.json`,
`validation/systemd_verify.log`. Le silence de ce dernier fichier correspond à
la vérification systemd sans erreur, code de retour zéro consigné dans l’audit.

## Validation restante sur le matériel

Après remise de la carte dans le Raspberry, connecter la source HDMI/USB et mettre
sous tension. Laisser fonctionner dix minutes puis contrôler les JPEG et le CSV.
Il faut encore vérifier la lisibilité, les capacités de la carte vidéo, la fraîcheur
des images, les intervalles effectivement obtenus, l’usage mémoire et la reconnexion.
Les tests sur PC ne constituent pas une mesure de performance du Zero 2 W.

Le guide de contrôle et les commandes de diagnostic sont dans `projet/README.md`
(et dans le même README sur le Bureau du Raspberry).

Après synchronisation, les deux partitions `bootfs` et `rootfs` ont été démontées
proprement. Le gestionnaire de fichiers qui conservait rootfs ouvert a été fermé
normalement ; aucun démontage forcé. La carte peut être retirée du PC.
