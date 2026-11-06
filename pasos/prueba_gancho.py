"""Prueba corta del gancho de 3 s y los subtitulos palabra a palabra (pasos/gancho.py).

    python pasos/prueba_gancho.py            # sin navegador
    python pasos/prueba_gancho.py --foto     # y pinta el cartel con Playwright
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gancho  # noqa: E402
import p7_callouts  # noqa: E402
import tipografia  # noqa: E402

# Sin Verdana (un Linux sin las fuentes de Windows) se mide con DejaVu: aqui
# solo se prueba que el SVG sale, no el ancho exacto.
if not os.path.exists(tipografia.FUENTES["verdana"][0]):
    _dv = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
    if os.path.exists(_dv + ".ttf"):
        tipografia.FUENTES["verdana"] = (_dv + ".ttf", _dv + "-Bold.ttf")


def _escena():
    palabras = ("¿Sabías que Pedro negó a Jesús tres veces antes de que "
                "cantara el gallo?").split()
    marcas = [(round(0.3 * i, 2), round(0.3 * i + 0.28, 2))
              for i in range(len(palabras))]
    return {"id": "S001", "t_in": 0.0, "t_out": 5.0,
            "narracion": " ".join(palabras), "marcas": marcas}


def main():
    assert gancho.texto_de("¿Sabías que Pedro lloró? Luego volvió.") == "¿Sabías que Pedro lloró?"
    assert gancho.texto_de("Pablo escribió.") == "Pablo escribió"
    largo = gancho.texto_de("En el año treinta y tres un hombre de Galilea cambió "
                            "la historia para siempre.")
    assert largo.startswith("¿Sabías esto?"), largo
    assert gancho.texto_de("lo que sea", "Mi gancho") == "Mi gancho"
    assert gancho.palabra_clave("Pedro negó 3 veces".split()) == 2
    assert gancho.palabra_clave("y en la casa de Jerusalén".split()) == 5

    p = p7_callouts._con_defectos({})
    salida = (1080, 1920)
    normal, _ = p7_callouts.capa_fija_de(_escena(), p, salida=salida, primera=True)
    assert "gancho" not in normal and "fill-opacity" not in normal, "sin param, como siempre"
    con, fichas = p7_callouts.capa_fija_de(_escena(), dict(p, gancho=True),
                                           salida=salida, primera=True)
    assert 'class="gancho"' in con and "fill-opacity" in con and fichas
    assert "¿SABÍAS" in con
    segundo, _ = p7_callouts.capa_fija_de(_escena(), dict(p, gancho=True),
                                          salida=salida, primera=False)
    assert 'class="gancho"' not in segundo and "fill-opacity" in segundo
    sin_cartel, _ = p7_callouts.capa_fija_de(dict(_escena(), gancho=False),
                                             dict(p, gancho=True), salida=salida,
                                             primera=True)
    assert 'class="gancho"' not in sin_cartel
    print("prueba_gancho: OK")
    if "--foto" in sys.argv:
        foto(con, salida)


def foto(svg, salida):
    from playwright.sync_api import sync_playwright
    destino = os.path.join(tempfile.gettempdir(), "prueba_gancho.png")
    html = ("<html><body style='margin:0;background:#345'>" + svg + "</body></html>")
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(viewport={"width": salida[0], "height": salida[1]})
        pag.set_content(html)
        pag.evaluate("document.querySelector('svg').pauseAnimations();"
                     "document.querySelector('svg').setCurrentTime(1.2)")
        pag.screenshot(path=destino)
        nav.close()
    print("foto:", destino)


if __name__ == "__main__":
    main()
