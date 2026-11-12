"""El escenario 3D fijo: una Biblia abierta sobre la mesa (P6 del plan NIVEL
PROFESIONAL, estilo «El origen de las cosas»).

Un decorado de verdad en 3D, el MISMO en todos los planos que lo llevan: mesa de
madera, Biblia abierta de tapas granates, cinta roja, y una lámpara de aceite de
barro con su llama (la del logo, Salmo 119:105). Todo con aspecto de PLASTILINA:
materiales mates, bordes redondeados y una huella de dedos muy suave.

En la página DERECHA va la imagen del plano, impresa como una lámina; en la
IZQUIERDA, el libro citado (si se nombra) y 3-6 palabras de lo que se dice, con
letra de libro antiguo. La cámara cambia de toma en cada plano (general, página,
rasante, cenital) y se mueve despacio dentro de él.

Three.js (MIT, `motores/js/three.min.js`, dentro del repo: el render no sale a
internet). Se pinta con WebGL por SOFTWARE (el navegador del render va sin GPU),
y todo sale de `t`: el mismo fotograma se pinta igual en cualquier lote.

QUÉ PLANOS: los que hablan de la Escritura (Biblia, escrito, versículo,
capítulo, profecía…) o nombran un libro (Génesis, Mateo…). Siempre el primero
del vídeo, para que el decorado se presente. A mano, en `plan.json`, escena:
`"biblia3d": true` o `false`. En el render: param `biblia3d: true`, o
`{"todos": true}` (todo el vídeo en el decorado).

OBJETOS DE PLASTILINA (P6b): encima de la mesa, junto a la Biblia, caen los
objetos que nombra la narración del plano —«treinta monedas» → un montón de
monedas, «corona», «piedra», «pan», «peces», «cruz»…— cada uno EN EL MOMENTO
en que se dice la palabra, con un botecito de plastilina al tocar la mesa.
Hasta 3 por plano. A mano, en `plan.json`, escena: `"objetos": ["corona",
"monedas"]` (ids de `OBJETOS`) o `false` (ese plano sin objetos).

CUALQUIER OTRO OBJETO (P6c, `pasos/piezas3d.py`): lo que nombre el guion y no
esté entre esos 18, Claude lo construye con piezas de plastilina y se guarda en
la biblioteca (`banco/objetos3d/`) para la próxima vez. Sus ids también valen
en `"objetos": [...]`.

No toca firmas de imágenes: basta «Regenerar Vídeo». Si WebGL no arranca, el
plano sale como siempre (la capa se oculta sola).
"""
import json
import os

import citas
import editorial
import partida
import piezas3d
import rotulos

THREE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "motores", "js", "three.min.js")
LETRA = editorial.LETRA
TOMAS = ("general", "pagina", "rasante", "cenital")

# Palabras que llevan al decorado (plegadas, sin tildes).
_PALABRAS = {"biblia", "escritura", "escrituras", "escrito", "escrita", "escribio",
             "versiculo", "versiculos", "capitulo", "capitulos", "profecia",
             "profecias", "profeta", "pergamino", "rollo", "rollos", "testamento",
             "evangelio", "evangelios", "salmo", "salmos", "palabra"}


# Objetos que caen en la mesa: palabra plegada (sin tildes) -> id del objeto.
# Cada id tiene su figura en BIBLIA_JS (`HACER`). Solo palabras que no dejan
# duda: «agua» o «mar» no, que salen en cualquier frase.
OBJETOS = {
    "piedra": ("piedra", "piedras", "roca", "rocas", "honda", "apedrearon",
               "apedrear", "lapida"),
    "monedas": ("moneda", "monedas", "plata", "denario", "denarios", "siclos",
                "talento", "talentos", "oro", "ofrenda", "diezmo"),
    "corona": ("corona", "coronas", "coronado", "rey", "reyes", "reina", "trono",
               "reino"),
    "pan": ("pan", "panes", "maná", "mana", "levadura"),
    "pez": ("pez", "peces", "pescado", "pescados", "pescador", "pescadores",
            "ballena", "red", "redes"),
    "cruz": ("cruz", "crucificado", "crucificaron", "crucifixion", "calvario",
             "golgota"),
    "espada": ("espada", "espadas", "batalla", "guerra", "ejercito", "soldado",
               "soldados", "goliat"),
    "cantaro": ("cantaro", "cantaros", "vasija", "vasijas", "tinaja", "tinajas",
                "pozo", "aceite"),
    "copa": ("copa", "caliz", "cena"),
    "llave": ("llave", "llaves", "puerta", "puertas"),
    "fruta": ("fruto", "fruta", "manzana", "higo", "higuera", "eden", "arbol"),
    "corazon": ("corazon", "corazones", "amor", "amaba"),
    "estrella": ("estrella", "estrellas", "magos", "lucero"),
    "barca": ("barca", "barco", "barcas", "arca", "nave", "noe"),
    "cadena": ("cadena", "cadenas", "carcel", "preso", "presos", "prision",
               "esclavo", "esclavos", "esclavitud", "cautivo", "cautiverio"),
    "clavos": ("clavo", "clavos", "clavaron", "clavado"),
    "oveja": ("oveja", "ovejas", "cordero", "corderos", "rebaño", "rebano",
              "pastor", "pastores"),
    "serpiente": ("serpiente", "serpientes", "vibora", "viboras"),
}
_OBJETO_DE = {w: k for k, ws in OBJETOS.items() for w in ws}
MAX_OBJETOS = 3


def objetos_de(escena, v=None, fichas=None, extra=None):
    """Los objetos del plano y cuándo caen: [{"id", "t"}] (t relativo al plano).

    A mano: `"objetos": [...]` en la escena (o `false`, ninguno). Si no, los que
    nombra la narración, en el orden en que se dicen, sin repetir: primero los
    18 hechos a mano, luego los de la biblioteca (`fichas`, P6c) y lo que
    Claude vio en el plano (`extra`: [{id, palabra}]).
    """
    v = v or rotulos._Voz(escena)
    fichas = fichas or {}
    propio = escena.get("objetos")
    if propio is False:
        return []
    if isinstance(propio, (list, tuple)):
        ids = [x for x in dict.fromkeys(piezas3d._id(o) for o in propio)
               if x in OBJETOS or x in fichas][:MAX_OBJETOS]
        paso = min(.6, max(.2, (v.dur - .6) / max(1, len(ids))))
        return [{"id": x, "t": round(.2 + k * paso, 2)} for k, x in enumerate(ids)]
    mapa = dict(piezas3d.palabras(fichas), **_OBJETO_DE)   # los fijos mandan
    vistos = {}
    for i, w in enumerate(v.pl):
        o = mapa.get(w)
        if o and o not in vistos:
            vistos[o] = round(v.t(i), 2)
    for o in extra or ():
        if o["id"] in vistos or not (o["id"] in OBJETOS or o["id"] in fichas):
            continue
        dicho = o.get("palabra") or o["id"]
        i = next((k for k, w in enumerate(v.pl)
                  if w == dicho or (len(dicho) > 3 and w.startswith(dicho[:-1]))), None)
        vistos[o["id"]] = round(v.t(i), 2) if i is not None else .2
    orden = sorted(vistos.items(), key=lambda kv: kv[1])[:MAX_OBJETOS]
    return [{"id": k, "t": t} for k, t in orden]


def conf_de(p):
    """El modo pedido en los params del render: None (apagado) o sus opciones."""
    v = (p or {}).get("biblia3d")
    if not v:
        return None
    return v if isinstance(v, dict) else {}


def pide_decorado(escena):
    """¿La narración del plano habla de la Escritura? -> bool"""
    v = rotulos._Voz(escena)
    if any(w in _PALABRAS for w in v.pl):
        return True
    return bool(partida._libros(v))


def _cabecera(v):
    """«MATEO 26» si se cita, «MATEO» si solo se nombra, o ''."""
    for c in citas.buscar(v.crudas):
        cap = c.get("cap")
        return (c["libro"].upper() + (f" {cap}" if cap else "")).strip()
    libros = partida._libros(v)
    return libros[0] if libros else ""


def preparar(escenas, p, ancho, alto, imagen_de, trabajo=None, llamar=None):
    """El decorado de TODO el vídeo, por plano. -> {id: conf}

    `imagen_de(id)` da la ruta de la imagen del plano (o None). Las tomas se
    reparten en orden de aparición, para que dos planos seguidos no repitan
    cámara. Con `trabajo` (al montar), Claude mira los planos y construye los
    objetos que falten (P6c, una llamada por vídeo, con cache); sin él, solo
    los 18 fijos y la biblioteca.
    """
    modo = conf_de(p)
    if modo is None:
        return {}
    todos = bool(modo.get("todos"))
    fichas = piezas3d.biblioteca()
    confs, n, primero, suyas = {}, 0, True, {}
    for e in escenas:
        sid = e.get("id")
        if e.get("cartela"):
            continue
        propio = e.get("biblia3d")
        if propio is False:
            primero = False
            continue
        if not (propio is True or todos or primero or pide_decorado(e)):
            primero = False
            continue
        primero = False
        img = imagen_de(sid)
        if not img or not os.path.exists(img):
            continue
        v = rotulos._Voz(e)
        tit = editorial.titular_auto(v) or []
        confs[sid] = {
            "W": int(ancho), "H": int(alto), "imagen": img,
            "toma": TOMAS[n % len(TOMAS)],
            "cabecera": _cabecera(v),
            "texto": " ".join(w["txt"] for w in tit),
            "objetos": objetos_de(e, v, fichas),
        }
        suyas[sid] = e
        n += 1
    # P6c: lo que Claude ve en los planos que aún tienen hueco en la mesa
    if trabajo is not None:
        huecos = [e for sid, e in suyas.items() if "objetos" not in e
                  and len(confs[sid]["objetos"]) < MAX_OBJETOS]
        vio = piezas3d.detectar(huecos, trabajo, set(OBJETOS), set(_OBJETO_DE),
                                p, llamar) if huecos else {}
        if vio:
            fichas = piezas3d.biblioteca()
            for sid in vio:
                confs[sid]["objetos"] = objetos_de(suyas[sid], None, fichas, vio[sid])
    for conf in confs.values():
        figuras = {o["id"]: fichas[o["id"]]["piezas"] for o in conf["objetos"]
                   if o["id"] not in OBJETOS and o["id"] in fichas}
        if figuras:
            conf["figuras"] = figuras
    return confs


def resumen(conf):
    if not conf:
        return "sin decorado 3D"
    extra = f", «{conf['cabecera']}»" if conf.get("cabecera") else ""
    if conf.get("objetos"):
        extra += ", con " + ", ".join(o["id"] for o in conf["objetos"])
    return f"Biblia 3D (toma {conf['toma']}{extra})"


def _url(ruta):
    return "file:///" + os.path.abspath(ruta).replace("\\", "/").lstrip("/")


def json_conf(conf):
    if not conf:
        return ""
    return json.dumps(dict(conf, imagen=_url(conf["imagen"])), ensure_ascii=False)


def css(conf):
    if not conf:
        return ""
    # LETRA en el CSS para que pasos/letras.py la declare y la página la cargue:
    # el lienzo la usa para escribir la página izquierda.
    return (f"#biblia3d{{position:absolute;left:0;top:0;width:{conf['W']}px;"
            f"height:{conf['H']}px;z-index:1;pointer-events:none;"
            f"font-family:'{LETRA}',serif}}")


def html(conf):
    if not conf:
        return ""
    return f'<canvas id="biblia3d" width="{conf["W"]}" height="{conf["H"]}"></canvas>'


def js(conf):
    """Three.js por <script src> (no se pega: 650 KB por plano) + el decorado."""
    if not conf:
        return ""
    return ("</script><script src=\"" + _url(THREE) + "\"></script><script>\n"
            + BIBLIA_JS)


BIBLIA_JS = r"""
// EL DECORADO 3D (pasos/biblia3d.py, P6). Todo sale de `t`.
const B3 = (function(){
  const lienzo = document.getElementById('biblia3d');
  let ren;
  try {
    ren = new THREE.WebGLRenderer({canvas: lienzo, antialias: true,
                                   preserveDrawingBuffer: true});
  } catch (e) { lienzo.style.display = 'none'; window.B3_ERROR = String(e); return null; }
  ren.setPixelRatio(1); ren.setSize(E3.W, E3.H, false);
  ren.shadowMap.enabled = true; ren.shadowMap.type = THREE.PCFSoftShadowMap;
  ren.toneMapping = THREE.ACESFilmicToneMapping; ren.toneMappingExposure = 1.05;
  const esc = new THREE.Scene();
  esc.background = new THREE.Color(0x140d08);
  esc.fog = new THREE.Fog(0x140d08, 6, 13);
  const cam = new THREE.PerspectiveCamera(E3.W < E3.H ? 52 : 38, E3.W / E3.H, 0.05, 40);

  // La huella de la plastilina: ruido suave como relieve, el mismo para todo.
  function ruido(lado, semilla, fino){
    const c = document.createElement('canvas'); c.width = c.height = lado;
    const g = c.getContext('2d'); const d = g.createImageData(lado, lado);
    let s = semilla;
    const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
    for (let i = 0; i < d.data.length; i += 4){
      const v = 128 + (r() - .5) * fino;
      d.data[i] = d.data[i+1] = d.data[i+2] = v; d.data[i+3] = 255;
    }
    g.putImageData(d, 0, 0);
    g.globalAlpha = .25; g.filter = 'blur(2px)'; g.drawImage(c, 0, 0);
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
  }
  const huella = ruido(256, 7, 70);
  function barro(color, extra){
    return new THREE.MeshStandardMaterial(Object.assign({color: color, roughness: .88,
      metalness: 0, bumpMap: huella, bumpScale: .012}, extra || {}));
  }
  function caja(w, h, d, mat, r){
    // una caja con los bordes redondeados a mano: la plastilina no tiene aristas
    const f = new THREE.Shape(), a = w/2, b = d/2; r = Math.min(r || .03, a, b);
    f.moveTo(-a + r, -b); f.lineTo(a - r, -b); f.quadraticCurveTo(a, -b, a, -b + r);
    f.lineTo(a, b - r); f.quadraticCurveTo(a, b, a - r, b); f.lineTo(-a + r, b);
    f.quadraticCurveTo(-a, b, -a, b - r); f.lineTo(-a, -b + r);
    f.quadraticCurveTo(-a, -b, -a + r, -b);
    const g = new THREE.ExtrudeGeometry(f, {depth: h, bevelEnabled: true,
      bevelThickness: Math.min(h * .3, .02), bevelSize: .015, bevelSegments: 3,
      curveSegments: 6});
    g.rotateX(-Math.PI / 2); g.translate(0, 0, 0);
    const m = new THREE.Mesh(g, mat); m.castShadow = m.receiveShadow = true; return m;
  }

  // LA MESA: madera con vetas, en plastilina marrón.
  const mc = document.createElement('canvas'); mc.width = 512; mc.height = 512;
  const mg = mc.getContext('2d'); mg.fillStyle = '#7a4a2a'; mg.fillRect(0, 0, 512, 512);
  for (let k = 0; k < 44; k++){
    mg.strokeStyle = 'rgba(' + (k % 3 ? '60,32,16' : '140,92,58') + ',.35)';
    mg.lineWidth = 2 + (k * 7) % 5; mg.beginPath();
    const y = (k * 37) % 512; mg.moveTo(0, y);
    for (let x = 0; x <= 512; x += 32) mg.lineTo(x, y + Math.sin(x / 70 + k) * 6);
    mg.stroke();
  }
  const madera = new THREE.CanvasTexture(mc); madera.colorSpace = THREE.SRGBColorSpace;
  madera.wrapS = madera.wrapT = THREE.RepeatWrapping; madera.repeat.set(3, 3);
  const mesa = new THREE.Mesh(new THREE.PlaneGeometry(30, 20), barro(0xffffff, {map: madera}));
  mesa.rotation.x = -Math.PI / 2; mesa.receiveShadow = true; esc.add(mesa);

  // LA BIBLIA: tapas granates, bloque de hojas y dos páginas curvadas.
  const tapa = barro(0x5e1a1c);
  const hojas = barro(0xeadfc4);
  [-1, 1].forEach(lado => {
    const t = caja(1.12, .035, 1.5, tapa, .05);
    t.position.set(lado * .56, 0, 0); t.rotation.z = lado * -.03; esc.add(t);
    const b = caja(1.02, .1, 1.4, hojas, .02);
    b.position.set(lado * .53, .035, 0); esc.add(b);
  });
  const lomo = new THREE.Mesh(new THREE.CylinderGeometry(.07, .07, 1.5, 16, 1, false, Math.PI, Math.PI), tapa);
  lomo.rotation.x = Math.PI / 2; lomo.position.y = .03; esc.add(lomo);

  // la curva de una hoja abierta: baja hacia el lomo y se aplana hacia fuera
  function hoja(lado, textura){
    const g = new THREE.PlaneGeometry(1.0, 1.36, 48, 1);
    const pos = g.attributes.position;
    for (let i = 0; i < pos.count; i++){
      const x = pos.getX(i) + .5;            // 0 en el lomo, 1 en el borde
      pos.setX(i, lado * (x + .02));
      pos.setZ(i, .07 + .09 * Math.sin(Math.min(1, x * 1.8) * Math.PI / 2) - .015 * x);
    }
    g.computeVertexNormals();
    // se pinta en el plano XZ: Z de la geometria es la altura
    g.rotateX(-Math.PI / 2);
    if (lado < 0){ const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setX(i, 1 - uv.getX(i)); }
    const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({map: textura,
      roughness: .92, metalness: 0,
      side: THREE.DoubleSide}));
    m.position.y = .05; m.receiveShadow = true; m.castShadow = true; esc.add(m);
    return m;
  }
  function papel(){
    const c = document.createElement('canvas'); c.width = 900; c.height = 1224;
    const g = c.getContext('2d');
    const gr = g.createRadialGradient(450, 612, 200, 450, 612, 820);
    gr.addColorStop(0, '#f3ead3'); gr.addColorStop(1, '#d9c69c');
    g.fillStyle = gr; g.fillRect(0, 0, 900, 1224);
    return [c, g];
  }
  const [cd, gd] = papel(), [ci, gi] = papel();
  const texD = new THREE.CanvasTexture(cd), texI = new THREE.CanvasTexture(ci);
  texD.colorSpace = texI.colorSpace = THREE.SRGBColorSpace;
  texD.anisotropy = texI.anisotropy = 4;
  hoja(1, texD); hoja(-1, texI);

  // la cinta roja, cayendo por el borde de abajo junto al lomo
  // la cinta: tumbada junto al lomo y colgando por el canto de abajo
  const rojo = barro(0xa3161c, {side: THREE.DoubleSide});
  const cinta = new THREE.Mesh(new THREE.PlaneGeometry(.05, .55), rojo);
  cinta.rotation.x = -Math.PI / 2; cinta.position.set(.07, .128, .42); esc.add(cinta);
  const cuelga = new THREE.Mesh(new THREE.PlaneGeometry(.05, .13), rojo);
  cuelga.position.set(.07, .065, .7); esc.add(cuelga);
  const suelo = new THREE.Mesh(new THREE.PlaneGeometry(.05, .3), rojo);
  suelo.rotation.x = -Math.PI / 2; suelo.position.set(.07, .004, .85); esc.add(suelo);

  // LA LAMPARA DE ACEITE de barro (la del logo), con su llama
  const perfil = [[0,0],[.16,.01],[.22,.05],[.2,.1],[.12,.13],[.05,.14],[.04,.16],[0,.16]]
    .map(p => new THREE.Vector2(p[0], p[1]));
  const lampara = new THREE.Mesh(new THREE.LatheGeometry(perfil, 32), barro(0xb5652f));
  lampara.castShadow = true; lampara.position.set(1.3, 0, -.5); esc.add(lampara);
  const pico = caja(.12, .05, .26, barro(0xb5652f), .04);
  pico.position.set(1.3, .07, -.28); esc.add(pico);
  const llama = new THREE.Mesh(new THREE.ConeGeometry(.035, .14, 16),
    new THREE.MeshBasicMaterial({color: 0xffc35a}));
  llama.position.set(1.3, .2, -.17); esc.add(llama);
  const luzLlama = new THREE.PointLight(0xffa64a, 2.2, 4, 1.6);
  luzLlama.position.set(1.3, .35, -.15); esc.add(luzLlama);


  // LOS OBJETOS DE PLASTILINA (P6b): figuras sencillas y gorditas, una por id
  // de biblia3d.OBJETOS. Cada una mide unos 0,3 de ancho y se apoya en y=0.
  function grupo(){ return new THREE.Group(); }
  function pon(g, geo, mat, x, y, z){
    const m = new THREE.Mesh(geo, mat); m.position.set(x || 0, y || 0, z || 0);
    g.add(m); return m;
  }
  function torno(puntos, mat){
    return new THREE.Mesh(new THREE.LatheGeometry(puntos.map(p => new THREE.Vector2(p[0], p[1])), 28), mat);
  }
  const HACER = {
    piedra(){ const g = grupo(), m = barro(0x8d877e);
      [[0,.07,0,.1],[.13,.05,.05,.07],[-.1,.045,.07,.06]].forEach(p => {
        const s = pon(g, new THREE.IcosahedronGeometry(p[3], 1), m, p[0], p[1], p[2]);
        s.scale.set(1.2, .75, 1); s.rotation.y = p[0] * 9; });
      return g; },
    monedas(){ const g = grupo(), m = barro(0xd8a83a);
      const geo = new THREE.CylinderGeometry(.065, .065, .018, 28);
      for (let k = 0; k < 6; k++) pon(g, geo, m, Math.sin(k * 2.1) * .015, .01 + k * .019, Math.cos(k * 1.7) * .015);
      [[.13,.03],[-.11,.1],[.06,-.12]].forEach(p => {
        const c = pon(g, geo, m, p[0], .01, p[1]); c.rotation.z = .08; });
      return g; },
    corona(){ const g = grupo(), oro = barro(0xd9a93b, {side: THREE.DoubleSide}), rojo = barro(0xb3202a);
      pon(g, new THREE.CylinderGeometry(.13, .12, .08, 28, 1, true), oro, 0, .04, 0);
      pon(g, new THREE.TorusGeometry(.125, .015, 8, 28), oro, 0, .005, 0).rotation.x = Math.PI / 2;
      for (let k = 0; k < 6; k++){
        const a = k / 6 * Math.PI * 2;
        pon(g, new THREE.ConeGeometry(.03, .07, 10), oro, Math.cos(a) * .125, .115, Math.sin(a) * .125);
        pon(g, new THREE.SphereGeometry(.015, 10, 8), rojo, Math.cos(a) * .125, .155, Math.sin(a) * .125);
      }
      return g; },
    pan(){ const g = grupo(), m = barro(0xc68642), raya = barro(0x8a5a2b);
      pon(g, new THREE.SphereGeometry(.12, 24, 16), m, 0, .055, 0).scale.set(1.5, .55, 1);
      [-.06, 0, .06].forEach(x => { const r = pon(g, new THREE.BoxGeometry(.012, .02, .14), raya, x, .118, 0); r.rotation.y = .5; });
      return g; },
    pez(){ const g = grupo(), m = barro(0x6f93ad), ojo = barro(0x111111);
      pon(g, new THREE.SphereGeometry(.09, 24, 16), m, 0, .055, 0).scale.set(1.7, .65, .75);
      const c = pon(g, new THREE.ConeGeometry(.07, .1, 3), m, -.19, .055, 0);
      c.rotation.z = Math.PI / 2; c.scale.set(1, 1, .4);
      pon(g, new THREE.SphereGeometry(.014, 10, 8), ojo, .1, .075, .05);
      return g; },
    cruz(){ const g = grupo(), m = barro(0x6b4426);
      g.add(caja(.05, .5, .05, m, .015));
      const b = caja(.26, .05, .05, m, .015); b.position.y = .33; g.add(b);
      pon(g, new THREE.SphereGeometry(.08, 18, 10, 0, Math.PI * 2, 0, Math.PI / 2), barro(0x7d6a55));
      return g; },
    espada(){ const g = grupo(), hoja = barro(0xb9bec4), mango = barro(0x5a3a20), oro = barro(0xd9a93b);
      const h = caja(.04, .015, .42, hoja, .012); h.position.set(0, .012, -.1); g.add(h);
      const gu = caja(.16, .025, .03, oro, .01); gu.position.set(0, .012, .12); g.add(gu);
      const ma = caja(.03, .025, .11, mango, .012); ma.position.set(0, .012, .19); g.add(ma);
      pon(g, new THREE.SphereGeometry(.022, 12, 8), oro, 0, .022, .255);
      g.rotation.y = .9; return g; },
    cantaro(){ const g = grupo(), m = barro(0x9c4f26);
      g.add(torno([[0,0],[.07,0],[.12,.07],[.13,.13],[.09,.2],[.05,.24],[.06,.28],[0,.28]], m));
      const a = pon(g, new THREE.TorusGeometry(.055, .014, 8, 16, Math.PI), m, .1, .2, 0);
      a.rotation.z = -Math.PI / 2;
      return g; },
    copa(){ const g = grupo(), m = barro(0xcfa13c, {side: THREE.DoubleSide});
      g.add(torno([[0,0],[.08,0],[.08,.015],[.02,.03],[.015,.12],[.04,.14],[.09,.2],[.095,.27],[.085,.27],[.0,.17]], m));
      return g; },
    llave(){ const g = grupo(), m = barro(0xc29a3a);
      pon(g, new THREE.TorusGeometry(.06, .02, 10, 22), m, -.14, .02, 0).rotation.x = Math.PI / 2;
      const v = caja(.24, .03, .03, m, .01); v.position.set(.03, .005, 0); g.add(v);
      [.1, .14].forEach(x => { const d = caja(.025, .03, .06, m, .008); d.position.set(x, .005, .035); g.add(d); });
      g.rotation.y = -.6; return g; },
    fruta(){ const g = grupo();
      pon(g, new THREE.SphereGeometry(.1, 24, 16), barro(0xb8262b), 0, .095, 0).scale.set(1, .92, 1);
      pon(g, new THREE.CylinderGeometry(.008, .01, .06, 8), barro(0x5a3a20), 0, .2, 0);
      const h = pon(g, new THREE.SphereGeometry(.04, 12, 8), barro(0x4f8a2e), .035, .21, 0);
      h.scale.set(1, .25, .55); h.rotation.z = .5;
      return g; },
    corazon(){ const g = grupo(), m = barro(0xc0222e);
      pon(g, new THREE.SphereGeometry(.07, 20, 14), m, -.055, .17, 0);
      pon(g, new THREE.SphereGeometry(.07, 20, 14), m, .055, .17, 0);
      const c = pon(g, new THREE.ConeGeometry(.115, .17, 24), m, 0, .08, 0); c.rotation.z = Math.PI;
      g.scale.z = .7; return g; },
    estrella(){ const g = grupo(), f = new THREE.Shape();
      for (let k = 0; k < 10; k++){
        const r = k % 2 ? .055 : .13, a = k / 10 * Math.PI * 2 + Math.PI / 2;
        k ? f.lineTo(Math.cos(a) * r, Math.sin(a) * r) : f.moveTo(Math.cos(a) * r, Math.sin(a) * r);
      }
      const geo = new THREE.ExtrudeGeometry(f, {depth: .03, bevelEnabled: true, bevelThickness: .012,
        bevelSize: .012, bevelSegments: 3});
      geo.rotateX(-Math.PI / 2);
      pon(g, geo, barro(0xe7b53c), 0, .012, 0);
      return g; },
    barca(){ const g = grupo(), m = barro(0x7a4a26, {side: THREE.DoubleSide});
      const c = pon(g, new THREE.SphereGeometry(.12, 24, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), m, 0, .085, 0);
      c.scale.set(2, .7, .85);
      pon(g, new THREE.CylinderGeometry(.008, .008, .26, 8), m, 0, .2, 0);
      const vela = new THREE.Shape(); vela.moveTo(0, 0); vela.lineTo(.13, 0); vela.lineTo(0, .2);
      pon(g, new THREE.ShapeGeometry(vela), barro(0xefe4c8, {side: THREE.DoubleSide}), .01, .1, 0);
      return g; },
    cadena(){ const g = grupo(), m = barro(0x77787c);
      for (let k = 0; k < 5; k++){
        const e = pon(g, new THREE.TorusGeometry(.035, .012, 8, 16), m, -.16 + k * .075, .03, 0);
        e.scale.x = 1.5;
        if (k % 2){ e.rotation.x = Math.PI / 2; e.position.y = .013; }
      }
      g.rotation.y = .4; return g; },
    clavos(){ const g = grupo(), m = barro(0x55565a);
      [[0,0,0],[.05,.07,.7],[-.06,-.06,-.5]].forEach(p => {
        const c = grupo();
        pon(c, new THREE.CylinderGeometry(.012, .004, .22, 8), m).rotation.z = Math.PI / 2;
        pon(c, new THREE.CylinderGeometry(.03, .03, .012, 14), m, -.11, 0, 0).rotation.z = Math.PI / 2;
        c.position.set(p[0], .016, p[1]); c.rotation.y = p[2]; g.add(c);
      });
      return g; },
    oveja(){ const g = grupo(), lana = barro(0xf1ece0), negro = barro(0x2a2522);
      [[-.06,0],[.06,0]].forEach(p => [-1, 1].forEach(l =>
        pon(g, new THREE.CylinderGeometry(.014, .014, .08, 8), negro, p[0], .04, l * .04)));
      pon(g, new THREE.SphereGeometry(.09, 20, 14), lana, 0, .12, 0).scale.set(1.35, .9, .95);
      for (let k = 0; k < 7; k++)
        pon(g, new THREE.SphereGeometry(.045, 12, 8), lana, Math.cos(k) * .09, .17 + (k % 2) * .02, Math.sin(k * 1.3) * .05);
      pon(g, new THREE.SphereGeometry(.045, 16, 10), negro, .13, .15, 0).scale.set(1.2, .9, .85);
      return g; },
    serpiente(){ const g = grupo(), m = barro(0x4d7a2e);
      const curva = new THREE.CatmullRomCurve3([[-.2,.03,-.06],[-.1,.03,.08],[0,.03,-.06],[.1,.03,.07],[.18,.05,0],[.2,.1,-.02]]
        .map(p => new THREE.Vector3(p[0], p[1], p[2])));
      g.add(new THREE.Mesh(new THREE.TubeGeometry(curva, 48, .026, 10, false), m));
      pon(g, new THREE.SphereGeometry(.038, 14, 10), m, .205, .115, -.02).scale.set(1.4, .8, 1);
      pon(g, new THREE.SphereGeometry(.026, 12, 8), m, -.2, .03, -.06);
      return g; },
  };
  // Los huecos de la mesa: en vertical, delante del libro (a los lados no se
  // ve); en horizontal, a izquierda y derecha. La lampara esta en (1.3, -.5).
  const HUECOS = E3.W < E3.H
    ? [[-.6, 1.08, .3], [.6, 1.1, -.4], [-.05, 1.42, .1]]
    : [[-1.36, .22, .3], [1.38, .3, -.4], [-1.38, -.62, .2]];
  const TAM = E3.W < E3.H ? 1.1 : 1.3;
  // P6c: los objetos que construyo Claude (pasos/piezas3d.py), pieza a pieza.
  // Se escalan a la medida de la mesa (unos 0,32) y se apoyan en y=0, digan
  // lo que digan sus numeros.
  function armar(piezas){
    const g = grupo(), R = Math.PI / 180;
    piezas.forEach(p => {
      const t = p.tam || [.1, .1, .1], m = barro(new THREE.Color(p.color).getHex());
      let geo, mesh;
      if (p.forma === 'caja'){ mesh = caja(t[0], t[1], t[2], m, Math.min(t[0], t[1], t[2]) / 4); mesh.position.y = -t[1] / 2; }
      else {
        if (p.forma === 'esfera') geo = new THREE.SphereGeometry(1, 20, 14);
        else if (p.forma === 'cilindro') geo = new THREE.CylinderGeometry(t[0], t[2] || t[0], t[1], 24);
        else if (p.forma === 'cono') geo = new THREE.ConeGeometry(t[0], t[1], 20);
        else if (p.forma === 'toro') geo = new THREE.TorusGeometry(t[0], t[1], 10, 24);
        else geo = new THREE.CapsuleGeometry(t[0], t[1], 6, 14);
        mesh = new THREE.Mesh(geo, m);
        if (p.forma === 'esfera') mesh.scale.set(t[0], t[1], t[2]);
      }
      const pieza = grupo(); pieza.add(mesh);
      const q = p.pos || [0, 0, 0], r = p.rot || [0, 0, 0];
      pieza.position.set(q[0], q[1], q[2]); pieza.rotation.set(r[0] * R, r[1] * R, r[2] * R);
      g.add(pieza);
    });
    const caja3 = new THREE.Box3().setFromObject(g), tam = caja3.getSize(new THREE.Vector3());
    const s = .32 / Math.max(tam.x, tam.z, tam.y * .8, .01), centro = caja3.getCenter(new THREE.Vector3());
    const fuera = grupo(); fuera.add(g);
    g.position.set(-centro.x, -caja3.min.y, -centro.z); fuera.scale.setScalar(s);
    return fuera;
  }
  const FIGURAS = E3.figuras || {};
  const hacer = id => HACER[id] ? HACER[id]() : (FIGURAS[id] ? armar(FIGURAS[id]) : null);
  const caen = (E3.objetos || []).filter(o => HACER[o.id] || FIGURAS[o.id]).slice(0, HUECOS.length).map((o, k) => {
    const g = hacer(o.id), h = HUECOS[k];
    g.traverse(m => { if (m.isMesh){ m.castShadow = true; m.receiveShadow = true; } });
    const quieto = grupo(); quieto.add(g);
    quieto.position.set(h[0], 0, h[1]); quieto.rotation.y += h[2];
    quieto.visible = false; esc.add(quieto);
    return {g: quieto, t: +o.t || 0};
  });
  // cae desde arriba y, al tocar la mesa, se aplasta y rebota como plastilina
  function caer(t){
    caen.forEach(o => {
      const k = (t - o.t) / .4;
      o.g.visible = k >= 0;
      if (k < 0) return;
      if (k < 1){ o.g.position.y = .55 * (1 - k * k); o.g.scale.setScalar(TAM); return; }
      const s = .2 * Math.exp(-(k - 1) * 5) * Math.cos((k - 1) * 13);
      o.g.position.y = 0; o.g.scale.set(TAM * (1 + s * .6), TAM * (1 - s), TAM * (1 + s * .6));
    });
  }

  esc.add(new THREE.HemisphereLight(0xffe9c8, 0x2a1a10, .9));
  const sol = new THREE.DirectionalLight(0xfff0d6, 2.1);
  sol.position.set(-2.5, 4, 2.2); sol.castShadow = true;
  sol.shadow.mapSize.set(1024, 1024); sol.shadow.radius = 5;
  sol.shadow.camera.left = sol.shadow.camera.bottom = -3;
  sol.shadow.camera.right = sol.shadow.camera.top = 3;
  esc.add(sol);

  // LAS PAGINAS se escriben cuando la letra ya esta (abrir espera a LETRAS_OK)
  // y la imagen ya se decodifico: por eso `pintar` devuelve esta promesa.
  function escribir(img){
    gd.save();
    const mx = 70, ancho = 900 - 2 * mx;
    let w = ancho, h = w * img.naturalHeight / Math.max(1, img.naturalWidth);
    if (h > 900){ h = 900; w = h * img.naturalWidth / img.naturalHeight; }
    const x = (900 - w) / 2, y = (1224 - h) / 2 - 20;
    gd.fillStyle = 'rgba(70,45,20,.25)'; gd.fillRect(x - 14, y - 14, w + 28, h + 28);
    gd.globalAlpha = .93; gd.drawImage(img, x, y, w, h); gd.restore();
    gd.strokeStyle = '#6b4a28'; gd.lineWidth = 4; gd.strokeRect(x - 8, y - 8, w + 16, h + 16);
    texD.needsUpdate = true;

    const L = "'" + getComputedStyle(lienzo).fontFamily.split(',')[0].replace(/['"]/g, '') + "',serif";
    gi.textAlign = 'center'; gi.fillStyle = '#5e1a1c';
    if (E3.cabecera){
      gi.font = '600 64px ' + L; gi.fillText(E3.cabecera, 450, 220);
      gi.fillRect(330, 250, 240, 4);
    }
    gi.fillStyle = '#2a2118'; gi.font = 'italic 72px ' + L;
    const palabras = (E3.texto || '').split(/\s+/).filter(Boolean);
    const lineas = []; let linea = '';
    palabras.forEach(p => {
      const prueba = linea ? linea + ' ' + p : p;
      if (gi.measureText(prueba).width > 700 && linea){ lineas.push(linea); linea = p; }
      else linea = prueba;
    });
    if (linea) lineas.push(linea);
    const y0 = 612 - (lineas.length - 1) * 48;
    lineas.forEach((l, k) => gi.fillText(l, 450, y0 + k * 96));
    // renglones grises, como un texto de fondo que no se lee
    gi.fillStyle = 'rgba(60,40,20,.13)';
    for (let k = 0; k < 9; k++) gi.fillRect(110, 860 + k * 34, 680 - (k % 3) * 60, 10);
    texI.needsUpdate = true;
  }
  const img = new Image();
  const listo = new Promise(r => { img.onload = r; img.onerror = r; })
    .then(() => img.decode ? img.decode().catch(() => 0) : 0)
    .then(() => { if (img.naturalWidth) escribir(img); });
  img.src = E3.imagen;

  // LAS TOMAS: [posicion, mira] al empezar y al acabar el plano.
  // En vertical la camara sube mas que se aleja: mirando mas hacia abajo la
  // mesa llena el cuadro y no asoma el fondo negro por arriba.
  const vy = E3.W < E3.H ? 1.6 : 1, vz = E3.W < E3.H ? 1.05 : 1;
  const TOMAS = {
    general: [[0, 2.3*vy, 2.6*vz], [0, .1, 0], [0, 1.9*vy, 2.0*vz], [0, .1, -.05]],
    pagina:  [[.75, 1.25*vy, 1.05*vz], [.55, .12, 0], [.6, 1.05*vy, .85*vz], [.55, .12, -.05]],
    rasante: [[-1.9*vz, .45*vy, 1.6*vz], [.2, .15, 0], [-1.3*vz, .5*vy, 1.9*vz], [.35, .15, 0]],
    cenital: [[.05, 2.9*vy, .25], [0, 0, 0], [-.05, 2.5*vy, .2], [0, 0, 0]],
  };
  const toma = TOMAS[E3.toma] || TOMAS.general;
  const P = new THREE.Vector3(), M = new THREE.Vector3();
  function lerp(a, b, e, out){ return out.set(a[0]+(b[0]-a[0])*e, a[1]+(b[1]-a[1])*e, a[2]+(b[2]-a[2])*e); }
  function pintar(t){
    const u = DUR > 0 ? Math.min(1, Math.max(0, t / DUR)) : 0;
    const e = u * u * (3 - 2 * u);
    cam.position.copy(lerp(toma[0], toma[2], e, P));
    cam.lookAt(lerp(toma[1], toma[3], e, M));
    const f = 1 + .12 * Math.sin(t * 9.1) + .07 * Math.sin(t * 23.3);
    llama.scale.set(1, f, 1); luzLlama.intensity = 2.2 * f;
    caer(t);
    ren.render(esc, cam);
  }
  return {listo: listo, pintar: pintar};
})();
function biblia3dPintar(t){
  if (!B3) return 1;
  return B3.listo.then(() => { B3.pintar(t); return 1; });
}
"""
