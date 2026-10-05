"""QA de la Fase 5 en Streamlit: la pestaña Red y rutas, los cortes y su efecto.

Requiere el servidor corriendo en :8501.

    .venv/Scripts/python reports/qa_fase5_app.py reports/qa/fase5
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/fase5")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2400})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto("http://localhost:8501", wait_until="networkidle")
    pagina.wait_for_selector("[role='tab']", timeout=120000)

    def quieto(maximo: int = 300) -> None:
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

    def correr() -> None:
        pagina.locator("button:has-text('Correr simulación')").first.click(force=True)
        quieto()

    quieto()
    ir("Red y rutas")
    print("Dock Sud por defecto | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "red_dock_defecto.png"), full_page=True)

    pagina.get_by_text("Ruta del camión y cortes").first.click()   # abre el panel de la barra lateral
    time.sleep(1)
    # Luján de Cuyo + E2 (RN 143 + RN 40 + RN 144 cerradas): el corte SÍ está en la ruta
    pagina.get_by_text("Luján de Cuyo (planta YPF)", exact=True).click()
    pagina.get_by_label("Escenario de cortes").first.click()
    pagina.get_by_role("option").filter(has_text="E2").first.click()
    correr()
    ir("Red y rutas")
    print("Luján + E2 | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "red_lujan_e2.png"), full_page=True)

    # Cortes sorteados en un mes de invierno y efecto en el quiebre
    pagina.get_by_label("Escenario de cortes").first.click()
    pagina.get_by_role("option").filter(has_text="Cortes sorteados").first.click()
    time.sleep(1)
    pagina.get_by_label("Mes a simular").first.click()
    pagina.keyboard.type("7")
    pagina.keyboard.press("Enter")
    time.sleep(1)
    correr()
    ir("Red y rutas")
    pagina.get_by_role("button", name="Simular el efecto de los cortes").click()
    quieto()
    ir("Red y rutas")
    print("efecto de los cortes | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "red_efecto_cortes.png"), full_page=True)

    # La animación muestra el origen y la ruta del camión
    ir("Animación")
    pagina.wait_for_selector("iframe:visible", timeout=60000)
    time.sleep(3)
    print("animación | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "animacion_ruta.png"), full_page=True)

    # El caso clásico dice que no tiene red
    pagina.get_by_text("Caso clásico", exact=False).first.click()
    quieto()
    ir("Red y rutas")
    print("clásico | excepciones:", excepciones(),
          "| aviso de que no hay red:", pagina.get_by_text("no tiene red").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
