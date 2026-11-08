"""Las CITAS BIBLICAS dichas en voz alta, reconocidas en las palabras del plano.

QUE PROBLEMA RESUELVE (8-nov-2026, David)
-----------------------------------------
El guion va con todo escrito en letra (lo locuta un sintetizador), y en
pantalla los numeros dichos se convierten en cifras y SUBEN contando
(`gancho.contador`). Con una cita eso salia mal de tres formas:

  - «Salmo sesenta y ocho» -> un «68» que corria de 0 a 68 sin decir que era;
  - «Lucas, capitulo veinticuatro, versiculo seis» -> «Lucas, capitulo 24,
    versiculo 6», con dos contadores y sin parecer una cita;
  - el motion graphics solo entendia numeros hasta el 24 y siempre con
    versiculo: «Mateo veintisiete, versiculo cuarenta y seis» no salia.

Aqui se reconoce la cita entera -- libro, capitulo, versiculo(s) -- en
cualquiera de las formas en que se dice, y se escribe como se escribe una
cita: «Lucas 24:6», «Salmo 22:7-8», «Salmo 68», «1 Corintios 13:4». Los
subtitulos dibujan el libro tal cual y el resto como UNA pieza («24:6») que no
cuenta; el motion graphics la usa para su tarjeta de versiculo.

    buscar(palabras)  -> [ficha] de cada cita, con indices de palabra
    es_libro(palabra) -> True si la palabra es el nombre de un libro
"""
import re
import unicodedata

#: libro plegado -> como se escribe
LIBROS = {
    "genesis": "Génesis", "exodo": "Éxodo", "levitico": "Levítico",
    "numeros": "Números", "deuteronomio": "Deuteronomio", "josue": "Josué",
    "jueces": "Jueces", "rut": "Rut", "samuel": "Samuel", "reyes": "Reyes",
    "cronicas": "Crónicas", "esdras": "Esdras", "nehemias": "Nehemías",
    "ester": "Ester", "job": "Job", "salmos": "Salmos", "salmo": "Salmo",
    "proverbios": "Proverbios", "eclesiastes": "Eclesiastés",
    "cantares": "Cantares", "isaias": "Isaías", "jeremias": "Jeremías",
    "lamentaciones": "Lamentaciones", "ezequiel": "Ezequiel", "daniel": "Daniel",
    "oseas": "Oseas", "joel": "Joel", "amos": "Amós", "abdias": "Abdías",
    "jonas": "Jonás", "miqueas": "Miqueas", "nahum": "Nahúm",
    "habacuc": "Habacuc", "sofonias": "Sofonías", "hageo": "Hageo",
    "zacarias": "Zacarías", "malaquias": "Malaquías", "mateo": "Mateo",
    "marcos": "Marcos", "lucas": "Lucas", "juan": "Juan", "hechos": "Hechos",
    "romanos": "Romanos", "corintios": "Corintios", "galatas": "Gálatas",
    "efesios": "Efesios", "filipenses": "Filipenses",
    "colosenses": "Colosenses", "tesalonicenses": "Tesalonicenses",
    "timoteo": "Timoteo", "tito": "Tito", "filemon": "Filemón",
    "hebreos": "Hebreos", "santiago": "Santiago", "pedro": "Pedro",
    "judas": "Judas", "apocalipsis": "Apocalipsis",
}

#: Libros que tambien son NOMBRES DE PERSONA («Pedro tres veces lo nego»,
#: «Juan doce», «Hechos dos» es otra cosa). Con ellos hace falta algo mas que
#: un numero detras: «capitulo»/«versiculo», o capitulo Y versiculo.
NOMBRES_DE_PERSONA = {"samuel", "job", "daniel", "amos", "jonas", "mateo",
                      "marcos", "lucas", "juan", "santiago", "pedro", "judas",
                      "timoteo", "tito", "rut", "ester", "josue", "joel",
                      "esdras", "nehemias", "isaias", "jeremias", "ezequiel",
                      "oseas", "miqueas", "zacarias", "malaquias", "hechos",
                      "numeros", "jueces", "reyes"}

ORDINALES = {"1": 1, "2": 2, "3": 3, "primera": 1, "primer": 1, "primero": 1,
             "segunda": 2, "segundo": 2, "tercera": 3, "tercer": 3, "tercero": 3}

CAPITULO = {"capitulo", "cap", "capitulos"}
VERSICULO = {"versiculo", "versiculos", "verso", "versos", "vers", "v"}
HASTA = {"y", "al", "a", "hasta"}

UNIDADES = {"cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3,
            "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8,
            "nueve": 9}
ESPECIALES = {"diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14,
              "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18,
              "diecinueve": 19, "veinte": 20, "veintiun": 21, "veintiuno": 21,
              "veintiuna": 21, "veintidos": 22, "veintitres": 23,
              "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
              "veintisiete": 27, "veintiocho": 28, "veintinueve": 29}
DECENAS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
           "setenta": 70, "ochenta": 80, "noventa": 90}

_DIGITOS = re.compile(r"^(\d{1,3})(?::(\d{1,3})(?:[-–](\d{1,3}))?)?$")


def plegar(palabra):
    """minusculas, sin tildes y sin signos (los dos puntos de «3:16» quedan)."""
    texto = unicodedata.normalize("NFD", str(palabra or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9:–-]+", "", texto).strip(":-–")


def es_libro(palabra):
    return plegar(palabra) in LIBROS


def _numero(plegadas, i):
    """Un numero dicho desde i (hasta 199) o en cifras. -> (valor, siguiente)|None"""
    if i >= len(plegadas):
        return None
    w = plegadas[i]
    if w.isdigit():
        return int(w), i + 1
    total, j = 0, i
    if w in ("cien", "ciento"):
        total, j = 100, i + 1
        if w == "cien" or j >= len(plegadas):
            return total, j
        w = plegadas[j]
    if w in ESPECIALES:
        return total + ESPECIALES[w], j + 1
    if w in DECENAS:
        total += DECENAS[w]
        j += 1
        if (j + 1 < len(plegadas) and plegadas[j] == "y"
                and plegadas[j + 1] in UNIDADES):
            total += UNIDADES[plegadas[j + 1]]
            j += 2
        return total, j
    if w in UNIDADES:
        return total + UNIDADES[w], j + 1
    return (total, j) if total else None


def _libro_en(plegadas, i):
    """(orden, libro, siguiente) si en i empieza un libro, o None."""
    orden = None
    j = i
    if plegadas[j] in ORDINALES and j + 1 < len(plegadas):
        k = j + 1 + (1 if plegadas[j + 1] == "de" else 0)
        if k < len(plegadas) and plegadas[k] in LIBROS:
            orden, j = ORDINALES[plegadas[j]], k
    if plegadas[j] not in LIBROS:
        return None
    return orden, plegadas[j], j + 1


def buscar(palabras):
    """Las citas de una lista de palabras (crudas, tal como se dicen).

    -> [{"inicio", "libro_fin", "fin", "libro", "orden", "cap", "v1", "v2",
         "ref" ("24:6"), "cita" ("Lucas 24:6")}] con indices de palabra:
    [inicio, libro_fin) es el libro y [libro_fin, fin) los numeros.
    """
    plegadas = [plegar(p) for p in (palabras or [])]
    salida, i = [], 0
    while i < len(plegadas):
        libro = _libro_en(plegadas, i) if plegadas[i] else None
        if not libro:
            i += 1
            continue
        orden, nombre, j = libro
        ficha = _cita_tras(plegadas, j, nombre)
        if not ficha:
            i += 1
            continue
        cap, v1, v2, fin = ficha
        ref = f"{cap}" + (f":{v1}" if v1 else "") + (f"-{v2}" if v2 else "")
        escrito = LIBROS[nombre]
        salida.append({
            "inicio": i, "libro_fin": j, "fin": fin, "libro": escrito,
            "orden": orden, "cap": cap, "v1": v1, "v2": v2, "ref": ref,
            "cita": (f"{orden} " if orden else "") + f"{escrito} {ref}"})
        i = fin
    return salida


def _cita_tras(plegadas, j, libro):
    """Capitulo y versiculos detras del libro. -> (cap, v1, v2, fin)|None"""
    n = len(plegadas)
    if j >= n:
        return None
    # «Juan 3:16», «Juan 3:16-18» en un solo token
    m = _DIGITOS.match(plegadas[j])
    if m and m.group(2):
        cap, v1 = int(m.group(1)), int(m.group(2))
        v2 = int(m.group(3)) if m.group(3) else None
        fin = j + 1
        if not v2 and fin + 1 < n and plegadas[fin] in HASTA:
            otro = _numero(plegadas, fin + 1)
            if otro and otro[0] > v1:
                v2, fin = otro[0], otro[1]
        return cap, v1, v2, fin
    con_palabra = False
    if plegadas[j] in CAPITULO:
        con_palabra, j = True, j + 1
    primero = _numero(plegadas, j)
    if not primero or not 0 < primero[0] <= 150:
        return None
    cap, k = primero
    v1 = v2 = None
    marca_vers = k < n and plegadas[k] in VERSICULO
    if marca_vers:
        con_palabra = True
        k += 1
    segundo = _numero(plegadas, k)
    if segundo and 0 < segundo[0] <= 176:
        v1, k = segundo
        if k + 1 < n and plegadas[k] in HASTA:
            tercero = _numero(plegadas, k + 1)
            if tercero and v1 < tercero[0] <= 176:
                v2, k = tercero
    elif marca_vers:
        return None                      # «versiculo» sin numero: no es cita
    if v1 is None and not con_palabra and libro in NOMBRES_DE_PERSONA:
        return None                      # «Pedro tres veces...»
    return cap, v1, v2, k
