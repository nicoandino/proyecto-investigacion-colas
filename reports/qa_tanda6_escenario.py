"""QA de la tanda 6: escenario único desde el menú, conclusión armada con los resultados y caso de informe.

    .venv/Scripts/python reports/qa_tanda6_escenario.py http://localhost:8502 reports/qa/tanda6
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda6")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1500})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def esperar(segundos: float = 2.0) -> None:
        time.sleep(segundos)

    def elegir(etiqueta: str, opcion: str) -> None:
        pagina.locator("[data-testid='stSelectbox']").filter(has_text=etiqueta).first.click()
        esperar(1)
        pagina.get_by_role("option", name=opcion).click()
        esperar(1)

    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)

    # --- Escenario único: 2 playeros en el pico de la mañana, verano, clientela máxima
    elegir("Clientela", "Máxima (alta y el doble en el pico)")
    pagina.get_by_role("button", name="Simular el escenario único").click()
    pagina.wait_for_selector("text=Conclusión de este escenario", timeout=300000)
    esperar(3)
    texto = pagina.locator("body").inner_text()
    print("Escenario único | título:", "2 playeros · pico de la mañana" in texto,
          "| sin pestañas:", pagina.locator("[role='tab']").count() == 0,
          "| veredicto:", any(x in texto for x in ("no alcanza", "al límite", "alcanza con margen")))
    pagina.screenshot(path=str(SALIDA / "escenario_unico.png"), full_page=True)
    pagina.get_by_role("button", name="Volver al menú").click()
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=60000)
    esperar()
    pagina.get_by_role("spinbutton", name="Playeros en la franja").fill("4")
    pagina.get_by_role("spinbutton", name="Playeros en la franja").press("Enter")
    esperar()
    pagina.get_by_role("button", name="Simular el escenario único").click()
    pagina.wait_for_selector("text=4 playeros · pico de la mañana", timeout=300000)
    esperar(3)
    texto4 = pagina.locator("body").inner_text()
    print("Con 4 playeros cambia la conclusión:", texto4.split("Conclusión de este escenario")[1][:160].replace("\n", " "))
    pagina.get_by_role("button", name="Volver al menú").click()
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=60000)
    esperar()

    # --- Flujo normal: sin pestaña Escenarios; conclusión adaptada
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    tabs = [t.strip() for t in pagina.locator("[role='tab']").all_inner_texts()]
    print("pestañas:", tabs)
    pagina.locator("[role='tab']").filter(has_text="Conclusión").first.click()
    esperar(2)
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("Conclusión | sin 'pestaña Escenarios':", "pestaña **Escenarios**" not in texto and "pestaña Escenarios" not in texto,
          "| sin 'Buscar la mejor política':", "Buscar la mejor política" not in texto,
          "| qué probar:", "Qué conviene probar después" in texto)
    pagina.screenshot(path=str(SALIDA / "conclusion.png"))
    pagina.get_by_role("button", name="Cambiar período").click()
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=60000)
    esperar()

    # --- Caso de informe
    pagina.get_by_role("button", name="Abrir el caso de informe").click()
    pagina.wait_for_selector("text=Caso de informe", timeout=60000)
    esperar(3)
    tabs = [t.strip() for t in pagina.locator("[role='tab']").all_inner_texts()]
    print("Caso de informe | pestañas:", tabs)
    pagina.screenshot(path=str(SALIDA / "caso_de_informe.png"))
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
