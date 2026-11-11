"""Prueba de la etapa 7 (publicar fácil): textos, capítulos, miniatura y Drive.

Gratis y sin red: no llama a Claude ni a rclone de verdad.
    python pasos/prueba_publicar.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402

import publicar  # noqa: E402

GUION = {"titulo": "Los dos Belén de la Biblia", "guion": [
    {"id": "B1", "texto": "¿Sabías que en la Biblia hay dos Belén? <break time='1s'/> "
                          "Miqueas 5:2 dice cuál es. Y Jesús nació en uno."},
    {"id": "B2", "texto": "Belén de Judea estaba cerca de Jerusalén, la ciudad de David."},
    {"id": "B3", "texto": "El otro Belén estaba en Galilea, lejos de allí. Lucas 2:4 lo aclara."},
]}
ESCENAS = [{"id": "S001", "t_in": 0, "origen": {"bloque": "B1"}},
           {"id": "S002", "t_in": 14, "origen": {"bloque": "B2"}},
           {"id": "S003", "t_in": 30, "origen": {"bloque": "B3"}}]


def main():
    t = publicar.textos("x", GUION, ESCENAS, 50.0, vertical=False)
    assert t["titulo"] == "Los dos Belén de la Biblia", t["titulo"]
    assert all(len(x) <= 70 for x in t["titulos"]) and len(t["titulos"]) >= 2
    assert "<break" not in t["descripcion"]
    assert "Miqueas 5:2" in t["versiculos"] and "Lucas 2:4" in t["versiculos"], t["versiculos"]
    assert t["tema"] == "fe" and "#biblia" in t["hashtags"], t["hashtags"]
    assert len(t["hashtags"]) <= publicar.MAX_HASHTAGS
    assert t["capitulos"][0].startswith("0:00 ") and len(t["capitulos"]) == 3, t["capitulos"]
    assert "Capítulos" in t["descripcion"] and "Versículos" in t["descripcion"]
    assert t["miniatura"] and len(t["miniatura"].split()) <= 4
    # capítulos imposibles (uno de menos de 10 s) -> ninguno
    corto = [dict(e) for e in ESCENAS]
    corto[1]["t_in"] = 25
    assert publicar.capitulos(corto, GUION["guion"], 50) == []
    # vertical: #shorts delante y sin capítulos
    v = publicar.textos("x", GUION, ESCENAS, 50.0, vertical=True)
    assert v["hashtags"][0] == "#shorts" and not v["capitulos"]
    assert len(v["tiktok"]) < 200 and "#shorts" not in v["tiktok"]
    assert "TEXTO PARA TIKTOK" in publicar.como_txt(t)

    with tempfile.TemporaryDirectory() as tmp:
        img = os.path.join(tmp, "S001.png")
        Image.new("RGB", (1920, 1080), (90, 120, 160)).save(img)
        for formato, tam in publicar.TAMANOS.items():
            salida = publicar.miniatura(img, "DOS BELÉN BIBLIA", os.path.join(
                tmp, "publicar", f"{formato}.jpg"), formato)
            con = Image.open(salida)
            assert con.size == tam, (formato, con.size)
            # el texto (blanco/amarillo) se ha dibujado
            assert con.getchannel("R").getextrema()[1] > 240
        sin = publicar.miniatura(None, "", os.path.join(tmp, "sin.jpg"))
        assert Image.open(sin).size == publicar.TAMANOS["youtube"]

    camino = os.environ.get("PATH", "")
    os.environ["PATH"] = ""                      # sin rclone a la vista
    listo, motivo = publicar.drive_listo()
    assert not listo and "rclone" in motivo

    # un rclone de mentira: apunta lo que le piden y da un enlace
    with tempfile.TemporaryDirectory() as tmp:
        falso = os.path.join(tmp, "rclone")
        registro = os.path.join(tmp, "llamadas.txt")
        with open(falso, "w") as fh:
            fh.write("#!/bin/sh\n"
                     f'echo "$@" >> "{registro}"\n'
                     'case "$1" in listremotes) echo "drive:";; '
                     'link) echo "https://drive.example/carpeta";; esac\n')
        os.chmod(falso, 0o755)
        os.environ["PATH"] = tmp + os.pathsep + camino
        assert publicar.drive_listo() == (True, "")
        fichero = os.path.join(tmp, "video.mp4")
        open(fichero, "wb").close()
        enlace = publicar.subir_a_drive([fichero], "Mi/vídeo")
        assert enlace == "https://drive.example/carpeta", enlace
        llamadas = open(registro).read()
        assert "copy" in llamadas and "drive:Shaddai Studio/Mi-vídeo" in llamadas, llamadas
    os.environ["PATH"] = camino
    print("prueba_publicar: OK")


if __name__ == "__main__":
    main()
