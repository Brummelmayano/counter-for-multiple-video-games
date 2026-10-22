#!/usr/bin/env python3
"""Activation hors ligne, strictement limitée à la carte Raspberry inspectée."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path('/media/mayano/rootfs')
EXPECTED_UUID = '4aa56689-dcb4-4759-90e6-179beae559ac'
PROJECT = ROOT / 'home/brummel/Desktop/Capture-dataset-jeux'
SYSTEMD = ROOT / 'etc/systemd/system'
BACKUP = ROOT / 'var/lib/capture-dataset-installation'
NAME = 'capture-dataset-jeux.service'
MARKER = ROOT / 'etc/capture-dataset-mode'
DROPIN = '[Unit]\nConditionPathExists=!/etc/capture-dataset-mode\n'


def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main():
    if os.geteuid() != 0:
        raise RuntimeError('Authentification administrateur requise pour les fichiers systemd de la carte')
    if ROOT.resolve() != ROOT or os.stat(ROOT).st_dev == os.stat('/').st_dev:
        raise RuntimeError('La cible ne correspond pas à un montage distinct')
    found = subprocess.check_output(['findmnt','-n','-o','UUID','--target',str(ROOT)], text=True).strip()
    if found != EXPECTED_UUID:
        raise RuntimeError('UUID inattendu ; aucune modification effectuée')
    if 'brummel:x:1000:1000:' not in (ROOT/'etc/passwd').read_text():
        raise RuntimeError('Utilisateur cible inattendu')
    manifest = json.loads((PROJECT/'installation_manifest.json').read_text())
    for name, expected in manifest['files'].items():
        path = PROJECT / name
        if path.is_symlink() or not path.resolve().is_relative_to(PROJECT) or digest(path) != expected:
            raise RuntimeError('Projet modifié ou incomplet : '+name)
    unit = SYSTEMD/NAME
    enabled = SYSTEMD/'multi-user.target.wants'/NAME
    drops = [SYSTEMD/(name+'.d')/'90-capture-dataset.conf' for name in ('compteur-boot.service','compteur.service')]
    changes = [unit, enabled, *drops, MARKER]
    if BACKUP.exists() or any(p.exists() or p.is_symlink() for p in changes):
        raise RuntimeError('Installation déjà présente ou conflit ; aucune réécriture automatique')
    BACKUP.mkdir(mode=0o755)
    original = {}
    for relative in ['etc/fstab','etc/rc.local','etc/os-release',
                     'etc/systemd/system/compteur-boot.service',
                     'etc/systemd/system/compteur-cluster.service','etc/systemd/system/compteur.service']:
        source = ROOT/relative
        original[relative] = digest(source)
        dest = BACKUP/'originals'/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    links = {p.name: os.readlink(p) for p in (SYSTEMD/'multi-user.target.wants').iterdir() if p.is_symlink()}
    record = {'installed_epoch': time.time(), 'root_uuid': EXPECTED_UUID,
              'original_hashes': original, 'previous_boot_links': links,
              'project_manifest': manifest, 'added_files': [str(p.relative_to(ROOT)) for p in changes]}
    (BACKUP/'before.json').write_text(json.dumps(record, indent=2)+'\n')
    created = []
    try:
        with unit.open('x') as f:
            created.append(unit)
            f.write((PROJECT/NAME).read_text())
        for path in drops:
            path.parent.mkdir(exist_ok=True)
            with path.open('x') as f:
                created.append(path)
                f.write(DROPIN)
        with MARKER.open('x') as f:
            created.append(MARKER)
            f.write('Collecte active ; retour : sudo python3 /home/brummel/Desktop/Capture-dataset-jeux/mode.py compteur\n')
        enabled.symlink_to('/etc/systemd/system/'+NAME)
        created.append(enabled)
        for relative, expected in original.items():
            if digest(ROOT/relative) != expected:
                raise RuntimeError('Un fichier original a changé : '+relative)
        for name, expected in links.items():
            if os.readlink(SYSTEMD/'multi-user.target.wants'/name) != expected:
                raise RuntimeError('Un lien original a changé : '+name)
        for path in created:
            if not path.is_symlink():
                os.chmod(path, 0o644)
                with path.open('rb') as f:
                    os.fsync(f.fileno())
        os.sync()
        (BACKUP/'complete.json').write_text(json.dumps({**record, 'status':'installed_offline_hardware_test_pending'}, indent=2)+'\n')
        os.sync()
    except BaseException:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        os.sync()
        raise
    print('INSTALLATION_OK : projet vérifié, service activé hors ligne, anciens fichiers et liens préservés.', flush=True)
    print('Sauvegarde : '+str(BACKUP), flush=True)


if __name__ == '__main__':
    main()
