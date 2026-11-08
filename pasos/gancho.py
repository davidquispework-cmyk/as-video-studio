"""EL GANCHO DE LOS 3 SEGUNDOS y los subtitulos palabra a palabra.

Etapa 3 de la hoja de ruta (formato TikTok: «¿Sabías…?» con letras grandes al
empezar, subtitulos que se encienden palabra a palabra con la clave resaltada y
las cifras grandes). Todo es SVG con SMIL dentro de la capa QUIETA del paso
callouts (p7): el render ya la pinta encima de la imagen, asi que no hay nada
que cambiar en el render ni nada que pagar.

Se enciende con el param `gancho` del paso callouts:

    true            gancho automatico (sale de la primera frase del guion)
    "¿Sabías que…?" ese texto, tal cual
    false / falta   como siempre (no va en los defectos: no mueve firmas)

Y en plan.json la PRIMERA escena puede llevar `"gancho": "texto"` (manda sobre
el automatico) o `"gancho": false` (sin cartel grande, pero con los subtitulos
palabra a palabra).

Cambiarlo solo rehace callouts y el montaje: gratis, ni una imagen.

PUNTO B y B+ DE LAS NOTAS (6-nov-2026), lo que cambio y por que:

- Mientras esta el cartel grande NO hay subtitulo debajo (se leia doble). El
  cartel dura lo que tarda la voz en decir lo que pone (`cartel_de` devuelve
  cuantas palabras dichas muestra), entre 1,8 y 5 s.
- UN SOLO CRITERIO DE LETRA: todo el subtitulo en minusculas normales (una
  palabra en MAYUSCULAS del guion pasa a «Dios»), mismo tamano para todo; lo
  unico distinto es el COLOR de la palabra clave y de las cifras. Con una letra
  de solo mayusculas (Bebas) va todo en mayusculas.
- El cartel ya no corta en «y…?»: corta en una coma o detras de una palabra
  con contenido (`_recortar`).
- Estilo TikTok: letra con caracter (pasos/letras.py), cada palabra da un
  pequeno salto al decirse, la clave con SUBRAYADO o RECUADRO que se dibuja
  (param `resalte`), TACHADO animado en «no X sino Y» / «no es X, es Y» (o
  ~~palabra~~ en el texto corregido a mano; *palabra* fuerza la clave), y
  CONTADORES: una cifra sube desde 0 (un ano, desde 50 antes) y llega a su
  valor justo cuando la voz acaba de decirla.
"""
import re

try:
    from . import citas
except ImportError:  # ejecutado con la carpeta pasos directamente en sys.path
    import citas

#: Cuanto dura el cartel grande del principio, en segundos.
DURACION_S = 3.0

#: Color de la palabra clave y de las cifras si la paleta no trae acento.
AMARILLO = "#FFD23F"

#: El cartel dura lo que tarda en decirse, pero nunca menos ni mas que esto.
DURACION_MIN, DURACION_MAX = 1.8, 5.0

#: Rojo TikTok: el del tachado (lo falso) y el resalte si la paleta no ayuda.
ROJO = "#FF3B3B"

#: Ya no se usa: las cifras van del MISMO tamano que el resto (un criterio).
ESCALA_CIFRA = 1.0

#: Las palabras dichas aun no llegan a blancas del todo: se ven, pero apagadas.
APAGADA = 0.45

_VACIAS = set("""
a al ante bajo con contra de del desde durante en entre hacia hasta mediante
para por segun sin sobre tras y e ni o u pero sino que como cuando donde
el la los las lo un una unos unas su sus mi mis tu tus se le les me te nos os
es era fue ser son estaba este esta esto estos estas ese esa eso aquel aquella
muy mas ya no si asi tan tambien pues porque aunque mientras entonces hay habia
the of and to in a is was for on with that his her their
""".split())

#: Palabras largas que no son la idea de nada: nunca son la palabra clave.
_NO_CLAVE = _VACIAS | set("""
antes despues ahora luego todo toda todos todas nada algo cada otro otra otros
otras tiene tenia tenian hacer hizo hacia dice dijo decir puede podia solo
siempre nunca aqui alli alla donde entonces cuando porque mientras tambien
tanto tanta muchos muchas mucho mucha pocos poco esos esas aquellos aquellas
estan estaban eran fueron seria habia hubo haber sido siendo vez veces dentro
fuera sobre despues segun hasta desde contra cosas cosa forma manera parte
""".split())


def es_cifra(palabra):
    return bool(re.search(r"\d", str(palabra or "")))


def _llana(palabra):
    return re.sub(r"[^0-9a-záéíóúüñ]", "", str(palabra or "").lower())


def palabra_clave(palabras):
    """El indice de la palabra que se resalta en un trozo, o None.

    Una cifra gana siempre; si no, la palabra con mas letras que no sea de
    relleno (articulos, preposiciones...) y tenga al menos cuatro. Un nombre
    propio en medio de la frase suma: suele ser de quien va el video.
    """
    mejor, puntos = None, 0
    for i, palabra in enumerate(palabras or []):
        llana = _llana(palabra)
        if es_cifra(palabra):
            return i
        sin_tilde = llana.translate(str.maketrans("áéíóúü", "aeiouu"))
        if len(llana) < 4 or sin_tilde in _NO_CLAVE:
            continue
        valor = len(llana) + (3 if i > 0 and str(palabra)[:1].isupper() else 0)
        if valor > puntos:
            mejor, puntos = i, valor
    return mejor




_LETRA = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
_FIN_FRASE = re.compile(r"[.!?…]$")
_FIN_TRAMO = re.compile(r"[,;:.!?…]$")


def _recortar(palabras, tope):
    """Las primeras palabras de una frase, cortadas en un sitio que se lee.

    Corta en la ultima coma que deje al menos tres palabras; si no hay, en el
    tope, y luego quita lo que cuelga al final (y, de, que, el...): «¿Sabías que
    José y…?» era justo lo que se veia mal.
    """
    palabras = list(palabras[:tope])
    for i in range(len(palabras) - 1, 2, -1):
        if palabras[i - 1].endswith((",", ";", ":")):
            palabras = palabras[:i]
            break
    while len(palabras) > 3 and _llana(palabras[-1]) in _VACIAS:
        palabras.pop()
    return palabras


def cartel_de(narracion, propio=None, max_palabras=12):
    """(texto del cartel, cuantas palabras DICHAS muestra o None).

    Con el segundo numero el cartel dura lo que la voz tarda en decirlo.
    """
    if isinstance(propio, str) and propio.strip():
        return " ".join(propio.split()), None
    texto = " ".join(str(narracion or "").split())
    if not texto:
        return "", None
    pregunta = re.match(r"\s*(¿[^?]{2,240}\?)", texto)
    if pregunta:
        dichas = pregunta.group(1).split()
        if len(dichas) <= max_palabras:
            return pregunta.group(1), len(dichas)
        corta = _recortar(dichas, 9)
        return " ".join(corta).rstrip(",;:") + "…?", len(corta)
    frase = re.split(r"(?<=[.!?…:;])\s", texto, maxsplit=1)[0]
    dichas = frase.split()
    if len(dichas) <= max_palabras:
        return frase.rstrip(".:;"), len(dichas)
    # la primera clausula, si es una frase por si misma
    for i, palabra in enumerate(dichas[:max_palabras]):
        if palabra.endswith(",") and i >= 3:
            return " ".join(dichas[:i + 1]).rstrip(","), i + 1
    corta = _recortar(dichas, 8)
    if re.match(r"(?i)¿?sab[ií]as", frase):
        return " ".join(corta).rstrip(",;:") + "…?", len(corta)
    return " ".join(corta).rstrip(",;:") + "…", len(corta)


def texto_de(narracion, propio=None, max_palabras=12):
    """El texto del cartel grande. -> str ('' = sin cartel). Ver `cartel_de`."""
    return cartel_de(narracion, propio, max_palabras)[0]


def duracion_cartel(escena, dichas):
    """Cuanto dura el cartel: lo que tarda la voz en decir sus palabras."""
    try:
        plano = float(escena.get("t_out")) - float(escena.get("t_in") or 0)
    except (TypeError, ValueError):
        plano = DURACION_S
    duracion = DURACION_S
    marcas = escena.get("marcas") or []
    if dichas and 0 < dichas <= len(marcas):
        try:
            fin = float(marcas[dichas - 1][1]) - float(escena.get("t_in") or 0)
            duracion = max(DURACION_MIN, min(DURACION_MAX, fin + 0.3))
        except (TypeError, ValueError, IndexError):
            pass
    return max(0.0, min(duracion, plano))


def _escapar(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _partir(palabras, medir, ancho):
    lineas, actual = [], []
    for palabra in palabras:
        prueba = " ".join(actual + [palabra])
        if actual and medir(prueba) > ancho:
            lineas.append(actual)
            actual = [palabra]
        else:
            actual.append(palabra)
    if actual:
        lineas.append(actual)
    return lineas


# ------------------------------------------------------------ el texto que se ve

def caso_limpio(palabra):
    """«DIOS» -> «Dios»: un solo criterio de mayusculas en el subtitulo.

    Solo palabras de cuatro letras o mas: «ONU», «XVI» o «EE.UU.» se quedan.
    """
    palabra = str(palabra or "")
    letras = re.sub(f"[^{_LETRA}]", "", palabra)
    if len(letras) < 4 or not letras.isupper():
        return palabra
    i = re.search(f"[{_LETRA}]", palabra).start()
    return palabra[:i] + palabra[i] + palabra[i + 1:].lower()


def _quitar_marcas(palabra):
    """'~~mito~~,' -> ('mito,', 'tachar'); '*Dios*' -> ('Dios', 'clave')."""
    for patron, tipo in ((r"^([^~*\w]*)~~(.+?)~~([^~*\w]*)$", "tachar"),
                         (r"^([^~*\w]*)\*(.+?)\*([^~*\w]*)$", "clave")):
        m = re.match(patron, palabra)
        if m:
            return m.group(1) + m.group(2) + m.group(3), tipo
    return palabra, None


def _mejor(indices, palabras):
    if not indices:
        return None
    elegida = palabra_clave([palabras[k] for k in indices])
    return indices[elegida if elegida is not None else -1]


def _primera(indices):
    """Lo verdadero es lo PRIMERO que se dice detras («sino un fruto
    cualquiera» -> fruto), no la palabra mas larga."""
    return indices[0] if indices else None


def _contenido(indices, llanas):
    return [k for k in indices if re.search(r"\d", llanas[k])
            or (len(llanas[k]) >= 3 and llanas[k] not in _VACIAS)]


_COPULAS = {"es", "era", "fue", "son", "eran", "fueron", "sera", "será"}


def contrastes(palabras):
    """Lo FALSO y lo VERDADERO de una frase. -> (tachar: set, verdad: set)

    Dos formas, las que de verdad usa un guion que desmiente algo:
      «no fue una manzana, sino un fruto»   -> tacha «manzana», marca «fruto»
      «no es un mito, es historia»          -> tacha «mito», marca «historia»
    No cruza un punto: lo de otra frase no es su contraste.
    """
    llanas = [_llana(p) for p in palabras]
    tachar, verdad = set(), set()

    def detras(desde):
        tramo = []
        for k in range(desde, min(len(palabras), desde + 8)):
            tramo.append(k)
            if _FIN_TRAMO.search(palabras[k]):
                break
        return tramo

    for i, llana in enumerate(llanas):
        if llana == "sino":
            ini = None
            for j in range(i - 1, max(-1, i - 11), -1):
                if _FIN_FRASE.search(palabras[j]):
                    break
                if llanas[j] == "no":
                    ini = j
                    break
            if ini is None:
                continue
            falso = _mejor(_contenido(list(range(ini + 1, i)), llanas), palabras)
            cierto = _primera(_contenido(detras(i + 1), llanas))
            if falso is not None and cierto is not None:
                tachar.add(falso)
                verdad.add(cierto)
        elif (llana == "no" and i + 1 < len(llanas)
                and llanas[i + 1] in _COPULAS):
            verbo = llanas[i + 1]
            for k in range(i + 2, min(len(palabras) - 1, i + 10)):
                if _FIN_FRASE.search(palabras[k]):
                    break
                if palabras[k].endswith(",") and llanas[k + 1] == verbo:
                    falso = _mejor(_contenido(list(range(i + 2, k + 1)), llanas),
                                   palabras)
                    cierto = _primera(_contenido(detras(k + 2), llanas))
                    if falso is not None and cierto is not None:
                        tachar.add(falso)
                        verdad.add(cierto)
                    break
    return tachar, verdad


def preparar(trozos, mayus=False):
    """Los trozos de UN plano con lo que se dibuja de cada palabra.

    Anade a cada trozo `vistas` (el texto de cada palabra, con el criterio de
    mayusculas ya aplicado), `clave` (indice o None) y `tachar` (set). Se hace
    con el plano entero porque un «no… sino…» puede caer en dos trozos.
    """
    todas, marcas, cortes, salida = [], [], [], []
    for trozo in trozos:
        cortes.append(len(todas))
        for palabra in str(trozo.get("texto") or "").split():
            limpia, tipo = _quitar_marcas(palabra)
            todas.append(limpia.upper() if mayus else caso_limpio(limpia))
            marcas.append(tipo)
    tachar, verdad = contrastes(todas)
    for g, tipo in enumerate(marcas):
        if tipo == "tachar":
            tachar.add(g)
            verdad.discard(g)
        elif tipo == "clave":
            verdad.add(g)
            tachar.discard(g)
    cortes.append(len(todas))
    for n, trozo in enumerate(trozos):
        a, b = cortes[n], cortes[n + 1]
        vistas = todas[a:b]
        mis_tachadas = {g - a for g in tachar if a <= g < b}
        mis_verdades = sorted(g - a for g in verdad if a <= g < b)
        if mis_verdades:
            clave = mis_verdades[0]
        else:
            clave = palabra_clave(["" if k in mis_tachadas else x
                                   for k, x in enumerate(vistas)])
        salida.append(dict(trozo, vistas=vistas, clave=clave,
                           tachar=mis_tachadas))
    return salida


def contador(palabra):
    """Si la palabra es una cifra que puede SUBIR, su ficha; si no, None.

    «350» sube de 0 a 350; «1.500» respeta el punto de miles; «1656» (un ano)
    sube desde 1606, que contar desde cero un ano no tiene sentido. Decimales,
    rangos o una cifra de un solo digito no suben.
    """
    m = re.fullmatch(r"([^\d]*)(\d{1,3}(?:[.,]\d{3})+|\d+)([^\d]*)", str(palabra or ""))
    if not m:
        return None
    previo, numero, sufijo = m.groups()
    valor = int(re.sub(r"\D", "", numero))
    if valor < 10:          # contar hasta 3 no luce: una cifra sola da el salto
        return None
    miles = "." if "." in numero else ("," if "," in numero else "")
    anio = (not miles and len(numero) == 4 and 1000 <= valor <= 2100
            and "%" not in sufijo)
    return {"previo": previo, "valor": valor, "sufijo": sufijo, "miles": miles,
            "desde": max(0, valor - 50) if anio else 0}


def _formato(ficha, valor):
    texto = str(int(valor))
    if ficha["miles"]:
        texto = f"{int(valor):,}".replace(",", ficha["miles"])
    return ficha["previo"] + texto + ficha["sufijo"]


def _pasos_contador(ficha, inicio, fin, pasos=16):
    """[(texto, instante)] de la cuenta, frenando al final (ease-out)."""
    salto = ficha["valor"] - ficha["desde"]
    n = max(1, min(pasos, salto))
    vistos, salida = None, []
    for k in range(n + 1):
        f = k / float(n)
        valor = ficha["desde"] + salto * (1 - (1 - f) ** 3)
        texto = _formato(ficha, round(valor))
        if texto != vistos:
            salida.append((texto, inicio + (fin - inicio) * f))
            vistos = texto
    # la cifra de verdad sale JUSTO al acabar de decirla, ni antes ni despues
    salida[-1] = (salida[-1][0], fin)
    return salida


# ------------------------------------------------------------- piezas animadas

def _pop(inicio, fuerza=1.18, dur=0.22):
    return (f'<animateTransform attributeName="transform" type="scale" '
            f'values="{fuerza};0.97;1" keyTimes="0;0.6;1" dur="{dur}s" '
            f'begin="{inicio:.2f}s" fill="freeze"/>')


def _trazo(x, y, ancho, alto, color, inicio, dur=0.28, radio=None, giro=0):
    """Una barra que SE DIBUJA de izquierda a derecha (subrayado, tachado,
    recuadro)."""
    radio = alto / 2.0 if radio is None else radio
    barra = (f'<g transform="translate({x:.1f} {y:.1f})">'
             f'<rect x="0" y="0" width="{ancho:.1f}" height="{alto:.1f}" '
             f'rx="{radio:.1f}" fill="{color}" transform="scale(0 1)">'
             f'<animateTransform attributeName="transform" type="scale" '
             f'values="0 1;1 1" dur="{dur}s" begin="{inicio:.2f}s" '
             f'fill="freeze"/></rect></g>')
    return f'<g transform="rotate({giro})">{barra}</g>' if giro else barra


def _contorno(tam):
    return (f'stroke="#000000" stroke-opacity="0.9" '
            f'stroke-width="{max(2.0, tam * 0.16):.1f}" stroke-linejoin="round" '
            f'paint-order="stroke"')


def svg_cartel(texto, salida, medidor, fuente="Verdana", acento=AMARILLO,
               duracion=DURACION_S, peso="900", resalte="subrayado"):
    """El cartel grande de los primeros segundos: destello, palabras que
    entran de golpe una detras de otra, la clave en el acento y fuera.

    `medidor(tam)` devuelve una funcion que mide texto a ese cuerpo con la
    fuente de verdad. Va en MAYUSCULAS y arriba del centro.
    """
    texto = " ".join(str(texto or "").split())
    if not texto or duracion <= 0.3:
        return ""
    ancho, alto = salida
    palabras = texto.upper().split()
    clave = palabra_clave(texto.split())
    ancho_max = ancho * 0.86
    tam = int(min(ancho, alto) * 0.115)
    while True:
        medir = medidor(tam)
        lineas = _partir(palabras, medir, ancho_max)
        largo = max(medir(" ".join(x)) for x in lineas)
        if (len(lineas) <= 4 and largo <= ancho_max) or tam <= 40:
            break
        tam = int(tam * 0.9)
    espacio = max(medir(" ") * 1.15, tam * 0.24)
    salto = tam * 1.12
    cx = ancho / 2.0
    cy = alto * (0.36 if alto > ancho else 0.40)
    arriba = cy - salto * (len(lineas) - 1) / 2.0
    caja_ancho = largo + tam * 0.9
    caja_alto = salto * len(lineas) + tam * 0.5
    piezas = [
        f'<rect x="{-caja_ancho / 2:.0f}" y="{arriba - cy - tam * 0.95:.0f}" '
        f'width="{caja_ancho:.0f}" height="{caja_alto:.0f}" rx="{tam * 0.25:.0f}" '
        f'fill="#000000" opacity="0.5"/>']
    n, total = 0, len(palabras)
    escalon = min(0.08, 0.9 / max(1, total))
    for indice, linea in enumerate(lineas):
        anchos = [medir(p) for p in linea]
        x = -(sum(anchos) + espacio * (len(linea) - 1)) / 2.0
        y = arriba - cy + salto * indice
        for palabra, w in zip(linea, anchos):
            entra = 0.1 + escalon * n
            es_clave = n == clave
            extra = ""
            if es_clave and resalte == "recuadro":
                extra = _trazo(-w / 2 - tam * 0.12, -tam * 0.86, w + tam * 0.24,
                               tam * 1.08, acento, entra + 0.15,
                               radio=tam * 0.14)
            elif es_clave and resalte != "color":
                extra = _trazo(-w / 2, tam * 0.14, w, tam * 0.12, acento,
                               entra + 0.2)
            relleno = ("#ffffff" if es_clave and resalte == "recuadro"
                       else acento if es_clave else "#ffffff")
            piezas.append(
                f'<g transform="translate({x + w / 2:.1f} {y:.1f})">'
                f'<g transform="scale(0)">{extra}'
                f'<text x="0" y="0" font-family="{fuente}" font-size="{tam}" '
                f'font-weight="{peso}" text-anchor="middle" fill="{relleno}" '
                f'{_contorno(tam)}>{_escapar(palabra)}</text>'
                f'<animateTransform attributeName="transform" type="scale" '
                f'values="0;1.18;0.96;1" keyTimes="0;0.55;0.8;1" dur="0.32s" '
                f'begin="{entra:.2f}s" fill="freeze"/></g></g>')
            x += w + espacio
            n += 1
    fin = max(0.3, duracion - 0.3)
    salida_anim = (f'<animate attributeName="opacity" from="1" to="0" '
                   f'begin="{fin:.2f}s" dur="0.3s" fill="freeze"/>')
    destello = (f'<rect x="0" y="0" width="{ancho}" height="{alto}" '
                f'fill="#ffffff" opacity="0">'
                f'<animate attributeName="opacity" values="0.85;0" '
                f'dur="0.35s" begin="0s" fill="freeze"/></rect>')
    return (f'<g class="gancho">{destello}'
            f'<g transform="translate({cx:.0f} {cy:.0f})">'
            f'{"".join(piezas)}{salida_anim}</g></g>')


def bloque_palabras(trozo, banda, tam, medir, fuente="Verdana", peso=600,
                    color="#ffffff", acento=AMARILLO, opacidad=0.0, radio=0,
                    partir=None, resalte="subrayado", contorno=True):
    """Un trozo de subtitulo que se enciende PALABRA A PALABRA.

    Cada palabra se coloca a mano (para poder subrayarla, tacharla o hacerla
    contar): esta desde que entra el trozo, apagada, y al decirse se enciende
    con un pequeno salto. Clave y cifras en el color de acento, del MISMO
    tamano que el resto. `medir(texto)` da el ancho exacto en px.
    """
    if "vistas" not in trozo:
        trozo = preparar([trozo])[0]
    vistas = list(trozo.get("vistas") or [])
    if not vistas:
        return ""
    partir = partir or (lambda t, m, a: [t])
    desde_t, hasta_t = float(trozo["desde"]), float(trozo["hasta"])
    tiempos = list(trozo.get("palabras") or [])
    if len(tiempos) != len(vistas):
        tiempos = repartir(len(vistas), desde_t, hasta_t)
    lineas, k = [], 0
    for linea in (partir(" ".join(vistas), medir, banda["ancho"]) or []):
        cuantas = len(linea.split())
        lineas.append(list(range(k, k + cuantas)))
        k += cuantas
    if k != len(vistas):
        lineas = [list(range(len(vistas)))]
    clave, tachar = trozo.get("clave"), set(trozo.get("tachar") or ())
    anchos = [medir(x) for x in vistas]
    espacio = max(medir(" ") * 1.1, tam * 0.22)
    salto = tam * 1.22
    base = float(banda["suelo"]) - salto * (len(lineas) - 1)
    centro = float(banda["centro"])
    totales = [sum(anchos[i] for i in fila) + espacio * (len(fila) - 1)
               for fila in lineas]
    piezas = []
    if opacidad and opacidad > 0:
        ancho_caja = max(totales) + 2 * tam * 0.38
        arriba = base - tam * 0.96
        alto_caja = salto * (len(lineas) - 1) + tam * 1.36
        piezas.append(f'<rect x="{centro - ancho_caja / 2:.0f}" y="{arriba:.0f}" '
                      f'width="{ancho_caja:.0f}" height="{alto_caja:.0f}" '
                      f'rx="{radio:.0f}" ry="{radio:.0f}" fill="#000000" '
                      f'opacity="{opacidad:g}"/>')
    trazo = _contorno(tam) if contorno else ""
    letra = (f'font-family="{fuente}" font-size="{tam}" font-weight="{peso}" '
             f'text-anchor="middle" {trazo}')
    for fila, total in zip(lineas, totales):
        x = centro - total / 2.0
        y = base + salto * lineas.index(fila)
        for i in fila:
            w, palabra = anchos[i], vistas[i]
            d0 = max(0.0, float(tiempos[i][0]))
            d1 = max(d0, float(tiempos[i][1]))
            es_clave, cifra = i == clave, es_cifra(palabra)
            relleno = acento if (es_clave or cifra) else color
            extra, fuerza = "", 1.18
            if es_clave or cifra:
                fuerza = 1.32
            if es_clave and resalte == "recuadro" and i not in tachar:
                relleno = "#ffffff"
                extra += _trazo(-w / 2 - tam * 0.14, -tam * 0.84,
                                w + tam * 0.28, tam * 1.1, acento, d0,
                                dur=0.2, radio=tam * 0.16)
            elif es_clave and resalte != "color" and i not in tachar:
                extra += _trazo(-w / 2, tam * 0.16, w, max(3.0, tam * 0.12),
                                acento, d0 + 0.05)
            # el numero de una cita («Salmo 68») no sube contando: es una cita
            ficha = (contador(palabra) if cifra and not (
                i > 0 and citas.es_libro(vistas[i - 1])) else None)
            if ficha:
                c1 = min(max(d1, d0 + 0.5), d0 + 1.2, max(d0 + 0.2, hasta_t - 0.05))
                pasos = _pasos_contador(ficha, d0, c1)
                cuerpo = (f'<text x="0" y="0" {letra} fill="{relleno}" '
                          f'fill-opacity="{APAGADA}">{_escapar(palabra)}'
                          f'<set attributeName="visibility" to="hidden" '
                          f'begin="{d0:.2f}s"/></text>')
                for n, (texto, t) in enumerate(pasos):
                    cierre = (f'<set attributeName="visibility" to="hidden" '
                              f'begin="{pasos[n + 1][1]:.2f}s"/>'
                              if n + 1 < len(pasos) else "")
                    cuerpo += (f'<text x="0" y="0" {letra} fill="{relleno}" '
                               f'visibility="hidden">{_escapar(texto)}'
                               f'<set attributeName="visibility" to="visible" '
                               f'begin="{t:.2f}s"/>{cierre}</text>')
                inicio_pop = c1
            else:
                cuerpo = (f'<text x="0" y="0" {letra} fill="{relleno}" '
                          f'fill-opacity="{APAGADA}">{_escapar(palabra)}'
                          f'<set attributeName="fill-opacity" to="1" '
                          f'begin="{d0:.2f}s"/>')
                if i in tachar:
                    raya = max(d0, min(d0 + (d1 - d0) * 0.4, hasta_t - 0.4))
                    cuerpo += (f'<set attributeName="fill-opacity" to="0.6" '
                               f'begin="{raya + 0.25:.2f}s"/>')
                cuerpo += '</text>'
                inicio_pop = d0
            if i in tachar:
                # se dibuja MIENTRAS se dice: si es la ultima del trozo, al
                # acabar de decirla el trozo ya se ha ido
                raya = max(d0, min(d0 + (d1 - d0) * 0.4, hasta_t - 0.4))
                cuerpo += _trazo(-w / 2 - tam * 0.1, -tam * 0.42,
                                 w + tam * 0.2, max(4.0, tam * 0.13), ROJO,
                                 raya, dur=0.25, giro=-4)
            piezas.append(f'<g transform="translate({x + w / 2:.1f} {y:.1f})">'
                          f'<g>{extra}{cuerpo}{_pop(inicio_pop, fuerza)}</g></g>')
            x += w + espacio
    sube = (f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 {tam * 0.25:.0f};0 0" dur="0.14s" '
            f'begin="{desde_t:.2f}s" fill="freeze"/>')
    entrada = (f'<set attributeName="opacity" to="1" begin="{desde_t:.2f}s"/>'
               f'<set attributeName="opacity" to="0" begin="{hasta_t:.2f}s"/>')
    return f'<g opacity="0"><g>{"".join(piezas)}{sube}</g>{entrada}</g>'


def _sin_primeras(trozo, n):
    """El trozo preparado sin sus `n` primeras palabras (o None si no queda)."""
    vistas = list(trozo.get("vistas") or [])
    if n >= len(vistas):
        return None
    tiempos = list(trozo.get("palabras") or [])
    if len(tiempos) != len(vistas):
        tiempos = repartir(len(vistas), trozo["desde"], trozo["hasta"])
    clave = trozo.get("clave")
    return dict(trozo, vistas=vistas[n:], palabras=tiempos[n:],
                texto=" ".join(vistas[n:]),
                desde=round(float(tiempos[n][0]), 3),
                clave=(clave - n) if clave is not None and clave >= n else None,
                tachar={k - n for k in (trozo.get("tachar") or ()) if k >= n})


def _juntar(a, b):
    """Dos trozos preparados en uno (a delante)."""
    def tiempos(t):
        lista = list(t.get("palabras") or [])
        return lista if len(lista) == len(t["vistas"]) else repartir(
            len(t["vistas"]), t["desde"], t["hasta"])
    n = len(a["vistas"])
    clave = (b["clave"] + n if b.get("clave") is not None else a.get("clave"))
    return dict(b, vistas=a["vistas"] + b["vistas"],
                palabras=tiempos(a) + tiempos(b),
                texto=" ".join(a["vistas"] + b["vistas"]),
                desde=a["desde"], clave=clave,
                tachar=set(a.get("tachar") or ()) | {k + n for k in (b.get("tachar") or ())})


def tras_el_cartel(trozos, fin, dichas=None):
    """Los trozos que quedan cuando el cartel se va (no se subtitula debajo).

    Con `dichas` (cuantas palabras dichas ensena el cartel) se quitan ESAS
    palabras y nada mas: lo que viene detras sale aunque la voz lo diga
    mientras el cartel se desvanece (antes se perdia el «No» de «… Jesús? No
    fue…»). Sin `dichas` (cartel escrito a mano) se quita lo que cae debajo.
    """
    salida = []
    if dichas:
        quedan, pendiente = int(dichas), None
        for trozo in trozos:
            cuantas = len(trozo.get("vistas") or str(trozo.get("texto") or "").split())
            if quedan >= cuantas:
                quedan -= cuantas
                continue
            if quedan:
                trozo = _sin_primeras(trozo, quedan)
                quedan = 0
            if trozo and not salida and not pendiente and len(trozo["vistas"]) <= 2:
                # lo que sobra de un trozo (el «No» de «… Jesús? No fue…»)
                # no sale solo: se pega delante del siguiente
                pendiente = trozo
                continue
            if trozo and pendiente:
                trozo = _juntar(pendiente, trozo)
                pendiente = None
            if trozo:
                desde = max(float(trozo["desde"]), fin - 0.3)
                if float(trozo["hasta"]) > desde + 0.15:
                    salida.append(dict(trozo, desde=round(desde, 3)))
        if pendiente:                       # no habia siguiente: sale solo
            salida.append(dict(pendiente, desde=round(
                max(float(pendiente["desde"]), fin - 0.3), 3)))
        return salida
    for trozo in trozos:
        if float(trozo["hasta"]) <= fin + 0.15:
            continue
        if float(trozo["desde"]) < fin:
            trozo = dict(trozo, desde=round(fin, 3))
        salida.append(trozo)
    return salida


def repartir(cuantas, desde, hasta):
    """Tiempos iguales para `cuantas` palabras entre desde y hasta."""
    cuantas = max(1, int(cuantas))
    paso = max(0.0, float(hasta) - float(desde)) / cuantas
    return [(round(float(desde) + paso * i, 3),
             round(float(desde) + paso * (i + 1), 3)) for i in range(cuantas)]
