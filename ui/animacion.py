"""Reproductor de la animación de la estación de servicio.

Cómo funciona
-------------
El motor ya dejó en la traza una foto del sistema cada `dt` minutos simulados, durante el
día elegido. Acá esos cuadros se mandan al navegador como datos (JSON) junto con un
reproductor que los dibuja en SVG.

Por qué el dibujo se hace en el navegador y no en Python: cada refresco del lado del
servidor cuesta casi un segundo (ida y vuelta por websocket más volver a montar el
componente), así que la película se veía a los saltos. Con el reproductor del lado del
cliente la animación corre a la velocidad de la pantalla y los botones de play, pausa,
velocidad y posición responden al instante.

Es la única parte del proyecto con JavaScript, y está acotada a dibujar: no simula nada.
Los colores NO están hardcodeados acá: llegan por JSON desde `ui/tema.py` (N15).
"""

from __future__ import annotations

import json

from sim.traza import Cuadro
from ui.tema import paleta_json

#: Alto del componente en píxeles (barra de controles + dibujo).
ALTO_COMPONENTE = 600


def _datos(cuadros: list[Cuadro]) -> list[list[float]]:
    """Cuadros en formato compacto (lista de listas) para que el JSON pese poco."""
    return [
        [
            round(c.minuto_del_dia, 2),
            c.surtidores_ocupados,
            c.cola_surtidor,
            c.cajas_ocupadas,
            c.cola_caja,
            c.atendidos,
            c.perdidos_surtidor,
            c.compras,
            c.perdidos_caja,
            round(c.nivel_tanque, 1),
            c.perdidos_sin_combustible,
            c.pedidos_en_camino,
            1 if c.en_calentamiento else 0,
        ]
        for c in cuadros
    ]


def reproductor_html(
    cuadros: list[Cuadro],
    surtidores: int,
    cajas: int,
    dt: float,
    capacidad_tanque: float,
    punto_pedido: float,
    dia: int,
    litros_minimos: float,
    velocidad_inicial: int = 120,
) -> str:
    """Devuelve el HTML completo del reproductor, listo para `st.components.v1.html`."""
    configuracion = {
        "cuadros": _datos(cuadros),
        "surtidores": int(surtidores),
        "cajas": int(cajas),
        "dt": float(dt),
        "capacidad": float(capacidad_tanque),
        "puntoPedido": float(punto_pedido),
        "dia": int(dia),
        "litrosMinimos": float(litros_minimos),
        "velocidad": int(velocidad_inicial),
        "paleta": paleta_json(),
    }
    return _PLANTILLA.replace("__CONFIG__", json.dumps(configuracion))


_PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  :root {
    --panel: transparent;
    --borde: transparent;
    --texto: transparent;
    --tenue: transparent;
    --amarillo: transparent;
    --rojo: transparent;
  }
  html, body { margin: 0; padding: 0; height: 100%; background: transparent; overflow: hidden;
               font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  #contenedor { display: flex; flex-direction: column; height: 100%; }
  #controles { display: flex; align-items: center; gap: 10px; padding: 6px 4px 10px;
               color: var(--texto); font-size: 13px; }
  button { background: var(--panel); color: var(--texto); border: 1px solid var(--borde);
           border-radius: 7px; padding: 7px 14px; font-size: 13px; cursor: pointer;
           font-family: inherit; }
  button:hover { border-color: var(--tenue); }
  #play { background: var(--rojo); border-color: var(--rojo); font-weight: 600; min-width: 116px; }
  #play:hover { filter: brightness(1.2); }
  select { background: var(--panel); color: var(--texto); border: 1px solid var(--borde);
           border-radius: 7px; padding: 6px 8px; font-size: 13px; font-family: inherit; }
  #barra { flex: 1; accent-color: var(--amarillo); }
  #reloj { color: var(--tenue); min-width: 128px; font-variant-numeric: tabular-nums; }
  #lienzo { flex: 1; min-height: 0; }
  svg { width: 100%; height: 100%; display: block; }
</style>
</head>
<body>
<div id="contenedor">
  <div id="controles">
    <button id="play">▶ Reproducir</button>
    <button id="reiniciar">⏮ Reiniciar</button>
    <select id="velocidad" title="Minutos simulados por segundo real">
      <option value="30">30 min/s</option>
      <option value="60">1 h/s</option>
      <option value="120">2 h/s</option>
      <option value="240">4 h/s</option>
      <option value="480">8 h/s</option>
    </select>
    <input type="range" id="barra" min="0" value="0" step="1">
    <span id="reloj"></span>
  </div>
  <div id="lienzo"></div>
</div>

<script>
const CONFIG = __CONFIG__;

// --- Paleta (llega por JSON desde ui/tema.py) --------------------------------
const P = CONFIG.paleta;
const RAIZ = document.documentElement;
RAIZ.style.setProperty("--panel", P.panel);
RAIZ.style.setProperty("--borde", P.borde);
RAIZ.style.setProperty("--texto", P.texto);
RAIZ.style.setProperty("--tenue", P.tenue);
RAIZ.style.setProperty("--amarillo", P.amarillo);
RAIZ.style.setProperty("--rojo", P.rojo);

const FONDO = P.fondo, PANEL = P.panel, ASFALTO = P.asfalto, BORDE = P.borde;
const TEXTO = P.texto, TENUE = P.tenue;
const LIBRE = P.libre, OCUPADO = P.ocupado, PERDIDO = P.perdido;
const COLORES_AUTO = P.coloresAuto;
const ANCHO = 1000, ALTO = 520;
const MAX_AUTOS = 6, MAX_PERSONAS = 6;

// --- Piezas del dibujo -------------------------------------------------------
function auto(x, y, color, escala) {
  return `<g transform="translate(${x},${y}) scale(${escala})">
    <rect x="0" y="6" width="56" height="16" rx="5" fill="${color}"/>
    <path d="M 11 7 L 18 0 L 39 0 L 45 7 Z" fill="${color}" opacity="0.85"/>
    <rect x="19" y="1" width="17" height="6" rx="2" fill="${P.vidrio}" opacity="0.55"/>
    <circle cx="15" cy="22" r="4.2" fill="${P.neumatico}"/>
    <circle cx="43" cy="22" r="4.2" fill="${P.neumatico}"/>
    <rect x="52" y="11" width="4" height="3" rx="1" fill="${P.faros}"/>
  </g>`;
}

function persona(x, y, color) {
  return `<g transform="translate(${x},${y})">
    <circle cx="0" cy="0" r="4.5" fill="${color}"/>
    <path d="M -5 6 Q 0 4 5 6 L 4 18 L -4 18 Z" fill="${color}" opacity="0.85"/>
  </g>`;
}

function surtidor(x, y, ocupado, activo) {
  const c = !activo ? PERDIDO : (ocupado ? OCUPADO : LIBRE);
  return `<g transform="translate(${x},${y})">
    <rect x="-3" y="32" width="26" height="5" rx="2" fill="${BORDE}"/>
    <rect x="0" y="0" width="20" height="34" rx="4" fill="${PANEL}" stroke="${c}" stroke-width="2"/>
    <rect x="4" y="5" width="12" height="8" rx="2" fill="${c}" opacity="0.9"/>
    <circle cx="10" cy="23" r="3.2" fill="${c}" opacity="0.7"/>
    <path d="M 20 15 q 9 2 9 10" fill="none" stroke="${c}" stroke-width="2" opacity="0.8"/>
  </g>`;
}

function camion(x, y) {
  return `<g transform="translate(${x},${y}) scale(0.8)">
    <rect x="0" y="4" width="34" height="14" rx="4" fill="${P.plata}"/>
    <rect x="34" y="7" width="14" height="11" rx="3" fill="${P.plata}"/>
    <circle cx="10" cy="19" r="3.5" fill="${P.neumatico}"/>
    <circle cx="28" cy="19" r="3.5" fill="${P.neumatico}"/>
    <circle cx="42" cy="19" r="3.5" fill="${P.neumatico}"/>
  </g>`;
}

function rotulo(x, y, titulo, detalle) {
  return `<text x="${x}" y="${y}" fill="${TEXTO}" font-size="13" font-weight="600"
            letter-spacing="1.2">${titulo}</text>
          <text x="${x}" y="${y + 15}" fill="${TENUE}" font-size="11">${detalle}</text>`;
}

function flecha(x1, y, x2, etiqueta) {
  const medio = (x1 + x2) / 2;
  const txt = etiqueta
    ? `<text x="${medio}" y="${y - 10}" fill="${TENUE}" font-size="11" text-anchor="middle">${etiqueta}</text>`
    : "";
  return `<line x1="${x1}" y1="${y}" x2="${x2 - 8}" y2="${y}" stroke="${BORDE}"
            stroke-width="2" stroke-dasharray="5 4"/>
          <path d="M ${x2 - 9} ${y - 5} L ${x2} ${y} L ${x2 - 9} ${y + 5} Z" fill="${BORDE}"/>${txt}`;
}

function reloj(minutoDelDia) {
  const m = Math.floor(minutoDelDia);
  return String(Math.floor(m / 60) % 24).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0");
}

function miles(n) { return Math.round(n).toLocaleString("es-AR"); }

// --- Dibujo de un cuadro -----------------------------------------------------
function dibujar(c) {
  const [t, ocupados, colaS, cajasOcup, colaC, atendidos, perdidosS,
         compras, perdidosC, nivel, sinNafta, enCamino, calent] = c;
  const N = CONFIG.surtidores, M = CONFIG.cajas;
  const hayNafta = nivel >= CONFIG.litrosMinimos;

  let s = `<svg viewBox="0 0 ${ANCHO} ${ALTO}" xmlns="http://www.w3.org/2000/svg"
             preserveAspectRatio="xMidYMid meet"
             style="font-family:system-ui,-apple-system,Segoe UI,sans-serif">`;
  s += `<rect width="${ANCHO}" height="${ALTO}" rx="10" fill="${FONDO}"/>`;

  // ---------------- Barra superior ----------------
  s += `<rect x="0" y="0" width="${ANCHO}" height="52" rx="10" fill="${PANEL}"/>`;
  s += `<text x="20" y="34" fill="${TEXTO}" font-size="22" font-weight="700">${reloj(t)}</text>`;
  s += `<text x="92" y="34" fill="${TENUE}" font-size="12">día ${CONFIG.dia}</text>`;

  if (!hayNafta) {
    s += `<rect x="150" y="14" width="168" height="24" rx="12" fill="${P.rojoOscuro}"/>
          <text x="234" y="30" fill="${P.rojoClaro}" font-size="11" text-anchor="middle"
            font-weight="700">SIN COMBUSTIBLE</text>`;
  } else if (calent) {
    s += `<rect x="150" y="14" width="168" height="24" rx="12" fill="${P.ambarOscuro}"/>
          <text x="234" y="30" fill="${P.ambarClaro}" font-size="11" text-anchor="middle"
            font-weight="600">CALENTAMIENTO</text>`;
  } else {
    s += `<rect x="150" y="14" width="168" height="24" rx="12" fill="${P.verdeOscuro}"/>
          <text x="234" y="30" fill="${P.verdeClaro}" font-size="11" text-anchor="middle"
            font-weight="600">MIDIENDO INDICADORES</text>`;
  }

  const marcadores = [[atendidos, "cargaron", LIBRE, 400],
                      [compras, "compraron", COLORES_AUTO[0], 545],
                      [perdidosS + perdidosC, "por cola", COLORES_AUTO[5], 690],
                      [sinNafta, "sin nafta", PERDIDO, 860]];
  for (const [valor, etiqueta, color, x] of marcadores) {
    s += `<text x="${x}" y="32" fill="${color}" font-size="18" font-weight="700"
            text-anchor="end">${valor}</text>
          <text x="${x + 6}" y="32" fill="${TENUE}" font-size="11">${etiqueta}</text>`;
  }

  // ---------------- Columna 1: llegadas y cola ----------------
  s += rotulo(20, 78, "LLEGADAS Y COLA", "Poisson con perfil horario");
  s += `<rect x="20" y="96" width="270" height="318" rx="8" fill="${ASFALTO}"/>`;
  s += `<line x1="42" y1="118" x2="42" y2="398" stroke="${BORDE}" stroke-width="2"
          stroke-dasharray="6 8"/>`;
  const visibles = Math.min(colaS, MAX_AUTOS);
  for (let i = 0; i < visibles; i++) {
    s += auto(70, 110 + i * 42, COLORES_AUTO[i % COLORES_AUTO.length], 0.9);
  }
  if (colaS > MAX_AUTOS) {
    s += `<text x="155" y="${110 + MAX_AUTOS * 42 + 18}" fill="${TENUE}" font-size="13"
            text-anchor="middle">+${colaS - MAX_AUTOS} autos más esperando</text>`;
  }
  if (colaS === 0) {
    s += `<text x="155" y="260" fill="${TENUE}" font-size="13" text-anchor="middle">sin cola</text>`;
  }
  s += `<text x="155" y="406" fill="${TEXTO}" font-size="12" text-anchor="middle"
          font-weight="600">${colaS} en cola</text>`;

  // ---------------- Columna 2: surtidores ----------------
  s += flecha(292, 255, 330, "");
  s += rotulo(340, 78, "SURTIDORES", "servicio triangular");
  s += `<rect x="340" y="96" width="290" height="318" rx="8" fill="${ASFALTO}"/>`;
  s += `<rect x="352" y="104" width="266" height="13" rx="6" fill="${BORDE}" opacity="0.75"/>`;
  const altoFila = Math.min(70, 286 / N);
  const y0 = 126 + Math.max(0, 286 - N * altoFila) / 2;
  for (let i = 0; i < N; i++) {
    const y = y0 + i * altoFila;
    const ocupado = i < ocupados;
    s += surtidor(364, y, ocupado, hayNafta);
    if (ocupado) {
      s += auto(402, y + 5, COLORES_AUTO[(i + 3) % COLORES_AUTO.length], 0.92);
    } else {
      s += `<text x="470" y="${y + 22}" fill="${TENUE}" font-size="11">
              ${hayNafta ? "libre" : "sin nafta"}</text>`;
    }
    s += `<text x="600" y="${y + 22}" fill="${TENUE}" font-size="10" text-anchor="end">S${i + 1}</text>`;
  }
  s += `<text x="485" y="406" fill="${TEXTO}" font-size="12" text-anchor="middle"
          font-weight="600">${ocupados} de ${N} ocupados</text>`;

  // ---------------- Columna 3: minimarket ----------------
  s += flecha(632, 255, 670, "compran");
  s += rotulo(680, 78, "MINIMARKET", "Bernoulli: sólo el % que compra");
  s += `<rect x="680" y="96" width="300" height="318" rx="8" fill="${ASFALTO}"/>`;
  s += `<rect x="694" y="106" width="272" height="24" rx="6" fill="${PANEL}"/>
        <text x="830" y="123" fill="${TEXTO}" font-size="12" text-anchor="middle"
          letter-spacing="2">MINIMARKET</text>`;
  s += `<text x="716" y="150" fill="${TENUE}" font-size="10" text-anchor="middle">cola</text>`;
  const personas = Math.min(colaC, MAX_PERSONAS);
  for (let i = 0; i < personas; i++) s += persona(716, 164 + i * 32, P.plata);
  if (colaC > MAX_PERSONAS) {
    s += `<text x="716" y="${164 + MAX_PERSONAS * 32 + 12}" fill="${TENUE}" font-size="11"
            text-anchor="middle">+${colaC - MAX_PERSONAS}</text>`;
  }
  const altoCaja = Math.min(76, 268 / M);
  const yCaja0 = 146 + Math.max(0, 268 - M * altoCaja) / 2;
  for (let i = 0; i < M; i++) {
    const y = yCaja0 + i * altoCaja;
    const ocupada = i < cajasOcup;
    const color = ocupada ? OCUPADO : LIBRE;
    s += `<rect x="770" y="${y}" width="120" height="${Math.min(54, altoCaja - 10)}" rx="6"
            fill="${PANEL}" stroke="${color}" stroke-width="2"/>
          <text x="830" y="${y + 21}" fill="${color}" font-size="11" text-anchor="middle"
            font-weight="600">CAJA ${i + 1}</text>
          <text x="830" y="${y + 36}" fill="${TENUE}" font-size="10" text-anchor="middle">
            ${ocupada ? "cobrando" : "libre"}</text>`;
    if (ocupada) s += persona(752, y + 24, COLORES_AUTO[2]);
  }
  s += `<text x="830" y="406" fill="${TEXTO}" font-size="12" text-anchor="middle"
          font-weight="600">${colaC} esperando para pagar</text>`;

  // ---------------- Banda inferior: el tanque ----------------
  s += `<rect x="20" y="428" width="960" height="76" rx="8" fill="${ASFALTO}"/>`;
  s += `<text x="40" y="452" fill="${TEXTO}" font-size="12" font-weight="600"
          letter-spacing="1">TANQUE DE COMBUSTIBLE</text>`;

  const bx = 210, by = 444, bw = 590, bh = 30;
  const fraccion = Math.max(0, Math.min(1, nivel / CONFIG.capacidad));
  const colorNivel = !hayNafta ? PERDIDO : (nivel <= CONFIG.puntoPedido ? OCUPADO : LIBRE);
  s += `<rect x="${bx}" y="${by}" width="${bw}" height="${bh}" rx="6" fill="${FONDO}"
          stroke="${BORDE}"/>`;
  s += `<rect x="${bx}" y="${by}" width="${bw * fraccion}" height="${bh}" rx="6"
          fill="${colorNivel}" opacity="0.85"/>`;

  // Marca del punto de pedido
  const xPedido = bx + bw * (CONFIG.puntoPedido / CONFIG.capacidad);
  s += `<line x1="${xPedido}" y1="${by - 6}" x2="${xPedido}" y2="${by + bh + 6}"
          stroke="${TEXTO}" stroke-width="2" stroke-dasharray="4 3"/>
        <text x="${xPedido}" y="${by + bh + 19}" fill="${TENUE}" font-size="10"
          text-anchor="middle">punto de pedido</text>`;

  s += `<text x="${bx + bw + 14}" y="${by + 20}" fill="${TEXTO}" font-size="13"
          font-weight="700">${miles(nivel)} L</text>`;
  s += `<text x="${bx + bw + 14}" y="${by + 36}" fill="${TENUE}" font-size="10">
          de ${miles(CONFIG.capacidad)} L</text>`;

  if (enCamino > 0) {
    s += camion(40, 464);
    s += `<text x="92" y="484" fill="${TENUE}" font-size="11">
            ${enCamino === 1 ? "camión en viaje" : enCamino + " camiones en viaje"}</text>`;
  } else {
    s += `<text x="40" y="484" fill="${TENUE}" font-size="11">sin pedidos pendientes</text>`;
  }

  s += `</svg>`;
  document.getElementById("lienzo").innerHTML = s;
}

// --- Reproductor -------------------------------------------------------------
const cuadros = CONFIG.cuadros;
const ultimo = cuadros.length - 1;
const barra = document.getElementById("barra");
const botonPlay = document.getElementById("play");
const selectorVelocidad = document.getElementById("velocidad");
const textoReloj = document.getElementById("reloj");

// La posición se guarda con decimales (cuadro fraccionario) para que la velocidad de
// reproducción no dependa de cuántos cuadros por segundo llegue a dibujar la pantalla.
let posicion = 0;
let reproduciendo = false;
let ultimoInstante = 0;

barra.max = String(ultimo);
selectorVelocidad.value = String(CONFIG.velocidad);

function mostrar(pos) {
  posicion = Math.max(0, Math.min(ultimo, pos));
  const i = Math.round(posicion);
  dibujar(cuadros[i]);
  barra.value = String(i);
  textoReloj.textContent = `${reloj(cuadros[i][0])} — día ${CONFIG.dia}`;
}

function paso(instante) {
  if (!reproduciendo) return;
  const transcurrido = (instante - ultimoInstante) / 1000;   // segundos reales
  ultimoInstante = instante;
  const minutos = transcurrido * Number(selectorVelocidad.value);
  const siguiente = posicion + minutos / CONFIG.dt;          // en cuadros
  if (siguiente >= ultimo) {
    mostrar(ultimo);
    pausar();
    return;
  }
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

function pausar() {
  reproduciendo = false;
  botonPlay.textContent = "▶ Reproducir";
}

botonPlay.addEventListener("click", () => (reproduciendo ? pausar() : reproducir()));
document.getElementById("reiniciar").addEventListener("click", () => {
  pausar();
  mostrar(0);
});
barra.addEventListener("input", () => {
  pausar();
  mostrar(Number(barra.value));
});

mostrar(0);
</script>
</body>
</html>
"""
