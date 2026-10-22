#!/bin/bash
# The pipelines the Raspberry Pi Zero 2 W could run, on the two held-out sessions (871 captures), with the frozen
# system (docs/counting/SESSIONS_INEDITES.md); playend.counting.pipelines describes them (A to D).
#   1. A: classifier + OCR + start rules, every capture, as on the PC (python -m playend.counting.heldout).
#   2. A few of C's captures read by llama-mtmd-cli, the way the VLM with LoRA was measured on 2026-10-10 and 11.
#   3. C: the VLM with LoRA on every gameplay capture of A, through llama-server, which keeps the model loaded.
#   4. The OCR reading captures while the server works: time and memory of the two together (pipeline D).
#   5. B: features, game state, gradient boosting and GRU with NumPy, capture by capture.
# Every step keeps one record per capture and starts again from them after a power cut; a step done leaves
# resultats/fait_<step>. The kit is copied into /home/brummel/debuts/ with the layout of the repository (from the PC,
# on the card, on 2026-10-15). Installed as /home/brummel/mesures_eleve/scripts/programme.sh, which
# mesures-eleve.service starts at boot. Once resultats/FIN exists the program does nothing; at the end it shuts the Pi
# down. The 14-hour budget counts the minutes the program has run, kept in resultats/temps_passe: the Pi has no battery
# clock, and its date can jump by days between two boots (a deadline in clock time ended the run of 2026-10-15).
D=/home/brummel/debuts
M=/home/brummel/mesures_eleve
cd "$D" || exit 1
R=resultats
mkdir -p $R
LOG=$R/programme.log
[ -f $R/FIN ] && exit 0
log() { echo "$(date '+%F %T') $*" >> "$LOG"; }
BUDGET=50400
spent() { value=$(cat $R/temps_passe 2> /dev/null); echo "${value:-0}"; }
log "start; $(spent) s of the ${BUDGET} s budget already spent"
(while true; do
    sleep 60
    echo $(($(spent) + 60)) > $R/temps_passe.tmp && sync && mv $R/temps_passe.tmp $R/temps_passe
done) &

sudo -n systemctl stop lightdm cups cups-browsed ModemManager bluetooth 2> /dev/null
# No battery clock and no network: keep the clock file systemd restores at boot close to the real time.
(while true; do sudo -n touch /var/lib/systemd/timesync/clock 2> /dev/null; sleep 300; done) &

PY=$M/specialise/venv/bin/python
export PYTHONPATH=$D/src
BIN=$M/llama.cpp-0.6.0/build/bin
MODEL=$M/modeles/lfm25_vl_450m/lora_final-Q4_0.gguf
MMPROJ=$M/modeles/lfm25_vl_450m/mmproj-LFM2.5-VL-450m-Q8_0.gguf
P="$PY -m playend.counting.pipelines"
COMMON=(--out $R/pipelines --ocr $R/sessions_inedites --final $D/build/training/starts_final)
left() { echo $((BUDGET - $(spent))); }

# Runs a step until it ends well, five times at most (a process killed for lack of memory goes on from its records).
step() {
    name=$1; shift
    [ -f $R/fait_$name ] && return 0
    for attempt in 1 2 3 4 5; do
        [ "$(left)" -gt 0 ] || return 1
        log "$name, attempt $attempt"
        timeout "$(left)" "$@" >> "$LOG" 2>&1
        status=$?
        log "$name exit $status"
        [ $status -eq 0 ] && touch $R/fait_$name && sync && return 0
        sleep 30
    done
    return 1
}

server_up() {
    "$BIN/llama-server" -m "$MODEL" --mmproj "$MMPROJ" -c 4096 -t 4 --host 127.0.0.1 --port 8080 >> $R/server.log 2>&1 &
    SERVER=$!
    for i in $(seq 1 120); do
        $PY -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=5)" 2> /dev/null \
            && log "server ready (pid $SERVER)" && return 0
        sleep 5
    done
    log "server not ready"
    return 1
}

step ocr $PY -m playend.counting.heldout --out $R/sessions_inedites
step cli $P check "${COMMON[@]}" --llama "$BIN/llama-mtmd-cli" --model "$MODEL" --mmproj "$MMPROJ"
if [ ! -f $R/fait_vlm ] || [ ! -f $R/fait_ensemble ]; then
    server_up
    step vlm $P vlm "${COMMON[@]}" --server-pid $SERVER
    step ensemble $P together "${COMMON[@]}" --server-pid $SERVER
    kill $SERVER 2> /dev/null
    wait $SERVER 2> /dev/null
fi
step detecteurs $P detectors "${COMMON[@]}"
sync
log "end; shutting down"
touch $R/FIN
sync
sudo -n poweroff
