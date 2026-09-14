import {Timeline, Win, makeTime} from './lib';

export type Sfx = {file: string; t: number; vol: number; len: number};

/**
 * Todo el guion visual y sonoro anclado a palabras dichas (no a segundos fijos):
 * si cambian los cortes, los efectos siguen cayendo en su palabra.
 */
export const buildEvents = (tl: Timeline) => {
  const {S, E, W, speechEnd} = makeTime(tl);
  const sfx: Sfx[] = [];
  const add = (file: string, t: number, vol: number, len = 2) => sfx.push({file, t: Math.max(0, t), vol, len});

  // Cambios de lugar / de toma: whip vertical + whoosh
  const whips = ['S02', 'S04', 'S05', 'S09', 'S12', 'S13', 'S15', 'S19', 'S22'].map(S);
  whips.forEach((t) => add('whoosh.wav', t - 0.22, 0.3, 0.9));

  // HOOK
  const hook = {b: S('S02') - 0.05};
  add('hook-hit.wav', 0, 0.5, 1.6);

  const halloween = {a: W('S02', 'halloween'), b: E('S02')};
  add('pop.wav', halloween.a, 0.3, 0.6);

  // Cliffhanger 1
  const stamp = {a: W('S03', 'no'), b: E('S03') - 0.05};
  add('impact.wav', stamp.a, 0.6, 1.4);
  add('suspense-hit.wav', W('S03', 'tickets', 0, 'e'), 0.4, 1.8);

  const chat = {
    a: W('S05', 'pregunte') - 0.15,
    reply: W('S06', 'tienes'),
    replyEnd: W('S06', 'cancelo', 0, 'e'),
    b: speechEnd('S06') + 0.12,
  };
  add('msg-pop.wav', chat.a + 0.15, 0.4, 0.8);
  add('msg-pop.wav', chat.reply, 0.4, 0.8);

  const mail = {
    a: S('S07') + 0.05,
    first: W('S07', 'primer'),
    many: W('S07', 'muchos'),
    every: W('S07', 'cada'),
    b: speechEnd('S07') + 0.1,
  };
  add('air.wav', mail.first, 0.45, 1);
  [0.12, 0.32, 0.52].forEach((d) => add('tone.wav', mail.many + d, 0.22, 0.5));

  // Cliffhanger 2: congelado con glitch y la música se corta
  const glitch: Win = {a: W('S08', 'ocupado'), b: E('S08')};
  add('glitch-hit.wav', glitch.a, 0.6, 1.1);
  add('glitch.wav', glitch.a + 0.1, 0.25, 0.6);

  // Revelación
  const reveal = {a: W('S10', 'cron'), sub: S('S11'), b: E('S11') + 0.05};
  const riser: Win = {a: S('S09'), b: reveal.a};
  add('riser.wav', reveal.a - 4.35, 0.5, 4.4);
  add('big-impact.wav', reveal.a, 0.75, 2.2);

  const logos = {
    items: [
      {key: 'chatgpt', a: W('S12', 'chatgpt')},
      {key: 'claude', a: W('S12', 'claude')},
      {key: 'gemini', a: W('S12', 'gemini')},
    ],
    extra: W('S12', 'toda'),
    b: E('S12') + 0.1,
  };
  logos.items.forEach((i) => add('pop.wav', i.a, 0.4, 0.6));
  add('click.wav', logos.extra, 0.3, 0.5);

  const walk = {src: 'broll/walk.mp4', a: W('S13', 'programar'), d: 1.3};
  const uses13 = {
    items: [
      {icon: 'lucide-repeat', text: 'Mensajes cada cierto tiempo', a: W('S13', 'mande')},
      {icon: 'lucide-mail', text: 'Contestar tus correos', a: W('S13', 'conteste')},
    ],
    b: E('S13') + 0.1,
  };
  uses13.items.forEach((i) => add('pop.wav', i.a, 0.3, 0.6));
  add('confirm.wav', W('S14', 'automatica'), 0.3, 0.8);

  // la tarjeta entra con la primera palabra del prompt (antes quedaba 2.6 s vacía sobre la cara)
  // y sale antes de que entre el reloj (en la v3 se encimaban «0:00 h» y el texto del prompt)
  const prompt = {
    a: W('S16', 'cada') - 0.35,
    typeA: W('S16', 'cada'),
    typeB: W('S16', 'cancela', 0, 'e'),
    b: Math.min(speechEnd('S16') + 0.6, W('S17', 'activ') - 0.2),
  };
  add('msg-pop.wav', prompt.a, 0.3, 0.8);
  for (let x = prompt.typeA; x < prompt.typeB - 0.3; x += 0.7) add('typing.wav', x, 0.2, 0.7);

  // Cliffhanger 3: dos horas
  const clock = {a: W('S17', 'activ'), runA: W('S17', 'despues'), runB: E('S17'), b: E('S17') + 0.05};
  add('click.wav', clock.a, 0.45, 0.5);
  add('ticktock.wav', clock.runA - 0.2, 0.45, clock.runB - clock.runA + 0.3);
  add('swell.wav', clock.runA - 0.4, 0.3, 2.6);

  // El remate «boletos comprados» cae sobre el b-roll de celebración (antes duraba 0.5 s sobre la nuca)
  const ticket = W('S18', 'boletos');
  const cheer = {src: 'broll/cheer.mp4', a: ticket, d: 1.2};
  const success = {a: W('S18', 'cancel'), ticket, b: cheer.a + 1.0};
  add('correct.wav', success.a, 0.55, 1.1);
  add('win.wav', success.ticket, 0.45, 1.6);
  add('air.wav', cheer.a - 0.1, 0.3, 0.8);

  const template = {a: W('S20', 'quiero') - 0.3, opts: [W('S20', '30'), W('S20', 'hora'), W('S20', 'horas')], b: speechEnd('S20') + 0.5};
  add('msg-pop.wav', template.a, 0.35, 0.8);
  template.opts.forEach((o) => add('click.wav', o, 0.3, 0.5));

  const uses22 = {
    items: [
      {icons: [{name: 'instagram', color: '#FF0069'}, {name: 'tiktok', color: '#000000'}], text: 'Tendencias', a: W('S22', 'tendencias')},
      {icons: [{name: 'gmail', color: '#EA4335'}], text: 'Correos', a: W('S22', 'correos')},
      {icons: [{name: 'whatsapp', color: '#25D366'}], text: 'Clientes', a: W('S22', 'cliente')},
    ],
    b: E('S22') + 0.1,
  };
  uses22.items.forEach((i) => add('pop.wav', i.a, 0.35, 0.6));

  const save = {a: W('S23', 'olvide'), b: tl.total};
  add('bell.wav', W('S23', 'guardar'), 0.45, 1.6);

  return {
    hook,
    halloween,
    stamp,
    chat,
    mail,
    reveal,
    riser,
    logos,
    uses13,
    prompt,
    clock,
    success,
    template,
    uses22,
    save,
    whips,
    punches: [
      {t: W('S01', 'fiesta'), amt: 0.12},
      {t: W('S02', 'halloween'), amt: 0.06},
      {t: W('S03', 'tickets'), amt: 0.14},
      {t: W('S04', 'pocos'), amt: 0.1},
      {t: W('S08', 'ocupado'), amt: 0.1},
      {t: reveal.a, amt: 0.2},
      {t: W('S12', 'toda'), amt: 0.06},
      {t: W('S14', 'automatica'), amt: 0.12},
      {t: success.ticket, amt: 0.12},
      {t: W('S19', 'automatizar'), amt: 0.08},
      {t: W('S22', 'cliente'), amt: 0.08},
      {t: W('S23', 'guardar'), amt: 0.12},
    ],
    shakes: [
      {t: W('S03', 'tickets'), d: 0.35, amp: 16},
      {t: reveal.a, d: 0.55, amp: 24},
      {t: success.ticket, d: 0.3, amp: 10},
    ],
    flashes: [
      {t: reveal.a, k: 1},
      {t: success.ticket, k: 0.45},
    ],
    glitches: [glitch],
    broll: [walk, cheer],
    // Subtítulos fuera cuando una tarjeta ya muestra lo que se dice (evita doble texto y tapar la cara)
    captionHide: [
      {a: 0, b: hook.b},
      {a: reveal.a - 0.03, b: reveal.b},
      {a: prompt.typeA - 0.05, b: prompt.b},
      {a: success.a, b: success.b},
      {a: template.a, b: template.b},
      {a: W('S23', 'presionar'), b: tl.total + 1},
    ] as Win[],
    musicCuts: [
      {a: glitch.a, b: reveal.a},
      {a: clock.runA, b: success.a},
    ] as Win[],
    // bed.mp3 = -9.8 LUFS, voz = -14.9 LUFS → 0.06 (-24 dB) deja la música ~19 dB bajo la voz
    musicGain: 0.06,
    sfx,
  };
};

export type Events = ReturnType<typeof buildEvents>;
