"""
Prueba de la VOZ GRATUITA (voces neuronales de Microsoft Edge).

No sale a la red: el servicio de Microsoft se dobla con un tono de ffmpeg y unas
marcas de palabra a cadencia fija, asi que la suite comprueba NUESTRO codigo
--como se parte el guion, como se cosen los trozos, que tiempos salen, como se
elige la voz-- y no el humor del servicio ese dia.

  1. las piezas: que es una voz gratuita, la velocidad en porcentaje, que voz
     se elige segun el video, Configuracion y el idioma;
  2. el guion anotado se parte en cada <break> y mete su silencio; <spell>
     se deletrea; speed/volume/emotion no se locutan;
  3. una toma: tiempos ABSOLUTOS y crecientes, la duracion cuadra con el wav;
  4. el paso de voz entero (`p4_voz.sintetizar_bloques`) con la voz gratuita:
     bloques con su tramo, aire entre bloques, resumen, y Cartesia sin tocar;
  5. el modo se cambia en ajustes y manda: con Cartesia puesto no se usa.

    python pasos/prueba_voz_gratis.py
"""
import asyncio
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "pasos"))

CARPETA = os.path.join(tempfile.gettempdir(), "estudio_prueba_voz_gratis")
if os.path.isdir(CARPETA):
    shutil.rmtree(CARPETA)
os.makedirs(CARPETA)
os.environ["ESTUDIO_AJUSTES"] = os.path.join(CARPETA, "ajustes.json")
os.environ["ESTUDIO_ESTADISTICAS"] = os.path.join(CARPETA, "estadisticas.json")
os.environ.pop("ESTUDIO_SIMULAR", None)

import ajustes  # noqa: E402
import p4_voz  # noqa: E402
import marcas_tts  # noqa: E402
import voz_gratis  # noqa: E402

_fallos = []
_comprobaciones = [0]


def ok(condicion, mensaje):
    _comprobaciones[0] += 1
    if not condicion:
        _fallos.append(mensaje)
        print(f"    FALLO: {mensaje}")
    else:
        print(f"  ok   {mensaje}")
    return bool(condicion)


def igual(obtenido, esperado, mensaje):
    return ok(obtenido == esperado,
              f"{mensaje} (obtenido {obtenido!r}, esperado {esperado!r})")


# ------------------------------------------------- el doble del servicio

PASO_S = 0.3          # cada palabra dura 0,3 s en el doble
PEDIDOS = []          # (texto, voz, velocidad) que ha recibido el «servicio»
PROSODIAS = []        # (texto, velocidad, tono, volumen): el punto E


async def _doble(edge, texto, voz, velocidad, pitch="+0Hz", volumen="+0%"):
    """Lo que devolveria Edge: un mp3 del largo justo y una marca por palabra."""
    PEDIDOS.append((texto, voz, velocidad))
    PROSODIAS.append((texto, velocidad, pitch, volumen))
    palabras = texto.split()
    duracion = max(0.2, len(palabras) * PASO_S + 0.1)
    mp3 = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
         f"sine=frequency=220:duration={duracion}", "-ac", "1", "-ar", "24000",
         "-f", "mp3", "pipe:1"], capture_output=True, check=True).stdout
    marcas = [{"w": p.strip(".,;:¿?¡!«»"), "s": round(0.05 + i * PASO_S, 3),
               "e": round(0.05 + i * PASO_S + PASO_S * 0.8, 3)}
              for i, p in enumerate(palabras)]
    return mp3, marcas


voz_gratis._sintetizar_trozo = _doble          # noqa: SLF001
voz_gratis._edge = lambda: None                 # noqa: SLF001


def probar_piezas():
    print("\n  LAS PIEZAS")
    for voz, es in (("es-PE-AlexNeural", True), ("en-US-AndrewMultilingualNeural", True),
                    ("es-MX-JorgeNeural", True),
                    ("a0e99841-438c-4a64-b679-ae501e7d6091", False), ("", False),
                    ("Alex", False)):
        igual(voz_gratis.es_voz_gratis(voz), es, f"«{voz}» {'es' if es else 'no es'} voz gratuita")
    igual(voz_gratis.porcentaje_velocidad("slow"), "-15%", "slow es un 15 % mas lenta")
    igual(voz_gratis.porcentaje_velocidad(None), "+0%", "sin velocidad, normal")
    igual(voz_gratis.porcentaje_velocidad(1.0), "+35%", "el tope numerico")
    igual(voz_gratis.porcentaje_velocidad(-2), "-35%", "y se acota")
    igual(voz_gratis.elegir("es-PE-CamilaNeural", "es", "es-ES-AlvaroNeural"),
          "es-PE-CamilaNeural", "manda la voz gratuita del video")
    igual(voz_gratis.elegir("a0e99841-uuid", "es", "es-ES-AlvaroNeural"),
          "es-ES-AlvaroNeural", "un id de Cartesia cae a la de Configuracion")
    igual(voz_gratis.elegir("a0e99841-uuid", "es", ""), "es-MX-JorgeNeural",
          "y sin ninguna, a la de fabrica del idioma")
    igual(voz_gratis.elegir("es-PE-AlexNeural", "en", ""), "en-US-AndrewNeural",
          "una voz de otro idioma no narra este")
    igual(voz_gratis.elegir("en-US-AndrewMultilingualNeural", "es", ""),
          "en-US-AndrewMultilingualNeural", "salvo que sea multilingue")


def probar_trozos():
    print("\n  EL GUION ANOTADO")
    trozos = voz_gratis._trozos(                                # noqa: SLF001
        'Uno dos. <break time="1s"/> Tres <speed ratio="0.8"/>cuatro. '
        '<break time="500ms"/><break time="500ms"/> La <spell>ONU</spell> habla.'
        '<emotion value="sad"/>')
    igual([t[0] for t in trozos], ["Uno dos.", "Tres cuatro.", "La O N U habla."],
          "se parte en cada pausa y no se locuta ninguna etiqueta")
    igual([round(t[1], 2) for t in trozos], [0.8, 0.8, 0.0],
          "cada pausa mete 0,8x lo pedido, y dos seguidas se suman")
    igual(voz_gratis._trozos("<break time=\"1s\"/>"), [],        # noqa: SLF001
          "una pausa sin texto no deja nada que locutar")


def probar_intencion():
    """El punto E: el tono por frase, los respiros y la neutralidad por bloque."""
    import intencion  # noqa: PLC0415
    print("\n  EL TONO Y LAS PAUSAS (punto E)")
    trozos = voz_gratis._trozos(                                # noqa: SLF001
        '<emotion value="neutral"/>¿Sabías que Pedro lloró? Lo negó tres veces.'
        '<break time="900ms"/><emotion value="sad"/><speed ratio="0.9"/>Y lloró '
        'amargamente... Nadie lo vio.<speed ratio="1"/>')
    igual([t[0] for t in trozos],
          ["¿Sabías que Pedro lloró?", "Lo negó tres veces.", "Y lloró amargamente...",
           "Nadie lo vio."], "se parte tras la pregunta, la pausa y los puntos suspensivos")
    igual([round(t[1], 2) for t in trozos], [0.32, 0.72, 0.28, 0.0],
          "un respiro tras la pregunta y el suspense; la pausa pedida, a 0,8x")
    igual([t[2][2] for t in trozos], ["neutral", "neutral", "sad", "sad"],
          "el tono cambia en la frontera de frase")
    igual(voz_gratis._trozos('Pedro <emotion value="sad"/>lloró.')[0][2][2],  # noqa: SLF001
          "neutral", "un cambio de tono a mitad de frase se ignora")
    igual(intencion.prosodia(-15, 0.9, 1.0, "sad"), ("-43%", "-12Hz", "-12%"),
          "triste: más lenta, más grave y más baja, sobre la velocidad de la voz")
    igual(intencion.prosodia(0, 1, 1, "content"), ("+9%", "+10Hz", "+6%"),
          "alegre: algo más viva y más aguda")
    igual(intencion.prosodia(0), ("+0%", "+0Hz", "+0%"), "neutro: como siempre")

    PROSODIAS.clear()
    voz_gratis.toma('<emotion value="content"/>Era la mejor noticia de toda su vida. '
                    '<emotion value="scared"/>Pero de noche llegaron los soldados del templo. '
                    '¿Qué iban a hacer?', "es-PE-AlexNeural", None, sr=44100)
    igual([(p[2], p[3]) for p in PROSODIAS], [("+10Hz", "+6%"), ("+4Hz", "-16%"),
                                              ("+10Hz", "-16%")],
          "cada frase se graba con la prosodia de su tono, y la pregunta sube")
    igual(intencion.matiz("Y lloró."), (-9, -3, 3), "el remate corto, despacio")
    igual(intencion.tono_automatico("Jesús murió en la cruz y lloraron."), "sad",
          "sin etiqueta, el tono sale de lo que cuenta: muerte -> triste")
    igual(intencion.tono_automatico("Al tercer día resucitó: un milagro."), "content",
          "resurrección -> alegre")
    igual(intencion.tono_automatico("Era pescador en Galilea."), "neutral",
          "sin pistas, neutro")

    igual(intencion.tono_de('<emotion value="sad"/>Hola.'), "sad", "el tono del bloque")
    igual(intencion.tono_de('Hola.'), "auto", "sin etiqueta, automático")
    igual(intencion.con_tono('<emotion value="sad"/>Hola.', "calm"),
          '<emotion value="calm"/>Hola.', "cambiar el tono de un bloque")
    igual(intencion.con_tono('<emotion value="sad"/>Hola.', "auto"), "Hola.",
          "automático quita la etiqueta")
    igual(intencion.con_tono('Hola.', "neutral"), '<emotion value="neutral"/>Hola.',
          "neutro a propósito se escribe")
    bloques = [{"id": "B001", "texto": '<emotion value="sad"/>Murió.'},
               {"id": "B002", "texto": "Al tercer día resucitó."}]
    igual(p4_voz.unir_bloques(bloques, {"motor_voz": "gratis"}),
          '<emotion value="sad"/>Murió. <emotion value="content"/>Al tercer día resucitó.',
          "con la voz gratuita cada bloque empieza con SU tono (automático si no trae)")
    igual(p4_voz.unir_bloques(bloques, {"motor_voz": "cartesia"}),
          '<emotion value="sad"/>Murió. Al tercer día resucitó.',
          "y Cartesia recibe el texto de siempre")

    print("\n  EL GUION SIN MULETILLAS Y CON RITMO (punto E)")
    for crudo, limpio in (
            ("Bueno, Pedro negó. O sea, lo negó tres veces.", "Pedro negó. Lo negó tres veces."),
            ("Era, básicamente, un pescador.", "Era un pescador."),
            ("O sea que no fue así.", "Así que no fue así."),
            ("La verdad es que nadie lo sabía.", "Nadie lo sabía."),
            ('Fin.<break time="900ms"/>Pues, entonces vino.',
             'Fin.<break time="900ms"/>Entonces vino.'),
            ("Oye, Israel: Jehová nuestro Dios, Jehová uno es.",
             "Oye, Israel: Jehová nuestro Dios, Jehová uno es."),
            ("Este, a su vez, fue rey.", "Este, a su vez, fue rey.")):
        igual(intencion.quitar_muletillas(crudo)[0], limpio, f"«{crudo[:34]}»")
    igual(intencion.quitar_muletillas("O sea, so.", "en")[0], "O sea, so.",
          "en otro idioma no se toca")
    largas = intencion.revisar_ritmo(
        [{"id": "B001", "texto": " ".join(["palabra"] * 20) + "."}], corto=True)
    ok(largas and "B001" in largas[0], "en un vídeo corto avisa de una frase de 20 palabras")
    ok(not intencion.revisar_ritmo(
        [{"id": "B001", "texto": " ".join(["palabra"] * 20) + "."}], corto=False),
       "en uno largo no")
    texto = marcas_tts.instrucciones(True, motor="un sintetizador de voz",
                                     pauta_tono=intencion.pauta_tono())
    ok("EL TONO DE LA VOZ" in texto and "Cartesia" not in texto.split("\n")[1],
       "con la voz gratuita, el guion pide decidir el tono de cada bloque")
    ok("MULETILLAS" in intencion.pauta_ritmo(True) and "8-10 segundos"
       in intencion.pauta_ritmo(True), "el ritmo de un vídeo corto")


def probar_toma():
    print("\n  UNA TOMA")
    PEDIDOS.clear()
    pcm, duracion, palabras = voz_gratis.toma(
        'Diez millones esperaban. <break time="1s"/> Nadie sabia nada.',
        "es-PE-AlexNeural", "slow", sr=44100)
    igual(len(PEDIDOS), 2, "un pedido por trozo")
    igual({v for _t, v, _r in PEDIDOS}, {"es-PE-AlexNeural"}, "con la voz pedida")
    igual({r for _t, _v, r in PEDIDOS} <= {"-15%", "-24%"}, True,
          "y su velocidad (el remate corto, un poco más despacio)")
    igual([p["w"] for p in palabras],
          ["Diez", "millones", "esperaban", "Nadie", "sabia", "nada"],
          "todas las palabras, en orden")
    inicios = [p["s"] for p in palabras]
    ok(inicios == sorted(inicios), "los tiempos crecen")
    ok(palabras[3]["s"] - palabras[2]["e"] > 0.8,
       f"la pausa escrita se oye entre los trozos ({palabras[3]['s'] - palabras[2]['e']:.2f} s)")
    igual(round(len(pcm) / (44100 * 2), 3), round(duracion, 3),
          "la duracion es la del audio a 44,1 kHz")
    ok(palabras[-1]["e"] <= duracion, "ninguna palabra acaba despues del audio")


def probar_personajes_y_claves():
    """Voz de personaje y frase clave (`<personaje>`, `<clave>`)."""
    print("\n  VOZ DE PERSONAJE Y FRASE CLAVE")
    texto = ('Jotam les gritó: <personaje nombre="Jotam" genero="hombre">'
             '¡Escúchenme, hombres de Siquem!</personaje> Nadie respondió. '
             '<clave>Y sobre una sola piedra mató a sus hermanos.</clave> Fin.')
    igual(marcas_tts.limpiar(marcas_tts.sanear(texto)),
          "Jotam les gritó: ¡Escúchenme, hombres de Siquem! Nadie respondió. "
          "Y sobre una sola piedra mató a sus hermanos. Fin.",
          "las etiquetas no se oyen ni cuentan como palabras")
    igual(marcas_tts.sanear(marcas_tts.sanear(texto)), marcas_tts.sanear(texto),
          "sanear las conserva y es idempotente")
    igual(marcas_tts.sanear("<clave>Abierta sin cerrar"), "<clave>Abierta sin cerrar</clave>",
          "un par sin cerrar se cierra al final del bloque")
    igual(marcas_tts.sin_voces(texto).count("<"), 0, "a Cartesia le llegan sin ellas")
    igual(marcas_tts.sanear("Uno dos tres."), "Uno dos tres.",
          "un texto sin estas etiquetas sale igual que antes")

    trozos = voz_gratis._trozos(marcas_tts.sanear(texto))            # noqa: SLF001
    igual([t[0] for t in trozos],
          ["Jotam les gritó:", "¡Escúchenme, hombres de Siquem!", "Nadie respondió.",
           "Y sobre una sola piedra mató a sus hermanos.", "Fin."],
          "se parte donde entra y sale cada voz")
    igual([t[2][3] for t in trozos],
          [None, ("Jotam", "hombre"), None, None, None], "el personaje va en su trozo")
    igual([t[2][4] for t in trozos], [False, False, False, True, False],
          "la frase clave va en el suyo")
    ok(trozos[2][1] >= voz_gratis.PAUSA_ANTES_CLAVE, "silencio antes de la frase clave")
    ok(trozos[3][1] >= voz_gratis.PAUSA_DESPUES_CLAVE, "y un poco despues")

    catalogo = [
        {"id": "es-PE-AlexNeural", "genero": "male", "nativa": True},
        {"id": "es-PE-CamilaNeural", "genero": "female", "nativa": True},
        {"id": "es-MX-JorgeNeural", "genero": "male", "nativa": True},
        {"id": "es-CO-GonzaloNeural", "genero": "male", "nativa": True},
        {"id": "es-AR-ElenaNeural", "genero": "female", "nativa": True}]
    antes = voz_gratis.voces
    voz_gratis.voces = lambda idioma=None, refrescar=False: catalogo
    try:
        jotam = voz_gratis.voz_de_personaje("Jotam", "hombre", "es-PE-AlexNeural")
        ok(jotam in ("es-MX-JorgeNeural", "es-CO-GonzaloNeural"),
           f"un personaje hombre: otra voz de hombre ({jotam})")
        igual(voz_gratis.voz_de_personaje("Jotam", "hombre", "es-PE-AlexNeural"), jotam,
              "y siempre la misma para el mismo nombre")
        # narrador MULTILINGUE (prefijo «en»): el personaje habla castellano nativo
        jesus = voz_gratis.voz_de_personaje("Jesús", "hombre",
                                            "en-US-BrianMultilingualNeural", idioma="es")
        ok(jesus.startswith("es-") and "Multilingual" not in jesus,
           f"con narrador multilingue, el personaje es una voz nativa de castellano ({jesus})")
        ok(voz_gratis.voz_de_personaje("Jesús", "hombre",
                                       "en-US-BrianMultilingualNeural").startswith("es-"),
           "y sin idioma dicho, tambien castellano")
        igual(voz_gratis.voz_de_personaje("Débora", "mujer", "es-PE-AlexNeural"),
              "es-PE-CamilaNeural", "una mujer: primero las del pais del narrador")
        PEDIDOS.clear()
        voz_gratis.toma(marcas_tts.sanear(texto), "es-PE-AlexNeural", 10 / 35, sr=44100)
        por_texto = {t: (v, r) for t, v, r in PEDIDOS}
        igual(por_texto["¡Escúchenme, hombres de Siquem!"][0], jotam,
              "en la toma, Jotam habla con su voz")
        igual(por_texto["Nadie respondió."][0], "es-PE-AlexNeural",
              "y el narrador sigue con la suya")
        clave = int(por_texto["Y sobre una sola piedra mató a sus hermanos."][1].rstrip("%"))
        ok(clave <= 10 - voz_gratis.CLAVE_MENOS_VELOCIDAD,
           f"la frase clave va mucho mas despacio ({clave:+d}% con la voz a +10%)")
    finally:
        voz_gratis.voces = antes


def probar_efectos():
    """El efecto de voz del video (pasos/efectos_voz.py)."""
    import numpy as np  # noqa: PLC0415
    import efectos_voz  # noqa: PLC0415
    print("\n  EL EFECTO DE VOZ (mas grave, misteriosa...)")
    igual(efectos_voz.normalizar({"estilo": "natural"}), None, "natural sin tono: sin efecto")
    igual(efectos_voz.normalizar({"estilo": "misteriosa"}),
          {"estilo": "misteriosa", "tono": -4}, "cada estilo trae su tono")
    igual(efectos_voz.normalizar({"estilo": "grave", "tono": -30})["tono"], -8,
          "el tono se acota")
    igual(efectos_voz.normalizar({"estilo": "inventado"}), None, "un estilo que no existe, nada")
    sr = 44100
    t = np.arange(int(sr * 3)) / sr
    tono = (0.3 * np.sin(2 * np.pi * 220 * t) * 32767).astype(np.int16).tobytes()
    for estilo in efectos_voz.ESTILOS:
        if estilo == "natural":
            continue
        salida = efectos_voz.aplicar(tono, sr, {"estilo": estilo})
        igual(len(salida), len(tono), f"«{estilo}» no cambia la duracion ni una muestra")
    grave = np.frombuffer(efectos_voz.aplicar(tono, sr, {"estilo": "grave", "tono": -8}),
                          dtype=np.int16).astype(np.float32)
    pico = np.argmax(np.abs(np.fft.rfft(grave[sr // 2: sr * 2]))) * sr / (sr * 1.5)
    ok(132 < pico < 146, f"8 semitonos mas grave: 220 Hz -> {pico:.0f} Hz (139)")

    ajustes.guardar({"modo_voz": "gratis"})
    con = {"voz_id": "es-PE-AlexNeural", "idioma": "es",
           "voz_del_video": {"efecto": {"estilo": "cine", "tono": -4}}}
    igual(p4_voz.resolver_params(con).get("efecto_voz"), {"estilo": "cine", "tono": -4},
          "con la voz gratuita el efecto va en la configuracion")
    igual(p4_voz.resolver_params(dict(con, grabacion="abc")).get("efecto_voz"),
          {"estilo": "cine", "tono": -4}, "y con tu voz grabada")
    ajustes.guardar({"modo_voz": "cartesia"})
    igual(p4_voz.resolver_params(con).get("efecto_voz"), None, "con Cartesia, no")
    ajustes.guardar({"modo_voz": "gratis"})


def probar_paso():
    print("\n  EL PASO DE VOZ ENTERO")
    ajustes.guardar({"modo_voz": "gratis", "voz_gratis": "es-PE-CamilaNeural"})
    ok(p4_voz.gratis(), "el modo gratuito queda puesto")

    def prohibido(*_a, **_k):
        raise AssertionError("la voz gratuita ha llamado a Cartesia")
    p4_voz._toma_real = prohibido                              # noqa: SLF001
    p4_voz._toma_por_contexto = prohibido                      # noqa: SLF001

    cfg = p4_voz.resolver_params({"voz_id": "a0e99841-438c-4a64-b679-ae501e7d6091",
                                  "idioma": "es", "velocidad": "normal",
                                  "hueco_minimo": 0.6})
    igual(cfg["motor_voz"], "gratis", "la configuracion dice voz gratuita")
    igual(cfg["voz_gratis"], "es-PE-CamilaNeural",
          "con la voz de Cartesia del estilo, usa la de Configuracion")
    bloques = [
        {"id": "B001", "texto": "Diez millones de personas esperaban aquel dia."},
        {"id": "B002", "texto": 'Nadie sabia lo que iba a pasar. <break time="700ms"/> '
                                "Pero algo cambio."},
        {"id": "B003", "texto": "Y todo empezo de nuevo en Jerusalen."},
    ]
    destino = os.path.join(CARPETA, "toma")
    salidas = p4_voz.sintetizar_bloques(bloques, destino, cfg)
    ok(os.path.isfile(os.path.join(destino, "narracion.wav")), "deja la pista")
    ok(os.path.isfile(os.path.join(destino, "audio_meta.json")), "y su meta")
    igual([b["palabras"] for b in salidas["bloques"]], [7, 10, 7],
          "cada bloque se lleva sus palabras")
    tramos = [(b["t_in"], b["t_out"]) for b in salidas["bloques"]]
    ok(all(a[1] <= b[0] for a, b in zip(tramos, tramos[1:])),
       f"los bloques no se pisan: {tramos}")
    ok(all(b[0] - a[1] >= 0.55 for a, b in zip(tramos, tramos[1:])),
       "entre bloques queda el aire pedido")
    ok("voz gratuita es-PE-CamilaNeural" in salidas["resumen"],
       f"el resumen dice que voz ha sonado ({salidas['resumen']})")
    igual(salidas["controles"]["motor_voz"], "gratis", "y queda apuntado en los controles")

    cfg2 = p4_voz.resolver_params({"voz_id": "es-PE-AlexNeural", "idioma": "es"})
    igual(cfg2["voz_gratis"], "es-PE-AlexNeural",
          "una voz gratuita elegida en el video manda sobre Configuracion")

    print("\n  CON CARTESIA PUESTO")
    ajustes.guardar({"modo_voz": "cartesia"})
    ok(not p4_voz.gratis(), "el modo Cartesia queda puesto")
    cfg3 = p4_voz.resolver_params({"voz_id": "es-PE-AlexNeural", "idioma": "es"})
    igual(cfg3["motor_voz"], "cartesia", "la configuracion dice Cartesia")
    ok(not voz_gratis.es_voz_gratis(cfg3["voz_id"]),
       "y una voz gratuita guardada no se le manda a Cartesia")
    try:
        ajustes.guardar({"modo_voz": "eleven"})
        ok(False, "un modo de voz que no existe deberia rechazarse")
    except ValueError:
        ok(True, "un modo de voz que no existe se rechaza")
    try:
        ajustes.guardar({"voz_gratis": "Carlos"})
        ok(False, "una voz gratuita mal escrita deberia rechazarse")
    except ValueError:
        ok(True, "una voz gratuita mal escrita se rechaza")


def probar_voz_por_tema():
    """La voz elegida por el tema del video (pasos/voz_tema.py)."""
    import voz_tema  # noqa: PLC0415
    print("\n  LA VOZ SEGUN EL TEMA")
    fe = voz_tema.elegir("Jesús oró en el huerto. Dios escuchó la oración de su "
                         "Hijo, y la cruz llegó al día siguiente. La fe de Pedro...")
    igual(fe["tema"], "fe", "un vídeo bíblico se reconoce como de fe")
    igual(fe["voz_id"], "es-CO-GonzaloNeural", "fe + tristeza: voz grave y serena")
    nino = voz_tema.elegir("Había una vez un niño y una niña que iban al colegio "
                           "con su juguete favorito. ¡Qué cuento tan bonito!")
    igual((nino["tema"], nino["voz_id"][-11:]), ("infantil", "DaliaNeural"),
          "un cuento para niños: voz de mujer alegre y cercana")
    miedo = voz_tema.elegir("El misterio del crimen: nadie sabe quién fue el "
                            "asesino. El secreto sigue oculto en la oscuridad.")
    igual(miedo["tema"], "misterio", "un misterio se reconoce")
    igual(miedo["voz_id"], "es-US-AlonsoNeural", "misterio: voz grave e intensa")
    igual(voz_tema.elegir("Hello world", "en"), None, "otro idioma: no se toca")
    sin = voz_tema.elegir("Una receta sencilla de pan casero.")
    igual(sin["tema"], "documental", "sin tema claro: documental")
    igual(voz_tema.elegir(fe and "Dios y la fe de Jesús", "es",
                          ["es-PE-AlexNeural"])["voz_id"], "es-PE-AlexNeural",
          "solo elige voces que están en el catálogo")
    igual(ajustes.leer()["voz_por_tema"], True, "encendida de fábrica")
    try:
        ajustes.guardar({"voz_por_tema": "si"})
        ok(False, "voz_por_tema solo admite verdadero o falso")
    except ValueError:
        ok(True, "voz_por_tema solo admite verdadero o falso")


def probar_voz_del_video():
    """La voz elegida a mano para UN video (pantalla del guion) y la del
    estilo frente a la del tema. Sin red: el catalogo se dobla."""
    print("\n  LA VOZ DEL VIDEO, A MANO, Y LA DEL ESTILO")
    ajustes.guardar({"modo_voz": "gratis", "voz_gratis": "", "voz_por_tema": True})
    cfg = p4_voz.resolver_params({"voz_id": "es-PE-AlexNeural", "idioma": "es",
                                  "voz_del_video": {"voz_id": "es-CO-GonzaloNeural"}})
    igual(cfg["voz_gratis"], "es-CO-GonzaloNeural",
          "la voz elegida en el video manda sobre la del estilo")
    cfg = p4_voz.resolver_params({"voz_id": "es-PE-AlexNeural", "idioma": "es",
                                  "voz_del_video": {"voz_id": "a0e99841-438c"}})
    igual(cfg["voz_gratis"], "es-PE-AlexNeural",
          "una voz del video que no es gratuita no cuenta")

    from nucleo.estado import Estado  # noqa: PLC0415
    from nucleo.proyecto import Proyecto  # noqa: PLC0415
    import app  # noqa: PLC0415
    vg = app.PASOS_MODULOS.voz_gratis
    vg.voces = lambda idioma=None, refrescar=False: [
        {"id": "es-PE-AlexNeural", "nombre": "Alex (Perú)", "idioma": "es"},
        {"id": "es-CO-GonzaloNeural", "nombre": "Gonzalo (Colombia)", "idioma": "es"}]

    class Bitacora:
        def anotar(self, *_a, **_k):
            pass

    class Ctx:
        pass

    def nuevo(nombre, voz):
        ctx = Ctx()
        ctx.proyecto = Proyecto.crear(os.path.join(CARPETA, "proyectos"), nombre)
        ctx.estado = Estado(ctx.proyecto)
        ctx.bitacora = Bitacora()
        ctx.estado.set_params("ingesta", {"texto": "Jesús oró y Dios escuchó. "
                                          "La fe de Pedro y la cruz."})
        ctx.estado.set_params("voz", {"voz_id": voz, "idioma": "es"})
        return ctx

    ctx = nuevo("estilo con voz gratis", "es-PE-AlexNeural")
    igual(app._voz_por_tema(ctx), None,
          "con una voz gratuita del estilo, el tema no la cambia")
    igual(ctx.estado.params("voz")["voz_id"], "es-PE-AlexNeural",
          "y sigue la del estilo (Alex)")
    igual(app._voz_que_suena(ctx, ctx.estado.params("voz"))["origen"], "estilo",
          "la pantalla dice que es la del estilo")

    ctx2 = nuevo("estilo con voz de Cartesia", "a0e99841-438c-4a64-b679-ae501e7d6091")
    elegida = app._voz_por_tema(ctx2)
    ok(elegida and elegida["tema"] == "fe",
       "si el estilo trae una voz de Cartesia, el tema si elige")

    firmas = {p: ctx.estado.firma(p) for p in ("voz", "revision_audio", "assets", "render")}
    unidad = ctx.estado.firma_unidad("assets", "S01")
    ok(app._esta_al_dia(ctx, {"id": "voz"}) is False, "sin audio, la voz esta pendiente")
    ctx.estado.actualizar_params("voz", {"voz_del_video": {
        "voz_id": "es-CO-GonzaloNeural", "voz_nombre": "Gonzalo", "grabada": False}})
    igual({p: ctx.estado.firma(p) for p in firmas}, firmas,
          "elegir la voz del video no mueve ninguna firma")
    igual(ctx.estado.firma_unidad("assets", "S01"), unidad,
          "ni la de una imagen")
    ok(app._voz_del_video_pendiente(ctx), "queda pendiente de grabar")
    ficha = app._voz_que_suena(ctx, ctx.estado.params("voz"))
    igual((ficha["origen"], ficha["nombre"], ficha["pendiente"], ficha["estilo"]),
          ("video", "Gonzalo (Colombia)", True, ""),
          "la pantalla la da por elegida a mano y por oir")
    usados = ctx.estado.params("voz")
    app._voz_del_video_grabada(ctx, usados)
    ok(not app._voz_del_video_pendiente(ctx), "grabada la voz, deja de estar pendiente")
    igual(app._voz_por_tema(ctx), None, "y el tema no la toca")
    igual({p: ctx.estado.firma(p) for p in firmas}, firmas,
          "marcarla grabada tampoco mueve firmas")

    print("\n  LA VELOCIDAD DEL VIDEO, A MANO")
    cfg = p4_voz.resolver_params({"voz_id": "es-PE-AlexNeural", "idioma": "es",
                                  "velocidad": "normal",
                                  "voz_del_video": {"velocidad": round(10 / 35, 4)}})
    igual(voz_gratis.porcentaje_velocidad(cfg["velocidad"]), "+10%",
          "la velocidad elegida en el video manda (+10 %)")
    ctx.estado.actualizar_params("voz", {"voz_del_video": dict(
        ctx.estado.params("voz")["voz_del_video"], velocidad=round(10 / 35, 4),
        grabada=False)})
    igual({p: ctx.estado.firma(p) for p in firmas}, firmas,
          "cambiar la velocidad no mueve ninguna firma")
    ok(app._voz_del_video_pendiente(ctx), "y deja la voz pendiente de grabar")
    ficha = app._voz_que_suena(ctx, ctx.estado.params("voz"))
    igual((ficha["velocidad"], ficha["velocidad_a_mano"]), (10, True),
          "la pantalla la ve: +10 %, elegida a mano")
    app._voz_del_video_grabada(ctx, ctx.estado.params("voz"))
    ok(not app._voz_del_video_pendiente(ctx), "grabada, deja de estar pendiente")

    print("\n  EL EFECTO DE VOZ DEL VIDEO, POR LA API")
    app._guardar_efecto_voz(ctx, {"estilo": "misteriosa", "tono": -5})
    igual({p: ctx.estado.firma(p) for p in firmas}, firmas,
          "poner un efecto no mueve ninguna firma")
    ok(app._voz_del_video_pendiente(ctx), "y deja la voz pendiente de grabar")
    ficha = app._voz_que_suena(ctx, ctx.estado.params("voz"))
    igual((ficha["efecto"], ficha["puede_efecto"]),
          ({"estilo": "misteriosa", "tono": -5}, True), "la pantalla lo ve")
    app._guardar_efecto_voz(ctx, None)
    igual(app._voz_que_suena(ctx, ctx.estado.params("voz"))["efecto"], None,
          "quitarlo lo quita")


def main():
    print("=" * 70)
    print("PRUEBA DE LA VOZ GRATUITA (servicio doblado, sin red)")
    print("=" * 70)
    if not shutil.which("ffmpeg"):
        print("falta ffmpeg: esta suite lo necesita")
        sys.exit(2)
    probar_piezas()
    probar_trozos()
    probar_intencion()
    probar_voz_por_tema()
    probar_voz_del_video()
    probar_toma()
    probar_personajes_y_claves()
    probar_efectos()
    probar_paso()
    print()
    print("=" * 70)
    if _fallos:
        print(f"VOZ GRATUITA CON FALLOS: {len(_fallos)}")
        for fallo in _fallos:
            print(f"  - {fallo}")
        sys.exit(1)
    print(f"VOZ GRATUITA OK: {_comprobaciones[0]} comprobaciones pasan")


if __name__ == "__main__":
    main()
