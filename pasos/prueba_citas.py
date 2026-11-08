"""
Prueba de las CITAS BIBLICAS dichas (pasos/citas.py) y de donde se usan.

  1. se reconocen en todas las formas en que se dicen (letras, cifras, con y
     sin «capitulo»/«versiculo», hasta el Salmo 119) y no se confunden con un
     nombre de persona («Pedro tres veces...»);
  2. los subtitulos las escriben «Lucas 24:6» sin partirlas en dos renglones;
  3. el numero de una cita no sube contando;
  4. el motion graphics saca la tarjeta con cualquier numero.

    python pasos/prueba_citas.py
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "pasos"))

import citas  # noqa: E402
import motion  # noqa: E402
import subtitulos  # noqa: E402

_fallos = []


def igual(obtenido, esperado, mensaje):
    if obtenido != esperado:
        _fallos.append(mensaje)
        print(f"    FALLO: {mensaje} (obtenido {obtenido!r}, esperado {esperado!r})")
    else:
        print(f"  ok   {mensaje}")


def _citas(texto):
    return [c["cita"] for c in citas.buscar(texto.split())]


def _escena(texto):
    w = texto.split()
    return {"narracion": texto, "marcas": [[i * 0.3, i * 0.3 + 0.25] for i in range(len(w))],
            "t_in": 0, "t_out": len(w) * 0.3}


def main():
    print("\n  RECONOCER LA CITA")
    for texto, esperado in (
            ("Como dice Lucas, capítulo veinticuatro, versículo seis: no está aquí.",
             ["Lucas 24:6"]),
            ("El Salmo sesenta y ocho lo dice.", ["Salmo 68"]),
            ("Mateo veintisiete, versículo cuarenta y seis.", ["Mateo 27:46"]),
            ("Salmos veintidós, siete y ocho.", ["Salmos 22:7-8"]),
            ("Mateo 27 versículo 46 y la gente", ["Mateo 27:46"]),
            ("Juan 3:16 dice", ["Juan 3:16"]),
            ("primera de Corintios trece, cuatro", ["1 Corintios 13:4"]),
            ("Salmo ciento diecinueve, versículo ciento cinco", ["Salmo 119:105"]),
            ("Pedro tres veces lo negó.", []),
            ("Juan, uno de los doce, lo vio.", [])):
        igual(_citas(texto), esperado, f"«{texto[:44]}»")

    print("\n  EN LOS SUBTITULOS")
    trozos = subtitulos.de_escena(_escena(
        "Como dice Lucas, capítulo veinticuatro, versículo seis: no está aquí."),
        cap_linea=16, cap_trozo=16, con_palabras=True)
    textos = [t["texto"] for t in trozos]
    igual("Lucas 24:6" in textos, True, f"la cita entera en un renglón: {textos}")
    igual(all(len(t["palabras"]) == len(t["texto"].split()) for t in trozos), True,
          "cada palabra dibujada con su tiempo")
    igual(subtitulos.limpiar_texto("El Salmo sesenta y ocho lo dice.".split()),
          "El Salmo 68 lo dice.", "un salmo sin versículo")
    igual(subtitulos.limpiar_texto("Eran cinco mil hombres.".split()),
          "Eran 5000 hombres.", "las cifras normales siguen igual")

    print("\n  NO CUENTA")
    import gancho  # noqa: PLC0415
    igual(citas.es_libro("Salmo") and not citas.es_libro("hombres"), True,
          "sabe qué es un libro (el contador no sube tras un libro)")
    igual(gancho.contador("24:6"), None, "«24:6» no es una cifra que suba")

    print("\n  EN EL MOTION GRAPHICS")
    voz = motion.Voz({"narracion": "Como dice Mateo veintisiete, versículo cuarenta y "
                                   "seis: «Dios mío, ¿por qué me has desamparado?»",
                      "t_in": 0, "t_out": 8})
    igual((motion.cita_de(voz) or {}).get("ref"), "Mateo 27:46",
          "tarjeta de versículo con números mayores de 24")

    print("\n" + "=" * 60)
    if _fallos:
        print(f"CITAS CON FALLOS: {len(_fallos)}")
        return 1
    print("CITAS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
