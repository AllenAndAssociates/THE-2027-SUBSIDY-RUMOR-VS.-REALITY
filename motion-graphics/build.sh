#!/usr/bin/env bash
# Builds the 16:9 (1920x1080, 25 fps) Shots 34-37 video.
#
#   1. HyperFrames renders the graphics + full audio mix  -> layer.mp4
#   2. ffmpeg crops Arric out of the 9:16 pillarbox in the source video, chroma-keys the
#      green screen, scales him into the left third, holds his last frame for the 1.2 s tail
#      and lays him over the graphics layer.
#
# Usage: ./build.sh [output.mp4]      (run from this folder; needs `git lfs pull` for the source)
set -euo pipefail
cd "$(dirname "$0")"

SRC="../Medicare Part D Changes for 2027_1080p.mp4"
OUT="${1:-../Medicare Part D Changes for 2027 - Shots 34-37 (16x9).mp4}"
LAYER="$(mktemp -d)/layer.mp4"

START=248.6      # source time (4:08.6) where Shot 34 begins, just before "Right now, pull out..."
DUR=30.84        # 29.64 s of footage (to the end of the source) + 1.2 s hold
HOLD=1.2

# 1. graphics + audio (narration, music, SFX are mixed by HyperFrames from assets/audio)
npx --yes hyperframes@0.9.39 render --fps 25 -q high -o "$LAYER"

# 2. key + composite
#    crop 808x1080 @ x=556  : the portrait green-screen region inside the 1920x1080 pillarbox
#    chromakey 0x08B83C     : the matte's actual green (~RGB 8,184,60), not pure 00FF00
#    scale to 972 px tall   : left third; centred on x=335, bottom-anchored (y=108)
ffmpeg -y -loglevel error -stats \
  -i "$LAYER" -ss "$START" -i "$SRC" \
  -filter_complex "
    [1:v]crop=808:1080:556:0,
         chromakey=color=0x08B83C:similarity=0.14:blend=0.07,
         despill=type=green:mix=0.6:expand=0.2,
         scale=728:972:flags=lanczos,
         tpad=stop_mode=clone:stop_duration=${HOLD}[fg];
    [0:v][fg]overlay=x=-29:y=108:eof_action=pass,format=yuv420p[v]" \
  -map "[v]" -map 0:a -t "$DUR" \
  -c:v libx264 -preset slow -crf 16 -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -af "alimiter=limit=0.891:attack=3:release=60:level=disabled" -c:a aac -b:a 192k -movflags +faststart "$OUT"

echo "wrote: $OUT"
