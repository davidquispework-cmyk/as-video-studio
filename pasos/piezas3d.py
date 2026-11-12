"""El constructor de objetos de plastilina (P6c del plan NIVEL PROFESIONAL).

P6b dejó 18 objetos hechos a mano (`biblia3d.OBJETOS`). Esto deja que CLAUDE
construya cualquier otro que nombre el guion —una lámpara, un arpa, un
pergamino, una tienda, una sandalia...— juntando PIEZAS de plastilina:
esferas, cajas, cilindros, conos, aros y cápsulas, cada una con su color,
posición, tamaño y giro. El navegador del render las monta (`armar` en
`biblia3d.BIBLIA_JS`), las escala a la medida de la mesa y las deja caer como
los demás.

LA BIBLIOTECA: cada objeto construido se guarda en
`banco/objetos3d/<id>.json` (fuera del árbol del programa: `asvs actualizar`
no la toca) con las palabras que lo nombran. La SIGUIENTE vez que el guion diga
una de esas palabras sale gratis, sin preguntar a nadie. Se puede editar a mano
o borrar un fichero para que se vuelva a construir.

CUÁNDO SE PREGUNTA: al montar un vídeo con «📖 Biblia 3D», UNA llamada por
vídeo (sonnet, esfuerzo bajo) con la narración de los planos del decorado que
aún tienen hueco en la mesa. La respuesta se guarda en
`trabajo/objetos3d.json` por la huella de esas frases: volver a montar no
vuelve a preguntar. Sin Claude (sin cupo, sin sesión), el plano sale con los
objetos de siempre y el montaje sigue.

Apagado: param del render `biblia3d: {"construir": false}` o
`ESTUDIO_PIEZAS3D=no`. No es un param por defecto ni toca firmas: basta
«Regenerar Vídeo».
"""
import hashlib
import json
import os
import re

import citas

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORMAS = ("esfera", "caja", "cilindro", "cono", "toro", "capsula")
MAX_PIEZAS = 16
MAX_PALABRAS = 12
_COLOR = re.compile(r"^#?[0-9a-fA-F]{6}$")
_ID = re.compile(r"[^a-z0-9]+")
# palabras que nunca deben llevar a un objeto (salen en cualquier frase)
_VACIAS = {"que", "los", "las", "una", "uno", "del", "con", "por", "para", "como",
           "dios", "jesus", "senor", "hombre", "mujer", "gente", "pueblo", "dia",
           "vez", "cosa", "cosas", "todo", "nada", "algo", "vida", "muerte"}


def carpeta():
    """Donde vive la biblioteca (se crea al guardar el primero)."""
    propia = os.environ.get("ESTUDIO_OBJETOS3D")
    if propia:
        return propia
    banco = os.environ.get("ESTUDIO_BANCO") or os.path.join(RAIZ, "banco")
    return os.path.join(banco, "objetos3d")


def _id(texto):
    return _ID.sub("_", citas.plegar(str(texto or ""))).strip("_")[:30]


def _num(x, lo, hi, defecto=0.0):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return defecto
    if v != v:          # NaN
        return defecto
    return round(max(lo, min(hi, v)), 4)


def _trio(xs, lo, hi, defecto):
    xs = list(xs) if isinstance(xs, (list, tuple)) else []
    xs = (xs + list(defecto))[:3]
    return [_num(x, lo, hi, d) for x, d in zip(xs, defecto)]


def validar(ficha, prohibidas=()):
    """Una ficha limpia ({id, nombre, palabras, piezas}) o None si no sirve.

    Todo número se acota: una pieza de Claude con un tamaño loco no puede
    tapar la Biblia (y además el navegador reescala el conjunto a la mesa).
    """
    if not isinstance(ficha, dict):
        return None
    oid = _id(ficha.get("id") or ficha.get("nombre"))
    if not oid:
        return None
    piezas = []
    for p in (ficha.get("piezas") or [])[:MAX_PIEZAS]:
        if not isinstance(p, dict) or p.get("forma") not in FORMAS:
            continue
        color = str(p.get("color") or "#a0a0a0").strip()
        if not _COLOR.match(color):
            color = "#a0a0a0"
        piezas.append({
            "forma": p["forma"],
            "color": "#" + color.lstrip("#").lower(),
            "pos": _trio(p.get("pos"), -1, 1, (0, 0, 0)),
            "tam": _trio(p.get("tam"), .005, 1, (.1, .1, .1)),
            "rot": _trio(p.get("rot"), -360, 360, (0, 0, 0)),
        })
    if not piezas:
        return None
    vetadas = set(prohibidas) | _VACIAS
    palabras = []
    for w in [oid] + list(ficha.get("palabras") or []):
        w = citas.plegar(str(w))
        if len(w) >= 3 and w not in vetadas and w not in palabras:
            palabras.append(w)
    return {"id": oid, "nombre": str(ficha.get("nombre") or oid)[:40],
            "palabras": palabras[:MAX_PALABRAS], "piezas": piezas}


def biblioteca():
    """{id: ficha} de todo lo construido. Un fichero roto se salta."""
    base, fichas = carpeta(), {}
    if not os.path.isdir(base):
        return fichas
    for nombre in sorted(os.listdir(base)):
        if not nombre.endswith(".json"):
            continue
        try:
            with open(os.path.join(base, nombre), encoding="utf-8") as f:
                ficha = validar(json.load(f))
        except (OSError, ValueError):
            continue
        if ficha:
            fichas[ficha["id"]] = ficha
    return fichas


def guardar(ficha):
    """Escribe la ficha en la biblioteca (atómico). -> ruta"""
    base = carpeta()
    os.makedirs(base, exist_ok=True)
    ruta = os.path.join(base, ficha["id"] + ".json")
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ficha, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ruta)
    return ruta


def palabras(fichas):
    """{palabra plegada: id} de la biblioteca."""
    return {w: k for k, f in fichas.items() for w in f["palabras"]}


# ------------------------------------------------------------------ Claude

INSTRUCCION = """Eres el escenógrafo de un vídeo bíblico hecho en PLASTILINA. Sobre una
mesa, junto a una Biblia abierta, caen objetos pequeños cuando la narración los
nombra. Ya existen estos objetos (NO los construyas otra vez): {conocidos}.

Para cada plano de abajo, di qué OBJETOS FÍSICOS CONCRETOS nombra la narración
y que se puedan poner encima de una mesa como una figurita (una lámpara, un
arpa, una sandalia, un pergamino, una tienda de campaña, un báculo, un altar,
una zarza...). Nada de personas, animales grandes ni lugares enteros
(«Jerusalén», «el desierto»), ni ideas («fe», «pecado»). Como mucho 2 por plano;
si no nombra ninguno, lista vacía. Usa un id de los existentes si encaja.

Para cada objeto NUEVO, constrúyelo con 3 a {max_piezas} piezas de plastilina,
gorditas y de colores mates y cálidos. Formas y su "tam":
- "esfera": [radio_x, radio_y, radio_z]
- "caja": [ancho, alto, fondo]
- "cilindro": [radio_arriba, alto, radio_abajo]
- "cono": [radio, alto, 0]
- "toro" (un aro): [radio, grosor, 0]
- "capsula": [radio, largo, 0]
"pos" = centro de la pieza [x, y, z] (y hacia arriba, el objeto apoyado en
y=0, unos 0,3 de ancho); "rot" = giro en grados [x, y, z]; "color" = "#rrggbb".
"palabras" = cómo puede nombrarlo un guion en español (singular, plural,
sinónimos), en minúsculas.

PLANOS:
{planos}

Contesta SOLO con JSON, sin texto alrededor:
{{"planos": {{"<id del plano>": [{{"id": "lampara", "palabra": "<la palabra tal como sale en la narración>"}}]}},
 "nuevos": [{{"id": "lampara", "nombre": "lámpara", "palabras": ["lampara", "lamparas", "candil"],
   "piezas": [{{"forma": "cilindro", "color": "#b5652f", "pos": [0, .05, 0], "tam": [.1, .1, .12], "rot": [0, 0, 0]}}]}}]}}
"""


def _llamar_claude(instruccion):
    """Se llama así para que el medidor de coste pueda engancharla por nombre."""
    import cli_claude                                   # noqa: PLC0415
    texto, _ = cli_claude.ejecutar(
        instruccion, modelo="sonnet", esfuerzo="low", tiempo_max_s=0,
        base_tiempo_s=180, para="los objetos de plastilina")
    return texto


def _json_de(texto):
    texto = str(texto or "")
    a, b = texto.find("{"), texto.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("Claude no devolvió JSON")
    return json.loads(texto[a:b + 1])


def apagado(p=None):
    if os.environ.get("ESTUDIO_PIEZAS3D", "").lower() in ("no", "0", "false"):
        return True
    modo = (p or {}).get("biblia3d")
    return isinstance(modo, dict) and modo.get("construir") is False


def pedir(textos, conocidos, llamar=None):
    """Una llamada: {sid: texto} -> {"planos": {sid: [{id, palabra}]}, "nuevos": [...]}"""
    planos = "\n".join(f"- {sid}: «{t}»" for sid, t in textos.items())
    instruccion = INSTRUCCION.format(conocidos=", ".join(sorted(conocidos)) or "ninguno",
                                     max_piezas=MAX_PIEZAS, planos=planos)
    datos = _json_de((llamar or _llamar_claude)(instruccion))
    if not isinstance(datos, dict):
        raise ValueError("respuesta sin forma")
    return datos


def detectar(escenas, trabajo, fijas, prohibidas=(), p=None, llamar=None):
    """Lo que Claude ve en cada plano: {sid: [{id, palabra}]}, y la biblioteca al día.

    `escenas`: las del decorado sin objetos puestos a mano. `fijas`: ids hechos
    a mano en biblia3d (no se construyen) y `prohibidas` sus palabras (un
    objeto nuevo no se las quita). Con cache en `trabajo`. Nunca lanza:
    sin Claude devuelve {} y el plano sale con lo de siempre.
    """
    textos = {e["id"]: " ".join(str(e.get("narracion") or "").split())
              for e in escenas if str(e.get("narracion") or "").strip()}
    if not textos or apagado(p):
        return {}
    huella = hashlib.sha1(json.dumps(textos, sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()
    cache = os.path.join(trabajo, "objetos3d.json") if trabajo else None
    if cache and os.path.exists(cache):
        try:
            with open(cache, encoding="utf-8") as f:
                guardado = json.load(f)
            if guardado.get("huella") == huella:
                return guardado.get("planos") or {}
        except (OSError, ValueError):
            pass
    fichas = biblioteca()
    try:
        datos = pedir(textos, set(fijas) | set(fichas), llamar)
    except Exception as e:  # noqa: BLE001
        print(f"[render] objetos de plastilina sin Claude ({str(e)[:120]})", flush=True)
        return {}
    nuevos = []
    for crudo in datos.get("nuevos") or []:
        ficha = validar(crudo, prohibidas)
        if ficha and ficha["id"] not in fijas and ficha["id"] not in fichas:
            guardar(ficha)
            fichas[ficha["id"]] = ficha
            nuevos.append(ficha["id"])
    if nuevos:
        print(f"[render] objetos de plastilina nuevos en la biblioteca: "
              f"{', '.join(nuevos)}", flush=True)
    planos = {}
    for sid, lista in (datos.get("planos") or {}).items():
        if sid not in textos or not isinstance(lista, list):
            continue
        buenos = []
        for o in lista:
            if not isinstance(o, dict):
                continue
            oid = _id(o.get("id"))
            if oid in fijas or oid in fichas:
                buenos.append({"id": oid, "palabra": citas.plegar(str(o.get("palabra") or oid))})
        if buenos:
            planos[sid] = buenos
    if cache:
        try:
            os.makedirs(trabajo, exist_ok=True)
            with open(cache, "w", encoding="utf-8") as f:
                json.dump({"huella": huella, "planos": planos}, f, ensure_ascii=False)
        except OSError:
            pass
    return planos
