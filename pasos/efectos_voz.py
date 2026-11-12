"""
Efectos sobre la VOZ de un video: mas grave, mas gruesa, misteriosa, de cine...

Para que
--------
David graba su voz (`voz_propia`) o usa la gratuita, y quiere que suene mas
grave o mas misteriosa, y poder variarlo. Aqui se le pasa un filtro de ffmpeg
a la toma YA ALINEADA: el tono se cambia SIN cambiar el tiempo, asi que cada
palabra sigue en su sitio y los subtitulos, los cortes y la camara cuadran
igual. Gratis y local, sin llamar a nadie.

Como se guarda
--------------
En `params.voz.voz_del_video.efecto` = {"estilo": "misteriosa", "tono": -4}
(tono en semitonos; None = el del estilo). Esa clave NO entra en ninguna firma
(`nucleo.estado.FUERA_DE_FIRMA`): cambiar el efecto solo pide «Regenerar
Audio», no deja obsoletas las imagenes.

El tono
-------
Con `rubberband` si el ffmpeg lo trae (suena mucho mejor: no hace voz de
robot) y si no con asetrate+atempo. Los dos conservan la duracion; aun asi el
resultado se recorta o se rellena a la longitud EXACTA de la entrada, porque
una muestra de mas o de menos desplazaria todas las marcas de palabra.
"""
import functools
import shutil
import subprocess

#: Los estilos. `tono` en semitonos (negativo = mas grave); `filtros`, la
#: cadena de ffmpeg que va DESPUES del cambio de tono. Todos acaban con un
#: limitador: subir graves satura si no.
ESTILOS = {
    "natural": {
        "nombre": "Natural", "tono": 0, "filtros": "",
        "descripcion": "tal cual, sin efecto"},
    "grave": {
        "nombre": "Más grave", "tono": -3,
        "filtros": "bass=g=4:f=110,acompressor=threshold=0.125:ratio=3:attack=10:release=200",
        "descripcion": "un poco más grave y con más cuerpo, sin que se note el truco"},
    "gruesa": {
        "nombre": "Gruesa y profunda", "tono": -5,
        "filtros": ("bass=g=6:f=100,equalizer=f=3200:t=q:w=1:g=-2,"
                    "acompressor=threshold=0.1:ratio=3.5:attack=8:release=180"),
        "descripcion": "voz de pecho, profunda; para historias serias"},
    "misteriosa": {
        "nombre": "Misteriosa", "tono": -4,
        "filtros": ("bass=g=4:f=110,lowpass=f=5000,"
                    "aecho=0.8:0.6:45|90:0.22|0.12,"
                    "acompressor=threshold=0.125:ratio=3:attack=10:release=250"),
        "descripcion": "grave, más apagada y con un poco de sala: suspense, misterio"},
    "cine": {
        "nombre": "Narrador de cine", "tono": -4,
        "filtros": ("bass=g=7:f=90,equalizer=f=2500:t=q:w=1:g=2,"
                    "acompressor=threshold=0.1:ratio=4:attack=5:release=150"),
        "descripcion": "la voz de un tráiler: grave, cercana y con presencia"},
    "cueva": {
        "nombre": "Eco de cueva", "tono": -2,
        "filtros": "bass=g=3:f=120,aecho=0.8:0.8:250|500:0.28|0.15",
        "descripcion": "con eco largo; para un momento, no para un vídeo entero"},
}

TONO_MIN, TONO_MAX = -8, 3


def _ffmpeg():
    ruta = shutil.which("ffmpeg")
    if not ruta:
        raise RuntimeError("falta ffmpeg para el efecto de voz")
    return ruta


@functools.lru_cache(maxsize=1)
def hay_rubberband():
    """Si el ffmpeg de esta maquina trae el filtro rubberband."""
    try:
        salida = subprocess.run([_ffmpeg(), "-hide_banner", "-filters"],
                                capture_output=True, text=True, timeout=30).stdout
    except Exception:                                       # noqa: BLE001
        return False
    return " rubberband " in salida


def normalizar(efecto):
    """{estilo, tono} valido, o None si no hay efecto que aplicar."""
    if not isinstance(efecto, dict):
        return None
    estilo = str(efecto.get("estilo") or "natural").strip().lower()
    if estilo not in ESTILOS:
        return None
    tono = efecto.get("tono")
    if tono in (None, ""):
        tono = ESTILOS[estilo]["tono"]
    try:
        tono = max(TONO_MIN, min(TONO_MAX, int(round(float(tono)))))
    except (TypeError, ValueError):
        tono = ESTILOS[estilo]["tono"]
    if estilo == "natural" and tono == 0:
        return None
    return {"estilo": estilo, "tono": tono}


def cadena(efecto, sr):
    """La cadena de filtros de ffmpeg para ese efecto, o "" si no hay."""
    puesto = normalizar(efecto)
    if not puesto:
        return ""
    partes = []
    if puesto["tono"]:
        factor = 2 ** (puesto["tono"] / 12.0)
        if hay_rubberband():
            partes.append(f"rubberband=pitch={factor:.5f}:pitchq=quality")
        else:
            partes.append(f"asetrate={int(round(sr * factor))},aresample={sr},"
                          f"atempo={1 / factor:.5f}")
    if ESTILOS[puesto["estilo"]]["filtros"]:
        partes.append(ESTILOS[puesto["estilo"]]["filtros"])
    partes.append("alimiter=limit=0.95")
    return ",".join(partes)


def aplicar(pcm, sr, efecto):
    """pcm s16le mono -> el mismo pcm con el efecto, de la MISMA longitud."""
    filtros = cadena(efecto, sr)
    if not filtros or not pcm:
        return pcm
    proceso = subprocess.run(
        [_ffmpeg(), "-hide_banner", "-loglevel", "error",
         "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0",
         "-af", filtros, "-f", "s16le", "-ar", str(sr), "-ac", "1", "pipe:1"],
        input=bytes(pcm), capture_output=True, timeout=1800)
    if proceso.returncode != 0 or not proceso.stdout:
        raise RuntimeError("no se ha podido aplicar el efecto de voz: "
                           + proceso.stderr.decode("utf-8", "replace")[:300])
    salida = proceso.stdout
    # la longitud EXACTA de la entrada: las marcas de palabra cuentan con ella
    if len(salida) < len(pcm):
        salida += b"\x00" * (len(pcm) - len(salida))
    return salida[:len(pcm)]


def catalogo():
    """Los estilos para la pantalla. -> [{id, nombre, descripcion, tono}]"""
    return [{"id": clave, "nombre": f["nombre"], "descripcion": f["descripcion"],
             "tono": f["tono"]} for clave, f in ESTILOS.items()]
