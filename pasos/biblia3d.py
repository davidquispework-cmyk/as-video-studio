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

No toca firmas de imágenes: basta «Regenerar Vídeo». Si WebGL no arranca, el
plano sale como siempre (la capa se oculta sola).
"""
import json
import os

import citas
import editorial
import partida
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


def preparar(escenas, p, ancho, alto, imagen_de):
    """El decorado de TODO el vídeo, por plano. -> {id: conf}

    `imagen_de(id)` da la ruta de la imagen del plano (o None). Las tomas se
    reparten en orden de aparición, para que dos planos seguidos no repitan
    cámara.
    """
    modo = conf_de(p)
    if modo is None:
        return {}
    todos = bool(modo.get("todos"))
    confs, n, primero = {}, 0, True
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
        }
        n += 1
    return confs


def resumen(conf):
    if not conf:
        return "sin decorado 3D"
    extra = f", «{conf['cabecera']}»" if conf.get("cabecera") else ""
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
    ren.render(esc, cam);
  }
  return {listo: listo, pintar: pintar};
})();
function biblia3dPintar(t){
  if (!B3) return 1;
  return B3.listo.then(() => { B3.pintar(t); return 1; });
}
"""
