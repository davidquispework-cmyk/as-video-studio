---
name: web-negocio
description: Crear la página web del negocio de ropa de la mamá de David (u otra web de negocio): portada, quiénes somos, catálogo enlazado, contacto/WhatsApp, ubicación, redes. Úsala cuando se hable de la página web, la web de la tienda, el dominio o la presencia en internet del negocio.
---

# Página web del negocio

## Qué es
La web «de presentación» de la tienda; el catálogo (skill `catalogo-ropa`, carpeta
`kit-negocio/catalogo/`) es su sección de productos. Mismo estilo, misma marca,
mismo servidor. Estática (HTML/CSS/JS), sin WordPress salvo que lo pidan.

## Secciones
1. Portada: nombre, eslogan, foto grande, botón «Ver catálogo» y «Escríbenos por WhatsApp».
2. Novedades / más vendidos (lee las primeras de `productos.json` del catálogo).
3. Quiénes somos (historia corta del negocio de la mamá).
4. Cómo comprar: elegir → pedir por WhatsApp → pago (Yape/Plin/transferencia) → envío o recojo.
5. Ubicación y horario (mapa de Google embebido si hay tienda física).
6. Redes (Facebook, Instagram, TikTok) y botón flotante de WhatsApp.
7. Pie con datos de contacto.

## Reglas
- Primero el celular. Cargar rápido: fotos comprimidas, sin librerías pesadas.
- SEO básico: `<title>`, descripción, Open Graph (que se vea bonita al compartir por
  WhatsApp), `lang="es"`.
- Textos en español de Perú, cercanos. Precios en S/.
- Datos a pedir de una vez: nombre, logo/colores, eslogan, historia corta,
  WhatsApp, dirección y horario, redes, formas de pago, envíos.

## Publicar
Igual que el catálogo (ver skill `catalogo-ropa` → «Publicarlo en el servidor»):
carpeta en `/var/www/<sitio>/`, sitio nginx nuevo, dominio con registro A a
2.24.29.157, certbot. El catálogo puede ir en `/catalogo/` del mismo dominio.
**Nunca tocar la configuración de Shaddai Studio.**

## Ahorrar consumo
Mismas reglas que en `catalogo-ropa`: datos de una vez, pocas iteraciones, capturas
en móvil y escritorio como única prueba, explicar en sencillo.
