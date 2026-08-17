# 🎬 Tutorial paso a paso — Shorts Virales IA

**Para quien nunca ha tocado una terminal.** Al final de este tutorial vas a poder darle un video
en crudo a la inteligencia artificial y recibir un short editado, con subtítulos, efectos y gancho
viral — sin abrir un editor de video.

Tiempo total la primera vez: **~15 minutos**. Después: solo arrastras tu video y escribes una frase.

---

## PASO 1 — Instala Claude Code (una sola vez)

Claude Code es la inteligencia artificial de Anthropic que trabaja en tu computadora.

1. Entra a **https://claude.com/claude-code** y sigue las instrucciones de descarga.
2. En Mac: abre la app **Terminal** (búscala con la lupa 🔍 Spotlight, escribe "Terminal").
   En Windows: instala primero **WSL** (busca "instalar WSL" — es un clic) y abre Ubuntu.
3. Escribe esto y presiona Enter:
   ```
   claude
   ```
4. La primera vez te pedirá iniciar sesión con tu cuenta de Claude. Hazlo y listo.

> 💡 Necesitas un plan de pago de Claude (Pro o superior) para usar Claude Code.

---

## PASO 2 — Instala la skill (una sola vez)

En la misma terminal, copia y pega esta línea completa y presiona Enter:

```
curl -fsSL https://raw.githubusercontent.com/m4nueldeleon/shorts-virales-ia/main/install.sh | bash
```

Espera a que termine (descarga tipografías, emojis y efectos de sonido — todo gratis y legal).
Cuando veas el mensaje de ✅ instalación completa, ya quedó.

---

## PASO 3 — Prepara tu video

1. Graba tu video como siempre: celular, cámara o computadora. **Vertical es ideal**, pero si lo
   grabaste horizontal, la skill lo reencuadra.
2. Consejos de grabación (hacen TODO más fácil):
   - Habla con energía desde el primer segundo. No importa si te equivocas: repite la frase y
     sigue — la IA borra la toma mala.
   - No te preocupes por los "ehh…" y silencios. De eso se encarga la skill.
   - Di tu mejor frase en algún momento. No importa dónde: la IA la encontrará y la pondrá de gancho.
3. Crea una carpeta (por ejemplo `mis-videos`) y pon ahí tu video (ej. `crudo.mp4`).

---

## PASO 4 — Edita con una sola frase

1. Abre la terminal **en esa carpeta**:
   - Mac: escribe `cd ` (con espacio), arrastra la carpeta a la ventana de la terminal, Enter.
2. Escribe `claude` y presiona Enter.
3. Escribe tu instrucción. La más simple:

   ```
   Edita mi video crudo.mp4 y hazlo viral
   ```

4. Claude va a trabajar varios minutos: transcribe, limpia el audio, corta muletillas, encuentra
   tu mejor gancho, pone subtítulos, zooms, efectos de sonido y verifica el resultado.
   Te irá contando qué hace. Si te pregunta algo (ej. qué estilo de subtítulo), responde y sigue.
5. Al final tendrás un archivo tipo `final.mp4` en tu carpeta. **Míralo antes de publicar.**

---

## PASO 5 — Pídele lo que quieras (ejemplos)

La skill entiende instrucciones en español normal:

| Quieres… | Escribe… |
|---|---|
| Un estilo específico de subtítulos | "Usa subtítulos estilo Hormozi con mi color de marca #D4AF37" |
| Elegir tú el gancho | "Usa como gancho el momento donde digo la cifra" |
| Más corto | "Máximo 30 segundos, solo lo mejor" |
| Imágenes con IA | "Genera b-roll con IA cuando hablo de los 3 errores" |
| Quitar el fondo | "Quita el fondo cuando doy el dato clave y pon un fondo con gradiente" |
| Música | "Ponle música energética de fondo" (o pon tu MP3 en la carpeta y dile que lo use) |
| Varios shorts de un video largo | "Saca 3 shorts distintos de esta clase de 40 minutos" |

---

## Preguntas frecuentes

**¿Cuánto cuesta?** La skill es gratis y de código abierto. Solo pagas tu plan de Claude.

**¿Los efectos de sonido y las letras son legales?** Sí: todo lo que descarga el setup es de uso
comercial libre (tipografías OFL/Apache 2.0 de Google Fonts, emojis Twemoji, efectos generados). Un detalle:
si usas los emojis, agrega "Emojis: Twemoji" en tu caption o créditos.

**¿Funciona con videos largos?** Sí. Puedes darle una clase de una hora y pedirle que saque los
mejores 3 shorts.

**Me dio un error de ffmpeg / Python.** Vuelve a correr el instalador (Paso 2) y lee lo que dice:
te indica exactamente qué falta y cómo instalarlo.

**¿Puedo cambiar los colores a mi marca?** Sí — díselo a Claude directamente ("usa mi dorado
#D4AF37 en los subtítulos") o edita las variables al inicio de `scripts/caption.html`.

**¿Publica el video por mí?** No. La skill edita; publicar y escribir el caption es tuyo (aunque
puedes pedirle a Claude que te sugiera caption y hashtags).

---

## ¿Qué hace por dentro? (para curiosos)

1. **Diagnostica** tu crudo (resolución, encuadre, audio).
2. **Transcribe palabra por palabra** con IA (Whisper).
3. **Limpia el audio** (ruido fuera, volumen al estándar de TikTok/IG).
4. **Corta** silencios, muletillas y tomas repetidas — por energía real del audio, no a ciegas.
5. **Encuentra el gancho más fuerte de TODO el video** y lo pone al inicio; lo segundo mejor, al
   final; y abre "loops" de curiosidad que se cierran hasta el cierre.
6. **Anima**: subtítulos kinéticos, zooms al beat, transiciones, íconos, overlays.
7. **Sonoriza**: efectos progresivos + música por debajo de tu voz.
8. **Verifica** el resultado (re-escucha el video final) y exporta optimizado para la plataforma.

Todo el conocimiento está en `SKILL.md` y `references/` — puedes leerlo, modificarlo y mejorarlo.

---

**¿Dudas o mejoras?** Abre un issue en GitHub: https://github.com/m4nueldeleon/shorts-virales-ia/issues
