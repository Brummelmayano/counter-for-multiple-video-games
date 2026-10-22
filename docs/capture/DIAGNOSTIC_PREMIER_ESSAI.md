# Premier essai matériel : aucune capture trouvée

L’utilisateur confirme avoir démarré le Raspberry avec cette carte, puis l’avoir
replacée dans le PC. À l’inspection : aucun dossier de session, aucun JPEG, aucun
fichier `.capture.lock`, aucune entrée du collecteur dans le journal persistant.
Les fichiers installés sont intacts, les liens de démarrage existent et les chemins
de la partition racine dans cmdline.txt et fstab correspondent à la carte.
Le journal système consulté passe sa vérification d’intégrité.

La cause de l’absence de lancement n’est pas établie. Une absence de source vidéo
ne suffit pas à l’expliquer : le programme crée sa session avant d’ouvrir la vidéo.
La durée de l’essai et les signes de démarrage vus par l’utilisateur ont été demandés.

Ajout effectué : `capture-dataset-diagnostic.service`, service léger indépendant,
qui écrit `diagnostics/boot-current.log` dans le projet dès son lancement, puis
relève six fois l’état du collecteur, les sources vidéo et ses dernières erreurs,
avec une pause de 15 secondes entre relevés. Le journal du démarrage précédent
est conservé dans `boot-previous.log`. Il ne lance pas le collecteur et ne modifie
ni la vidéo, ni le boot, ni les partitions, ni la configuration réseau.

Les deux services sont activés et passent la vérification systemd hors ligne.
Les dix fichiers du projet correspondant au manifeste sont vérifiés par SHA256.
Le collecteur lui-même, les intervalles de 10–45 s et les anciens fichiers système
ne sont pas modifiés par cet ajout. L’état avant nouvel essai est sauvegardé dans
`validation/diagnostic_avant_nouvel_essai.json` pour comparer les traces au retour.

Le journal kernel existant indique aussi un contrôleur mémoire cgroup désactivé.
Le plafond MemoryMax du service peut donc ne pas être appliqué sur ce système ;
il ne faut pas présenter les 180 Mio comme une limite matériellement vérifiée.
Cela n’établit pas la cause du non-démarrage. Aucun paramètre du noyau n’a été changé.
