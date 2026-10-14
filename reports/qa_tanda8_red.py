"""QA de la tanda 8: rutas alternativas, orígenes alternativos y el menú de abastecimiento.

    .venv/Scripts/python reports/qa_tanda8_red.py http://localhost:8502 reports/qa/tanda8
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda8")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1700})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def esperar(segundos: float = 2.0) -> None:
        time.sleep(segundos)

    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)
    pagina.get_by_text("🚚 Abastecimiento").click()
    esperar()
    pagina.locator("[data-testid='stMultiSelect']").filter(has_text="Marcar a mano").first.click()
    esperar(1)
    pagina.get_by_role("option", name="Dock Sud").click()
    esperar(1)
    pagina.keyboard.press("Escape")
    esperar()
    pagina.get_by_text("🚚 Abastecimiento").scroll_into_view_if_needed()
    pagina.screenshot(path=str(SALIDA / "menu_abastecimiento.png"))
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    cuerpo = pagina.locator("body").inner_text()
    print("encabezado:", "orígenes marcados como no disponibles" in cuerpo)
    pagina.locator("[role='tab']").filter(has_text="Red y rutas").first.click()
    esperar(3)
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("Red | otras rutas:", "Las otras rutas posibles" in texto, "| orígenes:", "De dónde puede salir el camión" in texto,
          "| redirigidos:", "se redirigieron" in texto)
    pagina.get_by_text("Las otras rutas posibles").first.scroll_into_view_if_needed()
    esperar(1)
    pagina.screenshot(path=str(SALIDA / "red_y_rutas.png"))
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
