"""Prueba de la camara viva y las transiciones con intencion (punto F).

    python pasos/prueba_camara.py

Sin red, sin Claude, sin claves. La parte del navegador (que la pagina del
render pinte sin errores y que nunca se vea el borde) se omite si no hay
Playwright para Python, y lo dice.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import camara  # noqa: E402
import transiciones  # noqa: E402

FALLOS = []


def comprobar(cond, texto):
    print(("  ok  " if cond else "  MAL ") + texto)
    if not cond:
        FALLOS.append(texto)


def escena(sid, t_in, texto, dur=None):
    palabras = texto.split()
    paso = (dur or 0.3 * len(palabras) + 0.6) / (len(palabras) + 1)
    marcas = [[t_in + 0.3 + i * paso, t_in + 0.3 + (i + 0.8) * paso]
              for i in range(len(palabras))]
    t_out = t_in + (dur or 0.3 * len(palabras) + 0.6)
    return {"id": sid, "t_in": t_in, "t_out": t_out, "narracion": texto,
            "marcas": marcas, "transicion": "suave"}


def prueba_camara():
    print("camara.preparar")
    es = [escena("S001", 0.0, "En el año 1606 todo cambió para siempre en la ciudad."),
          escena("S002", 3.9, "Y allí estaba Pedro, mirando el horizonte del mar azul."),
          escena("S003", 7.8, "Pero el techo cayó sobre ellos sin ningún aviso aquella noche."),
          escena("S004", 12.0, "la gente caminaba despacio por las calles del pueblo sin prisa")]
    cortes = transiciones.resolver(es, {})
    cortes["S003"] = dict(cortes["S003"], tipo="whip-pan")
    confs = camara.preparar(es, cortes, {}, semilla=7)
    comprobar(set(confs) == {"S001", "S002", "S003", "S004"}, "todos los planos tienen camara")
    comprobar(len(confs["S001"]["golpes"]) == 1, "golpe en la cifra (1606)")
    golpes = [(float(e["t_in"]) + g["t"]) for e in es for g in confs[e["id"]]["golpes"]]
    comprobar(all(b - a >= camara.RITMO_GOLPE for a, b in zip(golpes, golpes[1:])),
              f"golpes separados al menos {camara.RITMO_GOLPE} s: {golpes}")
    comprobar(len(confs["S003"]["temblores"]) == 1, "temblor en «cayó»")
    comprobar(not confs["S004"]["golpes"], "una frase normal no lleva golpe")
    comprobar(confs["S002"].get("sale", {}).get("tipo") == "pan"
              and confs["S003"].get("entra", {}).get("tipo") == "pan",
              "el latigazo arrastra la camara a los dos lados del corte")
    comprobar(camara.preparar(es, cortes, {"camara": "clasica"}) == {},
              "«clasica» deja la camara de siempre")
    sin = camara.preparar(es, cortes, {}, excluir={"S002"})
    comprobar("S002" not in sin and not sin["S003"].get("entra"),
              "una cartela no recibe camara ni arrastre")
    descuadre = dict(es[0], marcas=es[0]["marcas"][:-1])
    comprobar(not camara.preparar([descuadre], {}, {})["S001"]["golpes"],
              "texto y marcas descuadrados: sin golpe (no a destiempo)")
    return es, confs


def prueba_intencion():
    print("transiciones con intencion")
    es = [escena("S001", 0, "Todo empezó en una aldea pequeña."),
          escena("S002", 3, "Años después, la aldea era una ciudad."),
          escena("S003", 6, "Pero nadie lo esperaba."),
          escena("S004", 9, "Pero tampoco lo vieron venir."),
          escena("S005", 12, "De repente, la tierra se abrió."),
          escena("S006", 15, "Las llamas lo cubrieron todo."),
          escena("S007", 18, "¿Quién lo había provocado?"),
          escena("S008", 21, "La gente seguía trabajando como cada día.")]
    c = transiciones.resolver(es, {})
    comprobar(c["S001"]["tipo"] == "corte", "el primer plano no lleva transicion")
    comprobar(c["S002"]["tipo"] == "light-leak"
              and c["S002"].get("intencion") == "salto en el tiempo",
              f"«años después» → fuga de luz ({c['S002']['tipo']})")
    comprobar(c["S002"]["duracion"] > c["S005"]["duracion"],
              "el salto en el tiempo respira mas que el destello")
    comprobar(c["S003"]["tipo"] == "whip-pan", f"«pero» → latigazo ({c['S003']['tipo']})")
    comprobar(c["S004"]["tipo"] != "whip-pan", "dos latigazos seguidos no")
    comprobar(c["S005"]["tipo"] == "flash-through-white", "«de repente» → destello")
    comprobar(c["S006"]["tipo"] == "ridged-burn", "fuego → quemado")
    comprobar(c["S007"]["tipo"] == "sdf-iris", "pregunta → iris")
    comprobar(not c["S008"].get("intencion"), "frase sin intencion → la bolsa de siempre")
    propia = transiciones.resolver(es, {"transiciones": ["fundido", "whip-pan"]})
    comprobar(all(v["tipo"] in ("corte", "fundido", "whip-pan") for v in propia.values()),
              "con paleta elegida, la intencion solo usa las elegidas")
    apagada = transiciones.resolver(es, {"intencion": False})
    comprobar(not any(v.get("intencion") for v in apagada.values()),
              "«intencion»: false vuelve al reparto a ciegas")
    for v in c.values():
        if v["tipo"] != "corte":
            comprobar(v["shader"], f"{v['tipo']} tiene shader")
            break


def prueba_pagina(confs):
    print("pagina del render")
    try:
        from playwright.sync_api import sync_playwright
        from PIL import Image
    except ImportError:
        print("  (sin playwright/PIL para Python: omito la pagina)")
        return
    import p8_render
    tmp = tempfile.mkdtemp(prefix="prueba_camara_")
    hyper = os.path.join(tmp, "h.png")
    Image.new("RGB", (3072, 2048), (200, 40, 40)).save(hyper)
    conf = dict(confs["S003"], golpes=[{"t": 1.0, "fuerza": 1.0}],
                sale={"tipo": "zoom", "dir": 1, "dur": 0.45})
    mov = {"ventana_ini": [0.1, 0.1, 0.8, 0.8], "ventana_fin": [0.1, 0.1, 0.8, 0.8],
           "hyperframe_px": [3072, 2048]}
    pagina = p8_render._pagina_de({"t_in": 0, "t_out": 4}, mov, "<svg></svg>", hyper,
                                  {"resolucion": [1920, 1080]},
                                  os.path.join(tmp, "p.html"), cam=conf)
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(viewport={"width": 1920, "height": 1080})
        errores = []
        pag.on("pageerror", lambda e: errores.append(str(e)))
        pag.goto("file://" + pagina)
        bordes = []
        for i in range(0, 121, 3):
            t = i / 30.0
            pag.evaluate(f"pintar({t})")
            r = pag.evaluate("(() => { const b = document.getElementById('camara')"
                             ".getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; })()")
            if r[0] > 0.5 or r[1] > 0.5 or r[2] < 1919.5 or r[3] < 1079.5:
                bordes.append((round(t, 2), [round(x) for x in r]))
        k1 = pag.evaluate("extraCam(0.95, true)")
        k2 = pag.evaluate("extraCam(1.2, true)")
        nav.close()
    comprobar(not errores, f"la pagina pinta sin errores {errores[:1]}")
    comprobar(not bordes, f"nunca se ve el borde {bordes[:2]}")
    escala = lambda s: float(s.split("scale(")[1].split(")")[0])  # noqa: E731
    comprobar(escala(k2) > escala(k1) * 1.03, "el golpe de zoom se nota tras la palabra")


def main():
    es, confs = prueba_camara()
    prueba_intencion()
    prueba_pagina(confs)
    print()
    if FALLOS:
        print(f"FALLAN {len(FALLOS)}")
        sys.exit(1)
    print("todo bien")


if __name__ == "__main__":
    main()
