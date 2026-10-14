"""QA de la etapa P3 (parte 3): pestaña 📈 Pronóstico y la opción "índices de la serie real" del menú.

    .venv/Scripts/python reports/qa_p3_pronostico.py http://localhost:8502 reports/qa/p3
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/p3")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2600})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def esperar(segundos: float = 2.0) -> None:
        time.sleep(segundos)

    def pestania(nombre: str) -> str:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        esperar(4)
        return pagina.locator("[role='tabpanel']:visible").inner_text()

    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)

    # --- Con el calendario por defecto
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    texto = pestania("Pronóstico")
    graficos = pagina.locator("[role='tabpanel']:visible .js-plotly-plot").count()
    tablas = pagina.locator("[role='tabpanel']:visible [data-testid='stDataFrame']").count()
    print("Pronóstico | serie oficial:", "Secretaría de Energía" in texto, "| método elegido:",
          [linea for linea in texto.split("\n") if "Promedio móvil" in linea][:1], "| gráficos:", graficos,
          "| tablas:", tablas, "| verano casi neutro:", "pesa" in texto and "verano" in texto)
    pagina.screenshot(path=str(SALIDA / "pronostico.png"), full_page=True)
    print("excepciones:", pagina.locator("[data-testid='stException']").count())

    # --- Con los índices de la serie real
    pagina.get_by_role("button", name="Cambiar período").click()
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=60000)
    esperar()
    pagina.get_by_text("📅 Calendario de demanda").first.click()
    esperar()
    pagina.get_by_text("Índices de la serie real de Shell Mendoza").first.click()
    esperar(2)
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    cuerpo = pagina.locator("body").inner_text()
    # Desde el 14/10/2026 los índices reales son el valor por defecto: el encabezado no los lista como cambio.
    print("Con índices reales (por defecto) | encabezado sin cambios:", "Ajustes del menú distintos" not in cuerpo)
    texto = pestania("Demanda")
    print("Demanda | cuenta con el índice:", "(serie real)" in texto, "| aclaración:", "índices mensuales de la serie real" in texto)
    pagina.screenshot(path=str(SALIDA / "demanda_indices.png"), full_page=True)
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
