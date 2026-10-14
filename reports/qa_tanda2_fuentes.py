"""QA de la tanda 2: sin advertencias abiertas; el valor elegido de cada contradicción y su criterio.

    .venv/Scripts/python reports/qa_tanda2_fuentes.py http://localhost:8502 reports/qa/tanda2
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda2")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1700})
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

    def pestania(nombre: str) -> str:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        time.sleep(2)
        return pagina.locator("[role='tabpanel']:visible").inner_text()

    texto = pestania("La estación")
    print("La estación | 'Advertencias':", "Advertencias" in texto, "| 'Contradicciones':", "Contradicciones" in texto,
          "| frase general:", "la estación no aporta mediciones propias" in texto)
    pagina.screenshot(path=str(SALIDA / "la_estacion.png"))
    texto = pestania("Datos y fuentes")
    print("Datos y fuentes | 'Alternativas':", "Alternativas" in texto, "| qué se eligió:", "qué se eligió y por qué" in texto)
    pagina.get_by_text("qué se eligió y por qué").first.scroll_into_view_if_needed()
    time.sleep(1)
    pagina.screenshot(path=str(SALIDA / "datos_y_fuentes.png"))
    texto = pestania("GNC")
    print("GNC | 'Alerta de coherencia':", "Alerta de coherencia" in texto, "| observación:", "Lo que muestra el modelo" in texto)
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
