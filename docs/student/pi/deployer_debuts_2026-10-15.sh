#!/bin/bash
# Copy the start-counter kit to the Pi (ssh playend-pi, phone hotspot) and install it as the boot program.
# Run from the root of the repository. The copy keeps the repository layout, so playend finds its files as on the PC.
set -e
DEST=playend-pi:/home/brummel/debuts/
S2=data/captures/session_2e4eea2021f84f46990dc9dd33695b32
S4=data/captures/session_a4ad74e68da7491aa05270e6301d76f5
rsync -aR --info=progress2 --exclude __pycache__ \
    src/playend/ \
    $S2/captures.csv $S2/images/ $S4/captures.csv $S4/images/ \
    data/evaluation/sessions_inedites/frozen.json \
    data/evaluation/sessions_inedites/session_2e4eea2021f84f46990dc9dd33695b32.json \
    data/evaluation/sessions_inedites/session_a4ad74e68da7491aa05270e6301d76f5.json \
    build/student/classifier_v1.1_cine.npz build/student/marks.npz \
    build/student/models/mobilenetv2-12.onnx build/student/models/ppocrv6_tiny_det/ build/student/models/ppocrv6_tiny_rec/ \
    build/playend_v1.1/data/observations.csv \
    "$DEST"
scp docs/student/pi/debuts_2026-10-15.sh playend-pi:/home/brummel/debuts/programme.sh
ssh playend-pi 'S=/home/brummel/mesures_eleve/scripts; cp $S/programme.sh $S/programme_nuit_2026-10-08.sh 2> /dev/null;
    cp /home/brummel/debuts/programme.sh $S/programme.sh && chmod +x $S/programme.sh && echo installed'
