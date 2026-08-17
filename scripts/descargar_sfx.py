#!/usr/bin/env python3
"""Descarga efectos de sonido (SFX) gratuitos desde Mixkit a tu librería local.

Mixkit (https://mixkit.co) publica efectos de sonido gratuitos bajo la
"Mixkit Sound Effects Free License". Este script descarga los SFX listados en
las páginas públicas de categoría para llenar assets/sfx/ y usarlos en TUS
propios videos. Úsalo respetando los términos de Mixkit
(https://mixkit.co/license/): el uso en tus videos está permitido; redistribuir
la librería de sonidos como tal, no.

Técnica: Playwright abre la página de la categoría (el listado se hidrata con
JavaScript), del HTML se extraen los IDs de audio y se descarga cada .wav con
curl (con fallback al preview .mp3). Al final escribe un manifest.json con el
catálogo descargado.

Uso típico:
  python descargar_sfx.py                      # todas las categorías
  python descargar_sfx.py --categoria whoosh --destino assets/sfx
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

# Categorías públicas de Mixkit útiles para shorts (whoosh, impactos, pops...)
CATEGORIAS = {
    "whoosh":     "https://mixkit.co/free-sound-effects/whoosh/",
    "transition": "https://mixkit.co/free-sound-effects/transition/",
    "click":      "https://mixkit.co/free-sound-effects/click/",
    "pop":        "https://mixkit.co/free-sound-effects/pop/",
    "swoosh":     "https://mixkit.co/free-sound-effects/swoosh/",
    "game":       "https://mixkit.co/free-sound-effects/game/",
    "win":        "https://mixkit.co/free-sound-effects/win/",
    "bell":       "https://mixkit.co/free-sound-effects/bell/",
    "impact":     "https://mixkit.co/free-sound-effects/impact/",
    "crowd":      "https://mixkit.co/free-sound-effects/crowd/",
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Descarga SFX gratuitos de Mixkit (respetando sus términos) a assets/sfx/.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--categoria", default="all", choices=["all"] + sorted(CATEGORIAS),
                   help="categoría a descargar, o 'all' para todas")
    p.add_argument("--destino", default=None,
                   help="carpeta destino (default: assets/sfx de la skill)")
    p.add_argument("--limite", type=int, default=10,
                   help="máximo de SFX por categoría (default: 10 — descarga moderada; 0 = sin límite)")
    return p.parse_args()


def fallar(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def slug(texto):
    """Nombre de archivo seguro: minúsculas, sin acentos, solo [a-z0-9-]."""
    s = unicodedata.normalize("NFD", texto.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:48]


def parse_listado(html):
    """Extrae (id, título) de cada SFX del HTML de la categoría, en orden."""
    ids = re.findall(r'data-audio-player-item-id-value="(\d+)"', html)
    titulos = re.findall(r'item-grid-card__title">\s*([^<]+?)\s*</h2>', html)
    return [(sid, titulos[i] if i < len(titulos) else sid) for i, sid in enumerate(ids)]


def descargar_sfx(sid, base, carpeta):
    """Descarga un SFX: intenta el .wav completo y cae al preview .mp3.
    Devuelve (ruta, bytes) o (None, 0) si ambos fallan."""
    ruta = os.path.join(carpeta, base + ".wav")
    url_wav = f"https://assets.mixkit.co/active_storage/sfx/{sid}/{sid}.wav"
    r = subprocess.run(["curl", "-s", "-L", "--max-time", "40", "-o", ruta,
                        "-w", "%{http_code}", url_wav], capture_output=True, text=True)
    tam = os.path.getsize(ruta) if os.path.exists(ruta) else 0
    if r.stdout.strip() == "200" and tam >= 3000:
        return ruta, tam
    # fallback: preview mp3 (más ligero, suficiente para SFX de shorts)
    if os.path.exists(ruta):
        os.remove(ruta)
    ruta = os.path.join(carpeta, base + ".mp3")
    url_mp3 = f"https://assets.mixkit.co/active_storage/sfx/{sid}/{sid}-preview.mp3"
    subprocess.run(["curl", "-s", "-L", "--max-time", "40", "-o", ruta, url_mp3])
    tam = os.path.getsize(ruta) if os.path.exists(ruta) else 0
    if tam < 3000:
        if os.path.exists(ruta):
            os.remove(ruta)
        return None, 0
    return ruta, tam


def main():
    args = parse_args()
    if args.limite < 0:
        fallar("--limite debe ser >= 0")
    if not shutil.which("curl"):
        fallar("curl no está en el PATH")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fallar("falta playwright (corre scripts/setup.sh y activa el venv de la skill)")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.abspath(args.destino or os.path.join(script_dir, "..", "assets", "sfx"))
    os.makedirs(destino, exist_ok=True)
    elegidas = sorted(CATEGORIAS) if args.categoria == "all" else [args.categoria]

    # 1) Listar los SFX de cada categoría (la página se hidrata con JS)
    catalogo = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()
        for cat in elegidas:
            try:
                pg.goto(CATEGORIAS[cat], wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_timeout(2200)
                filas = parse_listado(pg.content())
            except Exception as e:
                print(f"[{cat}] error al listar: {e}", file=sys.stderr)
                filas = []
            if args.limite:
                filas = filas[:args.limite]
            print(f"[{cat}] {len(filas)} sfx encontrados")
            catalogo.append((cat, filas))
        br.close()

    if not any(filas for _, filas in catalogo):
        fallar("no se encontró ningún SFX; Mixkit pudo cambiar su HTML "
               "(revisa los patrones de parse_listado) o no hay conexión")

    # 2) Descargar y armar el manifiesto
    manifest = []
    for cat, filas in catalogo:
        carpeta = os.path.join(destino, cat)
        os.makedirs(carpeta, exist_ok=True)
        for sid, titulo in filas:
            base = slug(titulo) or sid
            ruta, tam = descargar_sfx(sid, base, carpeta)
            if ruta is None:
                print(f"[{cat}] falló la descarga de '{titulo}' (id {sid})", file=sys.stderr)
                continue
            manifest.append({"cat": cat, "id": sid, "title": titulo,
                             "file": os.path.relpath(ruta, destino), "bytes": tam})

    with open(os.path.join(destino, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    total_mb = sum(m["bytes"] for m in manifest) / 1e6
    print(f"OK -> {destino}  ({len(manifest)} sfx, {total_mb:.1f} MB, manifest.json listo)")


if __name__ == "__main__":
    main()
