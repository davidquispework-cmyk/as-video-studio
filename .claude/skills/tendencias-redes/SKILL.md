---
name: tendencias-redes
description: Construir y usar la herramienta de tendencias de David para YouTube y TikTok: qué vídeos están pegando, por qué, y ideas de contenido para su canal (videos animados narrados, temas bíblicos/historia) con vistas a monetizar. Úsala cuando hable de tendencias, algoritmo, vídeos virales, ideas de vídeos, monetizar, YouTube o TikTok.
---

# Tendencias de YouTube y TikTok + ideas

## Qué se quiere (decidido con David)
Una web propia, con contraseña, en su VPS de Hostinger (como Shaddai Studio y sin
tocarlo), que:
1. Muestre los vídeos más vistos/de mayor crecimiento por país (Perú y
   Latinoamérica), por categoría y por palabras clave de su nicho.
2. Calcule señales útiles: vistas por hora desde que se publicó, me gusta/vistas,
   comentarios/vistas, duración, título, miniatura, hora de publicación.
3. Guarde el histórico (SQLite) para ver qué sube y qué baja día a día.
4. Proponga ideas de vídeo con Claude (el CLI ya está en el servidor, usa la
   suscripción): título, gancho de los 3 primeros segundos, guion corto, miniatura.
5. Pase la idea elegida a Shaddai Studio como encargo de vídeo.

## De dónde salen los datos (honesto)
- **YouTube: API oficial YouTube Data API v3, gratis** con una clave de Google Cloud
  (cuota ~10.000 unidades/día: `videos.list chart=mostPopular regionCode=PE` cuesta 1;
  `search.list` cuesta 100, usarla poco). Pasos para David: console.cloud.google.com →
  proyecto → habilitar «YouTube Data API v3» → Credenciales → Clave de API.
- **TikTok: no hay API pública gratuita de tendencias** para personas. Opciones:
  TikTok Creative Center (página pública de tendencias: hashtags, canciones, vídeos
  top por país) consultada a mano o con lectura de la página respetando sus
  condiciones; la Research API es solo para académicos. No prometer datos de TikTok
  que no se puedan obtener legalmente.
- Su propio canal: YouTube Analytics API (con su permiso OAuth) para ver qué le
  funciona a ÉL, que es lo más valioso.

## Construcción (cuando lo pida)
Backend Python (FastAPI) + SQLite + tarea programada cada pocas horas (systemd
timer o cron) + página HTML simple. Nginx en un subdominio nuevo con certbot y
login. Ver la skill `catalogo-ropa` → «Publicarlo en el servidor» para el patrón.

## Monetizar (para orientar las ideas)
YouTube Partner: 1.000 suscriptores + 4.000 h de visualización en 12 meses (o 10 M
de vistas de Shorts en 90 días). Constancia > viralidad: un calendario semanal.
Contenido animado con voz sintética: añadir valor propio (guion original,
investigación) para cumplir las políticas de contenido repetitivo.
