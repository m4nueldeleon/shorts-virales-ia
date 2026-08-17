#!/usr/bin/env python3
"""Verificación de calidad del render final (FASE 8 del pipeline).

Chequeos:
  1. ffprobe      → 1080x1920, ~30 fps, h264, aac y moov al inicio (+faststart)
  2. silencedetect → silencios largos (noise=-30dB, d=1.0); deben ser 0
  3. volumedetect  → sin clipping (max < 0 dB) y volumen medio razonable
  4. re-transcripción del final (si transcribir.py y el venv existen) para
     inspeccionar muletillas, repeticiones o palabras cortadas
  5. extrae 4 frames repartidos a verificacion_frames/ para revisar safe zones

Uso:
  python verificar.py final.mp4
  python verificar.py final.mp4 --transcripcion transcripcion.json

Sale con código 1 si hay problemas (imprime cada uno con sugerencia de arreglo).
"""
import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys

MULETILLAS = {"eh", "eee", "mmm", "este", "o sea", "um", "uh", "like", "you know"}
PROBLEMAS = []  # [(descripción, sugerencia)]
AVISOS = []


def problema(desc, sugerencia):
    PROBLEMAS.append((desc, sugerencia))


def correr(cmd):
    """Ejecuta un comando y devuelve (returncode, stdout, stderr)."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def ffprobe_datos(video):
    rc, out, err = correr(["ffprobe", "-v", "error", "-print_format", "json",
                           "-show_format", "-show_streams", video])
    if rc != 0:
        print(f"ERROR: ffprobe no pudo leer el archivo:\n{err.strip()}", file=sys.stderr)
        sys.exit(1)
    return json.loads(out)


def chequear_formato(datos):
    """Chequeo 1: resolución, fps, codecs."""
    vid = next((s for s in datos["streams"] if s["codec_type"] == "video"), None)
    aud = next((s for s in datos["streams"] if s["codec_type"] == "audio"), None)
    if vid is None:
        problema("no hay pista de video", "revisa el ensamble final")
        return
    w, h = vid.get("width"), vid.get("height")
    if (w, h) != (1080, 1920):
        problema(f"resolución {w}x{h} (esperado 1080x1920)",
                 "reescala: -vf scale=1080:1920:force_original_aspect_ratio=decrease,"
                 "pad=1080:1920:(ow-iw)/2:(oh-ih)/2")
    num, _, den = (vid.get("avg_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    if not 29.7 <= fps <= 30.3:
        problema(f"fps={fps:.2f} (esperado ~30)", "re-exporta con -r 30")
    if vid.get("codec_name") != "h264":
        problema(f"codec de video {vid.get('codec_name')} (esperado h264)",
                 "re-exporta con -c:v libx264 -crf 18 -pix_fmt yuv420p")
    if vid.get("pix_fmt") not in (None, "yuv420p"):
        AVISOS.append(f"pix_fmt={vid.get('pix_fmt')} — usa yuv420p para máxima compatibilidad")
    if aud is None:
        problema("no hay pista de audio", "revisa la mezcla (voz + música + SFX)")
    elif aud.get("codec_name") != "aac":
        problema(f"codec de audio {aud.get('codec_name')} (esperado aac)",
                 "re-exporta con -c:a aac -b:a 192k")
    print(f"  video: {w}x{h} {fps:.2f}fps {vid.get('codec_name')} | "
          f"audio: {aud.get('codec_name') if aud else 'NINGUNO'}")


def chequear_faststart(video):
    """Chequeo 1b: moov antes que mdat (+faststart). Si no se puede detectar, avisa."""
    try:
        orden = []
        with open(video, "rb") as f:
            pos, size_total = 0, os.path.getsize(video)
            while pos < size_total and len(orden) < 12:
                f.seek(pos)
                cab = f.read(8)
                if len(cab) < 8:
                    break
                tam, tipo = struct.unpack(">I4s", cab)
                if tam == 1:  # atom de 64 bits
                    tam = struct.unpack(">Q", f.read(8))[0]
                elif tam == 0:  # hasta el final del archivo
                    tam = size_total - pos
                orden.append(tipo.decode("latin-1"))
                pos += max(tam, 8)
        if "moov" in orden and "mdat" in orden:
            if orden.index("moov") > orden.index("mdat"):
                problema("el archivo NO tiene +faststart (moov después de mdat)",
                         "re-exporta añadiendo -movflags +faststart")
            else:
                print("  +faststart: OK (moov antes de mdat)")
        else:
            AVISOS.append("no se pudo detectar +faststart (átomos no estándar)")
    except (OSError, struct.error) as e:
        AVISOS.append(f"no se pudo detectar +faststart ({e})")


def chequear_silencios(video):
    """Chequeo 2: silencios largos con silencedetect."""
    _, _, err = correr(["ffmpeg", "-hide_banner", "-i", video, "-af",
                        "silencedetect=noise=-30dB:d=1.0", "-f", "null", "-"])
    inicios = re.findall(r"silence_start:\s*([\d.]+)", err)
    duraciones = re.findall(r"silence_duration:\s*([\d.]+)", err)
    if inicios:
        detalle = ", ".join(f"{float(s):.1f}s ({float(d):.1f}s)"
                            for s, d in zip(inicios, duraciones))
        problema(f"{len(inicios)} silencio(s) largo(s): {detalle}",
                 "recórtalos con scripts/cortar_silencios.py y re-ensambla")
    else:
        print("  silencios largos: 0 ✓")


def chequear_volumen(video):
    """Chequeo 3: clipping y volumen medio."""
    _, _, err = correr(["ffmpeg", "-hide_banner", "-i", video, "-af",
                        "volumedetect", "-f", "null", "-"])
    m_max = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", err)
    m_mean = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", err)
    if not (m_max and m_mean):
        AVISOS.append("volumedetect no devolvió datos (¿hay pista de audio?)")
        return
    vmax, vmean = float(m_max.group(1)), float(m_mean.group(1))
    print(f"  volumen: max={vmax:.1f} dB, mean={vmean:.1f} dB")
    if vmax >= 0.0:
        problema(f"clipping: max_volume={vmax:.1f} dB (debe ser < 0)",
                 "baja la mezcla o aplica alimiter=limit=0.891 (−1 dBFS)")
    if vmean > -8.0:
        problema(f"volumen medio muy alto ({vmean:.1f} dB)",
                 "normaliza con loudnorm=I=-14:TP=-1.5:LRA=11")
    elif vmean < -33.0:
        problema(f"volumen medio muy bajo ({vmean:.1f} dB)",
                 "normaliza con loudnorm=I=-14:TP=-1.5:LRA=11")


def buscar_python_venv(raiz):
    """Busca el python del venv creado por setup.sh; None si no existe."""
    candidatos = [os.path.join(raiz, d, "bin", "python") for d in (".venv", "venv")]
    candidatos += [os.path.join(raiz, d, "Scripts", "python.exe") for d in (".venv", "venv")]
    return next((c for c in candidatos if os.path.isfile(c)), None)


def re_transcribir(video, transcripcion_previa):
    """Chequeo 4: re-transcribe el final e imprime el texto para inspección."""
    scripts = os.path.dirname(os.path.abspath(__file__))
    transcribir = os.path.join(scripts, "transcribir.py")
    py = buscar_python_venv(os.path.dirname(scripts)) or sys.executable
    if not os.path.isfile(transcribir):
        AVISOS.append("no se encontró transcribir.py; me salto la re-transcripción")
        return
    salida = os.path.join(os.getcwd(), "verificacion_transcripcion.json")
    rc, _, err = correr([py, transcribir, video, "--salida", salida])
    if rc != 0:
        AVISOS.append(f"la re-transcripción falló (no bloqueante): {err.strip().splitlines()[-1] if err.strip() else 'sin detalle'}")
        return
    with open(salida, encoding="utf-8") as f:
        datos = json.load(f)
    texto = " ".join(s["text"] for s in datos["segments"]).strip()
    print("\n  — Texto del render final (inspecciona muletillas/repeticiones/cortes) —")
    for s in datos["segments"]:
        print(f"    [{s['start']:7.2f}–{s['end']:7.2f}] {s['text']}")
    palabras = texto.lower().split()
    sospechosas = sorted({w.strip(".,¿?¡!…") for w in palabras} & MULETILLAS)
    if sospechosas:
        AVISOS.append(f"posibles muletillas en el final: {', '.join(sospechosas)} — "
                      "escucha esos puntos antes de publicar")
    repetidas = [palabras[i] for i in range(1, len(palabras))
                 if palabras[i] == palabras[i - 1] and len(palabras[i]) > 3]
    if repetidas:
        AVISOS.append(f"palabras repetidas consecutivas: {', '.join(sorted(set(repetidas)))}")
    if transcripcion_previa and os.path.isfile(transcripcion_previa):
        with open(transcripcion_previa, encoding="utf-8") as f:
            prev = json.load(f)
        n_prev = sum(len(s["words"]) for s in prev.get("segments", []))
        print(f"  palabras: original={n_prev}, final={len(palabras)} (el final debe ser menor)")


def extraer_frames(video, duracion):
    """Chequeo 5: 4 frames repartidos para revisión visual de safe zones."""
    carpeta = "verificacion_frames"
    os.makedirs(carpeta, exist_ok=True)
    for i, frac in enumerate((0.10, 0.37, 0.63, 0.90), start=1):
        t = duracion * frac
        destino = os.path.join(carpeta, f"frame_{i}_t{t:.1f}s.png")
        rc, _, err = correr(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                             "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", destino])
        if rc != 0:
            AVISOS.append(f"no se pudo extraer el frame en t={t:.1f}s")
    print(f"  frames → {carpeta}/  (revisa safe zones: top 220px, bottom 480px, right 120px)")


def main():
    p = argparse.ArgumentParser(
        description="QA del render final: formato, silencios, volumen, "
                    "re-transcripción y frames de revisión.",
        epilog="Veredicto: LISTO ✅ o lista de problemas ❌ (exit code 1).")
    p.add_argument("video", help="render final a verificar (MP4)")
    p.add_argument("--transcripcion", default=None,
                   help="transcripcion.json original para comparar conteo de palabras")
    a = p.parse_args()

    if not os.path.isfile(a.video):
        print(f"ERROR: no existe el archivo: {a.video}", file=sys.stderr)
        sys.exit(1)
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        print("ERROR: se necesitan ffmpeg y ffprobe. Corre scripts/setup.sh.", file=sys.stderr)
        sys.exit(1)

    print(f"Verificando {a.video} …")
    datos = ffprobe_datos(a.video)
    duracion = float(datos.get("format", {}).get("duration", 0) or 0)
    print(f"  duración: {duracion:.1f}s")
    chequear_formato(datos)
    chequear_faststart(a.video)
    chequear_silencios(a.video)
    chequear_volumen(a.video)
    re_transcribir(a.video, a.transcripcion)
    if duracion > 0:
        extraer_frames(a.video, duracion)

    print()
    for av in AVISOS:
        print(f"  AVISO: {av}")
    if PROBLEMAS:
        print(f"\n❌ {len(PROBLEMAS)} problema(s):")
        for i, (desc, fix) in enumerate(PROBLEMAS, 1):
            print(f"  {i}. {desc}\n     → arreglo: {fix}")
        sys.exit(1)
    print("\nLISTO ✅ — el video pasa todos los chequeos automáticos. "
          "Revisa los frames y el texto antes de publicar.")


if __name__ == "__main__":
    main()
