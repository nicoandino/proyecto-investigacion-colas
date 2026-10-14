"""QA de la etapa P4 (parte 3): el punto de pedido por pronóstico en Inventario, en el menú y en la búsqueda.

    .venv/Scripts/python reports/qa_p4_stock.py http://localhost:8502 reports/qa/p4
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/p4")
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
        esperar(4)
        return pagina.locator("[role='tabpanel']:visible").inner_text()

    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)

    # --- Política cargada: el bloque dice que no se usa
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    texto = pestania("Inventario")
    print("Inventario (cargada) | bloque:", "El punto de pedido con el pronóstico" in texto,
          "| no la usa:", "Esta corrida no la usa" in texto)

    # --- Con la opción del menú
    pagina.get_by_role("button", name="Cambiar período").click()
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=60000)
    esperar()
    pagina.get_by_text("🚚 Abastecimiento").first.click()
    esperar()
    pagina.get_by_text("Punto de pedido por pronóstico (stock de seguridad)").first.click()
    esperar(2)
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    print("Encabezado:", "política de reposición por pronóstico" in pagina.locator("body").inner_text())
    texto = pestania("Inventario")
    print("Inventario (pronóstico) | la usa:", "Esta corrida usa esta política" in texto)
    pagina.screenshot(path=str(SALIDA / "inventario_stock.png"), full_page=True)

    # --- Caso de informe: la búsqueda prueba 14 políticas
    pagina.get_by_role("button", name="Cambiar período").click()
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=60000)
    esperar()
    pagina.get_by_role("button", name="Abrir el caso de informe").click()
    pagina.wait_for_selector("text=Caso de informe", timeout=120000)
    esperar(4)
    print("Caso de informe | 14 políticas:", "14 políticas" in pagina.locator("body").inner_text())
    pagina.get_by_role("button", name="Buscar la mejor política de cada tanque").click()
    pagina.wait_for_selector("text=Se evaluaron las 14 políticas", timeout=300000)
    esperar(3)
    print("Búsqueda terminada | la del pronóstico en la tabla:", pagina.locator("[data-testid='stDataFrame']").count() > 0)
    pagina.screenshot(path=str(SALIDA / "busqueda.png"), full_page=True)
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
