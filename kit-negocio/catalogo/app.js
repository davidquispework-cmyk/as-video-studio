/* Catálogo: lee productos.json y pinta las prendas. Sin dependencias. */
let DATOS = { productos: [] };
const $ = s => document.querySelector(s);

function h(tag, props = {}, ...hijos) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'clase') n.className = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? '' : v);
  }
  hijos.flat().forEach(x => x !== null && x !== undefined
    && n.append(x instanceof Node ? x : document.createTextNode(String(x))));
  return n;
}

function enlaceWhatsApp(p, talla, color) {
  const texto = `Hola, quiero pedir: ${p.nombre}`
    + (talla ? ` · talla ${talla}` : '') + (color ? ` · color ${color}` : '')
    + ` · ${DATOS.moneda || 'S/'} ${p.precio}`;
  return `https://wa.me/${DATOS.whatsapp}?text=${encodeURIComponent(texto)}`;
}

function tarjeta(p) {
  const selTalla = h('select', { clase: 'mini', 'aria-label': 'Talla' },
    ...(p.tallas || []).map(t => h('option', { value: t }, `Talla ${t}`)));
  const selColor = h('select', { clase: 'mini', 'aria-label': 'Color' },
    ...(p.colores || []).map(c => h('option', { value: c }, c)));
  return h('article', { clase: `prenda${p.agotado ? ' agotado' : ''}` },
    h('div', { clase: 'foto' }, p.foto ? h('img', { src: p.foto, alt: p.nombre, loading: 'lazy' }) : 'Sin foto'),
    h('div', { clase: 'info' },
      h('h2', {}, p.nombre),
      h('div', { clase: 'precio' }, `${DATOS.moneda || 'S/'} ${p.precio}`),
      h('div', { clase: 'meta' }, p.categoria),
      (p.tallas || []).length ? selTalla : null,
      (p.colores || []).length > 1 ? selColor : null,
      h('button', {
        clase: 'pedir', disabled: p.agotado,
        onclick: () => window.open(enlaceWhatsApp(p, selTalla.value,
          (p.colores || []).length > 1 ? selColor.value : (p.colores || [])[0]), '_blank'),
      }, p.agotado ? 'Agotado' : 'Pedir por WhatsApp')));
}

function pintar() {
  const busca = $('#busca').value.trim().toLowerCase();
  const cat = $('#categoria').value;
  const talla = $('#talla').value;
  const lista = DATOS.productos.filter(p =>
    (!busca || p.nombre.toLowerCase().includes(busca))
    && (!cat || p.categoria === cat)
    && (!talla || (p.tallas || []).includes(talla)));
  $('#rejilla').replaceChildren(...lista.map(tarjeta));
  $('#vacio').hidden = lista.length > 0;
}

async function arrancar() {
  DATOS = await (await fetch('productos.json', { cache: 'no-cache' })).json();
  document.title = `${DATOS.tienda} · Catálogo`;
  $('#tienda').textContent = DATOS.tienda;
  $('#eslogan').textContent = DATOS.eslogan || '';
  $('#pie-tienda').textContent = DATOS.tienda;
  const cats = [...new Set(DATOS.productos.map(p => p.categoria))].sort();
  const tallas = [...new Set(DATOS.productos.flatMap(p => p.tallas || []))];
  cats.forEach(c => $('#categoria').append(h('option', { value: c }, c)));
  tallas.forEach(t => $('#talla').append(h('option', { value: t }, t)));
  ['#busca', '#categoria', '#talla'].forEach(s => $(s).addEventListener('input', pintar));
  $('#pdf').addEventListener('click', () => window.print());
  pintar();
}
arrancar().catch(e => { $('#rejilla').textContent = `No se pudo cargar el catálogo: ${e.message}`; });
