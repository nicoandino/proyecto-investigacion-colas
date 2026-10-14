"""QA textual: imprime lo que la app muestra para verificar sin ver la captura."""

import time

from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(channel="chrome", headless=True)
        pagina = navegador.new_page(viewport={"width": 1440, "height": 900})
        errores: list[str] = []
        pagina.on(
            "console",
            lambda m: errores.append(f"[{m.type}] {m.text}") if m.type == "error" else None,
        )
        pagina.on("pageerror", lambda e: errores.append(f"[pageerror] {e}"))
        pagina.goto("http://localhost:8501", wait_until="domcontentloaded", timeout=60_000)
        pagina.wait_for_selector("text=Animación del día", timeout=240_000)
        time.sleep(4)

        print("TITULO:", pagina.title())
        for selector in (
            "text=Demanda esperada (litros por mes)",
            "text=270000",
            "text=clientes/día",
            "text=Un mes (calendario real)",
            "text=Estacionalidad mensual",
            "text=Factor de fin de semana",
            "text=Animación del día",
            "text=Escenario Base",
            "text=31 días",
        ):
            try:
                pagina.wait_for_selector(selector, timeout=5_000)
                print("OK  ", selector)
            except Exception:
                print("FALTA", selector)

        # Pestañas presentes
        for texto in ("Animación", "Indicadores", "Demanda", "Inventario",
                      "Escenarios", "Economía", "Conclusión", "Modelo y método"):
            print("PESTAÑA" if pagina.locator(f"text={texto}").count() else "FALTA ", texto)

        print("errores de consola:", len(errores))
        for e in errores[:10]:
            print("  ", e)
        navegador.close()


if __name__ == "__main__":
    main()
