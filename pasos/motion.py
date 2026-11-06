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
    import fidelidad
except ImportError:  # importado como paquete (pasos.motion)
    from . import fidelidad

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
TIPOS = ("versiculo", "reloj", "mapa", "linea", "lamina", "texto", "icono")
ENTRADAS = ("abajo", "arriba", "izquierda", "derecha", "pop")
ICONOS = ("cruz", "corazon", "biblia", "moneda", "celular", "corona", "paloma",
          "casa", "vela", "estrella", "pan", "cadena", "pergamino", "reloj")

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
    ("pergamino", ("profec", "ley ", "carta", "rollo", "pergamino")),
    ("reloj", ("tiempo", "hora", "pronto", "tarde")),
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
    m = LIBRO_RE.search(voz.texto)
    ref, i_ref, fin_ref = None, None, None
    if m:
        orden, libro, cap, v1, v2 = m.groups()
        nombre = dict(LIBROS)[libro]
        if _n(cap) and _n(v1):
            ref = f"{nombre} {_n(cap)}:{_n(v1)}"
            if v2 and _n(v2):
                ref += f"-{_n(v2)}"
            if orden:
                ref = f"{_n(orden)} {ref}"
            i_ref = voz.indice_de(m.start())
            fin_ref = voz.indice_de(m.end() - 1)
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


def storyboard(escena, ancho, alto, lamina=None, laminas=True, hoy=None,
               mapeados=None):
    """Las piezas de UN plano en coordenadas del cuadro (px, origen arriba a la
    izquierda) y tiempos del video. -> [pieza]"""
    voz = Voz(escena)
    W, H = float(ancho), float(alto)
    vertical = H > W
    cx = W / 2
    cy = H * (0.37 if vertical else 0.42)     # el subtitulo vive abajo
    propio = escena.get("motion")
    if isinstance(propio, list):
        return [p for p in (_normalizar(x, voz, W, H) for x in propio) if p]
    piezas = []
    if propio is not False:
        cita = cita_de(voz)
        lugares = lugares_de(voz)
        fechas = fechas_de(voz, hoy=hoy)
        reloj = reloj_de(voz)
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
    if not piezas:
        iconos = iconos_de(voz)
        if lamina and laminas:
            lw = W * (0.8 if vertical else 0.56)
            lh = lw * lamina["alto"] / lamina["ancho"]
            if lh > H * (0.56 if vertical else 0.66):
                lh = H * (0.56 if vertical else 0.66)
                lw = lh * lamina["ancho"] / lamina["alto"]
            gira = -1.6 if _par(escena) else 1.4
            piezas.append({"tipo": "lamina", "href": lamina["href"], "x": cx, "y": cy,
                           "w": round(lw, 1), "h": round(lh, 1), "rot": gira,
                           "en": round(voz.t_in + 0.05, 3), "entra": "abajo",
                           "fin": round(voz.t_out, 3)})
            sitios = ((cx + lw * 0.46, cy - lh * 0.46), (cx - lw * 0.46, cy + lh * 0.44),
                      (cx + lw * 0.44, cy + lh * 0.46))
            tam = W * (0.15 if vertical else 0.085)
        else:
            sitios = ((cx, cy), (cx - W * 0.27, cy + H * 0.08), (cx + W * 0.27, cy + H * 0.08))
            tam = W * (0.3 if vertical else 0.16)
            if not iconos:
                clave = _palabra_fuerte(voz)
                if clave:
                    piezas.append({"tipo": "texto", "x": cx, "y": cy, "w": W * 0.84,
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
    return piezas


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


def _normalizar(pieza, voz, W, H):
    """Una pieza escrita a mano (fracciones del cuadro, `en` en palabras)."""
    if not isinstance(pieza, dict) or pieza.get("tipo") not in TIPOS:
        return None
    p = dict(pieza)
    for k, total in (("x", W), ("y", H), ("w", W), ("h", H)):
        if isinstance(p.get(k), (int, float)) and 0 <= p[k] <= 1.5:
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


def preparar(escenas, p, laminas_px, ancho, alto, hoy=None):
    """La configuracion de motion de CADA plano. -> {sid: conf}

    `laminas_px`: {sid: {"href", "ancho", "alto"}} con la imagen de cada plano
    (o nada). Cada conf lleva su plano y los dos anteriores (lo que se puede
    ver durante el viaje) con coordenadas del MUNDO.
    """
    tema = tema_de(p)
    if not tema:
        return {}
    opciones = _opciones(p)
    laminas = opciones.get("laminas", True) is not False
    W, H = float(ancho), float(alto)
    puntos = paradas(len(escenas), W, H)
    tramos = camara(escenas, puntos)
    por_plano, mapeados = [], set()
    for i, e in enumerate(escenas):
        ox, oy = puntos[i][0] - W / 2, puntos[i][1] - H / 2
        piezas = storyboard(e, W, H, (laminas_px or {}).get(e.get("id")),
                            laminas=laminas, hoy=hoy, mapeados=mapeados)
        for pz in piezas:
            pz["x"] = round(float(pz.get("x", W / 2)) + ox, 1)
            pz["y"] = round(float(pz.get("y", H / 2)) + oy, 1)
            for paso in pz.get("luego") or []:
                if "x" in paso:
                    paso["x"] = round(float(paso["x"]) + ox, 1)
                if "y" in paso:
                    paso["y"] = round(float(paso["y"]) + oy, 1)
        por_plano.append(piezas)
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
        confs[e.get("id")] = {
            "tema": TEMAS[tema], "nombre_tema": tema, "fuentes": FUENTES,
            "W": W, "H": H, "t0": round(float(e["t_in"]), 3),
            "cam": tramos[2 * desde:2 * i + 2],
            "caminos": caminos[max(0, desde - 1):i],
            "piezas": [pz for piezas in por_plano[desde:i + 1] for pz in piezas],
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
  const palabras = [];
  lineas.forEach(l => {
    let x = -l.w / 2;
    y += lh;
    l.ps.forEach(({i, a}) => {
      const pw = p.palabras[i];
      const color = pw.c === 1 ? MGT.acento : (pw.c === 2 ? MGT.acento2 : MGT.tinta);
      const e = txt(g, pw.t, {'font-family': MGF.verso, 'font-size': tam, fill: color});
      palabras.push({e, x, y: y - lh*0.22, en: pw.en, c: pw.c, a});
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
      // las que aun no se dicen se ven tenues: se lee la forma del versiculo
      // y cada palabra se entinta, salta y se asienta cuando suena
      const r = s <= 0 ? 0 : resorte(s, 16, .5);
      const op = s <= 0 ? .16 : lerp(.16, 1, cl(s/0.18, 0, 1));
      const dy = s <= 0 ? tam*0.12 : (1 - r) * tam*0.35;
      const esc = s <= 0 ? 1 : 1 + (w.c ? .22 : .1) * Math.exp(-s*6) * Math.sin(Math.min(s*14, Math.PI));
      w.e.setAttribute('opacity', op.toFixed(3));
      w.e.setAttribute('transform', `translate(${(w.x + w.a/2).toFixed(1)},${(w.y + dy).toFixed(1)}) scale(${esc.toFixed(3)}) translate(${(-w.a/2).toFixed(1)},0)`);
    });
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
  if (titulo) encaja(titulo, MG.W*0.88);
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
    if (titulo) titulo.setAttribute('opacity', cl((T - p.en - 0.3)/0.3, 0, 1));
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
  p.palabras.forEach(pw => {
    const e = txt(g, pw.t, {'font-family': MGF.titulo, 'font-size': tam, fill: pw.c ? MGT.acento : MGT.tinta,
      stroke: MGT.papel, 'stroke-width': tam*0.06, 'paint-order': 'stroke', 'stroke-linejoin': 'round'});
    const a = ancho(e);
    partes.push({e, x, a, en: pw.en});
    x += a + esp;
  });
  const total = x - esp;
  if (total > p.w) g.setAttribute('transform', `scale(${(p.w/total).toFixed(4)})`);
  return function(T){
    partes.forEach(q => {
      const s = T - q.en, r = resorte(s, 15, .38);
      q.e.setAttribute('opacity', s > 0 ? 1 : 0);
      q.e.setAttribute('transform', `translate(${(q.x - total/2 + q.a/2).toFixed(1)},${(tam*0.35 + (1 - r)*tam*0.8).toFixed(1)}) scale(${Math.max(0.001, 0.5 + 0.5*r).toFixed(3)}) translate(${(-q.a/2).toFixed(1)},0)`);
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

const CONSTRUCTORES = {versiculo: hazVersiculo, reloj: hazReloj, mapa: hazMapa, linea: hazLinea,
  lamina: hazLamina, texto: hazTexto, icono: hazIcono};

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
  } else {
    const k = 1 - r;
    if (d === 'abajo') oy = k*dist;
    if (d === 'arriba') oy = -k*dist;
    if (d === 'izquierda') ox = -k*MG.W;
    if (d === 'derecha') ox = k*MG.W;
    const estira = cl(Math.abs(v)*0.035, 0, 0.22) - cl((r - 1)*1.4, -0.15, 0.18);
    if (d === 'abajo' || d === 'arriba'){ sy = 1 + estira; sx = 1/sy; }
    else { sx = 1 + estira; sy = 1/sx; }
  }
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

function motionPintar(t){
  if (!MGHECHO || (!MGCONLETRAS && window.LETRAS_OK)) mgConstruir();
  const T = MG.t0 + t;
  const [cx, cy, z] = mgCamara(T);
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
    mgPieza(q, T);
  });
}
"""
