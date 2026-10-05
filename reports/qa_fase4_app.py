"""QA de la Fase 4 en Streamlit: tanques por producto, barrido de políticas y 'usar la mejor'.

Requiere el servidor corriendo en :8501.

    .venv/Scripts/python reports/qa_fase4_app.py reports/qa/fase4
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/fase4")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2700})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto("http://localhost:8501", wait_until="networkidle")
    pagina.wait_for_selector("[role='tab']", timeout=120000)

    def quieto(maximo: int = 240) -> None:
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
        time.sleep(2.5)

    quieto()
    ir("Inventario")
    print("excepciones al abrir Inventario:", excepciones())
    pagina.screenshot(path=str(SALIDA / "inventario_antes.png"), full_page=True)

    # Barrido por producto
    t0 = time.time()
    pagina.get_by_role("button", name="Buscar la mejor política de cada tanque").click()
    quieto(300)
    print("barrido terminado en", round(time.time() - t0, 1), "s | excepciones:", excepciones())
    ir("Inventario")
    ahorro = pagina.locator("text=Ahorro mensual de reponer mejor").count()
    print("aparece el ahorro mensual:", bool(ahorro))
    pagina.screenshot(path=str(SALIDA / "inventario_barrido.png"), full_page=True)

    # Usar las mejores políticas -> barra lateral editable -> volver a correr
    pagina.get_by_role("button", name="Usar las mejores políticas").click()
    quieto()
    editar = pagina.get_by_role("checkbox", name="Editar la política (s, Q) de cada tanque")
    print("checkbox 'Editar la política' tildado:", editar.is_checked() if editar.count() else "no está")
    pagina.get_by_role("button", name="Correr simulación").first.click(force=True)
    quieto(300)
    ir("Inventario")
    print("excepciones tras usar las mejores:", excepciones())
    pagina.screenshot(path=str(SALIDA / "inventario_despues.png"), full_page=True)
    ir("Conclusión")
    pagina.screenshot(path=str(SALIDA / "conclusion.png"), full_page=True)

    # El caso clásico conserva su barrido
    pagina.get_by_text("Caso clásico", exact=False).first.click()
    quieto(300)
    ir("Inventario")
    print("clásico: excepciones:", excepciones(),
          "| botón del barrido clásico:",
          pagina.get_by_role("button", name="Buscar la mejor política").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
