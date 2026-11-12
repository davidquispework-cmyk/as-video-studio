"""
LA VOZ GRATUITA: las voces neuronales de Microsoft Edge, sin clave y sin pagar.

QUE PROBLEMA RESUELVE
---------------------
La locucion con Cartesia se paga por caracter. Las voces neuronales que usa el
navegador Edge para «leer en voz alta» suenan muy naturales, hay decenas en
castellano (Peru, Mexico, Espana, Argentina, Colombia...) y, lo que de verdad
importa aqui, devuelven la MARCA DE TIEMPO DE CADA PALABRA: sin eso no habria
forma de sincronizar los planos, las cartelas ni los subtitulos con la voz.

Se llega a ellas con la biblioteca `edge-tts` (la misma conexion que usa el
navegador). No es un servicio con contrato: Microsoft podria cambiarlo, y por
eso Cartesia sigue entero detras del ajuste «De donde sale la voz».

COMO ENCAJA
-----------
`p4_voz` pide una toma y espera exactamente lo mismo que le da Cartesia: el wav
a 44,1 kHz mono y la lista de palabras con su inicio y su fin en segundos. Este
modulo da eso y nada mas, asi que todo lo de despues --secciones, aire entre
bloques, reparto de palabras, cortes de plano, subtitulos-- no se entera.

Las ANOTACIONES de voz del guion (`marcas_tts`) se traducen asi:
    <break time="900ms"/>   se respeta: se parte el texto ahi y se mete el
                            silencio (0,8x lo pedido, que es lo que Cartesia
                            anade de verdad: ver marcas_tts, punto 3)
    <spell>ABC</spell>      se locuta separando las letras
    speed, volume, emotion  se respetan POR FRASE (punto E): Edge no acepta
                            SSML propio, pero si rate/pitch/volume por peticion,
                            asi que se parte el texto en cada cambio y cada
                            trozo se graba con su prosodia (`intencion.prosodia`:
                            alegre, sereno, triste, tenso, firme...)
    «¿...? sigue» y «... sigue»  un respiro corto (`intencion.respiros`)

    voces(idioma)                  -> [ficha] en la forma del catalogo de p4_voz
    elegir(voz_id, idioma, defecto) -> ShortName de una voz gratuita
    toma(texto, voz, velocidad, sr, avisar) -> (pcm_s16le, duracion, palabras)
    muestra(voz, texto, destino)    -> ruta de un mp3 corto para escucharla
"""
import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

try:
    from . import intencion, marcas_tts
except ImportError:  # ejecutado con la carpeta pasos directamente en sys.path
    import intencion
    import marcas_tts

RAIZ_ESTUDIO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CACHE_VOCES = os.path.join(RAIZ_ESTUDIO, "cache", "voces_gratis.json")
DIAS_CACHE = 7

#: Una voz por idioma cuando no se ha elegido ninguna. Masculinas y neutras,
#: que es lo que pide un documental narrado; se cambian en Configuracion.
POR_IDIOMA = {
    "es": "es-MX-JorgeNeural",
    "en": "en-US-AndrewNeural",
    "pt": "pt-BR-AntonioNeural",
    "fr": "fr-FR-HenriNeural",
    "it": "it-IT-DiegoNeural",
    "de": "de-DE-ConradNeural",
}

#: Como se lee un nombre de voz de Edge: «es-PE-AlexNeural»,
#: «en-US-AndrewMultilingualNeural».
_ES_VOZ = re.compile(r"^[a-z]{2,3}-[A-Z]{2,}(?:-[A-Za-z]+)?-[A-Za-z]+Neural$")

#: La velocidad del estudio (slowest..fastest o un numero -1..1) en el
#: porcentaje que entiende Edge.
_VELOCIDAD = {"slowest": -30, "slow": -15, "normal": 0, "fast": 12, "fastest": 25}

PAISES = {
    "AR": "Argentina", "BO": "Bolivia", "CL": "Chile", "CO": "Colombia",
    "CR": "Costa Rica", "CU": "Cuba", "DO": "República Dominicana",
    "EC": "Ecuador", "ES": "España", "GQ": "Guinea Ecuatorial",
    "GT": "Guatemala", "HN": "Honduras", "MX": "México", "NI": "Nicaragua",
    "PA": "Panamá", "PE": "Perú", "PR": "Puerto Rico", "PY": "Paraguay",
    "SV": "El Salvador", "US": "Estados Unidos", "UY": "Uruguay",
    "VE": "Venezuela", "GB": "Reino Unido", "BR": "Brasil", "PT": "Portugal",
    "FR": "Francia", "IT": "Italia", "DE": "Alemania", "CA": "Canadá",
    "AU": "Australia", "IN": "India",
}

#: Cuantas peticiones a la vez cuando el guion trae pausas escritas y hay que
#: pedirlo en trozos. Mas no acelera y se arriesga a que corten.
A_LA_VEZ = 4


def es_voz_gratis(voz_id):
    """True si el id es el de una voz de Edge (y no un id de Cartesia)."""
    return bool(_ES_VOZ.match(str(voz_id or "").strip()))


def _edge():
    try:
        import edge_tts                                   # noqa: PLC0415
    except ImportError as fallo:
        raise RuntimeError(
            "falta la biblioteca de la voz gratuita (edge-tts). En el servidor: "
            "asvs actualizar, que instala lo que pide requirements.txt") from fallo
    return edge_tts


def _ffmpeg():
    puesto = (os.environ.get("ESTUDIO_FFMPEG") or "").strip().strip('"')
    if puesto and os.path.exists(puesto):
        return puesto
    encontrado = shutil.which("ffmpeg")
    if not encontrado:
        raise RuntimeError("no encuentro ffmpeg, y la voz gratuita lo necesita "
                           "para pasar el audio a wav")
    return encontrado


def _correr(corrutina):
    """Ejecuta una corrutina desde codigo normal (los pasos corren en hilos)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(corrutina)
    # dentro de un bucle ya en marcha (no deberia pasar): en un hilo aparte
    import concurrent.futures                               # noqa: PLC0415
    with concurrent.futures.ThreadPoolExecutor(1) as hilo:
        return hilo.submit(asyncio.run, corrutina).result()


# ------------------------------------------------------------------ catalogo

def _ficha(cruda):
    corto = cruda.get("ShortName") or ""
    locale = cruda.get("Locale") or ""
    partes = corto.split("-")
    nombre = partes[-1].replace("Neural", "") if partes else corto
    nombre = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", nombre)
    pais = PAISES.get(locale.split("-")[-1] if "-" in locale else "", "")
    genero = {"Male": "masculina", "Female": "femenina"}.get(cruda.get("Gender"), "")
    etiquetas = (cruda.get("VoiceTag") or {})
    estilo = ", ".join((etiquetas.get("VoicePersonalities") or [])[:4])
    uso = ", ".join((etiquetas.get("ContentCategories") or [])[:3])
    descripcion = "Voz " + " ".join(x for x in (genero, f"de {pais}" if pais else "")
                                    if x)
    if estilo:
        descripcion += f". Carácter: {estilo}"
    if uso:
        descripcion += f". Para: {uso}"
    return {
        "id": corto,
        "nombre": f"{nombre} ({pais or locale})" + (" · multilingüe"
                                                    if "Multilingual" in corto else ""),
        "descripcion": descripcion + " (voz gratuita)",
        "idioma": locale.split("-")[0].lower(),
        "genero": (cruda.get("Gender") or "").lower(),
        "pais": pais,
        "locales": [locale],
        "locales_nativos": [locale],
        "pro": False,
        "publica": True,
        "gratis": True,
    }


def _descargar():
    edge = _edge()
    crudas = _correr(edge.list_voices())
    return [_ficha(c) for c in crudas if c.get("ShortName")]


def voces(idioma=None, refrescar=False):
    """Catalogo de voces gratuitas, cacheado en disco una semana.

    Las MULTILINGUES de otro idioma tambien entran (leen castellano con buen
    acento), detras de las nativas.
    """
    fichas = None
    if not refrescar and os.path.exists(RUTA_CACHE_VOCES):
        try:
            if time.time() - os.path.getmtime(RUTA_CACHE_VOCES) < DIAS_CACHE * 86400:
                with open(RUTA_CACHE_VOCES, encoding="utf-8") as fh:
                    fichas = json.load(fh)
        except (OSError, ValueError):
            fichas = None
    if fichas is None:
        try:
            fichas = _descargar()
            os.makedirs(os.path.dirname(RUTA_CACHE_VOCES), exist_ok=True)
            temporal = RUTA_CACHE_VOCES + ".tmp"
            with open(temporal, "w", encoding="utf-8") as fh:
                json.dump(fichas, fh, ensure_ascii=False)
            os.replace(temporal, RUTA_CACHE_VOCES)
        except Exception:                                   # noqa: BLE001
            # sin red: lo que hubiera en disco, aunque este viejo, o lo minimo
            try:
                with open(RUTA_CACHE_VOCES, encoding="utf-8") as fh:
                    fichas = json.load(fh)
            except (OSError, ValueError):
                fichas = [_ficha({"ShortName": v, "Locale": "-".join(v.split("-")[:2]),
                                  "Gender": "Male"}) for v in POR_IDIOMA.values()]
    if not idioma:
        return [dict(f, nativa=True) for f in fichas]
    clave = str(idioma).strip().lower()
    nativas = [dict(f, nativa=True) for f in fichas if f["idioma"] == clave]
    otras = [dict(f, nativa=False) for f in fichas
             if f["idioma"] != clave and "Multilingual" in f["id"]]
    nativas.sort(key=lambda f: (f["pais"] != "Perú", f["pais"], f["nombre"]))
    return nativas + otras


def elegir(voz_id, idioma="es", defecto=""):
    """La voz gratuita que se usa. -> ShortName

    Manda la del video si es una voz gratuita de su idioma (o multilingue);
    si no --porque es un id de Cartesia, o de otro idioma--, la elegida en
    Configuracion si es de ese idioma, y si no la de fabrica del idioma.
    """
    clave = str(idioma or "es").strip().lower()

    def vale(voz):
        voz = str(voz or "").strip()
        return es_voz_gratis(voz) and (voz.lower().startswith(clave + "-")
                                       or "Multilingual" in voz)
    for candidata in (voz_id, defecto):
        if vale(candidata):
            return str(candidata).strip()
    return POR_IDIOMA.get(clave, POR_IDIOMA["en"] if clave != "es" else POR_IDIOMA["es"])


def porcentaje_velocidad(velocidad):
    """La velocidad del estudio -> «+12%» / «-15%» / «+0%»."""
    if isinstance(velocidad, (int, float)) and not isinstance(velocidad, bool):
        valor = int(round(max(-1.0, min(1.0, float(velocidad))) * 35))
    else:
        valor = _VELOCIDAD.get(str(velocidad or "normal").strip().lower(), 0)
    return f"{valor:+d}%"


# --------------------------------------------------------------------- toma

#: LA FRASE CLAVE (`<clave>`): la que pesa se dice MAS DESPACIO, un poco mas
#: baja y con un silencio delante. Medido en un video de referencia que
#: retiene muy bien (11-2026): narra a ~3,5 palabras/s y sus frases clave van
#: a 1,7-2,2 (un 40 % mas lentas), con 1-2 s de silencio antes del giro.
#: Medido con la voz de Microsoft de verdad: 25 puntos menos solo la frenaban
#: un 19 %; con 40 queda cerca de lo de la referencia. Y CADA TROZO YA TRAE
#: ~0,5 s de silencio al principio y al final (partir el texto lo mete solo),
#: asi que lo que se suma aqui es poco: con 0,9 s antes el hueco real era 2 s.
CLAVE_MENOS_VELOCIDAD = 40
CLAVE_PROSODIA = (-CLAVE_MENOS_VELOCIDAD, -2, -6)
PAUSA_ANTES_CLAVE = 0.5
PAUSA_DESPUES_CLAVE = 0.15
#: Lo que dice un personaje: el corte de trozo ya deja ~1 s de aire a cada
#: lado (medido), que es justo lo que hace notar que entra otra voz.
PAUSA_PERSONAJE = 0.0


def voz_de_personaje(nombre, genero, narrador):
    """La voz gratuita de un personaje. -> ShortName

    ESTABLE: sale del NOMBRE (no del orden en que aparece), asi regrabar un
    trozo suelto le da la misma voz que en la toma entera. Del mismo idioma que
    el narrador, distinta de la suya, del genero pedido (si no se dice, el del
    narrador) y nativa; primero las del mismo pais si hay mas de una.
    """
    narrador = str(narrador or "").strip()
    idioma = narrador.split("-")[0].lower() or "es"
    try:
        catalogo = [f for f in voces(idioma) if f.get("nativa", True)]
    except Exception:                                       # noqa: BLE001
        catalogo = []
    propio = next((f for f in catalogo if f["id"] == narrador), None)
    quiere = {"hombre": "male", "mujer": "female"}.get(str(genero or "").lower(),
                                                      (propio or {}).get("genero"))
    candidatas = [f for f in catalogo if f["id"] != narrador
                  and (not quiere or f.get("genero") == quiere)]
    if not candidatas:
        return narrador
    pais = narrador.split("-")[1] if narrador.count("-") >= 2 else ""
    mismas = [f for f in candidatas if f["id"].split("-")[1] == pais]
    lista = sorted(mismas if mismas else candidatas, key=lambda f: f["id"])
    clave = str(nombre or "").strip().lower()
    indice = int(hashlib.sha1(clave.encode("utf-8")).hexdigest(), 16) % len(lista)
    return lista[indice]["id"]


def _trozos(texto):
    """El texto anotado -> [[lo que se dice, silencio despues en s, prosodia]].

    prosodia = (speed, volume, emocion, matiz) en vigor para ese trozo; el
    matiz es el de la frase (`intencion.matiz`). Se parte en
    cada <break> (Edge no lo entiende y lo leeria en voz alta) y en cada cambio
    de speed/volume/emotion, que `marcas_tts.sanear` solo deja en frontera de
    frase. Y dentro de cada trozo, tras una pregunta o unos puntos suspensivos
    que siguen, un respiro (`intencion.respiros`).
    """
    estado = {"speed": 1.0, "volume": 1.0, "emotion": "neutral",
              "personaje": None, "clave": False}
    crudos = []                      # [texto crudo, silencio, prosodia]
    actual = []

    def cerrar(silencio=0.0):
        crudo = "".join(actual)
        actual.clear()
        crudos.append([crudo, silencio,
                       (estado["speed"], estado["volume"], estado["emotion"],
                        estado["personaje"], estado["clave"])])

    def silencio_antes(segundos):
        """Un silencio delante de lo que viene: se suma al trozo anterior."""
        cerrar(0.0)
        hecho = [c for c in crudos if marcas_tts.limpiar(c[0])]
        if hecho:
            hecho[-1][1] = max(hecho[-1][1], segundos)

    for clase, pieza in marcas_tts.trocear(str(texto or "")):
        if clase == "texto":
            actual.append(pieza)
        elif clase == "spell":
            # <spell>ABC</spell> -> «A B C»: separadas, Edge las deletrea
            actual.append(" " + " ".join(str(pieza).replace(" ", "")) + " ")
        elif clase == "break":
            cerrar(float(pieza) / 1000.0 * 0.8)
        elif clase in ("speed", "volume", "emotion"):
            # a mitad de frase se ignora (como en `marcas_tts.sanear`): partir
            # ahi sonaria a que entra otro locutor
            if "".join(actual).strip() and not marcas_tts._FIN_DE_FRASE.search(  # noqa: SLF001
                    "".join(actual)):
                continue
            cerrar(0.0)
            estado[clase] = pieza if clase == "emotion" else float(pieza)
        elif clase == "personaje":
            silencio_antes(PAUSA_PERSONAJE)
            estado["personaje"] = pieza          # (nombre, genero) o None
        elif clase == "clave":
            silencio_antes(PAUSA_ANTES_CLAVE if pieza else PAUSA_DESPUES_CLAVE)
            estado["clave"] = bool(pieza)
        # 'basura': fuera, se leeria en voz alta
    cerrar(0.0)

    limpios = []
    for crudo, silencio, tono in crudos:
        dicho = marcas_tts.limpiar(crudo)
        if not dicho:
            if limpios:
                limpios[-1][1] += silencio   # una pausa sin texto detras se suma
            continue
        partes = intencion.respiros(dicho)
        for indice, (trozo, respiro) in enumerate(partes):
            ultimo = indice == len(partes) - 1
            # y dentro, cada frase con su MATIZ (la pregunta sube, el remate
            # corto baja, la cita pesa): las seguidas con el mismo, juntas
            frases = intencion.frases_con_matiz(trozo)
            for k, (frase, matiz) in enumerate(frases):
                fin = k == len(frases) - 1
                limpios.append([frase, (silencio if ultimo else respiro) if fin else 0.0,
                                tono + (matiz,)])
    return limpios


async def _sintetizar_trozo(edge, texto, voz, velocidad, pitch="+0Hz", volumen="+0%"):
    def comunicar():
        return edge.Communicate(texto, voz, rate=velocidad, pitch=pitch,
                                volume=volumen, boundary="WordBoundary")
    audio = bytearray()
    palabras = []
    for intento in range(3):
        audio.clear()
        palabras.clear()
        try:
            async for trozo in comunicar().stream():
                if trozo["type"] == "audio":
                    audio.extend(trozo["data"])
                elif trozo["type"] == "WordBoundary":
                    ini = trozo["offset"] / 1e7
                    palabras.append({"w": trozo["text"], "s": round(ini, 3),
                                     "e": round(ini + trozo["duration"] / 1e7, 3)})
            break
        except Exception:                                   # noqa: BLE001
            if intento == 2:
                raise
            await asyncio.sleep(1.5 * (intento + 1))
    if not audio:
        raise RuntimeError("la voz gratuita devolvio un trozo sin audio")
    return bytes(audio), palabras


def _mp3_a_pcm(mp3, sr):
    proceso = subprocess.run(
        [_ffmpeg(), "-hide_banner", "-loglevel", "error", "-f", "mp3", "-i", "pipe:0",
         "-ac", "1", "-ar", str(sr), "-f", "s16le", "pipe:1"],
        input=mp3, capture_output=True, timeout=600)
    if proceso.returncode != 0 or not proceso.stdout:
        raise RuntimeError("ffmpeg no ha podido pasar la voz a wav: "
                           + proceso.stderr.decode("utf-8", "replace")[:300])
    return proceso.stdout


def toma(texto, voz, velocidad=None, sr=44100, avisar=None):
    """Una toma continua del texto anotado. -> (pcm_s16le, duracion, palabras)

    Los tiempos de las palabras son ABSOLUTOS en la toma entera, igual que los
    de Cartesia: se van sumando el audio y los silencios de cada trozo.
    """
    edge = _edge()
    avisa = avisar if callable(avisar) else (lambda *_a, **_k: None)
    trozos = _trozos(texto)
    if not trozos:
        raise ValueError("no hay texto que locutar")
    base = int(porcentaje_velocidad(velocidad).rstrip("%"))
    previstas = max(1, sum(len(t[0].split()) for t in trozos))

    async def todos():
        semaforo = asyncio.Semaphore(A_LA_VEZ)
        hechas = [0]

        async def uno(texto_trozo, tono):
            speed, volume, emocion, personaje, clave, matiz = tono
            if clave:
                matiz = tuple(a + b for a, b in zip(matiz, CLAVE_PROSODIA))
            rate, pitch, volumen = intencion.prosodia(base, speed, volume, emocion,
                                                      extra=matiz)
            quien = voz_de_personaje(*personaje, voz) if personaje else voz
            async with semaforo:
                resultado = await _sintetizar_trozo(edge, texto_trozo, quien, rate,
                                                    pitch, volumen)
                hechas[0] += len(texto_trozo.split())
                avisa(min(0.95, hechas[0] / previstas),
                      f"{hechas[0]} de ~{previstas} palabras (voz gratuita)")
                return resultado
        return await asyncio.gather(*(uno(t, tono) for t, _s, tono in trozos))

    resultados = _correr(todos())
    pcm = bytearray()
    palabras = []
    reloj = 0.0
    for (texto_trozo, silencio, _tono), (mp3, marcas) in zip(trozos, resultados):
        crudo = _mp3_a_pcm(mp3, sr)
        for marca in marcas:
            hablada = marcas_tts.texto_de_marca(marca["w"])
            if hablada is None:
                continue
            palabras.append({"w": hablada, "s": round(reloj + marca["s"], 3),
                             "e": round(reloj + marca["e"], 3)})
        pcm.extend(crudo)
        reloj += len(crudo) / (sr * 2)
        if silencio > 0:
            muestras = int(round(silencio * sr))
            pcm.extend(b"\x00\x00" * muestras)
            reloj += muestras / sr
    if not palabras:
        raise RuntimeError("la voz gratuita devolvio audio sin marcas de palabra: "
                           "sin marcas no se puede sincronizar el montaje")
    return bytes(pcm), len(pcm) / (sr * 2), palabras


def muestra(voz, destino, texto=None, velocidad=None):
    """Un mp3 corto con la voz, para escucharla en Configuracion. -> ruta"""
    if not es_voz_gratis(voz):
        raise ValueError(f"{voz!r} no es una voz gratuita")
    edge = _edge()
    texto = texto or ("Hola. Esta es la voz que narrará tus vídeos. Cuenta la "
                      "historia con calma, con claridad y sin prisa.")
    mp3, _marcas = _correr(_sintetizar_trozo(edge, texto, voz,
                                             porcentaje_velocidad(velocidad)))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "wb") as fh:
        fh.write(mp3)
    return destino
