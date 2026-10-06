"""QA de la etapa 3 dentro de Streamlit: la pestaña Animación con el tablero de todos los días.

    .venv/Scripts/python reports/qa_etapa3_app.py reports/qa/etapa3
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/etapa3")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1700})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto("http://localhost:8501", wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)

    def quieto(maximo: int = 600) -> None:
        t0 = time.time()
        time.sleep(2)
        while time.time() - t0 < maximo:
            if pagina.locator("[data-testid='stStatusWidget']").count() == 0:
                return
            time.sleep(0.5)

    def excepciones() -> int:
        return pagina.locator("[data-testid='stException']").count()

    # 30 días desde el 1 de enero (el default del menú)
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    quieto()
    pagina.locator("[role='tab']").filter(has_text="Animación").first.click()
    t0 = time.time()
    pagina.wait_for_selector("iframe:visible", timeout=120000)
    quieto(120)
    marco = pagina.frame_locator("iframe:visible").first
    marco.locator("#lienzo svg").wait_for(timeout=60000)
    print(f"animación lista en {time.time() - t0:.1f} s | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "app_animacion_inicio.png"), full_page=True)

    marco.locator("#play").click()
    time.sleep(6.5)
    estado = marco.locator("#estadoDia").inner_text()
    marco.locator("#play").click()
    print("tras 6,5 s de reproducción:", estado)
    pagina.screenshot(path=str(SALIDA / "app_animacion_dia2.png"), full_page=True)
    marco.locator("#saltoPico").click()
    time.sleep(0.5)
    pagina.screenshot(path=str(SALIDA / "app_animacion_pico.png"), full_page=True)

    # Año completo
    pagina.get_by_role("button", name="Cambiar período").click()
    pagina.wait_for_selector("text=¿Qué querés simular?")
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Año completo").first.click()
    quieto(30)
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    quieto()
    pagina.locator("[role='tab']").filter(has_text="Animación").first.click()
    t0 = time.time()
    pagina.wait_for_selector("iframe:visible", timeout=300000)
    quieto(300)
    marco = pagina.frame_locator("iframe:visible").first
    marco.locator("#lienzo svg").wait_for(timeout=120000)
    print(f"año completo: animación lista en {time.time() - t0:.1f} s | excepciones:", excepciones(),
          "|", marco.locator("#estadoDia").inner_text())
    pagina.screenshot(path=str(SALIDA / "app_animacion_anio.png"), full_page=True)
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
