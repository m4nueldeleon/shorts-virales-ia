# Transiciones y efectos — recetas ffmpeg (1080×1920, 30 fps)

Variables ffmpeg: `n`=nº frame, `t`=seg, `iw/ih`=dims entrada. Wrappers listos en
`scripts/transitions.py` (CLI + funciones importables). **Sincronía con audio = viralidad:**
punch/shake/flash/glitch/RGB deben caer en un beat o sílaba (saca timestamps con
`ffmpeg -af silencedetect=n=-30dB:d=0.4 -f null -`).

Antes de programar a mano, prueba `xfade=transition=`: `fade, fadewhite, fadeblack, wipeleft/right/up/
down, slideleft/right/up/down, circleopen/close, diagtl, dissolve, pixelize, radial, smoothleft`.

| Técnica | Efecto | Receta |
|---|---|---|
| **Zoom punch / Punch-in** | Énfasis en una sílaba | `zoompan=z='if(between(it,T,T+0.5),1.15,1.0)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30` (reloj = `it`, NO `t`; pre-`scale=1620:2880` para nitidez) → `transitions.py punch` |
| **Ken Burns** | Push-in/pan lento | `scale=8000:-1,zoompan=z='min(zoom+0.0009,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1080x1920:fps=30` (el pre-scale grande evita jitter) → `transitions.py kenburns` |
| **Impact shake** | Sacudida en un golpe | `crop=1080:1920:x='(in_w-1080)/2+20*sin(t*90)*max(0,1-(t-T)*8)':y='...+20*cos(t*110)*max(0,1-(t-T)*8)'` (desde `scale=iw*1.08`) → `transitions.py shake` |
| **Whip pan** | Barrido entre planos | cola de A con `boxblur=40:1` + crop desplazándose; empalme `xfade=transition=slideleft:duration=0.15` |
| **Speed ramp** | Slow-mo cinemático | `setpts=4.0*PTS,minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc` (interp evita el "a saltos"); audio `atempo`. Rampa = 3 tramos concatenados |
| **Jump cut** | Multicámara falso / quitar pausas | `silencedetect` → recorta `-ss A -to B` + `concat`; alterna `scale 1.0/1.06` entre cortes |
| **Match cut** | Corte invisible por forma | alinea escala/posición del sujeto en último frame de A e inicio de B con `scale`+`crop`; corte seco o `xfade=fade:0.08` |
| **Flash / Luma** | Transición de impacto | `xfade=transition=fadewhite:duration=0.2:offset=T` (`fadeblack` para negro) → `transitions.py flash` |
| **Glitch / Datamosh** | Energía/tech | `rgbashift=rh=8:bv=-8:enable='between(t,T,T+0.15)',noise=alls=20:allf=t+u:enable='...'` → `transitions.py glitch` |
| **RGB split** | Aberración cromática al beat | `rgbashift=rh='6*sin(t*8)':bh='-6*sin(t*8)'` → `transitions.py rgbsplit` |
| **Freeze frame** | Congelar + reaccionar | `-ss T -frames:v 1 frz.png` → `-loop 1 -i frz.png -t 1.5` → `concat`; combínalo con flash + zoom |
| **J/L cut** | Flujo de audio invisible | desfasa audio: J = audio de B adelantado; L = audio de A sobre inicio de B (`adelay`/`itsoffset` + `amix`) |
| **Chromakey** | Quitar fondo verde/uniforme | `[fondo][voz]overlay` con `[voz]chromakey=0x00FF00:0.20:0.08[cut]` — ver `scripts/quitar_fondo.py` para fondos reales (IA) |
| **Overlay alpha** | UI/captions/partículas | Playwright `omitBackground` → `ffmpeg -framerate 30 -i ov_%04d.png -c:v qtrle ov.mov` → `overlay=x:y:eof_action=pass:enable='between(t,a,b)'` → `transitions.py overlay`. Alpha real: qtrle / ProRes 4444 / VP9 yuva420p. **H.264/MP4 NO conserva alfa.** |

## Trampas conocidas (cada una costó un re-render)

- **`crop` no puede animar su tamaño** (`w`/`h` se evalúan una vez) → Ken Burns con `zoompan`,
  usando `on/30` como reloj (zoompan no tiene variable `t`). Pre-`scale` ~1.5× contra el jitter.
- **`overlay` congela el último frame** de un clip finito (default `eof_action=repeat`). Para
  overlays con horario: `-itsoffset <aparece> -i ov.mov` + `overlay=…:eof_action=pass:enable='between(t,a,b)'`.
- **Comas dentro de expresiones** del filtergraph van en comillas simples (`z='if(lt(...),a,b)'`)
  o se parsean como separadores de filtros.
- **Micro-fade de ~12 ms (`afade`) en cada borde de trim/concat** — sin él queda un clic audible.

## Encadenar `xfade` en una secuencia

`offset` de cada transición = (duración acumulada de clips previos) − (duración de la transición).
Automatízalo en script. Para audio usa `acrossfade=d=<dur>` en paralelo.

## Overlays de ambiente (grain / viñeta / light leak) — se generan, no se descargan

- **Film grain**: `ffmpeg -f lavfi -i "nullsrc=s=1080x1920:d=10,noise=alls=18:allf=t+u,format=gray" grain.mp4`
  → componer con `blend=all_mode=overlay:all_opacity=0.15` (10–20%).
- **Viñeta**: `ffmpeg -f lavfi -i "color=black:s=1080x1920" -vf "format=rgba,geq=a='120*pow(hypot((X-540)/540,(Y-960)/960),2)':r=0:g=0:b=0" -frames:v 1 vignette.png` → `overlay=0:0`.
- **Light leak / bokeh**: genera un gradiente animado cálido en HTML (`scripts/overlays.html`) y
  compón con blend **screen**: `[0][1]blend=all_mode=screen`.
- **Botones UI** (subscribe / follow / countdown / flecha / círculo): `scripts/overlays.html` +
  `scripts/render_overlays.py` los generan como .mov con alfa, editables (color, texto, posición).

## Receta exprés de "video viral" (orden recomendado)

1. Corte de silencios + muletillas (jump cut) + normaliza voz (`loudnorm I=-14`).
2. Ken Burns/punch suave en todo + zoom punch en sílabas clave (al beat).
3. Captions kinéticos (overlay alfa, un solo estilo).
4. SFX en cada transición/reveal (≤1 cada 2–4 s) + música −18/−24 dB.
5. Overlays de UI donde toque (countdown al inicio, follow/subscribe cerca del final).
6. Grain 12–15% + viñeta ligera para "look" premium.
7. Export H.264 CRF 18, AAC 192k, `+faststart`.
