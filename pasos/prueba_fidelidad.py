"""Pruebas de fidelidad (punto C): epoca, lugares, distancias y donde entra.

Lo que se protege:
  1. un video que NO es biblico no recibe ni una letra (ni en el prompt para
     copiar, ni en los encargos a Claude);
  2. uno biblico lleva la epoca (gente de Oriente Medio, ropa y sitios reales)
     y lo que NO va;
  3. «dos Belén» pide un MAPA con los dos y la distancia, y entonces el prompt
     permite los nombres del mapa;
  4. con muñecos, la gente de la epoca se quita (el fondo va sin personas);
  5. el guion biblico pide la Reina-Valera 1960.
Sin red, sin CLI, sin imagenes.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fidelidad  # noqa: E402
import marioneta  # noqa: E402
import subidas  # noqa: E402

fallos = []


def comprobar(titulo, condicion, detalle=""):
    if condicion:
        print(f"  ok   {titulo}")
    else:
        print(f"  MAL  {titulo} {detalle}")
        fallos.append(titulo)


BIBLICO = ("Jesús nació en Belén, pero ¿sabías que hay dos Belén? Los "
           "evangelios dicen que José y María subieron desde Nazaret de "
           "Galilea a Belén de Judea.")
LAICO = ("El oro ha subido un dos por ciento este año y los bancos centrales "
         "compran más que nunca en Londres y Nueva York.")

comprobar("reconoce un video biblico", fidelidad.es_biblico(BIBLICO))
comprobar("y uno que no lo es", not fidelidad.es_biblico(LAICO))
comprobar("«María» o «Juan» sueltos no hacen biblico un video",
          not fidelidad.es_biblico("María y Juan fueron al mercado."))
comprobar("epoca del siglo I", fidelidad.epocas(BIBLICO)[0] == "nt",
          fidelidad.epocas(BIBLICO))
comprobar("epoca del exodo",
          fidelidad.epocas("Moisés ante el faraón de Egipto; las plagas y el "
                           "mar Rojo")[0] == "exodo")
comprobar("epoca del exilio",
          fidelidad.epocas("Daniel en Babilonia ante Nabucodonosor")[0] == "exilio")

lugares = [n for n, _, _ in fidelidad.lugares_en(BIBLICO)]
comprobar("«dos Belén» da los dos Belén",
          "Belén de Judea" in lugares and "Belén de Galilea" in lugares, lugares)
comprobar("y Nazaret", "Nazaret" in lugares, lugares)
comprobar("«caña» no es Caná y «año» no es otra cosa",
          fidelidad.lugares_en("una caña en el año de la cosecha") == [])
km = fidelidad.distancia_km(fidelidad.lugares_en("Jerusalén")[0],
                            fidelidad.lugares_en("Belén")[0])
comprobar("Jerusalén–Belén ~ 9 km en linea recta", 7 < km < 11, km)
explica = fidelidad.explicar("¿Sabías que hay dos Belén?")
comprobar("dos Belén piden un mapa con la distancia",
          "MAPA" in explica and "km" in explica, explica)
comprobar("una escena normal no pide explicar nada",
          fidelidad.explicar("Pedro echó las redes al amanecer.") == "")

# ---- el prompt para copiar
escena = {"id": "S001", "narracion": "¿Sabías que hay dos Belén?",
          "prompt": "two villages on hills", "personajes": ["jose"]}
p = subidas.prompt_para_copiar(escena, fichas={"jose": "a man"},
                               contexto=BIBLICO)
comprobar("el prompt biblico lleva la epoca", "ÉPOCA" in p and "siglo I" in p)
comprobar("y la gente de Oriente Medio", "Oriente Medio" in p)
comprobar("y lo que no va", "NO DIBUJES" in p and "europeos" in p)
comprobar("y el mapa, con sus nombres permitidos",
          "EXPLICA LO QUE SE CUENTA" in p and "nombres de los lugares" in p)
laico = subidas.prompt_para_copiar(escena, contexto=LAICO)
comprobar("el laico no cambia", "ÉPOCA" not in laico
          and "Sin texto, sin letras" in laico
          and laico == subidas.prompt_para_copiar(escena))
fondo = marioneta.solo_fondo(p)
comprobar("con muñecos se quita la gente de la epoca",
          "PERSONAS DE LA ÉPOCA" not in fondo and "ÉPOCA" in fondo)

# ---- los encargos a Claude
cat = fidelidad.pauta_claude("Los dos Belén", BIBLICO, para="catalogo")
comprobar("el catalogo pide el reparto de la epoca",
          "REPARTO" in cat and "Reina-Valera 1960" in cat and "km" in cat)
comprobar("ninguno para un video laico",
          fidelidad.pauta_claude(LAICO) == "" and fidelidad.pauta_guion(LAICO) == "")
comprobar("el guion biblico pide la RV1960",
          "Reina-Valera 1960" in fidelidad.pauta_guion(BIBLICO))
texto = fidelidad.insertar("A\nDEVUELVE ESTE JSON:\n{}", "BLOQUE\n", "DEVUELVE")
comprobar("el bloque va antes del JSON", texto.index("BLOQUE") < texto.index("DEVUELVE"))

# --- 6. el video que mezcla dos tiempos (noviembre de 2026: David y la cruz)
MEZCLA = ("Cómo supo el rey David lo que pasaría en una cruz mil años después. "
          "David escribió el Salmo veintidós; Jesús, crucificado en el Gólgota, "
          "gritó sus primeras palabras y los soldados se repartieron su ropa.")
comprobar("David es de la Edad del Hierro",
          fidelidad.epoca_de_personaje("david", "a first-century-style man") == "reyes")
comprobar("Jesus es del siglo I", fidelidad.epoca_de_personaje("jesus") == "nt")
comprobar("el plano de David lleva SU epoca, no la del video",
          fidelidad.epoca_del_plano(MEZCLA, "Se llamaba David y escribía "
                                    "canciones a Dios en una cruz", ["david"]) == "reyes")
comprobar("el plano de la cruz lleva el siglo I",
          fidelidad.epoca_del_plano(MEZCLA, "Jesús en la cruz", ["jesus"]) == "nt")
comprobar("la ficha de David pierde el «first-century»",
          "Iron Age" in fidelidad.ficha_en_su_epoca("david", "A first-century-style man")
          and "first-century" not in fidelidad.ficha_en_su_epoca("david", "A first-century-style man"))
comprobar("la de un apostol no se toca",
          fidelidad.ficha_en_su_epoca("pedro", "a first-century man") == "a first-century man")
dav = subidas.prompt_para_copiar(
    {"prompt": "David on a rooftop with a scroll", "narracion": "Se llamaba David",
     "personajes": ["david"]},
    fichas={"david": "A first-century-style Hebrew man of about 45"}, contexto=MEZCLA)
comprobar("el prompt manual de David dice Edad del Hierro",
          "Edad del Hierro" in dav and "siglo I d. C." not in dav
          and "first-century" not in dav, dav[:300])
cruz = subidas.prompt_para_copiar(
    {"prompt": "Jesus on the cross on the bare hill", "narracion": "Jesús gritó en la cruz",
     "personajes": ["jesus"]}, contexto=MEZCLA)
comprobar("la crucifixion pide tres cruces y la cabeza erguida antes del grito",
          "TRES cruces" in cruz and "ERGUIDA" in cruz)
unico = subidas.prompt_unico([{"id": "S001", "personajes": ["david"]}],
                             contexto=MEZCLA, reparto={"david": {"descripcion": "a first-century man"}})
comprobar("el prompt unico dice que el video mezcla epocas",
          "mezcla tiempos" in unico and "first-century" not in unico)
pc = fidelidad.pauta_claude(MEZCLA, para="catalogo")
comprobar("el catalogo recibe las dos epocas y la regla de mezcla",
          "Edad del Hierro" in pc and "siglo I" in pc and "MEZCLA ÉPOCAS" in pc)

# --- 7. la cara de un momento grave no es «relajada»
import p6_assets  # noqa: E402
cara = p6_assets._cara_del_plano({"narracion": "Jesús muere en la cruz"}, {"tono": "neutro"})
comprobar("en la cruz, cara solemne y no la sonrisa del neutro",
          "No smiling" in cara and "smile" not in cara.replace("smiling", ""), cara)
comprobar("la burla con su cara dicha manda la linea",
          p6_assets._cara_del_plano({"narracion": "se burlan de él en la cruz",
                                     "direccion": "a mocking grin", "sencillo": True},
                                    {"tono": "neutro"}) == "")
comprobar("un momento normal sigue con el neutro",
          p6_assets._cara_del_plano({"narracion": "comen pan en la casa"},
                                    {"tono": "neutro"}) == p6_assets.TONOS["neutro"])

# --- 8. la accion va con SU frase aunque el corte se renumere
esc = [{"id": "S001", "narracion": "uno"}, {"id": "S002", "narracion": "Y"},
       {"id": "S003", "narracion": "dos"}, {"id": "S004", "narracion": "tres"}]
params = {"unidades": {
    "escena:S001": {"direccion": "A uno", "direccion_de": "uno"},
    "escena:S002": {"direccion": "A dos", "direccion_de": "dos"},
    "escena:S003": {"direccion": "A tres", "direccion_de": "tres"},
    "escena:S004": {"redactado": "P viejo", "redactado_de": "cuatro"}}}
dirigido = p6_assets._lo_dirigido(params, esc)
comprobar("tras renumerar, cada accion vuelve a su frase",
          (dirigido.get("S001") or {}).get("direccion") == "A uno"
          and (dirigido.get("S003") or {}).get("direccion") == "A dos"
          and (dirigido.get("S004") or {}).get("direccion") == "A tres", dirigido)
comprobar("el plano nuevo («Y») queda sin dirigir, no con la accion de otro",
          "S002" not in dirigido, dirigido)
comprobar("un redactado sellado para otra frase no se usa",
          "redactado" not in (dirigido.get("S004") or {}), dirigido)
viejo = p6_assets._lo_dirigido({"unidades": {"escena:S001": {"direccion": "sin sello"}}}, esc)
comprobar("lo guardado sin sello se lee como siempre (no mueve firmas)",
          (viejo.get("S001") or {}).get("direccion") == "sin sello")

print()
if fallos:
    print(f"FALLARON {len(fallos)} comprobaciones:")
    for f in fallos:
        print(f"  - {f}")
    raise SystemExit(1)
print("FIDELIDAD OK: todo en orden")
