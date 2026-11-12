"""Prueba de la posicion del subtitulo elegible (abajo / centro, 11-nov-2026).

    python pasos/prueba_subtitulo_pos.py

Sin red, sin Claude, sin claves: solo cuentas y el cableado de la pantalla.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import p7_callouts as p7  # noqa: E402

FALLOS = []


def comprobar(cond, texto):
    print(("  ok  " if cond else "  MAL ") + texto)
    if not cond:
        FALLOS.append(texto)


def main():
    h, v = (1920, 1080), (1080, 1920)
    # «abajo» es lo de siempre: sin param, con «abajo» o con basura, igual
    for salida in (h, v):
        base = p7.banda_subtitulo(salida)
        comprobar(base == p7.banda_subtitulo(salida, {"subtitulo_pos": "abajo"})
                  == p7.banda_subtitulo(salida, {"subtitulo_pos": "raro"})
                  == p7.banda_subtitulo(salida, {}),
                  f"{salida}: sin param, «abajo» o un valor raro dan la banda de siempre")
    comprobar(p7.banda_subtitulo(h)["suelo"] == 1080 - p7.SUB_MARGEN,
              "horizontal abajo: al pie")
    # 12-11-2026: en el cuarto de abajo (no a un tercio: tapaba cabezas) y por
    # encima de los controles del movil
    suelo = p7.banda_subtitulo(v)["suelo"]
    comprobar(0.75 * 1920 < suelo < 0.85 * 1920,
              f"vertical abajo: en el cuarto de abajo ({suelo})")
    # el palabra a palabra es el de siempre y va mas grande que el clasico
    grande = p7.letra_subtitulo({}, v)
    clasico = p7.letra_subtitulo({"subtitulo_estilo": "clasico"}, v)
    comprobar(grande["palabras"] and not clasico["palabras"],
              "sin param, palabra a palabra; «clasico» a mano")
    comprobar(grande["tam"] >= 85 and grande["tam"] > clasico["tam"] * 1.25,
              f"palabra a palabra grande ({grande['tam']} px frente a {clasico['tam']})")
    comprobar(grande["cap_trozo"] == grande["cap"] and grande["cap"] <= 16,
              f"un renglon corto por trozo ({grande['cap']} caracteres)")
    for salida in (h, v):
        centro = p7.banda_subtitulo(salida, {"subtitulo_pos": "centro"})
        alto = salida[1]
        comprobar(0.5 * alto < centro["suelo"] < 0.62 * alto,
                  f"{salida}: «centro» pone la base cerca de la mitad ({centro['suelo']})")
        comprobar(centro["ancho"] == p7.banda_subtitulo(salida)["ancho"],
                  f"{salida}: «centro» no cambia el ancho")
    # un trozo nunca junta el final de una frase con la siguiente («nombre La
    # Biblia» en el video de prueba del 12-11-2026)
    import subtitulos
    pal = "Dios conoce tu nombre. La Biblia lo dice. Sí.".split()
    for cap in (14, 38):
        textos = [" ".join(pal[a:b]) for a, b in
                  subtitulos.tramos(pal, cap_linea=cap, cap_trozo=cap)]
        comprobar(all(not any(w.endswith(".") for w in t.split()[:-1]) for t in textos),
                  f"con {cap} caracteres, ningun trozo cruza un punto: {textos}")
    # el tope de renglon sale de la misma banda
    plan = {"resolucion": list(h)}
    comprobar(p7.cap_subtitulo_de({"subtitulo_pos": "centro"}, plan) is not None,
              "cap_subtitulo_de acepta la posicion")

    raiz = os.path.dirname(AQUI)
    js = open(os.path.join(raiz, "web", "app.js"), encoding="utf-8").read()
    py = open(os.path.join(raiz, "app.py"), encoding="utf-8").read()
    comprobar("{ clave: 'subtitulo_pos', paso: 'callouts', param: 'subtitulo_pos' }" in js,
              "«El encargo» guarda la posicion")
    comprobar(js.count("selectorSubtitulo(e, () => {})") == 1 and js.count("selectorSubtitulo(e, programarGuardadoEncargo)") == 1,
              "el selector sale al crear y en «El encargo»")
    comprobar("subtitulo_pos: e.subtitulo_pos || ''" in js, "crear el video la envia")
    comprobar('{"subtitulo_pos": "centro"}' in py and '"subtitulo_pos": "abajo"' not in py,
              "al crear solo se escribe «centro» (abajo no mueve firmas)")
    print()
    if FALLOS:
        print(f"FALLAN {len(FALLOS)}")
        sys.exit(1)
    print("todo bien")


if __name__ == "__main__":
    main()
