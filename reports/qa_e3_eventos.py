"""QA de la etapa E3 (parte 4): eventos aleatorios desde el menú, pestaña Eventos, avisos del tablero, economía.

    .venv/Scripts/python reports/qa_e3_eventos.py http://localhost:8502 reports/qa/e3
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/e3")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1600})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

    def esperar(segundos: float = 2.0) -> None:
        time.sleep(segundos)

    def pestania(nombre: str) -> str:
        pagina.locator("[role='tab']").filter(has_text=nombre).first.click()
        esperar(3)
        return pagina.locator("[role='tabpanel']:visible").inner_text()

    def tablero():
        for _ in range(40):
            marcos = [f for f in pagina.frames if f.locator("#pGnc").count()]
            if marcos:
                return marcos[0]
            esperar(2)
        return None

    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)

    # --- Menú: prender todos los eventos, frecuencia × 5
    pagina.get_by_text("Eventos aleatorios: cosas").first.click()
    esperar()
    pagina.get_by_role("button", name="Prender todos").click()
    esperar(2)
    pagina.locator("[data-testid='stSelectbox']").filter(has_text="Frecuencia").first.click()
    esperar(1)
    pagina.get_by_role("option", name="× 5 (para verlos en un período corto)").click()
    esperar(3)
    menu = pagina.locator("body").inner_text()
    marcadas = pagina.locator("[data-testid='stCheckbox'] input:checked").count()
    print("Menú | casillas marcadas:", marcadas, "| vista previa:",
          [linea for linea in menu.split("\n") if "salen" in linea and "eventos" in linea][:1])
    pagina.screenshot(path=str(SALIDA / "menu_eventos.png"), full_page=True)

    # --- Simular
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(5)
    cuerpo = pagina.locator("body").inner_text()
    tabs = [t.strip() for t in pagina.locator("[role='tab']").all_inner_texts()]
    print("Resultados | aviso de eventos:", "Con eventos aleatorios" in cuerpo, "| ajustes:",
          [linea for linea in cuerpo.split("\n") if "eventos aleatorios (semilla" in linea][:1])
    print("pestañas:", tabs)

    pagina.locator("[role='tab']").filter(has_text="Animación").first.click()
    esperar(3)
    marco = tablero()
    n_ev = marco.evaluate("EVENTOS.length")
    caras_fuera = marco.evaluate("Object.values(F.g).reduce((n, g) => n + g.c.filter((s) => s.includes('x')).length, 0)")
    marco.evaluate("colaAvisos = [EVENTOS[0]]; abrirAviso();")
    esperar(1)
    titulo = marco.locator("#avisoTitulo").inner_text()
    nota = marco.locator("#avisoNota").inner_text()
    print("Tablero | eventos en los avisos:", n_ev, "| cuadros con una cara tachada:", caras_fuera,
          "| aviso:", titulo, "| nota con la semilla:", "semilla" in nota)
    pagina.screenshot(path=str(SALIDA / "aviso_evento.png"))
    marco.evaluate("cerrarAviso(false)")

    texto = pestania("Eventos")
    print("Pestaña Eventos | tarjetas:", "Eventos que ocurrieron" in texto and "Costo de los eventos" in texto,
          "| tabla:", pagina.locator("[role='tabpanel']:visible [data-testid='stDataFrame']").count())
    pagina.screenshot(path=str(SALIDA / "pestania_eventos.png"), full_page=True)
    texto = pestania("Economía")
    print("Economía | cascada con eventos:", "Eventos aleatorios" in pagina.content())
    texto = pestania("Conclusión")
    print("Conclusión | línea de eventos:", "Eventos aleatorios" in texto)
    pagina.screenshot(path=str(SALIDA / "conclusion.png"), full_page=True)
    print("excepciones (con eventos):", pagina.locator("[data-testid='stException']").count())

    # --- Volver, apagar todos y simular: no hay pestaña de eventos
    pagina.get_by_role("button", name="Cambiar período").click()
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=60000)
    esperar()
    pagina.get_by_text("Eventos aleatorios: cosas").first.click()
    esperar()
    pagina.get_by_role("button", name="Apagar todos").click()
    esperar(2)
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    esperar(4)
    tabs = [t.strip() for t in pagina.locator("[role='tab']").all_inner_texts()]
    print("Sin eventos | pestaña Eventos:", any("Eventos" in t for t in tabs),
          "| aviso:", "Con eventos aleatorios" in pagina.locator("body").inner_text())
    print("excepciones (sin eventos):", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
