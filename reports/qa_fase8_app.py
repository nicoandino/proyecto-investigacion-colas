"""QA de la Fase 8 en Streamlit: economía real y conclusión en $/mes.

Requiere el servidor corriendo en :8501.

    .venv/Scripts/python reports/qa_fase8_app.py reports/qa/fase8
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/fase8")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 3000})
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

    ir("Economía")
    print("economía | excepciones:", excepciones(),
          "| estado de resultados:", pagina.get_by_text("Estado de resultados").count(),
          "| margen de equilibrio:", pagina.get_by_text("Margen por litro de equilibrio").count())
    pagina.screenshot(path=str(SALIDA / "economia.png"), full_page=True)

    t0 = time.time()
    pagina.get_by_role("button", name="Calcular la economía por estación").click()
    quieto()
    print(f"economía por estación en {time.time() - t0:.1f} s | excepciones:", excepciones(),
          "| año estimado:", pagina.get_by_text("AÑO ESTIMADO").count())

    ir("Escenarios")
    t0 = time.time()
    pagina.get_by_role("button", name="Correr los escenarios").click()
    quieto(900)
    print(f"escenarios en {time.time() - t0:.1f} s | excepciones:", excepciones())

    ir("Economía")
    print("economía con escenarios | excepciones:", excepciones(),
          "| S6:", pagina.get_by_text("¿un playero más en el pico o más stock?").count())
    pagina.screenshot(path=str(SALIDA / "economia_escenarios.png"), full_page=True)

    ir("Conclusión")
    print("conclusión | excepciones:", excepciones(),
          "| respuestas del CASO:", pagina.get_by_text("Respuestas a las preguntas del CASO").count())
    pagina.screenshot(path=str(SALIDA / "conclusion.png"), full_page=True)

    pagina.get_by_text("Caso clásico", exact=False).first.click()
    quieto()
    ir("Economía")
    print("clásico | excepciones:", excepciones(),
          "| análisis clásico:", pagina.get_by_text("Análisis económico").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
