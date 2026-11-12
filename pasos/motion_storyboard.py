"""
EL STORYBOARD DEL MOTION, escrito por Claude (punto G, segunda parte).

Lo automatico de pasos/motion.py acierta con lo que se puede MEDIR (una cita
con su referencia, años, lugares con distancia, horas, cifras), pero en el resto
de planos solo sabe poner la lamina con iconos. Aqui Claude lee el guion ENTERO
y, plano a plano, decide la pieza con intencion: metaforas visuales («PECADO»
como una bola con cadena que cae), muñecos del reparto con su gesto y su cara,
flechas y circulos que señalan, barras, antes/ahora, arbol genealogico...

    params del render  "motion": {"tema": "papel", "storyboard": "claude"}
                       (sin "storyboard": "claude", nada de esto corre)

UNA llamada por video (sonnet, esfuerzo medio: un storyboard no pide Opus, y
el modo ahorro solo puede bajarlo). Lo que devuelve se guarda POR PLANO en
`<proyecto>/motion/storyboard.json`, con la huella de su narracion: volver a
montar no vuelve a llamar, y si se cambia la frase de un plano solo se le
pregunta por ESE plano (los demas ya estan dibujados y no deben cambiar: el
viaje de camara del siguiente empieza viendo lo que dejo el anterior).
Si Claude falla o no esta, el video sale con lo automatico y lo dice el
registro: nunca se para un montaje por esto.
"""
import hashlib
import json
import os
import re

VERSION = 1
MODELO, ESFUERZO = "sonnet", "medium"
MAX_PIEZAS = 4


def pedido(p):
    v = (p or {}).get("motion")
    return isinstance(v, dict) and v.get("storyboard") == "claude"


def huella(escena):
    base = json.dumps([VERSION, escena.get("narracion") or "",
                       list(escena.get("personajes") or [])], ensure_ascii=False)
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def ruta_cache(raiz):
    return os.path.join(raiz, "motion", "storyboard.json")


def _leer(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def _escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ruta)


CATALOGO = """PIEZAS (coordenadas en FRACCIONES del cuadro: x 0=izquierda 1=derecha, y 0=arriba 1=abajo;
`en` = la palabra EXACTA de la narración en la que entra; `entra` = abajo|arriba|izquierda|derecha|pop):
- {"tipo":"auto"}  la pieza que el estudio ya calcula sola para ese plano (te la digo en cada plano). ÚSALA
  siempre que sea versiculo, mapa, linea, reloj, comparacion, lista, contador, barras, antes o arbol:
  llevan la cita literal, las distancias y los años reales. Puedes añadirle UN acento (flecha, circulo,
  icono o personajes pequeños) que no tape.
- {"tipo":"texto","texto":"El *PECADO* pesa","x":.5,"y":.25,"en":"pecado","entra":"pop"}  *palabra* = en color.
  Máximo 4 palabras: es un rótulo, no una frase.
- {"tipo":"icono","nombre":"bola","x":.5,"y":.45,"tam":.32,"en":"pecado","entra":"arriba",
   "luego":[{"en":"libre","y":1.3,"rot":40}]}   `luego` = se transforma en ese momento (x, y, escala, rot,
   opacidad); con y > 1 se va del cuadro.
- {"tipo":"personajes","nombres":["Pedro"],"gesto":"senalar","expresion":"sorpresa","x":.3,"y":.66,
   "alto":.26,"mira":"derecha","en":"Pedro"}   muñecos planos del reparto; `y` = donde pisan.
   gestos: presentar, hablar (la boca sigue la voz), senalar, brazos (alabar), caminar, escuchar,
   arrodillarse (orar), saltar (alegría), asustarse, girar, pensar.
   expresiones: neutra, alegria, sorpresa, miedo, tristeza, enojo (exageradas: se ven en el móvil).
- {"tipo":"flecha","de":[.2,.6],"a":[.45,.4],"texto":"aquí","en":"mirad"}   flecha que se dibuja y señala.
- {"tipo":"circulo","x":.5,"y":.4,"w":.4,"h":.2,"texto":"¡ojo!","en":"detalle"}   lo rodea a mano.
- {"tipo":"barras","barras":[{"t":"Judíos","v":70,"en":"setenta"},{"t":"Gentiles","v":30,"en":"treinta"}],"unidad":"%"}
- {"tipo":"antes","antes":"Perseguidor","despues":"Apóstol","en":"antes","en_b":"ahora"}   cortina que barre.
- {"tipo":"arbol","nombres":["Abraham","Isaac","Jacob"]}   generaciones, de la más antigua a la más joven.
- {"tipo":"comparacion","a":"Tres reyes","b":"Unos magos","en":"reyes","en_b":"magos"}   lo falso se tacha.
- {"tipo":"lista","items":["Orar","Leer","Servir"],"en":"orar"}
- {"tipo":"contador","n":5000,"cosa":"hombres","en":"cinco"}
- {"tipo":"lamina","x":.5,"y":.37}   la imagen del plano enmarcada (solo si el plano tiene imagen).
- {"tipo":"escenario","nombre":"mar","hora":"noche","efectos":["fuego"],"mas":["antorcha"]}   el SITIO, de
  fondo, detrás de todo (ponlo PRIMERO). Úsalo con personajes cuando el plano no tiene imagen.
  nombre (sitio ya montado): mar, desierto, ciudad, torre, templo, trono, monte, campo, cueva, carcel,
  establo, rio. "mas" le SUMA cosas. O ármalo TÚ pieza a pieza según lo que cuente el guion:
  {"tipo":"escenario","fondo":"tierra","hora":"atardecer","cosas":[{"cosa":"cruz","x":.5,"tam":1.2},
   {"cosa":"cruz","x":.2},{"cosa":"cruz","x":.8},"roca"]}   (el Gólgota: TRES cruces)
  fondos: hierba, tierra, arena, mar, rio (exteriores); sala, cueva, celda, establo (interiores).
  cosas: palmera, olivo, tienda, roca, barca (flota si hay agua), pozo, oveja, burro, juncos, cruz, mesa,
  altar, antorcha, farol, pesebre, paja, rejas, cadenas; grandes (ocupan el fondo, van centradas):
  muralla, zigurat, santuario, cumbre, columnas, cortinas, alfombra, trono. Cada cosa: texto o
  {"cosa","x" 0-1 del cuadro,"tam" veces su tamaño (1 = normal),"dy" sube(-)/baja(+)}; sin x se colocan
  solas a los lados (el centro es de los personajes). Máximo 10. hora: dia, atardecer, noche;
  efectos (opcional): fuego, humo, luz (el fuego va encima del altar si lo hay).
ICONOS: {iconos}"""


def instruccion(escenas, autos, faltan, reparto, vertical, tema, iconos):
    zona = ("vertical 9:16: el subtítulo vive abajo, deja libre y > 0.72; el centro útil es x .5, y .37"
            if vertical else
            "horizontal 16:9: el subtítulo vive abajo, deja libre y > 0.8; el centro útil es x .5, y .42")
    lineas = []
    for e in escenas:
        dur = float(e.get("t_out") or 0) - float(e.get("t_in") or 0)
        marca = "  <- ESCRIBE ESTE" if e.get("id") in faltan else ""
        pj = ", ".join(e.get("personajes") or []) or "nadie"
        lineas.append(f"{e.get('id')} ({dur:.1f} s; personajes: {pj}; automático: "
                      f"{autos.get(e.get('id')) or 'lámina'}){marca}\n  «{e.get('narracion') or ''}»")
    reparto_txt = "\n".join(f"- {n}: {d[:140]}" for n, d in reparto.items()) or "- (sin reparto)"
    return f"""Eres el director de MOTION GRAPHICS de un canal de vídeos animados narrados (temas
bíblicos e historia, en español). El vídeo es UN SOLO MUNDO dibujado en vectores por el que viaja
la cámara sin cortes; cada plano es una parada y sus piezas ENTRAN con rebote cuando la voz dice su
palabra. Tema visual: {tema}. Formato {zona}.

Tu trabajo: el STORYBOARD de cada plano marcado con «ESCRIBE ESTE», pensado para RETENER:
1. Algo nuevo entra cada 2-3 segundos (un plano de 6 s pide 2-3 entradas escalonadas por palabras).
2. METÁFORAS VISUALES sorprendentes cuando la frase es abstracta: el pecado = una bola con cadena que
   cae pesada; la duda = un signo de pregunta que crece; la fe = una semilla; la salvación = el
   candado que se abre (icono que «luego» sale volando). Un rótulo de 1-4 palabras con la clave.
3. Los PERSONAJES del plano como muñecos con el gesto y la cara que pide la frase (si alguien habla,
   gesto «hablar»; si ora, «arrodillarse»; si se asusta, «asustarse» con cara de miedo). No los
   pongas en planos donde no están.
4. Si el automático ya explica (versículo, mapa, línea, reloj, barras…), usa {{"tipo":"auto"}} y como
   mucho un acento. No inventes citas, cifras, años ni distancias: solo lo que dice la narración.
5. Que no se tapen: reparte en el cuadro, como mucho {MAX_PIEZAS} piezas por plano.

{CATALOGO.replace("{iconos}", iconos)}

REPARTO (para «personajes», usa estos nombres tal cual):
{reparto_txt}

EL GUION ENTERO (para que entiendas la historia):
{chr(10).join(lineas)}

Responde SOLO con un objeto JSON, sin texto alrededor, con una clave por plano marcado:
{{"S001": [ {{pieza}}, ... ], "S002": [ ... ]}}"""


def leer_respuesta(texto):
    """El JSON de Claude -> {sid: [piezas]}; tolera ```json y texto alrededor."""
    texto = str(texto or "")
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", texto, re.S)
    crudo = m.group(1) if m else texto[texto.find("{"):texto.rfind("}") + 1]
    # lo que un modelo escribe y JSON no admite: «.5» y comas antes de cerrar
    crudo = re.sub(r"(?<=[:\[,\s-])\.(\d)", r"0.\1", crudo)
    crudo = re.sub(r",\s*([\]}])", r"\1", crudo)
    try:
        datos = json.loads(crudo)
    except ValueError:
        return {}
    if not isinstance(datos, dict):
        return {}
    salida = {}
    for sid, piezas in datos.items():
        if isinstance(piezas, dict) and isinstance(piezas.get("piezas"), list):
            piezas = piezas["piezas"]
        if isinstance(piezas, list):
            limpias = [q for q in piezas if isinstance(q, dict) and q.get("tipo")][:MAX_PIEZAS + 2]
            if limpias:
                salida[str(sid)] = limpias
    return salida


def obtener(raiz, escenas, ancho, alto, fichas=None, avisar=None, tema="papel",
            autos=None, iconos=(), ejecutar=None):
    """{sid: [piezas]} para todos los planos que tengan storyboard de Claude.

    Pregunta SOLO por los planos que no estan en la cache con su huella.
    `ejecutar(instruccion) -> texto` se puede cambiar (las pruebas lo doblan);
    por defecto es el CLI de Claude.
    """
    ruta = ruta_cache(raiz)
    cache = _leer(ruta)
    planos = cache.get("planos") if isinstance(cache.get("planos"), dict) else {}
    faltan = [e.get("id") for e in escenas
              if (planos.get(e.get("id")) or {}).get("huella") != huella(e)]
    if faltan and os.environ.get("ESTUDIO_STORYBOARD", "").lower() not in ("no", "0", "off"):
        if avisar:
            try:
                avisar(0.02, f"Claude escribe el storyboard ({len(faltan)} planos)")
            except Exception:                                   # noqa: BLE001
                pass
        texto_instr = instruccion(escenas, autos or {}, set(faltan), fichas or {},
                                  float(alto) > float(ancho), tema, ", ".join(iconos))
        try:
            if ejecutar is None:
                try:
                    import cli_claude                          # noqa: PLC0415
                except ImportError:
                    from . import cli_claude                   # noqa: PLC0415
                texto, _ = cli_claude.ejecutar(
                    texto_instr, modelo=MODELO, esfuerzo=ESFUERZO, tiempo_max_s=420,
                    base_tiempo_s=240, para="el storyboard del motion")
            else:
                texto = ejecutar(texto_instr)
            nuevos = leer_respuesta(texto)
            por_id = {e.get("id"): e for e in escenas}
            for sid in faltan:
                # el que no escribio se apunta como «automatico» (piezas None):
                # si no, cada montaje volveria a preguntar por el
                planos[sid] = {"huella": huella(por_id[sid]), "piezas": nuevos.get(sid)}
            cache = {"version": VERSION, "planos": planos}
            _escribir(ruta, cache)
            print(f"[render] storyboard de Claude: {len([s for s in faltan if s in nuevos])}"
                  f"/{len(faltan)} planos escritos", flush=True)
        except Exception as e:                                  # noqa: BLE001
            print(f"[render] storyboard de Claude no disponible ({str(e)[:200]}); "
                  "sale lo automatico", flush=True)
    salida = {}
    for e in escenas:
        fila = planos.get(e.get("id")) or {}
        if fila.get("huella") == huella(e) and isinstance(fila.get("piezas"), list):
            salida[e.get("id")] = fila["piezas"]
    return salida
