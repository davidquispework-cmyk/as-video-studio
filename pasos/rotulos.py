"""LOS ROTULOS (plan NIVEL PROFESIONAL, etapa P1).

Piezas graficas que se ponen ENCIMA del plano, quietas respecto al cuadro (no
hacen zoom con la imagen), como en los videos de referencia:

    sello      sello rojo torcido que cae de golpe («NO», «SIN REY», «NUNCA»)
    pastilla   la cita fija arriba («JUECES 9:5»); entra en el plano donde se
               nombra y SE QUEDA en los siguientes hasta que se nombra otra
    dato       etiqueta «DATO» (con la palabra hebrea/griega si la hay)
    cifra      placa con la cifra que sale rodando («DÍA 3», «+400 AÑOS»)
    rebobinar  «◀◀ REBOBINANDO −25 AÑOS» con rayas de cinta de video

Las curvas las pone anime.js (MIT, `motores/js/anime.min.js`, dentro del repo:
el render no sale a internet). Cada rotulo es una linea de tiempo con
`autoplay: false` y la pagina la BUSCA en el instante del fotograma
(`tl.seek`): sin reloj de pared, el mismo fotograma sale igual en cualquier lote.

Como se gobierna:
    params del render  "rotulos": false     apagados en todo el video
                       Falta = encendidos. No va en los defectos del paso: no
                       mueve la firma de ningun proyecto.
    plan.json, escena  "rotulos": false     ninguno en ese plano
                       "rotulos": [{"tipo": "sello", "texto": "SIN REY",
                                    "en": "rey"}, ...]   a mano; manda sobre
                       lo automatico de ese plano (la pastilla se hereda igual)
                       `en` = segundos del plano o una palabra de la voz.
Sin nada escrito, se sacan solos de la narracion (`automaticos`).
"""
import json
import os
import re

try:
    import citas
except ImportError:  # importado como paquete (pasos.rotulos)
    from . import citas

TIPOS = ("sello", "pastilla", "dato", "cifra", "rebobinar")
ANIME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "motores", "js", "anime.min.js")
LETRA = "Shaddai Montserrat"     # pasos/letras.py: se declara si sale en la pagina
LETRA_CIFRA = "Shaddai Bebas"

# ------------------------------------------------------------ numeros

_CENTENAS = {"doscientos": 200, "doscientas": 200, "trescientos": 300,
             "trescientas": 300, "cuatrocientos": 400, "cuatrocientas": 400,
             "quinientos": 500, "quinientas": 500, "seiscientos": 600,
             "seiscientas": 600, "setecientos": 700, "setecientas": 700,
             "ochocientos": 800, "ochocientas": 800, "novecientos": 900,
             "novecientas": 900}


def _numero(pl, i):
    """Un numero dicho desde i (hasta 999.999) o en cifras. -> (valor, sig)|None"""
    if i >= len(pl):
        return None
    w = pl[i].replace(".", "")
    if w.isdigit():
        return int(w), i + 1
    total, j = 0, i
    if w == "mil":
        total, j = 1000, i + 1
    else:
        if w in _CENTENAS:
            total, j = _CENTENAS[w], i + 1
            r = citas._numero(pl, j)
            if r:
                total, j = total + r[0], r[1]
        else:
            r = citas._numero(pl, i)
            if not r:
                return None
            total, j = r
        if j < len(pl) and pl[j] == "mil":
            total, j = total * 1000, j + 1
        else:
            return total, j
    # «... mil cuatrocientos»
    if j < len(pl) and pl[j] in _CENTENAS:
        total += _CENTENAS[pl[j]]
        j += 1
    r = citas._numero(pl, j) if j < len(pl) else None
    if r and r[0] < 100:
        total, j = total + r[0], r[1]
    return total, j


# ------------------------------------------------------------ la voz

class _Voz:
    """Palabras del plano con su tiempo RELATIVO al plano."""

    def __init__(self, escena):
        self.t_in = float(escena.get("t_in") or 0.0)
        self.dur = max(0.1, float(escena.get("t_out") or self.t_in + 1) - self.t_in)
        self.crudas = str(escena.get("narracion") or "").split()
        self.pl = [citas.plegar(w) for w in self.crudas]
        marcas = escena.get("marcas") or []
        n = len(self.crudas)
        try:
            ok = n and len(marcas) == n
            self.tiempos = [float(a) - self.t_in for a, _ in marcas] if ok else None
        except (TypeError, ValueError):
            self.tiempos = None
        if self.tiempos is None:
            paso = self.dur / max(1, n)
            self.tiempos = [paso * k for k in range(n)]

    def t(self, i):
        if not self.tiempos:
            return 0.0
        i = max(0, min(len(self.tiempos) - 1, int(i)))
        return max(0.0, min(self.dur - 0.3, self.tiempos[i]))

    def momento(self, en, defecto=0.0):
        if en is None:
            return defecto
        if isinstance(en, (int, float)):
            return max(0.0, min(self.dur - 0.3, float(en)))
        objetivo = citas.plegar(str(en).split()[0])
        for i, w in enumerate(self.pl):
            if objetivo and w.startswith(objetivo):
                return self.t(i)
        return defecto


# ------------------------------------------------------------ automaticos

_COSAS = {"ano": "AÑO", "anos": "AÑOS", "dia": "DÍA", "dias": "DÍAS",
          "noches": "NOCHES", "horas": "HORAS", "siglos": "SIGLOS",
          "generaciones": "GENERACIONES", "veces": "VECES", "monedas": "MONEDAS",
          "hermanos": "HERMANOS", "hijos": "HIJOS", "hombres": "HOMBRES",
          "personas": "PERSONAS", "km": "KM", "kilometros": "KM",
          "soldados": "SOLDADOS", "piezas": "PIEZAS", "siclos": "SICLOS"}
_SELLOS = (("nunca", "NUNCA"), ("jamas", "JAMÁS"), ("falso", "FALSO"),
           ("mentira", "MENTIRA"), ("prohibido", "PROHIBIDO"))
_NO_ERA = ("era", "fue", "es", "hubo", "tenia", "estaba", "fueron", "eran")
_NO_DICE = ("dice", "dijo", "dicen", "menciona", "ensena", "afirma", "cuenta")
_LO_DICHO = ("eso", "esto", "nada", "que", "tal", "asi")
#: «Primera.», «Segundo,»: el que abre la frase y va solo marca un punto de
#: una lista («cuatro veces en que...»); de ahi sale el marcador 1/4...4/4
_ORDINALES = {"primera": 1, "primero": 1, "segunda": 2, "segundo": 2,
              "tercera": 3, "tercero": 3, "cuarta": 4, "cuarto": 4,
              "quinta": 5, "quinto": 5, "sexta": 6, "sexto": 6,
              "septima": 7, "septimo": 7, "octava": 8, "octavo": 8,
              "novena": 9, "noveno": 9, "decima": 10, "decimo": 10}
_REBOBINAR = ("retroceder", "retrocedamos", "rebobinar", "rebobinemos",
              "volvamos")
_DATO = (("sabias", "que"), ("dato",), ("curiosamente",), ("pocos", "saben"),
         ("nadie", "sabe"), ("en", "hebreo"), ("en", "griego"),
         ("en", "arameo"))
_VACIAS = {"el", "la", "los", "las", "un", "una", "de", "del", "y", "o", "que",
           "su", "sus", "a", "al", "en"}


def _cifra(v, siguiente=None):
    """La primera cifra que merece placa. -> rotulo|None

    Como la cita, «cuatro» | «veces» puede quedar partido por el corte: se
    miran tambien las palabras del plano siguiente, pero la cifra tiene que
    EMPEZAR en este.
    """
    mias = len(v.pl)
    pl = v.pl + [citas.plegar(w) for w in (siguiente or [])]
    for i, w in enumerate(pl):
        if i >= mias:
            break
        # «el día 3», «día tres»
        if w == "dia" and i + 1 < len(pl):
            r = _numero(pl, i + 1)
            if r and 0 < r[0] < 1000:
                return {"tipo": "cifra", "valor": r[0], "antes": "DÍA",
                        "despues": "", "t": v.t(i)}
        r = _numero(pl, i)
        if not r or r[0] < 2:
            continue
        valor, j = r
        if j < len(pl) and pl[j] in ("de", "mil") and j + 1 < len(pl) \
                and pl[j + 1] in _COSAS and pl[j] == "de":
            j += 1
        if j < len(pl) and pl[j] in _COSAS:
            # no las horas de una cita («capitulo 3»), solo cosas contadas
            # «más de 400» / «más 400» -> «+400»
            mas = "mas" in pl[max(0, i - 2):i] and (pl[i - 1] in ("mas", "de"))
            return {"tipo": "cifra", "valor": valor,
                    "antes": "+" if mas else "",
                    "despues": _COSAS[pl[j]], "t": v.t(i)}
    return None


def _sello(v):
    pl = v.pl
    for i, w in enumerate(pl):
        for clave, texto in _SELLOS:
            if w == clave:
                return {"tipo": "sello", "texto": texto, "t": v.t(i)}
        if w == "sin" and i + 1 < len(pl):
            k = i + 1
            while k < len(pl) and pl[k] in _VACIAS:
                k += 1
            if k < len(pl) and len(pl[k]) >= 3:
                nombre = v.crudas[k].strip("«»“”\"(),.;:!?¿¡").upper()
                if nombre:
                    return {"tipo": "sello", "texto": "SIN " + nombre,
                            "t": v.t(k)}
        if w == "no" and i + 1 < len(pl) and pl[i + 1] in _NO_ERA:
            return {"tipo": "sello", "texto": "NO", "t": v.t(i)}
        # «La Biblia no dice eso», «no dice que...», «no menciona nada»; pero
        # «el texto no dice quien es» solo calla, no desmiente: sin sello
        if (w == "no" and i + 2 < len(pl) and pl[i + 1] in _NO_DICE
                and pl[i + 2] in _LO_DICHO):
            return {"tipo": "sello", "texto": "NO", "t": v.t(i)}
    return None


def _rebobinar(v):
    pl = v.pl
    t = None
    for i, w in enumerate(pl):
        if w in _REBOBINAR or (w == "atras" and i and pl[i - 1] in ("volver", "mas")):
            t = v.t(i)
            break
    # «25 años antes», «años atrás»
    menos = ""
    for i, w in enumerate(pl):
        if w in ("anos", "siglos") and i + 1 < len(pl) and pl[i + 1] in ("antes", "atras"):
            k = i - 1
            while k >= 0 and pl[k] not in ("", ) and k >= i - 4:
                r = _numero(pl, k)
                if r and r[1] == i:
                    menos = f"−{r[0]} {_COSAS.get(w, w.upper())}"
                    break
                k -= 1
            if t is None and menos:
                t = v.t(i)
            break
    if t is None:
        return None
    return {"tipo": "rebobinar", "texto": "REBOBINANDO", "menos": menos, "t": t}


def _dato(v):
    pl = v.pl
    for i in range(len(pl)):
        for frase in _DATO:
            if tuple(pl[i:i + len(frase)]) == frase:
                palabra = ""
                if frase[0] == "en" and i + 2 < len(pl):
                    # «en hebreo, "jesed"»: la palabra que sigue
                    palabra = v.crudas[i + 2].strip("«»“”\"(),.;:!?¿¡")
                    if citas.plegar(palabra) in _VACIAS or len(palabra) < 3:
                        palabra = ""
                return {"tipo": "dato", "texto": "DATO",
                        "palabra": palabra.upper(), "t": v.t(i)}
    return None


def _pastilla(v, siguiente=None):
    """La cita que EMPIEZA en este plano, aunque acabe en el siguiente.

    El corte parte una cita dicha en palabras por donde cae la pausa: «El
    Salmo ciento cuarenta y siete,» | «versiculo cuatro, habla...». Por eso
    se buscan las palabras de este plano seguidas de las del siguiente, y
    vale la cita que arranca aqui. Sin versiculo vale si se dijo «capitulo»
    («Lee Lucas capitulo uno» -> LUCAS 1), igual que en la Biblia 3D.
    """
    mias = len(v.crudas)
    for c in citas.buscar(v.crudas + list(siguiente or [])):
        if c["inicio"] >= mias:
            break
        dicho_cap = any(w in citas.CAPITULO for w in v.pl[c["libro_fin"]:c["fin"]])
        if c["v1"] or dicho_cap:
            return {"tipo": "pastilla", "texto": c["cita"].upper(),
                    "t": v.t(c["inicio"])}
    return None


def automaticos(escena, siguiente=None):
    """Los rotulos que salen solos de la narracion del plano. -> [rotulo]

    `siguiente` son las palabras del plano de despues: solo sirven para
    acabar una cita que el corte partio en dos.
    """
    v = _Voz(escena)
    salida = []
    for f in (_pastilla, _rebobinar, _cifra, _dato, _sello):
        r = f(v, siguiente) if f in (_pastilla, _cifra) else f(v)
        if r:
            salida.append(r)
    # la placa de cifra y el DATO comparten esquina de arriba: uno por plano
    tipos = [r["tipo"] for r in salida]
    if "cifra" in tipos and "dato" in tipos:
        salida = [r for r in salida if r["tipo"] != "dato"]
    return salida


def _a_mano(escena, lista):
    v = _Voz(escena)
    salida = []
    for r in lista:
        if not isinstance(r, dict) or r.get("tipo") not in TIPOS:
            continue
        r = dict(r)
        r["t"] = v.momento(r.pop("en", None))
        if r["tipo"] == "cifra":
            try:
                r["valor"] = int(r.get("valor"))
            except (TypeError, ValueError):
                continue
            r.setdefault("antes", "")
            r.setdefault("despues", "")
        else:
            r["texto"] = str(r.get("texto") or ("DATO" if r["tipo"] == "dato"
                                               else "")).upper()
            if not r["texto"] and r["tipo"] != "rebobinar":
                continue
            if r["tipo"] == "rebobinar":
                r["texto"] = r["texto"] or "REBOBINANDO"
                r.setdefault("menos", "")
            if r["tipo"] == "dato":
                r["palabra"] = str(r.get("palabra") or "").upper()
        salida.append(r)
    return salida


# ------------------------------------------------------------ el video

def activos(p):
    return (p or {}).get("rotulos") is not False


def _ordinal(v):
    """(n, i) si el plano trae un «Primera.» / «Segundo,» que abre frase."""
    for i, w in enumerate(v.pl):
        if w not in _ORDINALES:
            continue
        abre = i == 0 or v.crudas[i - 1][-1:] in ".!?:»"
        suelto = v.crudas[i][-1:] in ".,:;"
        if abre and suelto:
            return _ORDINALES[w], i
    return None


def _marcadores(hechos):
    """El marcador «1/4»...«4/4» de una lista que se cuenta en voz alta.

    Solo si en el video salen seguidos (por orden de aparicion) desde la
    «Primera» hasta al menos la «Segunda»; el total es el ultimo de la serie.
    Va en la placa de cifra (rodillos), y manda sobre otra cifra del plano.
    """
    vistos = []
    for k, (e, propios, items) in enumerate(hechos):
        if isinstance(propios, list) or propios is False:
            continue
        v = _Voz(e)
        r = _ordinal(v)
        if r:
            vistos.append((k, r[0], v.t(r[1])))
    serie, espera = [], 1
    for k, n, t in vistos:
        if n == espera:
            serie.append((k, n, t))
            espera += 1
        elif n == 1:                     # empieza otra lista: vale la ultima
            serie, espera = [(k, n, t)], 2
    if len(serie) < 2:
        return
    total = serie[-1][1]
    for k, n, t in serie:
        items = hechos[k][2]
        items[:] = [r for r in items if r["tipo"] not in ("cifra", "dato")]
        items.append({"tipo": "cifra", "valor": n, "antes": "",
                      "despues": f"/ {total}", "t": t})


def _bloque(escena):
    """El bloque del guion del que sale el plano (B003), o '' si no se sabe."""
    return str((escena.get("origen") or {}).get("bloque") or "")


def preparar(escenas, p, ancho, alto):
    """Los rotulos de TODO el video, por plano. -> {id: conf}

    Se recorre en orden porque la pastilla de la cita se HEREDA: entra en el
    plano donde se nombra y sigue arriba, quieta, en los siguientes. Pero al
    empezar un bloque del guion que cita OTRA cosa, la vieja se quita: si no,
    «DANIEL 10:11» seguia arriba con la narracion ya en Abraham, hasta que
    se nombraba Genesis. Un bloque que no cita nada la conserva (sigue
    hablando de lo mismo).
    """
    if not activos(p):
        return {}
    planos = [e for e in escenas if not e.get("cartela")]
    hechos = []
    for k, e in enumerate(planos):
        propios = e.get("rotulos")
        if propios is False:
            items = []
        elif isinstance(propios, list):
            items = _a_mano(e, propios)
        else:
            sig = (str(planos[k + 1].get("narracion") or "").split()
                   if k + 1 < len(planos) else None)
            items = automaticos(e, sig)
        hechos.append((e, propios, items))
    _marcadores(hechos)
    con_cita = {_bloque(e) for e, _p, items in hechos
                if _bloque(e) and any(r["tipo"] == "pastilla" for r in items)}
    confs, fija, bloque_fija = {}, None, ""
    for e, propios, items in hechos:
        sid = e.get("id")
        b = _bloque(e)
        if fija and b and b != bloque_fija and b in con_cita:
            fija = None                  # este bloque nombra la suya
        nueva = next((r for r in items if r["tipo"] == "pastilla"), None)
        if nueva:
            fija, bloque_fija = nueva["texto"], b
        elif fija and propios is not False:
            items.insert(0, {"tipo": "pastilla", "texto": fija, "t": 0.0,
                             "fija": True})
        if items:
            confs[sid] = {"W": int(ancho), "H": int(alto), "items": items}
    return confs


def resumen(conf):
    if not conf:
        return "sin rotulos"
    return "rotulos: " + ", ".join(
        f"{r['tipo']}" + ("" if r.get("fija") else f"@{r['t']:.1f}s")
        for r in conf["items"])


def json_conf(conf):
    return json.dumps(conf, ensure_ascii=False)


def css(conf):
    if not conf:
        return ""
    W, H = conf["W"], conf["H"]
    b = min(W, H)
    vertical = H > W
    arriba = int(H * (0.05 if vertical else 0.045))
    bajo_pastilla = int(H * (0.115 if vertical else 0.15))
    return f"""
#rotulos{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;z-index:2;
  pointer-events:none;font-family:'{LETRA}',sans-serif;color:#fff}}
#rotulos .rt{{position:absolute;opacity:0;will-change:transform,opacity}}
.rt-pastilla{{left:50%;top:{arriba}px;transform:translateX(-50%);
  background:#C62828;padding:{b*.012:.0f}px {b*.032:.0f}px;border-radius:{b*.05:.0f}px;
  font-size:{b*.036:.0f}px;letter-spacing:.06em;white-space:nowrap;
  box-shadow:0 {b*.006:.0f}px {b*.02:.0f}px rgba(0,0,0,.35);
  border:{max(2,b*.003):.0f}px solid rgba(255,255,255,.85)}}
.rt-pastilla .ico{{display:inline-block;margin-right:.45em;opacity:.9}}
.rt-sello{{left:50%;top:{H*.30:.0f}px;color:#D32020;
  font-size:{b*.11:.0f}px;letter-spacing:.04em;padding:.06em .28em;
  border:{b*.012:.0f}px solid #D32020;border-radius:{b*.016:.0f}px;
  filter:url(#rt-tinta) drop-shadow(0 0 {b*.01:.0f}px rgba(0,0,0,.45));
  white-space:nowrap;background:rgba(255,248,238,.16)}}
.rt-dato{{left:{W*.05:.0f}px;top:{bajo_pastilla}px;display:flex;align-items:center;
  gap:{b*.014:.0f}px}}
.rt-dato .tag{{background:#FFC845;color:#1C1530;font-size:{b*.034:.0f}px;
  padding:{b*.008:.0f}px {b*.02:.0f}px;border-radius:{b*.01:.0f}px;letter-spacing:.12em}}
.rt-dato .pal{{background:rgba(20,16,40,.82);font-size:{b*.044:.0f}px;
  padding:{b*.008:.0f}px {b*.024:.0f}px;border-radius:{b*.01:.0f}px;
  font-family:'Shaddai Playfair',serif;font-style:italic}}
.rt-cifra{{right:{W*.05:.0f}px;top:{bajo_pastilla}px;background:rgba(20,16,40,.86);
  border:{max(2,b*.004):.0f}px solid #FFC845;border-radius:{b*.02:.0f}px;
  padding:{b*.01:.0f}px {b*.026:.0f}px;display:flex;align-items:center;
  gap:{b*.016:.0f}px;font-family:'{LETRA_CIFRA}','{LETRA}',sans-serif;
  color:#FFC845;box-shadow:0 0 {b*.03:.0f}px rgba(255,200,69,.35)}}
.rt-cifra .txt{{font-size:{b*.06:.0f}px;line-height:1;color:#fff}}
.rt-cifra .num{{display:flex;clip-path:inset(0);font-size:{b*.1:.0f}px;line-height:1;height:1em;
  overflow:hidden;text-shadow:0 0 {b*.02:.0f}px rgba(255,200,69,.6)}}
.rt-cifra .col{{display:flex;flex-direction:column}}
.rt-cifra .col span{{height:1em;display:block;text-align:center}}
.rt-rebobinar{{left:{W*.05:.0f}px;top:{bajo_pastilla}px;font-size:{b*.05:.0f}px;
  letter-spacing:.08em;text-shadow:{b*.004:.0f}px 0 #FF2D55,-{b*.004:.0f}px 0 #2DE1FF}}
.rt-rebobinar .menos{{display:block;font-size:{b*.075:.0f}px;color:#FFC845}}
#rt-cinta{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;opacity:0;
  background:repeating-linear-gradient(0deg,rgba(255,255,255,.07) 0 2px,
  rgba(0,0,0,0) 2px 5px);mix-blend-mode:screen}}
#rt-cinta .banda{{position:absolute;left:0;width:{W}px;height:{H*.07:.0f}px;
  top:0;background:linear-gradient(180deg,rgba(255,255,255,0),
  rgba(255,255,255,.22),rgba(255,255,255,0))}}
"""


def html(conf):
    if not conf:
        return ""
    # el filtro de tinta del sello: borde comido, como un sello de goma
    return ('<svg width="0" height="0" style="position:absolute">'
            '<filter id="rt-tinta"><feTurbulence type="fractalNoise" '
            'baseFrequency="0.9" numOctaves="2" seed="7" result="r"/>'
            '<feColorMatrix in="r" type="matrix" values="0 0 0 0 0  0 0 0 0 0'
            '  0 0 0 0 0  0 0 0 -0.9 1.4" result="m"/>'
            '<feComposite in="SourceGraphic" in2="m" operator="in"/></filter>'
            '</svg><div id="rotulos"></div>')


def js(conf):
    """anime.js + el constructor. Vacio sin rotulos."""
    if not conf:
        return ""
    with open(ANIME, encoding="utf-8") as f:
        anime = f.read()
    return anime + "\n" + ROTULOS_JS


ROTULOS_JS = r"""
// LOS ROTULOS (pasos/rotulos.py): cada uno es una linea de tiempo de anime.js
// parada (autoplay:false) que `rotulosPintar` busca en el instante del fotograma.
const RT_LINEAS = [];
(function(){
  const caja = document.getElementById('rotulos');
  if (!caja || !RT) return;
  function el(clase, dentro){
    const d = document.createElement('div');
    d.className = 'rt ' + clase;
    if (dentro !== undefined) d.textContent = dentro;
    caja.appendChild(d);
    return d;
  }
  function linea(t){
    const tl = anime.timeline({autoplay: false});
    RT_LINEAS.push({tl: tl, t: t});
    return tl;
  }
  RT.items.forEach(function(r){
    const t = Math.max(0, r.t || 0) * 1000;
    if (r.tipo === 'pastilla'){
      const d = el('rt-pastilla');
      const i = document.createElement('span'); i.className = 'ico'; i.textContent = '✝';
      d.appendChild(i); d.appendChild(document.createTextNode(r.texto));
      if (r.fija){ d.style.opacity = 1; return; }
      linea(t).add({targets: d, opacity: [0, 1], translateX: ['-50%', '-50%'],
        translateY: ['-140%', '0%'], scale: [0.6, 1], duration: 900,
        easing: 'easeOutElastic(1, .6)'});
    } else if (r.tipo === 'sello'){
      const d = el('rt-sello', r.texto);
      // centrado a mano: el transform es de anime (giro y escala)
      d.style.marginLeft = (-d.offsetWidth / 2) + 'px';
      const giro = -8 - ((r.texto.length * 7) % 9);
      linea(t)
        .add({targets: d, opacity: [0, 1], scale: [3.2, 0.92],
              rotate: [giro - 14, giro], duration: 230, easing: 'easeInQuad'})
        .add({targets: d, scale: [0.92, 1], duration: 260,
              easing: 'easeOutBack'})
        // el golpe: tiembla el cuadro entero, con un 3 % de zoom para no
        // enseñar el borde negro de detras
        .add({targets: '#lienzo', translateX: [0, -7, 6, -3, 0],
              translateY: [0, 5, -4, 2, 0], scale: [1, 1.03, 1.03, 1.03, 1],
              duration: 260,
              easing: 'linear'}, 230);
    } else if (r.tipo === 'dato'){
      const d = el('rt-dato');
      const tag = document.createElement('span'); tag.className = 'tag';
      tag.textContent = r.texto || 'DATO'; d.appendChild(tag);
      let pal = null;
      if (r.palabra){
        pal = document.createElement('span'); pal.className = 'pal';
        pal.textContent = '«' + r.palabra.toLowerCase() + '»';
        d.appendChild(pal);
      }
      const tl = linea(t)
        .add({targets: d, opacity: [0, 1], translateX: [-60, 0], duration: 500,
              easing: 'easeOutExpo'})
        .add({targets: tag, scale: [1, 1.18, 1], duration: 380,
              easing: 'easeInOutSine'}, 300);
      if (pal) tl.add({targets: pal, opacity: [0, 1], translateY: [30, 0],
                       duration: 520, easing: 'easeOutBack'}, 420);
    } else if (r.tipo === 'cifra'){
      const d = el('rt-cifra');
      if (r.antes){
        const a = document.createElement('span'); a.className = 'txt';
        a.textContent = r.antes; d.appendChild(a);
      }
      const num = document.createElement('span'); num.className = 'num';
      d.appendChild(num);
      const cifras = String(r.valor).split('');
      const tl = linea(t).add({targets: d, opacity: [0, 1], scale: [0.4, 1],
        duration: 450, easing: 'easeOutBack'});
      cifras.forEach(function(c, k){
        // un rodillo por cifra: 0..9 dos vueltas y la cifra buena al final
        const col = document.createElement('span'); col.className = 'col';
        for (let n = 0; n < 20; n++){
          const s = document.createElement('span'); s.textContent = n % 10;
          col.appendChild(s);
        }
        const fin = document.createElement('span'); fin.textContent = c;
        col.appendChild(fin);
        num.appendChild(col);
        tl.add({targets: col, translateY: ['0em', '-20em'],
                duration: 1100 + 260 * k, easing: 'cubicBezier(.15,.75,.25,1)'},
               150);
      });
      if (r.despues){
        const b = document.createElement('span'); b.className = 'txt';
        b.textContent = r.despues; d.appendChild(b);
      }
      tl.add({targets: num, scale: [1, 1.15, 1], duration: 360,
              easing: 'easeInOutSine'});
    } else if (r.tipo === 'rebobinar'){
      const d = el('rt-rebobinar');
      d.textContent = '◀◀ ' + (r.texto || 'REBOBINANDO');
      if (r.menos){
        const m = document.createElement('span'); m.className = 'menos';
        m.textContent = r.menos; d.appendChild(m);
      }
      const cinta = document.createElement('div'); cinta.id = 'rt-cinta';
      const banda = document.createElement('div'); banda.className = 'banda';
      cinta.appendChild(banda); caja.insertBefore(cinta, caja.firstChild);
      linea(t)
        .add({targets: cinta, opacity: [0, 1, 1, 0], duration: 2600,
              easing: 'linear'}, 0)
        .add({targets: banda, top: ['-10%', '105%'], duration: 1300,
              easing: 'linear'}, 0)
        .add({targets: banda, top: ['-10%', '105%'], duration: 1300,
              easing: 'linear'}, 1300)
        .add({targets: d, opacity: [0, 1, 0.25, 1, 0.25, 1, 1, 0],
              duration: 2600, easing: 'steps(8)'}, 0);
    }
  });
  // ida y vuelta: asi cada hijo de la linea pinta su estado INICIAL al
  // buscar un instante anterior a su entrada (anime no lo hace en frio)
  RT_LINEAS.forEach(function(l){ l.tl.seek(l.tl.duration); l.tl.seek(0); });
})();
function rotulosPintar(t){
  const ms = t * 1000;
  for (let k = 0; k < RT_LINEAS.length; k++){
    const l = RT_LINEAS[k];
    l.tl.seek(Math.max(0, ms - l.t));
  }
}
"""
