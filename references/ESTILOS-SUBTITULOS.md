# Estilos de subtítulos virales — specs replicables (1080×1920)

**Fundamentos comunes:** safe zones top 220–250 px, **bottom 420–520 px** (caption + botones + barra),
laterales 80–100 px. Banda de oro del subtítulo: y ≈ 1050–1300 px (55–68% de altura). Legibilidad NO
negociable: stroke negro **por fuera** (`paint-order: stroke fill`, nunca centrado) + drop shadow
(blur 6–12 px, 50–70%), peso Bold/ExtraBold/Black, sans geométrica, **máx. 3–4 palabras/pantalla**,
sync word-level ±60 ms, all-caps para impacto / sentence-case para storytelling, ancho ≤85–90%.
Easing: `easeOutBack`/spring para entradas, `easeOutExpo` para pops limpios, lineal solo para karaoke.
**Regla:** UN estilo por video; mezclar Hormozi + word-pop + bounce se ve amateur.

| Estilo | Pal./pant. | Tamaño px | Stroke px | Animación | Color activo | Mejor para | Fuente sugerida |
|---|---|---|---|---|---|---|---|
| **Hormozi** | 1–3 | 95–130 | 10–16 | Color jump + micro-pop (scale 0.85→1, 80–120 ms) | Amarillo `#FFE000` / verde `#00E676` (o el color de tu marca) | Negocios, motivación | Montserrat Black, Anton |
| **MrBeast / Word-pop** | 1 | 130–180 | 14–20 | Scale 0→1.15→1 overshoot/spring, salida 120–200 ms | Amarillo/rojo/verde rotando | Alta energía, entretenimiento | Bangers, Luckiest Guy, Anton |
| **Karaoke fill** | 4–7 (línea) | 70–95 | 6–10 | Wipe de color izq→der word-level (60–120 ms) | Color de marca 100% sobre base 60–70% opacity | Podcast, storytelling, lyrics | Poppins Black, Montserrat |
| **Typewriter** | 1–2 líneas | 70–110 | 6–10 | Char-by-char 25–45 ms/char + cursor parpadeante | Cursor en color acento | Hooks, revelaciones, IA | Oswald, Bebas Neue (incluidas) — o Roboto/Inter/JetBrains Mono (descárgalas aparte) |
| **Bounce / Spring** | 1–3 | 90–130 | 8–14 | Spring físico (stiffness 180–260, damping 10–14), entra desde abajo +40–60 px | Acentos vivos | Lifestyle, fitness, comida | Poppins Black, Lilita One (incluidas) — o Fredoka (descárgala aparte) |
| **Highlight-box** | 1–4 | 70–110 | 0 (la caja da contraste) | Caja/marcador que salta con spring; padding 16–28×8–16 px, radius 8–16 px | Caja en color de marca o negro 85–95% | Educativo, marca, limpio | Montserrat, Inter |
| **Emoji-augmented** | hereda | hereda + emoji 90–160 px | hereda | Pop del emoji en la keyword (scale 0→1.2→1), máx 1 emoji cada 1–2 s | hereda | Lifestyle, finanzas-pop, comedia | cualquiera + Twemoji |

## Pipeline de captions (en esta skill)

1. **Transcribe word-level**: `python scripts/transcribir.py <video>` (whisper large-v3-turbo con
   `word_timestamps`). Para karaoke perfecto, WhisperX alinea fonéticamente.
2. **Chunk por ritmo** → `python scripts/generar_captions.py --transcripcion transcripcion.json
   --mapa mapa_tiempos.json` produce `captions.json` (lista de `{start,end,words:[{w,s}]}`) ya en
   tiempo del video cortado. Después `scripts/render_captions.py` (renderiza overlay alfa por
   Playwright — NO asumas libass en ffmpeg; verifica con `ffmpeg -filters | grep -w subtitles`).
3. **Estilo**: edita `caption.html` (fuente desde `assets/fonts/`, color activo, stroke, posición).
4. **Recolorea palabras "poder"** (verbos, números, emociones) para el resalte.
5. **Compón** el `caption.mov` (alfa) sobre el video con `overlay` (ver TRANSICIONES-EFECTOS.md).

`caption.html` ya implementa Hormozi/word-pop (palabra activa resaltada + pop). Para otros estilos,
ajusta el CSS/JS de `render(t)`:
- Word-pop puro: una sola palabra a la vez (chunks de 1), `scale 0→1.15→1`.
- Karaoke: muestra la línea completa, rellena color por palabra según `w.s`.
- Typewriter: revela caracteres por tiempo, cursor `▌` parpadeante.
- Highlight-box: fondo `border-radius` detrás de la palabra activa en vez de cambiar color de texto.

**Auto-captions rápidos (alternativa sin código):** Submagic, Captions.ai, Opus Clip, CapCut.
