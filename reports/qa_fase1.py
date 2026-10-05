"""QA de la Fase 1: pestañas nuevas (La estación, Datos y fuentes), insignias,
tema Shell y errores de consola. Uso: .venv/Scripts/python reports/qa_fase1.py"""

import time

from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(channel="chrome", headless=True)
        pagina = navegador.new_page(viewport={"width": 1440, "height": 900})
        errores: list[str] = []
        pagina.on("console", lambda m: errores.append(f"[{m.type}] {m.text}")
                  if m.type == "error" else None)
        pagina.on("pageerror", lambda e: errores.append(f"[pageerror] {e}"))

        pagina.goto("http://localhost:8501", wait_until="domcontentloaded", timeout=60_000)
        # La primera corrida termina cuando aparece el contenido de la pestaña inicial.
        pagina.wait_for_selector("text=La estación: Shell de Av. Balloffet", timeout=240_000)
        time.sleep(4)
        pagina.screenshot(path="reports/qa/fase1_estacion.jpg", type="jpeg", quality=80)
        for texto in ("LOS SAUCES S.R.L.", "AV. BALLOFFET", "Advertencias",
                      "Contradicciones entre fuentes"):
            print("OK  " if pagina.locator(f"text={texto}").count() else "FALTA", texto)

        # Insignias en la barra lateral (clases .insignia)
        insignias = pagina.locator(".insignia").count()
        print("insignias en la página:", insignias)

        # Pestaña Animación
        pagina.click("text=🎬 Animación")
        pagina.wait_for_selector("text=Animación del día", timeout=30_000)
        time.sleep(2)
        pagina.screenshot(path="reports/qa/fase1_animacion.jpg", type="jpeg", quality=80)

        # Pestaña Datos y fuentes
        pagina.click("text=📚 Datos y fuentes")
        pagina.wait_for_selector("text=Registro de datos", timeout=15_000)
        time.sleep(1)
        pagina.screenshot(path="reports/qa/fase1_datos.jpg", type="jpeg", quality=80)
        filas_registro = pagina.locator("[data-testid='stDataFrame']").count()
        print("tablas del Registro:", filas_registro)
        print("boton CSV:", "OK" if pagina.locator("text=Descargar el Registro completo")
              .count() else "FALTA")

        print("errores de consola:", len(errores))
        for e in errores[:10]:
            print("  ", e)
        navegador.close()


if __name__ == "__main__":
    main()
