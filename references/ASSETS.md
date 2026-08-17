# Assets — qué se descarga, qué se genera y licencias

El repo NO trae binarios: `bash scripts/setup.sh` llena `assets/` con material 100% libre para uso
comercial. Si una carpeta está vacía, corre el setup de nuevo.

## `assets/fonts/` — tipografías virales (OFL / Apache 2.0, uso comercial libre)

Descargadas de Google Fonts (repo oficial `google/fonts`): **Anton, Bangers, Luckiest Guy,
Archivo Black, Bebas Neue, Oswald, Permanent Marker, Poppins (Black), Montserrat (Black), Lilita
One, Russo One, Alfa Slab One**. Úsalas vía `@font-face` en los HTML de `scripts/`.

Cheat-sheet:
- **Captions Hormozi/negocios:** Montserrat Black, Anton, Archivo Black.
- **Word-pop alta energía / MrBeast:** Bangers, Luckiest Guy, Anton.
- **Condensadas (mucho texto):** Bebas Neue, Oswald.
- **Redondas friendly:** Poppins Black, Lilita One.
- **Acentos/handwritten:** Permanent Marker, Alfa Slab One, Russo One.

## `assets/emoji/` — Twemoji PNG 72×72 (CC-BY 4.0)

Set curado con nombres legibles (`fire.png`, `moneybag.png`, `check.png`, `rocket.png`…) desde el
CDN oficial. **Atribuir Twemoji** en los créditos/caption del video. Más emojis on-demand:
`https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72/<hex>.png` (o `/svg/<hex>.svg`).

## `assets/sfx/` — efectos de sonido

Dos fuentes:
1. **Sintéticos generados por `scripts/gen_sfx.sh`** (ffmpeg puro, sin licencia que respetar):
   whooshes, risers, impactos, pops, clicks, correct/wrong, notificación, coin, drumroll, win.
   Se generan solos en el setup.
2. **Librerías gratuitas para ampliar** (descarga manual del usuario):
   - Mixkit — https://mixkit.co/free-sound-effects/ (comercial, sin atribución)
   - Pixabay — https://pixabay.com/sound-effects/ (comercial, sin atribución; aquí están los memes:
     vine boom, airhorn, braam)
   `scripts/descargar_sfx.py` ayuda a bajar y organizar por categorías (uso personal, respeta los
   términos del sitio).

Guía de disparo:
- **Transición/corte:** whoosh, transition_swish · **reveal tech:** stamp o impact_boom (el efecto
  glitch es de VIDEO — `transitions.py glitch`; si quieres su SFX, descárgalo de Mixkit/Pixabay)
- **Tensión→reveal:** riser, drumroll, impact (progresivos: suben hacia el clímax)
- **Sí/no:** correct vs wrong · **hype/énfasis:** pop, click
- **Social proof:** notification, coin ($) · **Celebración/cierre:** win

Dosis: ≤1 SFX cada 2–4 s; un SFX "ancla" de marca por video.

## `assets/music/` — música de fondo

No se descarga automáticamente (elige por mood del video). Fuentes gratuitas comerciales:
- Mixkit Music — https://mixkit.co/free-stock-music/ (10 moods; no broadcast/juegos)
- Pixabay Music — https://pixabay.com/music/
- YouTube Audio Library — https://studio.youtube.com (sección Audio)
Coloca el archivo en `assets/music/` y mézclalo a **−18/−24 dB bajo la voz**; sube en tramos sin voz.

⚠️ Para anuncios o reuso multiplataforma usa SOLO audio royalty-free — nunca el trending nativo de
la app (licenciado solo para uso dentro de esa app).

## Overlays e íconos — se GENERAN, no se descargan (control de marca total)

- **UI animada** (subscribe, follow, like, countdown, flecha, círculo): `scripts/overlays.html` +
  `scripts/render_overlays.py` → .mov con alfa. Colores/textos editables en el HTML.
- **Grain / viñeta / light leak**: recetas ffmpeg en TRANSICIONES-EFECTOS.md.
- **Íconos UI**: Lucide (ISC) — `https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/<nombre>.svg`.
- Logos de plataformas: usa los oficiales de cada marca, no los redibujes.

## Cumplimiento de licencias (resumen)

| Fuente | Licencia | ¿Atribución? |
|---|---|---|
| Google Fonts (OFL/Apache) | Comercial libre | No |
| Twemoji | CC-BY 4.0 | **Sí** (créditos/caption) |
| Mixkit / Pixabay | Comercial libre | No |
| Lucide | ISC | No |
| SFX sintéticos (gen_sfx.sh) | Tuyos | No |
