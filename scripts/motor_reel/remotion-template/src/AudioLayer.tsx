import React from 'react';
import {Audio, Sequence, staticFile} from 'remotion';
import type {Events} from './events';
import {FPS, clamp, vis} from './lib';

/** Música bajo la voz; se corta en los cliffhangers y vuelve de golpe en la revelación. */
const musicVolume = (t: number, ev: Events, total: number) => {
  const cut = ev.musicCuts.reduce((acc, c) => Math.max(acc, vis(t, c.a, c.b, 0.05, 0.03)), 0);
  const tail = clamp((total - t) / 0.4);
  return ev.musicGain * (1 - cut) * tail;
};

export const AudioLayer: React.FC<{ev: Events; total: number}> = ({ev, total}) => (
  <>
    <Audio src={staticFile('music/bed.mp3')} volume={(f) => musicVolume(f / FPS, ev, total)} />
    {ev.sfx.map((s, i) => {
      const len = Math.max(1, Math.round(s.len * FPS));
      return (
        <Sequence key={`${s.file}-${i}`} from={Math.round(s.t * FPS)} durationInFrames={len} layout="none">
          <Audio src={staticFile(`sfx/${s.file}`)} volume={(f) => s.vol * clamp((len - f) / (0.12 * FPS))} />
        </Sequence>
      );
    })}
  </>
);
