# Protocolo PRO — de crudo a reel que se comparte (probado en producción)

Protocolo nacido de un reel real publicado en una cuenta de más de 500 mil seguidores. El creador lo
aprobó a la primera. Complementa a `SKILL.md` con **lo que la versión básica no cubre**:
- ruido ambiente;
- tomas repetidas que la transcripción esconde;
- desfase del timeline;
- motion graphics anclados a palabras;
- revisión de veracidad antes de publicar.

El motor que lo implementa está en `scripts/motor_reel/`; su README trae el arranque paso a paso.

## 4 fases con puerta

**PLAN → EJECUTAR → AUDITAR → ENTREGAR.** El plan se escribe (`PLAN.md`) y se muestra antes de
tocar el video. Después se ejecuta de corrido.

### 1. Plan
1. **Diagnóstico.** `ffprobe` y una hoja de contacto de ~40 frames. Ahí se ve el encuadre, el
   b-roll aprovechable, las personas ajenas y la marca de agua de la cámara.
2. **Transcripción word-level.** Primero WAV 16 kHz mono; luego whisper con `word_timestamps`.
3. **Hook con datos, no con gusto.**
   - Revisa tus reels con más alcance y seguidores ganados.
   - Copia la ESTRUCTURA de sus primeras frases, no el texto.
   - Patrón típico que gana: resultado concreto o dolor en ≤ 3 s + «la herramienta que casi nadie
     usa» + pasos + «guárdalo».
4. **Re-estructura.** El orden del crudo no manda. Arco:
   - **Hook:** la mejor frase de todo el crudo, con texto grande desde el cuadro 0.
   - Contexto mínimo.
   - **Open loop:** una promesa que se cierra al final.
   - Problema.
   - **3 cliffhangers:** sello del problema; congelado con glitch y la música cortada; reloj
     time-lapse.
   - **Revelación.**
   - Resultado.
   - Plantilla guardable.
   - Usos.
   - CTA «guárdalo» que reengancha con el hook.
5. **Lista de lo que sale.** Claqueta, backstage, instrucciones a quien graba, personas ajenas
   identificables, tomas repetidas, muletillas de cierre.

### 2. Ejecutar

**Base (ffmpeg)**
- **Cortes por envolvente de energía de voz** cuando hay ruido ambiente. `silencedetect` puede no
  encontrar ni un silencio en exteriores.
  - Media local de la banda 150–4000 Hz por debajo de ~−26 dB.
  - Picos < 100 ms no rompen la pausa.
  - Bordes en el valle de energía.
- **Protege palabras cortas reales** (≤ 0.45 s): el umbral se las come («tus», «ya», «el»).
- **Cuadros exactos por pieza.** Video con `trim=end_frame=N`; audio con
  `apad=whole_dur=N/30,atrim=end=N/30`. Si no, el concat rellena y el timeline se desfasa medio
  segundo al final: subtítulos y efectos caen fuera de su palabra.
- **Voz a 1.1×** con `atempo`: ritmo de reel con el tono intacto.
- **Congelado** de 0.5 s en cliffhangers y cola de 0.4 s al final.
- **Marca de agua de la cámara.** `delogo` en la caja más una etiqueta con tu @usuario encima.
  `removelogo` deja un fantasma legible sobre fondos lisos.

**Verificación de la base (antes de animar nada)**
- **Re-transcribe el corte.** Whisper **esconde tomas repetidas estirando una sola palabra 1–2.5 s**.
  - Busca palabras > 0.9 s y frases que se repiten.
  - En caso de duda, transcribe ventanas aisladas del crudo **sin `initial_prompt`**: con prompt,
    whisper «completa» lo que no está.
- **Arreglo:** recorta el tramo o empalma la mejor mitad de cada toma. La EDL admite varios tramos
  por segmento.

**Subtítulos**
- **Fuente:** la re-transcripción del corte, que da tiempos exactos. No mapees el transcript del
  crudo.
- **Caché:** whisper cambia entre corridas. Si solo cambia un tramo, reubica palabras con el mapa
  crudo → corte en vez de re-transcribir.
- **Correcciones de nombres** (ChatGPT, Claude, marcas) con un diccionario.
- **Estilo:**
  - ≤ 3 palabras en pantalla y palabra dicha en el color de acento.
  - Contorno por fuera (`paint-order`) y margen ≥ 24 px entre palabras, porque el contorno se come
    el espacio.
- **Se ocultan** cuando una tarjeta ya muestra el mismo texto.

**Motion graphics (Remotion)**
- **Todo anclado a PALABRAS dichas** (buscando en la ventana del segmento ±0.3 s), nunca a segundos
  fijos.
- **Cámara virtual.**
  - Escala alterna por toma más un push lento.
  - Zoom punch en palabras clave y shake en impactos.
  - Whip en cambios de lugar. Su amplitud debe ser menor que el margen del zoom, o sale una franja
    negra.
- **Piezas probadas:**
  - Título del hook y chip de contexto.
  - Sello del problema.
  - Chat con respuesta tecleada; contador de envíos.
  - Revelación con definición correcta.
  - Logos reales; lista con íconos.
  - Prompt tecleado al ritmo de la voz.
  - Reloj time-lapse.
  - Éxito con confeti sobre b-roll de celebración.
  - Plantilla guardable (solo se ilumina la opción que se dice).
  - CTA con flecha a los botones.
  - Etiqueta @usuario.
- **Logos reales** de simple-icons teñidos con `mask-image`. **Verifica renderizando.**
- **Tarjetas debajo de la cara** y encima de los subtítulos. Nada en la zona de UI y nada entra
  desde `scale(0)`.
- **Música.** Ganancia calculada por loudness (≈ 19 dB bajo la voz). Se **corta** en cada
  cliffhanger y vuelve de golpe en la revelación.
- **SFX progresivos.** El riser termina exactamente en la revelación.
- **Máster.**
  - Remotion saca `yuvj420p`: convierte con `scale=in_range=pc:out_range=tv,format=yuv420p`.
  - `loudnorm=I=-14:TP=-1.5` más `alimiter`, porque loudnorm solo puede pasar de 0 dBFS.

### 3. Auditar (dos capas)
1. **Técnica.** Specs, loudness y pico, re-transcripción del final, hoja de frames cada 2 s y un
   frame por cada gráfico.
2. **Revisión adversarial.** Un agente independiente, solo lectura, con 7 dimensiones:
   - texto en pantalla;
   - solapamientos y zonas seguras;
   - ritmo;
   - hook sin sonido;
   - **veracidad y riesgo de marca**;
   - audio medido;
   - arco de la historia.

   En el caso real encontró dos críticos que ninguna métrica ve: un hook que contradecía la
   historia y una plantilla que prometía algo que la herramienta no hace así.
3. **Corrige en una versión nueva** y re-audita.

### 4. Entregar
- Video final más **caption con la primera línea = hook**, la historia en 3 bloques, la plantilla
  copiable, «guárdalo» y 3–5 hashtags.
- Lista de decisiones pendientes para el creador (lo que no se pudo verificar).

## Reglas de veracidad
- El hook no promete algo que la historia contradice.
- Los gráficos no agregan afirmaciones que el creador no dijo; si él dijo algo impreciso, el
  gráfico lo precisa en vez de amplificarlo.
- La tarjeta y la voz dicen lo mismo.
- Nada de logos ni personajes de terceros en gráficos añadidos.

## Checklist de salida
- [ ] El primer cuadro engancha en mute; el hook es fiel a la historia.
- [ ] Re-transcripción del final sin repeticiones ni palabras cortadas.
- [ ] Duración del timeline = duración del video (±1 cuadro).
- [ ] Ningún plano > 4 s sin cambio; whips sin franja negra.
- [ ] Tarjetas fuera de la cara y de la zona de UI (arriba 220, abajo 480, derecha 120 px).
- [ ] −14 LUFS ±1, pico ≤ −1 dBFS, `yuv420p`, 1080×1920, 30 fps.
- [ ] Revisión adversarial corrida; críticos y altos corregidos.
