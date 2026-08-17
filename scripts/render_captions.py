#!/usr/bin/env python3
"""Renderiza subtítulos kinéticos como overlay .mov con canal alfa.

Técnica (no cambiar): Playwright abre caption.html con fondo transparente,
pinta cada frame llamando render(t) y lo captura como PNG RGBA
(omit_background); después ffmpeg empaqueta los frames en un .mov qtrle
(pix_fmt argb) listo para superponer encima del video.

Formato esperado de captions.json — lista de bloques:
  [{"start": 0.0, "end": 1.8,
    "words": [{"w": "HOLA", "s": 0.0}, {"w": "MUNDO", "s": 0.9}]}, ...]
"start"/"end" delimitan el bloque en pantalla; "s" es el inicio de cada
palabra. Todos los tiempos en segundos y en el tiempo FINAL del video
(después de cortar silencios/muletillas).

Uso típico:
  python render_captions.py --captions captions.json --test   # revisar estilo
  python render_captions.py --captions captions.json --salida caption.mov
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

# Fracciones de la duración usadas en modo --test (repartidas por el video)
FRACCIONES_TEST = (0.1, 0.35, 0.65, 0.9)


def parse_args():
    p = argparse.ArgumentParser(
        description="Renderiza subtítulos kinéticos (captions.json) a un overlay .mov con alfa.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--captions", default="captions.json",
                   help="JSON con los bloques de subtítulos")
    p.add_argument("--duracion", type=float, default=None,
                   help="duración total en segundos (default: fin del último caption + 0.5)")
    p.add_argument("--fps", type=int, default=30, help="frames por segundo")
    p.add_argument("--ancho", type=int, default=1080, help="ancho del lienzo en px")
    p.add_argument("--alto", type=int, default=380, help="alto de la banda de subtítulos en px")
    p.add_argument("--salida", default="caption.mov",
                   help="archivo .mov de salida (qtrle con canal alfa)")
    p.add_argument("--html", default=None,
                   help="plantilla HTML (default: caption.html junto a este script)")
    p.add_argument("--test", action="store_true",
                   help="solo 4 frames de prueba en cap_test/ (repartidos según la duración)")
    return p.parse_args()


def fallar(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def cargar_captions(ruta):
    """Carga y valida el JSON de captions; falla rápido con mensaje claro."""
    if not os.path.isfile(ruta):
        fallar(f"no existe el archivo de captions: {ruta}")
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        fallar(f"JSON inválido en {ruta}: {e}")
    if not isinstance(data, list) or not data:
        fallar(f"{ruta} debe ser una lista NO vacía de bloques {{start, end, words}}")
    for i, bloque in enumerate(data):
        if not all(k in bloque for k in ("start", "end", "words")):
            fallar(f"bloque #{i} incompleto (necesita start, end y words): {bloque}")
        for w in bloque["words"]:
            if "w" not in w or "s" not in w:
                fallar(f"bloque #{i}: cada palabra necesita 'w' (texto) y 's' (inicio en segundos)")
    return data


def tiempos_de_prueba(captions, duracion):
    """4 tiempos repartidos según la duración; si uno cae en un hueco sin
    subtítulo, lo ajusta al centro del bloque más cercano para que el frame
    de prueba muestre texto real."""
    tiempos = []
    for frac in FRACCIONES_TEST:
        t = duracion * frac
        if not any(b["start"] <= t < b["end"] for b in captions):
            cercano = min(captions, key=lambda b: abs((b["start"] + b["end"]) / 2 - t))
            t = (cercano["start"] + cercano["end"]) / 2
        tiempos.append(round(t, 2))
    return tiempos


def main():
    args = parse_args()
    if args.fps <= 0:
        fallar("--fps debe ser > 0")
    if args.ancho <= 0 or args.alto <= 0:
        fallar("--ancho y --alto deben ser > 0")

    captions = cargar_captions(args.captions)

    # Duración: explícita, o autodetectada del último caption + 0.5 s de colchón
    duracion = args.duracion if args.duracion is not None else max(b["end"] for b in captions) + 0.5
    if duracion <= 0:
        fallar("--duracion debe ser > 0 segundos")

    html = args.html or os.path.join(os.path.dirname(os.path.abspath(__file__)), "caption.html")
    if not os.path.isfile(html):
        fallar(f"no existe la plantilla HTML: {html}")
    if not shutil.which("ffmpeg"):
        fallar("ffmpeg no está en el PATH (corre scripts/setup.sh)")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fallar("falta playwright (corre scripts/setup.sh y activa el venv de la skill)")

    def activo(t):
        return any(b["start"] <= t < b["end"] for b in captions)

    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--force-color-profile=srgb"])
        pg = br.new_page(viewport={"width": args.ancho, "height": args.alto},
                         device_scale_factor=1)
        pg.goto("file://" + os.path.abspath(html))
        # Ajusta el lienzo HTML al tamaño pedido (por si difiere del default 1080×380)
        pg.evaluate("([w,h])=>{for(const e of [document.documentElement,document.body])"
                    "{e.style.width=w+'px';e.style.height=h+'px';}}", [args.ancho, args.alto])
        pg.evaluate("(c)=>setup(c)", captions)

        if args.test:
            os.makedirs("cap_test", exist_ok=True)
            for t in tiempos_de_prueba(captions, duracion):
                pg.evaluate("(t)=>render(t)", t)
                pg.screenshot(path=f"cap_test/t{int(t * 10):05d}.png", omit_background=True)
            br.close()
            print("Frames de prueba -> cap_test/  (revísalos antes del render completo)")
            return

        frames_dir = (os.path.splitext(args.salida)[0] or "caption") + "_frames"
        shutil.rmtree(frames_dir, ignore_errors=True)
        os.makedirs(frames_dir, exist_ok=True)

        # Frame transparente para los tramos sin subtítulo (se copia, no se recaptura)
        blank = os.path.join(frames_dir, "_blank.png")
        pg.evaluate("(t)=>render(t)", duracion + 999.0)
        pg.screenshot(path=blank, omit_background=True)

        total = int(round(duracion * args.fps))
        capturas = 0
        for f in range(total):
            t = f / args.fps
            dst = os.path.join(frames_dir, f"f{f:05d}.png")
            if activo(t):
                pg.evaluate("(t)=>render(t)", t)
                pg.screenshot(path=dst, omit_background=True)
                capturas += 1
            else:
                shutil.copyfile(blank, dst)
            if f % 600 == 0:
                print(f"  {f}/{total} frames (capturas={capturas})", flush=True)
        br.close()

    print(f"frames={total} capturas={capturas}")
    r = subprocess.run(["ffmpeg", "-y", "-framerate", str(args.fps),
                        "-i", os.path.join(frames_dir, "f%05d.png"),
                        "-c:v", "qtrle", "-pix_fmt", "argb", args.salida],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode != 0:
        fallar("ffmpeg falló al empaquetar el .mov:\n" + r.stderr.decode(errors="replace")[-800:])
    shutil.rmtree(frames_dir, ignore_errors=True)
    print(f"OK -> {args.salida}  ({duracion:.2f}s @ {args.fps}fps, {args.ancho}x{args.alto}, alfa)")


if __name__ == "__main__":
    main()
