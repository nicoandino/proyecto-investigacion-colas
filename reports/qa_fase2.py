"""QA visual de la Fase 2 con Playwright + Chrome instalado (sin descargar navegadores)."""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SALIDA = Path(sys.argv[1])
SALIDA.mkdir(parents=True, exist_ok=True)
MODELO = sys.argv[2] if len(sys.argv) > 2 else "real"
ANCHO, ALTO = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1440, 900)

consola = []
paginas_errores = []

with sync_playwright() as pw:
    navegador = pw.chromium.launch(channel="chrome", headless=True)
    pagina = navegador.new_page(viewport={"width": ANCHO, "height": ALTO})
    pagina.on("console", lambda m: consola.append((m.type, m.text)))
    pagina.on("pageerror", lambda e: paginas_errores.append(str(e)))
    pagina.goto("http://localhost:8501", wait_until="networkidle")

    def esperar_corrida(maximo=120):
        t0 = time.time()
        while time.time() - t0 < maximo:
            if pagina.locator("[data-testid='stStatusWidget']").count() == 0:
                # no hay "Running..." visible
                if pagina.locator("text=Simulando").count() == 0:
                    return True
            time.sleep(0.5)
        return False

    pagina.wait_for_selector("[data-testid='stSidebar']", timeout=60000)
    time.sleep(2)
    esperar_corrida()

    if MODELO == "clasico":
        pagina.get_by_text("Caso clásico", exact=False).first.click()
        time.sleep(2)
        esperar_corrida()

    pagina.wait_for_selector("[role='tab']", timeout=120000)
    pestanias = pagina.locator("[role='tab']")
    n = pestanias.count()
    print("pestañas:", n)
    nombres = []
    for i in range(n):
        nombre = pestanias.nth(i).inner_text().strip()
        nombres.append(nombre)
    # solo las pestañas de primer nivel (las 10 primeras)
    for i, nombre in enumerate(nombres[:10]):
        pestanias.nth(i).click()
        time.sleep(2.5)
        seguro = "".join(c if c.isalnum() else "_" for c in nombre)[:30]
        pagina.screenshot(path=str(SALIDA / f"{MODELO}_{i:02d}_{seguro}.png"), full_page=True)
        print("captura", i, nombre)

    excepciones = pagina.locator("[data-testid='stException']").count()
    print("excepciones de Streamlit en pantalla:", excepciones)
    if excepciones:
        for k in range(excepciones):
            print(pagina.locator("[data-testid='stException']").nth(k).inner_text()[:800])
    navegador.close()

errores = [c for c in consola if c[0] in ("error",)]
print("errores de consola:", len(errores))
for tipo, texto in errores[:15]:
    print("  ", tipo, texto[:300])
print("errores de pagina:", paginas_errores[:5])
