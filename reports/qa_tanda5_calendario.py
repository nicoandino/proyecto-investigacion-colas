"""QA de la tanda 5: calendario de temporadas en el menú, cuenta y rango por temporada, filtros por fecha.

    .venv/Scripts/python reports/qa_tanda5_calendario.py http://localhost:8502 reports/qa/tanda5
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda5")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1700})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def esperar(segundos: float = 2.0) -> None:
        time.sleep(segundos)

    def simular(tipo: str | None, dias: str | None = None) -> None:
        pagina.goto(URL, wait_until="networkidle")
        pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)
        if tipo:
            pagina.locator("[data-testid='stRadio'] label").filter(has_text=tipo).first.click()
            esperar()
        if dias:
            campo = pagina.get_by_role("spinbutton", name="Cantidad de días")
            campo.fill(dias)
            campo.press("Enter")
            esperar()
        # Desde el 14/10/2026 la app usa por defecto los índices reales: el calendario se elige en el menú.
        pagina.get_by_text("Calendario de demanda").first.click()
        esperar()
        pagina.get_by_text("Calendario de temporadas (supuesto del grupo, DEM-14)").first.click()
        esperar(2)
        pagina.get_by_role("button", name="Simular con datos reales").click()
        pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
        esperar(4)
        pagina.locator("[role='tab']").filter(has_text="Demanda").first.click()
        esperar(3)

    # Menú: el desplegable del calendario
    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)
    pagina.get_by_text("Calendario de demanda").click()
    esperar()
    pagina.get_by_text("Calendario de demanda").scroll_into_view_if_needed()
    pagina.screenshot(path=str(SALIDA / "menu_calendario.png"))

    # Año completo: rango por temporada y filtro de período
    simular("Año completo")
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("Año | rango por temporada:", "Rango de clientes por día en cada temporada" in texto,
          "| vacaciones:", "Vacaciones de invierno de Mendoza" in texto,
          "| filtro 'Ver':", pagina.locator("[role='tabpanel']:visible").get_by_text("Ver", exact=True).count() > 0)
    pagina.screenshot(path=str(SALIDA / "demanda_anio.png"))
    # Filtrar las vacaciones de invierno
    pagina.locator("[role='tabpanel']:visible [data-testid='stSelectbox']").first.click()
    esperar(1)
    pagina.get_by_role("option", name="Vacaciones de invierno").click()
    esperar(3)
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("Vacaciones | 12 días elegidos:", "los 12 días elegidos" in texto)
    pagina.get_by_text("2. Cuándo llegan: el perfil del día").first.scroll_into_view_if_needed()
    esperar(1)
    pagina.screenshot(path=str(SALIDA / "perfil_vacaciones.png"))
    print("excepciones (año):", pagina.locator("[data-testid='stException']").count())

    # 7 días: sin filtros
    simular(None, "7")
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("7 días | sin filtros:", "se muestran todos" in texto,
          "| selector de fechas:", pagina.locator("[role='tabpanel']:visible [data-testid='stDateInput']").count())
    print("excepciones (7 días):", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
