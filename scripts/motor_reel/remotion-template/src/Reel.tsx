import React, {useMemo} from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {AudioLayer} from './AudioLayer';
import {Captions} from './Captions';
import {ChatCard, MailCard, PromptCard, TemplateCard} from './Cards';
import {buildEvents, Events} from './events';
import {useFonts} from './fonts';
import {Flash, Grain, Vignette} from './Fx';
import {FPS, INK, Timeline, easeOut} from './lib';
import {ClockTimelapse, Chip, HandleTag, HookTitle, IconList, LogoRow, Reveal, SaveCTA, Stamp, Success, UsesRow} from './Titles';
import {VideoLayer} from './VideoLayer';

const BRoll: React.FC<{src: string}> = ({src}) => {
  const f = useCurrentFrame();
  const s = 1.1 - 0.1 * easeOut(f / 6);
  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: INK}}>
      <OffthreadVideo src={staticFile(src)} muted style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${s})`}} />
    </AbsoluteFill>
  );
};

const Overlays: React.FC<{ev: Events}> = ({ev}) => {
  const t = useCurrentFrame() / FPS;
  return (
    <>
      <HookTitle t={t} b={ev.hook.b} />
      <Chip t={t} a={ev.halloween.a} b={ev.halloween.b} top={1010} text="Fiesta de Halloween" img="icons/pumpkin-color.svg" />
      <Stamp t={t} a={ev.stamp.a} b={ev.stamp.b} top={800} text="Sin boletos" />
      <ChatCard t={t} {...ev.chat} />
      <MailCard t={t} {...ev.mail} />
      <Reveal t={t} {...ev.reveal} />
      <LogoRow t={t} {...ev.logos} top={740} />
      <IconList t={t} {...ev.uses13} top={820} />
      <PromptCard t={t} {...ev.prompt} />
      <ClockTimelapse t={t} {...ev.clock} />
      <Success t={t} {...ev.success} top={1000} />
      <TemplateCard t={t} {...ev.template} />
      <UsesRow t={t} {...ev.uses22} top={830} />
      <SaveCTA t={t} {...ev.save} />
    </>
  );
};

export const Reel: React.FC<{tl: Timeline}> = ({tl}) => {
  useFonts();
  const ev = useMemo(() => buildEvents(tl), [tl]);
  return (
    <AbsoluteFill style={{backgroundColor: INK}}>
      <VideoLayer tl={tl} ev={ev} />
      {ev.broll.map((b) => (
        <Sequence key={b.src} from={Math.round(b.a * FPS)} durationInFrames={Math.max(1, Math.round(b.d * FPS))}>
          <BRoll src={b.src} />
        </Sequence>
      ))}
      <Vignette />
      <Grain />
      <HandleTag />
      <Overlays ev={ev} />
      <Captions words={tl.words} hide={ev.captionHide} />
      <Flash ev={ev} />
      <AudioLayer ev={ev} total={tl.total} />
    </AbsoluteFill>
  );
};
