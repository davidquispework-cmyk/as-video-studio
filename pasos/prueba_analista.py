"""Prueba corta del analista (pestaña Análisis / Ideas). Sin red y sin Claude.

    python pasos/prueba_analista.py

Mide un nicho de mentira, importa un CSV de YouTube Studio, guarda vídeos a
mano y pide ideas en modo simulado. Todo en una carpeta temporal: no toca el
analisis.json ni las claves de verdad.
"""
import json
import os
import sys
import tempfile
import time

CARPETA = tempfile.mkdtemp(prefix="prueba_analista_")
os.environ["ESTUDIO_ANALISIS"] = os.path.join(CARPETA, "analisis.json")
os.environ["ESTUDIO_SECRETOS"] = os.path.join(CARPETA, "secretos")
os.environ["ESTUDIO_AJUSTES"] = os.path.join(CARPETA, "ajustes.json")
os.environ["ESTUDIO_SIMULAR"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import analista  # noqa: E402

FALLOS = []


def comprobar(cond, texto):
    print(("ok    " if cond else "FALLA ") + texto)
    if not cond:
        FALLOS.append(texto)


comprobar(analista.segundos_iso("PT1M5S") == 65, "duración ISO 8601")
comprobar(analista._numero("12,5k") == 12500 and analista._numero("1.2M") == 1200000
          and analista._numero("3.400") == 3400, "cifras con k / M / puntos")
comprobar(analista._segundos("1:05") == 65, "duración mm:ss")

# un nicho de mentira: los cortos con pregunta crecen más
videos = []
for n in range(16):
    corto = n < 8
    videos.append({"id": f"v{n}", "titulo": ("¿Sabías esto de Pablo? 3 datos" if corto
                                             else f"Historia completa de Moisés parte {n}"),
                   "canal": "c", "vistas": 1000 * (20 - n), "duracion_s": 70 if corto else 600,
                   "vistas_dia": (300 if corto else 40) - n, "interaccion": 0.05,
                   "hora": 18, "dia": 4, "url": "u"})
r = analista.resumir_nicho(videos)
comprobar(r["total"] == 16 and r["consejos"], "el nicho da consejos")
comprobar(any("1:01-1:30" in c for c in r["consejos"]), "detecta la duración que más crece")
comprobar(any("pregunta" in c for c in r["consejos"]), "detecta los títulos en pregunta")

# mis vídeos: a mano y por CSV de YouTube Studio
analista.guardar_mio({"titulo": "¿Quién era Bernabé?", "plataforma": "tiktok", "vistas": "2,1k",
                      "duracion_s": "1:10", "retencion_pct": "64", "abandono_s": "9"})
csv = ("Contenido,Título del vídeo,Visualizaciones,Duración media de las visualizaciones,"
       "Porcentaje medio visualizado (%),Duración\n"
       "Total,,5000,0:00:40,55,\n"
       "abcdefghijk,El viaje de Pablo a Roma,3000,0:00:45,58.5,80\n")
res = analista.importar_csv(csv)
d = analista.leer()
comprobar(res["anadidos"] == 1 and len(d["mios"]) == 2, "CSV de YouTube Studio importado (sin la fila Total)")
pablo = next(m for m in d["mios"] if m.get("video_id") == "abcdefghijk")
comprobar(pablo["vista_media_s"] == 45 and pablo["retencion_pct"] == 58.5, "retención del CSV")
rm = analista.resumir_mios(d["mios"])
comprobar(rm["retencion_media"] and rm["abandono_medio_s"] == 9, "resumen de mis vídeos")

# las ideas: extraer de una respuesta y pedirlas en simulado
ideas = analista.extraer_ideas('Aquí van:\n[{"titulo": "¿Sabías que Pablo naufragó 3 veces?", '
                               '"gancho": "Naufragó tres veces", "duracion_s": "80", '
                               '"formato": "vertical", "dibujo": "muñecos", "hashtags": "biblia pablo"}]')
comprobar(ideas[0]["dibujo"] == "munecos" and ideas[0]["duracion_s"] == 80
          and ideas[0]["hashtags"] == ["#biblia", "#pablo"], "ideas normalizadas")
texto = analista.instruccion_ideas(analista.leer(), "Pablo", 3, "vertical")
comprobar("JSON" in texto and "Bernabé" in texto, "el encargo a Claude lleva mis vídeos")
analista.pedir_ideas("Pablo", 3)
for _ in range(50):
    if analista.trabajo()["estado"] != "pensando":
        break
    time.sleep(0.1)
f = analista.ficha()
comprobar(f["trabajo"]["estado"] == "hecho" and len(f["ideas"]) == 3, "ideas simuladas guardadas")
analista.marcar_idea(f["ideas"][0]["id"], "usada")
comprobar(analista.leer()["ideas"][0]["estado"] == "usada", "marcar idea como usada")
comprobar("clave" not in json.dumps(f).lower() or not f["tiene_clave_youtube"], "la ficha no lleva claves")
try:
    analista.buscar_nicho(forzar=True)
    comprobar(False, "sin clave de YouTube avisa")
except analista.ErrorAnalista as e:
    comprobar("clave de YouTube" in str(e), "sin clave de YouTube avisa")

print("\n" + ("TODO BIEN" if not FALLOS else f"{len(FALLOS)} FALLOS"))
sys.exit(1 if FALLOS else 0)
