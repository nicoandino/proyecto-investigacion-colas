"""QA de los pendientes de §24 (G1–G3): tabla de camiones, red de nafta, diésel y GNC, cortes sólo si se editó.

    .venv/Scripts/python reports/qa_g_pendientes.py http://localhost:8502 reports/qa/g
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/g")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2400})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def esperar(segundos: float = 2.0) -> None:
        time.sleep(segundos)

    def pestania(nombre: str) -> str:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        esperar(5)
        return pagina.locator("[role='tabpanel']:visible").inner_text()

    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)
    print("Menú sin barra lateral:", pagina.locator("[data-testid='stSidebar']").count() == 0
          or not pagina.locator("[data-testid='stSidebar']").is_visible())
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)

    texto = pestania("Inventario")
    print("G1 Inventario | tabla de camiones:", "Cada camión, de punta a punta" in texto,
          "| totales:", [linea for linea in texto.split("\n") if "camiones de los tanques elegidos" in linea][:1])
    pagina.screenshot(path=str(SALIDA / "inventario_camiones.png"), full_page=True)

    texto = pestania("Red y rutas")
    print("G2 Red y rutas | sección nafta, diésel y GNC:", "La red de cada producto: nafta, diésel y GNC" in texto,
          "| diagrama del gas:", pagina.locator("[role='tabpanel']:visible [data-testid='stGraphVizChart'] svg").count() > 0,
          "| red del GNC:", "gasoducto" in texto.lower(),
          "| tabla de cortes oculta sin edición:", "Qué le hace cada corte a cada origen" not in texto,
          "| sin 'barra lateral':", "barra lateral" not in texto)
    pagina.screenshot(path=str(SALIDA / "red_y_rutas.png"), full_page=True)
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
