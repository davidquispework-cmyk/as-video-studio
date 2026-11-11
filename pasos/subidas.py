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

try:
    from . import fidelidad
except ImportError:  # ejecutado con la carpeta pasos directamente en sys.path
    import fidelidad

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
                       sitio="", anterior=None, contexto=""):
    """Un prompt corto y en limpio para pegar en Gemini, ChatGPT o similar.

    El prompt del motor esta escrito para gpt-image con sus referencias
    adjuntas ("reference image 3 is..."); pegado en un chat no sirve. Este
    dice lo mismo sin citar adjuntos: el estilo con palabras, que se ve en
    el plano y lo que se esta contando en ese momento.

    `contexto` es el texto de todo el video: si es biblico, el prompt lleva la
    epoca (gente, ropa, sitios y objetos reales, y lo que NO va) y lo que la
    frase tiene que EXPLICAR -- dos lugares piden un mapa con su distancia --.
    Ver `fidelidad.py`.
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
            descr = fidelidad.ficha_en_su_epoca(nombre, fichas.get(nombre) or "")
            partes.append(f"- {nombre}" + (f": {descr}" if descr else ""))
    narrado = " ".join(str(escena.get("narracion") or "").split())
    # LA EPOCA DE ESTE PLANO, no la del video: ver `fidelidad.epoca_del_plano`
    partes.extend(fidelidad.pauta_imagen(
        contexto, narrado, con_gente=bool(personajes), personajes=personajes,
        fichas=fichas, que=" ".join(str(x or "") for x in (que, lugar))))
    if anterior:
        partes.append(f"CONTINUIDAD: este plano va justo después de {anterior}. "
                      f"Si te dejo adjunta la imagen de {anterior}, usa el MISMO "
                      "estilo de dibujo, paleta de colores, luz y aspecto de los "
                      "personajes; solo cambia lo que dice «QUÉ SE VE».")
    narracion = " ".join(str(escena.get("narracion") or "").split())
    if narracion:
        partes.append(f"LO QUE SE ESTÁ NARRANDO (no lo escribas en la imagen): "
                      f"«{narracion}»")
    if contexto and fidelidad.es_biblico(contexto) and fidelidad.pide_rotulos(narrado):
        partes.append("Sin más texto que los nombres de los lugares y la "
                      "distancia del mapa (cortos, grandes y bien escritos en "
                      "español); sin marcos ni viñetas: una sola imagen a sangre.")
    else:
        partes.append("Sin texto, sin letras, sin rótulos, sin marcos ni viñetas: "
                      "una sola escena a sangre.")
    return "\n".join(partes)


# ------------------------------------------ ETAPA 6: un solo prompt para todas

def _limpio(texto):
    return " ".join(str(texto or "").split())


def ficha_fija(ident, ficha):
    """Una linea de la ficha de un personaje: como se llama, quien es y como es.

    `descripcion` es el aspecto PERMANENTE que escribio el catalogo (en ingles,
    tal cual: los generadores lo entienden igual y traducirlo lo cambiaria).
    """
    ficha = ficha if isinstance(ficha, dict) else {"descripcion": ficha}
    nombre = _limpio(ficha.get("nombre")) or ident.replace("_", " ").title()
    papel = _limpio(ficha.get("papel"))
    aspecto = fidelidad.ficha_en_su_epoca(ident, _limpio(ficha.get("descripcion")))
    linea = f"• {nombre.upper()}" + (f" ({papel})" if papel else "")
    if aspecto and aspecto.lower() != ident.lower():
        linea += f": {aspecto}"
    else:
        linea += (": invéntale un aspecto en la imagen donde salga por primera "
                  "vez y repítelo EXACTO en las demás")
    return linea


def prompt_unico(escenas, guia="", formato="", reparto=None, sets=None,
                 contexto="", munecos=False):
    """ETAPA 6: todas las imagenes del video en UN solo texto para Gemini.

    Lo comun va UNA vez arriba (estilo, epoca, la FICHA FIJA de cada personaje
    que sale y los sitios) y debajo cada plano numerado con su id (S001...),
    corto. Gemini hace una imagen por respuesta, asi que el texto le dice que
    haga la 1 y espere «sigue»: en la misma charla ve todas las fichas y las
    imagenes anteriores, y por eso mantiene caras y ropa.

    Con muñecos (`munecos=True`) la imagen es SOLO el fondo: los personajes los
    pinta el render, asi que no van fichas y se pide el sitio vacio.
    """
    reparto = reparto or {}
    sets = sets or {}
    escenas = list(escenas or [])
    vertical = str(formato or "").lower().startswith("vert")
    medida = "vertical (9:16)" if vertical else "horizontal (16:9)"
    n = len(escenas)
    if not n:
        return "No hay planos que necesiten imagen (o ya están todos subidos)."

    salen = []
    for e in escenas:
        for quien in e.get("personajes") or []:
            if quien not in salen:
                salen.append(quien)
    sitios = []
    for e in escenas:
        s = e.get("set")
        if s and s in sets and s not in sitios:
            sitios.append(s)

    cuantas = "1 ilustración" if n == 1 else f"{n} ilustraciones"
    t = [f"Vas a crear {cuantas} {medida} para UN mismo vídeo animado "
         "narrado. Son planos seguidos de la misma historia: tienen que parecer "
         "del mismo artista, con el mismo estilo, la misma paleta y los mismos "
         "personajes.",
         "",
         "CÓMO TRABAJAMOS: lee todo primero. Luego crea SOLO la imagen 1. "
         "Cuando yo escriba «sigue», crea la siguiente, y así hasta la "
         f"{n}. Si escribo «otra vez», repite la última corrigiendo lo que te "
         "diga. Antes de cada imagen escribe solo su número y su código "
         "(por ejemplo «1 · S001»), nada más.",
         ""]
    if guia:
        t += ["ESTILO (igual en TODAS): " + _limpio(guia), ""]
    epoca = fidelidad.pauta_imagen(contexto, "", con_gente=not munecos and bool(salen))
    if epoca:
        t += ["LA ÉPOCA (igual en TODAS):"] + epoca + [""]
    if munecos:
        t += ["SOLO EL FONDO: en ninguna imagen dibujes personas ni figuras; "
              "los personajes se ponen después encima. Deja sitio libre en el "
              "centro y abajo.", ""]
    elif salen:
        t += ["FICHAS FIJAS DE LOS PERSONAJES — cada uno con la MISMA cara, "
              "edad, pelo, barba, complexión y la MISMA ropa y colores en "
              "TODAS las imágenes donde salga. Nunca le cambies la ropa ni el "
              "aspecto de una imagen a otra:"]
        t += [ficha_fija(q, reparto.get(q)) for q in salen]
        t.append("")
    if sitios:
        t += ["LOS SITIOS (cuando vuelvan, que sean el mismo sitio):"]
        for s in sitios:
            f = sets.get(s) or {}
            f = f if isinstance(f, dict) else {"descripcion": f}
            d = _limpio(f.get("prompt") or f.get("descripcion")) or s
            luz = _limpio(f.get("luz"))
            t.append(f"• {s.upper()}: {d}" + (f" Luz: {luz}." if luz else ""))
        t.append("")
    t += ["EN TODAS: una sola escena a sangre, sin marcos ni viñetas, y sin "
          "texto ni letras (salvo los mapas que lo pidan abajo). Lo que va "
          "«entre comillas» es lo que narra la voz: sirve para entender el "
          "momento, NO lo escribas en la imagen.",
          "", "=" * 60, "LAS IMÁGENES", "=" * 60]

    for i, e in enumerate(escenas, 1):
        t += ["", f"{i} · {e.get('id')}"]
        que = _limpio(e.get("prompt") or e.get("direccion") or e.get("accion"))
        if que:
            t.append("Qué se ve: " + que)
        if e.get("set"):
            t.append(f"Dónde: {str(e['set']).upper()}")
        elif e.get("lugar"):
            t.append(f"Dónde: {_limpio(e['lugar'])}")
        quienes = e.get("personajes") or []
        if quienes and not munecos:
            nombres = [_limpio((reparto.get(q) or {}).get("nombre")
                               if isinstance(reparto.get(q), dict) else "")
                       or q.replace("_", " ").title() for q in quienes]
            t.append("Quién sale (según su ficha): " + ", ".join(nombres))
        narrado = _limpio(e.get("narracion"))
        explica = fidelidad.explicar(narrado) if contexto and \
            fidelidad.es_biblico(contexto) else ""
        if explica:
            t.append(f"Explica: {explica}.")
            if fidelidad.pide_rotulos(narrado):
                t.append("Esta SÍ lleva texto: los nombres de los lugares y la "
                         "distancia, cortos, grandes y bien escritos en español.")
        if narrado:
            t.append(f"«{narrado}»")
    t += ["", "Empieza ahora con la imagen 1."]
    return "\n".join(t)
