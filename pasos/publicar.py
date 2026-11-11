"""ETAPA 7: publicar fácil. Lo que hace falta DESPUÉS de tener el MP4.

  · `textos`: título (y dos alternativas), descripción con capítulos y
    versículos, hashtags para YouTube y el texto corto para TikTok.
  · `miniatura`: la portada 1280x720 (YouTube) o 1080x1920 (TikTok/Shorts)
    con una imagen del vídeo y 2-4 palabras grandes, la clave en amarillo.
  · `subir_a_drive`: copia el MP4, las miniaturas y los textos a Google Drive
    con rclone (si está instalado y tiene un remoto configurado).

GRATIS Y SIN FIRMAS: no llama a Claude (todo sale del guion, del plan y de
cuentas de texto) y no escribe ningún param. Lo que produce vive en
`<proyecto>/publicar/`, fuera de `pasos/`: rehacer una miniatura no deja nada
obsoleto ni se paga.
"""
import os
import re
import shutil
import subprocess
import unicodedata

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

try:
    from . import citas, letras, voz_tema
except ImportError:                                           # pragma: no cover
    import citas
    import letras
    import voz_tema

CARPETA = "publicar"
AMARILLO = (255, 214, 0)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
TAMANOS = {"youtube": (1280, 720), "vertical": (1080, 1920)}

VACIAS = set("""a al ante bajo con contra de del desde durante e el en entre
era eran es esta este esto fue fueron ha han hasta la las le les lo los mas más
me mi mis muy ni no nos o os para pero por que qué quien quién se ser si sí sin
sobre su sus te tu tus un una unas uno unos y ya yo él ella ellos como cómo
cual cuál cuando cuándo donde dónde porque hay sabias sabías""".split())

#: Hashtags fijos por tema (los de `voz_tema.TEMAS`). Van detrás de los propios
#: del vídeo: YouTube enseña los TRES primeros encima del título.
POR_TEMA = {
    "fe": ["#biblia", "#fe", "#dios", "#jesus", "#historiasbiblicas",
           "#cristianos", "#palabradedios"],
    "historia": ["#historia", "#curiosidades", "#documental", "#historiaantigua"],
    "misterio": ["#misterio", "#enigmas", "#curiosidades", "#sabiasque"],
    "infantil": ["#cuentos", "#niños", "#infantil", "#aprender"],
    "motivacion": ["#motivacion", "#reflexion", "#superacion", "#vida"],
    "ciencia": ["#ciencia", "#curiosidades", "#aprende", "#datoscuriosos"],
}
GENERICOS = ["#curiosidades", "#sabiasque", "#aprende"]
MAX_HASHTAGS = 15          # YouTube ignora TODOS si pasan de 60; 15 es su consejo


# ------------------------------------------------------------- utilidades
def _plegar(texto):
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def limpiar(texto):
    """Sin etiquetas de voz (<break/>, [risa]) ni marcas de subtítulo (~~ *)."""
    texto = re.sub(r"<[^<>]*>|\[[^\[\]]*\]", " ", str(texto or ""))
    texto = texto.replace("~~", "").replace("*", "")
    return re.sub(r"\s+", " ", texto).strip()


def _frases(texto):
    return [f.strip() for f in re.split(r"(?<=[.!?…])\s+", limpiar(texto)) if f.strip()]


def _cortar(texto, tope):
    texto = limpiar(texto)
    if len(texto) <= tope:
        return texto
    corte = texto[:tope - 1].rsplit(" ", 1)[0].rstrip(",;:")
    return corte + "…"


def _reloj(segundos):
    s = int(max(0, round(float(segundos or 0))))
    return f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}" if s >= 3600 \
        else f"{s // 60}:{s % 60:02d}"


def _hashtag(palabra):
    llana = re.sub(r"[^a-z0-9]", "", _plegar(palabra))
    return "#" + llana if len(llana) >= 3 else ""


def palabras_clave(texto, n=4):
    """Las palabras con contenido de un texto, en su orden (sin repetir)."""
    vistas, salida = set(), []
    for cruda in re.findall(r"[\wÁÉÍÓÚÑáéíóúñü]+", limpiar(texto)):
        llana = _plegar(cruda)
        if llana in VACIAS or len(llana) < 3 or llana in vistas:
            continue
        vistas.add(llana)
        salida.append(cruda)
        if len(salida) >= n:
            break
    return salida


# ------------------------------------------------------------------ textos
def _bloques(guion):
    return [b for b in (guion or {}).get("guion") or []
            if limpiar(b.get("texto") if isinstance(b, dict) else b)]


def _texto_de(b):
    return limpiar(b.get("texto") if isinstance(b, dict) else b)


def capitulos(escenas, bloques, duracion):
    """Capítulos de YouTube: uno por bloque del guion, con el segundo en que
    empieza su primer plano. YouTube los acepta con 3 o más, el primero en 0:00
    y cada uno de 10 s como mínimo; si no se cumple, no se ponen."""
    inicio = {}
    for e in escenas or []:
        bid = str(((e.get("origen") or {}).get("bloque")) or "")
        if bid and bid not in inicio:
            inicio[bid] = float(e.get("t_in") or 0.0)
    marcas = []
    for b in bloques:
        bid = str(b.get("id") or "") if isinstance(b, dict) else ""
        if bid not in inicio:
            continue
        nombre = " ".join(palabras_clave(_texto_de(b), 5)) or bid
        marcas.append([inicio[bid], nombre[:1].upper() + nombre[1:]])
    if not marcas:
        return []
    marcas.sort(key=lambda m: m[0])
    marcas[0][0] = 0.0
    finales = [m[0] for m in marcas[1:]] + [float(duracion or 0)]
    if len(marcas) < 3 or any(f - m[0] < 10 for m, f in zip(marcas, finales)):
        return []
    return [f"{_reloj(t)} {nombre}" for t, nombre in marcas]


def textos(nombre, guion=None, escenas=None, duracion=0.0, vertical=False):
    """Todo lo que se pega al publicar. -> dict (ver claves abajo)."""
    bloques = _bloques(guion)
    completo = " ".join(_texto_de(b) for b in bloques)
    titulo = limpiar((guion or {}).get("titulo") or nombre or "")
    frases = _frases(completo)
    gancho = frases[0] if frases else titulo

    tema, _ = voz_tema.tema_de(completo + " " + titulo)
    halladas = []
    for c in citas.buscar(completo.split()):
        if c["cita"] not in halladas:
            halladas.append(c["cita"])

    # TÍTULOS: el del guion y dos formas de gancho. Máximo 70 caracteres: lo
    # que YouTube enseña entero en el móvil.
    claves = palabras_clave(titulo or gancho, 4)
    candidatos = [titulo, _cortar(gancho, 70)]
    if claves:
        candidatos.append(f"¿Sabías esto de {' '.join(claves[:3])}?")
    vistos, titulos = set(), []
    for t in candidatos:
        t = _cortar(t, 70)
        if t and _plegar(t) not in vistos:
            vistos.add(_plegar(t))
            titulos.append(t)

    # HASHTAGS: los del propio vídeo (palabras del título, libros citados)
    # delante; los del tema detrás.
    tags = []
    for p in palabras_clave(titulo, 3):
        tags.append(_hashtag(p))
    for cita in halladas[:3]:
        tags.append(_hashtag(cita.rsplit(" ", 1)[0]))
    tags += POR_TEMA.get(tema or "", GENERICOS)
    if vertical:
        tags.insert(0, "#shorts")
    hashtags = []
    for t in tags:
        if t and t not in hashtags:
            hashtags.append(t)
    hashtags = hashtags[:MAX_HASHTAGS]

    # DESCRIPCIÓN: gancho, de qué va, versículos, capítulos, llamada y tags.
    partes = [gancho]
    resumen = " ".join(frases[1:3])
    if resumen:
        partes.append(_cortar(resumen, 300))
    if halladas:
        partes.append("📖 Versículos (Reina-Valera 1960):\n"
                      + "\n".join(f"• {c}" for c in halladas[:10]))
    caps = [] if vertical else capitulos(escenas, bloques, duracion)
    if caps:
        partes.append("⏱️ Capítulos:\n" + "\n".join(caps))
    partes.append("👉 Si te ha servido, suscríbete y compártelo con alguien "
                  "que lo necesite. ¿Qué te ha parecido? Te leo en los comentarios.")
    partes.append(" ".join(hashtags))
    descripcion = "\n\n".join(partes)[:4900]   # YouTube: 5000 como mucho

    tiktok = _cortar(gancho, 120) + " " + " ".join(
        [t for t in hashtags if t != "#shorts"][:5])
    texto_miniatura = " ".join(palabras_clave(titulo or gancho, 4)).upper()
    return {
        "titulo": titulos[0] if titulos else "",
        "titulos": titulos,
        "descripcion": descripcion,
        "hashtags": hashtags,
        "tiktok": tiktok.strip(),
        "miniatura": texto_miniatura,
        "versiculos": halladas,
        "capitulos": caps,
        "tema": tema or "",
    }


def como_txt(t):
    """Los textos en un .txt para el paquete y para Drive."""
    return "\n".join([
        "TÍTULO", t["titulo"], "",
        "OTROS TÍTULOS", *[f"- {x}" for x in t["titulos"][1:]], "",
        "DESCRIPCIÓN (YouTube)", t["descripcion"], "",
        "HASHTAGS", " ".join(t["hashtags"]), "",
        "TEXTO PARA TIKTOK", t["tiktok"], ""])


# --------------------------------------------------------------- miniatura
def _fuente(tam):
    ruta = letras.ruta(letras.POR_DEFECTO)
    try:
        return ImageFont.truetype(ruta, tam)
    except (OSError, ValueError):                             # pragma: no cover
        return ImageFont.load_default()


def _lineas(palabras, fuente, ancho, dibujo):
    """Parte las palabras en líneas que caben en `ancho` (2 como mucho)."""
    lineas, actual = [], []
    for p in palabras:
        prueba = " ".join(actual + [p])
        if actual and dibujo.textlength(prueba, font=fuente) > ancho:
            lineas.append(actual)
            actual = [p]
        else:
            actual.append(p)
    if actual:
        lineas.append(actual)
    return lineas


def miniatura(imagen, texto, salida, formato="youtube"):
    """Dibuja la portada y la guarda en `salida` (JPEG). -> ruta.

    La imagen se recorta a la proporción (centrada), se le sube un poco el
    contraste y la saturación, y se oscurece por abajo (arriba en vertical)
    para que las letras se lean en el móvil. Texto: 4 palabras como mucho, en
    mayúsculas, con contorno negro; la palabra más larga va en amarillo.
    """
    ancho, alto = TAMANOS.get(formato, TAMANOS["youtube"])
    if imagen and os.path.isfile(imagen):
        base = Image.open(imagen).convert("RGB")
        base = ImageOps.fit(base, (ancho, alto), Image.LANCZOS, centering=(0.5, 0.4))
        base = ImageEnhance.Contrast(base).enhance(1.12)
        base = ImageEnhance.Color(base).enhance(1.15)
    else:
        base = Image.new("RGB", (ancho, alto), (24, 20, 16))

    vertical = alto > ancho
    sombra = Image.new("L", (1, 256))
    for y in range(256):
        f = y / 255 if not vertical else 1 - y / 255
        sombra.putpixel((0, y), int(215 * max(0.0, f - 0.35) / 0.65))
    sombra = sombra.resize((ancho, alto))
    base = Image.composite(Image.new("RGB", (ancho, alto), NEGRO), base, sombra)

    palabras = [p for p in re.split(r"\s+", limpiar(texto).upper()) if p][:4]
    if palabras:
        dibujo = ImageDraw.Draw(base)
        caja = int(ancho * 0.9)
        tam = int(alto * (0.2 if not vertical else 0.11))
        while tam > 24:
            fuente = _fuente(tam)
            lineas = _lineas(palabras, fuente, caja, dibujo)
            if len(lineas) <= 2 and all(
                    dibujo.textlength(" ".join(l), font=fuente) <= caja for l in lineas):
                break
            tam = int(tam * 0.9)
        clave = max(palabras, key=len)
        alto_linea = int(tam * 1.08)
        total = alto_linea * len(lineas)
        y = (alto - total - int(alto * 0.06)) if not vertical else int(alto * 0.12)
        borde = max(3, tam // 12)
        for linea in lineas:
            medida = dibujo.textlength(" ".join(linea), font=fuente)
            x = (ancho - medida) / 2
            for p in linea:
                color = AMARILLO if p == clave else BLANCO
                dibujo.text((x, y), p, font=fuente, fill=color,
                            stroke_width=borde, stroke_fill=NEGRO)
                x += dibujo.textlength(p + " ", font=fuente)
            y += alto_linea
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    base.save(salida, "JPEG", quality=90, optimize=True)
    return salida


# ------------------------------------------------------------------- drive
def remoto_drive():
    """El remoto de rclone a usar (`ESTUDIO_DRIVE_REMOTO`, por defecto «drive»)."""
    return (os.environ.get("ESTUDIO_DRIVE_REMOTO") or "drive").strip().rstrip(":")


def carpeta_drive():
    return (os.environ.get("ESTUDIO_DRIVE_CARPETA") or "Shaddai Studio").strip()


def drive_listo():
    """-> (True, "") o (False, motivo para la pantalla)."""
    rclone = shutil.which("rclone")
    if not rclone:
        return False, "falta rclone en el servidor"
    try:
        r = subprocess.run([rclone, "listremotes"], capture_output=True,
                           text=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as fallo:
        return False, f"rclone no responde: {fallo}"
    remotos = [x.strip().rstrip(":") for x in (r.stdout or "").splitlines()]
    if remoto_drive() not in remotos:
        return False, f"rclone no tiene el remoto «{remoto_drive()}» (falta conectar Drive)"
    return True, ""


def subir_a_drive(ficheros, subcarpeta, avisar=None):
    """Copia los ficheros a `<remoto>:<carpeta>/<subcarpeta>/`. -> enlace o ""."""
    rclone = shutil.which("rclone")
    subcarpeta = re.sub(r"[\\/:]+", "-", str(subcarpeta or "video")).strip() or "video"
    destino = f"{remoto_drive()}:{carpeta_drive()}/{subcarpeta}"
    for ruta in ficheros:
        if avisar:
            avisar(f"subiendo {os.path.basename(ruta)}")
        r = subprocess.run([rclone, "copy", ruta, destino], capture_output=True,
                           text=True, timeout=3600)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout or "rclone falló").strip()[-400:])
    r = subprocess.run([rclone, "link", destino], capture_output=True,
                       text=True, timeout=60)
    return (r.stdout or "").strip() if r.returncode == 0 else ""
