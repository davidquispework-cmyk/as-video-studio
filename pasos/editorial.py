"""MODO EDITORIAL (plan NIVEL PROFESIONAL, etapa P5; estilo «Resumario»).

Dos recursos, en una sola capa del render (encima de la imagen y de la
pantalla partida, debajo de los rotulos y del subtitulo):

    titular   en CADA plano, unas pocas palabras de lo que se cuenta (3-6) en
              letra grande con serifa (Playfair), centradas arriba; entran
              palabra a palabra con la voz y UNA va en cursiva de color (el
              nombre propio, la cifra o la palabra mas larga).
    cuadro    cuando la narracion nombra una historia biblica conocida (José y
              sus hermanos, Lázaro, Jonás, la Última Cena...), un CUADRO
              CLÁSICO de dominio publico del Met Museum (Open Access, CC0) con
              su marco y su pie («Rembrandt, 1630»), sobre papel. Cada historia
              una sola vez por video y nunca dos planos seguidos tapados: el
              resto de planos lleva su imagen de siempre.

Los cuadros se buscan y bajan al PREPARAR el render (no en cada fotograma) y se
guardan en `trabajo/cuadros/` con su ficha: volver a montar no sale a internet.
Sin internet, o si el Met no encuentra nada, el plano sale sin cuadro y se dice.

Como se gobierna (no va en los defectos del paso: no mueve firmas):
    params del render  "editorial": true              el modo, en todo el video
                       "editorial": {"cuadros": false}  titulares sin cuadros
    plan.json, escena  "titular": "La túnica de *José*"   a mano (*acento*)
                       "titular": false                  ese plano sin titular
                       "cuadro": "Joseph and his brothers"  busca eso en el Met
                       "cuadro": {"ruta": "C:/…/x.jpg", "pie": "Velázquez, 1630"}
                       "cuadro": false                   ese plano sin cuadro
                       "editorial": false                ese plano sin nada
No va con motion graphics (pinta su propio mundo). En planos con clip de video
sale el titular, no el cuadro.
"""
import json
import os
import re
import urllib.parse
import urllib.request

try:
    import citas
    import rotulos
except ImportError:  # importado como paquete (pasos.editorial)
    from . import citas
    from . import rotulos

LETRA = "Shaddai Playfair"
BUSCAR = "https://collectionapi.metmuseum.org/public/collection/v1.1/search"
OBJETO = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{}"
_AGENTE = {"User-Agent": "estudio-video/1.0"}

# Historias -> busqueda en el Met (en ingles, como estan catalogados). Van de
# lo mas concreto a lo mas general: «la cruz de Jesús» es la Crucifixión, no
# «Christ». Cada entrada: (palabras que la disparan, pares, busqueda).
HISTORIAS = (
    (("crucifixion", "crucificado", "crucificaron", "golgota", "calvario"),
     (), "Crucifixion"),
    (("resurreccion", "resucito"), (("sepulcro", "vacio"),), "Resurrection"),
    ((), (("ultima", "cena"), ("santa", "cena")), "Last Supper"),
    (("lazaro",), (), "Raising of Lazarus"),
    (("jonas",), (), "Jonah"),
    (("noe", "diluvio"), (("el", "arca"),), "Noah"),
    (("babel",), (), "Tower of Babel"),
    (("goliat",), (), "David and Goliath"),
    (("daniel",), (), "Daniel"),
    (("isaac",), (), "Sacrifice of Isaac"),
    (("abraham",), (), "Abraham"),
    (("cain", "abel"), (), "Cain and Abel"),
    (("eden",), (("adan", "y"), ("adan", "eva")), "Adam and Eve"),
    ((), (("jose", "hermanos"), ("tunica", "jose"), ("jose", "egipto"),
          ("jose", "faraon"), ("jose", "suenos")), "Joseph and his brothers"),
    (("moises", "zarza"), (("mar", "rojo"),), "Moses"),
    (("sanson", "dalila"), (), "Samson"),
    (("elias",), (), "Elijah"),
    (("ester",), (), "Esther"),
    (("rut",), (), "Ruth"),
    (("job",), (), "Job"),
    (("salomon",), (), "Solomon"),
    (("judit", "holofernes"), (), "Judith"),
    (("jacob",), (), "Jacob"),
    (("gedeon",), (), "Gideon"),
    (("prodigo",), (), "Prodigal Son"),
    (("samaritano",), (), "Good Samaritan"),
    (("anunciacion",), (), "Annunciation"),
    (("belen", "pesebre", "magos"), (), "Adoration"),
    (("bautista",), (), "Saint John the Baptist"),
    ((), (("bautismo", "jesus"), ("rio", "jordan")), "Baptism of Christ"),
    (("judas",), (), "Judas"),
    (("pedro",), (), "Saint Peter"),
    (("pablo",), (), "Saint Paul"),
    (("apocalipsis",), (), "Apocalypse"),
    (("david",), (), "David"),
)


def tema_de(pl):
    """La busqueda del Met para estas palabras plegadas, o None."""
    juntas = set(pl)
    for sueltas, pares, busqueda in HISTORIAS:
        if juntas & set(sueltas):
            return busqueda
        for a, b in pares:
            if a in juntas and b in juntas:
                return busqueda
    return None


# ------------------------------------------------------------ el titular

_VACIAS = rotulos._VACIAS | {"y", "pero", "porque", "como", "cuando", "se", "lo",
                            "le", "les", "mas", "muy", "ya", "no", "es", "era",
                            "fue", "por", "para", "con", "sin", "este", "esta",
                            "eso", "esto", "aquel", "aquella", "hay"}
_CORTE = tuple(",.;:?!…")
_LIMPIAR = "\"'«»“”‘’()[],.;:…"


def _acento(v, indices):
    """Indice de la palabra que va en cursiva de color."""
    for i in indices:     # un nombre propio que no abre la frase
        c = v.crudas[i].strip(_LIMPIAR + "¿¡")
        if (c[:1].isupper() and i > 0 and not v.crudas[i - 1].endswith(_CORTE)
                and v.pl[i] not in _VACIAS):
            return i
    for i in indices:     # una cifra
        if any(ch.isdigit() for ch in v.crudas[i]):
            return i
    llenas = [i for i in indices if v.pl[i] not in _VACIAS]
    return max(llenas or indices, key=lambda i: len(v.pl[i]))


def titular_auto(v, maximo=6):
    """-> [{"txt", "t", "acento"}] | None. El trozo de frase con la palabra
    clave, de `maximo` palabras como mucho, sin vacias en los bordes."""
    n = len(v.crudas)
    if not n:
        return None
    trozos, actual = [], []
    for i, w in enumerate(v.crudas):
        actual.append(i)
        if w.endswith(_CORTE):
            trozos.append(actual)
            actual = []
    if actual:
        trozos.append(actual)
    acento = _acento(v, list(range(n)))
    trozo = next(t for t in trozos if acento in t)
    if len(trozo) > maximo:
        k = trozo.index(acento)
        ini = max(0, min(k - 2, len(trozo) - maximo))
        trozo = trozo[ini:ini + maximo]
    while len(trozo) > 1 and trozo[-1] != acento and v.pl[trozo[-1]] in _VACIAS:
        trozo = trozo[:-1]
    while len(trozo) > 1 and trozo[0] != acento and v.pl[trozo[0]] in _VACIAS:
        trozo = trozo[1:]
    if len(trozo) < 2:
        return None
    salida = []
    for i in trozo:
        txt = v.crudas[i].strip(_LIMPIAR)
        if txt:
            salida.append({"txt": txt, "t": round(v.t(i), 3), "acento": i == acento})
    return salida or None


def titular_a_mano(v, texto):
    """«La túnica de *José*»: cada palabra entra cuando la voz la dice (si no
    la dice, repartidas en el primer segundo y medio)."""
    palabras = str(texto).split()
    salida, desde = [], 0
    for k, w in enumerate(palabras):
        acento = w.startswith("*") and w.rstrip(_LIMPIAR + "?!").endswith("*")
        txt = w.replace("*", "")
        objetivo = citas.plegar(txt.strip(_LIMPIAR + "¿¡?!"))
        t = None
        for i in range(desde, len(v.pl)):
            if objetivo and v.pl[i] == objetivo:
                t, desde = v.t(i), i + 1
                break
        if t is None:
            t = min(1.5, 0.25 * k)
        salida.append({"txt": txt, "t": round(t, 3), "acento": acento})
    return salida or None


# ------------------------------------------------------------ los cuadros

def _leer(url, tiempo=10):
    pet = urllib.request.Request(url, headers=_AGENTE)
    with urllib.request.urlopen(pet, timeout=tiempo) as r:
        return r.read()


def _pie(ficha):
    autor = re.split(r"\s*[(,]", str(ficha.get("artistDisplayName") or ""))[0].strip()
    if autor.lower() in ("anonymous", "unknown"):
        autor = ""
    fecha = (str(ficha.get("objectDate") or "").strip()
             .replace("ca.", "h.").replace("century", "siglo").replace(" (?)", ""))
    return ", ".join(x for x in (autor or "Anónimo", fecha) if x)


def buscar_cuadro(busqueda, carpeta):
    """Un cuadro de dominio publico del Met para `busqueda`, guardado en
    `carpeta`. -> {"ruta", "pie", "titulo"} | None. Con cache: la segunda vez
    no sale a internet (tampoco si la primera no encontro nada)."""
    os.makedirs(carpeta, exist_ok=True)
    nombre = re.sub(r"[^a-z0-9]+", "_", busqueda.lower()).strip("_") or "cuadro"
    ficha_ruta = os.path.join(carpeta, nombre + ".json")
    if os.path.exists(ficha_ruta):
        with open(ficha_ruta, encoding="utf-8") as f:
            ficha = json.load(f)
        if not ficha.get("ruta"):
            return None
        if os.path.exists(ficha["ruta"]):
            return ficha
    elegido = _elegir(busqueda)
    ficha = {"busqueda": busqueda}
    if elegido:
        ruta = os.path.join(carpeta, nombre + ".jpg")
        _guardar_imagen(_leer(elegido["primaryImage"], 40), ruta)
        ficha.update(ruta=ruta, pie=_pie(elegido),
                     titulo=str(elegido.get("title") or ""),
                     fuente=f"Met Museum, objeto {elegido.get('objectID')} (CC0)")
    with open(ficha_ruta, "w", encoding="utf-8") as f:
        json.dump(ficha, f, ensure_ascii=False, indent=1)
    return ficha if elegido else None


_GENERICAS = {"raising", "of", "the", "and", "his", "sacrifice", "tower",
              "saint", "last", "good", "baptism"}
_CLASES = ("paintings", "drawings", "prints")   # por orden de preferencia


def _clave(busqueda):
    """La palabra que el TITULO del cuadro tiene que llevar («Lazarus»)."""
    for w in busqueda.lower().split():
        if w not in _GENERICAS:
            return w
    return busqueda.lower().split()[-1]


def _elegir(busqueda):
    """Primero las pinturas europeas (departamento 11); si ninguna lleva la
    historia en el titulo, todo el museo, y ahi vale tambien un dibujo o un
    grabado antiguo. Solo dominio publico. -> ficha del Met | None"""
    clave = _clave(busqueda)
    for extra in ({"departmentId": 11}, {}):
        q = urllib.parse.urlencode(dict({"q": busqueda, "hasImages": "true",
                                         "limit": 15}, **extra))
        ids = json.loads(_leer(f"{BUSCAR}?{q}")).get("objectIDs") or []
        mejor, rango = None, len(_CLASES)
        for oid in ids[:15]:
            obj = json.loads(_leer(OBJETO.format(oid)))
            if not obj.get("isPublicDomain") or not obj.get("primaryImage"):
                continue
            if clave not in str(obj.get("title") or "").lower():
                continue
            clase = str(obj.get("classification") or "").lower()
            r = next((k for k, c in enumerate(_CLASES) if c in clase), None)
            if r is not None and r < rango:
                mejor, rango = obj, r
                if r == 0:
                    break
        if mejor:
            return mejor
    return None


def _guardar_imagen(datos, ruta, lado=1600):
    """El original del Met puede pesar 20 MB: se guarda a 1600 px de lado."""
    import io
    from PIL import Image
    img = Image.open(io.BytesIO(datos)).convert("RGB")
    img.thumbnail((lado, lado))
    img.save(ruta, "JPEG", quality=90)


# ------------------------------------------------------------ el video

def conf_de(p):
    """El modo pedido en los params del render: None (apagado) o sus opciones."""
    v = (p or {}).get("editorial")
    if not v:
        return None
    return v if isinstance(v, dict) else {}


def preparar(escenas, p, ancho, alto, carpeta, buscar=buscar_cuadro):
    """La capa de TODO el video, por plano. -> {id: conf}

    Se recorre en orden: cada historia da cuadro una sola vez, y nunca en dos
    planos seguidos (la imagen del plano tambien tiene que verse).
    """
    modo = conf_de(p)
    if modo is None:
        return {}
    con_cuadros = modo.get("cuadros") is not False
    confs, usados, tapado_antes = {}, set(), False
    for e in escenas:
        sid = e.get("id")
        if e.get("cartela") or e.get("editorial") is False:
            tapado_antes = False
            continue
        v = rotulos._Voz(e)
        conf = {}
        propio = e.get("titular")
        if propio is False:
            tit = None
        elif isinstance(propio, str) and propio.strip():
            tit = titular_a_mano(v, propio)
        else:
            tit = titular_auto(v)
        if tit:
            conf["titular"] = tit
        cuadro = None
        manual = e.get("cuadro")
        if isinstance(manual, dict) and manual.get("ruta"):
            if os.path.exists(manual["ruta"]):
                cuadro = {"ruta": manual["ruta"], "pie": str(manual.get("pie") or "")}
        elif manual is not False and con_cuadros:
            busqueda = (manual.strip() if isinstance(manual, str) and manual.strip()
                        else tema_de(v.pl))
            if busqueda and (isinstance(manual, str) or
                             (busqueda not in usados and not tapado_antes)):
                usados.add(busqueda)
                try:
                    cuadro = buscar(busqueda, carpeta)
                except Exception as ex:  # noqa: BLE001 — sin red: sin cuadro
                    print(f"[editorial] {sid}: sin cuadro para «{busqueda}» ({ex})",
                          flush=True)
        if cuadro:
            conf["cuadro"] = {"ruta": cuadro["ruta"], "pie": cuadro.get("pie", "")}
        tapado_antes = bool(cuadro)
        if conf:
            conf.update(W=int(ancho), H=int(alto))
            confs[sid] = conf
    return confs


def sin_cuadro(conf):
    """Para planos con clip de video: el titular si, el cuadro no."""
    if not conf:
        return None
    c = {k: v for k, v in conf.items() if k != "cuadro"}
    return c if c.get("titular") else None


def resumen(conf):
    if not conf:
        return "sin editorial"
    trozos = []
    if conf.get("titular"):
        trozos.append("titular «" + " ".join(w["txt"] for w in conf["titular"]) + "»")
    if conf.get("cuadro"):
        trozos.append(f"cuadro ({conf['cuadro']['pie'] or 'sin pie'})")
    return ", ".join(trozos)


def _url(ruta):
    return "file:///" + os.path.abspath(ruta).replace("\\", "/").lstrip("/")


def json_conf(conf):
    if not conf:
        return ""
    c = dict(conf)
    if c.get("cuadro"):
        c["cuadro"] = dict(c["cuadro"], ruta=_url(c["cuadro"]["ruta"]))
    return json.dumps(c, ensure_ascii=False)


# El grano del papel, el mismo ruido que el tono «papel» de la partida.
_GRANO = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' "
          "width='300' height='300'><filter id='g'><feTurbulence "
          "type='fractalNoise' baseFrequency='.85' numOctaves='3' seed='3'/>"
          "<feColorMatrix values='0 0 0 0 .45 0 0 0 0 .33 0 0 0 0 .18 0 0 0 .35 0'/>"
          "</filter><rect width='300' height='300' filter='url(%23g)'/></svg>")


def css(conf):
    if not conf:
        return ""
    W, H = conf["W"], conf["H"]
    b = min(W, H)
    vertical = H > W
    papel = bool(conf.get("cuadro"))
    tinta = "#2a2118" if papel else "#fff"
    acento = "#8b1e1e" if papel else "#F2C45A"
    sombra = "none" if papel else f"0 {b * .004:.0f}px {b * .02:.0f}px rgba(0,0,0,.75)"
    salida = [
        f"#editorial{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;"
        "z-index:1;pointer-events:none;display:flex;flex-direction:column;"
        f"align-items:center;box-sizing:border-box;padding-top:{H * (.07 if vertical else .06):.0f}px}}",
        f"#ed-tit{{max-width:{W * .86:.0f}px;text-align:center;font-family:'{LETRA}',serif;"
        f"font-size:{b * (.085 if vertical else .075):.0f}px;line-height:1.08;color:{tinta};"
        f"text-shadow:{sombra};letter-spacing:-.01em}}",
        ".ed-p{display:inline-block;opacity:0}",
        f".ed-a{{font-style:italic;color:{acento}}}",
    ]
    if not papel:
        # un velo arriba, para que la letra se lea sobre cualquier imagen
        salida.append(f"#ed-velo{{position:absolute;left:0;top:0;width:{W}px;"
                      f"height:{H * (.34 if vertical else .4):.0f}px;z-index:-1;"
                      "background:linear-gradient(rgba(0,0,0,.55),rgba(0,0,0,0))}")
    else:
        salida += [
            "#editorial{background:#EFE6D2 url(\"" + _GRANO + "\");"
            "background-size:300px 300px;opacity:0}",
            f"#ed-velo{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;"
            "z-index:-1;background:radial-gradient(ellipse at center,"
            "rgba(0,0,0,0) 55%,rgba(92,60,22,.35) 100%)}",
            f"#ed-fig{{margin:{b * .045:.0f}px 0 0;display:flex;flex-direction:column;"
            "align-items:center}",
            f"#ed-marco{{overflow:hidden;border:{b * .012:.0f}px solid #3b2a1a;"
            f"outline:{b * .003:.0f}px solid #b8955a;outline-offset:-{b * .018:.0f}px;"
            f"box-shadow:0 {b * .012:.0f}px {b * .04:.0f}px rgba(40,25,10,.45)}}",
            f"#ed-img{{display:block;max-width:{W * .82:.0f}px;"
            f"max-height:{H * (.38 if vertical else .5):.0f}px;transform-origin:50% 50%}}",
            f"#ed-pie{{margin-top:{b * .018:.0f}px;font-family:'{LETRA}',serif;"
            f"font-style:italic;font-size:{b * .03:.0f}px;color:#5a4630;opacity:0}}",
        ]
    return "\n".join(salida)


def html(conf):
    if not conf:
        return ""
    fig = ""
    if conf.get("cuadro"):
        fig = ('<div id="ed-fig"><div id="ed-marco">'
               f'<img id="ed-img" src="{_url(conf["cuadro"]["ruta"])}"></div>'
               '<div id="ed-pie"></div></div>')
    return f'<div id="editorial"><div id="ed-velo"></div><div id="ed-tit"></div>{fig}</div>'


def js(conf):
    return EDITORIAL_JS if conf else ""


EDITORIAL_JS = r"""
// EL MODO EDITORIAL (pasos/editorial.py, P5): todo sale de `t`, sin reloj de
// pared, asi que el mismo fotograma se pinta igual en cualquier lote.
const edEl = document.getElementById('editorial');
const edTit = document.getElementById('ed-tit');
const edImg = document.getElementById('ed-img'), edPie = document.getElementById('ed-pie');
const edPal = (ED.titular || []).map(w => {
  const s = document.createElement('span');
  s.className = 'ed-p' + (w.acento ? ' ed-a' : '');
  s.textContent = w.txt;
  edTit.appendChild(s); edTit.appendChild(document.createTextNode(' '));
  return s;
});
if (edPie && ED.cuadro) edPie.textContent = ED.cuadro.pie || '';
function edCurva(u){ u = Math.min(1, Math.max(0, u)); return 1 - Math.pow(1 - u, 3); }
function editorialPintar(t){
  if (ED.cuadro){
    edEl.style.opacity = edCurva(t / 0.45).toFixed(4);
    edImg.style.transform = 'scale(' + (1 + 0.06 * Math.min(1, t / Math.max(1, DUR))).toFixed(4) + ')';
    edPie.style.opacity = edCurva((t - 0.6) / 0.5).toFixed(4);
  }
  (ED.titular || []).forEach((w, k) => {
    const e = edCurva((t - w.t) / 0.35);
    edPal[k].style.opacity = e.toFixed(4);
    edPal[k].style.transform = 'translateY(' + ((1 - e) * 0.35).toFixed(3) + 'em)';
  });
}
"""
