"""QA del tablero animado (rediseño v3, etapa 3), sin Streamlit: arma el HTML con una simulación de datos
reales, lo abre con Playwright y lo fotografía en distintos momentos.

    .venv/Scripts/python reports/qa_animacion.py reports/qa/etapa3
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dataclasses import replace  # noqa: E402

from sim.config import ParametrosEconomicos, ParametrosSimulacion  # noqa: E402
from sim.periodo import anio_completo, con_periodo, por_dias, por_temporada  # noqa: E402
from sim.runner import correr_replica  # noqa: E402
from ui import animacion  # noqa: E402

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/etapa3")
SALIDA.mkdir(parents=True, exist_ok=True)
eco = ParametrosEconomicos()
d = dict(eco.precios)
PRECIOS = {"super": d["super"], "vpower": d["premium"], "diesel_g2": d["diesel_g2"],
           "diesel_g3": d["diesel_g3"], "gnc": d["gnc"]}


def html_de(periodo, extra=None):
    p = con_periodo(ParametrosSimulacion().datos_reales(), periodo)
    if extra:
        p = replace(p, **extra)
    p = replace(p, animar_todo=True, dt_traza=animacion.dt_para(p.dias), dia_animado=1)
    t0 = time.time()
    _, traza = correr_replica(p, 1, con_traza=True)
    html = animacion.reproductor_html(traza, p, PRECIOS, periodo.titulo)
    print(f"{periodo.titulo}: {p.dias} días, dt {p.dt_traza:g} min, {len(traza.cuadros):,} cuadros, "
          f"{len(html) / 1e6:.2f} MB, {time.time() - t0:.1f} s")
    return html


consola: list[str] = []
with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": animacion.ALTO_COMPONENTE})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def abrir(html: str, nombre: str) -> None:
        ruta = SALIDA / f"{nombre}.html"
        ruta.write_text(html, encoding="utf-8")
        pagina.goto(ruta.resolve().as_uri())
        pagina.wait_for_selector("#lienzo svg", timeout=60000)
        time.sleep(1)

    # 12 días de enero
    abrir(html_de(por_dias(12, 1, 1)), "enero12")
    pagina.screenshot(path=str(SALIDA / "01_inicio.png"))
    pagina.locator("#saltoPico").click()
    time.sleep(0.5)
    pagina.screenshot(path=str(SALIDA / "02_hora_pico.png"))
    pagina.locator("#saltoQuiebre").click()
    time.sleep(0.5)
    pagina.screenshot(path=str(SALIDA / "03_quiebre.png"))
    # reproducir 7 segundos: al ritmo de 5 s por día tiene que cambiar de día
    pagina.locator("#barra").evaluate("e => { e.value = 0; e.dispatchEvent(new Event('input')); }")
    pagina.locator("#play").click()
    time.sleep(7)
    dia_txt = pagina.locator("#estadoDia").inner_text()
    pagina.locator("#play").click()
    pagina.screenshot(path=str(SALIDA / "04_reproduciendo_dia2.png"))
    print("tras 7 s de reproducción:", dia_txt)
    pagina.locator("#tipoGrafico").select_option("ventas")
    time.sleep(0.3)
    pagina.screenshot(path=str(SALIDA / "05_grafico_ventas.png"))

    # Invierno: corte de GNC
    abrir(html_de(por_temporada("Invierno")), "invierno")
    pagina.locator("#saltoCorte").click()
    time.sleep(0.5)
    pagina.screenshot(path=str(SALIDA / "06_corte_gnc.png"))
    print("botón del corte habilitado en invierno:", not pagina.locator("#saltoCorte").is_disabled())

    # Verano: no hay corte
    abrir(html_de(por_temporada("Verano")), "verano")
    print("botón del corte habilitado en verano:", not pagina.locator("#saltoCorte").is_disabled())

    # Año completo: peso del HTML
    abrir(html_de(anio_completo()), "anio")
    pagina.locator("#diaMas").click()
    print("año completo, tras 'Día ▶':", pagina.locator("#estadoDia").inner_text())
    pagina.screenshot(path=str(SALIDA / "07_anio_dia2.png"))
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
