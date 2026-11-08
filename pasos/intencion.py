"""Guion y voz con INTENCION (punto E de NOTAS-DAVID.md).

Tres cosas, las tres gratis y sin tocar ningun param (no mueven firmas):

1. EL TONO DE LA VOZ CAMBIA CON LA HISTORIA. El guion ya trae anotaciones de
   voz (`marcas_tts`: break, speed, volume, emotion). Cartesia las entiende;
   la voz gratuita (edge-tts) solo respetaba las pausas y TIRABA el resto.
   Edge no deja mandar SSML propio (lo escapa), pero si acepta por peticion
   `rate`, `pitch` y `volume`: con eso cada emocion se traduce a una prosodia
   (`prosodia`) y `voz_gratis` graba cada frase con la suya. Los nombres de
   las emociones son los de Cartesia (los mismos seis), para que un guion
   valga para las dos voces; aqui se les da nombre en castellano (`TONOS`).

   CON LA VOZ GRATUITA CADA BLOQUE EMPIEZA NEUTRO (`con_tono_neutro_al_empezar`):
   el mismo principio que `marcas_tts` aplica a speed/volume -- un bloque suena
   igual venga de donde venga el anterior --, que es lo que permite cambiar el
   tono de UN bloque desde la pantalla sin que cambie como suenan los demas.

2. PAUSAS CON INTENCION que no dependen de que el redactor se acuerde: tras
   una pregunta que sigue hablando («¿Por que? Porque...») y tras unos puntos
   suspensivos, un respiro corto (`PAUSA_PREGUNTA`, `PAUSA_SUSPENSE`). Solo en
   la voz gratuita: alli cada trozo se graba aparte y el silencio se mete a
   mano; Cartesia ya los hace sola.

3. UN GUION SIN MULETILLAS Y CON RITMO. `pauta_ritmo` va al prompt del guion
   (retencion: gancho, preguntas que abren, un giro cada poco, frases cortas;
   en un video corto, mas cortas aun). `quitar_muletillas` limpia lo que se
   cuela igual («o sea,», «bueno,» al empezar, «basicamente»...), y
   `revisar_ritmo` avisa de las frases que cansan. Solo se quita lo que es
   muletilla SEGURO: lo dudoso («tipo», «como que») se deja.
"""
import re
import unicodedata

# ------------------------------------------------------------------ los tonos

#: emocion (vocabulario de marcas_tts) -> (nombre en pantalla, para que sirve)
TONOS = {
    "neutral": ("Neutro", "contar sin mas"),
    "content": ("Alegre", "buenas noticias, esperanza, milagros, final feliz"),
    "calm": ("Sereno", "reflexion, oracion, versiculo que se medita"),
    "sad": ("Triste / lento", "muerte, perdida, pecado, dolor"),
    "scared": ("Tenso / miedo", "peligro, persecucion, suspense, algo que va a pasar"),
    "angry": ("Firme / enérgico", "denuncia, advertencia, injusticia, un «¡no!»"),
}

#: emocion -> (velocidad en puntos de %, tono en Hz, volumen en puntos de %).
#: Medidas a oido sobre las voces neuronales de Edge: mas alla de ~15 % de
#: velocidad o ~12 Hz la voz deja de sonar a la misma persona.
PROSODIA = {
    "neutral": (0, 0, 0),
    "content": (9, 10, 6),
    "calm": (-10, -4, -8),
    "sad": (-18, -12, -12),
    "scared": (6, 4, -16),
    "angry": (9, -4, 15),
}

#: Silencio (s) tras una pregunta que sigue y tras unos puntos suspensivos.
PAUSA_PREGUNTA = 0.32
PAUSA_SUSPENSE = 0.28

_EMOCION_INICIAL = re.compile(r'^\s*(?:<emotion\s+value="([A-Za-z]+)"\s*/>\s*)+', re.I)


def tono_de(texto):
    """La emocion con la que EMPIEZA un bloque, o 'auto' si no lleva ninguna.

    'auto' = el estudio la elige por lo que cuenta (`tono_automatico`); para
    que un bloque suene neutro A PROPOSITO se escribe `neutral`.
    """
    m = _EMOCION_INICIAL.match(str(texto or ""))
    if not m:
        return "auto"
    ultima = re.findall(r'value="([A-Za-z]+)"', m.group(0))[-1].lower()
    return ultima if ultima in PROSODIA else "auto"


def con_tono(texto, tono):
    """El texto del bloque empezando con ese tono ('auto' = sin etiqueta)."""
    resto = _EMOCION_INICIAL.sub("", str(texto or ""), count=1).lstrip()
    tono = str(tono or "auto").lower()
    if tono not in PROSODIA:
        return resto
    return f'<emotion value="{tono}"/>{resto}'


#: Las palabras que delatan el tono de lo que se cuenta (raices plegadas, sin
#: tildes). Se cuentan y gana la que mas sale, si gana con claridad.
PISTAS = {
    "sad": ("muri", "muerte", "muerto", "llor", "lagrima", "dolor", "sufri",
            "crucific", "sangre", "triste", "pecado", "perdi", "desampar",
            "angustia", "tumba", "sepult", "luto", "abandon", "solo y", "herid"),
    "content": ("resucit", "alegr", "gozo", "milagro", "sano", "sanad", "salvo",
                "victoria", "celebr", "fiesta", "esperanza", "bendic", "gloria",
                "aleluya", "nacio", "libre", "perdon", "feliz", "buena noticia",
                "vida eterna", "rescat", "gracia"),
    "scared": ("miedo", "temor", "tembl", "soldado", "persegu", "huir", "huy",
               "peligro", "amenaz", "tormenta", "oscur", "de repente", "ejercito",
               "matar", "prendi", "arrest", "espada", "grit", "terror", "nadie sabia"),
    "angry": ("ira", "enoj", "furi", "hipocrit", "ay de", "advert", "condena",
              "injust", "jamas", "maldic", "denunci", "rechaz"),
    "calm": ("oro ", "oracion", "orar", "paz", "descans", "silencio", "medit",
             "pastor", "quietud", "reposo", "confi", "susurr", "suave", "en calma"),
}


def _plegar(texto):
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def tono_automatico(texto):
    """El tono que pide lo que cuenta el bloque, por sus palabras. -> emocion"""
    plano = " " + re.sub(r"[^a-z ]+", " ", _plegar(re.sub(r"<[^<>]*>", " ", texto))) + " "
    cuentas = {tono: sum(plano.count(" " + raiz) for raiz in raices)
               for tono, raices in PISTAS.items()}
    orden = sorted(cuentas.items(), key=lambda kv: -kv[1])
    (mejor, n1), (_segundo, n2) = orden[0], orden[1]
    if n1 >= 1 and n1 > n2:
        return mejor
    return "neutral"


def con_tono_neutro_al_empezar(texto):
    """Cada bloque arranca con SU tono: el del guion o, si no trae, el que
    pide lo que cuenta (`tono_automatico`). Lo del anterior no se arrastra."""
    texto = str(texto or "").strip()
    if not texto or _EMOCION_INICIAL.match(texto):
        return texto
    return f'<emotion value="{tono_automatico(texto)}"/>' + texto


def matiz(frase):
    """Lo que cambia UNA frase dentro de su tono -> (vel %, Hz, vol %).

    La pregunta sube, la exclamacion empuja, el remate corto se dice despacio y
    la cita literal («…») con peso. Es lo que hace que no suene a lectura.
    """
    f = str(frase or "").strip()
    if not f:
        return (0, 0, 0)
    if f.endswith(("?", "?»", "?”")):
        return (3, 6, 0)
    if f.endswith(("!", "!»", "!”")):
        return (5, 4, 8)
    if f.startswith(("«", "“", '"')):
        return (-7, -2, 0)
    if len(f.split()) <= 5 and f.endswith("."):
        return (-9, -3, 3)
    return (0, 0, 0)


def frases_con_matiz(texto):
    """[(trozo, matiz)]: las frases seguidas con el mismo matiz, juntas."""
    salida = []
    for frase in re.split(r'(?<=[.!?…»”])\s+(?=[«“"¿¡A-ZÁÉÍÓÚÑ])', str(texto or "").strip()):
        if not frase.strip():
            continue
        m = matiz(frase)
        if salida and salida[-1][1] == m:
            salida[-1] = (salida[-1][0] + " " + frase.strip(), m)
        else:
            salida.append((frase.strip(), m))
    return salida or [(str(texto or "").strip(), (0, 0, 0))]


def prosodia(velocidad_base, speed=1.0, volume=1.0, emocion="neutral", extra=(0, 0, 0)):
    """-> (rate, pitch, volume) en el formato de edge-tts («+5%», «-3Hz», «+0%»).

    velocidad_base es el porcentaje de la voz elegida (Configuracion); speed y
    volume son los ratios de las anotaciones (1 = sin cambio).
    """
    mas_vel, hz, mas_vol = PROSODIA.get(str(emocion or "neutral").lower(), (0, 0, 0))
    mas_vel, hz, mas_vol = mas_vel + extra[0], hz + extra[1], mas_vol + extra[2]
    rate = int(round(velocidad_base + (float(speed) - 1.0) * 100 + mas_vel))
    vol = int(round((float(volume) - 1.0) * 100 + mas_vol))
    rate = max(-50, min(60, rate))
    vol = max(-50, min(50, vol))
    hz = max(-20, min(20, int(hz)))
    return f"{rate:+d}%", f"{hz:+d}Hz", f"{vol:+d}%"


def respiros(texto):
    """Parte un texto ya limpio en [(trozo, silencio)] tras «?» y «...» que siguen.

    Solo cuando detras hay mas texto: al final del trozo ya hay pausa.
    """
    salida = []
    resto = str(texto or "").strip()
    patron = re.compile(r'(\?|…|\.\.\.)["»”\')\]]?\s+(?=\S)')
    posicion = 0
    for m in patron.finditer(resto):
        trozo = resto[posicion:m.end()].strip()
        if len(trozo.split()) < 2:
            continue       # «¿Y?» suelto no merece un corte
        silencio = PAUSA_PREGUNTA if m.group(1) == "?" else PAUSA_SUSPENSE
        salida.append((trozo, silencio))
        posicion = m.end()
    final = resto[posicion:].strip()
    if final:
        salida.append((final, 0.0))
    return salida or [(resto, 0.0)]


# ------------------------------------------------------------- muletillas

# Al EMPEZAR una frase y seguidas de coma: no dicen nada.
# «Mira,» y «Oye,» NO: «Oye, Israel» es Deuteronomio 6:4 (RV1960). Ni «Este,»,
# que tambien es pronombre («Este, a su vez, ...»).
_INICIO = r"bueno|pues|vale|eh|digamos|en fin|total|a ver|y nada|entonces bueno"
_FRONTERA = r'(^|[.!?…:]["»”]?\s+|<[^<>]*/>\s*)'
_RE_INICIO = re.compile(_FRONTERA + r'(?:' + _INICIO + r')\s*,\s*', re.I)
# En cualquier sitio.
_RE_O_SEA_QUE = re.compile(r'\bo\s*sea\s+que\b', re.I)
_RE_O_SEA = re.compile(r',?\s*\bo\s*sea\b\s*,?\s*', re.I)
_RE_RELLENO = re.compile(
    r',?\s*\b(?:básicamente|basicamente|literalmente|la verdad es que|'
    r'digamos)\b\s*,?', re.I)


def _mayuscula_tras_frontera(texto):
    return re.sub(r'(^|[.!?…]["»”]?\s+|<[^<>]*/>\s*)([a-záéíóúñü])',
                  lambda m: m.group(1) + m.group(2).upper(), texto)


def quitar_muletillas(texto, idioma="es"):
    """-> (texto limpio, [muletillas quitadas]). Solo castellano."""
    if not str(idioma or "es").lower().startswith("es"):
        return texto, []
    original = str(texto or "")
    quitadas = []

    def apunta(m, desde=0):
        quitadas.append(" ".join(m.group(0)[desde:].strip(" ,").split()).lower())

    nuevo = _RE_INICIO.sub(lambda m: (apunta(m, len(m.group(1))), m.group(1))[1],
                           original)
    nuevo = _RE_O_SEA_QUE.sub(lambda m: (apunta(m), "así que")[1], nuevo)

    def o_sea(m):
        apunta(m)
        # «A, o sea, B» -> «A, B»; «o sea» al empezar -> nada
        return ", " if m.group(0).lstrip().startswith(",") else " "
    nuevo = _RE_O_SEA.sub(o_sea, nuevo)

    def relleno(m):
        # «Era, basicamente, un pescador» -> «Era un pescador»: la coma iba
        # solo para aislar la muletilla
        apunta(m)
        return " "
    nuevo = _RE_RELLENO.sub(relleno, nuevo)
    if not quitadas:
        return original, []
    # lo que dejo el corte: «, ,», « ,», espacios dobles, «así que» en minuscula
    nuevo = re.sub(r'\s+,', ',', nuevo)
    nuevo = re.sub(r',\s*,', ',', nuevo)
    nuevo = re.sub(r',\s*([.!?…])', r'\1', nuevo)
    nuevo = re.sub(r'(^|[.!?…:]\s+)\s*,\s*', r'\1', nuevo)
    nuevo = re.sub(r'[ \t]{2,}', ' ', nuevo).strip()
    nuevo = re.sub(r'^,\s*', '', nuevo)
    nuevo = _mayuscula_tras_frontera(nuevo)
    return nuevo, quitadas


# ------------------------------------------------------------------ el ritmo

def es_corto(maximo_palabras):
    """Un video corto (TikTok/Shorts): ~90 s o menos."""
    try:
        return 0 < int(maximo_palabras) <= 260
    except (TypeError, ValueError):
        return False


def tope_frase(corto):
    return 16 if corto else 28


def _frases(texto):
    return [f for f in re.split(r'(?<=[.!?…])\s+', str(texto or "").strip()) if f.strip()]


def revisar_ritmo(bloques, corto=False, limpiar=None):
    """Avisos (no correcciones) sobre frases que cansan y muletillas que quedan."""
    limpiar = limpiar or (lambda t: re.sub(r'<[^<>]*>', ' ', str(t or "")))
    tope = tope_frase(corto)
    largas = []
    for bloque in bloques or []:
        for frase in _frases(limpiar(bloque.get("texto"))):
            n = len(frase.split())
            if n > tope:
                largas.append(f"{bloque.get('id', '?')} ({n} palabras)")
    avisos = []
    if largas:
        avisos.append(
            f"frases de más de {tope} palabras, que cuestan de seguir al oído: "
            + ", ".join(largas[:6]) + (f" y {len(largas) - 6} más" if len(largas) > 6 else ""))
    return avisos


def pauta_ritmo(corto=False, idioma="es"):
    """Reglas de RETENCION y de estilo hablado para el prompt del guion."""
    tope = tope_frase(corto)
    lineas = [
        "== CUÉNTALO COMO UNA HISTORIA, NO COMO UNA LISTA ==",
        "- Personajes con nombre, un lugar y un momento concretos, qué quieren y "
        "qué se lo impide; luego el giro y el desenlace. Escenas que se puedan "
        "ver («La noche era fría. Pedro, junto al fuego, oyó la pregunta…»), no "
        "resúmenes de datos.",
        "- Cada frase empuja a la siguiente (porque, pero, entonces, hasta "
        "que…): quien escucha tiene que sentir que algo va a pasar.",
        "- Explica como a un amigo de quince años: si una palabra o una "
        "costumbre de la época no se entiende, se explica en media frase.",
        "",
        "== RITMO PARA RETENER (que nadie se vaya a mitad) ==",
        "- La PRIMERA frase es el gancho: una pregunta o un dato que choca, sin "
        "presentarse ni saludar antes.",
        "- ABRE PREGUNTAS y ciérralas más tarde («¿y por qué lo hizo? Ahora lo "
        "verás»): quien tiene una pregunta abierta se queda.",
        ("- Un GIRO cada 8-10 segundos (un dato nuevo, un «pero», una pregunta, "
         "un contraste): en un vídeo corto no hay tiempo para explicar despacio."
         if corto else
         "- Un GIRO cada 20-30 segundos (un dato nuevo, un «pero», una pregunta, "
         "un contraste) que vuelva a enganchar."),
        f"- FRASES CORTAS: una idea por frase, ninguna de más de {tope} palabras. "
        "Alterna alguna muy corta («Y funcionó.») con otras medias: el contraste "
        "es lo que da ritmo; todas iguales suenan a lista leída.",
        "- Habla A QUIEN ESCUCHA («tú», «imagina que…») y con verbos de acción, "
        "no con sustantivos abstractos.",
        "- El FINAL remata la pregunta del principio y deja una frase para "
        "recordar; nada de «y eso es todo» ni de resúmenes.",
        "- NADA DE MULETILLAS de conversación: «o sea», «bueno,», «pues,», "
        "«básicamente», «literalmente», «la verdad es que», «en plan», "
        "«digamos», «y nada». En un guion locutado suenan a que el narrador "
        "duda.",
    ]
    if corto:
        lineas.append(
            "- VÍDEO CORTO (TikTok/Shorts): ni una frase de relleno; si una frase "
            "no aporta un dato o una emoción, fuera.")
    return "\n".join(lineas)


def pauta_tono():
    """Como decidir el TONO de la voz en el guion (para la voz gratuita)."""
    lineas = [
        "== EL TONO DE LA VOZ CAMBIA CON LA HISTORIA ==",
        "Decide el tono de cada bloque según lo que CUENTA y ponlo con "
        "`<emotion value=\"...\"/>` al EMPEZAR el bloque. Cada bloque empieza "
        "de nuevo: si un tramo de tres bloques es triste, los tres llevan su "
        "etiqueta. Si un bloque no la lleva, el estudio elige el tono por sus "
        "palabras (muerte -> triste, milagro -> alegre); pon la etiqueta cuando "
        "sepas mejor lo que pide la historia, y `neutral` para contar sin "
        "color. Las preguntas, las exclamaciones, los remates cortos y las "
        "citas entre comillas ya cambian solos de entonación. Los tonos:",
    ]
    for clave, (nombre, uso) in TONOS.items():
        if clave != "neutral":
            lineas.append(f"  - {clave}: {nombre.lower()} -> {uso}")
    lineas.append(
        "Un vídeo con intención cambia de tono varias veces (de tres a seis en un "
        "vídeo largo, dos o tres en uno corto), siguiendo la historia: tensión "
        "antes del giro, alegría en la buena noticia, calma en el versículo. No "
        "pongas tono a todos los bloques: el contraste con lo neutro es lo que "
        "se nota.")
    lineas.append(
        "PAUSAS: tras una pregunta que deja pensar y tras unos puntos "
        "suspensivos ya se hace un respiro solo; usa `<break>` para lo que de "
        "verdad pesa (antes de la revelación, tras el gancho).")
    return "\n".join(lineas)
