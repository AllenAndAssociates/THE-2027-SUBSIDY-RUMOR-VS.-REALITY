#!/usr/bin/env bash
# Builds the full 4:38 16:9 video (1920x1080, 25 fps) with USAFacts-style motion graphics in the
# Allen & Associates brand colours.
#
#   0. narration track (assets/audio/voice_full.wav) is cut from the source video if missing
#   1. tools/gen_scenes.py writes compositions/shot01-33.html, index.html and the chapter tabs
#      (Shots 34-37 are hand-authored in compositions/checklist.html and contact.html)
#   2. HyperFrames renders the graphics + full audio mix                       -> layer.mp4
#   3. tools/composite.py keys the presenter out of the 9:16 green-screen pillarbox and places
#      him per shot layout (large on white / in the gold ring / hidden / left third)
#
# Usage: ./build.sh [output.mp4]       (needs `git lfs pull` for the source video)
#        LAYER_IN=<file> ./build.sh    reuse an existing graphics render
set -euo pipefail
cd "$(dirname "$0")"

SRC="../Medicare Part D Changes for 2027_1080p.mp4"
OUT="${1:-../Medicare Part D Changes for 2027 - Full (16x9).mp4}"
LAYER="${LAYER_IN:-$(mktemp -d)/layer.mp4}"

if [ ! -f assets/audio/voice_full.wav ]; then
  ffmpeg -y -loglevel error -i "$SRC" -vn \
    -af "volume=11dB,alimiter=limit=0.84:attack=3:release=60:level=disabled,apad=pad_dur=1.2,aresample=48000" \
    -ac 2 -t 279.44 assets/audio/voice_full.wav
fi

python3 tools/gen_scenes.py

if [ -z "${LAYER_IN:-}" ] || [ ! -f "$LAYER" ]; then
  npx --yes hyperframes@0.9.39 render --fps 25 -q high -w 3 -o "$LAYER"
fi

python3 tools/composite.py "$LAYER" "$SRC" "$OUT"
echo "wrote: $OUT"
