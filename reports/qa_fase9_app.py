"""QA de la Fase 9 en Streamlit: la pestaña Sensibilidad (tornado).

Requiere el servidor corriendo en :8501.

    .venv/Scripts/python reports/qa_fase9_app.py reports/qa/fase9
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/fase9")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2600})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto("http://localhost:8501", wait_until="networkidle")
    pagina.wait_for_selector("[role='tab']", timeout=120000)

    def quieto(maximo: int = 600) -> None:
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
    ir("Sensibilidad")
    print("antes de correr | excepciones:", excepciones(),
          "| listado de datos:", pagina.get_by_text("Qué datos son eje y cuáles no").count())
    pagina.screenshot(path=str(SALIDA / "sensibilidad_antes.png"), full_page=True)

    t0 = time.time()
    pagina.get_by_role("button", name="Correr el tornado").click()
    quieto()
    print(f"tornado en {time.time() - t0:.1f} s | excepciones:", excepciones(),
          "| gráfico:", pagina.locator(".js-plotly-plot").count())
    pagina.screenshot(path=str(SALIDA / "tornado_margen.png"), full_page=True)

    pagina.get_by_text("Espera en la hora pico (min)", exact=True).first.click()
    quieto(120)
    print("métrica espera | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "tornado_espera.png"), full_page=True)

    pagina.get_by_text("Todos los datos supuesto / heredado / estimación").first.click()
    time.sleep(2)
    print("listado abierto | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "sensibilidad_listado.png"), full_page=True)

    pagina.get_by_text("Caso clásico", exact=False).first.click()
    quieto()
    ir("Sensibilidad")
    print("clásico | excepciones:", excepciones(),
          "| aviso:", pagina.get_by_text("La sensibilidad es del caso real").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
