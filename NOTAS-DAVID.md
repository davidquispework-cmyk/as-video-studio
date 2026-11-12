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
  ahorro-claude, tendencias-redes, director-creativo (consejero para usar la plataforma),
  motion-graphics (reglas decididas del punto G).
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
copiar su estilo exacto. Canal real: «Nadie Me Lo Explicó» (NMLE); ver skill director-creativo.
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
5. **Agente analista + ideas — HECHA (6-nov-2026)**.
   Cómo se usa: barra de abajo → «💡 Ideas» (siempre a mano, no hace falta abrir un
   vídeo). Cuatro pestañas:
   - **📊 El nicho**: escribe las búsquedas (una por línea; vienen puestas las del
     nicho bíblico), país y días → «🔎 Buscar ahora». Mide en YouTube los vídeos que
     más crecen (vistas/día) y da consejos: qué duración crece más, qué títulos
     (pregunta, cifra, «sabías»), palabras repetidas, mejor hora y día (hora de Lima),
     interacción. Gráfico de duración y lista de los 30 mejores con miniatura.
   - **🎵 TikTok**: pega enlaces de TikToks que te gusten (+ vistas, duración, notas);
     el título y el autor salen solos. Enlace a TikTok Creative Center para ver
     tendencias. (TikTok no tiene API pública: no se puede automatizar más, legalmente.)
   - **📈 Mis vídeos**: pon tu @ de YouTube → «🔄 Traer mis vídeos» (vistas, me gusta,
     comentarios). La retención la escribes en cada vídeo («% visto» y «se van en el
     s») o pegas la exportación de YouTube Studio (Analytics → Modo avanzado →
     Exportar → CSV). Los TikTok, a mano. Da consejos («la gente se va en el s 8…»).
   - **💡 Ideas**: tema opcional, cuántas (3/5/8), para TikTok o YouTube largo →
     «💡 Pensar ideas» (Claude, ~1 min). Cada idea: título, gancho de 3 s, por qué
     (con el dato), duración, formato, muñecos/realista, estilo, MATERIAL con citas
     bíblicas, cómo contarlo, clips, hashtags y texto de miniatura. Botones:
     «🎬 Crear este vídeo» (rellena el encargo del vídeo nuevo: nombre, duración,
     formato, material, indicaciones con el gancho, gancho, muñecos y plantilla TikTok;
     tú eliges el estilo y pulsas Generar), «📋 Copiar», «⭐ Favorita», «Descartar».
     No repite ideas ya propuestas.
   **Hace falta la clave de YouTube (gratis)**: la pantalla explica los 3 pasos
   (console.cloud.google.com → habilitar «YouTube Data API v3» → Credenciales → Clave
   de API) y la guarda ahí mismo. Cuota: 10.000/día; una búsqueda del nicho gasta
   ~600 y se guarda 6 h. Sin la clave, TikTok, «a mano» e Ideas funcionan igual.
   Cómo quedó: `pasos/analista.py` (todo el cálculo + ideas con el CLI, sonnet/medium,
   en segundo plano; la pantalla pregunta cada 3 s) + rutas `/api/analisis/*` en
   `app.py` + clave `youtube` en `claves.py` (y «Probar» en `comprobar_claves.py`) +
   pantalla `vistaAnalisis` en `web/app.js` (parada «ideas» de `navLight`). Los datos
   van en `analisis.json` junto a `ajustes.json` (en el VPS `datos/analisis.json`;
   `asvs actualizar` no lo toca). No toca proyectos ni firmas. Prueba:
   `pasos/prueba_analista.py`. Pendiente: retención automática con OAuth de YouTube
   Analytics (curva segundo a segundo); histórico del nicho día a día; leer
   capturas de TikTok con Claude.
6. **Un solo prompt para todas las imágenes — HECHA (11-nov-2026)**: un texto con
   todas las escenas y la ficha fija de cada personaje para pedirle a Gemini las
   imágenes de una vez.
   Cómo quedó: en la pantalla de subir imágenes (modo manual) hay dos botones nuevos,
   «Copiar prompt único» y «Descargar prompt único» (si faltan algunas, solo las que
   faltan). El texto lleva UNA vez arriba el estilo, la época (si es bíblico), la
   FICHA FIJA de cada personaje que sale (nombre, papel y aspecto: misma cara, edad,
   pelo, barba y ropa en todas) y los sitios; debajo, cada plano numerado «1 · S001»
   con qué se ve, dónde, quién sale, el mapa si lo pide y la frase narrada. Se pega
   en Gemini: hace la 1 y con «sigue» la siguiente («otra vez» repite). Las imágenes
   se guardan como S001.png… y se suben como siempre. Con muñecos pide solo el fondo.
   Código: `subidas.prompt_unico` + `ficha_fija` (pasos/subidas.py),
   `p6_assets.prompt_unico` (y `_escenas_con_imagen`, compartido con
   `prompts_para_subir`), ruta `GET /api/proyectos/{pid}/subidas/prompt_unico.txt`
   en `app.py`, `copiarPromptUnico` en `web/app.js`. Solo lee: no toca params ni
   firmas. Prueba: `probar_prompt_unico` en `pasos/prueba_subidas.py`.
   Pendiente: editar a mano la ficha de un personaje desde la pantalla; partir el
   texto en tandas de 20 si Gemini se pierde en vídeos muy largos.
7. **Publicar más fácil — HECHA (11-nov-2026)**.
   Cómo se usa: con el vídeo montado, debajo del repaso sale «🚀 Publicar»:
   título (+ 2 alternativas), descripción, hashtags y texto para TikTok, cada uno
   con su botón «Copiar». Debajo, la MINIATURA (YouTube 1280x720 y portada
   vertical 1080x1920): eliges la imagen (desplegable u «Otra imagen →») y el
   texto grande (2-4 palabras; la más larga sale en amarillo) y se ve al momento;
   «Bajar…» la descarga. «📦 Descargar todo (.zip)» trae vídeo + las dos portadas
   + `textos_para_publicar.txt` (vale desde el móvil). «☁️ Subir a Google Drive»
   lo copia todo a la carpeta «Shaddai Studio/<nombre del vídeo>» de tu Drive
   (necesita conectar Drive UNA vez en el servidor, ver abajo).
   Qué sale: la descripción lleva el gancho, de qué va, los VERSÍCULOS citados
   (RV1960), los CAPÍTULOS de YouTube (uno por bloque del guion, solo en
   horizontal y si hay 3+ de 10 s o más), la llamada a suscribirse y los
   hashtags (máx. 15: los nombres propios más repetidos y los libros citados delante, los del tema
   detrás; en vertical #shorts el primero). GRATIS: no llama a Claude ni toca
   params ni firmas; todo vive en `<proyecto>/publicar/`.
   Conectar Drive (una vez, en la consola del VPS): `curl https://rclone.org/install.sh | sudo bash`,
   luego `rclone config` → n → nombre `drive` → tipo `drive` → Enter a todo
   hasta «Use web browser…?» → **n** → copia el comando `rclone authorize "drive" "…"`
   que te da, ejecútalo en tu PC (rclone.exe de rclone.org/downloads), entra con
   tu Google y pega el token que sale de vuelta en el VPS → «Shared Drive?» n → q.
   Después `asvs actualizar` (o reiniciar el estudio). Otro nombre/carpeta:
   variables `ESTUDIO_DRIVE_REMOTO` y `ESTUDIO_DRIVE_CARPETA`.
   Código: `pasos/publicar.py` (`textos`, `capitulos`, `miniatura`, `drive_listo`,
   `subir_a_drive`) + rutas `/api/proyectos/{pid}/publicar` (y `/miniatura.jpg`,
   `/paquete.zip`, POST `/drive`) en `app.py` + `panelPublicar` en `web/app.js`.
   Prueba: `pasos/prueba_publicar.py`.
   Pendiente: subir directo a YouTube (OAuth) y programar la hora; títulos
   «mejorados con Claude» (botón opcional, de pago); elegir la palabra en amarillo.
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

**ORDEN NUEVO (decidido 11-nov-2026) — manda sobre todo lo de abajo:**
1. Etapa 6, un solo prompt para todas las imágenes con ficha fija — **HECHA (11-nov)**.
2. Voz gratis elegida sola según el tema — **HECHA (11-nov)**. Cómo se usa: nada;
   está encendida de fábrica (Configuración → Voz → «Elegir la voz según el tema»
   para apagarla). Al grabar la voz de un vídeo POR PRIMERA VEZ, el estudio lee el
   guion (o el material) y decide el tema —fe/bíblico, historia, misterio, niños,
   motivación, ciencia o documental— más el tono dominante, y pone la voz que le va
   (p. ej. fe → Gonzalo de Colombia, grave y serena; niños → Dalia; misterio →
   Alonso). Gratis: no llama a Claude. Se GUARDA en el vídeo, así regrabar un bloque
   no cambia la voz; si cambias la voz a mano en un vídeo, manda la tuya
   (`voz_a_mano`). Los vídeos ya grabados no se tocan. Solo castellano.
   Código: `pasos/voz_tema.py` (temas, tabla de voces descritas a mano, `elegir`) +
   `app._voz_por_tema` (justo antes de la primera locución) + ajuste
   `voz_por_tema` en `pasos/ajustes.py`. Prueba: `pasos/prueba_voz_gratis.py`.
   Pendiente: afinar la tabla de voces oyéndolas; ver en la pantalla del vídeo qué
   voz eligió y por qué (hoy va en la bitácora y en los params de la voz).
3. Etapa 7, publicar fácil — **HECHA (11-nov)** (ver la etapa 7 de la hoja de ruta).
4. F, movimiento y transiciones — **HECHO (11-nov)**. Cómo se usa: nada; está
   encendido de fábrica. Al crear el vídeo (o en «El encargo») hay una fila nueva,
   «Cámara»: **🎥 Cámara viva** (de fábrica) o **🖼 Clásica** (el zoom de antes).
   Gratis: cambiarla solo pide volver a montar.
   Qué hace la cámara viva (en cada imagen, no en motion graphics ni cartelas):
   movimiento continuo (sin pararse en seco al principio y al final); **golpe de
   zoom** con anticipación y rebote en la palabra que importa (cifra, nombre
   propio, «nunca/todo/Dios…», la Y de «no X, sino Y», la clave de una pregunta o
   exclamación), como mucho uno cada 4 s en todo el vídeo; **temblor** corto en
   palabras de impacto (cayó, trueno, estalló…); **cámara al hombro** mínima
   para que ningún plano esté muerto; un plano sin recorrido se acerca o aleja un
   4 %; y **arrastre a través del corte**: antes de un latigazo la cámara acelera
   de lado y el plano siguiente llega con ese impulso (con zoom igual).
   **Transiciones con intención**: se lee cómo EMPIEZA la frase del plano que
   entra: «años después» → fuga de luz larga; «recuerda / hace siglos» →
   deformación; «pero / sin embargo» → latigazo; «de repente / entonces / ¡» →
   destello; fuego → quemado; muerte/pecado/oscuridad → disolución; agua/sueño →
   ondas; desierto → calor; luz/cielo/milagro → fuga de luz; «dentro de» → zoom;
   «¿…?» → iris. Si no dice nada, el reparto de siempre. Nunca dos iguales
   seguidas; los temas no se repiten en 3 cortes.
   Código: `pasos/camara.py` (`preparar` y `CAMARA_JS`) + `p8_render` (`__CAM__`,
   `confs_camara`) + `transiciones.INTENCIONES`/`intencion` + `selectorCamara` en
   `web/app.js` + `app.py` (param `camara` del render: solo se escribe
   «clasica», o «viva» para volver; no mueve firmas). `"intencion": false` en el
   render apaga la intención. Prueba: `pasos/prueba_camara.py`.
   Pendiente: verlo en un vídeo real y ajustar fuerza del golpe (5,5 %) y del
   temblor; ver en la pantalla qué transición eligió y por qué.
5. La voz grabada de David — **HECHA (11-nov)**. Cómo se usa: abre el vídeo →
   pantalla del guion → arriba, «🎙 ¿Prefieres tu propia voz?». (1) «Copiar el
   texto a leer» y léelo TAL CUAL en el móvil (grabadora o WhatsApp, sitio sin
   eco); (2) «Subir mi grabación» (mp3, m4a, wav, ogg, opus…); (3) «Regenerar
   Audio». Desde ahí el vídeo usa TU voz: subtítulos, cortes, cámara, todo
   igual. «Quitar» vuelve a la voz sintética. Gratis: no llama a nadie.
   Qué hace: limpia el audio (mono, filtro de graves, volumen igualado a
   -16 LUFS), busca los silencios y los empareja con los puntos y comas del
   guion; dentro de cada frase reparte las palabras por sílabas. Si improvisas
   al leer, los subtítulos se desfasan. Regrabar un tramo suelto no se puede
   con voz propia (se sube la grabación entera otra vez).
   Código: `pasos/voz_propia.py` (guardar, `alinear`, `toma`) + `p4_voz`
   (`motor_voz = "propia"` si los params de la voz traen `grabacion` = huella
   del fichero; `grabacion_de`) + `p5_revision_audio` + rutas
   `/api/proyectos/{pid}/voz/grabacion` (GET/POST/DELETE, y `/audio`) en
   `app.py` + `vozPropiaLight` en `web/app.js`. Guardada en
   `<proyecto>/subidas/voz/grabacion.wav`. Subirla mueve la firma de la voz
   (a propósito: la voz cambió); los demás vídeos no se tocan.
   Prueba: `pasos/prueba_voz_propia.py`.
   Pendiente: probarla con una grabación real tuya y afinar el alineado si
   los subtítulos se adelantan/atrasan; quizá grabar desde la propia página.
6. Ver en pantalla qué voz y qué transiciones eligió el estudio y por qué —
   **HECHO (11-nov)**. Cómo se usa: (a) abre el vídeo → pantalla del guion →
   arriba sale «🗣 Voz: Gonzalo (Colombia) · elegida sola por el tema del vídeo
   (tema fe/bíblico, …)» (o «elegida a mano»; no sale si usas tu voz grabada).
   (b) Pantalla del vídeo ya montado → abajo, plegable «🎬 Transiciones: N
   cortes, M elegidos por lo que dice la frase»: al abrirlo, la lista de cortes
   en orden con su transición; las elegidas por la frase llevan ✦, el motivo
   («giro o contraste», «salto en el tiempo»…) y las primeras palabras del plano
   que la pidieron. Gratis, solo lee: no mueve firmas.
   Código: `app._ficha_grabacion` (clave `voz`) + `leer_transiciones` (añade
   `arranque` a los cortes con intención) + `vozElegidaLight` y
   `panelTransicionesLight` en `web/app.js` + estilos `.voz-elegida`,
   `.trans-vista`, `.lista-trans` en `estilo.css`.
   Pendiente: con eso delante, oír las voces y ajustar la tabla de
   `voz_tema.VOCES_ES`, y la fuerza del golpe/temblor de la cámara.
   **Arreglo (11-nov)**: (a) en ese recuadro «🗣 Voz» ya se puede CAMBIAR la
   voz gratuita de ESE vídeo (lista + «▶ Escuchar»; «Quitar mi elección» la
   devuelve). Se guarda como elegida a mano en `voz.voz_del_video`, que NO entra
   en ninguna firma (`nucleo/estado.py:FUERA_DE_FIRMA`): no deja obsoleta
   ninguna imagen; se oye al pulsar «Regenerar Audio» (`app._esta_al_dia` da la
   voz por pendiente hasta grabarla). Ruta `PUT /api/proyectos/{pid}/voz/del-video`.
   (b) La voz por tema ya NO pisa la voz gratuita que trae el estilo (pasó: Alex
   Perú → Gonzalo Colombia); solo elige si el estilo no trae voz gratuita.
   (c) El recuadro dice de dónde sale la voz (tema, estilo, Configuración, a
   mano) y ya no manda a «cambiarla en el estilo o en Configuración».
   (d) Debajo, «Velocidad:» (−15 % … +30 %) también solo para ese vídeo,
   guardada en `voz_del_video.velocidad` (número −1..1, ×35 = %), fuera de
   firma igual que la voz; «▶ Escuchar» la pone a esa velocidad. Más rápida =
   el audio y el vídeo duran menos.
   Prueba: `pasos/prueba_voz_gratis.py` (`probar_voz_del_video`).
6b. Voz de personaje y frase clave — **HECHO (12-nov)** (pedido por David tras
   medir un vídeo de referencia de @sinfiltroperocontexto: narra a ~3,5 pal/s,
   frena las frases clave a 1,7-2,2 con 1-2 s de silencio antes, y los
   personajes hablan con otra voz). Cómo se usa: nada; con la voz gratuita, el
   guion NUEVO sale con dos etiquetas que no se oyen: `<personaje nombre="Jotam"
   genero="hombre">…</personaje>` (lo dice OTRA voz gratuita, estable por
   nombre: `voz_gratis.voz_de_personaje`) y `<clave>…</clave>` (40 puntos más
   lenta, un poco más baja y con silencio antes: `voz_gratis.CLAVE_*`). En la
   pestaña Guion cada bloque lo marca con «🎭 Nombre» / «🔑 frase clave». Con
   Cartesia se quitan antes de mandarle el texto (`marcas_tts.sin_voces`). Los
   guiones ya escritos no cambian; editar un bloque a mano quita sus marcas
   (como las pausas). No mueve firmas. Medido con la voz real (Alex +10 %):
   narrador 3,5 pal/s, frase clave 2,3, Jotam con Roberto (Panamá).
   Pendiente: oírlo David y ajustar; elegir a mano la voz de cada personaje;
   susurro y entrada fuerte (los otros dos puntos de la comparación).
   Prueba: `pasos/prueba_voz_gratis.py` (`probar_personajes_y_claves`).
6c. Efecto de voz por vídeo — **HECHO (12-nov)** (lo pidió David para su voz
   grabada: «más gruesa, misteriosa, y que se pueda variar»). Cómo se usa:
   pestaña Guion → «🎚 Efecto de voz (solo este vídeo)» (dentro de «🎙 Tu voz»
   si usas tu grabación, o de «🗣 Voz» con la gratuita): estilo (Natural, Más
   grave, Gruesa y profunda, Misteriosa, Narrador de cine, Eco de cueva) + tono
   (+3 … −8 semitonos), «▶ Escuchar» (15 s de la voz del vídeo con el efecto)
   y «Usar este efecto»; luego «Regenerar Audio». Se aplica DESPUÉS de alinear
   y sin cambiar la duración (subtítulos y cortes igual). Con Cartesia no.
   Código: `pasos/efectos_voz.py` (estilos = cadenas de ffmpeg; tono con
   rubberband si el ffmpeg lo trae) + `p4_voz._con_efecto` + `app._guardar_efecto_voz`
   y `GET /api/proyectos/{pid}/voz/efecto/muestra` + `efectoVozLight` en
   `web/app.js`. Guardado en `voz_del_video.efecto`, fuera de firma.
   Pendiente: oírlo con la grabación de David y afinar los estilos.
   Prueba: `pasos/prueba_voz_gratis.py` (`probar_efectos`).
7. Fuerza de la cámara elegible — **HECHO (11-nov)** (lo eligió David entre
   cuatro opciones). Cómo se usa: al crear el vídeo o en «El encargo», debajo
   de «Cámara» (solo con 🎥 Cámara viva) sale «Fuerza del movimiento»:
   **🌙 Suave** (golpe de zoom ×0,55, temblor ×0,5, cámara al hombro ×0,6 y
   golpes 1,5× más espaciados: fe, reflexión), **⚖ Normal** (la de fábrica,
   golpe del 5,5 %) o **🔥 Fuerte** (golpe ×1,45, temblor ×1,5, mano ×1,4,
   golpes más seguidos: misterio, acción, TikTok). Gratis: solo pide volver a
   montar. Así se afina viendo un vídeo real sin tocar código.
   Código: `camara.FUERZAS` + `fuerza_de` + `preparar` (y `CAM.mano` en
   `CAMARA_JS`) + `app.py` (param `camara_fuerza` del render: solo se escribe
   suave/fuerte, o «normal» para volver) + `selectorCamara(e, …)` en
   `web/app.js`. Arreglado de paso: cambiar la «Cámara» en «El encargo» de un
   vídeo ya creado NO se guardaba (faltaba en `CAMPOS_ENCARGO`); ya sí.
   Prueba: `pasos/prueba_camara.py`.
   Pendiente: si con un vídeo real ninguna de las tres convence, ajustar los
   números de `camara.FUERZAS`.
8. Posición del subtítulo elegible — **HECHA (11-nov)** (la eligió David entre
   cuatro opciones). Cómo se usa: al crear el vídeo o en «El encargo» hay una
   fila «Subtítulo»: **⬇ Abajo** (lo de siempre: al pie en horizontal y a un
   tercio desde abajo en vertical) o **⏺ Centro** (en mitad de la pantalla,
   estilo TikTok/Shorts). Gratis: cambiarlo solo pide volver a dibujar los
   textos y montar; no toca imágenes ni voz.
   Código: `p7_callouts.posicion_subtitulo` + `banda_subtitulo(salida, p)`
   (`SUB_ALTURA_CENTRO` = 0,56 del alto) + `app.py` (al crear solo escribe
   `subtitulo_pos: "centro"`; «abajo» se guarda vacío para no mover firmas) +
   `selectorSubtitulo` y `CAMPOS_ENCARGO` en `web/app.js`.
   Prueba: `pasos/prueba_subtitulo_pos.py` (añadida a `pruebas.ps1`).
   Pendiente: verlo en un vídeo real; si el centro queda alto/bajo, ajustar
   `SUB_ALTURA_CENTRO`.
9. Más giros «falso → verdadero» en los subtítulos — **HECHO (11-nov)** (lo
   eligió David entre tres opciones). Cómo se usa: nada; basta con escribirlo
   así en el guion. Además de «no X, sino Y» y «no es X, es Y», ahora se tacha
   lo falso (rojo) y se resalta lo verdadero en: «todos creen / crees / dicen
   / cuentan que X… **en realidad** Y», «X. **Lo cierto es** que Y», «**El
   mito**: X. **La verdad**: Y», «Es un mito. En realidad…» (tacha «mito»).
   Puede cruzar UN punto («Crees que fue una manzana. En realidad fue un
   higo.»). Un «en realidad» suelto, sin creencia delante, no hace nada (es
   muletilla), ni «buscaba la verdad». Gratis: no mueve firmas; los vídeos ya
   montados cambian solo si se vuelven a montar los textos.
   Código: `gancho._CREENCIA`, `_marca_realidad`, `_creencia_y_realidad`
   (llamada desde `gancho.contrastes`). Prueba: `pasos/prueba_gancho.py`.
   Pendiente: elegir la palabra tachada/resaltada a mano desde la pantalla
   (hoy se puede forzando `~~palabra~~` y `*palabra*` en el texto).
10. **SIGUIENTE: el plan «NIVEL PROFESIONAL» (12-nov)** — ver la sección del
   mismo nombre más abajo; P1, P2 y P3 HECHOS (12-nov); siguiente, P4. (Siguen sobre la mesa, para
   después: grabar tu voz desde la propia página; afinar la tabla de voces.)

PLAN INMEDIATO (antiguo, del 6-nov; ya lo sustituye el orden nuevo de arriba): primero los puntos de «OPINIÓN DE DAVID»
(abajo), un chat por punto. A, B+B+, C, **G con D** y **E** HECHOS (6-nov).
F HECHO (11-nov, ver orden nuevo). Mientras: David saca la clave de YouTube
(gratis), prueba «💡 Ideas» y publica para tener datos («Mis vídeos»). Después,
etapa 6 de la hoja de ruta (un solo prompt para todas las imágenes).

Mensaje que David pega en cada chat nuevo (con el repo as-video-studio elegido):
«Lee NOTAS-DAVID.md y la skill ahorro-claude. Haz el siguiente punto del ORDEN NUEVO
(11-nov). Pruebas ligeras. Súbelo a main, dame el comando para Hostinger y actualiza mis
notas.»

## OPINIÓN DE DAVID TRAS SU PRIMER VÍDEO (6-nov-2026) — hacer ANTES de la etapa 6
Orden decidido, un chat por punto (cada uno completo y pulido):
A. **Modo ahorro de Claude — HECHO (6-nov-2026)**.
   Cómo se usa: Configuración (engranaje) → «Cuánto gasta Claude» → tres botones:
   **Ahorro** (todo Sonnet con esfuerzo medio como mucho, Haiku donde basta),
   **Equilibrado** (el de fábrica: lo recomendado por tarea en `POR_FASE`, casi todo
   Sonnet y Opus solo en dirección de planos, prompts, guía de estilo, repaso y
   corrector) y **Potente** (todo Opus muy alto, como antes). Debajo, «Qué modelo usa
   cada tarea en cada modo» (tabla). Vale desde la siguiente llamada, sin reiniciar.
   Cómo quedó: ajuste `modo_claude` en `ajustes.json` (`pasos/ajustes.py`) que lee
   `cli_claude.ejecutar` EN CADA LLAMADA (`aplicar_modo`): solo BAJA modelo/esfuerzo,
   nunca sube; la fase sale del `para=` de cada llamada (`PARA_A_FASE`). No toca
   params ni `por_defecto_de`, así que no mueve firmas ni deja nada obsoleto. En el
   registro del servidor sale `[cli] modo ahorro: … con sonnet/medium (pedia
   opus/xhigh)`. `GET /api/ajustes` trae `claude` (la tabla). Pantalla:
   `seccionModoClaude` en `web/app.js`. `pruebas.ps1` fija `ESTUDIO_MODO_CLAUDE=potente`
   para las suites viejas. Prueba: `pasos/prueba_modo_claude.py`.
   Pendiente: que los selectores de modelo de cada tarjeta digan lo que de verdad
   correrá con el modo puesto (hoy enseñan lo pedido y la estimación de tiempo
   sale algo larga).
B. **Subtítulos — HECHO (6-nov-2026, junto con B+)**. Ver B+ abajo.
C. **Fidelidad histórica y bíblica — HECHO (6-nov-2026)**.
   Cómo se usa: no hay que tocar nada. Si el vídeo es de tema bíblico (lo detecta
   solo por las palabras: Jesús, evangelio, apóstol, Moisés, Babilonia…), todo lo
   que se dibuja sale fiel a la época; un vídeo que no es bíblico no cambia nada.
   Qué sale: (1) el prompt de cada plano (el de «Copiar prompt», modo manual)
   lleva «ÉPOCA» (sitios y objetos reales), «PERSONAS DE LA ÉPOCA» (judíos del
   s. I: piel morena oliva, pelo oscuro rizado y corto, barba corta; túnica sin
   teñir hasta la rodilla, manto con flecos, sandalias…) y «NO DIBUJES» (rasgos
   europeos, ojos azules, ropa medieval, cúpulas, libros encuadernados…). Cinco
   épocas: siglo I (por defecto), patriarcas, Egipto y éxodo, reyes de Israel,
   exilio en Babilonia/Persia. (2) Si la frase compara lugares («hay dos Belén»),
   «EXPLICA LO QUE SE CUENTA» pide un MAPA con los lugares rotulados y la
   distancia real calculada (Belén de Judea–Belén de Galilea: ~115 km en línea
   recta), y entonces el prompt deja escribir esos nombres. Si da una medida o una
   fecha, pide enseñarla. Con muñecos, la parte de «personas» se quita sola.
   (3) A Claude: el guion bíblico cita LITERAL la Reina-Valera 1960 (libro,
   capítulo, versículo), separa Biblia de tradición («los tres reyes») y usa los
   nombres de la RV1960; el reparto y los sitios del catálogo visual se describen
   con el aspecto y la ropa de la época; la dirección y el redactor de planos
   reciben la época, las distancias reales entre los lugares del guion y la orden
   de que cada imagen EXPLIQUE su frase.
   Cómo quedó: `pasos/fidelidad.py` (detección, épocas, nomenclátor de ~40 lugares
   bíblicos con coordenadas y distancias, bloques de texto) + `subidas.prompt_para_copiar(contexto=)`
   (lo llama `p6_assets.prompts_para_subir` con el texto de todo el vídeo) +
   `catalogo_visual`, `direccion`, `redactor` (`fidelidad.insertar` antes del JSON)
   + `p3_guion._instruccion` (`pauta_guion`) + `marioneta.solo_fondo`. Solo cambia
   el TEXTO de los encargos: no es un param, NO mueve firmas ni deja nada obsoleto;
   el prompt que arma `p6_assets` para OpenAI no se tocó a propósito (la fidelidad
   le llega por las descripciones que escribe Claude). Prueba: `pasos/prueba_fidelidad.py`.
   Pendiente: más lugares en el nomenclátor; elegir la época a mano en el encargo;
   que el mapa lo dibuje el propio estudio (eso es el punto D).
D. **Más explicativo en imagen** — va DENTRO de G (ver G, primera parte: mapa con
   distancia, línea de tiempo, reloj por porciones y tarjeta de versículo HECHOS).
   Falta: flechas/círculos que señalan y comparaciones.
E. **Guion y voz con intención — HECHO (6-nov-2026)**.
   Cómo se usa: no hay que tocar nada para que funcione; los vídeos NUEVOS (o un
   guion que se vuelva a escribir) ya salen así. Y en la pantalla del guion, cada
   bloque tiene arriba a la derecha un desplegable de **tono**: 😐 Neutro,
   😊 Alegre (buena noticia, milagro), 🕊️ Sereno (oración, versículo),
   😢 Triste / lento (muerte, pérdida), 😨 Tenso / miedo (peligro, suspense),
   💪 Firme (advertencia). Si ya había audio, sale el botón «Regrabar este tramo
   con el tono nuevo» (gratis con la voz gratuita: solo regraba ese trozo).
   Qué sale: (1) **La voz gratis cambia de tono de verdad**: antes tiraba todo
   menos las pausas; ahora cada frase se graba con su tono (más lenta, grave y
   baja si es triste; más viva y aguda si es alegre; baja y algo rápida si es
   tensa; más fuerte si es firme), y también respeta la velocidad y el volumen
   que pone Claude. (2) **Pausas con intención**: tras una pregunta que sigue
   («¿Por qué lo hizo? Porque…») y tras unos puntos suspensivos, un respiro
   corto solo; las pausas grandes (tras el gancho, antes de la revelación) las
   sigue poniendo el guion. (3) **Claude decide el tono** al escribir el guion
   (de 3 a 6 cambios en un vídeo largo, 2-3 en uno corto, siguiendo la
   historia). (4) **Ritmo para retener**: la 1.ª frase es el gancho, preguntas
   que se abren y se cierran después, un giro cada 20-30 s (cada 8-10 s en
   TikTok), frases cortas (máx. 28 palabras; 16 en un vídeo corto: era el
   pendiente de la etapa 4), hablar a «tú», final que remata. (5) **Sin
   muletillas**: se le prohíben a Claude y, si se cuela alguna, se quita sola
   («o sea,», «bueno,» al empezar, «básicamente», «literalmente», «la verdad es
   que», «digamos»; «o sea que» → «así que»). «Oye, Israel» o «Mira» NO se tocan
   (son de la Biblia). Lo escrito a mano se respeta. Los avisos del guion dicen
   qué muletillas se quitaron y qué frases son demasiado largas.
   Cómo quedó: `pasos/intencion.py` (TONOS, PROSODIA, respiros, muletillas,
   ritmo, pautas) + `voz_gratis._trozos` (parte en cada cambio de tono en
   frontera de frase; edge-tts recibe `rate`, `pitch` y `volume` por trozo) +
   `p4_voz.unir_bloques` (con voz gratis cada bloque empieza neutro, para que el
   tono de uno no se arrastre al siguiente) + `p3_guion` (`pauta_ritmo` al
   prompt, `pauta_tono` con voz gratis vía `marcas_tts.instrucciones(pauta_tono=)`,
   muletillas en `_aplicar_marcas`, aviso de ritmo en `_avisos`) + pantalla
   `selectorTonoLight` en `web/app.js` (el tono es la etiqueta `<emotion>` con
   la que EMPIEZA el bloque; editar el texto a mano conserva el tono). Las
   emociones son las mismas seis de Cartesia, así que el guion vale para las
   dos voces. Solo texto del encargo y del bloque: NO es un param nuevo, no
   mueve firmas. Prueba: `pasos/prueba_voz_gratis.py` (sección «punto E»).
   Pendiente: probar a oído los valores de `intencion.PROSODIA` con la voz que
   use David y ajustarlos si alguno suena exagerado; un tono a mitad de bloque
   desde la pantalla (hoy solo el del bloque entero).
E+. **Arreglos tras probar E (8-nov-2026)** — lo que vio David en su vídeo:
   - **Citas bíblicas en pantalla**: «Salmo sesenta y ocho» salía como un «68»
     que corría contando y «Lucas, capítulo veinticuatro, versículo seis» salía
     roto. Ahora se reconoce la cita dicha de cualquier forma (letras o cifras,
     con o sin «capítulo/versículo», hasta el Salmo 119) y se escribe como una
     cita: «Lucas 24:6», «Salmo 22:7-8», «Salmo 68», «1 Corintios 13:4»; no se
     parte en dos renglones y NO cuenta. También en el cartel del gancho. No
     confunde personas («Pedro tres veces lo negó» no es una cita). El motion
     graphics saca la tarjeta de versículo con cualquier número (antes solo
     hasta 24). `pasos/citas.py` + `subtitulos` (`_citas_de`, `_intocables_de`)
     + `gancho` (sin contador tras un libro) + `motion.cita_de` +
     `p7_callouts` (cartel). Prueba: `pasos/prueba_citas.py`.
   - **Citar bien en el guion**: cada cita en 3 pasos — el momento (quién
     habla y qué pasa), la cita literal dicha UNA vez, y qué significa; nunca
     dos citas seguidas sin explicar, nada de «Salmo veintidós, siete y ocho»
     suelto; como mucho 2-3 citas en un corto (`fidelidad.pauta_guion`). Y el
     guion se cuenta como HISTORIA (personajes, lugar, qué quieren, giro,
     desenlace; explicar como a un chico de 15 años) (`intencion.pauta_ritmo`).
   - **La voz ya no suena plana**: (1) si un bloque no trae tono, el estudio lo
     elige SOLO por lo que cuenta (muerte/lloró → triste; resucitó/milagro →
     alegre; soldados/miedo → tenso; oración/paz → sereno; «ay de» → firme)
     — `intencion.tono_automatico`; (2) dentro del tono cada frase tiene su
     matiz: la pregunta sube, la exclamación empuja, el remate corto («Y
     lloró.») se dice despacio y la cita entre comillas con peso
     (`intencion.matiz`); (3) los tonos se marcan más. En la pantalla del guion
     el desplegable de tono tiene «✨ Automático» (por defecto) y «😐 Neutro»
     para pedir neutro a propósito. Afecta a la voz al volver a GRABARLA
     (gratis con la voz gratuita); un guion ya escrito no cambia, pero su voz
     regrabada sí suena con tonos automáticos.
   - **Más imágenes en los vídeos cortos**: no había un tope de 24: las imágenes
     salen del RITMO del estilo («Medio» = una cada ~2,8 s → ~24 en 70 s). Ahora
     un vídeo NUEVO corto (TikTok o ≤ 2 min) con imágenes gratis (manual) corta
     como mínimo a ritmo «Rápido» (~2 s, ~35 imágenes en 70 s): cada frase con
     su imagen. `app._mas_planos_si_corto` (solo al crear y solo en manual: con
     OpenAI cada imagen se paga). Para aún más: en el estilo, ⏱️ Ritmo → «Muy
     rápido». En un vídeo ya hecho no se cambia solo (rehace todas las imágenes).
   Pendiente: oír los tonos con la voz de David y ajustar `intencion.PROSODIA`
   y `intencion.PISTAS` si alguno se pasa o falla.
F. **Movimiento de imágenes y transiciones — HECHO (11-nov-2026)**, ver el punto 4 del ORDEN NUEVO: mejor movimiento de cámara, cortes al
   ritmo de la voz, transiciones con intención y cosas que otros no hacen.
G. **FIGURAS PLANAS PROPIAS (decidido 6-nov)**: personajes de colores lisos como el
   vídeo «¿Se les debe rezar a los santos?» (cabeza redonda, cara simple, túnica en
   campana), pero con DISEÑO PROPIO, dibujados por código (SVG, evolución de
   `marioneta.py`) para que se muevan pieza a pieza: boca al hablar, parpadeo,
   brazos, caminar, arrodillarse, girar. José, María, Pedro… salen del reparto.
   Fondos de Gemini en el MISMO estilo plano («ilustración vectorial plana, sin
   personas») o escenarios SVG. Segundo estilo opcional: PALITOS (stick figure) para
   vídeos de reflexión con metáforas («PECADO» como bola con cadena).
   LO QUE MANDA ES LLAMAR LA ATENCIÓN, no la marca: NADA de lámpara ni dorado
   obligatorios. Colores vivos y con mucho contraste, caras MUY expresivas (ojos
   grandes, sorpresa, miedo, alegría exagerados), algo que cambia cada 2-3 s
   (zoom de golpe, objeto que entra, texto que salta), efectos de sonido al ritmo,
   metáforas visuales sorprendentes.
   ACLARADO: lo que quiere es MOTION GRAPHICS de nivel profesional, no imágenes:
   TODO son elementos gráficos vectoriales (fondo, personajes, objetos, textos) que
   ENTRAN y SALEN animados (pop con rebote, deslizar, crecer, escalonados), con
   curvas de animación profesionales (anticipación, overshoot, squash & stretch),
   cámara que se mueve por la escena y todo sincronizado con las palabras.
   Arquitectura pensada: el guion (Claude) devuelve por plano un STORYBOARD en JSON
   (qué elementos, dónde, cuándo entran/salen, qué hace cada personaje) y el render
   lo anima con SVG; biblioteca de elementos reutilizables (altar, velas, cruz,
   casas, palmeras, pergamino, mapa, cadena…) que crece con cada vídeo. Gemini
   sobra (como mucho, un fondo). Objetivo de David: «lo mejor del mercado».
   (El 3D low-poly del vídeo viral queda como idea lejana.)
   **PRIMERA PARTE — HECHA (6-nov-2026)**: el motor de motion graphics.
   Cómo se usa: al crear el vídeo (o en «El encargo») → «Animación» →
   «✏️ Motion graphics (papel)» o «🌙 Motion graphics (noche)». Luego montar el
   vídeo (gratis: no se pide ninguna imagen nueva). Sale: el vídeo es UN SOLO
   DIBUJO por el que viaja la cámara, sin cortes (al cambiar de plano se aleja un
   poco, un camino de puntos une un sitio con el siguiente y lo anterior se queda
   donde estaba, para no perderse). Cada plano explica su frase con una pieza
   que entra con rebote (se pasa y vuelve, se estira al moverse y se aplasta al
   llegar) en el momento en que la voz dice su palabra:
   - **Versículo**: si la frase cita entre comillas y/o con referencia («Juan
     14:23»), tarjeta con «JESÚS DIJO:», el texto que se va ENTINTANDO palabra a
     palabra con la voz (las palabras clave en color), la pastilla «JUAN 14:23 ·
     RVR1960» y una Biblia que se abre con destellos.
   - **Línea de tiempo**: si dice años («en el año 70 d. C.», «586 a. C.», «hace
     2000 años»): eje que se dibuja, tarjetas que caen, puntero que viaja y
     «hace N años» contando. Con un solo año pone «HOY».
   - **Mapa con distancia**: si nombra lugares (Belén, Nazaret, Roma…): costa,
     mar de Galilea, Jordán y mar Muerto esquemáticos, chinchetas que caen, la
     ruta que se dibuja y los km reales contando (Belén–Nazaret: 110 km). Un solo
     lugar se sitúa respecto de Jerusalén. No repite el mismo mapa.
   - **Reloj por porciones**: «hora tercera/sexta/novena» (= 9, 12, 15 h, como
     contaban los judíos), «de la hora sexta a la novena» (3 horas), «5 horas al
     día» (esfera de 24 h: «5 h = 21 % de tu día»).
   - Si no hay nada de eso: la imagen del plano como **lámina** enmarcada que
     sube rebotando, con iconos que saltan al decir su palabra (cruz, corazón,
     Biblia, moneda, celular, corona, paloma, casa, vela, estrella, pan, cadena…).
   **Ampliado el mismo día (tras ver David las referencias)**:
   - **Texto que se revela desde una MÁSCARA**: cada renglón del versículo es una
     ventana; la palabra SUBE desde detrás de su renglón cuando la voz la dice (su
     sombra tenue se ve antes, para leer la forma de la frase). La palabra clave
     se RODEA a mano después de decirla. Los títulos se descubren con un barrido.
   - **Movimientos encadenados**: cuando una pieza aterriza, la cámara da un
     golpecito y las piezas vecinas se mecen (reaccionan); en las listas la que
     entra empuja y apaga un poco a las de antes; los pictogramas del contador
     salen a la vez que cuenta el número.
   - **La cámara sigue lo importante**: dentro de cada plano va de foco en foco
     (se acerca a la chincheta que se nombra, al año que se dice, a la porción del
     reloj, a la tarjeta tachada y luego a la verdadera…) y vuelve a su sitio
     antes de acabar el plano, para que el viaje al siguiente no corte.
   - **Un objeto se transforma para presentar la escena siguiente**: al final de
     cada plano sale por el lado un objeto que anuncia lo que viene (chincheta →
     mapa, Biblia → versículo, reloj de arena → línea de tiempo, balanza →
     comparación…); se agacha, salta, vuela con la cámara y al llegar ESTALLA en
     un anillo del que nace la pieza nueva.
   - **Más recursos**: 3 piezas nuevas — **comparación** («no fueron tres reyes,
     sino unos magos»: la falsa cae, se tacha con ✗, la verdadera sube con ✓ y una
     flecha), **contador** («cinco mil hombres»: el número cuenta y salen
     muñequitos o puntos «cada ● = 125»; también panes, peces, ovejas, monedas,
     días…), **lista** («tres cosas: orar, leer la Biblia y servir»: cada una entra
     numerada cuando se dice) — y 46 iconos (antes 14): ojo, mano, llave, puerta,
     monte, sol, luna, nube, agua, fuego, árbol, pez, barca, oveja, espada, escudo,
     trompeta, tablas de la ley, templo, tumba, lupa, balanza, ancla, copa,
     persona, chincheta, reloj de arena, ?, ✓, ✗, flecha… que saltan junto a la
     lámina al decir su palabra.
   Subtítulos, gancho y plantilla TikTok siguen encima igual. Con motion no hay
   muñecos ni efectos de ambiente (eso va en la segunda parte).
   Cómo quedó: `pasos/motion.py` (detección, piezas, cámara y el JS que anima) +
   `p8_render` (capa `#mg`; sin transiciones entre planos) + `selectorMotion` en
   `web/app.js` + `app.py` al crear. Param del render `motion` (`"papel"`,
   `"noche"`, o `{"tema": "papel", "laminas": false}` para no usar imágenes); no
   va en los defectos (no mueve firmas). En plan.json una escena puede llevar
   `"motion": [piezas]` (storyboard a mano: texto, icono, versículo, mapa,
   línea, reloj, lámina, con `en`, `entra` y `luego`) o `"motion": false`.
   Prueba: `pasos/prueba_motion.py` (`--foto` pinta y comprueba que no hay corte).
   **SEGUNDA PARTE — HECHA (6-nov-2026)**: G y D completos.
   Cómo se usa: al crear el vídeo (o en «El encargo») → «Animación» → «✏️ papel»
   o «🌙 noche». Debajo salen tres filas nuevas:
   - **Quién elige las piezas**: «🧠 Claude, con metáforas» (por defecto) o
     «⚙️ Automático (no gasta Claude)». Con Claude, al montar el vídeo Claude
     lee el guion ENTERO y decide cada plano: metáforas (el pecado = bola con
     cadena que cae; la duda = «?» que crece; la fe = semilla; la salvación =
     candado que se abre), los muñecos con su gesto y su cara, flechas, círculos,
     barras… Donde lo automático ya explica (versículo, mapa, años, horas…) lo
     deja y como mucho añade un acento. UNA llamada a Sonnet por vídeo y se
     guarda: volver a montar NO gasta; si cambias la frase de un plano, solo
     pregunta por ese plano. Si Claude falla, sale lo automático (no se para).
   - **Muñecos planos dentro del mundo** (Sí por defecto): los personajes del
     plano (del reparto: color de túnica, velo si es mujer, barba, canas, alas
     si es ángel) como figuras planas de cabeza grande y ojos grandes, con caras
     MUY expresivas (alegría con mejillas, sorpresa con rayitas, miedo con gota
     de sudor y temblor, tristeza con lágrima, enfado). Gestos: presentar,
     hablar, señalar, levantar los brazos, caminar, escuchar (asiente),
     arrodillarse (orar), saltar (alegría), asustarse, girar, pensar. **La boca
     sigue la voz**: quien habla («Pedro dijo: …») abre la boca en cada palabra,
     una vez por sílaba. Parpadean, respiran y entran saltando; el nombre sale
     en una etiqueta si la frase lo dice. Con la imagen del plano salen
     pequeños delante de la lámina; sin imagen, grandes en el centro.
   - **Sonidos**: «whoosh» en cada viaje de cámara y «pop» cada vez que una pieza
     aterriza (sintéticos: suenan aunque no haya clave de FreeSound).
   **Piezas automáticas nuevas** (gratis, sin Claude): **barras** («el 70 % de
   la iglesia y el 30 % del mundo», «cinco panes y dos peces»: cada barra crece
   y cuenta cuando se dice su cifra), **antes/ahora** («antes era perseguidor,
   ahora es apóstol»: una cortina barre lo gris de antes y descubre lo nuevo con
   destellos), **árbol genealógico** («Isaac, hijo de Abraham, fue padre de
   Jacob»: cada generación cae al decir su nombre y la rama se dibuja). Y para
   Claude/a mano: **flecha** que se dibuja y señala (con rótulo) y **círculo a
   mano** que rodea algo. 10 iconos más para metáforas: bola con cadena,
   corazón roto, bombilla, rayo, semilla, candado, regalo, mundo, escalera, muro.
   Cómo quedó: `pasos/motion_mas.py` (muñecos, piezas nuevas en JS, iconos y
   sonidos) + `pasos/motion_storyboard.py` (Claude, caché en
   `<proyecto>/motion/storyboard.json`) + `motion.py` (detección, `_normalizar`
   de todas las piezas, `_automatico`, `tipos_auto`) + `p8_render` (fichas del
   reparto, storyboard, `sonido.anadir_muestras`) + `selectorMotion` en
   `web/app.js` + `app.py` al crear. Param del render `motion`:
   `{"tema": "papel", "storyboard": "claude", "munecos": false, "sonidos": false}`
   (lo que falta = sí; `"papel"` a secas, de antes, sigue valiendo = automático
   con muñecos y sonidos). No mueve firmas; cambiarlo pide volver a montar.
   Para no llamar a Claude nunca: variable `ESTUDIO_STORYBOARD=no`.
   Prueba: `pasos/prueba_motion.py` (`--foto` pinta los planos; con
   `ESTUDIO_CHROMIUM=<ruta de chrome>` si Playwright no encuentra el navegador).
   Pendiente: ver y corregir el storyboard de Claude desde la pantalla; estilo
   PALITOS para reflexión; que el muñeco camine de un sitio a otro del mundo.
B+. **Textos estilo TikTok — HECHO (6-nov-2026, con B)**.
   Cómo se usa: al crear el vídeo (o en «El encargo») → «Gancho» → «⚡ Gancho +
   textos TikTok». Debajo salen dos filas nuevas: «Letra de los textos»
   (Montserrat Black —la de TikTok, por defecto—, Bebas Neue —todo mayúsculas—,
   Lilita One —redonda, para muñecos—, Playfair —con serifa, historia— o «La del
   estilo») y «Palabra clave» (Subrayado —por defecto—, Recuadro o Solo color).
   Cambiarlo es gratis: volver a montar.
   Qué sale: subtítulos palabra a palabra con contorno negro (sin caja), cada
   palabra da un saltito al decirse; la clave en rojo (o el acento del estilo si
   es vivo) con raya/recuadro que se dibuja; las cifras CUENTAN desde 0 (un año,
   desde 50 antes: 1606→1656) y llegan a su valor justo al acabar de decirlas
   (solo de 10 para arriba); en «no fue X, sino Y» y «no es X, es Y» la X se
   TACHA en rojo y la Y es la clave. En el texto corregido a mano de un
   subtítulo: `~~palabra~~` la tacha, `*palabra*` la hace clave.
   Arreglos de B: (1) mientras sale el cartel del gancho NO hay subtítulo
   debajo, y el cartel dura lo que tarda la voz en decirlo (1,8-5 s); lo que se
   dice detrás no se pierde. (2) Un solo criterio: todo en minúsculas normales
   («DIOS» → «Dios»), todo del mismo tamaño; solo cambia el color. (3) Sincronía:
   una cifra dicha con varias palabras («dos mil» → «2000») dura lo que esas
   palabras, ya no se reparte a ojo. (4) El cartel ya no corta en «y…?»: corta
   en una coma o detrás de una palabra con contenido (hasta 12 palabras entra
   entera).
   Cómo quedó: `pasos/letras.py` (fuentes en `motores/fuentes/`, licencia OFL,
   dentro del repo: mide Python y dibuja el navegador con el MISMO fichero; la
   página del render las carga con `@font-face` y espera a que estén) +
   `pasos/gancho.py` (cartel_de, preparar, contrastes, contador, bloque_palabras
   reescrito colocando cada palabra a mano, tras_el_cartel) +
   `p7_callouts._subtitulos_gancho` + `subtitulos.de_escena` (tiempos de cifras)
   + `p8_render` (`__LETRASCSS__`, `LETRAS_OK`). Params de callouts `letra` y
   `resalte`; no van en los defectos (no mueven firmas). Pantalla:
   `selectorLetras` en `web/app.js` (+ ruta `/fuentes/<fichero>` en `app.py`
   para que los botones se vean con su letra). Prueba: `pasos/prueba_gancho.py`.
   Pendiente: ~~más formas de «lo falso → lo verdadero»~~ (HECHO 11-nov, punto 9
   del orden nuevo); elegir la palabra clave a mano desde la pantalla; posición
   del subtítulo elegible (centro / abajo).
Luego seguir el ORDEN NUEVO (11-nov): F, la voz grabada, los puntos 6, 7, 8 y 9 HECHOS; siguiente, el plan «NIVEL PROFESIONAL» (P1, P2 y P3 HECHOS; ahora P4).

## NIVEL PROFESIONAL (decidido 12-nov-2026) — manda sobre el punto 10 del ORDEN NUEVO
David quiere que sus vídeos queden AL MISMO NIVEL que los de referencia, no «parecidos
pero más simples». Referencias: Drive → carpeta «IMAGENES DE IDEAS DE TIKTOK»
(7 vídeos + 11 capturas; analizados el 12-nov, ver abajo). «Igual» = mismo nivel de
acabado y los mismos RECURSOS, con diseño PROPIO: no copiar marca, personajes ni
look exacto de esos canales (TikTok no paga contenido no original y es copia). Y nada
de trozos de películas (el vídeo de gnesis_2815 usa «El príncipe de Egipto»: NO).

**Lo que hacen las referencias (la fórmula):**
- Gancho en el 1.er segundo: pregunta o algo que contradice lo sabido («La túnica de
  José no era de colores»), o el FINAL primero y luego «hay que retroceder» (Abimelec).
- 55-110 s casi todos (Creator Rewards > 1 min). Frases de 3-8 palabras.
- UNA historia + UN dato que nadie sabe (palabra hebrea, «400 años», papiro 616).
- Algo que se repite (la piedra con 69 rayas) y frase que cierra el círculo.
- Cierre con Jesús en espejo (70 monedas ↔ 30; mató a sus hermanos ↔ murió por ellos).
- Final que pide algo: «envíaselo a ese amigo…», «¿tú cómo te la imaginabas?»,
  «en el próximo vídeo…» (serie). Lo PROPIO de David: «el reto de esta semana».
- Cifras enormes que brillan; subtítulos palabra a palabra con la clave resaltada.

**Los estilos (canal → qué hay que tener):**
- Sin filtro pero con-texto (Abimelec): vectorial plano, noche/rojo ↔ papel beige
  en el MISMO vídeo, siluetas con ojos rojos, SELLOS rojos torcidos («NO», «SIN
  REY»), pastilla fija arriba con la cita («JUECES 9:5»), «◀◀ rebobinando −25 años».
- Un Cristiano Inquieto (Jonás): ilustración plana con luz cuidada (atardecer, mar
  con olas por capas), mapa con ruta, «Día 3» / «40 días» en placa.
- unidos.en.oracion (el rico y Lázaro): siluetas a contraluz con borde que brilla,
  fuego de calidad, haces de luz, subtítulo arriba.
- Bibliando contigo (Apocalipsis): dibujo animado de colores dentro de una TARJETA,
  etiqueta «DATO», cita arriba a la derecha, «VS» con bocadillos «!» «?!».
- Tesoro Bíblico (capturas): fila de muñequitos de colores, «70 AÑOS» en círculo,
  ruta punteada con ✗, palito con bola y cadena «PECADO».
- Resumario (túnica de José): tipografía editorial grande con serifa y cursiva de
  acento, CUADROS clásicos de dominio público con su pie («Velázquez, 1630»),
  palabra hebrea/griega en placa.
- El origen de las cosas (los silencios): UN escenario fijo (Biblia abierta en 3D,
  muñecos de plastilina), marcador «+400 AÑOS» de rodillos, pantalla PARTIDA
  «ÉXODO | MATEO» con una raya roja.

**Código abierto a usar (todo gratis, se guarda DENTRO del repo, sin CDN: el render
del VPS no debe depender de internet; anotar licencia de cada cosa en un LICENCIAS):**
- anime.js (MIT): curvas y líneas de tiempo de animación en la página del render.
  (GSAP NO: su licencia gratuita no es libre y prohíbe ciertos usos.)
- lottie-web (MIT) + animaciones de LottieFiles con licencia libre: piezas animadas
  hechas por diseñadores (fuego, humo, destellos, explosión, llamas, agua).
- Three.js (MIT): escenarios 3D en el navegador del render (Biblia abierta, mesa,
  look plastilina), sin GPU (WebGL por software; medir el tiempo por fotograma).
- Rough.js (MIT): trazo «a mano» (círculos, tachados, flechas).
- Rhubarb Lip Sync (MIT, CPU): boca de los muñecos sincronizada con la voz real.
- Iconos: Tabler/Lucide (MIT/ISC) y game-icons.net (CC BY 3.0: poner crédito).
- Cuadros: Met Museum Open Access y Wikimedia Commons (dominio público / CC0), con
  autor y año en el pie, como Resumario.
- Sonidos: Kenney (CC0) y Freesound filtrado a CC0. Fuentes: Google Fonts (OFL).

**Etapas (una por chat, en orden; cada una con prueba y vista en un vídeo real):**
- P1. Sellos rojos, pastilla fija de la cita, etiqueta «DATO», placa de cifra
  («Día 3», «+400 AÑOS» de rodillos) y «◀◀ rebobinando». Con anime.js.
  **HECHO (12-nov-2026)**: `pasos/rotulos.py`, capa nueva del render encima de la
  imagen (no hace zoom con ella, debajo del subtítulo). Salen SOLOS leyendo la
  narración de cada plano: sello («sin rey» → SIN REY, «no era/fue» → NO, nunca,
  jamás, falso, mentira, prohibido; tiembla el cuadro al caer), pastilla con la
  cita (Jueces 9:5 → «✝ JUECES 9:5» arriba; se queda en los planos siguientes
  hasta que se nombra otra), «DATO» (sabías que, dato, pocos saben, en
  hebreo/griego + la palabra), placa de cifra con rodillos («día tres» → DÍA 3,
  «más de cuatrocientos años» → +400 AÑOS; cosas contadas: años, días, monedas,
  hermanos…) y «◀◀ REBOBINANDO −25 AÑOS» (retroceder, rebobinar, volvamos, «N
  años antes») con rayas de cinta. Las cartelas no llevan. anime.js 3.2.2 va
  dentro del repo (`motores/js/`), licencias en `LICENCIAS.md`.
  Cómo se apaga o se fuerza: param `rotulos: false` del render (todo el vídeo);
  en `plan.json`, escena `"rotulos": false` (ese plano) o a mano
  `[{"tipo":"sello","texto":"SIN REY","en":"rey"}]` (tipos: sello, pastilla,
  dato con `palabra`, cifra con `valor`/`antes`/`despues`, rebobinar con
  `menos`). No toca firmas: basta «Regenerar Vídeo» (no redibuja imágenes).
  Prueba: `pasos/prueba_rotulos.py` (`--ver CARPETA` escribe una página de
  render para mirarla). Falta: verlo en un vídeo real con la referencia al
  lado y apuntar aquí lo que se note distinto; aún no hay botón en pantalla.
- P2. Pantalla partida para paralelos (A | B con raya) y mezclar papel/noche por
  plano (el tema puede cambiar en una escena).
  **HECHO (12-nov-2026)**: `pasos/partida.py`, capa del render encima de la imagen
  y debajo de rótulos y subtítulo. **Pantalla partida**: A = imagen del plano
  anterior (la cartela no cuenta), B = la de este, raya roja que brilla y una
  etiqueta en cada mitad (los libros: «ÉXODO | MATEO»). En vertical, una encima
  de otra; en horizontal, lado a lado. Entra deslizándose en la palabra que
  compara. Sale SOLA si la frase compara («igual que», «así como», «en cambio»,
  «a diferencia de», «mientras que», «frente a», «espejo», «paralelo») o nombra
  dos libros. **Tono por plano**: «noche» (oscuro, azul, viñeta roja) si habla de
  noche, tinieblas, sangre, matar, traición, muerte…; «papel» (sepia, grano de
  papel, viñeta cálida) si rebobina («años antes», «retroceder») o habla de lo
  escrito (pergamino, papiro, profecía, «está escrito»). El resto, normal.
  Cómo se apaga o se fuerza: params del render `partida: false`, `tono:
  "normal"` (sin tono automático) o `tono: "papel"|"noche"` (todo el vídeo); en
  `plan.json`, escena `"partida": false`, `"partida": {"a": "S004", "eti_a":
  "ÉXODO", "eti_b": "MATEO", "en": "igual"}` y `"tono": "papel"|"noche"|"normal"`
  (manda sobre todo). No va con motion graphics ni en planos con clip de vídeo
  (el tono sí). No toca firmas: basta «Regenerar Vídeo». Prueba:
  `pasos/prueba_partida.py` (`--ver CARPETA` escribe páginas vertical/horizontal).
  Falta: verlo en un vídeo real con la referencia al lado; aún no hay botón en
  pantalla (igual que P1).
- P3. Calidad de dibujo: biblioteca de escenarios y objetos vectoriales con luz,
  sombras y capas (mar, desierto, ciudad amurallada, torre, templo, barca, trono…)
  y muñecos mejores; fuego/humo/luz con Lottie.
  **HECHO (12-nov-2026)**: `pasos/escenarios.py`, pieza nueva `escenario` del motion
  graphics (va DETRÁS de todo). Ocho sitios dibujados por código: **mar** (olas por
  capas, reflejo del sol, barca que se mece, orilla), **desierto** (dunas con cara
  al sol y cara en sombra, palmeras, tienda), **ciudad** amurallada (almenas, torres,
  puerta en arco, casas detrás), **torre** (zigurat de Babel), **templo** (fachada
  con columnas y remate de oro, escalinata, altar), **trono** (sala del palacio:
  columnas con volumen, cortinas, alfombra, haz de luz de la ventana), **monte**
  (camino en zigzag, luz y nube en la cumbre) y **campo** (colinas, olivo, pozo,
  ovejas). Tres horas: día, atardecer y noche (cielo, sol/luna con halo, estrellas,
  ventanas encendidas, color de toda la escena). Cada objeto con su sombra hacia el
  lado contrario al sol y borde de luz. Se mueve: nubes, olas, barca, palmeras,
  estrellas, halos. **Fuego, humo y luz** con Lottie (lottie-web MIT dentro del repo,
  `motores/js/lottie_light.min.js`; las animaciones las genera el módulo, sin
  licencias de nadie). **Muñecos**: túnica y cara con volumen (sombra y brillo).
  Cómo sale SOLO: plano con motion, SIN imagen y sin otra cosa que explicar (mapa,
  versículo...), si la narración nombra el sitio («barca», «mar» → mar; «muralla»
  → ciudad; «rey», «trono» → trono; «altar», «templo» → templo; «noche» → de noche;
  «fuego», «zarza» → fuego; «humo», «incienso» → humo; «gloria», «ángel» → luz).
  Con imagen del plano NO sale (manda la imagen pagada), salvo a mano.
  A mano: en `plan.json`, escena `"escenario": "mar"` o `{"nombre": "templo",
  "hora": "noche", "efectos": ["fuego", "humo"]}`, o `"escenario": false`; en un
  storyboard `{"tipo": "escenario", ...}` (Claude ya lo conoce). Apagar en todo el
  vídeo: param `motion: {"escenarios": false}`. No toca firmas: basta «Regenerar
  Vídeo». Prueba: `pasos/prueba_escenarios.py` (`--ver CARPETA` pinta los ocho).
  Falta: verlo en un vídeo real con la referencia al lado; más objetos (camello,
  cruz, mesa) y que el muñeco camine por el escenario; aún sin botón en pantalla.
- P4. Siluetas a contraluz con borde luminoso (estilo Lázaro) sobre imágenes de
  Gemini: rembg ya recorta; añadir el brillo y los haces.
- P5. Modo «editorial» (estilo Resumario): texto grande centrado a lo largo del
  vídeo + cuadros de dominio público buscados solos con su pie.
- P6. Escenario 3D fijo con Three.js (Biblia abierta, plastilina) y cámara.
- P7. Boca con Rhubarb y la voz grabada de David.
- P8. Guion con la fórmula de arriba (plantilla en el encargo: gancho, dato,
  espejo con Jesús, final que pide algo, «reto de la semana», serie numerada).
Al acabar cada etapa: hacer UN vídeo de prueba con su referencia al lado y apuntar
aquí lo que aún se nota distinto.

## Prompts de imagen: dos fallos de fondo arreglados (11-nov-2026)
Visto en el vídeo del rey David (borrado después; no se arregló ese vídeo).
- **Desfase plano ↔ audio**: los planos se numeran por POSICIÓN (S001, S002…) y
  se renumeran si el corte cambia (sale un plano de 0,3 s, otro se funde). La
  acción escrita («QUÉ SE VE», `direccion`/`redactado`) se guardaba por número y
  se quedaba en el número viejo: desde S006 iba 2-6 planos adelantada. Ahora se
  guarda con la frase para la que se escribió (`direccion_de`, `redactado_de`) y
  `p6_assets._lo_dirigido` la pone en el plano que dice ESA frase; un plano sin
  frase que case queda «sin dirigir» y la receta lo dirige antes de generar. Lo
  guardado antes del arreglo se lee como siempre (no mueve firmas).
- **Época por plano y por personaje**: `fidelidad.epoca_del_plano` decide por
  quién sale (su nombre: David → Edad del Hierro, Jesús → siglo I), lo que se ve
  y la frase; la del vídeo solo si nada de eso dice nada. Una ficha de David con
  «first-century» se corrige al copiar (`ficha_en_su_epoca`), y al catálogo se le
  avisa de que el vídeo mezcla épocas.
- De paso: cara solemne (no «sonrisa relajada») en momentos graves
  (`p6_assets._momento_grave`); en la crucifixión, TRES cruces y Jesús con la
  cabeza erguida hasta su último grito (`fidelidad.CRUCIFIXION`).
- **Botón «✨ Arreglar el guion»** (pestaña Guion, bajo los avisos): convierte
  los avisos de largo (por encima/debajo de la horquilla) y de pausas de más en
  UNA corrección de todos los bloques (`/api/proyectos/{pid}/guion/arreglar`,
  mismo camino que «Regenerar bloque»); las pausas que sigan sobrando se quitan
  a mano. Con la voz gratuita y sin voz propia subida, al acabar regraba el
  audio solo; con Cartesia o con tu grabación, solo avisa (no gasta ni pisa).
  Los avisos de la pantalla ya son los de AHORA (`/guion/avisos`), no los del
  día en que se escribió. Prueba: `pasos/prueba_arreglar_guion.py`.
  Prueba: `pasos/prueba_fidelidad.py`. Pendiente: por qué el corte dejó un plano
  de 0,3 s («Y»); ya no desfasa nada, pero un plano así sobra.

## Ángeles, aureolas y Jesús (11-nov-2026)
- **Reglas generales de todo vídeo bíblico** (`fidelidad.reglas_sagradas`, entran
  en `pauta_imagen` y `pauta_claude`): NINGUNA aureola en nadie (siempre); si salen
  ángeles, hombres con ropa blanca resplandeciente SIN alas ni aureola (alas solo
  para serafines/querubines si el texto los nombra); si sale Jesús, de espaldas, a
  contraluz o de lejos, sin rostro detallado. Solo texto de encargo: no mueve firmas.
- **Muñecos** (`marioneta.py`, `motion_mas.py`): el ángel ya no lleva alas ni
  aureola; túnica blanca y un brillo suave detrás. Hay que volver a montar el vídeo
  para verlo. Pruebas: `prueba_fidelidad.py`, `prueba_marioneta.py`, `prueba_motion.py`.
  Pendiente: el muñeco de Jesús sigue con cara (es un muñeco, no un retrato).

## Prompt para Meta AI (11-nov-2026)
- Configuración → «Para qué generador es el prompt» (sale solo en modo manual):
  **Gemini o ChatGPT** (el largo de siempre) o **Meta AI**: una línea que empieza
  por «Imagina:» con qué se ve, personajes (aspecto resumido), estilo y las reglas
  bíblicas esenciales (`fidelidad.reglas_cortas`). El botón de cada plano dice
  «Copiar prompt (Meta AI)». Con muñecos, solo el fondo.
- Cómo quedó: ajuste `prompt_para` («chat» | «meta») en `ajustes.json`, leído al
  copiar (`app._ficha_subidas` → `p6_assets.prompts_para_subir(para=)` →
  `subidas.prompt_meta`). No es un param: NO mueve firmas. El «prompt único» sigue
  siendo para Gemini. Prueba: `probar_prompt_meta` en `pasos/prueba_subidas.py`.

## Pendiente / ideas
1. Catálogo de la mamá: faltan nombre de tienda, WhatsApp, prendas y fotos.
2. Web del negocio.
3. Tendencias + ideas: HECHO dentro del estudio (etapa 5, pestaña «💡 Ideas»).
4. Tesis y presentaciones cuando las pida.
