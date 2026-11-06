"""
LAS IMAGENES QUE PONE UNA PERSONA, plano a plano (modo de imagen «manual»).

QUE PROBLEMA RESUELVE
---------------------
Generar los planos con gpt-image cuesta dinero de verdad (~0,05 $ por imagen,
un video de cuatro minutos son ~126). Hay muchas formas de conseguir una imagen
sin pagar por API --Gemini, ChatGPT o Copilot desde el navegador, fotos o
dibujos propios-- y lo unico que hace falta es que el estudio diga QUE imagen
necesita cada plano y la recoja.

Asi que en este modo el estudio hace todo lo de siempre (guion, voz, corte en
planos, cartelas, direccion) y, en vez de llamar a OpenAI, deja preparado el
prompt de cada plano para copiarlo. La persona sube la imagen de cada plano --de
una en una o en un zip-- y el paso de assets la coloca en su sitio.

DONDE VIVEN
-----------
En `<proyecto>/subidas/<plano>.png`, FUERA de las carpetas versionadas del paso
(`pasos/assets/vN`): una version nueva se construye copiando la anterior, y lo
que la persona ha subido no puede depender de que una tanda llegue a sellarse.
Cada imagen se guarda ya normalizada -- PNG, RGB y recortada al tamano del
plano (1536x1024 apaisado, 1024x1536 vertical) --, asi que el resto del
pipeline la ve exactamente igual que una dibujada por el motor.

Este modulo no sabe de HTTP ni del grafo: lo llaman `app.py` (las rutas de
subir, listar y borrar) y `p6_assets` (al montar los planos).
"""

import io
import os
import re
import zipfile

from PIL import Image, ImageOps

#: Tamano final de cada plano, el mismo que pide el motor de imagen.
TAMANOS = {"apaisado": (1536, 1024), "vertical": (1024, 1536),
           "cuadrado": (1024, 1024)}

#: Lo que se acepta subir. Se convierte todo a PNG al guardarlo.
EXTENSIONES = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")

#: Tope por imagen, para que un fichero enorme no tumbe el servidor.
MAX_BYTES = 25 * 1024 * 1024

#: Tope del zip entero.
MAX_ZIP_BYTES = 600 * 1024 * 1024

_ID_PLANO = re.compile(r"^S\d{3,4}$")


def carpeta(raiz_proyecto):
    """Donde se guardan las imagenes subidas de un proyecto."""
    return os.path.join(raiz_proyecto, "subidas")


def ruta_de(raiz_proyecto, sid):
    """La imagen subida de un plano (exista o no)."""
    return os.path.join(carpeta(raiz_proyecto), f"{validar_id(sid)}.png")


def existe(raiz_proyecto, sid):
    return os.path.isfile(ruta_de(raiz_proyecto, sid))


def validar_id(sid):
    """Un id de plano valido ('S001'). Lanza ValueError si no.

    Sale en una ruta de disco: sin esta comprobacion, un '../' en la URL
    escribiria fuera de la carpeta del proyecto.
    """
    sid = str(sid or "").strip().upper()
    if not _ID_PLANO.match(sid):
        raise ValueError(f"id de plano no valido: {sid!r} (se espera S001, S002...)")
    return sid


def id_desde_nombre(nombre):
    """El plano al que va un fichero por su nombre. -> 'S007' | None

    Acepta lo que sale de verdad al guardar a mano: 'S007.png', 's7.jpg',
    'S007_mercado.webp', '007.png', 'plano 7.png', '7.jpg'.
    """
    base = os.path.splitext(os.path.basename(str(nombre or "")))[0].strip()
    m = re.match(r"^\s*(?:plano|escena|s)?[\s_\-]*0*(\d{1,4})(?:\D.*)?$", base,
                 re.IGNORECASE)
    if not m:
        return None
    numero = int(m.group(1))
    if numero <= 0:
        return None
    return f"S{numero:03d}"


def normalizar(datos, tamano="apaisado"):
    """Bytes de una imagen cualquiera -> bytes PNG al tamano del plano.

    Se RECORTA para llenar (como `object-fit: cover`), no se deforma ni se
    rellena con bandas: el movimiento de camara del render recorre la imagen
    entera y una banda negra se veria pasar.
    """
    if not datos:
        raise ValueError("el fichero esta vacio")
    if len(datos) > MAX_BYTES:
        raise ValueError("la imagen pesa mas de 25 MB")
    try:
        imagen = Image.open(io.BytesIO(datos))
        imagen.load()
    except Exception as fallo:                       # noqa: BLE001
        raise ValueError(f"no se reconoce como imagen: {fallo}") from fallo
    imagen = ImageOps.exif_transpose(imagen)
    if imagen.mode in ("RGBA", "LA", "P"):
        imagen = imagen.convert("RGBA")
        fondo = Image.new("RGB", imagen.size, (0, 0, 0))
        fondo.paste(imagen, mask=imagen.split()[-1])
        imagen = fondo
    else:
        imagen = imagen.convert("RGB")
    ancho, alto = TAMANOS.get(tamano) or TAMANOS["apaisado"]
    imagen = ImageOps.fit(imagen, (ancho, alto), method=Image.LANCZOS,
                          centering=(0.5, 0.5))
    salida = io.BytesIO()
    imagen.save(salida, format="PNG", optimize=False)
    return salida.getvalue()


def guardar(raiz_proyecto, sid, datos, tamano="apaisado"):
    """Guarda la imagen de un plano, ya normalizada. -> ruta"""
    destino = ruta_de(raiz_proyecto, sid)
    png = normalizar(datos, tamano)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    temporal = destino + ".tmp"
    with open(temporal, "wb") as fh:
        fh.write(png)
    os.replace(temporal, destino)
    return destino


def borrar(raiz_proyecto, sid):
    """Quita la imagen subida de un plano. -> True si habia una."""
    ruta = ruta_de(raiz_proyecto, sid)
    if os.path.isfile(ruta):
        os.remove(ruta)
        return True
    return False


def listar(raiz_proyecto):
    """Los planos que ya tienen imagen subida. -> {sid: {"bytes", "mtime"}}"""
    base = carpeta(raiz_proyecto)
    if not os.path.isdir(base):
        return {}
    salida = {}
    for nombre in os.listdir(base):
        sid, ext = os.path.splitext(nombre)
        if ext.lower() != ".png" or not _ID_PLANO.match(sid):
            continue
        info = os.stat(os.path.join(base, nombre))
        salida[sid] = {"bytes": info.st_size, "mtime": int(info.st_mtime)}
    return salida


def importar_zip(raiz_proyecto, datos, validos, tamano="apaisado"):
    """Mete todas las imagenes de un zip en su plano, por el nombre del fichero.

    `validos` son los ids de plano que existen y llevan imagen: lo que no
    case con ninguno se devuelve en `ignorados` con su motivo, en vez de
    guardarse con un nombre que ningun plano va a leer.
    -> {"guardados": [sid], "ignorados": [{"fichero", "motivo"}]}
    """
    if len(datos) > MAX_ZIP_BYTES:
        raise ValueError("el zip pesa mas de 600 MB")
    try:
        archivo = zipfile.ZipFile(io.BytesIO(datos))
    except zipfile.BadZipFile as fallo:
        raise ValueError("el fichero no es un zip valido") from fallo
    validos = set(validos or [])
    guardados, ignorados = [], []
    for info in archivo.infolist():
        if info.is_dir():
            continue
        nombre = info.filename
        base = os.path.basename(nombre)
        if not base or base.startswith(".") or "__MACOSX" in nombre:
            continue
        if os.path.splitext(base)[1].lower() not in EXTENSIONES:
            ignorados.append({"fichero": nombre, "motivo": "no es una imagen"})
            continue
        sid = id_desde_nombre(base)
        if not sid:
            ignorados.append({"fichero": nombre,
                              "motivo": "el nombre no dice de que plano es "
                                        "(llamalo S001.png, S002.png...)"})
            continue
        if validos and sid not in validos:
            ignorados.append({"fichero": nombre,
                              "motivo": f"{sid} no es un plano con imagen en "
                                        f"este video"})
            continue
        if info.file_size > MAX_BYTES:
            ignorados.append({"fichero": nombre, "motivo": "pesa mas de 25 MB"})
            continue
        try:
            guardar(raiz_proyecto, sid, archivo.read(info), tamano)
        except ValueError as fallo:
            ignorados.append({"fichero": nombre, "motivo": str(fallo)})
            continue
        guardados.append(sid)
    return {"guardados": sorted(set(guardados)), "ignorados": ignorados}


# --------------------------------------------------- los prompts para copiar

def prompt_para_copiar(escena, guia="", idioma="", formato="", fichas=None,
                       sitio="", anterior=None):
    """Un prompt corto y en limpio para pegar en Gemini, ChatGPT o similar.

    El prompt del motor esta escrito para gpt-image con sus referencias
    adjuntas ("reference image 3 is..."); pegado en un chat no sirve. Este
    dice lo mismo sin citar adjuntos: el estilo con palabras, que se ve en
    el plano y lo que se esta contando en ese momento.
    """
    partes = []
    vertical = str(formato or "").lower().startswith("vert")
    partes.append("Crea UNA sola ilustración "
                  + ("vertical (9:16)" if vertical else "horizontal (16:9)")
                  + " para un plano de un vídeo animado narrado.")
    if guia:
        partes.append("ESTILO: " + " ".join(str(guia).split()))
    que = (escena.get("prompt") or escena.get("direccion")
           or escena.get("accion") or "")
    if que:
        partes.append("QUÉ SE VE: " + " ".join(str(que).split()))
    lugar = escena.get("lugar") or escena.get("set")
    if lugar:
        partes.append(f"DÓNDE: {lugar}.")
    if sitio and not lugar:
        partes.append(f"DÓNDE: {sitio}")
    personajes = escena.get("personajes") or []
    fichas = fichas or {}
    if personajes:
        partes.append("QUIÉN SALE (dibújalos SIEMPRE con este mismo aspecto: "
                      "cara, edad, pelo, barba y ropa):")
        for nombre in personajes:
            descr = fichas.get(nombre)
            partes.append(f"- {nombre}" + (f": {descr}" if descr else ""))
    if anterior:
        partes.append(f"CONTINUIDAD: este plano va justo después de {anterior}. "
                      f"Si te dejo adjunta la imagen de {anterior}, usa el MISMO "
                      "estilo de dibujo, paleta de colores, luz y aspecto de los "
                      "personajes; solo cambia lo que dice «QUÉ SE VE».")
    narracion = " ".join(str(escena.get("narracion") or "").split())
    if narracion:
        partes.append(f"LO QUE SE ESTÁ NARRANDO (no lo escribas en la imagen): "
                      f"«{narracion}»")
    partes.append("Sin texto, sin letras, sin rótulos, sin marcos ni viñetas: "
                  "una sola escena a sangre.")
    return "\n".join(partes)
