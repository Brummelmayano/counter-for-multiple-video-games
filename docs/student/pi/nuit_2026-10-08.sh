#!/bin/bash
# Night of 2026-10-08 on the Raspberry Pi Zero 2 W: the whole student loop, from the capture to the count
# (python -m playend.student.loop run), on four PlayEnd sessions read in order: 2,341 captures, 152 ends.
#
# Installed on the card as /home/brummel/mesures_eleve/scripts/programme.sh, which mesures-eleve.service starts at
# boot (the night of 2026-10-07 is kept as programme_nuit_2026-10-07.sh, its results in /home/brummel/eleve/resultats/).
# The folder made by `playend.student.loop prepare` is /home/brummel/eleve/boucle/. Every capture read is kept in
# resultats_boucle/, so a power cut loses only the capture in progress. Once resultats_boucle/FIN exists the program
# does nothing; at the end it shuts the Pi down.
E=/home/brummel/eleve
M=/home/brummel/mesures_eleve
cd "$E" || exit 1
R=resultats_boucle
mkdir -p $R
LOG=$R/programme.log
[ -f $R/FIN ] && exit 0
log() { echo "$(date '+%F %T') $*" >> "$LOG"; }
[ -f $R/deadline ] || echo $(($(date +%s) + 36000)) > $R/deadline
DEADLINE=$(cat $R/deadline)
log "start; deadline $(date -d "@$DEADLINE" '+%F %T')"

sudo -n systemctl stop lightdm cups cups-browsed ModemManager bluetooth 2> /dev/null
# No battery clock and no network: keep the clock file systemd restores at boot close to the real time.
(while true; do sudo -n touch /var/lib/systemd/timesync/clock 2> /dev/null; sleep 300; done) &

PY=$M/specialise/venv/bin/python
export PYTHONPATH=$E/src
left() { echo $((DEADLINE - $(date +%s))); }

# Started again if it stops before the end (a process killed for lack of memory): it goes on from its records.
for attempt in 1 2 3 4 5; do
    [ "$(left)" -gt 0 ] || break
    log "loop, attempt $attempt"
    timeout "$(left)" $PY -m playend.student.loop run boucle --out $R/boucle >> "$LOG" 2>&1
    status=$?
    log "loop exit $status"
    [ $status -eq 0 ] && break
    sleep 30
done
sync
log "end; shutting down"
touch $R/FIN
sync
sudo -n poweroff
