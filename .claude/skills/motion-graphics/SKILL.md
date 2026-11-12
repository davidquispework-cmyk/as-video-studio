---
name: motion-graphics
description: Reglas decididas para el MOTION GRAPHICS de Shaddai Studio (punto G de NOTAS-DAVID.md): figuras planas propias dibujadas por código (SVG) que se mueven pieza a pieza, elementos vectoriales que entran y salen animados, storyboard en JSON por plano, biblioteca de piezas, curvas de animación profesionales y sincronía con la voz. Úsala cuando David hable de motion graphics, animación vectorial, figuras planas, palitos, muñecos que se mueven, storyboard, o al trabajar en el punto G o en `pasos/marioneta.py`.
---

# Motion graphics de Shaddai Studio

Leer antes NOTAS-DAVID.md (punto G y etapa 1 «Muñecos que gesticulan») y seguir
`ahorro-claude`. David no es programador: explicarle en español sencillo.

## Qué quiere David (decidido 6-nov-2026)
- Motion graphics **de nivel profesional, «lo mejor del mercado»**, no imágenes con zoom.
- TODO son elementos vectoriales (fondo, personajes, objetos, textos) que **entran y
  salen animados**: pop con rebote, deslizar, crecer, aparecer escalonados.
- **Curvas profesionales**: anticipación, overshoot (se pasa y vuelve), squash &
  stretch (se aplasta y se estira), easing suave; nada de movimientos lineales.
- **Cámara** que se mueve por la escena (paneo, acercamiento de golpe) y todo
  **sincronizado con las palabras** de la voz (tiempos de `subtitulos.de_escena`).
- **Algo cambia cada 2-3 s**: zoom de golpe, objeto que entra, texto que salta,
  con efectos de sonido al ritmo.
- **Lo que manda es llamar la atención, no la marca**: nada de lámpara ni dorado
  obligatorios. Colores vivos y mucho contraste, metáforas visuales sorprendentes
  («PECADO» como bola con cadena).

## Personajes: FIGURAS PLANAS PROPIAS
- Colores lisos, cabeza redonda, cara simple, túnica en campana, **diseño propio**
  (inspirarse en el formato de otros canales, nunca copiar su estilo exacto).
- Dibujados por código (SVG), evolución de `pasos/marioneta.py`, para moverlos
  **pieza a pieza**: boca al hablar (ideal: que siga la voz), parpadeo, brazos,
  caminar, arrodillarse, girar.
- **Caras MUY expresivas**: ojos grandes; sorpresa, miedo y alegría exagerados.
- José, María, Pedro… salen del **reparto** (color de túnica, velo, barba, edad),
  y su aspecto respeta la época (ver `pasos/fidelidad.py`, punto C).
- Segundo estilo opcional: **PALITOS** (stick figure) para vídeos de reflexión con
  metáforas.

## Arquitectura pensada
1. El guion (Claude) devuelve por plano un **STORYBOARD en JSON**: qué elementos,
   dónde, cuándo entran y salen (en palabras del guion), qué hace cada personaje,
   qué hace la cámara.
2. El **render** lo anima con SVG/CSS/JS en la página de `p8_render` (ya dibuja
   cada fotograma con el navegador; capa de muñecos `#munecos`).
3. **Biblioteca de piezas reutilizables** (altar, velas, cruz, casas, palmeras,
   pergamino, mapa, cadena…) que crece con cada vídeo.
4. Gemini sobra; como mucho, un fondo «ilustración vectorial plana, sin personas».

## Reglas del repo que no se pueden romper (CLAUDE.md)
- Nada nuevo en los params por defecto: **no mover firmas** (como `marioneta: true`,
  que solo existe si se elige).
- Cambiar la animación de un vídeo hecho solo debe pedir **volver a montar** (gratis).
- Sin dependencias nuevas en la interfaz (JavaScript a pelo, sin `style=""`).
- Una prueba ligera propia (`pasos/prueba_<algo>.py`) añadida a `pruebas.ps1`.

## Lo que YA está hecho (primera parte, 6-nov-2026) — `pasos/motion.py`
- Param del render `motion`: `true` | `"papel"` | `"noche"` | `{"tema", "laminas": false}`;
  no va en los defectos (no mueve firmas). Pantalla: `selectorMotion` («Animación»).
- UN MUNDO por vídeo: cada plano es una «parada» (`motion.paradas`); la cámara viaja
  de una a otra (se aleja a mitad de viaje + camino de puntos) y lo anterior SE QUEDA.
  Por eso con motion `p8_render` pone `cortes = {}` (ninguna transición) y rehacer un
  plano arrastra al SIGUIENTE (su viaje empieza viendo este).
- Cada página pinta el mundo en T = t_in + t (tiempos del VÍDEO, de `marcas`), con
  su plano y los dos anteriores. JS en `motion.MOTION_JS`; curvas: `resorte` (se pasa
  y vuelve), `eBack` (anticipación), estirar/aplastar en `mgPieza`; `luego` transforma.
- Piezas automáticas (sin Claude, gratis), por prioridad: versículo (cita entre
  comillas + referencia) > línea de tiempo (años) > mapa (lugares de `fidelidad`, con
  distancia; no repite el mismo mapa; Jerusalén sola no) > reloj (hora tercera/sexta/
  novena, «N horas al día» sobre 24 h) > lámina (la imagen del plano) + iconos que
  saltan al decir su palabra (`PALABRAS_ICONO`). En plan.json `"motion": [piezas]`
  manda (storyboard a mano); `"motion": false` = solo lámina.
- Prioridad completa: versículo > comparación («no X sino Y») > línea > mapa > reloj
  > lista («: a, b y c») > contador («cinco mil hombres») > lámina + iconos (46).
- Máscaras: cada renglón del versículo y del texto es un clipPath (la palabra sube
  desde detrás); `barrido()` descubre títulos; `trazoOvalo` + `dibujar` rodean a mano.
- Encadenado: `impactos_de` (Python) -> golpe de cámara `mgGolpe` y reacción de las
  vecinas en `mgPieza`. Cámara que sigue: `focos_de`/`ventana_de` -> `mgFoco`; los
  focos acaban 1,3 s antes del final y vuelve a la base 0,8 s antes: NO romper eso o
  vuelve el corte entre planos.
- Objeto puente (`puentes` en `preparar`, `mgPuente` en JS): sale por el lado al
  final del plano, vuela con la cámara y estalla; la pieza siguiente pasa a
  `entra: "pop"` y `en` = llegada.
- Prueba: `pasos/prueba_motion.py` (`--foto` pinta y comprueba que no hay corte).

## Segunda parte — HECHA (6-nov-2026)
- `pasos/motion_mas.py`: MUÑECOS PLANOS (`figuras`, `hazFigura` en JS; aspecto de
  `marioneta.aspecto`; gestos `GESTOS`, caras `EXPRESIONES`; la boca sigue la voz con
  `habla` = [[t0, t1, silabas]] de las palabras tras «dijo/habló…»), piezas `barras`,
  `antes`, `arbol`, `flecha`, `circulo` (`Object.assign(CONSTRUCTORES, …)` al final del
  JS), `iconoMas` (10 iconos de metáfora) y sonidos (`eventos_sonido`: whoosh por viaje
  de cámara, pop por impacto, sin amontonar; `sonido.anadir_muestras`).
- `pasos/motion_storyboard.py`: Claude (sonnet/medium, una llamada) escribe
  `{sid: [piezas]}`; caché POR PLANO con huella de la narración en
  `<proyecto>/motion/storyboard.json` (un plano que Claude no escribió se guarda con
  `piezas: null` = automático, para no volver a preguntar). `{"tipo": "auto"}` dentro
  del storyboard mete lo automático. Falla → automático, nunca para el montaje.
- `motion.storyboard`: manda plan.json (`"motion": [...]`) > Claude > `_automatico`.
  `_normalizar` acepta TODAS las piezas (fracciones del cuadro, `en` = palabra) y
  descarta lo que no entiende. Entrada `"nada"` para flecha/círculo; el objeto puente
  nunca aterriza en una pieza `SUPERPUESTAS`.
- Prioridad automática: versículo > comparación > antes/ahora > árbol > línea > mapa >
  reloj > lista > barras > contador > lámina (+ muñecos delante) o muñecos grandes.
- Opciones del param: `storyboard: "claude"`, `munecos: false`, `sonidos: false`.

## Escenarios (P3, 12-nov-2026) — `pasos/escenarios.py`
- Pieza `escenario` (va PRIMERA: detrás de todo; `fondo: true` = no aterriza, no
  reacciona, no recibe el objeto puente). SVG hecho en Python (determinista por
  semilla), animado por clases en `ESCENARIO_JS` (`esc-nube`, `esc-ola`,
  `esc-barca`, `esc-mece`, `esc-estrella`, `esc-halo`, `esc-rayos`).
- Bordes fundidos con dos máscaras lineales (no radial: se comía las esquinas);
  ocupa 1,3 W × 1,5 H porque la cámara se acerca y sube a las caras.
- Efectos Lottie generados en `lottie_de` (fuego, humo, luz) dentro de un
  `foreignObject`; `motion.js_de(conf)` mete lottie-web solo si hacen falta.
  Siempre `goToAndStop(fotograma)`: nunca reloj.

## Lo siguiente
Ver/corregir el storyboard de Claude desde la pantalla; estilo PALITOS; que un
muñeco camine de una parada a otra; más metáforas animadas (cadena que se rompe).

## Ideas para más adelante
3D low-poly como el vídeo viral (lejano); mapas antiguos animados (viajes de
Pablo); línea de tiempo animada; acuarela animada (etapa 8 de la hoja de ruta).
