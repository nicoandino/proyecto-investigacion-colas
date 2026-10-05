"""Reproductor de la animación del playón (ORQUESTADOR §8.5).

Cómo funciona
-------------
El motor deja en la traza una foto del sistema cada `dt` minutos simulados, durante el
día elegido. Acá esas fotos se pasan a formato COLUMNAR (un arreglo por variable, no
listas posicionales) y se mandan al navegador junto con un reproductor que las dibuja
en SVG.

Por qué el dibujo se hace en el navegador y no en Python: cada refresco del lado del
servidor cuesta casi un segundo (ida y vuelta por websocket más volver a montar el
componente), así que la película se veía a los saltos. Con el reproductor del lado del
cliente la animación corre a la velocidad de la pantalla y los botones responden al
instante.

Es la única parte del proyecto con JavaScript, y está acotada a dibujar: no simula nada.
Los colores NO están hardcodeados acá: llegan por JSON desde `ui/tema.py` (N15).

Qué se ve (de las capturas del grupo): la avenida Balloffet con la entrada, el playón
techado con las zonas A (nafta), B (diésel) y C (GNC) y sus 12 caras, la cola de cada
zona (que desborda hacia la avenida cuando se llena), los playeros, el minimarket, un
tanque por producto y el camión en viaje. Nada se comunica sólo con el color: cada
estado lleva su texto.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from sim.config import ANO_REFERENCIA, ParametrosSimulacion
from sim.red import ETIQUETA_ESCENARIO, descripcion_ruta
from sim.traza import Cuadro, Traza
from ui.tema import COLOR_PRODUCTO, PRODUCTO, paleta_json

#: Alto del componente en píxeles (barra de controles + dibujo).
ALTO_COMPONENTE = 820


def _columnas(cuadros: list[Cuadro], ids_grupos: list[str], ids_tanques: list[str]) -> dict:
    """Cuadros en formato columnar: un arreglo por variable (`round` para que pese poco)."""
    salida: dict = {
        "t": [round(c.minuto_del_dia, 2) for c in cuadros],
        "playTurno": [c.playeros_en_turno for c in cuadros],
        "playOcup": [c.playeros_ocupados for c in cuadros],
        "cajasOcup": [c.cajas_ocupadas for c in cuadros],
        "colaCaja": [c.cola_caja for c in cuadros],
        "atend": [c.atendidos for c in cuadros],
        "compras": [c.compras for c in cuadros],
        "pEsp": [c.perdidos_surtidor for c in cuadros],
        "pSin": [c.perdidos_sin_combustible for c in cuadros],
        "pLlena": [c.perdidos_cola_llena for c in cuadros],
        "pCaja": [c.perdidos_caja for c in cuadros],
        "gnc": [c.gnc_cortado for c in cuadros],
        "calent": [1 if c.en_calentamiento else 0 for c in cuadros],
        "g": {},
        "tk": {},
    }
    for i, id_grupo in enumerate(ids_grupos):
        fotos = [c.grupos[i] for c in cuadros]      # (id, carriles, cola, largo, rechazados)
        salida["g"][id_grupo] = {
            "c": [list(f[1]) for f in fotos],
            "q": [list(f[2]) for f in fotos],
            "n": [f[3] for f in fotos],
            "r": [f[4] for f in fotos],
        }
    for i, id_tanque in enumerate(ids_tanques):
        fotos = [c.tanques[i] for c in cuadros]     # (producto, nivel, camino, progreso, horas)
        salida["tk"][id_tanque] = {
            "n": [round(f[1]) for f in fotos],
            "c": [round(f[2]) for f in fotos],
            "p": [round(f[3], 3) for f in fotos],
            "h": [round(f[4], 1) for f in fotos],
            "d": [round(f[5], 1) for f in fotos],
        }
    return salida


def minimo_de_carga(p: ParametrosSimulacion, producto: str) -> float:
    """Menor carga posible de un producto: bajo ese nivel el tanque 'no tiene combustible'
    para nadie (misma regla que usa el motor para el cartel de falta de combustible)."""
    matriz = dict(p.matriz_tipos)[producto]
    posibles = [
        t.litros.minimo
        for t, peso in zip(p.tipos_vehiculo, matriz)
        if peso > 0 and not t.es_gnc
    ]
    return min(posibles)


_DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
_MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre")


def fecha_texto(p: ParametrosSimulacion, dia: int) -> str:
    """'miércoles 7 de enero · día hábil' para el día `dia` de la corrida."""
    mes, dia_semana = p._fecha_del_dia(dia)
    inicio = date(ANO_REFERENCIA, p.fecha_inicio[0], p.fecha_inicio[1])
    fecha = inicio + timedelta(days=dia - 1)
    tipo = "fin de semana" if dia_semana >= 5 else "día hábil"
    return f"{_DIAS[dia_semana]} {fecha.day} de {_MESES[mes - 1]} · {tipo}"


def _texto_ruta(p: ParametrosSimulacion) -> dict:
    """Ruta del camión y escenario de cortes para el panel (sin red: el caso clásico)."""
    if p.red is None:
        return {"detalle": "", "escenario": "proveedor → estación"}
    escenario = ETIQUETA_ESCENARIO.get(p.red.escenario_corte, f"Corte {p.red.escenario_corte}")
    ruta = descripcion_ruta(p.red).rsplit(" · ", 1)[0]      # sin las horas
    return {"detalle": ruta, "escenario": escenario}


def _configuracion(
    traza: Traza, p: ParametrosSimulacion, dia: int, fecha_texto: str
) -> dict:
    """Todo lo que el navegador necesita: estructura de la estación + cuadros."""
    if p.estacion_real:
        productos = [
            {
                "id": pr.id,
                "nombre": pr.nombre,
                "color": COLOR_PRODUCTO[pr.id],
                "gnc": pr.es_gnc,
            }
            for pr in p.productos
        ]
        inventario = {i.producto: i for i in p.inventario}
        for prod in productos:
            inv = inventario.get(prod["id"])
            prod["capacidad"] = inv.capacidad if inv else 0.0
            prod["puntoPedido"] = inv.punto_pedido if inv else 0.0
            prod["minimo"] = minimo_de_carga(p, prod["id"]) if inv else 0.0
        indice = {pr["id"]: k for k, pr in enumerate(productos)}
        grupos = [
            {
                "id": g.id,
                "nombre": g.nombre,
                "caras": g.caras,
                "productos": [indice[x] for x in g.productos],
                "playero": g.requiere_playero,
                "cap": p.capacidad_cola,
            }
            for g in p.grupos
        ]
        ids_tanques = [i.producto for i in p.inventario]
    else:
        productos = [
            {
                "id": "super",
                "nombre": "Combustible",
                "color": PRODUCTO["super"],
                "gnc": False,
                "capacidad": p.tanque.capacidad,
                "puntoPedido": p.tanque.punto_pedido,
                "minimo": p.litros.minimo,
            }
        ]
        grupos = [
            {
                "id": "A",
                "nombre": "Surtidores",
                "caras": p.surtidores,
                "productos": [0],
                "playero": False,
                "cap": None,
            }
        ]
        ids_tanques = ["super"]
    ids_grupos = [g["id"] for g in grupos]
    return {
        "dt": float(p.dt_traza),
        "dia": int(dia),
        "fecha": fecha_texto,
        "real": bool(p.estacion_real),
        "grupos": grupos,
        "productos": productos,
        "tanques": ids_tanques,
        "ruta": _texto_ruta(p),
        "cajas": int(p.cajas),
        "probCompra": float(p.prob_compra),
        "frames": _columnas(traza.cuadros, ids_grupos, ids_tanques),
        "paleta": paleta_json(),
    }


def reproductor_html(
    traza: Traza,
    p: ParametrosSimulacion,
    dia: int,
    fecha_texto: str = "",
) -> str:
    """Devuelve el HTML completo del reproductor, listo para `st.components.v1.html`."""
    configuracion = _configuracion(traza, p, dia, fecha_texto)
    return _PLANTILLA.replace("__CONFIG__", json.dumps(configuracion, separators=(",", ":")))


_PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  :root {
    --panel: transparent; --borde: transparent; --tinta: transparent;
    --tenue: transparent; --amarillo: transparent; --rojo: transparent;
    --fondo: transparent;
  }
  html, body { margin: 0; padding: 0; height: 100%; background: transparent; overflow: hidden;
               font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  #contenedor { display: flex; flex-direction: column; height: 100%; }
  #controles { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding: 4px 2px 8px;
               color: var(--tinta); font-size: 13px; }
  button, select { background: var(--fondo); color: var(--tinta); border: 1px solid var(--borde);
           border-radius: 7px; padding: 7px 12px; font-size: 13px; cursor: pointer;
           font-family: inherit; }
  button:hover:not(:disabled) { border-color: var(--tinta); }
  button:disabled { opacity: 0.45; cursor: not-allowed; }
  button:focus-visible, select:focus-visible, input:focus-visible { outline: 3px solid var(--tinta);
           outline-offset: 2px; }
  #play { background: var(--amarillo); color: var(--tinta); border-color: var(--tinta);
          font-weight: 700; min-width: 118px; }
  #barra { flex: 1; min-width: 160px; accent-color: var(--rojo); }
  #reloj { color: var(--tenue); min-width: 150px; font-variant-numeric: tabular-nums; }
  #saltos { display: flex; gap: 6px; flex-wrap: wrap; width: 100%; padding-top: 2px; }
  #saltos .rotulo { color: var(--tenue); align-self: center; font-size: 12px; }
  #lienzo { flex: 1; min-height: 0; }
  svg { width: 100%; height: 100%; display: block; }
</style>
</head>
<body>
<div id="contenedor">
  <div id="controles">
    <button id="play" type="button">▶ Reproducir</button>
    <button id="reiniciar" type="button">⏮ Reiniciar</button>
    <label class="rotulo" for="velocidad" style="color:var(--tenue)">Velocidad</label>
    <select id="velocidad" title="Minutos simulados por segundo real">
      <option value="30">30 min/s</option>
      <option value="60">1 h/s</option>
      <option value="120">2 h/s</option>
      <option value="240">4 h/s</option>
      <option value="480">8 h/s</option>
    </select>
    <input type="range" id="barra" min="0" value="0" step="1" aria-label="Posición dentro del día">
    <span id="reloj" aria-live="off"></span>
    <div id="saltos">
      <span class="rotulo">Saltar a:</span>
      <button id="saltoPico" type="button">⏭ la hora pico</button>
      <button id="saltoQuiebre" type="button">⏭ el primer quiebre</button>
      <button id="saltoDescarga" type="button">⏭ la próxima descarga</button>
      <button id="saltoCorte" type="button">⏭ el corte de GNC</button>
    </div>
  </div>
  <div id="lienzo"></div>
</div>

<script>
const CONFIG = __CONFIG__;

// --- Paleta (llega por JSON desde ui/tema.py) --------------------------------
const P = CONFIG.paleta;
const RAIZ = document.documentElement;
for (const [css, clave] of [["--panel", "panel"], ["--borde", "borde"], ["--tinta", "tinta"],
     ["--tenue", "tenue"], ["--amarillo", "amarillo"], ["--rojo", "rojo"], ["--fondo", "fondo"]]) {
  RAIZ.style.setProperty(css, P[clave]);
}
const REDUCIDO = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// --- Geometría del lienzo ----------------------------------------------------
const W = 1200, H = 752;
const LANE = 56;              // ancho de una cara (y de un lugar de la cola)
const SLOT_H = 48;            // alto de un lugar de la cola
const X0 = 16, GAP = 12, PAD = 12;
const Y_AV = 66, Y_TECHO = 124, Y_ZONA = 148;
const Y_COLA_TOPE = 224, MAX_FILAS = 4;
const Y_COLA_BASE = Y_COLA_TOPE + MAX_FILAS * SLOT_H;      // 416
const Y_CARRIL = Y_COLA_BASE + 4, Y_BOMBA = Y_CARRIL + 62;  // 420 · 482
const Y_ESTADO = Y_BOMBA + 62, Y_PERSONAL = Y_ESTADO + 16;
const Y_TANQUES = 648;

const F = CONFIG.frames;
const NCUADROS = F.t.length;
const GRUPOS = CONFIG.grupos, PROD = CONFIG.productos;

// Posición de cada zona (de izquierda a derecha)
let cursor = X0;
for (const g of GRUPOS) {
  g.x = cursor; g.w = g.caras * LANE + 2 * PAD;
  cursor += g.w + GAP;
}
const X_FIN_ZONAS = cursor - GAP;
const X_MINI = Math.max(X_FIN_ZONAS + 16, 812), W_MINI = W - 16 - X_MINI;
const TANQUES = CONFIG.tanques.map((id) => PROD.findIndex((x) => x.id === id));

// --- Piezas del dibujo -------------------------------------------------------
function esc(t) { return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
function miles(n) { return Math.round(n).toLocaleString("es-AR"); }
function reloj(m) {
  const k = Math.floor(m);
  return String(Math.floor(k / 60) % 24).padStart(2, "0") + ":" + String(k % 60).padStart(2, "0");
}

// Auto visto desde arriba: el frente (parabrisas y faros) mira hacia el surtidor.
function autoV(cx, cy, color, anillo) {
  const aro = anillo
    ? `<rect x="-19" y="-27" width="38" height="54" rx="11" fill="none" stroke="${P.naranja}"
         stroke-width="3" stroke-dasharray="5 3"/>`
    : "";
  return `<g transform="translate(${cx},${cy})">${aro}
    <rect x="-14" y="-22" width="28" height="44" rx="8" fill="${color}" stroke="${P.fondo}" stroke-width="1.6"/>
    <rect x="-10" y="2" width="20" height="9" rx="3" fill="${P.vidrio}" opacity="0.6"/>
    <rect x="-10" y="-14" width="20" height="6" rx="2" fill="${P.vidrio}" opacity="0.4"/>
    <circle cx="-8" cy="19" r="2.2" fill="${P.faros}"/><circle cx="8" cy="19" r="2.2" fill="${P.faros}"/>
  </g>`;
}

// Auto de costado (sobre la avenida)
function autoH(cx, cy, color) {
  return `<g transform="translate(${cx},${cy})">
    <rect x="-22" y="-9" width="44" height="18" rx="6" fill="${color}" stroke="${P.fondo}" stroke-width="1.4"/>
    <rect x="-8" y="-6" width="14" height="12" rx="3" fill="${P.vidrio}" opacity="0.5"/>
    <circle cx="20" cy="-5" r="1.8" fill="${P.faros}"/><circle cx="20" cy="5" r="1.8" fill="${P.faros}"/>
  </g>`;
}

function persona(cx, cy, relleno, trazo) {
  return `<g transform="translate(${cx},${cy})">
    <circle cx="0" cy="-8" r="5.5" fill="${relleno}" stroke="${trazo}" stroke-width="1.6"/>
    <path d="M -8 11 Q -8 0 0 0 Q 8 0 8 11 Z" fill="${relleno}" stroke="${trazo}" stroke-width="1.6"/>
  </g>`;
}

function camionIcono(cx, cy, color) {
  return `<g transform="translate(${cx},${cy}) scale(0.62)">
    <rect x="-24" y="-11" width="32" height="20" rx="5" fill="${color}" stroke="${P.tinta}" stroke-width="1.6"/>
    <rect x="8" y="-6" width="15" height="15" rx="3" fill="${P.plata}" stroke="${P.tinta}" stroke-width="1.6"/>
    <circle cx="-14" cy="11" r="4.2" fill="${P.neumatico}"/><circle cx="14" cy="11" r="4.2" fill="${P.neumatico}"/>
  </g>`;
}

function texto(x, y, t, tam, opc) {
  const o = opc || {};
  return `<text x="${x}" y="${y}" fill="${o.color || P.tinta}" font-size="${tam}"
    font-weight="${o.peso || 400}" text-anchor="${o.ancla || "start"}"
    ${o.espaciado ? `letter-spacing="${o.espaciado}"` : ""}>${esc(t)}</text>`;
}

function pastilla(x, y, ancho, alto, relleno, trazo, t, colorTexto) {
  return `<rect x="${x}" y="${y}" width="${ancho}" height="${alto}" rx="${alto / 2}" fill="${relleno}"
      stroke="${trazo}" stroke-width="1.5"/>` +
    texto(x + ancho / 2, y + alto / 2 + 4.5, t, 13, { ancla: "middle", peso: 700, color: colorTexto });
}

// --- Un cuadro ---------------------------------------------------------------
function sinCombustible(i) {
  const lista = [];
  CONFIG.tanques.forEach((id, k) => {
    const prod = PROD[TANQUES[k]];
    if (F.tk[id].n[i] < prod.minimo) lista.push(prod.nombre);
  });
  return lista;
}

function dibujar(i) {
  const t = F.t[i];
  const faltantes = sinCombustible(i);
  const hayCorte = F.gnc[i] === 1;
  const ventana = Math.max(1, Math.round(20 / CONFIG.dt));      // los últimos 20 min simulados
  let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img"
    aria-label="Playón de la estación a las ${reloj(t)}" preserveAspectRatio="xMidYMid meet">`;
  s += `<rect width="${W}" height="${H}" rx="10" fill="${P.fondo}"/>`;

  // ---------------- Barra superior ----------------
  s += `<rect width="${W}" height="60" rx="10" fill="${P.panel}"/>
        <line x1="0" y1="60" x2="${W}" y2="60" stroke="${P.borde}" stroke-width="2"/>`;
  s += texto(20, 36, reloj(t), 30, { peso: 700 });
  s += texto(122, 28, CONFIG.fecha || `Día ${CONFIG.dia}`, 13, { peso: 600 });
  if (faltantes.length) {
    s += pastilla(122, 36, 232, 22, P.rojo, P.rojo, "SIN COMBUSTIBLE", P.fondo);
  } else if (F.calent[i]) {
    s += pastilla(122, 36, 232, 22, P.amarilloSuave, P.naranja, "CALENTAMIENTO (no se mide)", P.tinta);
  } else {
    s += pastilla(122, 36, 232, 22, P.fondo, P.libre, "MIDIENDO INDICADORES", P.tinta);
  }
  const marcadores = [
    [F.atend[i], "cargaron", P.libre, false],
    [F.compras[i], "compraron", P.libre, false],
    [F.pEsp[i], "se cansaron", P.rojo, true],
    [F.pLlena[i], "cola llena", P.rojo, true],
    [F.pSin[i], "sin combustible", P.rojo, true],
    [F.pCaja[i], "dejaron la caja", P.rojo, true],
  ];
  let mx = 380;
  for (const [valor, etiqueta, color, perdida] of marcadores) {
    s += texto(mx, 33, valor, 22, { peso: 700 });
    s += `<rect x="${mx}" y="42" width="9" height="9" rx="2" fill="${color}"/>`;
    s += texto(mx + 14, 51, etiqueta, 12, { color: P.tenue });
    mx += 134;
  }

  // ---------------- Avenida ----------------
  s += `<rect x="0" y="${Y_AV}" width="${W}" height="48" fill="${P.asfalto}"/>
        <line x1="0" y1="${Y_AV + 24}" x2="${W}" y2="${Y_AV + 24}" stroke="${P.linea}"
              stroke-width="2" stroke-dasharray="26 18" opacity="0.7"/>`;
  s += texto(W - 14, Y_AV + 16, "AV. BALLOFFET — RN 143 (tramo urbano)", 13,
             { ancla: "end", color: P.fondo, peso: 700, espaciado: 1 });

  // ---------------- Techo del playón ----------------
  s += `<rect x="${X0 - 4}" y="${Y_TECHO}" width="${X_FIN_ZONAS - X0 + 8}" height="20" rx="6" fill="${P.amarillo}"/>
        <rect x="${X0 - 4}" y="${Y_TECHO + 16}" width="${X_FIN_ZONAS - X0 + 8}" height="4" fill="${P.rojo}"/>`;

  // ---------------- Zonas ----------------
  let carasEsperando = 0;
  GRUPOS.forEach((g) => {
    const datos = F.g[g.id];
    const carriles = datos.c[i], cola = datos.q[i], largo = datos.n[i];
    const llena = g.cap !== null && largo >= g.cap;
    const rec = datos.r[i] - datos.r[Math.max(0, i - ventana)];
    const productosGrupo = g.productos.map((k) => PROD[k]);
    const faltaAqui = productosGrupo.filter((pr) => faltantes.includes(pr.nombre));
    const cortado = productosGrupo.some((pr) => pr.gnc) && hayCorte;

    // Panel de la zona
    s += `<rect x="${g.x}" y="${Y_ZONA}" width="${g.w}" height="${Y_ESTADO + 8 - Y_ZONA}" rx="8"
            fill="${P.panel}" stroke="${llena ? P.rojo : P.borde}" stroke-width="${llena ? 3 : 1.5}"/>`;
    const nombreCorto = productosGrupo.some((pr) => pr.gnc) ? "GNC" : g.nombre.toUpperCase();
    s += texto(g.x + PAD, Y_ZONA + 22, `ZONA ${g.id} · ${nombreCorto}`, 14, { peso: 700 });
    const cap = g.cap === null ? "" : ` / ${g.cap}`;
    s += texto(g.x + PAD, Y_ZONA + 40, `cola ${largo}${cap}`, 13, { color: P.tenue });
    const alerta = cortado ? "GNC CORTADO" : (faltaAqui.length ? "SIN STOCK" : (llena ? "COLA LLENA" : ""));
    if (alerta) {
      s += pastilla(g.x + PAD, Y_ZONA + 50, Math.min(116, g.w - 2 * PAD), 22, P.rojo, P.rojo, alerta, P.fondo);
    }

    // Asfalto de la cola: lugares numerados desde la cara hacia atrás
    const cols = g.caras;
    const filas = Math.min(MAX_FILAS, Math.ceil((g.cap === null ? 12 : g.cap) / cols));
    const visibles = filas * cols;
    s += `<rect x="${g.x + 4}" y="${Y_COLA_BASE - filas * SLOT_H - 4}" width="${g.w - 8}"
            height="${filas * SLOT_H + 8}" rx="6" fill="${P.asfalto}"/>`;
    for (let k = 0; k < visibles; k++) {
      const f = Math.floor(k / cols), c = k % cols;
      const cx = g.x + PAD + c * LANE + LANE / 2;
      const cy = Y_COLA_BASE - f * SLOT_H - SLOT_H / 2;
      const ocupado = k < cola.length;
      const habilitado = g.cap === null || k < g.cap;
      if (!ocupado) {
        s += `<rect x="${cx - 21}" y="${cy - 22}" width="42" height="44" rx="7" fill="none"
                stroke="${P.linea}" stroke-width="1.4" stroke-dasharray="4 4"
                opacity="${habilitado ? 0.55 : 0.18}"/>`;
      } else {
        s += autoV(cx, cy, PROD[cola[k]].color, false);
      }
    }
    if (largo > visibles) {
      s += pastilla(g.x + g.w / 2 - 34, Y_COLA_BASE - filas * SLOT_H - 14, 68, 20, P.fondo, P.tinta,
                    `+${largo - visibles} más`, P.tinta);
    }

    // Caras (carriles) y surtidores de a dos caras
    const yTop = Y_CARRIL;
    for (let c = 0; c < g.caras; c++) {
      const cx = g.x + PAD + c * LANE + LANE / 2;
      const codigo = carriles[c];
      s += `<rect x="${cx - LANE / 2 + 2}" y="${yTop}" width="${LANE - 4}" height="58" fill="${P.asfalto}"/>`;
      if (c > 0) {
        s += `<line x1="${cx - LANE / 2}" y1="${yTop + 2}" x2="${cx - LANE / 2}" y2="${yTop + 56}"
                stroke="${P.linea}" stroke-width="1.5" stroke-dasharray="5 4" opacity="0.6"/>`;
      }
      let estado = "libre", colorEstado = P.tenue;
      if (cortado) { estado = "cortada"; colorEstado = P.rojo; }
      if (codigo >= 0) {
        const k = codigo >> 1, espera = (codigo & 1) === 1;
        s += autoV(cx, yTop + 29, PROD[k].color, espera);
        estado = espera ? "espera" : "carga";
        colorEstado = P.tinta;
        if (espera) carasEsperando++;
      }
      s += texto(cx, Y_ESTADO, estado, 12, { ancla: "middle", color: colorEstado,
                                              peso: codigo >= 0 ? 700 : 400 });
    }
    for (let b = 0; b < Math.ceil(g.caras / 2); b++) {
      const xb = g.x + PAD + b * 2 * LANE + 6;
      const wb = Math.min(2, g.caras - b * 2) * LANE - 12;
      s += `<rect x="${xb}" y="${Y_BOMBA}" width="${wb}" height="40" rx="6" fill="${P.fondo}"
              stroke="${P.tinta}" stroke-width="1.8"/>`;
      const nb = productosGrupo.length;
      productosGrupo.forEach((pr, q) => {
        s += `<rect x="${xb + 4 + q * ((wb - 8) / nb)}" y="${Y_BOMBA + 4}" width="${(wb - 8) / nb}"
                height="9" fill="${pr.color}"/>`;
      });
      const numeroBomba = GRUPOS.slice(0, GRUPOS.indexOf(g)).reduce((a, x) => a + Math.ceil(x.caras / 2), 0) + b + 1;
      s += texto(xb + wb / 2, Y_BOMBA + 31, `S${numeroBomba}`, 14, { ancla: "middle", peso: 700 });
    }

    // Rechazados: pasan de largo por la avenida
    if (rec > 0) {
      const xr = g.x + g.w / 2;
      s += autoH(xr - 28, Y_AV + 36, P.rojo);
      if (rec > 1) s += autoH(xr + 22, Y_AV + 36, P.rojo);
      s += texto(xr, Y_AV + 12, `+${rec} pasaron de largo`, 12, { ancla: "middle", color: P.fondo, peso: 700 });
    }
  });

  // ---------------- Playeros (zonas que los usan) ----------------
  if (GRUPOS.some((g) => g.playero)) {
    const usan = GRUPOS.filter((g) => g.playero);
    const xp = usan[0].x, wp = usan[usan.length - 1].x + usan[usan.length - 1].w - xp;
    const turno = F.playTurno[i], ocup = F.playOcup[i];
    s += `<rect x="${xp}" y="${Y_PERSONAL}" width="${wp}" height="56" rx="8" fill="${P.panel}"
            stroke="${P.borde}" stroke-width="1.5"/>`;
    s += texto(xp + 12, Y_PERSONAL + 22, "PLAYEROS", 13, { peso: 700, espaciado: 1 });
    for (let k = 0; k < turno; k++) {
      s += persona(xp + 128 + k * 28, Y_PERSONAL + 22, k < ocup ? P.amarillo : P.fondo, P.tinta);
    }
    s += texto(xp + 12, Y_PERSONAL + 46, `${turno} en turno · ${ocup} atendiendo`, 13, { color: P.tenue });
    if (carasEsperando > 0) {
      s += pastilla(xp + wp - 156, Y_PERSONAL + 30, 146, 20, P.amarilloSuave, P.naranja,
                    `${carasEsperando} esperan playero`, P.tinta);
    }
  }
  // Estado del GNC
  const zGnc = GRUPOS.find((g) => g.productos.some((k) => PROD[k].gnc));
  if (zGnc) {
    s += `<rect x="${zGnc.x}" y="${Y_PERSONAL}" width="${zGnc.w}" height="56" rx="8" fill="${P.panel}"
            stroke="${P.borde}" stroke-width="1.5"/>`;
    s += texto(zGnc.x + 12, Y_PERSONAL + 21, "GNC", 13, { peso: 700, espaciado: 1 });
    if (hayCorte) s += pastilla(zGnc.x + 64, Y_PERSONAL + 8, 124, 24, P.rojo, P.rojo, "GNC CORTADO", P.fondo);
    else s += pastilla(zGnc.x + 64, Y_PERSONAL + 8, 124, 24, P.fondo, P.libre, "DISPONIBLE", P.tinta);
    s += texto(zGnc.x + 12, Y_PERSONAL + 46, "sin playero · los cortes llegan en la Fase 6", 12, { color: P.tenue });
  }

  // ---------------- Minimarket ----------------
  const colaC = F.colaCaja[i], ocupC = F.cajasOcup[i];
  s += `<rect x="${X_MINI}" y="${Y_ZONA}" width="${W_MINI}" height="312" rx="8" fill="${P.panel}"
          stroke="${P.borde}" stroke-width="1.5"/>`;
  s += `<rect x="${X_MINI}" y="${Y_ZONA}" width="${W_MINI}" height="26" rx="8" fill="${P.amarillo}"/>
        <rect x="${X_MINI}" y="${Y_ZONA + 22}" width="${W_MINI}" height="4" fill="${P.rojo}"/>`;
  s += texto(X_MINI + 12, Y_ZONA + 18, "MINIMARKET", 14, { peso: 700, espaciado: 1 });
  s += texto(X_MINI + 12, Y_ZONA + 48, `"Shell Select" (nombre sin confirmar) · entra el ${Math.round(CONFIG.probCompra * 100)} %`,
             12, { color: P.tenue });
  s += texto(X_MINI + 12, Y_ZONA + 82, "FILA PARA PAGAR", 12, { peso: 700, color: P.tenue, espaciado: 1 });
  const MAXP = 11;
  for (let k = 0; k < Math.min(colaC, MAXP); k++) {
    s += persona(X_MINI + 22 + k * 30, Y_ZONA + 114, P.fondo, P.tinta);
  }
  if (colaC > MAXP) s += texto(X_MINI + 22 + MAXP * 30, Y_ZONA + 118, `+${colaC - MAXP}`, 13, { peso: 700 });
  if (colaC === 0) s += texto(X_MINI + 12, Y_ZONA + 118, "sin fila", 13, { color: P.tenue });
  const nCajas = CONFIG.cajas;
  const altoCaja = Math.min(70, 168 / nCajas);
  for (let k = 0; k < nCajas; k++) {
    const y = Y_ZONA + 140 + k * altoCaja;
    const ocupada = k < ocupC;
    s += `<rect x="${X_MINI + 12}" y="${y}" width="${W_MINI - 24}" height="${altoCaja - 8}" rx="7"
            fill="${ocupada ? P.amarilloSuave : P.fondo}" stroke="${ocupada ? P.naranja : P.libre}" stroke-width="2"/>`;
    s += texto(X_MINI + 26, y + (altoCaja - 8) / 2 + 5, `CAJA ${k + 1}`, 14, { peso: 700 });
    s += texto(X_MINI + W_MINI - 36, y + (altoCaja - 8) / 2 + 5, ocupada ? "cobrando" : "libre", 13,
               { ancla: "end", peso: ocupada ? 700 : 400, color: ocupada ? P.tinta : P.tenue });
    if (ocupada) s += persona(X_MINI + W_MINI - 22, y + (altoCaja - 8) / 2 + 3, P.amarillo, P.tinta);
  }
  s += texto(X_MINI + 12, Y_ZONA + 304, `${F.compras[i]} cobradas · ${F.pCaja[i]} dejaron la compra`, 12,
             { color: P.tenue });

  // ---------------- Camión cisterna ----------------
  const yc = Y_ZONA + 322;
  s += `<rect x="${X_MINI}" y="${yc}" width="${W_MINI}" height="${Y_PERSONAL + 56 - yc}" rx="8" fill="${P.panel}"
          stroke="${P.borde}" stroke-width="1.5"/>`;
  s += texto(X_MINI + 12, yc + 21, "CAMIÓN CISTERNA", 13, { peso: 700, espaciado: 1 });
  s += texto(X_MINI + W_MINI - 12, yc + 21, CONFIG.ruta.escenario, 12,
             { ancla: "end", color: P.tenue });
  const xa = X_MINI + 96, xb = X_MINI + W_MINI - 112;
  let fila = 0;
  CONFIG.tanques.forEach((id, k) => {
    const prog = F.tk[id].p[i];
    if (prog < 0) return;
    const prod = PROD[TANQUES[k]];
    const y = yc + 52 + fila * 26;
    fila++;
    s += texto(X_MINI + 12, y + 5, prod.nombre, 12, { peso: 700 });
    s += `<line x1="${xa}" y1="${y}" x2="${xb}" y2="${y}" stroke="${P.asfalto}" stroke-width="5"/>
          <line x1="${xa}" y1="${y}" x2="${xb}" y2="${y}" stroke="${P.linea}" stroke-width="1.5" stroke-dasharray="8 7"/>`;
    s += camionIcono(xa + (xb - xa) * prog, y - 2, prod.color);
    s += texto(X_MINI + W_MINI - 12, y + 5, `llega en ${F.tk[id].h[i].toFixed(1)} h`, 12, { ancla: "end", peso: 700 });
    const demora = F.tk[id].d[i];
    if (demora > 0) {
      s += `<rect x="${X_MINI + 12}" y="${y + 9}" width="9" height="9" rx="2" fill="${P.rojo}"/>`;
      s += texto(X_MINI + 25, y + 18, `corte en la ruta: +${demora.toFixed(1)} h`, 11, { color: P.tinta, peso: 700 });
    }
  });
  if (fila === 0) s += texto(X_MINI + 12, yc + 56, "sin pedidos en camino", 13, { color: P.tenue });
  if (CONFIG.ruta.detalle) s += texto(X_MINI + 12, Y_PERSONAL + 46, CONFIG.ruta.detalle, 11, { color: P.tenue });

  // ---------------- Tanques ----------------
  s += texto(X0, Y_TANQUES - 10, "TANQUES (uno por producto líquido)", 13, { peso: 700, espaciado: 1 });
  const nT = CONFIG.tanques.length, wT = Math.min(236, (X_FIN_ZONAS - X0 - 10 * (nT - 1)) / nT);
  CONFIG.tanques.forEach((id, k) => {
    const prod = PROD[TANQUES[k]];
    const x = X0 + k * (wT + 10), nivel = F.tk[id].n[i], enCamino = F.tk[id].c[i];
    const fr = Math.max(0, Math.min(1, nivel / prod.capacidad));
    const bajo = nivel <= prod.puntoPedido, sin = nivel < prod.minimo;
    s += `<rect x="${x}" y="${Y_TANQUES}" width="${wT}" height="98" rx="8" fill="${P.panel}"
            stroke="${sin ? P.rojo : P.borde}" stroke-width="${sin ? 3 : 1.5}"/>`;
    s += texto(x + 10, Y_TANQUES + 20, prod.nombre, 14, { peso: 700 });
    s += texto(x + wT - 10, Y_TANQUES + 20, `${miles(nivel)} L`, 14, { ancla: "end", peso: 700 });
    s += `<rect x="${x + 10}" y="${Y_TANQUES + 30}" width="${wT - 20}" height="22" rx="5" fill="${P.fondo}"
            stroke="${P.borde}"/>
          <rect x="${x + 10}" y="${Y_TANQUES + 30}" width="${(wT - 20) * fr}" height="22" rx="5" fill="${prod.color}"/>`;
    const xs = x + 10 + (wT - 20) * (prod.puntoPedido / prod.capacidad);
    s += `<line x1="${xs}" y1="${Y_TANQUES + 26}" x2="${xs}" y2="${Y_TANQUES + 56}" stroke="${P.tinta}"
            stroke-width="2.4"/>`;
    let nota = enCamino > 0 ? `pedido en camino: ${miles(enCamino)} L` : (bajo ? "bajo el punto de pedido" : "sin pedido");
    s += texto(x + 10, Y_TANQUES + 72, nota, 12, { color: P.tenue });
    if (sin) s += pastilla(x + 10, Y_TANQUES + 76, 130, 18, P.rojo, P.rojo, "SIN COMBUSTIBLE", P.fondo);
  });

  // ---------------- Leyenda ----------------
  const xl = X_MINI, yl = Y_TANQUES;
  s += `<rect x="${xl}" y="${yl}" width="${W_MINI}" height="98" rx="8" fill="${P.panel}" stroke="${P.borde}" stroke-width="1.5"/>`;
  s += texto(xl + 12, yl + 20, "COLOR DEL AUTO = PRODUCTO", 12, { peso: 700, espaciado: 1 });
  PROD.forEach((pr, k) => {
    const cx = xl + 12 + (k % 3) * 118, cy = yl + 40 + Math.floor(k / 3) * 20;
    s += `<rect x="${cx}" y="${cy - 9}" width="12" height="12" rx="3" fill="${pr.color}" stroke="${P.tinta}"/>`;
    s += texto(cx + 18, cy + 2, pr.nombre, 12);
  });
  if (CONFIG.real) s += texto(xl + 12, yl + 78, "espera = cara ocupada esperando playero", 11, { color: P.tenue });

  s += `</svg>`;
  document.getElementById("lienzo").innerHTML = s;
}

// --- Reproductor -------------------------------------------------------------
const ultimo = NCUADROS - 1;
const barra = document.getElementById("barra");
const botonPlay = document.getElementById("play");
const selectorVelocidad = document.getElementById("velocidad");
const textoReloj = document.getElementById("reloj");

// La posición se guarda con decimales (cuadro fraccionario) para que la velocidad de
// reproducción no dependa de cuántos cuadros por segundo llegue a dibujar la pantalla.
let posicion = 0, reproduciendo = false, ultimoInstante = 0;

barra.max = String(ultimo);
selectorVelocidad.value = REDUCIDO ? "30" : "120";

function mostrar(pos) {
  posicion = Math.max(0, Math.min(ultimo, pos));
  const i = Math.round(posicion);
  dibujar(i);
  barra.value = String(i);
  textoReloj.textContent = `${reloj(F.t[i])} — día ${CONFIG.dia}`;
}

function paso(instante) {
  if (!reproduciendo) return;
  const transcurrido = (instante - ultimoInstante) / 1000;
  ultimoInstante = instante;
  const siguiente = posicion + (transcurrido * Number(selectorVelocidad.value)) / CONFIG.dt;
  if (siguiente >= ultimo) { mostrar(ultimo); pausar(); return; }
  mostrar(siguiente);
  requestAnimationFrame(paso);
}
function reproducir() {
  if (posicion >= ultimo) mostrar(0);
  reproduciendo = true;
  botonPlay.textContent = "⏸ Pausar";
  ultimoInstante = performance.now();
  requestAnimationFrame(paso);
}
function pausar() { reproduciendo = false; botonPlay.textContent = "▶ Reproducir"; }

botonPlay.addEventListener("click", () => (reproduciendo ? pausar() : reproducir()));
document.getElementById("reiniciar").addEventListener("click", () => { pausar(); mostrar(0); });
barra.addEventListener("input", () => { pausar(); mostrar(Number(barra.value)); });

// --- Saltos: hora pico, primer quiebre, próxima descarga, corte de GNC ---------
function colaTotal(i) { return GRUPOS.reduce((a, g) => a + F.g[g.id].n[i], 0); }
function camionesTotal(i) { return CONFIG.tanques.reduce((a, id) => a + F.tk[id].c[i], 0); }

let iPico = 0, mejor = -1;
for (let i = 0; i < NCUADROS; i++) {
  const c = colaTotal(i);
  if (c > mejor) { mejor = c; iPico = i; }
}
let iQuiebre = -1;
for (let i = 0; i < NCUADROS && iQuiebre < 0; i++) if (sinCombustible(i).length) iQuiebre = i;
let iCorte = -1;
for (let i = 0; i < NCUADROS && iCorte < 0; i++) if (F.gnc[i] === 1) iCorte = i;

function saltar(i) { pausar(); mostrar(i); }
document.getElementById("saltoPico").addEventListener("click", () => saltar(iPico));
const bQuiebre = document.getElementById("saltoQuiebre");
bQuiebre.disabled = iQuiebre < 0;
bQuiebre.title = iQuiebre < 0 ? "No hubo quiebre de stock este día" : "";
bQuiebre.addEventListener("click", () => saltar(iQuiebre));
const bCorte = document.getElementById("saltoCorte");
bCorte.disabled = iCorte < 0;
bCorte.title = iCorte < 0 ? "No hubo corte de GNC este día (los episodios llegan en la Fase 6)" : "";
bCorte.addEventListener("click", () => saltar(iCorte));
document.getElementById("saltoDescarga").addEventListener("click", () => {
  const desde = Math.round(posicion);
  for (let i = desde + 1; i < NCUADROS; i++) {
    if (camionesTotal(i) < camionesTotal(i - 1)) { saltar(i); return; }
  }
  saltar(ultimo);
});

mostrar(0);
</script>
</body>
</html>
"""
