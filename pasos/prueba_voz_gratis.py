"""
Prueba de la VOZ GRATUITA (voces neuronales de Microsoft Edge).

No sale a la red: el servicio de Microsoft se dobla con un tono de ffmpeg y unas
marcas de palabra a cadencia fija, asi que la suite comprueba NUESTRO codigo
--como se parte el guion, como se cosen los trozos, que tiempos salen, como se
elige la voz-- y no el humor del servicio ese dia.

  1. las piezas: que es una voz gratuita, la velocidad en porcentaje, que voz
     se elige segun el video, Configuracion y el idioma;
  2. el guion anotado se parte en cada <break> y mete su silencio; <spell>
     se deletrea; speed/volume/emotion no se locutan;
  3. una toma: tiempos ABSOLUTOS y crecientes, la duracion cuadra con el wav;
  4. el paso de voz entero (`p4_voz.sintetizar_bloques`) con la voz gratuita:
     bloques con su tramo, aire entre bloques, resumen, y Cartesia sin tocar;
  5. el modo se cambia en ajustes y manda: con Cartesia puesto no se usa.

    python pasos/prueba_voz_gratis.py
"""
import asyncio
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "pasos"))

CARPETA = os.path.join(tempfile.gettempdir(), "estudio_prueba_voz_gratis")
if os.path.isdir(CARPETA):
    shutil.rmtree(CARPETA)
os.makedirs(CARPETA)
os.environ["ESTUDIO_AJUSTES"] = os.path.join(CARPETA, "ajustes.json")
os.environ["ESTUDIO_ESTADISTICAS"] = os.path.join(CARPETA, "estadisticas.json")
os.environ.pop("ESTUDIO_SIMULAR", None)

import ajustes  # noqa: E402
import p4_voz  # noqa: E402
import voz_gratis  # noqa: E402

_fallos = []
_comprobaciones = [0]


def ok(condicion, mensaje):
    _comprobaciones[0] += 1
    if not condicion:
        _fallos.append(mensaje)
        print(f"    FALLO: {mensaje}")
    else:
        print(f"  ok   {mensaje}")
    return bool(condicion)


def igual(obtenido, esperado, mensaje):
    return ok(obtenido == esperado,
              f"{mensaje} (obtenido {obtenido!r}, esperado {esperado!r})")


# ------------------------------------------------- el doble del servicio

PASO_S = 0.3          # cada palabra dura 0,3 s en el doble
PEDIDOS = []          # (texto, voz, velocidad) que ha recibido el «servicio»


async def _doble(edge, texto, voz, velocidad):
    """Lo que devolveria Edge: un mp3 del largo justo y una marca por palabra."""
    PEDIDOS.append((texto, voz, velocidad))
    palabras = texto.split()
    duracion = max(0.2, len(palabras) * PASO_S + 0.1)
    mp3 = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
         f"sine=frequency=220:duration={duracion}", "-ac", "1", "-ar", "24000",
         "-f", "mp3", "pipe:1"], capture_output=True, check=True).stdout
    marcas = [{"w": p.strip(".,;:¿?¡!«»"), "s": round(0.05 + i * PASO_S, 3),
               "e": round(0.05 + i * PASO_S + PASO_S * 0.8, 3)}
              for i, p in enumerate(palabras)]
    return mp3, marcas


voz_gratis._sintetizar_trozo = _doble          # noqa: SLF001
voz_gratis._edge = lambda: None                 # noqa: SLF001


def probar_piezas():
    print("\n  LAS PIEZAS")
    for voz, es in (("es-PE-AlexNeural", True), ("en-US-AndrewMultilingualNeural", True),
                    ("es-MX-JorgeNeural", True),
                    ("a0e99841-438c-4a64-b679-ae501e7d6091", False), ("", False),
                    ("Alex", False)):
        igual(voz_gratis.es_voz_gratis(voz), es, f"«{voz}» {'es' if es else 'no es'} voz gratuita")
    igual(voz_gratis.porcentaje_velocidad("slow"), "-15%", "slow es un 15 % mas lenta")
    igual(voz_gratis.porcentaje_velocidad(None), "+0%", "sin velocidad, normal")
    igual(voz_gratis.porcentaje_velocidad(1.0), "+35%", "el tope numerico")
    igual(voz_gratis.porcentaje_velocidad(-2), "-35%", "y se acota")
    igual(voz_gratis.elegir("es-PE-CamilaNeural", "es", "es-ES-AlvaroNeural"),
          "es-PE-CamilaNeural", "manda la voz gratuita del video")
    igual(voz_gratis.elegir("a0e99841-uuid", "es", "es-ES-AlvaroNeural"),
          "es-ES-AlvaroNeural", "un id de Cartesia cae a la de Configuracion")
    igual(voz_gratis.elegir("a0e99841-uuid", "es", ""), "es-MX-JorgeNeural",
          "y sin ninguna, a la de fabrica del idioma")
    igual(voz_gratis.elegir("es-PE-AlexNeural", "en", ""), "en-US-AndrewNeural",
          "una voz de otro idioma no narra este")
    igual(voz_gratis.elegir("en-US-AndrewMultilingualNeural", "es", ""),
          "en-US-AndrewMultilingualNeural", "salvo que sea multilingue")


def probar_trozos():
    print("\n  EL GUION ANOTADO")
    trozos = voz_gratis._trozos(                                # noqa: SLF001
        'Uno dos. <break time="1s"/> Tres <speed ratio="0.8"/>cuatro. '
        '<break time="500ms"/><break time="500ms"/> La <spell>ONU</spell> habla.'
        '<emotion value="sad"/>')
    igual([t for t, _s in trozos], ["Uno dos.", "Tres cuatro.", "La O N U habla."],
          "se parte en cada pausa y no se locuta ninguna etiqueta")
    igual([round(s, 2) for _t, s in trozos], [0.8, 0.8, 0.0],
          "cada pausa mete 0,8x lo pedido, y dos seguidas se suman")
    igual(voz_gratis._trozos("<break time=\"1s\"/>"), [],        # noqa: SLF001
          "una pausa sin texto no deja nada que locutar")


def probar_toma():
    print("\n  UNA TOMA")
    PEDIDOS.clear()
    pcm, duracion, palabras = voz_gratis.toma(
        'Diez millones esperaban. <break time="1s"/> Nadie sabia nada.',
        "es-PE-AlexNeural", "slow", sr=44100)
    igual(len(PEDIDOS), 2, "un pedido por trozo")
    igual({v for _t, v, _r in PEDIDOS}, {"es-PE-AlexNeural"}, "con la voz pedida")
    igual({r for _t, _v, r in PEDIDOS}, {"-15%"}, "y su velocidad")
    igual([p["w"] for p in palabras],
          ["Diez", "millones", "esperaban", "Nadie", "sabia", "nada"],
          "todas las palabras, en orden")
    inicios = [p["s"] for p in palabras]
    ok(inicios == sorted(inicios), "los tiempos crecen")
    ok(palabras[3]["s"] - palabras[2]["e"] > 0.8,
       f"la pausa escrita se oye entre los trozos ({palabras[3]['s'] - palabras[2]['e']:.2f} s)")
    igual(round(len(pcm) / (44100 * 2), 3), round(duracion, 3),
          "la duracion es la del audio a 44,1 kHz")
    ok(palabras[-1]["e"] <= duracion, "ninguna palabra acaba despues del audio")


def probar_paso():
    print("\n  EL PASO DE VOZ ENTERO")
    ajustes.guardar({"modo_voz": "gratis", "voz_gratis": "es-PE-CamilaNeural"})
    ok(p4_voz.gratis(), "el modo gratuito queda puesto")

    def prohibido(*_a, **_k):
        raise AssertionError("la voz gratuita ha llamado a Cartesia")
    p4_voz._toma_real = prohibido                              # noqa: SLF001
    p4_voz._toma_por_contexto = prohibido                      # noqa: SLF001

    cfg = p4_voz.resolver_params({"voz_id": "a0e99841-438c-4a64-b679-ae501e7d6091",
                                  "idioma": "es", "velocidad": "normal",
                                  "hueco_minimo": 0.6})
    igual(cfg["motor_voz"], "gratis", "la configuracion dice voz gratuita")
    igual(cfg["voz_gratis"], "es-PE-CamilaNeural",
          "con la voz de Cartesia del estilo, usa la de Configuracion")
    bloques = [
        {"id": "B001", "texto": "Diez millones de personas esperaban aquel dia."},
        {"id": "B002", "texto": 'Nadie sabia lo que iba a pasar. <break time="700ms"/> '
                                "Pero algo cambio."},
        {"id": "B003", "texto": "Y todo empezo de nuevo en Jerusalen."},
    ]
    destino = os.path.join(CARPETA, "toma")
    salidas = p4_voz.sintetizar_bloques(bloques, destino, cfg)
    ok(os.path.isfile(os.path.join(destino, "narracion.wav")), "deja la pista")
    ok(os.path.isfile(os.path.join(destino, "audio_meta.json")), "y su meta")
    igual([b["palabras"] for b in salidas["bloques"]], [7, 10, 7],
          "cada bloque se lleva sus palabras")
    tramos = [(b["t_in"], b["t_out"]) for b in salidas["bloques"]]
    ok(all(a[1] <= b[0] for a, b in zip(tramos, tramos[1:])),
       f"los bloques no se pisan: {tramos}")
    ok(all(b[0] - a[1] >= 0.55 for a, b in zip(tramos, tramos[1:])),
       "entre bloques queda el aire pedido")
    ok("voz gratuita es-PE-CamilaNeural" in salidas["resumen"],
       f"el resumen dice que voz ha sonado ({salidas['resumen']})")
    igual(salidas["controles"]["motor_voz"], "gratis", "y queda apuntado en los controles")

    cfg2 = p4_voz.resolver_params({"voz_id": "es-PE-AlexNeural", "idioma": "es"})
    igual(cfg2["voz_gratis"], "es-PE-AlexNeural",
          "una voz gratuita elegida en el video manda sobre Configuracion")

    print("\n  CON CARTESIA PUESTO")
    ajustes.guardar({"modo_voz": "cartesia"})
    ok(not p4_voz.gratis(), "el modo Cartesia queda puesto")
    cfg3 = p4_voz.resolver_params({"voz_id": "es-PE-AlexNeural", "idioma": "es"})
    igual(cfg3["motor_voz"], "cartesia", "la configuracion dice Cartesia")
    ok(not voz_gratis.es_voz_gratis(cfg3["voz_id"]),
       "y una voz gratuita guardada no se le manda a Cartesia")
    try:
        ajustes.guardar({"modo_voz": "eleven"})
        ok(False, "un modo de voz que no existe deberia rechazarse")
    except ValueError:
        ok(True, "un modo de voz que no existe se rechaza")
    try:
        ajustes.guardar({"voz_gratis": "Carlos"})
        ok(False, "una voz gratuita mal escrita deberia rechazarse")
    except ValueError:
        ok(True, "una voz gratuita mal escrita se rechaza")


def main():
    print("=" * 70)
    print("PRUEBA DE LA VOZ GRATUITA (servicio doblado, sin red)")
    print("=" * 70)
    if not shutil.which("ffmpeg"):
        print("falta ffmpeg: esta suite lo necesita")
        sys.exit(2)
    probar_piezas()
    probar_trozos()
    probar_toma()
    probar_paso()
    print()
    print("=" * 70)
    if _fallos:
        print(f"VOZ GRATUITA CON FALLOS: {len(_fallos)}")
        for fallo in _fallos:
            print(f"  - {fallo}")
        sys.exit(1)
    print(f"VOZ GRATUITA OK: {_comprobaciones[0]} comprobaciones pasan")


if __name__ == "__main__":
    main()
