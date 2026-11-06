# Notas de David (lo que Claude debe saber al empezar)

David (Perú) no es programador: explicar en español sencillo, paso a paso, y con
el comando exacto a pegar. Plan Claude Pro: seguir la skill `ahorro-claude`.

## Qué es esto
Fork propio de AS Video Studio, rebautizado **Shaddai Studio** (logo: lámpara de
aceite, Salmo 119:105). Vídeos animados narrados, temas bíblicos (canal «HECHOS»).

## Lo hecho (noviembre 2026)
- **Imágenes gratis (modo manual)**: el estudio da el prompt de cada plano, David
  genera la imagen (Gemini, ChatGPT...) y la sube; se ponen solas. `pasos/subidas.py`.
- **Voz gratis**: voces neuronales de Microsoft Edge (edge-tts). `pasos/voz_gratis.py`.
- Ambos modos se eligen en Configuración; Cartesia y OpenAI siguen disponibles.
- Marca Shaddai Studio en el estudio y en el login.
- Skills en `.claude/skills/`: catalogo-ropa, web-negocio, presentaciones, tesis,
  ahorro-claude, tendencias-redes, director-creativo (consejero para usar la plataforma).
- `kit-negocio/`: catálogo de ropa que ya funciona (para la tienda de su mamá) +
  guías (`LEEME.md`, `CONECTORES-Y-AHORRO.md`).

## Servidor
VPS Hostinger KVM 4, `srv2128660.hstgr.cloud` (IP 2.24.29.157), Ubuntu 24.04.
Estudio en /opt/as-video-studio. Para actualizar tras subir cambios a `main`:
`asvs actualizar` en la consola de Hostinger. Claude Code está instalado en el VPS.
Conectores de David: GitHub, Hostinger (solo estado/DNS), Google Drive, Google Sheets.

## Plan de ANIMACIÓN (decidido, empezar por la etapa 1)
Inspiración: TikTok @uncristianoinquieto (vertical 9:16, ~1:05 para Creator Rewards,
gancho «¿Sabías…?», subtítulos palabra a palabra con la clave resaltada, cifras grandes,
muñecos geométricos con túnica, personajes que SE MUEVEN). Inspirarse en el formato, no
copiar su estilo exacto. Nombre de canal propuesto: «Lumbrera» (Salmo 119:105).
El VPS no tiene GPU: nada de modelos de vídeo locales. Todo a coste 0:
1. **Etapa 1 — HECHA (5-nov-2026)**: efectos de ambiente en el render (luces que parpadean, partículas,
   agua, nubes, rayos) + profundidad 2.5D (separar personaje/fondo con rembg en CPU,
   capas con parallax) + balanceo suave. El render ya dibuja cada fotograma con el
   navegador (p8_render / capas de p7): animar con CSS/SVG/JS ahí.
   Cómo quedó: `pasos/ambiente.py` + la página de `p8_render`. Elige solo los efectos
   leyendo narración y prompt de cada plano (fuego/lámpara→luz y brasas; mar/río→agua;
   cielo/monte→nubes; tormenta→rayos; lluvia; ángel/gloria→haces de luz; polvo siempre;
   viñeta siempre). Recorta la figura con rembg (CPU, con caché) y la mueve aparte
   (parallax + balanceo); sin figura clara, balancea el plano entero. Params del render:
   `ambiente` ("auto" | "no" | lista) y `profundidad` (true/false); en plan.json una
   escena puede llevar `"ambiente": [...]` para forzarlos. Probado en vertical 1080×1920:
   ~0,5 s por fotograma en un solo proceso. Pendiente: botón en la pantalla para
   elegir efectos por plano; detectar dónde está el agua (hoy: el 30 % de abajo).
2. **Etapa 2 — HECHA (5-nov-2026)**: CLIP de vídeo por plano (además de la imagen)
   para 1-3 momentos clave hechos gratis en Kling/Hailuo/Meta AI.
   Cómo se usa: pestaña Imágenes → tarjeta del plano → «🎬 Añadir clip de vídeo»:
   «Copiar prompt del clip» (prompt de MOVIMIENTO), hacer el clip con la imagen del
   plano, «Subir clip». Luego volver a montar el vídeo (solo se rehace ese plano).
   Cómo quedó: `pasos/clips.py` + rutas `/api/proyectos/{pid}/clips/{plano}` en
   `app.py` + `p8_render` (pone los fotogramas del clip en lugar de la imagen; voz,
   subtítulos, cartelas, partículas y zoom siguen encima). Guardado en
   `<proyecto>/subidas/clips/S00N.mp4`, mudo, 30 fps, recortado al plano, máx 20 s.
   Si el plano dura más que el clip, se congela el último fotograma. Si el plano no
   tenía imagen, se usa el primer fotograma del clip. Con clip no hay recorte de
   figura ni balanceo (el clip ya se mueve). Prueba: `pasos/prueba_clips.py`.
   **Modo automático (de pago) PREPARADO Y APAGADO**: Configuración → «Clips de vídeo»
   → automático + variable `FAL_KEY` en el servidor (fal.ai, Kling 2.1, ~0,28 $/clip).
   Sin las dos cosas no gasta nada. Pendiente: probar ese modo con saldo real.
   6-nov: arreglado el error «'list' object has no attribute 'ruta_de'» al montar
   (en p8_render una variable `clips` pisaba el módulo; ahora se importa como
   `clips_video`). Mejorados los prompts: el de imagen lleva la descripción fija de
   cada personaje y del sitio + «continuidad» con el plano anterior (adjuntar su
   imagen en Gemini/ChatGPT); el de clip dice qué se mueve, la cámara y qué evitar.
3. **Etapa 3 — HECHA (6-nov-2026)**: ver «Muñecos que gesticulan» en la hoja de ruta.

## Decisión de dinero (5-nov-2026)
Por ahora TODO GRATIS: imágenes y clips a mano (manual), voz gratis, efectos del render.
Al construir algo que pueda automatizarse pagando, dejar el modo automático PREPARADO
pero apagado (como el modo de imagen OpenAI), para activarlo más adelante con una
recarga única pequeña (~10 $, fal.ai o Replicate; nada de suscripciones). Lo que más
tiempo ahorraría al pagar: imágenes automáticas baratas (~0,5-1 $ por vídeo de 1 min).

## HOJA DE RUTA DEL ESTUDIO (decidida 6-nov-2026) — una mejora por chat, en orden
Regla: cada chat nuevo hace SOLO la siguiente etapa sin hacer, pruebas ligeras, sube a
main, da `asvs actualizar` y marca aquí la etapa como HECHA (con fecha y cómo quedó).
Todo gratis; lo de pago, preparado y apagado (ver «Decisión de dinero»).
1. **Muñecos que gesticulan — HECHA (6-nov-2026)** (= etapa 3 de animación).
   Cómo se usa: al crear el vídeo (o en «El encargo») → «Dibujo» → «🧍 Muñecos que
   gesticulan». Entonces el prompt de cada imagen pide SOLO EL FONDO (sin personas) y
   el render pinta encima a los personajes del plano (máx. 3) como muñecos SVG con
   túnica: cabeza que gira, brazos con codo, parpadeo, boca que se mueve en el que
   habla, sombra. El gesto sale solo de la narración: oró/alabó/gloria → levanta los
   brazos; señaló/mirad → señala; caminó/fue/llegó → camina; dijo/habló → habla; los
   demás escuchan (asienten). El aspecto sale de la ficha del reparto (color de
   túnica, mujer → velo, barba, anciano → canas, ángel → alas y aureola).
   Cómo quedó: `pasos/marioneta.py` + página de `p8_render` (capa `#munecos`, fija en
   pantalla, encima del fondo y debajo del subtítulo) + param del render
   `marioneta: true` (sin él, el realista de siempre; no va en los defectos para no
   mover firmas). En plan.json una escena puede llevar `"gesto": "senalar"` o
   `{"Pedro": "brazos"}` o `"marioneta": false`. Un plano con clip no lleva muñecos.
   Cambiarlo en un vídeo hecho solo pide volver a montar (gratis). Prueba:
   `pasos/prueba_marioneta.py`. Pendiente: que la boca siga la voz de verdad; elegir
   el gesto por plano desde la pantalla (va bien con la etapa 2).
2. **Botón de efectos por plano — HECHA (6-nov-2026)**.
   Cómo se usa: pestaña Imágenes → tarjeta del plano → «🎇 Efectos: …» (dice cuáles
   salen y si son automáticos). Tocar un efecto lo pone o lo quita (fuego/luz, polvo,
   agua, nubes, lluvia, rayos, haces de luz); «🚫 Ninguno» los quita todos;
   «↺ Automático» vuelve a que los elija el estudio. Luego volver a montar el vídeo
   (gratis, solo se rehace ese plano).
   Cómo quedó: ruta `PUT /api/proyectos/{pid}/ambiente/{plano}` en `app.py` (cuerpo
   `{"efectos": [...]}`, `null` = automático) que lo guarda en los params de ESA
   unidad del render (`unidades["escena:S007"]["ambiente"]`, como el clip); la ficha de
   subidas trae `ambiente` y `ambiente_auto` por plano; `p8_render` lo aplica encima
   del plan.json y de "auto". Pantalla: `bloqueEfectos` en `web/app.js`.
   Pendiente: elegir también el gesto de los muñecos por plano desde ahí.
3. **Gancho de 3 s automático — HECHA (6-nov-2026)**.
   Cómo se usa: al crear el vídeo (o en «El encargo») → «Gancho» → «⚡ Gancho +
   palabra a palabra». Luego volver a montar (gratis: ni una imagen). Sale: destello
   blanco + cartel GRANDE en mayúsculas los 3 primeros segundos (palabra clave en el
   color de acento del estilo) y, en todo el vídeo, subtítulos que se encienden
   palabra a palabra (las aún no dichas, apagadas), con la palabra clave resaltada
   y las cifras más grandes. El texto del cartel sale de la primera frase del guion:
   si empieza por pregunta «¿…?», esa; si es corta, entera; si es larga, «¿Sabías
   esto? …» + sus primeras palabras (consejo: empezar el guion con «¿Sabías que…?»).
   Cómo quedó: `pasos/gancho.py` + `p7_callouts.capa_fija_de(..., primera=)` (capa
   QUIETA, SVG con SMIL; el render no cambia) + `subtitulos.de_escena(con_palabras=True)`
   (tiempo de cada palabra). Param del paso callouts `gancho`: `true` o un texto propio;
   no va en los defectos (no mueve firmas). En plan.json la 1.ª escena puede llevar
   `"gancho": "texto"` o `"gancho": false` (sin cartel). Pantalla: `selectorGancho`
   en `web/app.js`; al crear lo escribe `_sembrar_video_light` en `app.py`.
   Prueba: `pasos/prueba_gancho.py` (`--foto` pide Playwright de Python).
   Pendiente: escribir el texto del cartel desde la pantalla; un golpe de sonido
   al empezar.
4. **Plantilla TikTok — HECHA (6-nov-2026)**.
   Cómo se usa: al crear el vídeo → «Plantilla» → «📱 TikTok / Shorts». Eso pone solo:
   Vertical 9:16, gancho, la llamada a la acción del final («que me sigan…») y, si la
   duración era de 1:00 o menos, 70 s. La duración la eliges tú con los botones
   rápidos de debajo de la barra (1:10, 1:30, 2:00, 3:00, 5:00, 8:00) o escribiendo
   los segundos; el guion se ajusta a ella. Puedes cambiar el texto de debajo de
   «SÍGUEME». En un vídeo ya hecho («El encargo») solo enciende la plantilla y el
   gancho (gratis, volver a montar); el formato y la duración no se tocan solos
   (rehacen imágenes / guion) y la pantalla avisa si faltan.
   Sale: barra de progreso arriba (color de acento, crece sin saltos de plano a
   plano), «SÍGUEME» con botón rosa «+» que late los últimos 3,5 s, y un golpe de
   sonido al empezar (sintético: suena aunque no haya clave de FreeSound). Si el
   MP4 dura 1:00 o menos, el montaje avisa (Creator Rewards).
   Cómo quedó: `pasos/plantilla_tiktok.py` + `p7_callouts` (lo mete en la capa quieta
   de cada plano y deja `plantilla` en movimiento.json) + `p8_render` (golpe con
   `sonido.anadir_golpe` y aviso de duración). Un solo param: `tiktok` de callouts
   (`true`, el texto de debajo de «SÍGUEME», o `{"seguir": false|"…", "barra":
   false, "golpe": false}`); no va en los defectos (no mueve firmas). Al crear lo
   escribe `_sembrar_video_light`. Pantalla: `selectorPlantilla` y duraciones rápidas
   en `duracionLight` (`web/app.js`). Prueba: `pasos/prueba_plantilla_tiktok.py`.
   Arreglado de paso: en «El encargo», cambiar «Muñecos» o «Gancho» NO se guardaba
   (`volcarEncargoLight` solo guardaba ingesta/brief/guion; ahora también callouts y
   render). Pendiente: que el guion de TikTok tenga un ritmo propio (frases más
   cortas) y que el golpe pueda elegirse entre varios.
5. **Agente analista + ideas** (pestaña nueva «📊 Análisis / 💡 Ideas» DENTRO de Shaddai
   Studio, no otra plataforma): (a) qué pega en el nicho (Biblia, historia, «¿sabías
   que…?») en YouTube (API oficial gratis) y TikTok (enlaces/capturas que pase David):
   gancho, duración, título, miniatura, ritmo, temas; (b) cómo van los vídeos de David
   (vistas, retención, en qué segundo se va la gente); (c) propone ideas con gancho,
   duración y estilo, y un botón «Crear este vídeo» las pasa al encargo. Sustituye a la
   antigua «ideas desde tendencias» (usar la skill tendencias-redes).
6. **Un solo prompt para todas las imágenes**: un texto con todas las escenas y la
   ficha fija de cada personaje para pedirle a Gemini las imágenes de una vez.
7. **Publicar más fácil**: título, descripción y hashtags listos para copiar +
   miniatura automática para YouTube + subir el MP4 terminado a Google Drive.
8. **Más estilos y más contexto** (innovar siempre, no solo muñecos): acuarela
   animada, mapas antiguos animados (viajes de Pablo), línea de tiempo animada para
   fechas; boca de los muñecos que siga la voz; gesto de los muñecos elegible por plano;
   varias versiones del gancho para probar cuál retiene más. El estudio elige o propone
   el estilo que mejor cuenta cada tema.
9. (De pago, apagado) imágenes automáticas baratas (~0,5-1 $/vídeo, fal.ai/Replicate).
10. (De pago, ya preparado y apagado) clips automáticos fal.ai (`modo_clip=auto`).

VISIÓN (David, 6-nov): llevar el estudio AL TOPE, el mejor estudio de creación de
contenido: de la idea al vídeo publicado en un solo sitio (Análisis/Ideas → Encargo y
guion → Voz → Imágenes y clips → Edición automática → Publicar). Cada etapa se hace
COMPLETA y pulida, calidad profesional, no en versión mínima; pero con ahorro-claude
(leer solo lo necesario, una prueba corta final). Innovar y contextualizar cada vez más:
cada vídeo se adapta a su tema. Medir qué le gusta a la gente y usarlo.

PLAN INMEDIATO (6-nov): David prueba un vídeo con la plantilla TikTok (gancho + 2-3
clips), lo publica en TikTok/YouTube Shorts (para tener datos reales), y luego chat
nuevo: primero los puntos A-F de «OPINIÓN DE DAVID» (abajo), luego la etapa 5.

Mensaje que David pega en cada chat nuevo (con el repo as-video-studio elegido):
«Lee NOTAS-DAVID.md y la skill ahorro-claude. Haz la siguiente etapa de la HOJA DE
RUTA. Pruebas ligeras. Súbelo a main, dame el comando para Hostinger y actualiza mis
notas.»

## OPINIÓN DE DAVID TRAS SU PRIMER VÍDEO (6-nov-2026) — hacer ANTES de la etapa 5
Orden decidido, un chat por punto (cada uno completo y pulido):
A. **Modo ahorro de Claude** (lo primero): el estudio corre TODO en Opus/xhigh
   (`cli_claude.MODELO_POR_DEFECTO`/`por_defecto_de`) con la misma cuenta Pro de
   David y se le acaba el límite. Interruptor en Configuración para usar el modelo
   de `POR_FASE` (casi todo Sonnet). Montar el vídeo NO gasta Claude.
B. **Subtítulos**: (1) mientras sale el cartel del gancho, NO subtitular debajo (se
   ve doble); igual con cualquier cartela/elemento que ya muestre la frase. (2)
   mayúsculas y minúsculas mezcladas al leer (palabra clave/cifras en otro formato
   se ve desordenado): un solo criterio, limpio. (3) revisar sincronía palabra a
   palabra. (4) el cartel del gancho cortó la frase en «Y…?»: que corte bien.
C. **Fidelidad histórica y bíblica en los prompts de imagen**: personajes como los
   describen fuentes serias (judíos del s. I en Judea/Galilea: aspecto mediterráneo
   / Oriente Medio, ropa de la época; nada inventado), lugares y objetos reales.
   Base: Reina-Valera 1960 para citas y hechos. Que cada prompt explique lo que
   cuenta esa frase (si se habla de dos Belén → mapa con las dos y la distancia).
D. **Más explicativo en imagen**: mapas, distancias, fechas, líneas de tiempo,
   flechas/círculos que señalan (enlaza con la etapa 8 de la hoja de ruta).
E. **Guion y voz con intención**: nada de muletillas («o sea»); ritmo para
   retener todo el vídeo; pausas mejor puestas; el TONO de la voz cambia según la
   historia (alegre, lento, tenso/miedo) — con la voz gratis (edge-tts) se puede
   con SSML (velocidad, tono, pausas) por frase; decidirlo en el guion.
F. **Movimiento de imágenes y transiciones**: mejor movimiento de cámara, cortes al
   ritmo de la voz, transiciones con intención y cosas que otros no hacen.
Luego seguir la HOJA DE RUTA por la etapa 5.

## Pendiente / ideas
1. Catálogo de la mamá: faltan nombre de tienda, WhatsApp, prendas y fotos.
2. Web del negocio.
3. Web de tendencias YouTube/TikTok + ideas → Shaddai Studio.
4. Tesis y presentaciones cuando las pida.
