# Installation sur la carte du Raspberry Pi

Le dossier `raspberry_pi/` contient le programme de capture tel qu'il tourne sur le Pi, dans
`/home/brummel/Desktop/Capture-dataset-jeux`. Chaque fichier est listé avec son empreinte SHA-256 dans
`installation_manifest.json`. Un fichier modifié sans refaire le manifeste fait échouer l'installation : c'est voulu.

Les deux scripts de ce dossier tournent sur le PC, avec la carte SD du Pi branchée et montée, en administrateur.

1. Copier le contenu de `raspberry_pi/` dans `home/brummel/Desktop/Capture-dataset-jeux/` sur la partition
   `rootfs` de la carte.
2. `sudo python3 install_on_card.py` vérifie que la carte est la bonne (UUID et utilisateur `brummel`), puis vérifie
   chaque fichier du programme avec le manifeste. Il sauvegarde ensuite les fichiers systemd d'origine dans
   `/var/lib/capture-dataset-installation`, active le service de collecte et empêche l'ancien compteur de démarrer.
   Il refuse de passer sur une installation existante.
3. Facultatif : `sudo python3 enable_boot_diagnostic.py` ajoute le diagnostic de démarrage (`diagnostic_boot.sh`),
   qui écrit deux journaux dans `diagnostics/` sur le Pi.

Le point de montage (`/media/mayano/rootfs`) et l'UUID de la carte sont écrits en dur dans les deux scripts : ils ne
valent que pour la carte installée le 21 septembre 2026. Pour une autre carte, il faut les changer.

Commandes sur le Pi et retour à l'ancien compteur : `../README.md`. Rapport de la première installation, preuves et
journaux du premier essai : `docs/capture/`.
