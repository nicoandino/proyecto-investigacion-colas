"""QA de la pestaña Animación dentro de Streamlit (Fase 3).

Requiere el servidor corriendo en :8501.

    .venv/Scripts/python reports/qa_fase3_app.py reports/qa/fase3

Saca la pestaña Animación en modo real y en modo clásico, cambia el día a animar, mueve
el reproductor con la barra y cuenta excepciones y errores de consola (tienen que ser 0).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/fase3")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1000})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto("http://localhost:8501", wait_until="networkidle")
    pagina.wait_for_selector("[role='tab']", timeout=120000)

    def quieto(maximo: int = 180) -> None:
        t0 = time.time()
        time.sleep(2)
        while time.time() - t0 < maximo:
            if pagina.locator("[data-testid='stStatusWidget']").count() == 0:
                return
            time.sleep(0.5)

    def ir_a_animacion() -> None:
        pagina.locator("[role='tab']").filter(has_text="Animación").first.click()
        pagina.wait_for_selector("iframe:visible", timeout=60000)
        time.sleep(3)

    def marco():
        return pagina.frame_locator("iframe:visible").first

    for modelo in ("real", "clasico"):
        if modelo == "clasico":
            pagina.get_by_text("Caso clásico", exact=False).first.click()
            quieto()
        else:
            quieto()
        ir_a_animacion()
        print(modelo, "excepciones:", pagina.locator("[data-testid='stException']").count())
        pagina.screenshot(path=str(SALIDA / f"app_{modelo}_animacion.png"), full_page=True)
        # El reproductor responde: salto a la hora pico dentro del iframe
        marco().locator("#saltoPico").click()
        time.sleep(1)
        reloj = marco().locator("#reloj").inner_text()
        print(modelo, "tras 'saltar a la hora pico':", reloj)
        pagina.screenshot(path=str(SALIDA / f"app_{modelo}_animacion_pico.png"), full_page=True)
        # Otro día desde el selector de la pestaña (sólo si el horizonte tiene más de un día)
        if pagina.get_by_text("Día a animar").count():
            slider = pagina.get_by_role("slider", name="Día a animar")
            slider.scroll_into_view_if_needed()
            slider.focus()
            for _ in range(4):
                pagina.keyboard.press("ArrowRight")
            quieto(60)
            print(modelo, "fecha mostrada:", marco().locator("#reloj").inner_text())
            print(modelo, "excepciones tras cambiar el día:",
                  pagina.locator("[data-testid='stException']").count())
            pagina.screenshot(path=str(SALIDA / f"app_{modelo}_otro_dia.png"), full_page=True)
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
