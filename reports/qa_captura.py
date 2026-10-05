"""QA visual: abre la app con Chrome (via Playwright) y captura una pestaña.

Uso (con la app corriendo en localhost:8501):
    .venv/Scripts/python reports/qa_captura.py [archivo_de_salida]
"""

import sys
import time

from playwright.sync_api import sync_playwright

SALIDA = sys.argv[1] if len(sys.argv) > 1 else "reports/qa/captura.png"


def main() -> None:
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(channel="chrome", headless=True)
        pagina = navegador.new_page(viewport={"width": 1440, "height": 900})
        errores: list[str] = []
        pagina.on(
            "console",
            lambda m: errores.append(f"[{m.type}] {m.text}") if m.type == "error" else None,
        )
        pagina.on(
            "pageerror",
            lambda e: errores.append(f"[pageerror] {e}"),
        )
        pagina.goto("http://localhost:8501", wait_until="domcontentloaded", timeout=60_000)
        # Espera a que termine la corrida inicial: aparece el subheader de Animación.
        pagina.wait_for_selector("text=Animación del día", timeout=240_000)
        time.sleep(5)
        pagina.screenshot(path=SALIDA, type="jpeg", quality=80)
        print("captura:", SALIDA)
        print("errores de consola:", len(errores))
        for e in errores[:20]:
            print("  ", e)
        navegador.close()


if __name__ == "__main__":
    main()
