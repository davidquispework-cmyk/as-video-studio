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
    # segunda parte (pasos/motion_mas.py y pasos/motion_storyboard.py)
    _escena("S010", "Antes era perseguidor, ahora es apóstol de Cristo", 36.0, 40.0),
    _escena("S011", "Isaac, hijo de Abraham, fue padre de Jacob", 40.0, 44.0),
    _escena("S012", "El 70% de la iglesia y el 30 % del mundo", 44.0, 48.0),
    dict(_escena("S013", "Pedro dijo: yo no conozco a ese hombre", 48.0, 52.0),
         personajes=["Pedro", "María"]),
    dict(_escena("S014", "María tuvo miedo y tembló en la noche", 52.0, 56.0),
         personajes=["María"]),
    _escena("S015", "El pecado te ata, pero Cristo te hace libre", 56.0, 61.0),
]
FICHAS = {"Pedro": "pescador, túnica azul, barba negra", "María": "mujer joven, manto azul"}
# lo que devolveria Claude para S015 (la metafora: el pecado = bola con cadena)
RESPUESTA = """Aqui va:
```json
{"S015": [
  {"tipo": "texto", "texto": "El *PECADO*", "x": .5, "y": .16, "en": "pecado", "entra": "pop"},
  {"tipo": "icono", "nombre": "bola", "x": .5, "y": .4, "tam": .34, "en": "ata",
   "entra": "arriba", "luego": [{"en": "libre", "y": 1.4, "rot": 40}]},
  {"tipo": "personajes", "nombres": ["Pedro"], "gesto": "saltar", "expresion": "alegria",
   "x": .3, "y": .66, "alto": .22, "en": "libre"},
  {"tipo": "flecha", "de": [.75, .62], "a": [.58, .45], "texto": "¡suelta!", "en": "Cristo"},
  {"tipo": "inventada", "x": 1},
  {"tipo": "circulo", "x": .5, "y": .16, "w": .6, "h": .1, "en": "libre"},
]}
```"""


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
    import motion_storyboard
    import motion_mas
    d = tempfile.mkdtemp(prefix="prueba_storyboard_")
    pedidos = []

    def falso(instr):
        pedidos.append(instr)
        return RESPUESTA
    p = {"motion": {"tema": "papel", "storyboard": "claude"}}
    assert motion_storyboard.pedido(p) and not motion_storyboard.pedido({"motion": "papel"})
    guion = motion_storyboard.obtener(d, ESCENAS, W, H, FICHAS, ejecutar=falso,
                                      autos=motion.tipos_auto(ESCENAS, W, H), iconos=motion.ICONOS)
    assert len(pedidos) == 1 and "S015 (" in pedidos[0] and "bola" in pedidos[0], pedidos[0][:300]
    assert list(guion) == ["S015"] and len(guion["S015"]) == 6, guion
    # la cache: volver a montar no vuelve a preguntar
    otra = motion_storyboard.obtener(d, ESCENAS, W, H, FICHAS, ejecutar=falso)
    assert len(pedidos) == 1 and otra == guion
    # cambiar la frase de UN plano solo pregunta por ese
    cambiada = [dict(e, narracion=e["narracion"] + " hoy") if e["id"] == "S006" else e
                for e in ESCENAS]
    motion_storyboard.obtener(d, cambiada, W, H, FICHAS, ejecutar=falso)
    assert len(pedidos) == 2 and pedidos[1].count("<- ESCRIBE ESTE") == 1, pedidos[1][-200:]
    confs = motion.preparar(ESCENAS, {"motion": True},
                            {e["id"]: lam for e in ESCENAS if e["id"] != "S013"}, W, H,
                            hoy=2026, fichas=FICHAS, claude=guion)
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
    # segunda parte: piezas automaticas nuevas
    tipos = {e["id"]: [p["tipo"] for p in confs[e["id"]]["piezas"]
                       if p["id"].startswith(e["id"] + "-")] for e in ESCENAS}
    assert tipos["S010"] == ["antes"] and tipos["S011"] == ["arbol"], tipos
    assert tipos["S012"] == ["barras"], tipos
    def pieza(sid, tipo):
        return next(p for p in confs[sid]["piezas"]
                    if p["tipo"] == tipo and p["id"].startswith(sid + "-"))
    bar = pieza("S012", "barras")
    assert [b["v"] for b in bar["barras"]] == [70, 30] and bar["barras"][0]["t"] == "iglesia" and bar["barras"][1]["t"] == "mundo", bar
    arb = pieza("S011", "arbol")
    assert [n["t"] for n in arb["nodos"]] == ["Abraham", "Isaac", "Jacob"], arb
    # muñecos: sin lamina, grandes en el centro; quien habla mueve la boca con la voz
    figs = pieza("S013", "personajes")
    pedro, maria = figs["figuras"]
    assert pedro["gesto"] == "hablar" and len(pedro["habla"]) == 6 and pedro["etiqueta"], pedro
    assert maria["gesto"] == "escuchar" and maria["mujer"] and not maria["habla"], maria
    assert pedro["tunica"] == "#3d5f9e" or pedro["tunica"].startswith("#"), pedro
    # con lamina, pequeños delante; el miedo se ve en la cara y en el cuerpo
    assert tipos["S014"][0] == "lamina" and tipos["S014"][-1] == "personajes", tipos
    m14 = pieza("S014", "personajes")["figuras"][0]
    assert m14["expr"] == "miedo" and m14["gesto"] == "asustarse", m14
    # el storyboard de Claude manda en S015; la pieza inventada se descarta (y la coma
    # antes de cerrar del JSON no lo rompe)
    assert tipos["S015"] == ["texto", "icono", "personajes", "flecha", "circulo"], tipos
    f15 = pieza("S015", "personajes")
    assert f15["figuras"][0]["gesto"] == "saltar" and f15["figuras"][0]["expr"] == "alegria"
    # el puente no aterriza en la flecha ni en el circulo
    assert all(q["icono"] != "flecha" for q in confs["S015"]["puentes"])
    # sonidos: un whoosh por viaje y pops que no se amontonan
    ev = motion_mas.eventos_sonido(confs)
    assert sum(1 for e in ev if e[1] == "whoosh") == len(ESCENAS) - 1, ev[:5]
    pops = [e[0] for e in ev if e[1] == "pop"]
    assert pops and all(b - a >= 0.14 for a, b in zip(pops, pops[1:])), pops
    muestras = motion_mas.pista(ev[:3])
    assert all(m.shape[1] == 2 and abs(m).max() <= 1.0 for _, m, _ in muestras)
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
        nav = pw.chromium.launch(executable_path=os.environ.get("ESTUDIO_CHROMIUM") or None)
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
