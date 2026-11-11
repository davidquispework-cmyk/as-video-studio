"""El botón «Arreglar el guion»: de los avisos sale la corrección pedida.

Lo que se protege: un guion largo pide recortarse a la horquilla con la cuenta
hecha; las pausas de más se piden quitar y, si el modelo no lo hace, se quitan
a mano dejando el tope; y un guion bien no ofrece el botón. Sin red ni CLI.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import app  # noqa: E402

fallos = []


def comprobar(titulo, condicion, detalle=""):
    print(f"  {'ok ' if condicion else 'MAL'}  {titulo} {detalle if not condicion else ''}")
    if not condicion:
        fallos.append(titulo)


PAUSA = '<break time="600ms"/>'
doc = {"palabras_minimo": 20, "palabras_maximo": 40, "presupuesto_palabras": 30,
       "idioma": "es"}
largo = [{"id": f"B00{i}", "texto": "palabra " * 12 + PAUSA + " fin."} for i in range(1, 5)]
avisos, pedir = app._que_arreglar(doc, largo)
comprobar("un guion largo pide recortar con la cuenta hecha",
          any("no puede pasar de 40" in p and "unas 30" in p for p in pedir), pedir)
comprobar("y las pausas de más (4 para 4 bloques, tope 2)",
          any("como mucho puede haber 2" in p for p in pedir), pedir)
comprobar("los avisos de ahora salen", any("por encima del maximo" in a for a in avisos), avisos)
limpios = app._quitar_silencios_de_mas(largo)
comprobar("las pausas que sobran se quitan a mano, dejando el tope",
          app._silencios(limpios) == 2 and limpios[3]["texto"].count("break") == 0,
          limpios)
bien = [{"id": "B001", "texto": "palabra " * 15}, {"id": "B002", "texto": "palabra " * 15}]
comprobar("un guion bien no ofrece el botón", app._que_arreglar(doc, bien)[1] == [])

print()
if fallos:
    print(f"FALLARON {len(fallos)}: " + ", ".join(fallos))
    raise SystemExit(1)
print("ARREGLAR GUION OK")
