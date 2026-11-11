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
    comprobar(p7.banda_subtitulo(v)["suelo"] == 1280.0, "vertical abajo: a un tercio")
    for salida in (h, v):
        centro = p7.banda_subtitulo(salida, {"subtitulo_pos": "centro"})
        alto = salida[1]
        comprobar(0.5 * alto < centro["suelo"] < 0.62 * alto,
                  f"{salida}: «centro» pone la base cerca de la mitad ({centro['suelo']})")
        comprobar(centro["ancho"] == p7.banda_subtitulo(salida)["ancho"],
                  f"{salida}: «centro» no cambia el ancho")
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
