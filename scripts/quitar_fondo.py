#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quitar_fondo.py — quita el fondo de un SEGMENTO de video (chroma o IA).

Modos:
  chroma  Fondo verde/azul uniforme → chromakey + despill de ffmpeg (rápido).
  ia      Cualquier fondo real → segmentación con rembg, frame a frame.
          ADVERTENCIA: LENTO (~1-2 fps de procesamiento). Úsalo SOLO en
          segmentos de énfasis de 2-5 segundos.

El resultado conserva los fps y la resolución del video original, por lo que
puede reinsertarse directamente en el timeline.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

CODEC_VIDEO = ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p"]
CODEC_AUDIO = ["-c:a", "aac", "-b:a", "192k"]
MOVFLAGS = ["-movflags", "+faststart"]
EXT_IMAGEN = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
RE_COLOR = re.compile(r"^(0x|#)?([0-9a-fA-F]{6})$")

EPILOGO = """\
Ejemplos:
  python quitar_fondo.py video.mp4 --inicio 4.0 --fin 8.0
  python quitar_fondo.py video.mp4 --inicio 4 --fin 8 --modo chroma \\
      --color 0x00FF00 --fondo fondo.jpg
  python quitar_fondo.py video.mp4 --inicio 12 --fin 15 --modo ia \\
      --fondo 0x101020 --salida enfasis.mp4

Notas:
  · --fondo acepta: color hex (0x101020 o #101020), imagen jpg/png/webp
    (se anima con un Ken Burns suave) o un video (se repite en loop).
  · Modo ia: ADVERTENCIA — procesamiento LENTO (~1-2 fps). Recomendado SOLO
    para segmentos de 2-5 s. Requiere rembg: bash scripts/setup.sh --con-fondo
  · La salida conserva fps y resolución del original → se reinserta
    directamente en el timeline sin re-escalar.
"""


def morir(mensaje):
    print(f"ERROR: {mensaje}", file=sys.stderr)
    sys.exit(1)


def correr(cmd, contexto):
    """Ejecuta un comando; si falla, muestra el final del stderr y termina."""
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        cola = "\n".join(res.stderr.strip().splitlines()[-8:])
        morir(f"{contexto}\n--- ffmpeg dijo ---\n{cola}")
    return res


def probar_video(ruta):
    """Devuelve (ancho, alto, fps_str, fps_val, duración) del primer stream de video."""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,r_frame_rate",
           "-show_entries", "format=duration", "-of", "json", ruta]
    res = correr(cmd, f"No pude leer '{ruta}' con ffprobe")
    datos = json.loads(res.stdout)
    if not datos.get("streams"):
        morir(f"'{ruta}' no tiene pista de video")
    s = datos["streams"][0]
    fps_str = s.get("r_frame_rate") or "30/1"
    try:
        num, den = fps_str.split("/")
        fps_val = float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        fps_str, fps_val = "30/1", 30.0
    try:
        dur = float(datos.get("format", {}).get("duration") or 0)
    except ValueError:
        dur = 0.0
    return int(s["width"]), int(s["height"]), fps_str, fps_val, dur


def tiene_audio(ruta):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a",
           "-show_entries", "stream=index", "-of", "csv=p=0", ruta]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return bool(res.stdout.strip())


def normalizar_color(color):
    """'#00ff00' / '00FF00' / '0x00FF00' → '0x00FF00'; None si no es hex válido."""
    m = RE_COLOR.match(color.strip())
    return f"0x{m.group(2).upper()}" if m else None


def tipo_despill(color_0x):
    """Elige el despill según el canal dominante del color chroma."""
    r = int(color_0x[2:4], 16)
    g = int(color_0x[4:6], 16)
    b = int(color_0x[6:8], 16)
    if g >= r and g >= b:
        return "green"
    if b >= r and b > g:
        return "blue"
    return None  # color raro (p. ej. rojo): mejor no despillar


def construir_fondo(fondo, w, h, fps_str, fps_val, dur):
    """Devuelve (args_de_entrada, cadena_de_filtro) que produce [bg] como input 0."""
    color = normalizar_color(fondo)
    if color:
        entrada = ["-f", "lavfi", "-i",
                   f"color=c={color}:s={w}x{h}:r={fps_str}:d={dur:.3f}"]
        return entrada, "[0:v]format=yuv420p[bg]"
    if not os.path.exists(fondo):
        morir(f"--fondo '{fondo}' no es un color hex válido ni un archivo existente")
    ext = os.path.splitext(fondo)[1].lower()
    if ext in EXT_IMAGEN:
        # Imagen: cubrir el lienzo + Ken Burns suave (zoom lento 8%).
        n = max(int(round(dur * fps_val)), 1)
        filtro = (f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
                  f"crop={w}:{h},"
                  f"zoompan=z='1+0.08*on/{n}':x='iw/2-(iw/zoom)/2':"
                  f"y='ih/2-(ih/zoom)/2':d={n}:s={w}x{h}:fps={fps_str}[bg]")
        return ["-i", fondo], filtro
    # Video: loop infinito recortado a la duración del segmento.
    filtro = (f"[0:v]trim=duration={dur:.3f},setpts=PTS-STARTPTS,"
              f"scale={w}:{h}:force_original_aspect_ratio=increase,"
              f"crop={w}:{h},fps={fps_str}[bg]")
    return ["-stream_loop", "-1", "-i", fondo], filtro


def modo_chroma(args, w, h, fps_str, fps_val, dur):
    color = normalizar_color(args.color)
    if not color:
        morir(f"--color '{args.color}' no es hex válido (ejemplo: 0x00FF00)")
    entrada_fondo, filtro_fondo = construir_fondo(args.fondo, w, h, fps_str, fps_val, dur)
    despill = tipo_despill(color)
    cadena_fg = f"[1:v]chromakey={color}:0.20:0.08"
    if despill:
        cadena_fg += f",despill=type={despill}"
    cadena_fg += "[fg]"
    fc = f"{filtro_fondo};{cadena_fg};[bg][fg]overlay=shortest=1,format=yuv420p[out]"
    cmd = (["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
           + entrada_fondo
           + ["-ss", f"{args.inicio:.3f}", "-t", f"{dur:.3f}", "-i", args.video,
              "-filter_complex", fc, "-map", "[out]", "-map", "1:a?"]
           + CODEC_VIDEO + ["-r", fps_str] + CODEC_AUDIO + MOVFLAGS + [args.salida])
    print(f"→ Chroma {color} sobre fondo '{args.fondo}'…")
    correr(cmd, "Falló la composición chroma")


def modo_ia(args, w, h, fps_str, fps_val, dur, con_audio):
    try:
        from rembg import remove, new_session
    except ImportError:
        morir("rembg no está instalado (necesario para --modo ia).\n"
              "Corre: bash scripts/setup.sh --con-fondo")
    n_estimado = max(int(round(dur * fps_val)), 1)
    print("ADVERTENCIA: modo IA es LENTO (~1-2 fps de procesamiento).")
    print(f"  Segmento de {dur:.1f}s ≈ {n_estimado} frames → estimado "
          f"{n_estimado / 1.5 / 60:.1f} min.")
    if dur > 6:
        print("  Recomendación: usa segmentos de énfasis de 2-5 s.")
    tmp = tempfile.mkdtemp(prefix="quitar_fondo_")
    try:
        dir_in = os.path.join(tmp, "in")
        dir_out = os.path.join(tmp, "out")
        os.makedirs(dir_in)
        os.makedirs(dir_out)

        print("→ Extrayendo frames…")
        correr(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-ss", f"{args.inicio:.3f}", "-t", f"{dur:.3f}", "-i", args.video,
                "-vf", f"fps={fps_str}", os.path.join(dir_in, "f_%06d.png")],
               "Falló la extracción de frames")

        audio = None
        if con_audio:
            audio = os.path.join(tmp, "audio.m4a")
            correr(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", f"{args.inicio:.3f}", "-t", f"{dur:.3f}",
                    "-i", args.video, "-vn"] + CODEC_AUDIO + [audio],
                   "Falló la extracción del audio del segmento")

        frames = sorted(f for f in os.listdir(dir_in) if f.endswith(".png"))
        if not frames:
            morir("No se extrajo ningún frame; revisa --inicio/--fin")

        print(f"→ Quitando fondo con IA ({len(frames)} frames)…")
        sesion = new_session("u2net")  # la primera vez descarga el modelo (~170 MB)
        t0 = time.time()
        for i, nombre in enumerate(frames, 1):
            with open(os.path.join(dir_in, nombre), "rb") as fh:
                datos = fh.read()
            resultado = remove(datos, session=sesion)  # PNG RGBA
            with open(os.path.join(dir_out, nombre), "wb") as fh:
                fh.write(resultado)
            velocidad = i / max(time.time() - t0, 1e-6)
            faltan = (len(frames) - i) / max(velocidad, 1e-6)
            print(f"\r  {i}/{len(frames)} · {velocidad:.1f} fps · "
                  f"faltan ~{faltan:.0f}s   ", end="", flush=True)
        print()

        entrada_fondo, filtro_fondo = construir_fondo(
            args.fondo, w, h, fps_str, fps_val, dur)
        fc = (f"{filtro_fondo};[1:v]format=rgba[fg];"
              f"[bg][fg]overlay=shortest=1,format=yuv420p[out]")
        cmd = (["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
               + entrada_fondo
               + ["-framerate", fps_str, "-i", os.path.join(dir_out, "f_%06d.png")])
        if audio:
            cmd += ["-i", audio]
        cmd += ["-filter_complex", fc, "-map", "[out]"]
        if audio:
            cmd += ["-map", "2:a"]
        cmd += CODEC_VIDEO + ["-r", fps_str] + CODEC_AUDIO + MOVFLAGS + [args.salida]
        print("→ Recomponiendo segmento…")
        correr(cmd, "Falló la recomposición del segmento")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(
        prog="quitar_fondo.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=("Quita el fondo de un SEGMENTO de video y lo compone sobre "
                     "un fondo nuevo.\nModo chroma (rápido, fondo verde/azul) o "
                     "modo ia (rembg — LENTO, solo segmentos de 2-5 s)."),
        epilog=EPILOGO)
    ap.add_argument("video", help="Video de entrada (cualquier formato que lea ffmpeg)")
    ap.add_argument("--inicio", type=float, required=True,
                    help="Segundo donde inicia el segmento (ej. 4.0)")
    ap.add_argument("--fin", type=float, required=True,
                    help="Segundo donde termina el segmento (ej. 8.0)")
    ap.add_argument("--modo", choices=["ia", "chroma"], default="chroma",
                    help="chroma (rápido, fondo uniforme) o ia (rembg, LENTO). "
                         "Por defecto: chroma")
    ap.add_argument("--color", default="0x00FF00",
                    help="Color del chroma en modo chroma. Por defecto: 0x00FF00")
    ap.add_argument("--fondo", default="0x000000",
                    help="Fondo nuevo: color hex, imagen (Ken Burns suave) o "
                         "video (loop). Por defecto: negro")
    ap.add_argument("--salida", default="segmento_sinfondo.mp4",
                    help="Archivo de salida. Por defecto: segmento_sinfondo.mp4")
    args = ap.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        morir("ffmpeg/ffprobe no encontrados. Corre: bash scripts/setup.sh")
    if not os.path.exists(args.video):
        morir(f"No existe el archivo '{args.video}'")

    w, h, fps_str, fps_val, dur_video = probar_video(args.video)

    if args.inicio < 0:
        morir("--inicio no puede ser negativo")
    if args.fin <= args.inicio:
        morir("--fin debe ser mayor que --inicio")
    if dur_video and args.inicio >= dur_video:
        morir(f"--inicio ({args.inicio}s) está fuera del video ({dur_video:.2f}s)")
    fin = args.fin
    if dur_video and fin > dur_video:
        print(f"Aviso: --fin ({fin}s) excede la duración ({dur_video:.2f}s); se recorta.")
        fin = dur_video
    dur = fin - args.inicio
    con_audio = tiene_audio(args.video)

    print(f"Video: {w}x{h} · {fps_val:.2f} fps · "
          f"segmento {args.inicio:.2f}-{fin:.2f}s ({dur:.2f}s) · modo {args.modo}")

    if args.modo == "chroma":
        modo_chroma(args, w, h, fps_str, fps_val, dur)
    else:
        modo_ia(args, w, h, fps_str, fps_val, dur, con_audio)

    print(f"✓ Listo: {args.salida} ({w}x{h}, {fps_val:.2f} fps — "
          f"mismos fps/resolución que el original, reinsertable en el timeline)")


if __name__ == "__main__":
    main()
