"""QA de la etapa E0 (parte 4): el GNC lo carga un playero, y la app lo dice en todos lados.

    .venv/Scripts/python reports/qa_e0_gnc.py http://localhost:8502 reports/qa/e0
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/e0")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []
VIEJOS = ("no usa playero", "no retiene playero", "sólo conecta la manguera", "· sin playero")

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1500})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def esperar(segundos: float = 2.0) -> None:
        time.sleep(segundos)

    def pestania(nombre: str) -> str:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        esperar(3)
        return pagina.locator("[role='tabpanel']:visible").inner_text()

    def viejos(texto: str) -> list[str]:
        return [v for v in VIEJOS if v in texto]

    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)

    # --- Escenario único: la cuenta de ρ incluye el GNC
    pagina.get_by_role("button", name="Simular el escenario único").click()
    pagina.wait_for_selector("text=Conclusión de este escenario", timeout=300000)
    esperar(3)
    texto = pagina.locator("body").inner_text()
    print("Escenario único | cuenta con el GNC:", "min de playero por" in texto and "a todos los carga un playero" in texto,
          "| textos viejos:", viejos(texto))
    pagina.screenshot(path=str(SALIDA / "escenario_unico.png"), full_page=True)
    pagina.get_by_role("button", name="Volver al menú").click()
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=60000)
    esperar()

    # --- Flujo normal
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)

    tablero = ""
    for _ in range(30):                     # el tablero es uno de varios iframes (hay uno auxiliar invisible)
        marcos = [f for f in pagina.frames if f.locator("#pGnc").count()]
        if marcos:
            tablero = marcos[0].locator("#pGnc").inner_text()
            break
        esperar(2)
    print("Animación | panel GNC:", tablero.replace("\n", " ")[-60:], "| dice 'lo carga un playero':", "lo carga un playero" in tablero)
    pagina.screenshot(path=str(SALIDA / "animacion.png"))

    texto = pestania("Modelo y método")
    print("Modelo y método | ρ con el GNC:", "a todos los atiende un playero" in texto,
          "| GNC con playero en el modelo:", "también lo carga un playero" in texto, "| textos viejos:", viejos(texto))
    pagina.screenshot(path=str(SALIDA / "modelo_metodo.png"), full_page=True)

    texto = pestania("Datos y fuentes")             # la tabla es un canvas: PER-04 se lee en DATOS_REALES.md
    registro = Path("DATOS_REALES.md").read_text(encoding="utf-8")
    print("Datos y fuentes | PER-04 nuevo (DATOS_REALES.md):", "| PER-04 | El GNC lo carga un playero | True" in registro,
          "| textos viejos:", viejos(texto))

    texto = pestania("Indicadores")
    print("Indicadores | textos viejos:", viejos(texto))
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
