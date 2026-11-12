"""Prueba de las siluetas a contraluz (pasos/ambiente.py, P4). Sin red, sin rembg.

    python pasos/prueba_contraluz.py            lo automatico y lo de a mano
    python pasos/prueba_contraluz.py --ver DIR  ademas guarda la silueta y un
                                                fotograma de render en DIR
"""
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ambiente  # noqa: E402


def _figura(carpeta, tam=(768, 512)):
    """Una «persona» de colores claros sobre transparente: cabeza y cuerpo."""
    img = Image.new("RGBA", tam, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((350, 120, 420, 190), fill=(230, 200, 170, 255))
    d.rectangle((330, 190, 440, 420), fill=(200, 200, 230, 255))
    ruta = os.path.join(carpeta, "fig.png")
    img.save(ruta)
    return ruta


def probar_eleccion():
    assert "contraluz" in ambiente.elegir("El rico en el hades, en tormento")
    assert "contraluz" in ambiente.elegir("Su silueta al atardecer")
    assert "contraluz" not in ambiente.elegir("Jesús enseñaba en la sinagoga")
    cc = lambda *a: ambiente.color_contraluz(*a)[0]  # noqa: E731
    # el color sigue lo que se cuenta
    assert cc("el infierno y el abismo") == "fuego"
    assert cc("de noche, bajo la luna") == "luna"
    assert cc("al atardecer") == "oro"
    assert cc("Caín mató a su hermano y la sangre clamaba") == "sangre"
    assert cc("La gloria del ángel llenó el cielo") == "gloria"
    assert cc("La tormenta y los relámpagos sobre la barca") == "tormenta"
    assert cc("La serpiente y el pecado") == "tinieblas"
    assert cc("Al amanecer volvió con esperanza") == "amanecer"
    assert cc("María caminaba sin miedo") != "mar"         # «mar» no es «María»
    # gana el que mas sale
    assert cc("noche de sangre, sangre y muerte") == "sangre"
    # a mano manda: un nombre o un color cualquiera
    assert cc("al atardecer", "luna") == "luna"
    assert ambiente.color_contraluz("x", "#ff8800") == ("propio", (255, 136, 0))
    # sin pistas en el texto, el color sale de la imagen
    with tempfile.TemporaryDirectory() as d:
        r = os.path.join(d, "i.png")
        img = Image.new("RGB", (300, 200), (20, 20, 30))
        ImageDraw.Draw(img).ellipse((120, 60, 180, 120), fill=(80, 220, 120))
        img.save(r)
        nombre, rgb = ambiente.color_contraluz("Pedro habló a la gente", None, r)
        assert nombre == "imagen" and rgb[1] > rgb[0] and rgb[1] > rgb[2], rgb
    assert all(k in ambiente.PALETA_LISTA[0] for k in ("nombre", "etiqueta", "hex"))


def probar_silueta(carpeta):
    fig = _figura(carpeta)
    sil = ambiente.silueta(fig, carpeta, (255, 120, 40))
    assert os.path.exists(sil["figura"]) and sil["rgb"] == [255, 120, 40]
    a = np.asarray(Image.open(sil["figura"]).convert("RGBA"), dtype=np.int32)
    # el centro del cuerpo queda casi negro, opaco
    cuerpo = a[300, 385]
    assert cuerpo[3] > 240 and cuerpo[:3].max() < 60, cuerpo
    # el borde de arriba de la cabeza brilla con el color del fuego
    borde = a[123, 385]
    assert borde[0] > 150 and borde[0] > borde[2], borde
    # fuera de la figura hay halo, translucido
    halo = a[300, 448]
    assert 0 < halo[3] < 255, halo
    # lejos, nada
    assert a[20, 20][3] == 0
    assert 0.4 < sil["centro"][0] < 0.6 and 0.3 < sil["alto"] < 0.7
    # cache: la segunda vez no rehace
    assert ambiente.silueta(fig, carpeta, (255, 120, 40)) == sil
    return fig


def probar_configurar(carpeta, fig):
    real = ambiente.preparar
    try:
        ambiente.preparar = lambda *a, **k: {"foco": [0.5, 0.4], "figura": fig,
                                             "fondo": fig, "ancla": [0.5, 0.8]}
        esc = {"id": "s1", "narracion": "Lázaro en el seno de Abraham y el rico en el hades"}
        c = ambiente.configurar(esc, fig, carpeta, {})
        assert "contraluz" in c["efectos"] and c["contraluz"]["color"] == "fuego"
        assert c["figura"].endswith("_silueta.png")
        # apagado en todo el video
        c = ambiente.configurar(esc, fig, carpeta, {"contraluz": False})
        assert "contraluz" not in c["efectos"] and "contraluz" not in c
        # forzado a mano en un plano que no lo pide
        esc2 = {"id": "s2", "narracion": "Pedro habló a la gente", "contraluz": "luna"}
        c = ambiente.configurar(esc2, fig, carpeta, {})
        assert c["contraluz"]["color"] == "luna"
        assert c["contraluz"]["rgb"] == [170, 200, 255]
        # color propio
        c = ambiente.configurar(dict(esc2, contraluz="#00ff00"), fig, carpeta, {})
        assert c["contraluz"]["rgb"] == [0, 255, 0]
        # sin figura recortada se quita
        ambiente.preparar = lambda *a, **k: {"foco": [0.5, 0.4]}
        c = ambiente.configurar(esc, fig, carpeta, {})
        assert "contraluz" not in c["efectos"]
    finally:
        ambiente.preparar = real
    assert "contraluz(t)" in ambiente.AMBIENTE_JS


def main():
    ver = sys.argv[sys.argv.index("--ver") + 1] if "--ver" in sys.argv else None
    probar_eleccion()
    with tempfile.TemporaryDirectory() as d:
        carpeta = ver or d
        os.makedirs(carpeta, exist_ok=True)
        fig = probar_silueta(carpeta)
        probar_configurar(carpeta, fig)
    print("prueba_contraluz: OK")


if __name__ == "__main__":
    main()
