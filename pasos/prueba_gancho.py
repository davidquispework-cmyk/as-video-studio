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
    palabras = ("¿Sabías que Pedro negó a Jesús? No fue una vez, sino 3 veces "
                "antes de que cantara el gallo, hace 2000 años.").split()
    marcas = [(round(0.3 * i, 2), round(0.3 * i + 0.28, 2))
              for i in range(len(palabras))]
    return {"id": "S001", "t_in": 0.0, "t_out": 7.0,
            "narracion": " ".join(palabras), "marcas": marcas}


def main():
    assert gancho.texto_de("¿Sabías que Pedro lloró? Luego volvió.") == "¿Sabías que Pedro lloró?"
    assert gancho.texto_de("Pablo escribió.") == "Pablo escribió"
    largo = gancho.texto_de("En el año treinta y tres un hombre de Galilea cambió "
                            "la historia para siempre y nadie lo esperaba.")
    assert largo.endswith("…") and len(largo.split()) <= 8, largo
    # B (4): nunca corta en «y…?» ni en una palabra vacia
    texto, dichas = gancho.cartel_de("¿Sabías que José y María viajaron a Belén y "
                                     "allí no había sitio en ninguna posada del pueblo?")
    assert texto == "¿Sabías que José y María viajaron a Belén…?" and dichas == 8, texto
    # B (2): un solo criterio de mayusculas
    assert gancho.caso_limpio("DIOS,") == "Dios," and gancho.caso_limpio("ONU") == "ONU"
    # B+: tachado (lo falso) y contador
    pal = "No fue una manzana, sino un fruto cualquiera.".split()
    tachar, verdad = gancho.contrastes(pal)
    assert pal[min(tachar)] == "manzana," and pal[min(verdad)] == "fruto", (tachar, verdad)
    t2, v2 = gancho.contrastes("no es un mito, es historia real.".split())
    assert t2 == {3} and v2 == {5}, (t2, v2)
    # creencia -> «en realidad» (11-nov): tacha lo creido, marca lo verdadero
    def _tv(frase):
        pal = frase.split()
        t, v = gancho.contrastes(pal)
        return sorted(pal[k] for k in t), sorted(pal[k] for k in v)
    assert _tv("Todos creen que fue una manzana, pero en realidad fue un higo.") \
        == (["manzana,"], ["higo."])
    assert _tv("Crees que fue una manzana. En realidad fue un higo.") \
        == (["manzana."], ["higo."])
    assert _tv("Dicen que Noé era joven. Lo cierto es que tenía seiscientos años.") \
        == (["joven."], ["seiscientos"])
    assert _tv("El mito: Colón llegó primero. La verdad: los vikingos.")[1] == ["vikingos."]
    assert _tv("Es un mito. En realidad nadie lo vio.")[0] == ["mito."]
    # sin creencia delante, «en realidad» es muletilla; «buscar la verdad», nada
    assert _tv("En realidad fue un higo.") == ([], [])
    assert _tv("Él buscaba la verdad en Roma.") == ([], [])
    assert _tv("Crees que es fácil. Mañana iremos. En realidad no.") == ([], [])
    assert gancho.contador("350")["desde"] == 0 and gancho.contador("1656")["desde"] == 1606
    assert gancho.contador("1.500")["miles"] == "." and gancho.contador("3,5") is None
    pasos = gancho._pasos_contador(gancho.contador("70"), 1.0, 2.0)
    assert pasos[0][0] == "0" and pasos[-1] == ("70", 2.0), pasos
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
    assert "¿SABÍAS" in con and "Shaddai Montserrat" in con
    # B (1): mientras esta el cartel (hasta que se dice «Jesús?» + 0,35 s) no
    # hay subtitulo: el primer trozo palabra a palabra entra despues
    import re
    entradas = [float(x) for x in re.findall(
        r'<set attributeName="opacity" to="1" begin="([\d.]+)s"/>', con)]
    assert entradas and min(entradas) >= 1.7, entradas
    assert 'type="translate"' in con and 'visibility="hidden"' in con  # contador
    assert "#FF3B3B" in con                                   # tachado rojo
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


def foto(svg, salida, instantes=(0.9, 2.5, 3.6, 5.0)):
    """Fotos del SVG en varios instantes, con las letras de verdad cargadas
    (las mismas reglas @font-face que mete p8_render)."""
    import letras
    from playwright.sync_api import sync_playwright
    html = ("<html><head><style>" + letras.css_para(svg) + "</style></head>"
            "<body style='margin:0;background:#345'>" + svg + "</body></html>")
    pagina = os.path.join(tempfile.gettempdir(), "prueba_gancho.html")
    with open(pagina, "w", encoding="utf-8") as fh:
        fh.write(html)
    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--allow-file-access-from-files"])
        pag = nav.new_page(viewport={"width": salida[0], "height": salida[1]})
        pag.goto("file://" + pagina)
        pag.evaluate("Promise.all(Array.from(document.fonts).map(f => f.load()))")
        for t in instantes:
            destino = os.path.join(tempfile.gettempdir(), f"prueba_gancho_{t}.png")
            pag.evaluate(f"document.querySelector('svg').pauseAnimations();"
                         f"document.querySelector('svg').setCurrentTime({t})")
            pag.screenshot(path=destino)
            print("foto:", destino)
        nav.close()


if __name__ == "__main__":
    main()
