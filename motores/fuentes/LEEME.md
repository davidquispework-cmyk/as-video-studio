# Fuentes de los textos estilo TikTok

Las usan los subtítulos palabra a palabra y el cartel del gancho
(`pasos/letras.py`). Van DENTRO del repositorio para que el ordenador que mide
(Python, `tipografia`) y el navegador que dibuja (`p8_render`, con `@font-face`)
usen el MISMO fichero, sin instalar nada en el servidor.

Todas son de Google Fonts, con licencia SIL Open Font License (los `OFL-*.txt`).
Montserrat Black y Playfair Display ExtraBold son instancias estáticas sacadas
de la fuente variable (`fontTools.varLib.instancer`, wght 900 y 800).
