#!/usr/bin/env python3
"""Sur le Raspberry : sudo python3 mode.py collecte|compteur. Données préservées."""
import argparse
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("mode", choices=("collecte", "compteur"))
args = parser.parse_args()
if os.geteuid() != 0:
    parser.error("Exécuter avec sudo sur le Raspberry")
if not Path('/home/brummel/Desktop/Capture-dataset-jeux/capture.py').exists():
    parser.error("Cet outil doit être exécuté sur le Raspberry installé")
marker = Path('/etc/capture-dataset-mode')


def ctl(*args):
    subprocess.run(['systemctl', *args], check=True)


if args.mode == "collecte":
    marker.touch(mode=0o644)
    ctl('stop', 'compteur-boot.service')
    ctl('stop', 'compteur.service')
    ctl('reset-failed', 'capture-dataset-jeux.service')
    ctl('enable', '--now', 'capture-dataset-jeux.service')
else:
    ctl('disable', '--now', 'capture-dataset-jeux.service')
    marker.unlink(missing_ok=True)
    ctl('start', 'compteur-boot.service')
print('Mode actif :', args.mode)
