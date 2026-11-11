"""FIDELIDAD HISTORICA Y BIBLICA EN LO QUE SE DIBUJA (punto C, 6-11-2026).

QUE PASABA
----------
En el primer video del canal los personajes salian como los pinta la costumbre
europea -- piel clara, pelo largo y liso, ropas de cuadro renacentista -- y los
sitios mezclaban siglos. Y una frase como «no hay un Belen, hay dos» se
ilustraba con un pueblo cualquiera, cuando lo que explica esa frase es un MAPA
con los dos Belen y lo que hay entre ellos.

QUE HACE ESTO
-------------
Tres cosas, todas deterministas y sin llamar a ningun modelo:

  1. RECONOCE si el video es biblico/historico (`es_biblico`) y de que EPOCA
     (`epocas`): el siglo I en Judea y Galilea, los patriarcas, Egipto y el
     exodo, los reyes de Israel, el exilio en Babilonia y Persia. Cada epoca
     trae como era la gente, la ropa, las casas y los objetos SEGUN FUENTES
     SERIAS (arqueologia e historia), y lo que NO va (lo inventado, lo
     anacronico).
  2. ENCUENTRA LOS LUGARES que nombra el texto (un nomenclator con coordenadas
     de los sitios biblicos) y calcula la distancia en linea recta entre ellos.
     Con eso un plano que habla de dos sitios pide un mapa con los dos y su
     distancia -- un dato, no una adivinanza del generador.
  3. LO PONE donde se escribe lo que se dibuja: en el encargo del guion
     (Reina-Valera 1960 como base para citas y hechos), en el del catalogo
     visual (reparto y sitios), en el de la direccion y el redactor de planos,
     y en el prompt que se copia en el modo manual.

POR QUE NO MUEVE FIRMAS
-----------------------
Nada de esto es un param. Cambia el TEXTO que se le manda a Claude o el que se
copia para Gemini, y ese texto no entra en la firma de ningun paso: un video ya
hecho no queda obsoleto, y uno nuevo sale con la fidelidad puesta. El prompt
que arma `p6_assets` para OpenAI NO se toca a proposito: cambiarlo haria fallar
la cache de imagenes ya pagadas. La fidelidad le llega por las descripciones
que escribe Claude (reparto, sitios, plano), que son de cada video.

Un video que no es biblico no recibe ni una letra: `pauta_*` devuelven "".
"""
import math
import re
import unicodedata


def plegar(texto):
    """minusculas, sin tildes y con espacios simples: para buscar palabras."""
    # la ñ se guarda: sin ella «año» seria «ano» y «caña», «cana» (Caná)
    texto = str(texto or "").lower().replace("ñ", "\x00")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("\x00", "ñ")
    return " ".join(re.sub(r"[^a-z0-9ñ]+", " ", texto).split())


def _hay(plegado, palabra):
    return re.search(rf"\b{palabra}\b", plegado) is not None


# ------------------------------------------------------------ es biblico?

#: Valen 2: con una basta casi para decir que el video es biblico.
FUERTES = ("biblia", "biblico", "biblica", "jesus", "jesucristo", "cristo",
           "evangelio", "evangelios", "apostol", "apostoles", "profeta",
           "profetas", "antiguo testamento", "nuevo testamento", "escrituras",
           "reina valera", "versiculo", "versiculos", "mesias", "fariseos",
           "fariseo", "israelitas", "salmo", "salmos", "genesis", "exodo")
#: Valen 1: sueltas no dicen nada (Juan, Pedro o Roma salen en cualquier sitio).
DEBILES = ("dios", "señor", "israel", "jerusalen", "galilea", "judea",
           "nazaret", "belen", "templo", "sinagoga", "discipulo", "discipulos",
           "moises", "abraham", "isaac", "jacob", "faraon", "egipto", "pablo",
           "pedro", "juan", "maria", "jose", "herodes", "pilato", "babilonia",
           "rey david", "salomon", "elias", "daniel", "cordero", "pecado",
           "oracion", "gracia", "fe", "iglesia", "cruz", "resurreccion",
           "milagro", "milagros", "angel", "angeles", "hechos", "romanos",
           "corintios", "mateo", "marcos", "lucas", "samaria", "jordan")


def puntuacion(*textos):
    plegado = plegar(" ".join(str(t or "") for t in textos))
    puntos = sum(2 for p in FUERTES if _hay(plegado, p))
    puntos += sum(1 for p in DEBILES if _hay(plegado, p))
    return puntos


def es_biblico(*textos):
    """True si el texto habla de la Biblia o de su historia (>= 3 puntos)."""
    return puntuacion(*textos) >= 3


# ----------------------------------------------------------------- epocas

#: Cada epoca: las palabras que la delatan y COMO ERA, segun la arqueologia y la
#: historia (no segun la pintura europea). Lo de «evita» es lo que sale solo si
#: no se dice: el generador dibuja la costumbre, no la historia.
EPOCAS = {
    "nt": {
        "nombre": "siglo I d. C., Judea y Galilea bajo Roma (Jesús y los apóstoles)",
        "ingles": "first-century",
        "palabras": ("jesus", "cristo", "apostol", "apostoles", "discipulos",
                     "evangelio", "galilea", "nazaret", "herodes", "pilato",
                     "fariseos", "fariseo", "saduceos", "romanos", "romano",
                     "pablo", "pedro", "maria magdalena", "juan el bautista",
                     "sinagoga", "cafarnaum", "hechos", "iglesia primitiva",
                     "centurion", "cesar", "samaritano", "cruz", "crucifixion",
                     "resurreccion", "pentecostes", "belen", "magos"),
        "gente": ("judíos del siglo I de Judea y Galilea: aspecto de Oriente "
                  "Medio / Mediterráneo oriental, piel morena oliva, ojos "
                  "oscuros, pelo oscuro rizado u ondulado; los hombres con "
                  "pelo CORTO o media melena y barba corta o media (nada de "
                  "melena larga y lisa ni rasgos europeos, ni ojos azules, ni "
                  "pelo rubio); estatura media-baja, manos de trabajo"),
        "ropa": ("túnica de lana o lino SIN TEÑIR o en tonos tierra (crudo, "
                 "beis, marrón), hasta la rodilla en los hombres y hasta el "
                 "tobillo en las mujeres, ceñida con un cinto; manto encima "
                 "(los hombres judíos con flecos —tsitsit— en las esquinas); "
                 "sandalias de cuero; las mujeres con manto que cubre la "
                 "cabeza. Soldados romanos (auxiliares): túnica roja o crudo, "
                 "casco de metal, cinturón, escudo y lanza o espada corta"),
        "sitios": ("casas de piedra caliza (Judea) o de basalto negro "
                   "(Galilea) con tejado PLANO de vigas y barro y patio "
                   "interior; calles de tierra o piedra, muros bajos de piedra "
                   "seca, olivos, viñas, colinas secas y pedregosas; "
                   "Jerusalén con murallas y el Templo de Herodes de piedra "
                   "caliza blanca y oro; barcas de pesca de madera de unos "
                   "8 m con vela en el lago de Galilea"),
        "objetos": ("lámparas de aceite de barro pequeñas, cántaros y tinajas "
                    "de barro, vasijas de piedra, ROLLOS (no libros "
                    "encuadernados), redes, molinos de piedra, monedas de "
                    "bronce y plata"),
        "evita": ("rasgos europeos, ojos azules, pelo rubio; ropa medieval o "
                  "renacentista, colores chillones o tejidos estampados; "
                  "aureolas o halos en nadie; ángeles con alas; cruces "
                  "como adorno o en iglesias; cúpulas y minaretes (son siglos "
                  "posteriores); libros encuadernados, cristal en ventanas, "
                  "pantalones, metal moderno"),
    },
    "patriarcas": {
        "nombre": "los patriarcas (hacia 2000-1700 a. C.), Canaán y Mesopotamia",
        "ingles": "Middle Bronze Age (around 1800 BC)",
        "palabras": ("abraham", "abram", "sara", "isaac", "jacob", "esau",
                     "rebeca", "raquel", "lot", "haran", "ur de los caldeos",
                     "canaan", "patriarca", "patriarcas", "sodoma", "genesis"),
        "gente": ("pastores seminómadas semitas: piel morena, pelo y barba "
                  "oscuros y largos en los hombres, pelo largo recogido en "
                  "las mujeres"),
        "ropa": ("túnicas de lana con franjas o dibujos de colores (como el "
                 "mural de Beni Hasan), mantos, sandalias, cayado de pastor"),
        "sitios": ("tiendas de pelo de cabra negro, rebaños de ovejas, cabras "
                   "y camellos, pozos de piedra, encinas, colinas y estepa; "
                   "ciudades amuralladas de adobe en el fondo"),
        "objetos": ("odres de cuero, vasijas de barro, cuchillos de bronce, "
                    "altares de piedras sin labrar"),
        "evita": ("ciudades de mármol, armaduras, caballos de guerra, "
                  "monedas, rollos y libros"),
    },
    "exodo": {
        "nombre": "Egipto y el éxodo (Moisés, el desierto del Sinaí)",
        "ingles": "Late Bronze Age (around 1300 BC)",
        "palabras": ("moises", "aaron", "faraon", "egipto", "egipcios",
                     "exodo", "plagas", "mar rojo", "sinai", "horeb",
                     "tabernaculo", "arca del pacto", "mana", "desierto",
                     "diez mandamientos", "tablas de la ley", "josue"),
        "gente": ("israelitas semitas (piel morena, pelo y barba oscuros) y "
                  "egipcios (piel morena rojiza, cabeza afeitada o peluca "
                  "negra, ojos con kohl)"),
        "ropa": ("egipcios con faldellín y túnicas de LINO BLANCO, collares "
                 "anchos; el faraón con tocado nemes de rayas y corona; "
                 "israelitas con túnicas de lana de colores apagados, mantos "
                 "y sandalias"),
        "sitios": ("ciudades de ladrillo de barro y paja, templos de piedra "
                   "con columnas y jeroglíficos de colores, el Nilo con "
                   "papiros y palmeras; el desierto del Sinaí: montañas de "
                   "granito rojizo, arena y roca, campamento de tiendas"),
        "objetos": ("carros ligeros egipcios, látigos de capataz, moldes de "
                    "ladrillo, el tabernáculo de telas y pieles, el arca de "
                    "madera cubierta de oro con dos querubines"),
        "evita": ("pirámides en cada plano (eran ya antiguas), camellos en "
                  "Egipto, rasgos europeos, armaduras de hierro"),
    },
    "reyes": {
        "nombre": "los reyes de Israel y Judá (siglos X-VI a. C., Edad del Hierro)",
        "ingles": "Iron Age (around 1000 BC)",
        "palabras": ("rey david", "david", "saul", "salomon", "goliat",
                     "salmista", "kinnor", "betsabe", "natan", "absalon",
                     "jonatan", "isai",
                     "samuel", "elias", "eliseo", "jezabel", "acab",
                     "ezequias", "josias", "filisteos", "arca", "isaias",
                     "jeremias", "primer templo", "reyes", "cronicas"),
        "gente": ("israelitas de la Edad del Hierro: piel morena, pelo y "
                  "barba oscuros, los hombres con barba"),
        "ropa": ("túnicas de lana largas de colores sobrios, mantos, cintos; "
                 "reyes con túnica más rica (púrpura, bordes bordados) y "
                 "corona sencilla de metal; soldados con casco de bronce, "
                 "escudo redondo, lanza, honda y arco"),
        "sitios": ("ciudades amuralladas de piedra sobre colinas, casas de "
                   "«cuatro estancias» con tejado plano, puertas de ciudad "
                   "con bancos donde se juzga, el Templo de Salomón de piedra "
                   "y cedro con dos columnas de bronce"),
        "objetos": ("arpa pequeña (kinnor), cuernos de aceite, carros de "
                    "guerra, espadas de hierro, lámparas de barro abiertas"),
        "evita": ("castillos medievales, armaduras de placas, coronas "
                  "europeas, cúpulas"),
    },
    "exilio": {
        "nombre": "el exilio en Babilonia y la época persa (siglos VI-V a. C.)",
        "ingles": "sixth-century BC",
        "palabras": ("babilonia", "nabucodonosor", "daniel", "sadrac",
                     "ciro", "persia", "persas", "dario", "ester", "mardoqueo",
                     "nehemias", "esdras", "exilio", "cautiverio", "susa",
                     "belsasar", "asirios", "ninive", "jonas"),
        "gente": ("judíos deportados (piel morena, pelo y barba oscuros), "
                  "babilonios y persas con barbas largas y RIZADAS en "
                  "tirabuzones"),
        "ropa": ("babilonios y persas con túnicas largas con flecos y "
                 "bordados, gorros cilíndricos o tiaras; guardias persas "
                 "con lanza y aljaba; judíos con túnicas y mantos sencillos"),
        "sitios": ("Babilonia: murallas y la Puerta de Ishtar de ladrillo "
                   "vidriado AZUL con leones y dragones dorados, zigurat "
                   "escalonado, el río Éufrates con palmeras datileras; "
                   "palacios persas de Susa con columnas altas y capiteles "
                   "de toros"),
        "objetos": ("tablillas de arcilla con escritura cuneiforme, sellos "
                    "cilíndricos, copas de oro, fosos y leones"),
        "evita": ("arquitectura islámica (cúpulas, minaretes, arcos de "
                  "herradura), turbantes modernos, rasgos europeos"),
    },
}


def _cuentas(*textos):
    """{clave de epoca: cuantas de sus palabras salen en el texto}."""
    plegado = plegar(" ".join(str(t or "") for t in textos))
    cuenta = {}
    for clave, epoca in EPOCAS.items():
        n = sum(1 for p in epoca["palabras"] if _hay(plegado, p))
        if n:
            cuenta[clave] = n
    return cuenta


def epocas(*textos, cuantas=2, minimo=2):
    """Las epocas de las que habla el texto, de mas a menos. -> [clave]

    Un video biblico sin pistas de epoca se toma del siglo I: es el caso del
    canal (Hechos, los evangelios) y el error mas frecuente.

    `minimo=1` cuenta tambien la epoca que sale de pasada (un video del
    Gólgota que cita a David): es lo que quiere el catalogo, que tiene que
    vestir a CADA personaje con la suya.
    """
    cuenta = sorted(((n, c) for c, n in _cuentas(*textos).items()),
                    key=lambda par: (-par[0], list(EPOCAS).index(par[1])))
    elegidas = [clave for n, clave in cuenta if n >= minimo][:cuantas]
    if not elegidas and cuenta:
        elegidas = [cuenta[0][1]]
    return elegidas or ["nt"]


def epoca_de_personaje(nombre, ficha=""):
    """La epoca de UN personaje, o None si nada la delata. -> clave

    Primero por su NOMBRE (david, jesus, moises: es lo que no se equivoca) y
    solo si el nombre no dice nada, por su ficha. La ficha la escribe Claude y
    puede traer la epoca equivocada --«a first-century-style ... Israelite
    king» para David, medido en noviembre de 2026--, asi que no manda.
    """
    for texto in (nombre, ficha):
        cuenta = _cuentas(str(texto or "").replace("_", " "))
        if cuenta:
            return max(cuenta, key=lambda c: (cuenta[c], -list(EPOCAS).index(c)))
    return None


def _texto_ficha(ficha):
    if isinstance(ficha, dict):
        return " ".join(str(ficha.get(k) or "") for k in ("nombre", "papel",
                                                          "descripcion"))
    return str(ficha or "")


def epoca_del_plano(contexto, narracion="", personajes=(), fichas=None, que=""):
    """La epoca de ESTE plano, no la del video. -> clave

    Un video puede mezclar dos tiempos (David hacia el 1000 a. C. y la cruz en
    el siglo I) y la ficha de epoca iba igual en todos los planos: la de la
    mayoria. Aqui manda, por este orden, quien sale (su nombre), lo que se ve y
    donde, y lo que se narra; y si nada de eso dice nada, la epoca del video.
    """
    fichas = fichas or {}
    puntos = {}
    for nombre in personajes or ():
        clave = epoca_de_personaje(nombre, _texto_ficha(fichas.get(nombre)))
        if clave:
            puntos[clave] = puntos.get(clave, 0) + 3
    for peso, texto in ((2, que), (1, narracion)):
        for clave, n in _cuentas(str(texto or "").replace("_", " ")).items():
            puntos[clave] = puntos.get(clave, 0) + peso * n
    if puntos:
        return max(puntos, key=lambda c: (puntos[c], -list(EPOCAS).index(c)))
    return epocas(contexto)[0]


_SIGLO_I = re.compile(r"\bfirst[- ]century(?:[- ]style)?\b", re.I)


def ficha_en_su_epoca(nombre, ficha):
    """La ficha de un personaje sin una epoca que no es la suya. -> str

    Si el nombre delata otra epoca y la ficha dice «first-century», se cambia
    por la suya («Iron Age (around 1000 BC)»). No toca nada mas.
    """
    texto = str(ficha or "")
    clave = epoca_de_personaje(nombre)
    if not clave or clave == "nt" or not _SIGLO_I.search(texto):
        return texto
    return _SIGLO_I.sub(EPOCAS[clave]["ingles"], texto)


#: Lo que la costumbre dibuja mal en la crucifixion, segun los evangelios.
CRUZ = re.compile(r"\b(cruz|cruces|crucific\w*|golgota|calvario|cross)\b")
CRUCIFIXION = (
    "EN LA CRUCIFIXIÓN: en el Gólgota hay TRES cruces --Jesús en la del centro y "
    "un malhechor a cada lado (Lucas 23:33; Juan 19:18)--, salvo que el plano "
    "sea un primer plano que solo deje ver la de Jesús. Mientras Jesús está vivo "
    "y habla o grita («Elí, Elí, ¿lama sabactani?», «Consumado es») tiene la "
    "cabeza ERGUIDA o alzada al cielo; solo la inclina sobre el pecho al morir, "
    "después de su último grito (Juan 19:30). Nadie sonríe junto a la cruz salvo "
    "los que se burlan, y con sorna, no con alegría")


#: Reglas generales de todo video biblico (11-nov-2026, David). Solo es
#: TEXTO del encargo: no es un param y no mueve ninguna firma.
SIN_AUREOLA = ("NINGUNA AUREOLA: nadie lleva aureola, halo ni círculo de luz "
               "sobre la cabeza (ni Jesús, ni María, ni los apóstoles, ni los "
               "ángeles)")
ANGELES = (
    "LOS ÁNGELES, como los describe la Biblia (Marcos 16:5; Lucas 24:4; "
    "Hechos 1:10): HOMBRES con ropa blanca resplandeciente y un brillo suave, "
    "SIN alas y SIN aureola; nada de niños alados ni querubines de adorno. "
    "Solo llevan alas los serafines (Isaías 6:2) y los querubines (Ezequiel "
    "1 y 10) cuando el texto los nombra")
JESUS = (
    "JESÚS NUNCA DE FRENTE CON EL ROSTRO DETALLADO: de espaldas, a contraluz, "
    "en silueta o de lejos, sin rasgos de la cara definidos; lo que cuenta "
    "son sus gestos, su postura y la gente que lo rodea")
_ANGEL = re.compile(r"\b(angel|angeles|gabriel|miguel|serafin\w*|querubin\w*|"
                    r"angel of|angels?)\b")
_JESUS = re.compile(r"\b(jesus|jesucristo|cristo|mesias|nazareno|hijo del hombre)\b")


def reglas_sagradas(*textos):
    """Las reglas generales de un video biblico que tocan a este texto.

    La de la aureola va siempre; la de los angeles, si salen ángeles; la de
    Jesús, si sale Jesús. -> lista de frases (sin punto final)."""
    plegado = plegar(" ".join(str(t or "") for t in textos))
    reglas = [SIN_AUREOLA]
    if _ANGEL.search(plegado):
        reglas.append(ANGELES)
    if _JESUS.search(plegado):
        reglas.append(JESUS)
    return reglas


def _toca_cruz(*textos):
    return CRUZ.search(plegar(" ".join(str(t or "") for t in textos))) is not None


# ------------------------------------------------------- lugares y distancias

#: (nombre bonito, latitud, longitud, formas de escribirlo ya plegadas). Las
#: coordenadas son las del yacimiento o la ciudad actual; para el Sinai, la
#: tradicional (Jebel Musa). Las formas LARGAS van antes que las cortas: «belen
#: de galilea» no puede leerse ademas como «belen».
LUGARES = (
    ("Belén de Galilea", 32.735, 35.190, ("belen de galilea", "belen de zabulon")),
    ("Belén de Judea", 31.705, 35.200, ("belen de judea", "belen de juda", "belen")),
    ("Jerusalén", 31.778, 35.235, ("jerusalen",)),
    ("Nazaret", 32.699, 35.304, ("nazaret", "nazareth")),
    ("Capernaúm", 32.881, 35.575, ("capernaum", "cafarnaum")),
    ("Caná", 32.747, 35.339, ("cana de galilea", "bodas de cana", "boda de cana")),
    ("Naín", 32.632, 35.348, ("nain",)),
    ("Magdala", 32.825, 35.517, ("magdala",)),
    ("Betsaida", 32.910, 35.630, ("betsaida",)),
    ("Tiberíades", 32.794, 35.531, ("tiberiades",)),
    ("Cesarea de Filipo", 33.248, 35.694, ("cesarea de filipo",)),
    ("Cesarea Marítima", 32.500, 34.892, ("cesarea maritima", "cesarea")),
    ("Jericó", 31.871, 35.444, ("jerico",)),
    ("Betania", 31.771, 35.262, ("betania",)),
    ("Sicar (Siquem)", 32.213, 35.282, ("sicar", "siquem")),
    ("Samaria", 32.276, 35.197, ("samaria", "sebaste")),
    ("Hebrón", 31.532, 35.095, ("hebron",)),
    ("Betel", 31.930, 35.222, ("betel",)),
    ("Silo", 32.055, 35.290, ("silo",)),
    ("Gaza", 31.502, 34.467, ("gaza",)),
    ("Jope", 32.054, 34.752, ("jope", "jaffa")),
    ("Masada", 31.316, 35.354, ("masada",)),
    ("Qumrán", 31.741, 35.459, ("qumran",)),
    ("Damasco", 33.513, 36.292, ("damasco",)),
    ("Antioquía de Siria", 36.202, 36.160, ("antioquia de siria", "antioquia")),
    ("Tarso", 36.918, 34.895, ("tarso",)),
    ("Salamina (Chipre)", 35.185, 33.900, ("salamina", "chipre")),
    ("Éfeso", 37.941, 27.342, ("efeso",)),
    ("Patmos", 37.310, 26.546, ("patmos",)),
    ("Filipos", 41.013, 24.286, ("filipos",)),
    ("Tesalónica", 40.640, 22.944, ("tesalonica",)),
    ("Atenas", 37.972, 23.727, ("atenas",)),
    ("Corinto", 37.906, 22.878, ("corinto",)),
    ("Malta", 35.900, 14.450, ("malta",)),
    ("Roma", 41.893, 12.483, ("roma",)),
    ("Alejandría", 31.200, 29.918, ("alejandria",)),
    ("Monte Sinaí", 28.539, 33.975, ("monte sinai", "sinai", "horeb")),
    ("Babilonia", 32.536, 44.420, ("babilonia",)),
    ("Nínive", 36.359, 43.153, ("ninive",)),
    ("Ur de los caldeos", 30.962, 46.103, ("ur de los caldeos",)),
    ("Harán", 36.865, 39.031, ("haran", "harran")),
    ("Susa", 32.190, 48.257, ("susa",)),
)


def lugares_en(texto):
    """Los lugares que nombra el texto, en el orden en que aparecen. -> [(nombre, lat, lon)]

    «dos Belén» (o «otro Belén») da los dos: es justo la frase que pide el mapa.
    """
    plegado = plegar(texto)
    hallados, ocupado = [], []
    for nombre, lat, lon, formas in LUGARES:
        for forma in formas:
            for m in re.finditer(rf"\b{forma}\b", plegado):
                if any(a <= m.start() < b for a, b in ocupado):
                    continue
                ocupado.append((m.start(), m.end()))
                hallados.append((m.start(), nombre, lat, lon))
    if re.search(r"\b(dos|otro|ambos) belen|\bbelenes\b", plegado):
        for nombre, lat, lon, _ in LUGARES[:2]:
            hallados.append((10 ** 9, nombre, lat, lon))
    vistos, salida = set(), []
    for _, nombre, lat, lon in sorted(hallados):
        if nombre not in vistos:
            vistos.add(nombre)
            salida.append((nombre, lat, lon))
    return salida


def distancia_km(a, b):
    """Distancia en linea recta (haversine) entre dos (nombre, lat, lon)."""
    _, lat1, lon1 = a
    _, lat2, lon2 = b
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _km(valor):
    if valor < 20:
        return f"{round(valor)} km"
    paso = 5 if valor < 300 else 10
    return f"{int(round(valor / paso) * paso)} km"


def distancias(lugares, maximo=6):
    """Pares de lugares con su distancia, en frases: «Belén – Nazaret: 110 km»."""
    frases = []
    for i, a in enumerate(lugares):
        for b in lugares[i + 1:]:
            frases.append(f"{a[0]} – {b[0]}: unos {_km(distancia_km(a, b))} "
                          f"en línea recta")
            if len(frases) >= maximo:
                return frases
    return frases


# ----------------------------------------------- lo que explica cada frase

FECHAS = re.compile(r"\b(año|años|siglo|siglos|antes de cristo|despues de "
                    r"cristo|a c|d c|reinado)\b")
MEDIDAS = re.compile(r"\b(kilometros?|km|millas?|estadios?|leguas?|codos?|"
                     r"dias de camino|dia de camino|jornadas?)\b")


def explicar(narracion):
    """Que tiene que EXPLICAR la imagen de esta frase, o "" si es una escena normal.

    No adivina el dibujo: dice el dato que la frase cuenta (los lugares y su
    distancia, una fecha, una medida) para que la imagen lo ENSENE.
    """
    texto = str(narracion or "")
    plegado = plegar(texto)
    lugares = lugares_en(texto)
    partes = []
    if len(lugares) >= 2:
        nombres = ", ".join(n for n, _, _ in lugares[:5])
        partes.append(
            f"esta frase compara lugares: dibuja un MAPA sencillo de la zona "
            f"(vista desde arriba, costa y ríos reconocibles) con {nombres} "
            f"marcados con un punto y su nombre, y una línea entre ellos con "
            f"la distancia ({'; '.join(distancias(lugares[:5], 3))})")
    elif MEDIDAS.search(plegado):
        partes.append("esta frase da una distancia o medida: enséñala (una "
                      "flecha o un camino con la cifra, o la comparación a "
                      "escala)")
    if FECHAS.search(plegado) and not partes:
        partes.append("esta frase sitúa en el tiempo: que se note la época "
                      "(y si ayuda, una línea de tiempo sencilla con el "
                      "momento marcado)")
    return "; ".join(partes)


def pide_rotulos(narracion):
    """True si la imagen de esta frase necesita nombres escritos (un mapa)."""
    return len(lugares_en(narracion)) >= 2


# ------------------------------------------------------------ los bloques

def _ficha_epoca(clave):
    e = EPOCAS[clave]
    return (f"· ÉPOCA: {e['nombre']}.\n"
            f"  Gente: {e['gente']}.\n"
            f"  Ropa: {e['ropa']}.\n"
            f"  Sitios: {e['sitios']}.\n"
            f"  Objetos: {e['objetos']}.\n"
            f"  NO dibujar: {e['evita']}.")


def pauta_claude(*textos, para="catalogo"):
    """El bloque de fidelidad para el encargo a Claude, o "" si no es biblico.

    `para`: "catalogo" (reparto y sitios), "planos" (direccion / redactor).
    """
    if not es_biblico(*textos):
        return ""
    claves = epocas(*textos, cuantas=3, minimo=1)
    lugares = lugares_en(" ".join(str(t or "") for t in textos))
    lineas = [
        "=====================================================================",
        "FIDELIDAD HISTÓRICA Y BÍBLICA (este vídeo es de tema bíblico)",
        "=====================================================================",
        "Todo lo que se dibuja tiene que ser como lo describen las fuentes "
        "serias -- el texto bíblico (Reina-Valera 1960) y la arqueología e "
        "historia de la época --, NO como lo pinta la costumbre europea. Nada "
        "inventado: si el texto no lo dice y la historia no lo sabe, se "
        "dibuja lo sencillo y típico de la época, no un adorno.",
    ]
    for clave in claves:
        lineas.append(_ficha_epoca(clave))
    if len(claves) > 1:
        lineas.append(
            "ESTE VÍDEO MEZCLA ÉPOCAS. La época NO es una para todo el vídeo: "
            "va con cada personaje, cada sitio y cada plano. David, Saúl o "
            "Salomón son de la Edad del Hierro (hacia el 1000 a. C.) y visten, "
            "viven y escriben como entonces aunque el vídeo hable de Jesús; "
            "Jesús y los apóstoles, del siglo I. Nunca escribas «first-century» "
            "en un personaje o un sitio de otra época.")
    if para == "catalogo":
        lineas.append(
            "En el REPARTO, cada `descripcion` escribe esto en inglés: origen "
            "y aspecto de SU época (p. ej. «a first-century Galilean Jewish "
            "man, olive-brown skin, dark curly short hair, short dark beard» "
            "para un apóstol, o «an Iron Age Israelite king, around 1000 BC» "
            "para David), edad, y la ropa de esa época con sus colores. En los "
            "SITIOS, la arquitectura, materiales y paisaje reales del lugar y "
            "la época. Si un personaje es conocido, su papel según el texto "
            "bíblico.")
    else:
        lineas.append(
            "En cada plano, lo que se ve es de la época (gente, ropa, sitio, "
            "objetos), y la imagen EXPLICA lo que cuenta su frase: si compara "
            "lugares, un mapa sencillo con esos lugares rotulados y la "
            "distancia; si da una fecha, que se note la época o una línea de "
            "tiempo; si cita un versículo, la escena que ese versículo "
            "describe, tal como lo describe. Los nombres de un mapa cuentan "
            "como rótulos permitidos (cortos y en el idioma del vídeo). La "
            "cara de cada plano va con SU momento: junto a la cruz, en el dolor "
            "o en la burla, nada de caras relajadas ni sonrisas (los que se "
            "burlan, con sorna).")
    lineas.extend(r + "." for r in reglas_sagradas(*textos))
    if "nt" in claves and _toca_cruz(*textos):
        lineas.append(CRUCIFIXION + ".")
    if len(lugares) >= 2:
        lineas.append("Lugares que nombra el guion y sus distancias reales "
                      "(úsalas tal cual si hace falta una cifra):")
        lineas.extend(f"  - {f}" for f in distancias(lugares, 8))
    return "\n".join(lineas) + "\n"


def pauta_guion(*textos):
    """La regla del guion biblico (Reina-Valera 1960), o "" si no es biblico."""
    if not es_biblico(*textos):
        return ""
    return (
        "== FIDELIDAD BÍBLICA (este vídeo es de tema bíblico) ==\n"
        "- Las citas bíblicas, LITERALES de la Reina-Valera 1960, con su libro, "
        "capítulo y versículo correctos («Mateo dos, uno»). Si no estás seguro "
        "de la letra exacta, cuéntalo con tus palabras y di dónde está, pero "
        "no inventes una cita.\n"
        "- Los hechos, como los cuenta la Biblia (RV1960) y la historia seria. "
        "Lo que viene de la tradición o de una leyenda («los tres reyes», «la "
        "manzana») se dice como tal («la tradición dice…») o se corrige, nunca "
        "se da por bíblico.\n"
        "- Nombres de personas y lugares como en la RV1960 (Capernaúm, Jope, "
        "Belén de Judea).\n"
        # CITAR EN VOZ ALTA (8-nov-2026, David): «MATEO 27 VERSICULO 46 Y LA
        # GENTE» y luego «SALMOS 22 7 Y 8 SE BURLAN» -- citas encadenadas sin
        # contar quien habla ni por que importa. El estudio ya escribe la cita
        # en pantalla («Mateo 27:46», `citas.py`): la voz tiene que CONTAR.
        "\n== CÓMO SE CITA LA BIBLIA EN VOZ ALTA ==\n"
        "Cada cita va en TRES pasos, en este orden, y nunca falta ninguno:\n"
        "  1. EL MOMENTO: quién habla, a quién y qué está pasando («Ya en la "
        "cruz, a media tarde, Jesús gritó con fuerza…»).\n"
        "  2. LA CITA: el libro y el capítulo dichos de forma natural, UNA vez, "
        "y el texto literal entre comillas («…está en Mateo, capítulo "
        "veintisiete, versículo cuarenta y seis: «Dios mío, Dios mío, ¿por qué "
        "me has desamparado?»»). En pantalla se escribe solo como «Mateo "
        "27:46».\n"
        "  3. QUÉ SIGNIFICA, con palabras de todos los días, y por qué importa "
        "para la historia («No era un grito de derrota: era el comienzo del "
        "Salmo veintidós, y todos los judíos que lo oyeron lo sabían.»).\n"
        "- NUNCA dos citas seguidas sin explicar la primera. Si una profecía se "
        "cumple, dilo claro: primero lo que pasó, luego «mil años antes, David "
        "ya lo había escrito en el Salmo veintidós: «…»», y luego la conexión.\n"
        "- Nada de referencias sueltas sin su texto («Salmo veintidós, siete y "
        "ocho») ni de leer números de versículos que no se van a citar.\n"
        "- Como mucho una cita por bloque y, en un vídeo corto, dos o tres en "
        "todo el vídeo: las que mejor cuentan la historia.")


def pauta_imagen(contexto, narracion="", con_gente=True, personajes=(),
                 fichas=None, que=""):
    """Las lineas del prompt para copiar (modo manual), o [] si no es biblico.

    `contexto` es el texto de todo el video; `narracion`, la frase del plano;
    `personajes`/`fichas`/`que`, quien sale y lo que se ve. La epoca es la DEL
    PLANO (`epoca_del_plano`), no la del video. Sin nada del plano (el prompt
    unico) y con un video que mezcla tiempos, se dicen todas y que cada uno
    va con la suya.
    """
    if not es_biblico(contexto):
        return []
    del_plano = bool(narracion or personajes or que)
    if not del_plano and len(epocas(contexto, cuantas=3, minimo=1)) > 1:
        claves = epocas(contexto, cuantas=3, minimo=1)
        lineas = ["ÉPOCAS (este vídeo mezcla tiempos; cada personaje, sitio e "
                  "imagen con LA SUYA, fiel a la historia y a la Biblia):"]
        for clave in claves:
            e = EPOCAS[clave]
            lineas.append(f"- {e['nombre']}. Sitios: {e['sitios']}. Objetos: "
                          f"{e['objetos']}." + (f" Personas: {e['gente']}. Ropa: "
                                               f"{e['ropa']}." if con_gente else "")
                          + f" No dibujes: {e['evita']}.")
        lineas.extend(r + "." for r in reglas_sagradas(contexto))
        if "nt" in claves and _toca_cruz(contexto):
            lineas.append(CRUCIFIXION + ".")
        return lineas
    clave = epoca_del_plano(contexto, narracion, personajes, fichas, que)
    e = EPOCAS[clave]
    lineas = [f"ÉPOCA (fiel a la historia y a la Biblia, nada inventado): "
              f"{e['nombre']}. Sitios: {e['sitios']}. Objetos: {e['objetos']}."]
    if con_gente:
        lineas.append(f"PERSONAS DE LA ÉPOCA: {e['gente']}. Ropa: {e['ropa']}.")
        otros = []
        for nombre in personajes or ():
            suya = epoca_de_personaje(nombre, _texto_ficha((fichas or {}).get(nombre)))
            if suya and suya != clave:
                otros.append(f"{nombre}: {EPOCAS[suya]['nombre']}")
        if otros:
            lineas.append("CADA UNO CON SU ÉPOCA (aunque salgan juntos): "
                          + "; ".join(otros) + ".")
    lineas.append(f"NO DIBUJES: {e['evita']}.")
    lineas.extend(r + "." for r in reglas_sagradas(contexto, narracion, que,
                                                   " ".join(personajes or ())))
    if clave == "nt" and _toca_cruz(narracion, que):
        lineas.append(CRUCIFIXION + ".")
    que = explicar(narracion)
    if que:
        lineas.append(f"EXPLICA LO QUE SE CUENTA: {que}.")
    return lineas


def insertar(instruccion, bloque, antes_de):
    """Mete `bloque` justo antes de `antes_de` (o al final si no esta)."""
    if not bloque:
        return instruccion
    sitio = instruccion.find(antes_de) if antes_de else -1
    if sitio < 0:
        return instruccion.rstrip() + "\n\n" + bloque
    return instruccion[:sitio] + bloque + "\n" + instruccion[sitio:]
