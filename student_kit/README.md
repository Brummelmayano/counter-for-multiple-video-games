# Kit de l'élève PlayEnd

Merci de faire tourner ce kit. Il fait trois calculs que l'ordinateur de Brummel ne peut pas faire :

1. **gru** : réentraîner les détecteurs de fin de partie (GRU, gradient boosting, régression logistique) sur les
   observations produites par l'élève, avec le même protocole que le calcul du 6 octobre (sur le processeur) ;
2. **lora** : entraîner un adaptateur LoRA pour le petit modèle de vision LFM2.5-VL-450M (sur la carte graphique
   Intel Arc si PyTorch la reconnaît, sinon sur le processeur), puis le convertir pour llama.cpp ;
3. **vlm** : faire lire au modèle, avec et sans LoRA, les images de test (sur la carte graphique, par Vulkan).

## Ce qu'il faut

- Windows 11 ou Linux, processeur 64 bits, environ 15 Go libres.
- Python 3.10 ou plus récent (python.org). Si `install` annonce « PyTorch on cpu » alors que l'ordinateur a une
  carte Intel Arc, mettre à jour le pilote graphique Intel (intel.com) puis relancer `python launch.py install`.
- Une connexion internet pour l'installation : environ 3 à 4 Go à télécharger (PyTorch, llama.cpp, le modèle).
- Brancher l'ordinateur sur le secteur et désactiver la mise en veille pendant le calcul.

## Les commandes

Ouvrir un terminal (PowerShell) dans ce dossier, puis :

```text
python launch.py install    installation (30 à 60 minutes selon la connexion)
python launch.py check      tout en petit, environ 20 minutes : vérifie que chaque étape marche
python launch.py all        le calcul complet, de 15 à 24 heures, puis le fichier de résultats
```

Si une commande s'arrête (coupure, erreur, ordinateur éteint), relancer **la même commande** : elle reprend où elle en
était. Si `check` échoue, envoyer à Brummel le message affiché et le dossier `results/` (ou lancer
`python launch.py pack`, qui en fait un zip).

On peut aussi lancer les étapes une par une : `python launch.py gru`, `python launch.py lora`, `python launch.py vlm`,
puis `python launch.py pack`.

## Ce qu'il faut rapporter

À la fin, la commande affiche deux fichiers à copier sur la clé USB :

- `playend_eleve_resultats_<date>.zip` : les résultats (quelques dizaines de Mo) ;
- `models/lora_final-Q4_0.gguf` : le modèle adapté par LoRA sur toutes les images (environ 250 Mo), pour
  l'essayer sur le Raspberry Pi.

## Les données

Le dossier `data/` contient des observations pseudonymisées et des morceaux de captures d'écran de jeux (les zones du
tableau de score). Elles servent seulement à ce calcul : merci de ne pas les partager et de supprimer le dossier une
fois les résultats rapportés.
