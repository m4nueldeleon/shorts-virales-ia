#!/usr/bin/env bash
# gen_sfx.sh — genera la librería completa de SFX sintéticos con ffmpeg puro (lavfi).
#
# Uso: ./gen_sfx.sh [dir_salida]
#   dir_salida  Carpeta destino (por defecto: assets/sfx de la skill).
#
# 48 kHz estéreo, picos consistentes ~-3 dB (alimiter). Sin descargas ni
# dependencias extra: todo se sintetiza con fuentes lavfi de ffmpeg.
set -euo pipefail

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg no encontrado. Corre: bash scripts/setup.sh" >&2
  exit 1
fi

DIR_SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR_SALIDA="${1:-$DIR_SKILL/assets/sfx}"
mkdir -p "$DIR_SALIDA"

SR=48000
GENERADOS=()
FALLIDOS=()

# gen <nombre> <grafo lavfi con la cadena final abierta>
# A cada grafo se le añade: formato 48 kHz estéreo + limitador con techo -3 dB.
# Cada sonido se diseña "caliente" para que el limitador iguale los picos.
gen() {
  local nombre="$1" grafo="$2"
  if ffmpeg -y -hide_banner -loglevel error \
       -filter_complex "${grafo},aformat=sample_rates=${SR}:channel_layouts=stereo,alimiter=limit=0.708:level=false[out]" \
       -map "[out]" "$DIR_SALIDA/$nombre.wav" 2>&1; then
    GENERADOS+=("$nombre.wav")
  else
    echo "  ✗ falló: $nombre" >&2
    FALLIDOS+=("$nombre")
  fi
}

echo "Generando SFX sintéticos en: $DIR_SALIDA"

# --- Whooshes: ruido rosa + bandpass + flanger (duraciones distintas) --------
gen whoosh_1 "anoisesrc=color=pink:r=${SR}:a=0.9:d=0.7,bandpass=f=800:t=h:w=600,flanger=delay=4:depth=6:speed=0.6,afade=t=in:d=0.28,afade=t=out:st=0.32:d=0.38,volume=10"
gen whoosh_2 "anoisesrc=color=pink:r=${SR}:a=0.9:d=1.1,bandpass=f=450:t=h:w=400,flanger=delay=6:depth=8:speed=0.4,afade=t=in:d=0.45,afade=t=out:st=0.5:d=0.6,volume=12"
gen transition_swish "anoisesrc=color=pink:r=${SR}:a=0.9:d=0.4,bandpass=f=1600:t=h:w=1000,flanger=delay=2:depth=4:speed=1.2,afade=t=in:d=0.12,afade=t=out:st=0.16:d=0.24,volume=10"

# --- Risers: barrido de frecuencia ascendente + crescendo --------------------
gen riser_corto "aevalsrc=(0.15+0.85*(t/2)*(t/2))*sin(2*PI*t*(150+187.5*t)):d=2:s=${SR}[rc1];anoisesrc=color=pink:r=${SR}:a=0.5:d=2,bandpass=f=1200:t=h:w=900,afade=t=in:d=1.8[rc2];[rc1][rc2]amix=inputs=2:normalize=0,afade=t=out:st=1.9:d=0.1,volume=1.3"
gen riser_largo "aevalsrc=(0.1+0.9*(t/4)*(t/4))*sin(2*PI*t*(100+112.5*t)):d=4:s=${SR}[rl1];anoisesrc=color=pink:r=${SR}:a=0.5:d=4,bandpass=f=1000:t=h:w=800,afade=t=in:d=3.6[rl2];[rl1][rl2]amix=inputs=2:normalize=0,afade=t=out:st=3.85:d=0.15,volume=1.3"

# --- Impactos ----------------------------------------------------------------
# impact_boom: seno grave 52 Hz decayendo + golpe de ruido + reverb (aecho)
gen impact_boom "aevalsrc=exp(-2.5*t)*sin(2*PI*52*t):d=1.6:s=${SR},volume=1.6[grave];anoisesrc=color=white:r=${SR}:a=0.8:d=1.6,lowpass=f=500,afade=t=out:st=0:d=0.22[golpe];[grave][golpe]amix=inputs=2:normalize=0,aecho=0.8:0.55:40|90:0.4|0.25,bass=g=6:f=80,afade=t=out:st=1.2:d=0.4,volume=1.5"
# stamp: golpe seco (cuerpo grave + textura de ruido, sin reverb)
gen stamp "aevalsrc=exp(-18*t)*sin(2*PI*130*t):d=0.3:s=${SR},volume=1.5[cuerpo];anoisesrc=color=white:r=${SR}:a=0.9:d=0.3,lowpass=f=900,afade=t=out:st=0:d=0.08[textura];[cuerpo][textura]amix=inputs=2:normalize=0,volume=1.5"

# --- Cortos: apariciones de texto / UI ---------------------------------------
gen pop "aevalsrc=0.9*exp(-28*t)*sin(2*PI*320*t):d=0.18:s=${SR},highpass=f=120,volume=1.3"
gen click "anoisesrc=color=white:r=${SR}:a=0.9:d=0.06,highpass=f=2500,afade=t=out:st=0.01:d=0.05,volume=3"

# --- Feedback: acierto / error -----------------------------------------------
# correct: 2 notas ascendentes (C5 → G5)
gen correct "aevalsrc=0.95*sin(2*PI*523.25*t):d=0.16:s=${SR},afade=t=in:d=0.008,afade=t=out:st=0.1:d=0.06[c1];aevalsrc=0.95*sin(2*PI*783.99*t):d=0.32:s=${SR},afade=t=in:d=0.008,afade=t=out:st=0.18:d=0.14[c2];[c1][c2]concat=n=2:v=0:a=1,volume=1.25"
# wrong: buzz cuadrado descendente (170 → 110 Hz)
gen wrong "aevalsrc=0.6*(2*gt(sin(2*PI*t*(170-60*t))\,0)-1):d=0.6:s=${SR},lowpass=f=1500,afade=t=out:st=0.45:d=0.15,volume=1.8"

# --- Notificaciones / recompensas --------------------------------------------
# notification: campanita de 2 tonos (A5 → D6) con cola de eco
gen notification "aevalsrc=exp(-5*t)*sin(2*PI*880*t):d=0.35:s=${SR}[t1];aevalsrc=exp(-5*t)*sin(2*PI*1174.66*t):d=0.6:s=${SR}[t2];[t1][t2]concat=n=2:v=0:a=1,apad=pad_dur=0.3,aecho=0.6:0.4:90:0.3,afade=t=out:st=0.95:d=0.3,volume=4"
# coin: 988 Hz → 1319 Hz rápido (estilo videojuego)
gen coin "aevalsrc=0.95*sin(2*PI*988*t):d=0.085:s=${SR},afade=t=in:d=0.004[m1];aevalsrc=exp(-6*t)*sin(2*PI*1319*t):d=0.5:s=${SR}[m2];[m1][m2]concat=n=2:v=0:a=1,volume=1.2"
# win: arpegio 4 notas (C5-E5-G5-C6) + eco
gen win "aevalsrc=0.95*sin(2*PI*523.25*t):d=0.14:s=${SR},afade=t=in:d=0.008,afade=t=out:st=0.09:d=0.05[w1];aevalsrc=0.95*sin(2*PI*659.25*t):d=0.14:s=${SR},afade=t=in:d=0.008,afade=t=out:st=0.09:d=0.05[w2];aevalsrc=0.95*sin(2*PI*783.99*t):d=0.14:s=${SR},afade=t=in:d=0.008,afade=t=out:st=0.09:d=0.05[w3];aevalsrc=0.95*sin(2*PI*1046.5*t):d=0.4:s=${SR},afade=t=in:d=0.008,afade=t=out:st=0.2:d=0.2[w4];[w1][w2][w3][w4]concat=n=4:v=0:a=1,apad=pad_dur=0.5,aecho=0.7:0.5:120:0.35,afade=t=out:st=1.0:d=0.3,volume=2.4"

# --- Tensión -----------------------------------------------------------------
# drumroll: ruido rosa con gate rápido (tremolo 15 Hz), 2 s
gen drumroll "anoisesrc=color=pink:r=${SR}:a=0.9:d=2,highpass=f=200,lowpass=f=2500,tremolo=f=15:d=0.95,afade=t=in:d=0.1,afade=t=out:st=1.85:d=0.15,volume=4"

# --- Resumen -----------------------------------------------------------------
echo ""
echo "SFX generados (${#GENERADOS[@]}):"
if [ ${#GENERADOS[@]} -gt 0 ]; then
  for f in "${GENERADOS[@]}"; do
    d=""
    if command -v ffprobe >/dev/null 2>&1; then
      d="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$DIR_SALIDA/$f" 2>/dev/null || true)"
    fi
    case "$d" in
      "") printf '  %s\n' "$f" ;;
      *)  LC_ALL=C printf '  %-24s %.2f s\n' "$f" "$d" ;;
    esac
  done
fi
if [ ${#FALLIDOS[@]} -gt 0 ]; then
  echo ""
  echo "ADVERTENCIA — fallaron: ${FALLIDOS[*]:-}" >&2
  exit 1
fi
echo "Listo → $DIR_SALIDA"
