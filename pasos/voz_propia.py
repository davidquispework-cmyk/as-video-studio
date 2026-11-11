"""
LA VOZ GRABADA DE DAVID (punto 5 del orden nuevo, 11-nov-2026).

QUE PROBLEMA RESUELVE
---------------------
Las voces sinteticas (gratis o Cartesia) suenan bien, pero un canal con la voz
de su dueno conecta mas. Asi que un video puede llevar, EN LUGAR de la voz
sintetica, una grabacion propia: se lee el guion en el movil (o en el PC), se
sube el fichero y el estudio lo usa como la voz del video. Todo lo demas sigue
igual: subtitulos palabra a palabra, cortes de plano, cartelas, camara.

DONDE VIVE
----------
`<proyecto>/subidas/voz/grabacion.wav`, fuera de las carpetas versionadas de los
pasos (igual que las imagenes y los clips subidos). Se guarda ya LIMPIA: mono,
44,1 kHz, sin graves de ruido (filtro de 80 Hz) y con el volumen igualado al de
las voces del estudio (loudnorm a -16 LUFS).

COMO ENTRA EN EL GRAFO, SIN MOVER FIRMAS DE NADIE MAS
---------------------------------------------------
Al SUBIRLA, los params de `voz` reciben `grabacion` = su huella (y al quitarla
se borra la clave). Es una edicion de alguien, no un valor «por defecto»: la
firma de la voz se mueve -- y tiene que moverse, la voz ha cambiado -- y los
videos que no la usan no se enteran. Con `grabacion` en los params,
`p4_voz.resolver_params` pone `motor_voz = "propia"` y la toma sale de aqui en
vez de un sintetizador. No llama a nadie: gratis.

LOS TIEMPOS DE CADA PALABRA (`alinear`)
---------------------------------------
Los subtitulos y los cortes de plano necesitan saber cuando se dice cada
palabra. Un sintetizador lo devuelve; una grabacion no. En el VPS no hay GPU ni
reconocedor de voz, asi que se alinea con lo que SI se sabe:

  1. Se mide la energia del audio cada 10 ms y se encuentran los SILENCIOS.
  2. Las pausas del texto se puntuan: un punto o una interrogacion piden pausa
     larga, una coma una corta, entre dos palabras casi ninguna.
  3. Se emparejan silencios con pausas del texto (programacion dinamica,
     monotona): un silencio largo cerca de donde «toca» un punto se ancla ahi.
  4. Entre dos anclas, las palabras se reparten por el tiempo HABLADO segun
     sus silabas.

Con una lectura normal del guion, cada frase empieza y acaba donde de verdad
empieza y acaba, y dentro de la frase el error es de una o dos palabras. Si se
improvisa mucho, los tiempos se van; por eso la pantalla dice «lee el guion tal
cual» y da el texto para copiarlo.
"""

import hashlib
import os
import re
import shutil
import subprocess
import wave

#: Lo que se acepta subir (lo que graba un movil o un PC).
EXTENSIONES = (".mp3", ".m4a", ".aac", ".wav", ".ogg", ".oga", ".opus", ".webm",
               ".flac", ".amr", ".3gp", ".mp4", ".mov", ".wma")

#: Tope del fichero subido (una hora de m4a son ~60 MB; un wav, mas).
MAX_BYTES = 400 * 1024 * 1024

#: Lo mas largo que se acepta (segundos).
MAX_SEGUNDOS = 45 * 60

#: Lo mas corto: menos que esto no es una locucion.
MIN_SEGUNDOS = 1.0

SR = 44100
NOMBRE = "grabacion.wav"

# El analisis
_PASO = 0.01             # 10 ms por trama
_RELLENO = 0.12          # un hueco mas corto que esto es la oclusiva de una p/t/k
_MIN_VOZ = 0.05          # un chasquido no es voz
_MIN_SILENCIO = 0.15     # lo mas corto que cuenta como pausa
_VOCALES = re.compile(r"[aeiouáéíóúüy]+", re.IGNORECASE)


def carpeta(raiz_proyecto):
    return os.path.join(raiz_proyecto, "subidas", "voz")


def ruta(raiz_proyecto):
    return os.path.join(carpeta(raiz_proyecto), NOMBRE)


def existe(raiz_proyecto):
    return os.path.isfile(ruta(raiz_proyecto))


def _ffmpeg():
    puesto = (os.environ.get("ESTUDIO_FFMPEG") or "").strip().strip('"')
    if puesto and os.path.exists(puesto):
        return puesto
    encontrado = shutil.which("ffmpeg")
    if not encontrado:
        raise RuntimeError("no encuentro ffmpeg, y hace falta para leer la grabacion")
    return encontrado


def huella(raiz_proyecto):
    """Huella corta del fichero guardado, o '' si no hay."""
    destino = ruta(raiz_proyecto)
    if not os.path.isfile(destino):
        return ""
    sha = hashlib.sha1()
    with open(destino, "rb") as fh:
        for trozo in iter(lambda: fh.read(1 << 20), b""):
            sha.update(trozo)
    return sha.hexdigest()[:16]


def duracion(raiz_proyecto):
    destino = ruta(raiz_proyecto)
    if not os.path.isfile(destino):
        return 0.0
    with wave.open(destino, "rb") as wav:
        return wav.getnframes() / float(wav.getframerate() or SR)


def a_pcm(origen, sr=SR, limpiar=False):
    """Cualquier audio -> PCM s16le mono a `sr`. `limpiar` filtra y nivela."""
    filtros = ["-af", "highpass=f=80,loudnorm=I=-16:TP=-1.5:LRA=11"] if limpiar else []
    proceso = subprocess.run(
        [_ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", origen, "-vn",
         *filtros, "-ac", "1", "-ar", str(sr), "-f", "s16le", "pipe:1"],
        capture_output=True, timeout=900)
    if proceso.returncode != 0 or not proceso.stdout:
        raise ValueError("no he podido leer ese audio: "
                         + proceso.stderr.decode("utf-8", "replace")[-300:].strip())
    return proceso.stdout


def guardar(raiz_proyecto, datos, nombre="grabacion.m4a"):
    """Guarda la grabacion subida, ya limpia. -> {duracion, huella}"""
    extension = os.path.splitext(str(nombre or "").lower())[1]
    if extension and extension not in EXTENSIONES:
        raise ValueError(f"«{extension}» no es un audio que entienda; sube "
                         f"mp3, m4a, wav, ogg u opus")
    if not datos:
        raise ValueError("el fichero llego vacio")
    if len(datos) > MAX_BYTES:
        raise ValueError("la grabacion pesa demasiado (maximo 400 MB)")
    os.makedirs(carpeta(raiz_proyecto), exist_ok=True)
    temporal = os.path.join(carpeta(raiz_proyecto), "_subida" + (extension or ".bin"))
    with open(temporal, "wb") as fh:
        fh.write(datos)
    try:
        pcm = a_pcm(temporal, SR, limpiar=True)
    finally:
        try:
            os.remove(temporal)
        except OSError:
            pass
    segundos = len(pcm) / (SR * 2)
    if segundos < MIN_SEGUNDOS:
        raise ValueError("la grabacion dura menos de un segundo")
    if segundos > MAX_SEGUNDOS:
        raise ValueError("la grabacion dura mas de 45 minutos")
    nuevo = ruta(raiz_proyecto) + ".tmp"
    with wave.open(nuevo, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(pcm)
    os.replace(nuevo, ruta(raiz_proyecto))
    return {"duracion": round(segundos, 2), "huella": huella(raiz_proyecto)}


def borrar(raiz_proyecto):
    try:
        os.remove(ruta(raiz_proyecto))
    except FileNotFoundError:
        pass


# ------------------------------------------------------------- el alineado

def _silabas(palabra):
    limpia = re.sub(r"[^\wáéíóúüñ]", "", palabra.lower())
    if limpia.isdigit():
        return max(1.0, 1.5 * len(limpia))
    return float(max(1, len(_VOCALES.findall(limpia))))


def _pausa_pedida(palabra):
    """Cuanto pide el texto parar DESPUES de esta palabra (0-1)."""
    final = palabra.rstrip()[-1:] if palabra.strip() else ""
    if palabra.rstrip().endswith(("...", "…")):
        return 1.0
    return {".": 1.0, "?": 1.0, "!": 1.0, ";": 0.75, ":": 0.7, ",": 0.5,
            ")": 0.4, "»": 0.4, '"': 0.3, "—": 0.5, "-": 0.3}.get(final, 0.08)


def _tramos_de_voz(pcm, sr):
    """-> lista de (inicio, fin) en segundos de lo que suena a voz."""
    import numpy as np                                     # noqa: PLC0415
    muestras = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
    trama = max(1, int(sr * _PASO))
    cuantas = len(muestras) // trama
    if cuantas < 3:
        return []
    bloques = muestras[:cuantas * trama].reshape(cuantas, trama)
    db = 10 * np.log10(np.mean(bloques * bloques, axis=1) + 1e-10)
    suelo = float(np.percentile(db, 10))
    voz = float(np.percentile(db, 90))
    umbral = max(suelo + 6.0, suelo + 0.35 * (voz - suelo))
    activo = db > umbral

    tramos, dentro, inicio = [], False, 0
    for i, sonando in enumerate(activo):
        if sonando and not dentro:
            dentro, inicio = True, i
        elif not sonando and dentro:
            dentro = False
            tramos.append([inicio * _PASO, i * _PASO])
    if dentro:
        tramos.append([inicio * _PASO, cuantas * _PASO])
    # los huecos de una oclusiva se rellenan; los chasquidos se tiran
    unidos = []
    for tramo in tramos:
        if unidos and tramo[0] - unidos[-1][1] < _RELLENO:
            unidos[-1][1] = tramo[1]
        else:
            unidos.append(tramo)
    return [(a, b) for a, b in unidos if b - a >= _MIN_VOZ]


def _emparejar(silencios, f_sil, huecos, f_hue):
    """Silencios con huecos del texto: emparejamiento monotono de maxima nota.

    -> lista de (indice_silencio, indice_hueco)."""
    m, n = len(silencios), len(huecos)
    if not m or not n:
        return []

    def nota(j, i):
        lejos = abs(f_sil[j] - f_hue[i])
        if lejos > 0.12:
            return 0.0
        largo = min(1.0, (silencios[j][1] - silencios[j][0]) / 0.45)
        valor = largo * (0.25 + huecos[i]) - 6.0 * lejos
        return valor if valor > 0.02 else 0.0

    # tabla de (m+1) x (n+1), con la jugada para volver atras
    previa = [0.0] * (n + 1)
    jugadas = []
    for j in range(m):
        fila = [0.0] * (n + 1)
        jug = bytearray(n + 1)
        for i in range(n):
            mejor, de = previa[i + 1], 1             # saltarse el silencio
            if fila[i] > mejor:
                mejor, de = fila[i], 2               # saltarse el hueco
            s = nota(j, i)
            if s and previa[i] + s > mejor:
                mejor, de = previa[i] + s, 3         # emparejar
            fila[i + 1] = mejor
            jug[i + 1] = de
        jugadas.append(jug)
        previa = fila
    pares, j, i = [], m, n
    while j > 0 and i > 0:
        de = jugadas[j - 1][i]
        if de == 3:
            pares.append((j - 1, i - 1))
            j, i = j - 1, i - 1
        elif de == 2:
            i -= 1
        else:
            j -= 1
    return pares[::-1]


def _repartir(palabras, pesos, t0, t1, tramos):
    """Reparte palabras entre t0 y t1 por el tiempo HABLADO -> [(s, e)]."""
    trozos = [(max(a, t0), min(b, t1)) for a, b in tramos if b > t0 and a < t1]
    trozos = [(a, b) for a, b in trozos if b - a > 0.005]
    if not trozos:
        trozos = [(t0, max(t1, t0 + 0.05 * len(palabras)))]
    hablado = sum(b - a for a, b in trozos)
    total = sum(pesos) or 1.0

    def real(u, de_inicio):
        acumulado = 0.0
        for a, b in trozos:
            largo = b - a
            if (u < acumulado + largo) if de_inicio else (u <= acumulado + largo):
                return a + (u - acumulado)
            acumulado += largo
        return trozos[-1][1]

    tiempos, cuenta = [], 0.0
    for peso in pesos:
        u0 = hablado * cuenta / total
        cuenta += peso
        u1 = hablado * cuenta / total
        s, e = real(u0, True), real(u1, False)
        tiempos.append((s, max(e, s + 0.04)))
    return tiempos


def alinear(pcm, sr, texto):
    """Tiempos de cada palabra del texto en la grabacion.

    -> lista de {"w", "s", "e"} (segundos absolutos), en el orden del texto.
    """
    palabras = [p for p in str(texto or "").split() if p.strip()]
    if not palabras:
        return []
    total = len(pcm) / (sr * 2)
    tramos = _tramos_de_voz(pcm, sr)
    if not tramos:
        tramos = [(0.0, total)]
    inicio, fin = tramos[0][0], tramos[-1][1]
    silencios = [(tramos[k][1], tramos[k + 1][0]) for k in range(len(tramos) - 1)
                 if tramos[k + 1][0] - tramos[k][1] >= _MIN_SILENCIO]

    pesos = [_silabas(p) for p in palabras]
    total_pesos = sum(pesos)
    hablado = sum(b - a for a, b in tramos) or 1.0

    def fraccion_hablada(t):
        return sum(max(0.0, min(b, t) - a) for a, b in tramos if a < t) / hablado

    f_sil = [fraccion_hablada(a) for a, _b in silencios]
    huecos, f_hue, cuenta = [], [], 0.0
    for k, palabra in enumerate(palabras[:-1]):
        cuenta += pesos[k]
        huecos.append(_pausa_pedida(palabra))
        f_hue.append(cuenta / total_pesos)

    anclas = _emparejar(silencios, f_sil, huecos, f_hue)
    # tramos: [palabra_desde, palabra_hasta), t0, t1
    cortes = [(0, inicio)]
    for j, i in anclas:
        cortes.append((i + 1, silencios[j][1], silencios[j][0]))
    resultado = []
    desde, t0 = 0, inicio
    for corte in cortes[1:] + [(len(palabras), None, fin)]:
        hasta, siguiente_t0, t1 = corte
        if hasta > desde:
            for palabra, (s, e) in zip(palabras[desde:hasta],
                                       _repartir(palabras[desde:hasta],
                                                 pesos[desde:hasta], t0, t1, tramos)):
                resultado.append({"w": palabra, "s": round(s, 3), "e": round(e, 3)})
        desde = hasta
        t0 = siguiente_t0 if siguiente_t0 is not None else t1
    # monotonas sin solaparse
    for k in range(1, len(resultado)):
        if resultado[k]["s"] < resultado[k - 1]["e"]:
            resultado[k - 1]["e"] = max(resultado[k - 1]["s"] + 0.02, resultado[k]["s"])
        if resultado[k]["s"] < resultado[k - 1]["s"]:
            resultado[k]["s"] = resultado[k - 1]["e"]
            resultado[k]["e"] = max(resultado[k]["e"], resultado[k]["s"] + 0.04)
    return resultado


def toma(raiz_o_ruta, texto, sr=SR, avisar=None):
    """La toma de la grabacion -> (pcm_s16le, duracion, palabras).

    Misma forma que `voz_gratis.toma`, para que `p4_voz` no tenga que saber de
    donde viene el audio.
    """
    avisa = avisar if callable(avisar) else (lambda *_a, **_k: None)
    origen = raiz_o_ruta if str(raiz_o_ruta).lower().endswith(".wav") else ruta(raiz_o_ruta)
    if not os.path.isfile(origen):
        raise RuntimeError("este video no tiene grabacion propia subida")
    avisa(0.1, "leyendo tu grabacion")
    pcm = a_pcm(origen, sr)
    avisa(0.5, "buscando donde dices cada palabra")
    palabras = alinear(pcm, sr, texto)
    if not palabras:
        raise RuntimeError("el guion no tiene palabras que alinear con la grabacion")
    segundos = len(pcm) / (sr * 2)
    ritmo = len(palabras) / max(0.1, segundos)
    if ritmo < 0.8 or ritmo > 5.0:
        avisa(0.9, f"AVISO: la grabacion dura {segundos:.0f}s para {len(palabras)} "
                   f"palabras; ¿es la del guion de este video?")
    return pcm, segundos, palabras
