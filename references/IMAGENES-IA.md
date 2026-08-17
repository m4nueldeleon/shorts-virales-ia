# Imágenes y b-roll con IA — cuándo, cómo y con qué

El b-roll es la herramienta #1 de retención (pattern interrupt + prueba visual). Esta guía cubre
cómo generar el que NO existe. Regla: **genera solo lo que falta** — una captura real, un screenshot
o un plano B real siempre gana a una imagen IA mediocre.

## 1. Cuándo insertar b-roll generado

Del transcript, marca momentos que piden apoyo visual:
- **Conceptos abstractos** ("libertad financiera", "escalar tu negocio") → imagen metafórica.
- **Datos y números** → gráfico animado (mejor HTML→Playwright que imagen estática, ver §4).
- **Objetos/lugares mencionados** que no salen en cámara.
- **Antes/después** o resultados que el hablante describe.
Dosis: 3–6 inserciones por short de 45–60 s, de 2–4 s cada una, SIEMPRE con la voz del hablante
encima (el audio principal nunca se corta).

## 2. Con qué generar (usa lo que exista en el entorno)

En orden de preferencia, detecta qué herramienta tiene el usuario disponible:
1. **MCP de imágenes conectado a Claude Code** — cualquiera sirve: Gemini/nano-banana, Higgsfield,
   DALL·E, fal.ai, Stable Diffusion local. Pide 1080×1920 o 4K vertical si el modelo lo permite.
2. **APIs con key del usuario** (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `FAL_KEY`…) vía script corto.
3. **Sin ninguna herramienta de imagen** → NO bloquees la edición: usa gráficos HTML/CSS renderizados
   con Playwright (§4), capturas de pantalla, o zoom/crop creativo del propio material.

## 3. Prompts que funcionan para b-roll vertical

- Especifica SIEMPRE: formato vertical 9:16, fotorrealista o el estilo elegido, sin texto
  ("no text, no words, no letters" — el texto lo pones tú con overlays).
- **Consistencia**: define UNA dirección de arte para todo el video (misma paleta, mismo estilo,
  misma iluminación) y repítela en cada prompt. Cambiar de estilo entre inserciones se ve amateur.
- Plantilla: `"<sujeto/concepto>, vertical 9:16 composition, <estilo: cinematic photo / 3D render /
  editorial illustration>, <paleta>, dramatic lighting, no text"`.
- Para conceptos de negocio/dinero: objetos físicos metafóricos (relojes, escaleras, puertas,
  cofres, gráficas físicas) funcionan mejor que ilustraciones literales.

## 4. Gráficos de datos animados (HTML → Playwright)

Para números, contadores, barras y comparativas, genera un HTML/CSS con la animación y renderízalo
a overlay alfa (misma técnica que los subtítulos — ver `scripts/render_overlays.py`):
1. Escribe un HTML con la gráfica animada por `t` (función `render(t)` como en `overlays.html`).
2. Renderiza frames RGBA con Playwright (`omit_background=True`) → `ffmpeg -c:v qtrle out.mov`.
3. Compón con `overlay` + `enable='between(t,a,b)'`.
Ventaja: control total de marca, tipografía y sincronía word-level con lo que se dice.

## 5. Montaje del b-roll

- Inserta con **Ken Burns** (`python scripts/transitions.py kenburns`) — una imagen estática sin
  movimiento mata el ritmo.
- Entrada/salida con whoosh (`assets/sfx/`) o flash si es un reveal.
- Alterna dirección del movimiento (push-in, luego pan, luego push-out) entre inserciones seguidas.
- Respeta safe zones si la imagen lleva elementos importantes (top 220 / bottom 480 / right 120 px).

## 6. Video generado con IA (opcional)

Si el entorno tiene generación de video (Higgsfield, Veo, Kling, Runway…), un clip de 3–5 s como
b-roll de alto impacto en el hook o el peak puede elevar el video. Mismo principio: estilo
consistente, sin texto, vertical. No sustituyas al hablante: la cara humana retiene.
