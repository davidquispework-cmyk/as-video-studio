"""Prueba corta de los clips de video por plano (pasos/clips.py). Sin navegador.

    python pasos/prueba_clips.py
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["ESTUDIO_AJUSTES"] = os.path.join(tempfile.mkdtemp(), "ajustes.json")

import clips  # noqa: E402
import subidas  # noqa: E402
import medios  # noqa: E402


def main():
    raiz = tempfile.mkdtemp(prefix="prueba_clips_")
    fuente = os.path.join(raiz, "kling.mp4")
    subprocess.run([medios.ffmpeg(), "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "testsrc2=size=640x360:rate=24:duration=1", fuente],
                   check=True)
    with open(fuente, "rb") as fh:
        ficha = clips.guardar(raiz, "S002", fh.read(), "vertical", "kling.mp4")
    assert ficha["segundos"] >= 0.9, ficha
    assert subidas.existe(raiz, "S002"), "sin imagen sacada del clip"
    assert "S002" in clips.listar(raiz)
    fotos = clips.extraer_fotogramas(clips.ruta_de(raiz, "S002"),
                                     os.path.join(raiz, "f"), 30, 45)
    assert len(fotos) == 45 and fotos[-1] == fotos[-2], "no congela el final"
    try:
        clips.guardar(raiz, "S003", b"no soy un video", "vertical", "x.mp4")
        raise AssertionError("acepto basura")
    except ValueError:
        pass
    listo, motivo = clips.automatico_disponible()
    assert not listo and "apagado" in motivo, "el modo de pago no esta apagado"
    assert clips.borrar(raiz, "S002") and not clips.existe(raiz, "S002")
    print("prueba_clips: OK")


if __name__ == "__main__":
    main()
