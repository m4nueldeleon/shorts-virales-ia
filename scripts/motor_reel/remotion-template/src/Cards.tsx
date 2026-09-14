import React from 'react';
import {ACCENT, ACCENT_TINT, BODY, DISPLAY, INK, Icon, MUTED, clamp, easeOut, plate, pop, vis} from './lib';

const CARD_LEFT = 64;
const CARD_W = 890;

const typed = (text: string, t: number, a: number, b: number) =>
  text.slice(0, Math.ceil(text.length * clamp((t - a) / Math.max(0.3, b - a))));

const Card: React.FC<{t: number; a: number; b: number; top: number; children: React.ReactNode}> = ({
  t,
  a,
  b,
  top,
  children,
}) => {
  const v = vis(t, a, b, 0.14, 0.16);
  if (!v) return null;
  const p = pop(t, a);
  const rise = (1 - easeOut((t - a) / 0.22)) * 36;
  return (
    <div
      style={{
        position: 'absolute',
        left: CARD_LEFT,
        width: CARD_W,
        top,
        boxSizing: 'border-box',
        opacity: v * p.opacity,
        transform: `translateY(${rise}px) scale(${p.scale})`,
        transformOrigin: '50% 0%',
        background: '#fff',
        borderRadius: 38,
        padding: '32px 36px',
        boxShadow: '0 30px 70px rgba(0,0,0,.45)',
        color: INK,
        fontFamily: BODY,
      }}
    >
      {children}
    </div>
  );
};

const Cursor: React.FC<{t: number}> = ({t}) => (
  <span
    style={{
      display: 'inline-block',
      width: 7,
      height: '0.9em',
      marginLeft: 6,
      verticalAlign: '-0.12em',
      background: ACCENT,
      opacity: Math.floor(t * 3) % 2 === 0 ? 1 : 0,
    }}
  />
);

const Dots: React.FC<{t: number}> = ({t}) => (
  <span style={{display: 'inline-flex', gap: 10, padding: '14px 4px'}}>
    {[0, 1, 2].map((i) => (
      <span
        key={i}
        style={{width: 16, height: 16, borderRadius: 8, background: '#fff', opacity: 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * 9 - i * 0.9))}}
      />
    ))}
  </span>
);

const Pill: React.FC<{t: number; at: number; icon: string; text: string; dark?: boolean}> = ({t, at, icon, text, dark = true}) => {
  const p = pop(t, at);
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 14,
        marginTop: 22,
        background: dark ? INK : ACCENT_TINT,
        color: dark ? '#fff' : INK,
        borderRadius: 999,
        padding: '10px 28px 10px 12px',
        opacity: t >= at ? p.opacity : 0,
        transform: `scale(${p.scale})`,
        transformOrigin: '0% 50%',
      }}
    >
      <div style={plate(56, ACCENT, 0.5)}>
        <Icon name={icon} size={34} color={INK} />
      </div>
      <div style={{fontSize: 36, fontWeight: 900}}>{text}</div>
    </div>
  );
};

const USER_Q = '¿Qué hago para entrar a la fiesta si no tengo boletos?';
const AI_A = 'Manda un correo para ver si alguien canceló.';

export const ChatCard: React.FC<{t: number; a: number; reply: number; replyEnd: number; b: number}> = ({t, a, reply, replyEnd, b}) => {
  const q = pop(t, a + 0.15);
  const ans = typed(AI_A, t, reply, replyEnd);
  return (
    <Card t={t} a={a} b={b} top={700}>
      <div style={{display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20}}>
        <div style={{...plate(62, '#fff'), border: '2px solid #E4E4E8'}}>
          <Icon name="openai" size={40} color="#000" />
        </div>
        <div style={{fontSize: 42, fontWeight: 900}}>ChatGPT</div>
      </div>
      <div style={{display: 'flex', justifyContent: 'flex-end', opacity: q.opacity, transform: `scale(${q.scale})`, transformOrigin: '100% 50%'}}>
        <div style={{background: '#EDEDF0', borderRadius: '28px 28px 8px 28px', padding: '16px 24px', fontSize: 42, fontWeight: 700, lineHeight: 1.2, maxWidth: 700}}>
          {USER_Q}
        </div>
      </div>
      <div style={{display: 'flex', marginTop: 16, opacity: t >= reply - 0.6 ? 1 : 0}}>
        <div style={{background: INK, color: '#fff', borderRadius: '28px 28px 28px 8px', padding: '16px 24px', fontSize: 42, fontWeight: 700, lineHeight: 1.2, maxWidth: 740, minHeight: 50}}>
          {t < reply ? (
            <Dots t={t} />
          ) : (
            <>
              {ans}
              {ans.length < AI_A.length && <Cursor t={t} />}
            </>
          )}
        </div>
      </div>
    </Card>
  );
};

export const MailCard: React.FC<{t: number; a: number; first: number; many: number; every: number; b: number}> = ({
  t,
  a,
  first,
  many,
  every,
  b,
}) => {
  const arrivals = [first, ...[0, 1, 2, 3, 4].map((i) => many + 0.12 + i * 0.2)];
  return (
    <Card t={t} a={a} b={b} top={720}>
      <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
        <div style={plate(92, ACCENT)}>
          <Icon name="lucide-send" size={52} color={INK} />
        </div>
        <div style={{fontFamily: DISPLAY, fontSize: 60, textTransform: 'uppercase', lineHeight: 1}}>
          {t < many ? 'Correo #1' : 'Muchos correos'}
        </div>
      </div>
      <div style={{display: 'flex', gap: 14, marginTop: 24}}>
        {arrivals.map((at, i) => {
          const p = pop(t, at);
          return (
            <div key={i} style={{...plate(118, '#EDEDF0'), opacity: t >= at ? p.opacity : 0, transform: `scale(${p.scale})`}}>
              <Icon name="lucide-mail" size={64} color={INK} />
            </div>
          );
        })}
      </div>
      <Pill t={t} at={every} icon="lucide-timer" text="Cada 10–20 minutos" />
    </Card>
  );
};

// Igual a lo que dice el creador (la tarjeta y la voz no deben contradecirse)
const PROMPT = 'Cada 20 minutos, escribe al soporte técnico para ver si alguien cancela.';

export const PromptCard: React.FC<{t: number; a: number; typeA: number; typeB: number; b: number}> = ({t, a, typeA, typeB, b}) => {
  const txt = typed(PROMPT, t, typeA, typeB);
  const done = txt.length === PROMPT.length;
  return (
    <Card t={t} a={a} b={b} top={960}>
      <div style={{display: 'flex', alignItems: 'center', gap: 14, fontSize: 32, fontWeight: 700, color: MUTED}}>
        <Icon name="lucide-message-square" size={36} color={MUTED} />
        Lo que le dije a la IA
      </div>
      <div style={{height: 2, background: '#E4E4E8', margin: '18px 0 20px'}} />
      <div style={{fontSize: 50, fontWeight: 900, lineHeight: 1.18, minHeight: 177}}>
        {txt}
        {!done && <Cursor t={t} />}
      </div>
      <Pill t={t} at={typeA + 0.8} icon="lucide-repeat" text="Se repite sola" />
    </Card>
  );
};

const OPTIONS = ['30 min', '1 hora', '2 horas'];

// Un chat normal no repite nada solo: la instrucción va en las tareas programadas de la IA.
// Debajo de la cara (top 1000) y sin fila de logos para no pasar de la zona segura (y ≤ 1440).
export const TemplateCard: React.FC<{t: number; a: number; opts: number[]; b: number}> = ({t, a, opts, b}) => (
  <Card t={t} a={a} b={b} top={1000}>
    <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
      <Icon name="lucide-calendar-clock" size={40} color={ACCENT} />
      <div style={{fontFamily: DISPLAY, fontSize: 32, color: ACCENT, textTransform: 'uppercase', letterSpacing: 1}}>En tareas programadas, escribe:</div>
    </div>
    <div style={{fontSize: 46, fontWeight: 900, lineHeight: 1.2, marginTop: 16}}>
      Quiero que actúes como un <span style={{color: ACCENT}}>cron job</span> para{' '}
      <span style={{background: ACCENT_TINT, borderRadius: 12, padding: '0 12px'}}>[tu tarea]</span> y lo hagas cada:
    </div>
    <div style={{display: 'flex', gap: 16, marginTop: 22}}>
      {OPTIONS.map((o, i) => {
        // solo la opción que se está diciendo (las tres encendidas parecía «elige las tres»)
        const on = t >= opts[i] && (i === opts.length - 1 || t < opts[i + 1]);
        return (
          <div
            key={o}
            style={{
              flex: 1,
              textAlign: 'center',
              borderRadius: 999,
              padding: '14px 0',
              fontSize: 40,
              fontWeight: 900,
              background: on ? ACCENT : '#EDEDF0',
              color: INK,
              transform: on ? `scale(${1.08 - 0.08 * easeOut((t - opts[i]) / 0.25)})` : undefined,
            }}
          >
            {o}
          </div>
        );
      })}
    </div>
  </Card>
);
