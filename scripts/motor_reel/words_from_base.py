"""Palabras de subtítulos desde la re-transcripción de base.mp4.

El transcript del crudo oculta tomas repetidas y estira palabras sobre pausas; mapearlo al corte
dejó palabras fuera. Transcribir el corte final da tiempos exactos del timeline nuevo.
"""
import json
import os
import subprocess
import unicodedata
from pathlib import Path

W = Path(__file__).resolve().parent
OUT = Path(os.environ.get("REEL_OUT", str(W / "03-render")))
PY = os.environ.get(
    "WHISPER_PY", "python3"
)
MAX_WORD = 0.8   # whisper estira el inicio de la palabra sobre la pausa previa
PUNCT = ".,;:¿?¡!"

# claves normalizadas (sin acentos ni puntuación, minúsculas)
FIX = {
    "chayipiti": "ChatGPT", "chayipity": "ChatGPT", "chagipity": "ChatGPT", "chagipiti": "ChatGPT",
    "chatgpt": "ChatGPT", "cloud": "Claude", "cronjob": "Cron Job", "chrome": "Cron", "sias": "IAs",
    "ia": "IA", "ias": "IAs", "sia": "IAs",
}
FIX_SEG = {
    ("S16", "el"): "al", ("S16", "escriba"): "escribe", ("S03", "ticket"): "tickets",
    ("S12", "toda"): "todas", ("S12", "la"): "las", ("S12", "cia"): "IAs",
}


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(c for c in s.lower() if c.isalnum())


def segment_at(tl, t):
    for g in tl["segments"]:
        if g["new_start"] <= t < g["new_end"]:
            return g
    return tl["segments"][-1]


def main():
    wav = OUT / "base16k.wav"
    raw_json = OUT / "base_words.json"
    base = OUT / "base.mp4"
    # caché: whisper varía entre corridas; solo se re-transcribe si la base cambió
    if not raw_json.exists() or raw_json.stat().st_mtime < base.stat().st_mtime:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(base), "-ac", "1", "-ar", "16000", str(wav)], check=True)
        subprocess.run([PY, str(W / "01-transcripcion" / "transcribe.py"), str(wav), str(raw_json)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tr = json.loads(raw_json.read_text())
    tl = json.loads((OUT / "timeline.json").read_text())

    words = []
    for s in tr["segments"]:
        for w in s.get("words", []):
            raw = w["word"].strip()
            core = norm(raw)
            if not core:
                continue
            end = w["end"]
            start = max(w["start"], end - MAX_WORD)
            # punto medio: whisper estira tanto inicios como finales en los bordes de tramo
            seg = segment_at(tl, (start + end) / 2)
            txt = FIX_SEG.get((seg["id"], core)) or FIX.get(core) or raw.strip(PUNCT)
            words.append({"seg": seg["id"], "w": txt,
                          "s": round(max(start, seg["new_start"]), 3),
                          "e": round(min(end, seg["new_end"]), 3)})

    tl["words"] = words
    (OUT / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    by_seg = {}
    for w in words:
        by_seg.setdefault(w["seg"], []).append(w["w"])
    for sid, ws in by_seg.items():
        print(sid, " ".join(ws))


if __name__ == "__main__":
    main()
