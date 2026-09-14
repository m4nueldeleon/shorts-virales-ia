# Motor reel PRO

El motor que produjo un reel real aprobado a la primera. El flujo:
1. EDL → base con cuadros exactos.
2. Subtítulos desde la re-transcripción.
3. Capa Remotion anclada a palabras.
4. Máster.
5. Auditoría.

El protocolo completo, con el porqué de cada paso, está en `../../references/PROTOCOLO-PRO.md`.

## Requisitos
- Haber corrido `scripts/setup.sh` (fuentes y SFX).
- `ffmpeg` y Node 18+.
- Un Python con `mlx-whisper` (Mac) o `faster-whisper` más `numpy`.

## Variables de entorno

| Variable | Qué es | Por omisión |
|---|---|---|
| `WHISPER_PY` | python con whisper + numpy | `python3` |
| `REEL_SRC` | ruta de tu crudo | `00-crudo/crudo.mov` |
| `REEL_OUT` | carpeta de salida de la base | `03-render` (usa `03-render-vN` para versiones) |

> `transcribe.py` usa `mlx_whisper`. Fuera de Mac, adáptalo a `faster-whisper` y conserva el mismo
> JSON de salida (segments → words con start/end).

## Arranque en 6 pasos

### 0. Carpeta del reel

```bash
R=mi-reel; M=~/.claude/skills/shorts-virales-ia/scripts/motor_reel
mkdir -p "$R"/{00-crudo,01-transcripcion,02-frames,03-render,04-final,05-auditoria}
cp "$M"/{build_base.py,words_from_base.py,remap_words.py,audit.sh} "$R/"
cp "$M"/{transcribe.py,vad.py} "$R/01-transcripcion/"
cp -R "$M/remotion-template" "$R/remotion-reel" && (cd "$R/remotion-reel" && npm ci)
MUSIC_BED=~/Music/mi-bed.mp3 bash "$M/preparar_public.sh" "$R"
```

### 1. Transcribir y medir energía

```bash
cd "$R/01-transcripcion"
ffmpeg -i ../00-crudo/crudo.mov -ac 1 -ar 16000 audio16k.wav
ffmpeg -i audio16k.wav -af "highpass=f=150,lowpass=f=4000" voiceband.wav
$WHISPER_PY transcribe.py audio16k.wav transcripcion.json > transcripcion.txt
$WHISPER_PY vad.py voiceband.wav energy.json
```

### 2. EDL y base

1. En `build_base.py`, edita:
   - `EDL`: segmentos `S01…`; con varios tramos por segmento empalmas tomas.
   - `SPEED`.
   - `DELOGO`: la caja de la marca de agua de tu cámara.
   - `FIX` y `FIX_SEG`: correcciones de nombres y lapsus.
2. Corre `python3 build_base.py --solo-plan`, revisa el plan y luego corre
   `python3 build_base.py`.
3. **Re-transcribe la base y léela completa.** Busca tomas repetidas ocultas (una palabra de más
   de 0.9 s). En caso de duda, transcribe ventanas aisladas del crudo **sin `initial_prompt`**.

### 3. Subtítulos

`python3 words_from_base.py` usa caché. Si solo cambia un tramo, corre antes
`remap_words.py viejo_timeline.json palabras.json nuevo_timeline.json salida.json`.

### 4. Capa Remotion

1. Copia `03-render/base.mp4` a `remotion-reel/public/` y `03-render/timeline.json` a
   `remotion-reel/public/data/`, junto con clips de b-roll de tu crudo en `public/broll/`.
2. Edita `src/events.ts`. Todo se ancla con `W('Sxx','palabra')`: nunca uses segundos fijos.
3. Cambia los textos de `Cards.tsx` y `Titles.tsx`. Traen **un reel de ejemplo** (una historia de
   boletos y un Cron Job) para que veas cada pieza funcionando; también cambia el @usuario de
   `HandleTag`.
4. Genera un borrador y revisa frames clave:
   `npx remotion render src/index.ts Reel ../03-render/draft.mp4 --scale=0.5`

### 5. Final y máster

```bash
npx remotion render src/index.ts Reel ../03-render/remotion-full.mp4 --crf=18
ffmpeg -i ../03-render/remotion-full.mp4 -vf "scale=in_range=pc:out_range=tv,format=yuv420p" \
  -c:v libx264 -crf 18 -preset slow -profile:v high -color_range tv \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.79:level=false" \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart ../04-final/Reel-FINAL.mp4
bash ../audit.sh ../04-final/Reel-FINAL.mp4 ../05-auditoria/final
```

### 6. Revisión adversarial

Lanza un agente independiente de solo lectura con las 7 dimensiones del protocolo, **incluida la
veracidad**. Corrige en una versión nueva (`REEL_OUT=03-render-v2`) y re-audita antes de publicar.

## Qué trae `remotion-template/src`

| Archivo | Contenido |
|---|---|
| `lib.tsx` | Tipos del timeline, `makeTime` (W/S/E por palabra), easing, `pop`, `Icon` (máscara SVG), `strokeText` |
| `events.ts` | El guion visual y sonoro: punches, shakes, whips, glitch, riser, SFX, cortes de música, subtítulos ocultos |
| `VideoLayer.tsx` | Cámara virtual y glitch |
| `Captions.tsx` | Subtítulos estilo Hormozi |
| `Cards.tsx` | Chat, contador, prompt tecleado, plantilla guardable |
| `Titles.tsx` | Hook, chip, sello, revelación, logos, lista, usos, reloj, éxito + confeti, CTA con flecha, `HandleTag` |
| `Fx.tsx` | Grano, viñeta, flash |
| `AudioLayer.tsx` | Música con cortes y SFX con fade |
| `Reel.tsx` / `Root.tsx` | Composición 1080×1920 a 30 fps; la duración sale de `timeline.json` |
