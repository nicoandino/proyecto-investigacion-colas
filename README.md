# Simulador de la Estación Shell — San Rafael

TP de **Investigación Operativa** (4º año, grupo Andino–Assenza). Es un simulador de eventos discretos de una estación
real: la **Shell de Av. Balloffet 1810 esq. Av. Los Sauces, San Rafael, Mendoza**. Está hecho en Python con SimPy, y la
interfaz usa Streamlit y Plotly.

> Proyecto académico: no es oficial ni está afiliado a Shell. La estación no aportó mediciones propias. Los números
> salen de fuentes públicas y estimaciones, y cada uno está en el Registro (`sim/datos.py`) con su fuente.

## Cómo iniciarlo

Los comandos se corren desde la carpeta del proyecto, en Windows (Git Bash o PowerShell).

### La primera vez (si no existe la carpeta `.venv`)

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python -m pip install -r requirements.txt
```

### Cada vez que se quiere usar

```bash
.venv/Scripts/streamlit run app.py
```

Se abre en **http://localhost:8501**. Para cerrarlo, hay que apretar `Ctrl+C` en la terminal.

Si el puerto 8501 está ocupado, hay otro simulador corriendo: o se cierra ese, o se lanza en otro puerto.

```bash
.venv/Scripts/streamlit run app.py --server.port 8502
```

Si se modifica algo de `sim/` o `ui/`, hay que **cerrar y volver a lanzar** el simulador: Streamlit no recarga solo esos
módulos.

## Cómo se usa

1. **Menú inicial: ¿qué querés simular?** Se elige el período (por días, por meses, por estación o el año completo).
   Hay ajustes opcionales que arrancan con los valores del Registro: economía, GNC, calendario de demanda,
   abastecimiento y eventos aleatorios.
2. **Simular con datos reales.** Corre sin azar, así que siempre da el mismo resultado y se puede comprobar. Los
   resultados están en pestañas: La estación, Animación, Indicadores, Colas, Demanda, Pronóstico, Inventario, Red y rutas,
   GNC, Economía, Conclusión y Datos y fuentes (al final, un desplegable con Modelo y método). La pestaña Eventos
   aparece sólo si se prendieron eventos aleatorios en el menú.
3. **Editar simulación** (al final de los resultados) cambia playeros, demanda o precios. La versión editada usa azar
   y agrega una pestaña que explica qué se sorteó.
4. Desde el menú también se puede abrir:
   - el **escenario único**: una semana con los playeros, la franja, la temporada y la clientela que se elijan;
   - el **Caso de informe**: la búsqueda de la mejor política de reposición, los escenarios S0–S12 y el tornado de
     sensibilidad. Tarda más que el resto.

## Verificar que el modelo anda bien

```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 .venv/Scripts/python verificar.py
```

Corre todos los controles y tarda unos 5 minutos. Tiene que terminar en **"Todos los controles pasaron"**.

Los QA visuales están en `reports/qa_*.py` y usan Playwright con el Chrome instalado. Se corren contra un simulador ya
lanzado, por ejemplo:

```bash
.venv/Scripts/python reports/qa_frontend.py
```

## Qué hay en cada carpeta

| Carpeta o archivo | Qué es |
|---|---|
| `app.py` | La aplicación de Streamlit (la única entrada). |
| `sim/` | El motor, sin Streamlit: datos (el Registro), parámetros, modelo SimPy, red de rutas (Dijkstra), GNC, pronóstico, eventos, escenarios y economía. |
| `ui/` | La presentación: tema y colores, la animación (dibujada en el navegador), los gráficos y las vistas. |
| `verificar.py` | Los controles del modelo. |
| `reports/` | Los QA con Playwright, sus capturas y `generar_datos_reales.py`, que regenera `DATOS_REALES.md`. |
| `research_notes/` | Las notas de investigación con citas y URL. |
| `static/` | La tipografía Archivo y las imágenes que sirve la app. |
| `DATOS_REALES.md` | El Registro de datos en versión legible. Es un archivo generado: no se edita a mano. |
| `ORQUESTADOR.md` | El plan de trabajo por etapas y tandas, con las decisiones y el avance. |
| `CLAUDE.md`, `PRODUCT.md`, `DESIGN.md` | El contexto del proyecto, del producto y del diseño. |

## Requisitos

- Python 3.11 o superior. El proyecto se usa con Python 3.14.
- Las dependencias de `requirements.txt`: SimPy, Streamlit, Plotly, pandas y NumPy.
- Para los QA, Playwright y Google Chrome instalados.
- El mapa con relieve de Red y rutas necesita internet porque usa las teselas de OpenTopoMap. Sin conexión, hay que
  elegir "Esquema".
