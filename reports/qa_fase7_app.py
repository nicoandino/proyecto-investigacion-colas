"""QA de la Fase 7 en Streamlit: las pestañas Estaciones del año y Escenarios (S0–S12).

Requiere el servidor corriendo en :8501.

    .venv/Scripts/python reports/qa_fase7_app.py reports/qa/fase7
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/fase7")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2700})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto("http://localhost:8501", wait_until="networkidle")
    pagina.wait_for_selector("[role='tab']", timeout=120000)

    def quieto(maximo: int = 400) -> None:
        t0 = time.time()
        time.sleep(2)
        while time.time() - t0 < maximo:
            if pagina.locator("[data-testid='stStatusWidget']").count() == 0:
                return
            time.sleep(0.5)

    def excepciones() -> int:
        return pagina.locator("[data-testid='stException']").count()

    def ir(nombre: str) -> None:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        time.sleep(3)

    quieto()

    # ---- Estaciones del año
    ir("Estaciones")
    print("estaciones sin correr | excepciones:", excepciones(),
          "| gráfico de litros por mes:", pagina.locator(".js-plotly-plot").count() >= 1)
    pagina.screenshot(path=str(SALIDA / "estaciones_antes.png"), full_page=True)
    t0 = time.time()
    pagina.get_by_role("button", name="Correr las 4 estaciones").click()
    quieto()
    print(f"estaciones corridas en {time.time() - t0:.1f} s | excepciones:", excepciones(),
          "| tabla:", pagina.get_by_text("Resultados por estación").count())
    pagina.screenshot(path=str(SALIDA / "estaciones.png"), full_page=True)

    # ---- Comparar escenarios
    ir("Escenarios")
    print("escenarios sin correr | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "comparar_antes.png"), full_page=True)
    t0 = time.time()
    pagina.get_by_role("button", name="Correr los escenarios").click()
    quieto(600)
    print(f"catálogo corrido en {time.time() - t0:.1f} s | excepciones:", excepciones(),
          "| tabla:", pagina.get_by_text("Resultados en julio").count())
    pagina.screenshot(path=str(SALIDA / "comparar.png"), full_page=True)

    # Otro indicador en el gráfico de diferencias
    pagina.get_by_label("Indicador a comparar contra S0").first.click()
    pagina.keyboard.type("Tasa de abandono")
    pagina.keyboard.press("Enter")
    quieto(60)
    print("otro indicador | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "comparar_abandono.png"), full_page=True)

    # El caso clásico conserva su comparación de capacidad
    pagina.get_by_text("Caso clásico", exact=False).first.click()
    quieto()
    ir("Escenarios")
    print("clásico | excepciones:", excepciones(),
          "| comparación de capacidad:", pagina.get_by_text("Comparación de escenarios de capacidad").count())
    ir("Estaciones")
    print("clásico, estaciones | aviso:", pagina.get_by_text("son del caso real").count(),
          "| excepciones:", excepciones())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
