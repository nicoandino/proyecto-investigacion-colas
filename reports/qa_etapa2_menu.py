"""QA de la etapa 2 del rediseño: el menú inicial, las 4 formas de elegir el período, los resultados y
el modo Editar simulación. Requiere el servidor corriendo en :8501.

    .venv/Scripts/python reports/qa_etapa2_menu.py reports/qa/etapa2
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/etapa2")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []
resumen: list[tuple[str, int, str]] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 2200})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def abrir() -> None:
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

    def anotar(nombre: str, detalle: str = "") -> None:
        resumen.append((nombre, excepciones(), detalle))
        pagina.screenshot(path=str(SALIDA / f"{nombre}.png"), full_page=True)

    def elegir_tipo(texto: str) -> None:
        pagina.locator("[data-testid='stRadio'] label").filter(has_text=texto).first.click()
        quieto(30)

    def simular() -> float:
        t0 = time.time()
        pagina.get_by_role("button", name="Simular con datos reales").click()
        pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
        quieto()
        return time.time() - t0

    def volver_al_menu() -> None:
        pagina.get_by_role("button", name="Cambiar período").click()
        pagina.wait_for_selector("text=¿Qué querés simular?")
        quieto(30)

    # ---- Menú inicial
    abrir()
    anotar("menu_por_dias", pagina.get_by_text("Del 1 de enero al 30 de enero").count() and "ok" or "")
    print("menú inicial | excepciones:", excepciones())

    # ---- Por días: 180 días desde el 1 de enero (llega hasta invierno)
    pagina.get_by_label("Cantidad de días").fill("180")
    pagina.get_by_label("Cantidad de días").press("Enter")
    quieto(30)
    cartel = pagina.get_by_text("Incluye invierno").count()
    print("por días 180 | cartel de invierno:", cartel, "| excepciones:", excepciones())
    anotar("menu_180_dias", f"cartel invierno={cartel}")
    seg = simular()
    print(f"por días 180: simulado en {seg:.1f} s | excepciones:", excepciones())
    anotar("resultados_180_dias")

    # ---- Pestañas principales con resultados (sin excepciones)
    for nombre in ("Animación", "Indicadores", "Demanda", "Inventario", "GNC", "Economía", "Conclusión"):
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        time.sleep(2.5)
        n = excepciones()
        resumen.append((f"pestaña {nombre}", n, ""))
        if n:
            print("  excepciones en", nombre, pagina.locator("[data-testid='stException']").first.inner_text()[:200])
    print("pestañas | excepciones por pestaña:", [(a, b) for a, b, _ in resumen if a.startswith("pestaña")])

    # ---- Por meses: enero a marzo
    volver_al_menu()
    elegir_tipo("Por meses")
    pagina.get_by_label("Hasta").first.click()
    pagina.keyboard.type("Marzo")
    pagina.keyboard.press("Enter")
    quieto(30)
    print("por meses | texto:", pagina.get_by_text("90 días").count(), "| excepciones:", excepciones())
    anotar("menu_por_meses")
    seg = simular()
    print(f"por meses ene–mar: {seg:.1f} s | GNC sin cortes:", pagina.get_by_text("no hay cortes").count())
    pagina.locator("[role='tab']").filter(has_text="GNC").first.click()
    time.sleep(2.5)
    anotar("gnc_verano_sin_cortes", f"cartel={pagina.get_by_text('Ningún episodio').count()}")

    # ---- Por estaciones: invierno
    volver_al_menu()
    elegir_tipo("Por estaciones")
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Invierno").first.click()
    quieto(30)
    anotar("menu_estacion_invierno")
    seg = simular()
    print(f"invierno: {seg:.1f} s | excepciones:", excepciones())
    pagina.locator("[role='tab']").filter(has_text="GNC").first.click()
    time.sleep(2.5)
    anotar("gnc_invierno")

    # ---- Año completo
    volver_al_menu()
    elegir_tipo("Año completo")
    anotar("menu_anio")
    seg = simular()
    print(f"año completo: {seg:.1f} s | excepciones:", excepciones())
    anotar("resultados_anio")

    # ---- Editar simulación
    pagina.get_by_role("button", name="Editar simulación").click()
    pagina.wait_for_selector("text=Playeros por turno")
    quieto(30)
    anotar("editar_menu")
    pagina.get_by_text("Alta ·", exact=False).first.click()
    pagina.get_by_text("Duplicar la demanda en la hora pico").first.click()
    quieto(30)
    pagina.get_by_role("button", name="Simular editada").click()
    pagina.wait_for_selector("text=Simulación EDITADA", timeout=600000)
    quieto()
    print("editada | excepciones:", excepciones(), "| aviso de azar:", pagina.get_by_text("Simulación EDITADA").count())
    anotar("resultados_editada")
    pagina.get_by_role("button", name="Volver a los datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    quieto()
    print("volver a real | excepciones:", excepciones())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
print("capturas con excepciones:", [(a, n) for a, n, _ in resumen if n])
