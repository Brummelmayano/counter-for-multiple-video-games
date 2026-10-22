#!/bin/bash
# Night of 2026-10-07 on the Raspberry Pi Zero 2 W: the student on 236 PlayEnd captures, then a llama-server build.
#
# Installed on the card as /home/brummel/mesures_eleve/scripts/programme.sh, which mesures-eleve.service starts at
# boot (the earlier comparison is kept as programme_comparaison.sh and resultats_comparaison/). Every capture read
# is kept in /home/brummel/eleve/resultats/, so a power cut loses only the capture in progress. Once
# resultats/FIN exists the program does nothing; at the end it shuts the Pi down.
#   1. the OCR student (classifier with its vote, reading boxes, zone OCR, marks) on every capture;
#   2. LFM2.5-VL-450M with the grammar of each game on the gameplay captures (model loaded for each image);
#   3. llama-server, compiled for the next measurement: the loop with the model loaded once.
E=/home/brummel/eleve
M=/home/brummel/mesures_eleve
cd "$E" || exit 1
mkdir -p resultats
LOG=resultats/programme.log
[ -f resultats/FIN ] && exit 0
log() { echo "$(date '+%F %T') $*" >> "$LOG"; }
[ -f resultats/deadline ] || echo $(($(date +%s) + 36000)) > resultats/deadline
DEADLINE=$(cat resultats/deadline)
log "start; deadline $(date -d "@$DEADLINE" '+%F %T')"

sudo -n systemctl stop lightdm cups cups-browsed ModemManager bluetooth 2> /dev/null
# No battery clock and no network: keep the clock file systemd restores at boot close to the real time.
(while true; do sudo -n touch /var/lib/systemd/timesync/clock 2> /dev/null; sleep 300; done) &

PY=$M/specialise/venv/bin/python
export PYTHONPATH=$E/src
left() { echo $((DEADLINE - $(date +%s))); }

if [ "$(left)" -gt 0 ]; then
    log "ocr"
    timeout "$(left)" $PY -m playend.student.run ocr echantillon/frames.json --out resultats/ocr >> "$LOG" 2>&1
    log "ocr exit $?"
fi
if [ "$(left)" -gt 0 ]; then
    log "vlm"
    timeout "$(left)" $PY -m playend.student.run vlm echantillon/frames.json --out resultats/vlm \
        --llama $M/llama.cpp-0.6.0/build/bin/llama-mtmd-cli \
        --model $M/modeles/lfm25_vl_450m/LFM2.5-VL-450M-Q4_0.gguf \
        --mmproj $M/modeles/lfm25_vl_450m/mmproj-LFM2.5-VL-450m-Q8_0.gguf >> "$LOG" 2>&1
    log "vlm exit $?"
fi
if [ "$(left)" -gt 0 ] && [ ! -x $M/llama.cpp-0.6.0/build/bin/llama-server ]; then
    log "llama-server build"
    (cd $M/llama.cpp-0.6.0 && timeout "$(left)" cmake --build build --target llama-server -j1) \
        > resultats/server_build.log 2>&1
    log "llama-server build exit $?"
fi
sync
log "end; shutting down"
touch resultats/FIN
sync
sudo -n poweroff
