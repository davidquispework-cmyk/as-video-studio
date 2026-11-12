"""Prueba de los rotulos (pasos/rotulos.py, P1). Sin red y sin gastar nada.

    python pasos/prueba_rotulos.py            lo automatico y lo heredado
    python pasos/prueba_rotulos.py --ver DIR  ademas pinta una pagina de render
                                              en Chromium y guarda fotogramas
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rotulos  # noqa: E402


def _escena(sid, texto, t_in=0.0, dur=6.0):
    palabras = texto.split()
    paso = dur / len(palabras)
    return {"id": sid, "t_in": t_in, "t_out": t_in + dur, "narracion": texto,
            "marcas": [[t_in + paso * i, t_in + paso * (i + 1)]
                       for i in range(len(palabras))]}


def _tipos(items):
    return [r["tipo"] for r in items]


def probar_automaticos():
    a = rotulos.automaticos(_escena("a", "Israel vivía sin rey y cada uno hacía lo que quería"))
    assert any(r["tipo"] == "sello" and r["texto"] == "SIN REY" for r in a), a
    a = rotulos.automaticos(_escena("b", "La túnica de José no era de colores"))
    assert any(r["tipo"] == "sello" and r["texto"] == "NO" for r in a), a
    a = rotulos.automaticos(_escena("c", "Pasaron más de cuatrocientos años de silencio"))
    c = next(r for r in a if r["tipo"] == "cifra")
    assert c["valor"] == 400 and c["despues"] == "AÑOS" and c["antes"] == "+", c
    a = rotulos.automaticos(_escena("d", "Y al día tres Jonás seguía dentro del pez"))
    c = next(r for r in a if r["tipo"] == "cifra")
    assert c["valor"] == 3 and c["antes"] == "DÍA", c
    a = rotulos.automaticos(_escena("e", "Para entenderlo hay que retroceder veinticinco años antes"))
    r = next(r for r in a if r["tipo"] == "rebobinar")
    assert r["menos"] == "−25 AÑOS", r
    a = rotulos.automaticos(_escena("f", "En hebreo jesed significa amor que no se rinde"))
    d = next(r for r in a if r["tipo"] == "dato")
    assert d["palabra"] == "JESED", d
    a = rotulos.automaticos(_escena("g", "Como dice Jueces 9:5 mató a sus hermanos"))
    p = next(r for r in a if r["tipo"] == "pastilla")
    assert p["texto"] == "JUECES 9:5", p
    a = rotulos.automaticos(_escena("h", "Dios habló con Moisés en el monte"))
    assert a == [], a
    print("ok automaticos")


def probar_video():
    escenas = [_escena("s1", "Como dice Jueces 9:5 Abimelec mató a sus hermanos", 0),
               _escena("s2", "Y fueron setenta hermanos sobre una piedra", 6),
               {"id": "s3", "cartela": True, "t_in": 12, "t_out": 14},
               dict(_escena("s4", "Nadie lo sabía", 14), rotulos=False),
               dict(_escena("s5", "Pero el pueblo calló", 20),
                    rotulos=[{"tipo": "sello", "texto": "sin rey", "en": "calló"}])]
    c = rotulos.preparar(escenas, {}, 1080, 1920)
    assert _tipos(c["s1"]["items"])[0] == "pastilla"
    s2 = c["s2"]["items"]
    assert s2[0]["fija"] and s2[0]["texto"] == "JUECES 9:5", s2
    assert any(r["tipo"] == "cifra" and r["valor"] == 70 for r in s2), s2
    assert "s3" not in c and "s4" not in c, c
    s5 = c["s5"]["items"]
    assert _tipos(s5) == ["pastilla", "sello"] and s5[1]["texto"] == "SIN REY", s5
    assert s5[1]["t"] > 0
    assert rotulos.preparar(escenas, {"rotulos": False}, 1080, 1920) == {}
    print("ok video")


def probar_citas_dichas():
    """Lo que fallo en el video de prueba de los angeles (12-nov-2026)."""
    def en(bloque, sid, texto, t):
        return dict(_escena(sid, texto, t), origen={"bloque": bloque})
    escenas = [
        en("B004", "s1", "Le dice en Daniel, capítulo diez, versículo once:", 0),
        en("B004", "s2", "«Daniel, varón muy amado».", 6),
        # bloque nuevo que cita OTRA cosa: la de Daniel se quita al empezar
        en("B005", "s3", "Cuarta. Abraham, en el monte.", 12),
        en("B005", "s4", "lo llama, en Génesis, capítulo veintidós, versículo once", 18),
        # el corte parte la cita dicha en palabras en dos planos
        en("B007", "s5", "Quien lo sabe es Dios. El Salmo ciento cuarenta y siete,", 24),
        en("B007", "s6", "versículo cuatro, habla de las estrellas", 30),
        # un bloque que no cita nada conserva la de antes
        en("B008", "s7", "Si lo hace con cada estrella, ¿no va a saber el tuyo?", 36),
        en("B009", "s8", "Lee Lucas capítulo uno tú mismo", 42),
    ]
    c = rotulos.preparar(escenas, {}, 1080, 1920)

    def pastilla(sid):
        return next((r for r in c.get(sid, {}).get("items", [])
                     if r["tipo"] == "pastilla"), None)
    assert pastilla("s1")["texto"] == "DANIEL 10:11"
    assert pastilla("s2")["fija"] and pastilla("s2")["texto"] == "DANIEL 10:11"
    assert pastilla("s3") is None, c.get("s3")
    assert pastilla("s4")["texto"] == "GÉNESIS 22:11"
    p5 = pastilla("s5")
    assert p5["texto"] == "SALMO 147:4" and not p5.get("fija"), p5
    assert p5["t"] > 2, p5          # entra al decir «Salmo», no al empezar
    assert pastilla("s6")["texto"] == "SALMO 147:4"
    assert pastilla("s7")["texto"] == "SALMO 147:4"
    assert pastilla("s8")["texto"] == "LUCAS 1"
    # sin «capitulo» ni versiculo no hay pastilla («Lucas uno» a secas, no)
    a = rotulos.automaticos(_escena("x", "como cuenta Mateo cinco amigos"))
    assert not any(r["tipo"] == "pastilla" for r in a), a
    # un plano que EMPIEZA a media cita no la repite como suya
    assert rotulos.automaticos(_escena("y", "versículo cuatro, habla")) == []
    print("ok citas dichas")


def probar_placas_y_sellos():
    """Punto 4 del video de prueba: «4 VECES», «1/4...4/4» y el sello «NO»."""
    escenas = [
        _escena("s1", "¿Los ángeles conocen tu nombre? Mira cuatro", 0),
        _escena("s2", "veces en que un ángel llama a alguien.", 6),   # corte
        _escena("s3", "Primera. Zacarías está en el templo.", 12),
        _escena("s4", "Es Gabriel, y sabe cómo se llama.", 18),
        _escena("s5", "Segunda. María recibe la visita, por primera vez.", 24),
        _escena("s6", "Tercera. Daniel recibe la visita de un varón.", 30),
        _escena("s7", "Cuarta. Abraham, en el monte, día tres.", 36),
        _escena("s8", "La Biblia no dice eso. El texto no dice quién es.", 42),
    ]
    c = rotulos.preparar(escenas, {}, 1080, 1920)

    def de(sid, tipo):
        return [r for r in c.get(sid, {}).get("items", []) if r["tipo"] == tipo]
    placa = de("s1", "cifra")
    assert placa and placa[0]["valor"] == 4 and placa[0]["despues"] == "VECES", c
    assert not de("s2", "cifra"), c.get("s2")
    for sid, n in (("s3", 1), ("s5", 2), ("s6", 3), ("s7", 4)):
        m = de(sid, "cifra")
        assert len(m) == 1 and m[0]["valor"] == n and m[0]["despues"] == "/ 4", (sid, m)
    assert m[0]["t"] == 0.0                # entra al decir «Cuarta»
    assert not de("s4", "cifra")
    sellos = de("s8", "sello")
    assert len(sellos) == 1 and sellos[0]["texto"] == "NO", c.get("s8")
    # «el texto no dice quien es» solo calla: sin sello
    a = rotulos.automaticos(_escena("x", "El texto no dice quién es él."))
    assert not any(r["tipo"] == "sello" for r in a), a
    # un ordinal suelto, sin lista, no pone marcador
    solo = rotulos.preparar([_escena("y", "Primera. Una cosa nada más.")],
                            {}, 1080, 1920)
    assert not solo, solo
    print("ok placas y sellos")


def ver(carpeta):
    """Una pagina de render de verdad, con todos los rotulos, en Chromium."""
    import p8_render
    os.makedirs(carpeta, exist_ok=True)
    fondo = os.path.join(carpeta, "fondo.png")
    from PIL import Image
    Image.new("RGB", (1536, 2304), (196, 170, 132)).save(fondo)
    rt = {"W": 1080, "H": 1920, "items": [
        {"tipo": "pastilla", "texto": "JUECES 9:5", "t": 0.2},
        {"tipo": "sello", "texto": "SIN REY", "t": 0.6},
        {"tipo": "cifra", "valor": 400, "antes": "+", "despues": "AÑOS", "t": 0.4},
        {"tipo": "rebobinar", "texto": "REBOBINANDO", "menos": "−25 AÑOS", "t": 2.6}]}
    pagina = os.path.join(carpeta, "escena.html")
    p8_render._pagina_de({"t_in": 0, "t_out": 5}, {
        "ventana_ini": [0, 0, 1, 1], "ventana_fin": [0, 0, 1, 1],
        "hyperframe_px": [1536, 2304]}, "", fondo, {"resolucion": [1080, 1920]},
        pagina, rt=rt)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("pagina escrita (sin playwright de Python no se abre):", pagina)
        return
    errores = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pg = nav.new_page(viewport={"width": 1080, "height": 1920})
        pg.on("pageerror", lambda e: errores.append(str(e)))
        pg.goto("file://" + os.path.abspath(pagina))
        pg.wait_for_function("window.LETRAS_OK")
        for t in (0.0, 2.2, 3.4):
            pg.evaluate(f"pintar({t})")
            pg.screenshot(path=os.path.join(carpeta, f"t{t:.1f}.png"))
        assert pg.evaluate("RT_LINEAS.length") == 4
        assert pg.evaluate("getComputedStyle(document.querySelector('.rt-sello')).opacity") == "1"
        nav.close()
    assert not errores, errores
    print("ok pagina:", carpeta)


if __name__ == "__main__":
    probar_automaticos()
    probar_video()
    probar_citas_dichas()
    probar_placas_y_sellos()
    if "--ver" in sys.argv:
        ver(sys.argv[sys.argv.index("--ver") + 1])
