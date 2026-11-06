"""LA PLANTILLA TIKTOK / SHORTS: barra de progreso, «Sígueme» al final y golpe
de sonido al empezar.

Etapa 4 de la hoja de ruta. Se enciende con el param `tiktok` del paso
callouts (y solo si alguien lo pide: no va en los defectos, no mueve firmas):

    true                    plantilla con el texto de siempre
    "para más historias"    ese texto debajo de «SÍGUEME»
    {"seguir": "...", "barra": false, "golpe": false}   a la carta
    false / falta           como siempre

Lo que pinta va en la capa QUIETA de cada plano (p7), como el gancho: SVG con
SMIL que el render ya sabe pintar fotograma a fotograma. La barra de cada plano
va del punto del vídeo en que empieza al punto en que acaba, así que al
encadenar los clips se ve UNA barra que crece sin saltos.

El golpe de sonido es SINTÉTICO (numpy): no necesita la clave de FreeSound ni
nada del banco, así que suena también en un estudio sin claves. El render lo
lee de `movimiento.json` (`plantilla`), que escribe p7: así la plantilla es UN
solo param, en UN paso.

La duración no es cosa de este módulo: se elige al crear el vídeo (siempre algo
más de 1:00, que es lo que pide Creator Rewards) y el guion se ajusta a ella.
Aquí solo se avisa al montar si el vídeo ha salido por debajo del minuto.
"""
import math

#: Creator Rewards de TikTok solo paga vídeos de MÁS de un minuto.
MINIMO_S = 60.0

#: Duración que se propone al elegir la plantilla (con margen sobre el minuto).
PROPUESTA_S = 70

#: Cuánto antes del final aparece el «Sígueme».
SEGUIR_S = 3.5

#: Lo que va debajo de «SÍGUEME» si nadie escribe nada.
TEXTO_SEGUIR = "para más historias como esta"

#: Rosa de TikTok para el botón «+».
ROSA = "#FE2C55"

AMARILLO = "#FFD23F"


def normalizar(valor):
    """El param tal como llegue -> None (apagada) o {seguir, barra, golpe}."""
    if not valor:
        return None
    ficha = {"seguir": TEXTO_SEGUIR, "barra": True, "golpe": True}
    if isinstance(valor, str):
        ficha["seguir"] = " ".join(valor.split())[:80] or TEXTO_SEGUIR
    elif isinstance(valor, dict):
        if "seguir" in valor:
            seguir = valor.get("seguir")
            ficha["seguir"] = (False if seguir is False
                               else (" ".join(str(seguir or "").split())[:80]
                                     or TEXTO_SEGUIR))
        ficha["barra"] = valor.get("barra", True) is not False
        ficha["golpe"] = valor.get("golpe", True) is not False
    return ficha


def _escapar(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def svg_barra(salida, desde, hasta, duracion, acento=AMARILLO):
    """La barra de progreso de UN plano: de `desde` a `hasta` (0..1) en `duracion` s.

    Arriba del todo: abajo la tapan el texto y los botones de TikTok. Lleva una
    pista oscura para que se lea sobre un cielo blanco, y una cabeza redonda.
    """
    ancho, alto = salida
    grueso = max(10, round(alto * 0.008))
    x0, x1 = ancho * max(0.0, desde), ancho * min(1.0, hasta)
    dur = max(0.05, float(duracion))
    return (f'<g class="tiktok-barra">'
            f'<rect x="0" y="0" width="{ancho}" height="{grueso}" '
            f'fill="#000000" opacity="0.35"/>'
            f'<rect x="0" y="0" width="{x0:.1f}" height="{grueso}" fill="{acento}">'
            f'<animate attributeName="width" from="{x0:.1f}" to="{x1:.1f}" '
            f'dur="{dur:.3f}s" begin="0s" fill="freeze"/></rect>'
            f'<circle cx="{x0:.1f}" cy="{grueso / 2:.1f}" r="{grueso * 0.9:.1f}" '
            f'fill="#ffffff" stroke="{acento}" stroke-width="{max(2, grueso // 3)}">'
            f'<animate attributeName="cx" from="{x0:.1f}" to="{x1:.1f}" '
            f'dur="{dur:.3f}s" begin="0s" fill="freeze"/></circle></g>')


def svg_seguir(salida, texto, empieza=0.0, entra=True, acento=AMARILLO,
               fuente="Verdana"):
    """La llamada a seguir del final: botón «+», «SÍGUEME» y una línea debajo.

    `empieza` es el segundo DEL PLANO en que aparece; `entra` dice si entra con
    golpe (en este plano empieza) o ya estaba (viene del plano anterior).
    """
    ancho, alto = salida
    base = min(ancho, alto)
    tam = int(base * 0.12)
    sub = int(base * 0.052)
    radio = int(base * 0.075)
    cx = ancho / 2.0
    cy = alto * (0.40 if alto > ancho else 0.42)
    texto = " ".join(str(texto or "").split())
    caja_ancho = max(tam * 4.6, len(texto) * sub * 0.58) + tam * 0.6
    caja_alto = radio * 2 + tam * 1.25 + (sub * 1.6 if texto else 0) + tam * 0.6
    arriba = -radio - tam * 0.35
    piezas = [
        f'<rect x="{-caja_ancho / 2:.0f}" y="{arriba:.0f}" width="{caja_ancho:.0f}" '
        f'height="{caja_alto:.0f}" rx="{tam * 0.35:.0f}" fill="#000000" opacity="0.6"/>',
        # el botón: aro blanco, círculo rosa y la cruz
        f'<g transform="translate(0 {radio * 0.15:.0f})">'
        f'<circle r="{radio}" fill="{ROSA}" stroke="#ffffff" '
        f'stroke-width="{max(4, radio // 8)}"/>'
        f'<rect x="{-radio * 0.5:.0f}" y="{-radio * 0.11:.0f}" width="{radio:.0f}" '
        f'height="{radio * 0.22:.0f}" rx="{radio * 0.08:.0f}" fill="#ffffff"/>'
        f'<rect x="{-radio * 0.11:.0f}" y="{-radio * 0.5:.0f}" width="{radio * 0.22:.0f}" '
        f'height="{radio:.0f}" rx="{radio * 0.08:.0f}" fill="#ffffff"/>'
        f'<animateTransform attributeName="transform" type="scale" additive="sum" '
        f'values="1;1.12;1" dur="0.9s" begin="{empieza + 0.5:.2f}s" '
        f'repeatCount="indefinite"/></g>',
        f'<text x="0" y="{radio + tam * 1.05:.0f}" font-family="{fuente}" '
        f'font-size="{tam}" font-weight="900" text-anchor="middle" fill="#ffffff" '
        f'stroke="#000000" stroke-width="{max(2, tam // 14)}" '
        f'paint-order="stroke">SÍGUEME</text>',
    ]
    if texto:
        piezas.append(
            f'<text x="0" y="{radio + tam * 1.05 + sub * 1.5:.0f}" '
            f'font-family="{fuente}" font-size="{sub}" font-weight="700" '
            f'text-anchor="middle" fill="{acento}">{_escapar(texto)}</text>')
    interior = "".join(piezas)
    if not entra:
        return (f'<g class="tiktok-seguir" transform="translate({cx:.0f} {cy:.0f})">'
                f'{interior}</g>')
    golpe = (f'<animateTransform attributeName="transform" type="scale" '
             f'values="0.2;1.12;0.96;1" keyTimes="0;0.5;0.8;1" dur="0.5s" '
             f'begin="{empieza:.2f}s" fill="freeze"/>')
    return (f'<g class="tiktok-seguir" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{empieza:.2f}s" fill="freeze"/>'
            f'<g transform="translate({cx:.0f} {cy:.0f})"><g>{interior}{golpe}</g></g></g>')


def piezas_de_plano(escena, ficha, salida, inicio_video, fin_video,
                    acento=AMARILLO, fuente="Verdana"):
    """Lo que la plantilla pinta encima de UN plano. -> str (SVG sin envolver)."""
    if not ficha:
        return ""
    try:
        t_in, t_out = float(escena.get("t_in") or 0), float(escena.get("t_out") or 0)
    except (TypeError, ValueError):
        return ""
    total = float(fin_video) - float(inicio_video)
    if total <= 0 or t_out <= t_in:
        return ""
    piezas = []
    if ficha.get("barra", True):
        piezas.append(svg_barra(salida, (t_in - inicio_video) / total,
                                (t_out - inicio_video) / total, t_out - t_in,
                                acento))
    if ficha.get("seguir") is not False:
        aparece = max(float(inicio_video), float(fin_video) - SEGUIR_S)
        if t_out > aparece + 0.05:
            entra = aparece >= t_in
            piezas.append(svg_seguir(salida, ficha.get("seguir") or "",
                                     empieza=max(0.0, aparece - t_in) if entra else 0.0,
                                     entra=entra, acento=acento, fuente=fuente))
    return "".join(piezas)


def incrustar(svg, piezas):
    """Mete `piezas` al final de una capa SVG ya envuelta (encima de todo)."""
    if not piezas:
        return svg
    corte = svg.rfind("</svg>")
    if corte < 0:
        return svg
    return svg[:corte] + piezas + svg[corte:]


# ------------------------------------------------------------------ el golpe

def golpe(frecuencia=48000):
    """El golpe del principio: impacto grave + chasquido + barrido que se apaga.

    -> numpy float32 (n, 2), pico 1. Sintético y siempre igual (semilla fija).
    Coincide con el destello del gancho (t = 0).
    """
    import numpy as np                                  # noqa: PLC0415
    n = int(frecuencia * 1.1)
    t = np.arange(n, dtype=np.float32) / frecuencia
    # impacto grave: seno que cae de 90 a 42 Hz con decaimiento rapido
    f = 42.0 + 48.0 * np.exp(-t * 9.0)
    fase = 2 * math.pi * np.cumsum(f) / frecuencia
    grave = np.sin(fase) * np.exp(-t * 5.5)
    rng = np.random.default_rng(119105)
    ruido = rng.standard_normal(n).astype(np.float32)
    # chasquido: ruido muy corto
    chasquido = ruido * np.exp(-t * 90.0) * 0.6
    # barrido: ruido suavizado (paso bajo que se va cerrando) que se apaga
    suave = np.convolve(ruido, np.ones(24, dtype=np.float32) / 24, mode="same")
    barrido = suave * np.exp(-t * 3.2) * (1 - np.exp(-t * 40.0)) * 1.4
    mono = grave * 0.9 + chasquido + barrido
    mono[-int(frecuencia * 0.05):] *= np.linspace(1, 0, int(frecuencia * 0.05))
    pico = float(np.max(np.abs(mono))) or 1.0
    mono = (mono / pico).astype(np.float32)
    # un pelín de anchura: el barrido algo distinto en cada lado
    der = np.roll(mono, 37)
    return np.stack([mono, der], axis=1)


def aviso_duracion(segundos):
    """Texto de aviso si el vídeo no llega al minuto de Creator Rewards, o None."""
    try:
        s = float(segundos)
    except (TypeError, ValueError):
        return None
    if s > MINIMO_S:
        return None
    return (f"el vídeo dura {int(s) // 60}:{int(s) % 60:02d} y TikTok solo paga "
            f"(Creator Rewards) vídeos de MÁS de 1:00. Sube la duración objetivo "
            f"en «El encargo» y regenera el guion, o alarga el guion a mano.")
