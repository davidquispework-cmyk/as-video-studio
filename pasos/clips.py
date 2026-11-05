"""
LOS CLIPS DE VIDEO DE UN PLANO (etapa 2 del plan de animacion).

QUE PROBLEMA RESUELVE
---------------------
Una imagen quieta con zoom y efectos de ambiente da mucho de si, pero hay 1-3
momentos de cada video que piden movimiento DE VERDAD: un personaje que anda,
el mar que se abre, una lampara que se enciende. Eso se hace gratis fuera del
estudio (Kling, Hailuo, Meta AI: se les da la imagen del plano y una frase de
movimiento y devuelven 5-10 s de video). Aqui solo hace falta recogerlo.

Asi que un plano puede llevar, ADEMAS de su imagen, un clip. El render lo pone
en lugar de la imagen quieta y encima va todo lo de siempre: voz, subtitulos,
cartelas, cifras y transiciones. El clip sale MUDO (la voz es la del estudio).

DONDE VIVEN
-----------
`<proyecto>/subidas/clips/<plano>.mp4`, junto a las imagenes subidas y por la
misma razon: fuera de las carpetas versionadas de los pasos. Se guardan ya
normalizados -- H.264, sin audio, 30 fps, recortados al tamano del plano y como
mucho `MAX_SEGUNDOS` --, asi el render no tiene que adivinar nada.

Si el plano aun no tenia imagen, se saca una del clip (`subidas/<plano>.png`):
el paso de assets necesita una imagen por plano y no tiene sentido pedirle a
nadie que suba dos veces lo mismo.

Si el plano dura mas que el clip, el ultimo fotograma se queda quieto (con el
zoom de la camara encima, no se nota parado); si dura menos, se corta.

LOS DOS MODOS (ajuste `modo_clip`)
----------------------------------
  manual  (de fabrica, gratis) los clips los sube una persona.
  auto    (DE PAGO, apagado) el estudio pide el clip a fal.ai con la imagen del
          plano. Necesita `modo_clip = auto` en Configuracion Y la variable de
          entorno `FAL_KEY`. Sin las dos cosas `generar_automatico` se niega y
          no gasta nada. Ver `generar_automatico`.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request

try:
    from . import medios, subidas
except ImportError:                       # ejecutado con pasos/ en sys.path
    import medios                         # type: ignore
    import subidas                        # type: ignore

#: Lo que se acepta subir.
EXTENSIONES = (".mp4", ".mov", ".webm", ".m4v", ".mkv", ".avi", ".gif")

#: Tope por clip subido (los de Kling/Hailuo pesan 5-30 MB).
MAX_BYTES = 200 * 1024 * 1024

#: Lo mas largo que se guarda: un plano no pasa de esto y asi un video entero
#: subido por error no llena el disco.
MAX_SEGUNDOS = 20

#: Los fps del clip guardado: los del render.
FPS = 30


def carpeta(raiz_proyecto):
    return os.path.join(subidas.carpeta(raiz_proyecto), "clips")


def ruta_de(raiz_proyecto, sid):
    """El clip de un plano (exista o no)."""
    return os.path.join(carpeta(raiz_proyecto), f"{subidas.validar_id(sid)}.mp4")


def existe(raiz_proyecto, sid):
    try:
        return os.path.isfile(ruta_de(raiz_proyecto, sid))
    except ValueError:
        return False


def listar(raiz_proyecto):
    """Los planos que ya tienen clip. -> {sid: {"bytes", "mtime", "segundos"}}"""
    base = carpeta(raiz_proyecto)
    if not os.path.isdir(base):
        return {}
    salida = {}
    for nombre in os.listdir(base):
        sid, ext = os.path.splitext(nombre)
        if ext.lower() != ".mp4" or not re.match(r"^S\d{3,4}$", sid):
            continue
        ruta = os.path.join(base, nombre)
        info = os.stat(ruta)
        salida[sid] = {"bytes": info.st_size, "mtime": int(info.st_mtime),
                       "segundos": duracion(ruta)}
    return salida


def duracion(ruta):
    """Segundos de un video (0.0 si no se puede leer)."""
    try:
        proceso = subprocess.run(
            [medios.ffprobe(), "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", ruta],
            capture_output=True, text=True, timeout=60)
        return round(float(proceso.stdout.strip() or 0), 2)
    except Exception:                                   # noqa: BLE001
        return 0.0


def _tamano(tamano):
    return subidas.TAMANOS.get(tamano) or subidas.TAMANOS["apaisado"]


def _filtro_cubrir(ancho, alto):
    """Recorta para llenar (como object-fit: cover), igual que las imagenes."""
    return (f"scale={ancho}:{alto}:force_original_aspect_ratio=increase:"
            f"flags=lanczos,crop={ancho}:{alto},setsar=1")


def guardar(raiz_proyecto, sid, datos, tamano="apaisado", nombre="clip.mp4"):
    """Guarda el clip de un plano, ya normalizado. -> ficha del plano.

    Si el plano no tenia imagen subida, deja una sacada del clip.
    """
    sid = subidas.validar_id(sid)
    if not datos:
        raise ValueError("el fichero esta vacio")
    if len(datos) > MAX_BYTES:
        raise ValueError("el clip pesa mas de 200 MB")
    ext = os.path.splitext(str(nombre or ""))[1].lower() or ".mp4"
    if ext not in EXTENSIONES:
        raise ValueError(f"{ext} no es un video ({', '.join(EXTENSIONES)})")
    destino = ruta_de(raiz_proyecto, sid)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    ancho, alto = _tamano(tamano)
    with tempfile.TemporaryDirectory(prefix="clip_") as tmp:
        bruto = os.path.join(tmp, "entrada" + ext)
        with open(bruto, "wb") as fh:
            fh.write(datos)
        temporal = os.path.join(tmp, "salida.mp4")
        orden = [medios.ffmpeg(), "-y", "-loglevel", "error", "-i", bruto,
                 "-t", str(MAX_SEGUNDOS), "-an",
                 "-vf", f"{_filtro_cubrir(ancho, alto)},fps={FPS},format=yuv420p",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                 "-movflags", "+faststart", temporal]
        proceso = subprocess.run(orden, capture_output=True, text=True,
                                 timeout=600)
        if proceso.returncode != 0 or not os.path.isfile(temporal):
            raise ValueError("no se reconoce como video: "
                             + (proceso.stderr or "").strip()[-200:])
        segundos = duracion(temporal)
        if segundos < 0.3:
            raise ValueError("el clip no tiene fotogramas (dura menos de 0,3 s)")
        shutil.move(temporal, destino)
    if not subidas.existe(raiz_proyecto, sid):
        _imagen_desde_clip(raiz_proyecto, sid, destino, tamano)
    return {"id": sid, "segundos": segundos}


def _imagen_desde_clip(raiz_proyecto, sid, clip, tamano):
    """Deja como imagen del plano el primer fotograma del clip."""
    with tempfile.TemporaryDirectory(prefix="clipimg_") as tmp:
        png = os.path.join(tmp, "f.png")
        subprocess.run([medios.ffmpeg(), "-y", "-loglevel", "error", "-i", clip,
                        "-frames:v", "1", png], capture_output=True, timeout=120)
        if os.path.isfile(png):
            with open(png, "rb") as fh:
                subidas.guardar(raiz_proyecto, sid, fh.read(), tamano)


def borrar(raiz_proyecto, sid):
    """Quita el clip de un plano (su imagen se queda). -> True si habia uno."""
    ruta = ruta_de(raiz_proyecto, sid)
    if os.path.isfile(ruta):
        os.remove(ruta)
        return True
    return False


def huella(raiz_proyecto, sid):
    """Lo que identifica el clip de un plano ("" sin clip): entra en el render."""
    try:
        return medios.huella_fichero(ruta_de(raiz_proyecto, sid))
    except ValueError:
        return ""


# ------------------------------------------------------------- en el render

def extraer_fotogramas(clip, carpeta_salida, fps, cuantos):
    """Los fotogramas del clip a los fps del render, en JPEG. -> [rutas]

    Devuelve exactamente `cuantos`: si el clip es mas corto, el ultimo se
    repite (el plano se queda en su ultimo fotograma); si es mas largo, se
    corta. JPEG y no PNG: el navegador los decodifica igual de bien y se
    escriben cinco veces mas rapido.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    patron = os.path.join(carpeta_salida, "c%05d.jpg")
    proceso = subprocess.run(
        [medios.ffmpeg(), "-y", "-loglevel", "error", "-i", clip,
         "-vf", f"fps={int(fps)}", "-frames:v", str(int(cuantos)),
         "-q:v", "3", patron], capture_output=True, text=True, timeout=900)
    hechos = sorted(n for n in os.listdir(carpeta_salida)
                    if re.match(r"^c\d{5}\.jpg$", n))
    if proceso.returncode != 0 or not hechos:
        raise RuntimeError("ffmpeg no pudo sacar los fotogramas del clip: "
                           + (proceso.stderr or "").strip()[-300:])
    rutas = [os.path.join(carpeta_salida, n) for n in hechos]
    while len(rutas) < cuantos:
        rutas.append(rutas[-1])
    return rutas[:int(cuantos)]


# ------------------------------------------------------ el prompt de movimiento

def prompt_para_copiar(escena, formato=""):
    """Lo que se pega en Kling / Hailuo / Meta AI junto a la imagen del plano.

    Es un prompt de MOVIMIENTO, no de dibujo: la imagen ya dice como es todo,
    el prompt dice que se mueve. Corto, que esas webs cortan los largos.
    """
    vertical = str(formato or "").lower().startswith("vert")
    que = " ".join(str(escena.get("prompt") or escena.get("direccion")
                       or escena.get("accion") or "").split())
    if len(que) > 300:
        que = que[:300].rsplit(" ", 1)[0] + "…"
    partes = [
        "Anima esta imagen (image-to-video), "
        + ("vertical 9:16" if vertical else "horizontal 16:9") + ", 5 segundos.",
        f"ESCENA: {que}" if que else "",
        "MOVIMIENTO: los personajes se mueven con naturalidad (andan, gesticulan, "
        "giran la cabeza), la ropa y el pelo se mecen, el fuego, el agua y las "
        "nubes se mueven; cámara lenta y suave.",
        "Mantén el mismo estilo, colores y personajes de la imagen. Sin texto, "
        "sin cortes, sin cambios de escena.",
    ]
    return "\n".join(p for p in partes if p)


# ------------------------------------------------- el modo automatico (DE PAGO)

#: El modelo de fal.ai que se usaria. Kling 2.1 estandar, imagen a video, 5 s:
#: ~0,25-0,30 $ por clip (precio de fal.ai a nov-2026; mirar antes de activar).
FAL_MODELO = os.environ.get("ESTUDIO_FAL_MODELO_CLIP",
                            "fal-ai/kling-video/v2.1/standard/image-to-video")
COSTE_APROX_CLIP = 0.28


def automatico_disponible():
    """(True, "") si se puede pedir un clip pagando; (False, motivo) si no."""
    try:
        from . import ajustes
    except ImportError:
        import ajustes                    # type: ignore
    if ajustes.leer().get("modo_clip") != "auto":
        return False, ("el modo automático de clips está apagado (se activa en "
                       "Configuración y es de pago)")
    if not (os.environ.get("FAL_KEY") or "").strip():
        return False, "falta la clave de fal.ai (variable de entorno FAL_KEY)"
    return True, ""


def _fal(metodo, url, cuerpo=None, timeout=60):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(url, data=datos, method=metodo, headers={
        "Authorization": "Key " + os.environ["FAL_KEY"].strip(),
        "Content-Type": "application/json"})
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        return json.loads(respuesta.read().decode() or "{}")


def generar_automatico(raiz_proyecto, sid, escena, tamano="apaisado",
                       formato="", espera_max=600):
    """Pide el clip a fal.ai con la imagen subida del plano y lo guarda.

    APAGADO DE FABRICA: se niega (ValueError) sin `modo_clip = auto` y sin
    FAL_KEY, antes de tocar la red. Cuesta ~COSTE_APROX_CLIP $ por llamada.
    """
    listo, motivo = automatico_disponible()
    if not listo:
        raise ValueError(motivo)
    imagen = subidas.ruta_de(raiz_proyecto, sid)
    if not os.path.isfile(imagen):
        raise ValueError(f"{sid} no tiene imagen: el clip automático parte de ella")
    import base64
    with open(imagen, "rb") as fh:
        uri = "data:image/png;base64," + base64.b64encode(fh.read()).decode()
    cola = f"https://queue.fal.run/{FAL_MODELO}"
    pedido = _fal("POST", cola, {
        "prompt": prompt_para_copiar(escena, formato),
        "image_url": uri, "duration": "5",
        "aspect_ratio": "9:16" if tamano == "vertical" else "16:9"})
    estado_url = pedido.get("status_url")
    resultado_url = pedido.get("response_url")
    if not estado_url or not resultado_url:
        raise RuntimeError(f"fal.ai no acepto el pedido: {pedido}")
    limite = time.time() + espera_max
    while time.time() < limite:
        estado = _fal("GET", estado_url).get("status")
        if estado == "COMPLETED":
            break
        if estado not in ("IN_QUEUE", "IN_PROGRESS"):
            raise RuntimeError(f"fal.ai fallo con {sid}: {estado}")
        time.sleep(5)
    else:
        raise RuntimeError(f"fal.ai no termino {sid} en {espera_max} s")
    video = (_fal("GET", resultado_url).get("video") or {}).get("url")
    if not video:
        raise RuntimeError(f"fal.ai no devolvio video para {sid}")
    with urllib.request.urlopen(video, timeout=300) as respuesta:
        datos = respuesta.read()
    return guardar(raiz_proyecto, sid, datos, tamano, "auto.mp4")
