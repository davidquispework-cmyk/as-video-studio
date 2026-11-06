"""Prueba corta de los muñecos que gesticulan (pasos/marioneta.py).

    python pasos/prueba_marioneta.py            # sin navegador
    python pasos/prueba_marioneta.py --foto     # y pinta un plano con Playwright
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import marioneta  # noqa: E402


def main():
    assert marioneta.gesto_de("Pedro levantó las manos y oró") == "brazos"
    assert marioneta.gesto_de("Mirad, señaló el templo") == "senalar"
    assert marioneta.gesto_de("Pablo caminó hasta Corinto") == "caminar"
    assert marioneta.gesto_de("Entonces Jesús dijo a sus discípulos") == "hablar"
    a = marioneta.aspecto("María", "joven con túnica azul y manto blanco")
    assert a["mujer"] and not a["barba"] and a["tunica"] == marioneta.COLORES["azul"]
    b = marioneta.aspecto("Pedro", "pescador con barba, túnica marrón")
    assert b["barba"] and b["tunica"] == marioneta.COLORES["marron"]
    escena = {"id": "S003", "personajes": ["Pedro", "Juan", "Pablo", "Ana"],
              "narracion": "Pedro dijo: mirad, y señaló la puerta"}
    conf = marioneta.configurar(escena, {"Pedro": "túnica marrón"})
    assert len(conf["figuras"]) == 3, "como mucho tres muñecos por plano"
    assert [f["gesto"] for f in conf["figuras"]] == ["senalar", "escuchar", "escuchar"]
    assert conf["figuras"][0]["habla"] and not conf["figuras"][1]["habla"]
    forzada = marioneta.configurar(dict(escena, gesto={"Juan": "brazos"}))
    assert forzada["figuras"][1]["gesto"] == "brazos"
    assert marioneta.configurar({"id": "S1", "personajes": []}) is None
    assert marioneta.configurar(dict(escena, marioneta=False)) is None
    p = marioneta.solo_fondo("Crea UNA\nQUIÉN SALE (x):\n- Pedro: barba\n"
                             "LO QUE SE ESTÁ NARRANDO: «hola»")
    assert "Pedro" not in p and "SOLO EL FONDO" in p and "NARRANDO" in p
    print("prueba_marioneta: OK")
    if "--foto" in sys.argv:
        foto(conf)


def foto(conf):
    """Pinta un plano vertical con los muñecos y guarda tres fotogramas."""
    from PIL import Image
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("sin playwright para Python: omito la foto")
        return
    import p8_render
    d = tempfile.mkdtemp(prefix="prueba_munecos_")
    fondo = os.path.join(d, "fondo.png")
    Image.new("RGB", (1536, 1024), (196, 170, 128)).save(fondo)
    conf["figuras"][1]["gesto"] = "brazos"
    pagina = p8_render._pagina_de(
        {"id": "S003", "t_in": 0, "t_out": 4},
        {"ventana_ini": [0, 0, 1536], "ventana_fin": [0, 0, 1536],
         "hyperframe_px": [1536, 1024]}, "", fondo, {"resolucion": [608, 1080]},
        os.path.join(d, "p.html"), mar=conf)
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        hoja = nav.new_page(viewport={"width": 608, "height": 1080})
        errores = []
        hoja.on("pageerror", lambda e: errores.append(str(e)))
        hoja.goto("file://" + os.path.abspath(pagina))
        for t in (0.2, 1.3, 2.6):
            hoja.evaluate(f"pintar({t})")
            hoja.screenshot(path=os.path.join(d, f"t{t}.png"))
        nav.close()
    assert not errores, errores
    print("fotogramas en", d)


if __name__ == "__main__":
    main()
