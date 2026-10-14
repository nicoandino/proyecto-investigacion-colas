"""QA de la tanda 4: el menú inicial con los desplegables de Economía y GNC.

    .venv/Scripts/python reports/qa_tanda4_menu.py http://localhost:8502 reports/qa/tanda4
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda4")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1900})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)

    def esperar(segundos: float = 2.0) -> None:
        time.sleep(segundos)

    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Por estaciones").first.click()
    esperar()
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Invierno").first.click()
    esperar()
    pagina.get_by_text("💰 Economía: márgenes").click()
    pagina.get_by_text("🔥 GNC: cortes de invierno").click()
    esperar()
    antes = pagina.locator("body").inner_text()
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Pueden ocurrir más cortes").first.click()
    esperar()
    entrada = pagina.get_by_role("spinbutton", name="Margen Súper ($/L)")
    entrada.fill("120")
    entrada.press("Enter")
    esperar()
    despues = pagina.locator("body").inner_text()
    print("cortes habituales en el aviso:", antes.count(" días)"), "· con 'todo el invierno':", despues.count(" días)"))
    pagina.screenshot(path=str(SALIDA / "menu.png"), full_page=True)

    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    cuerpo = pagina.locator("body").inner_text()
    print("encabezado con ajustes:", "Ajustes del menú distintos del Registro" in cuerpo,
          "| márgenes:", "márgenes por litro" in cuerpo, "| cortes:", "más cortes de GNC" in cuerpo)
    pagina.locator("[role='tab']").filter(has_text="Economía").first.click()
    esperar()
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("Economía muestra los márgenes por producto:", "Súper $120" in texto)
    pagina.screenshot(path=str(SALIDA / "economia_con_ajustes.png"))
    # Volver al menú: los ajustes se conservan
    pagina.get_by_role("button", name="Cambiar período").click()
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=60000)
    esperar()
    pagina.get_by_text("💰 Economía: márgenes").click()
    esperar()
    print("al volver, el margen de Súper sigue en 120:", pagina.get_by_role("spinbutton", name="Margen Súper ($/L)").input_value() == "120")
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
