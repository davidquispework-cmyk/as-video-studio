"""Prueba corta del motion graphics (pasos/motion.py).

    python pasos/prueba_motion.py            # sin navegador
    python pasos/prueba_motion.py --foto     # y pinta fotogramas con Playwright

Con --foto comprueba ademas que NO HAY CORTE: el ultimo fotograma de un plano
y el primero del siguiente son casi el mismo dibujo.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import motion  # noqa: E402


def _escena(sid, texto, t_in, t_out):
    palabras = texto.split()
    paso = (t_out - t_in - 0.3) / len(palabras)
    marcas = [[round(t_in + 0.15 + paso * i, 3), round(t_in + 0.15 + paso * (i + 1), 3)]
              for i in range(len(palabras))]
    return {"id": sid, "narracion": texto, "marcas": marcas, "t_in": t_in, "t_out": t_out}


ESCENAS = [
    _escena("S001", "Jesús dijo: «El que me ama, mi palabra guardará» Juan 14:23", 0.0, 5.0),
    _escena("S002", "De Belén a Nazaret hay un buen camino para una familia a pie", 5.0, 9.0),
    _escena("S003", "En el año 70 d. C. Roma destruyó el templo de Jerusalén", 9.0, 13.0),
    _escena("S004", "Desde la hora sexta hasta la hora novena hubo tinieblas", 13.0, 17.0),
    _escena("S005", "Si pasas cinco horas al día en el celular tu tiempo se va", 17.0, 21.0),
    _escena("S006", "El corazón lleno de cosas no tiene hambre de Dios", 21.0, 24.0),
    _escena("S007", "No fueron tres reyes, sino unos magos de oriente.", 24.0, 28.0),
    _escena("S008", "Jesús alimentó a cinco mil hombres con cinco panes", 28.0, 32.0),
    _escena("S009", "Haz tres cosas: orar, leer la Biblia y servir.", 32.0, 36.0),
]


def main():
    assert motion.tema_de({}) is None and motion.tema_de({"motion": False}) is None
    assert motion.tema_de({"motion": True}) == "papel"
    assert motion.tema_de({"motion": {"tema": "noche"}}) == "noche"
    voz = motion.Voz(ESCENAS[0])
    cita = motion.cita_de(voz)
    assert cita and cita["ref"] == "Juan 14:23", cita
    assert cita["cabecera"] == "JESÚS DIJO:", cita["cabecera"]
    assert [w for w, _ in cita["palabras"]][:2] == ["El", "que"]
    assert motion.reloj_de(motion.Voz(ESCENAS[3]))["porciones"][0]["desde"] == 12
    assert motion.reloj_de(motion.Voz(ESCENAS[4]))["modo"] == 24
    fechas = motion.fechas_de(motion.Voz(ESCENAS[2]), hoy=2026)
    assert fechas and fechas[0]["anio"] == 70, fechas
    assert motion.fechas_de(motion.Voz(_escena("X", "En el 586 a. C. cayó", 0, 2)))[0]["anio"] == -586
    W, H = 608, 1080
    lam = {"href": "file:///no/existe.png", "ancho": 1024, "alto": 1536}
    confs = motion.preparar(ESCENAS, {"motion": True},
                            {e["id"]: lam for e in ESCENAS}, W, H, hoy=2026)
    tipos = [[p["tipo"] for p in confs[e["id"]]["piezas"] if p["en"] >= e["t_in"] - 0.8]
             for e in ESCENAS]
    assert tipos[0] == ["versiculo"], tipos
    assert tipos[1] == ["mapa"], tipos
    assert tipos[2] == ["linea"], tipos
    assert tipos[3] == ["reloj"] and tipos[4] == ["reloj"], tipos
    assert tipos[5][0] == "lamina" and "icono" in tipos[5], tipos
    assert tipos[6] == ["comparacion"] and tipos[7] == ["contador"] and tipos[8] == ["lista"], tipos
    comp = confs["S007"]["piezas"][-1]
    assert comp["a"] == "tres reyes" and comp["b"].startswith("unos magos"), comp
    cont = next(p for p in confs["S008"]["piezas"] if p["tipo"] == "contador")
    assert cont["n"] == 5000 and cont["etq"] == "HOMBRES" and cont["icono"] == "persona"
    # el objeto puente: sale al final de un plano y la pieza siguiente nace de el
    pu = confs["S002"]["puentes"]
    assert any(q["icono"] == "chincheta" for q in pu), pu
    mapa_ = next(p for p in confs["S002"]["piezas"] if p["tipo"] == "mapa")
    assert mapa_["entra"] == "pop" and mapa_["desde_puente"]
    # la camara sigue lo importante: hay focos y vuelve a su sitio antes del final
    ven = confs["S002"]["ventanas"][-1]
    assert ven["focos"] and all(f["t"] <= ven["b"] - 1.3 for f in ven["focos"]), ven
    mapa = next(p for p in confs["S002"]["piezas"] if p["tipo"] == "mapa")
    assert 100 <= mapa["tramos"][0]["km"] <= 125, mapa["tramos"]   # Belén–Nazaret ~110 km
    # la camara: cada plano empieza donde acabo el anterior (no hay corte)
    for a, b in zip(ESCENAS, ESCENAS[1:]):
        fin = confs[a["id"]]["cam"][-1]["a"]
        ini = next(t for t in confs[b["id"]]["cam"] if t["tipo"] == "viaje"
                   and t["t0"] == b["t_in"])["de"]
        assert fin == ini, (a["id"], fin, ini)
    # un storyboard escrito a mano
    propio = dict(ESCENAS[5], motion=[{"tipo": "texto", "texto": "Sin *hambre*",
                                       "x": .5, "y": .3, "en": "hambre",
                                       "luego": [{"en": "Dios", "y": .2, "escala": .8}]}])
    piezas = motion.storyboard(propio, W, H)
    assert piezas[0]["tipo"] == "texto" and piezas[0]["palabras"][1]["c"] == 1
    assert piezas[0]["en"] > propio["t_in"] and piezas[0]["luego"][0]["y"] == round(.2 * H, 1)
    print("prueba_motion: OK")
    if "--foto" in sys.argv:
        foto(confs, W, H)


def foto(confs, W, H):
    from PIL import Image, ImageChops, ImageStat
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("sin playwright para Python: omito la foto")
        return
    import p8_render
    d = tempfile.mkdtemp(prefix="prueba_motion_")
    fondo = os.path.join(d, "lamina.png")
    img = Image.new("RGB", (1024, 1536), (90, 140, 200))
    img.paste((230, 190, 120), (0, 900, 1024, 1536))
    img.save(fondo)
    url = p8_render._url_local(fondo)
    for c in confs.values():
        for p in c["piezas"]:
            if p["tipo"] == "lamina":
                p["href"] = url
    fotos = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        hoja = nav.new_page(viewport={"width": W, "height": H})
        errores = []
        hoja.on("pageerror", lambda e: errores.append(str(e)))
        for e in ESCENAS:
            pagina = p8_render._pagina_de(
                {"id": e["id"], "t_in": e["t_in"], "t_out": e["t_out"]},
                {"ventana_ini": [0, 0, 1, 1], "ventana_fin": [0, 0, 1, 1],
                 "hyperframe_px": [1024, 1536]}, "", fondo, {"resolucion": [W, H]},
                os.path.join(d, f"{e['id']}.html"), mg=confs[e["id"]])
            hoja.goto("file://" + os.path.abspath(pagina))
            hoja.wait_for_function("window.LETRAS_OK === true", timeout=10000)
            dur = e["t_out"] - e["t_in"]
            for t in (0.0, 0.5, dur * 0.55, dur - 1 / 30):
                hoja.evaluate(f"pintar({t})")
                ruta = os.path.join(d, f"{e['id']}_{t:.2f}.png")
                hoja.screenshot(path=ruta)
                fotos.append(ruta)
        nav.close()
    assert not errores, errores
    # SIN CORTE: ultimo de un plano vs primero del siguiente
    for k in range(len(ESCENAS) - 1):
        a = Image.open(fotos[4 * k + 3]).convert("RGB")
        b = Image.open(fotos[4 * k + 4]).convert("RGB")
        dif = sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3
        assert dif < 6, f"corte entre {ESCENAS[k]['id']} y {ESCENAS[k + 1]['id']}: {dif:.1f}"
    # una hoja de contactos para mirarla de un vistazo
    peq = [Image.open(f).convert("RGB").resize((W // 3, H // 3)) for f in fotos]
    hoja_c = Image.new("RGB", (4 * (W // 3), len(ESCENAS) * (H // 3)), "white")
    for i, im in enumerate(peq):
        hoja_c.paste(im, ((i % 4) * (W // 3), (i // 4) * (H // 3)))
    hoja_c.save(os.path.join(d, "contactos.png"))
    print("fotogramas en", d)


if __name__ == "__main__":
    main()
