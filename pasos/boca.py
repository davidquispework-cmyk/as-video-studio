"""
LA BOCA SIGUE LA VOZ DE VERDAD (P7 del plan NIVEL PROFESIONAL, NOTAS-DAVID.md).

Saca del audio de la narracion (la voz gratuita, Cartesia o la GRABACION de
David) las formas de la boca a lo largo del tiempo, y el render se las da a los
muñecos: los de motion graphics (pasos/motion_mas.py) y las marionetas
(pasos/marioneta.py). Antes la boca se abria «una vez por silaba» con una
onda: imitaba hablar. Ahora se cierra en las pausas y se abre con cada golpe
de voz, en su sitio.

Dos caminos, el mismo resultado:

    rhubarb   Rhubarb Lip Sync (MIT, CPU, sin internet) con el reconocedor
              FONETICO, que no depende del idioma: sirve para el español.
              Da las formas de Preston Blair (A-H y X). Se busca en
              ESTUDIO_RHUBARB, en el PATH o en motores/rhubarb/.
    energia   sin Rhubarb: la fuerza de la voz en cada trozo de 1/30 s
              (cerrada en el silencio, entreabierta, abierta, muy abierta).
              Va siempre: solo pide numpy, que ya esta.

`ESTUDIO_BOCA=energia` fuerza el segundo; `ESTUDIO_BOCA=no` vuelve a la boca
de antes (la que imita).

Los tiempos salen en segundos del AUDIO, que son los mismos que los del VIDEO
(`escena["t_in"]`, `t_out`): el montaje corta el audio desde el t_in del
primer plano y el video tambien empieza ahi.

No es un param ni entra en ninguna firma: es lectura del audio al montar.
Basta «Regenerar Vídeo». El resultado se guarda en la carpeta de trabajo del
render por la huella del audio, asi que el segundo montaje no lo recalcula.
"""
import hashlib
import json
import os
import shutil
import subprocess
import wave

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

#: forma de Rhubarb -> (abertura 0..1, redonda 0..1)
FORMAS = {
    "X": (0.0, 0.0),    # en reposo, cerrada
    "A": (0.0, 0.0),    # cerrada apretada (m, b, p)
    "B": (0.3, 0.0),    # entreabierta, dientes (casi todas las consonantes)
    "C": (0.6, 0.0),    # abierta (e, a corta)
    "D": (1.0, 0.0),    # muy abierta (a)
    "E": (0.5, 0.6),    # redondeada (o)
    "F": (0.25, 1.0),   # labios en piquito (u, w)
    "G": (0.2, 0.0),    # dientes sobre el labio (f, v)
    "H": (0.45, 0.0),   # lengua arriba (l)
}

PASO = 1 / 30.0         # trozo del camino por energia


def modo():
    m = (os.environ.get("ESTUDIO_BOCA") or "").strip().lower()
    return m if m in ("no", "energia", "rhubarb") else "auto"


def rhubarb_ruta():
    """El ejecutable de Rhubarb, o None."""
    env = os.environ.get("ESTUDIO_RHUBARB")
    if env and os.path.isfile(env):
        return env
    en_path = shutil.which("rhubarb")
    if en_path:
        return en_path
    for nombre in ("rhubarb", "rhubarb.exe"):
        for carpeta in ("motores/rhubarb",):
            base = os.path.join(RAIZ, carpeta)
            directo = os.path.join(base, nombre)
            if os.path.isfile(directo):
                return directo
            # el zip oficial trae una carpeta «Rhubarb-Lip-Sync-1.x-Linux»
            if os.path.isdir(base):
                for sub in sorted(os.listdir(base)):
                    cand = os.path.join(base, sub, nombre)
                    if os.path.isfile(cand):
                        return cand
    return None


def _huella(ruta):
    h = hashlib.sha1()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest()[:16]


# -------------------------------------------------------------- los caminos

def _por_rhubarb(audio, exe):
    """[[t0, t1, forma]] con Rhubarb, o lanza."""
    largo = _duracion(audio)
    orden = [exe, "-q", "-f", "json", "-r", "phonetic",
             "--extendedShapes", "GHX", audio]
    r = subprocess.run(orden, capture_output=True, text=True,
                       timeout=max(120, int(largo * 3) + 60))
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "rhubarb fallo").strip()[-300:])
    datos = json.loads(r.stdout)
    return [[round(float(c["start"]), 3), round(float(c["end"]), 3), str(c["value"])]
            for c in datos.get("mouthCues", []) if str(c.get("value")) in FORMAS]


def _leer_wav(audio):
    """(muestras float mono, frecuencia). Solo PCM de 8/16/24/32 bits."""
    import numpy as np                                  # noqa: PLC0415
    with wave.open(audio, "rb") as w:
        canales, ancho, fr, n = (w.getnchannels(), w.getsampwidth(),
                                 w.getframerate(), w.getnframes())
        crudo = w.readframes(n)
    if ancho == 1:
        x = np.frombuffer(crudo, dtype=np.uint8).astype(np.float32) - 128.0
    elif ancho == 2:
        x = np.frombuffer(crudo, dtype="<i2").astype(np.float32)
    elif ancho == 3:
        b = np.frombuffer(crudo, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        x = np.where(v >= 1 << 23, v - (1 << 24), v).astype(np.float32)
    else:
        x = np.frombuffer(crudo, dtype="<i4").astype(np.float32)
    if canales > 1:
        x = x[: len(x) // canales * canales].reshape(-1, canales).mean(axis=1)
    return x, fr


def _duracion(audio):
    try:
        with wave.open(audio, "rb") as w:
            return w.getnframes() / float(w.getframerate() or 1)
    except Exception:
        return 300.0


def _por_energia(audio):
    """[[t0, t1, forma]] a partir de la fuerza de la voz."""
    import numpy as np                                  # noqa: PLC0415
    x, fr = _leer_wav(audio)
    paso = max(1, int(fr * PASO))
    n = len(x) // paso
    if n == 0:
        return []
    rms = np.sqrt((x[: n * paso].reshape(n, paso) ** 2).mean(axis=1))
    techo = float(np.percentile(rms, 95)) or 1.0
    suelo = float(np.percentile(rms, 20))
    v = np.clip((rms - suelo) / max(1e-9, techo - suelo), 0, 1)
    # suaviza un pelo: la boca no salta de cerrada a abierta en 1/30 s
    v = np.convolve(v, [0.25, 0.5, 0.25], mode="same")
    formas = []
    for k in range(n):
        f = "X" if v[k] < 0.1 else "B" if v[k] < 0.3 else "C" if v[k] < 0.6 else "D"
        formas.append(f)
    return _juntar([[k * PASO, (k + 1) * PASO, f] for k, f in enumerate(formas)])


def _juntar(tramos, minimo=0.05):
    """Une los tramos seguidos iguales y se come los de menos de `minimo`."""
    iguales = []
    for a, b, f in tramos:
        if iguales and iguales[-1][2] == f:
            iguales[-1][1] = b
        else:
            iguales.append([a, b, f])
    salida = []
    for a, b, f in iguales:
        if salida and (salida[-1][2] == f or b - a < minimo):
            salida[-1][1] = b
        else:
            salida.append([a, b, f])
    return [[round(a, 3), round(b, 3), f] for a, b, f in salida]


# ------------------------------------------------------------------ la API

def formas_de(audio, carpeta=None, avisar=print):
    """Las formas de la boca de TODO el audio: [[t0, t1, forma]] (o [])."""
    if modo() == "no" or not audio or not os.path.exists(audio):
        return []
    huella = _huella(audio)
    cache = os.path.join(carpeta, "boca.json") if carpeta else None
    if cache and os.path.exists(cache):
        try:
            with open(cache, encoding="utf-8") as f:
                guardado = json.load(f)
            if guardado.get("huella") == huella and guardado.get("modo") == modo():
                return guardado["formas"]
        except (OSError, ValueError, KeyError):
            pass
    formas, como = [], "energia"
    exe = rhubarb_ruta() if modo() in ("auto", "rhubarb") else None
    if exe:
        try:
            formas, como = _por_rhubarb(audio, exe), "rhubarb"
        except Exception as e:  # se dice y se sigue con la energia
            avisar(f"[boca] Rhubarb no pudo ({e}); va por la fuerza de la voz")
            formas = []
    if not formas:
        try:
            formas, como = _por_energia(audio), "energia"
        except Exception as e:
            avisar(f"[boca] sin boca de verdad ({e}); la boca imita como antes")
            return []
    avisar(f"[boca] {len(formas)} formas de boca ({como})")
    if cache:
        try:
            os.makedirs(carpeta, exist_ok=True)
            with open(cache, "w", encoding="utf-8") as f:
                json.dump({"huella": huella, "modo": modo(), "como": como,
                           "formas": formas}, f)
        except OSError:
            pass
    return formas


def tramo(formas, a, b, desde=0.0):
    """Las formas entre a y b como [[t, abertura, redonda]] (t menos `desde`).

    Un punto en cada cambio de forma; la pagina interpola entre puntos."""
    salida = []
    for t0, t1, f in formas or []:
        if t1 <= a or t0 >= b:
            continue
        ab, re = FORMAS.get(f, (0.0, 0.0))
        salida.append([round(max(t0, a) - desde, 3), ab, re])
    if salida:
        salida.append([round(b - desde, 3), 0.0, 0.0])
    return salida


def aplicar_motion(confs, formas):
    """Pone la boca de verdad en los muñecos de motion graphics. -> cuantos"""
    if not formas:
        return 0
    n = 0
    for conf in (confs or {}).values():
        for pz in _piezas(conf):
            if pz.get("tipo") != "personajes":
                continue
            for f in pz.get("figuras") or []:
                if f.get("habla"):
                    a = min(h[0] for h in f["habla"])
                    b = max(h[1] for h in f["habla"])
                    f["boca"] = tramo(formas, a, b)
                    n += 1
    return n


def _piezas(conf):
    return (conf or {}).get("piezas") or [] if isinstance(conf, dict) else []


def aplicar_marioneta(conf, formas, escena):
    """Pone la boca de verdad en las marionetas de un plano (tiempo del plano)."""
    if not conf or not formas:
        return conf
    a = float(escena.get("t_in") or 0.0)
    b = float(escena.get("t_out") or a)
    boca = tramo(formas, a, b, desde=a)
    if boca:
        conf["boca"] = boca
    return conf
