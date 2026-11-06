"""LAS LETRAS ESTILO TIKTOK de los subtitulos palabra a palabra y del gancho.

Punto B+ de las notas de David: fuentes con caracter (Montserrat Black, Bebas
Neue, Lilita One, Playfair) en vez de la letra de sistema del estilo.

Los ficheros viven en `motores/fuentes/` (dentro del repo, licencia OFL) y eso
es lo que importa: el estudio MIDE con Python y DIBUJA con el navegador, y los
dos tienen que abrir el MISMO fichero (ver `tipografia`). Asi no hay que
instalar nada en el servidor ni tocar fontconfig: `tipografia.FUENTES` las
registra por su familia y `p8_render` mete un `@font-face` con la ruta en la
pagina de cada plano (el navegador corre con --allow-file-access-from-files).

Param del paso callouts `letra`: una clave de LETRAS, o "estilo" (la del set de
diseno, como antes). Si falta y el gancho esta puesto, va "montserrat": no esta
en los defectos, asi que no mueve firmas.
"""
import os

CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "motores", "fuentes")

#: clave -> ficha. `familia` es el nombre con el que se declara en la pagina:
#: propio, para que nunca se confunda con una fuente del sistema que se llame
#: igual y mida distinto. `mayus`: la fuente solo tiene mayusculas (Bebas) o se
#: lee mejor asi, y entonces TODO el texto va en mayusculas (un solo criterio).
LETRAS = {
    "montserrat": {"nombre": "Montserrat Black", "familia": "Shaddai Montserrat",
                   "fichero": "Montserrat-Black.ttf", "escala": 1.12,
                   "mayus": False},
    "bebas": {"nombre": "Bebas Neue", "familia": "Shaddai Bebas",
              "fichero": "BebasNeue-Regular.ttf", "escala": 1.45, "mayus": True},
    "lilita": {"nombre": "Lilita One", "familia": "Shaddai Lilita",
               "fichero": "LilitaOne-Regular.ttf", "escala": 1.25,
               "mayus": False},
    "playfair": {"nombre": "Playfair Display", "familia": "Shaddai Playfair",
                 "fichero": "PlayfairDisplay-ExtraBold.ttf", "escala": 1.2,
                 "mayus": False},
}

#: La que se usa con el gancho puesto si nadie eligio otra.
POR_DEFECTO = "montserrat"


def ruta(clave):
    ficha = LETRAS.get(clave)
    return os.path.join(CARPETA, ficha["fichero"]) if ficha else ""


def de_params(p):
    """La ficha de la letra pedida, o None (= la del estilo, como siempre)."""
    p = p or {}
    clave = str(p.get("letra") or "").strip().lower()
    if not clave:
        clave = POR_DEFECTO if p.get("gancho") else "estilo"
    ficha = LETRAS.get(clave)
    if not ficha or not os.path.exists(ruta(clave)):
        return None
    return dict(ficha, clave=clave)


def registrar(fuentes):
    """Mete las letras en la tabla de `tipografia` (familia en minusculas)."""
    for clave, ficha in LETRAS.items():
        r = ruta(clave)
        fuentes.setdefault(ficha["familia"].lower(), (r, r))


def css_para(svg):
    """Los @font-face de las letras que de verdad salen en `svg`. -> str"""
    reglas = []
    for clave, ficha in LETRAS.items():
        if ficha["familia"] in (svg or "") and os.path.exists(ruta(clave)):
            url = "file:///" + os.path.abspath(ruta(clave)).replace("\\", "/").lstrip("/")
            reglas.append("@font-face{font-family:'%s';src:url('%s') "
                          "format('truetype');font-display:block}"
                          % (ficha["familia"], url))
    return "".join(reglas)
