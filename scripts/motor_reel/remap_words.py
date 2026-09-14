"""Reubica palabras ya transcritas de una base vieja a una base nueva sin volver a transcribir.

Whisper cambia su salida entre corridas («todas las IAs» → «toda la CIA»); cuando solo cambia un
tramo de la EDL, las palabras se pasan exactas: tiempo viejo → tiempo del crudo → tiempo nuevo.
Las palabras cuyo audio ya no está en la base nueva se descartan.

Uso: python3 remap_words.py <timeline_viejo> <words_viejo> <timeline_nuevo> <words_salida>
"""
import json
import sys

SPEED = 1.10


def pieces(tl):
    return [p for s in tl["segments"] for p in s["pieces"]]


def old_to_orig(t, old_pieces):
    for p in old_pieces:
        n0, n1 = p["new"]
        if n0 - 1e-3 <= t <= n1 + 0.6:   # +0.6: congelados al final de una pieza
            return p["orig"][0] + (min(t, n1) - n0) * SPEED
    return None


def orig_to_new(o, new_pieces):
    for p in new_pieces:
        a, b = p["orig"]
        if a - 0.02 <= o <= b + 0.02:
            return p["new"][0] + (min(max(o, a), b) - a) / SPEED
    return None


def main(old_tl_path, old_words_path, new_tl_path, out_path):
    old_p = pieces(json.load(open(old_tl_path)))
    new_p = pieces(json.load(open(new_tl_path)))
    raw = json.load(open(old_words_path))
    kept, dropped = 0, []
    segments = []
    for s in raw["segments"]:
        words = []
        for w in s.get("words", []):
            o_s, o_e = old_to_orig(w["start"], old_p), old_to_orig(w["end"], old_p)
            n_s = orig_to_new(o_s, new_p) if o_s is not None else None
            n_e = orig_to_new(o_e, new_p) if o_e is not None else None
            if n_s is None and n_e is None:
                dropped.append(w["word"].strip())
                continue
            n_s = n_e - 0.2 if n_s is None else n_s
            n_e = n_s + 0.2 if n_e is None else n_e
            words.append({**w, "start": round(n_s, 3), "end": round(max(n_e, n_s + 0.05), 3)})
            kept += 1
        if words:
            segments.append({**s, "start": words[0]["start"], "end": words[-1]["end"], "words": words})
    json.dump({**raw, "segments": segments}, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f"palabras reubicadas={kept} descartadas={len(dropped)}: {' '.join(dropped)}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
