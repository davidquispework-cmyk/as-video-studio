"""Prueba de los escenarios vectoriales y sus efectos Lottie (pasos/escenarios.py, P3).
Sin red.

    python pasos/prueba_escenarios.py            deteccion, SVG, Lottie y motion
    python pasos/prueba_escenarios.py --ver DIR  ademas pinta en Chromium todos
                                                 los escenarios (con muñecos) y
                                                 deja una hoja de contactos
"""
import json
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import escenarios  # noqa: E402
import motion  # noqa: E402
from prueba_motion import _escena  # noqa: E402


def probar_deteccion():
    d = escenarios.escenario_de
    assert d("Jonás subió a una barca en medio de la tormenta")["nombre"] == "mar"
    assert d("Las murallas de Jericó cayeron")["nombre"] == "ciudad"
    assert d("El rey se sentó en su trono")["nombre"] == "trono"
    assert d("En el altar del templo de Jerusalén")["nombre"] == "templo"   # templo > ciudad
    assert d("Construyeron la torre de Babel")["nombre"] == "torre"
    assert d("Moisés subió al monte Sinaí")["nombre"] == "monte"
    assert d("Cuarenta años en el desierto")["nombre"] == "desierto"
    assert d("El pastor buscó a sus ovejas")["nombre"] == "campo"
    assert d("Dios ama a todos") is None
    e = d("Aquella noche ardía una zarza en el desierto y brilló una luz")
    assert e["hora"] == "noche" and e["efectos"] == ["fuego", "luz"], e
    assert d("Al atardecer llegaron a la orilla del mar")["hora"] == "atardecer"
    # a mano manda; False quita
    assert escenarios.de_la_escena({"narracion": "en el mar", "escenario": False}) is False
    m = escenarios.de_la_escena({"narracion": "de noche", "escenario": "templo"})
    assert (m["nombre"], m["hora"], m["efectos"], m["mas"]) == ("templo", "noche", [], []), m
    m = escenarios.de_la_escena({"narracion": "x", "escenario": {"nombre": "mar",
                                                             "efectos": ["fuego", "rayo"]}})
    assert m["efectos"] == ["fuego"] and m["hora"] == "dia", m
    # los cuatro nuevos
    assert d("Pablo y Silas, encadenados en la cárcel")["nombre"] == "carcel"
    assert d("María lo acostó en un pesebre")["nombre"] == "establo"
    assert d("David se escondió en la cueva de Adulam")["nombre"] == "cueva"
    assert d("Juan bautizaba en el río Jordán")["nombre"] == "rio"


def probar_piezas_sueltas():
    """Las recetas son fondo + cosas; la narracion SUMA lo que nombra; a mano
    se monta un sitio pieza a pieza con la x del cuadro."""
    for n, r in escenarios.RECETAS.items():
        assert r["fondo"] in escenarios.FONDOS, n
        assert all((q if isinstance(q, str) else q["cosa"]) in escenarios.COSAS for q in r["cosas"]), n
    assert set(escenarios.NOMBRES) == set(escenarios.RECETAS)
    e = escenarios.escenario_de("Jesús entró en la barca a la orilla del río y vio una cruz")
    assert e["nombre"] == "rio" and e["mas"] == ["barca", "cruz"], e
    assert escenarios.escenario_de("Jonás en la barca, en el mar")["mas"] == []   # ya la tiene
    # x del cuadro (0..1) -> del escenario (1.3 veces mas ancho, centro 0)
    q = escenarios.del_cuadro([{"cosa": "cruz", "x": 1.0, "tam": 2}, "nada", "olivo"])
    assert [c["cosa"] for c in q] == ["cruz", "olivo"] and abs(q[0]["x"] - 0.385) < 0.001, q
    assert abs(q[0]["tam"] - 2 * escenarios.COSAS["cruz"][1]) < 1e-6
    # sin x: las grandes al centro, las demas a huecos libres distintos
    f, cs = escenarios.receta(fondo="tierra", cosas=["muralla", "cruz", "cruz", "cruz"])
    assert f == "tierra" and cs[0]["x"] == 0 and len({c["x"] for c in cs[1:]}) == 3, cs
    # golgota a mano: fondo + tres cruces; y el templo con el fuego en su altar
    m = escenarios.de_la_escena({"narracion": "al atardecer", "escenario": {
        "fondo": "tierra", "cosas": [{"cosa": "cruz", "x": .5}, {"cosa": "cruz", "x": .2}, "cruz"]}})
    p = escenarios.pieza(m["nombre"], m["hora"], [], 1080, 1920, 0, fondo=m["fondo"], cosas=m["cosas"])
    assert p["nombre"] == "tierra" and p["cosas"] == ["cruz"] * 3 and m["hora"] == "atardecer", p["cosas"]
    t = escenarios.pieza("templo", "dia", ["fuego"], 1080, 1920, 0)
    alt = escenarios.receta("templo")[1][1]
    assert alt["cosa"] == "altar" and abs(t["efectos"][0]["x"] - 1080 * 1.3 * alt["x"]) < 1, t["efectos"]
    # cada cosa se dibuja en cada fondo sin romper el SVG
    todas = list(escenarios.COSAS)
    for fondo in escenarios.FONDOS:
        for hora in escenarios.HORAS:
            p = escenarios.pieza(None, hora, [], 1920, 1080, 0, fondo=fondo, cosas=todas[:10] if hora == "dia"
                                 else todas[10:20] if hora == "noche" else todas[20:])
            xml.dom.minidom.parseString(f'<svg xmlns="http://www.w3.org/2000/svg">{p["svg"]}</svg>')


def probar_svg_y_lottie():
    for nombre in escenarios.NOMBRES:
        for hora in escenarios.HORAS:
            for W, H in ((1080, 1920), (1920, 1080)):
                p = escenarios.pieza(nombre, hora, ["fuego", "humo", "luz"], W, H, 1.0)
                # SVG bien formado (si no, innerHTML lo pinta a medias sin error)
                xml.dom.minidom.parseString(
                    f'<svg xmlns="http://www.w3.org/2000/svg">{p["svg"]}</svg>')
                assert p["fondo"] and p["entra"] == "nada" and p["w"] > W, p["w"]
                assert len(p["efectos"]) == 3
    # cada hora pinta distinto y es determinista (el mismo fotograma en cada lote)
    a = escenarios.svg("mar", "dia", 1300, 2400, 100)
    assert a == escenarios.svg("mar", "dia", 1300, 2400, 100)
    assert a != escenarios.svg("mar", "noche", 1300, 2400, 100)
    assert "esc-estrella" in escenarios.svg("campo", "noche", 1300, 2400, 100)
    assert "esc-barca" in a and "esc-ola" in a
    for ef in escenarios.EFECTOS:
        L = escenarios.lottie_de(ef)
        json.dumps(L)
        assert L["op"] == 60 and L["layers"], ef
        for capa in L["layers"]:
            for prop in capa["ks"].values():
                if prop.get("a") == 1:
                    ts = [k["t"] for k in prop["k"]]
                    assert ts == sorted(ts) and ts[0] == 0 and ts[-1] == 60, (ef, ts)


def probar_motion():
    W, H = 1080, 1920
    escenas = [_escena("S001", "Pedro subió a la barca en el mar de Galilea", 0.0, 4.0),
               _escena("S002", "Dios ama a los suyos", 4.0, 7.0),
               _escena("S003", "El rey David se sentó en su trono", 7.0, 11.0)]
    escenas[0]["personajes"] = ["Pedro"]
    escenas[2]["personajes"] = ["David"]
    c = motion.preparar(escenas, {"motion": True}, {}, W, H)
    tipos = [p["tipo"] for p in c["S001"]["piezas"]]
    assert tipos[0] == "escenario" and "personajes" in tipos, tipos
    esc = c["S001"]["piezas"][0]
    assert esc["nombre"] == "mar" and esc["id"] == "S001-0"
    figs = next(p for p in c["S001"]["piezas"] if p["tipo"] == "personajes")
    assert esc["x"] == round(figs["x"], 1) or abs(esc["x"] - figs["x"]) < 1, (esc["x"], figs["x"])
    assert not any(p["tipo"] == "escenario" for p in c["S003"]["piezas"]
                   if p["id"].startswith("S002"))
    assert any(p.get("nombre") == "trono" for p in c["S003"]["piezas"])
    # el escenario no aterriza ni reacciona ni recibe el objeto puente
    assert not any(im["id"] == "S001-0" for im in c["S001"]["impactos"])
    assert "fondo" in motion.MOTION_JS and "hazEscenario" in motion.MOTION_JS
    # sin efectos no se carga lottie; con fuego, si
    assert "lottie" not in motion.js_de(c["S001"])[:2000]
    # con lamina no sale solo; a mano, si
    lam = {"href": "x.png", "ancho": 1024, "alto": 1536}
    c2 = motion.preparar(escenas, {"motion": True}, {"S001": lam}, W, H)
    assert c2["S001"]["piezas"][0]["tipo"] == "lamina", c2["S001"]["piezas"][0]["tipo"]
    escenas[0]["escenario"] = {"nombre": "mar", "hora": "noche", "efectos": ["fuego"]}
    c3 = motion.preparar(escenas, {"motion": True}, {"S001": lam}, W, H)
    assert c3["S001"]["piezas"][0]["hora"] == "noche"
    assert escenarios.con_efectos(c3["S001"]) and "lottie" in motion.js_de(c3["S001"])[:3000]
    # apagado en todo el video
    c4 = motion.preparar(escenas, {"motion": {"escenarios": False}}, {}, W, H)
    assert not any(p["tipo"] == "escenario" for v in c4.values() for p in v["piezas"])
    # storyboard a mano
    escenas[1]["motion"] = [{"tipo": "escenario", "nombre": "desierto", "efectos": "luz"}]
    c5 = motion.preparar(escenas, {"motion": True}, {}, W, H)
    p = [q for q in c5["S002"]["piezas"] if q["id"].startswith("S002")][0]
    assert p["nombre"] == "desierto" and p["efectos"][0]["tipo"] == "luz", p["nombre"]
    # storyboard de Claude montado pieza a pieza
    escenas[1]["motion"] = [{"tipo": "escenario", "fondo": "establo", "hora": "noche",
                             "cosas": ["pesebre", {"cosa": "burro", "x": .85}], "mas": ["farol"]}]
    c6 = motion.preparar(escenas, {"motion": True}, {}, W, H)
    p = [q for q in c6["S002"]["piezas"] if q["id"].startswith("S002")][0]
    assert p["suelo"] == "establo" and p["cosas"] == ["pesebre", "burro", "farol"], p["cosas"]
    assert p["hora"] == "noche" and "esc-halo" in p["svg"]


def ver(carpeta):
    from PIL import Image
    from playwright.sync_api import sync_playwright
    import p8_render
    os.makedirs(carpeta, exist_ok=True)
    fotos = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch(executable_path=os.environ.get("ESTUDIO_CHROMIUM") or None)
        errores = []
        for W, H in ((1080, 1920), (1920, 1080)):
            hoja = nav.new_page(viewport={"width": W, "height": H})
            hoja.on("pageerror", lambda e: errores.append(str(e)))
            for k, nombre in enumerate(escenarios.NOMBRES):
                hora = escenarios.HORAS[k % 3]
                e = _escena("S001", "Pedro dijo: aquí estamos todos juntos hoy", 0.0, 4.0)
                e["personajes"] = ["Pedro", "María"]
                e["escenario"] = {"nombre": nombre, "hora": hora,
                                  "efectos": [["fuego"], ["humo", "fuego"], ["luz"]][k % 3]}
                conf = motion.preparar([e], {"motion": True}, {}, W, H)["S001"]
                pagina = p8_render._pagina_de(
                    {"id": "S001", "t_in": 0.0, "t_out": 4.0},
                    {"ventana_ini": [0, 0, 1, 1], "ventana_fin": [0, 0, 1, 1],
                     "hyperframe_px": [1024, 1536]}, "", __file__, {"resolucion": [W, H]},
                    os.path.join(carpeta, f"{nombre}_{W}.html"), mg=conf)
                hoja.goto("file://" + os.path.abspath(pagina))
                hoja.wait_for_function("window.LETRAS_OK === true", timeout=10000)
                hoja.evaluate("pintar(2.2)")
                ruta = os.path.join(carpeta, f"{nombre}_{hora}_{W}.png")
                hoja.screenshot(path=ruta)
                fotos.append(ruta)
            hoja.close()
        nav.close()
    assert not errores, errores
    for W in (1080, 1920):
        mias = [f for f in fotos if f.endswith(f"_{W}.png")]
        peq = [Image.open(f).convert("RGB").resize((W // 4, (1920 if W == 1080 else 1080) // 4))
               for f in mias]
        cw, ch = peq[0].size
        hoja_c = Image.new("RGB", (4 * cw, -(-len(peq) // 4) * ch), "white")
        for i, im in enumerate(peq):
            hoja_c.paste(im, ((i % 4) * cw, (i // 4) * ch))
        hoja_c.save(os.path.join(carpeta, f"contactos_{W}.png"))
    print("fotogramas en", carpeta)


def main():
    probar_deteccion()
    probar_piezas_sueltas()
    probar_svg_y_lottie()
    probar_motion()
    if "--ver" in sys.argv:
        ver(sys.argv[sys.argv.index("--ver") + 1])
    print("OK prueba_escenarios")


if __name__ == "__main__":
    main()
