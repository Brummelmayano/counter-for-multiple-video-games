#!/bin/sh
# Diagnostic borné à deux journaux. Ne lance ni ne redémarre le collecteur.
set -u
cd /home/brummel/Desktop/Capture-dataset-jeux || exit 1
mkdir -p diagnostics || exit 1
if [ -f diagnostics/boot-current.log ]; then
    mv -f diagnostics/boot-current.log diagnostics/boot-previous.log || exit 1
fi
exec > diagnostics/boot-current.log 2>&1
printf 'DIAGNOSTIC_BOOT_V1\n'
date -u '+wall_utc=%Y-%m-%dT%H:%M:%SZ'
printf 'boot_id='
cat /proc/sys/kernel/random/boot_id
printf 'uptime='
cat /proc/uptime
printf '\nMode collecte :\n'
ls -l /etc/capture-dataset-mode
printf '\nMémoire disponible et swap :\n'
sed -n '/^MemTotal:/p; /^MemAvailable:/p; /^SwapTotal:/p; /^SwapFree:/p' /proc/meminfo
printf '\nContrôleurs cgroup :\n'
cat /sys/fs/cgroup/cgroup.controllers 2>/dev/null
printf '\nStockage :\n'
df -h .
printf '\nInterpréteur :\n'
/usr/bin/python3 --version
/usr/bin/sync -f diagnostics/boot-current.log

for pass in 1 2 3 4 5 6; do
    printf '\n=== État %s ===\n' "$pass"
    cat /proc/uptime
    /usr/bin/timeout 5 /usr/bin/systemctl show capture-dataset-jeux.service \
        -p LoadState -p ActiveState -p SubState -p Result -p ExecMainCode \
        -p ExecMainStatus -p NRestarts -p ConditionResult -p FragmentPath
    printf '\nSources vidéo :\n'
    ls -l /dev/video* /dev/v4l/by-id/* 2>/dev/null
    printf '\nFichiers créés :\n'
    find dataset -maxdepth 2 -type f \( -name status.json -o -name metadata.json \) -print
    printf '\nDernières traces du collecteur :\n'
    /usr/bin/timeout 5 /usr/bin/journalctl -b -u capture-dataset-jeux.service -n 40 --no-pager
    /usr/bin/sync -f diagnostics/boot-current.log
    if [ "$pass" -lt 6 ]; then sleep 15; fi
done
printf '\nDIAGNOSTIC_TERMINE\n'
/usr/bin/sync -f diagnostics/boot-current.log
