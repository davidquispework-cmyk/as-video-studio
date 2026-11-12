"""PANTALLA PARTIDA y TONO POR PLANO (plan NIVEL PROFESIONAL, etapa P2).

Dos recursos de los videos de referencia, en una sola capa del render:

    partida   el cuadro se parte en dos («ÉXODO | MATEO») con una raya roja en
              medio: A es la imagen del plano ANTERIOR y B la de este, cada una
              con su etiqueta. En horizontal van lado a lado; en vertical, una
              encima de la otra (dos mitades de 540 px de ancho no se leen).
    tono      el color del plano: «papel» (beige envejecido, grano de papel y
              viñeta calida) o «noche» (oscuro, frio, con viñeta roja). Cambia
              de un plano a otro dentro del MISMO video, como en Abimelec.

Salen SOLOS leyendo la narracion (`automaticos`):
    partida   la frase compara («igual que», «así como», «en cambio», «a
              diferencia de», «mientras que», «frente a», «espejo»…) o nombra
              DOS libros distintos. Las etiquetas son los libros citados (los
              de este plano, o el ultimo citado antes y el de ahora).
    tono      «noche» si habla de noche, tinieblas, sangre, matar, traicion…;
              «papel» si rebobina («años antes», «retroceder») o habla de lo
              escrito (pergamino, papiro, profecía, «está escrito»).

Como se gobierna (nada de esto va en los defectos del paso: no mueve firmas):
    params del render  "partida": false        sin pantallas partidas
                       "tono": "normal"         sin tono automatico
                       "tono": "papel"|"noche"  ese tono en TODO el video
    plan.json, escena  "partida": false          ese plano no se parte
                       "partida": {"a": "S004", "eti_a": "ÉXODO",
                                   "eti_b": "MATEO", "en": "igual"}
                                   a mano (`a` = plano cuya imagen va en A;
                                   `en` = segundos o una palabra de la voz)
                       "tono": "papel"|"noche"|"normal"   manda sobre todo
Sin motion graphics: ese modo pinta su propio mundo y no lleva esta capa.
"""
import json
import os

try:
    import citas
    import rotulos
except ImportError:  # importado como paquete (pasos.partida)
    from . import citas
    from . import rotulos

TONOS = ("papel", "noche")
LETRA = rotulos.LETRA

_COMPARA = (("igual", "que"), ("asi", "como"), ("lo", "mismo", "que"),
            ("en", "cambio"), ("a", "diferencia"), ("mientras", "que"),
            ("frente", "a"), ("versus",), ("vs",), ("espejo",), ("paralelo",),
            ("comparado",), ("comparemos",), ("compara",))
_NOCHE = {"noche", "tinieblas", "oscuridad", "oscuro", "oscura", "sangre",
          "mato", "mataron", "matar", "asesino", "asesinato", "asesinaron",
          "traicion", "traiciono", "traidor", "masacre", "degollo", "maldicion",
          "maldito", "infierno", "tumba", "sepulcro", "muerte"}
_PAPEL = {"pergamino", "papiro", "manuscrito", "rollo", "profecia", "profeta",
          "escrito", "escribio", "genealogia"}
_PAPEL_PARES = (("anos", "antes"), ("siglos", "antes"), ("hace", "siglos"),
                ("esta", "escrito"))


def _busca(pl, frases):
    """Indice de la primera frase de `frases` en las palabras plegadas, o None."""
    for i in range(len(pl)):
        for f in frases:
            if tuple(pl[i:i + len(f)]) == f:
                return i
    return None


# Libros cuyo nombre es tambien una palabra corriente («los hechos», «los
# jueces», «los romanos»): sin capitulo detras no se toman por libro.
_DUDOSOS = {"hechos", "numeros", "jueces", "reyes", "cronicas", "lamentaciones",
            "cantares", "proverbios", "hebreos", "romanos"}


def _libros(v):
    """Libros nombrados en el plano, en orden y sin repetir.

    Vale la cita entera («Mateo capítulo veintiséis») y tambien el nombre a
    secas con mayuscula («Génesis y Apocalipsis»), salvo los dudosos.
    """
    con_cita = {c["inicio"]: c["libro"].upper() for c in citas.buscar(v.crudas)}
    vistos = []
    for i, (cruda, w) in enumerate(zip(v.crudas, v.pl)):
        nombre = con_cita.get(i)
        if (not nombre and w in citas.LIBROS and w not in _DUDOSOS
                and cruda[:1].isupper() and (i == 0 or v.pl[i - 1] not in ("los", "las"))):
            nombre = citas.LIBROS[w].upper()
        if nombre and nombre not in vistos:
            vistos.append(nombre)
    return vistos


def tono_auto(v):
    pl = set(v.pl)
    if rotulos._rebobinar(v):
        return "papel"
    if _busca(v.pl, _PAPEL_PARES) is not None or pl & _PAPEL:
        return "papel"
    if pl & _NOCHE:
        return "noche"
    return None


def partida_auto(v, libro_antes):
    """-> {"t", "eti_a", "eti_b"} | None"""
    if v.dur < 2.0:
        return None
    libros = _libros(v)
    i = _busca(v.pl, _COMPARA)
    if i is None and len(libros) < 2:
        return None
    if len(libros) >= 2:
        a, b = libros[0], libros[1]
    else:
        b = libros[0] if libros else ""
        a = libro_antes if libro_antes and libro_antes != b else ""
    t = v.t(i) if i is not None else 0.0
    return {"t": round(t if t > 0.3 else 0.0, 3), "eti_a": a, "eti_b": b}


def activa(p):
    return (p or {}).get("partida") is not False


def tono_base(p):
    v = (p or {}).get("tono")
    return v if v in TONOS + ("normal",) else None


def preparar(escenas, p, ancho, alto, imagen_de):
    """La capa de TODO el video, por plano. -> {id: conf}

    `imagen_de(id)` da la ruta de la imagen de un plano (o None). Se recorre en
    orden: la mitad A de una pantalla partida es la imagen del plano anterior
    (la cartela no cuenta), y su etiqueta, el ultimo libro citado antes.
    """
    confs = {}
    base = tono_base(p)
    previa, libro_antes = None, ""
    por_id = {e.get("id"): e for e in escenas}
    for e in escenas:
        sid = e.get("id")
        if e.get("cartela"):
            continue
        v = rotulos._Voz(e)
        conf = {}
        # --- el tono
        propio = e.get("tono")
        if propio in TONOS + ("normal",):
            tono = propio
        elif base:
            tono = base
        else:
            tono = tono_auto(v)
        if tono in TONOS:
            conf["tono"] = tono
        # --- la pantalla partida
        manual = e.get("partida")
        pt = None
        if isinstance(manual, dict):
            otra = manual.get("a")
            img_a = imagen_de(otra) if otra in por_id else previa
            pt = {"t": round(v.momento(manual.get("en"), 0.0), 3),
                  "eti_a": str(manual.get("eti_a") or "").upper(),
                  "eti_b": str(manual.get("eti_b") or "").upper()}
        elif manual is not False and activa(p):
            img_a = previa
            pt = partida_auto(v, libro_antes)
        propia = imagen_de(sid)
        if pt and img_a and propia and os.path.exists(img_a) and os.path.exists(propia):
            pt.update(a=img_a, b=propia)
            conf["partida"] = pt
        if conf:
            conf.update(W=int(ancho), H=int(alto))
            confs[sid] = conf
        libros = _libros(v)
        if libros:
            libro_antes = libros[-1]
        if propia and os.path.exists(propia):
            previa = propia
    return confs


def resumen(conf):
    if not conf:
        return "sin partida ni tono"
    trozos = []
    if conf.get("tono"):
        trozos.append(f"tono {conf['tono']}")
    pt = conf.get("partida")
    if pt:
        eti = " | ".join(x for x in (pt["eti_a"] or "A", pt["eti_b"] or "B"))
        trozos.append(f"partida «{eti}» @{pt['t']:.1f}s")
    return ", ".join(trozos)


def _url(ruta):
    return "file:///" + os.path.abspath(ruta).replace("\\", "/").lstrip("/")


def json_conf(conf):
    if not conf:
        return ""
    c = dict(conf)
    if c.get("partida"):
        c["partida"] = dict(c["partida"], a=_url(c["partida"]["a"]),
                            b=_url(c["partida"]["b"]))
    return json.dumps(c, ensure_ascii=False)


# El grano del papel: ruido de SVG (feTurbulence), sin azar de JavaScript, asi
# que el mismo fotograma sale igual en cualquier lote.
_GRANO = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' "
          "width='300' height='300'><filter id='g'><feTurbulence "
          "type='fractalNoise' baseFrequency='.85' numOctaves='3' seed='7'/>"
          "<feColorMatrix values='0 0 0 0 .45 0 0 0 0 .33 0 0 0 0 .18 0 0 0 .55 0'/>"
          "</filter><rect width='300' height='300' filter='url(%23g)'/></svg>")

_FILTRO = {"papel": "sepia(.6) saturate(.75) contrast(.94) brightness(1.05)",
           "noche": "brightness(.6) saturate(.65) contrast(1.15) hue-rotate(-10deg)"}


def css(conf):
    if not conf:
        return ""
    W, H = conf["W"], conf["H"]
    b = min(W, H)
    vertical = H > W
    salida = [f"#partida,#tono{{position:absolute;left:0;top:0;width:{W}px;"
              f"height:{H}px;pointer-events:none}}",
              "#partida{z-index:1;opacity:0;overflow:hidden}",
              "#tono{z-index:1}",
              ".pt-tono{position:absolute;left:0;top:0;width:100%;height:100%}"]
    tono = conf.get("tono")
    if tono:
        salida.append(f"#camara,#partida .pt-img{{filter:{_FILTRO[tono]}}}")
    if tono == "papel":
        salida.append(
            "#tono,.pt-tono{background:radial-gradient(ellipse at center,"
            "rgba(0,0,0,0) 55%,rgba(92,60,22,.42) 100%),"
            f"url(\"{_GRANO}\");background-size:100% 100%,300px 300px;"
            "mix-blend-mode:multiply}")
    elif tono == "noche":
        salida.append(
            "#tono,.pt-tono{background:radial-gradient(ellipse at center,"
            "rgba(0,0,0,0) 45%,rgba(110,0,0,.55) 100%),"
            "linear-gradient(rgba(12,20,70,.32),rgba(12,20,70,.32));"
            "mix-blend-mode:multiply}")
    if conf.get("partida"):
        if vertical:
            mitad = (f"width:{W}px;height:{H / 2:.0f}px;left:0")
            a, bb = "top:0", f"top:{H / 2:.0f}px"
            raya = (f"left:0;top:{H / 2 - b * .006:.0f}px;width:{W}px;"
                    f"height:{b * .012:.0f}px")
            eti_a = f"left:{b * .05:.0f}px;top:{H * .125:.0f}px"
            eti_b = f"left:{b * .05:.0f}px;top:{H / 2 + b * .05:.0f}px"
        else:
            mitad = (f"width:{W / 2:.0f}px;height:{H}px;top:0")
            a, bb = "left:0", f"left:{W / 2:.0f}px"
            raya = (f"top:0;left:{W / 2 - b * .006:.0f}px;height:{H}px;"
                    f"width:{b * .012:.0f}px")
            eti_a = f"left:{b * .05:.0f}px;top:{H * .17:.0f}px"
            eti_b = f"left:{W / 2 + b * .05:.0f}px;top:{H * .17:.0f}px"
        salida += [
            f".pt-mitad{{position:absolute;overflow:hidden;{mitad};background:#111}}",
            f"#pt-a{{{a}}}#pt-b{{{bb}}}",
            ".pt-img{position:absolute;left:0;top:0;width:100%;height:100%;"
            "object-fit:cover;transform-origin:50% 50%}",
            f"#pt-raya{{position:absolute;{raya};background:#D32F2F;"
            f"box-shadow:0 0 {b * .02:.0f}px rgba(255,60,40,.85),"
            f"0 0 {b * .004:.0f}px #fff}}",
            f".pt-eti{{position:absolute;font-family:'{LETRA}',sans-serif;"
            f"font-size:{b * .042:.0f}px;letter-spacing:.08em;color:#fff;"
            f"background:rgba(15,15,20,.78);padding:{b * .01:.0f}px {b * .028:.0f}px;"
            f"border-left:{b * .01:.0f}px solid #D32F2F;opacity:0;white-space:nowrap}}",
            f"#pt-eti-a{{{eti_a}}}#pt-eti-b{{{eti_b}}}",
        ]
    return "\n".join(salida)


def html(conf):
    if not conf:
        return ""
    # el velo del tono va DEBAJO de la pantalla partida, y otro igual dentro
    # de ella, bajo la raya y las etiquetas: que no se apaguen con la viñeta
    trozos = ['<div id="tono"></div>'] if conf.get("tono") else []
    pt = conf.get("partida")
    velo = '<div class="pt-tono"></div>' if conf.get("tono") else ""
    if pt:
        trozos.append(
            '<div id="partida"><div class="pt-mitad" id="pt-a">'
            f'<img class="pt-img" src="{_url(pt["a"])}"></div>'
            f'<div class="pt-mitad" id="pt-b"><img class="pt-img" src="{_url(pt["b"])}">'
            f'</div>{velo}<div id="pt-raya"></div>'
            '<div class="pt-eti" id="pt-eti-a"></div>'
            '<div class="pt-eti" id="pt-eti-b"></div></div>')
    return "".join(trozos)


def js(conf):
    return PARTIDA_JS if conf and conf.get("partida") else ""


PARTIDA_JS = r"""
// LA PANTALLA PARTIDA (pasos/partida.py, P2): todo sale de `t`, sin reloj de
// pared, asi que el mismo fotograma se pinta igual en cualquier lote.
const PT_V = H > W;
const ptEl = document.getElementById('partida');
const ptA = document.getElementById('pt-a'), ptB = document.getElementById('pt-b');
const ptRaya = document.getElementById('pt-raya');
const ptEA = document.getElementById('pt-eti-a'), ptEB = document.getElementById('pt-eti-b');
ptEA.textContent = PT.partida.eti_a || ''; ptEB.textContent = PT.partida.eti_b || '';
if (!PT.partida.eti_a) ptEA.style.display = 'none';
if (!PT.partida.eti_b) ptEB.style.display = 'none';
function ptCurva(u){ u = Math.min(1, Math.max(0, u)); return 1 - Math.pow(1 - u, 3); }
function partidaPintar(t){
  const d = t - PT.partida.t;
  if (d < 0){ ptEl.style.opacity = 0; return; }
  ptEl.style.opacity = 1;
  const e = ptCurva(d / 0.55), q = (1 - e) * 100;
  ptA.style.transform = PT_V ? 'translateY(' + (-q) + '%)' : 'translateX(' + (-q) + '%)';
  ptB.style.transform = PT_V ? 'translateY(' + q + '%)' : 'translateX(' + q + '%)';
  const r = ptCurva((d - 0.3) / 0.4);
  ptRaya.style.transform = (PT_V ? 'scaleX(' : 'scaleY(') + r.toFixed(4) + ')';
  const z = 1.04 + 0.06 * Math.min(1, d / Math.max(1, DUR - PT.partida.t));
  for (const img of ptEl.querySelectorAll('.pt-img')) img.style.transform = 'scale(' + z.toFixed(4) + ')';
  const l = ptCurva((d - 0.55) / 0.35);
  for (const el of [ptEA, ptEB]){
    el.style.opacity = l;
    el.style.transform = 'translateY(' + ((1 - l) * 20).toFixed(1) + 'px)';
  }
}
"""
