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

## Ideas para más adelante
3D low-poly como el vídeo viral (lejano); mapas antiguos animados (viajes de
Pablo); línea de tiempo animada; acuarela animada (etapa 8 de la hoja de ruta).
