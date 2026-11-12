"""
Prueba de pasos/boca.py (P7): la boca sigue el audio de verdad.

Sin red y sin Rhubarb (fuerza ESTUDIO_BOCA=energia): fabrica un wav con
golpes de voz y silencios y comprueba que la boca va CERRADA en el silencio y
ABIERTA en la voz, que el tramo de un plano sale en su tiempo, que llega a los
muñecos de motion y a las marionetas, y que el JavaScript de las dos paginas
compila y lee bien la lista (con node, si esta).

    python pasos/prueba_boca.py
"""
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["ESTUDIO_BOCA"] = "energia"

import boca  # noqa: E402
import marioneta  # noqa: E402
import motion_mas  # noqa: E402

FALLOS = []


def ok(cond, que):
    print(("  ok  " if cond else "  MAL ") + que)
    if not cond:
        FALLOS.append(que)


def wav_de_prueba(ruta, fr=16000):
    """0-1 s silencio, 1-2 s voz fuerte, 2-3 s silencio, 3-3,5 s voz suave."""
    muestras = []
    for i in range(int(3.5 * fr)):
        t = i / fr
        if 1 <= t < 2:
            a = 12000
        elif 3 <= t < 3.5:
            a = 3500
        else:
            a = 30
        muestras.append(int(a * math.sin(2 * math.pi * 180 * t)))
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fr)
        w.writeframes(struct.pack(f"<{len(muestras)}h", *muestras))


def forma_en(formas, t):
    for a, b, f in formas:
        if a <= t < b:
            return f
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="prueba_boca_")
    try:
        audio = os.path.join(tmp, "narracion.wav")
        wav_de_prueba(audio)
        print("el audio:")
        formas = boca.formas_de(audio, os.path.join(tmp, "cache"), avisar=lambda m: None)
        ok(bool(formas), "salen formas")
        ok(forma_en(formas, 0.5) == "X", "cerrada en el silencio del principio")
        ok(forma_en(formas, 1.5) in ("C", "D"), "abierta en la voz fuerte")
        ok(forma_en(formas, 2.5) == "X", "cerrada en la pausa")
        ok(forma_en(formas, 3.25) not in (None, "X", "D"), f"entreabierta en la voz suave ({forma_en(formas, 3.25)})")
        ok(os.path.exists(os.path.join(tmp, "cache", "boca.json")), "se guarda")
        ok(boca.formas_de(audio, os.path.join(tmp, "cache"), avisar=lambda m: None) == formas,
           "la segunda vez sale lo guardado")

        print("los planos:")
        tr = boca.tramo(formas, 1.0, 2.0)
        ok(tr and tr[0][0] >= 1.0 and tr[-1] == [2.0, 0.0, 0.0], "tramo en tiempo del video y cierra al final")
        tr = boca.tramo(formas, 1.0, 2.0, desde=1.0)
        ok(tr[0][0] < 0.2 and tr[-1][0] == 1.0, "tramo en tiempo del plano (marioneta)")

        fig = {"habla": [[1.0, 1.4, 2], [1.4, 1.9, 1]]}
        conf = {"piezas": [{"tipo": "personajes", "figuras": [fig, {"habla": []}]}]}
        ok(boca.aplicar_motion({"e1": conf}, formas) == 1, "un muñeco de motion con boca")
        ok(fig["boca"][0][0] >= 1.0 and fig["boca"][-1][0] == 1.9, "su boca va de 1,0 a 1,9 s")

        mar = marioneta.configurar({"personajes": ["Pedro"], "narracion": "Pedro dijo"}, {})
        boca.aplicar_marioneta(mar, formas, {"t_in": 1.0, "t_out": 2.0})
        ok(bool(mar.get("boca")), "la marioneta lleva su boca")

        os.environ["ESTUDIO_BOCA"] = "no"
        ok(boca.formas_de(audio, None) == [], "ESTUDIO_BOCA=no la apaga")
        os.environ["ESTUDIO_BOCA"] = "energia"

        node = shutil.which("node")
        if node:
            print("la pagina (node):")
            for nombre, js, fn in (("motion", motion_mas.MOTION_MAS_JS, "bocaEn"),
                                   ("marioneta", marioneta.MARIONETA_JS, "marBoca")):
                # la pagina entera solo se COMPILA (pide el DOM); la funcion
                # de la boca se saca sola y se ejecuta
                entera = os.path.join(tmp, f"{nombre}_entera.js")
                with open(entera, "w", encoding="utf-8") as f:
                    f.write(js)
                r = subprocess.run([node, "--check", entera], capture_output=True, text=True)
                ok(r.returncode == 0, f"{nombre}: el JS compila {r.stderr.strip()[:160]}")
                ini = js.index(f"function {fn}(")
                cuerpo = js[ini:js.index("\nfunction ", ini + 10)]
                ruta = os.path.join(tmp, f"{nombre}.js")
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(cuerpo)
                    f.write(f"\nconst L = [[1,0,0],[1.5,1,0],[2,0,0]];"
                            f"\nconsole.log(JSON.stringify([{fn}(L, 1.2), {fn}(L, 1.7), {fn}(L, 2.5)]));\n")
                r = subprocess.run([node, ruta], capture_output=True, text=True)
                ok(r.returncode == 0, f"{nombre}: la boca corre {r.stderr.strip()[:160]}")
                if r.returncode == 0:
                    a, b, c = json.loads(r.stdout.strip().splitlines()[-1])
                    ok(a[0] == 0 and b[0] == 1 and (c is None or c[0] == 0),
                       f"{nombre}: cerrada, abierta y fuera de tramo")
        else:
            print("  (sin node: no se prueba el JS)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nTODO BIEN" if not FALLOS else f"\n{len(FALLOS)} FALLOS")
    return 1 if FALLOS else 0


if __name__ == "__main__":
    sys.exit(main())
