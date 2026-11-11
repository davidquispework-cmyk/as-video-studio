"""
La mejor voz GRATUITA para un video, elegida por su TEMA.

Para que
--------
Con la voz gratis, todos los videos salian con la misma voz (la del estilo o la
de Configuracion), contaran una crucifixion, un cuento para ninos o un misterio.
Aqui el estudio lee de que va el video (el guion; si aun no hay, el material) y
elige la voz que mejor le va. Sin llamar a Claude: es una cuenta de palabras de
un segundo y no gasta nada del plan.

Cuando se elige, y por que solo entonces
----------------------------------------
UNA VEZ, la primera vez que se locuta el video (`app._voz_por_tema`), y se
GUARDA en los params de la voz. Si se eligiera en cada locucion, regrabar un
bloque con el guion retocado podria cambiar de voz a media pieza. Guardada
antes de la primera toma no deja nada obsoleto: aun no hay nada debajo.

No pisa nunca una voz elegida a mano en el video (`voz_a_mano`), y se apaga en
Configuracion (`ajustes.voz_por_tema`). Solo castellano: en otros idiomas se
queda la voz de siempre.
"""
import re
import unicodedata

#: Los temas: palabras que lo delatan (raices plegadas, sin tildes), como
#: tiene que sonar y si va mejor una voz de hombre o de mujer (None = da igual).
TEMAS = {
    "infantil": {
        "nombre": "para niños",
        "raices": ("nino", "nina", "ninos", "peque", "infantil", "cuento",
                   "juguete", "colegio", "escuela", "dibujo", "osito", "travies"),
        "rasgos": ("alegre", "cercana", "clara"), "genero": "female"},
    "fe": {
        "nombre": "bíblico / de fe",
        "raices": ("dios", "jesus", "cristo", "biblia", "biblic", "senor", "fe ",
                   "oracion", "orar", "salmo", "apostol", "profeta", "iglesia",
                   "evangeli", "espiritu", "versiculo", "gracia", "pecado",
                   "israel", "moises", "david", "pablo", "pedro", "cruz"),
        "rasgos": ("calida", "serena", "grave"), "genero": "male"},
    "misterio": {
        "nombre": "misterio / suspense",
        "raices": ("misterio", "crimen", "asesin", "desaparec", "secreto",
                   "enigma", "oscur", "terror", "leyenda", "fantasma", "maldic",
                   "investigac", "sospech", "nadie sabe", "inexplicable"),
        "rasgos": ("grave", "seria", "intensa"), "genero": "male"},
    "historia": {
        "nombre": "historia / documental",
        "raices": ("historia", "siglo", "imperio", "guerra", "batalla", "rey ",
                   "reina", "antigu", "civilizac", "conquist", "emperador",
                   "revoluc", "dinastia", "ejercito", "milenio"),
        "rasgos": ("autoridad", "grave", "clara"), "genero": "male"},
    "motivacion": {
        "nombre": "motivación / crecimiento",
        "raices": ("exito", "meta", "suen", "logr", "motiva", "super", "disciplin",
                   "habito", "productiv", "dinero", "negocio", "emprend",
                   "tu vida", "cambia tu", "mentalidad"),
        "rasgos": ("energica", "segura", "cercana"), "genero": None},
    "ciencia": {
        "nombre": "ciencia / tecnología",
        "raices": ("ciencia", "cientific", "tecnolog", "universo", "planeta",
                   "cerebro", "estudio", "inteligencia artificial", "espacio",
                   "fisica", "quimic", "biolog", "experiment", "datos"),
        "rasgos": ("clara", "segura", "joven"), "genero": None},
}

#: Sin tema claro: un documental narrado.
TEMA_POR_DEFECTO = {"nombre": "documental", "rasgos": ("clara", "autoridad", "calida"),
                    "genero": "male"}

#: Lo que el tono dominante (`intencion.tono_automatico` del guion entero) suma
#: a lo que pide el tema: una historia triste pide una voz serena aunque sea
#: de historia.
POR_TONO = {
    "sad": ("serena", "calida"),
    "calm": ("serena", "calida"),
    "scared": ("grave", "intensa"),
    "angry": ("intensa", "segura"),
    "content": ("alegre", "cercana"),
}

#: Las voces gratuitas en castellano, oidas y descritas a mano: las etiquetas
#: de Microsoft dicen «Friendly, Positive» de casi todas y no sirven para
#: decidir. Acento latino primero (el publico del canal es de Peru y Latam).
VOCES_ES = {
    "es-MX-JorgeNeural": ("male", "México", ("calida", "cercana", "clara", "autoridad")),
    "es-CO-GonzaloNeural": ("male", "Colombia", ("grave", "serena", "calida", "autoridad")),
    "es-US-AlonsoNeural": ("male", "Estados Unidos", ("grave", "seria", "intensa", "autoridad")),
    "es-PE-AlexNeural": ("male", "Perú", ("cercana", "joven", "clara", "segura")),
    "es-AR-TomasNeural": ("male", "Argentina", ("energica", "cercana", "joven")),
    "es-VE-SebastianNeural": ("male", "Venezuela", ("energica", "segura", "clara")),
    "es-CL-LorenzoNeural": ("male", "Chile", ("seria", "clara")),
    "es-ES-AlvaroNeural": ("male", "España", ("seria", "autoridad", "clara")),
    "es-MX-DaliaNeural": ("female", "México", ("clara", "cercana", "alegre")),
    "es-CO-SalomeNeural": ("female", "Colombia", ("calida", "serena", "cercana")),
    "es-PE-CamilaNeural": ("female", "Perú", ("calida", "cercana", "clara")),
    "es-US-PalomaNeural": ("female", "Estados Unidos", ("clara", "serena", "segura")),
    "es-AR-ElenaNeural": ("female", "Argentina", ("alegre", "energica", "cercana")),
    "es-ES-ElviraNeural": ("female", "España", ("clara", "seria")),
    "es-ES-XimenaNeural": ("female", "España", ("joven", "alegre")),
}

#: Cuantas veces tiene que salir el tema para fiarse de el.
MINIMO = 2


def _plegar(texto):
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " " + re.sub(r"[^a-z ]+", " ", re.sub(r"<[^<>]*>", " ", texto)) + " "


def tema_de(texto):
    """El tema del video por sus palabras -> (id o None, cuentas)."""
    plano = _plegar(texto)
    cuentas = {tid: sum(plano.count(" " + r) for r in t["raices"])
               for tid, t in TEMAS.items()}
    orden = sorted(cuentas.items(), key=lambda kv: -kv[1])
    (mejor, n1), (_otro, n2) = orden[0], orden[1]
    if n1 >= MINIMO and n1 > n2:
        return mejor, cuentas
    return None, cuentas


def _tono(texto):
    try:
        from . import intencion
    except ImportError:
        import intencion
    return intencion.tono_automatico(texto)


def elegir(texto, idioma="es", disponibles=None):
    """La voz que mejor le va a este texto -> dict, o None si no se decide.

    `disponibles`: ids del catalogo de verdad; una voz que no este no se elige
    (con el catalogo vacio --sin red-- vale la tabla entera).
    """
    if str(idioma or "es").strip().lower() != "es" or not str(texto or "").strip():
        return None
    tid, _cuentas = tema_de(texto)
    tema = TEMAS[tid] if tid else TEMA_POR_DEFECTO
    tono = _tono(texto)
    pedidos = list(tema["rasgos"]) + list(POR_TONO.get(tono, ()))
    validas = set(disponibles or ())

    def puntos(item):
        vid, (genero, pais, rasgos) = item
        p = sum(2 if i < len(tema["rasgos"]) else 1
                for i, r in enumerate(pedidos) if r in rasgos)
        if tema["genero"] and genero == tema["genero"]:
            p += 2
        if pais == "España":
            p -= 1
        return p

    candidatas = [(v, f) for v, f in VOCES_ES.items() if not validas or v in validas]
    if not candidatas:
        return None
    # max() se queda con la primera en empate: el orden de la tabla decide
    voz, (genero, pais, rasgos) = max(candidatas, key=puntos)
    nombre = re.sub(r"(?<=[a-z])(?=[A-Z])", " ",
                    voz.split("-")[-1].replace("Neural", ""))
    return {
        "voz_id": voz,
        "voz_nombre": f"{nombre} ({pais})",
        "tema": tid or "documental",
        "tono": tono,
        "por_que": (f"tema {tema['nombre']}" + (f", tono {tono}" if tono != "neutral" else "")
                    + f": voz {', '.join(rasgos[:3])}"),
    }
