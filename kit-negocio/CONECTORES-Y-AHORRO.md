# Cómo trabajar con Claude Pro gastando poco

## Conexiones que ya tienes (y sirven)
- **GitHub** (conectado): donde se guarda todo. Abre cada sesión nueva con el
  repositorio `davidquispework-cmyk/as-video-studio` seleccionado: así Claude carga
  solo las skills `catalogo-ropa` y `web-negocio` y ya sabe todo esto.
- **Hostinger** (conectado): ver el estado del VPS, DNS/dominios. No ejecuta comandos
  dentro del servidor.
- **Google Drive** (conectado): sube ahí las fotos de las prendas en una carpeta y pásale
  el enlace a Claude; las baja él. Más cómodo que adjuntarlas una a una.
- **Google Sheets** (conectado): la lista de prendas en una hoja (columnas: id, nombre,
  categoría, precio, tallas, colores, agotado). Claude la lee y genera productos.json.

## En el servidor
- **Claude Code ya está instalado en el VPS**: en la consola de Hostinger escribe
  `claude` y pídele cosas allí mismo (publicar el catálogo, crear un dominio nuevo...).
  Usa la misma cuenta Pro.

## Para gastar menos del plan Pro
1. Todo en UN mensaje: datos, fotos (enlace de Drive) y lo que quieres.
2. Empieza cuando el límite de la sesión se haya reiniciado.
3. Pide «sin pruebas pesadas, solo una captura en móvil».
4. Una cosa por sesión (hoy el catálogo, otro día la web).
5. Frase de arranque: «Usa la skill catalogo-ropa. Datos: ... Fotos: <enlace Drive>».
