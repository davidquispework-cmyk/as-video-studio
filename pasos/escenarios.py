"""Biblioteca de ESCENARIOS vectoriales (P3 del plan «NIVEL PROFESIONAL»).

Un escenario es el sitio donde pasa el plano, dibujado por código (SVG), con
LUZ (cielo en degradado, sol o luna con halo, haces de luz, color de la hora),
SOMBRAS (cada objeto proyecta la suya hacia el lado contrario del sol; cada
edificio tiene cara iluminada y cara en sombra) y CAPAS (cielo, nubes, montes
lejanos con neblina, medio, suelo, objetos, primer plano) que se mueven a su
ritmo: las nubes avanzan, las olas van y vienen, la barca se mece, las palmeras
se balancean, las estrellas titilan.

Escenarios: mar, desierto, ciudad (amurallada), torre, templo, trono (sala del
palacio), monte y campo. Horas: dia, atardecer y noche. Y tres EFECTOS hechos
con Lottie (lottie-web, MIT, `motores/js/lottie_light.min.js`, dentro del repo):
fuego, humo y luz (destello de gloria). Las animaciones Lottie las genera este
módulo (`lottie_de`): son propias, sin licencias de terceros.

Cómo entra en el vídeo (pasos/motion.py, pieza `escenario`):
- SOLO, en los planos con motion graphics que no tienen lámina (imagen) y no
  explican otra cosa (mapa, versículo...): si la narración nombra el sitio
  (`escenario_de`: «mar», «barca» → mar; «muralla» → ciudad; «rey» → trono...),
  el escenario va detrás de los muñecos.
- A MANO en plan.json: escena `"escenario": "mar"` o `{"nombre": "templo",
  "hora": "noche", "efectos": ["fuego", "humo"]}`; `"escenario": false` lo
  quita en ese plano. En un storyboard: `{"tipo": "escenario", "nombre": ...}`.
- Param del render `motion: {"escenarios": false}` lo apaga en todo el vídeo.
No es un param por defecto ni toca firmas: basta «Regenerar Vídeo».
"""
import hashlib
import json
import math
import os
import random

try:
    import fidelidad
except ImportError:  # importado como paquete (pasos.escenarios)
    from . import fidelidad

NOMBRES = ("mar", "desierto", "ciudad", "torre", "templo", "trono", "monte", "campo")
HORAS = ("dia", "atardecer", "noche")
EFECTOS = ("fuego", "humo", "luz")
LOTTIE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "motores", "js", "lottie_light.min.js")

# ------------------------------------------------------------ deteccion
# palabra plegada (o principio de palabra con «*») -> escenario. El orden
# manda: «el altar del templo de la ciudad» es templo.
_PALABRAS = (
    ("templo", ("templo", "santuario", "altar", "altares", "sacerdote", "sacerdotes",
                "tabernaculo", "holocausto", "lugar santisimo")),
    ("torre", ("torre", "babel", "zigurat")),
    ("trono", ("trono", "palacio", "rey", "reyes", "reina", "faraon", "corona",
               "coronado", "corte", "salomon")),
    ("mar", ("mar", "barca", "barco", "barcas", "nave", "pescador", "pescadores",
             "pescar", "redes", "olas", "tormenta", "tempestad", "jonas", "lago",
             "tiberiades", "orilla")),
    ("monte", ("monte", "montaña", "montañas", "cima", "sinai", "horeb", "carmelo",
               "colina", "golgota", "calvario")),
    ("ciudad", ("ciudad", "muralla", "murallas", "muros", "jerico", "jerusalen",
                "nínive", "ninive", "babilonia", "puerta de la ciudad")),
    ("desierto", ("desierto", "arena", "dunas", "camello", "camellos", "oasis",
                  "peregrinaron", "errantes", "tiendas", "beduino")),
    ("campo", ("campo", "campos", "pastor", "pastores", "ovejas", "rebaño", "siembra",
               "sembrador", "sembro", "trigo", "cosecha", "huerto", "jardin", "eden",
               "pozo", "vid", "viña")),
)
_HORA = (
    ("noche", ("noche", "tinieblas", "oscuridad", "oscuro", "oscura", "estrellas",
               "luna", "medianoche", "nocturno")),
    ("atardecer", ("atardecer", "tarde", "ocaso", "anochecer", "anochecia",
                   "amanecer", "alba", "madrugada", "aurora", "crepusculo")),
)
_EFECTO = (
    ("fuego", ("fuego", "llamas", "llama", "hoguera", "zarza", "ardiendo", "ardia",
               "ardiente", "quemo", "quemaron", "horno", "antorcha", "antorchas",
               "brasas", "fogata")),
    ("humo", ("humo", "incienso", "holocausto", "humeante", "ceniza", "cenizas")),
    ("luz", ("luz", "gloria", "resplandor", "resplandecio", "resplandeciente", "brillo",
             "brillo", "ilumino", "angel", "angeles", "milagro", "aparecio")),
)


def _busca(texto_plegado, palabras):
    pl = " " + texto_plegado + " "
    return any((" " + fidelidad.plegar(p) + " ") in pl for p in palabras)


def escenario_de(texto):
    """Lo que la narración dice del sitio. -> {"nombre", "hora", "efectos"} o None."""
    t = fidelidad.plegar(texto)
    if not t:
        return None
    nombre = next((n for n, ps in _PALABRAS if _busca(t, ps)), None)
    if not nombre:
        return None
    return dict(_luz_de(t), nombre=nombre)


def _luz_de(t):
    """La hora y los efectos que nombra un texto ya plegado."""
    return {"hora": next((h for h, ps in _HORA if _busca(t, ps)), "dia"),
            "efectos": [e for e, ps in _EFECTO if _busca(t, ps)]}


def de_la_escena(escena):
    """Lo de a mano manda (`escena["escenario"]`); si no, lo que dice la voz.
    -> dict, None (nada que poner) o False (quitado a mano)."""
    propio = escena.get("escenario")
    if propio is False:
        return False
    if isinstance(propio, str) and propio in NOMBRES:
        propio = {"nombre": propio}
    if isinstance(propio, dict) and propio.get("nombre") in NOMBRES:
        auto = _luz_de(fidelidad.plegar(escena.get("narracion") or ""))
        return {"nombre": propio["nombre"],
                "hora": propio.get("hora") if propio.get("hora") in HORAS
                else auto.get("hora", "dia"),
                "efectos": [e for e in (propio.get("efectos") if "efectos" in propio
                                        else auto.get("efectos", [])) if e in EFECTOS]}
    return escenario_de(escena.get("narracion") or "")


# ------------------------------------------------------------ color
def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mezcla(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ra, rb))


def osc(c, k=0.25):
    return mezcla(c, "#000000", k)


def cla(c, k=0.25):
    return mezcla(c, "#ffffff", k)


# luz de cada hora: cielo (arriba, medio, horizonte), astro, halo, sombra y
# el tinte que «colorea» todo el escenario (gradacion de color)
LUCES = {
    "dia": {"cielo": ("#3D8FE0", "#7DC0F2", "#D8F0FF"), "astro": "#FFF7CF",
            "halo": "#FFF2A8", "sombra": "#1B2440", "s_op": 0.24, "tinte": "#FFE9B0",
            "t_op": 0.06, "lado": 1, "alto": 0.30, "neblina": "#E6F4FF",
            "nube": "#FFFFFF", "nube_s": "#BCD3EA", "rayos": 0.10},
    "atardecer": {"cielo": ("#3A2A6B", "#C75B7A", "#FFB86B"), "astro": "#FFE08A",
                  "halo": "#FF9E5E", "sombra": "#2A1030", "s_op": 0.30,
                  "tinte": "#FF8A3D", "t_op": 0.16, "lado": -1, "alto": 0.08,
                  "neblina": "#FFC690", "nube": "#FFC2A0", "nube_s": "#9A5A7E",
                  "rayos": 0.14},
    "noche": {"cielo": ("#05071C", "#121A4A", "#2C3878"), "astro": "#F4F1DC",
              "halo": "#9FB3FF", "sombra": "#000010", "s_op": 0.30, "tinte": "#1E2C7A",
              "t_op": 0.34, "lado": 1, "alto": 0.34, "neblina": "#34417F",
              "nube": "#4A5590", "nube_s": "#1A2050", "rayos": 0.0},
}

# los colores propios de cada sitio (de dia: la hora los tiñe despues)
SUELOS = {
    "mar": ("#E8C98E", "#C99A5B"), "desierto": ("#F2C877", "#C98B45"),
    "ciudad": ("#D9B27A", "#A87A48"), "torre": ("#D8B074", "#A07040"),
    "templo": ("#DDB98A", "#A9845A"), "trono": ("#6E2A2E", "#3E1418"),
    "monte": ("#9DB86A", "#6B8A45"), "campo": ("#9CCB62", "#5F9A3E"),
}
PIEDRA = "#E3CFA3"
ADOBE = "#D9A86C"
MADERA = "#8A5A34"
ORO = "#E8B23A"


# ------------------------------------------------------------ piezas sueltas
class Lienzo:
    """Acumula el SVG de un escenario: defs, capas y objetos."""

    def __init__(self, uid, w, h, luz, rnd):
        self.uid, self.w, self.h, self.luz, self.rnd = uid, w, h, luz, rnd
        self.defs, self.capas = [], []

    def id(self, nombre):
        return f"{self.uid}{nombre}"

    def add(self, s):
        self.capas.append(s)

    # una sombra en el suelo, alargada hacia el lado contrario a la luz
    def sombra(self, x, y, ancho, largo=1.0):
        L = self.luz
        lado = -L["lado"]
        estira = 1.0 + (0.8 if L["alto"] < 0.15 else 0.15) * largo
        return (f'<ellipse cx="{x + lado * ancho * 0.35 * (estira - 0.8):.1f}" cy="{y:.1f}" '
                f'rx="{ancho * 0.55 * estira:.1f}" ry="{ancho * 0.09:.1f}" '
                f'fill="{L["sombra"]}" opacity="{L["s_op"]:.2f}"/>')

    # un bloque con cara de frente, cara de lado (en sombra) y techo con luz
    def caja(self, x, y, w, h, color, fondo=None, techo=True, ventanas=0, puerta=False):
        L = self.luz
        d = fondo if fondo is not None else w * 0.18
        lado = L["lado"]
        frente = color
        sombra = osc(color, 0.32)
        arriba = cla(color, 0.25)
        partes = [self.sombra(x + w / 2, y, w * 1.1)]
        # la cara lateral va del lado contrario a la luz
        if lado > 0:
            sx = x
            lat = (f"M{sx:.1f},{y:.1f} L{sx - d:.1f},{y - d * 0.5:.1f} "
                   f"L{sx - d:.1f},{y - h - d * 0.5:.1f} L{sx:.1f},{y - h:.1f}Z")
            top = (f"M{x:.1f},{y - h:.1f} L{x - d:.1f},{y - h - d * 0.5:.1f} "
                   f"L{x + w - d:.1f},{y - h - d * 0.5:.1f} L{x + w:.1f},{y - h:.1f}Z")
        else:
            sx = x + w
            lat = (f"M{sx:.1f},{y:.1f} L{sx + d:.1f},{y - d * 0.5:.1f} "
                   f"L{sx + d:.1f},{y - h - d * 0.5:.1f} L{sx:.1f},{y - h:.1f}Z")
            top = (f"M{x:.1f},{y - h:.1f} L{x + d:.1f},{y - h - d * 0.5:.1f} "
                   f"L{x + w + d:.1f},{y - h - d * 0.5:.1f} L{x + w:.1f},{y - h:.1f}Z")
        partes.append(f'<path d="{lat}" fill="{sombra}"/>')
        if techo:
            partes.append(f'<path d="{top}" fill="{arriba}"/>')
        partes.append(f'<rect x="{x:.1f}" y="{y - h:.1f}" width="{w:.1f}" height="{h:.1f}" '
                      f'fill="{frente}"/>')
        # borde de luz (rim) en la arista que mira al sol
        bx = x + w if lado > 0 else x
        partes.append(f'<rect x="{bx - w * 0.03:.1f}" y="{y - h:.1f}" width="{w * 0.03:.1f}" '
                      f'height="{h:.1f}" fill="{cla(color, 0.45)}" opacity=".7"/>')
        noche = L is LUCES["noche"]
        for k in range(ventanas):
            vx = x + w * (0.2 + 0.6 * k / max(1, ventanas - 1)) if ventanas > 1 else x + w * 0.5
            vw, vh = w * 0.13, h * 0.18
            fill = "#FFC860" if noche else osc(color, 0.55)
            partes.append(f'<rect x="{vx - vw / 2:.1f}" y="{y - h * 0.72:.1f}" width="{vw:.1f}" '
                          f'height="{vh:.1f}" rx="{vw * 0.45:.1f}" fill="{fill}"/>')
            if noche:
                partes.append(f'<circle class="esc-halo" cx="{vx:.1f}" cy="{y - h * 0.63:.1f}" '
                              f'r="{vw * 1.6:.1f}" fill="#FFC860" opacity=".18"/>')
        if puerta:
            pw, ph = w * 0.26, h * 0.42
            px = x + w / 2 - pw / 2
            partes.append(f'<path d="M{px:.1f},{y:.1f} L{px:.1f},{y - ph + pw / 2:.1f} '
                          f'A{pw / 2:.1f},{pw / 2:.1f} 0 0 1 {px + pw:.1f},{y - ph + pw / 2:.1f} '
                          f'L{px + pw:.1f},{y:.1f}Z" fill="{osc(color, 0.6)}"/>')
        return "<g>" + "".join(partes) + "</g>"

    def palmera(self, x, y, s, mece=True):
        L = self.luz
        tronco = mezcla("#8C6239", L["sombra"], 0.15)
        hoja = "#3F8F4A" if L is not LUCES["noche"] else "#24503A"
        partes = [self.sombra(x, y, s * 0.9, 1.4)]
        # tronco curvo con anillos
        tx = x + s * 0.18
        partes.append(f'<path d="M{x - s * 0.05:.1f},{y:.1f} Q{x + s * 0.02:.1f},{y - s * 0.6:.1f} '
                      f'{tx:.1f},{y - s * 1.15:.1f} L{tx + s * 0.08:.1f},{y - s * 1.12:.1f} '
                      f'Q{x + s * 0.1:.1f},{y - s * 0.6:.1f} {x + s * 0.06:.1f},{y:.1f}Z" fill="{tronco}"/>')
        for k in range(6):
            yy = y - s * (0.15 + k * 0.17)
            partes.append(f'<path d="M{x - s * 0.02 + k * s * 0.025:.1f},{yy:.1f} l{s * 0.1:.1f},{-s * 0.02:.1f}" '
                          f'stroke="{osc(tronco, 0.35)}" stroke-width="{s * 0.02:.1f}"/>')
        cx, cy = tx + s * 0.04, y - s * 1.15
        hojas = []
        for k, ang in enumerate((-160, -120, -75, -30, 10, 50)):
            a = math.radians(ang)
            ex, ey = cx + math.cos(a) * s * 0.62, cy + math.sin(a) * s * 0.35 + s * 0.18
            mx, my = cx + math.cos(a) * s * 0.35, cy + math.sin(a) * s * 0.35 - s * 0.12
            col = cla(hoja, 0.2) if (math.cos(a) * L["lado"]) > 0 else osc(hoja, 0.15)
            hojas.append(f'<path d="M{cx:.1f},{cy:.1f} Q{mx:.1f},{my - s * 0.08:.1f} {ex:.1f},{ey:.1f} '
                         f'Q{mx:.1f},{my + s * 0.06:.1f} {cx:.1f},{cy:.1f}Z" fill="{col}"/>')
        clase = ' class="esc-mece"' if mece else ""
        partes.append(f'<g{clase} data-ox="{cx:.1f}" data-oy="{cy:.1f}" data-a="3">'
                      + "".join(hojas) + "</g>")
        return "<g>" + "".join(partes) + "</g>"

    def olivo(self, x, y, s):
        L = self.luz
        hoja = "#6E8F4E" if L is not LUCES["noche"] else "#34503A"
        partes = [self.sombra(x, y, s * 1.2)]
        partes.append(f'<path d="M{x - s * 0.08:.1f},{y:.1f} C{x - s * 0.02:.1f},{y - s * 0.3:.1f} '
                      f'{x - s * 0.18:.1f},{y - s * 0.4:.1f} {x - s * 0.05:.1f},{y - s * 0.62:.1f} '
                      f'L{x + s * 0.06:.1f},{y - s * 0.6:.1f} C{x + s * 0.02:.1f},{y - s * 0.4:.1f} '
                      f'{x + s * 0.12:.1f},{y - s * 0.25:.1f} {x + s * 0.08:.1f},{y:.1f}Z" fill="#6B4E32"/>')
        bolas = ((-0.28, -0.72, 0.26), (0.05, -0.86, 0.3), (0.3, -0.7, 0.24), (-0.05, -0.62, 0.28))
        for bx, by, br in bolas:
            partes.append(f'<circle cx="{x + bx * s:.1f}" cy="{y + by * s:.1f}" r="{br * s:.1f}" fill="{hoja}"/>')
        # luz por el lado del sol, sombra por el otro
        lado = L["lado"]
        for bx, by, br in bolas:
            partes.append(f'<circle cx="{x + bx * s + lado * br * s * 0.3:.1f}" cy="{y + by * s - br * s * 0.25:.1f}" '
                          f'r="{br * s * 0.6:.1f}" fill="{cla(hoja, 0.22)}" opacity=".8"/>')
        return '<g class="esc-mece" data-ox="%.1f" data-oy="%.1f" data-a="1.2">%s</g>' % (
            x, y, "".join(partes))

    def tienda(self, x, y, s, color="#C9A27A"):
        L = self.luz
        lado = L["lado"]
        luz, sombra = cla(color, 0.15), osc(color, 0.3)
        partes = [self.sombra(x, y, s * 1.3)]
        izq, der = (sombra, luz) if lado > 0 else (luz, sombra)
        partes.append(f'<path d="M{x - s * 0.7:.1f},{y:.1f} L{x:.1f},{y - s * 0.7:.1f} L{x:.1f},{y:.1f}Z" fill="{izq}"/>')
        partes.append(f'<path d="M{x:.1f},{y - s * 0.7:.1f} L{x + s * 0.7:.1f},{y:.1f} L{x:.1f},{y:.1f}Z" fill="{der}"/>')
        partes.append(f'<path d="M{x - s * 0.14:.1f},{y:.1f} L{x:.1f},{y - s * 0.38:.1f} L{x + s * 0.14:.1f},{y:.1f}Z" '
                      f'fill="{osc(color, 0.65)}"/>')
        for k in (-1, 1):
            partes.append(f'<path d="M{x + k * s * 0.08:.1f},{y - s * 0.62:.1f} l{k * s * 0.42:.1f},{s * 0.42:.1f}" '
                          f'stroke="{osc(color, 0.2)}" stroke-width="{s * 0.03:.1f}"/>')
        if L is LUCES["noche"]:
            partes.append(f'<circle class="esc-halo" cx="{x:.1f}" cy="{y - s * 0.12:.1f}" r="{s * 0.25:.1f}" '
                          f'fill="#FFC860" opacity=".25"/>')
        return "<g>" + "".join(partes) + "</g>"

    def roca(self, x, y, s, color="#B9946A"):
        L = self.luz
        lado = L["lado"]
        partes = [self.sombra(x, y, s)]
        partes.append(f'<path d="M{x - s * 0.5:.1f},{y:.1f} L{x - s * 0.38:.1f},{y - s * 0.35:.1f} '
                      f'L{x - s * 0.05:.1f},{y - s * 0.5:.1f} L{x + s * 0.35:.1f},{y - s * 0.3:.1f} '
                      f'L{x + s * 0.5:.1f},{y:.1f}Z" fill="{color}"/>')
        cara = (f'M{x - s * 0.05:.1f},{y - s * 0.5:.1f} L{x + s * 0.35:.1f},{y - s * 0.3:.1f} '
                f'L{x + s * 0.5:.1f},{y:.1f} L{x + s * 0.05:.1f},{y:.1f}Z') if lado < 0 else (
                f'M{x - s * 0.5:.1f},{y:.1f} L{x - s * 0.38:.1f},{y - s * 0.35:.1f} '
                f'L{x - s * 0.05:.1f},{y - s * 0.5:.1f} L{x - s * 0.02:.1f},{y:.1f}Z')
        partes.append(f'<path d="{cara}" fill="{osc(color, 0.3)}"/>')
        return "<g>" + "".join(partes) + "</g>"

    def barca(self, x, y, s):
        L = self.luz
        madera = mezcla(MADERA, L["sombra"], 0.1)
        vela = "#F3E6C8" if L is not LUCES["noche"] else "#9AA0C0"
        partes = []
        partes.append(f'<ellipse cx="{x:.1f}" cy="{y + s * 0.03:.1f}" rx="{s * 0.75:.1f}" ry="{s * 0.06:.1f}" '
                      f'fill="{L["sombra"]}" opacity=".25"/>')
        partes.append(f'<path d="M{x - s * 0.72:.1f},{y - s * 0.22:.1f} L{x + s * 0.72:.1f},{y - s * 0.22:.1f} '
                      f'Q{x + s * 0.55:.1f},{y + s * 0.02:.1f} {x + s * 0.3:.1f},{y + s * 0.04:.1f} '
                      f'L{x - s * 0.3:.1f},{y + s * 0.04:.1f} Q{x - s * 0.55:.1f},{y + s * 0.02:.1f} '
                      f'{x - s * 0.72:.1f},{y - s * 0.22:.1f}Z" fill="{madera}"/>')
        partes.append(f'<path d="M{x - s * 0.66:.1f},{y - s * 0.14:.1f} L{x + s * 0.66:.1f},{y - s * 0.14:.1f}" '
                      f'stroke="{osc(madera, 0.35)}" stroke-width="{s * 0.025:.1f}"/>')
        partes.append(f'<path d="M{x - s * 0.72:.1f},{y - s * 0.22:.1f} L{x + s * 0.72:.1f},{y - s * 0.22:.1f}" '
                      f'stroke="{cla(madera, 0.35)}" stroke-width="{s * 0.03:.1f}"/>')
        partes.append(f'<rect x="{x - s * 0.02:.1f}" y="{y - s * 1.1:.1f}" width="{s * 0.04:.1f}" '
                      f'height="{s * 0.9:.1f}" fill="{osc(madera, 0.2)}"/>')
        lado = L["lado"]
        partes.append(f'<path d="M{x + s * 0.03:.1f},{y - s * 1.05:.1f} Q{x + s * 0.5:.1f},{y - s * 0.7:.1f} '
                      f'{x + s * 0.52:.1f},{y - s * 0.3:.1f} L{x + s * 0.03:.1f},{y - s * 0.3:.1f}Z" '
                      f'fill="{vela if lado > 0 else osc(vela, 0.2)}"/>')
        partes.append(f'<path d="M{x - s * 0.03:.1f},{y - s * 0.95:.1f} Q{x - s * 0.36:.1f},{y - s * 0.65:.1f} '
                      f'{x - s * 0.4:.1f},{y - s * 0.32:.1f} L{x - s * 0.03:.1f},{y - s * 0.32:.1f}Z" '
                      f'fill="{osc(vela, 0.2) if lado > 0 else vela}"/>')
        return (f'<g class="esc-barca" data-ox="{x:.1f}" data-oy="{y:.1f}">'
                + "".join(partes) + "</g>")

    def pozo(self, x, y, s):
        partes = [self.caja(x - s * 0.4, y, s * 0.8, s * 0.35, PIEDRA, fondo=s * 0.12)]
        partes.append(f'<rect x="{x - s * 0.36:.1f}" y="{y - s * 0.9:.1f}" width="{s * 0.05:.1f}" height="{s * 0.55:.1f}" fill="{MADERA}"/>')
        partes.append(f'<rect x="{x + s * 0.31:.1f}" y="{y - s * 0.9:.1f}" width="{s * 0.05:.1f}" height="{s * 0.55:.1f}" fill="{MADERA}"/>')
        partes.append(f'<rect x="{x - s * 0.42:.1f}" y="{y - s * 0.94:.1f}" width="{s * 0.84:.1f}" height="{s * 0.06:.1f}" fill="{osc(MADERA, 0.2)}"/>')
        return "<g>" + "".join(partes) + "</g>"

    def oveja(self, x, y, s):
        partes = [self.sombra(x, y, s * 0.8)]
        lana = "#F5F1E6" if self.luz is not LUCES["noche"] else "#9BA0BE"
        for dx, dy, r in ((-0.2, -0.32, 0.18), (0.0, -0.38, 0.2), (0.2, -0.32, 0.18), (0.0, -0.26, 0.2)):
            partes.append(f'<circle cx="{x + dx * s:.1f}" cy="{y + dy * s:.1f}" r="{r * s:.1f}" fill="{lana}"/>')
        partes.append(f'<ellipse cx="{x + s * 0.34:.1f}" cy="{y - s * 0.36:.1f}" rx="{s * 0.1:.1f}" ry="{s * 0.08:.1f}" fill="#3A3030"/>')
        for dx in (-0.15, 0.15):
            partes.append(f'<rect x="{x + dx * s:.1f}" y="{y - s * 0.12:.1f}" width="{s * 0.04:.1f}" height="{s * 0.12:.1f}" fill="#3A3030"/>')
        return "<g>" + "".join(partes) + "</g>"

    def nube(self, x, y, s, v):
        L = self.luz
        cuerpo = "".join(f'<circle cx="{x + dx * s:.1f}" cy="{y + dy * s:.1f}" r="{r * s:.1f}" fill="{L["nube"]}"/>'
                         for dx, dy, r in ((-0.4, 0, 0.28), (-0.1, -0.15, 0.36), (0.25, -0.05, 0.3),
                                           (0.5, 0.05, 0.2)))
        base = (f'<rect x="{x - 0.68 * s:.1f}" y="{y:.1f}" width="{1.38 * s:.1f}" height="{0.25 * s:.1f}" '
                f'rx="{0.12 * s:.1f}" fill="{L["nube_s"]}"/>')
        return f'<g class="esc-nube" data-v="{v:.1f}" opacity=".92">{base}{cuerpo}</g>'


# ------------------------------------------------------------ el escenario
def _uid(*cosas):
    return "es" + hashlib.sha1(json.dumps(cosas, sort_keys=True).encode()).hexdigest()[:7]


def svg(nombre, hora, w, h, suelo, H=None):
    """El SVG (sin la etiqueta <svg>: es un <g>) de un escenario de w x h
    centrado en (0, 0). `suelo`: la y (local) donde pisan los personajes."""
    nombre = nombre if nombre in NOMBRES else "campo"
    hora = hora if hora in HORAS else "dia"
    H = H or h / 1.5
    L = LUCES[hora]
    uid = _uid(nombre, hora, round(w), round(h), round(suelo))
    rnd = random.Random(uid)
    c = Lienzo(uid, w, h, L, rnd)
    x0, y0 = -w / 2, -h / 2
    vertical = H > w / 1.3
    # horizonte: en horizontal, mas alto (si no, todo es cielo)
    hz = suelo - H * ((0.16 if vertical else 0.26) + (0.04 if nombre == "mar" else 0))
    # escala de los objetos: lo que mide un personaje de pie
    s = H * (0.26 if vertical else 0.34)

    # --- defs: cielo, halo, suelo, neblina y la mascara que funde los bordes
    cid, hid, sid, nid, mid, gid = (c.id(k) for k in ("c", "h", "s", "n", "m", "g"))
    c1, c2, c3 = L["cielo"]
    sue1, sue2 = SUELOS[nombre]
    sue1, sue2 = mezcla(sue1, L["tinte"], L["t_op"] * 1.4), mezcla(sue2, L["sombra"], L["t_op"])
    c.defs.append(f'<linearGradient id="{cid}" x1="0" y1="0" x2="0" y2="1">'
                  f'<stop offset="0" stop-color="{c1}"/><stop offset=".6" stop-color="{c2}"/>'
                  f'<stop offset="1" stop-color="{c3}"/></linearGradient>')
    c.defs.append(f'<radialGradient id="{hid}"><stop offset="0" stop-color="{L["halo"]}" stop-opacity=".9"/>'
                  f'<stop offset=".35" stop-color="{L["halo"]}" stop-opacity=".35"/>'
                  f'<stop offset="1" stop-color="{L["halo"]}" stop-opacity="0"/></radialGradient>')
    c.defs.append(f'<linearGradient id="{sid}" x1="0" y1="0" x2="0" y2="1">'
                  f'<stop offset="0" stop-color="{mezcla(sue1, L["neblina"], .35)}"/>'
                  f'<stop offset=".4" stop-color="{sue1}"/><stop offset="1" stop-color="{sue2}"/></linearGradient>')
    c.defs.append(f'<linearGradient id="{nid}" x1="0" y1="0" x2="0" y2="1">'
                  f'<stop offset="0" stop-color="{L["neblina"]}" stop-opacity="0"/>'
                  f'<stop offset=".7" stop-color="{L["neblina"]}" stop-opacity=".55"/>'
                  f'<stop offset="1" stop-color="{L["neblina"]}" stop-opacity="0"/></linearGradient>')
    # los bordes se funden con el mundo SOLO fuera del cuadro (el cuadro es el
    # 77 % de ancho y 67 % de alto del escenario): de lado y de arriba/abajo por separado, para que
    # las esquinas del cuadro no se coman
    for eje, (a, b) in (("x", ("1", "0")), ("y", ("0", "1"))):
        c.defs.append(f'<linearGradient id="{gid}{eje}" x1="0" y1="0" x2="{a}" y2="{b}">'
                      f'<stop offset="0" stop-color="#000"/><stop offset=".07" stop-color="#fff"/>'
                      f'<stop offset=".93" stop-color="#fff"/><stop offset="1" stop-color="#000"/>'
                      f'</linearGradient><mask id="{mid}{eje}"><rect x="{x0:.1f}" y="{y0:.1f}" '
                      f'width="{w:.1f}" height="{h:.1f}" fill="url(#{gid}{eje})"/></mask>')

    interior = nombre == "trono"
    if not interior:
        # --- cielo y astro
        c.add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{hz - y0 + 2:.1f}" fill="url(#{cid})"/>')
        if hora == "noche":
            for _ in range(46):
                ex, ey = rnd.uniform(x0, -x0), rnd.uniform(y0, hz - H * 0.05)
                c.add(f'<circle class="esc-estrella" data-f="{rnd.uniform(0, 6.28):.2f}" cx="{ex:.1f}" '
                      f'cy="{ey:.1f}" r="{rnd.uniform(1.0, 2.6) * H / 1000:.2f}" fill="#FFFFFF"/>')
        ax = L["lado"] * w * 0.24
        ay = hz - H * L["alto"] - H * 0.04
        ar = H * (0.05 if hora != "atardecer" else 0.075)
        c.add(f'<circle class="esc-halo" cx="{ax:.1f}" cy="{ay:.1f}" r="{ar * 5:.1f}" fill="url(#{hid})"/>')
        c.add(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="{ar:.1f}" fill="{L["astro"]}"/>')
        if hora == "noche":     # la luna con su sombra
            c.add(f'<circle cx="{ax + ar * 0.38:.1f}" cy="{ay - ar * 0.2:.1f}" r="{ar * 0.85:.1f}" fill="{c2}" opacity=".85"/>')
        if L["rayos"]:
            rayos = []
            for k in range(7):
                a = math.radians(60 + k * 10 + rnd.uniform(-3, 3))
                largo = H * 1.2
                a2 = a + math.radians(2.2)
                rayos.append(f'<path d="M{ax:.1f},{ay:.1f} L{ax - L["lado"] * math.cos(a) * largo:.1f},'
                             f'{ay + math.sin(a) * largo:.1f} L{ax - L["lado"] * math.cos(a2) * largo:.1f},'
                             f'{ay + math.sin(a2) * largo:.1f}Z" fill="{L["astro"]}"/>')
            c.add(f'<g class="esc-rayos" opacity="{L["rayos"]:.2f}">' + "".join(rayos) + "</g>")
        # --- nubes (capa que avanza)
        for k in range(3):
            c.add(c.nube(rnd.uniform(x0 + w * 0.1, -x0 - w * 0.1), y0 + (hz - y0) * rnd.uniform(0.15, 0.6),
                         H * rnd.uniform(0.07, 0.11), rnd.uniform(6, 16) * H / 1000))
        # --- montes lejanos con neblina (dos capas)
        for k, (alto, tono) in enumerate(((0.16, 0.55), (0.1, 0.3))):
            pts = [f"M{x0:.1f},{hz + 2:.1f}"]
            n = 7
            for i in range(n + 1):
                px = x0 + w * i / n
                py = hz - H * alto * rnd.uniform(0.35, 1.0)
                pts.append(f"L{px:.1f},{py:.1f}")
            pts.append(f"L{-x0:.1f},{hz + 2:.1f}Z")
            colm = mezcla(osc(sue2, 0.2) if nombre != "mar" else "#5E7FA0", L["neblina"], tono)
            if hora == "noche":
                colm = mezcla("#141A40", c3, tono)
            c.add(f'<path d="{" ".join(pts)}" fill="{colm}"/>')
        c.add(f'<rect x="{x0:.1f}" y="{hz - H * 0.12:.1f}" width="{w:.1f}" height="{H * 0.14:.1f}" fill="url(#{nid})"/>')

    # --- lo propio de cada sitio
    globals()["_" + nombre](c, x0, y0, w, h, hz, suelo, s, sid, H, vertical)

    # --- gradacion de color de la hora y vineta
    c.add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{L["tinte"]}" '
          f'opacity="{L["t_op"] * 0.6:.2f}"/>')
    return (f'<defs>{"".join(c.defs)}</defs><g mask="url(#{mid}x)"><g mask="url(#{mid}y)">'
            + "".join(c.capas) + "</g></g>")


def _suelo(c, x0, w, h, hz, sid, y0):
    c.add(f'<rect x="{x0:.1f}" y="{hz:.1f}" width="{w:.1f}" height="{-y0 - hz + 1:.1f}" fill="url(#{sid})"/>')


def _mar(c, x0, y0, w, h, hz, suelo, s, sid, H, vertical):
    L = c.luz
    agua1 = mezcla("#2E86C1", L["tinte"], L["t_op"] * 1.6)
    agua2 = mezcla("#14507E", L["sombra"], L["t_op"])
    if L is LUCES["noche"]:
        agua1, agua2 = "#1C2A66", "#070C2A"
    orilla = suelo + H * 0.01
    gid = c.id("a")
    c.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{cla(agua1, .25)}"/>'
                  f'<stop offset="1" stop-color="{agua2}"/></linearGradient>')
    c.add(f'<rect x="{x0:.1f}" y="{hz:.1f}" width="{w:.1f}" height="{orilla - hz + 2:.1f}" fill="url(#{gid})"/>')
    # reflejo del astro en el agua
    ax = L["lado"] * w * 0.24
    refl = []
    for k in range(9):
        yy = hz + (orilla - hz) * (k + 0.5) / 10
        an = w * (0.02 + 0.012 * k)
        refl.append(f'<rect class="esc-ola" data-v="{0.5 + k * 0.2:.1f}" x="{ax - an / 2:.1f}" y="{yy:.1f}" '
                    f'width="{an:.1f}" height="{H * 0.004:.1f}" rx="2" fill="{L["astro"]}"/>')
    c.add('<g opacity=".55">' + "".join(refl) + "</g>")
    # olas por capas (las de delante, mas grandes y mas rapidas)
    for k in range(4):
        u = (k + 1) / 5
        yy = hz + (orilla - hz) * u
        amp = H * (0.004 + 0.008 * u)
        lam = w * (0.06 + 0.06 * u)
        pts = [f"M{x0 - lam * 2:.1f},{yy + amp * 3:.1f}"]
        x = x0 - lam * 2
        while x < -x0 + lam * 2:
            pts.append(f"Q{x + lam / 4:.1f},{yy - amp:.1f} {x + lam / 2:.1f},{yy:.1f} "
                       f"T{x + lam:.1f},{yy:.1f}")
            x += lam
        pts.append(f"L{x:.1f},{yy + amp * 3:.1f}Z")
        col = mezcla(agua1, agua2, u * 0.7)
        c.add(f'<g class="esc-ola" data-v="{(1 + 2 * u) * (1 if k % 2 else -1):.1f}" data-l="{lam:.1f}">'
              f'<path d="{" ".join(pts)}" fill="{col}"/>'
              f'<path d="{" ".join(pts[:-1])}" fill="none" stroke="{cla(agua1, .55)}" '
              f'stroke-width="{H * 0.002:.1f}" opacity=".6"/></g>')
    # barca a un lado (la de la pesca)
    c.add(c.barca(-L["lado"] * w * 0.27, hz + (orilla - hz) * 0.55, s * 0.62))
    # orilla de arena donde pisan
    arena1, arena2 = SUELOS["mar"]
    if L is LUCES["noche"]:
        arena1, arena2 = "#5A5878", "#2E2C48"
    c.add(f'<path d="M{x0:.1f},{orilla + H * 0.02:.1f} Q{x0 + w * 0.3:.1f},{orilla - H * 0.012:.1f} '
          f'{0:.1f},{orilla + H * 0.005:.1f} T{-x0:.1f},{orilla:.1f} L{-x0:.1f},{-y0:.1f} L{x0:.1f},{-y0:.1f}Z" '
          f'fill="{arena1}"/>')
    c.add(f'<rect x="{x0:.1f}" y="{suelo + H * 0.08:.1f}" width="{w:.1f}" height="{-y0 - suelo:.1f}" fill="{arena2}" opacity=".5"/>')
    c.add(c.roca(L["lado"] * w * 0.38, suelo + H * 0.03, s * 0.35))


def _desierto(c, x0, y0, w, h, hz, suelo, s, sid, H, vertical):
    L = c.luz
    _suelo(c, x0, w, h, hz, sid, y0)
    a1, a2 = SUELOS["desierto"]
    if L is LUCES["noche"]:
        a1, a2 = "#6A6290", "#2E2A50"
    # dunas por capas: cara al sol clara, la otra en sombra
    for k, (yy, alto) in enumerate(((hz + H * 0.03, 0.06), (hz + H * 0.09, 0.07))):
        cx = c.rnd.uniform(-w * 0.2, w * 0.2)
        col = mezcla(a1, a2, 0.2 + 0.25 * k)
        c.add(f'<path d="M{x0:.1f},{yy + H * 0.05:.1f} Q{cx - w * 0.2:.1f},{yy - H * alto:.1f} {cx:.1f},{yy - H * alto:.1f} '
              f'Q{cx + w * 0.25:.1f},{yy - H * alto * 0.4:.1f} {-x0:.1f},{yy + H * 0.04:.1f} '
              f'L{-x0:.1f},{-y0:.1f} L{x0:.1f},{-y0:.1f}Z" fill="{col}"/>')
        lado = L["lado"]
        c.add(f'<path d="M{cx:.1f},{yy - H * alto:.1f} Q{cx - lado * w * 0.12:.1f},{yy - H * alto * 0.2:.1f} '
              f'{cx - lado * w * 0.3:.1f},{yy + H * 0.05:.1f} L{cx:.1f},{yy + H * 0.05:.1f}Z" '
              f'fill="{osc(col, 0.22)}" opacity=".7"/>')
    c.add(c.palmera(w * 0.36, suelo - H * 0.02, s * 1.05))
    c.add(c.palmera(w * 0.27, suelo - H * 0.04, s * 0.7))
    c.add(c.tienda(-w * 0.32, suelo - H * 0.01, s * 0.7))
    c.add(c.roca(-w * 0.12, suelo + H * 0.06, s * 0.28))


def _ciudad(c, x0, y0, w, h, hz, suelo, s, sid, H, vertical):
    _suelo(c, x0, w, h, hz, sid, y0)
    L = c.luz
    piedra = mezcla(PIEDRA, L["sombra"], 0.08)
    base = hz + H * 0.07
    # casas detras de la muralla
    for k in range(7):
        cw = s * c.rnd.uniform(0.35, 0.55)
        cx = x0 + w * (0.08 + 0.13 * k)
        c.add(c.caja(cx, base - H * 0.04, cw, s * c.rnd.uniform(0.45, 0.8), mezcla(ADOBE, PIEDRA, c.rnd.random()),
                     ventanas=1))
    # la muralla con almenas, dos torres y la puerta en arco
    mh = s * 0.55
    c.add(c.caja(x0 - 10, base, w + 20, mh, piedra, fondo=s * 0.05, techo=False))
    almenas = []
    paso = s * 0.14
    x = x0
    while x < -x0:
        almenas.append(f'<rect x="{x:.1f}" y="{base - mh - paso * 0.5:.1f}" width="{paso * 0.6:.1f}" '
                       f'height="{paso * 0.5:.1f}" fill="{piedra}"/>')
        x += paso
    c.add("".join(almenas))
    for k in range(4):     # juntas de los sillares
        yy = base - mh * (0.25 + 0.25 * k)
        c.add(f'<path d="M{x0:.1f},{yy:.1f} L{-x0:.1f},{yy:.1f}" stroke="{osc(piedra, .2)}" '
              f'stroke-width="{H * 0.0015:.1f}" opacity=".6"/>')
    for tx in (-w * 0.2, w * 0.2):
        c.add(c.caja(tx - s * 0.2, base, s * 0.4, mh * 1.6, piedra, ventanas=1))
    pw, ph = s * 0.32, mh * 0.75
    c.add(f'<path d="M{-pw / 2:.1f},{base:.1f} L{-pw / 2:.1f},{base - ph + pw / 2:.1f} '
          f'A{pw / 2:.1f},{pw / 2:.1f} 0 0 1 {pw / 2:.1f},{base - ph + pw / 2:.1f} L{pw / 2:.1f},{base:.1f}Z" '
          f'fill="{osc(piedra, .65)}"/>')
    c.add(c.olivo(-w * 0.38, suelo + H * 0.02, s * 0.75))
    c.add(c.palmera(w * 0.38, suelo + H * 0.02, s * 0.85))


def _torre(c, x0, y0, w, h, hz, suelo, s, sid, H, vertical):
    _suelo(c, x0, w, h, hz, sid, y0)
    L = c.luz
    ladrillo = mezcla("#C98A55", L["sombra"], 0.08)
    base = hz + H * 0.06
    ancho = w * 0.62
    alto = s * 0.3
    for k in range(6):       # el zigurat, piso a piso
        aw = ancho * (1 - 0.14 * k)
        col = mezcla(ladrillo, "#E6C08A", k * 0.08)
        c.add(c.caja(-aw / 2, base - alto * k, aw, alto, col, fondo=s * 0.08, ventanas=0))
        for j in range(int(aw / (s * 0.18))):
            xx = -aw / 2 + s * 0.09 + j * s * 0.18
            c.add(f'<rect x="{xx:.1f}" y="{base - alto * (k + 0.75):.1f}" width="{s * 0.05:.1f}" '
                  f'height="{alto * 0.5:.1f}" fill="{osc(col, .35)}"/>')
    # rampa
    c.add(f'<path d="M{-ancho * 0.1:.1f},{base:.1f} L{ancho * 0.06:.1f},{base - alto * 3:.1f} '
          f'L{ancho * 0.14:.1f},{base - alto * 3:.1f} L{ancho * 0.05:.1f},{base:.1f}Z" fill="{cla(ladrillo, .2)}"/>')
    c.add(c.nube(-w * 0.18, base - alto * 5.6, s * 0.35, 4))
    c.add(c.palmera(-w * 0.4, suelo + H * 0.02, s * 0.9))
    c.add(c.roca(w * 0.36, suelo + H * 0.04, s * 0.35))


def _templo(c, x0, y0, w, h, hz, suelo, s, sid, H, vertical):
    _suelo(c, x0, w, h, hz, sid, y0)
    L = c.luz
    marmol = mezcla("#F1E6CF", L["sombra"], 0.06)
    base = hz + H * 0.08
    # explanada y escalinata
    c.add(c.caja(-w * 0.46, base, w * 0.92, s * 0.18, mezcla(PIEDRA, marmol, .5), fondo=s * 0.06))
    for k in range(4):
        c.add(f'<rect x="{-w * 0.12 + k * w * 0.01:.1f}" y="{base - s * 0.045 * (k + 1):.1f}" '
              f'width="{w * 0.24 - k * w * 0.02:.1f}" height="{s * 0.045:.1f}" fill="{cla(marmol, .1) if k % 2 else marmol}"/>')
    # el santuario: fachada alta con columnas y remate de oro
    fw, fh = w * 0.34, s * 1.25
    fb = base - s * 0.18
    c.add(c.caja(-fw / 2, fb, fw, fh, marmol, fondo=s * 0.22, puerta=True))
    for k in range(4):
        cx = -fw / 2 + fw * (0.12 + 0.76 * k / 3)
        c.add(f'<rect x="{cx - fw * 0.035:.1f}" y="{fb - fh * 0.92:.1f}" width="{fw * 0.07:.1f}" height="{fh * 0.92:.1f}" fill="{cla(marmol, .25)}"/>')
        c.add(f'<rect x="{cx + fw * 0.01:.1f}" y="{fb - fh * 0.92:.1f}" width="{fw * 0.025:.1f}" height="{fh * 0.92:.1f}" fill="{osc(marmol, .18)}"/>')
    c.add(f'<rect x="{-fw / 2 - fw * 0.03:.1f}" y="{fb - fh - s * 0.06:.1f}" width="{fw * 1.06:.1f}" height="{s * 0.07:.1f}" fill="{ORO}"/>')
    c.add(f'<rect x="{-fw / 2:.1f}" y="{fb - fh - s * 0.06:.1f}" width="{fw:.1f}" height="{s * 0.018:.1f}" fill="{cla(ORO, .5)}"/>')
    # alas bajas a los lados (atrios)
    for lado in (-1, 1):
        c.add(c.caja(lado * w * 0.17 - (s * 0.5 if lado < 0 else 0) + (0 if lado < 0 else 0), fb,
                     s * 0.5, s * 0.55, cla(marmol, .05), ventanas=2))
    # altar de piedra delante, a un lado
    c.add(c.caja(-w * 0.34, suelo - H * 0.01, s * 0.32, s * 0.2, osc(PIEDRA, .05), fondo=s * 0.07))
    c.add(c.olivo(w * 0.38, suelo + H * 0.02, s * 0.7))


def _trono(c, x0, y0, w, h, hz, suelo, s, sid, H, vertical):
    L = c.luz
    noche = L is LUCES["noche"]
    pared1 = "#8E5A3A" if not noche else "#3A2A40"
    pared2 = osc(pared1, .45)
    pid, lid = c.id("p"), c.id("l")
    c.defs.append(f'<linearGradient id="{pid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{pared2}"/>'
                  f'<stop offset="1" stop-color="{pared1}"/></linearGradient>')
    c.defs.append(f'<linearGradient id="{lid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6E4A30"/>'
                  f'<stop offset=".35" stop-color="#E9D2A8"/><stop offset=".6" stop-color="#C9A880"/>'
                  f'<stop offset="1" stop-color="#5A3A24"/></linearGradient>')
    piso = hz + H * 0.02
    c.add(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{piso - y0 + 2:.1f}" fill="url(#{pid})"/>')
    # ventana alta con el haz de luz que cae sobre el trono
    vx = -L["lado"] * w * 0.08 + w * 0.22 * L["lado"]
    vy = y0 + h * 0.18
    vw, vh = w * 0.09, H * 0.16
    luzv = "#FFF1C4" if not noche else "#AFC0FF"
    c.add(f'<path d="M{vx - vw / 2:.1f},{vy + vh:.1f} L{vx - vw / 2:.1f},{vy + vw / 2:.1f} A{vw / 2:.1f},{vw / 2:.1f} 0 0 1 '
          f'{vx + vw / 2:.1f},{vy + vw / 2:.1f} L{vx + vw / 2:.1f},{vy + vh:.1f}Z" fill="{luzv}"/>')
    c.add(f'<path class="esc-rayos" d="M{vx - vw / 2:.1f},{vy + vh * 0.3:.1f} L{vx + vw / 2:.1f},{vy + vh * 0.3:.1f} '
          f'L{-L["lado"] * w * 0.1 + vw:.1f},{suelo + H * 0.02:.1f} L{-L["lado"] * w * 0.1 - vw * 2.5:.1f},{suelo + H * 0.02:.1f}Z" '
          f'fill="{luzv}" opacity=".16"/>')
    # columnas con volumen (degradado de cilindro)
    for k in range(4):
        cx = x0 + w * (0.08 + 0.28 * k)
        cw = w * 0.07
        c.add(f'<rect x="{cx - cw / 2:.1f}" y="{y0:.1f}" width="{cw:.1f}" height="{piso - y0:.1f}" fill="url(#{lid})"/>')
        c.add(f'<rect x="{cx - cw * 0.7:.1f}" y="{piso - H * 0.03:.1f}" width="{cw * 1.4:.1f}" height="{H * 0.03:.1f}" fill="#B8956C"/>')
    # cortinas
    for lado in (-1, 1):
        cx = lado * w * 0.5
        c.add(f'<path d="M{cx:.1f},{y0:.1f} L{cx - lado * w * 0.16:.1f},{y0:.1f} Q{cx - lado * w * 0.08:.1f},{(y0 + piso) / 2:.1f} '
              f'{cx - lado * w * 0.12:.1f},{piso:.1f} L{cx:.1f},{piso:.1f}Z" fill="#8E1E2A"/>')
        c.add(f'<path d="M{cx - lado * w * 0.05:.1f},{y0:.1f} Q{cx - lado * w * 0.02:.1f},{(y0 + piso) / 2:.1f} '
              f'{cx - lado * w * 0.06:.1f},{piso:.1f}" stroke="#5E0E18" stroke-width="{w * 0.008:.1f}" fill="none"/>')
    # suelo y alfombra en perspectiva
    c.add(f'<rect x="{x0:.1f}" y="{piso:.1f}" width="{w:.1f}" height="{-y0 - piso + 1:.1f}" fill="url(#{sid})"/>')
    c.add(f'<path d="M{-w * 0.06:.1f},{piso:.1f} L{w * 0.06:.1f},{piso:.1f} L{w * 0.22:.1f},{-y0:.1f} '
          f'L{-w * 0.22:.1f},{-y0:.1f}Z" fill="#B3263A"/>')
    c.add(f'<path d="M{-w * 0.05:.1f},{piso:.1f} L{-w * 0.19:.1f},{-y0:.1f} M{w * 0.05:.1f},{piso:.1f} L{w * 0.19:.1f},{-y0:.1f}" '
          f'stroke="{ORO}" stroke-width="{w * 0.006:.1f}"/>')
    # el trono al fondo, sobre escalones, con su brillo
    tb = piso - H * 0.005
    for k in range(3):
        c.add(f'<rect x="{-w * (0.13 - 0.025 * k):.1f}" y="{tb - s * 0.06 * (k + 1):.1f}" '
              f'width="{w * (0.26 - 0.05 * k):.1f}" height="{s * 0.06:.1f}" fill="{mezcla("#C9A880", "#8A6A48", k * 0.3)}"/>')
    ty = tb - s * 0.18
    c.add(f'<circle class="esc-halo" cx="0" cy="{ty - s * 0.35:.1f}" r="{s * 0.6:.1f}" fill="#FFD77A" opacity=".18"/>')
    c.add(f'<path d="M{-s * 0.2:.1f},{ty:.1f} L{-s * 0.2:.1f},{ty - s * 0.65:.1f} Q0,{ty - s * 0.85:.1f} '
          f'{s * 0.2:.1f},{ty - s * 0.65:.1f} L{s * 0.2:.1f},{ty:.1f}Z" fill="{ORO}"/>')
    c.add(f'<path d="M{-s * 0.13:.1f},{ty - s * 0.08:.1f} L{-s * 0.13:.1f},{ty - s * 0.58:.1f} Q0,{ty - s * 0.72:.1f} '
          f'{s * 0.13:.1f},{ty - s * 0.58:.1f} L{s * 0.13:.1f},{ty - s * 0.08:.1f}Z" fill="#8E1E2A"/>')
    c.add(f'<rect x="{-s * 0.26:.1f}" y="{ty - s * 0.12:.1f}" width="{s * 0.52:.1f}" height="{s * 0.12:.1f}" rx="{s * 0.03:.1f}" fill="{cla(ORO, .15)}"/>')
    c.add(f'<rect x="{(s * 0.2 - s * 0.04) * (1 if L["lado"] > 0 else -1) - s * 0.02:.1f}" y="{ty - s * 0.65:.1f}" '
          f'width="{s * 0.04:.1f}" height="{s * 0.53:.1f}" fill="{cla(ORO, .5)}" opacity=".8"/>')


def _monte(c, x0, y0, w, h, hz, suelo, s, sid, H, vertical):
    _suelo(c, x0, w, h, hz, sid, y0)
    L = c.luz
    roca = mezcla("#A3735A", L["sombra"], 0.1)
    if L is LUCES["noche"]:
        roca = "#3C3460"
    cima = hz - H * 0.4
    cx = w * 0.06 * L["lado"]
    c.add(f'<path d="M{x0 - w * 0.05:.1f},{hz + H * 0.05:.1f} L{cx - w * 0.12:.1f},{cima + H * 0.06:.1f} '
          f'L{cx:.1f},{cima:.1f} L{cx + w * 0.14:.1f},{cima + H * 0.08:.1f} L{-x0 + w * 0.05:.1f},{hz + H * 0.05:.1f}Z" '
          f'fill="{roca}"/>')
    lado = L["lado"]
    c.add(f'<path d="M{cx:.1f},{cima:.1f} L{cx - lado * w * 0.12:.1f},{cima + H * 0.07:.1f} '
          f'L{cx - lado * w * 0.55:.1f},{hz + H * 0.05:.1f} L{cx - lado * w * 0.05:.1f},{hz + H * 0.05:.1f}Z" '
          f'fill="{osc(roca, .3)}"/>')
    # camino en zigzag hasta la cima
    pts = []
    for k in range(6):
        u = k / 5
        pts.append(f"{cx + (w * 0.1 if k % 2 else -w * 0.08) * (1 - u):.1f},{hz + H * 0.05 - (hz + H * 0.05 - cima - H * 0.03) * u:.1f}")
    c.add(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{cla(roca, .35)}" stroke-width="{H * 0.004:.1f}" '
          f'stroke-dasharray="{H * 0.01:.1f} {H * 0.008:.1f}"/>')
    # nube y luz en la cumbre
    c.add(f'<circle class="esc-halo" cx="{cx:.1f}" cy="{cima - H * 0.02:.1f}" r="{H * 0.14:.1f}" fill="#FFF3C4" opacity=".22"/>')
    c.add(c.nube(cx - s * 0.2, cima + H * 0.02, s * 0.42, 3))
    c.add(c.olivo(-w * 0.36, suelo + H * 0.02, s * 0.8))
    c.add(c.olivo(w * 0.4, suelo + H * 0.03, s * 0.6))
    c.add(c.roca(w * 0.22, suelo + H * 0.05, s * 0.3))


def _campo(c, x0, y0, w, h, hz, suelo, s, sid, H, vertical):
    _suelo(c, x0, w, h, hz, sid, y0)
    L = c.luz
    v1, v2 = SUELOS["campo"]
    if L is LUCES["noche"]:
        v1, v2 = "#2E4A50", "#14262E"
    for k, (yy, amp) in enumerate(((hz + H * 0.02, 0.05), (hz + H * 0.07, 0.04))):
        col = mezcla(v1, v2, 0.15 + 0.3 * k)
        c.add(f'<path d="M{x0:.1f},{yy + H * 0.03:.1f} Q{-w * 0.2:.1f},{yy - H * amp:.1f} {w * 0.05:.1f},{yy:.1f} '
              f'T{-x0:.1f},{yy - H * 0.01:.1f} L{-x0:.1f},{-y0:.1f} L{x0:.1f},{-y0:.1f}Z" fill="{col}"/>')
    # surcos/hierba
    for k in range(18):
        gx = c.rnd.uniform(x0, -x0)
        gy = c.rnd.uniform(suelo, -y0)
        c.add(f'<path d="M{gx:.1f},{gy:.1f} l{-H * 0.006:.1f},{-H * 0.018:.1f} M{gx:.1f},{gy:.1f} l{H * 0.006:.1f},{-H * 0.02:.1f}" '
              f'stroke="{osc(v2, .2)}" stroke-width="{H * 0.002:.1f}"/>')
    c.add(c.olivo(-w * 0.38, suelo - H * 0.01, s * 0.9))
    c.add(c.pozo(w * 0.33, suelo + H * 0.01, s * 0.55))
    c.add(c.oveja(-w * 0.18, suelo + H * 0.05, s * 0.32))
    c.add(c.oveja(w * 0.14, suelo + H * 0.07, s * 0.28))


# ------------------------------------------------------------ efectos Lottie
def _k(v):
    return {"a": 0, "k": v}


def _kf(lista, op=60):
    """[(t, valor)] -> propiedad animada de Lottie (suave dentro y fuera)."""
    ks = []
    for t, v in lista:
        v = v if isinstance(v, list) else [v]
        ks.append({"t": round(t, 2), "s": v, "i": {"x": [0.45], "y": [1]},
                   "o": {"x": [0.55], "y": [0]}})
    return {"a": 1, "k": ks}


def _ciclo(puntos, fase, op=60):
    """Un perfil [(u, valor)] de 0 a 1 repetido cada `op` fotogramas y
    adelantado `fase`: varias piezas iguales que no van al unisono."""
    def valor(u):
        for (u0, a), (u1, b) in zip(puntos, puntos[1:]):
            if u0 <= u <= u1:
                k = 0 if u1 == u0 else (u - u0) / (u1 - u0)
                return [x + (y - x) * k for x, y in zip(a, b)] if isinstance(a, list) else a + (b - a) * k
        return puntos[-1][1]
    claves = sorted((((u - fase) % 1.0) * op, v) for u, v in puntos)
    return _kf([(0, valor(fase))] + claves + [(op, valor(fase))], op)


def _capa(ind, forma, color, ks, op=60, opacidad=100):
    return {"ddd": 0, "ind": ind, "ty": 4, "sr": 1, "ao": 0, "bm": 0, "ip": 0, "op": op, "st": 0,
            "ks": ks, "shapes": [{"ty": "gr", "it": [forma,
                                                      {"ty": "fl", "c": _k(color + [1]), "o": _k(opacidad), "r": 1},
                                                      {"ty": "tr", "p": _k([0, 0]), "a": _k([0, 0]), "s": _k([100, 100]),
                                                       "r": _k(0), "o": _k(100)}]}]}


def _tr(p, s=None, o=None, r=None):
    return {"p": p if isinstance(p, dict) else _k(p + [0]),
            "s": s if isinstance(s, dict) else _k((s or [100, 100]) + [100]),
            "o": o if isinstance(o, dict) else _k(100 if o is None else o),
            "r": r if isinstance(r, dict) else _k(r or 0), "a": _k([0, 0, 0])}


_GOTA = {"ty": "sh", "ks": _k({"c": True,
                               "v": [[0, -100], [36, -28], [0, 0], [-36, -28]],
                               "i": [[-12, 30], [0, -30], [22, 0], [0, 22]],
                               "o": [[12, 30], [0, 22], [-22, 0], [0, -30]]})}


def _circulo(d):
    return {"ty": "el", "p": _k([0, 0]), "s": _k([d, d]), "d": 1}


def lottie_de(efecto):
    """La animacion Lottie (dict) de un efecto: 200x200, 30 fps, 2 s en bucle."""
    op = 60
    capas = []
    if efecto == "fuego":
        chispas = []
        for k in range(5):
            x0 = 100 + (k - 2) * 12
            chispas.append(_capa(10 + k, _circulo(6), [1, 0.85, 0.4], _tr(
                _ciclo([(0, [x0, 168]), (0.5, [x0 + (k % 2 * 2 - 1) * 14, 100]), (0.999, [x0 - (k % 2 * 2 - 1) * 8, 30])], k / 5),
                o=_ciclo([(0, 0), (0.1, 100), (0.999, 0)], k / 5)), op))
        capas += chispas
        llamas = (([1, 0.95, 0.6], 0.42, 0, 0.0), ([1, 0.72, 0.15], 0.66, 0, 0.3),
                  ([0.95, 0.38, 0.08], 0.9, 0, 0.55), ([0.95, 0.38, 0.08], 0.5, -26, 0.15),
                  ([0.95, 0.38, 0.08], 0.48, 27, 0.7))
        for k, (col, tam, dx, fase) in enumerate(llamas):
            sx = tam * 100
            capas.append(_capa(20 + k, _GOTA, col, _tr(
                [100 + dx, 176],
                s=_ciclo([(0, [sx, sx]), (0.25, [sx * 0.92, sx * 1.18]), (0.5, [sx * 1.05, sx * 0.94]),
                          (0.75, [sx * 0.95, sx * 1.12]), (1, [sx, sx])], fase),
                r=_ciclo([(0, -4), (0.33, 5), (0.66, -2), (1, -4)], fase)), op))
        capas.append(_capa(30, _circulo(170), [1, 0.55, 0.15], _tr(
            [100, 150], s=[100, 70], o=_ciclo([(0, 22), (0.5, 34), (1, 22)], 0)), op))
    elif efecto == "humo":
        for k in range(6):
            x0 = 100 + (k % 3 - 1) * 10
            gris = 0.55 + 0.08 * (k % 3)
            capas.append(_capa(1 + k, _circulo(44), [gris * 0.8, gris * 0.8, gris * 0.84], _tr(
                _ciclo([(0, [x0, 175]), (0.5, [x0 + 18 * (1 if k % 2 else -1), 105]), (0.999, [x0 - 10, 25])], k / 6),
                s=_ciclo([(0, [60, 60]), (0.999, [230, 230])], k / 6),
                o=_ciclo([(0, 0), (0.2, 72), (0.999, 0)], k / 6)), op))
    else:   # luz: gloria que gira despacio y respira, con destellos
        for k in range(4):
            ang = math.radians(45 + 90 * k)
            x, y = 100 + math.cos(ang) * 62, 100 + math.sin(ang) * 62
            estrella = {"ty": "sr", "sy": 1, "d": 1, "pt": _k(4), "p": _k([0, 0]), "r": _k(0),
                        "ir": _k(3), "is": _k(0), "or": _k(12), "os": _k(0)}
            capas.append(_capa(1 + k, estrella, [1, 1, 0.92], _tr(
                [x, y], s=_ciclo([(0, [0, 0]), (0.2, [110, 110]), (0.4, [0, 0]), (1, [0, 0])], k / 4)), op))
        capas.append(_capa(10, _circulo(70), [1, 1, 0.9], _tr(
            [100, 100], s=_ciclo([(0, [90, 90]), (0.5, [110, 110]), (1, [90, 90])], 0), o=70), op))
        capas.append(_capa(11, _circulo(130), [1, 0.95, 0.7], _tr(
            [100, 100], s=_ciclo([(0, [95, 95]), (0.5, [108, 108]), (1, [95, 95])], 0.25), o=30), op))
        rayos = {"ty": "sr", "sy": 1, "d": 1, "pt": _k(12), "p": _k([0, 0]), "r": _k(0),
                 "ir": _k(30), "is": _k(0), "or": _k(98), "os": _k(0)}
        capas.append(_capa(12, rayos, [1, 0.92, 0.6], _tr(
            [100, 100], r=_kf([(0, 0), (op, 30)]), o=28), op))
    return {"v": "5.7.4", "fr": 30, "ip": 0, "op": op, "w": 200, "h": 200, "nm": efecto,
            "ddd": 0, "assets": [], "layers": capas}


# ------------------------------------------------------------ la pieza
def pieza(nombre, hora, efectos, W, H, en, suelo_px=None):
    """La pieza `escenario` de motion: ocupa el cuadro entero (algo mas, para
    que el viaje de la camara no le vea el borde) con centro en el del cuadro.
    `suelo_px`: la y del cuadro donde pisan los personajes."""
    W, H = float(W), float(H)
    vertical = H > W
    if suelo_px is None:
        suelo_px = H * (0.556 if vertical else 0.71)
    suelo = suelo_px - H / 2
    w, h = W * 1.3, H * 1.5     # la camara se acerca y sube a las caras
    nombre = nombre if nombre in NOMBRES else "campo"
    hora = hora if hora in HORAS else "dia"
    efectos = [e for e in (efectos or []) if e in EFECTOS][:3]
    tam = H * (0.2 if vertical else 0.3)
    # donde va cada efecto: el fuego y el humo a un lado (el altar, la
    # hoguera), la luz detras de los personajes
    lado = W * (0.34 if vertical else 0.3)
    sitio = {"fuego": (-lado, suelo - tam * 0.38), "humo": (-lado, suelo - tam * 1.0),
             "luz": (0, suelo - H * (0.2 if vertical else 0.3))}
    if nombre == "templo":
        sitio["fuego"] = (-W * 0.34 * 1.0 + W * 0.04, suelo - H * 0.01 - tam * 0.62)
        sitio["humo"] = (sitio["fuego"][0], sitio["fuego"][1] - tam * 0.7)
    lista = []
    for e in efectos:
        x, y = sitio[e]
        t = tam * (2.2 if e == "luz" else 1.0) * (1.3 if e == "humo" else 1)
        lista.append({"tipo": e, "x": round(x, 1), "y": round(y, 1), "tam": round(t, 1),
                      "datos": lottie_de(e)})
    return {"tipo": "escenario", "nombre": nombre, "hora": hora, "fondo": True,
            "svg": svg(nombre, hora, w, h, suelo, H=H), "w": round(w, 1), "h": round(h, 1),
            "efectos": lista, "x": round(W / 2, 1), "y": round(H / 2, 1),
            "en": round(float(en), 3), "entra": "nada"}


def con_efectos(conf):
    """¿Hay algun efecto Lottie en las piezas de esta pagina?"""
    return any(p.get("tipo") == "escenario" and p.get("efectos")
               for p in (conf or {}).get("piezas") or [])


def lottie_js():
    with open(LOTTIE, encoding="utf-8") as f:
        return f.read()


ESCENARIO_JS = r"""
// ===== ESCENARIOS (pasos/escenarios.py) ======================================
// El SVG llega hecho; aqui solo se mueve por capas en funcion de T: nubes que
// avanzan, olas que van y vienen, barca que se mece, palmeras al viento,
// estrellas que titilan, halos que respiran; y los efectos Lottie (fuego,
// humo, luz) se ponen en el fotograma exacto con goToAndStop.
function hazEscenario(p, padre){
  const g = mk('g', {}, padre);
  g.innerHTML = p.svg;
  const pick = c => Array.from(g.querySelectorAll('.' + c));
  const nubes = pick('esc-nube'), olas = pick('esc-ola'), barcas = pick('esc-barca'),
        meces = pick('esc-mece'), estrellas = pick('esc-estrella'), halos = pick('esc-halo'),
        rayos = pick('esc-rayos');
  const anims = [];
  (p.efectos || []).forEach(ef => {
    if (!window.lottie) return;
    const fo = mk('foreignObject', {x: ef.x - ef.tam/2, y: ef.y - ef.tam/2, width: ef.tam, height: ef.tam}, g);
    const div = document.createElementNS('http://www.w3.org/1999/xhtml', 'div');
    div.setAttribute('class', 'esc-lottie');
    fo.appendChild(div);
    try {
      const a = lottie.loadAnimation({container: div, renderer: 'svg', loop: true, autoplay: false,
        animationData: JSON.parse(JSON.stringify(ef.datos))});
      anims.push(a);
    } catch (e) { console.log('lottie ' + ef.tipo + ': ' + e); }
  });
  const base = halos.map(h => +h.getAttribute('opacity') || 1);
  const baseR = rayos.map(h => +h.getAttribute('opacity') || 1);
  return function(T){
    const s = T - p.en;
    g.setAttribute('opacity', cl(s/0.6, 0, 1).toFixed(3));
    nubes.forEach(n => n.setAttribute('transform', `translate(${(T*(+n.dataset.v)).toFixed(1)},0)`));
    olas.forEach(o => {
      const v = +o.dataset.v, l = +o.dataset.l || 0;
      const dx = l ? ((T*v*18) % l) : Math.sin(T*v*2)*4;
      o.setAttribute('transform', `translate(${dx.toFixed(1)},${(Math.sin(T*1.6 + v)*2).toFixed(1)})`);
    });
    barcas.forEach(b => {
      const ox = +b.dataset.ox, oy = +b.dataset.oy;
      b.setAttribute('transform', `translate(0,${(Math.sin(T*1.7)*5).toFixed(1)}) rotate(${(Math.sin(T*1.3)*3.5).toFixed(2)},${ox},${oy})`);
    });
    meces.forEach(m => m.setAttribute('transform', `rotate(${(Math.sin(T*1.1 + (+m.dataset.ox)*0.01)*(+m.dataset.a || 2)).toFixed(2)},${m.dataset.ox},${m.dataset.oy})`));
    estrellas.forEach(e => e.setAttribute('opacity', (0.45 + 0.55*Math.abs(Math.sin(T*1.8 + (+e.dataset.f)))).toFixed(2)));
    halos.forEach((h, k) => h.setAttribute('opacity', (base[k]*(0.85 + 0.15*Math.sin(T*2 + k))).toFixed(3)));
    rayos.forEach((r, k) => r.setAttribute('opacity', (baseR[k]*(0.75 + 0.25*Math.sin(T*0.9 + k))).toFixed(3)));
    anims.forEach(a => { try { a.goToAndStop(((Math.max(0, s)*30) % a.totalFrames), true); } catch (e) {} });
  };
}
Object.assign(CONSTRUCTORES, {escenario: hazEscenario});
"""
