import React from 'react';
import {staticFile} from 'remotion';

export type Word = {seg: string; w: string; s: number; e: number};
export type Piece = {orig: [number, number]; new: [number, number]};
export type Segment = {
  id: string;
  orig: [number, number];
  new_start: number;
  new_end: number;
  pieces: Piece[];
  freeze: number;
};
export type Timeline = {total: number; segments: Segment[]; words: Word[]};
export type Win = {a: number; b: number};

export const FPS = 30;
// Un solo acento: naranja Halloween. Base neutra tinta/blanco.
export const ACCENT = '#FF7A1A';
export const ACCENT_TINT = '#FFE6D3';
export const INK = '#0E0E10';
export const MUTED = '#6B6B73';
export const DISPLAY = "'Archivo Black', 'Poppins', sans-serif";
export const BODY = "'Poppins', sans-serif";

export const norm = (s: string) =>
  s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '');

/** Resuelve tiempos del timeline nuevo a partir de segmentos y palabras dichas. */
export const makeTime = (tl: Timeline) => {
  const seg = (id: string) => {
    const found = tl.segments.find((x) => x.id === id);
    if (!found) throw new Error(`Segmento inexistente: ${id}`);
    return found;
  };
  // Busca por ventana de tiempo del segmento (±0.3 s), no por la etiqueta: la última palabra de
  // un tramo a veces queda asignada al siguiente.
  const W = (id: string, q: string, nth = 0, edge: 's' | 'e' = 's') => {
    const s = seg(id);
    const hits = tl.words.filter(
      (w) => w.s >= s.new_start - 0.3 && w.s <= s.new_end + 0.1 && norm(w.w).startsWith(norm(q)),
    );
    const hit = hits[nth];
    if (!hit) throw new Error(`Palabra inexistente: ${id} "${q}" #${nth}`);
    return edge === 's' ? hit.s : hit.e;
  };
  return {
    S: (id: string) => seg(id).new_start,
    E: (id: string) => seg(id).new_end,
    speechEnd: (id: string) => {
      const s = seg(id);
      return s.pieces[s.pieces.length - 1].new[1];
    },
    W,
  };
};

export const clamp = (x: number, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, x));
export const easeOut = (x: number) => 1 - Math.pow(1 - clamp(x), 3);
export const easeInOut = (x: number) => {
  const c = clamp(x);
  return c < 0.5 ? 4 * c * c * c : 1 - Math.pow(-2 * c + 2, 3) / 2;
};
const backOut = (x: number) => {
  const c1 = 1.70158;
  const c = clamp(x) - 1;
  return 1 + (c1 + 1) * c * c * c + c1 * c * c;
};

/** Visibilidad 0..1 dentro de [a,b] con entrada y salida suaves. */
export const vis = (t: number, a: number, b: number, fi = 0.16, fo = 0.16) => {
  if (t < a || t > b) return 0;
  const inn = fi <= 0.001 ? 1 : easeOut((t - a) / fi);
  const out = fo <= 0.001 ? 1 : easeOut((b - t) / fo);
  return Math.min(inn, out);
};

/** Entrada tipo pop: nunca desde scale(0); 0.9 → 1 con rebote corto. */
export const pop = (t: number, a: number) => ({
  opacity: easeOut((t - a) / 0.1),
  scale: t < a ? 0.9 : 0.9 + 0.1 * backOut((t - a) / 0.24),
});

export const plate = (size: number, bg: string, radius = 0.28): React.CSSProperties => ({
  width: size,
  height: size,
  borderRadius: size * radius,
  background: bg,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  flexShrink: 0,
});

/** Ícono SVG monocromo (simple-icons / Lucide) teñido por máscara. */
export const Icon: React.FC<{name: string; size: number; color: string; style?: React.CSSProperties}> = ({
  name,
  size,
  color,
  style,
}) => {
  const url = `url(${staticFile(`icons/${name}.svg`)})`;
  return (
    <div
      style={{
        width: size,
        height: size,
        flexShrink: 0,
        backgroundColor: color,
        WebkitMaskImage: url,
        maskImage: url,
        WebkitMaskSize: 'contain',
        maskSize: 'contain',
        WebkitMaskRepeat: 'no-repeat',
        maskRepeat: 'no-repeat',
        WebkitMaskPosition: 'center',
        maskPosition: 'center',
        ...style,
      }}
    />
  );
};

export const strokeText = (size: number, color = '#fff', stroke = 16): React.CSSProperties => ({
  fontFamily: DISPLAY,
  fontSize: size,
  lineHeight: 1.02,
  color,
  textTransform: 'uppercase',
  textAlign: 'center',
  letterSpacing: -1.5,
  WebkitTextStroke: stroke ? `${stroke}px #000` : undefined,
  paintOrder: 'stroke fill',
  textShadow: stroke ? '0 10px 24px rgba(0,0,0,.45)' : 'none',
});
