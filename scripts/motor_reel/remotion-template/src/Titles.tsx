import React from 'react';
import {AbsoluteFill, Img, random, staticFile} from 'remotion';
import {ACCENT, BODY, DISPLAY, INK, Icon, clamp, easeOut, plate, pop, strokeText, vis} from './lib';

const SIDE_L = 70;
const SIDE_R = 130;
const HOOK_TOP = 740;

const Band: React.FC<{top: number; children: React.ReactNode; style?: React.CSSProperties}> = ({top, children, style}) => (
  <div
    style={{position: 'absolute', top, left: SIDE_L, right: SIDE_R, display: 'flex', flexDirection: 'column', alignItems: 'center', ...style}}
  >
    {children}
  </div>
);

const fadeOutAfter = (t: number, b: number, d = 0.2) => (t > b ? 1 - easeOut((t - b) / d) : 1);

/**
 * Etiqueta fija de la cuenta. Cubre exactamente la zona de la marca de agua de la cámara
 * (x 53-422, y 300-350) para que no se note el parche de delogo, y protege contra reposteos.
 */
export const HandleTag: React.FC = () => (
  <AbsoluteFill>
    <div
      style={{
        position: 'absolute',
        left: 40,
        top: 290,
        height: 70,
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '0 28px 0 18px',
        borderRadius: 999,
        background: 'rgba(14,14,16,.66)',
      }}
    >
      <div style={{width: 20, height: 20, borderRadius: 10, background: ACCENT}} />
      <div style={{fontFamily: BODY, fontWeight: 900, fontSize: 38, color: '#fff', letterSpacing: -0.5}}>@tu_cuenta</div>
    </div>
  </AbsoluteFill>
);

// Promesa fiel a la historia (compró boletos por una cancelación): nada de «entré sin boletos».
// Las tres líneas desde el cuadro 0 para que el primer frame ya diga «IA».
export const HookTitle: React.FC<{t: number; b: number}> = ({t, b}) => {
  if (t > b + 0.22) return null;
  const out = t > b ? easeOut((t - b) / 0.22) : 0;
  const settle = 1.05 - 0.05 * easeOut(t / 0.3);
  return (
    <AbsoluteFill>
      <Band top={HOOK_TOP} style={{gap: 18, opacity: 1 - out, transform: `translateY(${-50 * out}px) scale(${settle})`}}>
        <div style={strokeText(78)}>No teníamos boletos…</div>
        <div
          style={{...strokeText(96, INK, 0), background: ACCENT, padding: '8px 30px 16px', borderRadius: 20, transform: 'rotate(-2.5deg)', whiteSpace: 'nowrap'}}
        >
          y la IA
        </div>
        <div style={{...strokeText(86), whiteSpace: 'nowrap'}}>los consiguió</div>
      </Band>
    </AbsoluteFill>
  );
};

export const Chip: React.FC<{t: number; a: number; b: number; top: number; text: string; img: string}> = ({t, a, b, top, text, img}) => {
  const v = vis(t, a, b, 0.12, 0.16);
  if (!v) return null;
  const p = pop(t, a);
  return (
    <AbsoluteFill>
      <Band top={top}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            background: '#fff',
            borderRadius: 999,
            padding: '12px 32px 12px 14px',
            opacity: v * p.opacity,
            transform: `scale(${p.scale})`,
            boxShadow: '0 18px 40px rgba(0,0,0,.35)',
          }}
        >
          <Img src={staticFile(img)} style={{width: 76, height: 76}} />
          <div style={{fontFamily: BODY, fontWeight: 900, fontSize: 46, color: INK}}>{text}</div>
        </div>
      </Band>
    </AbsoluteFill>
  );
};

export const Stamp: React.FC<{t: number; a: number; b: number; top: number; text: string}> = ({t, a, b, top, text}) => {
  if (t < a || t > b) return null;
  const k = easeOut((t - a) / 0.13);
  const out = vis(t, a, b, 0.001, 0.18);
  return (
    <AbsoluteFill>
      <Band top={top}>
        <div
          style={{
            opacity: clamp((t - a) / 0.05) * out,
            transform: `rotate(-8deg) scale(${1.7 - 0.7 * k})`,
            border: `12px solid ${ACCENT}`,
            borderRadius: 24,
            padding: '6px 36px 14px',
            background: 'rgba(14,14,16,.6)',
            fontFamily: DISPLAY,
            fontSize: 96,
            color: ACCENT,
            textTransform: 'uppercase',
            letterSpacing: 1,
            lineHeight: 1.05,
            whiteSpace: 'nowrap',
          }}
        >
          {text}
        </div>
      </Band>
    </AbsoluteFill>
  );
};

export const Reveal: React.FC<{t: number; a: number; sub: number; b: number}> = ({t, a, sub, b}) => {
  const v = vis(t, a, b, 0.001, 0.2);
  if (!v) return null;
  const k = easeOut((t - a) / 0.24);
  const s = pop(t, sub);
  return (
    <AbsoluteFill style={{opacity: v}}>
      <AbsoluteFill style={{background: 'rgba(8,8,10,.52)'}} />
      <Band top={680} style={{gap: 30}}>
        <div style={{...plate(150, ACCENT, 0.3), transform: `rotate(${-90 + 90 * k}deg) scale(${0.9 + 0.1 * k})`}}>
          <Icon name="lucide-timer" size={96} color={INK} />
        </div>
        <div style={{...strokeText(136), transform: `scale(${1.2 - 0.2 * k})`, whiteSpace: 'nowrap'}}>Cron Job</div>
        <div
          style={{
            opacity: t >= sub ? s.opacity : 0,
            transform: `scale(${s.scale})`,
            background: '#fff',
            borderRadius: 999,
            padding: '12px 34px',
            fontFamily: BODY,
            fontWeight: 900,
            fontSize: 46,
            color: INK,
          }}
        >
          = tarea programada
        </div>
      </Band>
    </AbsoluteFill>
  );
};

const BRANDS: Record<string, {icon: string; color: string; label: string}> = {
  chatgpt: {icon: 'openai', color: '#000000', label: 'ChatGPT'},
  claude: {icon: 'claude', color: '#D97757', label: 'Claude'},
  gemini: {icon: 'googlegemini', color: '#8E75B2', label: 'Gemini'},
};

export const LogoRow: React.FC<{t: number; items: {key: string; a: number}[]; extra: number; b: number; top: number}> = ({
  t,
  items,
  extra,
  b,
  top,
}) => {
  if (t < items[0].a - 0.05 || t > b + 0.2) return null;
  const ex = pop(t, extra);
  return (
    <AbsoluteFill>
      <Band top={top} style={{gap: 26, opacity: fadeOutAfter(t, b)}}>
        <div style={{display: 'flex', gap: 28}}>
          {items.map((it) => {
            const br = BRANDS[it.key];
            const p = pop(t, it.a);
            return (
              <div
                key={it.key}
                style={{
                  width: 240,
                  height: 270,
                  borderRadius: 44,
                  background: '#fff',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 18,
                  opacity: t >= it.a ? p.opacity : 0,
                  transform: `scale(${p.scale})`,
                  boxShadow: '0 22px 50px rgba(0,0,0,.4)',
                }}
              >
                <Icon name={br.icon} size={130} color={br.color} />
                <div style={{fontFamily: BODY, fontWeight: 900, fontSize: 40, color: INK}}>{br.label}</div>
              </div>
            );
          })}
        </div>
        <div
          style={{
            opacity: t >= extra ? ex.opacity : 0,
            transform: `scale(${ex.scale})`,
            background: ACCENT,
            borderRadius: 999,
            padding: '12px 34px',
            fontFamily: BODY,
            fontWeight: 900,
            fontSize: 46,
            color: INK,
          }}
        >
          + todas las IAs
        </div>
      </Band>
    </AbsoluteFill>
  );
};

export const IconList: React.FC<{t: number; items: {icon: string; text: string; a: number}[]; b: number; top: number}> = ({t, items, b, top}) => {
  if (t < items[0].a - 0.05 || t > b + 0.2) return null;
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', top, left: SIDE_L, right: SIDE_R, display: 'flex', flexDirection: 'column', gap: 20, opacity: fadeOutAfter(t, b)}}>
        {items.map((it) => {
          const p = pop(t, it.a);
          return (
            <div
              key={it.text}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                alignSelf: 'flex-start',
                background: 'rgba(14,14,16,.86)',
                borderRadius: 30,
                padding: '16px 30px 16px 16px',
                opacity: t >= it.a ? p.opacity : 0,
                transform: `scale(${p.scale})`,
                transformOrigin: '0% 50%',
              }}
            >
              <div style={plate(84, ACCENT)}>
                <Icon name={it.icon} size={50} color={INK} />
              </div>
              <div style={{fontFamily: BODY, fontWeight: 900, fontSize: 44, color: '#fff'}}>{it.text}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

type UseItem = {icons: {name: string; color: string}[]; text: string; a: number};

export const UsesRow: React.FC<{t: number; items: UseItem[]; b: number; top: number}> = ({t, items, b, top}) => {
  if (t < items[0].a - 0.05 || t > b + 0.2) return null;
  return (
    <AbsoluteFill>
      <Band top={top} style={{opacity: fadeOutAfter(t, b)}}>
        <div style={{display: 'flex', gap: 22}}>
          {items.map((it) => {
            const p = pop(t, it.a);
            return (
              <div
                key={it.text}
                style={{
                  width: 272,
                  boxSizing: 'border-box',
                  borderRadius: 34,
                  background: 'rgba(14,14,16,.88)',
                  padding: '24px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 16,
                  opacity: t >= it.a ? p.opacity : 0,
                  transform: `scale(${p.scale})`,
                }}
              >
                <div style={{display: 'flex', gap: 10}}>
                  {it.icons.map((ic) => (
                    <div key={ic.name} style={plate(92, '#fff')}>
                      <Icon name={ic.name} size={58} color={ic.color} />
                    </div>
                  ))}
                </div>
                <div style={{fontFamily: BODY, fontWeight: 900, fontSize: 38, color: '#fff'}}>{it.text}</div>
              </div>
            );
          })}
        </div>
      </Band>
    </AbsoluteFill>
  );
};

export const ClockTimelapse: React.FC<{t: number; a: number; runA: number; runB: number; b: number}> = ({t, a, runA, runB, b}) => {
  const v = vis(t, a, b, 0.2, 0.22);
  if (!v) return null;
  const minutes = 120 * clamp((t - runA) / Math.max(0.3, runB - runA));
  const label = `${Math.floor(minutes / 60)}:${String(Math.floor(minutes % 60)).padStart(2, '0')}`;
  return (
    <AbsoluteFill style={{opacity: v}}>
      <AbsoluteFill style={{background: 'rgba(8,8,10,.55)'}} />
      <Band top={520} style={{gap: 30}}>
        <svg width={420} height={420} viewBox="0 0 200 200">
          <circle cx={100} cy={100} r={92} fill="#fff" stroke={ACCENT} strokeWidth={10} />
          {Array.from({length: 12}, (_, i) => (
            <line
              key={i}
              x1={100}
              y1={18}
              x2={100}
              y2={i % 3 === 0 ? 34 : 28}
              stroke={INK}
              strokeWidth={i % 3 === 0 ? 5 : 3}
              strokeLinecap="round"
              transform={`rotate(${i * 30} 100 100)`}
            />
          ))}
          <line x1={100} y1={100} x2={100} y2={58} stroke={INK} strokeWidth={8} strokeLinecap="round" transform={`rotate(${minutes * 0.5} 100 100)`} />
          <line x1={100} y1={100} x2={100} y2={30} stroke={ACCENT} strokeWidth={5} strokeLinecap="round" transform={`rotate(${minutes * 6} 100 100)`} />
          <circle cx={100} cy={100} r={7} fill={INK} />
        </svg>
        <div style={strokeText(120)}>
          {label} <span style={{fontSize: 70}}>h</span>
        </div>
      </Band>
    </AbsoluteFill>
  );
};

const CONFETTI = Array.from({length: 70}, (_, i) => ({
  vx: (random(`cx${i}`) - 0.5) * 1500,
  vy: -700 - random(`cy${i}`) * 900,
  rot: random(`cr${i}`) * 360,
  spin: (random(`cs${i}`) - 0.5) * 900,
  w: 14 + random(`cw${i}`) * 12,
  h: 24 + random(`ch${i}`) * 16,
  color: [ACCENT, '#FFFFFF', '#FFB36B'][i % 3],
}));

const Confetti: React.FC<{t: number; a: number}> = ({t, a}) => {
  const d = t - a;
  if (d < 0 || d > 1.7) return null;
  return (
    <AbsoluteFill style={{opacity: 1 - clamp((d - 1.2) / 0.5)}}>
      {CONFETTI.map((c, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: 540 + c.vx * d,
            top: 920 + c.vy * d + 1300 * d * d,
            width: c.w,
            height: c.h,
            background: c.color,
            borderRadius: 3,
            transform: `rotate(${c.rot + c.spin * d}deg)`,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

export const Success: React.FC<{t: number; a: number; ticket: number; b: number; top: number}> = ({t, a, ticket, b, top}) => {
  if (t < a || t > b + 0.2) return null;
  const c = pop(t, a);
  const tk = pop(t, ticket);
  return (
    <AbsoluteFill>
      <Confetti t={t} a={ticket} />
      <Band top={top} style={{gap: 24, opacity: fadeOutAfter(t, b)}}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            background: '#fff',
            borderRadius: 999,
            padding: '12px 34px 12px 14px',
            opacity: c.opacity,
            transform: `scale(${c.scale})`,
          }}
        >
          <div style={plate(72, ACCENT, 0.5)}>
            <Icon name="lucide-circle-check" size={48} color={INK} />
          </div>
          <div style={{fontFamily: BODY, fontWeight: 900, fontSize: 46, color: INK}}>Alguien canceló</div>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 22,
            background: ACCENT,
            borderRadius: 34,
            padding: '18px 36px 18px 20px',
            opacity: t >= ticket ? tk.opacity : 0,
            transform: `rotate(-3deg) scale(${tk.scale})`,
            boxShadow: '0 24px 50px rgba(0,0,0,.4)',
          }}
        >
          <div style={plate(110, INK)}>
            <Icon name="lucide-ticket" size={70} color={ACCENT} />
          </div>
          <div style={{fontFamily: DISPLAY, fontSize: 64, color: INK, textTransform: 'uppercase', lineHeight: 1}}>
            Boletos
            <br />
            comprados
          </div>
        </div>
      </Band>
    </AbsoluteFill>
  );
};

export const SaveCTA: React.FC<{t: number; a: number; b: number}> = ({t, a}) => {
  if (t < a) return null;
  const p = pop(t, a);
  const d = t - a;
  const bob = Math.sin(d * 7) * 8 * Math.exp(-d * 0.8);
  const draw = clamp((d - 0.25) / 0.35);
  // apunta a la columna de botones de IG (derecha), no a la mano del creador
  const arrow = 'M 700 1000 C 860 1050, 950 1150, 950 1420';
  return (
    <AbsoluteFill>
      <Band top={800}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 22,
            background: ACCENT,
            borderRadius: 34,
            padding: '18px 42px 18px 22px',
            opacity: p.opacity,
            transform: `translateY(${bob}px) scale(${p.scale})`,
            boxShadow: '0 24px 50px rgba(0,0,0,.4)',
          }}
        >
          <div style={plate(112, INK)}>
            <Icon name="lucide-bookmark" size={66} color={ACCENT} />
          </div>
          <div style={{fontFamily: DISPLAY, fontSize: 88, color: INK, textTransform: 'uppercase', lineHeight: 1}}>Guárdalo</div>
        </div>
      </Band>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {[{c: '#000', w: 24}, {c: '#fff', w: 12}].map((s) => (
          <g key={s.c}>
            <path d={arrow} fill="none" stroke={s.c} strokeWidth={s.w} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} />
            {draw >= 1 && <path d="M 906 1370 L 950 1424 L 994 1372" fill="none" stroke={s.c} strokeWidth={s.w} strokeLinecap="round" strokeLinejoin="round" />}
          </g>
        ))}
      </svg>
    </AbsoluteFill>
  );
};
