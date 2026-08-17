#!/usr/bin/env python3
"""Transcripción word-level cross-platform (FASE 1 del pipeline).

Backend automático:
  1. mlx-whisper   (Apple Silicon, rápido)  → modelo mlx-community/whisper-large-v3-turbo
  2. faster-whisper (cualquier sistema)      → modelo large-v3-turbo (compute auto → int8)

Salida JSON normalizada (idéntica con ambos backends):
  {"language": "es", "segments": [{"start", "end", "text",
                                   "words": [{"w", "start", "end"}]}]}

Uso:
  python transcribir.py video.mp4
  python transcribir.py video.mp4 --idioma es --salida transcripcion.json
  python transcribir.py video.mp4 --inicio 12.5 --fin 18.0   # ventana aislada
                                  (los timestamps de salida quedan en tiempo ORIGINAL)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

MODELO_MLX = "mlx-community/whisper-large-v3-turbo"
MODELO_FW = "large-v3-turbo"


def morir(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def extraer_audio(video, inicio=None, fin=None):
    """Extrae el audio a un wav temporal 16 kHz mono. Devuelve la ruta del wav."""
    if not shutil.which("ffmpeg"):
        morir("no se encontró ffmpeg en el PATH. Corre scripts/setup.sh primero.")
    fd, wav = tempfile.mkstemp(suffix=".wav", prefix="transcribir_")
    os.close(fd)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", video]
    if inicio is not None:
        cmd += ["-ss", str(inicio)]
    if fin is not None:
        cmd += ["-to", str(fin)]
    cmd += ["-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.getsize(wav):
        os.unlink(wav)
        morir(f"ffmpeg no pudo extraer el audio:\n{r.stderr.strip()}")
    return wav


def _norm_palabra(w, start, end):
    return {"w": str(w).strip(), "start": round(float(start), 3), "end": round(float(end), 3)}


def _norm_segmento(start, end, text, words):
    return {"start": round(float(start), 3), "end": round(float(end), 3),
            "text": str(text).strip(), "words": words}


def transcribir_mlx(wav, idioma):
    """Backend 1: mlx-whisper (devuelve dict normalizado o None si no está instalado)."""
    try:
        import mlx_whisper
    except ImportError:
        return None
    print(f"Backend: mlx-whisper ({MODELO_MLX})", file=sys.stderr)
    res = mlx_whisper.transcribe(
        wav, path_or_hf_repo=MODELO_MLX, language=idioma,
        word_timestamps=True, condition_on_previous_text=False)
    segs = []
    for s in res.get("segments", []):
        words = [_norm_palabra(w["word"], w["start"], w["end"]) for w in s.get("words", [])]
        segs.append(_norm_segmento(s["start"], s["end"], s.get("text", ""), words))
    return {"language": res.get("language") or idioma, "segments": segs}


def transcribir_faster(wav, idioma):
    """Backend 2: faster-whisper con compute_type auto y fallback a int8."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        morir("no hay backend de whisper disponible (ni mlx-whisper ni faster-whisper).\n"
              "Corre scripts/setup.sh para instalar las dependencias.")
    ultimo_error = None
    for compute in ("auto", "int8"):
        try:
            print(f"Backend: faster-whisper ({MODELO_FW}, compute_type={compute})", file=sys.stderr)
            model = WhisperModel(MODELO_FW, compute_type=compute)
            seg_iter, info = model.transcribe(
                wav, language=idioma, word_timestamps=True,
                condition_on_previous_text=False)
            segs = []
            for s in seg_iter:
                words = [_norm_palabra(w.word, w.start, w.end) for w in (s.words or [])]
                segs.append(_norm_segmento(s.start, s.end, s.text, words))
            return {"language": info.language or idioma, "segments": segs}
        except Exception as e:  # p. ej. compute type no soportado en este hardware
            ultimo_error = e
            print(f"  compute_type={compute} falló ({e}); probando fallback…", file=sys.stderr)
    morir(f"faster-whisper falló con todos los compute_type: {ultimo_error}")


def aplicar_offset(datos, offset):
    """Suma `offset` a todos los timestamps (para ventanas aisladas con --inicio)."""
    segs = []
    for s in datos["segments"]:
        words = [{"w": w["w"], "start": round(w["start"] + offset, 3),
                  "end": round(w["end"] + offset, 3)} for w in s["words"]]
        segs.append({"start": round(s["start"] + offset, 3), "end": round(s["end"] + offset, 3),
                     "text": s["text"], "words": words})
    return {"language": datos["language"], "segments": segs}


def main():
    p = argparse.ArgumentParser(
        description="Transcribe un video a JSON con timestamps por palabra "
                    "(mlx-whisper en Apple Silicon, faster-whisper en el resto).",
        epilog="Con --inicio/--fin se transcribe solo esa ventana y los timestamps "
               "de salida se devuelven en tiempo ORIGINAL del video (offset aplicado).")
    p.add_argument("video", help="video o audio de entrada (cualquier formato que lea ffmpeg)")
    p.add_argument("--idioma", default="es", help="idioma del audio (default: es)")
    p.add_argument("--salida", default="transcripcion.json",
                   help="archivo JSON de salida (default: transcripcion.json)")
    p.add_argument("--inicio", type=float, default=None, metavar="S",
                   help="segundo inicial de la ventana a transcribir")
    p.add_argument("--fin", type=float, default=None, metavar="S",
                   help="segundo final de la ventana a transcribir")
    a = p.parse_args()

    if not os.path.isfile(a.video):
        morir(f"no existe el archivo: {a.video}")
    if a.inicio is not None and a.inicio < 0:
        morir("--inicio debe ser >= 0")
    if a.fin is not None and a.inicio is not None and a.fin <= a.inicio:
        morir("--fin debe ser mayor que --inicio")

    wav = extraer_audio(a.video, a.inicio, a.fin)
    try:
        datos = transcribir_mlx(wav, a.idioma)
        if datos is None:
            datos = transcribir_faster(wav, a.idioma)
    finally:
        if os.path.exists(wav):
            os.unlink(wav)

    if a.inicio:
        datos = aplicar_offset(datos, a.inicio)

    with open(a.salida, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    n_seg = len(datos["segments"])
    n_pal = sum(len(s["words"]) for s in datos["segments"])
    print(f"OK → {a.salida}  ({n_seg} segmentos, {n_pal} palabras, idioma={datos['language']})")


if __name__ == "__main__":
    main()
