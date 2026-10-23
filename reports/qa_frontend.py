"""QA de la etapa 7 (frontend, "tótem de precios nocturno"): capturas de escritorio y celular.

Uso (con el servidor de QA en localhost:8502):
    .venv/Scripts/python reports/qa_frontend.py [carpeta_de_salida]

Captura el menú, el encabezado de resultados y varias pestañas; cuenta los errores de consola, los emojis que
queden en la página y las fuentes cargadas (tiene que estar Archivo).
"""

import pathlib
import re
import sys
import time

from playwright.sync_api import sync_playwright

URL = "http://localhost:8502"
SALIDA = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".impeccable/review")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⏩-⏺⬀-⯿]")
PESTANIAS = ("Animación", "Indicadores", "Demanda", "Pronóstico", "Inventario", "Red y rutas", "GNC", "Economía",
             "Datos y fuentes")


def quieto(pagina) -> None:
    """Espera a que termine la corrida (sin elementos atenuados) y vuelve al principio de la página."""
    pagina.wait_for_function(
        "document.querySelectorAll('[data-stale=\"true\"]').length === 0"
        " && !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=240_000)
    time.sleep(1.5)
    pagina.evaluate("document.querySelector('[data-testid=\"stMain\"]').scrollTo(0, 0)")
    time.sleep(0.5)


def pagina_completa(pagina, archivo, ancho: int) -> None:
    """Captura toda la página: el que se desplaza es stMain, así que se agranda la ventana hasta su alto."""
    alto = pagina.evaluate("document.querySelector('[data-testid=\"stMain\"]').scrollHeight")
    pagina.set_viewport_size({"width": ancho, "height": int(alto) + 20})
    time.sleep(1.5)
    pagina.screenshot(path=str(archivo))


def simular(pagina) -> None:
    pagina.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    pagina.get_by_text("Simular con datos reales").wait_for(timeout=60_000)
    quieto(pagina)


def resultados(pagina) -> None:
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.locator('[role="tab"]').first.wait_for(timeout=240_000)
    quieto(pagina)


def pestania(pagina, nombre: str) -> None:
    pagina.locator('[role="tab"]').filter(has_text=nombre).first.click()
    time.sleep(2.5)
    quieto(pagina)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(channel="chrome", headless=True)
        errores: list[str] = []

        # ------------------------------------------------------------------ escritorio (notebook)
        pagina = navegador.new_page(viewport={"width": 1440, "height": 900})
        pagina.on("console", lambda m: errores.append(f"[{m.type}] {m.text}") if m.type == "error" else None)
        pagina.on("pageerror", lambda e: errores.append(f"[pageerror] {e}"))
        simular(pagina)
        pagina.screenshot(path=str(SALIDA / "escritorio-menu.png"))
        pagina_completa(pagina, SALIDA / "escritorio-menu-completo.png", 1440)
        pagina.set_viewport_size({"width": 1440, "height": 900})
        resultados(pagina)
        pagina.screenshot(path=str(SALIDA / "escritorio-resultados.png"))
        pagina.screenshot(path=str(SALIDA / "desktop.png"))
        fuentes = pagina.evaluate("Array.from(document.fonts).filter(f => f.status === 'loaded').map(f => f.family)")
        print("fuentes cargadas:", sorted(set(fuentes)))
        print("¿Archivo?", any("Archivo" in f for f in fuentes))
        for nombre in PESTANIAS:
            pestania(pagina, nombre)
            if nombre == "Animación":
                time.sleep(4)
            archivo = SALIDA / f"escritorio-{nombre.lower().replace(' ', '-')}.png"
            pagina.screenshot(path=str(archivo))
            texto = pagina.locator('[data-testid="stMain"]').inner_text()
            sobrantes = sorted(set(EMOJI.findall(texto)))
            if pagina.locator('[data-testid="stIconEmoji"]').count():
                sobrantes.append("ícono emoji")
            print(f"{nombre}: captura {archivo.name}" + (f" · emojis: {sobrantes}" if sobrantes else ""))
        tabs = pagina.locator('[role="tab"]').all_inner_texts()
        lista = pagina.evaluate("(() => { const l = document.querySelector('[role=\"tablist\"]');"
                                " return [l.scrollWidth, l.clientWidth]; })()")
        print("¿entran todas las pestañas a 1440 px?", lista[0] <= lista[1] + 1, lista)
        pagina.set_viewport_size({"width": 1366, "height": 768})      # la notebook típica
        pestania(pagina, "Indicadores")
        pagina.screenshot(path=str(SALIDA / "notebook-1366-indicadores.png"))
        lista = pagina.evaluate("(() => { const l = document.querySelector('[role=\"tablist\"]');"
                                " return [l.scrollWidth, l.clientWidth]; })()")
        print("¿entran todas las pestañas a 1366 px?", lista[0] <= lista[1] + 1, lista)
        print("pestañas:", [t.replace("\n", " ") for t in tabs])

        # ------------------------------------------------------------------ celular (no es objetivo, se revisa igual)
        movil = navegador.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        movil.on("pageerror", lambda e: errores.append(f"[pageerror movil] {e}"))
        simular(movil)
        movil.screenshot(path=str(SALIDA / "movil-menu.png"))
        resultados(movil)
        movil.screenshot(path=str(SALIDA / "movil-resultados.png"))
        movil.screenshot(path=str(SALIDA / "mobile.png"))
        iconos = movil.evaluate("Array.from(document.querySelectorAll('[data-testid=\"stAlertContainer\"]'))"
                                ".map(a => (a.querySelector('[data-testid=\"stIconEmoji\"]') ? 'EMOJI' : 'ok'))")
        print("celular: íconos de los avisos:", iconos)
        ancho = movil.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        print("celular: ancho del documento / ventana:", ancho)

        print("errores de consola:", len(errores))
        for e in errores[:20]:
            print("  ", e)
        navegador.close()


if __name__ == "__main__":
    main()
