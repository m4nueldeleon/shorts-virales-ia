# Remotion — animaciones avanzadas en React (opcional)

El pipeline base de esta skill (ffmpeg + Playwright) cubre el 90% de un short viral. **Remotion**
entra cuando necesitas motion graphics de nivel superior o plantillas reutilizables. Es video como
código React: cada frame es un render de un componente.

## Cuándo conviene Remotion (y cuándo no)

| Úsalo para | NO lo uses para |
|---|---|
| Contadores y números animados con spring físico | Cortes y trims simples (ffmpeg es 10× más rápido) |
| Gráficas de datos animadas (charts) | Subtítulos one-off (caption.html ya lo hace) |
| Escenas componibles y plantillas que reutilizarás en muchos videos | Un solo video sin reuso |
| Lower-thirds, intros y outros de marca parametrizables | Overlays estáticos |
| Captions estilo TikTok con `@remotion/captions` a escala | |
| Transiciones custom programadas (`@remotion/transitions`) | |

## Arranque

```bash
npx create-video@latest    # elige la plantilla (Hello World / TikTok captions)
npx remotion studio        # editor visual con timeline
npx remotion render src/index.ts MiComposicion out.mp4
```

## Patrones clave para shorts 9:16

1. **Composición vertical**: `<Composition width={1080} height={1920} fps={30} …/>`.
2. **El video real como capa base**, animaciones encima:
```tsx
import {AbsoluteFill, OffthreadVideo, Sequence, useCurrentFrame, spring, interpolate} from 'remotion';

export const Short: React.FC = () => {
  const frame = useCurrentFrame();
  const pop = spring({frame: frame - 30, fps: 30, config: {damping: 12}});
  return (
    <AbsoluteFill>
      <OffthreadVideo src={staticFile('base_cut.mp4')} />
      <Sequence from={30} durationInFrames={90}>
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
          <h1 style={{fontSize: 120, transform: `scale(${pop})`, color: 'white',
                      WebkitTextStroke: '12px black', paintOrder: 'stroke fill'}}>
            +$10,000
          </h1>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
```
3. **`spring()` para todo lo que aparece** (pops, entradas) e `interpolate()` con
   `extrapolateRight: 'clamp'` para movimientos lineales.
4. **`<Sequence from={f}>`** desplaza el reloj de sus hijos — así construyes el timeline.
5. **Captions TikTok**: `@remotion/captions` (`createTikTokStyleCaptions()`) consume el JSON
   word-level de `transcribir.py` (conviértelo a formato `Caption[]`).
6. **Audio**: `<Audio src={} volume={}/>` con `interpolate` para ducking bajo la voz.
7. **Assets**: siempre `staticFile('...')` desde `public/`, nunca rutas absolutas.

## Integración con esta skill

Flujo híbrido recomendado: ffmpeg corta y limpia (Fases 0–5) → Remotion añade la capa de motion
graphics sobre `base_cut.mp4` → `npx remotion render` → sigue la verificación de la Fase 8.

## Dominio profundo

Instala la skill oficial de Remotion (29 reglas: 3D, charts, transiciones, captions, Lottie,
audio, timing…): **https://github.com/remotion-dev/skills** — y la doc: https://www.remotion.dev/docs.
