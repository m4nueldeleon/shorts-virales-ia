#!/usr/bin/env bash
# Instalador de la skill Shorts Virales IA para Claude Code.
# Uso: curl -fsSL https://raw.githubusercontent.com/m4nueldeleon/shorts-virales-ia/main/install.sh | bash
set -euo pipefail

DESTINO="$HOME/.claude/skills/shorts-virales-ia"
REPO_URL="https://github.com/m4nueldeleon/shorts-virales-ia.git"

echo "🎬 Instalando Shorts Virales IA…"

if ! command -v git >/dev/null 2>&1; then
  echo "❌ Falta git. Instálalo primero:"
  echo "   Mac:    xcode-select --install"
  echo "   Ubuntu: sudo apt install git"
  exit 1
fi

if [ -d "$DESTINO/.git" ]; then
  echo "↻ Ya existe una instalación — actualizando…"
  git -C "$DESTINO" pull --ff-only
else
  mkdir -p "$HOME/.claude/skills"
  git clone --depth 1 "$REPO_URL" "$DESTINO"
fi

echo ""
echo "📦 Preparando dependencias y materiales (puede tardar unos minutos)…"
bash "$DESTINO/scripts/setup.sh" || {
  echo "⚠️  El setup reportó pendientes. Revisa los mensajes de arriba,"
  echo "    resuelve lo que falte y vuelve a correr: bash $DESTINO/scripts/setup.sh"
}

echo ""
echo "✅ Skill instalada en: $DESTINO"
echo ""
echo "Cómo usarla:"
echo "  1. Abre una terminal en la carpeta donde está tu video"
echo "  2. Escribe: claude"
echo "  3. Dile:    Edita mi video crudo.mp4 y hazlo viral"
