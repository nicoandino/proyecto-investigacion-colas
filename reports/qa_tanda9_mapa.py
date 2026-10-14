"""QA de la tanda 9: la red sobre un mapa con relieve (OpenTopoMap) y el esquema como alternativa.

    .venv/Scripts/python reports/qa_tanda9_mapa.py http://localhost:8502 reports/qa/tanda9
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/qa/tanda9")
SALIDA.mkdir(parents=True, exist_ok=True)
consola: list[str] = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": 1440, "height": 1400})
    pagina.on("console", lambda m: consola.append(m.text) if m.type == "error" else None)
    pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))
    teselas = []
    pagina.on("response", lambda r: teselas.append(r.status) if "opentopomap" in r.url else None)
    pagina.goto(URL, wait_until="networkidle")
    pagina.wait_for_selector("text=¿Qué querés simular?", timeout=120000)
    pagina.get_by_role("button", name="Simular con datos reales").click()
    pagina.wait_for_selector("text=Simulación con datos reales (sin azar)", timeout=600000)
    time.sleep(4)
    pagina.locator("[role='tab']").filter(has_text="Red y rutas").first.click()
    time.sleep(3)
    pagina.get_by_text("Ver la red como").first.scroll_into_view_if_needed()
    time.sleep(8)
    mapa = pagina.locator("[role='tabpanel']:visible .js-plotly-plot").filter(has=pagina.locator(".maplibregl-map, .mapboxgl-map")).first
    mapa.scroll_into_view_if_needed()
    time.sleep(3)
    pagina.screenshot(path=str(SALIDA / "mapa_relieve.png"))
    print("teselas pedidas:", len(teselas), "· OK:", sum(1 for s in teselas if s == 200))
    print("atribución visible:", pagina.get_by_text("OpenTopoMap").count() > 0)
    pagina.locator("[data-testid='stRadio'] label").filter(has_text="Esquema").first.click()
    time.sleep(3)
    print("esquema sin error:", pagina.locator("[data-testid='stException']").count() == 0)
    print("excepciones:", pagina.locator("[data-testid='stException']").count())
    navegador.close()

print("errores de consola:", len(consola))
for linea in consola[:10]:
    print("  ", linea[:300])
