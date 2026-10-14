"""QA de la Fase 6 en Streamlit: la pestaña GNC, los episodios sombreados y la animación con corte.

Requiere el servidor corriendo en :8501.

    .venv/Scripts/python reports/qa_fase6_app.py reports/qa/fase6
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/fase6")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2300})
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
    ir("GNC")
    print("enero por defecto | excepciones:", excepciones(),
          "| aviso de que ningún episodio cae en el horizonte:",
          pagina.get_by_text("Ningún episodio cae dentro de este horizonte").count())
    pagina.screenshot(path=str(SALIDA / "gnc_enero.png"), full_page=True)

    # Julio, con los episodios forzados dentro del horizonte
    pagina.get_by_text("GNC y cortes de invierno").first.click()
    time.sleep(1)
    pagina.get_by_text("Forzar que los episodios caigan dentro del horizonte").first.click()
    pagina.get_by_label("Mes a simular").first.click()
    pagina.keyboard.type("7")
    pagina.keyboard.press("Enter")
    time.sleep(1)
    correr()
    ir("GNC")
    print("julio con episodios | excepciones:", excepciones())
    pagina.get_by_role("button", name="Simular el efecto del corte de GNC").click()
    quieto()
    ir("GNC")
    print("efecto del corte | excepciones:", excepciones())
    pagina.screenshot(path=str(SALIDA / "gnc_julio.png"), full_page=True)

    # La animación en un día de corte
    ir("Animación")
    pagina.wait_for_selector("iframe:visible", timeout=60000)
    slider = pagina.get_by_role("slider", name="Día a animar")
    slider.scroll_into_view_if_needed()
    slider.focus()
    for _ in range(6):
        pagina.keyboard.press("ArrowRight")
    quieto(120)
    pagina.wait_for_selector("iframe:visible", timeout=60000)
    time.sleep(3)
    marco = pagina.frame_locator("iframe:visible").first
    habilitado = marco.locator("#saltoCorte").is_enabled()
    print("animación | botón 'el corte de GNC' habilitado:", habilitado,
          "| excepciones:", excepciones())
    if habilitado:
        marco.locator("#saltoCorte").click()
        time.sleep(1)
    pagina.screenshot(path=str(SALIDA / "animacion_corte.png"), full_page=True)

    # Contrato firme: sin cortes
    pagina.get_by_text("Firme (sin cortes)").first.click()
    correr()
    ir("GNC")
    print("contrato firme | excepciones:", excepciones(),
          "| aviso de 'no hay cortes':", pagina.get_by_text("No hay cortes").count())

    # El caso clásico dice que no vende GNC
    pagina.get_by_text("Caso clásico", exact=False).first.click()
    quieto()
    ir("GNC")
    print("clásico | excepciones:", excepciones(),
          "| aviso:", pagina.get_by_text("no vende GNC").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
