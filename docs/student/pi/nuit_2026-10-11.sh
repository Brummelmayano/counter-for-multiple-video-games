#!/bin/bash
# Night of 2026-10-11 on the Raspberry Pi Zero 2 W: the time of LFM2.5-VL-450M adapted by LoRA (the final adapter of the
# friend's kit, merged and quantized to Q4_0), on the 216 gameplay captures of the night of 2026-10-07.
#
# Installed on the card as /home/brummel/mesures_eleve/scripts/programme.sh, which mesures-eleve.service starts at
# boot (the night of 2026-10-08 is kept as programme_nuit_2026-10-08.sh). Every capture read is kept in
# /home/brummel/eleve/resultats_lora/, so a power cut loses only the capture in progress. Once resultats_lora/FIN
# exists the program does nothing; at the end it shuts the Pi down.
#   1. without the grammar, which the adapter no longer needs;
#   2. with the grammar, as the base model was measured on 2026-10-07 (46.9 s per image).
# The final adapter was trained on every PlayEnd capture, these ones included: this night measures time, not accuracy.
E=/home/brummel/eleve
M=/home/brummel/mesures_eleve
cd "$E" || exit 1
R=resultats_lora
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
VLM=(--llama $M/llama.cpp-0.6.0/build/bin/llama-mtmd-cli
     --model $M/modeles/lfm25_vl_450m/lora_final-Q4_0.gguf
     --mmproj $M/modeles/lfm25_vl_450m/mmproj-LFM2.5-VL-450m-Q8_0.gguf)

# Each run goes on from its records if it stops before the end (a process killed for lack of memory).
for run in sans_grammaire avec_grammaire; do
    flag=$([ $run = sans_grammaire ] && echo --no-grammar)
    for attempt in 1 2 3; do
        [ "$(left)" -gt 0 ] || break
        log "$run, attempt $attempt"
        timeout "$(left)" $PY -m playend.student.run vlm echantillon/frames.json --out $R/$run "${VLM[@]}" $flag \
            >> "$LOG" 2>&1
        status=$?
        log "$run exit $status"
        [ $status -eq 0 ] && break
        sleep 30
    done
done
sync
log "end; shutting down"
touch $R/FIN
sync
sudo -n poweroff
