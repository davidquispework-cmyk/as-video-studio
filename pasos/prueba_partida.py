"""Prueba de la pantalla partida y el tono (pasos/partida.py, P2). Sin red.

    python pasos/prueba_partida.py            lo automatico y lo de a mano
    python pasos/prueba_partida.py --ver DIR  ademas pinta paginas de render en
                                              Chromium y guarda fotogramas
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partida  # noqa: E402
from prueba_rotulos import _escena  # noqa: E402


def _imagenes(carpeta, ids, tam=(1536, 2304)):
    from PIL import Image
    colores = [(196, 170, 132), (60, 90, 150), (150, 60, 60), (70, 130, 80),
               (120, 100, 160), (200, 150, 60)]
    rutas = {}
    for k, sid in enumerate(ids):
        rutas[sid] = os.path.join(carpeta, f"{sid}.png")
        Image.new("RGB", tam, colores[k % len(colores)]).save(rutas[sid])
    return rutas


def probar_video():
    with tempfile.TemporaryDirectory() as d:
        escenas = [
            _escena("s1", "En Éxodo capítulo doce el cordero salvó a cada casa", 0),
            {"id": "c", "cartela": True, "t_in": 6, "t_out": 8},
            _escena("s2", "Igual que en Mateo veintiséis la sangre del cordero", 8),
            _escena("s3", "Aquella noche hubo traición en el huerto", 14),
            _escena("s4", "Para entenderlo hay que retroceder cuatrocientos años antes", 20),
            _escena("s5", "Y aquí la historia sigue tranquila", 26),
            _escena("s6", "Génesis y Apocalipsis cuentan lo mismo", 32),
        ]
        escenas[5]["tono"] = "noche"
        rutas = _imagenes(d, ["s1", "c", "s2", "s3", "s4", "s5", "s6"])
        c = partida.preparar(escenas, {}, 1080, 1920, rutas.get)
        assert "c" not in c and "s1" not in c, c
        pt = c["s2"]["partida"]
        assert pt["eti_a"] == "ÉXODO" and pt["eti_b"] == "MATEO", pt
        assert pt["a"] == rutas["s1"] and pt["b"] == rutas["s2"], pt   # salta la cartela
        assert c["s2"]["tono"] == "noche"            # «sangre»
        assert c["s3"] == {"tono": "noche", "W": 1080, "H": 1920}, c["s3"]
        assert c["s4"]["tono"] == "papel", c["s4"]   # rebobina
        assert c["s5"]["tono"] == "noche"             # a mano
        p6 = c["s6"]["partida"]
        assert (p6["eti_a"], p6["eti_b"]) == ("GÉNESIS", "APOCALIPSIS"), p6
        # apagados
        assert all("partida" not in v for v in
                   partida.preparar(escenas, {"partida": False}, 1080, 1920, rutas.get).values())
        solo = partida.preparar(escenas, {"partida": False, "tono": "normal"},
                                1080, 1920, rutas.get)
        assert list(solo) == ["s5"], solo             # lo de a mano sigue mandando
        todo = partida.preparar(escenas, {"tono": "papel", "partida": False}, 1080, 1920, rutas.get)
        assert todo["s3"]["tono"] == "papel" and todo["s5"]["tono"] == "noche", todo
        # a mano: A = un plano elegido, etiquetas propias, entra en una palabra
        escenas[6]["partida"] = {"a": "s3", "eti_a": "antes", "eti_b": "ahora", "en": "cuentan"}
        escenas[2]["partida"] = False
        c = partida.preparar(escenas, {}, 1080, 1920, rutas.get)
        assert "partida" not in c["s2"], c["s2"]
        p6 = c["s6"]["partida"]
        assert p6["a"] == rutas["s3"] and p6["eti_a"] == "ANTES" and p6["t"] > 0, p6
        print("ok video:", "; ".join(f"{k}={partida.resumen(v)}" for k, v in c.items()))


def ver(carpeta):
    """Paginas de render de verdad (vertical y horizontal) en Chromium."""
    import p8_render
    os.makedirs(carpeta, exist_ok=True)
    casos = [("vertical_papel", 1080, 1920, (1536, 2304), "papel"),
             ("horizontal_noche", 1920, 1080, (3072, 2048), "noche")]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sync_playwright = None
    for nombre, W, H, tam, tono in casos:
        rutas = _imagenes(carpeta, [f"{nombre}_a", f"{nombre}_b"], tam)
        pt = {"W": W, "H": H, "tono": tono, "partida": {
            "t": 0.5, "eti_a": "ÉXODO", "eti_b": "MATEO",
            "a": rutas[f"{nombre}_a"], "b": rutas[f"{nombre}_b"]}}
        rt = {"W": W, "H": H, "items": [{"tipo": "pastilla", "texto": "MATEO 26:28", "t": 0.1}]}
        pagina = os.path.join(carpeta, f"{nombre}.html")
        p8_render._pagina_de({"t_in": 0, "t_out": 4}, {
            "ventana_ini": [0, 0, 1, 1], "ventana_fin": [0, 0, 1, 1],
            "hyperframe_px": list(tam)}, "", rutas[f"{nombre}_b"],
            {"resolucion": [W, H]}, pagina, rt=rt, pt=pt)
        if not sync_playwright:
            print("pagina escrita (sin playwright de Python no se abre):", pagina)
            continue
        errores = []
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pg = nav.new_page(viewport={"width": W, "height": H})
            pg.on("pageerror", lambda e: errores.append(str(e)))
            pg.goto("file://" + os.path.abspath(pagina))
            pg.wait_for_function("window.LETRAS_OK")
            pg.evaluate("pintar(0.2)")
            assert pg.evaluate("getComputedStyle(document.getElementById('partida')).opacity") == "0"
            for t in (0.2, 0.7, 2.5):
                pg.evaluate(f"pintar({t})")
                pg.screenshot(path=os.path.join(carpeta, f"{nombre}_t{t:.1f}.png"))
            assert pg.evaluate("getComputedStyle(document.getElementById('pt-eti-b')).opacity") == "1"
            assert "sepia" in pg.evaluate("getComputedStyle(camara).filter") or tono != "papel"
            nav.close()
        assert not errores, errores
    print("ok pagina:", carpeta)


if __name__ == "__main__":
    probar_video()
    if "--ver" in sys.argv:
        ver(sys.argv[sys.argv.index("--ver") + 1])
