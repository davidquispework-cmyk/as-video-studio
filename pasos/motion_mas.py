"""
MOTION GRAPHICS, segunda parte (punto G de NOTAS-DAVID.md): lo que se suma al
mundo de `pasos/motion.py` sin tocar su motor.

    figuras     MUÑECOS PLANOS PROPIOS dentro del mundo: cabeza grande, túnica
                en campana, colores lisos del reparto (pasos/marioneta.aspecto)
                y caras MUY expresivas (alegría, sorpresa, miedo, tristeza,
                enfado). Se mueven pieza a pieza: brazos con codo, parpadeo,
                cabeza que asiente, caminar, arrodillarse, saltar, asustarse,
                girar, pensar... y la BOCA SIGUE LA VOZ: se abre en cada
                palabra que dice quien habla (tiempos de `escena["marcas"]`).
    piezas      barras (porcentajes y cantidades), antes/después (cortina que
                barre), árbol genealógico, flecha que señala y círculo a mano.
    iconos      diez más para las metáforas: bola con cadena, corazón roto,
                bombilla, rayo, semilla, candado, regalo, mundo, escalera, muro.
    sonido      «whoosh» en cada viaje de cámara y «pop» en cada pieza que
                aterriza: sintéticos (sin clave de FreeSound), siempre iguales.

Nada de esto es un param nuevo en los defectos: vive dentro del param `motion`
del render (ver motion.py), así que no mueve la firma de ningún proyecto.
"""
import hashlib
import math
import re

try:
    import fidelidad
    import marioneta
except ImportError:  # importado como paquete (pasos.motion_mas)
    from . import fidelidad, marioneta

GESTOS = ("presentar", "hablar", "senalar", "brazos", "caminar", "escuchar",
          "arrodillarse", "saltar", "asustarse", "girar", "pensar")
EXPRESIONES = ("neutra", "alegria", "sorpresa", "miedo", "tristeza", "enojo")
ICONOS_MAS = ("bola", "corazon_roto", "bombilla", "rayo", "semilla", "candado",
              "regalo", "mundo", "escalera", "muro")

# palabra (plegada, principio) -> expresion de la cara
PALABRAS_EXPRESION = (
    ("miedo", ("miedo", "temor", "temia", "temian", "asust", "terror", "tembl",
               "panico", "angusti", "espant", "aterr")),
    ("tristeza", ("llor", "triste", "lament", "dolor", "sufr", "luto", "murio",
                  "muerte", "perdio", "abandon", "soledad")),
    ("enojo", ("ira", "enoj", "furi", "odi", "rabia", "celos", "envidi", "indign")),
    ("sorpresa", ("sabias", "increible", "asombr", "sorpr", "milagro", "de repente",
                  "nadie esperaba", "maravill", "atonit", "imagina")),
    ("alegria", ("alegr", "gozo", "feliz", "celebr", "fiesta", "gloria", "alab",
                 "cant", "sonri", "bendic", "gracias", "victoria", "salv")),
)
# palabra -> gesto propio de las figuras planas (antes que los de marioneta)
PALABRAS_GESTO = (
    ("arrodillarse", ("arrodill", "postr", "de rodillas", "adoro", "adoraron",
                      "se inclino", "oro ", "oraba", "orando", "rezo", "rezaba")),
    ("saltar", ("salt", "danz", "celebr", "gozo", "alegr")),
    ("asustarse", ("miedo", "temor", "asust", "terror", "tembl", "espant")),
    ("girar", ("se volvio", "se giro", "dio la vuelta", "volviendose", "miro atras")),
    ("pensar", ("penso", "pensaba", "medit", "se pregunt", "dudo", "dudaba",
                "imagina", "reflexion")),
)
VERBOS_HABLA = ("dijo", "dice", "hablo", "habla", "respondio", "pregunto", "clamo",
                "grito", "exclamo", "decia", "contesto", "ordeno", "anuncio",
                "predico", "enseno", "declaro")


def _pl(texto):
    return " " + fidelidad.plegar(texto) + " "


def _numero(texto, n):
    return int(hashlib.sha1(str(texto).encode("utf-8")).hexdigest()[:8], 16) % n


def expresion_de(texto):
    t = _pl(texto)
    for expr, formas in PALABRAS_EXPRESION:
        if any(re.search(r"\s" + re.escape(f), t) for f in formas):
            return expr
    return "neutra"


def gesto_de(texto):
    """El gesto de la figura principal leyendo la frase. -> GESTOS"""
    t = _pl(texto)
    for gesto, formas in PALABRAS_GESTO:
        if any(re.search(r"\s" + re.escape(f), t) for f in formas):
            return gesto
    g = marioneta.gesto_de(texto)
    if g == "hablar":
        # marioneta da «hablar» cuando no encuentra nada: aqui solo habla
        # quien de verdad dice algo; si no, presenta lo que se cuenta
        return "hablar" if any(f" {v} " in t for v in VERBOS_HABLA) else "presentar"
    return g


def _silabas(palabra):
    return max(1, len(re.findall(r"[aeiouáéíóúü]+", str(palabra).lower())))


def figuras(voz, nombres, fichas, gesto=None, expresion=None, mira=1):
    """Las figuras de un plano. `voz` es motion.Voz. -> [dict]"""
    nombres = [str(n) for n in (nombres or []) if str(n or "").strip()][:3]
    if not nombres:
        return []
    texto = " ".join(voz.crudas)
    principal = gesto if gesto in GESTOS else gesto_de(texto)
    expr = expresion if expresion in EXPRESIONES else expresion_de(texto)
    # LA BOCA SIGUE LA VOZ: quien habla mueve la boca en cada palabra que se
    # dice DESPUES del verbo («Pedro dijo: ...»), con una abertura por silaba
    habla = []
    if principal == "hablar":
        desde = 0
        for k, pl in enumerate(voz.plegadas):
            if pl in VERBOS_HABLA:
                desde = k + 1
                break
        for k in range(desde, len(voz.crudas)):
            a, b = voz.tiempos[k]
            habla.append([round(a, 3), round(b, 3), _silabas(voz.crudas[k])])
    plano = _pl(texto)
    salida = []
    for k, nombre in enumerate(nombres):
        aspecto = marioneta.aspecto(nombre, (fichas or {}).get(nombre, ""))
        if k == 0:
            g = principal
        elif principal in ("caminar", "brazos", "arrodillarse", "saltar", "asustarse"):
            g = principal                       # lo hacen juntos
        else:
            g = "escuchar"
        e = expr if (k == 0 or expr in ("miedo", "alegria", "sorpresa", "tristeza")) else "neutra"
        # el nombre sale en una etiqueta si la frase lo dice
        dicho = fidelidad.plegar(nombre).split()[:1]
        salida.append(dict(aspecto, gesto=g, expr=e, mira=mira,
                           habla=habla if k == 0 else [],
                           etiqueta=bool(dicho and f" {dicho[0]} " in plano),
                           semilla=_numero(nombre, 997)))
    return salida


# ------------------------------------------------------------------ sonido

def whoosh(frecuencia=48000, dur=0.7):
    """Ruido que sube y baja con un filtro que se abre: el «fiuuu» del viaje."""
    import numpy as np                                  # noqa: PLC0415
    n = int(frecuencia * dur)
    t = np.arange(n, dtype=np.float32) / frecuencia
    rng = np.random.default_rng(119106)
    ruido = rng.standard_normal(n).astype(np.float32)
    u = t / dur
    env = np.sin(np.pi * np.clip(u, 0, 1)) ** 1.6
    # paso bajo variable: media movil cuyo largo baja (se abre) y vuelve
    salida = np.zeros(n, dtype=np.float32)
    acum = np.concatenate([[0.0], np.cumsum(ruido, dtype=np.float64)])
    largo = (40 - 30 * np.sin(np.pi * u)).astype(int)
    idx = np.arange(n)
    ini = np.maximum(0, idx - largo)
    salida = ((acum[idx + 1] - acum[ini]) / np.maximum(1, idx + 1 - ini)).astype(np.float32)
    mono = salida * env
    pico = float(np.max(np.abs(mono))) or 1.0
    mono = (mono / pico).astype(np.float32)
    # se mueve de izquierda a derecha, como la camara
    pan = np.clip(u, 0, 1)
    return np.stack([mono * (1 - 0.5 * pan), mono * (0.5 + 0.5 * pan)], axis=1)


def pop(frecuencia=48000, tono=1.0):
    """Burbuja corta: seno que sube de tono y se apaga, con un clic delante."""
    import numpy as np                                  # noqa: PLC0415
    n = int(frecuencia * 0.12)
    t = np.arange(n, dtype=np.float32) / frecuencia
    f = (380.0 + 900.0 * (1 - np.exp(-t * 60.0))) * tono
    fase = 2 * math.pi * np.cumsum(f) / frecuencia
    mono = np.sin(fase) * np.exp(-t * 38.0)
    mono[:int(frecuencia * 0.003)] += 0.4
    mono = (mono / (float(np.max(np.abs(mono))) or 1.0)).astype(np.float32)
    return np.stack([mono, mono], axis=1)


def eventos_sonido(confs):
    """Los sonidos del motion de TODO el video: [(t, "whoosh"|"pop", dur|tono)].

    Un whoosh por viaje de camara (y por objeto puente) y un pop por cada cosa
    que aterriza (los «impactos», los mismos que mueven la camara), sin
    amontonarlos: dos pops a menos de 0,14 s suenan como uno.
    """
    whooshes, pops, vistos = [], [], set()
    for conf in (confs or {}).values():
        if not conf:
            continue
        for tr in conf.get("cam") or []:
            clave = ("w", tr["t0"])
            if tr.get("tipo") == "viaje" and clave not in vistos:
                vistos.add(clave)
                whooshes.append((max(0.0, tr["t0"] - 0.05), "whoosh",
                                 max(0.45, min(1.2, tr["t1"] - tr["t0"] + 0.25))))
        for im in conf.get("impactos") or []:
            clave = ("p", round(im["t"], 2))
            if clave not in vistos:
                vistos.add(clave)
                pops.append(im["t"] - 0.04)
    salida = list(whooshes)
    ultimo = -1.0
    for k, t in enumerate(sorted(pops)):
        if t - ultimo < 0.14:
            continue
        ultimo = t
        salida.append((max(0.0, t), "pop", 0.85 + 0.1 * (k % 4)))
    return sorted(salida)


def pista(eventos, frecuencia=48000):
    """[(t, muestra float32 (n, 2), dB)] listos para `sonido.anadir_muestras`."""
    salida, cache = [], {}
    for t, tipo, extra in eventos:
        clave = (tipo, round(extra, 2))
        if clave not in cache:
            cache[clave] = (whoosh(frecuencia, extra) if tipo == "whoosh"
                            else pop(frecuencia, extra))
        salida.append((t, cache[clave], -17.0 if tipo == "whoosh" else -19.0))
    return salida


# ------------------------------------------------------------------ JS

MOTION_MAS_JS = r"""
// ===== MOTION GRAPHICS, segunda parte (pasos/motion_mas.py) ==================

// ---- ICONOS PARA METAFORAS (los llama icono() cuando no conoce el nombre)
function iconoMas(nombre, g, a){
  const T = MGT.tinta;
  switch (nombre){
    case 'bola':
      mk('path', a({d: 'M-40,-38 C-30,-46 -18,-30 -10,-36 C-2,-42 6,-24 14,-28', fill: 'none', 'stroke-width': 7}), g);
      [[-40,-38],[-26,-37],[-12,-34],[2,-31]].forEach(([x,y]) => mk('ellipse', a({cx: x, cy: y, rx: 7, ry: 5, fill: 'none', 'stroke-width': 4}), g));
      mk('circle', a({cx: 12, cy: 10, r: 32, fill: T}), g);
      mk('circle', {cx: 2, cy: 0, r: 8, fill: '#fff', opacity: .35}, g); break;
    case 'corazon_roto':
      mk('path', a({d: 'M-3,38 C-60,0 -48,-46 -18,-40 C-8,-38 -2,-30 -2,-24 L-10,-6 L2,4 L-6,20z', fill: MGT.acento, transform: 'translate(-6,0) rotate(-8)'}), g);
      mk('path', a({d: 'M3,38 C60,0 48,-46 18,-40 C8,-38 2,-30 2,-24 L-6,-6 L6,4 L-2,20z', fill: MGT.acento, transform: 'translate(6,0) rotate(8)'}), g); break;
    case 'bombilla':
      mk('path', a({d: 'M-14,22 C-14,8 -32,0 -32,-16 A32,32 0 1 1 32,-16 C32,0 14,8 14,22z', fill: MGT.oro}), g);
      mk('path', a({d: 'M-14,28 H14 M-12,36 H12 M-6,44 H6', fill: 'none', 'stroke-width': 6}), g);
      mk('path', {d: 'M-8,6 L-4,-14 L4,-6 L8,-20', fill: 'none', stroke: T, 'stroke-width': 4, 'stroke-linejoin': 'round'}, g); break;
    case 'rayo':
      mk('path', a({d: 'M10,-46 L-24,6 H-2 L-12,46 L26,-8 H4z', fill: MGT.oro}), g); break;
    case 'semilla':
      mk('path', a({d: 'M-40,30 H40', 'stroke-width': 7}), g);
      mk('ellipse', a({cx: 0, cy: 22, rx: 14, ry: 10, fill: '#8a5a3a'}), g);
      mk('path', a({d: 'M0,14 C0,-6 2,-18 0,-30', fill: 'none', stroke: MGT.acento2, 'stroke-width': 6}), g);
      mk('path', a({d: 'M0,-14 C-24,-18 -28,-36 -26,-40 C-10,-38 -2,-30 0,-14z M0,-22 C18,-28 26,-42 24,-46 C8,-44 0,-34 0,-22z', fill: MGT.acento2, 'stroke-width': 4}), g); break;
    case 'candado':
      mk('path', a({d: 'M-20,-6 V-22 A20,20 0 0 1 20,-22 V-6', fill: 'none', 'stroke-width': 10}), g);
      mk('rect', a({x: -34, y: -8, width: 68, height: 52, rx: 8, fill: MGT.oro}), g);
      mk('path', a({d: 'M0,10 V26', 'stroke-width': 8}), g);
      mk('circle', {cy: 10, r: 7, fill: T}, g); break;
    case 'regalo':
      mk('rect', a({x: -36, y: -10, width: 72, height: 52, rx: 4, fill: MGT.acento}), g);
      mk('rect', a({x: -42, y: -26, width: 84, height: 18, rx: 4, fill: MGT.acento}), g);
      mk('path', a({d: 'M0,-26 V42', stroke: MGT.oro, 'stroke-width': 10}), g);
      mk('path', a({d: 'M0,-26 C-20,-50 -40,-30 0,-26 C40,-30 20,-50 0,-26z', fill: MGT.oro, 'stroke-width': 4}), g); break;
    case 'mundo':
      mk('circle', a({r: 42, fill: MGT.cielo}), g);
      mk('path', {d: 'M-30,-20 C-14,-30 -6,-14 -16,-4 C-26,4 -20,18 -30,22 C-40,6 -40,-10 -30,-20z M6,-36 C22,-32 30,-14 20,-4 C10,6 22,20 12,32 C2,22 -2,8 6,-2 C14,-12 -4,-26 6,-36z', fill: MGT.acento2, stroke: T, 'stroke-width': 3}, g);
      mk('circle', {r: 42, fill: 'none', stroke: T, 'stroke-width': 6}, g); break;
    case 'escalera':
      mk('path', a({d: 'M-24,46 L-14,-46 M24,46 L14,-46 M-22,28 H22 M-20,8 H20 M-18,-12 H18 M-16,-32 H16', fill: 'none', stroke: '#8a5a3a', 'stroke-width': 8}), g); break;
    case 'muro':
      for (let f = 0; f < 4; f++) for (let c = 0; c < 3; c++){
        const off = f % 2 ? 14 : 0;
        mk('rect', a({x: -42 + c*28 + off - (f % 2 ? 14 : 0), y: -40 + f*20, width: 28, height: 20, fill: f % 2 ? '#C0704A' : '#D9895E', 'stroke-width': 3}), g);
      }
      break;
    default:
      mk('circle', a({r: 30, fill: MGT.acento}), g);
  }
}

// ---- BARRAS: cada barra crece cuando la voz dice su cifra, y la cifra cuenta
function hazBarras(p, g){
  const n = p.barras.length, tam = p.tam, w = p.w, h = p.h;
  const maxv = p.pct ? 100 : Math.max(...p.barras.map(b => b.v)) || 1;
  const hueco = w/n, bw = Math.min(hueco*0.62, tam*3.4), base = h/2 - tam*1.4, alto = h - tam*3.2;
  mk('path', {d: `M${-w/2},${base} H${w/2}`, stroke: MGT.tinta, 'stroke-width': Math.max(4, tam*0.1), 'stroke-linecap': 'round'}, g);
  const cols = [MGT.acento, MGT.acento2, MGT.oro, MGT.cielo];
  const barras = p.barras.map((b, k) => {
    const x = -w/2 + hueco*(k + 0.5), e = mk('g', {}, g);
    if (p.pct) mk('rect', {x: x - bw/2, y: base - alto, width: bw, height: alto, rx: bw*0.12, fill: MGT.tinta, opacity: .1}, e);
    const rect = mk('rect', {x: x - bw/2, width: bw, rx: bw*0.12, fill: cols[k % 4], stroke: MGT.tinta, 'stroke-width': Math.max(3, tam*0.08)}, e);
    const num = txt(e, '0', {'font-family': MGF.titulo, 'font-size': tam*1.15, fill: MGT.tinta, 'text-anchor': 'middle', x});
    const etq = txt(e, b.t || '', {'font-family': MGF.titulo, 'font-size': tam*0.7, fill: MGT.tinta, 'text-anchor': 'middle', x, y: base + tam*1.05});
    const aw = ancho(etq); if (aw > hueco*0.95) etq.setAttribute('font-size', (tam*0.7*hueco*0.95/aw).toFixed(1));
    return {b, e, rect, num, x};
  });
  return function(T){
    barras.forEach(q => {
      const s = T - q.b.en, r = resorte(s, 11, .45), u = eOut(s/0.9);
      const hh = Math.max(0, alto*(q.b.v/maxv)*r);
      q.e.setAttribute('opacity', s > -0.25 ? 1 : 0);
      q.rect.setAttribute('y', (base - hh).toFixed(1)); q.rect.setAttribute('height', hh.toFixed(1));
      const v = q.b.v*cl(u, 0, 1);
      q.num.textContent = s > 0 ? (p.pct ? Math.round(v) + ' %' : Math.round(v).toLocaleString('es')) : '';
      q.num.setAttribute('y', (base - hh - tam*0.35).toFixed(1));
    });
  };
}

// ---- ANTES / AHORA: una cortina barre lo de antes (gris) y descubre lo nuevo
function hazAntes(p, g){
  const tam = p.tam, w = p.w, h = p.h, sw = Math.max(5, tam*0.09), r = tam*0.4;
  const id = 'mgad' + (MGID++);
  const cp = mk('clipPath', {id}, mk('defs', {}, g));
  const cortina = mk('rect', {x: -w/2, y: -h/2, width: 0, height: h}, cp);
  mk('rect', {x: -w/2 + sw*1.6, y: -h/2 + sw*1.6, width: w, height: h, rx: r, fill: MGT.tinta}, g);
  const antes = mk('g', {}, g);
  mk('rect', {x: -w/2, y: -h/2, width: w, height: h, rx: r, fill: '#D9D4CC', stroke: MGT.tinta, 'stroke-width': sw}, antes);
  const ea = bloqueTexto(antes, p.a, MGF.titulo, tam*1.1, w*0.8, '#6F6A63', 3);
  ea.g.setAttribute('transform', `translate(0,${(tam*0.3).toFixed(1)})` + (ea.g.getAttribute('transform') ? ' ' + ea.g.getAttribute('transform') : ''));
  const despues = mk('g', {'clip-path': `url(#${id})`}, g);
  mk('rect', {x: -w/2, y: -h/2, width: w, height: h, rx: r, fill: MGT.papel, stroke: MGT.acento2, 'stroke-width': sw}, despues);
  const eb = bloqueTexto(despues, p.b, MGF.titulo, tam*1.25, w*0.8, MGT.tinta, 3);
  eb.g.setAttribute('transform', `translate(0,${(tam*0.3).toFixed(1)})` + (eb.g.getAttribute('transform') ? ' ' + eb.g.getAttribute('transform') : ''));
  for (let k = 0; k < 7; k++){
    const a = k/7*Math.PI*2;
    mk('path', {d: `M${(Math.cos(a)*w*0.36).toFixed(1)},${(Math.sin(a)*h*0.36).toFixed(1)} l${(Math.cos(a)*tam*0.5).toFixed(1)},${(Math.sin(a)*tam*0.5).toFixed(1)}`,
      stroke: MGT.oro, 'stroke-width': tam*0.16, 'stroke-linecap': 'round', opacity: .9}, despues);
  }
  const pastilla = (texto, color) => {
    const e = mk('g', {}, g);
    const t = txt(e, texto, {'font-family': MGF.titulo, 'font-size': tam*0.62, fill: '#fff', 'text-anchor': 'middle', y: tam*0.22, 'letter-spacing': tam*0.05});
    const aw = ancho(t) + tam*1.1;
    e.insertBefore(mk('rect', {x: -aw/2, y: -tam*0.5, width: aw, height: tam, rx: tam*0.5, fill: color}), t);
    return e;
  };
  const pa = pastilla('ANTES', '#6F6A63'), pb = pastilla('AHORA', MGT.acento);
  const linea = mk('rect', {y: -h/2 - tam*0.3, width: sw*1.6, height: h + tam*0.6, fill: MGT.oro, stroke: MGT.tinta, 'stroke-width': sw*0.5}, g);
  return function(T){
    const sa = T - p.a_en, ra = resorte(sa, 14, .4);
    pa.setAttribute('opacity', sa > 0 ? 1 : 0);
    pa.setAttribute('transform', `translate(${(-w*0.3).toFixed(1)},${(-h/2).toFixed(1)}) scale(${Math.max(0.001, ra).toFixed(3)})`);
    const u = eIO((T - p.b_en + 0.1)/0.75);
    const xc = -w/2 + w*u;
    cortina.setAttribute('width', (w*u).toFixed(1));
    linea.setAttribute('x', (xc - sw*0.8).toFixed(1));
    linea.setAttribute('opacity', u > 0.001 && u < 0.999 ? 1 : 0);
    antes.setAttribute('opacity', (1 - 0.35*u).toFixed(3));
    const sb = T - p.b_en - 0.55, rb = resorte(sb, 14, .4);
    pb.setAttribute('opacity', sb > 0 ? 1 : 0);
    pb.setAttribute('transform', `translate(${(w*0.3).toFixed(1)},${(-h/2).toFixed(1)}) scale(${Math.max(0.001, rb).toFixed(3)})`);
  };
}

// ---- ARBOL GENEALOGICO: cada generacion cae al decir su nombre y la rama se dibuja
function hazArbol(p, g){
  const n = p.nodos.length, R = p.r, tam = p.tam, v = p.vertical;
  const pos = k => v ? [((k % 2) ? 1 : -1)*R*0.9, (k - (n - 1)/2)*p.paso] : [(k - (n - 1)/2)*p.paso, ((k % 2) ? 1 : -1)*R*0.5];
  const ramas = [];
  for (let k = 1; k < n; k++){
    const [x0, y0] = pos(k - 1), [x1, y1] = pos(k);
    const d = v ? `M${x0},${y0 + R} C${x0},${(y0 + y1)/2} ${x1},${(y0 + y1)/2} ${x1},${y1 - R}`
                : `M${x0 + R},${y0} C${(x0 + x1)/2},${y0} ${(x0 + x1)/2},${y1} ${x1 - R},${y1}`;
    ramas.push({e: mk('path', {d, fill: 'none', stroke: MGT.suave, 'stroke-width': Math.max(5, R*0.12), 'stroke-linecap': 'round', opacity: 0}, g), k});
  }
  const cols = [MGT.acento, MGT.acento2, MGT.oro, MGT.cielo];
  const nodos = p.nodos.map((nd, k) => {
    const [x, y] = pos(k), e = mk('g', {}, g);
    mk('circle', {cx: R*0.1, cy: R*0.12, r: R, fill: MGT.tinta}, e);
    mk('circle', {r: R, fill: cols[k % 4], stroke: MGT.tinta, 'stroke-width': Math.max(4, R*0.1)}, e);
    txt(e, (nd.t || '?').charAt(0).toUpperCase(), {'font-family': MGF.titulo, 'font-size': R*1.05, fill: '#fff', 'text-anchor': 'middle', y: R*0.37});
    const lado = v ? ((k % 2) ? -1 : 1) : 0;
    txt(e, nd.t, {'font-family': MGF.titulo, 'font-size': tam, fill: MGT.tinta, 'text-anchor': v ? (lado > 0 ? 'start' : 'end') : 'middle',
      x: v ? lado*R*1.3 : 0, y: v ? tam*0.35 : R + tam*1.15, stroke: MGT.papel, 'stroke-width': tam*0.12, 'paint-order': 'stroke'});
    return {nd, e, x, y};
  });
  return function(T){
    nodos.forEach(q => {
      const s = T - q.nd.en, r = resorte(s, 13, .42);
      q.e.setAttribute('opacity', s > 0 ? 1 : 0);
      q.e.setAttribute('transform', `translate(${q.x.toFixed(1)},${(q.y - (1 - r)*R*2).toFixed(1)}) scale(${Math.max(0.001, 0.4 + 0.6*r).toFixed(3)})`);
    });
    ramas.forEach(rm => dibujar(rm.e, eOut((T - p.nodos[rm.k].en + 0.35)/0.45)));
  };
}

// ---- FLECHA que se dibuja y señala (con su rotulo)
function hazFlecha(p, g){
  const dx = p.dx, dy = p.dy, L = Math.hypot(dx, dy) || 1, sw = p.grosor;
  const nx = -dy/L, ny = dx/L, cu = (p.curva === undefined ? 0.25 : p.curva)*L;
  const mx = dx/2 + nx*cu, my = dy/2 + ny*cu;
  const cuerpo = mk('path', {d: `M0,0 Q${mx.toFixed(1)},${my.toFixed(1)} ${dx.toFixed(1)},${dy.toFixed(1)}`, fill: 'none', stroke: MGT.acento,
    'stroke-width': sw, 'stroke-linecap': 'round', opacity: 0}, g);
  const ang = Math.atan2(dy - my, dx - mx)*180/Math.PI;
  const punta = mk('path', {d: `M${-sw*2.6},${-sw*1.9} L0,0 L${-sw*2.6},${sw*1.9}`, fill: 'none', stroke: MGT.acento, 'stroke-width': sw,
    'stroke-linecap': 'round', 'stroke-linejoin': 'round'}, g);
  let rot = null;
  if (p.texto){
    rot = mk('g', {}, g);
    const t = txt(rot, p.texto, {'font-family': MGF.titulo, 'font-size': p.tam, fill: MGT.tinta, 'text-anchor': 'middle', y: p.tam*0.35,
      stroke: MGT.papel, 'stroke-width': p.tam*0.14, 'paint-order': 'stroke'});
    rot.setAttribute('transform', `translate(${(-nx*p.tam*0.9 - dx*0.08).toFixed(1)},${(-ny*p.tam*0.9 - dy*0.08 - p.tam*0.6).toFixed(1)})`);
  }
  return function(T){
    const u = eOut((T - p.en)/0.45);
    dibujar(cuerpo, u);
    const r = resorte(T - p.en - 0.4, 16, .4), late = T - p.en > 0.9 ? 1 + 0.08*Math.sin((T - p.en)*7) : 1;
    punta.setAttribute('opacity', T - p.en > 0.4 ? 1 : 0);
    punta.setAttribute('transform', `translate(${dx.toFixed(1)},${dy.toFixed(1)}) rotate(${ang.toFixed(1)}) scale(${(Math.max(0.001, r)*late).toFixed(3)})`);
    if (rot) rot.setAttribute('opacity', cl((T - p.en)/0.25, 0, 1).toFixed(3));
  };
}

// ---- CIRCULO a mano alzada que rodea algo (con rotulo opcional)
function hazCirculo(p, g){
  const ov = mk('path', {d: trazoOvalo(0, 0, p.w/2, p.h/2), fill: 'none', stroke: MGT.acento, 'stroke-width': p.grosor, 'stroke-linecap': 'round', opacity: 0}, g);
  let rot = null;
  if (p.texto){
    rot = txt(g, p.texto, {'font-family': MGF.titulo, 'font-size': p.tam, fill: MGT.acento, 'text-anchor': 'middle', y: -p.h/2 - p.tam*0.45,
      stroke: MGT.papel, 'stroke-width': p.tam*0.14, 'paint-order': 'stroke'});
  }
  return function(T){
    dibujar(ov, eIO((T - p.en)/0.55));
    if (rot){
      const r = resorte(T - p.en - 0.4, 15, .45);
      rot.setAttribute('opacity', T - p.en > 0.4 ? 1 : 0);
      rot.setAttribute('transform', `translate(0,${((1 - r)*p.tam).toFixed(1)})`);
    }
  };
}

// ---- LOS MUÑECOS PLANOS. Unidades: 100 = alto de la figura, pies en (0,0).
const MGBRAZOS = {
  // [hombro, antebrazo] en grados: 0 = hacia abajo, 90 = hacia fuera, 180 = arriba,
  // negativo = hacia dentro. f(t, lado, hablando) -> [a1, a2]
  reposo: (t, s) => [12 + 2*Math.sin(t*2.2 + s), 8],
  hablar: (t, s, h) => s > 0 ? [28 + 6*Math.sin(t*2.3), 110 + (h ? 28 : 12)*Math.sin(t*(h ? 6.2 : 3.1))] : [12, 8],
  presentar: (t, s, h, m) => s === m ? [42 + 3*Math.sin(t*1.7), 100 + 6*Math.sin(t*2.1)] : [12, 8],
  senalar: (t, s, h, m) => s === m ? [92 + 2*Math.sin(t*3), 94] : [14, 10],
  brazos: (t, s) => [150 + 9*Math.sin(t*2.4 + s), 166 + 10*Math.sin(t*2.4 + s)],
  caminar: (t, s) => { const a = 18*Math.sin(t*6.5)*s; return [12 + a, 18 + a]; },
  escuchar: (t, s) => [12, 8],
  arrodillarse: (t, s) => [25, -118],
  saltar: (t, s) => [140 + 12*Math.sin(t*5 + s), 168],
  asustarse: (t, s) => [108 + 4*Math.sin(t*40), -158],
  girar: (t, s) => [14, 10],
  pensar: (t, s) => s > 0 ? [22, -150] : [30, -95],
};
const MGCARAS = {
  // cejas [dentro, fuera], ojo alto, pupila, boca [ancho, curva, abierta], extra
  neutra:   {ce: [0, 0], oj: 6.6, pu: 3, bo: [5.5, 2, 0]},
  alegria:  {ce: [-2, -2], oj: 5.4, pu: 3, bo: [8, 5, 5], mej: 1},
  sorpresa: {ce: [-5, -4], oj: 8.2, pu: 2.2, bo: [3.6, -4.5, 9.5], ex: 1},
  miedo:    {ce: [-5, 1], oj: 8, pu: 1.9, bo: [6.5, -1, 5], sudor: 1},
  tristeza: {ce: [-4, 2], oj: 6, pu: 3, bo: [5.5, -3.2, 0.6], lagrima: 1},
  enojo:    {ce: [4, -2.5], oj: 5.4, pu: 3.2, bo: [6.5, -1.5, 1.2], enojo: 1},
};
function mgBoca(w, cu, op){
  return `M${-w},0 Q0,${cu.toFixed(2)} ${w},0 Q0,${(cu + op*2).toFixed(2)} ${-w},0Z`;
}
function hazFigura(f, padre, k){
  const T0 = MGT.tinta, g = mk('g', {}, padre), sw = 2.2, esc = f.nino ? 0.78 : 1;
  const raiz = mk('g', {}, g);
  const sombra = mk('ellipse', {rx: 22, ry: 4, fill: '#000', opacity: .16}, raiz);
  const cuerpo = mk('g', {}, raiz);
  // angel: hombre con ropa blanca y un brillo suave detras; sin alas ni aureola
  if (f.angel) [[44, 60, .10], [35, 52, .14], [27, 45, .18]].forEach(([rx, ry, o]) =>
    mk('ellipse', {cy: -32, rx, ry, fill: '#FFF8D7', opacity: o}, cuerpo));
  const pie1 = mk('ellipse', {cx: -7, cy: -3, rx: 6.5, ry: 3.6, fill: '#5a3b26', stroke: T0, 'stroke-width': 1.5}, cuerpo);
  const pie2 = mk('ellipse', {cx: 7, cy: -3, rx: 6.5, ry: 3.6, fill: '#5a3b26', stroke: T0, 'stroke-width': 1.5}, cuerpo);
  const tronco = mk('g', {}, cuerpo);
  mk('path', {d: 'M-12,-55 C-6,-58 6,-58 12,-55 L21,-7 C8,-3 -8,-3 -21,-7Z', fill: f.tunica, stroke: T0, 'stroke-width': sw, 'stroke-linejoin': 'round'}, tronco);
  mk('path', {d: 'M-12,-55 L-4,-56.5 L19,-17 L20.5,-8 L14,-7.5Z', fill: f.manto, stroke: T0, 'stroke-width': 1.6, 'stroke-linejoin': 'round'}, tronco);
  mk('path', {d: 'M-15.5,-31 Q0,-28 15.5,-31', fill: 'none', stroke: T0, 'stroke-width': 2, opacity: .45}, tronco);
  // VOLUMEN (P3): la tunica con su lado en sombra y un brillo del lado de la luz
  mk('path', {d: 'M5,-56.6 C9,-56.8 11,-56 12,-55 L21,-7 C17,-5.6 13,-5 9,-4.6 C12,-20 10,-40 5,-56.6Z', fill: '#000', opacity: .14}, tronco);
  mk('path', {d: 'M-9,-53 C-12,-40 -15,-22 -17,-9', fill: 'none', stroke: '#fff', 'stroke-width': 2.4, 'stroke-linecap': 'round', opacity: .22}, tronco);
  const brazo = s => {
    const e = mk('g', {}, tronco);
    const fondo = mk('path', {fill: 'none', stroke: T0, 'stroke-width': 8.6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'}, e);
    const tela = mk('path', {fill: 'none', stroke: f.tunica, 'stroke-width': 5.4, 'stroke-linecap': 'round', 'stroke-linejoin': 'round'}, e);
    const dedo = mk('path', {fill: 'none', stroke: f.piel, 'stroke-width': 2.8, 'stroke-linecap': 'round', opacity: 0}, e);
    const mano = mk('circle', {r: 3.9, fill: f.piel, stroke: T0, 'stroke-width': 1.5}, e);
    return {s, fondo, tela, mano, dedo};
  };
  const brazos = [brazo(-1), brazo(1)];
  const cabeza = mk('g', {}, cuerpo);
  if (f.mujer) mk('path', {d: 'M-25,22 C-31,-31 31,-31 25,22 L19,22 C22,-9 -22,-9 -19,22Z', fill: f.manto, stroke: T0, 'stroke-width': sw}, cabeza);
  mk('circle', {r: 21, fill: f.piel, stroke: T0, 'stroke-width': sw}, cabeza);
  // la cara con volumen: media luna de sombra y un brillo en la frente
  mk('path', {d: 'M6,-20 A21,21 0 0 1 6,20 A26,26 0 0 0 6,-20Z', fill: '#000', opacity: .12}, cabeza);
  mk('ellipse', {cx: -9, cy: -11, rx: 5, ry: 3.2, fill: '#fff', opacity: .28, transform: 'rotate(-30,-9,-11)'}, cabeza);
  if (!f.mujer) mk('path', {d: 'M-21,-3 C-23,-27 23,-27 21,-3 C15,-13 -15,-13 -21,-3Z', fill: f.pelo, stroke: T0, 'stroke-width': 1.6}, cabeza);
  else mk('path', {d: 'M-20,-6 C-18,-24 18,-24 20,-6 C12,-15 -12,-15 -20,-6Z', fill: f.manto, stroke: T0, 'stroke-width': 1.6}, cabeza);
  if (f.barba) mk('path', {d: 'M-17,3 C-16,27 16,27 17,3 C10,11 -10,11 -17,3Z', fill: f.pelo, stroke: T0, 'stroke-width': 1.5}, cabeza);
  const mejillas = [-13, 13].map(x => mk('ellipse', {cx: x, cy: 6, rx: 4.2, ry: 2.6, fill: '#F2797A', opacity: 0}, cabeza));
  const ojos = [-8, 8].map(x => {
    const o = mk('g', {transform: `translate(${x},-1)`}, cabeza);
    const blanco = mk('ellipse', {rx: 5.6, ry: 6.6, fill: '#fff', stroke: T0, 'stroke-width': 1.3}, o);
    const pupila = mk('circle', {r: 3, fill: T0}, o);
    const brillo = mk('circle', {r: 1.1, fill: '#fff'}, o);
    return {o, blanco, pupila, brillo, x};
  });
  const cejas = [-1, 1].map(s => mk('path', {fill: 'none', stroke: f.mujer ? '#3a2a1e' : f.pelo === '#d8d4cc' ? '#9a948a' : T0, 'stroke-width': 2.6, 'stroke-linecap': 'round'}, cabeza));
  const boca = mk('path', {fill: '#7A2230', stroke: T0, 'stroke-width': 1.5, 'stroke-linejoin': 'round', transform: 'translate(0,11)'}, cabeza);
  const sudor = mk('path', {d: 'M0,-5 C3,0 4,3 0,5 C-4,3 -3,0 0,-5z', fill: '#9AD8FF', stroke: T0, 'stroke-width': 1.2, opacity: 0}, cabeza);
  const lagrima = mk('path', {d: 'M0,-4 C2.5,0 3,2.5 0,4 C-3,2.5 -2.5,0 0,-4z', fill: '#9AD8FF', stroke: T0, 'stroke-width': 1, opacity: 0}, cabeza);
  const rayas = mk('g', {opacity: 0}, cabeza);
  [[-14, -30, -18, -38], [0, -33, 0, -42], [14, -30, 18, -38]].forEach(([a, b, c, d]) => mk('path', {d: `M${a},${b} L${c},${d}`, stroke: MGT.acento, 'stroke-width': 2.6, 'stroke-linecap': 'round'}, rayas));
  const vena = mk('path', {d: 'M12,-18 l4,-4 m-4,0 l4,4', stroke: MGT.acento, 'stroke-width': 2.4, 'stroke-linecap': 'round', opacity: 0}, cabeza);
  let etq = null;
  if (f.etiqueta){
    etq = mk('g', {}, g);
    const t = txt(etq, String(f.nombre).toUpperCase(), {'font-family': MGF.titulo, 'font-size': 9, fill: '#fff', 'text-anchor': 'middle', y: 3.2, 'letter-spacing': .6});
    const aw = ancho(t) + 10;
    etq.insertBefore(mk('rect', {x: -aw/2, y: -6.5, width: aw, height: 13, rx: 6.5, fill: MGT.acento2, stroke: T0, 'stroke-width': 1.2}), t);
  }
  const cara = MGCARAS[f.expr] || MGCARAS.neutra;
  const gesto = MGBRAZOS[f.gesto] ? f.gesto : 'reposo';
  return function(T){
    const s = T - f.en;
    if (s < 0){ g.setAttribute('display', 'none'); return; }
    g.removeAttribute('display');
    const t = T + f.semilla*0.37;
    // ¿esta hablando ahora? abertura de la boca con una oscilacion por silaba
    let abre = 0, hablando = false;
    (f.habla || []).forEach(([a, b, sil]) => {
      if (T >= a && T < b){ hablando = true; abre = Math.max(abre, Math.abs(Math.sin(Math.PI*sil*(T - a)/Math.max(0.05, b - a)))); }
    });
    // ENTRADA: salta desde abajo con resorte y se aplasta al aterrizar
    const r = resorte(s, 12, .42);
    let y = 0, x = 0, sx = 1, sy = 1, rot = 0;
    const llega = cl((r - 1)*1.8, -0.18, 0.2);
    sy = 1 + llega; sx = 1/sy;
    let esc2 = Math.max(0.001, r);
    // respira
    sy *= 1 + 0.012*Math.sin(t*2.2);
    // el gesto del cuerpo
    let baja = 0, mira = f.mira || 1;
    if (gesto === 'caminar'){ y -= Math.abs(Math.sin(t*6.5))*2.4; pie1.setAttribute('cx', (-7 + 3*Math.sin(t*6.5)).toFixed(2)); pie2.setAttribute('cx', (7 - 3*Math.sin(t*6.5)).toFixed(2)); }
    if (gesto === 'saltar' && s > 0.5){ const fase = ((s - 0.5) % 0.62)/0.62; y -= Math.sin(Math.PI*fase)*16; const ap = fase < 0.12 ? 1 - fase/0.12 : 0; sy *= 1 - 0.14*ap; sx *= 1 + 0.12*ap; }
    if (gesto === 'arrodillarse') baja = 13*eOut(s/0.6);
    if (gesto === 'asustarse'){ x += Math.sin(t*47)*0.9; }
    if (gesto === 'girar' && s > 0.6){ const u = cl((s - 0.6)/0.45, 0, 1); sx *= Math.cos(Math.PI*u) || 0.001; if (u > 0.5) mira = -mira; }
    raiz.setAttribute('transform', `translate(${x.toFixed(2)},0) scale(${(esc*esc2*sx).toFixed(4)},${(esc*esc2*sy).toFixed(4)})`);
    cuerpo.setAttribute('transform', `translate(0,${(y + baja).toFixed(2)})`);
    tronco.setAttribute('transform', baja ? `translate(0,-7) scale(1,${(1 - baja/70).toFixed(3)}) translate(0,7)` : '');
    sombra.setAttribute('rx', (22*(1 + y/60)).toFixed(2));
    // la cabeza: asiente al escuchar, sube y baja con la voz, se inclina al orar
    let cr = 0, cy = -74 - baja*0.2;
    if (gesto === 'escuchar') cr = 4*Math.sin(t*1.9);
    if (hablando) cy -= abre*1.2;
    if (gesto === 'arrodillarse') cr = 8*mira;
    if (gesto === 'pensar') cr = -7;
    if (gesto === 'asustarse') cy += 3;
    cabeza.setAttribute('transform', `translate(0,${cy.toFixed(2)}) rotate(${(cr + 2.5*Math.sin(t*1.3)).toFixed(2)})`);
    // brazos (hombro + codo + mano)
    brazos.forEach(b => {
      const [a1, a2] = MGBRAZOS[gesto](t, b.s, hablando, mira);
      const S = [b.s*10, -50], r1 = a1*Math.PI/180, r2 = a2*Math.PI/180;
      const E = [S[0] + b.s*15*Math.sin(r1), S[1] + 15*Math.cos(r1)];
      const H = [E[0] + b.s*14*Math.sin(r2), E[1] + 14*Math.cos(r2)];
      const d = `M${S[0].toFixed(1)},${S[1].toFixed(1)} L${E[0].toFixed(1)},${E[1].toFixed(1)} L${H[0].toFixed(1)},${H[1].toFixed(1)}`;
      b.fondo.setAttribute('d', d); b.tela.setAttribute('d', d);
      b.mano.setAttribute('cx', H[0].toFixed(1)); b.mano.setAttribute('cy', H[1].toFixed(1));
      if (gesto === 'senalar' && b.s === mira){
        b.dedo.setAttribute('d', `M${H[0].toFixed(1)},${H[1].toFixed(1)} l${(b.s*6*Math.sin(r2)).toFixed(1)},${(6*Math.cos(r2)).toFixed(1)}`);
        b.dedo.setAttribute('opacity', 1);
      }
    });
    // la cara
    const parpadea = ((t + f.semilla*0.11) % 3.4) < 0.11 || gesto === 'arrodillarse' && s > 0.8;
    ojos.forEach(o => {
      const alto = parpadea ? 0.7 : cara.oj;
      o.blanco.setAttribute('ry', alto.toFixed(2));
      const px = 1.7*mira + (gesto === 'pensar' ? 0.8 : 0), py = gesto === 'pensar' ? -2.4 : (f.expr === 'tristeza' ? 1.6 : 0.4);
      o.pupila.setAttribute('r', parpadea ? 0 : cara.pu);
      o.pupila.setAttribute('cx', px.toFixed(2)); o.pupila.setAttribute('cy', py.toFixed(2));
      o.brillo.setAttribute('cx', (px + 1).toFixed(2)); o.brillo.setAttribute('cy', (py - 1.2).toFixed(2));
      o.brillo.setAttribute('r', parpadea ? 0 : 1.1);
    });
    cejas.forEach((c, j) => {
      const sd = j ? 1 : -1, [di, fu] = cara.ce;
      c.setAttribute('d', `M${(sd*3.5).toFixed(1)},${(-10.5 + di).toFixed(1)} L${(sd*12).toFixed(1)},${(-10.5 + fu).toFixed(1)}`);
    });
    const [bw, bc, bo] = cara.bo;
    boca.setAttribute('d', mgBoca(hablando ? Math.max(4, bw*0.85) : bw, bc, Math.max(bo, abre*5.2)));
    mejillas.forEach(m => m.setAttribute('opacity', cara.mej ? .55 : 0));
    sudor.setAttribute('opacity', cara.sudor ? 1 : 0);
    if (cara.sudor) sudor.setAttribute('transform', `translate(${(19*mira).toFixed(1)},${(-14 + ((t*0.8) % 1)*10).toFixed(1)})`);
    lagrima.setAttribute('opacity', cara.lagrima ? 1 - ((t*0.7) % 1)*0.6 : 0);
    if (cara.lagrima) lagrima.setAttribute('transform', `translate(-8,${(5 + ((t*0.7) % 1)*14).toFixed(1)})`);
    if (cara.ex){ const u = resorte(s - 0.2, 15, .4); rayas.setAttribute('opacity', s > 0.2 ? cl(2.5 - s*0.8, 0, 1).toFixed(3) : 0); rayas.setAttribute('transform', `scale(${Math.max(0.001, u).toFixed(3)})`); }
    vena.setAttribute('opacity', cara.enojo ? (0.6 + 0.4*Math.sin(t*6)).toFixed(3) : 0);
    if (etq){
      const se = s - 0.25, re = resorte(se, 15, .45);
      etq.setAttribute('opacity', se > 0 ? cl((3.2 - se)/0.4, 0, 1).toFixed(3) : 0);
      etq.setAttribute('transform', `translate(0,${(10 + (1 - re)*8).toFixed(1)}) scale(${Math.max(0.001, re).toFixed(3)})`);
    }
  };
}
function hazPersonajes(p, g){
  const k = p.alto/100, ups = [];
  const capa = mk('g', {transform: `scale(${k.toFixed(4)})`}, g);
  p.figuras.forEach((f, j) => {
    const e = mk('g', {transform: `translate(${(f.dx/k).toFixed(1)},0)`}, capa);
    ups.push(hazFigura(f, e, j));
  });
  return function(T){ ups.forEach(u => u(T)); };
}
Object.assign(CONSTRUCTORES, {barras: hazBarras, antes: hazAntes, arbol: hazArbol,
  flecha: hazFlecha, circulo: hazCirculo, personajes: hazPersonajes});
"""
