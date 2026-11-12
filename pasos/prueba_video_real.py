"""Los fallos vistos en un video REAL (Epafrodito, motion graphics, voz
gratuita; 12-nov-2026). Sin red y sin gastar nada.

    python pasos/prueba_video_real.py

1. La voz gratuita devolvia las palabras SIN signos: el gancho juntaba dos
   frases y cortaba en «SU». -> marcas_tts.puntuar / puntuar_escenas, gancho.
2. «Filipenses capitulo dos» | «versiculo veintisiete»: el corte partia la cita
   y salia una placa «2 VERSICULO». -> motion.cita_de con el plano de antes,
   motion.contador_de sin numeros de cita.
3. Los mismos muñecos dos veces (los de Claude y los automaticos), y el muñeco
   delante del mapa con «990 km» en la cabeza. -> motion.storyboard,
   motion._apartar_munecos.
4. Tres «SÍGUEME» al final, uno encima de la cara. -> UNA tarjeta final
   (rotulos, con la frase de la plantilla TikTok), plantilla_tiktok.sin_seguir,
   motion._sin_llamadas.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gancho  # noqa: E402
import marcas_tts  # noqa: E402
import motion  # noqa: E402
import plantilla_tiktok  # noqa: E402
import rotulos  # noqa: E402


def probar_signos():
    edge = ["Un", "hombre", "casi", "muere", "por", "llevar", "una", "entrega",
            "Casi", "nadie", "recuerda", "su", "nombre", "Epafrodito"]
    texto = ("Un hombre casi muere por llevar una entrega. Casi nadie recuerda "
             "su nombre: «Epafrodito».")
    con = marcas_tts.puntuar(edge, texto)
    assert len(con) == len(edge)
    assert con[7] == "entrega." and con[12] == "nombre:" and con[13] == "«Epafrodito».", con
    # una palabra que no casa no se toca, y el recuento nunca cambia
    raro = marcas_tts.puntuar(["Hola", "mundo", "extra"], "Hola, mundo.")
    assert raro == ["Hola,", "mundo.", "extra"], raro
    escenas = [{"narracion": "Un hombre casi muere por llevar una entrega Casi"},
               {"narracion": "nadie recuerda su nombre Epafrodito"}]
    marcas_tts.puntuar_escenas(escenas, texto)
    assert escenas[0]["narracion"].endswith("entrega. Casi"), escenas
    # el gancho, ya con signos, corta en la frase; sin signos, no cuelga «su»
    assert gancho.cartel_de(" ".join(con))[0] == "Un hombre casi muere por llevar una entrega"
    sin = gancho.cartel_de("Un hombre casi muere por llevar una entrega casi nadie recuerda su")[0]
    assert not sin.lower().rstrip("…").endswith(" su"), sin
    print("ok signos y gancho")


def probar_cita_partida():
    a = {"id": "a", "t_in": 0, "t_out": 4,
         "narracion": "Pablo lo escribe en Filipenses capítulo dos,"}
    b = {"id": "b", "t_in": 4, "t_out": 9,
         "narracion": "versículo veintisiete: «Estuvo enfermo, a punto de morir».",
         "_previas": a["narracion"].split()}
    assert motion.contador_de(motion.Voz(a)) is None     # nada de «2 VERSÍCULO»
    assert motion.cita_de(motion.Voz(a)) is None
    cita = motion.cita_de(motion.Voz(b))
    assert cita and cita["ref"] == "Filipenses 2:27", cita
    assert [w for w, _ in cita["palabras"]][:2] == ["Estuvo", "enfermo,"], cita
    assert motion.contador_de(motion.Voz({"t_in": 0, "t_out": 3,
                                          "narracion": "capítulo dos versículo veintisiete"})) is None
    assert motion.contador_de(motion.Voz({"t_in": 0, "t_out": 3,
                                          "narracion": "cinco mil hombres"}))["n"] == 5000
    # en el video entero: la tarjeta de la cita sale en el plano del versiculo
    confs = motion.preparar([a, b], {"motion": True}, {}, 1080, 1920)
    tipos_b = [q["tipo"] for q in confs["b"]["piezas"] if q["id"].startswith("b-")]
    tipos_a = [q["tipo"] for q in confs["a"]["piezas"]]
    assert "versiculo" in tipos_b and "contador" not in tipos_a, (tipos_a, tipos_b)
    print("ok cita partida")


def probar_munecos():
    e = {"id": "S004", "t_in": 0, "t_out": 6, "personajes": ["Pablo", "Epafrodito"],
         "narracion": "Pablo y Epafrodito en la cárcel escriben la carta."}
    claude = [{"tipo": "personajes", "nombres": ["Pablo", "Epafrodito"]}, {"tipo": "auto"}]
    piezas = motion.storyboard(e, 1080, 1920, claude=claude, fichas={})
    assert [q["tipo"] for q in piezas].count("personajes") == 1, piezas
    # Claude pone al muñeco y lo automatico un mapa: el muñeco baja al pie
    m = {"id": "S003", "t_in": 0, "t_out": 6, "personajes": ["Epafrodito"],
         "narracion": "Epafrodito viajó de Filipos a Roma con la ofrenda."}
    piezas = motion.storyboard(m, 1080, 1920, fichas={}, claude=[
        {"tipo": "auto"}, {"tipo": "personajes", "nombres": ["Epafrodito"], "x": .5, "y": .7}])
    mapa = next(q for q in piezas if q["tipo"] == "mapa")
    fig = next(q for q in piezas if q["tipo"] == "personajes")
    assert fig["y"] - fig["alto"] > mapa["y"] + mapa["h"] / 2, (fig, mapa["y"], mapa["h"])
    print("ok muñecos")


def probar_un_solo_sigueme():
    fin = {"id": "S20", "t_in": 70, "t_out": 76, "narracion": "Sígueme para más historias.",
           "personajes": ["Pablo"]}
    piezas = motion.storyboard(fin, 1080, 1920, fichas={},
                               claude=[{"tipo": "texto", "texto": "*SÍGUEME*"}, {"tipo": "auto"}])
    textos = [w["t"] for q in piezas if q["tipo"] == "texto" for w in q["palabras"]]
    assert "SÍGUEME" not in textos, textos
    # la plantilla TikTok va DENTRO de la tarjeta; sin pedir nada, la pone ella
    escenas = [{"id": "a", "t_in": 0, "t_out": 6, "narracion": "Y se fue a casa."},
               {"id": "b", "t_in": 6, "t_out": 12, "narracion": "Dios no lo olvidó."}]
    c = rotulos.preparar(escenas, {}, 1080, 1920, seguir="para más historias como esta")
    f = [r for r in c["b"]["items"] if r["tipo"] == "final"]
    assert len(f) == 1 and f[0]["botones"] == ["SÍGUEME"], c
    assert f[0]["nota"] == "para más historias como esta" and f[0]["t"] <= 6 - 1.3
    # si la narracion ya pedia comentar, se le suma SÍGUEME: una tarjeta
    escenas[1]["narracion"] = "Cuéntame en los comentarios qué harías tú."
    c = rotulos.preparar(escenas, {}, 1080, 1920, seguir="para más historias como esta")
    f = [r for r in c["b"]["items"] if r["tipo"] == "final"]
    assert len(f) == 1 and "SÍGUEME" in f[0]["botones"], f
    # y el cuadro de la plantilla sale de la capa quieta
    svg = ("<svg><g id='sub'>hola</g>"
           + plantilla_tiktok.svg_seguir((1080, 1920), "para más", empieza=1.0)
           + "<g>barra</g></svg>")
    limpio = plantilla_tiktok.sin_seguir(svg)
    assert "tiktok-seguir" not in limpio and "hola" in limpio and "barra" in limpio, limpio
    print("ok un solo SÍGUEME")


if __name__ == "__main__":
    probar_signos()
    probar_cita_partida()
    probar_munecos()
    probar_un_solo_sigueme()
    print("prueba_video_real: OK")
