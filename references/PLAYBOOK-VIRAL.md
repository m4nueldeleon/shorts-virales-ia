# Playbook viral — Short-form 15–60s, 9:16

Sistema accionable para maximizar **retención** (watch-time, %, replays) y **viralidad** (shares,
saves). Cada decisión de edición se justifica contra estas métricas.

## 0. Métrica norte

| Métrica | Objetivo | Qué la mueve |
|---|---|---|
| Hook rate (% que pasa de 3 s) | >70% | Primer frame + primera frase + movimiento |
| Avg view duration | >50% | Pacing, open loops, pattern interrupts |
| Saves / Shares | maximizar | Valor denso, listas, "guárdalo", utilidad |
| Replays / completion | >100% | Bucle final que engancha con el hook |

Regla madre: pregúntate **"¿por qué no deslizan AQUÍ?"** cada 2–3 segundos.

## 1. HOOK (primeros 1–3 s) — tres capas en paralelo (<1 s)

Dispara las tres a la vez: **visual** (primer frame ya en movimiento, sin intro estática ni logo),
**verbal** (la afirmación más fuerte primero, sin "hola, hoy les hablo de…", ≤8 palabras) y **texto
grande** en pantalla (85% ve en mute). Recorta el aire muerto hasta el frame donde empieza la energía.

**El hook puede venir de CUALQUIER parte del crudo** — mitad, final o inicio. Transcribe todo,
puntúa los momentos más fuertes y usa el mejor como cold-open aunque en el crudo aparezca al minuto 4.

Tipos de hook (combínalos):
- **A. Resultado/promesa:** "Así pasé de 0 a 100k en 90 días."
- **B. Contradicción/contra-intuitivo:** "Deja de hacer cardio si quieres bajar de peso."
- **C. Curiosidad/open loop:** "Nadie te dice esto sobre…"
- **D. Negativo/pérdida (loss aversion):** "Estás perdiendo dinero si…"
- **E. Callout al nicho:** "Si eres coach, esto es para ti."
- **F. Lista numeral:** "3 errores que te están costando clientes."
- **G. Prueba/shock visual:** muestra el resultado PRIMERO.
- **H. Historia in-media-res:** entra a mitad de la acción.
- **I. Autoridad/dato duro:** "El 92% de los reels fallan por esto."

Combos top: contradicción+lista · resultado mostrado+open loop · callout de nicho+pérdida.

## 2. RETENCIÓN

- **Pattern interrupt cada 2–4 s:** corte de plano, zoom punch (5–15%), b-roll, texto/emoji/flecha,
  silencio dramático, SFX. Ningún plano >3–4 s sin cambio visual.
- **B-roll = herramienta #1:** literal, metafórico o de prueba (screenshots → saves). Audio principal
  por encima del b-roll. Si el b-roll no existe, genéralo con IA (ver IMAGENES-IA.md).
- **Open loops / cliffhangers:** abre uno al inicio ("al final te enseño el truco #3"), encadena
  micro-loops (corta justo antes del dato clave y mete un pattern interrupt), y cierra el principal
  **SOLO al final** → sostiene replays/completion.
- **Subtítulos siempre**, con la palabra clave resaltada (ver ESTILOS-SUBTITULOS.md).
- **Densidad:** una idea por video, cero relleno, habla más rápido de lo natural.

## 3. ESTRUCTURA base

```
[0–3s]   HOOK      promesa/tensión + open loop + texto grande
[3–8s]   SETUP     contexto mínimo, por qué AHORA
[8–45s]  PAYLOAD   valor en pasos; cada paso = micro-loop + pattern interrupt
[45–55s] PEAK/GIRO lo mejor al final; cierra el loop principal
[55–60s] CTA+LOOP  una sola acción; la última frase engancha con el hook
```
Lo mejor NO va al inicio del cuerpo: resérvalo para el final. Arcos: listicle · tutorial (resultado
primero) · storytime (in-media-res) · POV · mito vs realidad.

## 4. PACING y corte al beat

- Corte cada **1.5–3 s**, frame-tight: elimina silencios, muletillas ("ehh", "este", "o sea"),
  respiraciones (silencedetect).
- J-cuts / L-cuts para flujo invisible (audio entra antes/sale después del corte de video).
- Acelera 1.05–1.2× lo lento; slow-mo solo el momento emocional (con `minterpolate`).
- **Sincroniza** cortes/transiciones/zooms con el beat de la música; los hits/drops = punto para zoom
  punch o reveal. Saca beats de `silencedetect`/onsets.
- Mezcla de audio: voz limpia y normalizada al frente (`loudnorm I=-14`), música **−18/−24 dB**, SFX
  en cada transición, cero silencio muerto.

## 5. CTA y bucle final

UNA sola acción (save / comenta una palabra / follow para parte 2 / comparte etiquetando). Breve, sin
cierre largo de vendedor. **Bucle final:** la última frase encadena con el hook → completion >100%,
sin pantalla muerta de logo.

## 6. Errores que matan retención

Preámbulo · primer frame estático · sin subtítulos · planos >4 s · aire muerto · audio sucio o bajo ·
cerrar el loop demasiado pronto · demasiadas ideas · CTA múltiple · efectos en TODO (cansa) · texto en
la zona de UI · ritmo conversacional normal · final con logo muerto · música que tapa la voz ·
mezclar varios estilos de subtítulo en un mismo video.

## 7. Checklist pre-publicación

- [ ] ¿El primer frame engancha en mute? ¿La primera frase es la más fuerte de TODO el crudo?
- [ ] ¿Hay un pattern interrupt cada 2–4 s? ¿Algún plano >4 s?
- [ ] ¿Subtítulos legibles, en safe zone, un solo estilo, palabra clave resaltada?
- [ ] ¿Cortes al beat? ¿Voz al frente, música −18/−24 dB, SFX dosificados (≤1 cada 2–4 s)?
- [ ] ¿Open loop abierto al inicio y cerrado al final? ¿Bucle final que reengancha?
- [ ] ¿Cero muletillas y cero aire muerto? ¿Una sola CTA clara?
- [ ] ¿Texto y gráficos fuera de top 220px / bottom 480px / right 120px (UI de la app)?
- [ ] ¿Exporta 1080×1920, H.264 CRF 18, AAC 192k, +faststart?
