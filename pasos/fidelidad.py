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
                  "aureolas doradas (salvo que lo pida el estilo); cruces "
                  "como adorno o en iglesias; cúpulas y minaretes (son siglos "
                  "posteriores); libros encuadernados, cristal en ventanas, "
                  "pantalones, metal moderno"),
    },
    "patriarcas": {
        "nombre": "los patriarcas (hacia 2000-1700 a. C.), Canaán y Mesopotamia",
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
        "palabras": ("rey david", "david", "saul", "salomon", "goliat",
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


def epocas(*textos, cuantas=2):
    """Las epocas de las que habla el texto, de mas a menos. -> [clave]

    Un video biblico sin pistas de epoca se toma del siglo I: es el caso del
    canal (Hechos, los evangelios) y el error mas frecuente.
    """
    plegado = plegar(" ".join(str(t or "") for t in textos))
    cuenta = []
    for clave, epoca in EPOCAS.items():
        n = sum(1 for p in epoca["palabras"] if _hay(plegado, p))
        if n:
            cuenta.append((n, clave))
    cuenta.sort(key=lambda par: (-par[0], list(EPOCAS).index(par[1])))
    elegidas = [clave for n, clave in cuenta if n >= 2][:cuantas]
    if not elegidas and cuenta:
        elegidas = [cuenta[0][1]]
    return elegidas or ["nt"]


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
    claves = epocas(*textos)
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
    if para == "catalogo":
        lineas.append(
            "En el REPARTO, cada `descripcion` escribe esto en inglés: origen "
            "y aspecto de la época (p. ej. «a first-century Galilean Jewish "
            "man, olive-brown skin, dark curly short hair, short dark beard»), "
            "edad, y la ropa de la época con sus colores. En los SITIOS, la "
            "arquitectura, materiales y paisaje reales del lugar y la época. "
            "Si un personaje es conocido, su papel según el texto bíblico.")
    else:
        lineas.append(
            "En cada plano, lo que se ve es de la época (gente, ropa, sitio, "
            "objetos), y la imagen EXPLICA lo que cuenta su frase: si compara "
            "lugares, un mapa sencillo con esos lugares rotulados y la "
            "distancia; si da una fecha, que se note la época o una línea de "
            "tiempo; si cita un versículo, la escena que ese versículo "
            "describe, tal como lo describe. Los nombres de un mapa cuentan "
            "como rótulos permitidos (cortos y en el idioma del vídeo).")
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
        "Belén de Judea).")


def pauta_imagen(contexto, narracion="", con_gente=True):
    """Las lineas del prompt para copiar (modo manual), o [] si no es biblico.

    `contexto` es el texto de todo el video (para decidir epoca); `narracion`,
    la frase del plano (para lo que hay que explicar).
    """
    if not es_biblico(contexto):
        return []
    e = EPOCAS[epocas(contexto, narracion, cuantas=1)[0]]
    lineas = [f"ÉPOCA (fiel a la historia y a la Biblia, nada inventado): "
              f"{e['nombre']}. Sitios: {e['sitios']}. Objetos: {e['objetos']}."]
    if con_gente:
        lineas.append(f"PERSONAS DE LA ÉPOCA: {e['gente']}. Ropa: {e['ropa']}.")
    lineas.append(f"NO DIBUJES: {e['evita']}.")
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
