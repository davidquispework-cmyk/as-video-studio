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
"""
import re

#: Cuanto dura el cartel grande del principio, en segundos.
DURACION_S = 3.0

#: Color de la palabra clave y de las cifras si la paleta no trae acento.
AMARILLO = "#FFD23F"

#: Cuanto mas grande va una cifra que el resto del subtitulo.
ESCALA_CIFRA = 1.45

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
        if len(llana) < 4 or llana in _VACIAS:
            continue
        valor = len(llana) + (3 if i > 0 and str(palabra)[:1].isupper() else 0)
        if valor > puntos:
            mejor, puntos = i, valor
    return mejor


def texto_de(narracion, propio=None, max_palabras=8):
    """El texto del cartel grande. -> str ('' = sin cartel)

    Con `propio` (el param o el de la escena) va ese. Si no, la primera frase
    del guion: si es una pregunta, hasta el «?»; si es corta, entera; si es
    larga, «¿Sabías…?» y sus primeras palabras, que es justo el gancho.
    """
    if isinstance(propio, str) and propio.strip():
        return " ".join(propio.split())
    texto = " ".join(str(narracion or "").split())
    if not texto:
        return ""
    pregunta = re.match(r"\s*(¿[^?]{2,120}\?)", texto)
    if pregunta and len(pregunta.group(1).split()) <= max_palabras + 2:
        return pregunta.group(1)
    frase = re.split(r"(?<=[.!?…:;])\s", texto, maxsplit=1)[0].rstrip(".:;")
    palabras = frase.split()
    if len(palabras) <= max_palabras:
        return frase
    if re.match(r"(?i)¿?sab[ií]as", frase):
        return " ".join(palabras[:max_palabras]).rstrip(",") + "…?"
    return "¿Sabías esto? " + " ".join(palabras[:5]).rstrip(",") + "…"


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


def svg_cartel(texto, salida, medidor, fuente="Verdana", acento=AMARILLO,
               duracion=DURACION_S):
    """El cartel grande de los primeros segundos: destello, golpe y fuera.

    `medidor(tam)` devuelve una funcion que mide texto a ese cuerpo (la de p7,
    con la fuente de verdad). Las letras van en MAYUSCULAS y la palabra clave
    en el color de acento. Arriba del centro, para no pisar el subtitulo.
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
    salto = tam * 1.12
    cx = ancho / 2.0
    cy = alto * (0.36 if alto > ancho else 0.40)
    arriba = cy - salto * (len(lineas) - 1) / 2.0
    piezas = []
    caja_ancho = largo + tam * 0.9
    caja_alto = salto * len(lineas) + tam * 0.5
    piezas.append(
        f'<rect x="{-caja_ancho / 2:.0f}" y="{arriba - cy - tam * 0.95:.0f}" '
        f'width="{caja_ancho:.0f}" height="{caja_alto:.0f}" rx="{tam * 0.25:.0f}" '
        f'fill="#000000" opacity="0.55"/>')
    n = 0
    for indice, linea in enumerate(lineas):
        trozos = []
        for palabra in linea:
            color = acento if n == clave else "#ffffff"
            trozos.append(f'<tspan fill="{color}">{_escapar(palabra)}</tspan>')
            n += 1
        piezas.append(
            f'<text x="0" y="{arriba - cy + salto * indice:.0f}" '
            f'font-family="{fuente}" font-size="{tam}" font-weight="900" '
            f'text-anchor="middle" stroke="#000000" '
            f'stroke-width="{max(2, tam // 14)}" paint-order="stroke">'
            f'{" ".join(trozos)}</text>')
    fin = max(0.3, duracion - 0.3)
    golpe = ('<animateTransform attributeName="transform" type="scale" '
             'values="1.6;0.94;1.04;1" keyTimes="0;0.55;0.8;1" dur="0.45s" '
             'begin="0s" fill="freeze"/>')
    salida_anim = (f'<animate attributeName="opacity" from="1" to="0" '
                   f'begin="{fin:.2f}s" dur="0.3s" fill="freeze"/>')
    destello = (f'<rect x="0" y="0" width="{ancho}" height="{alto}" '
                f'fill="#ffffff" opacity="0">'
                f'<animate attributeName="opacity" values="0.85;0" '
                f'dur="0.35s" begin="0s" fill="freeze"/></rect>')
    return (f'<g class="gancho">{destello}'
            f'<g transform="translate({cx:.0f} {cy:.0f})">'
            f'<g>{"".join(piezas)}{golpe}</g>{salida_anim}</g></g>')


def bloque_palabras(trozo, banda, tam, medir, fuente="Verdana", peso=600,
                    color="#ffffff", acento=AMARILLO, opacidad=0.4, radio=0,
                    partir=None):
    """Un trozo de subtitulo que se enciende PALABRA A PALABRA.

    Las palabras del trozo estan desde que entra, apagadas, y cada una se pone
    blanca cuando se dice (con los tiempos de `trozo["palabras"]`). La palabra
    clave va en el color de acento y las cifras, ademas, mas grandes. Misma
    caja y misma banda que el subtitulo de siempre (p7.bloque_subtitulo).
    """
    texto = str(trozo.get("texto") or "")
    if not texto.strip():
        return ""
    partir = partir or (lambda t, m, a: [t])
    lineas = partir(texto, medir, banda["ancho"]) or [texto]
    todas = texto.split()
    tiempos = list(trozo.get("palabras") or [])
    if len(tiempos) != len(todas):
        tiempos = repartir(len(todas), trozo["desde"], trozo["hasta"])
    clave = palabra_clave(todas)
    hay_cifra = any(es_cifra(x) for x in todas)
    salto = int(tam * (1.28 + (0.3 if hay_cifra else 0)))
    base = float(banda["suelo"]) - salto * (len(lineas) - 1)
    centro = float(banda["centro"])

    def ancho_de(linea):
        extra = sum(medir(x) * (ESCALA_CIFRA - 1) for x in linea.split()
                    if es_cifra(x))
        return medir(linea) + extra

    ancho_texto = max(ancho_de(x) for x in lineas)
    ancho_caja = ancho_texto + 2 * tam * 0.38
    subida = tam * (ESCALA_CIFRA - 1) * 0.8 if hay_cifra else 0
    arriba = base - tam * 0.96 - subida
    alto_caja = salto * (len(lineas) - 1) + tam * 1.36 + subida
    piezas = [f'<rect x="{centro - ancho_caja / 2:.0f}" y="{arriba:.0f}" '
              f'width="{ancho_caja:.0f}" height="{alto_caja:.0f}" '
              f'rx="{radio:.0f}" ry="{radio:.0f}" fill="#000000" '
              f'opacity="{opacidad:g}"/>']
    n = 0
    for indice, linea in enumerate(lineas):
        trozos = []
        for palabra in linea.split():
            desde = max(0.0, float(tiempos[n][0]) if n < len(tiempos)
                        else float(trozo["desde"]))
            relleno = acento if (n == clave or es_cifra(palabra)) else color
            cuerpo = (f' font-size="{int(tam * ESCALA_CIFRA)}"'
                      if es_cifra(palabra) else "")
            trozos.append(
                f'<tspan fill="{relleno}" fill-opacity="{APAGADA}"{cuerpo}>'
                f'{_escapar(palabra)}'
                f'<set attributeName="fill-opacity" to="1" '
                f'begin="{desde:.2f}s"/></tspan>')
            n += 1
        piezas.append(
            f'<text x="{centro:.0f}" y="{base + salto * indice:.0f}" '
            f'font-family="{fuente}" font-size="{tam}" font-weight="{peso}" '
            f'text-anchor="middle">{" ".join(trozos)}</text>')
    entrada = (f'<set attributeName="opacity" to="1" '
               f'begin="{float(trozo["desde"]):.2f}s"/>'
               f'<set attributeName="opacity" to="0" '
               f'begin="{float(trozo["hasta"]):.2f}s"/>')
    return f'<g opacity="0">{"".join(piezas)}{entrada}</g>'


def repartir(cuantas, desde, hasta):
    """Tiempos iguales para `cuantas` palabras entre desde y hasta."""
    cuantas = max(1, int(cuantas))
    paso = max(0.0, float(hasta) - float(desde)) / cuantas
    return [(round(float(desde) + paso * i, 3),
             round(float(desde) + paso * (i + 1), 3)) for i in range(cuantas)]
