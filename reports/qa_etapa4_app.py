"""QA de la etapa 4: Indicadores (menú "qué querés saber"), Demanda verificable y "Qué se sorteó".

    .venv/Scripts/python reports/qa_etapa4_app.py reports/qa/etapa4
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/etapa4")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []
SECCIONES = ["Resumen", "Colas y esperas", "Clientes", "Playeros y surtidores", "Inventario", "Detalle completo"]

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2400})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto("http://localhost:8501", wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)

    def quieto(maximo: int = 600) -> None:
        t0 = time.time()
        time.sleep(2)
        while time.time() - t0 < maximo:
            if pagina.locator("[data-testid='stStatusWidget']").count() == 0:
                return
            time.sleep(0.5)

    def excepciones() -> int:
        return pagina.locator("[data-testid='stException']").count()

    def pestania(nombre: str) -> None:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        time.sleep(2.5)

    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    quieto()
    tabs = pagina.locator("[role='tab']").all_inner_texts()
    print("pestañas (real):", [t.strip() for t in tabs])
    print("¿existe 'Qué se sorteó' con datos reales?", any("sorteó" in t for t in tabs))

    pestania("Indicadores")
    for sec in SECCIONES:
        pagina.locator("[data-testid='stRadio'] label").filter(has_text=sec).first.click()
        quieto(30)
        n = excepciones()
        print(f"Indicadores · {sec}: excepciones {n}")
        pagina.screenshot(path=str(SALIDA / f"ind_{sec.replace(' ', '_').lower()}.png"), full_page=True)
        # nada de decimales en los clientes: busca un número con coma pegado a la palabra "clientes"
    texto = pagina.locator("body").inner_text()

    pestania("Demanda")
    texto_dem = pagina.locator("body").inner_text()
    print("Demanda | excepciones:", excepciones(),
          "| menciona Monte Carlo:", "Monte Carlo" in texto_dem, "| 'Número aleatorio':", "Número aleatorio" in texto_dem)
    pagina.screenshot(path=str(SALIDA / "demanda.png"), full_page=True)

    # Editada
    pagina.get_by_role("button", name="Editar simulación").click()
    pagina.wait_for_selector("text=Playeros por turno")
    pagina.get_by_text("Duplicar la demanda en la hora pico").first.click()
    quieto(30)
    pagina.get_by_role("button", name="Simular editada").click()
    pagina.wait_for_selector("text=Simulación EDITADA", timeout=600000)
    quieto()
    tabs = pagina.locator("[role='tab']").all_inner_texts()
    print("pestañas (editada):", [t.strip() for t in tabs])
    pestania("Qué se sorteó")
    print("Qué se sorteó | excepciones:", excepciones(), "| Monte Carlo:", "Monte Carlo" in pagina.locator("body").inner_text())
    pagina.screenshot(path=str(SALIDA / "que_se_sorteo.png"), full_page=True)
    pestania("Indicadores")
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Colas y esperas").first.click()
    quieto(30)
    pagina.screenshot(path=str(SALIDA / "ind_editada_colas.png"), full_page=True)
    print("Indicadores editada | excepciones:", excepciones())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
