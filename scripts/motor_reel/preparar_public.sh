#!/usr/bin/env bash
# Prepara <reel>/remotion-reel/public con los recursos que usa la plantilla Remotion:
# fuentes, íconos reales (simple-icons + Lucide), SFX con los nombres que espera events.ts,
# música de fondo, grano y viñeta. Uso: bash preparar_public.sh <carpeta-del-reel>
#
# Variables opcionales:
#   SKILL_DIR  carpeta de la skill (por omisión, dos niveles arriba de este script)
#   SFX_DIR    librería de SFX propia; si no, usa los SFX sintéticos de setup.sh
#   MUSIC_BED  ruta a tu música de fondo (mp3); si no, se crea un bed silencioso y se avisa
set -euo pipefail

REEL="${1:?Uso: bash preparar_public.sh <carpeta-del-reel>}"
AQUI="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="${SKILL_DIR:-$(cd "$AQUI/../.." && pwd)}"
P="$REEL/remotion-reel/public"
mkdir -p "$P"/{fonts,icons,sfx,music,fx,broll,data}

# --- Fuentes (las descarga scripts/setup.sh) -----------------------------------------------
F="$SKILL_DIR/assets/fonts"
cp "$F/ArchivoBlack-Regular.ttf" "$F/Poppins-Black.ttf" "$P/fonts/"
if [ -f "$F/Poppins-Bold.ttf" ]; then cp "$F/Poppins-Bold.ttf" "$P/fonts/"; else cp "$F/Poppins-Black.ttf" "$P/fonts/Poppins-Bold.ttf"; fi

# --- SFX: nombre que espera events.ts : archivo de la librería sintética ------------------
S="${SFX_DIR:-$SKILL_DIR/assets/sfx}"
MAPA="whoosh.wav:transition_swish.wav
hook-hit.wav:impact_boom.wav
impact.wav:stamp.wav
suspense-hit.wav:impact_boom.wav
msg-pop.wav:notification.wav
air.wav:whoosh_1.wav
tone.wav:coin.wav
glitch-hit.wav:stamp.wav
glitch.wav:click.wav
riser.wav:riser_largo.wav
big-impact.wav:impact_boom.wav
pop.wav:pop.wav
typing.wav:click.wav
ticktock.wav:drumroll.wav
swell.wav:riser_corto.wav
correct.wav:correct.wav
confirm.wav:coin.wav
click.wav:click.wav
bell.wav:notification.wav
win.wav:win.wav"
echo "$MAPA" | while IFS=: read -r destino origen; do
  if [ -f "$S/$destino" ]; then cp "$S/$destino" "$P/sfx/$destino"   # librería propia con los mismos nombres
  else cp "$S/$origen" "$P/sfx/$destino"; fi
done

# --- Música --------------------------------------------------------------------------------
if [ -n "${MUSIC_BED:-}" ] && [ -f "$MUSIC_BED" ]; then
  cp "$MUSIC_BED" "$P/music/bed.mp3"
else
  echo "⚠️  Sin MUSIC_BED: se crea un bed silencioso. Pon tu música en public/music/bed.mp3."
  ffmpeg -v error -y -f lavfi -i anullsrc=r=48000:cl=stereo -t 180 -c:a libmp3lame -b:a 128k "$P/music/bed.mp3"
fi

# --- Grano y viñeta generados por código ------------------------------------------------------
ffmpeg -v error -y -f lavfi -i "color=gray:s=1080x1920:d=4:r=30,noise=alls=40:allf=t+u" \
  -c:v libx264 -pix_fmt yuv420p "$P/fx/film_grain.mp4"
ffmpeg -v error -y -f lavfi -i "color=black:s=1080x1920:d=1" -frames:v 1 \
  -vf "format=rgba,geq=r=0:g=0:b=0:a='255*pow(min(1\,hypot(X-540\,Y-960)/1150)\,2.4)'" "$P/fx/vignette.png"

# --- Íconos reales. Verificar RENDERIZANDO: hay íconos que dicen ser la marca y dibujan otra.
for slug in openai claude googlegemini gmail whatsapp instagram tiktok; do
  curl -fsSL -o "$P/icons/$slug.svg" "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/$slug.svg"
done
for name in timer mail send repeat ticket bookmark circle-check message-square calendar-clock clock; do
  curl -fsSL -o "$P/icons/lucide-$name.svg" "https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/$name.svg"
done
# Objetos a color (por reel): https://api.iconify.design/fluent-emoji-flat/<nombre>.svg

echo "public listo en $P — faltan base.mp4, data/timeline.json y el b-roll de tu crudo en broll/"
