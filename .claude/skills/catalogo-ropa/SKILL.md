---
name: catalogo-ropa
description: Crear, ampliar o publicar el catálogo de ropa del negocio de la mamá de David (fotos, precios, tallas, filtros, pedido por WhatsApp, PDF). Úsala siempre que se hable del catálogo, la tienda de ropa, las prendas, subir productos o publicarlo en el servidor de Hostinger.
---

# Catálogo de ropa (negocio de la mamá de David)

## Punto de partida
Ya existe una versión que funciona en `kit-negocio/catalogo/` (HTML + CSS + JS sin
dependencias, los productos en `productos.json`). **Parte de ahí, no empieces de cero.**
Ábrelo con un servidor local (`python3 -m http.server` dentro de la carpeta) y
míralo antes de cambiar nada.

## Lo que el negocio necesita (decidido con David)
- Cada prenda: foto(s), nombre, precio en soles (S/), tallas, colores, categoría, «agotado».
- Filtros por categoría y talla, y buscador.
- Botón **«Pedir por WhatsApp»** en cada prenda: abre `https://wa.me/<numero>?text=...`
  con el mensaje ya escrito (prenda, talla, color, precio). Sin pasarela de pagos.
- Botón **«Descargar catálogo en PDF»**: hoja de impresión (`@media print`) con
  todas las prendas en rejilla; se imprime a PDF desde el navegador y se manda por WhatsApp.
- Se ve perfecto en el **celular** (es donde lo verán las clientas).
- Fase 2 (cuando lo pidan): panel con contraseña para que la mamá suba fotos,
  cambie precios y marque agotado desde el celular → backend pequeño (Python
  FastAPI o Node) con SQLite, en el mismo servidor.

## Datos que hay que pedir ANTES de programar (todo en un solo mensaje)
1. Nombre de la tienda, logo o colores. 2. Número de WhatsApp (con 51 de Perú).
3. Categorías. 4. Lista de prendas (nombre, precio, tallas, colores) — vale una foto
de una libreta o un Excel. 5. Fotos de las prendas (o si hay que generarlas/mejorarlas).
6. Dominio deseado (si tiene).

## Fotos
- Recórtalas a 4:5 (vertical, como Instagram), 1080 px de ancho, JPG ~80 %.
- Nombre del fichero = id de la prenda (`p001.jpg`). Van en `fotos/`.
- Si no hay buenas fotos: fondo neutro, luz de día; o generarlas gratis con Gemini
  (como las imágenes del estudio) y avisar de que son ilustrativas.

## Publicarlo en el servidor (VPS Hostinger srv2128660, Ubuntu 24.04)
En ese servidor YA corre **Shaddai Studio** (nginx + servicios as-video-studio y
as-video-login, puerto interno 8110, carpeta /opt/as-video-studio). **No tocar nada
de eso.** El catálogo es estático, así que:
1. Copiar la carpeta a `/var/www/catalogo/` (dueño www-data).
2. Un sitio nginx NUEVO en `/etc/nginx/sites-available/catalogo` con `server_name`
   del dominio del catálogo y `root /var/www/catalogo;`, enlazarlo en sites-enabled,
   `nginx -t` y `systemctl reload nginx`.
3. Dominio: registro A apuntando a la IP del VPS (2.24.29.157) en el panel de Hostinger.
4. HTTPS: `certbot --nginx -d <dominio>`.
5. Antes de cambios grandes: snapshot del VPS desde el panel de Hostinger.
El dueño puede hacer todo esto escribiendo `claude` en la consola del servidor
(Claude Code ya está instalado allí) o pegando los comandos que se le den.

## Ahorrar consumo (David está en el plan Pro)
- Pedir todos los datos de una vez; no ir y venir.
- Nada de baterías de pruebas pesadas: abrir la página en Playwright, una captura
  en móvil y otra en escritorio, y listo.
- Cambios pequeños y concretos; enseñar el resultado con una captura.
- Explicar todo a David en español sencillo: no es programador.
