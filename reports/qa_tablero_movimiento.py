"""QA del tablero (14/10/2026): surtidores de doble cara, autos en movimiento, tránsito, colas ilustrativas, el panel
de Alertas y que nada se corte a la derecha en pantallas más angostas; también las fotos de arriba.

Uso (con el servidor de QA en localhost:8502):
    .venv/Scripts/python reports/qa_tablero_movimiento.py [carpeta_de_salida]
"""

import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

URL = "http://localhost:8502"
SALIDA = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/tablero")


def marco_tablero(pagina):
    for f in pagina.frames:
        try:
            if f.locator("#lienzo").count():
                return f
        except Exception:
            pass
    return None


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    errores: list[str] = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch(channel="chrome", headless=True)
        for ancho in (1180, 1440):
            pagina = nav.new_page(viewport={"width": ancho, "height": 900})
            pagina.on("pageerror", lambda e: errores.append(f"[pageerror] {e}"))
            pagina.on("console", lambda m: errores.append(f"[{m.type}] {m.text}") if m.type == "error" else None)
            pagina.goto(URL, wait_until="domcontentloaded")
            pagina.get_by_role("button", name="Simular con datos reales").wait_for(timeout=60_000)
            time.sleep(2)
            if ancho == 1440:
                pagina.screenshot(path=str(SALIDA / "menu_con_foto.png"))
            pagina.get_by_role("button", name="Simular con datos reales").click()
            pagina.locator('[role="tab"]').filter(has_text="Animación").first.wait_for(timeout=240_000)
            time.sleep(2)
            if ancho == 1440:
                pagina.screenshot(path=str(SALIDA / "resultados_con_marquesina.png"))
            pagina.locator('[role="tab"]').filter(has_text="Animación").first.click()
            time.sleep(6)
            marco = marco_tablero(pagina)
            medidas = marco.evaluate("""() => { const r = (id) => Math.round(document.getElementById(id).getBoundingClientRect().right);
                return {ventana: innerWidth, app: document.getElementById('app').scrollWidth, play: r('play'), derecha: r('derecha')}; }""")
            print(f"{ancho} px | ¿algo se sale por la derecha?", medidas["app"] > medidas["ventana"] or medidas["play"] > medidas["ventana"], medidas)
            marco.locator("#saltoPico").click()
            time.sleep(1)
            textos = marco.locator("#lienzo").inner_text()
            print(f"{ancho} px | surtidores S1…S6:", all(f"S{k}" in textos for k in range(1, 7)), "| sin S7:", "S7" not in textos,
                  "| caras 1…12:", all(str(k) in textos for k in range(1, 13)))
            print(f"{ancho} px | rótulo de colas ilustrativas:", "COLAS ILUSTRATIVAS" in textos)
            pagina.locator("iframe").nth(1).screenshot(path=str(SALIDA / f"tablero_pico_{ancho}.png"))
            # reproducir un rato: los autos se mueven (el lienzo cambia sin que cambie el cuadro)
            marco.locator("#play").click()
            time.sleep(1.5)
            a = marco.locator("#lienzo").inner_html()
            time.sleep(0.12)
            b = marco.locator("#lienzo").inner_html()
            print(f"{ancho} px | el lienzo se redibuja mientras corre:", a != b)
            pagina.locator("iframe").nth(1).screenshot(path=str(SALIDA / f"tablero_movimiento_{ancho}.png"))
            if marco.locator("#avisoOk").is_visible():
                marco.locator("#avisoOk").click()
            if marco.locator("#play").inner_text().strip().startswith("Pausar"):
                marco.locator("#play").click()
            # panel de alertas
            marco.locator("#botonAlertas").evaluate("e => e.click()")
            time.sleep(0.4)
            print(f"{ancho} px | panel de alertas abierto:", marco.locator("#panelAlertas").is_visible(),
                  "| casillas:", marco.locator("#panelAlertas input[type=checkbox]").count(),
                  "| estado:", marco.locator("#estadoAlertas").inner_text())
            marco.locator("#panelAlertas input[data-tipo='pedido']").evaluate("e => e.click()")
            print(f"{ancho} px | al silenciar los camiones:", marco.locator("#estadoAlertas").inner_text())
            pagina.locator("iframe").nth(1).screenshot(path=str(SALIDA / f"tablero_alertas_{ancho}.png"))
            marco.locator("#panelAlertas input[data-tipo='pedido']").evaluate("e => e.click()")
            marco.locator("#colasIlus").evaluate("e => e.click()")
            time.sleep(0.3)
            print(f"{ancho} px | sin colas ilustrativas, sin rótulo:", "COLAS ILUSTRATIVAS" not in marco.locator("#lienzo").inner_text())
            marco.locator("#colasIlus").evaluate("e => e.click()")
            pagina.close()
        print("errores de consola:", len(errores))
        for e in errores[:10]:
            print("  ", e)
        nav.close()


if __name__ == "__main__":
    main()
