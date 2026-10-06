"""QA visual completo (ORQUESTADOR §10.4): todas las pestañas a 1440 y 390 de ancho (ventana alta para capturar la página entera), y la animación
en 3 instantes (madrugada, hora pico, corte de GNC).

Requiere el servidor corriendo en :8501.

    .venv/Scripts/python reports/qa_fase10_completo.py reports/qa/fase10
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/qa/fase10")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

PESTANIAS = [
    ("estacion", "La estación"), ("animacion", "Animación"), ("indicadores", "Indicadores"),
    ("demanda", "Demanda"), ("inventario", "Inventario"), ("red", "Red y rutas"),
    ("gnc", "GNC"), ("estaciones", "Estaciones"), ("escenarios", "Escenarios"),
    ("economia", "Economía"), ("sensibilidad", "Sensibilidad"), ("conclusion", "Conclusión"),
    ("modelo", "Modelo y método"), ("datos", "Datos y fuentes"),
]
SUBPESTANIAS_INDICADORES = ["Colas", "Clientes", "Inventario", "Complementarios"]
resumen: list[tuple[str, str, int, bool]] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 3000})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    pagina.goto("http://localhost:8501", wait_until="networkidle")
    pagina.wait_for_selector("[role='tab']", timeout=120000)

    def quieto(maximo: int = 900) -> None:
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
        time.sleep(2.5)

    def desborda() -> bool:
        return bool(pagina.evaluate(
            "document.documentElement.scrollWidth > window.innerWidth + 2"))

    def capturar(clave: str, formato: str) -> None:
        n = excepciones()
        resumen.append((clave, formato, n, desborda()))
        pagina.screenshot(path=str(SALIDA / f"{formato}_{clave}.png"), full_page=True)

    quieto()

    # ---- Dejar corridas hechas para que las pestañas tengan contenido
    ir("Estaciones")
    pagina.get_by_role("button", name="Correr las 4 estaciones").click()
    quieto()
    ir("Escenarios")
    pagina.get_by_role("button", name="Correr los escenarios").click()
    quieto()
    ir("Inventario")
    boton = pagina.get_by_role("button", name="Buscar la mejor política")
    if boton.count():
        boton.first.click()
        quieto()
    ir("Sensibilidad")
    pagina.get_by_role("button", name="Correr el tornado").click()
    quieto()

    # ---- Escritorio 1440×900 (página completa)
    for clave, nombre in PESTANIAS:
        ir(nombre)
        if clave == "indicadores":
            for sub in SUBPESTANIAS_INDICADORES:
                pagina.locator("[role='tabpanel']:visible [role='tab']").filter(has_text=sub).first.click()
                time.sleep(1.5)
                capturar(f"indicadores_{sub.lower()}", "escritorio")
            continue
        capturar(clave, "escritorio")

    # ---- Celular 390×844
    pagina.set_viewport_size({"width": 390, "height": 2600})
    time.sleep(2)
    for clave, nombre in PESTANIAS:
        try:
            ir(nombre)
        except Exception as e:  # la barra de pestañas puede necesitar scroll en pantallas angostas
            consola.append(f"no se pudo abrir {nombre} en celular: {str(e)[:120]}")
            continue
        capturar(clave, "celular")
    pagina.set_viewport_size({"width": 1440, "height": 3000})
    time.sleep(2)

    # ---- Animación en 3 instantes
    ir("Animación")
    pagina.wait_for_selector("iframe:visible", timeout=60000)
    time.sleep(3)
    pagina.screenshot(path=str(SALIDA / "animacion_1_madrugada.png"), full_page=True)
    marco = pagina.frame_locator("iframe:visible").first
    marco.locator("#saltoPico").click()
    time.sleep(1.5)
    pagina.screenshot(path=str(SALIDA / "animacion_2_hora_pico.png"), full_page=True)

    # Corte de GNC: julio con los episodios adentro
    pagina.get_by_text("GNC y cortes de invierno").first.click()
    time.sleep(1)
    pagina.get_by_text("Forzar que los episodios caigan dentro del horizonte").first.click()
    pagina.get_by_label("Mes a simular").first.click()
    pagina.keyboard.type("7")
    pagina.keyboard.press("Enter")
    time.sleep(1)
    pagina.locator("button:has-text('Correr simulación')").first.click(force=True)
    quieto()
    ir("Animación")
    pagina.wait_for_selector("iframe:visible", timeout=60000)
    slider = pagina.get_by_role("slider", name="Día a animar")
    slider.scroll_into_view_if_needed()
    slider.focus()
    for _ in range(6):
        pagina.keyboard.press("ArrowRight")
    quieto(180)
    pagina.wait_for_selector("iframe:visible", timeout=60000)
    time.sleep(3)
    marco = pagina.frame_locator("iframe:visible").first
    habilitado = marco.locator("#saltoCorte").is_enabled()
    if habilitado:
        marco.locator("#saltoCorte").click()
        time.sleep(1.5)
    pagina.screenshot(path=str(SALIDA / "animacion_3_corte_gnc.png"), full_page=True)
    print("animación: botón del corte habilitado:", habilitado, "| excepciones:", excepciones())
    navegador.close()

print(f"{'pestaña':26s} {'formato':10s} excepciones  desborde horizontal")
for clave, formato, n, d in resumen:
    print(f"{clave:26s} {formato:10s} {n:^11d}  {'SÍ' if d else 'no'}")
print("pestañas con excepciones:", sum(1 for _, _, n, _ in resumen if n))
print("pestañas con desborde horizontal de la página:",
      [(c, f) for c, f, _, d in resumen if d])
print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
