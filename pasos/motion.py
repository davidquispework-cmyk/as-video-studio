"""
MOTION GRAPHICS (punto G, primera parte; incluye el punto D de las notas).

Un ESTILO OPCIONAL del render: en vez de una imagen con zoom por plano, el video
es UN SOLO MUNDO VECTORIAL por el que viaja la camara. Cada plano tiene su
«parada» en ese mundo; al empezar un plano la camara VIAJA desde la parada
anterior (se aleja un poco a mitad de viaje para que se vea de donde viene y a
donde va, y un camino de puntos une las dos) y lo dibujado en los planos
anteriores SE QUEDA donde estaba. No hay cortes: el ultimo fotograma de un
plano y el primero del siguiente son el mismo sitio del mundo, asi que entre
planos no se cuece ninguna transicion.

Cada plano lleva su pieza, y cada parte de la pieza entra cuando la voz dice su
palabra (tiempos de `escena["marcas"]`, los mismos que el subtitulo):
    versiculo   tarjeta con la cita LITERAL (RVR1960) que se va entintando
                palabra a palabra, la referencia en su pastilla y la Biblia que
                se abre con destellos
    reloj       esfera con la PORCION de horas que se rellena (hora tercera,
                sexta, novena... = 9, 12, 15 h; «N horas al dia» sobre 24 h)
    mapa        los lugares (pasos/fidelidad.py) con chinchetas que caen, la
                ruta que se dibuja y la DISTANCIA real contando
    linea       linea de tiempo con los años, el puntero que viaja y «N años»
    lamina      la imagen del plano como lamina enmarcada (si no hay otra
                cosa que explicar), con iconos que saltan al decir su palabra
    texto/icono piezas sueltas para el storyboard escrito a mano
Todas entran con resorte (se pasan y vuelven), estiramiento al moverse y
aplastamiento al llegar; luego pueden TRANSFORMARSE (`luego`) y se quedan.

Como se gobierna:
    params del render  "motion": true | "papel" | "noche"
                       | {"tema": "papel", "laminas": false}
                       | {"tema": "papel", "imagenes": false}   (todo dibujado: ver sin_imagenes)
                       Falta = el render de siempre. No va en los defectos del
                       paso: no mueve la firma de ningun proyecto.
    plan.json, escena  "motion": [ {pieza}, ... ]   el storyboard de ese plano
                       "motion": false              solo la lamina
                       Una pieza: {"tipo": "texto", "texto": "El *AMOR* vence",
                       "x": .5, "y": .3, "en": "amor", "entra": "arriba",
                       "luego": [{"en": "vence", "y": .2, "escala": .8}]}
                       (`en` = segundos del plano o una palabra de la voz)
Todo se calcula aqui, en Python, con tiempos del VIDEO ENTERO; la pagina de
cada plano (p8_render.PAGINA) pinta el mundo en el instante t_in + t con
MOTION_JS, sin reloj de pared: el mismo fotograma sale igual en cualquier lote.
"""
import json
import math
import re
from datetime import date

try:
    import citas
    import fidelidad
    import motion_mas
    import escenarios
except ImportError:  # importado como paquete (pasos.motion)
    from . import citas, fidelidad, motion_mas, escenarios

TEMAS = {
    # DISEÑO PROPIO: papel claro con tinta índigo (no negra) y acentos vivos
    # que se ven en el móvil; «noche» para historias de miedo o de noche.
    "papel": {"fondo1": "#FFF6E6", "fondo2": "#EDD3AE", "tinta": "#241C3A",
              "papel": "#FFFCF4", "acento": "#E8402E", "acento2": "#15968A",
              "oro": "#F2A922", "cielo": "#6CB8EA", "mar": "#A9D8EE",
              "tierra": "#F6E7C8", "suave": "#B79E7C", "puntos": "#D8BE98"},
    "noche": {"fondo1": "#2C2560", "fondo2": "#0E0B22", "tinta": "#FBF1DD",
              "papel": "#2A2452", "acento": "#FF5E4D", "acento2": "#3FD6C4",
              "oro": "#FFC845", "cielo": "#7CC4FF", "mar": "#253F78",
              "tierra": "#3A3270", "suave": "#8D84C6", "puntos": "#3E3680"},
}
FUENTES = {"titulo": "Shaddai Montserrat", "verso": "Shaddai Playfair"}
TIPOS = ("versiculo", "reloj", "mapa", "linea", "lamina", "texto", "icono",
         "contador", "comparacion", "lista",
         # segunda parte (pasos/motion_mas.py)
         "barras", "antes", "arbol", "flecha", "circulo", "personajes", "escenario")
ENTRADAS = ("abajo", "arriba", "izquierda", "derecha", "pop", "nada")
ICONOS = ("cruz", "corazon", "biblia", "moneda", "celular", "corona", "paloma",
          "casa", "vela", "estrella", "pan", "cadena", "pergamino", "reloj",
          "ojo", "mano", "llave", "puerta", "montana", "sol", "luna", "nube",
          "gota", "fuego", "arbol", "pez", "barca", "oveja", "espada", "escudo",
          "trompeta", "tablas", "templo", "tumba", "lupa", "balanza", "ancla",
          "copa", "persona", "chincheta", "arena", "pregunta", "check", "equis",
          "flecha", "punto") + motion_mas.ICONOS_MAS

# palabra (plegada, principio) -> icono que salta junto a la lamina
PALABRAS_ICONO = (
    ("cruz", ("cruz", "crucific", "calvario", "golgota")),
    ("corazon", ("corazon", "amor", "amo ", "ama ", "amar", "aman")),
    ("biblia", ("biblia", "escritura", "evangelio", "palabra de dios")),
    ("moneda", ("dinero", "moneda", "plata", "denario", "riqueza",
                "tesoro", "pago", "precio")),
    ("celular", ("celular", "movil", "telefono", "redes", "pantalla")),
    ("corona", ("rey ", "reyes", "reina", "corona", "reino", "trono")),
    ("paloma", ("espiritu", "paloma", "paz ")),
    ("casa", ("casa", "hogar", "familia")),
    ("vela", ("luz ", "lampara", "vela", "brill")),
    ("estrella", ("estrella", "magos", "cielo")),
    ("pan", ("pan ", "panes", "comida", "hambre", "cena")),
    ("cadena", ("pecado", "cadena", "esclav", "carcel", "preso")),
    ("tablas", ("mandamiento", "ley ", "tablas", "moises")),
    ("pergamino", ("profec", "carta", "rollo", "pergamino", "escrib")),
    ("reloj", ("tiempo", "pronto", "tarde")),
    ("ojo", ("ojo", "mirar", "miro", "vio ", "ver ", "ciego", "vista")),
    ("mano", ("mano", "manos", "toco", "tocar", "sano")),
    ("llave", ("llave", "abrir", "abrio", "secreto")),
    ("puerta", ("puerta", "entrar", "entro")),
    ("montana", ("monte", "montana", "cerro", "sinai")),
    ("sol", ("sol ", "amanec", "manana", "luz del dia")),
    ("luna", ("luna", "noche", "oscur", "tiniebla")),
    ("nube", ("nube", "tormenta", "viento")),
    ("gota", ("agua", "lluvia", "rio ", "bautiz", "llor", "lagrima", "sed ")),
    ("fuego", ("fuego", "llama", "ardi", "infierno", "zarza")),
    ("arbol", ("arbol", "higuera", "olivo", "vid ", "fruto", "semilla", "jardin")),
    ("pez", ("pez ", "peces", "pesca", "red ", "redes de")),
    ("barca", ("barca", "barco", "mar ", "naveg", "arca")),
    ("oveja", ("oveja", "pastor", "cordero", "rebano")),
    ("espada", ("espada", "guerra", "batalla", "pelea", "lucha")),
    ("escudo", ("escudo", "proteg", "fe ", "armadura")),
    ("trompeta", ("trompeta", "anunci", "alarma")),
    ("templo", ("templo", "sinagoga", "iglesia", "altar")),
    ("tumba", ("tumba", "sepulcro", "muerte", "muri", "resucit")),
    ("lupa", ("buscar", "busca", "investig", "descubr", "detalle")),
    ("balanza", ("justicia", "juicio", "juez", "justo")),
    ("ancla", ("esperanza", "ancla", "firme")),
    ("copa", ("copa", "vino", "caliz", "beber")),
    ("pregunta", ("por que", "pregunta", "duda")),
)

LIBROS = (
    ("genesis", "Génesis"), ("exodo", "Éxodo"), ("levitico", "Levítico"),
    ("numeros", "Números"), ("deuteronomio", "Deuteronomio"), ("josue", "Josué"),
    ("jueces", "Jueces"), ("rut", "Rut"), ("samuel", "Samuel"), ("reyes", "Reyes"),
    ("cronicas", "Crónicas"), ("esdras", "Esdras"), ("nehemias", "Nehemías"),
    ("ester", "Ester"), ("job", "Job"), ("salmos", "Salmos"), ("salmo", "Salmos"),
    ("proverbios", "Proverbios"), ("eclesiastes", "Eclesiastés"),
    ("cantares", "Cantares"), ("isaias", "Isaías"), ("jeremias", "Jeremías"),
    ("lamentaciones", "Lamentaciones"), ("ezequiel", "Ezequiel"),
    ("daniel", "Daniel"), ("oseas", "Oseas"), ("joel", "Joel"), ("amos", "Amós"),
    ("abdias", "Abdías"), ("jonas", "Jonás"), ("miqueas", "Miqueas"),
    ("nahum", "Nahúm"), ("habacuc", "Habacuc"), ("sofonias", "Sofonías"),
    ("hageo", "Hageo"), ("zacarias", "Zacarías"), ("malaquias", "Malaquías"),
    ("mateo", "Mateo"), ("marcos", "Marcos"), ("lucas", "Lucas"), ("juan", "Juan"),
    ("hechos", "Hechos"), ("romanos", "Romanos"), ("corintios", "Corintios"),
    ("galatas", "Gálatas"), ("efesios", "Efesios"), ("filipenses", "Filipenses"),
    ("colosenses", "Colosenses"), ("tesalonicenses", "Tesalonicenses"),
    ("timoteo", "Timoteo"), ("tito", "Tito"), ("filemon", "Filemón"),
    ("hebreos", "Hebreos"), ("santiago", "Santiago"), ("pedro", "Pedro"),
    ("judas", "Judas"), ("apocalipsis", "Apocalipsis"),
)
NUMEROS = {"un": 1, "una": 1, "uno": 1, "primera": 1, "primer": 1, "primero": 1,
           "dos": 2, "segunda": 2, "segundo": 2, "tres": 3, "tercera": 3,
           "tercer": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
           "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
           "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
           "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20,
           "veintiuno": 21, "veintidos": 22, "veintitres": 23,
           "veinticuatro": 24}
HORAS_JUDIAS = {"primera": 1, "tercera": 3, "sexta": 6, "novena": 9,
                "undecima": 11, "duodecima": 12}
VACIAS = set("""el la los las un una unos unas de del al a y o que en por para con
sin su sus mi mis tu tus se lo le les es son fue ser era no si ya mas muy pero
como cuando donde porque este esta estos estas ese esa eso nos me te yo tu el
ella ellos ellas hay sobre entre hasta desde todo toda todos todas""".split())

_NUM = r"(\d{1,3}|" + "|".join(sorted(NUMEROS, key=len, reverse=True)) + r")"


def _n(palabra):
    palabra = str(palabra)
    return int(palabra) if palabra.isdigit() else NUMEROS.get(palabra)


# ------------------------------------------------------------ parametros

def tema_de(p):
    """El tema pedido en los params del render, o None (= sin motion)."""
    v = (p or {}).get("motion")
    if isinstance(v, dict):
        if v.get("activo") is False:
            return None
        v = v.get("tema") or True
    if not v:
        return None
    return v if isinstance(v, str) and v in TEMAS else "papel"


def _opciones(p):
    v = (p or {}).get("motion")
    return v if isinstance(v, dict) else {}


def sin_imagenes(p):
    """¿Video TODO DIBUJADO? Opcion `motion: {"imagenes": false}` del render:
    ningun plano pide imagen (ni se sube ni se paga) y cada uno lleva su
    escenario dibujado (pasos/escenarios.py). Solo existe con motion graphics:
    sin motion no hay nada que dibujar en su lugar. Lo lee tambien el paso de
    imagenes al GENERAR (p6_assets.todo_dibujado), sin escribirlo en sus params:
    encenderla no deja obsoleta ninguna imagen ya hecha."""
    return bool(tema_de(p)) and _opciones(p).get("imagenes") is False


# ------------------------------------------------------------ las palabras

class Voz:
    """Las palabras de un plano con su tiempo (del VIDEO) y su forma plegada."""

    def __init__(self, escena):
        self.t_in = float(escena.get("t_in") or 0.0)
        self.t_out = float(escena.get("t_out") or self.t_in + 1.0)
        self.crudas = str(escena.get("narracion") or "").split()
        marcas = escena.get("marcas") or []
        n = len(self.crudas)
        if n and len(marcas) == n:
            try:
                self.tiempos = [(float(a), float(b)) for a, b in marcas]
            except (TypeError, ValueError):
                self.tiempos = None
        else:
            self.tiempos = None
        if self.tiempos is None:
            # sin marcas que cuadren se reparte a partes iguales: la pieza
            # sale igual, solo menos clavada a la voz
            paso = (self.t_out - self.t_in) / max(1, n)
            self.tiempos = [(self.t_in + paso * i, self.t_in + paso * (i + 1))
                            for i in range(n)]
        self.plegadas = [fidelidad.plegar(p) for p in self.crudas]
        # el texto plegado entero y donde empieza cada palabra en el
        partes, self.inicios, pos = [], [], 0
        for pl in self.plegadas:
            self.inicios.append(pos)
            partes.append(pl)
            pos += len(pl) + 1
        self.texto = " ".join(partes)

    def indice_de(self, posicion):
        """La palabra que contiene ese caracter del texto plegado."""
        i = 0
        for j, ini in enumerate(self.inicios):
            if ini <= posicion:
                i = j
        return i

    def t(self, i, fin=False):
        if not self.tiempos:
            return self.t_in
        i = max(0, min(len(self.tiempos) - 1, int(i)))
        return self.tiempos[i][1 if fin else 0]

    def buscar(self, palabra, desde=0):
        """Indice de la primera palabra (o frase) que empieza por `palabra`."""
        objetivo = fidelidad.plegar(palabra)
        if not objetivo or not self.inicios:
            return None
        base = self.inicios[desde] if 0 <= desde < len(self.inicios) else 0
        m = re.search(r"(?<![a-z0-9ñ])" + re.escape(objetivo), self.texto[base:])
        return self.indice_de(base + m.start()) if m else None

    def momento(self, spec, defecto=None):
        """`en` de una pieza -> segundo del VIDEO."""
        if spec is None:
            return self.t_in if defecto is None else defecto
        if isinstance(spec, (int, float)):
            return min(self.t_out - 0.05, self.t_in + max(0.0, float(spec)))
        spec = str(spec).strip()
        if spec.startswith("#") and spec[1:].isdigit():
            return self.t(int(spec[1:]))
        i = self.buscar(spec)
        if i is None:
            return self.t_in if defecto is None else defecto
        return self.t(i)


# ------------------------------------------------------------ deteccion

def _libro_re():
    nombres = "|".join(sorted({p for p, _ in LIBROS}, key=len, reverse=True))
    return re.compile(
        r"\b(?:(1|2|3|primera|segunda|tercera|primer|segundo|tercer) (?:de )?)?"
        r"(" + nombres + r") (?:capitulo )?" + _NUM +
        r"(?: versiculos?| verso)? " + _NUM + r"(?: (?:al|a|y) " + _NUM + r")?\b")


LIBRO_RE = _libro_re()


def cita_de(voz):
    """La cita biblica del plano. -> dict|None

    {"ref": "JUAN 14:23", "i_ref": i, "palabras": [(texto, indice)],
     "cabecera": "JESÚS DIJO"}. El texto de la cita es lo que la VOZ dice entre
    comillas («…», “…” o "…"): el guion bíblico ya la cita literal de la
    RVR1960 (punto C), así que la tarjeta enseña lo mismo que se oye.
    """
    # LA CITA, con `citas.buscar` (8-nov-2026): antes una expresion que solo
    # sabia contar hasta 24, asi que «Mateo veintisiete, versiculo cuarenta y
    # seis» o «Salmo ciento diecinueve» no sacaban tarjeta
    ref, i_ref, fin_ref = None, None, None
    for c in citas.buscar(voz.crudas):
        if not c["v1"]:
            continue
        nombre = "Salmos" if c["libro"] == "Salmo" else c["libro"]
        ref = f"{nombre} {c['ref']}"
        if c["orden"]:
            ref = f"{c['orden']} {ref}"
        i_ref, fin_ref = c["inicio"], c["fin"] - 1
        break
    # las comillas, sobre las palabras CRUDAS
    abre = cierra = None
    for i, w in enumerate(voz.crudas):
        if abre is None:
            if w[:1] not in "«“\"":
                continue
            abre = i
        fin = w.rstrip(".,;:!?)")
        if fin[-1:] in "»”\"" and (i > abre or len(fin) > 1):
            cierra = i
            break
    if abre is not None and cierra is None:
        cierra = len(voz.crudas) - 1
    if abre is None:
        if ref is None:
            return None
        # sin comillas: lo que va detras de la referencia (o delante, si la
        # referencia cierra la frase)
        if fin_ref is not None and fin_ref + 1 < len(voz.crudas) - 2:
            abre, cierra = fin_ref + 1, len(voz.crudas) - 1
        elif i_ref and i_ref > 2:
            abre, cierra = 0, i_ref - 1
        else:
            return None
    elif ref is None and not re.search(
            r"\b(dijo|dice|decia|escrito|escribio|declara|ensena|palabra)\b",
            voz.texto):
        return None
    palabras = []
    for i in range(abre, min(cierra + 1, abre + 34)):
        w = voz.crudas[i].strip("«»“”\"()")
        if ref and i_ref is not None and fin_ref is not None and i_ref <= i <= fin_ref:
            continue
        w = w.rstrip(",;") if i == cierra else w
        if w:
            palabras.append((w, i))
    if len(palabras) < 2:
        return None
    # la cabecera: «Jesús dijo:» justo antes de las comillas
    cabecera = ""
    previas = [w for w in voz.crudas[max(0, abre - 4):abre]]
    junto = " ".join(previas)
    mm = re.search(r"(?:^|.*\s)([A-ZÁÉÍÓÚÑ][\wáéíóúñ]*(?: [\wáéíóúñ]+){0,2} "
                   r"(?:dijo|dice|decía|escribió|declaró|enseñó|respondió)):?\s*$",
                   junto)
    if mm:
        cabecera = mm.group(1)
    elif ref:
        cabecera = "Escrito está" if ref.split()[0] not in ("Salmos",) else "Dice el salmo"
    return {"ref": ref, "i_ref": i_ref, "palabras": palabras,
            "cabecera": cabecera.upper().rstrip(":") + ":" if cabecera else ""}


def _claves(palabras, cuantas=2):
    """Las palabras con más contenido de la cita (las que se colorean)."""
    candidatas = []
    for orden, (w, _) in enumerate(palabras):
        pl = fidelidad.plegar(w)
        if pl in VACIAS or len(pl) < 4:
            continue
        candidatas.append((-len(pl), orden))
    return [o for _, o in sorted(candidatas)[:cuantas]]


def reloj_de(voz):
    """Las porciones de horas que se nombran. -> dict|None"""
    t = voz.texto
    jud = r"(primera|tercera|sexta|novena|undecima|duodecima)"
    rango = re.search(r"\bhora " + jud + r"\b.{0,40}?\bhora " + jud + r"\b", t)
    if rango:
        a, b = HORAS_JUDIAS[rango.group(1)], HORAS_JUDIAS[rango.group(2)]
        if b > a:
            i = voz.indice_de(rango.start())
            j = voz.indice_de(rango.start(2))
            return {"modo": 12, "porciones": [
                {"desde": 6 + a, "hasta": 6 + b, "i": i, "i_fin": j,
                 "etiqueta": f"{b - a} HORAS"}],
                "titulo": f"De la hora {rango.group(1)} a la {rango.group(2)}".upper(),
                "pie": f"de las {_hora_txt(6 + a)} a las {_hora_txt(6 + b)}"}
    una = re.search(r"\bhora " + jud + r"\b|\b" + jud + r" hora\b", t)
    if una:
        nombre = una.group(1) or una.group(2)
        h = HORAS_JUDIAS[nombre]
        i = voz.indice_de(una.start())
        return {"modo": 12, "porciones": [
            {"desde": 6, "hasta": 6 + h, "i": i, "etiqueta": f"HORA {nombre.upper()}"}],
            "titulo": "Se cuenta desde el amanecer".upper(),
            "pie": f"hora {nombre} = {_hora_txt(6 + h)}"}
    dia = re.search(r"\b" + _NUM + r" horas? (?:al dia|cada dia|diarias|de tu dia|"
                    r"del dia|por dia|a diario|en el dia)\b", t)
    if dia and _n(dia.group(1)) and _n(dia.group(1)) <= 24:
        n = _n(dia.group(1))
        i = voz.indice_de(dia.start())
        pct = round(100 * n / 24)
        return {"modo": 24, "porciones": [
            {"desde": 0, "hasta": n, "i": i, "etiqueta": f"{n} h"}],
            "titulo": "TU DÍA: 24 HORAS", "pie": f"{n} h = {pct} % de tu día"}
    horas = re.search(r"\b" + _NUM + r" horas\b", t)
    if horas and _n(horas.group(1)) and 1 <= _n(horas.group(1)) <= 12:
        n = _n(horas.group(1))
        i = voz.indice_de(horas.start())
        return {"modo": 12, "porciones": [
            {"desde": 12, "hasta": 12 + n, "i": i, "etiqueta": f"{n} HORAS"}],
            "titulo": "", "pie": f"{n} horas"}
    return None


def _hora_txt(h):
    h = int(h) % 24
    if h == 12:
        return "12 del mediodía"
    if h < 12:
        return f"{h} de la mañana" if h else "medianoche"
    return f"{h - 12} de la tarde" if h < 19 else f"{h - 12} de la noche"


def _anio_txt(a):
    return f"{-a} a. C." if a < 0 else (str(a) if a > 300 else f"{a} d. C.")


def fechas_de(voz, hoy=None):
    """Los años que dice el plano, en orden. -> [{"anio", "i", "texto"}]"""
    hoy = hoy or date.today().year
    t = voz.texto
    hallados = []
    patrones = (
        (r"\b(\d{1,4}) (a c|ac|antes de cristo|d c|dc|despues de cristo)\b", "era"),
        (r"\bano (\d{1,4})\b(?: (a c|ac|antes de cristo|d c|dc|despues de cristo)\b)?", "era"),
        (r"\ben el (\d{2,4})\b(?! (?:por ciento|km|kilometros|personas|anos))", None),
        (r"\bhace (?:mas de |casi |unos |unos )?(\d{2,4}) anos\b", "hace"),
    )
    ocupado = []
    for patron, clase in patrones:
        for m in re.finditer(patron, t):
            if any(m.start() < b and a < m.end() for a, b in ocupado):
                continue
            n = int(m.group(1))
            if clase == "hace":
                anio = hoy - n
            else:
                anio = n
                era = m.group(2) if clase == "era" and m.lastindex >= 2 else None
                if era and era.startswith(("a", "antes")):
                    anio = -n
            if anio == 0 or abs(anio) > hoy:
                continue
            ocupado.append((m.start(), m.end()))
            hallados.append({"anio": anio, "i": voz.indice_de(m.start()),
                             "fin": voz.indice_de(m.end() - 1)})
    hallados.sort(key=lambda f: f["i"])
    vistos, salida = set(), []
    for f in hallados:
        if f["anio"] not in vistos:
            vistos.add(f["anio"])
            # el pie: hasta 4 palabras con contenido detras del año
            pie = []
            for w in voz.crudas[f["fin"] + 1:f["fin"] + 8]:
                limpia = w.strip(",.;:¿?¡!«»\"")
                if not limpia or fidelidad.plegar(limpia) in ("a", "c", "d"):
                    continue
                pie.append(limpia)
                if len(pie) >= 4 or w[-1:] in ",.;:?!":
                    break
            f["texto"] = " ".join(pie)
            salida.append(f)
    return salida[:5]


def lugares_de(voz):
    """Lugares del nomenclator que nombra el plano, con la palabra donde salen."""
    salida = []
    for nombre, lat, lon in fidelidad.lugares_en(" ".join(voz.crudas)):
        formas = next((f for n, _, _, f in fidelidad.LUGARES if n == nombre), ())
        i = None
        for forma in formas:
            m = re.search(rf"\b{forma}\b", voz.texto)
            if m:
                i = voz.indice_de(m.start())
                break
        salida.append({"nombre": nombre, "lat": lat, "lon": lon,
                       "i": i if i is not None else 0})
    return salida[:4]


def iconos_de(voz, maximo=3):
    salida, vistos = [], set()
    texto = voz.texto + " "
    for icono, formas in PALABRAS_ICONO:
        for forma in formas:
            m = re.search(r"(?:^|\s)" + re.escape(forma), texto)
            if m and icono not in vistos:
                vistos.add(icono)
                salida.append((voz.indice_de(m.start() + 1), icono))
                break
    salida.sort()
    return salida[:maximo]


GENTE = ("hombre", "mujer", "persona", "discipulo", "apostol", "nino", "hijo",
         "tribu", "familia", "soldado", "profeta", "sacerdote", "rey", "pastor",
         "hermano", "fariseo", "levita", "anciano", "creyente", "pueblo")
ICONO_DE_COSA = (("pan", "pan"), ("pez", "pez"), ("peces", "pez"), ("oveja", "oveja"),
                 ("moneda", "moneda"), ("denario", "moneda"), ("siclo", "moneda"),
                 ("talento", "moneda"), ("dia", "sol"), ("noche", "luna"),
                 ("ano", "arena"), ("estrella", "estrella"), ("cantaro", "copa"),
                 ("tinaja", "copa"), ("piedra", "tumba"), ("rollo", "pergamino"),
                 ("trompeta", "trompeta"), ("lampara", "vela"), ("barca", "barca"))
NO_CONTABLES = ("hora", "horas", "km", "kilometros", "por", "veces", "de", "mas",
                "anos", "ano", "siglos", "siglo")


def contador_de(voz):
    """«5000 hombres», «40 días», «doce apóstoles» -> {"n", "cosa", "i", "fin"}"""
    patron = re.compile(r"\b" + _NUM + r"( mil)? ([a-zñ]{3,})\b")
    for m in patron.finditer(voz.texto):
        n = _n(m.group(1))
        cosa = m.group(3)
        if n and m.group(2):
            n *= 1000
        if n and n >= 2 and cosa not in VACIAS and cosa not in NO_CONTABLES:
            fin = voz.indice_de(m.start(3))
            return {"n": n, "cosa": voz.crudas[fin].strip(",.;:¿?¡!«»\"()"),
                    "plegada": cosa, "i": voz.indice_de(m.start()), "fin": fin}
    return None


def _icono_de_cosa(cosa):
    if any(cosa.startswith(g) for g in GENTE):
        return "persona"
    for raiz, icono in ICONO_DE_COSA:
        if cosa.startswith(raiz):
            return icono
    return "punto"


def _trozo(voz, a, b, maximo=7):
    palabras = [w.strip(",.;:¿?¡!«»\"()") for w in voz.crudas[a:b + 1]]
    palabras = [w for w in palabras if w][:maximo]
    return " ".join(palabras)


def comparacion_de(voz):
    """«no fue X, sino Y» / «no es X, es Y» -> {"a", "b", "i_a", "i_b"}"""
    t = voz.texto
    patrones = (
        r"\bno (?:fue|fueron|es|era|son|eran|somos|eres|estaba|esta|vino|vine) (?P<x>[a-zñ0-9 ]{3,60}?) "
        r"sino (?:que )?(?P<y>[a-zñ0-9 ]{3,60})",
        r"\bno (?P<x>[a-zñ0-9 ]{3,50}?) sino (?:que )?(?P<y>[a-zñ0-9 ]{3,50})",
        r"\bno (?:fue|es|era) (?P<x>[a-zñ0-9 ]{3,40}?) (?:fue|es|era) (?P<y>[a-zñ0-9 ]{3,40})",
    )
    for patron in patrones:
        m = re.search(patron, t)
        if not m:
            continue
        ia, fa = voz.indice_de(m.start("x")), voz.indice_de(m.end("x") - 1)
        ib, fb = voz.indice_de(m.start("y")), voz.indice_de(m.end("y") - 1)
        # la Y acaba donde acaba la frase en la voz (coma o punto)
        for k in range(ib, min(fb + 1, len(voz.crudas))):
            if voz.crudas[k][-1:] in ",.;:?!":
                fb = k
                break
        a, b = _trozo(voz, ia, fa), _trozo(voz, ib, fb)
        if a and b:
            return {"a": a, "b": b, "i_a": ia, "i_b": ib}
    return None


def lista_de(voz):
    """«tres cosas: orar, leer y servir» -> [(texto, indice)] (3 a 5 cosas)"""
    for k, w in enumerate(voz.crudas):
        if not w.endswith(":"):
            continue
        items, actual, inicio = [], [], k + 1
        for j in range(k + 1, len(voz.crudas)):
            limpia = voz.crudas[j].strip(",.;:¿?¡!«»\"()")
            if voz.plegadas[j] in ("y", "e") and actual and len(items) >= 1:
                items.append((" ".join(actual), inicio))
                actual, inicio = [], j + 1
                continue
            actual.append(limpia)
            if voz.crudas[j][-1:] in ",;":
                items.append((" ".join(actual), inicio))
                actual, inicio = [], j + 1
            elif voz.crudas[j][-1:] in ".!?":
                break
        if actual:
            items.append((" ".join(actual), inicio))
        items = [(t, i) for t, i in items if t]
        if 3 <= len(items) <= 5 and all(len(t.split()) <= 6 for t, _ in items):
            return items
    return None


# ------------------------------------------------------------ las piezas

# La costa del Levante, en (lat, lon): el mar va al oeste. Esquematica, para
# que un mapa de Israel se reconozca de un vistazo (no es cartografia).
COSTA = ((31.15, 32.3), (31.1, 33.8), (31.32, 34.22), (31.5, 34.45),
         (31.67, 34.56), (32.05, 34.74), (32.5, 34.89), (32.83, 34.97),
         (32.93, 35.07), (33.27, 35.19), (33.56, 35.37), (34.4, 35.82),
         (35.5, 35.9), (36.2, 35.85), (36.8, 36.15))
LAGOS = (((32.82, 35.59), 0.095, 0.07), ((31.45, 35.5), 0.32, 0.07))  # Galilea, Muerto
JORDAN = ((32.71, 35.57), (32.4, 35.55), (32.1, 35.53), (31.76, 35.55))


def _proyectar(lugares, w, h, margen=0.2):
    """lat/lon -> px relativos al centro de una caja w*h (equirectangular)."""
    lats = [l["lat"] for l in lugares]
    lons = [l["lon"] for l in lugares]
    lat0 = sum(lats) / len(lats)
    k = math.cos(math.radians(lat0))
    xs = [lo * k for lo in lons]
    span_x = max(max(xs) - min(xs), 0.55)
    span_y = max(max(lats) - min(lats), 0.55)
    escala = min(w * (1 - 2 * margen) / span_x, h * (1 - 2 * margen) / span_y)
    cx = (max(xs) + min(xs)) / 2
    cy = (max(lats) + min(lats)) / 2

    def p(lat, lon):
        return (round((lon * k - cx) * escala, 1), round((cy - lat) * escala, 1))
    return p, escala / k   # px por grado de longitud (sin el coseno)


def pieza_mapa(voz, lugares, w, h):
    if len(lugares) == 1 and lugares[0]["nombre"] != "Jerusalén":
        # un solo sitio: se situa respecto de Jerusalen (el centro de todo)
        jer = next(l for l in fidelidad.LUGARES if l[0] == "Jerusalén")
        lugares = [dict(lugares[0]), {"nombre": jer[0], "lat": jer[1], "lon": jer[2],
                                      "i": lugares[0]["i"], "referencia": True}]
    p, px_por_grado = _proyectar(lugares, w, h)
    km_por_px = 111.32 * math.cos(math.radians(lugares[0]["lat"])) / px_por_grado
    pins = []
    for n, l in enumerate(lugares):
        x, y = p(l["lat"], l["lon"])
        en = voz.t(l["i"]) + (0.5 * n if l.get("referencia") else 0)
        pins.append({"n": l["nombre"], "x": x, "y": y, "en": round(en, 3),
                     "ref": bool(l.get("referencia"))})
    tramos = []
    for a in range(len(pins) - 1):
        b = a + 1
        km = fidelidad.distancia_km((None, lugares[a]["lat"], lugares[a]["lon"]),
                                    (None, lugares[b]["lat"], lugares[b]["lon"]))
        en = max(pins[a]["en"], pins[b]["en"]) + 0.45
        tramos.append({"a": a, "b": b, "km": int(round(km / (5 if km > 30 else 1))
                                                    * (5 if km > 30 else 1)),
                       "en": round(min(en, voz.t_out - 1.2), 3)})
    # la costa solo si el mapa cae en el Levante
    lats = [l["lat"] for l in lugares]
    lons = [l["lon"] for l in lugares]
    costa = None
    if 29 <= min(lats) and max(lats) <= 34.6 and 33.8 <= min(lons) and max(lons) <= 36.6:
        linea = [p(a, b) for a, b in COSTA]
        mar = [(-w, linea[0][1] + h)] + linea + [(-w, linea[-1][1] - h)]
        cerca = min(linea, key=lambda q: abs(q[1]))
        etq = ([round((-w / 2 + cerca[0]) / 2, 1), round(cerca[1], 1)]
               if cerca[0] - (-w / 2) > w * 0.24 else None)
        costa = {"mar": mar, "etq": etq,
                 "lagos": [{"c": p(*c), "rx": round(rx * px_por_grado * 0.85, 1),
                            "ry": round(ry * px_por_grado * 0.85 * 1.0, 1)}
                           for c, ry, rx in LAGOS],
                 "rio": [p(a, b) for a, b in JORDAN]}
    # la barra de escala: 10, 25, 50, 100... km que midan ~22 % del ancho
    objetivo = w * 0.22 * km_por_px
    km_barra = min((10, 20, 25, 50, 100, 200, 250, 500, 1000),
                   key=lambda v: abs(v - objetivo))
    return {"tipo": "mapa", "w": round(w, 1), "h": round(h, 1), "lugares": pins,
            "tramos": tramos, "costa": costa,
            "escala": {"px": round(km_barra / km_por_px, 1), "texto": f"{km_barra} km"},
            "en": round(min(p_["en"] for p_ in pins) - 0.35, 3), "entra": "abajo"}


def pieza_linea(voz, fechas, w, hoy=None):
    hoy = hoy or date.today().year
    eventos = [dict(f) for f in fechas]
    if len(eventos) == 1:
        f = eventos[0]
        eventos.append({"anio": hoy, "i": f["i"], "texto": "hoy", "hoy": True})
    eventos.sort(key=lambda e: e["anio"])
    a0, a1 = eventos[0]["anio"], eventos[-1]["anio"]
    span = max(1, a1 - a0)
    salida = []
    for n, e in enumerate(eventos):
        x = -w / 2 + w * (0.1 + 0.8 * (e["anio"] - a0) / span)
        en = voz.t(e["i"]) + (0.9 if e.get("hoy") else 0)
        salida.append({"etq": "HOY" if e.get("hoy") else _anio_txt(e["anio"]),
                       "txt": "" if e.get("hoy") else e.get("texto", ""),
                       "x": round(x, 1), "en": round(min(en, voz.t_out - 0.6), 3),
                       "arriba": n % 2 == 0})
    # la llave entre el primero y el ultimo: «N años»
    anios = a1 - a0 - (1 if a0 < 0 < a1 else 0)
    hace = any(e.get("hoy") for e in eventos)
    tramo = {"a": 0, "b": len(salida) - 1, "n": anios,
             "etq": ("hace {n} años" if hace else "{n} años"),
             "en": round(min(max(e["en"] for e in salida) + 0.5, voz.t_out - 0.4), 3)}
    return {"tipo": "linea", "w": round(w, 1), "eventos": salida, "tramo": tramo,
            "en": round(min(e["en"] for e in salida) - 0.4, 3), "entra": "pop"}


def pieza_reloj(voz, datos, r):
    porciones = []
    for n, por in enumerate(datos["porciones"]):
        en = voz.t(por["i"])
        porciones.append({"desde": por["desde"], "hasta": por["hasta"],
                          "etq": por["etiqueta"], "en": round(en, 3),
                          "dur": round(max(0.9, min(2.2, voz.t(por.get("i_fin", por["i"]), True) - en)), 3),
                          "color": "acento" if n == 0 else "acento2"})
    primero = porciones[0]["en"]
    return {"tipo": "reloj", "r": round(r, 1), "modo": datos["modo"],
            "porciones": porciones, "titulo": datos.get("titulo", ""),
            "pie": datos.get("pie", ""),
            "pie_en": round(min(primero + porciones[0]["dur"] + 0.3, voz.t_out - 0.4), 3),
            "en": round(max(voz.t_in, primero - 0.7), 3), "entra": "arriba"}


def pieza_versiculo(voz, cita, w, tam):
    claves = _claves(cita["palabras"])
    palabras = []
    for orden, (texto, i) in enumerate(cita["palabras"]):
        c = 1 if claves and orden == claves[0] else (2 if orden in claves[1:] else 0)
        palabras.append({"t": texto, "c": c, "en": round(voz.t(i), 3)})
    # el principio y el final llevan las comillas angulares
    palabras[0]["t"] = "«" + palabras[0]["t"]
    palabras[-1]["t"] = palabras[-1]["t"].rstrip(",;:") + "»"
    ultima = palabras[-1]["en"]
    ref_en = voz.t(cita["i_ref"]) if cita.get("i_ref") is not None else ultima + 0.4
    en = max(voz.t_in, min(palabras[0]["en"], ref_en) - 0.6)
    return {"tipo": "versiculo", "w": round(w, 1), "tam": round(tam, 1),
            "cab": cita["cabecera"], "palabras": palabras,
            "ref": ((cita["ref"] or "").upper() + " · RVR1960") if cita["ref"] else "RVR1960",
            "ref_en": round(min(max(ref_en, en + 0.3), voz.t_out - 0.3), 3),
            "libro_en": round(en + 0.15, 3),
            "en": round(en, 3), "entra": "pop"}


def pieza_contador(voz, datos, W, H):
    vertical = H > W
    tam = W * 0.24 if vertical else H * 0.26
    en = voz.t(datos["i"])
    fin = max(en + 0.6, voz.t(datos["fin"], True) + 0.15)
    return {"tipo": "contador", "n": datos["n"], "etq": datos["cosa"].upper(),
            "icono": _icono_de_cosa(datos["plegada"]), "tam": round(tam, 1),
            "w": round(W * (0.84 if vertical else 0.6), 1),
            "en": round(max(voz.t_in, en - 0.1), 3),
            "fin": round(min(fin, voz.t_out - 0.3), 3), "entra": "pop"}


def pieza_comparacion(voz, datos, W, H):
    vertical = H > W
    w = W * (0.86 if vertical else 0.84)
    h = H * (0.5 if vertical else 0.5)
    return {"tipo": "comparacion", "a": datos["a"], "b": datos["b"],
            "a_en": round(voz.t(datos["i_a"]), 3),
            "b_en": round(max(voz.t(datos["i_b"]), voz.t(datos["i_a"]) + 0.7), 3),
            "w": round(w, 1), "h": round(h, 1), "vertical": vertical,
            "sep": round(h * 0.27 if vertical else w * 0.25, 1),
            "tam": round(W * (0.075 if vertical else 0.038), 1),
            "en": round(max(voz.t_in, voz.t(datos["i_a"]) - 0.15), 3), "entra": "pop"}


def pieza_lista(voz, items, W, H):
    vertical = H > W
    tam = W * (0.072 if vertical else 0.036)
    paso = tam * 2.1
    return {"tipo": "lista", "w": round(W * (0.84 if vertical else 0.56), 1),
            "tam": round(tam, 1), "paso": round(paso, 1),
            "items": [{"t": t, "en": round(voz.t(i), 3)} for t, i in items],
            "en": round(max(voz.t_in, voz.t(items[0][1]) - 0.3), 3), "entra": "pop"}


# ------------------------------------------------------------ segunda parte:
# barras, antes/despues, arbol genealogico, flechas, circulos y MUÑECOS

def barras_de(voz):
    """«el 70 % ... y el 30 %» o «cinco panes y dos peces» -> [{t, v, i, pct}]"""
    salida = []
    for k, cruda in enumerate(voz.crudas):
        m = re.match(r"^(\d{1,3}(?:[.,]\d+)?)(%?)", cruda.strip("(«\""))
        if not m:
            continue
        siguiente = voz.crudas[k + 1] if k + 1 < len(voz.crudas) else ""
        desp = 2 if voz.plegadas[k + 1:k + 3] == ["por", "ciento"] else (
            1 if siguiente.startswith("%") else 0)
        if not (m.group(2) or desp):
            continue
        valor = float(m.group(1).replace(",", "."))
        # la etiqueta: lo que viene detras de «de» (el 70 % DE LOS JUDIOS)
        etq = ""
        if voz.plegadas[k + 1 + desp:k + 2 + desp] in (["de"], ["del"]):
            palabras = [w.strip(",.;:¿?¡!«»\"()") for w in voz.crudas[k + 2 + desp:k + 6 + desp]]
            limpias = []
            for w in palabras:
                pl = fidelidad.plegar(w)
                if pl in ("y", "e", "o", "u", "que", "en", "con", "por", "mientras"):
                    break
                if w and pl not in ("los", "las", "la", "el", "lo"):
                    limpias.append(w)
            etq = " ".join(limpias[:2])
        salida.append({"t": etq, "v": valor, "txt": f"{m.group(1)} %", "i": k, "pct": True})
    if salida:
        return salida[:4]
    patron = re.compile(r"\b" + _NUM + r"( mil)? ([a-zñ]{3,})\b")
    vistos = set()
    for m in patron.finditer(voz.texto):
        n = _n(m.group(1))
        cosa = m.group(3)
        if not n or cosa in VACIAS or cosa in NO_CONTABLES or cosa in vistos:
            continue
        if m.group(2):
            n *= 1000
        vistos.add(cosa)
        fin = voz.indice_de(m.start(3))
        salida.append({"t": voz.crudas[fin].strip(",.;:¿?¡!«»\"()"), "v": float(n),
                       "txt": f"{n:,}".replace(",", "."), "i": voz.indice_de(m.start()),
                       "pct": False})
    if len(salida) >= 2:
        vals = [b["v"] for b in salida]
        if max(vals) / max(1.0, min(vals)) <= 25:
            return salida[:4]
    return None


def antes_de(voz):
    """«antes era perseguidor, ahora es apostol» -> {"a", "b", "i_a", "i_b"}"""
    t = voz.texto
    patrones = (
        r"\bantes (?:era|eras|eran|fue|fuimos|eramos|estaba|estabas|tenia|vivia)? ?"
        r"(?P<x>[a-zñ0-9 ]{3,50}?) (?:pero |y )?(?:ahora|hoy|despues|luego) "
        r"(?:es|eres|son|somos|esta|estas|tiene|vive|fue)? ?(?P<y>[a-zñ0-9 ]{3,50})",
        r"\b(?:era|eras|eran|fue) (?P<x>[a-zñ0-9 ]{3,40}?) (?:pero |y )?(?:ahora|hoy) "
        r"(?:es|eres|son|somos) (?P<y>[a-zñ0-9 ]{3,40})",
    )
    for patron in patrones:
        m = re.search(patron, t)
        if not m:
            continue
        ia, fa = voz.indice_de(m.start("x")), voz.indice_de(m.end("x") - 1)
        ib, fb = voz.indice_de(m.start("y")), voz.indice_de(m.end("y") - 1)
        for k in range(ia, min(fa + 1, len(voz.crudas))):
            if voz.crudas[k][-1:] in ",.;:?!":
                fa = k
                break
        for k in range(ib, min(fb + 1, len(voz.crudas))):
            if voz.crudas[k][-1:] in ",.;:?!":
                fb = k
                break
        a, b = _trozo(voz, ia, fa, 5), _trozo(voz, ib, fb, 5)
        if a and b:
            return {"a": a, "b": b, "i_a": ia, "i_b": ib}
    return None


_PARENTESCO = (("hijo de", "sube"), ("hija de", "sube"), ("nieto de", "sube"),
               ("padre de", "baja"), ("madre de", "baja"), ("engendro a", "baja"),
               ("engendro", "baja"), ("abuelo de", "baja"))


def _nombre_en(voz, k):
    w = voz.crudas[k].strip(",.;:¿?¡!«»\"()") if 0 <= k < len(voz.crudas) else ""
    return w if w[:1].isupper() and len(w) > 1 and w.isalpha() else None


def arbol_de(voz):
    """«Isaac, hijo de Abraham» / «Abraham engendró a Isaac» -> [(nombre, i)]
    del mas antiguo al mas joven (una linea de generaciones)."""
    padres, previa = {}, None
    for k in range(len(voz.plegadas)):
        for frase, sentido in _PARENTESCO:
            partes = frase.split()
            if voz.plegadas[k:k + len(partes)] != partes:
                continue
            antes = None
            for j in range(k - 1, max(-1, k - 4), -1):
                antes = _nombre_en(voz, j)
                if antes:
                    break
            despues, j_desp = None, None
            for j in range(k + len(partes), min(len(voz.crudas), k + len(partes) + 3)):
                despues = _nombre_en(voz, j)
                if despues:
                    j_desp = j
                    break
            # «Isaac, hijo de Abraham, fue padre de Jacob»: lo de entre comas
            # es un inciso y el sujeto sigue siendo Isaac
            if previa and antes == previa[1] and previa[2]:
                antes = previa[0]
            if antes and despues:
                previa = (antes, despues, voz.crudas[j_desp].endswith(","))
            if antes and despues and antes != despues:
                hijo, padre = (antes, despues) if sentido == "sube" else (despues, antes)
                padres.setdefault(hijo, padre)
            break
    if not padres:
        return None
    hijos = set(padres)
    raices = [p for p in padres.values() if p not in hijos]
    if not raices:
        return None
    hijo_de = {}
    for h, p in padres.items():
        hijo_de.setdefault(p, h)
    cadena, actual = [raices[0]], raices[0]
    while actual in hijo_de and len(cadena) < 6:
        actual = hijo_de[actual]
        if actual in cadena:
            break
        cadena.append(actual)
    if len(cadena) < 2:
        return None
    salida = []
    for nombre in cadena:
        i = voz.buscar(nombre)
        salida.append((nombre, i if i is not None else 0))
    return salida


def pieza_barras(voz, barras, W, H):
    vertical = H > W
    w = W * (0.84 if vertical else 0.62)
    h = H * (0.36 if vertical else 0.5)
    return {"tipo": "barras", "w": round(w, 1), "h": round(h, 1),
            "tam": round(W * (0.06 if vertical else 0.032), 1),
            "pct": bool(barras[0].get("pct")),
            "barras": [{"t": b["t"], "v": b["v"], "txt": b["txt"],
                        "en": round(max(voz.t_in + 0.2, voz.t(b["i"])), 3)} for b in barras],
            "en": round(max(voz.t_in, voz.t(barras[0]["i"]) - 0.5), 3), "entra": "pop"}


def pieza_antes(voz, datos, W, H):
    vertical = H > W
    w = W * (0.86 if vertical else 0.78)
    h = H * (0.5 if vertical else 0.48)
    return {"tipo": "antes", "a": datos["a"], "b": datos["b"],
            "a_en": round(voz.t(datos["i_a"]), 3),
            "b_en": round(max(voz.t(datos["i_b"]), voz.t(datos["i_a"]) + 0.8), 3),
            "w": round(w, 1), "h": round(h, 1), "vertical": vertical,
            "tam": round(W * (0.07 if vertical else 0.036), 1),
            "en": round(max(voz.t_in, voz.t(datos["i_a"]) - 0.4), 3), "entra": "pop"}


def pieza_arbol(voz, nombres, W, H):
    vertical = H > W
    n = len(nombres)
    largo = H * (0.5 if vertical else 0.0) or W * 0.7
    paso = min(largo / max(1, n - 1), (H * 0.14 if vertical else W * 0.2))
    return {"tipo": "arbol", "vertical": vertical, "paso": round(paso, 1),
            "r": round(min(W, H) * (0.075 if vertical else 0.07), 1),
            "tam": round(W * (0.05 if vertical else 0.026), 1),
            "nodos": [{"t": t, "en": round(max(voz.t_in + 0.15, voz.t(i)), 3)}
                      for t, i in nombres],
            "en": round(max(voz.t_in, min(voz.t(i) for _, i in nombres) - 0.3), 3),
            "entra": "pop"}


def pieza_personajes(voz, nombres, fichas, W, H, alto, gesto=None, expresion=None,
                     mira=1, sep=None):
    """Las figuras planas del plano (pasos/motion_mas.py), de pie sobre (0, 0)."""
    figs = motion_mas.figuras(voz, nombres, fichas or {}, gesto=gesto,
                                  expresion=expresion, mira=mira)
    if not figs:
        return None
    sep = alto * 0.62 if sep is None else sep
    n = len(figs)
    for k, f in enumerate(figs):
        f["dx"] = round((k - (n - 1) / 2) * sep, 1)
        f["en"] = round(max(voz.t_in + 0.1, voz.t_in + 0.12 + 0.18 * k), 3)
    return {"tipo": "personajes", "alto": round(alto, 1), "figuras": figs,
            "en": figs[0]["en"], "entra": "abajo"}


def _lamina(escena, voz, lamina, W, H, cx, cy):
    vertical = H > W
    lw = W * (0.8 if vertical else 0.56)
    lh = lw * lamina["alto"] / lamina["ancho"]
    if lh > H * (0.56 if vertical else 0.66):
        lh = H * (0.56 if vertical else 0.66)
        lw = lh * lamina["ancho"] / lamina["alto"]
    gira = -1.6 if _par(escena) else 1.4
    return {"tipo": "lamina", "href": lamina["href"], "x": cx, "y": cy,
            "w": round(lw, 1), "h": round(lh, 1), "rot": gira,
            "en": round(voz.t_in + 0.05, 3), "entra": "abajo",
            "fin": round(voz.t_out, 3)}


def storyboard(escena, ancho, alto, lamina=None, laminas=True, hoy=None,
               mapeados=None, fichas=None, munecos=True, claude=None, fondos=True):
    """Las piezas de UN plano en coordenadas del cuadro (px, origen arriba a la
    izquierda) y tiempos del video. -> [pieza]

    Manda, por este orden: el storyboard escrito a mano en plan.json
    (`escena["motion"]`), el que escribio Claude (`claude`, ver
    pasos/motion_storyboard.py; `{"tipo": "auto"}` dentro mete lo automatico)
    y lo automatico. Un storyboard que no deja ninguna pieza valida cae a lo
    automatico: el plano nunca sale vacio por un JSON torcido.
    """
    voz = Voz(escena)
    W, H = float(ancho), float(alto)
    ctx = {"lamina": lamina if laminas else None, "fichas": fichas or {},
           "personajes": [n for n in (escena.get("personajes") or []) if n],
           "escena": escena}
    propio = escena.get("motion")
    if isinstance(propio, list):
        return [p for p in (_normalizar(x, voz, W, H, ctx) for x in propio) if p]
    if isinstance(claude, list) and claude and propio is not False:
        piezas = []
        for x in claude:
            if isinstance(x, dict) and x.get("tipo") == "auto":
                piezas += _automatico(escena, voz, W, H, lamina, laminas, hoy,
                                      mapeados, fichas, munecos, fondos)
            else:
                q = _normalizar(x, voz, W, H, ctx)
                if q:
                    piezas.append(q)
        if piezas:
            return piezas
    return _automatico(escena, voz, W, H, lamina, laminas, hoy, mapeados, fichas,
                       munecos, fondos)


def _automatico(escena, voz, W, H, lamina, laminas, hoy, mapeados, fichas, munecos,
                fondos=True):
    """Lo que el estudio pone solo (gratis, sin Claude) en un plano."""
    vertical = H > W
    cx = W / 2
    cy = H * (0.37 if vertical else 0.42)     # el subtitulo vive abajo
    propio = escena.get("motion")
    piezas = []
    if propio is not False:
        cita = cita_de(voz)
        lugares = lugares_de(voz)
        fechas = fechas_de(voz, hoy=hoy)
        reloj = reloj_de(voz)
        comparacion = None if cita else comparacion_de(voz)
        antes = None if (cita or comparacion) else antes_de(voz)
        arbol = None if (cita or comparacion or antes) else arbol_de(voz)
        if cita:
            ancho_txt = W * (0.88 if vertical else 0.72)
            tam = W * 0.1 if vertical else min(W * 0.05, H * 0.07)
            piezas.append(dict(pieza_versiculo(voz, cita, ancho_txt, tam),
                               x=cx, y=H * (0.36 if vertical else 0.4)))
        clave_mapa = tuple(sorted(l["nombre"] for l in lugares))
        repetido = mapeados is not None and clave_mapa in mapeados
        if len(lugares) == 1 and lugares[0]["nombre"] == "Jerusalén":
            repetido = True       # Jerusalen sola no explica nada
        if cita:
            pass
        elif comparacion:
            piezas.append(dict(pieza_comparacion(voz, comparacion, W, H), x=cx, y=cy))
        elif antes:
            piezas.append(dict(pieza_antes(voz, antes, W, H), x=cx, y=cy))
        elif arbol:
            piezas.append(dict(pieza_arbol(voz, arbol, W, H), x=cx, y=cy))
        elif fechas:
            # la fecha manda sobre el mapa: «en el año 70 Roma destruyo
            # Jerusalen» cuenta CUANDO, no cuanto hay de Roma a Jerusalen
            piezas.append(dict(pieza_linea(voz, fechas, W * (0.86 if vertical else 0.78),
                                           hoy=hoy), x=cx, y=cy))
        elif lugares and not repetido and (len(lugares) >= 2 or not reloj):
            if mapeados is not None:
                mapeados.add(clave_mapa)
            mw, mh = (W * 0.88, H * 0.56) if vertical else (W * 0.68, H * 0.7)
            piezas.append(dict(pieza_mapa(voz, lugares, mw, mh), x=cx, y=cy))
        elif reloj:
            r = min(W * 0.34, H * 0.22) if vertical else H * 0.27
            piezas.append(dict(pieza_reloj(voz, reloj, r), x=cx, y=cy + r * 0.1))
        else:
            lista = lista_de(voz)
            barras = None if lista else barras_de(voz)
            contador = None if (lista or barras) else contador_de(voz)
            if lista:
                piezas.append(dict(pieza_lista(voz, lista, W, H), x=cx, y=cy))
            elif barras:
                piezas.append(dict(pieza_barras(voz, barras, W, H), x=cx, y=cy))
            elif contador:
                piezas.append(dict(pieza_contador(voz, contador, W, H), x=cx,
                                   y=cy - H * (0.08 if vertical else 0.06)))
    if not piezas:
        iconos = iconos_de(voz)
        # LOS MUÑECOS PLANOS (pasos/motion_mas.py): los personajes del plano
        # dentro del mundo. Con lamina, pequeños delante de ella (como quien
        # la presenta); sin lamina, grandes en el centro.
        nombres = [n for n in (escena.get("personajes") or []) if n] if munecos else []
        figs = None
        if lamina and laminas:
            lam = _lamina(escena, voz, lamina, W, H, cx, cy)
            lw, lh = lam["w"], lam["h"]
            piezas.append(lam)
            if nombres:
                alto = H * (0.2 if vertical else 0.3)
                figs = pieza_personajes(voz, nombres, fichas, W, H, alto,
                                        mira=1 if _par(escena) else -1)
                if figs:
                    lado = -1 if _par(escena) else 1
                    figs.update(x=round(cx + lado * lw * 0.3, 1),
                                y=round(min(cy + lh / 2 + alto * 0.12,
                                            H * (0.7 if vertical else 0.86)), 1))
            sitios = ((cx + lw * 0.46, cy - lh * 0.46), (cx - lw * 0.46, cy + lh * 0.44),
                      (cx + lw * 0.44, cy + lh * 0.46))
            tam = W * (0.15 if vertical else 0.085)
        else:
            sitios = ((cx, cy), (cx - W * 0.27, cy + H * 0.08), (cx + W * 0.27, cy + H * 0.08))
            tam = W * (0.3 if vertical else 0.16)
            ty = cy
            if nombres:
                alto = H * (0.32 if vertical else 0.5)
                figs = pieza_personajes(voz, nombres, fichas, W, H, alto,
                                        mira=1 if _par(escena) else -1)
                if figs:
                    figs.update(x=round(cx, 1), y=round(cy + alto * 0.58, 1))
                    # los iconos y la palabra van encima y a los lados
                    sitios = ((cx + W * 0.3, cy - alto * 0.55), (cx - W * 0.3, cy - alto * 0.5),
                              (cx + W * 0.32, cy + alto * 0.05))
                    tam = W * (0.17 if vertical else 0.1)
                    ty = cy - alto * 0.62
            if not iconos:
                clave = _palabra_fuerte(voz)
                if clave:
                    piezas.append({"tipo": "texto", "x": cx, "y": ty, "w": W * 0.84,
                                   "tam": W * (0.13 if vertical else 0.08),
                                   "palabras": [{"t": clave[0].upper(), "c": 1,
                                                 "en": round(voz.t(clave[1]), 3)}],
                                   "en": round(voz.t(clave[1]), 3), "entra": "pop"})
        for n, (i, icono) in enumerate(iconos):
            x, y = sitios[n]
            piezas.append({"tipo": "icono", "nombre": icono, "x": round(x, 1),
                           "y": round(y, 1), "tam": round(tam * (1 if n == 0 or lamina else 0.7), 1),
                           "en": round(max(voz.t_in + 0.25, voz.t(i)), 3),
                           "entra": "arriba" if n % 2 == 0 else "abajo"})
        if figs:
            piezas.append(figs)
        # EL ESCENARIO (pasos/escenarios.py, P3): el sitio donde pasa, detras
        # de todo. Solo sin lamina (la imagen pagada manda), salvo que el
        # plano lo pida a mano en plan.json
        esc = escenarios.de_la_escena(escena) if fondos else None
        a_mano = escena.get("escenario") not in (None, False)
        if esc and (a_mano or not (lamina and laminas)):
            pies = figs["y"] if figs and not (lamina and laminas) else None
            piezas.insert(0, escenarios.pieza(esc.get("nombre"), esc["hora"], esc["efectos"],
                                              W, H, voz.t_in, suelo_px=pies, fondo=esc.get("fondo"),
                                              cosas=esc.get("cosas"), mas=esc.get("mas")))
    return piezas


def _escenario_dibujado(e, piezas, ultimo, W, H):
    """En un video todo dibujado, CADA plano lleva escenario: el que nombra su
    voz (o el de a mano) y, si no nombra ninguno, el del plano de antes (la
    escena sigue en el mismo sitio). Lo pone delante si el storyboard (de
    Claude o automatico) no lo trajo. -> el escenario que queda para el siguiente."""
    if e.get("escenario") is False:
        return ultimo
    propio = escenarios.de_la_escena(e)
    if propio:
        esc = propio
    elif ultimo:
        esc = dict(ultimo, efectos=escenarios.efectos_de(e.get("narracion") or ""))
    else:
        return None
    if not any(pz.get("tipo") == "escenario" for pz in piezas):
        figs = next((pz for pz in piezas if pz.get("tipo") == "personajes"), None)
        piezas.insert(0, escenarios.pieza(
            esc.get("nombre"), esc["hora"], esc["efectos"], W, H, Voz(e).t_in,
            suelo_px=figs["y"] if figs else None, fondo=esc.get("fondo"),
            cosas=esc.get("cosas"), mas=esc.get("mas")))
    return esc


def _par(escena):
    return sum(map(ord, str(escena.get("id") or ""))) % 2 == 0


def _palabra_fuerte(voz):
    mejor = None
    for i, (cruda, pl) in enumerate(zip(voz.crudas, voz.plegadas)):
        if pl in VACIAS or len(pl) < 5 or not pl.isalpha():
            continue
        if mejor is None or len(pl) > len(mejor[2]):
            mejor = (cruda.strip(",.;:¿?¡!«»\""), i, pl)
    return mejor[:2] if mejor else None


def _indice(voz, spec, defecto=0):
    """`en` (palabra, «#N» o segundos del plano) -> indice de palabra."""
    if spec is None or not voz.crudas:
        return defecto
    if isinstance(spec, (int, float)):
        t = voz.t_in + float(spec)
        for k, (a, b) in enumerate(voz.tiempos):
            if b >= t:
                return k
        return len(voz.crudas) - 1
    spec = str(spec).strip()
    if spec.startswith("#") and spec[1:].isdigit():
        return min(len(voz.crudas) - 1, int(spec[1:]))
    i = voz.buscar(spec)
    if i is None and spec.split():
        i = voz.buscar(spec.split()[0])
    return defecto if i is None else i


def _normalizar(pieza, voz, W, H, ctx=None):
    """Una pieza escrita a mano o por Claude (fracciones del cuadro, `en` en
    palabras). -> pieza lista para el render, o None si no se entiende."""
    if not isinstance(pieza, dict) or pieza.get("tipo") not in TIPOS:
        return None
    ctx = ctx or {}
    try:
        return _normalizar_de_verdad(pieza, voz, W, H, ctx)
    except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError) as e:
        print(f"[motion] pieza {pieza.get('tipo')} descartada ({e})", flush=True)
        return None


def _normalizar_de_verdad(pieza, voz, W, H, ctx):
    p = dict(pieza)
    for k, total in (("x", W), ("y", H), ("w", W), ("h", H)):
        if isinstance(p.get(k), (int, float)) and 0 <= p[k] <= 1.5:
            p[k] = round(p[k] * total, 1)
    for k, total in (("tam", W), ("alto", H), ("r", min(W, H))):
        if isinstance(p.get(k), (int, float)) and 0 < p[k] <= 1.5:
            p[k] = round(p[k] * total, 1)
    p.setdefault("x", W / 2)
    p.setdefault("y", H * 0.4)
    p["en"] = round(voz.momento(p.get("en")), 3)
    if p.get("entra") not in ENTRADAS:
        p["entra"] = "abajo"
    if p.get("sale") is not None:
        p["sale"] = round(voz.momento(p["sale"]), 3)
    luego = []
    for paso in p.get("luego") or []:
        if not isinstance(paso, dict):
            continue
        q = dict(paso)
        q["en"] = round(voz.momento(q.get("en"), voz.t_in + 1.0), 3)
        if isinstance(q.get("x"), (int, float)) and abs(q["x"]) <= 1.5:
            q["x"] = round(q["x"] * W, 1)
        if isinstance(q.get("y"), (int, float)) and abs(q["y"]) <= 1.5:
            q["y"] = round(q["y"] * H, 1)
        luego.append(q)
    p["luego"] = luego
    vertical = H > W
    t = p["tipo"]
    if t == "lamina":
        lam = ctx.get("lamina")
        if not lam:
            return None
        q = _lamina(ctx.get("escena") or {}, voz, lam, W, H, p["x"], p["y"])
        q.update({k: p[k] for k in ("luego", "sale") if p.get(k)})
        if pieza.get("entra") in ENTRADAS:
            q["entra"] = pieza["entra"]
        return q
    if t == "escenario":
        narr = (ctx.get("escena") or {}).get("narracion") or ""
        auto = escenarios.escenario_de(narr) or {}
        if not p.get("nombre") and not p.get("fondo"):
            p = dict(p, nombre=auto.get("nombre") or "campo")
            if "mas" not in p:
                p["mas"] = auto.get("mas") or []
        esc = escenarios.a_mano(p, narr)
        return escenarios.pieza(esc["nombre"], esc["hora"], esc["efectos"],
                                W, H, p["en"] if pieza.get("en") is not None else voz.t_in,
                                fondo=esc["fondo"], cosas=esc.get("cosas"), mas=esc["mas"])
    if t == "personajes":
        nombres = p.get("nombres") or ctx.get("personajes") or []
        if isinstance(nombres, str):
            nombres = [nombres]
        mira = p.get("mira")
        mira = -1 if mira in ("izquierda", -1) else 1
        q = pieza_personajes(voz, nombres, ctx.get("fichas"), W, H,
                             p.get("alto") or H * (0.26 if vertical else 0.4),
                             gesto=p.get("gesto"), expresion=p.get("expresion"),
                             mira=mira)
        if not q:
            return None
        if pieza.get("en") is not None:
            for k, f in enumerate(q["figuras"]):
                f["en"] = round(p["en"] + 0.18 * k, 3)
            q["en"] = p["en"]
        q.update({k: p[k] for k in ("x", "y", "luego", "sale") if k in p})
        if pieza.get("entra") in ENTRADAS:
            q["entra"] = pieza["entra"]
        return q
    if t == "flecha":
        de, a = p.get("de"), p.get("a")
        if not (isinstance(de, (list, tuple)) and isinstance(a, (list, tuple))):
            return None
        de = [float(de[0]) * W if abs(de[0]) <= 1.5 else float(de[0]),
              float(de[1]) * H if abs(de[1]) <= 1.5 else float(de[1])]
        a = [float(a[0]) * W if abs(a[0]) <= 1.5 else float(a[0]),
             float(a[1]) * H if abs(a[1]) <= 1.5 else float(a[1])]
        p.update(x=round(de[0], 1), y=round(de[1], 1), dx=round(a[0] - de[0], 1),
                 dy=round(a[1] - de[1], 1), texto=str(p.get("texto") or "")[:30],
                 curva=float(p.get("curva", 0.25)), entra="nada",
                 grosor=round(W * (0.014 if vertical else 0.008), 1))
        p.setdefault("tam", W * (0.06 if vertical else 0.032))
        return p
    if t == "circulo":
        p.setdefault("w", W * 0.3)
        p.setdefault("h", p["w"] * 0.6)
        p.update(texto=str(p.get("texto") or "")[:30], entra="nada",
                 grosor=round(W * (0.012 if vertical else 0.007), 1))
        p.setdefault("tam", W * (0.06 if vertical else 0.032))
        return p
    if t == "comparacion":
        if not (p.get("a") and p.get("b")):
            return None
        ia = _indice(voz, pieza.get("en"), 0)
        ib = _indice(voz, pieza.get("en_b"), max(ia, min(len(voz.crudas) - 1, ia + 3)))
        q = pieza_comparacion(voz, {"a": str(p["a"])[:60], "b": str(p["b"])[:60],
                                    "i_a": ia, "i_b": ib}, W, H)
        q.update({k: p[k] for k in ("x", "y", "luego", "sale") if k in p})
        return q
    if t == "antes":
        a, b = p.get("antes") or p.get("a"), p.get("despues") or p.get("b")
        if not (a and b):
            return None
        ia = _indice(voz, pieza.get("en"), 0)
        defecto_b = next((k for k, pl in enumerate(voz.plegadas)
                          if pl in ("ahora", "hoy", "despues", "luego") and k > ia),
                         max(ia, min(len(voz.crudas) - 1, ia + 3)))
        ib = _indice(voz, pieza.get("en_b") or pieza.get("en_despues"), defecto_b)
        q = pieza_antes(voz, {"a": str(a)[:50], "b": str(b)[:50], "i_a": ia, "i_b": ib}, W, H)
        q.update({k: p[k] for k in ("x", "y", "luego", "sale") if k in p})
        return q
    if t == "lista":
        items = [str(x)[:40] for x in (p.get("items") or []) if str(x).strip()][:5]
        if len(items) < 2:
            return None
        base = _indice(voz, pieza.get("en"), 0)
        resto = len(voz.crudas) - base
        pares = []
        for k, it in enumerate(items):
            i = voz.buscar(it.split()[0], base) if it.split() else None
            pares.append((it, i if i is not None else
                          min(len(voz.crudas) - 1, base + k * max(1, resto // len(items)))))
        q = pieza_lista(voz, pares, W, H)
        q.update({k: p[k] for k in ("x", "y", "luego", "sale") if k in p})
        return q
    if t == "contador":
        n = int(float(p.get("n") or 0))
        if n < 2:
            return None
        cosa = str(p.get("cosa") or "").strip()[:20]
        i = _indice(voz, pieza.get("en"), 0)
        q = pieza_contador(voz, {"n": n, "cosa": cosa or "veces", "plegada": fidelidad.plegar(cosa),
                                 "i": i, "fin": min(len(voz.crudas) - 1, i + 2)}, W, H)
        q.update({k: p[k] for k in ("x", "y", "luego", "sale") if k in p})
        return q
    if t == "barras":
        crudas = [b for b in (p.get("barras") or []) if isinstance(b, dict)][:4]
        pct = str(p.get("unidad") or "").strip() == "%"
        barras = []
        for k, b in enumerate(crudas):
            v = float(b.get("v") or 0)
            if v <= 0:
                continue
            txt = f"{v:g} %" if pct else f"{int(v):,}".replace(",", ".")
            i = _indice(voz, b.get("en"), min(len(voz.crudas) - 1, k * 2))
            barras.append({"t": str(b.get("t") or "")[:24], "v": v, "txt": txt, "i": i, "pct": pct})
        if not barras:
            return None
        q = pieza_barras(voz, barras, W, H)
        q.update({k: p[k] for k in ("x", "y", "luego", "sale") if k in p})
        return q
    if t == "arbol":
        nombres = [str(x)[:20] for x in (p.get("nombres") or []) if str(x).strip()][:6]
        if len(nombres) < 2:
            return None
        pares = []
        for k, nombre in enumerate(nombres):
            i = voz.buscar(nombre)
            pares.append((nombre, i if i is not None else min(len(voz.crudas) - 1, k)))
        q = pieza_arbol(voz, pares, W, H)
        q.update({k: p[k] for k in ("x", "y", "luego", "sale") if k in p})
        return q
    if p["tipo"] == "texto":
        texto = str(p.get("texto") or "")
        palabras, desde = [], 0
        for w in texto.split():
            c = 1 if w.startswith("*") and w.rstrip(".,;:!?").endswith("*") else 0
            limpia = w.replace("*", "")
            i = voz.buscar(limpia, desde) if limpia else None
            if i is not None:
                desde = i
            palabras.append({"t": limpia, "c": c,
                             "en": round(voz.t(i) if i is not None else p["en"], 3)})
        p["palabras"] = palabras
        p.setdefault("tam", W * (0.09 if H > W else 0.06))
        p.setdefault("w", W * 0.84)
    elif p["tipo"] == "icono":
        if p.get("nombre") not in ICONOS:
            return None
        p.setdefault("tam", W * 0.18)
    elif p["tipo"] == "versiculo":
        texto = str(p.get("texto") or "").split()
        if not texto:
            return None
        t0 = p["en"]
        paso = 0.32
        p["palabras"] = [{"t": w.replace("*", ""), "c": 1 if w.startswith("*") else 0,
                          "en": round(t0 + 0.5 + paso * n, 3)} for n, w in enumerate(texto)]
        p["palabras"][0]["t"] = "«" + p["palabras"][0]["t"]
        p["palabras"][-1]["t"] += "»"
        p["ref"] = (str(p.get("ref") or "").upper() + " · RVR1960").lstrip(" ·")
        p["cab"] = str(p.get("cabecera") or "").upper()
        p["ref_en"] = round(p["palabras"][-1]["en"] + 0.3, 3)
        p["libro_en"] = round(t0 + 0.15, 3)
        p.setdefault("w", W * 0.84)
        p.setdefault("tam", W * (0.074 if H > W else 0.042))
    elif p["tipo"] == "mapa":
        nombres = p.get("lugares") or []
        lugares = []
        for n in nombres:
            hall = fidelidad.lugares_en(str(n))
            if hall:
                i = voz.buscar(str(n))
                lugares.append({"nombre": hall[0][0], "lat": hall[0][1],
                                "lon": hall[0][2], "i": i if i is not None else 0})
        if not lugares:
            return None
        q = pieza_mapa(voz, lugares, p.get("w") or W * 0.86, p.get("h") or H * 0.5)
        q.update({k: p[k] for k in ("x", "y", "luego", "entra") if k in p})
        return q
    elif p["tipo"] == "linea":
        fechas = []
        for e in p.get("eventos") or []:
            if isinstance(e, dict) and isinstance(e.get("anio"), int):
                i = voz.buscar(str(abs(e["anio"])))
                fechas.append({"anio": e["anio"], "i": i if i is not None else 0,
                               "texto": str(e.get("texto") or "")})
        if not fechas:
            return None
        q = pieza_linea(voz, fechas, p.get("w") or W * 0.86)
        q.update({k: p[k] for k in ("x", "y", "luego") if k in p})
        return q
    elif p["tipo"] == "reloj":
        porciones = []
        for por in p.get("porciones") or []:
            if isinstance(por, dict) and "desde" in por and "hasta" in por:
                i = voz.buscar(str(por.get("en") or "")) if por.get("en") else None
                porciones.append({"desde": float(por["desde"]), "hasta": float(por["hasta"]),
                                  "etiqueta": str(por.get("etiqueta") or ""),
                                  "i": i if i is not None else 0})
        if not porciones:
            return None
        q = pieza_reloj(voz, {"modo": 24 if p.get("modo") == 24 else 12,
                              "porciones": porciones, "titulo": p.get("titulo", ""),
                              "pie": p.get("pie", "")},
                        p.get("r") or min(W * 0.34, H * 0.22))
        q.update({k: p[k] for k in ("x", "y", "luego") if k in p})
        return q
    return p


# ------------------------------------------------------------ el mundo

SEPARACION = 1.3   # una parada de la siguiente, en anchos de cuadro


def paradas(n, ancho, alto):
    """El centro de cada plano en el mundo: hacia la derecha, ondulando."""
    W, H = float(ancho), float(alto)
    return [(round(i * W * SEPARACION, 1),
             round(math.sin(i * 1.25) * H * 0.2, 1)) for i in range(n)]


def camara(escenas, puntos):
    """Los tramos de camara de cada plano (tiempos del video).

    Cada plano empieza donde acabo el anterior (mismo sitio y mismo zoom): por
    eso no hay corte. Viaja a su parada en ~1 s y luego se acerca despacio.
    """
    tramos = []
    previo = None
    for i, e in enumerate(escenas):
        t0, t1 = float(e["t_in"]), float(e["t_out"])
        dur = max(0.1, t1 - t0)
        x, y = puntos[i]
        acerca = 1.0 + min(0.07, 0.012 * dur)
        if previo is None:
            viaje = min(1.4, dur * 0.4)
            ini = [x, y + 40.0, 1.18]
        else:
            viaje = max(0.45, min(1.15, dur * 0.35))
            ini = previo
        llega = [x, y, 1.0]
        fin = [x, y, acerca]
        tramos.append({"de": ini, "a": llega, "t0": round(t0, 3),
                       "t1": round(t0 + viaje, 3), "tipo": "inicio" if previo is None else "viaje"})
        tramos.append({"de": llega, "a": fin, "t0": round(t0 + viaje, 3),
                       "t1": round(t1, 3), "tipo": "deriva"})
        previo = fin
    return tramos


def _angulo(h, modo):
    return (h / 24.0 if modo == 24 else (h % 12) / 12.0) * math.pi * 2


def focos_de(pz, W, H):
    """A donde mira la camara mientras se dice cada cosa: [(t, x, y, z)] (mundo)."""
    x, y, t = pz["x"], pz["y"], pz["tipo"]
    f = []
    if t == "mapa":
        for pin in pz["lugares"]:
            if not pin.get("ref"):
                f.append((pin["en"], x + pin["x"], y + pin["y"] - pz["w"] * 0.05, 1.25))
        for tr in pz["tramos"]:
            f.append((tr["en"] + 0.1, x, y, 1.0))
    elif t == "linea":
        for ev in pz["eventos"]:
            f.append((ev["en"], x + ev["x"] * 0.7, y, 1.16))
        f.append((pz["tramo"]["en"], x, y, 1.0))
    elif t == "reloj":
        for por in pz["porciones"]:
            a0 = _angulo(por["desde"], pz["modo"])
            a1 = a0 + (por["hasta"] - por["desde"]) / pz["modo"] * math.pi * 2
            mid = (a0 + a1) / 2
            f.append((por["en"] + 0.15, x + math.sin(mid) * pz["r"] * 0.35,
                      y - math.cos(mid) * pz["r"] * 0.35, 1.2))
        if pz.get("pie"):
            f.append((pz["pie_en"], x, y + pz["r"] * 0.3, 0.97))
    elif t == "versiculo":
        f.append((pz["palabras"][0]["en"], x, y - H * 0.04, 1.1))
        f.append((pz["ref_en"], x, y, 1.0))
    elif t == "contador":
        f.append((pz["en"] + 0.1, x, y - pz["tam"] * 0.2, 1.18))
        f.append((pz["fin"] + 0.2, x, y + pz["tam"] * 0.4, 1.0))
    elif t == "comparacion":
        sep = pz["sep"]
        ax, ay = (x, y - sep) if pz["vertical"] else (x - sep, y)
        bx, by = (x, y + sep) if pz["vertical"] else (x + sep, y)
        f.append((pz["a_en"], ax, ay, 1.15))
        f.append((pz["b_en"], bx, by, 1.15))
        f.append((pz["b_en"] + 1.1, x, y, 1.0))
    elif t == "lista":
        n = len(pz["items"])
        for k, it in enumerate(pz["items"]):
            f.append((it["en"], x, y + (k - (n - 1) / 2) * pz["paso"], 1.1))
        f.append((pz["items"][-1]["en"] + 0.9, x, y, 1.0))
    elif t == "texto":
        f.append((pz["en"], x, y, 1.12))
    elif t == "barras":
        n = len(pz["barras"])
        for k, b in enumerate(pz["barras"]):
            f.append((b["en"], x - pz["w"] / 2 + pz["w"] / n * (k + 0.5), y, 1.12))
        f.append((pz["barras"][-1]["en"] + 1.0, x, y, 1.0))
    elif t == "antes":
        f.append((pz["a_en"], x, y, 1.06))
        f.append((pz["b_en"] + 0.5, x, y, 1.16))
        f.append((pz["b_en"] + 1.5, x, y, 1.0))
    elif t == "arbol":
        n = len(pz["nodos"])
        for k, nd in enumerate(pz["nodos"]):
            if pz["vertical"]:
                px_, py_ = (1 if k % 2 else -1) * pz["r"] * 0.9, (k - (n - 1) / 2) * pz["paso"]
            else:
                px_, py_ = (k - (n - 1) / 2) * pz["paso"], (1 if k % 2 else -1) * pz["r"] * 0.5
            f.append((nd["en"], x + px_, y + py_, 1.18))
        f.append((pz["nodos"][-1]["en"] + 0.9, x, y, 1.0))
    elif t == "personajes":
        if pz["alto"] > H * 0.24:
            f.append((pz["en"] + 0.1, x, y - pz["alto"] * 0.62, 1.1))
    elif t == "flecha":
        f.append((pz["en"] + 0.4, x + pz["dx"], y + pz["dy"], 1.1))
    elif t == "circulo":
        f.append((pz["en"] + 0.3, x, y, 1.15))
    return f


def ventana_de(piezas, a, b, W, H, sy):
    """Los focos de un plano, ya como CENTRO DE CAMARA y limpios."""
    crudos = sorted(fo for pz in piezas for fo in focos_de(pz, W, H))
    salida = []
    for t, fx, fy, z in crudos:
        t = max(t, a + 0.05)
        if t > b - 1.3:
            continue
        z = min(1.3, max(0.9, z))
        cam = [round(fx, 1), round(fy + (H / 2 - sy) / z, 1), round(z, 3)]
        if salida and t - salida[-1]["t"] < 0.45:
            salida[-1] = {"t": salida[-1]["t"], "x": cam[0], "y": cam[1], "z": cam[2]}
            continue
        salida.append({"t": round(t, 3), "x": cam[0], "y": cam[1], "z": cam[2]})
    return {"a": round(a, 3), "b": round(b, 3), "focos": salida}


ICONO_PUENTE = {"versiculo": "biblia", "mapa": "chincheta", "linea": "arena",
                "reloj": "reloj", "contador": "estrella", "comparacion": "balanza",
                "lista": "pergamino", "texto": "estrella", "lamina": "estrella",
                "barras": "lupa", "antes": "arena", "arbol": "arbol",
                "personajes": "persona", "flecha": "flecha", "circulo": "lupa"}
SUPERPUESTAS = ("flecha", "circulo")   # señalan otra cosa: no son la pieza principal


def impactos_de(pz):
    """Cuando una pieza «aterriza»: la camara da un golpecito y las vecinas
    reaccionan (movimientos encadenados)."""
    t = pz["tipo"]
    if pz.get("fondo"):
        return []          # el escenario no «aterriza»: esta ahi
    sale = {"abajo": 0.2, "arriba": 0.2, "izquierda": 0.2, "derecha": 0.2}.get(
        pz.get("entra"), 0.12)
    fuerza = {"icono": 0.5, "lamina": 0.8, "texto": 0.7, "personajes": 0.6,
              "flecha": 0.3, "circulo": 0.3}.get(t, 1.0)
    salida = [(pz["en"] + sale, fuerza)]
    if t == "mapa":
        salida += [(pin["en"] + 0.2, 0.35) for pin in pz["lugares"]]
    elif t == "contador":
        salida.append((pz["fin"], 0.8))
    elif t == "comparacion":
        salida.append((pz["b_en"] + 0.2, 0.9))
    elif t == "lista":
        salida += [(it["en"] + 0.2, 0.4) for it in pz["items"]]
    elif t == "barras":
        salida += [(b["en"] + 0.25, 0.4) for b in pz["barras"][1:]]
    elif t == "antes":
        salida.append((pz["b_en"] + 0.6, 0.9))
    elif t == "arbol":
        salida += [(nd["en"] + 0.2, 0.4) for nd in pz["nodos"][1:]]
    elif t == "personajes":
        salida += [(fg["en"] + 0.25, 0.4) for fg in pz["figuras"][1:]]
    elif t == "flecha":
        salida.append((pz["en"] + 0.45, 0.3))
    return [{"t": round(a, 3), "f": f, "id": pz.get("id"), "x": pz["x"], "y": pz["y"]}
            for a, f in salida]


def preparar(escenas, p, laminas_px, ancho, alto, hoy=None, fichas=None, claude=None):
    """La configuracion de motion de CADA plano. -> {sid: conf}

    `laminas_px`: {sid: {"href", "ancho", "alto"}} con la imagen de cada plano
    (o nada). Cada conf lleva su plano y los dos anteriores (lo que se puede
    ver durante el viaje) con coordenadas del MUNDO.
    `fichas`: {nombre: descripcion} del reparto, para vestir a los muñecos.
    `claude`: {sid: [piezas]}, el storyboard de pasos/motion_storyboard.py.
    """
    tema = tema_de(p)
    if not tema:
        return {}
    opciones = _opciones(p)
    laminas = opciones.get("laminas", True) is not False
    munecos = opciones.get("munecos", True) is not False
    fondos = opciones.get("escenarios", True) is not False
    dibujado = sin_imagenes(p) and fondos
    if sin_imagenes(p):
        laminas_px = {}       # todo dibujado: ninguna imagen, aunque quede alguna vieja
    W, H = float(ancho), float(alto)
    puntos = paradas(len(escenas), W, H)
    tramos = camara(escenas, puntos)
    por_plano, mapeados = [], set()
    ultimo = None
    for i, e in enumerate(escenas):
        ox, oy = puntos[i][0] - W / 2, puntos[i][1] - H / 2
        piezas = storyboard(e, W, H, (laminas_px or {}).get(e.get("id")),
                            laminas=laminas, hoy=hoy, mapeados=mapeados,
                            fichas=fichas, munecos=munecos, fondos=fondos,
                            claude=(claude or {}).get(e.get("id")))
        if dibujado:
            ultimo = _escenario_dibujado(e, piezas, ultimo, W, H)
        for pz in piezas:
            pz["x"] = round(float(pz.get("x", W / 2)) + ox, 1)
            pz["y"] = round(float(pz.get("y", H / 2)) + oy, 1)
            for paso in pz.get("luego") or []:
                if "x" in paso:
                    paso["x"] = round(float(paso["x"]) + ox, 1)
                if "y" in paso:
                    paso["y"] = round(float(paso["y"]) + oy, 1)
        for k, pz in enumerate(piezas):
            pz["id"] = f"{e.get('id')}-{k}"
        por_plano.append(piezas)
    # EL OBJETO QUE LLEVA A LA ESCENA SIGUIENTE: sale de la pieza principal de
    # este plano al final, vuela con la camara y, al llegar, estalla y se
    # TRANSFORMA en la pieza del plano siguiente (que nace de el, con pop)
    puentes = []
    for i in range(len(escenas) - 1):
        if not por_plano[i] or not por_plano[i + 1]:
            puentes.append(None)
            continue
        principal = (lambda ps: next((q for q in ps if q["tipo"] not in SUPERPUESTAS
                                      and not q.get("fondo")), ps[0]))
        a, b = principal(por_plano[i]), principal(por_plano[i + 1])
        viaje = tramos[2 * (i + 1)]
        t_out = float(escenas[i]["t_out"])
        sale = max(float(escenas[i]["t_in"]) + 0.3, t_out - 0.55)
        llega = viaje["t1"]
        icono = ICONO_PUENTE.get(b["tipo"], "estrella")
        if b["tipo"] == "lamina":
            otros = [q for q in por_plano[i + 1] if q["tipo"] == "icono"]
            icono = otros[0]["nombre"] if otros else icono
        # sale por el LADO hacia el que va la camara, sin tapar la pieza
        de = [round(a["x"] + W * 0.34, 1), round(a["y"] - H * 0.1, 1)]
        puentes.append({"de": de, "a": [b["x"], b["y"]], "sale": round(sale, 3),
                        "vuela": round(float(escenas[i + 1]["t_in"]), 3),
                        "llega": round(llega, 3), "icono": icono,
                        "tam": round(W * (0.16 if H > W else 0.09), 1)})
        if b.get("fondo") or a.get("fondo"):
            puentes.append(None)      # un escenario solo: nada que llevar ni que estalle
            continue
        if b["en"] < llega - 0.06:
            b["en"] = round(llega - 0.06, 3)
        b["entra"] = "pop"
        b["desde_puente"] = True
    sy = H * (0.37 if H > W else 0.42)
    ventanas = [ventana_de(por_plano[i], tramos[2 * i]["t1"], float(e["t_out"]), W, H, sy)
                for i, e in enumerate(escenas)]
    caminos = []
    for i in range(1, len(escenas)):
        (x0, y0), (x1, y1) = puntos[i - 1], puntos[i]
        viaje = tramos[2 * i]
        caminos.append({"de": [round(x0 + W * 0.36, 1), round(y0 + H * 0.06, 1)],
                        "a": [round(x1 - W * 0.36, 1), round(y1 + H * 0.06, 1)],
                        "t0": viaje["t0"], "t1": viaje["t1"]})
    confs = {}
    for i, e in enumerate(escenas):
        desde = max(0, i - 2)
        incluidas = [pz for piezas in por_plano[desde:i + 1] for pz in piezas]
        mis_puentes = [q for q in puentes[max(0, desde - 1):i + 1] if q]
        impactos = [im for pz in incluidas for im in impactos_de(pz)]
        impactos += [{"t": q["llega"], "f": 1.2, "id": None, "x": q["a"][0],
                      "y": q["a"][1]} for q in mis_puentes]
        confs[e.get("id")] = {
            "puentes": mis_puentes,
            "impactos": sorted(impactos, key=lambda im: im["t"]),
            "ventanas": ventanas[desde:i + 1],
            "tema": TEMAS[tema], "nombre_tema": tema, "fuentes": FUENTES,
            "W": W, "H": H, "t0": round(float(e["t_in"]), 3),
            "cam": tramos[2 * desde:2 * i + 2],
            "caminos": caminos[max(0, desde - 1):i],
            "piezas": incluidas,
            "plano": i,
        }
    return confs


def resumen(conf):
    if not conf:
        return "sin motion"
    propias = [p["tipo"] for p in conf["piezas"]
               if p.get("en", 0) >= conf["t0"] - 0.8]
    return "motion: " + (", ".join(propias) or "nada que explicar")


def html_capa(conf, ancho, alto):
    """El SVG del mundo (vacio: lo rellena MOTION_JS) y su CSS. -> (html, css)"""
    if not conf:
        return "", ""
    tema = conf["tema"]
    css = (f"#camara{{display:none}}"
           f"#lienzo{{background:radial-gradient(ellipse at 50% 42%,{tema['fondo1']} 0%,"
           f"{tema['fondo1']} 28%,{tema['fondo2']} 100%)}}"
           f"#mg{{position:absolute;left:0;top:0;width:{ancho}px;height:{alto}px;"
           f"z-index:1;overflow:hidden}}"
           f"#mgvineta{{position:absolute;left:0;top:0;width:{ancho}px;height:{alto}px;"
           f"z-index:1;pointer-events:none;background:radial-gradient(ellipse at 50% 45%,"
           f"rgba(0,0,0,0) 55%,rgba(40,20,0,.22) 100%)}}")
    html = (f'<svg id="mg" xmlns="http://www.w3.org/2000/svg" width="{ancho}" '
            f'height="{alto}" viewBox="0 0 {ancho} {alto}"><g id="mgmundo"></g></svg>'
            f'<div id="mgvineta"></div>')
    return html, css


def json_conf(conf):
    return json.dumps(conf, ensure_ascii=False)


MOTION_JS = r"""
// ===== MOTION GRAPHICS (pasos/motion.py) =====================================
// Todo es funcion de T (segundo del VIDEO) y nunca del reloj: el mismo
// fotograma sale identico en cualquier lote.
const MGNS = 'http://www.w3.org/2000/svg';
const MGT = MG.tema, MGF = MG.fuentes;
let MGHECHO = false, MGCONLETRAS = false, MGPIEZAS = [];
function mk(tag, at, padre){
  const e = document.createElementNS(MGNS, tag);
  for (const k in (at || {})) e.setAttribute(k, at[k]);
  if (padre) padre.appendChild(e);
  return e;
}
function cl(v, a, b){ return Math.min(b, Math.max(a, v)); }
function lerp(a, b, u){ return a + (b - a) * u; }
function eIO(u){ u = cl(u, 0, 1); return u < .5 ? 4*u*u*u : 1 - Math.pow(-2*u + 2, 3)/2; }
function eOut(u){ u = cl(u, 0, 1); return 1 - Math.pow(1 - u, 3); }
// anticipacion + se pasa y vuelve
function eBack(u){ u = cl(u, 0, 1); const c1 = 1.70158, c2 = c1*1.525;
  return u < .5 ? (Math.pow(2*u, 2)*((c2+1)*2*u - c2))/2
                : (Math.pow(2*u-2, 2)*((c2+1)*(u*2-2) + c2) + 2)/2; }
// resorte amortiguado: 0 -> 1 pasandose un poco y volviendo
function resorte(s, w, z){
  if (s <= 0) return 0;
  w = w || 13; z = z || 0.42;
  const wd = w*Math.sqrt(1 - z*z);
  return 1 - Math.exp(-z*w*s)*(Math.cos(wd*s) + (z*w/wd)*Math.sin(wd*s));
}
function col(n){ return MGT[n] || n || MGT.tinta; }
let MGID = 0;
// un ovalo a mano alzada (no cierra justo: se pasa un poco, como un rotulador)
function trazoOvalo(cx, cy, rx, ry){
  const pts = [];
  for (let k = 0; k <= 44; k++){
    const a = 3.4 + k/44*Math.PI*2.18, f = 1 + 0.05*Math.sin(a*3);
    pts.push((cx + Math.cos(a)*rx*f).toFixed(1) + ',' + (cy + Math.sin(a)*ry*f).toFixed(1));
  }
  return 'M' + pts.join(' L');
}
// revela un trazo como si se dibujara
function dibujar(e, u){
  if (!e._len){ try { e._len = e.getTotalLength(); } catch(_) { e._len = 0; } if (e._len) e.setAttribute('stroke-dasharray', e._len.toFixed(1)); }
  u = cl(u, 0, 1);
  if (e._len) e.setAttribute('stroke-dashoffset', (e._len*(1 - u)).toFixed(1));
  e.setAttribute('opacity', u > 0 ? 1 : 0);
}
// MASCARA DE BARRIDO: el nodo se descubre de izquierda a derecha
function barrido(nodo, x, y, w, h){
  const id = 'mgb' + (MGID++);
  const cp = mk('clipPath', {id}, mk('defs', {}, nodo.parentNode));
  const r = mk('rect', {x, y, width: 0, height: h}, cp);
  nodo.setAttribute('clip-path', `url(#${id})`);
  return u => r.setAttribute('width', (w*cl(u, 0, 1)).toFixed(1));
}
// texto partido en lineas que caben en `maxw` (centrado en 0,0)
function bloqueTexto(padre, texto, fam, tam, maxw, color, maxLineas){
  const g = mk('g', {}, padre), pal = String(texto).split(/\s+/), lineas = [];
  const prueba = txt(g, '', {'font-family': fam, 'font-size': tam});
  let act = '';
  pal.forEach(w => { const c = act ? act + ' ' + w : w; prueba.textContent = c;
    if (ancho(prueba) > maxw && act){ lineas.push(act); act = w; } else act = c; });
  if (act) lineas.push(act);
  prueba.remove();
  let mx = 0; const lh = tam*1.12;
  lineas.slice(0, maxLineas || 3).forEach((l, k, todas) => {
    const e = txt(g, l, {'font-family': fam, 'font-size': tam, fill: color, 'text-anchor': 'middle',
      y: ((k - (todas.length - 1)/2)*lh + tam*0.35).toFixed(1)});
    mx = Math.max(mx, ancho(e));
  });
  let k = 1;
  if (mx > maxw){ k = maxw/mx; g.setAttribute('transform', `scale(${k.toFixed(4)})`); }
  return {g, w: Math.min(mx, maxw), h: Math.min(lineas.length, maxLineas || 3)*lh*k};
}
function txt(padre, s, at){ const e = mk('text', at, padre); e.textContent = s; return e; }
function ancho(e){ try { return e.getComputedTextLength(); } catch(_) { return 0; } }

// ---------------------------------------------------------------- iconos
// Dibujados en una caja de 100x100 centrada en 0,0, con contorno grueso.
function icono(nombre, padre){
  const g = mk('g', {}, padre);
  const T = MGT.tinta, S = {stroke: T, 'stroke-width': 6, 'stroke-linejoin': 'round', 'stroke-linecap': 'round'};
  const a = (o) => Object.assign({}, S, o);
  switch (nombre){
    case 'cruz':
      mk('circle', a({r: 46, fill: MGT.oro}), g);
      mk('path', a({d: 'M-6,-32h12v14h14v12h-14v32h-12v-32h-14v-12h14z', fill: T, stroke: 'none'}), g); break;
    case 'corazon':
      mk('path', a({d: 'M0,40 C-60,0 -48,-46 -18,-40 C-6,-38 0,-28 0,-22 C0,-28 6,-38 18,-40 C48,-46 60,0 0,40z', fill: MGT.acento}), g);
      mk('path', {d: 'M-30,-22 C-28,-30 -20,-32 -14,-30', stroke: '#fff', 'stroke-width': 6, fill: 'none', 'stroke-linecap': 'round', opacity: .7}, g); break;
    case 'biblia':
      mk('rect', a({x: -32, y: -42, width: 64, height: 84, rx: 6, fill: MGT.tinta === '#241C3A' ? '#5B3A2E' : '#8E5A44'}), g);
      mk('rect', a({x: -24, y: -42, width: 4, height: 84, fill: MGT.oro, stroke: 'none'}), g);
      mk('path', a({d: 'M4,-22v28M-6,-12h20', stroke: MGT.oro, 'stroke-width': 7}), g); break;
    case 'moneda':
      mk('circle', a({r: 40, fill: MGT.oro}), g);
      mk('circle', {r: 29, fill: 'none', stroke: T, 'stroke-width': 3, opacity: .5}, g);
      txt(g, '$', {'text-anchor': 'middle', y: 16, 'font-size': 46, 'font-family': MGF.titulo, fill: T}); break;
    case 'celular':
      mk('rect', a({x: -24, y: -42, width: 48, height: 84, rx: 9, fill: T}), g);
      mk('rect', {x: -17, y: -32, width: 34, height: 58, rx: 3, fill: MGT.cielo}, g);
      mk('circle', {cy: 33, r: 3.5, fill: MGT.papel}, g); break;
    case 'corona':
      mk('path', a({d: 'M-40,22 L-44,-22 L-20,0 L0,-34 L20,0 L44,-22 L40,22z', fill: MGT.oro}), g);
      mk('rect', a({x: -40, y: 22, width: 80, height: 13, rx: 3, fill: MGT.oro}), g);
      mk('circle', {cx: 0, cy: 10, r: 6, fill: MGT.acento}, g); break;
    case 'paloma':
      mk('path', a({d: 'M-40,6 C-20,-6 -4,-2 6,8 C10,-24 26,-38 40,-36 C30,-22 30,-6 26,4 C34,6 40,10 44,16 C20,24 -10,26 -40,6z', fill: '#fff'}), g);
      mk('circle', {cx: 22, cy: 2, r: 3, fill: T}, g); break;
    case 'casa':
      mk('path', a({d: 'M-38,-2 L0,-38 L38,-2 V38 H-38z', fill: MGT.papel}), g);
      mk('path', a({d: 'M-46,2 L0,-44 L46,2', fill: 'none', stroke: MGT.acento, 'stroke-width': 9}), g);
      mk('rect', a({x: -11, y: 12, width: 22, height: 26, fill: MGT.oro}), g); break;
    case 'vela':
      mk('rect', a({x: -16, y: -6, width: 32, height: 50, rx: 4, fill: MGT.papel}), g);
      mk('path', a({d: 'M0,-46 C14,-30 12,-16 0,-12 C-12,-16 -14,-30 0,-46z', fill: MGT.oro}), g);
      mk('path', {d: 'M0,-30 C5,-24 4,-18 0,-17 C-4,-18 -5,-24 0,-30z', fill: MGT.acento}, g); break;
    case 'estrella':
      mk('path', a({d: 'M0,-44 L12,-14 L44,-12 L18,8 L28,40 L0,22 L-28,40 L-18,8 L-44,-12 L-12,-14z', fill: MGT.oro}), g); break;
    case 'pan':
      mk('path', a({d: 'M-44,14 C-44,-24 44,-24 44,14 C44,26 -44,26 -44,14z', fill: '#D99A4E'}), g);
      mk('path', {d: 'M-18,-6 l8,10 M0,-10 l8,10 M18,-6 l8,10', stroke: T, 'stroke-width': 5, 'stroke-linecap': 'round'}, g); break;
    case 'cadena':
      mk('path', a({d: 'M-46,-30 l14,10 m10,8 l14,10 m10,8 l14,10', stroke: MGT.suave, 'stroke-width': 10}), g);
      mk('circle', a({cx: 22, cy: 22, r: 24, fill: T}), g);
      txt(g, '!', {'text-anchor': 'middle', x: 22, y: 34, 'font-size': 34, 'font-family': MGF.titulo, fill: MGT.papel}); break;
    case 'pergamino':
      mk('rect', a({x: -34, y: -34, width: 68, height: 68, fill: '#F3DFAF'}), g);
      mk('rect', a({x: -42, y: -42, width: 84, height: 14, rx: 7, fill: '#C99556'}), g);
      mk('rect', a({x: -42, y: 30, width: 84, height: 14, rx: 7, fill: '#C99556'}), g);
      mk('path', {d: 'M-20,-12h40M-20,2h40M-20,16h26', stroke: T, 'stroke-width': 4, 'stroke-linecap': 'round', opacity: .6}, g); break;
    case 'reloj':
      mk('circle', a({r: 42, fill: MGT.papel}), g);
      mk('path', a({d: 'M0,0V-26M0,0L18,10', fill: 'none'}), g); break;
    case 'ojo':
      mk('path', a({d: 'M-46,0 C-24,-30 24,-30 46,0 C24,30 -24,30 -46,0z', fill: MGT.papel}), g);
      mk('circle', a({r: 16, fill: MGT.cielo}), g);
      mk('circle', {r: 7, fill: T}, g); mk('circle', {cx: -5, cy: -6, r: 3.5, fill: '#fff'}, g); break;
    case 'mano':
      mk('path', a({d: 'M-24,44 C-34,24 -40,4 -40,-6 C-40,-14 -30,-14 -27,-6 L-22,6 L-22,-34 C-22,-42 -11,-42 -11,-34 L-11,-6 L-11,-42 C-11,-50 0,-50 0,-42 L0,-6 L0,-38 C0,-46 11,-46 11,-38 L11,-4 L11,-28 C11,-36 22,-36 22,-28 L22,14 C22,30 14,40 10,44z', fill: '#E9B98F'}), g); break;
    case 'llave':
      mk('circle', a({cx: -24, r: 18, fill: 'none', stroke: MGT.oro, 'stroke-width': 11}), g);
      mk('path', a({d: 'M-8,0 H42 M28,0 V14 M40,0 V12', fill: 'none', stroke: MGT.oro, 'stroke-width': 11}), g); break;
    case 'puerta':
      mk('path', a({d: 'M-30,46 V-18 A30,30 0 0 1 30,-18 V46z', fill: '#8E5A44'}), g);
      mk('path', {d: 'M0,-46 V46', stroke: T, 'stroke-width': 4, opacity: .5}, g);
      mk('circle', {cx: 12, cy: 10, r: 4.5, fill: MGT.oro}, g); break;
    case 'montana':
      mk('path', a({d: 'M-48,40 L-12,-30 L4,-4 L18,-24 L48,40z', fill: '#8C7A64'}), g);
      mk('path', a({d: 'M-22,-10 L-12,-30 L-2,-10 L-8,-14 L-14,-6z', fill: '#fff', 'stroke-width': 4}), g); break;
    case 'sol':
      for (let k = 0; k < 8; k++){ const an = k*Math.PI/4; mk('line', a({x1: Math.cos(an)*30, y1: Math.sin(an)*30, x2: Math.cos(an)*46, y2: Math.sin(an)*46, 'stroke-width': 8, stroke: MGT.oro}), g); }
      mk('circle', a({r: 24, fill: MGT.oro}), g); break;
    case 'luna':
      mk('path', a({d: 'M14,-40 A42,42 0 1 0 14,40 A32,32 0 1 1 14,-40z', fill: MGT.oro}), g); break;
    case 'nube':
      mk('path', a({d: 'M-38,22 C-54,22 -54,-4 -36,-4 C-36,-28 -6,-34 4,-14 C14,-30 42,-22 38,0 C54,2 52,22 38,22z', fill: '#fff'}), g); break;
    case 'gota':
      mk('path', a({d: 'M0,-46 C18,-18 32,2 32,16 C32,34 18,44 0,44 C-18,44 -32,34 -32,16 C-32,2 -18,-18 0,-46z', fill: MGT.cielo}), g);
      mk('path', {d: 'M-14,14 C-14,24 -8,30 0,32', stroke: '#fff', 'stroke-width': 6, fill: 'none', 'stroke-linecap': 'round', opacity: .8}, g); break;
    case 'fuego':
      mk('path', a({d: 'M0,46 C-30,46 -38,22 -30,2 C-24,-12 -12,-18 -10,-40 C6,-28 10,-14 8,-2 C14,-8 18,-16 18,-24 C34,-6 40,16 30,32 C24,42 12,46 0,46z', fill: MGT.acento}), g);
      mk('path', {d: 'M0,40 C-14,40 -18,28 -12,16 C-8,8 -2,4 0,-6 C10,6 16,18 12,30 C10,36 6,40 0,40z', fill: MGT.oro}, g); break;
    case 'arbol':
      mk('rect', a({x: -8, y: 4, width: 16, height: 42, fill: '#8E5A44'}), g);
      mk('circle', a({cy: -12, r: 34, fill: MGT.acento2}), g);
      mk('circle', {cx: -12, cy: -18, r: 5, fill: MGT.acento}, g); mk('circle', {cx: 12, cy: -6, r: 5, fill: MGT.acento}, g); break;
    case 'pez':
      mk('path', a({d: 'M-36,0 C-20,-26 18,-26 30,0 C18,26 -20,26 -36,0z M28,0 L48,-18 L48,18z', fill: MGT.cielo}), g);
      mk('circle', {cx: -18, cy: -4, r: 4, fill: T}, g); break;
    case 'barca':
      mk('path', a({d: 'M-46,12 H46 L32,36 H-32z', fill: '#9C6A48'}), g);
      mk('path', a({d: 'M2,8 V-44 L36,4z', fill: MGT.papel}), g); break;
    case 'oveja':
      mk('path', a({d: 'M-14,30 v14 M14,30 v14', stroke: T, 'stroke-width': 7}), g);
      mk('path', a({d: 'M-36,16 C-48,4 -36,-14 -24,-12 C-22,-28 0,-30 6,-18 C16,-28 36,-20 32,-4 C44,4 36,26 22,26 C14,34 -8,34 -14,26 C-28,32 -40,26 -36,16z', fill: '#fff'}), g);
      mk('ellipse', a({cx: 36, cy: -12, rx: 12, ry: 15, fill: T}), g); break;
    case 'espada':
      mk('path', a({d: 'M-4,-46 L4,-46 L6,14 L-6,14z', fill: '#DDE3EA'}), g);
      mk('rect', a({x: -22, y: 14, width: 44, height: 9, rx: 3, fill: MGT.oro}), g);
      mk('rect', a({x: -5, y: 23, width: 10, height: 20, rx: 3, fill: '#8E5A44'}), g); break;
    case 'escudo':
      mk('path', a({d: 'M0,-44 L38,-30 C38,8 24,32 0,46 C-24,32 -38,8 -38,-30z', fill: MGT.acento2}), g);
      mk('path', {d: 'M0,-22 V24 M-16,-4 H16', stroke: MGT.papel, 'stroke-width': 9, 'stroke-linecap': 'round'}, g); break;
    case 'trompeta':
      mk('path', a({d: 'M-44,-6 H8 L40,-30 V30 L8,6 H-44z', fill: MGT.oro}), g); break;
    case 'tablas':
      [-22, 22].forEach(x => {
        mk('path', a({d: `M${x-20},44 V-20 A20,20 0 0 1 ${x+20},-20 V44z`, fill: '#C9C2B5'}), g);
        [-10, 4, 18, 32].forEach(yy => mk('line', {x1: x-11, y1: yy, x2: x+11, y2: yy, stroke: T, 'stroke-width': 4, 'stroke-linecap': 'round', opacity: .55}, g));
      }); break;
    case 'templo':
      mk('path', a({d: 'M-46,-14 L0,-42 L46,-14z', fill: MGT.oro}), g);
      [-34, -12, 12, 34].forEach(x => mk('rect', a({x: x - 6, y: -12, width: 12, height: 44, fill: MGT.papel, 'stroke-width': 4}), g));
      mk('rect', a({x: -48, y: 32, width: 96, height: 12, fill: MGT.papel}), g); break;
    case 'tumba':
      mk('path', a({d: 'M-48,40 C-46,-20 46,-20 48,40z', fill: '#A39584'}), g);
      mk('circle', a({cx: 18, cy: 20, r: 20, fill: '#7E7266'}), g);
      mk('path', {d: 'M-14,40 V18 A12,12 0 0 1 10,18', fill: T}, g); break;
    case 'lupa':
      mk('line', a({x1: 14, y1: 14, x2: 42, y2: 42, 'stroke-width': 14}), g);
      mk('circle', a({cx: -8, cy: -8, r: 28, fill: MGT.cielo, 'fill-opacity': .5}), g); break;
    case 'balanza':
      mk('path', a({d: 'M0,-40 V40 M-26,40 H26 M-40,-26 H40', fill: 'none'}), g);
      mk('path', a({d: 'M-40,-26 L-52,6 H-28z M40,-26 L28,6 H52z', fill: MGT.oro, 'stroke-width': 5}), g); break;
    case 'ancla':
      mk('path', a({d: 'M0,-30 V40 M-36,14 C-30,36 30,36 36,14 M-14,-14 H14', fill: 'none', 'stroke-width': 9}), g);
      mk('circle', a({cy: -38, r: 9, fill: 'none', 'stroke-width': 7}), g); break;
    case 'copa':
      mk('path', a({d: 'M-30,-40 H30 C30,-6 14,6 0,6 C-14,6 -30,-6 -30,-40z', fill: MGT.oro}), g);
      mk('path', a({d: 'M0,6 V32 M-20,40 H20', fill: 'none', 'stroke-width': 8}), g); break;
    case 'persona':
      mk('circle', a({cy: -26, r: 17, fill: '#E2B48A'}), g);
      mk('path', a({d: 'M-28,46 C-28,0 -16,-6 0,-6 C16,-6 28,0 28,46z', fill: MGT.acento2}), g); break;
    case 'chincheta':
      mk('path', a({d: 'M0,46 C-6,30 -32,8 -32,-14 A32,32 0 1 1 32,-14 C32,8 6,30 0,46z', fill: MGT.acento}), g);
      mk('circle', {cy: -14, r: 12, fill: MGT.papel}, g); break;
    case 'arena':
      mk('path', a({d: 'M-28,-44 H28 M-28,44 H28', 'stroke-width': 9}), g);
      mk('path', a({d: 'M-22,-40 H22 C22,-14 4,-6 4,0 C4,6 22,14 22,40 H-22 C-22,14 -4,6 -4,0 C-4,-6 -22,-14 -22,-40z', fill: MGT.papel}), g);
      mk('path', {d: 'M-14,36 C-8,22 8,22 14,36z M-10,-26 H10 C6,-16 2,-12 0,-8 C-2,-12 -6,-16 -10,-26z', fill: MGT.oro}, g); break;
    case 'pregunta': case 'check': case 'equis': {
      mk('circle', a({r: 44, fill: nombre === 'check' ? MGT.acento2 : MGT.acento}), g);
      if (nombre === 'pregunta') txt(g, '?', {'text-anchor': 'middle', y: 22, 'font-size': 64, 'font-family': MGF.titulo, fill: '#fff'});
      if (nombre === 'check') mk('path', {d: 'M-20,2 L-6,16 L22,-14', fill: 'none', stroke: '#fff', 'stroke-width': 11, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'}, g);
      if (nombre === 'equis') mk('path', {d: 'M-16,-16 L16,16 M16,-16 L-16,16', stroke: '#fff', 'stroke-width': 11, 'stroke-linecap': 'round'}, g);
      break; }
    case 'flecha':
      mk('path', a({d: 'M-44,-10 H10 V-30 L44,0 L10,30 V10 H-44z', fill: MGT.acento}), g); break;
    default:
      if (typeof iconoMas === 'function') iconoMas(nombre, g, a);
      else mk('circle', a({r: 30, fill: MGT.acento}), g);
  }
  return g;
}

// ---------------------------------------------------------------- piezas
// Cada constructor dibuja la pieza centrada en 0,0 y devuelve upd(T) para lo
// que se mueve DENTRO de ella.
function hazVersiculo(p, g){
  const tam0 = p.tam;
  let tam = tam0, lineas = [];
  const prueba = mk('text', {'font-family': MGF.verso, 'font-size': tam}, g);
  const medir = (s) => { prueba.textContent = s; prueba.setAttribute('font-size', tam); return ancho(prueba); };
  for (let intento = 0; intento < 6; intento++){
    lineas = []; let actual = [], w = 0; const esp = medir('n') * 0.55;
    p.palabras.forEach((pw, i) => {
      const a = medir(pw.t);
      if (actual.length && w + esp + a > p.w){ lineas.push({ps: actual, w}); actual = []; w = 0; }
      w += (actual.length ? esp : 0) + a; actual.push({i, a});
    });
    if (actual.length) lineas.push({ps: actual, w});
    if (lineas.length <= 5) break;
    tam *= 0.88;
  }
  prueba.remove();
  const lh = tam * 1.2, esp = (() => { const e = mk('text', {'font-family': MGF.verso, 'font-size': tam}, g); e.textContent = 'n'; const v = ancho(e)*0.55; e.remove(); return v; })();
  // alto total: cabecera + lineas + referencia + libro
  const cabH = p.cab ? tam * 0.66 : 0, refH = tam * 0.66, libH = tam * 2.9;
  const total = cabH + (p.cab ? tam*0.5 : 0) + lineas.length * lh + tam*0.45 + refH + tam*0.7 + libH;
  let y = -total / 2;
  const partes = [];
  // la cabecera: pastilla de tinta con letras de papel
  let cab = null;
  if (p.cab){
    cab = mk('g', {}, g);
    const t = txt(cab, p.cab, {'font-family': MGF.titulo, 'font-size': tam*0.37, 'letter-spacing': tam*0.09, fill: MGT.papel, 'text-anchor': 'middle', y: tam*0.12});
    const wc = ancho(t) + tam*0.9;
    const r = mk('rect', {x: -wc/2, y: -cabH/2, width: wc, height: cabH, rx: cabH/2, fill: MGT.tinta}, cab);
    cab.insertBefore(r, t);
    cab.setAttribute('data-y', y + cabH/2);
    y += cabH + tam*0.5;
  }
  // CADA LINEA ES UNA MASCARA: la palabra sube desde detras de su renglon
  // cuando suena; encima queda su sombra tenue para leer la forma del versiculo
  const palabras = [], ovalos = [];
  lineas.forEach(l => {
    let x = -l.w / 2;
    y += lh;
    const base = y - lh*0.22, id = 'mgm' + (MGID++);
    const cp = mk('clipPath', {id}, mk('defs', {}, g));
    mk('rect', {x: -p.w/2 - tam, y: base - tam*1.02, width: p.w + 2*tam, height: tam*1.34}, cp);
    const capa = mk('g', {'clip-path': `url(#${id})`}, g);
    l.ps.forEach(({i, a}) => {
      const pw = p.palabras[i];
      const color = pw.c === 1 ? MGT.acento : (pw.c === 2 ? MGT.acento2 : MGT.tinta);
      const sombra = txt(g, pw.t, {'font-family': MGF.verso, 'font-size': tam, fill: MGT.tinta, x: x.toFixed(1), y: base.toFixed(1), opacity: .13});
      g.insertBefore(sombra, capa);
      const e = txt(capa, pw.t, {'font-family': MGF.verso, 'font-size': tam, fill: color});
      palabras.push({e, sombra, x, y: base, en: pw.en, c: pw.c, a});
      if (pw.c === 1){
        // la palabra clave se RODEA a mano despues de decirla
        const o = mk('path', {d: trazoOvalo(x + a/2, base - tam*0.33, a/2 + tam*0.28, tam*0.62), fill: 'none',
          stroke: MGT.acento, 'stroke-width': Math.max(4, tam*0.07), 'stroke-linecap': 'round', opacity: 0}, g);
        ovalos.push({o, en: pw.en + 0.4});
      }
      x += a + esp;
    });
  });
  y += tam*0.45;
  const ref = mk('g', {}, g);
  const rt = txt(ref, p.ref, {'font-family': MGF.titulo, 'font-size': tam*0.34, 'letter-spacing': tam*0.08, fill: MGT.tinta, 'text-anchor': 'middle', y: tam*0.1});
  const wr = ancho(rt) + tam*0.8;
  ref.insertBefore(mk('rect', {x: -wr/2, y: -refH/2, width: wr, height: refH, rx: refH/2, fill: MGT.papel, stroke: MGT.acento2, 'stroke-width': Math.max(3, tam*0.06)}), rt);
  const refY = y + refH/2;
  y += refH + tam*0.7;
  // el libro abierto con su cinta y sus destellos
  const lib = mk('g', {}, g), libY = y + libH*0.5, lw = Math.min(p.w*0.95, libH*3.2);
  const rayos = mk('g', {}, lib);
  for (let k = 0; k < 14; k++){
    const ang = -Math.PI + (k + .5) * Math.PI / 14;
    mk('line', {x1: Math.cos(ang)*libH*0.55, y1: Math.sin(ang)*libH*0.55, x2: Math.cos(ang)*libH*1.05, y2: Math.sin(ang)*libH*1.05,
      stroke: MGT.oro, 'stroke-width': tam*0.09, 'stroke-linecap': 'round'}, rayos);
  }
  const sw = Math.max(4, tam*0.08);
  mk('path', {d: `M${-lw/2-sw},${-libH*0.32} L0,${-libH*0.22} L${lw/2+sw},${-libH*0.32} L${lw/2+sw},${libH*0.46} L0,${libH*0.52} L${-lw/2-sw},${libH*0.46}z`,
    fill: MGT.tinta}, lib);
  const hoja = (lado) => {
    const h = mk('g', {}, lib), s = lado;
    mk('path', {d: `M0,${-libH*0.26} C${s*lw*0.18},${-libH*0.42} ${s*lw*0.36},${-libH*0.4} ${s*lw*0.47},${-libH*0.34} L${s*lw*0.47},${libH*0.4} C${s*lw*0.34},${libH*0.34} ${s*lw*0.16},${libH*0.36} 0,${libH*0.46}z`,
      fill: MGT.papel, stroke: MGT.tinta, 'stroke-width': sw, 'stroke-linejoin': 'round'}, h);
    for (let k = 0; k < 5; k++){
      const yy = -libH*0.18 + k*libH*0.13;
      mk('line', {x1: s*lw*0.07, y1: yy, x2: s*lw*0.4, y2: yy - libH*0.02, stroke: MGT.suave, 'stroke-width': sw*0.7, 'stroke-linecap': 'round'}, h);
    }
    return h;
  };
  const izq = hoja(-1), der = hoja(1);
  const cinta = mk('path', {d: `M${-sw},${libH*0.4} h${sw*2.4} v${libH*0.42} l${-sw*1.2},${-libH*0.1} l${-sw*1.2},${libH*0.1}z`, fill: MGT.acento}, lib);
  lib.insertBefore(cinta, izq);
  return function(T){
    if (cab){
      const s = T - p.en, r = resorte(s, 14, .45);
      cab.setAttribute('transform', `translate(0,${+cab.getAttribute('data-y')}) scale(${Math.max(0.001, r)})`);
    }
    palabras.forEach(w => {
      const s = T - w.en;
      const r = s <= 0 ? 0 : resorte(s, 15, .6);
      w.e.setAttribute('opacity', s > 0 ? 1 : 0);
      w.e.setAttribute('transform', `translate(${w.x.toFixed(1)},${(w.y + (1 - r)*tam*1.15).toFixed(1)})`);
      w.sombra.setAttribute('opacity', (s <= 0 ? .13 : .13*cl(1 - s/0.25, 0, 1)).toFixed(3));
    });
    ovalos.forEach(v => dibujar(v.o, eOut((T - v.en)/0.5)));
    const sr = T - p.ref_en, rr = resorte(sr, 12, .4);
    ref.setAttribute('transform', `translate(0,${(refY + (1 - rr)*tam*1.2).toFixed(1)})`);
    ref.setAttribute('opacity', cl(sr/0.15, 0, 1).toFixed(3));
    const sl = T - p.libro_en, ab = resorte(sl, 10, .38);
    lib.setAttribute('transform', `translate(0,${libY.toFixed(1)}) scale(${Math.max(0.001, cl(sl/0.25, 0, 1)).toFixed(3)})`);
    izq.setAttribute('transform', `scale(${Math.max(0.02, ab).toFixed(3)},1)`);
    der.setAttribute('transform', `scale(${Math.max(0.02, ab).toFixed(3)},1)`);
    const sr2 = sl - 0.4;
    rayos.setAttribute('opacity', (cl(sr2/0.4, 0, 1) * (0.75 + 0.25*Math.sin(T*3))).toFixed(3));
    rayos.setAttribute('transform', `translate(0,${-libH*0.25}) scale(${(0.6 + 0.4*eOut(sr2/0.6) + 0.04*Math.sin(T*2.2)).toFixed(3)})`);
  };
}

function sector(r, a0, a1){
  const p = (a) => [Math.sin(a)*r, -Math.cos(a)*r];
  const [x0, y0] = p(a0), [x1, y1] = p(a1);
  const grande = (a1 - a0) > Math.PI ? 1 : 0;
  return `M0,0 L${x0.toFixed(1)},${y0.toFixed(1)} A${r},${r} 0 ${grande} 1 ${x1.toFixed(1)},${y1.toFixed(1)}z`;
}

function hazReloj(p, g){
  const r = p.r, modo = p.modo, sw = Math.max(5, r*0.05);
  const ang = (h) => (modo === 24 ? h/24 : (h % 12)/12) * Math.PI*2 + (modo === 12 && h % 12 === 0 && h >= 12 ? 0 : 0);
  const angH = (desde, hasta) => {
    let a0 = ang(desde), a1 = a0 + (hasta - desde) / modo * Math.PI*2;
    return [a0, a1];
  };
  let titulo = null;
  if (p.titulo){
    titulo = txt(g, p.titulo, {'font-family': MGF.titulo, 'font-size': r*0.15, 'letter-spacing': r*0.03, fill: MGT.tinta, 'text-anchor': 'middle', y: -r*1.22});
  }
  let barreTitulo = null;
  mk('circle', {cx: r*0.06, cy: r*0.07, r: r, fill: MGT.tinta, opacity: .9}, g);
  mk('circle', {r: r, fill: MGT.papel, stroke: MGT.tinta, 'stroke-width': sw}, g);
  const sectores = p.porciones.map(por => {
    const e = mk('path', {fill: col(por.color), opacity: .88}, g);
    return {por, e, a: angH(por.desde, por.hasta)};
  });
  const marcas = modo === 24 ? 24 : 12;
  for (let k = 0; k < marcas; k++){
    const a = k / marcas * Math.PI*2, larga = modo === 24 ? k % 6 === 0 : k % 3 === 0;
    const r0 = r*(larga ? 0.8 : 0.88);
    mk('line', {x1: Math.sin(a)*r0, y1: -Math.cos(a)*r0, x2: Math.sin(a)*r*0.96, y2: -Math.cos(a)*r*0.96,
      stroke: MGT.tinta, 'stroke-width': larga ? sw*0.9 : sw*0.5, 'stroke-linecap': 'round'}, g);
  }
  const numeros = modo === 24 ? [[0, '0'], [6, '6'], [12, '12'], [18, '18']] : [[0, '12'], [3, '3'], [6, '6'], [9, '9']];
  numeros.forEach(([h, s]) => {
    const a = h / (modo === 24 ? 24 : 12) * Math.PI*2;
    txt(g, s, {'font-family': MGF.titulo, 'font-size': r*0.13, fill: MGT.suave, 'text-anchor': 'middle',
      x: Math.sin(a)*r*0.64, y: -Math.cos(a)*r*0.64 + r*0.05});
  });
  const etiquetas = sectores.map(s => {
    const e = mk('g', {}, g);
    const t = txt(e, s.por.etq, {'font-family': MGF.titulo, 'font-size': r*0.12, fill: MGT.papel, 'text-anchor': 'middle', y: r*0.04});
    const w = ancho(t) + r*0.16;
    e.insertBefore(mk('rect', {x: -w/2, y: -r*0.1, width: w, height: r*0.2, rx: r*0.1, fill: MGT.tinta}), t);
    return e;
  });
  const aguja = mk('line', {x1: 0, y1: 0, x2: 0, y2: -r*0.78, stroke: MGT.tinta, 'stroke-width': sw*1.2, 'stroke-linecap': 'round'}, g);
  mk('circle', {r: sw*1.5, fill: MGT.tinta}, g);
  let pie = null;
  if (p.pie){
    pie = mk('g', {}, g);
    const t = txt(pie, p.pie, {'font-family': MGF.titulo, 'font-size': r*0.19, fill: MGT.acento, 'text-anchor': 'middle', y: r*0.06});
    const w = ancho(t) + r*0.3;
    pie.insertBefore(mk('rect', {x: -w/2, y: -r*0.14, width: w, height: r*0.28, rx: r*0.06, fill: MGT.papel, stroke: MGT.tinta, 'stroke-width': sw*0.7}), t);
  }
  // que el titulo y el pie no se salgan del cuadro
  const encaja = (e, max) => { const a = ancho(e); if (a > max){ const fs = parseFloat(e.getAttribute('font-size')) * max / a; e.setAttribute('font-size', fs.toFixed(1)); e.setAttribute('letter-spacing', (fs*0.12).toFixed(1)); } };
  if (titulo){ encaja(titulo, MG.W*0.88); const aw = ancho(titulo) + 20, fs = parseFloat(titulo.getAttribute('font-size'));
    barreTitulo = barrido(titulo, -aw/2, -r*1.22 - fs, aw, fs*1.4); }
  if (pie){
    const t = pie.querySelector('text'), caja = pie.querySelector('rect');
    encaja(t, MG.W*0.8);
    const w = ancho(t) + r*0.3;
    caja.setAttribute('x', -w/2); caja.setAttribute('width', w);
  }
  return function(T){
    let aguja_a = sectores.length ? sectores[0].a[0] : 0;
    sectores.forEach((s, k) => {
      const u = eOut((T - s.por.en) / s.por.dur);
      if (u <= 0){ s.e.setAttribute('d', ''); etiquetas[k].setAttribute('opacity', 0); return; }
      const a1 = lerp(s.a[0], s.a[1], u);
      s.e.setAttribute('d', sector(r*0.93, s.a[0], Math.max(s.a[0] + 0.001, a1)));
      aguja_a = a1;
      const mid = (s.a[0] + s.a[1]) / 2, rr = resorte(T - s.por.en - s.por.dur*0.6, 13, .45);
      etiquetas[k].setAttribute('opacity', cl((T - s.por.en - s.por.dur*0.6)/0.12, 0, 1));
      etiquetas[k].setAttribute('transform', `translate(${(Math.sin(mid)*r*0.5).toFixed(1)},${(-Math.cos(mid)*r*0.5).toFixed(1)}) scale(${Math.max(0.001, rr).toFixed(3)})`);
    });
    aguja.setAttribute('transform', `rotate(${(aguja_a*180/Math.PI).toFixed(2)})`);
    if (barreTitulo) barreTitulo(eIO((T - p.en - 0.25)/0.6));
    if (pie){
      const s = T - p.pie_en, rr = resorte(s, 12, .4);
      pie.setAttribute('opacity', cl(s/0.12, 0, 1));
      pie.setAttribute('transform', `translate(0,${(r*1.32 + (1 - rr)*r*0.4).toFixed(1)}) scale(${Math.max(0.001, 0.6 + 0.4*rr).toFixed(3)})`);
    }
  };
}

function puntosRuta(a, b, n){
  // un arco suave entre dos sitios (la ruta no es una regla)
  const mx = (a[0] + b[0])/2, my = (a[1] + b[1])/2, dx = b[0] - a[0], dy = b[1] - a[1];
  const cx = mx - dy*0.18, cy = my + dx*0.18, out = [];
  for (let k = 0; k <= n; k++){
    const u = k/n;
    out.push([(1-u)*(1-u)*a[0] + 2*(1-u)*u*cx + u*u*b[0], (1-u)*(1-u)*a[1] + 2*(1-u)*u*cy + u*u*b[1]]);
  }
  return out;
}

function hazMapa(p, g){
  const w = p.w, h = p.h, sw = Math.max(5, w*0.008), rx = w*0.04;
  const id = 'mgclip' + Math.round(p.x) + '_' + Math.round(p.y);
  const defs = mk('defs', {}, g);
  const cp = mk('clipPath', {id}, defs);
  mk('rect', {x: -w/2, y: -h/2, width: w, height: h, rx}, cp);
  mk('rect', {x: -w/2 + w*0.018, y: -h/2 + w*0.022, width: w, height: h, rx, fill: MGT.tinta}, g);
  mk('rect', {x: -w/2, y: -h/2, width: w, height: h, rx, fill: MGT.tierra}, g);
  const dentro = mk('g', {'clip-path': `url(#${id})`}, g);
  for (let k = 1; k < 6; k++){
    mk('line', {x1: -w/2 + k*w/6, y1: -h/2, x2: -w/2 + k*w/6, y2: h/2, stroke: MGT.suave, 'stroke-width': 2, opacity: .25, 'stroke-dasharray': '8 10'}, dentro);
    mk('line', {x1: -w/2, y1: -h/2 + k*h/6, x2: w/2, y2: -h/2 + k*h/6, stroke: MGT.suave, 'stroke-width': 2, opacity: .25, 'stroke-dasharray': '8 10'}, dentro);
  }
  if (p.costa){
    const pts = p.costa.mar.map(q => q.join(',')).join(' ');
    mk('polygon', {points: pts, fill: MGT.mar, stroke: MGT.tinta, 'stroke-width': sw*0.7, 'stroke-linejoin': 'round'}, dentro);
    if (p.costa.etq) txt(dentro, 'MAR GRANDE', {'font-family': MGF.titulo, 'font-size': w*0.032, 'letter-spacing': w*0.008, fill: MGT.tinta, opacity: .4,
      'text-anchor': 'middle', x: p.costa.etq[0], y: p.costa.etq[1]});
    mk('polyline', {points: p.costa.rio.map(q => q.join(',')).join(' '), fill: 'none', stroke: MGT.cielo, 'stroke-width': sw*0.9, 'stroke-linecap': 'round'}, dentro);
    p.costa.lagos.forEach(l => mk('ellipse', {cx: l.c[0], cy: l.c[1], rx: Math.max(6, l.rx), ry: Math.max(8, l.ry), fill: MGT.mar, stroke: MGT.tinta, 'stroke-width': sw*0.5}, dentro));
  }
  mk('rect', {x: -w/2, y: -h/2, width: w, height: h, rx, fill: 'none', stroke: MGT.tinta, 'stroke-width': sw}, g);
  // la rosa: una N sobre una flecha
  const rosa = mk('g', {transform: `translate(${w/2 - w*0.08},${-h/2 + w*0.1})`}, g);
  mk('path', {d: `M0,${-w*0.045} L${w*0.022},${w*0.03} L0,${w*0.015} L${-w*0.022},${w*0.03}z`, fill: MGT.acento, stroke: MGT.tinta, 'stroke-width': sw*0.4, 'stroke-linejoin': 'round'}, rosa);
  txt(rosa, 'N', {'font-family': MGF.titulo, 'font-size': w*0.032, fill: MGT.tinta, 'text-anchor': 'middle', y: -w*0.055});
  // la escala
  const esc = mk('g', {transform: `translate(${-w/2 + w*0.06},${h/2 - w*0.06})`}, g);
  mk('line', {x1: 0, y1: 0, x2: p.escala.px, y2: 0, stroke: MGT.tinta, 'stroke-width': sw, 'stroke-linecap': 'round'}, esc);
  mk('line', {x1: 0, y1: -w*0.012, x2: 0, y2: w*0.012, stroke: MGT.tinta, 'stroke-width': sw*0.6}, esc);
  mk('line', {x1: p.escala.px, y1: -w*0.012, x2: p.escala.px, y2: w*0.012, stroke: MGT.tinta, 'stroke-width': sw*0.6}, esc);
  txt(esc, p.escala.texto, {'font-family': MGF.titulo, 'font-size': w*0.026, fill: MGT.tinta, x: p.escala.px/2, y: -w*0.02, 'text-anchor': 'middle'});
  // las rutas, debajo de las chinchetas
  const rutas = p.tramos.map(tr => {
    const a = p.lugares[tr.a], b = p.lugares[tr.b];
    const pts = puntosRuta([a.x, a.y], [b.x, b.y], 40);
    const camino = mk('polyline', {fill: 'none', stroke: MGT.acento, 'stroke-width': sw*1.1, 'stroke-linecap': 'round', 'stroke-dasharray': `${sw*1.6} ${sw*1.5}`}, g);
    const viajero = mk('circle', {r: sw*1.5, fill: MGT.acento, stroke: MGT.papel, 'stroke-width': sw*0.6}, g);
    const et = mk('g', {}, g);
    const t = txt(et, '0 km', {'font-family': MGF.titulo, 'font-size': w*0.05, fill: MGT.papel, 'text-anchor': 'middle', y: w*0.017});
    // la distancia va AL LADO de la ruta (no encima de las chinchetas)
    let nx = -(b.y - a.y), ny = b.x - a.x; const ln = Math.hypot(nx, ny) || 1;
    nx /= ln; ny /= ln; if (nx > 0){ nx = -nx; ny = -ny; }
    const mid = [pts[20][0] + nx*w*0.14, pts[20][1] + ny*w*0.14 + w*0.07];
    return {tr, pts, camino, viajero, et, t, mid};
  });
  const pins = p.lugares.map(l => {
    const e = mk('g', {}, g);
    const sombra = mk('ellipse', {cx: l.x, cy: l.y + w*0.004, rx: w*0.022, ry: w*0.008, fill: MGT.tinta, opacity: .3}, g);
    g.insertBefore(sombra, e);
    const R = w*(l.ref ? 0.024 : 0.032);
    mk('path', {d: `M0,0 C${-R*0.4},${-R*1.1} ${-R*1.1},${-R*1.5} ${-R*1.1},${-R*2.3} A${R*1.1},${R*1.1} 0 1 1 ${R*1.1},${-R*2.3} C${R*1.1},${-R*1.5} ${R*0.4},${-R*1.1} 0,0z`,
      fill: l.ref ? MGT.acento2 : MGT.acento, stroke: MGT.tinta, 'stroke-width': sw*0.7, 'stroke-linejoin': 'round'}, e);
    mk('circle', {cy: -R*2.3, r: R*0.42, fill: MGT.papel}, e);
    const et = mk('g', {}, g);
    const t = txt(et, l.n, {'font-family': MGF.titulo, 'font-size': w*(l.ref ? 0.034 : 0.044), fill: MGT.tinta, 'text-anchor': 'middle', y: w*0.014});
    const tw = ancho(t) + w*0.04;
    et.insertBefore(mk('rect', {x: -tw/2, y: -w*0.03, width: tw, height: w*0.06, rx: w*0.03, fill: MGT.papel, stroke: MGT.tinta, 'stroke-width': sw*0.5}), t);
    // la etiqueta va debajo si hay sitio, encima si no
    const otros = p.lugares.filter(o => o !== l);
    const media = otros.length ? otros.reduce((a, o) => a + o.y, 0) / otros.length : l.y - 1;
    // debajo si los otros quedan arriba, encima si quedan abajo; si no hay
    // sitio, a la derecha de la chincheta
    const cabeAbajo = l.y + w*0.09 < h/2 - w*0.08, cabeArriba = l.y - R*2.3 - w*0.1 > -h/2;
    let dx = 0, dy;
    if (media <= l.y && cabeAbajo) dy = w*0.05;
    else if (media > l.y && cabeArriba) dy = -R*2.3 - w*0.07;
    else { dx = R*1.4 + tw/2; dy = -R*1.6; }
    return {l, e, sombra, et, R, dx, dy};
  });
  return function(T){
    pins.forEach(pn => {
      const s = T - pn.l.en, r = resorte(s, 12, .38);
      const vis = s > 0;
      pn.e.setAttribute('opacity', vis ? 1 : 0);
      // cae desde arriba, se aplasta al llegar y se estira al rebotar
      const caida = (1 - r) * -h*0.35;
      const sq = vis ? 1 + cl((r - 1)*1.6, -0.25, 0.3) : 1;
      pn.e.setAttribute('transform', `translate(${pn.l.x},${(pn.l.y + caida).toFixed(1)}) scale(${(1/sq).toFixed(3)},${sq.toFixed(3)})`);
      pn.sombra.setAttribute('opacity', vis ? (0.3*cl(r, 0, 1)).toFixed(3) : 0);
      const se = s - 0.25, re = resorte(se, 14, .45);
      pn.et.setAttribute('opacity', se > 0 ? 1 : 0);
      pn.et.setAttribute('transform', `translate(${(pn.l.x + pn.dx).toFixed(1)},${(pn.l.y + pn.dy).toFixed(1)}) scale(${Math.max(0.001, re).toFixed(3)})`);
    });
    rutas.forEach(ru => {
      const s = T - ru.tr.en, u = eIO(s / 1.3);
      if (s <= 0){ ru.camino.setAttribute('points', ''); ru.viajero.setAttribute('opacity', 0); ru.et.setAttribute('opacity', 0); return; }
      const n = Math.max(1, Math.round(u * (ru.pts.length - 1)));
      ru.camino.setAttribute('points', ru.pts.slice(0, n + 1).map(q => q[0].toFixed(1) + ',' + q[1].toFixed(1)).join(' '));
      const q = ru.pts[n];
      ru.viajero.setAttribute('cx', q[0].toFixed(1)); ru.viajero.setAttribute('cy', q[1].toFixed(1));
      ru.viajero.setAttribute('opacity', u < 1 ? 1 : cl(1 - (s - 1.3)/0.3, 0, 1));
      // la distancia CUENTA mientras se dibuja la ruta
      ru.t.textContent = Math.round(ru.tr.km * u) + ' km';
      const tw = ancho(ru.t) + w*0.06;
      let caja = ru.et.querySelector('rect');
      if (!caja){ caja = mk('rect', {rx: w*0.035, fill: MGT.tinta}); ru.et.insertBefore(caja, ru.t); }
      caja.setAttribute('x', -tw/2); caja.setAttribute('y', -w*0.038); caja.setAttribute('width', tw); caja.setAttribute('height', w*0.076);
      const r = resorte(s, 13, .45);
      ru.et.setAttribute('opacity', 1);
      ru.et.setAttribute('transform', `translate(${ru.mid[0].toFixed(1)},${(ru.mid[1] - w*0.07).toFixed(1)}) scale(${Math.max(0.001, r).toFixed(3)}) rotate(${(-3*Math.exp(-s*3)*Math.sin(s*10)).toFixed(2)})`);
    });
  };
}

function hazLinea(p, g){
  const w = p.w, sw = Math.max(6, w*0.01), tam = Math.min(w*0.095, MG.H*0.07);
  const eje = mk('line', {x1: -w/2, y1: 0, x2: -w/2, y2: 0, stroke: MGT.tinta, 'stroke-width': sw, 'stroke-linecap': 'round'}, g);
  const punta = mk('path', {d: `M0,${-sw*2} L${sw*3},0 L0,${sw*2}z`, fill: MGT.tinta}, g);
  const puntero = mk('path', {d: `M0,${-sw*1.2} L${-sw*2},${-sw*4.4} L${sw*2},${-sw*4.4}z`, fill: MGT.acento, stroke: MGT.tinta, 'stroke-width': sw*0.4, 'stroke-linejoin': 'round'}, g);
  const evs = p.eventos.map((ev, k) => {
    const dir = ev.arriba ? -1 : 1, largo = tam*1.6;
    const tallo = mk('line', {x1: ev.x, y1: 0, x2: ev.x, y2: 0, stroke: MGT.tinta, 'stroke-width': sw*0.6}, g);
    const punto = mk('circle', {cx: ev.x, cy: 0, r: sw*1.5, fill: k === 0 ? MGT.acento : MGT.oro, stroke: MGT.tinta, 'stroke-width': sw*0.6}, g);
    const tarj = mk('g', {}, g);
    const t1 = txt(tarj, ev.etq, {'font-family': MGF.titulo, 'font-size': tam, fill: ev.etq === 'HOY' ? MGT.acento2 : MGT.acento, 'text-anchor': 'middle', y: tam*0.35});
    let anchoT = ancho(t1);
    let alto = tam*1.25;
    if (ev.txt){
      const t2 = txt(tarj, ev.txt, {'font-family': MGF.titulo, 'font-size': tam*0.4, fill: MGT.tinta, 'text-anchor': 'middle', y: tam*0.95, opacity: .8});
      anchoT = Math.max(anchoT, ancho(t2)); alto += tam*0.55;
    }
    const wc = Math.min(w*0.55, anchoT + tam*0.6);
    tarj.insertBefore(mk('rect', {x: -wc/2, y: -tam*0.62, width: wc, height: alto, rx: tam*0.25, fill: MGT.papel, stroke: MGT.tinta, 'stroke-width': sw*0.6}), tarj.firstChild);
    const cy = dir < 0 ? -largo - alto + tam*0.62 : largo + tam*0.62;
    // la tarjeta no se sale por los lados: se corre y el tallo la sigue
    const m = MG.W*0.04, cx2 = cl(ev.x, -MG.W/2 + m + wc/2, MG.W/2 - m - wc/2);
    return {ev, tallo, punto, tarj, dir, largo, cy, cx: cx2};
  });
  let llave = null;
  if (p.tramo && evs.length > 1){
    llave = mk('g', {}, g);
    const a = evs[p.tramo.a].ev.x, b = evs[p.tramo.b].ev.x;
    const yy = tam*0.9 + (evs.some(e => e.dir > 0) ? tam*2.9 : 0);
    mk('path', {d: `M${a},${yy - tam*0.3} Q${a},${yy} ${a + tam*0.3},${yy} L${(a+b)/2 - tam*0.3},${yy} Q${(a+b)/2},${yy} ${(a+b)/2},${yy + tam*0.3} Q${(a+b)/2},${yy} ${(a+b)/2 + tam*0.3},${yy} L${b - tam*0.3},${yy} Q${b},${yy} ${b},${yy - tam*0.3}`,
      fill: 'none', stroke: MGT.acento2, 'stroke-width': sw*0.7, 'stroke-linecap': 'round'}, llave);
    const lt = txt(llave, '', {'font-family': MGF.titulo, 'font-size': tam*0.7, fill: MGT.acento2, 'text-anchor': 'middle', x: (a+b)/2, y: yy + tam*1.05});
    llave._t = lt;
  }
  return function(T){
    const u = eIO((T - p.en) / 0.8);
    eje.setAttribute('x2', (-w/2 + w*u).toFixed(1));
    punta.setAttribute('transform', `translate(${(-w/2 + w*u).toFixed(1)},0)`);
    punta.setAttribute('opacity', u > 0.02 ? 1 : 0);
    // el puntero viaja (con anticipacion) al ultimo año que se ha dicho
    let x = evs.length ? evs[0].ev.x : 0, desde = x, tcambio = -1;
    evs.forEach(e => { if (T >= e.ev.en){ desde = x; x = e.ev.x; tcambio = e.ev.en; } });
    const um = eBack((T - tcambio) / 0.6);
    const px = tcambio < 0 ? x : lerp(desde, x, um);
    puntero.setAttribute('transform', `translate(${px.toFixed(1)},${(-Math.abs(Math.sin(T*4))*sw*0.6).toFixed(1)})`);
    puntero.setAttribute('opacity', cl((T - p.en - 0.4)/0.2, 0, 1));
    evs.forEach(e => {
      const s = T - e.ev.en;
      const rp = resorte(s, 15, .4);
      e.punto.setAttribute('r', (sw*1.5*Math.max(0, rp)).toFixed(2));
      const ut = eOut(s / 0.3);
      e.tallo.setAttribute('y2', (e.dir * e.largo * ut).toFixed(1));
      const rt = resorte(s - 0.15, 12, .4);
      e.tarj.setAttribute('opacity', s > 0.15 ? 1 : 0);
      const caida = (1 - rt) * e.dir * -tam*2.2;
      e.tarj.setAttribute('transform', `translate(${e.cx.toFixed(1)},${(e.cy + caida).toFixed(1)}) scale(${(0.7 + 0.3*cl(rt, 0, 1.2)).toFixed(3)})`);
    });
    if (llave){
      const s = T - p.tramo.en, uu = eOut(s / 0.9);
      llave.setAttribute('opacity', cl(s/0.2, 0, 1));
      llave._t.textContent = p.tramo.etq.replace('{n}', Math.round(p.tramo.n * uu).toLocaleString('es'));
    }
  };
}

function hazLamina(p, g){
  const w = p.w, h = p.h, sw = Math.max(6, w*0.012), r = w*0.035;
  const id = 'mglam' + Math.round(p.x) + '_' + Math.round(p.y);
  const cp = mk('clipPath', {id}, mk('defs', {}, g));
  mk('rect', {x: -w/2, y: -h/2, width: w, height: h, rx: r}, cp);
  mk('rect', {x: -w/2 + sw*2.2, y: -h/2 + sw*2.6, width: w, height: h, rx: r, fill: MGT.tinta}, g);
  const caja = mk('g', {'clip-path': `url(#${id})`}, g);
  mk('rect', {x: -w/2, y: -h/2, width: w, height: h, fill: MGT.papel}, caja);
  const img = mk('image', {href: p.href, x: -w/2, y: -h/2, width: w, height: h, preserveAspectRatio: 'xMidYMid slice'}, caja);
  mk('rect', {x: -w/2, y: -h/2, width: w, height: h, rx: r, fill: 'none', stroke: MGT.tinta, 'stroke-width': sw}, g);
  [[-1, -1], [1, -1]].forEach(([sx]) => {
    mk('rect', {x: -w*0.07, y: -h*0.02, width: w*0.14, height: h*0.05, fill: MGT.oro, opacity: .82,
      transform: `translate(${sx*w*0.4},${-h/2}) rotate(${sx*-28})`}, g);
  });
  return function(T){
    const u = cl((T - p.en) / Math.max(1, p.fin - p.en), 0, 1);
    img.setAttribute('transform', `scale(${(1 + 0.07*u).toFixed(4)})`);
  };
}

function hazTexto(p, g0){
  const tam = p.tam, partes = [], g = mk('g', {}, g0);
  let x = 0;
  const esp = tam*0.28;
  const id = 'mgm' + (MGID++);
  const cpr = mk('rect', {x: -1e4, y: -tam*0.75, width: 2e4, height: tam*1.25}, mk('clipPath', {id}, mk('defs', {}, g)));
  const capa = mk('g', {'clip-path': `url(#${id})`}, g);
  p.palabras.forEach(pw => {
    const e = txt(capa, pw.t, {'font-family': MGF.titulo, 'font-size': tam, fill: pw.c ? MGT.acento : MGT.tinta,
      stroke: MGT.papel, 'stroke-width': tam*0.06, 'paint-order': 'stroke', 'stroke-linejoin': 'round'});
    const a = ancho(e);
    partes.push({e, x, a, en: pw.en});
    x += a + esp;
  });
  const total = x - esp;
  if (total > p.w) g.setAttribute('transform', `scale(${(p.w/total).toFixed(4)})`);
  return function(T){
    partes.forEach(q => {
      // sube desde detras de la mascara del renglon
      const s = T - q.en, r = resorte(s, 15, .55);
      q.e.setAttribute('opacity', s > 0 ? 1 : 0);
      q.e.setAttribute('transform', `translate(${(q.x - total/2).toFixed(1)},${(tam*0.35 + (1 - r)*tam*1.15).toFixed(1)})`);
    });
  };
}

function hazIcono(p, g){
  const k = p.tam / 100;
  const ic = icono(p.nombre, g);
  ic.setAttribute('transform', `scale(${k.toFixed(4)})`);
  return function(T){
    // ya en su sitio respira un poco: sigue vivo sin distraer
    const s = T - p.en - 0.7;
    if (s > 0) ic.setAttribute('transform', `rotate(${(4*Math.sin(s*2.1)).toFixed(2)}) scale(${(k*(1 + 0.03*Math.sin(s*3.3))).toFixed(4)})`);
  };
}

function hazContador(p, g){
  const tam = p.tam;
  const num = txt(g, '0', {'font-family': MGF.titulo, 'font-size': tam, fill: MGT.acento, 'text-anchor': 'middle', y: (-tam*0.12).toFixed(1),
    stroke: MGT.papel, 'stroke-width': tam*0.05, 'paint-order': 'stroke'});
  const etq = txt(g, p.etq, {'font-family': MGF.titulo, 'font-size': tam*0.26, 'letter-spacing': tam*0.04, fill: MGT.tinta, 'text-anchor': 'middle', y: (tam*0.3).toFixed(1)});
  let ew = ancho(etq);
  if (ew > p.w){ etq.setAttribute('font-size', (tam*0.26*p.w/ew).toFixed(1)); ew = p.w; }
  const barre = barrido(etq, -ew/2 - 10, tam*0.0, ew + 20, tam*0.45);
  // los pictogramas aparecen A LA VEZ que cuenta el numero
  const k = p.n <= 12 ? p.n : 40, cols = p.n <= 12 ? Math.min(p.n, 6) : 10;
  const filas = Math.ceil(k/cols), lado = Math.min(p.w/cols, tam*0.58, MG.H*0.34/filas), pics = [];
  for (let j = 0; j < k; j++){
    const fila = Math.floor(j/cols), c = j % cols, enFila = Math.min(cols, k - fila*cols);
    const e = mk('g', {}, g);
    if (p.n <= 12){ const ic = icono(p.icono, e); ic.setAttribute('transform', `scale(${(lado*0.82/100).toFixed(4)})`); }
    else mk('circle', {r: lado*0.3, fill: j % 2 ? MGT.acento2 : MGT.acento, stroke: MGT.tinta, 'stroke-width': lado*0.05}, e);
    pics.push({e, x: (c - (enFila - 1)/2)*lado, y: tam*0.62 + fila*lado + lado/2, t: p.en + (p.fin - p.en)*(j + 1)/k});
  }
  const nota = p.n > 12 ? txt(g, 'cada ● = ' + Math.round(p.n/40).toLocaleString('es'), {'font-family': MGF.titulo, 'font-size': tam*0.17,
    fill: MGT.suave, 'text-anchor': 'middle', y: (tam*0.75 + filas*lado).toFixed(1)}) : null;
  return function(T){
    const u = eOut((T - p.en) / Math.max(0.3, p.fin - p.en));
    num.textContent = Math.round(p.n*u).toLocaleString('es');
    const s2 = T - p.fin, golpe = s2 > 0 ? 1 + 0.16*Math.exp(-s2*6)*Math.sin(Math.min(s2*14, Math.PI)) : 1;
    num.setAttribute('transform', `translate(0,${(-tam*0.45).toFixed(1)}) scale(${golpe.toFixed(3)}) translate(0,${(tam*0.45).toFixed(1)})`);
    barre(eIO((T - p.en - 0.2)/0.55));
    pics.forEach(q => { const s = T - q.t, r = resorte(s, 16, .4);
      q.e.setAttribute('opacity', s > 0 ? 1 : 0);
      q.e.setAttribute('transform', `translate(${q.x.toFixed(1)},${(q.y - (1 - r)*lado*0.8).toFixed(1)}) scale(${Math.max(0.001, r).toFixed(3)})`); });
    if (nota) nota.setAttribute('opacity', cl((T - p.fin)/0.3, 0, 1).toFixed(3));
  };
}

function hazComparacion(p, g){
  const tam = p.tam, v = p.vertical, cw = v ? p.w*0.92 : p.w*0.44, sw = Math.max(5, tam*0.09);
  const tarjeta = (texto, borde, cx, cy) => {
    const t = mk('g', {}, g), sombra = mk('rect', {}, t), caja = mk('rect', {}, t);
    const b = bloqueTexto(t, texto, MGF.titulo, tam, cw*0.8, MGT.tinta, 3);
    const ch = Math.max(b.h + tam*1.1, tam*2.3);
    [[sombra, sw*1.6, MGT.tinta, 'none'], [caja, 0, MGT.papel, borde]].forEach(([e, d, fill, st]) => {
      e.setAttribute('x', -cw/2 + d); e.setAttribute('y', -ch/2 + d); e.setAttribute('width', cw); e.setAttribute('height', ch);
      e.setAttribute('rx', tam*0.35); e.setAttribute('fill', fill);
      if (st !== 'none'){ e.setAttribute('stroke', st); e.setAttribute('stroke-width', sw); }
    });
    return {t, b, ch, cx, cy};
  };
  const A = tarjeta(p.a, MGT.tinta, v ? 0 : -p.sep, v ? -p.sep : 0);
  const B = tarjeta(p.b, MGT.acento2, v ? 0 : p.sep, v ? p.sep : 0);
  const tacha = mk('path', {d: `M${-cw*0.4},${tam*0.1} C${-cw*0.1},${-tam*0.2} ${cw*0.15},${tam*0.25} ${cw*0.4},${-tam*0.15}`,
    fill: 'none', stroke: MGT.acento, 'stroke-width': tam*0.18, 'stroke-linecap': 'round', opacity: 0}, A.t);
  const insignia = (cual, T0) => { const e = mk('g', {}, cual.t); icono(T0, e).setAttribute('transform', `scale(${(tam*0.012).toFixed(4)})`); return e; };
  const xA = insignia(A, 'equis'), okB = insignia(B, 'check');
  const flecha = mk('path', {d: v ? `M0,${-p.sep + A.ch/2 + tam*0.3} V${p.sep - B.ch/2 - tam*0.45} M${-tam*0.35},${p.sep - B.ch/2 - tam*0.8} L0,${p.sep - B.ch/2 - tam*0.4} L${tam*0.35},${p.sep - B.ch/2 - tam*0.8}`
    : `M${-p.sep + cw/2 + tam*0.3},0 H${p.sep - cw/2 - tam*0.45} M${p.sep - cw/2 - tam*0.8},${-tam*0.35} L${p.sep - cw/2 - tam*0.4},0 L${p.sep - cw/2 - tam*0.8},${tam*0.35}`,
    fill: 'none', stroke: MGT.tinta, 'stroke-width': sw, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: 0}, g);
  return function(T){
    const sa = T - p.a_en, ra = resorte(sa, 13, .42);
    const sx = T - (p.b_en - 0.2), ux = eOut(sx/0.4);
    // A cae; cuando llega la verdad se TACHA, encoge y se apaga (y se queda)
    A.t.setAttribute('opacity', sa > 0 ? 1 : 0);
    A.t.setAttribute('transform', `translate(${A.cx},${(A.cy - (1 - ra)*tam*3).toFixed(1)}) scale(${(1 - 0.1*ux).toFixed(3)}) rotate(${(-2.5*ux).toFixed(2)})`);
    A.b.g.setAttribute('opacity', (1 - 0.5*ux).toFixed(3));
    dibujar(tacha, ux);
    const rx = resorte(sx - 0.25, 15, .4);
    xA.setAttribute('opacity', sx > 0.25 ? 1 : 0);
    xA.setAttribute('transform', `translate(${(cw/2 - tam*0.2).toFixed(1)},${(-A.ch/2 + tam*0.2).toFixed(1)}) scale(${Math.max(0.001, rx).toFixed(3)})`);
    const sb = T - p.b_en, rb = resorte(sb, 13, .42);
    B.t.setAttribute('opacity', sb > 0 ? 1 : 0);
    const late = sb > 0.8 ? 1 + 0.025*Math.sin((sb - 0.8)*5) : 1;
    B.t.setAttribute('transform', `translate(${B.cx},${(B.cy + (1 - rb)*tam*3).toFixed(1)}) scale(${(Math.max(0.001, rb)*late).toFixed(3)})`);
    const rk = resorte(sb - 0.3, 15, .4);
    okB.setAttribute('opacity', sb > 0.3 ? 1 : 0);
    okB.setAttribute('transform', `translate(${(cw/2 - tam*0.2).toFixed(1)},${(-B.ch/2 + tam*0.2).toFixed(1)}) scale(${Math.max(0.001, rk).toFixed(3)})`);
    dibujar(flecha, eOut((sb - 0.05)/0.35));
  };
}

function hazLista(p, g){
  const tam = p.tam, n = p.items.length, w = p.w, alto = tam*1.6, sw = Math.max(4, tam*0.08);
  const filas = p.items.map((it, k) => {
    const e = mk('g', {}, g);
    mk('rect', {x: -w/2 + sw*1.4, y: -alto/2 + sw*1.4, width: w, height: alto, rx: alto/2, fill: MGT.tinta}, e);
    mk('rect', {x: -w/2, y: -alto/2, width: w, height: alto, rx: alto/2, fill: MGT.papel, stroke: MGT.tinta, 'stroke-width': sw}, e);
    mk('circle', {cx: -w/2 + alto/2, r: alto*0.38, fill: k % 2 ? MGT.acento2 : MGT.acento}, e);
    txt(e, String(k + 1), {'font-family': MGF.titulo, 'font-size': tam*0.9, fill: '#fff', 'text-anchor': 'middle', x: -w/2 + alto/2, y: tam*0.32});
    const t = txt(e, it.t, {'font-family': MGF.titulo, 'font-size': tam, fill: MGT.tinta, x: -w/2 + alto*1.05, y: tam*0.35});
    const maxw = w - alto*1.4, aw = ancho(t);
    if (aw > maxw) t.setAttribute('font-size', (tam*maxw/aw).toFixed(1));
    return {e, it, y: (k - (n - 1)/2)*p.paso, dir: k % 2 ? -1 : 1};
  });
  return function(T){
    filas.forEach((f, k) => {
      const s = T - f.it.en, r = resorte(s, 13, .45);
      // la que entra empuja: las de antes se apagan un poco (encadenado)
      const siguiente = filas[k + 1], apaga = siguiente ? eOut((T - siguiente.it.en)/0.4) : 0;
      f.e.setAttribute('opacity', s > 0 ? (1 - 0.3*apaga).toFixed(3) : 0);
      const estira = 1 + cl((1 - r)*0.25, -0.06, 0.25);
      f.e.setAttribute('transform', `translate(${((1 - r)*f.dir*MG.W).toFixed(1)},${f.y.toFixed(1)}) scale(${estira.toFixed(3)},${(1/estira).toFixed(3)}) scale(${(1 - 0.06*apaga).toFixed(3)})`);
    });
  };
}

const CONSTRUCTORES = {versiculo: hazVersiculo, reloj: hazReloj, mapa: hazMapa, linea: hazLinea,
  lamina: hazLamina, texto: hazTexto, icono: hazIcono, contador: hazContador,
  comparacion: hazComparacion, lista: hazLista};

// ---------------------------------------------------------------- el mundo
function mgConstruir(){
  const mundo = document.getElementById('mgmundo');
  while (mundo.firstChild) mundo.removeChild(mundo.firstChild);
  // el suelo del mundo: puntos que se mueven con la camara (asi se nota el viaje)
  const defs = mk('defs', {}, mundo);
  const pat = mk('pattern', {id: 'mgpuntos', width: 64, height: 64, patternUnits: 'userSpaceOnUse'}, defs);
  mk('circle', {cx: 32, cy: 32, r: 3, fill: MGT.puntos}, pat);
  mk('rect', {x: -MG.W*4, y: -MG.H*3, width: MG.W*(4 + 2*Math.max(4, MG.plano + 4)), height: MG.H*6, fill: 'url(#mgpuntos)', opacity: .7}, mundo);
  MGPIEZAS = [];
  MG.caminos.forEach(c => {
    const g = mk('g', {}, mundo), pts = puntosRuta(c.de, c.a, 22), dots = [];
    pts.forEach((q, k) => dots.push(mk('circle', {cx: q[0].toFixed(1), cy: q[1].toFixed(1), r: 0, fill: MGT.suave}, g)));
    const fl = mk('path', {d: 'M-14,-18 L14,0 L-14,18z', fill: MGT.suave}, g);
    MGPIEZAS.push({camino: true, c, dots, fl, pts});
  });
  MG.piezas.forEach(p => {
    const fuera = mk('g', {}, mundo), dentro = mk('g', {}, fuera);
    let upd = () => {};
    try { upd = CONSTRUCTORES[p.tipo](p, dentro) || upd; } catch (e) { console.log('motion ' + p.tipo + ': ' + e); }
    MGPIEZAS.push({p, fuera, upd});
  });
  (MG.puentes || []).forEach(pu => {
    const g = mk('g', {}, mundo);
    const ring = mk('circle', {fill: 'none', stroke: MGT.oro, opacity: 0}, g);
    const ic = mk('g', {}, g);
    icono(pu.icono, ic);
    MGPIEZAS.push({puente: true, pu, g, ic, ring});
  });
  MGHECHO = true;
  MGCONLETRAS = !!window.LETRAS_OK;
}

function mgCamara(T){
  const tramos = MG.cam;
  let tr = tramos[0];
  for (const x of tramos){ if (T >= x.t0) tr = x; }
  const u = cl((T - tr.t0) / Math.max(0.001, tr.t1 - tr.t0), 0, 1);
  let x, y, z;
  if (tr.tipo === 'viaje'){
    const e = eIO(u);
    x = lerp(tr.de[0], tr.a[0], e); y = lerp(tr.de[1], tr.a[1], e);
    // se aleja a mitad de viaje: se ve de donde viene y a donde va
    z = lerp(tr.de[2], tr.a[2], e) * (1 - 0.3*Math.sin(Math.PI*e));
  } else if (tr.tipo === 'inicio'){
    const e = eOut(u);
    x = lerp(tr.de[0], tr.a[0], e); y = lerp(tr.de[1], tr.a[1], e); z = lerp(tr.de[2], tr.a[2], e);
  } else {
    const e = u*u*(3 - 2*u);
    x = lerp(tr.de[0], tr.a[0], e); y = lerp(tr.de[1], tr.a[1], e); z = lerp(tr.de[2], tr.a[2], e);
  }
  return [x, y, z];
}

function mgPieza(q, T){
  const p = q.p, s = T - p.en;
  if (s < 0){ q.fuera.setAttribute('display', 'none'); return; }
  q.fuera.removeAttribute('display');
  let x = p.x, y = p.y, esc = 1, rot = p.rot || 0, op = 1;
  // LUEGO: se transforma (con anticipacion y rebote) y se queda asi
  (p.luego || []).forEach(l => {
    const e = eBack((T - l.en) / (l.dur || 0.7));
    if (T <= l.en) return;
    if (l.x !== undefined) x = lerp(x, l.x, e);
    if (l.y !== undefined) y = lerp(y, l.y, e);
    if (l.escala !== undefined) esc = lerp(esc, l.escala, e);
    if (l.rot !== undefined) rot = lerp(rot, l.rot, e);
    if (l.opacidad !== undefined) op = lerp(op, l.opacidad, cl((T - l.en)/0.4, 0, 1));
  });
  // ENTRADA con resorte; estira en la direccion del movimiento y se aplasta
  // al llegar (squash & stretch)
  const r = resorte(s, p.tipo === 'lamina' ? 11 : 13, p.tipo === 'lamina' ? .5 : .42);
  const v = (resorte(s + 0.016, 13, .42) - resorte(s, 13, .42)) / 0.016;
  let ox = 0, oy = 0, sx = 1, sy = 1;
  const d = p.entra || 'abajo', dist = MG.H*0.75;
  if (d === 'pop'){
    esc *= Math.max(0.001, r);
  } else if (d !== 'nada'){
    const k = 1 - r;
    if (d === 'abajo') oy = k*dist;
    if (d === 'arriba') oy = -k*dist;
    if (d === 'izquierda') ox = -k*MG.W;
    if (d === 'derecha') ox = k*MG.W;
    const estira = cl(Math.abs(v)*0.035, 0, 0.22) - cl((r - 1)*1.4, -0.15, 0.18);
    if (d === 'abajo' || d === 'arriba'){ sy = 1 + estira; sx = 1/sy; }
    else { sx = 1 + estira; sy = 1/sx; }
  }
  // ENCADENADO: cuando otra pieza aterriza cerca, esta reacciona (se mece)
  let reac = 0;
  (MG.impactos || []).forEach(im => {
    if (im.id === p.id || p.fondo || T < p.en + 0.45) return;
    const si = T - im.t;
    if (si > 0 && si < 1.2 && Math.abs(im.x - p.x) < MG.W*0.9) reac += im.f*Math.exp(-si*6)*Math.sin(si*17);
  });
  rot += 2.2*reac; esc *= 1 + 0.012*reac;
  op *= cl(s/0.12, 0, 1);
  if (p.sale !== undefined && T > p.sale){
    const e = eIO((T - p.sale)/0.5);
    op *= 1 - e; esc *= 1 - 0.4*e;
  }
  q.fuera.setAttribute('opacity', op.toFixed(3));
  q.fuera.setAttribute('transform',
    `translate(${(x + ox).toFixed(1)},${(y + oy).toFixed(1)}) rotate(${rot.toFixed(2)}) scale(${(esc*sx).toFixed(4)},${(esc*sy).toFixed(4)})`);
  q.upd(T);
}

// LA CAMARA SIGUE LO IMPORTANTE: dentro de cada plano va de foco en foco
// (la chincheta que se nombra, el año que se dice, la porcion del reloj...) y
// vuelve a su sitio antes de acabar el plano, para que el viaje al siguiente
// empiece donde toca (sin corte)
function mgFoco(T, base){
  const v = (MG.ventanas || []).find(w => T >= w.a && T < w.b);
  if (!v || !v.focos.length) return base;
  const est = [{t: v.a, f: null}].concat(v.focos.map(f => ({t: f.t, f})), [{t: v.b - 0.8, f: null}]);
  let k = 0;
  for (let j = 0; j < est.length; j++) if (T >= est[j].t) k = j;
  if (k === 0) return base;
  const val = e => e.f ? [e.f.x, e.f.y, e.f.z] : base;
  const dur = Math.max(0.2, Math.min(0.75, est[k].t - est[k - 1].t));
  const a = val(est[k - 1]), b = val(est[k]), u = eIO((T - est[k].t)/dur);
  return [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
}
// el golpecito de camara cuando algo aterriza
function mgGolpe(T){
  let v = 0;
  (MG.impactos || []).forEach(im => { const s = T - im.t; if (s > 0 && s < 0.9) v += im.f*Math.exp(-s*7)*Math.sin(s*20); });
  return v;
}
// EL OBJETO PUENTE: sale de la pieza de este plano, vuela con la camara y se
// transforma (estalla en un anillo) en la pieza del plano siguiente
function mgPuente(q, T){
  const pu = q.pu, tam = pu.tam;
  if (T < pu.sale || T > pu.llega + 0.6){ q.g.setAttribute('display', 'none'); return; }
  q.g.removeAttribute('display');
  let x = pu.de[0], y = pu.de[1], esc = 1, rot = 0, sx = 1, sy = 1, op = 1, anillo = 0;
  if (T < pu.vuela){
    const s = T - pu.sale, r = resorte(s, 14, .4);
    esc = Math.max(0.001, r);
    y -= tam*0.6*cl(r, 0, 1.2);
    // anticipacion: se agacha justo antes de saltar
    const ag = cl((T - (pu.vuela - 0.15))/0.15, 0, 1);
    sy = 1 - 0.22*ag; sx = 1 + 0.18*ag;
  } else if (T < pu.llega){
    const u = eIO((T - pu.vuela)/Math.max(0.1, pu.llega - pu.vuela));
    const a = [pu.de[0], pu.de[1] - tam*0.6], b = pu.a;
    const cx = (a[0] + b[0])/2, cy = Math.min(a[1], b[1]) - MG.H*0.22;
    x = (1-u)*(1-u)*a[0] + 2*(1-u)*u*cx + u*u*b[0];
    y = (1-u)*(1-u)*a[1] + 2*(1-u)*u*cy + u*u*b[1];
    rot = 360*eIO(u);
    const vel = Math.sin(Math.PI*u);
    sx = 1 + 0.25*vel; sy = 1/sx;
  } else {
    const s = T - pu.llega;
    x = pu.a[0]; y = pu.a[1];
    esc = 1 + 3.5*eOut(s/0.4); op = 1 - eOut(s/0.35); anillo = s;
  }
  q.ic.setAttribute('transform', `translate(${x.toFixed(1)},${y.toFixed(1)}) rotate(${rot.toFixed(1)}) scale(${(esc*sx*tam/100).toFixed(4)},${(esc*sy*tam/100).toFixed(4)})`);
  q.ic.setAttribute('opacity', op.toFixed(3));
  if (anillo > 0){
    q.ring.setAttribute('cx', pu.a[0]); q.ring.setAttribute('cy', pu.a[1]);
    q.ring.setAttribute('r', (tam*(0.5 + 3.2*eOut(anillo/0.55))).toFixed(1));
    q.ring.setAttribute('stroke-width', (tam*0.14*(1 - eOut(anillo/0.55))).toFixed(2));
    q.ring.setAttribute('opacity', (1 - eOut(anillo/0.55)).toFixed(3));
  } else q.ring.setAttribute('opacity', 0);
}

function motionPintar(t){
  if (!MGHECHO || (!MGCONLETRAS && window.LETRAS_OK)) mgConstruir();
  const T = MG.t0 + t;
  let [cx, cy, z] = mgFoco(T, mgCamara(T));
  z *= 1 + 0.014*mgGolpe(T);
  document.getElementById('mgmundo').setAttribute('transform',
    `translate(${MG.W/2},${MG.H/2}) scale(${z.toFixed(5)}) translate(${(-cx).toFixed(2)},${(-cy).toFixed(2)})`);
  MGPIEZAS.forEach(q => {
    if (q.camino){
      const u = eIO((T - q.c.t0) / Math.max(0.2, q.c.t1 - q.c.t0));
      q.dots.forEach((d, k) => {
        const s = u*q.dots.length - k;
        d.setAttribute('r', (cl(s, 0, 1)*7).toFixed(2));
      });
      const fin = q.pts[q.pts.length - 1], ant = q.pts[q.pts.length - 2];
      const a = Math.atan2(fin[1] - ant[1], fin[0] - ant[0])*180/Math.PI;
      q.fl.setAttribute('transform', `translate(${fin[0].toFixed(1)},${fin[1].toFixed(1)}) rotate(${a.toFixed(1)}) scale(${cl((u - 0.9)*10, 0, 1).toFixed(3)})`);
      return;
    }
    if (q.puente){ mgPuente(q, T); return; }
    mgPieza(q, T);
  });
}
"""

# la segunda parte (muñecos planos, barras, antes/despues, arbol, flecha,
# circulo e iconos de metafora) se suma al final: CONSTRUCTORES ya existe
MOTION_JS += motion_mas.MOTION_MAS_JS
# P3: los escenarios con luz, sombras y capas (y sus efectos Lottie)
MOTION_JS += escenarios.ESCENARIO_JS


def js_de(conf):
    """El JS de motion para una pagina: con lottie-web delante solo si algun
    escenario de la pagina lleva fuego, humo o luz."""
    if not conf:
        return ""
    return (escenarios.lottie_js() + "\n" if escenarios.con_efectos(conf) else "") + MOTION_JS


def tipos_auto(escenas, ancho, alto, laminas_px=None, hoy=None):
    """{sid: "mapa" | "lamina, icono"...}: lo que pondria lo automatico en cada
    plano (para contarselo a Claude al pedirle el storyboard)."""
    mapeados, salida = set(), {}
    for e in escenas:
        piezas = storyboard(e, ancho, alto, (laminas_px or {}).get(e.get("id")),
                            hoy=hoy, mapeados=mapeados, munecos=False)
        salida[e.get("id")] = ", ".join(dict.fromkeys(p["tipo"] for p in piezas)) or "nada"
    return salida


def resumen_opciones(p):
    """Para el registro: que se pidio del motion."""
    o = _opciones(p)
    return (f"tema {tema_de(p)}, storyboard "
            f"{'de Claude' if o.get('storyboard') == 'claude' else 'automatico'}, "
            f"muñecos {'no' if o.get('munecos') is False else 'si'}, "
            f"sonidos {'no' if o.get('sonidos') is False else 'si'}, "
            f"escenarios {'no' if o.get('escenarios') is False else 'si'}")
