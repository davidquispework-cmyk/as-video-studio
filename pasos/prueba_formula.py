"""Prueba de la formula de las referencias (P8): `pasos/formula.py`.

Sin red ni Claude: comprueba la pauta y que entra en el encargo del guion.
    python pasos/prueba_formula.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formula  # noqa: E402

fallos = []


def comprobar(cond, que):
    print(("ok   " if cond else "FALLO ") + que)
    if not cond:
        fallos.append(que)


os.environ.pop("ESTUDIO_FORMULA", None)
p = formula.pauta_guion(corto=True, biblico=True, encargo="Abimelec")
comprobar("GANCHO" in p and "CERRAR EL CÍRCULO" in p, "gancho y círculo")
comprobar("ESPEJO CON JESÚS" in p, "espejo con Jesús en bíblico")
comprobar("RETO DE ESTA SEMANA" in p, "reto de la semana en bíblico")
comprobar("55 y 110" in p, "duración en corto")
comprobar("PARTE" not in p, "sin serie si no se pide")

p = formula.pauta_guion(biblico=False, encargo="la historia del cafe")
comprobar("ESPEJO" not in p and "RETO" not in p, "sin espejo ni reto fuera de lo bíblico")
comprobar("55 y 110" not in p, "sin duración corta en vídeo largo")

p = formula.pauta_guion(biblico=True, encargo="sin reto, por favor")
comprobar("RETO" not in p, "«sin reto» lo quita")

p = formula.pauta_guion(biblico=True, con_cta_final=True)
comprobar("no añadas otra" in p and "RETO" not in p, "con cta_final no pide otra cosa")

comprobar(formula.serie_de("Parte 3 de la serie: Los jueces") ==
          {"parte": 3, "nombre": "los jueces"}, "serie con número y nombre")
comprobar(formula.serie_de("episodio dos")["parte"] == 2, "número en letra")
comprobar(formula.serie_de("Jueces capítulo 9, una serie de milagros") is None,
          "capítulo bíblico y «una serie de» no son serie")
p = formula.pauta_guion(encargo="parte 4")
comprobar("PARTE 4" in p, "la serie entra en la pauta")

os.environ["ESTUDIO_FORMULA"] = "no"
comprobar(formula.pauta_guion(biblico=True) == "", "ESTUDIO_FORMULA=no la apaga")
os.environ.pop("ESTUDIO_FORMULA")

# entra en el encargo del guion (sin llamar a Claude)
import p3_guion  # noqa: E402
opciones = p3_guion._normalizar({"prompt_general": "Parte 2 de la serie: Jueces"},
                                estricto=False)
brief = {"titulo": "Abimelec, el rey que mató a sus hermanos",
         "resumen": "Jueces 9, la Biblia", "palabras_objetivo": 200}
try:
    texto = p3_guion._instruccion([{"texto": "Abimelec en la Biblia"}], {},
                                  brief, None, opciones, [], "es")
    comprobar("LA FÓRMULA" in texto and "PARTE 2" in texto,
              "la pauta va en el encargo del guion")
except Exception as e:  # noqa: BLE001
    comprobar(False, f"_instruccion lanzó {e!r}")

print("\nTODO BIEN" if not fallos else f"\n{len(fallos)} FALLO(S)")
sys.exit(1 if fallos else 0)
