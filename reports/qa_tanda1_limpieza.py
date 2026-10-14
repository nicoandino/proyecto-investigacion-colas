"""QA de la tanda 1: La estación sin etiquetas ni imagen, Shell Shop, la ayuda "?" y Economía más corta.

    .venv/Scripts/python reports/qa_tanda1_limpieza.py http://localhost:8502 reports/qa/tanda1
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda1")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1600})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    time.sleep(4)

    def pestania(nombre: str) -> None:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        time.sleep(2)

    # --- La estación
    pestania("La estación")
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("La estación | insignias:", pagina.locator("[role='tabpanel']:visible .insignia").count(),
          "| imagen del playón (iframe):", pagina.locator("[role='tabpanel']:visible iframe").count(),
          "| menciona 12 caras:", "12 caras" in texto)
    pagina.screenshot(path=str(SALIDA / "la_estacion.png"))

    # --- Shell Shop en la animación
    pestania("Animación")
    marco = pagina.frame_locator("[role='tabpanel']:visible iframe").first
    print("Animación | Shell Shop:", marco.locator("text=Shell Shop").count() > 0,
          "| Shell Select:", marco.locator("text=Shell Select").count())

    # --- Ayuda "?": con el mouse aparece y se va; el clic no la traba; teclado. Desde la tanda 6 Inventario ya no
    # tiene ninguna ayuda (la búsqueda pasó al Caso de informe): se prueba en Modelo y método (las tarjetas de ρ).
    pestania("Modelo y método")
    icono = pagina.locator("[role='tabpanel']:visible [data-testid='stTooltipIcon'] button").first
    icono.scroll_into_view_if_needed()

    def visible() -> bool:
        cartel = pagina.locator("[data-testid='stTooltipContent']")
        return cartel.count() > 0 and cartel.first.is_visible()

    def despues(segundos: float) -> bool:
        time.sleep(segundos)
        return visible()

    icono.hover()
    abre = despues(1.0)
    pagina.mouse.move(5, 5)
    cierra = not despues(0.8)
    icono.click()
    pagina.mouse.move(5, 5)
    cierra_tras_clic = not despues(0.8)
    icono.focus()
    abre_con_foco = despues(1.0)
    pagina.keyboard.press("Escape")
    cierra_con_escape = not despues(0.5)
    print(f"Ayuda | abre con el mouse: {abre} · se va al salir: {cierra} · tras un clic se va al salir: "
          f"{cierra_tras_clic} · abre con el teclado: {abre_con_foco} · Escape la cierra: {cierra_con_escape}")

    # --- Economía
    pestania("Economía")
    texto = pagina.locator("[role='tabpanel']:visible").inner_text()
    print("Economía | estado de resultados:", "MARGEN OPERATIVO (ingresos" in texto,
          "| año estimado:", "AÑO ESTIMADO" in texto or "Por estación y año" in texto,
          "| ingresos y costos:", "Ingresos y costos de un mes" in texto)
    pagina.screenshot(path=str(SALIDA / "economia.png"))
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
