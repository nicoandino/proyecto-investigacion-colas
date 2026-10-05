"""QA visual de la animación (Fase 3) sin Streamlit: arma el HTML del reproductor con el
motor, lo abre con Playwright + el Chrome instalado y saca capturas en instantes clave.

    .venv/Scripts/python reports/qa_animacion.py reports/qa/fase3

Imprime los errores de consola (tiene que dar 0) y comprueba que los saltos funcionan.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sim.config import ParametrosSimulacion, inventario_real  # noqa: E402
from sim.runner import correr_replica  # noqa: E402
from ui import animacion  # noqa: E402

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/fase3")
SALIDA.mkdir(parents=True, exist_ok=True)


def html_de(p: ParametrosSimulacion, semilla: int = 1, dia: int = 3) -> Path:
    p = replace(p, dia_animado=dia)
    _, traza = correr_replica(p, semilla, con_traza=True)
    ruta = SALIDA / f"_{'real' if p.estacion_real else 'clasico'}_{semilla}.html"
    ruta.write_text(
        animacion.reproductor_html(traza, p, dia, animacion.fecha_texto(p, dia)),
        encoding="utf-8",
    )
    return ruta


def indice(hora: float, dt: float = 0.5) -> int:
    return int(round(hora * 60 / dt))


consola: list[str] = []
escenarios = {
    "real": ParametrosSimulacion(),
    # Pocos playeros y mucha demanda: la cola llena y se pasan de largo
    "saturado": replace(
        ParametrosSimulacion(), litros_mes=480_000.0, playeros_por_turno=(1, 1, 1),
        turnos=((0.0, 1), (6.0, 1), (14.0, 1), (22.0, 1)),
    ),
    # Cola de 3 autos por zona: se llena y los que llegan pasan de largo por la avenida
    "desborde": replace(
        ParametrosSimulacion(), litros_mes=480_000.0, playeros_por_turno=(1, 1, 1),
        turnos=((0.0, 1), (6.0, 1), (14.0, 1), (22.0, 1)), capacidad_cola=3,
    ),
    # Tanques casi vacíos: quiebre de stock y camiones en viaje
    "quiebre": replace(
        ParametrosSimulacion(), inventario=inventario_real(270_000.0, nivel_inicial_pct=0.12)
    ),
    "clasico": ParametrosSimulacion.clasico(),
}

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    for nombre, p in escenarios.items():
        ruta = html_de(p, dia=2 if nombre == "quiebre" else 3)
        pagina = navegador.new_page(viewport={"width": 1180, "height": 820})
        pagina.on("console", lambda m, n=nombre: consola.append(f"[{n}] {m.type}: {m.text}")
                  if m.type == "error" else None)
        pagina.on("pageerror", lambda e, n=nombre: consola.append(f"[{n}] pageerror: {e}"))
        pagina.goto(ruta.resolve().as_uri())
        pagina.wait_for_selector("svg")
        if nombre in ("real", "saturado", "quiebre", "desborde"):
            momentos = {"madrugada": 3.0, "pico_manana": 8.5, "mediodia": 12.5, "pico_tarde": 17.5}
        else:
            momentos = {"pico_tarde": 19.0}
        for etiqueta, hora in momentos.items():
            pagina.evaluate(f"mostrar({indice(hora)})")
            pagina.screenshot(path=str(SALIDA / f"{nombre}_{etiqueta}.png"))
        # Saltos: pico, quiebre, descarga, corte
        pagina.evaluate("saltar(iPico)")
        pagina.screenshot(path=str(SALIDA / f"{nombre}_salto_pico.png"))
        estado = pagina.evaluate(
            "({pico: iPico, quiebre: iQuiebre, corte: iCorte, n: NCUADROS})"
        )
        print(nombre, estado)
        if estado["quiebre"] >= 0:
            pagina.evaluate("saltar(iQuiebre)")
            pagina.screenshot(path=str(SALIDA / f"{nombre}_salto_quiebre.png"))
        pagina.evaluate("mostrar(0)")
        pagina.click("#saltoDescarga")
        pos = pagina.evaluate("Math.round(posicion)")
        print(nombre, "salto a la próxima descarga ->", pos, "(0 = no se movió)")
        if pos > 0:
            pagina.screenshot(path=str(SALIDA / f"{nombre}_salto_descarga.png"))
        # Desborde: un cuadro donde acaban de pasar autos de largo por la avenida
        desborde = pagina.evaluate(
            "F.t.findIndex((_, i) => i > 40 && GRUPOS.some((g) => F.g[g.id].r[i] - F.g[g.id].r[i - 40] > 0))"
        )
        print(nombre, "primer cuadro con rechazados recientes:", desborde)
        if desborde >= 0:
            pagina.evaluate(f"mostrar({desborde})")
            pagina.screenshot(path=str(SALIDA / f"{nombre}_desborde.png"))
        # Camión en viaje: el primer cuadro con un pedido en camino
        viaje = pagina.evaluate("F.t.findIndex((_, i) => camionesTotal(i) > 0)")
        print(nombre, "primer cuadro con camión en viaje:", viaje)
        if viaje >= 0:
            pagina.evaluate(f"mostrar({viaje + 400})")
            pagina.screenshot(path=str(SALIDA / f"{nombre}_camion.png"))
        # Reproducción: el reloj avanza
        pagina.evaluate("mostrar(0)")
        pagina.click("#play")
        pagina.wait_for_timeout(1500)
        avance = pagina.evaluate("Math.round(posicion)")
        print(nombre, "tras 1,5 s reproduciendo, cuadro:", avance)
        pagina.close()
    navegador.close()

# Camión en viaje: buscar un instante con pedido en camino en el escenario real
print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
