import React from 'react';
import {AbsoluteFill, Img, Loop, OffthreadVideo, staticFile, useCurrentFrame} from 'remotion';
import type {Events} from './events';
import {FPS, clamp} from './lib';

const GRAIN_FRAMES = 4 * FPS; // film_grain.mp4 dura 4 s

export const Grain: React.FC = () => (
  <Loop durationInFrames={GRAIN_FRAMES}>
    <AbsoluteFill style={{mixBlendMode: 'overlay', opacity: 0.13}}>
      <OffthreadVideo src={staticFile('fx/film_grain.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </AbsoluteFill>
  </Loop>
);

export const Vignette: React.FC = () => (
  <AbsoluteFill style={{opacity: 0.5}}>
    <Img src={staticFile('fx/vignette.png')} style={{width: '100%', height: '100%'}} />
  </AbsoluteFill>
);

export const Flash: React.FC<{ev: Events}> = ({ev}) => {
  const t = useCurrentFrame() / FPS;
  const k = ev.flashes.reduce((acc, f) => {
    const d = t - f.t;
    return d < 0 || d > 0.2 ? acc : Math.max(acc, f.k * (1 - clamp(d / 0.2)));
  }, 0);
  if (k <= 0) return null;
  return <AbsoluteFill style={{background: '#fff', opacity: k}} />;
};
