# 🎬 Shorts Virales IA

**Sube tu video en crudo. Recibe un short listo para volverse viral.**

Una skill gratuita de [Claude Code](https://claude.com/claude-code) que convierte cualquier video
en crudo (celular, cámara, Zoom, OBS) en un short 9:16 optimizado para **TikTok, Reels y YouTube
Shorts** — de forma automática:

- 🎙️ **Corrige el audio** — limpia ruido, normaliza al estándar de las plataformas
- ✂️ **Quita muletillas y silencios** — "ehh", "este…", "o sea", pausas muertas, tomas repetidas
- 🪝 **Encuentra tu mejor gancho** — aunque esté a la mitad o al final del video, lo pone PRIMERO
- 🔁 **Cliffhangers** — re-estructura el video con open loops que sostienen la atención
- 💬 **Subtítulos kinéticos** — 7 estilos (Hormozi, word-pop, karaoke…) con la palabra clave resaltada
- 🎞️ **Movimiento constante** — zooms, Ken Burns, shakes, flashes, glitch, transiciones al beat
- 🔊 **Efectos de sonido progresivos** — whooshes, risers, impactos que crecen hacia el clímax
- 🖼️ **Imágenes generadas con IA** — b-roll que no existe, creado al vuelo con estilo consistente
- 🎭 **Quita fondos** — chroma o IA, por segmentos de énfasis
- 📱 **Optimizado para la plataforma** — 1080×1920, safe zones respetadas, export perfecto

Tú solo entregas el crudo. La skill se encarga del resto.

## Instalación (2 minutos)

Necesitas [Claude Code](https://claude.com/claude-code) instalado. Después, en tu terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/m4nueldeleon/shorts-virales-ia/main/install.sh | bash
```

O manual:

```bash
git clone https://github.com/m4nueldeleon/shorts-virales-ia.git ~/.claude/skills/shorts-virales-ia
bash ~/.claude/skills/shorts-virales-ia/scripts/setup.sh
```

El setup instala/verifica ffmpeg y Python, y descarga los materiales gratuitos (tipografías
virales OFL/Apache 2.0, emojis, efectos de sonido). Todo es **gratis y de uso comercial libre**.

> 🐣 ¿Nunca has usado una terminal? Sigue el **[TUTORIAL.md](TUTORIAL.md)** — paso a paso desde cero.

## Uso

Abre Claude Code en la carpeta donde está tu video y escribe:

```
Edita mi video crudo.mp4 y hazlo viral
```

Eso es todo. Claude va a diagnosticar tu video, transcribirlo palabra por palabra, limpiar el
audio, quitar muletillas, encontrar el mejor gancho, re-estructurar, subtitular, animar, sonorizar
y entregarte el MP4 final verificado.

También puedes pedir cosas específicas:

```
Hazme un short de 45 segundos con estilo Hormozi y música energética
Usa el momento donde hablo del resultado como gancho
Quítale el fondo cuando digo la frase clave y pon un fondo dorado
Genera b-roll con IA para la parte de los 3 errores
```

## Qué hay adentro

| Carpeta | Contenido |
|---|---|
| `SKILL.md` | El cerebro: pipeline completo de 8 fases, de crudo a viral |
| `references/` | Playbook viral (hooks, retención, cliffhangers) · 7 estilos de subtítulos · recetas de transiciones ffmpeg · guía de imágenes IA · Remotion · assets y licencias |
| `scripts/` | Transcripción word-level · corte de silencios y muletillas · subtítulos kinéticos · overlays animados · transiciones · quitar fondos · SFX sintéticos · verificación final |
| `assets/` | Se llena con `setup.sh`: fuentes (OFL), emojis Twemoji, SFX generados |

## Requisitos

- macOS, Linux o Windows (WSL)
- [Claude Code](https://claude.com/claude-code)
- `ffmpeg` (el setup te dice cómo instalarlo si falta)
- Python 3.9+
- Opcional: un MCP de generación de imágenes (Gemini, DALL·E, fal.ai…) para el b-roll con IA

## Filosofía

Este no es un "filtro mágico". Es el **playbook de edición viral completo** — hooks, retención,
pacing, pattern interrupts, dosificación de SFX, safe zones — codificado para que una IA lo ejecute
con criterio sobre TU material. Las reglas vienen de editar shorts reales y de las mejores
prácticas públicas de los creadores más grandes del formato.

## Licencia

MIT — úsala, modifícala y compártela. Los assets descargados conservan sus licencias originales
(todas gratuitas para uso comercial; ver [references/ASSETS.md](references/ASSETS.md)).
