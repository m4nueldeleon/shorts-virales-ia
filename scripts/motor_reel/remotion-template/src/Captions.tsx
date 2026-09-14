import React, {useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {ACCENT, DISPLAY, FPS, Win, Word, pop} from './lib';

type Chunk = {words: Word[]; a: number; b: number};

const MAX_WORDS = 3;
const MAX_CHARS = 16;
const BREAK_GAP = 0.35;
const HOLD = 0.3;

const chunkWords = (words: Word[]): Chunk[] => {
  const groups = words.reduce<Word[][]>((acc, w) => {
    const cur = acc[acc.length - 1];
    const prev = cur?.[cur.length - 1];
    const text = [...(cur ?? []), w].map((x) => x.w).join(' ');
    const split =
      !cur ||
      prev.seg !== w.seg ||
      w.s - prev.e > BREAK_GAP ||
      cur.length >= MAX_WORDS ||
      text.length > MAX_CHARS;
    return split ? [...acc, [w]] : [...acc.slice(0, -1), [...cur, w]];
  }, []);
  return groups.map((g, i) => {
    const next = groups[i + 1];
    const end = g[g.length - 1].e + HOLD;
    return {words: g, a: g[0].s, b: next ? Math.min(next[0].s, end) : end};
  });
};

/** Subtítulos estilo Hormozi: un solo estilo en todo el video, palabra dicha en acento. */
export const Captions: React.FC<{words: Word[]; hide: Win[]}> = ({words, hide}) => {
  const t = useCurrentFrame() / FPS;
  const chunks = useMemo(() => chunkWords(words), [words]);
  if (hide.some((h) => t >= h.a && t <= h.b)) return null;
  const chunk = chunks.find((c) => t >= c.a && t < c.b);
  if (!chunk) return null;
  const p = pop(t, chunk.a);
  const active = chunk.words.reduce((idx, w, i) => (w.s <= t + 0.02 ? i : idx), 0);

  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: 80,
          right: 130,
          top: 1165,
          height: 250,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 90,
            lineHeight: 1.05,
            textTransform: 'uppercase',
            textAlign: 'center',
            letterSpacing: -1,
            color: '#fff',
            WebkitTextStroke: '18px #000',
            paintOrder: 'stroke fill',
            textShadow: '0 10px 22px rgba(0,0,0,.5)',
            opacity: p.opacity,
            transform: `scale(${p.scale})`,
          }}
        >
          {chunk.words.map((w, i) => (
            <span
              key={`${w.s}-${i}`}
              style={{
                color: i === active ? ACCENT : '#fff',
                display: 'inline-block',
                transform: i === active ? 'scale(1.06)' : undefined,
                margin: '0 24px', // el contorno de 18 px se come un margen menor

              }}
            >
              {w.w}
            </span>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
