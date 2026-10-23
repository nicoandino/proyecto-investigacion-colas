"""QA de la tanda 0: la búsqueda de la mejor política no se cuelga (año completo).

Elige el año completo, abre el Caso de informe (ahí vive la búsqueda desde la tanda 6), aprieta "Buscar la mejor
política", hace clics en otras pestañas mientras corre (no tiene que reiniciarse) y espera las 13 evaluaciones.

    .venv/Scripts/python reports/qa_tanda0_busqueda.py http://localhost:8503 reports/qa/tanda0
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda0")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2200})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)

    def quieto(maximo: int = 600) -> None:
        t0 = time.time()
        time.sleep(2)
        while time.time() - t0 < maximo:
            if pagina.locator("[data-testid='stStatusWidget']").count() == 0:
                return
            time.sleep(0.5)

    def pestania(nombre: str) -> None:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        time.sleep(1.5)

    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Año completo").first.click()
    quieto(30)
    # Desde la tanda 6 la búsqueda vive en el Caso de informe (fuera del flujo normal).
    pagina.get_by_role("button", name="Abrir el caso de informe").click()
    pagina.wait_for_selector("text=Caso de informe", timeout=120000)
    quieto()
    t0 = time.time()
    pagina.get_by_role("button", name="Buscar la mejor política de cada tanque").click()
    pagina.wait_for_selector("text=Evaluando políticas", timeout=120000)
    progresos = []
    clics = 0
    while time.time() - t0 < 400:
        cuerpo = pagina.locator("body").inner_text()
        m = re.search(r"Evaluando políticas: (\d+) de (\d+)", cuerpo)
        if m:
            progresos.append(int(m.group(1)))
        if "evaluaciones (costo de los 4 tanques" in cuerpo:
            break
        # Mientras corre: otra pestaña y un radio de Indicadores (antes esto reiniciaba la búsqueda)
        if clics < 2 and m and int(m.group(1)) >= 3 + 4 * clics:
            pestania("Sensibilidad")
            time.sleep(1)
            pestania("Mejor política")
            clics += 1
        time.sleep(1)
    duracion = time.time() - t0
    pagina.get_by_text("evaluaciones (costo de los 4 tanques").first.scroll_into_view_if_needed()
    time.sleep(1)
    pagina.screenshot(path=str(SALIDA / "busqueda_terminada.png"))
    cuerpo = pagina.locator("body").inner_text()
    print(f"duración {duracion:.0f} s · avance visto: {sorted(set(progresos))} · clics en otras pestañas: {clics}")
    print("¿13 evaluaciones juntas?", "Las 13 evaluaciones" in cuerpo, "| ¿ganadora marcada?", "ganadora" in cuerpo)
    print("¿avance monótono (no se reinició)?", progresos == sorted(progresos))
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
