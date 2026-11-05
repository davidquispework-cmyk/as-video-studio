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
  ahorro-claude, tendencias-redes.
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
1. **Etapa 1**: efectos de ambiente en el render (luces que parpadean, partículas,
   agua, nubes, rayos) + profundidad 2.5D (separar personaje/fondo con rembg en CPU,
   capas con parallax) + balanceo suave. El render ya dibuja cada fotograma con el
   navegador (p8_render / capas de p7): animar con CSS/SVG/JS ahí.
2. **Etapa 2**: subir un CLIP de vídeo por plano (además de imagen) para 1-3 momentos
   clave hechos en Kling/Hailuo/Meta AI gratis; el estudio pone voz, subtítulos y cifras.
3. **Etapa 3**: personajes «marioneta» SVG por piezas (brazos articulados) con gestos.

## Pendiente / ideas
1. Catálogo de la mamá: faltan nombre de tienda, WhatsApp, prendas y fotos.
2. Web del negocio.
3. Web de tendencias YouTube/TikTok + ideas → Shaddai Studio.
4. Tesis y presentaciones cuando las pida.
