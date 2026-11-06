"""Prueba corta de la plantilla TikTok (pasos/plantilla_tiktok.py).

    python pasos/prueba_plantilla_tiktok.py            # sin navegador
    python pasos/prueba_plantilla_tiktok.py --foto     # y pinta el final con Playwright
"""
import os
import sys
import tempfile
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

import plantilla_tiktok as pt  # noqa: E402
import sonido  # noqa: E402

SALIDA = (1080, 1920)


def _capa(piezas):
    svg = pt.incrustar(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SALIDA[0]}" '
                       f'height="{SALIDA[1]}"></svg>', piezas)
    xml.dom.minidom.parseString(svg.encode("utf-8"))      # XML valido
    return svg


def main():
    assert pt.normalizar(False) is None and pt.normalizar(None) is None
    assert pt.normalizar(True)["seguir"] == pt.TEXTO_SEGUIR
    assert pt.normalizar("  para más  de Pablo ")["seguir"] == "para más de Pablo"
    assert pt.normalizar({"seguir": False, "golpe": False}) == {
        "seguir": False, "barra": True, "golpe": False}

    # tres planos: 0-30, 30-62, 62-64 (el ultimo es mas corto que el «Sígueme»)
    escenas = [{"id": "S001", "t_in": 0.0, "t_out": 30.0},
               {"id": "S002", "t_in": 30.0, "t_out": 62.0},
               {"id": "S003", "t_in": 62.0, "t_out": 64.0}]
    ficha = pt.normalizar(True)
    capas = [_capa(pt.piezas_de_plano(e, ficha, SALIDA, 0.0, 64.0)) for e in escenas]
    assert "tiktok-barra" in capas[0] and "tiktok-seguir" not in capas[0]
    # el «Sígueme» empieza en 60.5 -> entra en S002 a los 30.5 s del plano...
    assert 'begin="30.50s"' in capas[1] and "<set " in capas[1]
    # ...y en S003 ya esta, sin volver a entrar
    assert "tiktok-seguir" in capas[2] and "<set " not in capas[2]
    # la barra encadena: S002 empieza donde acaba S001 (30/64 del ancho)
    assert f'from="{1080 * 30 / 64:.1f}"' in capas[1]
    assert pt.piezas_de_plano(escenas[0], None, SALIDA, 0, 64) == ""

    assert pt.aviso_duracion(58) and pt.aviso_duracion(75) is None

    golpe = pt.golpe(sonido.FRECUENCIA)
    assert golpe.shape[1] == 2 and abs(float(np.max(np.abs(golpe))) - 1) < 1e-3
    with tempfile.TemporaryDirectory() as tmp:
        ruta = sonido.anadir_golpe(None, 5.0, os.path.join(tmp, "e.wav"), golpe)
        datos = sonido._leer(ruta)
        assert len(datos) == 5 * sonido.FRECUENCIA
        assert float(np.max(np.abs(datos[:sonido.FRECUENCIA]))) > 0.5
        assert float(np.max(np.abs(datos[-sonido.FRECUENCIA:]))) == 0.0
        # encima de una pista que ya existe, sin pasarse de 0,98
        ruta = sonido.anadir_golpe(ruta, 5.0, ruta, golpe)
        assert float(np.max(np.abs(sonido._leer(ruta)))) <= 0.99

    if "--foto" in sys.argv:
        try:
            from playwright.sync_api import sync_playwright  # noqa: PLC0415
        except ImportError:
            print("(--foto pide Playwright de Python: pip install playwright)")
            print("prueba_plantilla_tiktok: OK")
            return
        destino = os.path.join(tempfile.gettempdir(), "tiktok_final.png")
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            pag = nav.new_page(viewport={"width": SALIDA[0], "height": SALIDA[1]})
            pag.set_content('<body style="margin:0;background:#3a5a7a">' + capas[1]
                            + "</body>")
            pag.evaluate("document.querySelector('svg').pauseAnimations();"
                         "document.querySelector('svg').setCurrentTime(31.4)")
            pag.screenshot(path=destino)
            nav.close()
        print("foto:", destino)
    print("prueba_plantilla_tiktok: OK")


if __name__ == "__main__":
    main()
