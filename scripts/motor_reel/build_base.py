"""EDL del crudo -> base.mp4 (1080x1920/30fps, voz tratada) + timeline.json para Remotion.

Cortes por envolvente de energía de la banda de voz (silencedetect no sirve con el ruido del
parque). Bordes en el valle de energía más cercano; huecos internos largos fuera; 12 ms de fade.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
SRC = Path(os.environ.get("REEL_SRC", str(W / "00-crudo" / "crudo.mov")))
ENERGY = json.loads((W / "01-transcripcion" / "energy.json").read_text())
TRANS = json.loads((W / "01-transcripcion" / "transcripcion.json").read_text())
OUT_DIR = Path(os.environ.get("REEL_OUT", str(W / "03-render")))
OUT_DIR.mkdir(parents=True, exist_ok=True)
HOP = ENERGY["hop"]
DB = ENERGY["db"]

THR_DB = -26.0        # media local por debajo = pausa (pausas medidas -30..-42, voz -10..-25)
MIN_GAP = 0.22        # hueco interno mínimo a quitar
GAP_PAD = 0.07        # aire que se deja a cada lado de un hueco quitado
BLIP = 0.10           # un pico de ruido del parque más corto que esto no rompe la pausa
SPEED = 1.10          # ritmo de reel: voz 1.1x con tono preservado (atempo)
# Marca de agua «DJI OSMO POCKET 3» (x 53-422, y 300-350). Probado: removelogo con máscara deja un
# fantasma legible sobre cielo; delogo queda limpio sobre cielo y el parche en texturas lo tapa la
# etiqueta @tu_cuenta que Remotion pone encima (HandleTag).
DELOGO = "delogo=x=45:y=296:w=392:h=58"
FADE = 0.012

# (id, inicio, fin, congelado_al_final_s) en tiempo del crudo — ver PLAN.md
EDL = [
    ("S01", 23.48, 26.58, 0.0),
    ("S02", 35.92, 38.88, 0.0),
    ("S03", 42.20, 44.42, 0.0),
    ("S04", 240.60, 245.50, 0.0),
    ("S05", 51.48, 56.36, 0.0),
    ("S06", 63.04, 67.74, 0.0),
    ("S07", 73.26, 78.94, 0.0),
    ("S08", 83.72, 84.92, 0.55),
    ("S09", 87.10, 90.40, 0.0),   # 86.2-86.8 = «para eso» repetido (whisper lo ocultó en «usa»)
    ("S10", 91.36, 94.32, 0.0),
    ("S11", 95.16, 97.24, 0.0),
    ("S12", 252.10, 257.86, 0.0),
    ("S13", 98.06, 105.18, 0.0),
    ("S14", 112.78, 114.94, 0.0),
    ("S15", 139.22, 141.86, 0.0),
    # Empalme: «Cada 20 minutos» de la 1.ª toma + «escribe al soporte…» de la 2.ª.
    # 146.5-148.7 = toma fallida («escríbelele») que whisper ocultó; verificado con ventanas aisladas.
    ("S16", [(145.16, 146.22), (148.72, 151.22)], None, 0.0),
    ("S17", 152.40, 155.64, 0.45),
    ("S18", 155.64, 160.58, 0.0),
    ("S19", 198.28, 200.72, 0.0),
    ("S20", 205.36, 215.58, 0.0),
    # hueco de ~1 s (225.52-226.48) que el umbral no quitó: toma de 7.5 s sin cambios
    ("S22", [(221.72, 225.56), (226.46, 229.66)], None, 0.0),
    ("S23", 233.84, 237.84, 0.4),   # cola congelada: la «r» de «guardar» ya no cae en el último cuadro
]

# Correcciones de reconocimiento para subtítulos (lo dicho, bien escrito)
FIX = {
    "chayipiti": "ChatGPT", "cloud": "Claude", "cronjob": "Cron Job", "chrome": "Cron",
    "sias": "IAs", "tickets": "tickets", "ia": "IA",
}
# Correcciones puntuales por segmento (lapsus de lectura, no de reconocimiento)
FIX_SEG = {("S16", "el"): "al"}


def db_at(t):
    i = int(round(t / HOP))
    return DB[max(0, min(len(DB) - 1, i))]


def mean_db(t, win=0.04):
    n = int(win / HOP)
    i = int(round(t / HOP))
    window = DB[max(0, i - n): min(len(DB), i + n + 1)]
    return sum(window) / len(window)


def quiet_runs(start, end):
    """Pausas reales: tramos bajo umbral, fusionando picos de ruido cortos (BLIP)."""
    runs = []
    cur = None
    for k in range(int((end - start) / HOP) + 1):
        t = start + k * HOP
        if mean_db(t) < THR_DB:
            cur = [t, t] if cur is None else [cur[0], t]
        elif cur is not None:
            runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] <= BLIP:
            merged[-1] = [merged[-1][0], r[1]]
        else:
            merged.append(list(r))
    return [(ra, rb + HOP) for ra, rb in merged if rb + HOP - ra >= MIN_GAP]


SHORT_WORD = 0.45     # palabras reales cortas; las más largas suelen ser whisper estirando pausas


def protects_word(ra, rb):
    """Una pausa candidata no puede comerse una palabra corta real (p. ej. «tus» en S13)."""
    for w in all_words():
        d = w["end"] - w["start"]
        if 0 < d <= SHORT_WORD and min(rb, w["end"]) - max(ra, w["start"]) > 0.5 * d:
            return True
    return False


def valley(t_from, t_to):
    """Instante de menor energía en [t_from, t_to]."""
    best_t, best = t_from, 1e9
    t = t_from
    while t <= t_to:
        v = db_at(t)
        if v < best:
            best, best_t = v, t
        t += HOP
    return best_t


def refine(a, b, next_word_start=None, prev_word_end=None):
    lo = a - 0.22 if prev_word_end is None else max(a - 0.22, prev_word_end)
    start = valley(lo, a + 0.04)
    hi = b + 0.22 if next_word_start is None else min(b + 0.22, next_word_start + 0.02)
    end = valley(b - 0.06, hi)
    runs = [r for r in quiet_runs(start, end) if not protects_word(r[0], r[1])]
    # pausa pegada a los bordes: se recorta el borde
    if runs and runs[0][0] <= start + 0.05:
        start = max(start, runs[0][1] - GAP_PAD)
        runs = runs[1:]
    if runs and runs[-1][1] >= end - 0.05:
        end = min(end, runs[-1][0] + GAP_PAD)
        runs = runs[:-1]
    pieces, cur_a = [], start
    for ga, gb in runs:
        pieces.append((cur_a, ga + GAP_PAD))
        cur_a = gb - GAP_PAD
    pieces.append((cur_a, end))
    return [(round(x, 3), round(y, 3)) for x, y in pieces if y - x > 0.05]


def all_words():
    return [w for s in TRANS["segments"] for w in s.get("words", [])]


def build():
    words = all_words()
    starts = sorted(w["start"] for w in words)
    ends = sorted(w["end"] for w in words)
    timeline, filters, labels, new_t, idx = [], [], [], 0.0, 0
    for sid, a, b, freeze in EDL:
        ranges = a if isinstance(a, list) else [(a, b)]   # varios tramos = empalme de tomas
        pieces = []
        for ra, rb in ranges:
            nxt = next((s for s in starts if s > rb + 0.01), None)
            prv = next((e for e in reversed(ends) if e < ra - 0.01), None)
            pieces += refine(ra, rb, nxt, prv)
        seg = {"id": sid, "orig": [ranges[0][0], ranges[-1][1]], "new_start": round(new_t, 3), "pieces": [], "freeze": freeze}
        for k, (pa, pb) in enumerate(pieces):
            # Cuadros exactos por pieza: si video y audio difieren, concat rellena y el timeline
            # se desfasa (medido: ~0.5 s al final). Video = N cuadros; audio = N/30 s exactos.
            dur = (pb - pa) / SPEED
            n = max(1, round(dur * 30))
            last = k == len(pieces) - 1
            fz = round(freeze * 30) if last else 0
            total_s = (n + fz) / 30
            v = (f"[0:v]trim={pa}:{pb},{DELOGO},setpts=(PTS-STARTPTS)/{SPEED},fps=30,format=yuv420p,"
                 f"tpad=stop_mode=clone:stop_duration=0.2,trim=end_frame={n},setpts=PTS-STARTPTS"
                 + (f",tpad=stop_mode=clone:stop={fz}" if fz else "") + f"[v{idx}]")
            au = (f"[0:a]atrim={pa}:{pb},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,"
                  f"atempo={SPEED},afade=t=in:d={FADE},afade=t=out:st={max(0, min(dur, n / 30) - FADE):.4f}:d={FADE},"
                  f"apad=whole_dur={total_s:.6f},atrim=end={total_s:.6f},asetpts=PTS-STARTPTS[a{idx}]")
            filters += [v, au]
            labels.append(f"[v{idx}][a{idx}]")
            seg["pieces"].append({"orig": [pa, pb], "new": [round(new_t, 4), round(new_t + n / 30, 4)]})
            new_t += total_s
            idx += 1
        seg["new_end"] = round(new_t, 3)
        timeline.append(seg)

    voice = "highpass=f=85,afftdn=nf=-24:tn=1,acompressor=threshold=-20dB:ratio=3:attack=4:release=90:makeup=2"
    filters.append("".join(labels) + f"concat=n={idx}:v=1:a=1[vc][ac]")
    filters.append(f"[ac]{voice}[aout]")
    graph = ";\n".join(filters)
    (OUT_DIR / "base_graph.txt").write_text(graph)

    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(SRC), "-filter_complex_script", str(OUT_DIR / "base_graph.txt"),
           "-map", "[vc]", "-map", "[aout]", "-c:v", "libx264", "-crf", "15", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-g", "30", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
           "-movflags", "+faststart", str(OUT_DIR / "base.mp4")]
    if "--solo-plan" not in sys.argv:
        subprocess.run(cmd, check=True)

    # palabras en tiempo nuevo
    # Cada palabra va a la pieza con la que más se traslapa (whisper estira el inicio de la
    # palabra sobre la pausa previa: por punto medio se perdían «Pero», «Quiero», «Esta»…).
    mapped = []
    for seg in timeline:
        sa, sb = seg["orig"]
        for w in words:
            if not (sa - 0.3 <= (w["start"] + w["end"]) / 2 <= sb + 0.3):
                continue
            overlaps = [(min(p["orig"][1], w["end"]) - max(p["orig"][0], w["start"]), p) for p in seg["pieces"]]
            ov, p = max(overlaps, key=lambda x: x[0])
            if ov < 0.04:
                continue
            pa = p["orig"][0]
            n0, n1 = p["new"]
            raw = w["word"].strip()
            core = raw.strip(".,¿?¡!").lower()
            txt = FIX_SEG.get((seg["id"], core), FIX.get(core, raw.strip(".,")))
            mapped.append({"seg": seg["id"], "w": txt,
                           "s": round(max(n0, n0 + (w["start"] - pa) / SPEED), 3),
                           "e": round(min(n1, n0 + (w["end"] - pa) / SPEED), 3)})
    mapped.sort(key=lambda x: x["s"])
    total = round(new_t, 3)
    (OUT_DIR / "timeline.json").write_text(json.dumps(
        {"total": total, "segments": timeline, "words": mapped}, ensure_ascii=False, indent=1))
    print(f"piezas={idx} duracion={total:.2f}s palabras={len(mapped)}")
    for seg in timeline:
        cut = sum(p["orig"][1] - p["orig"][0] for p in seg["pieces"]) / SPEED
        print(f'{seg["id"]} nuevo {seg["new_start"]:6.2f}-{seg["new_end"]:6.2f} piezas={len(seg["pieces"])} voz={cut:.2f}s')


if __name__ == "__main__":
    build()
