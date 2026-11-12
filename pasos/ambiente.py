"""
AMBIENTE Y PROFUNDIDAD 2.5D DEL RENDER (etapa 1 del plan de animacion).

Que da vida a un plano que es UNA imagen quieta, sin gastar un centimo y sin
GPU, con lo que el render ya tiene: el navegador que pinta cada fotograma.

    1. EFECTOS DE AMBIENTE. Se eligen solos leyendo la narracion y el prompt
       del plano (`elegir`): luz que parpadea (fuego, lampara), particulas
       (polvo, brasas, destellos), agua que ondula, nubes que pasan, lluvia,
       rayos de tormenta y «gloria» (haces de luz desde arriba). Los pinta la
       propia pagina del render (ver AMBIENTE_JS) en funcion de `t`, nunca del
       reloj: el mismo fotograma sale identico en cualquier lote.
    2. PROFUNDIDAD 2.5D. Se recorta la figura del fondo con rembg (en CPU, una
       vez por imagen y con cache), se rellena el hueco que deja en el fondo y
       la pagina mueve las dos capas a distinta velocidad (parallax) mas un
       balanceo suave de la figura. Sin rembg, o si la imagen no tiene una
       figura clara (un paisaje), el plano entero se balancea un poco y ya.

Como se gobierna:
    params del render  "ambiente": "auto" (defecto) | "no" | ["lluvia", ...]
                       "profundidad": True | False
    plan.json, escena  "ambiente": [...]   manda sobre lo automatico (o [] = nada)

Nada de esto toca firmas de imagenes ni de capas: es solo como se PINTA el
render, que es gratis de repetir.
"""
import hashlib
import json
import os
import re
import unicodedata

import numpy as np
from PIL import Image, ImageFilter

EFECTOS = ("luz", "particulas", "agua", "nubes", "lluvia", "rayos", "gloria",
           "contraluz")

# Palabras (sin tildes, en minuscula) que encienden cada efecto. Cada una es el
# PRINCIPIO de una palabra («nube» vale para «nubes»); las cortas que se
# confunden («mar» en «Maria», «rio» en «imperio», «llama» en «llamado») van
# cerradas con \b. Van en
# espanol y en ingles porque el prompt de imagen puede estar en cualquiera.
PALABRAS = {
    "luz": ("fuego", "lampara", "lumbrera", "antorcha", "vela", "hoguera",
            "fogata", "zarza", "candelero", "candelabro", "aceite", "brasa",
            r"llamas?\b", "fire", "torch", "lamp", "candle", "flame", "bonfire"),
    "agua": ("agua", r"mar\b", r"rios?\b", "lago", "jordan", "olas",
             "diluvio", "barca", "pesca", "galilea", "pozo", "fuente", "orilla",
             "water", r"seas?\b", "river", "lake", "waves", "flood", "boat", "shore"),
    "nubes": ("cielo", "nube", "monte", "montana", "sinai", "horizonte",
              "sky", "cloud", "mountain", "horizon"),
    "lluvia": ("lluvia", "llovio", "llover", "diluvio", "rain", "flood"),
    "rayos": ("rayo", "relampago", "tormenta", "trueno", "tempestad",
              "lightning", "storm", "thunder", "tempest"),
    "gloria": ("gloria", "angel", "espiritu", "celestial", "divina", "divino",
               "resplandor", "milagro", "trono", "glory", "heaven", "divine",
               "holy", "miracle", "radiant"),
    # P4 (NIVEL PROFESIONAL): la figura recortada pasa a SILUETA a contraluz
    # con borde que brilla y haces detras (estilo «el rico y Lazaro»). Solo
    # cuaja si rembg separo una figura; sin ella se quita (ver `configurar`).
    "contraluz": ("contraluz", "silueta", "abismo", "hades", "infierno",
                  "tormento", "seno de abraham", "atardecer", "ocaso",
                  "amanecer", "puesta de sol", "anochecer", "backlit",
                  "silhouette", "sunset", "sunrise"),
}

# El color del borde y de los haces: fuego si el texto arde, oro si no.
_CONTRALUZ_FUEGO = ("infierno", "hades", "tormento", "fuego", "llama",
                    "abismo", "fire", "hell", "flame")
COLORES_CONTRALUZ = {"oro": (255, 214, 140), "fuego": (255, 120, 40),
                     "luna": (170, 200, 255)}


def _plano(texto):
    texto = unicodedata.normalize("NFKD", str(texto or "").lower())
    return "".join(c for c in texto if not unicodedata.combining(c)) + " "


def elegir(texto, forzados=None):
    """Los efectos de un plano. -> lista ordenada de EFECTOS.

    `forzados` (lista) manda si viene: es lo que pone el plan o el param. Las
    particulas van siempre (polvo en el aire): son las que hacen que una imagen
    quieta no parezca una foto pegada.
    """
    if isinstance(forzados, (list, tuple)):
        return [e for e in EFECTOS if e in forzados]
    t = _plano(texto)
    elegidos = {e for e, palabras in PALABRAS.items()
                if any(re.search(r"\b" + p, t) for p in palabras)}
    elegidos.add("particulas")
    if "rayos" in elegidos:
        elegidos.add("nubes")
    return [e for e in EFECTOS if e in elegidos]


# ------------------------------------------------------------- la imagen

def foco_de_luz(img):
    """Donde esta lo mas brillante de la imagen, en [0..1]. -> [x, y]

    Es donde se pone el resplandor que parpadea: si la imagen tiene una
    lampara o una hoguera, casi siempre es su punto mas claro.
    """
    peq = img.convert("L").resize((96, 64)).filter(ImageFilter.GaussianBlur(3))
    a = np.asarray(peq, dtype=np.float32)
    y, x = np.unravel_index(int(a.argmax()), a.shape)
    return [round((x + 0.5) / a.shape[1], 4), round((y + 0.5) / a.shape[0], 4)]


def _caja(a, k):
    """Media en caja de lado 2k+1 (separable, con sumas acumuladas)."""
    def eje(m, ax):
        m = np.swapaxes(m, 0, ax)
        p = np.pad(m, [(k + 1, k)] + [(0, 0)] * (m.ndim - 1), mode="edge")
        c = np.cumsum(p, axis=0)
        return np.swapaxes((c[2 * k + 1:] - c[:-2 * k - 1]) / (2 * k + 1), 0, ax)
    return eje(eje(a, 0), 1)


def _rellenar(img, hueco):
    """Tapa el hueco que deja la figura con lo que la rodea (a baja resolucion).

    Convolucion normalizada a varias escalas: cada pixel del hueco toma la
    media de los pixeles CONOCIDOS de alrededor, del radio mas pequeno que
    tenga suficientes. Queda un borron del fondo, que es justo lo que se ve
    tras una figura que se mueve unos pixeles.
    """
    ancho, alto = img.size
    f = 384.0 / max(ancho, alto)
    pw, ph = max(8, int(ancho * f)), max(8, int(alto * f))
    rgb = np.asarray(img.convert("RGB").resize((pw, ph), Image.BILINEAR),
                     dtype=np.float32)
    h = np.asarray(hueco.resize((pw, ph), Image.BILINEAR), dtype=np.float32) > 127
    conocido = (~h).astype(np.float32)
    lleno = rgb.copy()
    pendiente = h.copy()
    for k in (2, 4, 8, 16, 32, 64, 128):
        peso = _caja(conocido, k)
        suma = _caja(rgb * conocido[..., None], k)
        vale = pendiente & (peso > 0.05)
        lleno[vale] = suma[vale] / peso[vale][:, None]
        pendiente &= ~vale
        if not pendiente.any():
            break
    lleno = Image.fromarray(np.clip(lleno, 0, 255).astype(np.uint8))
    lleno = lleno.filter(ImageFilter.GaussianBlur(2)).resize((ancho, alto),
                                                            Image.BICUBIC)
    borde = hueco.filter(ImageFilter.GaussianBlur(max(2, ancho // 400)))
    return Image.composite(lleno, img.convert("RGB"), borde)


def sesion_recorte():
    """La sesion de rembg, o None si no esta instalado. Cargarla cuesta: UNA
    por render, en el proceso principal, nunca en los lotes."""
    try:
        from rembg import new_session
        return new_session(os.environ.get("ESTUDIO_REMBG_MODELO") or "u2net")
    except Exception as e:  # sin rembg el video sale igual, sin capas
        print(f"[ambiente] sin recorte de figura (rembg: {e})", flush=True)
        return None


def _huella(ruta, extra=""):
    st = os.stat(ruta)
    base = f"{os.path.abspath(ruta)}|{st.st_size}|{int(st.st_mtime)}|{extra}|v1"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def preparar(hyper, carpeta, sesion=None, profundidad=True):
    """Lo que la pagina necesita de la imagen de un plano. -> dict

    {"foco": [x, y]} siempre; y con figura recortada ademas
    {"fondo": png sin figura, "figura": png con transparencia, "ancla": [x, y]}.
    Se guarda en `carpeta` por huella de la imagen: rehacer el render no
    vuelve a recortar.
    """
    os.makedirs(carpeta, exist_ok=True)
    huella = _huella(hyper, "p" if (profundidad and sesion) else "")
    ficha = os.path.join(carpeta, f"{huella}.json")
    if os.path.exists(ficha):
        try:
            with open(ficha, "r", encoding="utf-8") as fh:
                datos = json.load(fh)
            if all(os.path.exists(datos[k]) for k in ("fondo", "figura")
                   if k in datos):
                return datos
        except (OSError, ValueError, KeyError):
            pass
    img = Image.open(hyper).convert("RGB")
    datos = {"foco": foco_de_luz(img)}
    if profundidad and sesion is not None:
        datos.update(_recortar(img, sesion, carpeta, huella))
    with open(ficha, "w", encoding="utf-8") as fh:
        json.dump(datos, fh)
    return datos


def _recortar(img, sesion, carpeta, huella):
    from rembg import remove
    mascara = remove(img, session=sesion, only_mask=True)
    if mascara.size != img.size:
        mascara = mascara.resize(img.size, Image.BILINEAR)
    a = np.asarray(mascara, dtype=np.uint8)
    figura_px = a > 127
    cubre = float(figura_px.mean())
    # Sin figura clara (un paisaje, un mapa) o con la «figura» comiendose el
    # cuadro, separar capas no aporta y el relleno se veria: se deja entera.
    if cubre < 0.02 or cubre > 0.6:
        return {}
    ys, xs = np.nonzero(figura_px)
    ancho, alto = img.size
    ancla = [round(float(xs.mean()) / ancho, 4),
             round(float(ys.max()) / alto, 4)]
    # El hueco, algo MAS GRANDE que la figura: la figura se mueve unos
    # pixeles y lo que asoma por detras tiene que ser fondo, no su contorno.
    k = max(3, (ancho // 90) | 1)
    peq = mascara.resize((ancho // 4, alto // 4), Image.BILINEAR)
    hueco = peq.point(lambda v: 255 if v > 20 else 0).filter(
        ImageFilter.MaxFilter(min(31, (k // 4) | 1)))
    hueco = hueco.resize(img.size, Image.BILINEAR)
    fondo = _rellenar(img, hueco)
    figura = img.convert("RGBA")
    figura.putalpha(mascara.filter(ImageFilter.GaussianBlur(1)))
    r_fondo = os.path.join(carpeta, f"{huella}_fondo.jpg")
    r_figura = os.path.join(carpeta, f"{huella}_figura.png")
    fondo.save(r_fondo, quality=92)
    figura.save(r_figura, optimize=False, compress_level=1)
    return {"fondo": r_fondo, "figura": r_figura, "ancla": ancla}


def color_contraluz(texto, pedido=None):
    """"oro" | "fuego" | "luna". `pedido` (param o plan) manda si es valido."""
    if pedido in COLORES_CONTRALUZ:
        return pedido
    t = _plano(texto)
    if any(re.search(r"\b" + p, t) for p in _CONTRALUZ_FUEGO):
        return "fuego"
    if re.search(r"\b(noche|luna|moon|night)", t):
        return "luna"
    return "oro"


def silueta(figura, carpeta, color="oro"):
    """La figura recortada vuelta SILUETA a contraluz. -> dict

    Tres cosas en UN png (se mueve con la figura sin capas de mas): el cuerpo
    casi negro con un poco de su color, un BORDE de luz por dentro del
    contorno (mas fuerte arriba, de donde viene la luz) y un HALO por fuera
    que se funde con el fondo. Devuelve la ruta y el centro/alto de la figura
    en [0..1] para poner detras el resplandor y los haces. Cache por huella.
    """
    huella = _huella(figura, "contraluz-" + color)
    ruta = os.path.join(carpeta, f"{huella}_silueta.png")
    ficha = ruta[:-4] + ".json"
    if os.path.exists(ruta) and os.path.exists(ficha):
        try:
            with open(ficha, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            pass
    img = Image.open(figura).convert("RGBA")
    ancho, alto = img.size
    alfa = img.getchannel("A")
    a = np.asarray(alfa, dtype=np.float32) / 255.0
    ys, xs = np.nonzero(a > 0.5)
    if not len(xs):
        return {}
    alto_fig = float(ys.max() - ys.min()) / alto
    col = np.array(COLORES_CONTRALUZ[color], dtype=np.float32)
    # radio del borde y del halo, proporcional a la figura (no al cuadro)
    r = max(2, int(alto_fig * alto * 0.012))
    dentro = np.asarray(alfa.filter(ImageFilter.MinFilter((r * 2) | 1)),
                        dtype=np.float32) / 255.0
    borde = np.clip(a - dentro, 0, 1)
    borde = np.asarray(Image.fromarray((borde * 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(r * 0.8)),
                       dtype=np.float32) / 255.0
    # la luz viene de detras y de arriba: el borde de arriba brilla mas
    fila = np.linspace(0, 1, alto, dtype=np.float32)[:, None]
    y0, y1 = ys.min() / alto, ys.max() / alto
    arriba = np.clip(1.15 - (fila - y0) / max(1e-3, y1 - y0) * 0.7, 0.35, 1)
    borde = np.clip(borde * 1.8 * arriba, 0, 1)
    halo = np.asarray(alfa.filter(ImageFilter.GaussianBlur(r * 4)),
                      dtype=np.float32) / 255.0
    halo = np.clip(halo * 1.3 - a, 0, 1) * 0.75
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
    cuerpo = rgb * 0.10 + np.array([8, 6, 10], dtype=np.float32)
    mezcla = cuerpo * (1 - borde[..., None]) + col * borde[..., None]
    # fuera del cuerpo solo hay halo: color puro, con su transparencia
    luz = np.clip(col * 1.0 + 30, 0, 255)
    salida = np.where(a[..., None] > 0.02, mezcla, luz)
    alfa_out = np.clip(np.maximum(a, halo), 0, 1)
    out = np.dstack([np.clip(salida, 0, 255), alfa_out * 255]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(ruta, optimize=False, compress_level=1)
    datos = {"figura": ruta, "color": color,
             "centro": [round(float(xs.mean()) / ancho, 4),
                        round(float(ys.mean()) / alto, 4)],
             "alto": round(alto_fig, 4)}
    with open(ficha, "w", encoding="utf-8") as fh:
        json.dump(datos, fh)
    return datos


def configurar(escena_plan, hyper, carpeta, p, sesion=None):
    """La configuracion de ambiente de UN plano para la pagina. -> dict|None"""
    modo = p.get("ambiente", "auto")
    if modo in ("no", False, None):
        return None
    forzados = escena_plan.get("ambiente") if isinstance(
        escena_plan.get("ambiente"), list) else None
    if forzados is None and isinstance(modo, (list, tuple)):
        forzados = list(modo)
    texto = " ".join(str(escena_plan.get(k) or "")
                     for k in ("narracion", "texto", "prompt", "descripcion",
                               "titulo"))
    efectos = elegir(texto, forzados)
    datos = preparar(hyper, carpeta, sesion,
                     profundidad=bool(p.get("profundidad", True)))
    # P4. Param `contraluz`: False lo apaga en todo el video; "oro" | "fuego" |
    # "luna" fija el color. En plan.json, `"contraluz": "fuego"` o False.
    pedido = escena_plan.get("contraluz", p.get("contraluz"))
    if pedido is False:
        efectos = [e for e in efectos if e != "contraluz"]
    elif pedido and "contraluz" not in efectos:
        efectos = [e for e in EFECTOS if e in set(efectos) | {"contraluz"}]
    if "contraluz" in efectos:
        sil = silueta(datos["figura"], carpeta,
                      color_contraluz(texto, pedido)) if datos.get("figura") else {}
        if sil:
            datos = dict(datos, figura=sil["figura"],
                         contraluz={k: sil[k] for k in ("color", "centro", "alto")})
        else:   # sin figura recortada no hay silueta que hacer
            efectos = [e for e in efectos if e != "contraluz"]
    return {"efectos": efectos, **datos,
            "semilla": int(hashlib.sha1(str(escena_plan.get("id")).encode())
                           .hexdigest()[:6], 16) % 997}


# ---------------------------------------------------------- en la pagina
#
# Va DENTRO de la pagina del render (p8_render.PAGINA). `ambiente(t, v, s)` se
# llama desde `pintar` con la ventana de camara ya calculada: v = [x, y, ancho]
# en pixeles del hyperframe y s la escala a la salida. Todo es funcion de t y
# de la semilla del plano: nada de Math.random ni de relojes.

AMBIENTE_JS = r"""
const fig = document.getElementById('figura');
const cAtras = document.getElementById('atras');
const cAgua = document.getElementById('agua');
const cDel = document.getElementById('delante');
const xA = cAtras ? cAtras.getContext('2d') : null;
const xW = cAgua ? cAgua.getContext('2d') : null;
const xD = cDel ? cDel.getContext('2d') : null;
const EF = new Set((AMB && AMB.efectos) || []);
const SEM = (AMB && AMB.semilla) || 0;
const TAU = Math.PI * 2;
const AGUA = 0.30;               // franja baja del hyperframe que ondula
function azar(n){ const x = Math.sin((n + SEM*7.31)*127.1 + 311.7)*43758.5453;
                  return x - Math.floor(x); }
function ruido(t, k){ const i = Math.floor(t), f = t - i;
  const a = azar(i + k*101), b = azar(i + 1 + k*101);
  return a + (b - a)*f*f*(3 - 2*f); }
let v0 = null;

function capaFigura(t, v, s){
  if (!fig) return;
  if (!v0) v0 = ventana(0);
  const PAR = 0.22;
  const cx = v[0] + v[2]/2, cx0 = v0[0] + v0[2]/2;
  const cy = v[1] + v[2]*H/W/2, cy0 = v0[1] + v0[2]*H/W/2;
  let dx = -(cx - cx0)*PAR + Math.sin(TAU*t/7.3)*HW*0.003;
  let dy = -(cy - cy0)*PAR + Math.sin(TAU*t/4.1 + 1.1)*HH*0.0025;
  const z = 1 + (v0[2]/v[2] - 1)*0.35;
  const rot = Math.sin(TAU*t/4.6)*0.6;
  const resp = 1 + 0.007*Math.sin(TAU*t/3.3);
  fig.style.transform = 'translate(' + dx.toFixed(2) + 'px,' + dy.toFixed(2) +
    'px) rotate(' + rot.toFixed(3) + 'deg) scale(' + z.toFixed(5) + ',' +
    (z*resp).toFixed(5) + ')';
}

function nubes(t){
  if (!xA) return;
  const w = cAtras.width, h = cAtras.height;
  xA.clearRect(0, 0, w, h);
  if (!EF.has('nubes')) return;
  const tormenta = EF.has('rayos') || EF.has('lluvia');
  for (let i = 0; i < 7; i++){
    const vel = 0.006 + azar(i+3)*0.012;
    let x = ((azar(i)*1.6 + t*vel) % 1.6) - 0.3;
    const y = 0.04 + azar(i+9)*0.30, r = (0.09 + azar(i+5)*0.10)*w;
    for (let j = 0; j < 5; j++){
      const px = (x + (azar(i*13+j)-0.5)*0.12)*w;
      const py = y*h + (azar(i*17+j)-0.5)*r*0.5;
      const pr = r*(0.5 + azar(i*19+j)*0.6);
      const g = xA.createRadialGradient(px, py, 0, px, py, pr);
      const c = tormenta ? '70,74,88' : '255,255,255';
      g.addColorStop(0, 'rgba(' + c + ',' + (tormenta ? 0.30 : 0.20) + ')');
      g.addColorStop(1, 'rgba(' + c + ',0)');
      xA.fillStyle = g;
      xA.fillRect(px - pr, py - pr, pr*2, pr*2);
    }
  }
}

// P4. CONTRALUZ: detras de la silueta, un resplandor que respira y haces que
// salen de la figura hacia fuera, girando muy despacio. Va en #atras (dentro
// de la camara, debajo de la figura), asi que acompana al zoom.
function contraluz(t){
  if (!xA || !EF.has('contraluz') || !AMB.contraluz) return;
  const C = AMB.contraluz, w = cAtras.width, h = cAtras.height;
  const col = C.color === 'fuego' ? '255,120,40' :
              (C.color === 'luna' ? '170,200,255' : '255,214,140');
  const X = C.centro[0]*w, Y = (C.centro[1] - C.alto*0.12)*h;
  const R = Math.max(w, h)*(0.25 + C.alto*0.35);
  const resp = 0.85 + 0.15*ruido(t*1.4, 7);
  xA.globalCompositeOperation = 'lighter';
  let g = xA.createRadialGradient(X, Y, 0, X, Y, R);
  g.addColorStop(0, 'rgba(255,250,235,' + (0.55*resp).toFixed(3) + ')');
  g.addColorStop(0.25, 'rgba(' + col + ',' + (0.40*resp).toFixed(3) + ')');
  g.addColorStop(1, 'rgba(' + col + ',0)');
  xA.fillStyle = g; xA.fillRect(X - R, Y - R, R*2, R*2);
  const n = 14, largo = Math.max(w, h)*1.1, giro = t*0.025;
  for (let i = 0; i < n; i++){
    const a = TAU*i/n + giro + (azar(i+300) - 0.5)*0.3;
    const an = 0.025 + azar(i+310)*0.04;
    const al = (0.05 + 0.07*ruido(t*0.6, i + 320))*resp;
    const gr = xA.createRadialGradient(X, Y, R*0.1, X, Y, largo);
    gr.addColorStop(0, 'rgba(' + col + ',' + al.toFixed(3) + ')');
    gr.addColorStop(1, 'rgba(' + col + ',0)');
    xA.fillStyle = gr;
    xA.beginPath(); xA.moveTo(X, Y);
    xA.lineTo(X + Math.cos(a - an)*largo, Y + Math.sin(a - an)*largo);
    xA.lineTo(X + Math.cos(a + an)*largo, Y + Math.sin(a + an)*largo);
    xA.closePath(); xA.fill();
  }
  xA.globalCompositeOperation = 'source-over';
}

function agua(t){
  if (!xW || !EF.has('agua')) return;
  const w = cAgua.width, h = cAgua.height, y0 = HH*(1 - AGUA);
  const fuente = fondo;
  xW.globalCompositeOperation = 'source-over';
  xW.clearRect(0, 0, w, h);
  const paso = 3, amp = HW*0.0035;
  for (let y = 0; y < h; y += paso){
    const prof = y / h;
    const off = Math.sin(y*0.05 + t*2.6) * amp * (0.3 + prof) +
                Math.sin(y*0.013 - t*1.3) * amp * 0.6;
    xW.drawImage(fuente, 0, y0 + y, HW, paso, -amp*2 + off, y, w + amp*4, paso);
  }
  // destellos sobre el agua
  xW.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 60; i++){
    const brillo = Math.max(0, Math.sin(TAU*(t*0.7 + azar(i+40))) );
    if (brillo < 0.6) continue;
    const x = azar(i+50)*w, y = (0.15 + azar(i+60)*0.85)*h;
    xW.fillStyle = 'rgba(255,250,230,' + ((brillo - 0.6)*0.9).toFixed(3) + ')';
    xW.fillRect(x, y, HW*0.012*(0.5 + azar(i+70)), HH*0.0016);
  }
  // la franja entra fundida por arriba: no hay costura con el fondo quieto
  xW.globalCompositeOperation = 'destination-in';
  const g = xW.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.18, 'rgba(0,0,0,1)');
  g.addColorStop(1, 'rgba(0,0,0,1)');
  xW.fillStyle = g; xW.fillRect(0, 0, w, h);
  xW.globalCompositeOperation = 'source-over';
}

function delante(t, v, s){
  if (!xD) return;
  const k = W / 1080;          // tamanos pensados en 1080 de ancho
  xD.clearRect(0, 0, W, H);
  const tormenta = EF.has('rayos') || EF.has('lluvia');
  if (tormenta){ xD.fillStyle = 'rgba(12,18,38,0.22)'; xD.fillRect(0,0,W,H); }

  if (EF.has('luz')){
    const f = (AMB.foco || [0.5, 0.4]);
    const X = (f[0]*HW - v[0])*s, Y = (f[1]*HH - v[1])*s;
    const fl = 0.72 + 0.28*(0.6*ruido(t*6, 1) + 0.4*ruido(t*15, 2));
    const r = Math.max(W, H)*0.42*(0.9 + 0.1*fl);
    xD.globalCompositeOperation = 'screen';
    const g = xD.createRadialGradient(X, Y, 0, X, Y, r);
    g.addColorStop(0, 'rgba(255,180,90,' + (0.42*fl).toFixed(3) + ')');
    g.addColorStop(0.35, 'rgba(255,130,40,' + (0.16*fl).toFixed(3) + ')');
    g.addColorStop(1, 'rgba(255,120,30,0)');
    xD.fillStyle = g; xD.fillRect(0, 0, W, H);
    xD.globalCompositeOperation = 'source-over';
    xD.fillStyle = 'rgba(15,6,0,' + (0.16*(1 - fl)).toFixed(3) + ')';
    xD.fillRect(0, 0, W, H);
  }

  if (EF.has('gloria')){
    xD.globalCompositeOperation = 'screen';
    const ox = W*0.5, oy = -H*0.12;
    for (let i = 0; i < 7; i++){
      const a = Math.PI/2 + (i - 3)*0.17 + Math.sin(t*0.35 + i)*0.04;
      const al = 0.07 + 0.05*ruido(t*0.8, i + 20);
      const largo = H*1.3, ancho = 0.05 + azar(i+80)*0.05;
      xD.fillStyle = 'rgba(255,235,170,' + al.toFixed(3) + ')';
      xD.beginPath(); xD.moveTo(ox, oy);
      xD.lineTo(ox + Math.cos(a - ancho)*largo, oy + Math.sin(a - ancho)*largo);
      xD.lineTo(ox + Math.cos(a + ancho)*largo, oy + Math.sin(a + ancho)*largo);
      xD.closePath(); xD.fill();
    }
    xD.globalCompositeOperation = 'source-over';
  }

  if (EF.has('particulas')){
    const brasas = EF.has('luz'), oro = EF.has('gloria');
    const n = brasas ? 55 : 45;
    xD.globalCompositeOperation = 'screen';
    for (let i = 0; i < n; i++){
      const sube = brasas ? 0.05 + azar(i+1)*0.07 : 0.008 + azar(i+1)*0.02;
      const y = 1.05 - ((azar(i+2)*1.1 + t*sube) % 1.1);
      const x = azar(i+3) + Math.sin(t*(0.3 + azar(i+4)*0.6) + i)*0.02;
      const tam = (brasas ? 1.6 + azar(i+5)*2.4 : 1.2 + azar(i+5)*3.0)*k;
      const vivo = 0.35 + 0.65*Math.abs(Math.sin(t*(0.8 + azar(i+6)*2) + i));
      const col = brasas ? '255,150,60' : (oro ? '255,225,140' : '255,245,225');
      const g = xD.createRadialGradient(x*W, y*H, 0, x*W, y*H, tam*3);
      g.addColorStop(0, 'rgba(' + col + ',' + (0.85*vivo).toFixed(3) + ')');
      g.addColorStop(1, 'rgba(' + col + ',0)');
      xD.fillStyle = g;
      xD.fillRect(x*W - tam*3, y*H - tam*3, tam*6, tam*6);
    }
    xD.globalCompositeOperation = 'source-over';
  }

  if (EF.has('lluvia')){
    xD.strokeStyle = 'rgba(200,215,255,0.32)';
    xD.lineWidth = 1.4*k;
    xD.beginPath();
    for (let i = 0; i < 160; i++){
      const vel = 1.6 + azar(i+90)*0.8;
      const y = ((azar(i+91) + t*vel) % 1.2) - 0.1;
      const x = azar(i+92)*1.2 - 0.1 - y*0.12;
      const l = (0.03 + azar(i+93)*0.03);
      xD.moveTo(x*W, y*H); xD.lineTo((x - l*0.12)*W, (y + l)*H*0.56);
    }
    xD.stroke();
  }

  if (EF.has('rayos')){
    const per = 3.4, n = Math.floor(t/per);
    for (let m = n - 1; m <= n; m++){
      if (m < 0) continue;
      const te = m*per + 0.5 + azar(m+200)*1.8, dt = t - te;
      if (dt < 0 || dt > 0.5) continue;
      let I = dt < 0.05 ? 1 : Math.exp(-(dt - 0.05)*10);
      if (dt > 0.12 && dt < 0.2) I = Math.max(I, 0.7);
      xD.fillStyle = 'rgba(225,232,255,' + (0.5*I).toFixed(3) + ')';
      xD.fillRect(0, 0, W, H);
      xD.strokeStyle = 'rgba(255,255,255,' + I.toFixed(3) + ')';
      xD.shadowColor = 'rgba(170,190,255,1)'; xD.shadowBlur = 18*k;
      xD.lineWidth = 3.5*k;
      let x = (0.2 + azar(m+210)*0.6)*W, y = 0;
      xD.beginPath(); xD.moveTo(x, y);
      for (let j = 0; j < 14; j++){
        x += (azar(m*31 + j) - 0.5)*W*0.09; y += H*0.035;
        xD.lineTo(x, y);
      }
      xD.stroke(); xD.shadowBlur = 0;
    }
  }

  // vineta: siempre, suave. Centra la mirada y oculta los bordes del cuadro.
  const g = xD.createRadialGradient(W/2, H*0.45, Math.min(W,H)*0.35,
                                    W/2, H*0.45, Math.max(W,H)*0.75);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.42)');
  xD.fillStyle = g; xD.fillRect(0, 0, W, H);
}

function ambiente(t, v, s){
  capaFigura(t, v, s);
  nubes(t);
  contraluz(t);
  agua(t);
  delante(t, v, s);
}
"""


def html_capas(amb, hw, hh, ancho, alto):
    """Los elementos que la pagina anade dentro y fuera de la camara."""
    if not amb:
        return "", "", ""
    dentro = ""
    if "agua" in amb.get("efectos", []):
        dentro += (f'<canvas id="agua" width="{hw}" height="{int(hh * 0.30)}"'
                   f' class="amb-agua"></canvas>')
    dentro += (f'<canvas id="atras" width="{hw // 2}" height="{hh // 2}"'
               f' class="amb-atras"></canvas>')
    if amb.get("figura"):
        dentro += (f'<img id="figura" src="file:///'
                   f'{os.path.abspath(amb["figura"]).replace(os.sep, "/")}">')
    fuera = f'<canvas id="delante" width="{ancho}" height="{alto}"></canvas>'
    ancla = amb.get("ancla") or [0.5, 1.0]
    css = (f"#atras{{position:absolute;left:0;top:0;width:{hw}px;"
           f"height:{hh}px}}"
           f"#agua{{position:absolute;left:0;top:{hh - int(hh * 0.30)}px;"
           f"width:{hw}px;height:{int(hh * 0.30)}px}}"
           f"#figura{{position:absolute;left:0;top:0;width:{hw}px;"
           f"height:{hh}px;transform-origin:{ancla[0] * hw:.1f}px "
           f"{ancla[1] * hh:.1f}px;will-change:transform}}"
           f"#delante{{position:absolute;left:0;top:0;width:{ancho}px;"
           f"height:{alto}px;z-index:1}}")
    return dentro, fuera, css
