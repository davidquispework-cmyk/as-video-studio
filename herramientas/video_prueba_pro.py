"""Vídeo de prueba del plan NIVEL PROFESIONAL (P1-P8) con un guion real.

Fabrica un proyecto aparte (no toca los de verdad ni los ajustes), locuta el
guion con la voz GRATUITA (Edge, Brian Multilingual +5 %), pone en cada plano
una lámina dibujada aquí (sin pagar imágenes: modo «adoptar») y renderiza el
mismo vídeo con los tres looks del plan:

  A  vectorial  rótulos P1 + pantalla partida P2 + contraluz P4 + muñecos con
                boca P7 (y ambiente, gancho, subtítulos)
  B  editorial  P5: titular con serifa y cuadro clásico (si hay internet)
  C  biblia3d   P6/P6b: la Biblia de plastilina en la mesa con objetos

y deja, junto a los MP4, una hoja de contactos por look para ponerla al lado
de la referencia. P8 (la fórmula del guion) es el propio texto.

    python herramientas/video_prueba_pro.py [carpeta] [--looks A,B,C]
            [--fps 15] [--ancho 540]

Gasta 0 €: ni Claude, ni OpenAI, ni Cartesia. Sin internet la voz cae a una
locución simulada (marcas estimadas y un tono) y el vídeo sale igual.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "pasos"))

TITULO = "¿Los ángeles conocen tu nombre?"
VOZ = "en-US-BrianMultilingualNeural"

GUION = [
    ("B001", "¿Los ángeles conocen tu nombre? La Biblia da pistas. Mira cuatro "
             "veces en que un ángel llama a alguien por su nombre."),
    ("B002", "Primera. Zacarías, un sacerdote, está en el templo, junto al altar "
             "del incienso. Un ángel le dice, en Lucas, capítulo uno, versículo "
             "trece: «Zacarías, no temas». Es Gabriel, y sabe cómo se llama."),
    ("B003", "Segunda. María recibe la visita del mismo Gabriel. Él le dice, en "
             "Lucas, capítulo uno, versículo treinta: «María, no temas». Otra vez, "
             "primero el nombre."),
    ("B004", "Tercera. Daniel recibe la visita de un varón vestido de lino. Le "
             "dice, en Daniel, capítulo diez, versículo once: «Daniel, varón muy "
             "amado». El texto no dice quién es él."),
    ("B005", "Cuarta. Abraham, en el monte. Desde el cielo, el ángel de Jehová lo "
             "llama, en Génesis, capítulo veintidós, versículo once: «Abraham, "
             "Abraham». Muchos creen que era Dios mismo."),
    ("B006", "Pero ¿saben todos los ángeles el nombre de todos? La Biblia no dice "
             "eso. Tampoco dice que tengas un ángel que sepa el tuyo. Dice que "
             "Dios los envió. Gabriel lo aclara en Lucas uno, diecinueve."),
    ("B007", "Quien lo sabe con certeza es Dios. El Salmo ciento cuarenta y siete, "
             "versículo cuatro, habla de las estrellas: «A todas ellas llama por "
             "sus nombres». Si lo hace con cada estrella, ¿no va a saber el tuyo?"),
    ("B008", "Y en Isaías, capítulo cuarenta y tres, versículo uno, Dios le dice a "
             "su pueblo Israel: «te puse nombre, mío eres tú»."),
    ("B009", "Lee Lucas capítulo uno tú mismo y cuéntame qué te llamó la atención. "
             "Sígueme para la parte dos: ¿tienes un ángel de la guarda?"),
]

EMOCIONES = {"B007": "sereno", "B008": "sereno", "B009": "alegre"}

CATALOGO = {
    "luz_por_defecto": "warm golden light",
    "prompt_por_defecto": "biblical scene, flat illustration",
    "sets": {
        "templo": {"palabras": {"templo": 2, "altar": 2, "incienso": 2,
                                "sacerdote": 1.5},
                   "luz": "warm lamp light", "prompt": "temple interior"},
        "monte": {"palabras": {"monte": 2, "cielo": 1}, "luz": "dawn",
                  "prompt": "a mountain at dawn"},
        "noche": {"palabras": {"estrellas": 2, "estrella": 2}, "luz": "night",
                  "prompt": "starry night sky"},
    },
    "reparto": {
        nombre: {"palabras": [nombre.lower()], "descripcion": desc}
        for nombre, desc in (
            ("Zacarías", "old priest with white beard and linen robe"),
            ("María", "young woman with blue veil"),
            ("Gabriel", "angel in white robe with golden light"),
            ("Daniel", "man in brown robe"),
            ("Abraham", "old man with grey beard and staff"),
        )
    },
}

#: Paleta de cada lámina por palabras (fondo de arriba, de abajo, figura).
TONOS = (
    (("templo", "altar", "incienso"), ((70, 40, 20), (190, 120, 50), (25, 15, 10))),
    (("estrellas", "estrella", "noche"), ((10, 15, 50), (40, 50, 110), (5, 5, 20))),
    (("monte", "cielo"), ((250, 170, 90), (120, 60, 70), (30, 15, 20))),
    (("maría", "gabriel"), ((230, 220, 200), (150, 170, 210), (40, 40, 70))),
)

LOOKS = {
    "A": ("vectorial", {"rotulos": True, "partida": True, "marioneta": True,
                        "contraluz": "dorado", "ambiente": "auto"}),
    "B": ("editorial", {"editorial": True, "rotulos": True}),
    "C": ("biblia3d", {"biblia3d": True, "rotulos": True}),
}


def _entorno(carpeta):
    """Todo lo que el estudio escribiría fuera, a la carpeta de la prueba."""
    os.makedirs(carpeta, exist_ok=True)
    import json
    ajustes = os.path.join(carpeta, "ajustes.json")
    with open(ajustes, "w", encoding="utf-8") as fh:
        json.dump({"modo_voz": "gratis", "modo_imagen": "openai",
                   "modo_claude": "ahorro"}, fh)
    os.environ.update({
        "ESTUDIO_AJUSTES": ajustes,
        "ESTUDIO_MODO_VOZ": "gratis",
        "ESTUDIO_SECRETOS": os.path.join(carpeta, "_secretos"),
        "ESTUDIO_ESTADISTICAS": os.path.join(carpeta, "estadisticas.json"),
        "ESTUDIO_FORMULA": "si",
    })
    # SIN LAS FUENTES DE WINDOWS (un Linux sin ttf-mscorefonts): una carpeta
    # con DejaVu bajo los nombres que pide `tipografia`. Mide y pinta con otra
    # letra, pero el vídeo sale; en el VPS el instalador ya pone las de verdad.
    if not os.environ.get("ESTUDIO_FUENTES") and not os.path.exists(r"C:\Windows\Fonts") \
            and not os.path.exists("/usr/share/fonts/truetype/msttcorefonts/verdana.ttf"):
        sustitutas = os.path.join(carpeta, "_fuentes")
        os.makedirs(sustitutas, exist_ok=True)
        dv = "/usr/share/fonts/truetype/dejavu/"
        for n in ("verdana", "arial", "tahoma", "consola", "segoeui"):
            for suf, origen in (("", "DejaVuSans.ttf"), ("b", "DejaVuSans-Bold.ttf"),
                                ("bd", "DejaVuSans-Bold.ttf")):
                destino = os.path.join(sustitutas, f"{n}{suf}.ttf")
                if os.path.exists(dv + origen) and not os.path.exists(destino):
                    os.symlink(dv + origen, destino)
        for suf, origen in (("", "DejaVuSerif.ttf"), ("b", "DejaVuSerif-Bold.ttf")):
            destino = os.path.join(sustitutas, f"georgia{suf}.ttf")
            if os.path.exists(dv + origen) and not os.path.exists(destino):
                os.symlink(dv + origen, destino)
        os.environ["ESTUDIO_FUENTES"] = sustitutas
    elif os.path.exists("/usr/share/fonts/truetype/msttcorefonts/verdana.ttf"):
        os.environ.setdefault("ESTUDIO_FUENTES", "/usr/share/fonts/truetype/msttcorefonts")
    # DETRÁS DE UN PROXY CON SU PROPIA CA (un contenedor en la nube), edge-tts
    # solo se fía de certifi: se le da la CA del sistema que diga SSL_CERT_FILE.
    if os.environ.get("SSL_CERT_FILE"):
        try:
            import certifi
            certifi.where = lambda: os.environ["SSL_CERT_FILE"]
        except ImportError:
            pass
    if not os.environ.get("ESTUDIO_EDGE"):
        for ruta in ("/opt/pw-browsers/chromium/chrome-linux/chrome",
                     "/opt/pw-browsers/chromium-1243/chrome-linux64/chrome",
                     "/usr/bin/chromium"):
            if os.path.exists(ruta):
                os.environ["ESTUDIO_EDGE"] = ruta
                break
        # COMO ROOT (un contenedor), Chromium no arranca sin --no-sandbox; el
        # estudio no lo pone porque en el VPS corre como su propio usuario.
        if os.environ.get("ESTUDIO_EDGE") and hasattr(os, "geteuid") and os.geteuid() == 0:
            envoltorio = os.path.join(carpeta, "_chrome.sh")
            with open(envoltorio, "w", encoding="utf-8") as fh:
                fh.write(f'#!/bin/sh\nexec "{os.environ["ESTUDIO_EDGE"]}" --no-sandbox "$@"\n')
            os.chmod(envoltorio, 0o755)
            os.environ["ESTUDIO_EDGE"] = envoltorio


def _lamina(destino, texto, k, ancho, alto):
    """Una lámina digna de mirar: degradado, sol/halo y una silueta con túnica."""
    from PIL import Image, ImageDraw, ImageFilter
    t = texto.lower()
    arriba, abajo, figura = (90, 120, 170), (220, 190, 140), (30, 25, 35)
    for palabras, tonos in TONOS:
        if any(p in t for p in palabras):
            arriba, abajo, figura = tonos
            break
    im = Image.new("RGB", (ancho, alto))
    d = ImageDraw.Draw(im)
    for y in range(alto):
        f = y / alto
        d.line([(0, y), (ancho, y)], fill=tuple(
            int(a + (b - a) * f) for a, b in zip(arriba, abajo)))
    halo = Image.new("L", (ancho, alto), 0)
    hd = ImageDraw.Draw(halo)
    cx, cy, r = ancho * (0.35 + 0.1 * (k % 3)), alto * 0.33, ancho * 0.18
    hd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=200)
    halo = halo.filter(ImageFilter.GaussianBlur(ancho * 0.05))
    im.paste((255, 235, 180), (0, 0), halo)
    d = ImageDraw.Draw(im)
    # suelo
    d.polygon([(0, alto * 0.78), (ancho * 0.5, alto * 0.72), (ancho, alto * 0.8),
               (ancho, alto), (0, alto)], fill=tuple(max(0, c - 30) for c in abajo))
    # una o dos figuras con túnica (alas si es un ángel)
    n = 2 if ("ángel" in t or "gabriel" in t) else 1
    for i in range(n):
        x = ancho * (0.5 + (i - (n - 1) / 2) * 0.28)
        base, h = alto * 0.78, alto * 0.42
        if i == n - 1 and n == 2:
            d.polygon([(x, base - h * 0.75), (x - h * 0.45, base - h * 0.95),
                       (x - h * 0.2, base - h * 0.45)], fill=(245, 240, 225))
            d.polygon([(x, base - h * 0.75), (x + h * 0.45, base - h * 0.95),
                       (x + h * 0.2, base - h * 0.45)], fill=(245, 240, 225))
        d.polygon([(x - h * 0.17, base), (x + h * 0.17, base),
                   (x + h * 0.08, base - h * 0.78), (x - h * 0.08, base - h * 0.78)],
                  fill=figura)
        d.ellipse([x - h * 0.09, base - h, x + h * 0.09, base - h * 0.8], fill=figura)
    # grano, para que no pese como una página de error
    import random
    rnd = random.Random(k)
    px = im.load()
    for _ in range(ancho * alto // 12):
        x, y = rnd.randrange(ancho), rnd.randrange(alto)
        r_, g_, b_ = px[x, y]
        e = rnd.randint(-10, 10)
        px[x, y] = (max(0, min(255, r_ + e)), max(0, min(255, g_ + e)),
                    max(0, min(255, b_ + e)))
    im.save(destino, "PNG")


def _voz(proyecto, estado, avisar):
    """Locuta con Edge; sin red, la locución simulada del estudio."""
    import p4_voz
    # COMO LO GUARDA LA PANTALLA DEL GUION: la voz y la velocidad elegidas a
    # mano para este vídeo van en `voz_del_video` (fuera de toda firma).
    params = {"idioma": "es", "modo": "continuo",
              "voz_del_video": {"voz_id": VOZ, "velocidad": round(5 / 35, 3)}}
    estado.set_params("voz", params)
    try:
        salidas = p4_voz.ejecutar(proyecto, params, avisar)
    except Exception as e:  # noqa: BLE001
        print(f"  voz gratuita no disponible ({e}); locución simulada", flush=True)
        os.environ["ESTUDIO_SIMULAR"] = "1"
        os.environ["ESTUDIO_MODO_VOZ"] = "cartesia"
        salidas = p4_voz.ejecutar(proyecto, params, avisar)
    estado.completar("voz", salidas)


def preparar(carpeta, ancho):
    import medios
    import p6_assets
    import p7_callouts
    from nucleo.estado import Estado
    from nucleo.proyecto import Proyecto

    raiz = os.path.join(carpeta, "proyecto")
    if os.path.isdir(raiz):
        shutil.rmtree(raiz)
    proyecto = Proyecto.crear(raiz, TITULO)
    estado = Estado(proyecto)
    material = "\n\n".join(t for _b, t in GUION)

    def avisar(_v, m=""):
        if m:
            print("   ", m, flush=True)

    estado.set_params("ingesta", {"texto": material})
    medios.escribir_json(os.path.join(proyecto.ruta_trabajo("ingesta"), "ingesta.json"),
                         {"palabras": len(material.split())})
    estado.completar("ingesta", {"palabras": len(material.split())})
    estado.set_params("brief", {"formato": "vertical", "idioma": "es"})
    medios.escribir_json(os.path.join(proyecto.ruta_trabajo("brief"), "brief.json"),
                         {"formato": "vertical", "idioma": "es", "tema": TITULO})
    estado.completar("brief", {"brief": "brief.json"})
    medios.escribir_json(os.path.join(proyecto.ruta_trabajo("guion"), "guion.json"), {
        "catalogo": CATALOGO,
        "guion": [{"id": b, "texto": t, "abre_seccion": b == "B001",
                   **({"emocion": EMOCIONES[b]} if b in EMOCIONES else {})}
                  for b, t in GUION]})
    estado.set_params("guion", {"idioma": "es"})
    estado.completar("guion", {"guion": "guion.json", "catalogo": "guion.json"})

    print("· voz (Brian Multilingual, +5 %)", flush=True)
    _voz(proyecto, estado, avisar)

    print("· planos y láminas", flush=True)
    arte = os.path.join(carpeta, "_arte")
    shutil.rmtree(arte, ignore_errors=True)
    os.makedirs(os.path.join(arte, "escenas"))
    os.makedirs(os.path.join(arte, "reparto"))
    params = {"calidad": "low", "min_s": 3.0, "max_s": 6.0, "semilla": 7,
              "motor_imagen": "adoptar", "imagenes_previas": [arte],
              "banco_imagenes": os.path.join(carpeta, "_banco"),
              "catalogo": CATALOGO,
              "estilo": {"prompt": "flat vector illustration", "referencias": []}}
    plan = p6_assets.planificar(proyecto, params)
    lw, lh = 1024, 1536
    for k, e in enumerate(plan["escenas"]):
        texto = " ".join(str(e.get(c) or "") for c in ("narracion", "texto"))
        _lamina(os.path.join(arte, "escenas", f"{e['id']}.png"), texto, k, lw, lh)
    for k, nombre in enumerate(CATALOGO["reparto"]):
        _lamina(os.path.join(arte, "reparto", f"{nombre}.png"), nombre, 50 + k, lw, lh)
    estado.set_params("assets", params)
    estado.completar("assets", p6_assets.ejecutar(proyecto, params, avisar))
    # sin las miniaturas de vista previa: no salen en el vídeo y, con el
    # Chromium de algunos contenedores, la captura suelta no termina nunca
    callouts = {"previsualizar": False}
    estado.set_params("callouts", callouts)
    estado.completar("callouts", p7_callouts.ejecutar(proyecto, callouts, avisar))
    return proyecto, estado


def render(proyecto, estado, look, carpeta, fps, ancho):
    import p8_render
    nombre, extra = LOOKS[look]
    alto = ancho * 16 // 9
    params = dict({"fps": fps, "resolucion": [ancho, alto], "calidad_video": "baja",
                   "sonido": False, "lotes": 0}, **extra)
    print(f"· render {look} ({nombre})", flush=True)

    def avisar(_v, m=""):
        if m:
            print("   ", m, flush=True)

    res = p8_render.ejecutar(proyecto, params, avisar)
    mp4 = os.path.join(carpeta, f"prueba_{look}_{nombre}.mp4")
    shutil.copy2(res["mp4"], mp4)
    _contactos(mp4, os.path.join(carpeta, f"contactos_{look}_{nombre}.png"))
    print(f"  -> {mp4}", flush=True)
    return mp4


def _contactos(mp4, destino, n=12):
    """Doce fotogramas repartidos en una hoja (4 x 3) para mirarlos de un golpe."""
    import medios
    sal = subprocess.run([medios.ffmpeg(), "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", "-i", mp4],
                         capture_output=True, text=True)
    try:
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout)
    except ValueError:
        dur = 60.0
    del sal
    paso = dur / (n + 1)
    subprocess.run([medios.ffmpeg(), "-y", "-v", "error", "-i", mp4, "-vf",
                    f"fps=1/{paso:.3f},scale=270:-1,tile=6x2", "-frames:v", "1",
                    destino], check=False)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("carpeta", nargs="?",
                   default=os.path.join(tempfile.gettempdir(), "video_prueba_pro"))
    a.add_argument("--looks", default="A,B,C")
    a.add_argument("--fps", type=int, default=15)
    a.add_argument("--ancho", type=int, default=540)
    args = a.parse_args()
    carpeta = os.path.abspath(args.carpeta)
    _entorno(carpeta)
    proyecto, estado = preparar(carpeta, args.ancho)
    hechos = []
    for look in [x.strip().upper() for x in args.looks.split(",") if x.strip()]:
        try:
            hechos.append(render(proyecto, estado, look, carpeta, args.fps, args.ancho))
        except Exception as e:  # noqa: BLE001  -- un look roto no tumba los otros
            print(f"  ✗ look {look}: {e}", flush=True)
    print("\nHECHO:", *hechos, sep="\n  ")


if __name__ == "__main__":
    main()
