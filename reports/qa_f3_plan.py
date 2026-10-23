"""QA de la etapa F3 (parte 3): el plan del período en Red y rutas y "Despachar según el plan" en el menú.

    .venv/Scripts/python reports/qa_f3_plan.py http://localhost:8502 reports/qa/f3
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/f3")
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

    # --- Menú: Arroyo Seco al 40 % y despachar según el plan
    pagina.get_by_text("Abastecimiento: de dónde").first.click()
    esperar()
    campo = pagina.get_by_role("spinbutton", name="Arroyo Seco puede despachar (% de los camiones)")
    campo.fill("40")
    campo.press("Enter")
    esperar()
    pagina.get_by_text("Despachar según el plan").first.click()
    esperar(2)
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    cuerpo = pagina.locator("body").inner_text()
    print("Encabezado | despacho según el plan:", "camiones despachados según el plan" in cuerpo,
          "| topes:", "topes de despacho de los orígenes" in cuerpo)

    texto = pestania("Red y rutas")
    print("Red y rutas | sección del plan:", "El plan del período" in texto, "| rutas independientes:",
          "Rutas independientes" in texto, "| corte mínimo:", "corte mínimo" in texto)
    tarjetas = [linea for linea in texto.split("\n") if "%" in linea and linea.strip().startswith("-")]
    print("Diferencia contra hoy:", tarjetas[:1])
    pagina.get_by_text("La misma cuenta como problema de transporte").first.click()
    esperar(3)
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("Transporte de la cátedra | rincón noroeste, costo mínimo y óptimo:",
          all(x in texto for x in ("Rincón noroeste", "costo mínimo", "óptimo")),
          "| transbordo igual al flujo:", "igual que el flujo de costo mínimo" in texto)
    pagina.screenshot(path=str(SALIDA / "plan_red.png"), full_page=True)
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
