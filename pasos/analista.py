"""El agente analista y las ideas: qué pega en el nicho, cómo van los vídeos
propios y qué vídeo hacer después. Es la pestaña «📊 Análisis / 💡 Ideas».

QUÉ HACE, EN TRES PARTES
------------------------
(a) **El nicho.** Busca en YouTube (API oficial YouTube Data v3, gratis con una
    clave de Google Cloud) los vídeos más vistos de los últimos N días para unas
    búsquedas del nicho («¿sabías que…? biblia», «historia bíblica animada»…),
    y los MIDE: vistas por día desde que se publicó, interacción, duración,
    cómo es el título (pregunta, cifra, «sabías»), a qué hora se publicó. De ahí
    salen consejos en cristiano («los que más crecen duran 60-90 s», «el 70 % de
    los mejores títulos son una pregunta»). Es una cuenta, sin modelo: gratis.
    TikTok no tiene API pública de tendencias: David pega ENLACES de vídeos que
    le gustan y, si quiere, sus cifras; el título y el autor se leen con el
    oEmbed público de TikTok (el mismo que usan las webs para incrustarlos).

(b) **Mis vídeos.** Con el @ del canal, la misma clave trae vistas, me gusta y
    comentarios de cada vídeo subido. La RETENCIÓN no la da la API pública (pide
    OAuth de YouTube Analytics): se escribe a mano por vídeo («% visto» y «en
    qué segundo se va la gente») o se pega la exportación de YouTube Studio
    (Analytics → Modo avanzado → Exportar → CSV). TikTok, igual: a mano.

(c) **Ideas.** Claude (el CLI con la suscripción, sonnet/medium como el
    asistente: segundos, no minutos) lee el resumen del nicho, las referencias
    de TikTok y los números propios, y propone vídeos con título, gancho de los
    3 primeros segundos, duración, formato, estilo de dibujo y el MATERIAL para
    el guion. «Crear este vídeo» (en la pantalla) lo pasa al encargo.

DÓNDE VIVE
----------
Un fichero: `analisis.json`, junto a `ajustes.json` (en el servidor,
`datos/analisis.json`, fuera del código: `asvs actualizar` no lo toca). Se
puede mover con `ESTUDIO_ANALISIS`. La clave de YouTube va en el almacén de
claves (`claves.json`, `youtube`), nunca aquí.

LA CUOTA DE YOUTUBE
-------------------
10.000 unidades al día. `search.list` cuesta 100 y `videos.list` 1, así que una
pasada de seis búsquedas son ~606. Por eso el nicho se guarda y NO se vuelve a
pedir antes de `REFRESCO_S` salvo que se fuerce.
"""
import csv
import io
import json
import math
import os
import re
import statistics
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

try:
    from . import ajustes, claves, cli_claude
except ImportError:                                   # pasos/ suelto en sys.path
    import ajustes                                    # noqa: E402
    import claves                                     # noqa: E402
    import cli_claude                                 # noqa: E402

RUTA = os.environ.get("ESTUDIO_ANALISIS") or os.path.join(
    os.path.dirname(os.path.abspath(ajustes.RUTA)), "analisis.json")

API_YT = "https://www.googleapis.com/youtube/v3"
OEMBED_TIKTOK = "https://www.tiktok.com/oembed"

#: Lo que se busca si David no ha escrito sus búsquedas. Su nicho: Biblia,
#: historia bíblica y el formato «¿sabías que…?».
BUSQUEDAS_POR_DEFECTO = [
    "sabías que biblia",
    "historia bíblica animada",
    "curiosidades de la biblia",
    "hechos de los apóstoles",
    "personajes de la biblia explicados",
]
REFRESCO_S = 6 * 3600
MAX_BUSQUEDAS = 8
MAX_POR_BUSQUEDA = 15
MAX_IDEAS = 30            # las que se guardan (las nuevas empujan a las viejas)

#: Lima: las horas de publicación se cuentan en la hora de David.
ZONA = timezone(timedelta(hours=-5))
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

MODELO = os.environ.get("ESTUDIO_IDEAS_MODELO") or "sonnet"
ESFUERZO = os.environ.get("ESTUDIO_IDEAS_ESFUERZO") or "medium"

_LOCK = threading.RLock()


class ErrorAnalista(ValueError):
    """Algo que se le puede decir a David tal cual."""


# ------------------------------------------------------------------ el fichero

def _vacio():
    return {
        "version": 1,
        "config": {"busquedas": list(BUSQUEDAS_POR_DEFECTO), "region": "",
                   "dias": 90, "canal": ""},
        "nicho": {"ultima": 0, "videos": [], "resumen": {}, "firma": ""},
        "tiktok": [],
        "mios": [],
        "canal": {"ultima": 0, "titulo": "", "suscriptores": 0},
        "ideas": [],
    }


def leer():
    with _LOCK:
        try:
            with open(RUTA, "r", encoding="utf-8") as fh:
                datos = json.load(fh)
        except (OSError, ValueError):
            datos = {}
        base = _vacio()
        if isinstance(datos, dict):
            for clave, valor in datos.items():
                if clave in base and isinstance(valor, type(base[clave])):
                    base[clave] = valor
            base["config"] = {**_vacio()["config"], **base["config"]}
        return base


def _guardar(datos):
    with _LOCK:
        carpeta = os.path.dirname(RUTA)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        temporal = RUTA + ".tmp"
        with open(temporal, "w", encoding="utf-8") as fh:
            json.dump(datos, fh, ensure_ascii=False, indent=1)
        os.replace(temporal, RUTA)
        return datos


def _cambiar(funcion):
    """Lee, aplica `funcion(datos)` y guarda, todo bajo el cerrojo."""
    with _LOCK:
        datos = leer()
        salida = funcion(datos)
        _guardar(datos)
        return salida


def _nuevo_id():
    return uuid.uuid4().hex[:10]


def guardar_config(cambios):
    if not isinstance(cambios, dict):
        raise ErrorAnalista("la configuración se cambia con un objeto")

    def aplicar(datos):
        cfg = datos["config"]
        if "busquedas" in cambios:
            crudas = cambios["busquedas"]
            if isinstance(crudas, str):
                crudas = re.split(r"[\n,;]+", crudas)
            lista = []
            for b in crudas or []:
                b = re.sub(r"\s+", " ", str(b)).strip()[:80]
                if b and b.lower() not in [x.lower() for x in lista]:
                    lista.append(b)
            if not lista:
                raise ErrorAnalista("escribe al menos una búsqueda")
            cfg["busquedas"] = lista[:MAX_BUSQUEDAS]
        if "region" in cambios:
            region = str(cambios["region"] or "").strip().upper()
            if region and not re.fullmatch(r"[A-Z]{2}", region):
                raise ErrorAnalista("la región son dos letras (PE, MX, ES…) o vacía")
            cfg["region"] = region
        if "dias" in cambios:
            try:
                dias = int(cambios["dias"])
            except (TypeError, ValueError):
                raise ErrorAnalista("los días son un número") from None
            cfg["dias"] = max(7, min(365, dias))
        if "canal" in cambios:
            cfg["canal"] = str(cambios["canal"] or "").strip()[:200]
        return cfg
    return _cambiar(aplicar)


# ------------------------------------------------------------------ YouTube

def clave_youtube():
    try:
        return claves.leer().get("youtube", {}).get("clave", "")
    except Exception:                                 # noqa: BLE001
        return ""


def _requests():
    import requests                                   # noqa: PLC0415
    return requests


def _yt(recurso, params, clave):
    """Una llamada a la API de YouTube, con los fallos dichos en cristiano."""
    if not clave:
        raise ErrorAnalista("falta la clave de YouTube: ponla arriba, en «La clave "
                            "de YouTube» (es gratis, sale de Google Cloud)")
    try:
        respuesta = _requests().get(f"{API_YT}/{recurso}",
                                    params={**params, "key": clave}, timeout=20)
    except Exception as fallo:                        # noqa: BLE001
        raise ErrorAnalista(f"no se ha podido hablar con YouTube: {fallo}") from None
    if respuesta.status_code == 200:
        return respuesta.json()
    try:
        error = respuesta.json().get("error", {})
    except ValueError:
        error = {}
    motivos = {e.get("reason") for e in error.get("errors", []) if isinstance(e, dict)}
    if "quotaExceeded" in motivos or "dailyLimitExceeded" in motivos:
        raise ErrorAnalista("se ha gastado la cuota de hoy de YouTube (10.000 unidades); "
                            "se renueva a medianoche, hora del Pacífico")
    if "keyInvalid" in motivos or respuesta.status_code == 400 and "API key" in str(error):
        raise ErrorAnalista("YouTube no reconoce la clave: cópiala otra vez desde "
                            "Google Cloud → Credenciales")
    if "accessNotConfigured" in motivos or "SERVICE_DISABLED" in str(error):
        raise ErrorAnalista("la clave es buena pero falta habilitar «YouTube Data API v3» "
                            "en ese proyecto de Google Cloud (Biblioteca → buscarla → "
                            "Habilitar)")
    texto = error.get("message") or respuesta.text[:200]
    raise ErrorAnalista(f"YouTube contesta {respuesta.status_code}: {texto}")


def segundos_iso(texto):
    """'PT1M5S' -> 65. Lo que no se entiende, 0."""
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", str(texto or ""))
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def _fecha(texto):
    try:
        return datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
    except ValueError:
        return None


def ficha_video(item, ahora=None):
    """Un vídeo de `videos.list` en lo que se mide."""
    ahora = ahora or datetime.now(timezone.utc)
    sn = item.get("snippet") or {}
    st = item.get("statistics") or {}
    cd = item.get("contentDetails") or {}
    publicado = _fecha(sn.get("publishedAt"))
    dias = max(1.0, (ahora - publicado).total_seconds() / 86400) if publicado else 1.0
    vistas = int(st.get("viewCount") or 0)
    gustos = int(st.get("likeCount") or 0)
    comentarios = int(st.get("commentCount") or 0)
    miniaturas = sn.get("thumbnails") or {}
    mini = (miniaturas.get("medium") or miniaturas.get("high")
            or miniaturas.get("default") or {}).get("url", "")
    local = publicado.astimezone(ZONA) if publicado else None
    return {
        "id": item.get("id", ""),
        "url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
        "titulo": sn.get("title", ""),
        "canal": sn.get("channelTitle", ""),
        "publicado": sn.get("publishedAt", ""),
        "hora": local.hour if local else None,
        "dia": local.weekday() if local else None,
        "duracion_s": segundos_iso(cd.get("duration")),
        "vistas": vistas,
        "me_gusta": gustos,
        "comentarios": comentarios,
        "vistas_dia": round(vistas / dias, 1),
        "interaccion": round((gustos + comentarios) / vistas, 4) if vistas else 0,
        "miniatura": mini,
    }


def _videos(ids, clave):
    fichas = []
    ids = [i for i in dict.fromkeys(ids) if i]
    for inicio in range(0, len(ids), 50):
        datos = _yt("videos", {"part": "snippet,statistics,contentDetails",
                               "id": ",".join(ids[inicio:inicio + 50])}, clave)
        fichas.extend(ficha_video(it) for it in datos.get("items", []))
    return fichas


def buscar_nicho(forzar=False):
    """Busca el nicho en YouTube, lo mide y lo guarda. -> el bloque `nicho`."""
    datos = leer()
    cfg = datos["config"]
    firma = json.dumps([cfg["busquedas"], cfg["region"], cfg["dias"]], ensure_ascii=False)
    nicho = datos["nicho"]
    if (not forzar and nicho.get("firma") == firma and nicho.get("videos")
            and time.time() - float(nicho.get("ultima") or 0) < REFRESCO_S):
        return nicho
    clave = clave_youtube()
    desde = (datetime.now(timezone.utc) - timedelta(days=cfg["dias"])).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    ids, por_busqueda = [], {}
    for busqueda in cfg["busquedas"][:MAX_BUSQUEDAS]:
        params = {"part": "id", "type": "video", "q": busqueda, "order": "viewCount",
                  "publishedAfter": desde, "relevanceLanguage": "es",
                  "maxResults": MAX_POR_BUSQUEDA, "safeSearch": "none"}
        if cfg["region"]:
            params["regionCode"] = cfg["region"]
        respuesta = _yt("search", params, clave)
        encontrados = [it.get("id", {}).get("videoId") for it in respuesta.get("items", [])]
        for vid in encontrados:
            if vid:
                por_busqueda.setdefault(vid, busqueda)
        ids.extend(encontrados)
    videos = _videos(ids, clave)
    for v in videos:
        v["busqueda"] = por_busqueda.get(v["id"], "")
    videos.sort(key=lambda v: v["vistas_dia"], reverse=True)

    def aplicar(d):
        d["nicho"] = {"ultima": time.time(), "firma": firma, "videos": videos,
                      "resumen": resumir_nicho(videos)}
        return d["nicho"]
    return _cambiar(aplicar)


# ------------------------------------------------------------------ las cuentas

PALABRAS_VACIAS = set("""
a al algo ante como con contra cual de del desde donde el ella en entre era es esa
ese eso esta este esto fue ha hay la las le lo los mas más me mi muy no nos o para
pero por que qué se ser si sí sin sobre su sus te tu tú un una uno y ya the of and
to in is it you this que la lo video vídeo videos vídeos shorts short parte
""".split())


def _rasgos_titulo(titulo):
    t = str(titulo or "")
    return {
        "pregunta": "?" in t or "¿" in t,
        "cifra": bool(re.search(r"\d", t)),
        "sabias": bool(re.search(r"sab[ií]as", t, re.I)),
        "mayusculas": bool(re.search(r"\b[A-ZÁÉÍÓÚÑ]{4,}\b", t)),
        "emoji": bool(re.search(r"[\U0001F300-\U0001FAFF☀-➿]", t)),
        "corto": len(t) <= 50,
    }


NOMBRE_RASGO = {
    "pregunta": "son una pregunta",
    "cifra": "llevan una cifra",
    "sabias": "dicen «sabías»",
    "mayusculas": "llevan una palabra en MAYÚSCULAS",
    "emoji": "llevan un emoji",
    "corto": "tienen 50 caracteres o menos",
}

TRAMOS = [(0, 60, "hasta 1:00"), (61, 90, "1:01-1:30"), (91, 180, "1:31-3:00"),
          (181, 480, "3-8 min"), (481, 10 ** 9, "más de 8 min")]


def _tramo(segundos):
    for desde, hasta, nombre in TRAMOS:
        if desde <= segundos <= hasta:
            return nombre
    return TRAMOS[-1][2]


def _mediana(valores, defecto=0):
    valores = [v for v in valores if v is not None]
    return statistics.median(valores) if valores else defecto


def _pct(parte, total):
    return round(100 * parte / total) if total else 0


def mmss(segundos):
    segundos = int(round(segundos or 0))
    return f"{segundos // 60}:{segundos % 60:02d}"


def resumir_nicho(videos):
    """Las cuentas del nicho y los consejos que salen de ellas."""
    videos = [v for v in videos if v.get("vistas")]
    if not videos:
        return {"total": 0, "consejos": ["No hay vídeos que medir: prueba otras búsquedas "
                                         "o más días."]}
    orden = sorted(videos, key=lambda v: v["vistas_dia"], reverse=True)
    corte = max(3, math.ceil(len(orden) / 4))
    mejores, resto = orden[:corte], orden[corte:] or orden

    rasgos = {}
    for nombre in NOMBRE_RASGO:
        en_mejores = _pct(sum(_rasgos_titulo(v["titulo"])[nombre] for v in mejores), len(mejores))
        en_resto = _pct(sum(_rasgos_titulo(v["titulo"])[nombre] for v in resto), len(resto))
        rasgos[nombre] = {"mejores": en_mejores, "resto": en_resto}

    tramos = {}
    for v in videos:
        tramos.setdefault(_tramo(v["duracion_s"]), []).append(v["vistas_dia"])
    tabla_tramos = [{"tramo": n, "videos": len(tramos[n]), "vistas_dia": round(_mediana(tramos[n]))}
                    for _, _, n in TRAMOS if n in tramos]
    candidatos = [t for t in tabla_tramos if t["videos"] >= 2] or tabla_tramos
    mejor_tramo = max(candidatos, key=lambda t: t["vistas_dia"]) if candidatos else None

    horas = {}
    for v in videos:
        if v.get("hora") is not None:
            horas.setdefault(v["hora"] // 3 * 3, []).append(v["vistas_dia"])
    tabla_horas = sorted(({"desde": h0, "videos": len(l), "vistas_dia": round(_mediana(l))}
                          for h0, l in horas.items()), key=lambda x: x["desde"])
    con_datos = [h for h in tabla_horas if h["videos"] >= 3]
    mejor_hora = max(con_datos, key=lambda h: h["vistas_dia"]) if con_datos else None

    dias = {}
    for v in videos:
        if v.get("dia") is not None:
            dias.setdefault(v["dia"], []).append(v["vistas_dia"])
    con_dias = [(d, l) for d, l in dias.items() if len(l) >= 3]
    mejor_dia = max(con_dias, key=lambda x: _mediana(x[1]))[0] if con_dias else None

    cuenta = {}
    for v in mejores:
        vistas_en = set()
        for palabra in re.findall(r"[a-záéíóúñü]{4,}", v["titulo"].lower()):
            if palabra not in PALABRAS_VACIAS and palabra not in vistas_en:
                vistas_en.add(palabra)
                cuenta[palabra] = cuenta.get(palabra, 0) + 1
    palabras = [p for p, n in sorted(cuenta.items(), key=lambda x: (-x[1], x[0])) if n >= 2][:12]

    cortos = [v for v in videos if v["duracion_s"] <= 180]
    largos = [v for v in videos if v["duracion_s"] > 180]

    consejos = []
    if mejor_tramo:
        consejos.append(f"Los que más crecen duran {mejor_tramo['tramo']} "
                        f"(mediana {mejor_tramo['vistas_dia']:,} vistas/día)."
                        .replace(",", "."))
    if cortos and largos:
        mc, ml = _mediana([v["vistas_dia"] for v in cortos]), _mediana([v["vistas_dia"] for v in largos])
        if mc > ml * 1.2:
            consejos.append(f"Los cortos (≤3 min) crecen {mc / max(ml, 1):.1f}× más rápido que los "
                            f"largos: prioriza Shorts/TikTok y usa los largos para profundizar.")
        elif ml > mc * 1.2:
            consejos.append(f"Aquí los largos (>3 min) crecen {ml / max(mc, 1):.1f}× más que los "
                            f"cortos: hay público para historias completas.")
    for nombre, r in sorted(rasgos.items(), key=lambda x: x[1]["resto"] - x[1]["mejores"]):
        if r["mejores"] >= 30 and r["mejores"] - r["resto"] >= 15:
            consejos.append(f"El {r['mejores']} % de los títulos que más crecen "
                            f"{NOMBRE_RASGO[nombre]} (frente al {r['resto']} % del resto).")
    if palabras:
        consejos.append("Palabras que se repiten en los mejores títulos: "
                        + ", ".join(palabras[:8]) + ".")
    if mejor_hora:
        consejos.append(f"Publicados entre las {mejor_hora['desde']}:00 y las "
                        f"{mejor_hora['desde'] + 3}:00 (hora de Lima) son los que mejor arrancan.")
    if mejor_dia is not None:
        consejos.append(f"El día con mejor arranque: {DIAS[mejor_dia]}.")
    inter = _mediana([v["interaccion"] for v in mejores])
    if inter:
        consejos.append(f"Los mejores tienen ~{inter * 100:.1f} % de interacción (me gusta + "
                        f"comentarios por vista): termina con una pregunta que invite a comentar.")

    return {
        "total": len(videos),
        "mejores": len(mejores),
        "vistas_dia_mediana": round(_mediana([v["vistas_dia"] for v in videos])),
        "duracion_mejores_s": round(_mediana([v["duracion_s"] for v in mejores])),
        "rasgos": rasgos,
        "tramos": tabla_tramos,
        "horas": tabla_horas,
        "palabras": palabras,
        "ejemplos": [{"titulo": v["titulo"], "vistas_dia": v["vistas_dia"],
                      "duracion_s": v["duracion_s"], "url": v["url"]} for v in mejores[:8]],
        "consejos": consejos,
    }


# ------------------------------------------------------------------ TikTok

def _oembed_tiktok(url):
    try:
        r = _requests().get(OEMBED_TIKTOK, params={"url": url}, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:                                 # noqa: BLE001
        pass
    return {}


def _numero(valor):
    """'12,5k' / '1.2M' / '3400' / 3400 -> int. Vacío -> None."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return int(valor)
    t = str(valor).strip().lower().replace(" ", "")
    mult = 1
    if t.endswith(("k", "mil")):
        mult, t = 1000, re.sub(r"(k|mil)$", "", t)
    elif t.endswith(("m", "mill")):
        mult, t = 1_000_000, re.sub(r"(m|mill)$", "", t)
    t = t.replace(",", ".") if mult > 1 else t.replace(".", "").replace(",", "")
    try:
        return int(float(t) * mult)
    except ValueError:
        return None


def _segundos(valor):
    """'1:05' / '65' / 65 -> 65. Vacío -> None."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return int(valor)
    partes = str(valor).strip().split(":")
    try:
        total = 0
        for p in partes:
            total = total * 60 + float(p.replace(",", "."))
        return int(round(total))
    except ValueError:
        return None


def anadir_tiktok(datos_in):
    url = str((datos_in or {}).get("url") or "").strip()
    if not re.match(r"https?://([a-z]+\.)?tiktok\.com/", url):
        raise ErrorAnalista("pega el enlace de un vídeo de TikTok (https://www.tiktok.com/…)")
    meta = _oembed_tiktok(url)
    ficha = {
        "id": _nuevo_id(), "url": url,
        "autor": meta.get("author_name") or "",
        "titulo": str(datos_in.get("titulo") or meta.get("title") or "")[:300],
        "miniatura": meta.get("thumbnail_url") or "",
        "vistas": _numero(datos_in.get("vistas")),
        "me_gusta": _numero(datos_in.get("me_gusta")),
        "duracion_s": _segundos(datos_in.get("duracion")),
        "notas": str(datos_in.get("notas") or "")[:500],
        "anadido": time.time(),
    }

    def aplicar(d):
        d["tiktok"] = [t for t in d["tiktok"] if t.get("url") != url]
        d["tiktok"].insert(0, ficha)
        d["tiktok"] = d["tiktok"][:60]
        return ficha
    return _cambiar(aplicar)


def quitar(lista, ident):
    if lista not in ("tiktok", "mios", "ideas"):
        raise ErrorAnalista("lista desconocida")

    def aplicar(d):
        antes = len(d[lista])
        d[lista] = [x for x in d[lista] if x.get("id") != ident]
        return antes != len(d[lista])
    return _cambiar(aplicar)


# ------------------------------------------------------------------ mis vídeos

CAMPOS_MIOS = ("titulo", "url", "plataforma", "duracion_s", "vistas", "me_gusta",
               "comentarios", "retencion_pct", "abandono_s", "vista_media_s", "notas",
               "proyecto")


def _limpiar_mio(entrada, base=None):
    ficha = dict(base or {})
    for campo in CAMPOS_MIOS:
        if campo not in entrada:
            continue
        valor = entrada[campo]
        if campo in ("vistas", "me_gusta", "comentarios"):
            ficha[campo] = _numero(valor)
        elif campo in ("duracion_s", "abandono_s", "vista_media_s"):
            ficha[campo] = _segundos(valor)
        elif campo == "retencion_pct":
            try:
                ficha[campo] = (None if valor in (None, "")
                                else max(0.0, min(100.0, float(str(valor).replace("%", "")
                                                               .replace(",", ".")))))
            except ValueError:
                raise ErrorAnalista("la retención es un porcentaje (por ejemplo 62)") from None
        elif campo == "plataforma":
            ficha[campo] = "tiktok" if "tiktok" in str(valor).lower() else (
                "youtube" if "you" in str(valor).lower() else "otra")
        else:
            ficha[campo] = str(valor or "").strip()[:500]
    if not ficha.get("plataforma"):
        url = ficha.get("url", "")
        ficha["plataforma"] = ("tiktok" if "tiktok.com" in url else
                               "youtube" if "youtu" in url else "otra")
    return ficha


def guardar_mio(entrada, ident=None):
    entrada = entrada if isinstance(entrada, dict) else {}

    def aplicar(d):
        if ident:
            for i, m in enumerate(d["mios"]):
                if m.get("id") == ident:
                    d["mios"][i] = _limpiar_mio(entrada, m)
                    return d["mios"][i]
            raise ErrorAnalista("ese vídeo ya no está en la lista")
        ficha = _limpiar_mio(entrada)
        if not ficha.get("titulo") and not ficha.get("url"):
            raise ErrorAnalista("pon al menos el título o el enlace del vídeo")
        ficha.update({"id": _nuevo_id(), "origen": "manual", "anadido": time.time()})
        d["mios"].insert(0, ficha)
        return ficha
    return _cambiar(aplicar)


def _canal_id(texto, clave):
    t = str(texto or "").strip()
    if not t:
        raise ErrorAnalista("escribe el @ de tu canal de YouTube (o su enlace)")
    m = re.search(r"(UC[\w-]{22})", t)
    if m:
        return {"id": m.group(1)}
    m = re.search(r"@([\w.\-]+)", t)
    handle = m.group(1) if m else t.rstrip("/").split("/")[-1]
    return {"forHandle": "@" + handle}


def sincronizar_canal():
    """Trae los vídeos del canal de David con sus cifras públicas."""
    datos = leer()
    clave = clave_youtube()
    filtro = _canal_id(datos["config"].get("canal"), clave)
    canal = _yt("channels", {"part": "snippet,contentDetails,statistics", **filtro}, clave)
    items = canal.get("items") or []
    if not items:
        raise ErrorAnalista("YouTube no encuentra ese canal: revisa el @ (tal como sale "
                            "en tu canal, por ejemplo @lumbrera)")
    ficha_canal = items[0]
    subidas = (ficha_canal.get("contentDetails", {}).get("relatedPlaylists", {})
               .get("uploads"))
    ids, pagina = [], None
    while subidas and len(ids) < 150:
        params = {"part": "contentDetails", "playlistId": subidas, "maxResults": 50}
        if pagina:
            params["pageToken"] = pagina
        lista = _yt("playlistItems", params, clave)
        ids += [it.get("contentDetails", {}).get("videoId") for it in lista.get("items", [])]
        pagina = lista.get("nextPageToken")
        if not pagina:
            break
    videos = _videos(ids, clave)

    def aplicar(d):
        por_video = {m.get("video_id"): m for m in d["mios"] if m.get("video_id")}
        nuevos = 0
        for v in videos:
            m = por_video.get(v["id"])
            cifras = {"titulo": v["titulo"], "url": v["url"], "plataforma": "youtube",
                      "duracion_s": v["duracion_s"], "vistas": v["vistas"],
                      "me_gusta": v["me_gusta"], "comentarios": v["comentarios"],
                      "publicado": v["publicado"], "vistas_dia": v["vistas_dia"],
                      "miniatura": v["miniatura"]}
            if m:
                m.update(cifras)          # la retención escrita a mano se queda
            else:
                nuevos += 1
                d["mios"].append({"id": _nuevo_id(), "video_id": v["id"],
                                  "origen": "youtube", "anadido": time.time(), **cifras})
        d["mios"].sort(key=lambda m: m.get("publicado") or "", reverse=True)
        d["canal"] = {"ultima": time.time(),
                      "titulo": ficha_canal.get("snippet", {}).get("title", ""),
                      "suscriptores": int(ficha_canal.get("statistics", {})
                                          .get("subscriberCount") or 0)}
        return {"videos": len(videos), "nuevos": nuevos, "canal": d["canal"]}
    return _cambiar(aplicar)


#: Columnas de la exportación de YouTube Studio, en español y en inglés.
COLUMNAS_CSV = {
    "video_id": ("contenido", "content", "video id", "id del video", "id del vídeo"),
    "titulo": ("título del video", "título del vídeo", "video title", "título", "title"),
    "vistas": ("visualizaciones", "views", "vistas"),
    "vista_media_s": ("duración media de las visualizaciones", "average view duration",
                      "duración promedio"),
    "retencion_pct": ("porcentaje medio visualizado", "average percentage viewed",
                      "porcentaje promedio"),
    "duracion_s": ("duración", "duration"),
    "me_gusta": ("me gusta", "likes"),
    "comentarios": ("comentarios añadidos", "comments added", "comentarios"),
}


def importar_csv(texto):
    """La exportación de YouTube Studio (o una tabla pegada): rellena retención."""
    texto = str(texto or "").strip()
    if not texto:
        raise ErrorAnalista("pega el contenido del CSV (o la tabla copiada de YouTube Studio)")
    muestra = texto.splitlines()[0]
    sep = "\t" if "\t" in muestra else (";" if muestra.count(";") > muestra.count(",") else ",")
    filas = list(csv.reader(io.StringIO(texto), delimiter=sep))
    if len(filas) < 2:
        raise ErrorAnalista("el CSV no tiene filas de datos")
    cabecera = [c.strip().lower() for c in filas[0]]
    indice = {}
    for campo, nombres in COLUMNAS_CSV.items():
        for nombre in nombres:
            hallado = next((i for i, c in enumerate(cabecera)
                            if c == nombre or c.startswith(nombre)), None)
            if hallado is not None and hallado not in indice.values():
                indice[campo] = hallado
                break
    if "titulo" not in indice and "video_id" not in indice:
        raise ErrorAnalista("no encuentro la columna del título ni la del vídeo; exporta "
                            "desde YouTube Studio → Analytics → Modo avanzado → Exportar")

    def aplicar(d):
        por_id = {m.get("video_id"): m for m in d["mios"] if m.get("video_id")}
        por_titulo = {str(m.get("titulo", "")).strip().lower(): m for m in d["mios"]}
        cambiados = anadidos = 0
        for fila in filas[1:]:
            if not any(c.strip() for c in fila):
                continue
            valor = {c: (fila[i].strip() if i < len(fila) else "") for c, i in indice.items()}
            if str(valor.get("video_id", "")).lower() in ("total", "") and \
                    str(valor.get("titulo", "")).lower() in ("total", ""):
                continue
            entrada = {k: v for k, v in valor.items() if k != "video_id" and v != ""}
            m = por_id.get(valor.get("video_id")) or por_titulo.get(
                str(valor.get("titulo", "")).strip().lower())
            if m:
                m.update({k: v for k, v in _limpiar_mio(entrada).items() if k != "plataforma"})
                cambiados += 1
            else:
                ficha = _limpiar_mio({**entrada, "plataforma": "youtube"})
                vid = valor.get("video_id")
                if vid and re.fullmatch(r"[\w-]{11}", vid):
                    ficha["video_id"] = vid
                    ficha["url"] = f"https://www.youtube.com/watch?v={vid}"
                ficha.update({"id": _nuevo_id(), "origen": "csv", "anadido": time.time()})
                d["mios"].append(ficha)
                anadidos += 1
        return {"actualizados": cambiados, "anadidos": anadidos}
    return _cambiar(aplicar)


def resumir_mios(mios):
    """Cómo van los vídeos de David, y qué hacer con eso."""
    con_vistas = [m for m in mios if m.get("vistas")]
    con_ret = [m for m in mios if m.get("retencion_pct") is not None]
    con_aband = [m for m in mios if m.get("abandono_s")]
    consejos = []
    if not mios:
        return {"total": 0, "consejos": [
            "Aún no hay vídeos tuyos: conecta tu canal de YouTube o añádelos a mano. "
            "Con 3-5 vídeos ya se ve qué funciona."]}
    mejor = max(con_vistas, key=lambda m: m.get("vistas") or 0) if con_vistas else None
    if mejor:
        consejos.append(f"Tu vídeo con más vistas: «{mejor.get('titulo', '')[:70]}» "
                        f"({mejor['vistas']:,} vistas)".replace(",", ".")
                        + (f", dura {mmss(mejor['duracion_s'])}." if mejor.get("duracion_s") else "."))
    if len(con_ret) >= 2:
        media = statistics.mean(m["retencion_pct"] for m in con_ret)
        consejos.append(f"Retención media: {media:.0f} %. "
                        + ("Muy buena: en Shorts por encima del 70 % el algoritmo empuja."
                           if media >= 70 else
                           "Para Shorts/TikTok apunta a más del 70 %: gancho más fuerte y "
                           "frases más cortas al principio."))
        cortos = [m["retencion_pct"] for m in con_ret if (m.get("duracion_s") or 0) <= 75]
        largos = [m["retencion_pct"] for m in con_ret if (m.get("duracion_s") or 0) > 75]
        if cortos and largos:
            consejos.append(f"Tus vídeos de ≤1:15 retienen {statistics.mean(cortos):.0f} % y los "
                            f"más largos {statistics.mean(largos):.0f} %.")
    if con_aband:
        media_ab = statistics.mean(m["abandono_s"] for m in con_aband)
        consejos.append(f"La gente se suele ir hacia el segundo {media_ab:.0f}: pon ahí un "
                        f"cambio fuerte (una cifra grande, una pregunta, un clip que se mueva).")
        if media_ab <= 5:
            consejos.append("Se van en los 5 primeros segundos: el gancho no engancha. Prueba "
                            "a abrir con una pregunta «¿Sabías que…?» y una imagen impactante.")
    if len(con_vistas) >= 4:
        orden = sorted(con_vistas, key=lambda m: m["vistas"], reverse=True)
        arriba = orden[:max(2, len(orden) // 3)]
        preg_arriba = _pct(sum(_rasgos_titulo(m.get("titulo"))["pregunta"] for m in arriba), len(arriba))
        if preg_arriba >= 60:
            consejos.append(f"El {preg_arriba} % de tus vídeos más vistos tienen título en pregunta: sigue así.")
    return {
        "total": len(mios),
        "vistas_total": sum(m.get("vistas") or 0 for m in mios),
        "retencion_media": round(statistics.mean(m["retencion_pct"] for m in con_ret), 1) if con_ret else None,
        "abandono_medio_s": round(statistics.mean(m["abandono_s"] for m in con_aband)) if con_aband else None,
        "consejos": consejos,
    }


# ------------------------------------------------------------------ las ideas

#: Una idea, tal como la usa la pantalla y el encargo.
CAMPOS_IDEA = ("titulo", "gancho", "por_que", "duracion_s", "formato", "plantilla_tiktok",
               "dibujo", "estilo", "material", "indicaciones", "hashtags", "miniatura",
               "clips", "tema")

_TRABAJO = {"estado": "libre", "inicio": 0, "fin": 0, "error": "", "nuevas": 0}


def trabajo():
    return dict(_TRABAJO)


def simulado():
    return str(os.environ.get("ESTUDIO_SIMULAR", "")).strip().lower() in ("1", "si", "sí", "true")


def _tabla(videos, n=12):
    lineas = []
    for v in videos[:n]:
        lineas.append(f"- «{v.get('titulo', '')}» — {int(v.get('vistas_dia') or 0)} vistas/día, "
                      f"{mmss(v.get('duracion_s'))}, {v.get('canal', '')}")
    return "\n".join(lineas) or "(sin datos)"


def instruccion_ideas(datos, tema="", cuantas=5, formato=""):
    """El encargo para Claude, con todo lo medido delante."""
    nicho = datos["nicho"]
    resumen = nicho.get("resumen") or {}
    mios = datos["mios"]
    rmios = resumir_mios(mios)
    tiktok = datos["tiktok"][:12]
    previas = [i.get("titulo", "") for i in datos["ideas"][:25]]
    partes = [
        "Eres el analista y director de contenido de un canal hispano de vídeos animados "
        "narrados sobre la Biblia y su historia (formato «¿Sabías que…?», hechos de los "
        "apóstoles, personajes, curiosidades, contexto histórico). El canal se hace con "
        "Shaddai Studio, que ofrece: formato vertical 9:16 u horizontal; plantilla "
        "TikTok/Shorts (barra de progreso, «Sígueme» al final, golpe de sonido); gancho de "
        "3 s con cartel grande y subtítulos palabra a palabra; dibujo «muñecos» (personajes "
        "geométricos con túnica que gesticulan) o «realista"
        "» (ilustración); efectos de ambiente (fuego, agua, nubes, rayos, haces de luz); y "
        "1-3 clips de vídeo cortos en los momentos clave.",
        "",
        "## Qué está pegando en el nicho (YouTube, medido)",
        "Consejos sacados de los datos:\n" + "\n".join(f"- {c}" for c in resumen.get("consejos", []))
        if resumen.get("consejos") else "(todavía no se ha buscado el nicho)",
        "Los que más crecen:\n" + _tabla(nicho.get("videos", [])),
        "",
        "## Referencias de TikTok que ha guardado el creador",
        "\n".join(f"- «{t.get('titulo', '')[:150]}» de {t.get('autor') or '?'}"
                  + (f", {t['vistas']} vistas" if t.get("vistas") else "")
                  + (f", dura {mmss(t['duracion_s'])}" if t.get("duracion_s") else "")
                  + (f". Nota: {t['notas']}" if t.get("notas") else "")
                  for t in tiktok) or "(ninguna)",
        "",
        "## Cómo van los vídeos del creador",
        "\n".join(f"- {c}" for c in rmios.get("consejos", [])),
        "\n".join(f"- «{m.get('titulo', '')[:90]}» ({m.get('plataforma', '')}): "
                  f"{m.get('vistas') or '?'} vistas"
                  + (f", retención {m['retencion_pct']:.0f} %" if m.get("retencion_pct") is not None else "")
                  + (f", se van en el s {m['abandono_s']}" if m.get("abandono_s") else "")
                  + (f", dura {mmss(m['duracion_s'])}" if m.get("duracion_s") else "")
                  for m in mios[:15]),
        "",
        "## Ideas ya propuestas (NO las repitas)",
        "\n".join(f"- {t}" for t in previas) or "(ninguna)",
        "",
        "## Lo que se pide",
        f"Propón {cuantas} ideas de vídeo DISTINTAS entre sí"
        + (f" sobre: {tema}" if tema else "")
        + (f". Formato preferido: {formato}" if formato else "")
        + ". Cada idea tiene que apoyarse en lo medido (dilo en «por_que» citando el dato), "
          "ser fiel a la Biblia (cita libro y capítulo en el material) y tener un gancho que "
          "en 3 segundos genere curiosidad (pregunta, dato sorprendente o cifra). Para "
          "TikTok/Shorts la duración ideal es 61-90 s (Creator Rewards pide más de 1 min).",
        "",
        "Responde SOLO con un array JSON, sin texto antes ni después. Cada elemento:",
        '{"titulo": "título para YouTube, máx 70 caracteres", '
        '"gancho": "la primera frase del guion, máx 14 palabras, empieza fuerte", '
        '"por_que": "1-2 frases: qué dato del análisis la respalda", '
        '"duracion_s": 75, "formato": "vertical" o "horizontal", '
        '"plantilla_tiktok": true o false, "dibujo": "munecos" o "realista", '
        '"estilo": "estilo visual sugerido en una frase (paleta, luz, época)", '
        '"material": "120-250 palabras: los hechos a contar en orden, con citas bíblicas '
        '(libro capítulo:versículo), nombres, lugares y cifras", '
        '"indicaciones": "cómo contarlo: ritmo, tono, qué evitar", '
        '"hashtags": ["#biblia", "..."], "miniatura": "texto de la miniatura, máx 4 palabras", '
        '"clips": "1-3 momentos que merecen un clip animado"}',
    ]
    return "\n".join(partes)


def extraer_ideas(texto):
    """Saca el array JSON de la respuesta y lo deja en la forma de la pantalla."""
    texto = str(texto or "")
    m = re.search(r"\[.*\]", texto, re.S)
    if not m:
        raise ErrorAnalista("Claude no ha devuelto una lista de ideas; vuelve a pedirlas")
    try:
        crudas = json.loads(m.group(0))
    except ValueError:
        raise ErrorAnalista("la respuesta de Claude no es JSON válido; vuelve a pedirlas") from None
    ideas = []
    for c in crudas if isinstance(crudas, list) else []:
        if not isinstance(c, dict) or not str(c.get("titulo") or "").strip():
            continue
        idea = normalizar_idea(c)
        ideas.append(idea)
    if not ideas:
        raise ErrorAnalista("Claude no ha devuelto ninguna idea utilizable")
    return ideas


def normalizar_idea(c):
    try:
        dur = int(float(c.get("duracion_s") or 75))
    except (TypeError, ValueError):
        dur = 75
    hashtags = c.get("hashtags") or []
    if isinstance(hashtags, str):
        hashtags = re.findall(r"#?[\wáéíóúñ]+", hashtags)
    hashtags = [("#" + h.lstrip("#"))[:40] for h in hashtags if str(h).strip()][:12]
    formato = "horizontal" if str(c.get("formato", "")).lower().startswith("h") else "vertical"
    return {
        "id": _nuevo_id(),
        "creada": time.time(),
        "estado": "nueva",
        "titulo": str(c.get("titulo", "")).strip()[:120],
        "gancho": str(c.get("gancho", "")).strip()[:200],
        "por_que": str(c.get("por_que", "")).strip()[:500],
        "duracion_s": max(20, min(900, dur)),
        "formato": formato,
        "plantilla_tiktok": bool(c.get("plantilla_tiktok", formato == "vertical")),
        "dibujo": "munecos" if "mu" in str(c.get("dibujo", "")).lower() else "realista",
        "estilo": str(c.get("estilo", "")).strip()[:300],
        "material": str(c.get("material", "")).strip()[:4000],
        "indicaciones": str(c.get("indicaciones", "")).strip()[:1000],
        "hashtags": hashtags,
        "miniatura": str(c.get("miniatura", "")).strip()[:60],
        "clips": str(c.get("clips", "")).strip()[:400],
        "tema": str(c.get("tema", "")).strip()[:200],
    }


def _ideas_simuladas(cuantas, tema):
    base = tema or "los Hechos de los Apóstoles"
    return [normalizar_idea({
        "titulo": f"¿Sabías esto de {base}? (idea {n + 1})",
        "gancho": f"¿Sabías que casi nadie conoce esto de {base}?",
        "por_que": "Simulado: los títulos en pregunta crecen más en el nicho.",
        "duracion_s": 75, "formato": "vertical", "plantilla_tiktok": True,
        "dibujo": "munecos", "estilo": "tonos cálidos de lámpara de aceite",
        "material": f"Hechos 2:1-4. Material de prueba sobre {base}.",
        "indicaciones": "frases cortas", "hashtags": ["#biblia", "#sabiasque"],
        "miniatura": "NADIE LO SABE", "clips": "el momento central",
    }) for n in range(cuantas)]


def pedir_ideas(tema="", cuantas=5, formato=""):
    """Lanza la petición de ideas en segundo plano. -> el estado del trabajo."""
    try:
        cuantas = max(1, min(10, int(cuantas or 5)))
    except (TypeError, ValueError):
        cuantas = 5
    tema = str(tema or "").strip()[:300]
    formato = str(formato or "").strip()[:40]
    with _LOCK:
        if _TRABAJO["estado"] == "pensando":
            raise ErrorAnalista("ya estoy pensando ideas: espera a que terminen")
        _TRABAJO.update({"estado": "pensando", "inicio": time.time(), "fin": 0,
                         "error": "", "nuevas": 0})

    def correr():
        try:
            if simulado():
                ideas = _ideas_simuladas(cuantas, tema)
            else:
                texto, _ = cli_claude.ejecutar(
                    instruccion_ideas(leer(), tema, cuantas, formato),
                    modelo=MODELO, esfuerzo=ESFUERZO, tiempo_max_s=300,
                    base_tiempo_s=180, para="las ideas del analista")
                ideas = extraer_ideas(texto)
            for idea in ideas:
                idea["tema"] = idea.get("tema") or tema

            def aplicar(d):
                d["ideas"] = (ideas + d["ideas"])[:MAX_IDEAS]
            _cambiar(aplicar)
            _TRABAJO.update({"estado": "hecho", "fin": time.time(), "nuevas": len(ideas)})
        except Exception as fallo:                    # noqa: BLE001
            _TRABAJO.update({"estado": "error", "fin": time.time(),
                             "error": str(fallo)[:600] or type(fallo).__name__})

    threading.Thread(target=correr, name="ideas-analista", daemon=True).start()
    return trabajo()


def marcar_idea(ident, estado):
    if estado not in ("nueva", "usada", "descartada", "favorita"):
        raise ErrorAnalista("estado de idea desconocido")

    def aplicar(d):
        for idea in d["ideas"]:
            if idea.get("id") == ident:
                idea["estado"] = estado
                return idea
        raise ErrorAnalista("esa idea ya no está")
    return _cambiar(aplicar)


# ------------------------------------------------------------------ lo que ve la pantalla

def ficha():
    """Todo lo que pinta la pestaña (sin ninguna clave)."""
    datos = leer()
    datos["tiene_clave_youtube"] = bool(clave_youtube())
    datos["resumen_mios"] = resumir_mios(datos["mios"])
    datos["trabajo"] = trabajo()
    datos["refresco_s"] = REFRESCO_S
    datos["nicho"].pop("firma", None)
    return datos
