import React from 'react';
import {Composition, staticFile} from 'remotion';
import {Reel} from './Reel';
import {FPS, Timeline} from './lib';

const EMPTY: Timeline = {total: 10, segments: [], words: []};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    fps={FPS}
    width={1080}
    height={1920}
    durationInFrames={300}
    defaultProps={{tl: EMPTY}}
    calculateMetadata={async ({props}) => {
      const res = await fetch(staticFile('data/timeline.json'));
      if (!res.ok) throw new Error(`No se pudo leer timeline.json (${res.status})`);
      const tl: Timeline = await res.json();
      return {durationInFrames: Math.ceil(tl.total * FPS), props: {...props, tl}};
    }}
  />
);
