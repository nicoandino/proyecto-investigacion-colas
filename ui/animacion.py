"""Tablero animado de la estación (rediseño v3, etapa 3).

Cómo funciona
-------------
El motor deja en la traza una foto del sistema cada `dt` minutos simulados **durante todo el período**. Acá
esas fotos se pasan a formato COLUMNAR y compacto (un arreglo por variable; los carriles y la cola de
cada zona como cadenas de caracteres) y se mandan al navegador junto con un reproductor que las dibuja.

El dibujo lo hace el navegador y no Python: cada refresco del lado del servidor cuesta casi un segundo, así
que la película se vería a los saltos. Es la única parte del proyecto con JavaScript y está acotada a
dibujar: no simula nada. Los colores NO están hardcodeados acá: llegan por JSON desde `ui/tema.py` (N15).

Qué se ve (referencia de diseño del usuario): barra superior con el estado, el día y los números de hoy;
el playón visto desde arriba con las zonas A (nafta), B (diésel) y C (GNC), cada cara con su surtidor
arriba y **3 lugares de cola debajo**; el minimarket, los playeros, el GNC y el camión a la derecha; y
abajo los tanques, las colas actuales, los indicadores del día y un gráfico a elección.
Se reproduce todo el período: **un día cada 5 segundos** (se puede cambiar).
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from sim.config import ANO_REFERENCIA, ParametrosSimulacion
from sim.datos import valor
from sim.eventos import POR_ID as TIPOS_EVENTO
from sim.red import ETIQUETA_ESCENARIO, NOMBRE_NODO, camino_mas_corto, descripcion_ruta
from sim.traza import Cuadro, Traza
from ui.graficos_red import POSICION_NODO
from ui.tema import COLOR_PRODUCTO_OSCURO, paleta_json, paleta_oscura_json

#: Alto del componente en píxeles.
ALTO_COMPONENTE = 1080

#: Tope de cuadros que se mandan al navegador (un año con 36 min entre cuadros ≈ 14.600).
MAXIMO_CUADROS = 16_000
#: Minutos simulados entre cuadros, del más fino al más grueso: se elige el menor que no pase el tope.
OPCIONES_DT = (12.0, 15.0, 20.0, 24.0, 30.0, 36.0, 48.0, 60.0)


def dt_para(dias: int) -> float:
    """Minutos entre cuadros para que el período entero tenga ≤ `MAXIMO_CUADROS` cuadros."""
    for dt in OPCIONES_DT:
        if dias * 1440.0 / dt <= MAXIMO_CUADROS:
            return dt
    return OPCIONES_DT[-1]


def _codigo_carril(k: int) -> str:
    """Un carácter por cara: '.' libre, 'x' fuera de servicio (EVT-05), 'a'.. el código (2·producto + 1 si espera al
    playero)."""
    if k == -2:
        return "x"
    return "." if k < 0 else chr(97 + k)


def _columnas(cuadros: list[Cuadro], p: ParametrosSimulacion) -> dict:
    """Cuadros en formato columnar y compacto (`round` y cadenas para que pese poco)."""
    ids_tanques = [i.producto for i in p.inventario]
    salida: dict = {
        "t": [round(c.t, 1) for c in cuadros],
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
        "comp": [c.compresores_ocupados for c in cuadros],
        "compTot": [c.compresores_total for c in cuadros],
        "migr": [c.migrados_gnc for c in cuadros],
        "pCorte": [c.perdidos_corte_gnc for c in cuadros],
        "lit": [
            [round(c.litros_producto[k], 1) for c in cuadros] for k in range(len(p.productos))
        ],
        "g": {},
        "tk": {},
    }
    for i, grupo in enumerate(p.grupos):
        fotos = [c.grupos[i] for c in cuadros]   # (id, carriles, cola, largo, rechazados, suma, n)
        salida["g"][grupo.id] = {
            "c": ["".join(_codigo_carril(k) for k in f[1]) for f in fotos],
            "q": ["".join(str(x) for x in f[2]) for f in fotos],
            "n": [f[3] for f in fotos],
            "r": [f[4] for f in fotos],
            "sw": [round(f[5], 1) for f in fotos],
            "ne": [f[6] for f in fotos],
        }
    for i, id_tanque in enumerate(ids_tanques):
        fotos = [c.tanques[i] for c in cuadros]  # (producto, nivel, camino, progreso, horas, demora)
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
    """Ruta del camión y escenario de cortes para el panel."""
    if p.red is None:
        return {"detalle": "", "escenario": "proveedor → estación"}
    escenario = ETIQUETA_ESCENARIO.get(p.red.escenario_corte, f"Corte {p.red.escenario_corte}")
    ruta = descripcion_ruta(p.red).rsplit(" · ", 1)[0]      # sin las horas
    return {"detalle": ruta, "escenario": escenario}


def _por_dia(p: ParametrosSimulacion, precios: dict[str, float]) -> dict:
    """Lo que se espera de cada día (clientes, litros, ventas) para las barras de avance."""
    clientes, litros, ventas = [], [], []
    liquidos = [pr for pr in p.productos if not pr.es_gnc]
    gnc = next((pr for pr in p.productos if pr.es_gnc), None)
    for d in range(1, p.dias + 1):
        autos = p.autos_por_dia_fecha(d)
        lit_dia = p.litros_del_dia(d)
        clientes.append(int(round(autos)))
        litros.append(round(lit_dia))
        v = sum(lit_dia * pr.pct_litros * precios.get(pr.id, 0.0) for pr in liquidos)
        if gnc is not None:
            v += autos * p.pct_gnc * gnc.carga_media * precios.get(gnc.id, 0.0)
        ventas.append(round(v))
    return {"clientes": clientes, "litros": litros, "ventas": ventas}


def _eventos(traza: Traza, p: ParametrosSimulacion) -> list[dict]:
    """Los avisos de la animación, leídos de la traza (el motor los anota sin sortear nada)."""
    nombres = {pr.id: pr.nombre for pr in p.productos}
    salida: list[dict] = []
    for ev in traza.eventos:
        if ev[0] == "pedido":
            _, t, prod, nivel, origen, redirigido, llega, litros = ev
            salida.append({
                "tipo": "pedido", "t": round(t, 1), "id": prod, "producto": nombres[prod],
                "pct": round(100 * nivel), "nodo": origen, "origen": NOMBRE_NODO.get(origen, origen),
                "redirigido": bool(redirigido), "llega": round(llega, 1), "litros": round(litros),
            })
        elif ev[0] == "descarga":
            _, t, prod, litros = ev
            salida.append({"tipo": "descarga", "t": round(t, 1), "id": prod, "producto": nombres[prod],
                           "litros": round(litros)})
        elif ev[0] == "corte_gnc":
            _, t, _, inicio, fin = ev
            salida.append({"tipo": "gnc", "t": round(t, 1), "inicio": round(inicio, 1), "fin": round(fin, 1)})
        elif ev[0] == "evento":                    # eventos aleatorios (parte 4)
            _, t, id_, fin, _, detalle = ev
            salida.append({"tipo": "evento", "t": round(t, 1), "fin": round(fin, 1), "id": id_,
                           "titulo": TIPOS_EVENTO[id_].nombre, "texto": detalle[:1].upper() + detalle[1:] + "."})
    return salida


def _configuracion(
    traza: Traza, p: ParametrosSimulacion, precios: dict[str, float], titulo: str, corrida: str = ""
) -> dict:
    """Todo lo que el navegador necesita: estructura de la estación, calendario y cuadros."""
    productos = [
        {
            "id": pr.id,
            "nombre": pr.nombre,
            "color": COLOR_PRODUCTO_OSCURO[pr.id],
            "gnc": pr.es_gnc,
            "precio": float(precios.get(pr.id, 0.0)),
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
            "cap": p.capacidad_de(g.id),
        }
        for g in p.grupos
    ]
    return {
        "dt": float(p.dt_traza),
        "titulo": titulo,
        "inicio": date(ANO_REFERENCIA, *p.fecha_inicio).isoformat(),
        "dias": int(p.dias),
        "grupos": grupos,
        "productos": productos,
        "tanques": [i.producto for i in p.inventario],
        "ruta": _texto_ruta(p),
        "cajas": int(p.cajas),
        "probCompra": float(p.prob_compra),
        "esperado": _por_dia(p, precios),
        "frames": _columnas(traza.cuadros, p),
        "paleta": paleta_oscura_json(),
        "eventos": _eventos(traza, p),
        "semillaEventos": int(p.eventos.semilla) if p.eventos.activos else None,
        "corrida": corrida,
    }


def reproductor_html(
    traza: Traza,
    p: ParametrosSimulacion,
    precios: dict[str, float],
    titulo: str = "",
    corrida: str = "",
) -> str:
    """Devuelve el HTML completo del tablero, listo para `st.components.v1.html`."""
    if not p.estacion_real:
        raise ValueError("La animación es del caso real (12 caras en 3 zonas).")
    configuracion = _configuracion(traza, p, precios, titulo, corrida)
    return _PLANTILLA.replace("__CONFIG__", json.dumps(configuracion, separators=(",", ":")))


_PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root { --fondo: transparent; --panel: transparent; --panel2: transparent; --borde: transparent;
          --tinta: transparent; --tenue: transparent; --amarillo: transparent; --rojo: transparent;
          --azul: transparent; --libre: transparent; --naranja: transparent; --asfalto: transparent; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; height: 100%; background: var(--fondo); color: var(--tinta);
               font-family: system-ui, -apple-system, "Segoe UI", sans-serif; overflow: hidden; }
  #app { display: grid; grid-template-rows: auto minmax(0, 1fr) auto auto; gap: 10px; height: 100%;
         padding: 10px; }
  .tarjeta { background: var(--panel); border: 1px solid var(--borde); border-radius: 12px; padding: 10px 14px; }
  .titulo { font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--tenue);
            font-weight: 700; margin-bottom: 6px; }
  .grande { font-size: clamp(16px, 1.55vw, 22px); font-weight: 800; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .chico { font-size: 12px; color: var(--tenue); }
  button, select { background: var(--panel2); color: var(--tinta); border: 1px solid var(--borde);
                   border-radius: 8px; padding: 7px 12px; font-size: 13px; cursor: pointer; font-family: inherit; }
  button:hover:not(:disabled) { border-color: var(--tinta); }
  button:disabled { opacity: .4; cursor: not-allowed; }
  button:focus-visible, select:focus-visible, input:focus-visible { outline: 3px solid var(--amarillo); outline-offset: 2px; }

  #cabecera { display: grid; grid-template-columns: minmax(250px, 1.5fr) repeat(4, minmax(130px, 1fr)) auto; gap: 10px; }
  #marca { display: flex; align-items: center; gap: 12px; }
  #marca .logo { width: 44px; height: 44px; border-radius: 12px; background: var(--amarillo); color: var(--fondo);
                 display: flex; align-items: center; justify-content: center; font-size: 24px; }
  #marca b { font-size: 18px; } #marca div div { font-size: 12px; color: var(--tenue); }
  #estado .punto { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
  #tiempo { display: flex; align-items: center; gap: 10px; }
  #play { background: var(--amarillo); color: var(--fondo); border-color: var(--amarillo); font-weight: 800;
          min-width: 108px; font-size: 14px; }

  #cuerpo { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 10px; min-height: 0; }
  #lienzo { background: var(--asfalto); border: 1px solid var(--borde); border-radius: 12px; min-height: 0;
            overflow: hidden; }
  #lienzo svg { width: 100%; height: 100%; display: block; }
  #derecha { display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow: hidden; }
  #derecha .tarjeta { padding: 10px 12px; }
  .fila { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .pastilla { display: inline-block; border-radius: 999px; padding: 2px 10px; font-size: 12px; font-weight: 800; }
  .barra { height: 8px; border-radius: 6px; background: var(--panel2); overflow: hidden; margin-top: 5px; }
  .barra > i { display: block; height: 100%; border-radius: 6px; }

  #inferior { display: grid; grid-template-columns: 1.3fr 1.2fr 1fr 1.2fr; gap: 10px; }
  #inferior .tarjeta { min-height: 196px; }
  .tanque { text-align: center; }
  .tanque .cuerpo { position: relative; width: 38px; height: 78px; margin: 4px auto; border: 2px solid var(--tenue);
                    border-radius: 7px; overflow: hidden; background: var(--fondo); }
  .tanque .cuerpo i { position: absolute; left: 0; right: 0; bottom: 0; }
  .tanque b { font-size: 11.5px; display: block; white-space: nowrap; } .tanque span { font-size: 11.5px; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .zona-cola { display: flex; align-items: center; justify-content: space-between; gap: 6px; padding: 8px 10px;
               border-radius: 10px; background: var(--panel2); margin-bottom: 6px; font-size: 12.5px; }
  .zona-cola span { white-space: nowrap; }
  .zona-cola b { font-variant-numeric: tabular-nums; }
  #grafico select { float: right; padding: 3px 8px; font-size: 12px; }

  #controles { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 2px 2px 0; }
  #barra { flex: 1; min-width: 200px; accent-color: var(--amarillo); }
  #saltos { display: flex; gap: 6px; flex-wrap: wrap; }
  /* Avisos con pausa (tanda 7) */
  #aviso { position: fixed; inset: 0; display: none; align-items: center; justify-content: center; z-index: 10;
           background: color-mix(in srgb, var(--fondo) 72%, transparent); }
  #aviso.abierto { display: flex; }
  #aviso .caja { max-width: 560px; width: calc(100% - 32px); background: var(--panel); border: 2px solid var(--amarillo);
                 border-radius: 16px; padding: 20px 22px; box-shadow: 0 12px 40px color-mix(in srgb, var(--fondo) 80%, transparent); }
  #aviso h2 { margin: 6px 0 8px; font-size: 22px; }
  #aviso p { margin: 0 0 8px; font-size: 15px; line-height: 1.45; }
  #aviso .botones { display: flex; gap: 10px; justify-content: flex-end; flex-wrap: wrap; margin-top: 14px; }
  #aviso .botones button { font-size: 14px; padding: 9px 14px; }
  #avisoOk { background: var(--amarillo); color: var(--fondo); border-color: var(--amarillo); font-weight: 800; }
  #avisoIcono { font-size: 30px; }
  #avisoCola { float: right; }
  @media (max-width: 1000px) {
    #cabecera { grid-template-columns: 1fr 1fr; } #cuerpo { grid-template-columns: 1fr; }
    #inferior { grid-template-columns: 1fr 1fr; } html, body { overflow: auto; }
  }
</style>
</head>
<body>
<div id="app">
  <div id="cabecera">
    <div id="marca" class="tarjeta">
      <div class="logo" aria-hidden="true">⛽</div>
      <div><b>Estación Shell</b><div>Av. Balloffet 1810 esq. Av. Los Sauces</div><div>San Rafael, Mendoza</div></div>
    </div>
    <div id="estado" class="tarjeta"><div class="titulo">Simulación</div><div id="estadoTexto" class="grande"></div><div id="estadoDia" class="chico"></div></div>
    <div class="tarjeta"><div class="titulo">Clientes hoy</div><div id="kClientes" class="grande"></div><div class="chico">atendidos / esperados</div></div>
    <div class="tarjeta"><div class="titulo">Litros hoy</div><div id="kLitros" class="grande"></div><div class="chico">vendidos / esperados</div></div>
    <div class="tarjeta"><div class="titulo">Ventas hoy</div><div id="kVentas" class="grande"></div><div id="kVentasSub" class="chico"></div></div>
    <div class="tarjeta" id="tiempo"><div><div class="titulo">Tiempo simulado</div><div id="kTiempo" class="grande"></div></div>
      <button id="play" type="button">▶ Reproducir</button></div>
  </div>

  <div id="cuerpo">
    <div id="lienzo"></div>
    <div id="derecha">
      <div class="tarjeta" id="pMini"></div>
      <div class="tarjeta" id="pPlay"></div>
      <div class="tarjeta" id="pGnc"></div>
      <div class="tarjeta" id="pCamion"></div>
      <div class="tarjeta" id="pLeyenda"></div>
    </div>
  </div>

  <div id="inferior">
    <div class="tarjeta"><div class="titulo">Tanques (litros)</div><div id="tanques"></div></div>
    <div class="tarjeta"><div class="titulo">Colas actuales</div><div id="colas"></div></div>
    <div class="tarjeta"><div class="titulo">Indicadores del día</div><div id="indicadores"></div></div>
    <div class="tarjeta" id="grafico">
      <div class="titulo">Gráfico del día
        <select id="tipoGrafico" aria-label="Qué gráfico mostrar">
          <option value="clientes">Clientes por hora</option>
          <option value="ventas">Ventas acumuladas</option>
          <option value="cola">Autos en cola</option>
          <option value="ocupacion">Caras ocupadas</option>
          <option value="nada">Ocultar el gráfico</option>
        </select></div>
      <div id="graficoSvg"></div>
    </div>
  </div>

  <div id="controles">
    <button id="diaMenos" type="button" title="Día anterior">◀ Día</button>
    <button id="diaMas" type="button" title="Día siguiente">Día ▶</button>
    <input type="range" id="barra" min="0" value="0" step="1" aria-label="Posición en el período">
    <label class="chico" for="velocidad">Velocidad</label>
    <select id="velocidad" title="Segundos reales que dura cada día simulado">
      <option value="2">2 s por día</option><option value="5">5 s por día</option>
      <option value="10">10 s por día</option><option value="20">20 s por día</option>
    </select>
    <div id="saltos">
      <button id="saltoPico" type="button">⏭ la hora pico</button>
      <button id="saltoQuiebre" type="button">⏭ el primer quiebre</button>
      <button id="saltoDescarga" type="button">⏭ la próxima descarga</button>
      <button id="saltoCorte" type="button">⏭ el corte de GNC</button>
    </div>
    <label class="chico"><input type="checkbox" id="pausarAvisos" checked> Pausar en los avisos</label>
  </div>
</div>
<div id="aviso" role="dialog" aria-modal="true" aria-labelledby="avisoTitulo" aria-describedby="avisoTexto">
  <div class="caja">
    <span id="avisoCola" class="chico"></span>
    <div id="avisoIcono" aria-hidden="true"></div>
    <h2 id="avisoTitulo"></h2>
    <p id="avisoTexto"></p>
    <div id="avisoNota" class="chico"></div>
    <div class="botones">
      <button id="avisoSeguir" type="button">🚚 Seguir trayectoria del camión</button>
      <button id="avisoOk" type="button">Ok, seguir</button>
    </div>
  </div>
</div>

<script>
const CONFIG = __CONFIG__;
const P = CONFIG.paleta;
const RAIZ = document.documentElement;
for (const [css, clave] of [["--fondo", "fondo"], ["--panel", "panel"], ["--panel2", "panel2"], ["--borde", "borde"],
     ["--tinta", "tinta"], ["--tenue", "tenue"], ["--amarillo", "amarillo"], ["--rojo", "rojo"], ["--azul", "azul"],
     ["--libre", "libre"], ["--naranja", "naranja"], ["--asfalto", "asfalto"]]) RAIZ.style.setProperty(css, P[clave]);
const REDUCIDO = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const F = CONFIG.frames, N = F.t.length, NDIAS = CONFIG.dias;
const GRUPOS = CONFIG.grupos, PROD = CONFIG.productos, ESP = CONFIG.esperado;
const TANQUES = CONFIG.tanques.map((id) => PROD.findIndex((x) => x.id === id));
const EV = CONFIG.eventos || [];
const DESCARGAS = EV.filter((e) => e.tipo === "descarga");
const CORTES = EV.filter((e) => e.tipo === "gnc");
const EVENTOS = EV.filter((e) => e.tipo === "evento");
const DIAS_SEM = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

// ---------------- utilidades ----------------
function esc(t) { return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
function miles(n) { return Math.round(n).toLocaleString("es-AR"); }
function pesos(n) { return "$ " + Math.round(n).toLocaleString("es-AR"); }
function hhmm(m) { const k = Math.floor(m); return String(Math.floor(k / 60) % 24).padStart(2, "0") + ":" + String(k % 60).padStart(2, "0"); }
function diaDe(i) { return Math.min(NDIAS - 1, Math.floor(F.t[i] / 1440)); }
function fechaDe(d) { const [a, m, dd] = CONFIG.inicio.split("-").map(Number); return new Date(Date.UTC(a, m - 1, dd + d)); }
function fechaTexto(d) {
  const f = fechaDe(d), ds = f.getUTCDay();
  return `${DIAS_SEM[ds]} ${f.getUTCDate()} de ${MESES[f.getUTCMonth()]}` + (ds === 0 || ds === 6 ? " · fin de semana" : " · día hábil");
}
const iniDia = new Array(NDIAS + 1).fill(N);
for (let i = N - 1; i >= 0; i--) iniDia[diaDe(i)] = i;
function carriles(g, i) { const s = F.g[g.id].c[i]; const a = []; for (let k = 0; k < s.length; k++) { const c = s.charCodeAt(k); a.push(c === 46 ? -1 : (c === 120 ? -2 : c - 97)); } return a; }
function cola(g, i) { const s = F.g[g.id].q[i]; const a = []; for (let k = 0; k < s.length; k++) a.push(s.charCodeAt(k) - 48); return a; }
function hoy(arr, i) { return arr[i] - arr[iniDia[diaDe(i)]]; }
function sinCombustible(i) {
  const lista = [];
  CONFIG.tanques.forEach((id, k) => { const prod = PROD[TANQUES[k]]; if (F.tk[id].n[i] < prod.minimo) lista.push(prod.nombre); });
  return lista;
}
function fechaHora(minuto) { const d = Math.floor(minuto / 1440); return `${fechaTexto(d).split(" · ")[0]}, ${hhmm(minuto % 1440)}`; }
function corteActivo(t) { return CORTES.find((e) => e.t <= t && t < e.fin); }
function faltaTexto(minutos) {
  const d = Math.floor(minutos / 1440), h = Math.floor((minutos % 1440) / 60);
  return d > 0 ? `${d} d ${h} h` : `${h} h`;
}
function colaTotal(i) { return GRUPOS.reduce((a, g) => a + F.g[g.id].n[i], 0); }
function ocupadasTotal(i) { return GRUPOS.reduce((a, g) => a + carriles(g, i).filter((k) => k >= 0).length, 0); }
function camionesTotal(i) { return CONFIG.tanques.reduce((a, id) => a + F.tk[id].c[i], 0); }

// ---------------- piezas del dibujo ----------------
function texto(x, y, t, tam, o) {
  o = o || {};
  return `<text x="${x}" y="${y}" fill="${o.color || P.tinta}" font-size="${tam}" font-weight="${o.peso || 400}"
    text-anchor="${o.ancla || "start"}" ${o.espaciado ? `letter-spacing="${o.espaciado}"` : ""}>${esc(t)}</text>`;
}
function pastilla(x, y, ancho, alto, relleno, t, colorTexto) {
  return `<rect x="${x}" y="${y}" width="${ancho}" height="${alto}" rx="${alto / 2}" fill="${relleno}"/>` +
    texto(x + ancho / 2, y + alto / 2 + 4, t, 11.5, { ancla: "middle", peso: 800, color: colorTexto });
}
// Auto visto desde arriba: el frente (parabrisas y faros) mira hacia el surtidor (arriba).
function autoV(cx, cy, color, espera) {
  const aro = espera ? `<rect x="-24" y="-33" width="48" height="66" rx="12" fill="none" stroke="${P.naranja}" stroke-width="3" stroke-dasharray="6 4"/>` : "";
  return `<g transform="translate(${cx},${cy})">${aro}
    <rect x="-17" y="-27" width="34" height="54" rx="10" fill="${color}" stroke="${P.tinta}" stroke-width="1.4"/>
    <rect x="-12" y="-17" width="24" height="9" rx="3" fill="${P.vidrio}" opacity="0.75"/>
    <rect x="-12" y="8" width="24" height="9" rx="3" fill="${P.vidrio}" opacity="0.55"/>
    <circle cx="-10" cy="-25" r="2.3" fill="${P.faros}"/><circle cx="10" cy="-25" r="2.3" fill="${P.faros}"/>
  </g>`;
}
function autoH(cx, cy, color) {
  return `<g transform="translate(${cx},${cy})"><rect x="-22" y="-9" width="44" height="18" rx="6" fill="${color}" stroke="${P.tinta}" stroke-width="1.2"/>
    <rect x="-8" y="-6" width="14" height="12" rx="3" fill="${P.vidrio}" opacity="0.6"/>
    <circle cx="20" cy="-5" r="1.8" fill="${P.faros}"/><circle cx="20" cy="5" r="1.8" fill="${P.faros}"/></g>`;
}
function persona(cx, cy, relleno) {
  return `<g transform="translate(${cx},${cy})"><circle cx="0" cy="-7" r="5" fill="${relleno}" stroke="${P.tinta}" stroke-width="1.2"/>
    <path d="M -8 10 Q -8 0 0 0 Q 8 0 8 10 Z" fill="${relleno}" stroke="${P.tinta}" stroke-width="1.2"/></g>`;
}
function arbol(cx, cy, r) {
  return `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${P.arbol}"/><circle cx="${cx - r * 0.25}" cy="${cy - r * 0.25}" r="${r * 0.6}" fill="${P.arbol2}"/>`;
}
function camionIcono(cx, cy, color, escala) {
  return `<g transform="translate(${cx},${cy}) scale(${escala || 0.6})"><rect x="-24" y="-11" width="32" height="20" rx="5" fill="${color}" stroke="${P.tinta}" stroke-width="1.6"/>
    <rect x="8" y="-6" width="15" height="15" rx="3" fill="${P.plata}" stroke="${P.tinta}" stroke-width="1.6"/>
    <circle cx="-14" cy="11" r="4.2" fill="${P.neumatico}"/><circle cx="14" cy="11" r="4.2" fill="${P.neumatico}"/></g>`;
}

// ---------------- geometría del playón (SVG 940 × 592) ----------------
const W = 940, H = 592, LANE = 64, PAD = 12, GAP = 14, X0 = 30;
const Y_PANEL = 40, Y_TAG = 48, Y_ALERTA = 78, Y_BOMBA = 104, Y_BAHIA = 164, Y_ESTADO = 246, Y_COLA = 262, FILA = 66;
const Y_AV = 500;
let cursor = X0;
for (const g of GRUPOS) { g.x = cursor; g.w = g.caras * LANE + 2 * PAD; cursor += g.w + GAP; }
const X_FIN = cursor - GAP;
const COLOR_TAG = { A: ["amarillo", "fondo"], B: ["rojo", "blanco"], C: ["azul", "blanco"] };
let BOMBA_N = {};   // número de surtidor (S1, S2…) dentro de cada zona: una cara = un surtidor

function dibujarCanvas(i) {
  const faltantes = sinCombustible(i), hayCorte = F.gnc[i] === 1;
  const ventana = Math.max(1, Math.round(20 / CONFIG.dt));
  let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Playón de la estación a las ${hhmm(F.t[i] % 1440)}" preserveAspectRatio="xMidYMid meet">`;
  s += `<rect width="${W}" height="${H}" fill="${P.asfalto}"/>`;
  s += arbol(14, 60, 22) + arbol(10, 200, 18) + arbol(W - 16, 70, 24) + arbol(W - 10, 220, 18) + arbol(W - 22, 360, 22);
  // techo del playón
  s += `<rect x="${X0 - 8}" y="10" width="${X_FIN - X0 + 16}" height="24" rx="8" fill="${P.amarillo}"/><rect x="${X0 - 8}" y="28" width="${X_FIN - X0 + 16}" height="6" fill="${P.rojo}"/>`;
  let esperando = 0;
  GRUPOS.forEach((g) => {
    const datos = F.g[g.id], car = carriles(g, i), cl = cola(g, i), largo = datos.n[i];
    const llena = g.cap !== null && largo >= g.cap;
    const rec = datos.r[i] - datos.r[Math.max(0, i - ventana)];
    const prods = g.productos.map((k) => PROD[k]);
    const esGnc = prods.some((pr) => pr.gnc);
    const falta = prods.filter((pr) => faltantes.includes(pr.nombre));
    const cortado = esGnc && hayCorte;
    const ocup = car.filter((k) => k >= 0).length;
    s += `<rect x="${g.x}" y="${Y_PANEL}" width="${g.w}" height="${Y_AV - 14 - Y_PANEL}" rx="12" fill="${P.asfalto2}" stroke="${llena ? P.rojo : P.borde}" stroke-width="${llena ? 3 : 1.5}"/>`;
    const [fondoTag, textoTag] = COLOR_TAG[g.id] || ["amarillo", "fondo"];
    const nombre = esGnc ? "GNC" : g.nombre.toUpperCase();
    s += `<rect x="${g.x + 8}" y="${Y_TAG}" width="${g.w - 16}" height="24" rx="6" fill="${P[fondoTag]}"/>` +
         texto(g.x + 16, Y_TAG + 17, `ZONA ${g.id} · ${nombre}`, 12.5, { peso: 800, color: P[textoTag] });
    s += texto(g.x + g.w - 10, Y_ALERTA + 14, (g.w < 200 ? `${ocup} / ${g.caras}` : `${ocup} / ${g.caras} ocupadas`), 11.5, { ancla: "end", peso: 700, color: P.tenue });
    const alerta = cortado ? "GNC CORTADO" : (falta.length ? "SIN STOCK" : (llena ? "COLA LLENA" : ""));
    if (alerta) s += pastilla(g.x + 8, Y_ALERTA, Math.min(112, Math.max(64, g.w - 16 - 74)), 18, P.rojo, alerta, P.blanco);
    if (cortado) {
      const corte = corteActivo(F.t[i]);
      if (corte) s += texto(g.x + g.w / 2, Y_AV - 44, `el GNC vuelve en ${faltaTexto(corte.fin - F.t[i])}`, 13, { ancla: "middle", peso: 800, color: P.rojo });
    }
    // surtidores y bahías, una por cara
    for (let c = 0; c < g.caras; c++) {
      const cx = g.x + PAD + c * LANE + LANE / 2;
      s += `<rect x="${cx - 21}" y="${Y_BOMBA}" width="42" height="58" rx="8" fill="${P.panel2}" stroke="${P.tinta}" stroke-width="1.6"/>`;
      const nb = prods.length;
      prods.forEach((pr, q) => { s += `<rect x="${cx - 17 + q * (34 / nb)}" y="${Y_BOMBA + 5}" width="${34 / nb}" height="10" fill="${pr.color}"/>`; });
      s += texto(cx, Y_BOMBA + 40, `S${c + 1}`, 15, { ancla: "middle", peso: 800 });
      s += `<rect x="${cx - 28}" y="${Y_BAHIA}" width="56" height="74" rx="8" fill="${P.asfalto}" stroke="${P.linea}" stroke-width="1.4" stroke-dasharray="5 5" opacity="0.8"/>`;
      const codigo = car[c];
      let estado = "libre", colorEstado = P.tenue;
      if (cortado) { estado = "cortada"; colorEstado = P.rojo; }
      if (codigo === -2) {            // cara fuera de servicio (evento aleatorio): tachada hasta que llega el técnico
        estado = "fuera"; colorEstado = P.rojo;
        s += `<line x1="${cx - 18}" y1="${Y_BOMBA + 4}" x2="${cx + 18}" y2="${Y_BOMBA + 54}" stroke="${P.rojo}" stroke-width="4"/>` +
             `<line x1="${cx + 18}" y1="${Y_BOMBA + 4}" x2="${cx - 18}" y2="${Y_BOMBA + 54}" stroke="${P.rojo}" stroke-width="4"/>`;
      }
      if (codigo >= 0) {
        const k = codigo >> 1, espera = (codigo & 1) === 1;
        s += autoV(cx, Y_BAHIA + 37, PROD[k].color, espera);
        estado = espera ? "espera" : "carga"; colorEstado = P.tinta; if (espera) esperando++;
      }
      s += texto(cx, Y_ESTADO + 4, estado, 11.5, { ancla: "middle", color: colorEstado, peso: codigo >= 0 ? 800 : 400 });
    }
    // cola: 3 lugares por cara, ordenados desde la cara hacia atrás
    const cols = g.caras, filas = Math.ceil((g.cap === null ? 12 : g.cap) / cols);
    for (let k = 0; k < filas * cols; k++) {
      const f = Math.floor(k / cols), c = k % cols;
      const cx = g.x + PAD + c * LANE + LANE / 2, cy = Y_COLA + f * FILA + FILA / 2;
      if (k < cl.length) s += autoV(cx, cy, PROD[cl[k]].color, false);
      else s += `<rect x="${cx - 21}" y="${cy - 30}" width="42" height="60" rx="9" fill="none" stroke="${P.tenue}" stroke-width="1.3" stroke-dasharray="4 4" opacity="0.55"/>`;
    }
    if (largo > cl.length) s += pastilla(g.x + g.w / 2 - 36, Y_COLA + filas * FILA + 2, 72, 18, P.panel2, `+${largo - cl.length} más`, P.tinta);
    s += texto(g.x + g.w / 2, Y_AV - 24, `cola ${largo} / ${g.cap === null ? "∞" : g.cap}`, 12.5, { ancla: "middle", color: P.tenue, peso: 700 });
    // rechazados: pasan de largo por la avenida
    if (rec > 0) {
      const xr = g.x + g.w / 2;
      s += autoH(xr - 28, Y_AV + 42, P.rojo) + (rec > 1 ? autoH(xr + 24, Y_AV + 42, P.rojo) : "");
      s += texto(xr, Y_AV + 16, `+${rec} pasaron de largo`, 12, { ancla: "middle", peso: 800 });
    }
  });
  // avenida
  s += `<rect x="0" y="${Y_AV}" width="${W}" height="${H - Y_AV}" fill="${P.negro}"/><line x1="0" y1="${Y_AV + 46}" x2="${W}" y2="${Y_AV + 46}" stroke="${P.linea}" stroke-width="2" stroke-dasharray="26 18" opacity="0.7"/>`;
  s += texto(W - 14, Y_AV + 18, "AV. BALLOFFET — RN 143 (tramo urbano)", 12.5, { ancla: "end", peso: 800, espaciado: 1 });
  // camión cisterna: se lo ve llegar por la avenida (2 h antes) y descargar (45 min, INV-04)
  const ahora = F.t[i];
  DESCARGAS.filter((e) => e.t - 120 <= ahora && ahora <= e.t + 45).slice(0, 2).forEach((e, k) => {
    const xFin = W - 150 - k * 130, llegando = ahora < e.t;
    const x = llegando ? W + 60 - ((ahora - (e.t - 120)) / 120) * (W + 60 - xFin) : xFin;
    const prod = PROD.find((pr) => pr.id === e.id);
    s += camionIcono(x, Y_AV + 62, prod ? prod.color : P.amarillo, 1.25);
    s += texto(x, Y_AV + 38, llegando ? `camión de ${e.producto} llegando` : `descargando ${miles(e.litros)} L de ${e.producto}`, 11.5, { ancla: "middle", peso: 800 });
  });
  s += `</svg>`;
  document.getElementById("lienzo").innerHTML = s;
  return esperando;
}

// ---------------- paneles ----------------
function panelDerecho(i, esperando) {
  const colaC = F.colaCaja[i], ocupC = F.cajasOcup[i], MAXP = 9;
  let h = `<div class="titulo">Shell Shop</div><div class="chico">minimarket · entra el ${Math.round(CONFIG.probCompra * 100)} %</div>`;
  h += `<div class="chico" style="margin-top:8px">Fila para pagar</div><svg width="100%" height="30" viewBox="0 0 270 30">`;
  for (let k = 0; k < Math.min(colaC, MAXP); k++) h += persona(14 + k * 28, 18, P.panel2);
  if (colaC > MAXP) h += texto(14 + MAXP * 28, 22, `+${colaC - MAXP}`, 13, { peso: 800 });
  if (colaC === 0) h += texto(2, 20, "sin fila", 13, { color: P.tenue });
  h += `</svg>`;
  for (let k = 0; k < CONFIG.cajas; k++) {
    const ocupada = k < ocupC;
    h += `<div class="fila" style="border:2px solid ${ocupada ? P.naranja : P.libre};border-radius:8px;padding:6px 10px;margin-top:4px"><b>CAJA ${k + 1}</b><span style="color:${ocupada ? P.tinta : P.libre};font-weight:700">${ocupada ? "cobrando" : "libre"}</span></div>`;
  }
  document.getElementById("pMini").innerHTML = h;

  const turno = F.playTurno[i], ocup = F.playOcup[i];
  let pl = `<div class="titulo">Playeros</div><svg width="100%" height="30" viewBox="0 0 270 30">`;
  for (let k = 0; k < turno; k++) pl += persona(14 + k * 28, 18, k < ocup ? P.amarillo : P.panel2);
  pl += `</svg><div class="chico">${turno} en turno · ${ocup} atendiendo · naranja punteado = cara esperando al playero</div>`;
  if (esperando > 0) pl += `<div style="margin-top:6px"><span class="pastilla" style="background:${P.naranja};color:${P.negro}">${esperando} cara${esperando > 1 ? "s" : ""} espera${esperando > 1 ? "n" : ""} playero</span></div>`;
  EVENTOS.filter((e) => e.t <= F.t[i] && F.t[i] < e.fin).slice(0, 3).forEach((e) => {
    pl += `<div class="chico" style="margin-top:6px;color:${P.amarillo};font-weight:700">⚡ ${e.titulo} · hasta ${fechaHora(e.fin)}</div>`;
  });
  document.getElementById("pPlay").innerHTML = pl;

  let gn = `<div class="titulo">GNC</div><div class="fila">`;
  if (F.gnc[i] === 1) { const corte = corteActivo(F.t[i]); gn += `<span class="pastilla" style="background:${P.rojo};color:${P.blanco}">GNC CORTADO</span>` + (corte ? `<b>vuelve en ${faltaTexto(corte.fin - F.t[i])}</b>` : ""); }
  else if (F.gnc[i] === 2) gn += `<span class="pastilla" style="background:${P.naranja};color:${P.negro}">COMPRESORES AL 50 %</span>`;
  else gn += `<span class="pastilla" style="background:${P.libre};color:${P.negro}">DISPONIBLE</span>`;
  gn += `</div><div class="chico" style="margin-top:6px">${F.comp[i]} de ${F.compTot[i]} compresores en uso · ${GRUPOS.some(g => g.playero && g.productos.includes(PROD.findIndex(x => x.id === "gnc"))) ? "lo carga un playero" : "sin playero"}</div>`;
  document.getElementById("pGnc").innerHTML = gn;

  let cm = `<div class="titulo">Camión cisterna</div><div class="chico">${esc(CONFIG.ruta.escenario)}</div>`;
  let n = 0;
  CONFIG.tanques.forEach((id, k) => {
    const prog = F.tk[id].p[i]; if (prog < 0) return; n++;
    const prod = PROD[TANQUES[k]];
    cm += `<div class="fila" style="margin-top:4px;font-size:12.5px"><b>${esc(prod.nombre)}</b><span>llega en ${F.tk[id].h[i].toFixed(1)} h</span></div>
      <div class="barra" style="height:6px;margin-top:2px"><i style="width:${Math.round(prog * 100)}%;background:${prod.color}"></i></div>`;
    if (F.tk[id].d[i] > 0) cm += `<div class="chico" style="color:${P.naranja}">corte en la ruta: +${F.tk[id].d[i].toFixed(1)} h</div>`;
  });
  if (!n) cm += `<div class="chico" style="margin-top:6px">sin pedidos en camino</div>`;
  document.getElementById("pCamion").innerHTML = cm;

  if (!panelDerecho.leyenda) {
    panelDerecho.leyenda = true;
    let ly = `<div class="titulo">Color del auto = producto</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 8px;font-size:12px">`;
    PROD.forEach((pr) => { ly += `<div><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${pr.color};border:1px solid ${P.tinta};vertical-align:-2px"></span> ${esc(pr.nombre)}</div>`; });
    ly += `</div>`;
    document.getElementById("pLeyenda").innerHTML = ly;
  }
}

function panelesInferiores(i) {
  const d = diaDe(i), ini = iniDia[d];
  let t = `<div id="tanquesGrid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">`;
  CONFIG.tanques.forEach((id, k) => {
    const prod = PROD[TANQUES[k]], nivel = F.tk[id].n[i], fr = Math.max(0, Math.min(1, nivel / prod.capacidad));
    const pct = Math.round(fr * 100), color = pct > 50 ? P.libre : (pct > 20 ? P.naranja : P.rojo);
    t += `<div class="tanque"><b>${esc(prod.nombre)}</b><div class="cuerpo"><i style="height:${fr * 100}%;background:${prod.color}"></i></div>
      <span>${miles(nivel)} L</span><br><span style="color:${color};font-weight:800">${pct} %</span></div>`;
  });
  document.getElementById("tanques").innerHTML = t + "</div>";

  let c = "";
  GRUPOS.forEach((g) => {
    const dat = F.g[g.id], n = dat.n[i];
    const dn = dat.ne[i] - dat.ne[ini], dsw = dat.sw[i] - dat.sw[ini];
    const tc = dn > 0 ? (dsw / dn) : null;
    const esGnc = g.productos.some((k) => PROD[k].gnc);
    c += `<div class="zona-cola"><span>${esGnc ? "GNC" : esc(g.nombre)} · S1–S${g.caras}</span>
      <span><b>${n}</b> en cola</span><span class="chico" title="espera promedio de hoy">⏱ ${tc === null ? "—" : tc.toFixed(1).replace(".", ",") + " min"}</span></div>`;
  });
  document.getElementById("colas").innerHTML = c;

  const cli = hoy(F.atend, i), eCli = ESP.clientes[d];
  let lit = 0, ven = 0;
  PROD.forEach((pr, k) => { const dl = F.lit[k][i] - F.lit[k][ini]; if (!pr.gnc) lit += dl; ven += dl * pr.precio; });
  const eLit = ESP.litros[d], eVen = ESP.ventas[d];
  const fila = (nombre, texto, frac, color) => `<div style="margin-bottom:10px"><div class="fila"><span>${nombre}</span><b>${texto}</b></div>
    <div class="barra"><i style="width:${Math.min(100, Math.round(frac * 100))}%;background:${color}"></i></div><div class="chico" style="text-align:right">${Math.round(frac * 100)} %</div></div>`;
  document.getElementById("indicadores").innerHTML =
    fila("Clientes atendidos", `${miles(cli)} / ${miles(eCli)}`, eCli ? cli / eCli : 0, P.libre) +
    fila("Litros vendidos", `${miles(lit)} / ${miles(eLit)}`, eLit ? lit / eLit : 0, P.amarillo) +
    fila("Ventas", pesos(ven), eVen ? ven / eVen : 0, P.azul);
  return { cli, eCli, lit, eLit, ven, eVen };
}

// ---------------- gráfico a elección ----------------
function marcaFrame(d, minuto) { return Math.min(N - 1, iniDia[d] + Math.round(minuto / CONFIG.dt)); }
function grafico(i) {
  const tipo = document.getElementById("tipoGrafico").value, cont = document.getElementById("graficoSvg");
  if (tipo === "nada") { cont.innerHTML = `<div class="chico" style="padding:20px 0">Gráfico oculto.</div>`; return; }
  const d = diaDe(i), ini = iniDia[d], minAhora = F.t[i] - d * 1440;
  const w = 330, h = 150, ml = 38, mb = 22, mt = 8, mr = 8, pw = w - ml - mr, ph = h - mt - mb;
  let pts = [], etiqueta = "", barras = false;
  if (tipo === "clientes") {
    barras = true; etiqueta = "clientes";
    for (let hr = 0; hr < 24; hr++) { if (hr * 60 > minAhora) break;
      const a = marcaFrame(d, hr * 60), b = Math.min(i, marcaFrame(d, (hr + 1) * 60)); pts.push([hr + 0.5, Math.max(0, F.atend[b] - F.atend[a])]); }
  } else if (tipo === "ventas") {
    etiqueta = "$"; for (let hr = 0; hr <= 24; hr++) { if (hr * 60 > minAhora) break;
      const f = Math.min(i, marcaFrame(d, hr * 60)); let v = 0; PROD.forEach((pr, k) => { v += (F.lit[k][f] - F.lit[k][ini]) * pr.precio; }); pts.push([hr, v]); }
  } else {
    etiqueta = tipo === "cola" ? "autos" : "caras";
    for (let f = ini; f <= i; f++) pts.push([(F.t[f] - d * 1440) / 60, tipo === "cola" ? colaTotal(f) : ocupadasTotal(f)]);
  }
  const ymax = Math.ceil(Math.max(4, ...pts.map((q) => q[1])) * 1.05 / 4) * 4;
  const X = (x) => ml + (x / 24) * pw, Y = (y) => mt + ph - (y / ymax) * ph;
  let s = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="150">`;
  for (let g = 0; g <= 4; g++) { const yv = (ymax / 4) * g; s += `<line x1="${ml}" y1="${Y(yv)}" x2="${w - mr}" y2="${Y(yv)}" stroke="${P.borde}"/>` +
    texto(ml - 4, Y(yv) + 4, tipo === "ventas" ? (Math.round(yv / 1000) + " k") : (Math.round(yv * 10) / 10).toString().replace(".", ","), 10.5, { ancla: "end", color: P.tenue }); }
  [0, 6, 12, 18, 24].forEach((hr) => { s += texto(X(hr), h - 6, hr + " h", 10.5, { ancla: "middle", color: P.tenue }); });
  if (barras) pts.forEach((q) => { s += `<rect x="${X(q[0]) - 6}" y="${Y(q[1])}" width="12" height="${mt + ph - Y(q[1])}" fill="${P.amarillo}"/>`; });
  else if (pts.length) s += `<polyline fill="none" stroke="${P.amarillo}" stroke-width="2.2" points="${pts.map((q) => X(q[0]) + "," + Y(q[1])).join(" ")}"/>`;
  s += `<line x1="${X(minAhora / 60)}" y1="${mt}" x2="${X(minAhora / 60)}" y2="${mt + ph}" stroke="${P.tenue}" stroke-dasharray="3 3"/></svg>`;
  cont.innerHTML = s;
}

// ---------------- cabecera ----------------
function cabecera(i, k, terminada) {
  const d = diaDe(i), minD = F.t[i] - d * 1440;
  document.getElementById("estadoTexto").innerHTML = `<span class="punto" style="background:${terminada ? P.tenue : (reproduciendo ? P.libre : P.naranja)}"></span>` +
    (terminada ? "Terminada" : (reproduciendo ? "En curso" : "En pausa"));
  document.getElementById("estadoDia").textContent = `Día ${d + 1} de ${NDIAS} · ${hhmm(minD)}`;
  document.getElementById("kClientes").textContent = `${miles(k.cli)} / ${miles(k.eCli)}`;
  document.getElementById("kLitros").textContent = `${miles(k.lit)} / ${miles(k.eLit)}`;
  document.getElementById("kVentas").textContent = pesos(k.ven);
  document.getElementById("kVentasSub").textContent = fechaTexto(d);
  document.getElementById("kTiempo").textContent = `${d} d ${hhmm(minD)}`;
}

// ---------------- reproductor ----------------
const barra = document.getElementById("barra"), botonPlay = document.getElementById("play"), selVel = document.getElementById("velocidad");
const ultimo = N - 1;
let posicion = 0, reproduciendo = false, ultimoInstante = 0, ultimoDibujado = -1;
barra.max = String(ultimo);
selVel.value = REDUCIDO ? "20" : "5";

function mostrar(pos) {
  posicion = Math.max(0, Math.min(ultimo, pos));
  const i = Math.round(posicion);
  if (i === ultimoDibujado) return;
  ultimoDibujado = i;
  const esperando = dibujarCanvas(i);
  panelDerecho(i, esperando);
  const k = panelesInferiores(i);
  cabecera(i, k, i >= ultimo && !reproduciendo);
  grafico(i);
  barra.value = String(i);
}
// ---------------- avisos con pausa (los lee de la traza; se muestran de a uno, en orden) ----------------
function frameDe(t) { let lo = 0, hi = N - 1; while (lo < hi) { const m = (lo + hi) >> 1; if (F.t[m] < t) lo = m + 1; else hi = m; } return lo; }
const AVISOS = new Map();
EV.forEach((e) => { if (e.tipo === "descarga") return; const f = frameDe(e.t); if (!AVISOS.has(f)) AVISOS.set(f, []); AVISOS.get(f).push(e); });
let colaAvisos = [], avisoActual = null, revisadoHasta = -1, reanudar = false;
const caja = document.getElementById("aviso"), botonOk = document.getElementById("avisoOk"), botonSeguir = document.getElementById("avisoSeguir");
function abrirAviso() {
  avisoActual = colaAvisos.shift();
  const e = avisoActual;
  document.getElementById("avisoCola").textContent = colaAvisos.length ? `+${colaAvisos.length} aviso${colaAvisos.length > 1 ? "s" : ""} más` : "";
  document.getElementById("avisoNota").textContent = "";
  if (e.tipo === "pedido") {
    document.getElementById("avisoIcono").textContent = "⛽";
    document.getElementById("avisoTitulo").textContent = `Bajo nivel de combustible: ${e.producto}, ${e.pct} %`;
    document.getElementById("avisoTexto").textContent = `Se pidió un camión de ${miles(e.litros)} L a ${e.origen}` +
      (e.redirigido ? " (el origen habitual no podía cumplirlo: pedido redirigido)" : "") + `. Llega el ${fechaHora(e.llega)}.`;
    document.getElementById("avisoNota").textContent = "El aviso salta cuando lo que hay en el tanque más lo que viene en camino baja al punto de pedido s: es el mismo momento en que se pide el camión.";
    botonSeguir.hidden = false;
  } else if (e.tipo === "evento") {
    document.getElementById("avisoIcono").textContent = "⚡";
    document.getElementById("avisoTitulo").textContent = e.titulo;
    document.getElementById("avisoTexto").textContent = e.texto;
    document.getElementById("avisoNota").textContent = `Evento aleatorio sorteado con la semilla ${CONFIG.semillaEventos}: con la misma semilla sale siempre igual. El detalle de todos está en la pestaña ⚡ Eventos.`;
    botonSeguir.hidden = true;
  } else {
    const total = Math.round((e.fin - e.inicio) / 1440), resta = e.fin - e.t;
    document.getElementById("avisoIcono").textContent = "🔥";
    document.getElementById("avisoTitulo").textContent = e.inicio < e.t ? "El GNC sigue cortado" : `El GNC se cortó por ${total} día${total === 1 ? "" : "s"}`;
    document.getElementById("avisoTexto").textContent = (e.inicio < e.t ? "El corte empezó antes del período. " : "") +
      `Vuelve el ${fechaHora(e.fin)} (en ${faltaTexto(resta)}). Mientras tanto los clientes de GNC pasan a Súper o se van; en la zona GNC se ve la cuenta regresiva.`;
    botonSeguir.hidden = true;
  }
  caja.classList.add("abierto");
  botonOk.focus();
}
function cerrarAviso(seguirReproduciendo) {
  caja.classList.remove("abierto");
  avisoActual = null;
  if (colaAvisos.length) { abrirAviso(); return; }
  if (seguirReproduciendo && reanudar) { reanudar = false; reproducir(); }
}
botonOk.addEventListener("click", () => cerrarAviso(true));
caja.addEventListener("keydown", (ev) => { if (ev.key === "Escape") cerrarAviso(true); });
botonSeguir.addEventListener("click", () => {
  const e = avisoActual;
  const detalle = Object.assign({}, e, { corrida: CONFIG.corrida, fechaPedido: fechaHora(e.t), fechaLlega: fechaHora(e.llega) });
  try {
    const padre = window.parent, doc = padre.document;
    padre.sessionStorage.setItem("camionSeguido", JSON.stringify(detalle));
    padre.dispatchEvent(new CustomEvent("camion-seguido", { detail: detalle }));
    const pestania = Array.from(doc.querySelectorAll('[role="tab"]')).find((b) => b.textContent.includes("Red y rutas"));
    if (!pestania) throw new Error("sin pestaña");
    pestania.click();
    pestania.scrollIntoView({ block: "start" });
    reanudar = false;
    caja.classList.remove("abierto");
    avisoActual = null;
  } catch (err) {
    document.getElementById("avisoNota").textContent = "Abrí la pestaña 🗺️ Red y rutas (arriba): ahí se ve el camión sobre su ruta.";
  }
});
function revisarAvisos(hasta) {
  if (!document.getElementById("pausarAvisos").checked) { revisadoHasta = hasta; return false; }
  for (let f = revisadoHasta + 1; f <= hasta; f++) {
    if (AVISOS.has(f)) {
      revisadoHasta = f;
      mostrar(f); reproduciendo = false; botonPlay.textContent = "▶ Reproducir"; ultimoDibujado = -1; mostrar(f);
      colaAvisos = colaAvisos.concat(AVISOS.get(f)); reanudar = true; abrirAviso();
      return true;
    }
  }
  revisadoHasta = hasta;
  return false;
}
function paso(instante) {
  if (!reproduciendo) return;
  const transcurrido = (instante - ultimoInstante) / 1000; ultimoInstante = instante;
  const siguiente = posicion + (transcurrido * (1440 / Number(selVel.value))) / CONFIG.dt;
  if (revisarAvisos(Math.min(ultimo, Math.round(siguiente)))) return;
  if (siguiente >= ultimo) { mostrar(ultimo); pausar(); return; }
  mostrar(siguiente);
  requestAnimationFrame(paso);
}
function reproducir() {
  if (posicion >= ultimo) { ultimoDibujado = -1; mostrar(0); revisadoHasta = -1; }
  if (colaAvisos.length) { reanudar = true; abrirAviso(); return; }
  reproduciendo = true; botonPlay.textContent = "⏸ Pausar"; ultimoInstante = performance.now();
  if (revisarAvisos(Math.round(posicion))) return;
  requestAnimationFrame(paso);
}
function pausar() { reproduciendo = false; botonPlay.textContent = "▶ Reproducir"; ultimoDibujado = -1; mostrar(posicion); }
botonPlay.addEventListener("click", () => (reproduciendo ? pausar() : reproducir()));
barra.addEventListener("input", () => { reproduciendo = false; botonPlay.textContent = "▶ Reproducir"; ultimoDibujado = -1; mostrar(Number(barra.value)); revisadoHasta = Math.round(posicion); });
document.getElementById("tipoGrafico").addEventListener("change", () => grafico(Math.round(posicion)));
function saltar(i) { reproduciendo = false; botonPlay.textContent = "▶ Reproducir"; ultimoDibujado = -1; mostrar(i); revisadoHasta = Math.round(posicion); }
document.getElementById("diaMas").addEventListener("click", () => saltar(iniDia[Math.min(NDIAS - 1, diaDe(Math.round(posicion)) + 1)]));
document.getElementById("diaMenos").addEventListener("click", () => saltar(iniDia[Math.max(0, diaDe(Math.round(posicion)) - 1)]));

let iPico = 0, mejor = -1, iQuiebre = -1, iCorte = -1;
for (let i = 0; i < N; i++) { const c = colaTotal(i); if (c > mejor) { mejor = c; iPico = i; } }
for (let i = 0; i < N && iQuiebre < 0; i++) if (sinCombustible(i).length) iQuiebre = i;
for (let i = 0; i < N && iCorte < 0; i++) if (F.gnc[i] > 0) iCorte = i;
document.getElementById("saltoPico").addEventListener("click", () => saltar(iPico));
const bQ = document.getElementById("saltoQuiebre"); bQ.disabled = iQuiebre < 0;
bQ.title = iQuiebre < 0 ? "No hubo quiebre de stock en este período" : ""; bQ.addEventListener("click", () => saltar(iQuiebre));
const bC = document.getElementById("saltoCorte"); bC.disabled = iCorte < 0;
bC.title = iCorte < 0 ? "No hubo cortes de GNC en este período (no incluye invierno)" : ""; bC.addEventListener("click", () => saltar(iCorte));
document.getElementById("saltoDescarga").addEventListener("click", () => {
  for (let i = Math.round(posicion) + 1; i < N; i++) if (camionesTotal(i) < camionesTotal(i - 1)) { saltar(i); return; }
  saltar(ultimo);
});
mostrar(0);
</script>
</body>
</html>
"""


# =============================================================================
# Seguimiento del camión (pestaña Red y rutas, tanda 7)
# =============================================================================
#: Alto del componente de seguimiento en píxeles.
ALTO_SEGUIMIENTO = 470


def seguimiento_html(p: ParametrosSimulacion, corrida: str = "") -> str:
    """El mapa de la red con el camión que se eligió seguir desde un aviso de la animación.

    No simula nada: recibe el pedido (producto, origen, fechas) del tablero por un evento del navegador
    y lo dibuja sobre la ruta óptima desde ese origen.
    """
    red = p.red
    origenes = ("DOCK", *valor("RED-19"))
    configuracion = {
        "corrida": corrida,
        "nodos": {n: POSICION_NODO[n] for n in POSICION_NODO},
        "nombres": NOMBRE_NODO,
        "arcos": [[a.a, a.b, a.km, a.ruta] for a in red.arcos] if red else [],
        "rutas": {o: list(camino_mas_corto(red, origen=o).ruta) for o in origenes} if red else {},
        "km": {o: round(camino_mas_corto(red, origen=o).km, 1) for o in origenes} if red else {},
        "habitual": red.origen if red else "DOCK",
        "paleta": paleta_json(),
    }
    return _PLANTILLA_SEGUIMIENTO.replace("__CONFIG__", json.dumps(configuracion, separators=(",", ":")))


_PLANTILLA_SEGUIMIENTO = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  #cartel { border-radius: 12px; padding: 10px 14px; margin-bottom: 8px; font-size: 15px; line-height: 1.4; }
  #cartel b { font-size: 16px; }
  svg { width: 100%; height: 360px; display: block; border-radius: 12px; }
</style></head><body>
<div id="cartel" role="status" aria-live="polite"></div>
<div id="mapa"></div>
<script>
const C = __CONFIG__, P = C.paleta;
document.body.style.background = P.fondo; document.body.style.color = P.tinta;
const W = 900, H = 360, LON = [-70.4, -65.4], LAT = [-35.8, -32.6];
const X = (lon) => 20 + (lon - LON[0]) / (LON[1] - LON[0]) * (W - 40);
const Y = (lat) => H - 20 - (lat - LAT[0]) / (LAT[1] - LAT[0]) * (H - 40);
const pos = (n) => [X(C.nodos[n][0]), Y(C.nodos[n][1])];
const REDUCIDO = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
function esc(t) { return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
function miles(n) { return Math.round(n).toLocaleString("es-AR"); }
let animando = null;
function dibujar(origen, progreso) {
  const ruta = C.rutas[origen] || [];
  const enRuta = new Set(ruta.slice(1).map((n, k) => [ruta[k], n].sort().join("|")));
  let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ruta del camión desde ${esc(C.nombres[origen] || "")}">`;
  s += `<rect width="${W}" height="${H}" fill="${P.panel}"/>`;
  C.arcos.forEach(([a, b, km, nombre]) => {
    const [x1, y1] = pos(a), [x2, y2] = pos(b), activa = enRuta.has([a, b].sort().join("|"));
    if (activa) s += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${P.tinta}" stroke-width="12" stroke-linecap="round"/>`;
    s += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${activa ? P.amarillo : P.borde}" stroke-width="${activa ? 8 : 3}" stroke-linecap="round"/>`;
  });
  Object.keys(C.nodos).forEach((n) => {
    const [x, y] = pos(n), esDestino = n === "SANRAFAEL", esOrigen = n === origen;
    s += `<circle cx="${x}" cy="${y}" r="${esDestino || esOrigen ? 9 : 6}" fill="${esDestino ? P.rojo : (esOrigen ? P.tinta : P.tenue)}" stroke="${P.fondo}" stroke-width="2"/>`;
    const abajo = ["MONTECOMAN", "ALVEAR", "SOSNEADO", "DOCK"].includes(n), izquierda = n === "SANRAFAEL";
    s += `<text x="${x + (izquierda ? -12 : 0)}" y="${abajo ? y + 24 : y - 13}" font-size="13" font-weight="${esDestino || esOrigen ? 800 : 500}" fill="${P.tinta}" text-anchor="${izquierda ? "end" : "middle"}">${esc(C.nombres[n])}</text>`;
  });
  if (ruta.length > 1 && progreso !== null) {
    const largos = ruta.slice(1).map((n, k) => { const [a, b] = [pos(ruta[k]), pos(n)]; return Math.hypot(b[0] - a[0], b[1] - a[1]); });
    let objetivo = progreso * largos.reduce((x, y) => x + y, 0), k = 0;
    while (k < largos.length - 1 && objetivo > largos[k]) { objetivo -= largos[k]; k++; }
    const [a, b] = [pos(ruta[k]), pos(ruta[k + 1])], f = largos[k] ? Math.min(1, objetivo / largos[k]) : 1;
    const x = a[0] + (b[0] - a[0]) * f, y = a[1] + (b[1] - a[1]) * f;
    s += `<g transform="translate(${x},${y})"><rect x="-16" y="-10" width="22" height="16" rx="4" fill="${P.amarillo}" stroke="${P.tinta}" stroke-width="2"/>
      <rect x="6" y="-6" width="11" height="12" rx="2" fill="${P.plata}" stroke="${P.tinta}" stroke-width="2"/>
      <circle cx="-9" cy="8" r="3.5" fill="${P.tinta}"/><circle cx="10" cy="8" r="3.5" fill="${P.tinta}"/></g>`;
  }
  s += `</svg>`;
  document.getElementById("mapa").innerHTML = s;
}
function mostrar(d) {
  const cartel = document.getElementById("cartel");
  cartel.style.background = P.amarilloSuave; cartel.style.border = `2px solid ${P.amarillo}`;
  cartel.innerHTML = `<b>🚚 Se ha pedido el camión de ${esc(d.producto)} a ${esc(d.origen)}</b><br>` +
    `${miles(d.litros)} L · pedido el ${esc(d.fechaPedido)} con el tanque al ${d.pct} % · llega el ${esc(d.fechaLlega)}` +
    ` · ${miles(C.km[d.nodo] || 0)} km por ${esc((C.rutas[d.nodo] || []).map((n) => C.nombres[n]).join(" → "))}` +
    (d.redirigido ? "<br>El origen habitual no podía cumplirlo: el pedido se redirigió." : "");
  if (animando) cancelAnimationFrame(animando);
  if (REDUCIDO) { dibujar(d.nodo, 1); return; }
  const inicio = performance.now();
  const cuadro = (ahora) => { const f = Math.min(1, (ahora - inicio) / 8000); dibujar(d.nodo, f); if (f < 1) animando = requestAnimationFrame(cuadro); };
  animando = requestAnimationFrame(cuadro);
}
function vacio() {
  const cartel = document.getElementById("cartel");
  cartel.style.background = P.panel; cartel.style.border = `1px solid ${P.borde}`;
  cartel.innerHTML = "Cuando la animación avise que un tanque está bajo, el botón <b>«Seguir trayectoria del camión»</b> muestra acá el camión sobre su ruta.";
  dibujar(C.habitual, null);
}
vacio();
try {
  const guardado = JSON.parse(window.parent.sessionStorage.getItem("camionSeguido") || "null");
  if (guardado && guardado.corrida === C.corrida) mostrar(guardado);
  window.parent.addEventListener("camion-seguido", (ev) => { if (ev.detail && ev.detail.corrida === C.corrida) mostrar(ev.detail); });
} catch (err) { /* sin acceso a la página: queda el mapa con la ruta habitual */ }
</script></body></html>
"""

