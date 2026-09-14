#!/usr/bin/env bash
# setup.sh — Instalación de dependencias de la skill shorts-virales-ia.
# Idempotente y tolerante a fallos de red: si una descarga falla, avisa y continúa.
#
# Uso:
#   bash scripts/setup.sh              # instalación estándar
#   bash scripts/setup.sh --con-fondo  # añade rembg[cpu] + onnxruntime (quitar fondo con IA)
#   bash scripts/setup.sh --help

set -u

# ---------------------------------------------------------------- utilidades
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FONTS_DIR="$SKILL_DIR/assets/fonts"
EMOJI_DIR="$SKILL_DIR/assets/emoji"
SFX_DIR="$SKILL_DIR/assets/sfx"
VENV_DIR="$SKILL_DIR/.venv"

OK=()      # qué quedó listo
FALLOS=()  # qué falló (para el resumen final)

info()  { printf '\033[1;34m[setup]\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m[aviso]\033[0m %s\n' "$*" >&2; }
error() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; }

ayuda() {
  cat <<'EOF'
setup.sh — prepara todo lo que necesita la skill shorts-virales-ia.

Hace, en orden:
  1. Verifica ffmpeg y ffprobe (con instrucciones de instalación si faltan).
  2. Crea el venv .venv/ e instala whisper (mlx-whisper en Apple Silicon,
     faster-whisper en el resto) + playwright con chromium.
  3. Descarga fuentes libres (OFL/Google Fonts) a assets/fonts/.
  4. Descarga ~40 emojis Twemoji a assets/emoji/.
  5. Genera la librería de SFX sintéticos en assets/sfx/ (scripts/gen_sfx.sh).
  6. Imprime un resumen de lo instalado y lo que falló.

Opciones:
  --con-fondo   Instala también rembg[cpu] + onnxruntime (quitar fondo con IA).
  -h, --help    Muestra esta ayuda.

Es idempotente: lo ya instalado/descargado se omite. Si una descarga falla
(red caída, etc.) avisa y continúa; vuelve a correr el script para reintentarlo.
EOF
}

CON_FONDO=0
for arg in "$@"; do
  case "$arg" in
    --con-fondo) CON_FONDO=1 ;;
    -h|--help) ayuda; exit 0 ;;
    *) error "Opción desconocida: $arg (usa --help)"; exit 2 ;;
  esac
done

# Descarga con curl (sin globbing: hay URLs con corchetes) y 1 reintento.
# Omite si el destino ya existe y no está vacío. Registra éxito/fallo.
descargar() { # $1=url  $2=destino  $3=etiqueta
  local url="$1" destino="$2" etiqueta="$3"
  if [ -s "$destino" ]; then
    return 0
  fi
  if curl -fsSL -g --retry 1 --connect-timeout 15 -o "$destino.tmp" "$url" \
     && [ -s "$destino.tmp" ]; then
    mv "$destino.tmp" "$destino"
    return 0
  fi
  rm -f "$destino.tmp"
  warn "No se pudo descargar: $etiqueta ($url)"
  FALLOS+=("$etiqueta")
  return 1
}

# ------------------------------------------------------- 1. ffmpeg / ffprobe
info "1/6 · Verificando ffmpeg y ffprobe…"
FFMPEG_OK=1
for bin in ffmpeg ffprobe; do
  if command -v "$bin" >/dev/null 2>&1; then
    info "  $bin ✓ ($(command -v "$bin"))"
  else
    FFMPEG_OK=0
    error "  $bin no está instalado."
  fi
done
if [ "$FFMPEG_OK" -eq 1 ]; then
  OK+=("ffmpeg + ffprobe")
else
  FALLOS+=("ffmpeg/ffprobe (instálalo y vuelve a correr el setup)")
  case "$(uname -s)" in
    Darwin) warn "  Instálalo con:  brew install ffmpeg" ;;
    Linux)  warn "  Instálalo con:  sudo apt update && sudo apt install -y ffmpeg" ;;
    MINGW*|MSYS*|CYGWIN*) warn "  Instálalo con:  choco install ffmpeg  (o winget install ffmpeg)" ;;
    *) warn "  Instala ffmpeg desde https://ffmpeg.org/download.html" ;;
  esac
  warn "  El setup continúa, pero la skill no puede renderizar sin ffmpeg."
fi

# --------------------------------------------------------- 2. venv de Python
info "2/6 · Preparando entorno de Python en .venv/…"
PY_OK=0
if command -v python3 >/dev/null 2>&1; then
  if [ ! -x "$VENV_DIR/bin/python" ]; then
    python3 -m venv "$VENV_DIR" || true
  fi
  if [ -x "$VENV_DIR/bin/python" ]; then
    PY_OK=1
  else
    error "  No se pudo crear el venv en .venv/."
    FALLOS+=("venv de Python")
  fi
else
  error "  python3 no está instalado (se requiere Python 3.9+)."
  FALLOS+=("python3 (instálalo y vuelve a correr el setup)")
fi

pip_install() { # $1=etiqueta  $2…=paquetes
  local etiqueta="$1"; shift
  if "$VENV_DIR/bin/python" -m pip install --quiet --upgrade "$@"; then
    OK+=("$etiqueta")
  else
    warn "  Falló la instalación de: $etiqueta"
    FALLOS+=("$etiqueta")
  fi
}

if [ "$PY_OK" -eq 1 ]; then
  "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip || warn "  No se pudo actualizar pip (continuando)."

  if [ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
    info "  Apple Silicon detectado → instalando mlx-whisper…"
    pip_install "mlx-whisper" mlx-whisper
  else
    info "  Instalando faster-whisper…"
    pip_install "faster-whisper" faster-whisper
  fi

  info "  Instalando playwright…"
  pip_install "playwright" playwright
  if [ -x "$VENV_DIR/bin/playwright" ]; then
    info "  Descargando navegador chromium para playwright…"
    if "$VENV_DIR/bin/playwright" install chromium; then
      OK+=("chromium (playwright)")
    else
      warn "  Falló 'playwright install chromium' (¿red?). Reintenta luego con: .venv/bin/playwright install chromium"
      FALLOS+=("chromium (playwright)")
    fi
  fi

  if [ "$CON_FONDO" -eq 1 ]; then
    info "  --con-fondo → instalando rembg[cpu] + onnxruntime (puede tardar)…"
    pip_install "rembg[cpu] + onnxruntime" "rembg[cpu]" onnxruntime
  else
    info "  (Opcional) Para quitar fondos con IA, vuelve a correr con --con-fondo."
  fi
else
  warn "  Sin venv: se omite la instalación de paquetes de Python."
fi

# ------------------------------------------------------------- 3. fuentes
info "3/6 · Descargando fuentes libres (OFL/Apache) a assets/fonts/…"
mkdir -p "$FONTS_DIR"
GF="https://github.com/google/fonts/raw/main"
FUENTES="
Anton-Regular.ttf|$GF/ofl/anton/Anton-Regular.ttf
Bangers-Regular.ttf|$GF/ofl/bangers/Bangers-Regular.ttf
LuckiestGuy-Regular.ttf|$GF/apache/luckiestguy/LuckiestGuy-Regular.ttf
ArchivoBlack-Regular.ttf|$GF/ofl/archivoblack/ArchivoBlack-Regular.ttf
BebasNeue-Regular.ttf|$GF/ofl/bebasneue/BebasNeue-Regular.ttf
Oswald.ttf|$GF/ofl/oswald/Oswald%5Bwght%5D.ttf
PermanentMarker-Regular.ttf|$GF/apache/permanentmarker/PermanentMarker-Regular.ttf
LilitaOne-Regular.ttf|$GF/ofl/lilitaone/LilitaOne-Regular.ttf
RussoOne-Regular.ttf|$GF/ofl/russoone/RussoOne-Regular.ttf
AlfaSlabOne-Regular.ttf|$GF/ofl/alfaslabone/AlfaSlabOne-Regular.ttf
Montserrat.ttf|$GF/ofl/montserrat/Montserrat%5Bwght%5D.ttf
Poppins-Black.ttf|$GF/ofl/poppins/Poppins-Black.ttf
Poppins-Bold.ttf|$GF/ofl/poppins/Poppins-Bold.ttf
"
FUENTES_OK=0
FUENTES_TOTAL=0
while IFS='|' read -r archivo url; do
  [ -z "$archivo" ] && continue
  FUENTES_TOTAL=$((FUENTES_TOTAL + 1))
  descargar "$url" "$FONTS_DIR/$archivo" "fuente $archivo" && FUENTES_OK=$((FUENTES_OK + 1))
done <<EOF
$FUENTES
EOF
info "  Fuentes listas: $FUENTES_OK/$FUENTES_TOTAL"
[ "$FUENTES_OK" -gt 0 ] && OK+=("fuentes ($FUENTES_OK/$FUENTES_TOTAL)")

# --------------------------------------------------------------- 4. emojis
info "4/6 · Descargando emojis Twemoji a assets/emoji/…"
mkdir -p "$EMOJI_DIR"
TW="https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72"
EMOJIS="
fire|1f525 moneybag|1f4b0 check|2705 cross|274c rocket|1f680 brain|1f9e0
eyes|1f440 point-down|1f447 point-right|1f449 warning|26a0 bulb|1f4a1
chart-up|1f4c8 chart-down|1f4c9 money-fly|1f4b8 dollar|1f4b5 clock|23f0
hourglass|23f3 lock|1f512 key|1f511 gift|1f381 trophy|1f3c6 medal|1f947
star|2b50 sparkles|2728 boom|1f4a5 lightning|26a1 gem|1f48e crown|1f451
target|1f3af muscle|1f4aa handshake|1f91d clap|1f44f thumbsup|1f44d
mind-blown|1f92f thinking|1f914 shush|1f92b siren|1f6a8 bell|1f514
megaphone|1f4e3 phone|1f4f1
"
EMOJIS_OK=0
EMOJIS_TOTAL=0
for par in $EMOJIS; do
  nombre="${par%%|*}"
  hex="${par##*|}"
  EMOJIS_TOTAL=$((EMOJIS_TOTAL + 1))
  descargar "$TW/$hex.png" "$EMOJI_DIR/$nombre.png" "emoji $nombre" && EMOJIS_OK=$((EMOJIS_OK + 1))
done
info "  Emojis listos: $EMOJIS_OK/$EMOJIS_TOTAL"
[ "$EMOJIS_OK" -gt 0 ] && OK+=("emojis Twemoji ($EMOJIS_OK/$EMOJIS_TOTAL)")

# ------------------------------------------------------------------ 5. SFX
info "5/6 · Generando librería de SFX sintéticos en assets/sfx/…"
mkdir -p "$SFX_DIR"
if [ ! -f "$SKILL_DIR/scripts/gen_sfx.sh" ]; then
  warn "  scripts/gen_sfx.sh no existe todavía; se omite la generación de SFX."
  FALLOS+=("SFX (falta scripts/gen_sfx.sh)")
elif [ "$FFMPEG_OK" -ne 1 ]; then
  warn "  Sin ffmpeg no se pueden generar los SFX; instala ffmpeg y reintenta."
  FALLOS+=("SFX (requiere ffmpeg)")
elif bash "$SKILL_DIR/scripts/gen_sfx.sh" "$SFX_DIR"; then
  OK+=("SFX sintéticos ($(ls "$SFX_DIR" 2>/dev/null | wc -l | tr -d ' ') archivos)")
else
  warn "  gen_sfx.sh terminó con errores; revisa su salida."
  FALLOS+=("SFX (gen_sfx.sh falló)")
fi

# --------------------------------------------------------------- 6. resumen
info "6/6 · Resumen"
echo
echo "══════════════════════ RESUMEN DEL SETUP ══════════════════════"
if [ "${#OK[@]}" -gt 0 ]; then
  echo "Listo:"
  for item in "${OK[@]}"; do echo "  ✓ $item"; done
fi
if [ "${#FALLOS[@]}" -gt 0 ]; then
  echo "Falló (vuelve a correr el setup para reintentar):"
  for item in "${FALLOS[@]}"; do echo "  ✗ $item"; done
  echo "═══════════════════════════════════════════════════════════════"
  exit 1
fi
echo "Todo listo. Activa el entorno con:  source .venv/bin/activate"
echo "═══════════════════════════════════════════════════════════════"
exit 0
