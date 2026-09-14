#!/usr/bin/env bash
# Auditoría técnica de un render: specs, loudness, picos, re-transcripción y hoja de frames.
# Uso: bash audit.sh <video.mp4> <carpeta_salida>
set -euo pipefail

VID="$1"
OUT="$2"
PY="${WHISPER_PY:-python3}"
W="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT/frames"

echo "== specs"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels:format=duration,size,bit_rate -of default=nw=1 "$VID"

echo "== loudness (objetivo I≈-14, TP≤-1)"
ffmpeg -nostats -i "$VID" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):" | head -3

echo "== volumedetect"
ffmpeg -nostats -i "$VID" -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume"

echo "== hoja de frames (cada 2 s)"
rm -f "$OUT"/frames/*.jpg
ffmpeg -v error -i "$VID" -vf "fps=1/2,scale=216:-2" "$OUT/frames/f_%03d.jpg"
ffmpeg -v error -y -pattern_type glob -i "$OUT/frames/f_*.jpg" -filter_complex "tile=10x4:padding=4" "$OUT/sheet_%02d.jpg"
ls "$OUT"/sheet_*.jpg

echo "== re-transcripción"
ffmpeg -v error -y -i "$VID" -ac 1 -ar 16000 "$OUT/final16k.wav"
"$PY" "$W/01-transcripcion/transcribe.py" "$OUT/final16k.wav" "$OUT/transcripcion_final.json" > "$OUT/transcripcion_final.txt" 2> "$OUT/transcribe.err"
cat "$OUT/transcripcion_final.txt"
