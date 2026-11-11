"""
Prueba de LA VOZ GRABADA (pasos/voz_propia.py).

No hace falta una voz de verdad: se fabrica una «grabacion» con ffmpeg donde
cada frase es un tono (con huecos cortos entre palabras, como las oclusivas) y
entre frases hay silencio. Asi se sabe donde empieza y acaba cada frase y se
comprueba que el alineado las encuentra.

  1. guardar: cualquier audio -> wav mono 44,1 kHz limpio, con huella; los
     ficheros que no son audio se rechazan;
  2. alinear: cada frase empieza y acaba donde suena (±0,25 s), las palabras
     van en orden y sin solaparse;
  3. resolver_params: con `grabacion` en los params el motor es «propia»;
  4. el paso de voz entero (`sintetizar_bloques`) con la grabacion: la pista
     dura lo que la grabacion, cada bloque tiene su tramo y el resumen lo dice;
     regrabar un tramo suelto se niega.

    python pasos/prueba_voz_propia.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import wave

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "pasos"))

CARPETA = os.path.join(tempfile.gettempdir(), "estudio_prueba_voz_propia")
if os.path.isdir(CARPETA):
    shutil.rmtree(CARPETA)
os.makedirs(CARPETA)
os.environ["ESTUDIO_AJUSTES"] = os.path.join(CARPETA, "ajustes.json")
os.environ["ESTUDIO_ESTADISTICAS"] = os.path.join(CARPETA, "estadisticas.json")
os.environ.pop("ESTUDIO_SIMULAR", None)

import voz_propia  # noqa: E402
import p4_voz  # noqa: E402

FALLOS = []


def comprobar(cond, texto):
    print(("  ok   " if cond else "  MAL  ") + texto)
    if not cond:
        FALLOS.append(texto)


# Tres frases: (texto, segundos de voz). Entre frases, 0,7 s de silencio.
FRASES = [("En el principio era el Verbo, y el Verbo era con Dios.", 3.2),
          ("Todo fue hecho por él.", 1.6),
          ("¿Quién puede contar las estrellas del cielo?", 2.6)]
PAUSA = 0.7
INICIO = 0.5


def fabricar(destino):
    """Una grabacion falsa en m4a: tonos por palabra, silencios entre frases."""
    partes, t, esperado = [], INICIO, []
    filtros = []
    for texto, dur in FRASES:
        palabras = texto.split()
        por_palabra = dur / len(palabras)
        esperado.append((t, t + dur))
        for _ in palabras:
            # voz: tono de por_palabra - 0,06 s y un hueco de 0,06 s (oclusiva)
            filtros.append((t, t + por_palabra - 0.06))
            t += por_palabra
        t += PAUSA
    total = t + 0.4
    expr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in filtros)
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
         "-i", f"sine=frequency=220:duration={total:.2f}",
         "-f", "lavfi", "-i", f"anoisesrc=amplitude=0.002:duration={total:.2f}",
         "-filter_complex", f"[0]volume='0.6*({expr})':eval=frame[v];[v][1]amix=2",
         "-c:a", "aac", destino], check=True)
    return esperado, total


print("1. guardar")
raiz = os.path.join(CARPETA, "proyecto")
os.makedirs(raiz)
origen = os.path.join(CARPETA, "mi_voz.m4a")
esperado, total = fabricar(origen)
with open(origen, "rb") as fh:
    hecho = voz_propia.guardar(raiz, fh.read(), "mi_voz.m4a")
comprobar(voz_propia.existe(raiz), "queda en subidas/voz/grabacion.wav")
with wave.open(voz_propia.ruta(raiz)) as wav:
    comprobar(wav.getnchannels() == 1 and wav.getframerate() == 44100,
              "mono a 44,1 kHz")
comprobar(abs(hecho["duracion"] - total) < 0.3, f"dura lo mismo ({hecho['duracion']} s)")
comprobar(len(hecho["huella"]) == 16, "trae huella")
for malo, nombre in ((b"no soy audio", "notas.txt"), (b"basura" * 100, "x.mp3")):
    try:
        voz_propia.guardar(os.path.join(CARPETA, "otro"), malo, nombre)
        comprobar(False, f"rechaza {nombre}")
    except ValueError:
        comprobar(True, f"rechaza {nombre}")

print("2. alinear")
texto = " ".join(f for f, _d in FRASES)
pcm = voz_propia.a_pcm(voz_propia.ruta(raiz))
palabras = voz_propia.alinear(pcm, 44100, texto)
comprobar(len(palabras) == len(texto.split()), "una marca por palabra")
comprobar(all(p["e"] > p["s"] for p in palabras), "cada palabra dura algo")
comprobar(all(palabras[k]["s"] >= palabras[k - 1]["e"] - 1e-6
              for k in range(1, len(palabras))), "en orden y sin solaparse")
k = 0
for (frase, _d), (a, b) in zip(FRASES, esperado):
    n = len(frase.split())
    s, e = palabras[k]["s"], palabras[k + n - 1]["e"]
    comprobar(abs(s - a) < 0.25 and abs(e - b) < 0.25,
              f"«{frase[:22]}…» {s:.2f}-{e:.2f} (suena {a:.2f}-{b:.2f})")
    k += n

print("3. resolver_params")
cfg = p4_voz.resolver_params({"grabacion": hecho["huella"]})
comprobar(cfg["motor_voz"] == "propia" and cfg["grabacion"] == hecho["huella"],
          "con grabacion el motor es «propia»")
comprobar(p4_voz.resolver_params({})["motor_voz"] != "propia", "sin ella, no")

print("4. el paso de voz con la grabacion")
bloques = [{"id": f"B{i + 1:03d}", "texto": f} for i, (f, _d) in enumerate(FRASES)]
destino = os.path.join(CARPETA, "trabajo")
salidas = p4_voz.sintetizar_bloques(
    bloques, destino, dict(cfg, hueco_minimo=0),
    grabacion=p4_voz.grabacion_de(type("P", (), {"raiz": raiz})(), cfg))
comprobar(abs(salidas["duracion"] - total) < 0.3, f"la pista dura {salidas['duracion']} s")
comprobar(all(b["t_in"] is not None for b in salidas["bloques"]), "cada bloque tiene tramo")
comprobar(abs(salidas["bloques"][1]["t_in"] - esperado[1][0]) < 0.25,
          "el segundo bloque empieza donde suena")
comprobar("tu voz grabada" in salidas["resumen"], "el resumen lo dice")
try:
    p4_voz.regrabar_seccion(bloques, "SB001", cfg, salidas, destino)
    comprobar(False, "regrabar un tramo se niega")
except RuntimeError:
    comprobar(True, "regrabar un tramo se niega")

shutil.rmtree(CARPETA, ignore_errors=True)
if FALLOS:
    print(f"\n{len(FALLOS)} FALLOS")
    sys.exit(1)
print("\nTODO BIEN")
