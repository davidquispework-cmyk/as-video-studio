"""Prueba del modo editorial (pasos/editorial.py, P5). Sin red por defecto.

    python pasos/prueba_editorial.py            titulares, temas y reparto de cuadros
    python pasos/prueba_editorial.py --red      ademas baja un cuadro de verdad del Met
    python pasos/prueba_editorial.py --ver DIR  ademas pinta paginas de render en
                                                Chromium y guarda fotogramas
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editorial  # noqa: E402
from prueba_rotulos import _escena  # noqa: E402
import rotulos  # noqa: E402


def _palabras(tit):
    return " ".join(w["txt"] for w in tit)


def probar_titular():
    v = rotulos._Voz(_escena("a", "La túnica de José no era de colores, era otra cosa"))
    t = editorial.titular_auto(v)
    assert _palabras(t) == "La túnica de José no era de colores" or len(t) <= 6, t
    assert [w["txt"] for w in t if w["acento"]] == ["José"], t
    v = rotulos._Voz(_escena("b", "y después de mucho tiempo llegó el silencio"))
    t = editorial.titular_auto(v)
    assert len(t) <= 6 and t[-1]["txt"] == "silencio", t
    assert [w["txt"] for w in t if w["acento"]] == ["silencio"], t
    assert all(t[k]["t"] <= t[k + 1]["t"] for k in range(len(t) - 1))
    m = editorial.titular_a_mano(rotulos._Voz(_escena("c", "Hablemos de José y su túnica")),
                                 "La túnica de *José*")
    assert [w["txt"] for w in m] == ["La", "túnica", "de", "José"], m
    assert m[3]["acento"] and not m[0]["acento"] and m[3]["t"] > 0, m


def probar_temas():
    pl = lambda s: [editorial.citas.plegar(w) for w in s.split()]  # noqa: E731
    assert editorial.tema_de(pl("Lázaro estaba muerto")) == "Raising of Lazarus"
    assert editorial.tema_de(pl("José y sus hermanos lo vendieron")) == "Joseph and his brothers"
    assert editorial.tema_de(pl("la última cena con sus discípulos")) == "Last Supper"
    assert editorial.tema_de(pl("y fue crucificado en el Gólgota")) == "Crucifixion"
    assert editorial.tema_de(pl("una mañana tranquila")) is None


def probar_video():
    pedidas = []

    def falso(busqueda, carpeta):
        pedidas.append(busqueda)
        if busqueda == "Jonah":
            raise OSError("sin red")
        ruta = os.path.join(carpeta, "x.jpg")
        open(ruta, "wb").close()
        return {"ruta": ruta, "pie": "Rembrandt, 1630"}

    with tempfile.TemporaryDirectory() as d:
        escenas = [
            _escena("s1", "José y sus hermanos no se hablaban", 0),
            _escena("s2", "Los hermanos de José lo vendieron", 6),   # seguido: sin cuadro
            {"id": "c", "cartela": True, "t_in": 12, "t_out": 14},
            _escena("s3", "Años después Lázaro murió en Betania", 14),
            _escena("s3b", "Y nadie entendía lo que pasaba", 18, 2),
            _escena("s4", "Jonás huyó en un barco", 20),               # sin red: sin cuadro
            _escena("s5", "Otra vez José y sus hermanos", 26),         # ya usado
            _escena("s6", "Y aquí el plano dice otra cosa", 32),
        ]
        escenas[6]["titular"] = False
        os.makedirs(os.path.join(d, "c"), exist_ok=True)
        assert editorial.preparar(escenas, {}, 1080, 1920, d, falso) == {}
        c = editorial.preparar(escenas, {"editorial": True}, 1080, 1920,
                               os.path.join(d, "c"), falso)
        assert "c" not in c
        assert c["s1"]["cuadro"]["pie"] == "Rembrandt, 1630", c["s1"]
        assert "cuadro" not in c["s2"] and c["s2"]["titular"], c["s2"]
        assert "cuadro" in c["s3"] and "cuadro" not in c["s4"], c
        assert "s5" not in c or "cuadro" not in c["s5"], c.get("s5")
        assert pedidas == ["Joseph and his brothers", "Raising of Lazarus", "Jonah"], pedidas
        assert c["s6"]["titular"] and "cuadro" not in c["s6"]
        sin = editorial.preparar(escenas, {"editorial": {"cuadros": False}}, 1080, 1920,
                                 os.path.join(d, "c"), falso)
        assert all("cuadro" not in x for x in sin.values()) and sin["s1"]["titular"]
        # a mano: buscar otra cosa, y apagar el plano
        escenas[7]["cuadro"] = "Prodigal Son"
        escenas[0]["editorial"] = False
        c = editorial.preparar(escenas, {"editorial": True}, 1080, 1920,
                               os.path.join(d, "c"), falso)
        assert "s1" not in c and "cuadro" in c["s6"], c
        # la pagina se arma sin romperse
        for conf in (c["s6"], c["s4"]):
            assert "#editorial" in editorial.css(conf)
            assert 'id="ed-tit"' in editorial.html(conf)
            assert editorial.json_conf(conf).startswith("{")
        assert editorial.sin_cuadro(c["s6"]) and "cuadro" not in editorial.sin_cuadro(c["s6"])


def probar_red(carpeta):
    f = editorial.buscar_cuadro("Raising of Lazarus", carpeta)
    assert f and os.path.exists(f["ruta"]) and f["pie"], f
    print("  cuadro:", f["titulo"], "—", f["pie"])
    assert editorial.buscar_cuadro("Raising of Lazarus", carpeta) == f   # cache


def ver(carpeta):
    """Paginas de render en Chromium, con y sin cuadro, en vertical y horizontal."""
    import p8_render
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sync_playwright = None
    from PIL import Image
    os.makedirs(carpeta, exist_ok=True)
    fondo = os.path.join(carpeta, "fondo.png")
    Image.new("RGB", (1536, 2304), (70, 110, 150)).save(fondo)
    cuadro = os.path.join(carpeta, "cuadro.jpg")
    if not os.path.exists(cuadro):
        try:
            cuadro = editorial.buscar_cuadro("Raising of Lazarus", carpeta)["ruta"]
        except Exception:  # noqa: BLE001
            Image.new("RGB", (900, 1100), (120, 80, 40)).save(cuadro)
    e = _escena("s", "Años después Lázaro murió en Betania", 0, 4)
    paginas = []
    for nombre, (w, h) in (("vertical", (1080, 1920)), ("horizontal", (1920, 1080))):
        for con in (False, True):
            conf = {"W": w, "H": h, "titular": editorial.titular_auto(rotulos._Voz(e))}
            if con:
                conf["cuadro"] = {"ruta": cuadro, "pie": "Sano di Pietro, h. 1460–70"}
            destino = os.path.join(carpeta, f"{nombre}_{'cuadro' if con else 'solo'}.html")
            p8_render._pagina_de({"t_in": 0, "t_out": 4},
                                 {"ventana_ini": [0, 0, 1, 1], "ventana_fin": [0, 0, 1, 1],
                                  "hyperframe_px": [1536, 2304]},
                                 "", fondo, {"resolucion": [w, h]}, destino, ed=conf)
            paginas.append((destino, w, h))
    if not sync_playwright:
        print("  paginas escritas (sin playwright de Python no se abren)")
        return
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        for destino, w, h in paginas:
            errores = []
            pag = nav.new_page(viewport={"width": w, "height": h})
            pag.on("pageerror", lambda x: errores.append(str(x)))
            pag.goto("file://" + os.path.abspath(destino))
            pag.wait_for_function("window.LETRAS_OK")
            pag.evaluate("pintar(3.5)")
            pag.screenshot(path=destino.replace(".html", ".png"))
            assert pag.evaluate("document.querySelectorAll('.ed-p').length") >= 2
            assert pag.evaluate("getComputedStyle(document.querySelector('.ed-p')).opacity") == "1"
            pag.close()
            assert not errores, errores
        nav.close()
    print("  paginas en", carpeta)


if __name__ == "__main__":
    probar_titular()
    probar_temas()
    probar_video()
    if "--red" in sys.argv:
        with tempfile.TemporaryDirectory() as d:
            probar_red(d)
    if "--ver" in sys.argv:
        ver(sys.argv[sys.argv.index("--ver") + 1])
    print("prueba_editorial: OK")
