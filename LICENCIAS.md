# Licencias del código y los recursos de terceros que van DENTRO del repo

El render del servidor no descarga nada de internet: todo lo de fuera vive aquí,
con su licencia al lado. Al añadir una pieza nueva, apúntala en esta tabla.

| Qué | Dónde | Licencia | Para qué |
|---|---|---|---|
| anime.js 3.2.2 (Julian Garnier) | `motores/js/anime.min.js` | MIT (`motores/js/LICENSE-animejs.md`) | curvas y líneas de tiempo de los rótulos (`pasos/rotulos.py`) |
| lottie-web 5.12.2 (Airbnb/Bodymovin), versión «light» (solo SVG) | `motores/js/lottie_light.min.js` | MIT (`motores/js/LICENSE-lottie.md`) | fuego, humo y luz de los escenarios (`pasos/escenarios.py`); las animaciones las genera el propio módulo |
| three.js r159 (three.js authors) | `motores/js/three.min.js` | MIT (`motores/js/LICENSE-three.md`) | el decorado 3D de la Biblia abierta (`pasos/biblia3d.py`), con WebGL por software |
| Montserrat, Bebas Neue, Lilita One, Playfair Display | `motores/fuentes/` | SIL OFL 1.1 (`OFL-*.txt`) | letras de subtítulos y rótulos |

GSAP NO: su licencia gratuita no es libre.

**Lo que se baja al montar (no va en el repo):** los cuadros del modo editorial
(`pasos/editorial.py`) salen de **The Met Open Access** (solo obras marcadas de
dominio público, CC0). Se bajan una vez por vídeo a `trabajo/cuadros/` con su
ficha (título, autor, fecha, número de objeto), y el pie del cuadro dice autor y
año. Sin internet el plano sale sin cuadro.
