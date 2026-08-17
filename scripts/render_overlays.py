#!/usr/bin/env python3
"""Renderiza overlays virales (SUSCRÍBETE, SÍGUEME, like, countdown 3-2-1,
flecha, círculo, viñeta, light leak) como .mov con canal alfa o .png transparente.

Técnica (no cambiar): Playwright abre overlays.html con fondo transparente,
anima cada escena con render(t), captura PNGs RGBA (omit_background) y ffmpeg
los empaqueta en un .mov qtrle (pix_fmt argb). Las escenas estáticas van a PNG.

Colores y textos se editan en las variables de arriba de overlays.html.

Uso típico:
  python render_overlays.py                       # todos -> ../assets/overlays/
  python render_overlays.py --overlay subscribe --salida sub.mov --dur 3.0
"""
import argparse
import os
import shutil
import subprocess
import sys

# Duración por defecto (segundos) de cada overlay animado
ANIMADOS = {"subscribe": 2.5, "follow": 2.6, "like": 2.2,
            "countdown": 3.0, "circle": 1.6, "arrow": 1.6, "lightleak": 2.0}
# Escenas estáticas -> 1 solo frame PNG
ESTATICOS = ("vignette",)
ANCHO, ALTO = 1080, 1920  # lienzo 9:16


def parse_args():
    nombres = sorted(ANIMADOS) + list(ESTATICOS)
    p = argparse.ArgumentParser(
        description="Renderiza overlays con canal alfa (.mov qtrle o .png) para shorts 9:16.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--overlay", default="all", choices=["all"] + nombres,
                   help="overlay a renderizar, o 'all' para todos")
    p.add_argument("--salida", default=None,
                   help="archivo de salida (overlay único) o carpeta (default: assets/overlays de la skill)")
    p.add_argument("--fps", type=int, default=30, help="frames por segundo")
    p.add_argument("--dur", type=float, default=None,
                   help="duración en segundos (solo con un overlay animado; default según overlay)")
    return p.parse_args()


def fallar(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def render_png(pg, escena, salida):
    """Escena estática: 1 frame transparente a PNG."""
    pg.evaluate("([s,d])=>setup(s,d)", [escena, 1])
    pg.screenshot(path=salida, omit_background=True)
    print(f"PNG {escena} -> {salida}")


def render_mov(pg, escena, dur, fps, salida):
    """Escena animada: frames PNG RGBA -> .mov qtrle con alfa."""
    pg.evaluate("([s,d])=>setup(s,d)", [escena, dur])
    frames = (os.path.splitext(salida)[0] or escena) + "_frames"
    shutil.rmtree(frames, ignore_errors=True)
    os.makedirs(frames, exist_ok=True)
    for f in range(int(dur * fps) + 1):
        pg.evaluate("(t)=>render(t)", f / fps)
        pg.screenshot(path=os.path.join(frames, f"f{f:04d}.png"), omit_background=True)
    r = subprocess.run(["ffmpeg", "-y", "-framerate", str(fps),
                        "-i", os.path.join(frames, "f%04d.png"),
                        "-c:v", "qtrle", "-pix_fmt", "argb", salida],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    shutil.rmtree(frames, ignore_errors=True)
    if r.returncode != 0:
        fallar(f"ffmpeg falló con '{escena}':\n" + r.stderr.decode(errors="replace")[-800:])
    print(f"MOV {escena} ({dur}s) -> {salida}")


def ruta_salida(args, escena, dir_default):
    """Resuelve la ruta de salida para un overlay único (archivo o carpeta)."""
    ext = ".png" if escena in ESTATICOS else ".mov"
    salida = args.salida
    if not salida:
        salida = os.path.join(dir_default, escena + ext)
    elif os.path.isdir(salida) or salida.endswith(os.sep):
        salida = os.path.join(salida, escena + ext)
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    return salida


def main():
    args = parse_args()
    if args.fps <= 0:
        fallar("--fps debe ser > 0")
    if args.dur is not None and args.dur <= 0:
        fallar("--dur debe ser > 0 segundos")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    html = os.path.join(script_dir, "overlays.html")
    if not os.path.isfile(html):
        fallar(f"no existe la plantilla HTML: {html}")
    if not shutil.which("ffmpeg"):
        fallar("ffmpeg no está en el PATH (corre scripts/setup.sh)")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fallar("falta playwright (corre scripts/setup.sh y activa el venv de la skill)")

    dir_default = os.path.abspath(os.path.join(script_dir, "..", "assets", "overlays"))

    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--force-color-profile=srgb"])
        pg = br.new_page(viewport={"width": ANCHO, "height": ALTO}, device_scale_factor=1)
        pg.goto("file://" + html)

        if args.overlay == "all":
            if args.dur is not None:
                print("AVISO: --dur se ignora con --overlay all (usa las duraciones por defecto)")
            out_dir = os.path.abspath(args.salida) if args.salida else dir_default
            os.makedirs(out_dir, exist_ok=True)
            for escena in ESTATICOS:
                render_png(pg, escena, os.path.join(out_dir, escena + ".png"))
            for escena, dur in ANIMADOS.items():
                render_mov(pg, escena, dur, args.fps, os.path.join(out_dir, escena + ".mov"))
            print(f"Overlays listos -> {out_dir}")
        else:
            escena = args.overlay
            salida = ruta_salida(args, escena, dir_default)
            if escena in ESTATICOS:
                render_png(pg, escena, salida)
            else:
                render_mov(pg, escena, args.dur or ANIMADOS[escena], args.fps, salida)
        br.close()


if __name__ == "__main__":
    main()
