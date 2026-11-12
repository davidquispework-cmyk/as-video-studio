"""LA FÓRMULA DE LAS REFERENCIAS (P8 del plan «NIVEL PROFESIONAL», 12-nov-2026).

Lo que hacen los vídeos de referencia de David (Drive → «IMAGENES DE IDEAS DE
TIKTOK»), puesto como pauta en el encargo del guion:

  - gancho en el primer segundo (pregunta, algo que contradice lo sabido, o el
    FINAL primero y luego «hay que retroceder»);
  - UNA historia + UN dato que casi nadie sabe;
  - algo que se repite y una frase que cierra el círculo;
  - en un vídeo bíblico, el cierre en ESPEJO con Jesús;
  - un final que pide algo, y lo propio de David: «el reto de esta semana»;
  - si el encargo dice que es parte de una serie, «Parte N» y el próximo.

Es SOLO TEXTO DEL ENCARGO (como `intencion.pauta_ritmo` o
`fidelidad.pauta_guion`): no es un param, no mueve la firma del guion y los
proyectos guardados no quedan obsoletos. Cambia el siguiente guion que se
redacte.

Se apaga con `ESTUDIO_FORMULA=no`; el reto solo, escribiendo «sin reto» en el
encargo. Si el vídeo ya tiene una llamada final propia (casilla «cta_final»),
el final que pide algo es ESA y aquí no se pide otra.
"""
import os
import re
import unicodedata

_NUMEROS = {"uno": 1, "primera": 1, "primer": 1, "primero": 1, "dos": 2,
            "segunda": 2, "segundo": 2, "tres": 3, "tercera": 3, "tercer": 3,
            "tercero": 3, "cuatro": 4, "cuarta": 4, "cuarto": 4, "cinco": 5,
            "quinta": 5, "quinto": 5, "seis": 6, "sexta": 6, "sexto": 6,
            "siete": 7, "septima": 7, "septimo": 7, "ocho": 8, "octava": 8,
            "octavo": 8, "nueve": 9, "novena": 9, "noveno": 9, "diez": 10,
            "decima": 10, "decimo": 10}

_PARTE = re.compile(
    r"\b(?:parte|episodio|ep\.|entrega)\s*(?:n[o.º]?\s*)?"
    r"(\d{1,3}|" + "|".join(_NUMEROS) + r")\b")
# «serie: Los jueces» o «serie «Los jueces»»; «una serie de milagros» NO.
_SERIE = re.compile(r"\bserie\s*[:«\"]\s*([^\n.,;»\"]{3,60})")
_SIN_RETO = re.compile(r"\bsin\s+reto\b")


def _plegar(texto):
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def activa():
    return os.environ.get("ESTUDIO_FORMULA", "").strip().lower() not in (
        "no", "0", "false", "off")


def serie_de(*textos):
    """{'parte': N | None, 'nombre': str | None} si el encargo habla de una
    serie («parte 3», «serie: Los jueces»); None si no."""
    plegado = _plegar(" \n".join(str(t or "") for t in textos))
    parte = _PARTE.search(plegado)
    serie = _SERIE.search(plegado)
    if not parte and not serie:
        return None
    numero = None
    if parte:
        crudo = parte.group(1)
        numero = int(crudo) if crudo.isdigit() else _NUMEROS.get(crudo)
    nombre = None
    if serie:
        nombre = " ".join(serie.group(1).split()) or None
    return {"parte": numero, "nombre": nombre}


def pide_reto(*textos):
    return not _SIN_RETO.search(_plegar(" ".join(str(t or "") for t in textos)))


def pauta_guion(corto=False, biblico=False, encargo="", con_cta_final=False,
                titulos=()):
    """La pauta de la fórmula para el encargo del guion, o "" si está apagada."""
    if not activa():
        return ""
    lineas = [
        "== LA FÓRMULA DE LOS VÍDEOS QUE FUNCIONAN ==",
        "- GANCHO en el primer segundo, de una de estas tres formas: una "
        "pregunta, algo que contradice lo que todos creen («La túnica de José "
        "no era de colores»), o el FINAL primero y luego «para entenderlo hay "
        "que retroceder».",
        "- UNA sola historia y UN dato que casi nadie sabe (una palabra en "
        "hebreo o griego, una cifra, un detalle del texto original). El dato se "
        "anuncia pronto y se paga más adelante: es la razón de quedarse.",
        "- Algo que SE REPITE (un objeto, una frase, una cifra) y que vuelve al "
        "final para CERRAR EL CÍRCULO con una frase que remate el gancho.",
        "- Cifras dichas enteras y con peso («cuatrocientos años», «setenta "
        "monedas»): en pantalla brillan.",
    ]
    if corto:
        lineas.append(
            "- Entre 55 y 110 segundos; frases de 3 a 8 palabras casi todas.")
    if biblico:
        lineas.append(
            "- CIERRE EN ESPEJO CON JESÚS: lo que pasó en la historia, puesto al "
            "lado de lo que hizo Jesús («Abimelec mató a sus setenta hermanos "
            "para reinar; Jesús murió por sus hermanos para salvarlos»). Una o "
            "dos frases, sin sermón, y fiel al texto bíblico.")
    if con_cta_final:
        lineas.append(
            "- El FINAL pide algo: es la llamada final que ya está encargada "
            "arriba; no añadas otra.")
    else:
        lineas.append(
            "- El FINAL pide algo concreto a quien mira: «envíaselo a ese amigo "
            "que…», «¿tú cómo te lo imaginabas? Te leo en los comentarios», o "
            "el próximo vídeo de la serie. Una sola cosa, en una frase.")
        if biblico and pide_reto(encargo):
            lineas.append(
                "- Y justo antes, «EL RETO DE ESTA SEMANA»: una acción pequeña y "
                "concreta que se pueda hacer de lunes a viernes, sacada de la "
                "historia («esta semana, perdona a alguien antes de que te pida "
                "perdón»). Dicho con esas palabras, en una o dos frases.")
    serie = serie_de(encargo, *titulos)
    if serie:
        nombre = f" «{serie['nombre']}»" if serie["nombre"] else ""
        if serie["parte"]:
            lineas.append(
                f"- Es la PARTE {serie['parte']} de la serie{nombre}: dilo en la "
                f"primera o segunda frase («Parte {serie['parte']}»), sin "
                "saludar, y en la última frase anuncia de qué va la siguiente "
                "parte para que la busquen.")
        else:
            lineas.append(
                f"- Es parte de una serie{nombre}: la última frase anuncia de "
                "qué va el próximo vídeo para que lo busquen.")
    return "\n".join(lineas)
