"""
Prueba del modo de imagen MANUAL: las imagenes las sube una persona.

Monta un proyecto de verdad con el material fabricado de
`prueba_pasos_visuales` (locucion con marcas, catalogo, cartelas) y recorre el
camino entero del paso de imagenes sin llamar a ningun generador:

  1. las piezas sueltas de `subidas`: a que plano va cada nombre de fichero, el
     recorte al tamano del plano, que un id raro no se salga de la carpeta, y
     el reparto de un .zip;
  2. sin ninguna imagen subida, la tanda se para diciendo TODAS las que faltan
     (y solo las que llevan imagen: ni la cartela sobre negro ni la segunda
     mitad de un plano largo);
  3. con la mitad subida, faltan exactamente las otras;
  4. con todas, el paso termina, cada plano lleva SU imagen byte a byte, el
     coste es cero y se versiona;
  5. cambiar una imagen ya colocada la recoloca en la pasada siguiente sin
     tocar las demas;
  6. el prompt para copiar existe para cada plano y no habla de adjuntos.

    python pasos/prueba_subidas.py
"""
import io
import os
import shutil
import sys
import tempfile
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "pasos"))

CARPETA = os.path.join(tempfile.gettempdir(), "estudio_prueba_subidas")
if os.path.isdir(CARPETA):
    shutil.rmtree(CARPETA)
os.makedirs(CARPETA)
# lo que toca esta suite va a temporal: ni los ajustes ni el historico de
# tiempos de verdad
os.environ["ESTUDIO_AJUSTES"] = os.path.join(CARPETA, "ajustes.json")
os.environ["ESTUDIO_ESTADISTICAS"] = os.path.join(CARPETA, "estadisticas.json")

from PIL import Image  # noqa: E402

import ajustes  # noqa: E402
import cartelas  # noqa: E402
import medios  # noqa: E402
import p6_assets  # noqa: E402
import prueba_pasos_visuales as visual  # noqa: E402
import subidas  # noqa: E402

# el material de la suite visual, pero en NUESTRA carpeta
visual.CARPETA = os.path.join(CARPETA, "proyecto")
visual.BANCO_PRUEBA = os.path.join(CARPETA, "_banco")

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


def _png(ancho, alto, color):
    salida = io.BytesIO()
    Image.new("RGB", (ancho, alto), color).save(salida, "PNG")
    return salida.getvalue()


def _jpg(ancho, alto, color):
    salida = io.BytesIO()
    Image.new("RGB", (ancho, alto), color).save(salida, "JPEG")
    return salida.getvalue()


def probar_piezas():
    print("\n  LAS PIEZAS DE subidas")
    for nombre, esperado in (("S007.png", "S007"), ("s7.jpg", "S007"),
                             ("S007_mercado.webp", "S007"), ("007.png", "S007"),
                             ("plano 12.png", "S012"), ("7.jpg", "S007"),
                             ("S0123.png", "S123"), ("foto.png", None),
                             ("0.png", None), ("IMG_2024.jpg", None)):
        igual(subidas.id_desde_nombre(nombre), esperado, f"«{nombre}» va a {esperado}")
    for malo in ("../S001", "S1", "S001/../../x", "", "X001"):
        try:
            subidas.validar_id(malo)
            ok(False, f"«{malo}» deberia rechazarse como id de plano")
        except ValueError:
            ok(True, f"«{malo}» se rechaza como id de plano")

    png = subidas.normalizar(_jpg(800, 800, (10, 200, 30)), "apaisado")
    imagen = Image.open(io.BytesIO(png))
    igual(imagen.size, (1536, 1024), "una cuadrada se recorta al plano apaisado")
    igual(imagen.format, "PNG", "y se guarda como PNG")
    igual(Image.open(io.BytesIO(subidas.normalizar(_png(3000, 1000, (1, 2, 3)),
                                                   "vertical"))).size,
          (1024, 1536), "una muy ancha se recorta al plano vertical")
    try:
        subidas.normalizar(b"esto no es una imagen")
        ok(False, "un fichero que no es imagen deberia rechazarse")
    except ValueError:
        ok(True, "un fichero que no es imagen se rechaza con su motivo")


def probar_prompt_meta():
    escena = {"id": "S002", "personajes": ["Gabriel", "María"],
              "direccion": "el ángel Gabriel se aparece a María en su casa",
              "narracion": "Y el ángel Gabriel le dijo a María: no temas"}
    fichas = {"Gabriel": "a tall man in shining white clothes",
              "María": "a young first-century Galilean Jewish woman, blue mantle"}
    contexto = "El ángel Gabriel anunció a María en Nazaret que Jesús nacería"
    largo = subidas.prompt_para_copiar(escena, guia="acuarela suave " * 40,
                                       formato="vertical", fichas=fichas,
                                       contexto=contexto)
    meta = subidas.prompt_para_copiar(escena, guia="acuarela suave " * 40,
                                      formato="vertical", fichas=fichas,
                                      contexto=contexto, para="meta")
    ok(meta.startswith("Imagina: "), "el de Meta AI empieza por «Imagina:»")
    ok(len(meta) < len(largo) and len(meta) < 1300, f"y es corto ({len(meta)} letras)")
    ok("Gabriel" in meta and "María" in meta and "Estilo:" in meta,
       "lleva los personajes y el estilo")
    ok("sin alas" in meta and "sin aureolas" in meta and "contraluz" in meta,
       "y las reglas bíblicas esenciales")
    ok("9:16" in meta and "\n" not in meta, "en una sola línea, con su formato")
    fondo = subidas.prompt_para_copiar(escena, fichas=fichas, contexto=contexto,
                                       para="meta", munecos=True)
    ok("Personajes:" not in fondo and "Solo el fondo" in fondo,
       "con muñecos, solo el fondo")
    laico = subidas.prompt_para_copiar({"direccion": "un pan recién horneado"},
                                       para="meta")
    ok("Reglas:" not in laico, "un vídeo no bíblico no lleva reglas")


def probar_prompt_unico():
    print("\n  ETAPA 6: UN SOLO PROMPT PARA TODAS LAS IMAGENES")
    reparto = {"pedro": {"nombre": "Pedro", "papel": "el apóstol",
                         "descripcion": "40s fisherman, grey curly beard, brown tunic"},
               "juan": {"nombre": "Juan", "descripcion": "young man, no beard, blue cloak"}}
    sets = {"templo": {"descripcion": "stone temple gate", "luz": "afternoon sun"}}
    escenas = [{"id": "S001", "prompt": "Pedro y Juan suben al templo",
                "set": "templo", "personajes": ["pedro", "juan"],
                "narracion": "Pedro y Juan subían juntos al templo"},
               {"id": "S002", "prompt": "un cojo pide limosna", "set": "templo",
                "personajes": ["pedro"], "narracion": "Allí había un cojo"}]
    texto = subidas.prompt_unico(escenas, guia="acuarela suave", formato="vertical",
                                 reparto=reparto, sets=sets,
                                 contexto="Pedro y Juan en el templo de Jerusalén")
    ok("2 ilustraciones vertical (9:16)" in texto, "dice cuántas y en qué formato")
    igual(texto.count("grey curly beard"), 1, "la ficha de Pedro va UNA sola vez")
    ok("FICHAS FIJAS" in texto and "• JUAN: young man" in texto,
       "lleva la ficha fija de cada personaje que sale")
    ok("1 · S001" in texto and "2 · S002" in texto, "cada plano numerado con su código")
    ok("«sigue»" in texto, "explica cómo pedir la siguiente")
    ok(texto.index("FICHAS") < texto.index("\n1 · S001"), "las fichas van antes de los planos")
    fondo = subidas.prompt_unico(escenas, reparto=reparto, munecos=True)
    ok("FICHAS" not in fondo and "SOLO EL FONDO" in fondo,
       "con muñecos pide solo el fondo, sin fichas")
    ok("No hay planos" in subidas.prompt_unico([]), "sin planos lo dice")


def probar_zip(proyecto, validos):
    print("\n  UN .ZIP CON VARIAS")
    crudo = io.BytesIO()
    with zipfile.ZipFile(crudo, "w") as z:
        z.writestr("fotos/S001.png", _png(600, 400, (200, 10, 10)))
        z.writestr("S002_otra.jpg", _jpg(600, 400, (10, 10, 200)))
        z.writestr("notas.txt", "hola")
        z.writestr("sin_numero.png", _png(10, 10, (0, 0, 0)))
        z.writestr("S999.png", _png(10, 10, (0, 0, 0)))
        z.writestr("__MACOSX/._S001.png", b"basura")
    hecho = subidas.importar_zip(proyecto.raiz, crudo.getvalue(), validos)
    igual(hecho["guardados"], ["S001", "S002"], "cada imagen va al plano de su nombre")
    motivos = {i["fichero"]: i["motivo"] for i in hecho["ignorados"]}
    ok("notas.txt" in motivos, "lo que no es imagen se dice y no se guarda")
    ok("sin_numero.png" in motivos, "una imagen sin numero de plano se dice")
    ok("S999.png" in motivos, "un plano que no existe se dice")
    ok(not any("__MACOSX" in f for f in motivos), "la basura del Mac se ignora callada")
    # se quitan: el resto de la suite sube las suyas
    subidas.borrar(proyecto.raiz, "S001")
    subidas.borrar(proyecto.raiz, "S002")
    igual(subidas.listar(proyecto.raiz), {}, "y se pueden quitar")


def _subir(proyecto, sids, base=0):
    for indice, sid in enumerate(sids):
        subidas.guardar(proyecto.raiz, sid,
                        _png(900, 600, ((indice * 37 + base) % 255,
                                        (indice * 91 + 50) % 255, 120)))


def main():
    print("=" * 70)
    print("PRUEBA DEL MODO MANUAL (imagenes subidas, sin generador)")
    print("=" * 70)
    ajustes.guardar({"modo_imagen": "manual"})
    igual(ajustes.modo_imagen(), "manual", "el modo manual queda guardado")
    try:
        ajustes.guardar({"modo_imagen": "gemini"})
        ok(False, "un modo que no existe deberia rechazarse")
    except ValueError:
        ok(True, "un modo que no existe se rechaza")

    probar_piezas()
    probar_prompt_unico()
    probar_prompt_meta()

    # EL PROMPT PARA META AI es un ajuste leido al copiar, no un param
    ok(ajustes.leer()["prompt_para"] == "chat", "de fabrica, prompt para Gemini/ChatGPT")
    ajustes.guardar({"prompt_para": "meta"})
    ok(ajustes.prompt_para() == "meta", "se guarda el prompt para Meta AI")
    try:
        ajustes.guardar({"prompt_para": "midjourney"})
        ok(False, "un generador que no existe deberia rechazarse")
    except ValueError:
        ok(True, "un generador que no existe se rechaza")
    ajustes.guardar({"prompt_para": "chat"})

    # EL GENERADOR NO SE PUEDE LLAMAR: si alguna linea del modo manual se
    # escapara hacia OpenAI, revienta aqui con su traza en vez de salir a red
    motor = medios.motor("imagen_openai/imagen.py")

    def prohibido(*_a, **_k):
        raise AssertionError("el modo manual ha llamado al generador de imagen")
    motor.generar = prohibido

    proyecto, estado = visual.preparar_proyecto()
    params = visual.parametros(os.path.join(CARPETA, "_arte"))
    # sin modo fijado en el proyecto: manda el ajuste global, que es manual
    params.pop("motor_imagen", None)
    params["imagenes_previas"] = []
    params["estilo"] = {"prompt": "flat cartoon, thick outlines", "referencias": []}
    estado.set_params("assets", params)

    plan = p6_assets.planificar(proyecto, params)
    con_imagen = [e["id"] for e in plan["escenas"]
                  if not cartelas.sin_imagen(e) and not e.get("sigue_a")
                  and not e.get("componente")]
    ok(len(con_imagen) >= 4, f"el plan tiene planos que piden imagen ({len(con_imagen)})")
    probar_zip(proyecto, con_imagen)

    print("\n  SIN NINGUNA SUBIDA")
    try:
        p6_assets.ejecutar(proyecto, params, visual.avisador("p6"))
        ok(False, "sin imagenes la tanda deberia pararse")
    except p6_assets.FaltanImagenes as falta:
        igual(falta.sids, sorted(con_imagen), "dice TODAS las que faltan, y solo esas")
        ok("Tus imagenes" in str(falta), "y dice donde subirlas")

    fichas = p6_assets.prompts_para_subir(proyecto, params)
    igual([f["id"] for f in fichas], con_imagen,
          "la pantalla tiene un prompt por plano con imagen")
    ok(all(f["prompt"] and "reference image" not in f["prompt"] for f in fichas),
       "los prompts para copiar no hablan de imagenes adjuntas")
    ok(all(f["narracion"] and f["narracion"].split()[0] in f["prompt"]
           for f in fichas), "y llevan lo que se esta narrando")
    ok(not any(f["subida"] for f in fichas), "y ninguno figura como subido")

    print("\n  CON LA MITAD")
    mitad = con_imagen[: len(con_imagen) // 2]
    _subir(proyecto, mitad)
    try:
        p6_assets.ejecutar(proyecto, params, visual.avisador("p6"))
        ok(False, "con la mitad la tanda deberia pararse igual")
    except p6_assets.FaltanImagenes as falta:
        igual(falta.sids, sorted(set(con_imagen) - set(mitad)),
              "faltan exactamente las que no se han subido")

    print("\n  CON TODAS")
    _subir(proyecto, con_imagen[len(mitad):], base=len(mitad))
    resultado = p6_assets.ejecutar(proyecto, params, visual.avisador("p6"))
    trabajo = proyecto.ruta_trabajo("assets", crear=False)
    for sid in con_imagen:
        colocada = os.path.join(trabajo, "escenas", f"{sid}.png")
        ok(os.path.exists(colocada)
           and medios.huella_fichero(colocada)
           == medios.huella_fichero(subidas.ruta_de(proyecto.raiz, sid)),
           f"{sid} lleva SU imagen subida, byte a byte")
    origenes = {r.get("origen") for uid, r in resultado["unidades"].items()
                if uid.startswith("escena:") and uid[7:] in con_imagen}
    # las que ya se colocaron en la pasada de la mitad se conservan: su imagen
    # es la subida (lo dice la comprobacion byte a byte de arriba)
    ok(origenes <= {"subida", "conservado"} and "subida" in origenes,
       f"todas salen de lo subido, nada generado ({sorted(origenes)})")
    igual(resultado["salidas"]["coste_usd"], 0.0, "y no han costado nada")
    repartos = [r for r in resultado["unidades"].values() if r.get("tipo") == "reparto"]
    ok(all(r.get("origen") == "manual" for r in repartos),
       "las hojas de personaje no se dibujan en modo manual")
    p6_assets.propagar_dependencias(estado, resultado["dependencias"])
    version = estado.completar("assets", resultado["salidas"], resultado["unidades"])
    igual(version, 1, "el paso queda versionado")
    igual(estado.estado_de("assets"), "listo", "y listo")

    print("\n  CAMBIAR UNA YA COLOCADA")
    cambiada = con_imagen[1]
    subidas.guardar(proyecto.raiz, cambiada, _png(700, 700, (250, 250, 0)))
    otra = p6_assets.ejecutar(proyecto, params, visual.avisador("p6"))
    trabajo = proyecto.ruta_trabajo("assets", crear=False)
    igual(medios.huella_fichero(os.path.join(trabajo, "escenas", f"{cambiada}.png")),
          medios.huella_fichero(subidas.ruta_de(proyecto.raiz, cambiada)),
          "la imagen nueva se coloca sola en la pasada siguiente")
    igual(otra["unidades"][f"escena:{cambiada}"].get("origen"), "subida",
          "y figura como subida")
    quietas = [sid for sid in con_imagen if sid != cambiada
               and otra["unidades"].get(f"escena:{sid}", {}).get("origen") == "conservado"]
    igual(sorted(quietas), sorted(set(con_imagen) - {cambiada}),
          "las demas se quedan como estaban")

    print("\n  EL COSTE QUE SE ENSENA")
    import presets_light  # noqa: PLC0415
    igual(presets_light.usd_por_imagen("medium"), 0.0,
          "en modo manual una imagen cuesta cero en todas las cuentas")
    ajustes.guardar({"modo_imagen": "openai"})
    ok(presets_light.usd_por_imagen("medium") > 0,
       "y en modo OpenAI vuelve a costar lo suyo")
    ok(not p6_assets._es_manual({}), "con OpenAI puesto el paso no es manual")  # noqa: SLF001
    ok(p6_assets._es_manual({"motor_imagen": "manual"}),  # noqa: SLF001
       "salvo que el proyecto lo fije a manual")

    print()
    print("=" * 70)
    if _fallos:
        print(f"MODO MANUAL CON FALLOS: {len(_fallos)}")
        for fallo in _fallos:
            print(f"  - {fallo}")
        sys.exit(1)
    print(f"MODO MANUAL OK: {_comprobaciones[0]} comprobaciones pasan")


if __name__ == "__main__":
    main()
