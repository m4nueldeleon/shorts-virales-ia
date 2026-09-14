import React from 'react';
import {AbsoluteFill, OffthreadVideo, random, staticFile, useCurrentFrame} from 'remotion';
import type {Events} from './events';
import {ACCENT, FPS, INK, Timeline, clamp, easeInOut} from './lib';

const WHIP = 0.13;
const pulse = (d: number) => (d < 0 ? 0 : d < 0.08 ? d / 0.08 : Math.exp(-(d - 0.08) * 4.2));

/** Cámara virtual: alternancia de escala por toma, push-in lento, zoom punch, riser, shake y whip. */
const cameraAt = (t: number, tl: Timeline, ev: Events) => {
  const idx = Math.max(0, tl.segments.findIndex((s) => t >= s.new_start && t < s.new_end));
  const seg = tl.segments[idx];
  const prog = clamp((t - seg.new_start) / Math.max(0.1, seg.new_end - seg.new_start));
  const base = (idx % 2 === 1 ? 1.07 : 1.0) + 0.035 * prog;
  const punch = ev.punches.reduce((acc, p) => acc + p.amt * pulse(t - p.t), 0);
  const rise = t >= ev.riser.a && t < ev.riser.b ? 0.14 * easeInOut((t - ev.riser.a) / (ev.riser.b - ev.riser.a)) : 0;

  const shake = ev.shakes.reduce(
    (acc, s) => {
      const d = t - s.t;
      if (d < 0 || d >= s.d) return acc;
      const k = s.amp * (1 - d / s.d);
      return {x: acc.x + k * Math.sin(d * 95), y: acc.y + k * Math.cos(d * 73)};
    },
    {x: 0, y: 0},
  );
  const whip = ev.whips.reduce(
    (acc, w) => {
      const d = t - w;
      if (Math.abs(d) >= WHIP) return acc;
      const k = 1 - Math.abs(d) / WHIP;
      // 150·k² < margen del zoom (0.25·k·0.4·1920 ≈ 192·k): sin franja negra en el borde superior
      return {y: acc.y + (d < 0 ? -1 : 1) * 150 * k * k, blur: acc.blur + 24 * k, zoom: acc.zoom + 0.25 * k};
    },
    {y: 0, blur: 0, zoom: 0},
  );
  return {zoom: base + punch + rise + whip.zoom, x: shake.x, y: shake.y + whip.y, blur: whip.blur};
};

const GlitchSlices: React.FC<{frame: number; style: React.CSSProperties}> = ({frame, style}) => (
  <>
    {[0, 1, 2, 3].map((i) => {
      const top = random(`gt-${frame}-${i}`) * 88;
      const h = 3 + random(`gh-${frame}-${i}`) * 9;
      const dx = (random(`gx-${frame}-${i}`) - 0.5) * 160;
      return (
        <AbsoluteFill
          key={i}
          style={{clipPath: `inset(${top}% 0 ${Math.max(0, 100 - top - h)}% 0)`, transform: `translateX(${dx}px)`}}
        >
          <OffthreadVideo src={staticFile('base.mp4')} muted style={style} />
        </AbsoluteFill>
      );
    })}
    <AbsoluteFill
      style={{background: ACCENT, mixBlendMode: 'color', opacity: random(`gc-${frame}`) > 0.5 ? 0.22 : 0.06}}
    />
  </>
);

export const VideoLayer: React.FC<{tl: Timeline; ev: Events}> = ({tl, ev}) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const cam = cameraAt(t, tl, ev);
  const glitch = ev.glitches.find((g) => t >= g.a && t <= g.b);
  const filter = [cam.blur > 0.5 ? `blur(${cam.blur.toFixed(1)}px)` : '', glitch ? 'grayscale(0.6) contrast(1.3)' : '']
    .filter(Boolean)
    .join(' ');
  const style: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    transformOrigin: '50% 40%',
    transform: `translate(${cam.x.toFixed(1)}px, ${cam.y.toFixed(1)}px) scale(${cam.zoom.toFixed(4)})`,
    filter: filter || undefined,
  };
  return (
    <AbsoluteFill style={{backgroundColor: INK, overflow: 'hidden'}}>
      <OffthreadVideo src={staticFile('base.mp4')} style={style} />
      {glitch && <GlitchSlices frame={frame} style={style} />}
    </AbsoluteFill>
  );
};
