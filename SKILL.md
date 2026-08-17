---
name: shorts-virales-ia
description: >
  Convierte un video en crudo en un short viral (TikTok / Reels / YouTube Shorts, 9:16) de forma
  automática: corrige el audio, quita muletillas y silencios, encuentra el mejor gancho en CUALQUIER
  parte del video, re-estructura con cliffhangers, añade subtítulos kinéticos, zooms, transiciones,
  efectos de sonido progresivos, íconos, overlays e imágenes generadas con IA. El usuario solo
  entrega el crudo; la skill entrega el video listo para publicar. Triggers: "edita mi video",
  "hazlo viral", "convierte esto en un reel/short/tiktok", "edita este crudo", "haz un short de esto".
---

# Shorts Virales IA — de crudo a viral en un solo paso

El usuario entrega **un video en crudo** (celular, cámara, OBS, Zoom — cualquier formato). Tú
entregas **un short 9:16 optimizado para viralidad**: audio limpio, sin muletillas, con gancho
fuerte, cliffhangers, subtítulos kinéticos, movimiento constante, SFX y look premium.

**Lienzo objetivo: 1080×1920, 30 fps, H.264 CRF 18, AAC 192k, `+faststart`.**

## Requisitos (una sola vez)

Ejecuta `bash scripts/setup.sh` desde la carpeta de la skill. Instala/verifica: `ffmpeg`, venv de
Python con whisper (word-level) + `playwright` (+ chromium), y descarga fuentes libres (OFL/Apache 2.0),
emojis Twemoji y genera la librería de SFX sintéticos en `assets/`. Si algo falta a mitad de una
edición, vuelve a correr el setup.

## Flujo maestro (síguelo en orden)

### FASE 0 — Diagnóstico del crudo
1. `ffprobe` → duración, resolución, fps, orientación, codec, pistas de audio.
2. Extrae 4–6 frames (`ffmpeg -ss N -frames:v 1`) para VER el encuadre: ¿dónde está la cara?
   ¿hay pantalla compartida? ¿fondo limpio o sucio? Esto decide el crop 9:16 y las safe zones.
3. Si el video es horizontal → planifica reencuadre vertical con la cara centrada
   (`crop=ih*9/16:ih` + ajuste de `x` para seguir al sujeto; si el sujeto se mueve, crop por tramos).

### FASE 1 — Transcripción word-level (la columna vertebral)
`python scripts/transcribir.py <video>` → `transcripcion.json` con timestamps por palabra.
En Mac usa `mlx-whisper` (rápido, Apple Silicon); en otros sistemas `faster-whisper`. Idioma: el
del video (por defecto `es`). TODO lo demás (cortes, subtítulos, SFX, hook) se ancla a estas palabras.

⚠️ Dos trampas conocidas de whisper (te costarán un re-render si las ignoras):
- **Estira palabras sobre pausas** → NUNCA cortes silencios usando timestamps de palabras.
- **Oculta tomas repetidas** en el texto (el audio tartamudea pero el transcript se ve limpio) →
  detecta repeticiones re-transcribiendo ventanas aisladas o el render final.

### FASE 2 — Corrección de audio
Sobre la pista de voz, en este orden:
1. **Denoise** si hay ruido de fondo: `afftdn=nf=-25` (suave; no lo apliques si la voz es limpia).
2. **De-esser / EQ suave** si silba: `deesser`, o `highpass=f=80,lowpass=f=12000`.
3. **Normalización**: `loudnorm=I=-14:TP=-1.5:LRA=11` (estándar de plataformas sociales).
La voz SIEMPRE al frente; música y SFX por debajo (Fase 7).

### FASE 3 — Muletillas, silencios y tomas falsas
1. **Muletillas**: busca en `transcripcion.json` las palabras de relleno del idioma
   ("eh", "eee", "mmm", "este…", "o sea", "pues", "¿no?", "¿sí?", "¿verdad?", "digamos",
   "como que", "um", "uh", "like", "you know") y falsos arranques (frase que se corta y se
   reinicia). Marca sus intervalos como candidatos a KILL. Criterio: si al quitarla la frase
   sigue fluyendo, se quita; si la muletilla es parte del estilo del hablante y aparece 1 vez, respeta.
2. **Silencios por ENERGÍA real** + plan de corte. Primero revisa el plan sin renderizar:
   `python scripts/cortar_silencios.py <video> --transcripcion transcripcion.json --muletillas --solo-plan`
   (usa `silencedetect` noise=-30dB d=0.4 y padding ~0.15 s en los bordes).
3. **Tomas repetidas / errores**: pásalos como `--kill "12.3-14.1,55-57.2"` en tiempo ORIGINAL.
   El script los fusiona con silencios y muletillas. Cuando el plan esté bien, quita `--solo-plan`
   para renderizar → produce `base_cut.mp4` + `mapa_tiempos.json`.
4. El script genera el **mapa tiempo-viejo → tiempo-nuevo**. Todo lo que coloques después
   (subtítulos, SFX, overlays) va en tiempo NUEVO vía este mapa.
5. Cada unión lleva **micro-fade de ~12 ms** (mata el clic/"trabado" del concat).

### FASE 4 — Minería del gancho + re-estructura viral
El gancho NO tiene que ser el inicio del crudo. Con el transcript completo:
1. **Puntúa candidatos a hook** en TODO el video (inicio, mitad, final): la afirmación más fuerte,
   un número/dato duro, una contradicción, el resultado final, la frase más emocional. ≤8 palabras
   habladas o un momento visual de shock.
2. **Cold-open**: extrae ese momento (1–3 s) y colócalo COMO PRIMER CLIP, luego corre la historia.
   Si el momento se repetirá después de forma redundante, corta la repetición o úsala como cierre
   de bucle.
3. **Re-estructura** al arco viral (no respetes el orden del crudo si otro orden retiene más):
   ```
   [0–3s]   HOOK      el mejor momento del video + texto grande en pantalla
   [3–8s]   SETUP     contexto mínimo, por qué importa AHORA
   [8–45s]  PAYLOAD   el valor en pasos; cada paso abre un micro-loop
   [45–55s] PEAK      lo segundo mejor del video va AL FINAL
   [55–60s] CTA+LOOP  una sola acción; la última frase reengancha con el hook
   ```
4. **Cliffhangers / open loops**: abre un loop en el hook ("al final te muestro X"), siembra
   micro-loops entre pasos (corta la frase justo antes del dato y mete un pattern interrupt),
   y cierra el loop principal SOLO al final. Los cortes de tensión caen justo antes de la
   palabra clave (usa los timestamps).
Referencia completa de hooks, retención y errores: `references/PLAYBOOK-VIRAL.md`.

### FASE 5 — Fondos (solo si mejora el video)
- **Fondo verde/uniforme** → `chromakey` de ffmpeg (rápido y limpio):
  `chromakey=0x00FF00:0.20:0.08` + fondo nuevo (color de marca, gradiente animado o b-roll).
- **Fondo real** → `python scripts/quitar_fondo.py <video> --inicio 4.0 --fin 8.0 --modo ia`
  (IA con rembg — requiere haber corrido `setup.sh --con-fondo`; es lento: úsalo por SEGMENTOS de
  énfasis de 2–5 s, no en todo el video; `--fondo` acepta color hex, imagen o video).
- Fondos de reemplazo atractivos: gradiente animado generado por código, b-roll con Ken Burns,
  o imagen IA (Fase 6). Si el fondo original es bueno, NO lo quites: un talking-head auténtico
  retiene mejor que un recorte mediocre.

### FASE 6 — Imágenes y b-roll con IA
El b-roll es la herramienta #1 de retención. Genera SOLO lo que no existe:
1. Del transcript, identifica 3–6 momentos que piden apoyo visual (conceptos abstractos, datos,
   objetos mencionados).
2. Genera imágenes con la herramienta disponible en el entorno (MCP de imágenes: nano-banana /
   Gemini, Higgsfield, DALL·E, fal.ai — la que exista; si no hay ninguna, usa capturas o gráficos
   HTML renderizados con Playwright). Estilo consistente en todo el video: mismo look, misma paleta.
3. Insértalas como b-roll con **Ken Burns** (`transitions.py kenburns`) 2–4 s, con el audio del
   hablante ENCIMA (el audio principal nunca se corta).
4. Gráficos de datos/números → genera HTML/CSS animado y renderízalo con Playwright a overlay alfa
   (misma técnica que los subtítulos). Guía: `references/IMAGENES-IA.md`.

### FASE 7 — Subtítulos kinéticos, movimiento, SFX y música
1. **Subtítulos** (siempre — 85% ve en mute): elige UN estilo (`references/ESTILOS-SUBTITULOS.md`:
   Hormozi, word-pop, karaoke, typewriter, bounce, highlight-box, emoji) según el tono. Cadena:
   `python scripts/generar_captions.py --transcripcion transcripcion.json --mapa mapa_tiempos.json`
   → produce `captions.json` en tiempo NUEVO → `python scripts/render_captions.py --captions
   captions.json --duracion <dur_final>` → `caption.mov` (overlay alfa vía Playwright — NO asumas
   libass; muchos ffmpeg no lo traen). Al componer, el caption.mov (banda de 1080×380) va en
   **y≈1020**: `python scripts/transitions.py overlay base.mp4 caption.mov out.mp4 --y 1020`, para
   que el texto caiga en la banda y≈1050–1300 px. Máx 3–4 palabras por pantalla, palabra clave
   resaltada, stroke negro por fuera.
2. **Movimiento — pattern interrupt cada 2–4 s**: ningún plano >4 s sin cambio. Alterna:
   zoom punch (5–15%) en sílabas clave, Ken Burns lento de base, shake en golpes, flash/glitch
   en reveals, jump cuts con alternancia de escala 1.0/1.06. Recetas: `scripts/transitions.py`
   y `references/TRANSICIONES-EFECTOS.md`. **Sincroniza al beat** de la música.
3. **SFX progresivos** (`assets/sfx/`, dosificación ≤1 cada 2–4 s):
   whoosh en transiciones · riser/drumroll antes del reveal (tensión que CRECE) · impact/boom en
   el golpe · pop/click en apariciones de texto · notification/coin en social proof · win al cierre.
   La progresión importa: los SFX suben de intensidad hacia el clímax del video.
4. **Música**: el bed lo aporta el usuario en `assets/music/` (el setup NO descarga música;
   fuentes gratuitas en `references/ASSETS.md`). Mézclalo a **−18/−24 dB bajo la voz**; sube en
   tramos sin voz. Cortes y zooms caen en los beats. Si no hay bed, el video funciona solo con voz+SFX.
5. **Íconos y overlays**: emojis Twemoji (`assets/emoji/`) en keywords (≤1 cada 1–2 s), flecha/
   círculo para señalar, follow/subscribe cerca del final, countdown en aperturas. Render:
   `scripts/overlays.html` + `scripts/render_overlays.py`. Íconos UI extra: Lucide
   (`https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/<nombre>.svg`).
6. **Look final**: film grain 12–15% + viñeta ligera = acabado premium.

### FASE 8 — Ensamble, verificación y export
1. Compón en orden: video cortado → zooms/transiciones → b-roll → overlays alfa (subtítulos al
   final, siempre encima) → mezcla de audio (voz + música + SFX con `amix=normalize=0` + `alimiter`).
2. **Safe zones**: nada de texto/gráficos en top 220 px, bottom 480 px, right 120 px (UI de la app).
3. **Verifica ANTES de entregar** — `python scripts/verificar.py <final>`:
   - Re-transcribe el render final: ¿quedó alguna muletilla/repetición? ¿se cortó una palabra?
   - `silencedetect`: 0 silencios largos. `volumedetect`: sin clipping (max < 0 dB).
   - Revisa 3–4 frames: ¿subtítulos dentro de safe zones? ¿algún plano >4 s sin cambio?
4. Export final: `-c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart`.
5. Entrega al usuario: el MP4 + 2 líneas con el hook usado y sugerencia de caption/hashtags.

## Reglas de oro (violarlas = video amateur)
- UN solo estilo de subtítulo por video. UNA sola CTA.
- La voz manda: nada la tapa, nada la corta.
- Cortes por energía de audio, no por timestamps de palabras.
- Lo mejor del video va al hook; lo segundo mejor, al final. El medio sostiene con loops.
- Efectos al servicio de la retención: si un efecto no evita un swipe, sobra.
- Verifica re-transcribiendo el final. Siempre.

## Animaciones avanzadas (opcional, Remotion)
Para motion graphics complejos (contadores animados, gráficas, escenas componibles y plantillas
reutilizables) usa **Remotion** (React): `npx create-video@latest`. Guía de cuándo conviene y
patrones: `references/REMOTION-ANIMACIONES.md`. Para dominio profundo instala la skill oficial:
`https://github.com/remotion-dev/skills`.

## Estructura de la skill
```
scripts/    setup.sh · transcribir.py · cortar_silencios.py · generar_captions.py
            quitar_fondo.py · verificar.py · caption.html + render_captions.py
            overlays.html + render_overlays.py · transitions.py · gen_sfx.sh · descargar_sfx.py
references/ PLAYBOOK-VIRAL.md · ESTILOS-SUBTITULOS.md · TRANSICIONES-EFECTOS.md
            IMAGENES-IA.md · REMOTION-ANIMACIONES.md · ASSETS.md
assets/     fonts/ · emoji/ · sfx/ (se llenan con setup.sh) · music/ (la aporta el usuario)
```
