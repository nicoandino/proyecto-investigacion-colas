"""QA de la tanda 7: la animación se detiene en los avisos (corte de GNC, pedido de camión), los muestra de a
uno, "Seguir trayectoria del camión" lleva a Red y rutas con el camión sobre la ruta, y el camión descarga.

    .venv/Scripts/python reports/qa_tanda7_avisos.py http://localhost:8502 reports/qa/tanda7
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda7")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1500})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def esperar(segundos: float = 2.0) -> None:
        time.sleep(segundos)

    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Por estaciones").first.click()
    esperar()
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Invierno").first.click()
    esperar()
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    pagina.locator("[role='tab']").filter(has_text="Animación").first.click()
    esperar(4)
    marco = pagina.frame_locator("[role='tabpanel']:visible iframe").first
    marco.locator("#velocidad").select_option("2")
    marco.locator("#play").click()

    vistos = []
    seguido = False
    for _ in range(12):
        marco.locator("#aviso.abierto").wait_for(timeout=120000)
        titulo = marco.locator("#avisoTitulo").inner_text()
        cola = marco.locator("#avisoCola").inner_text()
        vistos.append(titulo + (f" [{cola}]" if cola else ""))
        if titulo.startswith("Bajo nivel de combustible") and not seguido:
            pagina.screenshot(path=str(SALIDA / "aviso_pedido.png"))
            marco.locator("#avisoSeguir").click()
            seguido = True
            esperar(3)
            break
        if titulo.startswith("El GNC"):
            pagina.screenshot(path=str(SALIDA / "aviso_gnc.png"))
        marco.locator("#avisoOk").click()
        esperar(0.5)
    print("avisos en orden:", vistos)
    activa = pagina.locator("[role='tab'][aria-selected='true']").inner_text().strip()
    print("pestaña después de 'Seguir trayectoria':", activa)
    seg = pagina.frame_locator("[role='tabpanel']:visible iframe").first
    cartel = seg.locator("#cartel").inner_text()
    print("cartel en Red y rutas:", cartel.splitlines()[0] if cartel else "")
    esperar(9)
    pagina.locator("[role='tabpanel']:visible iframe").first.scroll_into_view_if_needed()
    pagina.screenshot(path=str(SALIDA / "red_seguimiento.png"))

    # El camión llega y descarga en el playón
    pagina.locator("[role='tab']").filter(has_text="Animación").first.click()
    esperar(2)
    marco.locator("#pausarAvisos").uncheck()
    marco.locator("#saltoDescarga").click()
    esperar(1)
    texto_svg = marco.locator("#lienzo").inner_text()
    print("camión en el playón:", "descargando" in texto_svg or "llegando" in texto_svg)
    pagina.locator("[role='tabpanel']:visible iframe").first.screenshot(path=str(SALIDA / "camion_descargando.png"))
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
