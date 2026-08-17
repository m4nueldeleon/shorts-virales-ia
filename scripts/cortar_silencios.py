#!/usr/bin/env python3
"""Corte de silencios, muletillas y tomas falsas — el corazón del pipeline.

Detecta silencios por ENERGÍA real (silencedetect), fusiona con muletillas del
transcript y con intervalos KILL manuales, y re-renderiza frame-accurate con
micro-fades de audio (mata clics) + loudnorm. Genera el mapa tiempo-viejo →
tiempo-nuevo que usan subtítulos, SFX y overlays.

Uso:
  python cortar_silencios.py video.mp4
  python cortar_silencios.py video.mp4 --transcripcion transcripcion.json --muletillas --solo-plan
  python cortar_silencios.py video.mp4 --kill "12.3-14.1,55.0-57.2" --salida base_cut.mp4

Regla de oro: los cortes se hacen por energía de audio, NUNCA por timestamps de
palabras (whisper estira palabras sobre las pausas).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

Intervalo = Tuple[float, float]

# Muletillas como palabras completas (case-insensitive). Solo se marcan si están
# AISLADAS: pausa >= PAUSA_AISLADA a un lado — así "este" muletilla cae, pero
# "este proyecto" se respeta.
MULETILLAS_1 = {"eh", "eee", "mmm", "este", "pues", "um", "uh", "like"}
MULETILLAS_2 = {("o", "sea"), ("you", "know")}
PAUSA_AISLADA = 0.25   # s de pausa mínima a un lado para considerarla aislada
MARGEN_MULETILLA = 0.05  # s extra a cada lado del intervalo de la muletilla
MIN_SEGMENTO = 0.08    # s: segmentos a conservar más cortos se descartan
FADE_AUDIO = 0.012     # s: micro-fade en cada borde de audio (mata el clic)
LIMITE_INLINE = 100    # >100 segmentos → filtergraph a archivo (límite de argv)


def fallar(msg: str) -> "None":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def fmt_t(t: float) -> str:
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m):02d}:{s:05.2f}"


def verificar_binarios() -> None:
    for b in ("ffmpeg", "ffprobe"):
        if not shutil.which(b):
            fallar(f"no encuentro `{b}` en el PATH. Corre `bash scripts/setup.sh` primero.")


def probar_video(video: str) -> float:
    """Devuelve la duración; falla claro si no hay video o pista de audio."""
    def probe(args: List[str]) -> str:
        r = subprocess.run(["ffprobe", "-v", "error"] + args, capture_output=True, text=True)
        if r.returncode != 0:
            fallar(f"ffprobe no pudo leer `{video}`: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'archivo inválido'}")
        return r.stdout.strip()

    dur_txt = probe(["-show_entries", "format=duration", "-of", "default=nw=1:nk=1", video])
    try:
        dur = float(dur_txt)
    except ValueError:
        fallar(f"no pude leer la duración de `{video}` (¿archivo corrupto?)")
    if not probe(["-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", video]):
        fallar(f"`{video}` no tiene pista de audio; este script corta por energía de audio.")
    return dur


# ---------------------------------------------------------------- Paso 1: silencios
def detectar_silencios(video: str, noise_db: float, dur_min: float, dur_total: float) -> List[Intervalo]:
    """silencedetect por energía real; parsea silence_start/end del stderr."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", video,
           "-af", f"silencedetect=noise={noise_db}dB:d={dur_min}", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        fallar(f"silencedetect falló:\n{r.stderr.strip().splitlines()[-1] if r.stderr.strip() else '(sin detalle)'}")
    silencios: List[Intervalo] = []
    inicio: Optional[float] = None
    for linea in r.stderr.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", linea)
        if m:
            inicio = max(0.0, float(m.group(1)))
            continue
        m = re.search(r"silence_end:\s*(-?[\d.]+)", linea)
        if m and inicio is not None:
            silencios.append((inicio, min(float(m.group(1)), dur_total)))
            inicio = None
    if inicio is not None:  # silencio abierto hasta el final del archivo
        silencios.append((inicio, dur_total))
    return silencios


# ---------------------------------------------------------------- Paso 2: muletillas
def cargar_palabras(ruta: str) -> List[Dict]:
    """Acepta transcripcion.json de transcribir.py, formato whisper (segments→words)
    o una lista plana de palabras {word|text, start, end}."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        fallar(f"no pude leer la transcripción `{ruta}`: {e}")
    if isinstance(data, dict) and "segments" in data:
        crudas = [w for seg in data["segments"] for w in seg.get("words", [])]
    elif isinstance(data, dict) and "words" in data:
        crudas = data["words"]
    elif isinstance(data, list):
        crudas = data
    else:
        fallar(f"formato de transcripción no reconocido en `{ruta}` (espero words con start/end)")
    palabras = []
    for w in crudas:
        try:
            palabras.append({"texto": str(w.get("word", w.get("text", ""))).strip(),
                             "ini": float(w["start"]), "fin": float(w["end"])})
        except (KeyError, TypeError, ValueError):
            continue  # palabra sin timestamps: se ignora
    if not palabras:
        fallar(f"`{ruta}` no contiene palabras con timestamps (¿corriste scripts/transcribir.py?)")
    return sorted(palabras, key=lambda w: w["ini"])


def _norm(texto: str) -> str:
    return re.sub(r"[^\wáéíóúüñ]+", "", texto.lower(), flags=re.UNICODE)


def detectar_muletillas(palabras: List[Dict]) -> List[Dict]:
    """Muletillas es/en como palabra completa Y aisladas (pausa >= 0.25 s a un lado)."""
    def pausa_antes(i: int) -> float:
        return palabras[i]["ini"] - palabras[i - 1]["fin"] if i > 0 else 99.0

    def pausa_despues(i: int) -> float:
        return palabras[i + 1]["ini"] - palabras[i]["fin"] if i < len(palabras) - 1 else 99.0

    detectadas, usadas = [], set()
    for i in range(len(palabras) - 1):  # pares primero ("o sea", "you know")
        par = (_norm(palabras[i]["texto"]), _norm(palabras[i + 1]["texto"]))
        if par in MULETILLAS_2 and (pausa_antes(i) >= PAUSA_AISLADA or pausa_despues(i + 1) >= PAUSA_AISLADA):
            detectadas.append({"ini": palabras[i]["ini"], "fin": palabras[i + 1]["fin"],
                               "texto": f"{palabras[i]['texto']} {palabras[i + 1]['texto']}".strip()})
            usadas.update((i, i + 1))
    for i, w in enumerate(palabras):
        if i in usadas or _norm(w["texto"]) not in MULETILLAS_1:
            continue
        if pausa_antes(i) >= PAUSA_AISLADA or pausa_despues(i) >= PAUSA_AISLADA:
            detectadas.append({"ini": w["ini"], "fin": w["fin"], "texto": w["texto"].strip()})
    return sorted(detectadas, key=lambda d: d["ini"])


# ---------------------------------------------------------------- Paso 3: fusión
def parsear_kill(spec: str, dur: float) -> List[Intervalo]:
    """Parsea --kill "a1-b1,a2-b2" (segundos, tiempo ORIGINAL)."""
    kills = []
    for trozo in filter(None, (t.strip() for t in spec.split(","))):
        m = re.fullmatch(r"([\d.]+)\s*-\s*([\d.]+)", trozo)
        if not m:
            fallar(f"--kill: no entiendo `{trozo}` (formato: inicio-fin en segundos, ej. 12.3-14.1)")
        a, b = float(m.group(1)), float(m.group(2))
        if a >= b:
            fallar(f"--kill: intervalo inválido `{trozo}` (inicio debe ser < fin)")
        kills.append((max(0.0, a), min(b, dur)))
    return kills


def fusionar(intervalos: List[Intervalo]) -> List[Intervalo]:
    """Fusiona intervalos solapados/contiguos; devuelve lista nueva ordenada."""
    resultado: List[Intervalo] = []
    for a, b in sorted(intervalos):
        if resultado and a <= resultado[-1][1] + 1e-4:
            resultado[-1] = (resultado[-1][0], max(resultado[-1][1], b))
        else:
            resultado.append((a, b))
    return resultado


def segmentos_a_conservar(silencios: List[Intervalo], kills: List[Intervalo],
                          dur: float, pad: float) -> List[Intervalo]:
    """Complemento de lo removido. El pad encoge SOLO los silencios (cada lado
    respira ~pad s); kills y muletillas se quitan completos, ya traen su margen."""
    recortados = [(a + pad, b - pad) for a, b in silencios if (b - pad) - (a + pad) > 1e-3]
    remover = fusionar(recortados + kills)
    conservar, cursor = [], 0.0
    for a, b in remover:
        if a - cursor >= MIN_SEGMENTO:
            conservar.append((cursor, a))
        cursor = max(cursor, b)
    if dur - cursor >= MIN_SEGMENTO:
        conservar.append((cursor, dur))
    return conservar


# ---------------------------------------------------------------- Paso 4: mapa de tiempos
def construir_mapa(conservar: List[Intervalo]) -> List[Dict]:
    mapa, nuevo = [], 0.0
    for a, b in conservar:
        mapa.append({"viejo_ini": round(a, 4), "viejo_fin": round(b, 4), "nuevo_ini": round(nuevo, 4)})
        nuevo += b - a
    return mapa


def mapear(t_viejo: float, mapa: List[Dict]) -> Optional[float]:
    """Tiempo original → tiempo del video cortado, o None si ese instante se eliminó.
    Importable: from cortar_silencios import mapear."""
    for seg in mapa:
        if seg["viejo_ini"] <= t_viejo <= seg["viejo_fin"]:
            return round(seg["nuevo_ini"] + (t_viejo - seg["viejo_ini"]), 4)
    return None


# ---------------------------------------------------------------- Paso 5: render
def construir_filtergraph(conservar: List[Intervalo]) -> str:
    """trim/atrim por segmento + afade 12 ms en cada borde + concat + loudnorm.
    Nota: cualquier expresión con comas iría en comillas simples (aquí solo hay
    parámetros numéricos, no hace falta)."""
    lineas, entradas = [], []
    for i, (a, b) in enumerate(conservar):
        d = b - a
        st_out = max(0.0, d - FADE_AUDIO)
        lineas.append(f"[0:v]trim=start={a:.4f}:end={b:.4f},setpts=PTS-STARTPTS[v{i}];")
        lineas.append(f"[0:a]atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:st=0:d={FADE_AUDIO},afade=t=out:st={st_out:.4f}:d={FADE_AUDIO}[a{i}];")
        entradas.append(f"[v{i}][a{i}]")
    lineas.append(f"{''.join(entradas)}concat=n={len(conservar)}:v=1:a=1[vc][ca];")
    lineas.append("[ca]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[ac]")
    return "\n".join(lineas)


def renderizar(video: str, graph: str, salida: str) -> None:
    n_segs = graph.count("[0:v]")
    base = ["ffmpeg", "-y", "-hide_banner", "-i", video]
    cola = ["-map", "[vc]", "-map", "[ac]", "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", salida]
    if n_segs > LIMITE_INLINE:  # límite de argv → filtergraph a archivo
        ruta_graph = salida + ".filtergraph.txt"
        with open(ruta_graph, "w", encoding="utf-8") as f:
            f.write(graph)
        print(f"→ {n_segs} segmentos: filtergraph escrito en {ruta_graph}")
        r = subprocess.run(base + ["-/filter_complex", ruta_graph] + cola, capture_output=True, text=True)
        if r.returncode != 0 and ("Unrecognized option" in r.stderr or "Error splitting" in r.stderr):
            # ffmpeg < 7: la sintaxis -/opt no existe; fallback equivalente
            r = subprocess.run(base + ["-filter_complex_script", ruta_graph] + cola, capture_output=True, text=True)
    else:
        r = subprocess.run(base + ["-filter_complex", graph] + cola, capture_output=True, text=True)
    if r.returncode != 0:
        detalle = "\n".join(r.stderr.strip().splitlines()[-12:])
        fallar(f"el render de ffmpeg falló:\n{detalle}")


# ---------------------------------------------------------------- plan / main
def imprimir_plan(silencios, muletillas, kills, conservar, dur) -> None:
    dur_final = sum(b - a for a, b in conservar)
    print(f"\n— PLAN DE CORTE ————————————————————————————")
    print(f"Silencios detectados: {len(silencios)}")
    for a, b in silencios:
        print(f"  · {fmt_t(a)}–{fmt_t(b)}  ({b - a:.2f}s)")
    if muletillas:
        print(f"Muletillas aisladas: {len(muletillas)}  (revisa y ajusta con --kill si alguna debe quedarse)")
        for m in muletillas:
            print(f"  · {fmt_t(m['ini'])}–{fmt_t(m['fin'])}  «{m['texto']}»")
    if kills:
        print(f"KILL manual: {len(kills)}")
        for a, b in kills:
            print(f"  · {fmt_t(a)}–{fmt_t(b)}")
    print(f"Segmentos a conservar: {len(conservar)}")
    print(f"Duración: {fmt_t(dur)} → {fmt_t(dur_final)}  (se quitan {dur - dur_final:.1f}s, {100 * (dur - dur_final) / dur:.0f}%)")
    print("—————————————————————————————————————————————\n")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Corta silencios (por energía real), muletillas y tomas falsas; "
                    "renderiza frame-accurate con micro-fades + loudnorm y genera el "
                    "mapa tiempo-viejo → tiempo-nuevo.",
        epilog='Ejemplo: python cortar_silencios.py crudo.mp4 --transcripcion transcripcion.json '
               '--muletillas --kill "83.2-96.0" --solo-plan')
    p.add_argument("video", help="video de entrada (cualquier formato que lea ffmpeg)")
    p.add_argument("--transcripcion", metavar="JSON", help="transcripcion.json word-level (de scripts/transcribir.py)")
    p.add_argument("--kill", default="", metavar='"a-b,c-d"', help="intervalos a eliminar en tiempo ORIGINAL, ej. \"12.3-14.1,55-57.2\"")
    p.add_argument("--muletillas", action="store_true", help="detectar y cortar muletillas aisladas (requiere --transcripcion)")
    p.add_argument("--noise", type=float, default=-30, help="umbral de silencio en dB (default: -30)")
    p.add_argument("--dur", type=float, default=0.40, help="duración mínima de silencio en s (default: 0.40)")
    p.add_argument("--pad", type=float, default=0.15, help="respiración que se deja en cada borde del corte, en s (default: 0.15)")
    p.add_argument("--salida", default="base_cut.mp4", help="video de salida (default: base_cut.mp4)")
    p.add_argument("--mapa", default="mapa_tiempos.json", help="mapa viejo→nuevo en JSON (default: mapa_tiempos.json)")
    p.add_argument("--solo-plan", action="store_true", help="solo imprime el plan de corte, sin renderizar ni escribir archivos")
    args = p.parse_args()

    verificar_binarios()
    dur = probar_video(args.video)

    silencios = detectar_silencios(args.video, args.noise, args.dur, dur)
    kills = parsear_kill(args.kill, dur) if args.kill else []

    muletillas: List[Dict] = []
    if args.muletillas:
        if not args.transcripcion:
            fallar("--muletillas requiere --transcripcion (corre antes scripts/transcribir.py)")
        muletillas = detectar_muletillas(cargar_palabras(args.transcripcion))
    kills_muletillas = [(max(0.0, m["ini"] - MARGEN_MULETILLA), min(dur, m["fin"] + MARGEN_MULETILLA))
                        for m in muletillas]

    conservar = segmentos_a_conservar(silencios, kills + kills_muletillas, dur, args.pad)
    if not conservar:
        fallar("no quedó ningún segmento que conservar; revisa --noise/--dur/--kill.")

    imprimir_plan(silencios, muletillas, kills, conservar, dur)
    if args.solo_plan:
        print("Modo --solo-plan: no se renderiza. Quita el flag para producir el corte.")
        return

    mapa = construir_mapa(conservar)
    with open(args.mapa, "w", encoding="utf-8") as f:
        json.dump(mapa, f, ensure_ascii=False, indent=1)
    print(f"✓ Mapa de tiempos → {args.mapa}  ({len(mapa)} segmentos)")

    print(f"Renderizando {len(conservar)} segmentos (micro-fade {FADE_AUDIO * 1000:.0f} ms + loudnorm)…")
    renderizar(args.video, construir_filtergraph(conservar), args.salida)
    print(f"✓ Corte listo → {args.salida}")
    print("Siguiente: subtítulos/SFX/overlays van en tiempo NUEVO — usa mapear() con el mapa.")


if __name__ == "__main__":
    main()
