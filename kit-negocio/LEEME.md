# Kit del negocio (catálogo y web de la tienda de mamá)

- `catalogo/` — catálogo que YA funciona: abre `index.html` con un servidor
  (`python3 -m http.server` dentro de la carpeta). Las prendas se editan en
  `productos.json`; las fotos van en `catalogo/fotos/` y se ponen en el campo `foto`
  (por ejemplo `"foto": "fotos/p001.jpg"`).
- Las instrucciones para Claude están en `.claude/skills/catalogo-ropa` y
  `.claude/skills/web-negocio`: se cargan solas al abrir una sesión con este repositorio.

## Para la próxima sesión, ten listo (todo en UN mensaje)
1. Nombre de la tienda, logo o colores.
2. WhatsApp de pedidos (con 51 delante).
3. Categorías y lista de prendas: nombre, precio, tallas, colores.
4. Fotos de las prendas.
5. Dominio que te gustaría (si ya tienes uno).
6. Para la web: eslogan, historia corta, dirección y horario, redes, formas de pago, envíos.

Frase para empezar: «Usa la skill catalogo-ropa: aquí están los datos de la tienda de mi mamá…»
