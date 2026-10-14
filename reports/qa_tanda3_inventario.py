"""QA de la tanda 3: quiebres (cuántos, cuánto duraron, qué costaron) y litros no vendidos por causa.

    .venv/Scripts/python reports/qa_tanda3_inventario.py http://localhost:8502 reports/qa/tanda3
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda3")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1500})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Por estaciones").first.click()
    time.sleep(2)
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Invierno").first.click()
    time.sleep(2)
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    time.sleep(4)

    def pestania(nombre: str) -> None:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        time.sleep(2)

    pestania("Indicadores")
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Inventario").first.click()
    time.sleep(3)
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("Indicadores · Inventario | qué es un quiebre:", "¿Qué es un quiebre de stock?" in texto,
          "| por qué no se vendió:", "Lo que no se vendió, y por qué" in texto)
    pagina.get_by_text("¿Qué es un quiebre de stock?").first.scroll_into_view_if_needed()
    pagina.screenshot(path=str(SALIDA / "indicadores_inventario.png"))

    pestania("Inventario")
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("Inventario | 1-2-3:", all(x in texto for x in ("1. Cómo se movió", "2. Quiebres de stock", "3. Cuándo se pide")),
          "| ± IC:", "IC 95" in texto)
    pagina.get_by_text("2. Quiebres de stock y lo que no se vendió").first.scroll_into_view_if_needed()
    time.sleep(1)
    pagina.screenshot(path=str(SALIDA / "inventario_quiebres.png"))
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
