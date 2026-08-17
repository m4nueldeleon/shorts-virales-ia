#!/usr/bin/env python3
"""Puente transcripcion.json (+ mapa_tiempos.json) → captions.json.

Agrupa las palabras word-level en bloques de 3-4 palabras (un bloque = una
pantalla de subtítulo), convierte cada timestamp al tiempo NUEVO del video ya
cortado usando el mapa de cortar_silencios.py, y descarta las palabras que
cayeron en tramos eliminados. El captions.json resultante es el formato que
consume scripts/caption.html + scripts/render_captions.py:

    [{"start": s, "end": s, "words": [{"w": "PALABRA", "s": s}, ...]}, ...]

Uso:
  python generar_captions.py --transcripcion transcripcion.json --mapa mapa_tiempos.json
  python generar_captions.py --transcripcion transcripcion.json --sin-mapa   # video sin cortes
  Opciones: --palabras 3 (por pantalla) · --pausa 0.6 (corte de bloque en gaps mayores)
            --salida captions.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cortar_silencios import mapear  # noqa: E402


def cargar_palabras(ruta: str):
    data = json.load(open(ruta, encoding="utf-8"))
    palabras = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            texto = w["w"].strip()
            if texto:
                palabras.append({"w": texto, "start": float(w["start"]), "end": float(w["end"])})
    return palabras


def remapear(palabras, mapa):
    """Convierte a tiempo nuevo; descarta palabras eliminadas por el corte."""
    out = []
    for w in palabras:
        s = mapear(w["start"], mapa)
        e = mapear(w["end"], mapa)
        if s is None and e is None:
            continue  # la palabra completa cayó en un tramo cortado
        if s is None:
            s = max(0.0, e - (w["end"] - w["start"]))
        if e is None:
            e = s + (w["end"] - w["start"])
        out.append({"w": w["w"], "start": round(s, 3), "end": round(e, 3)})
    return out


def agrupar(palabras, por_pantalla: int, pausa_corte: float):
    """Bloques de N palabras; corta antes si hay un gap > pausa_corte (respiro/frase)."""
    bloques, actual = [], []
    for w in palabras:
        if actual:
            gap = w["start"] - actual[-1]["end"]
            if len(actual) >= por_pantalla or gap > pausa_corte:
                bloques.append(actual)
                actual = []
        actual.append(w)
    if actual:
        bloques.append(actual)

    captions = []
    for i, b in enumerate(bloques):
        fin_natural = b[-1]["end"] + 0.15
        # el bloque no debe pisar el inicio del siguiente
        fin = min(fin_natural, bloques[i + 1][0]["start"]) if i + 1 < len(bloques) else fin_natural
        captions.append({
            "start": round(b[0]["start"], 3),
            "end": round(max(fin, b[0]["start"] + 0.2), 3),
            "words": [{"w": w["w"].upper(), "s": w["start"]} for w in b],
        })
    return captions


def main():
    p = argparse.ArgumentParser(description="Genera captions.json para render_captions.py "
                                            "desde la transcripción word-level y el mapa de cortes.")
    p.add_argument("--transcripcion", required=True, help="transcripcion.json (de scripts/transcribir.py)")
    p.add_argument("--mapa", help="mapa_tiempos.json (de scripts/cortar_silencios.py)")
    p.add_argument("--sin-mapa", action="store_true",
                   help="el video no se cortó: usar los tiempos originales tal cual")
    p.add_argument("--palabras", type=int, default=3, help="palabras por pantalla (default: 3, máx recomendado 4)")
    p.add_argument("--pausa", type=float, default=0.6, help="gap en s que fuerza bloque nuevo (default: 0.6)")
    p.add_argument("--salida", default="captions.json")
    a = p.parse_args()

    if not a.mapa and not a.sin_mapa:
        p.error("pasa --mapa mapa_tiempos.json, o --sin-mapa si el video no se cortó")

    palabras = cargar_palabras(a.transcripcion)
    if not palabras:
        raise SystemExit("❌ La transcripción no tiene palabras word-level.")

    if a.sin_mapa:
        remapeadas = [{"w": w["w"], "start": round(w["start"], 3), "end": round(w["end"], 3)}
                      for w in palabras]
    else:
        mapa = json.load(open(a.mapa, encoding="utf-8"))
        remapeadas = remapear(palabras, mapa)

    captions = agrupar(remapeadas, a.palabras, a.pausa)
    json.dump(captions, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    dur = captions[-1]["end"] if captions else 0
    print(f"✅ {a.salida}: {len(captions)} bloques · {len(remapeadas)}/{len(palabras)} palabras "
          f"(las demás cayeron en cortes) · última pantalla termina en {dur:.2f}s")
    print(f"   Siguiente paso: python scripts/render_captions.py --captions {a.salida} --duracion <dur_video>")


if __name__ == "__main__":
    main()
