"""La CAMARA VIVA del render (punto F de NOTAS-DAVID, 11-nov-2026).

Hasta aqui cada plano era una ventana que iba de un encuadre a otro con una
curva en S: arrancaba parada, se paraba al final, y en el corte el plano
siguiente volvia a arrancar desde cero. Eso es un salvapantallas, no una
camara. Lo que hace este modulo, plano a plano y sin gastar nada:

  1. LA CURVA. Velocidad en trapecio (rampa corta, crucero, rampa corta) en
     vez de la S: la camara no se queda muerta en los extremos. Los planos
     cortos (< 2,2 s) salen con el empujon delante y frenan despacio.
  2. EL GOLPE DE ZOOM en la palabra que importa (cifra, nombre propio, la
     clave de una pregunta o exclamacion, la Y de «no fue X, sino Y»), con
     ANTICIPACION (un 1 % hacia atras justo antes) y rebote. Con presupuesto
     para TODO el video: como mucho uno cada RITMO_GOLPE s, que un golpe en
     cada frase deja de ser un golpe.
  3. EL TEMBLOR en las palabras de impacto (cayo, trueno, estallo...), corto
     y amortiguado.
  4. LA RESPIRACION: un vaiven de camara al hombro, minimo, para que ningun
     plano este muerto. Se apaga donde ya hay balanceo o un clip de video.
  5. EL ARRASTRE QUE CRUZA EL CORTE: si la transicion que viene es un
     latigazo o un zoom, el plano que sale ACELERA en esa direccion y el que
     entra llega con el resto del movimiento y frena. La transicion deja de
     ser un efecto pegado encima y pasa a ser el movimiento de la camara.

Todo se decide aqui, en Python y de forma determinista (misma semilla, mismo
video); la pagina de p8_render solo lo pinta (`CAMARA_JS`).

NO MUEVE FIRMAS: es un param del render (`camara`: "viva" de fabrica, o
"clasica" para la de antes) que no va en los defectos, y cambiarlo solo pide
volver a montar, que es gratis.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import medios  # noqa: E402
import gancho  # noqa: E402

#: segundos minimos entre dos golpes de zoom en todo el video
RITMO_GOLPE = 4.0
#: segundos minimos entre dos temblores
RITMO_TEMBLOR = 3.0
#: un golpe no cae encima de la transicion de entrada ni pegado al corte
MARGEN_INICIO = 0.3
MARGEN_FIN = 0.45
#: plano corto: la curva sale con el empujon delante
PLANO_CORTO = 2.2

#: lo que hace temblar la camara (sin tildes, en minusculas)
IMPACTO = re.compile(
    r"\b(cay[oe]|cayeron|derrib\w*|derrumb\w*|explot\w*|estall\w*|terremoto\w*|"
    r"tembl\w*|trueno\w*|rayos?|golpe[oa]?\w*|choc[oa]\w*|destroz\w*|destru\w*|"
    r"rompi\w*|quebr\w*|azot\w*|grit[oa]\w*|rugi\w*|bum|boom|crash|impacto\w*|"
    r"sacudi\w*|hundi\w*|desplom\w*|arras\w*)\b")

#: palabras que piden golpe aunque no sean la mas larga de la frase
ENFASIS = {"nunca", "jamas", "nadie", "todo", "todos", "nada", "siempre",
           "unico", "unica", "imposible", "milagro", "verdad", "mentira",
           "muerte", "dios", "jesus", "cristo", "secreto", "prohibido"}

#: el arrastre que cruza el corte, por transicion
ARRASTRE = {"whip-pan": "pan", "cinematic-zoom": "zoom",
            "gravitational-lens": "zoom", "swirl-vortex": "zoom"}
DUR_ARRASTRE = {"pan": 0.35, "zoom": 0.45}


def modo_de(params):
    """'viva' (de fabrica) o 'clasica' (la de antes del 11-nov-2026)."""
    valor = (params or {}).get("camara", "viva")
    return "clasica" if valor in ("clasica", "no", False) else "viva"


def _llana(palabra):
    texto = str(palabra or "").lower()
    texto = texto.translate(str.maketrans("áéíóúüñ", "aeiouun"))
    return re.sub(r"[^0-9a-z]", "", texto)


def _frases(palabras):
    """Indices de palabras agrupados por frase (corta en . ! ? … ; :)."""
    grupos, actual = [], []
    for i, palabra in enumerate(palabras):
        actual.append(i)
        if re.search(r"[.!?…;:]$", str(palabra)):
            grupos.append(actual)
            actual = []
    if actual:
        grupos.append(actual)
    return grupos


def _candidato_golpe(palabras, grupo):
    """(indice, fuerza) de la palabra que merece golpe en esta frase, o None.

    Solo hay golpe si la frase lo pide: una cifra, un nombre propio, una
    palabra de ENFASIS, una pregunta/exclamacion o un contraste. Una frase
    normal sigue con su movimiento, que es lo que tiene que pasar casi siempre.
    """
    trozo = [palabras[i] for i in grupo]
    texto = " ".join(trozo)
    # «no fue X, sino Y»: el golpe va en la Y
    for k, palabra in enumerate(trozo[:-1]):
        if _llana(palabra) == "sino":
            return grupo[k + 1], 1.0
    for k, palabra in enumerate(trozo):
        if gancho.es_cifra(palabra):
            return grupo[k], 1.0
    enfasis = [k for k, p in enumerate(trozo) if _llana(p) in ENFASIS]
    if enfasis:
        return grupo[enfasis[0]], 0.85
    clave = gancho.palabra_clave(trozo)
    if clave is None:
        return None
    exclama = bool(re.search(r"[!¡?¿]", texto))
    propio = clave > 0 and str(trozo[clave])[:1].isupper()
    if exclama or propio:
        return grupo[clave], 0.9 if exclama else 0.7
    return None


def _palabras_con_tiempo(escena):
    """[(palabra, t_relativo)] del plano, o [] si texto y marcas no cuadran.

    La misma guarda que subtitulos.de_escena: con las marcas descuadradas el
    golpe caeria en otra palabra, y un golpe a destiempo es peor que ninguno.
    """
    palabras = str(escena.get("narracion") or "").split()
    marcas = escena.get("marcas") or []
    if not palabras or len(palabras) != len(marcas):
        return []
    t_in = float(escena.get("t_in") or 0.0)
    try:
        return [(p, float(m[0]) - t_in) for p, m in zip(palabras, marcas)]
    except (TypeError, ValueError, IndexError):
        return []


def _curva(duracion, indice):
    if duracion < PLANO_CORTO:
        return {"tipo": "salida"}
    # rampas cortas: la de entrada algo mas larga en el primer plano, que
    # arranca de parado de verdad
    return {"tipo": "trapecio", "entra": 0.22 if indice == 0 else 0.12,
            "sale": 0.14}


def preparar(escenas, cortes=None, params=None, semilla=0, excluir=(),
             con_clip=()):
    """{id_de_plano: conf de camara} para todo el video, o {} en 'clasica'.

    `excluir`: planos sin camara viva (cartelas, motion graphics): salen como
    siempre. `con_clip`: planos con video subido, sin respiracion.
    """
    if modo_de(params) != "viva":
        return {}
    cortes = cortes or {}
    excluir, con_clip = set(excluir or ()), set(con_clip or ())
    salida = {}
    ultimo_golpe = ultimo_temblor = -1e9
    ids = [e.get("id") for e in escenas or []]
    for indice, escena in enumerate(escenas or []):
        sid = escena.get("id")
        if not sid or sid in excluir:
            continue
        t_in = float(escena.get("t_in") or 0.0)
        duracion = float(escena.get("t_out") or 0.0) - t_in
        if duracion <= 0:
            continue
        azar = medios.desempatar(semilla, sid, "camara")
        conf = {"curva": _curva(duracion, indice), "golpes": [], "temblores": [],
                "respira": sid not in con_clip,
                "fase": round((azar % 628) / 100.0, 2),
                # un plano sin recorrido (ventana fija) deriva un 4 %: hacia
                # dentro o hacia fuera, alternando para que no se note la regla
                "deriva": 1 if azar % 2 else -1}
        palabras = _palabras_con_tiempo(escena)
        limite = duracion - MARGEN_FIN
        for grupo in _frases([p for p, _ in palabras]):
            cand = _candidato_golpe([p for p, _ in palabras], grupo)
            if not cand:
                continue
            i, fuerza = cand
            t = palabras[i][1]
            if t < MARGEN_INICIO or t > limite:
                continue
            if t_in + t - ultimo_golpe < RITMO_GOLPE:
                continue
            conf["golpes"].append({"t": round(t, 3), "fuerza": fuerza})
            ultimo_golpe = t_in + t
        for palabra, t in palabras:
            if not IMPACTO.search(_llana(palabra)):
                continue
            if t < 0.05 or t > duracion - 0.2:
                continue
            if t_in + t - ultimo_temblor < RITMO_TEMBLOR:
                continue
            conf["temblores"].append({"t": round(t, 3), "fuerza": 1.0})
            ultimo_temblor = t_in + t
        salida[sid] = conf

    # EL ARRASTRE, que necesita a los dos lados del corte: solo si los dos
    # planos llevan camara viva (una cartela no sabe recibirlo)
    for k in range(1, len(ids)):
        antes, ahora = ids[k - 1], ids[k]
        tipo = ARRASTRE.get((cortes.get(ahora) or {}).get("tipo"))
        if not tipo or antes not in salida or ahora not in salida:
            continue
        sentido = 1 if medios.desempatar(semilla, ahora, "arrastre") % 2 else -1
        dur = DUR_ARRASTRE[tipo]
        salida[antes]["sale"] = {"tipo": tipo, "dir": sentido, "dur": dur}
        salida[ahora]["entra"] = {"tipo": tipo, "dir": sentido, "dur": dur}
    return salida


def resumen(conf):
    if not conf:
        return "camara clasica"
    trozos = [conf["curva"]["tipo"]]
    if conf["golpes"]:
        trozos.append(f"{len(conf['golpes'])} golpe(s) de zoom")
    if conf["temblores"]:
        trozos.append(f"{len(conf['temblores'])} temblor(es)")
    if conf.get("sale") or conf.get("entra"):
        trozos.append("arrastre en el corte")
    return "camara viva: " + ", ".join(trozos)


#: Lo que pinta la pagina de p8_render. `curvaCam(u)` sustituye a la S de
#: siempre y `extraCam(t)` devuelve la transformacion que va DELANTE de la
#: ventana (escala y desplazamiento alrededor del centro del cuadro). El
#: desplazamiento nunca enseña borde: la escala sube lo que haga falta.
CAMARA_JS = r"""
function curvaCam(u){
  const c = CAM.curva || {};
  if (c.tipo === 'salida') return 1 - Math.pow(1 - u, 3);
  const a = c.entra || 0, b = c.sale || 0, v = 1 / (1 - a/2 - b/2);
  if (a > 0 && u < a) return v * u * u / (2*a);
  if (b > 0 && u > 1 - b) return 1 - v * (1-u) * (1-u) / (2*b);
  return v * (a/2 + (u - a));
}
function _atras(x){ const c1 = 1.70158, c3 = c1 + 1;
  return 1 + c3*Math.pow(x-1,3) + c1*Math.pow(x-1,2); }
function extraCam(t, quieto){
  let k = 1, dx = 0, dy = 0;
  // la deriva del plano que no tiene recorrido propio
  if (quieto){
    const e = curvaCam(DUR > 0 ? Math.min(1, t/DUR) : 0);
    k *= CAM.deriva > 0 ? 1 + 0.04*e : 1.04 - 0.04*e;
  }
  // golpes de zoom: anticipacion, ataque con rebote y vuelta lenta
  (CAM.golpes || []).forEach(g => {
    const d = t - g.t, A = 0.055 * g.fuerza;
    if (d < -0.12) return;
    if (d < 0) { k *= 1 - 0.012*g.fuerza*Math.sin(Math.PI*(d+0.12)/0.12*0.5); return; }
    const a0 = -0.012 * g.fuerza;
    if (d < 0.16) { k *= 1 + a0 + (A - a0)*_atras(d/0.16); return; }
    k *= 1 + A*Math.exp(-(d-0.16)/0.9);
  });
  // temblores amortiguados
  (CAM.temblores || []).forEach(s => {
    const d = t - s.t;
    if (d < 0 || d > 0.6) return;
    const m = Math.exp(-d/0.16) * s.fuerza;
    dx += 0.009*W*m*Math.sin(2*Math.PI*17*d + 1.3);
    dy += 0.007*H*m*Math.sin(2*Math.PI*13*d + 0.4);
  });
  // respiracion: camara al hombro, minima
  if (CAM.respira){
    const f = CAM.fase || 0;
    dx += 0.0018*W*(Math.sin(2*Math.PI*t/4.7 + f) + 0.5*Math.sin(2*Math.PI*t/2.9 + 2*f));
    dy += 0.0014*H*(Math.sin(2*Math.PI*t/6.3 + 3*f) + 0.4*Math.sin(2*Math.PI*t/3.7 + f));
  }
  // el arrastre que cruza el corte
  const sale = CAM.sale, entra = CAM.entra;
  if (sale && t > DUR - sale.dur){
    const e = Math.pow((t - (DUR - sale.dur)) / sale.dur, 2);
    if (sale.tipo === 'pan') dx -= sale.dir * 0.04 * W * e; else k *= 1 + 0.09*e;
  }
  if (entra && t < entra.dur){
    const e = Math.pow(1 - t / entra.dur, 2);
    if (entra.tipo === 'pan') dx += entra.dir * 0.04 * W * e; else k *= 1 + 0.09*e;
  }
  // que el desplazamiento no enseñe nunca el borde
  k = Math.max(k, 1 + 2*Math.max(Math.abs(dx)/W, Math.abs(dy)/H) + 0.002);
  return 'translate(' + (W/2 + dx).toFixed(2) + 'px,' + (H/2 + dy).toFixed(2) +
         'px) scale(' + k.toFixed(5) + ') translate(' + (-W/2) + 'px,' + (-H/2) + 'px) ';
}
"""
