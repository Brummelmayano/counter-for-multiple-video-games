#!/usr/bin/env python3
"""Ajout hors ligne du diagnostic ; ne change pas les services existants."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path('/media/mayano/rootfs')
expected_uuid = '4aa56689-dcb4-4759-90e6-179beae559ac'
project = root/'home/brummel/Desktop/Capture-dataset-jeux'
unit_name = 'capture-dataset-diagnostic.service'
unit = root/'etc/systemd/system'/unit_name
link = root/'etc/systemd/system/multi-user.target.wants'/unit_name
if os.geteuid() != 0:
    raise SystemExit('Droits administrateur nécessaires')
if subprocess.check_output(['findmnt','-n','-o','UUID','--target',str(root)], text=True).strip() != expected_uuid:
    raise SystemExit('Carte inattendue')
if unit.exists() or link.exists() or link.is_symlink():
    raise SystemExit('Diagnostic déjà présent : aucune réécriture')
manifest = json.loads((project/'installation_manifest.json').read_text())
for name in (unit_name, 'diagnostic_boot.sh'):
    if hashlib.sha256((project/name).read_bytes()).hexdigest() != manifest['files'][name]:
        raise SystemExit('Fichier non vérifié : '+name)
try:
    with unit.open('x') as f:
        f.write((project/unit_name).read_text())
        f.flush()
        os.fsync(f.fileno())
    os.chmod(unit, 0o644)
    link.symlink_to('/etc/systemd/system/'+unit_name)
    os.sync()
except BaseException:
    link.unlink(missing_ok=True)
    unit.unlink(missing_ok=True)
    raise
print('Diagnostic activé au prochain démarrage. Collecteur et OS inchangés.')
