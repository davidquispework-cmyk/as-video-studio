"""
MUÑECOS QUE GESTICULAN (etapa 1 de la hoja de ruta; etapa 3 del plan de animacion).

Un ESTILO OPCIONAL del video: en vez de que los personajes vengan dibujados en
la imagen, la imagen es solo el FONDO y el render pinta encima a cada personaje
como una marioneta geometrica de piezas SVG (cabeza, torso con tunica, brazos
con codo, pies) que se mueve: habla, señala, levanta los brazos, camina,
escucha. Gratis y sin GPU: lo pinta el mismo navegador que ya dibuja cada
fotograma (p8_render.PAGINA), en funcion de `t` y nunca del reloj, asi que el
mismo fotograma sale identico en cualquier lote.

Como se gobierna:
    params del render  "marioneta": True | False (falta = False: el realista)
                       Lo escribe la pantalla al crear el video o en el
                       encargo; NO va en los defectos del paso, para no mover la
                       firma del render de los proyectos que nunca lo tuvieron.
    plan.json, escena  "gesto": "senalar"            para todos los del plano
                       "gesto": {"Pedro": "brazos"}  por personaje
                       "marioneta": false            este plano sin muñecos
Quien sale en cada plano lo dice `escena["personajes"]` (lo decide assets); el
aspecto (color de tunica, barba, velo...) se lee de la ficha del reparto.
"""
import hashlib
import re
import unicodedata

GESTOS = ("hablar", "senalar", "brazos", "caminar", "escuchar")
NOMBRES_GESTO = {"hablar": "habla", "senalar": "señala", "brazos": "levanta los brazos",
                 "caminar": "camina", "escuchar": "escucha"}

# Principios de palabra (sin tildes) que deciden el gesto del que HABLA. El
# orden es la prioridad: levantar los brazos gana a señalar, y señalar a hablar.
PALABRAS_GESTO = (
    ("brazos", ("oro", "oraba", "orar", "oracion", "alab", "gloria", "clam",
                "levant", "bendij", "bendec", "milagro", "celebr", "gozo",
                "alegr", "adora", "grito", "aleluya", "victoria")),
    ("senalar", ("senal", "mostr", "mira", "miren", "ahi", "alli", "aqui",
                 "indic", "apunt", "este es", "esta es", "he aqui")),
    ("caminar", ("camin", "anduv", "viaj", "march", "fue a", "fueron a",
                 "llego", "llegaron", "salio", "salieron", "partio", "huy",
                 "subio", "bajo", "cruz", "recorr", "segu")),
    ("hablar", ("dijo", "dice", "decia", "habl", "pregunt", "respond",
                "contest", "predic", "ensen", "anunc", "proclam", "explic",
                "llamo", "orden", "mand")),
)

COLORES = {   # palabra de la ficha -> color de tela
    "blanc": "#ece6d6", "roj": "#b23a35", "carmes": "#9c2232", "escarlat": "#b8282e",
    "azul": "#3d5f9e", "celest": "#7aa5cf", "verde": "#4f7d4a", "amarill": "#d7b046",
    "dorad": "#c9a043", "marron": "#7a5536", "pard": "#8a6a47", "cafe": "#6f4c33",
    "gris": "#8a8a86", "negr": "#2e2b29", "morad": "#6a3f7c", "purpur": "#6e2c6b",
    "naranj": "#cf7a35", "beige": "#d2bf9a", "crema": "#e4d6b4", "ocre": "#b98a3f",
}
TELAS = ("#7a5536", "#3d5f9e", "#b23a35", "#4f7d4a", "#c9a043", "#6a3f7c",
         "#8a6a47", "#ece6d6")
PIELES = ("#e9c29d", "#d9a87c", "#c48b5e", "#a8704a", "#8a5a3a")


def _plano(texto):
    texto = unicodedata.normalize("NFKD", str(texto or "").lower())
    return " " + "".join(c for c in texto if not unicodedata.combining(c)) + " "


def _numero(texto, n):
    return int(hashlib.sha1(str(texto).encode("utf-8")).hexdigest()[:8], 16) % n


def gesto_de(texto):
    """El gesto de quien habla en un plano, leyendo su narracion. -> GESTOS"""
    t = _plano(texto)
    for gesto, palabras in PALABRAS_GESTO:
        if any(re.search(r"\b" + re.escape(p), t) for p in palabras):
            return gesto
    return "hablar"


def aspecto(nombre, ficha=""):
    """Como se dibuja un personaje, leyendo su ficha del reparto. -> dict"""
    f = _plano(ficha)
    hallados = []
    for palabra, color in COLORES.items():
        i = f.find(palabra)
        if i >= 0:
            hallados.append((i, color))
    hallados.sort()
    tunica = hallados[0][1] if hallados else TELAS[_numero(nombre, len(TELAS))]
    manto = (hallados[1][1] if len(hallados) > 1
             else TELAS[(_numero(nombre, len(TELAS)) + 3) % len(TELAS)])
    mujer = bool(re.search(r"\b(mujer|madre|nina|joven reina|reina|esposa|viuda|"
                           r"hija|hermana|profetisa|ella|woman|girl|queen)\b", f)
                 or re.search(r"\b(maria|marta|sara|rut|ester|ana|eva|rebeca|"
                              r"raquel|lea|debora|lidia|dorcas|tabita|priscila|"
                              r"elisabet|noemi|abigail|betsabe|jezabel)\b",
                              _plano(nombre)))
    nino = bool(re.search(r"\b(nino|nina|muchacho|chico|pequeno|child|boy)\b", f))
    viejo = bool(re.search(r"\b(anciano|viejo|canas|cano|blanca barba|barba blanca|"
                           r"old|elder)\b", f))
    barba = (not mujer and not nino
             and not re.search(r"\b(sin barba|lampino|imberbe|beardless)\b", f))
    pelo = "#d8d4cc" if viejo else ("#2a1d14" if _numero(nombre + "p", 3) else "#4a3020")
    if re.search(r"\b(rubi|rubio|dorado)", f):
        pelo = "#c9a14a"
    angel = bool(re.search(r"\b(angel|gabriel|miguel)\b", f + _plano(nombre)))
    return {"nombre": str(nombre), "tunica": tunica, "manto": manto,
            "piel": PIELES[_numero(nombre + "piel", len(PIELES))], "pelo": pelo,
            "barba": barba and not angel, "mujer": mujer, "nino": nino,
            "angel": angel}


def configurar(escena, fichas=None, maximo=3):
    """Los muñecos de UN plano para la pagina del render. -> dict|None"""
    if escena.get("marioneta") is False:
        return None
    nombres = [n for n in (escena.get("personajes") or []) if n][:maximo]
    if not nombres:
        return None          # un paisaje, un mapa: el plano sale como siempre
    fichas = fichas or {}
    texto = " ".join(str(escena.get(k) or "") for k in ("narracion", "texto"))
    forzado = escena.get("gesto")
    principal = gesto_de(texto)
    figuras = []
    for i, nombre in enumerate(nombres):
        if isinstance(forzado, dict) and forzado.get(nombre) in GESTOS:
            gesto = forzado[nombre]
        elif isinstance(forzado, str) and forzado in GESTOS:
            gesto = forzado
        elif i == 0:
            gesto = principal
        elif principal == "caminar":
            gesto = "caminar"          # caminan juntos
        elif principal == "brazos" and i == 1:
            gesto = "brazos"
        else:
            gesto = "escuchar"
        figuras.append(dict(aspecto(nombre, fichas.get(nombre)), gesto=gesto,
                            habla=(i == 0)))
    return {"figuras": figuras,
            "semilla": _numero(escena.get("id") or texto, 997)}


def resumen(conf):
    """Una linea para el registro: «Pedro señala, Juan escucha»."""
    if not conf:
        return "sin muñecos"
    return ", ".join(f"{f['nombre']} {NOMBRES_GESTO.get(f['gesto'], f['gesto'])}"
                     for f in conf["figuras"])


def html_capa(conf, ancho, alto):
    """El SVG vacio (lo rellena MARIONETA_JS) y su CSS. -> (html, css)"""
    if not conf:
        return "", ""
    html = (f'<svg id="munecos" width="{ancho}" height="{alto}" '
            f'viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg"></svg>')
    css = (f"#munecos{{position:absolute;left:0;top:0;width:{ancho}px;"
           f"height:{alto}px;z-index:1;overflow:visible}}")
    return html, css


# ---------------------------------------------------------- en la pagina
#
# `marionetas(t)` se llama desde `pintar`. Cada muñeco mide 100 unidades de
# alto (los pies en y=100) y se escala al cuadro; los brazos giran sobre el
# hombro y el antebrazo sobre el codo. Angulo 0 = brazo colgando; en el brazo
# derecho (x>0) un angulo NEGATIVO lo abre hacia fuera, en el izquierdo uno
# positivo. Todo depende de t y de la semilla: nada de Math.random.

MARIONETA_JS = r"""
const MSVG = document.getElementById('munecos');
const MNS = 'http://www.w3.org/2000/svg';
function mel(tag, at, padre){
  const e = document.createElementNS(MNS, tag);
  for (const k in at) e.setAttribute(k, at[k]);
  if (padre) padre.appendChild(e);
  return e;
}
const MUN = [];
(function montarMunecos(){
  if (!MSVG || !MAR) return;
  const figs = MAR.figuras, n = figs.length;
  const vertical = H > W;
  const alto = H * (vertical ? 0.34 : 0.46) * (n > 2 ? 0.88 : 1);
  const xs = n === 1 ? [0.5] : (n === 2 ? [0.32, 0.68] : [0.2, 0.5, 0.8]);
  const pie = H * (vertical ? 0.80 : 0.97);
  figs.forEach((f, i) => {
    const esc = alto / 100 * (f.nino ? 0.72 : 1);
    // mira hacia el centro: los de la derecha se dan la vuelta
    const giro = xs[i] > 0.5 ? -1 : 1;
    const raiz = mel('g', {}, MSVG);
    mel('ellipse', {cx: 0, cy: 100, rx: 24, ry: 4, fill: 'rgba(0,0,0,0.28)'}, raiz);
    const cuerpo = mel('g', {}, raiz);
    // pies
    const pieI = mel('ellipse', {cx: -7, cy: 98, rx: 6, ry: 3, fill: '#4a3424'}, cuerpo);
    const pieD = mel('ellipse', {cx: 7, cy: 98, rx: 6, ry: 3, fill: '#4a3424'}, cuerpo);
    // brazo de atras (izquierdo) va detras del torso
    function brazo(lado){
      const hx = 12 * lado, hy = 40;
      const g = mel('g', {}, cuerpo);
      mel('rect', {x: hx - 4, y: hy - 2, width: 8, height: 23, rx: 4, fill: f.tunica,
                   stroke: 'rgba(0,0,0,0.25)', 'stroke-width': 0.8}, g);
      const ante = mel('g', {}, g);
      mel('rect', {x: hx - 3.5, y: hy + 18, width: 7, height: 19, rx: 3.5, fill: f.tunica,
                   stroke: 'rgba(0,0,0,0.25)', 'stroke-width': 0.8}, ante);
      mel('circle', {cx: hx, cy: hy + 38, r: 3.6, fill: f.piel}, ante);
      return {g, ante, hx, hy};
    }
    const bI = brazo(-1);
    // torso: tunica trapecio, cinturon y manto cruzado
    const torso = mel('g', {}, cuerpo);
    if (f.angel){
      mel('path', {d: 'M-10 44 C-40 30 -46 62 -30 80 C-24 66 -16 58 -10 56 Z',
                   fill: 'rgba(255,250,235,0.9)'}, torso);
      mel('path', {d: 'M10 44 C40 30 46 62 30 80 C24 66 16 58 10 56 Z',
                   fill: 'rgba(255,250,235,0.9)'}, torso);
    }
    mel('path', {d: 'M-13 37 L13 37 L21 96 L-21 96 Z', fill: f.tunica,
                 stroke: 'rgba(0,0,0,0.3)', 'stroke-width': 1}, torso);
    mel('path', {d: 'M-13 37 L2 37 L21 90 L12 96 Z', fill: f.manto, opacity: 0.92}, torso);
    mel('rect', {x: -16, y: 60, width: 32, height: 3.5, fill: 'rgba(60,40,25,0.75)'}, torso);
    // cabeza (gira sobre el cuello)
    const cabeza = mel('g', {}, cuerpo);
    mel('rect', {x: -3, y: 31, width: 6, height: 7, fill: f.piel}, cabeza);
    if (f.mujer) mel('path', {d: 'M-14 26 C-15 6 15 6 14 26 L16 44 L-16 44 Z',
                              fill: f.manto}, cabeza);
    mel('circle', {cx: 0, cy: 22, r: 10, fill: f.piel}, cabeza);
    if (f.mujer){
      mel('path', {d: 'M-11 21 C-11 9 11 9 11 21 C8 14 -8 14 -11 21 Z', fill: f.manto}, cabeza);
    } else {
      mel('path', {d: 'M-10.5 21 C-11 10 11 10 10.5 21 C7 15 -7 15 -10.5 21 Z', fill: f.pelo}, cabeza);
      if (f.barba) mel('path', {d: 'M-9 24 C-8 36 8 36 9 24 C5 30 -5 30 -9 24 Z', fill: f.pelo}, cabeza);
    }
    if (f.angel) mel('ellipse', {cx: 0, cy: 8, rx: 9, ry: 2.2, fill: 'none',
                                 stroke: '#f3d77a', 'stroke-width': 1.6}, cabeza);
    const ojos = mel('g', {}, cabeza);
    mel('circle', {cx: -3.6, cy: 21, r: 1.2, fill: '#1d1712'}, ojos);
    mel('circle', {cx: 3.6, cy: 21, r: 1.2, fill: '#1d1712'}, ojos);
    const boca = mel('ellipse', {cx: 0, cy: 27, rx: 2.2, ry: 0.6, fill: '#5a2a22'}, cabeza);
    const bD = brazo(1);   // el de delante, encima del torso
    MUN.push({f, raiz, cuerpo, cabeza, ojos, boca, bI, bD, pieI, pieD, esc, giro,
              x0: xs[i] * W, pie, fase: i * 1.7 + (MAR.semilla % 7) * 0.31});
  });
})();

function rot(el, a, cx, cy){ el.setAttribute('transform',
  'rotate(' + a.toFixed(2) + ' ' + cx + ' ' + cy + ')'); }

function marionetas(t){
  const k = Math.min(1, t / 0.5);          // entra en el gesto, no de golpe
  const kk = k * k * (3 - 2 * k);
  for (const m of MUN){
    const ph = t + m.fase, g = m.f.gesto;
    let hD = -8, cD = -12, hI = 8, cI = 12, cab = Math.sin(ph * 0.9) * 2.5;
    let dx = 0, bob = Math.sin(ph * 2.1) * 0.6, piesA = 0;
    if (g === 'hablar'){
      hD = -28 + Math.sin(ph * 2.3) * 14; cD = -45 + Math.sin(ph * 3.1) * 20;
      hI = 10 + Math.sin(ph * 1.7) * 5;   cI = 20;
      cab = Math.sin(ph * 2.6) * 5;
    } else if (g === 'senalar'){
      hD = -92 + Math.sin(ph * 4) * 3; cD = -6;
      hI = 6; cI = 14; cab = 7 + Math.sin(ph * 1.3) * 2;
    } else if (g === 'brazos'){
      hD = -155 + Math.sin(ph * 2) * 9; cD = -14 + Math.sin(ph * 2.4) * 8;
      hI = 155 - Math.sin(ph * 2 + 0.6) * 9; cI = 14 - Math.sin(ph * 2.4) * 8;
      cab = -8 + Math.sin(ph * 1.5) * 2; bob = Math.sin(ph * 3) * 1.2;
    } else if (g === 'caminar'){
      const paso = Math.sin(ph * 5.2);
      hD = -paso * 22; cD = -10; hI = -paso * 22; cI = 10;
      bob = -Math.abs(Math.cos(ph * 5.2)) * 2.2; piesA = paso;
      dx = t * W * 0.018 * m.giro;            // avanza despacio hacia el centro
    } else {   // escuchar: manos juntas y asiente
      hD = -12; cD = -70; hI = 12; cI = 70;
      cab = 4 + Math.sin(ph * 1.6) * 4;
    }
    rot(m.bD.g, hD * kk, m.bD.hx, m.bD.hy);
    rot(m.bD.ante, cD * kk, m.bD.hx, m.bD.hy + 20);
    rot(m.bI.g, hI * kk, m.bI.hx, m.bI.hy);
    rot(m.bI.ante, cI * kk, m.bI.hx, m.bI.hy + 20);
    rot(m.cabeza, cab, 0, 34);
    m.pieI.setAttribute('transform', 'translate(' + (-piesA * 4).toFixed(2) + ' 0)');
    m.pieD.setAttribute('transform', 'translate(' + (piesA * 4).toFixed(2) + ' 0)');
    const balanceo = Math.sin(ph * 1.1) * 1.2;
    m.cuerpo.setAttribute('transform', 'translate(0 ' + bob.toFixed(2) +
      ') rotate(' + balanceo.toFixed(2) + ' 0 98)');
    // parpadeo cada ~3,7 s, 0,12 s
    const ciclo = (ph * 0.27) % 1;
    m.ojos.setAttribute('transform', ciclo < 0.033
      ? 'translate(0 21) scale(1 0.15) translate(0 -21)' : '');
    // la boca del que habla se abre y se cierra (no sigue la voz: la imita)
    let abre = 0.6;
    if (m.f.habla && g !== 'escuchar'){
      const s = Math.abs(Math.sin(ph * 9.3) * Math.sin(ph * 3.7 + 1));
      abre = 0.6 + s * 2.6;
    }
    m.boca.setAttribute('ry', abre.toFixed(2));
    m.raiz.setAttribute('transform', 'translate(' + (m.x0 + dx).toFixed(1) + ' ' +
      m.pie.toFixed(1) + ') scale(' + (m.esc * m.giro).toFixed(4) + ' ' +
      m.esc.toFixed(4) + ') translate(0 -100)');
  }
}
"""


def solo_fondo(prompt):
    """El prompt de imagen de un video con muñecos: SOLO el sitio, sin gente.

    Los personajes los pone el render encima; si la imagen ya los trae, saldrian
    dos veces. Se quita la lista de «QUIÉN SALE» y se dice bien claro.
    """
    lineas, saltando = [], False
    for linea in str(prompt or "").splitlines():
        if linea.startswith("QUIÉN SALE"):
            saltando = True
            continue
        if saltando and linea.startswith("- "):
            continue
        saltando = False
        if linea.startswith("CONTINUIDAD:"):
            linea = linea.replace(" y aspecto de los personajes", "")
        lineas.append(linea)
    lineas.insert(1, "SOLO EL FONDO: dibuja el lugar SIN NINGUNA persona, animal "
                     "ni personaje (los muñecos se ponen encima después). Deja "
                     "libre la parte de abajo y el centro, con el suelo visible.")
    return "\n".join(lineas)
