"""Prueba del decorado 3D (pasos/biblia3d.py, P6). Ligera por defecto.

    python pasos/prueba_biblia3d.py            que planos lo llevan, tomas y pagina
    python pasos/prueba_biblia3d.py --ver DIR  ademas pinta paginas en Chromium
                                               (WebGL por software), guarda PNG
                                               y mide el tiempo por fotograma
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import biblia3d  # noqa: E402
from prueba_rotulos import _escena  # noqa: E402


def probar_reparto():
    with tempfile.TemporaryDirectory() as d:
        img = os.path.join(d, "i.png")
        open(img, "wb").close()
        escenas = [
            _escena("s1", "Hace mucho tiempo vivía un pastor", 0),       # el primero: siempre
            _escena("s2", "y nadie sabía por qué", 6),                     # nada: no
            {"id": "c", "cartela": True, "t_in": 12, "t_out": 14},
            _escena("s3", "Mateo capítulo veintiséis lo cuenta así", 14),  # libro + cita
            _escena("s4", "porque estaba escrito desde antes", 20),        # escrito
            _escena("s5", "Y al final se fue a su casa", 26),
            _escena("s6", "la Biblia no lo dice", 32),
        ]
        escenas[6]["biblia3d"] = False
        escenas[5]["biblia3d"] = True
        imagen_de = lambda sid: img  # noqa: E731
        assert biblia3d.preparar(escenas, {}, 1080, 1920, imagen_de) == {}
        c = biblia3d.preparar(escenas, {"biblia3d": True}, 1080, 1920, imagen_de)
        assert sorted(c) == ["s1", "s3", "s4", "s5"], sorted(c)
        assert [c[k]["toma"] for k in ("s1", "s3", "s4", "s5")] == list(biblia3d.TOMAS)
        assert c["s3"]["cabecera"] == "MATEO 26", c["s3"]
        assert c["s1"]["cabecera"] == "" and c["s1"]["imagen"] == img
        todos = biblia3d.preparar(escenas, {"biblia3d": {"todos": True}}, 1080, 1920, imagen_de)
        assert "s2" in todos and "s6" not in todos and "c" not in todos, sorted(todos)
        # sin imagen, sin decorado (no hay nada que poner en la pagina)
        assert biblia3d.preparar(escenas, {"biblia3d": True}, 1080, 1920, lambda s: None) == {}
        conf = c["s3"]
        assert "#biblia3d" in biblia3d.css(conf) and biblia3d.LETRA in biblia3d.css(conf)
        assert 'id="biblia3d"' in biblia3d.html(conf)
        assert "three.min.js" in biblia3d.js(conf) and os.path.exists(biblia3d.THREE)
        assert biblia3d.json_conf(conf).startswith("{") and "file:///" in biblia3d.json_conf(conf)
        assert biblia3d.css(None) == biblia3d.html(None) == biblia3d.js(None) == ""


def probar_objetos():
    e = _escena("o", "Judas vendió a Jesús por treinta monedas de plata y una corona", 0, 6)
    obs = biblia3d.objetos_de(e)
    assert [o["id"] for o in obs] == ["monedas", "corona"], obs   # plata no repite
    assert 0 < obs[0]["t"] < obs[1]["t"] < 6, obs                    # caen al decirse
    assert biblia3d.objetos_de(_escena("v", "Y vino a casa con su amo", 0)) == []
    muchas = "piedra pan pez cruz espada"
    assert len(biblia3d.objetos_de(_escena("m", muchas, 0))) == biblia3d.MAX_OBJETOS
    assert biblia3d.objetos_de(dict(e, objetos=False)) == []
    mano = biblia3d.objetos_de(dict(e, objetos=["Oveja", "nada", "oveja", "cruz"]))
    assert [o["id"] for o in mano] == ["oveja", "cruz"], mano
    # cada id tiene su figura en el JavaScript
    for k in biblia3d.OBJETOS:
        assert f"    {k}(){{" in biblia3d.BIBLIA_JS, k
    c = biblia3d.preparar([e], {"biblia3d": True}, 1080, 1920, lambda s: __file__)["o"]
    assert c["objetos"] == obs and "con monedas, corona" in biblia3d.resumen(c)


def ver(carpeta):
    import p8_render
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw
    os.makedirs(carpeta, exist_ok=True)
    fondo = os.path.join(carpeta, "fondo.png")
    im = Image.new("RGB", (1536, 1024), (70, 110, 150))
    dib = ImageDraw.Draw(im)
    dib.rectangle([0, 700, 1536, 1024], fill=(150, 120, 70))
    dib.ellipse([600, 250, 950, 600], fill=(240, 200, 90))
    im.save(fondo)
    e = _escena("s", "Mateo capítulo veintiséis: treinta monedas, la corona y un pez", 0, 4)
    paginas = []
    for formato, (w, h) in (("horizontal", (1920, 1080)), ("vertical", (1080, 1920))):
        for toma in biblia3d.TOMAS:
            conf = biblia3d.preparar([dict(e, biblia3d=True)], {"biblia3d": True},
                                     w, h, lambda s: fondo)["s"]
            conf["toma"] = toma
            destino = os.path.join(carpeta, f"{formato}_{toma}.html")
            p8_render._pagina_de({"t_in": 0, "t_out": 4},
                                 {"ventana_ini": [0, 0, 1, 1], "ventana_fin": [0, 0, 1, 1],
                                  "hyperframe_px": [1536, 1024]},
                                 "", fondo, {"resolucion": [w, h]}, destino, e3=conf)
            paginas.append((destino, w, h))
    with sync_playwright() as pw:
        exe = os.environ.get("ESTUDIO_EDGE") or None   # el navegador del render
        nav = pw.chromium.launch(executable_path=exe, args=["--disable-gpu", "--enable-unsafe-swiftshader",
                                       "--allow-file-access-from-files"])
        for destino, w, h in paginas:
            errores = []
            pag = nav.new_page(viewport={"width": w, "height": h})
            pag.on("pageerror", lambda x: errores.append(str(x)))
            pag.goto("file://" + os.path.abspath(destino))
            pag.wait_for_function("window.LETRAS_OK")
            assert pag.evaluate("!window.B3_ERROR && !!B3"), pag.evaluate("window.B3_ERROR")
            pag.evaluate("Promise.resolve(pintar(0))")
            t0 = time.time()
            for k in range(5):
                pag.evaluate(f"Promise.resolve(pintar({k * 0.8}))")
            ms = (time.time() - t0) / 5 * 1000
            pag.screenshot(path=destino.replace(".html", ".png"))
            pag.close()
            assert not errores, errores
            print(f"  {os.path.basename(destino)}: {ms:.0f} ms por fotograma")
        nav.close()
    print("  paginas en", carpeta)


if __name__ == "__main__":
    probar_reparto()
    probar_objetos()
    if "--ver" in sys.argv:
        ver(sys.argv[sys.argv.index("--ver") + 1])
    print("prueba_biblia3d: OK")
