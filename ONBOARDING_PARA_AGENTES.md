# 🚀 Onboarding para agentes — Simulador de la Shell de San Rafael (v3)

> **Leé esto primero (5 minutos).** Después `ORQUESTADOR_SIMULADOR.md`, la especificación completa (§9 trae el cierre de cada fase).
> **Versión:** v3.0 · **6/10/2026** (Fase 10). Reemplaza a la v2, que describía un simulador a medio construir. **Si este archivo y otro documento se contradicen, mandan este archivo y el orquestador.**

---

## 1. En 30 segundos

Simulador de **eventos discretos** (Python + SimPy + Streamlit + Plotly) de **una estación Shell real**: **Av. Balloffet 1810 esq. Av. Los Sauces, San Rafael, Mendoza** (operador LOS SAUCES S.R.L.). TP de **Investigación Operativa** (colas + Monte Carlo + inventario/redes), grupo Andino–Assenza.

- **Producto del TP:** un **informe del caso**. El simulador ilustra escenarios y tiene que ser **defendible**: cada dato se muestra con su fuente, nivel y confianza.
- **Preguntas que responde (en pesos por mes):** ¿alcanza la dotación de playeros en el pico? · ¿cuál es la mejor política de reposición, con camión desde Dock Sud y rutas que se cortan? · ¿cuánto se pierde cuando se corta el GNC en invierno y adónde va? · ¿qué dato incierto mueve más la conclusión?
- **Estética:** paleta **Shell** (amarillo `#FBCE07`, rojo `#DD1D21`), **sin logo**; todo hex vive en `ui/tema.py`.

---

## 2. Estado real (6/10/2026)

| Cosa | Estado |
|---|---|
| Motor DES de la estación real (12 caras en 3 zonas, 5 productos, playeros por turno, cola finita, GNC, tanques y camión por producto, red de rutas) | ✅ `python verificar.py` → **100/100 OK** |
| Caso clásico (3 surtidores, 1 tanque) | ✅ conservado; reproduce los **números dorados** (control N1) |
| Registro de datos con fuente, tipo y confianza; paleta Shell | ✅ 108 datos, 20 contradicciones, cero parámetros huérfanos (N14), N15 de color |
| Calendario real, estaciones del año, escenarios S0–S12 con diferencias pareadas | ✅ |
| Economía real (estado de resultados, personal, flete, año estimado) y sensibilidad (tornado, 26 ejes) | ✅ |
| App Streamlit con animación SVG | ✅ 14 pestañas; QA visual en escritorio y celular (`reports/qa/fase10/`) |
| Datos **de la propia estación** | ❌ **Ninguno.** Todo es estimación o supuesto hasta el relevamiento (`ORQUESTADOR §12`) |
| Margen por litro, flete y almacenamiento | ⚠️ **Heredados sin fuente** (placeholders visibles) |

**Qué falta:** el relevamiento en la estación y el informe. La lista está en `TASK.md`.

---

## 3. Errores que tenían los documentos viejos (ya corregidos; no los repitas)

Estos puntos estaban escritos con aplomo y eran falsos. Están corregidos en `CLAUDE.md`, `FASE2_IMPLEMENTACION.md` y `DATOS_OPERACIONALES…md` (fe de erratas), pero conviene conocerlos:

1. **"270k L/mes = ~9.000 autos/día"** y **"100–150k L/mes = 3.300–5.000 autos/día"**: son **litros por día**. Con ≈ 36 L por cliente, 270.000 L/mes son **≈ 250 clientes/día**. Con 9.000 autos/día el simulador colapsa (ρ_pico ≈ 22).
2. **"El modelo determinista no necesita réplicas ni calentamiento"**: falso. Llegadas Poisson y tiempos aleatorios siguen ahí y el tanque arranca al 75 %. Réplicas, IC 95 % y calentamiento (2 días) **se mantienen**.
3. **"Datos únicamente de fuentes verificadas"**: no. Las etiquetas "Alta" del compilado `DATOS_OPERACIONALES` **sobreestiman** la confianza. Se aplica la **jerarquía de evidencia** (`ORQUESTADOR §4.1`).
4. **"Horario 06–22, NO 24 h"**: lo contradice la API oficial de Shell (`twenty_four_hour`). Default: **24 h**; el cierre nocturno es el escenario S10.
5. **"2–3 playeros por turno, 21 personas"**: `DATOS §4` dice 5 personas por turno = encargado 1 + playeros 2 + cajero 1 + tienda 1 (noche: 2). Playeros adoptados: **1 · 2 · 2**.
6. **"−50 % de oferta de GNC en invierno"** no tiene fuente: el corte documentado es **total** (ENARGAS, contrato interrumpible).

Detalle y las 20 contradicciones: `ORQUESTADOR §3` y `§4.2`.

---

## 4. Qué archivo manda (y mapa del repo)

**Orden de autoridad:** `ORQUESTADOR_SIMULADOR.md` > este archivo > `CLAUDE.md` / `README.md` / `TASK.md` > `CASO_SHELL_SAN_RAFAEL.md` (contexto) > `research_notes/…` (datos verificados por parámetro) > `DATOS_OPERACIONALES_…md` (útil, con su fe de erratas) > `FASE2_IMPLEMENTACION.md` (historia).

```
proyecto-investigacion-colas/
├── ORQUESTADOR_SIMULADOR.md        # ★ especificación, fases, compuertas y cierre de cada fase
├── ONBOARDING_PARA_AGENTES.md      # ESTE archivo
├── CLAUDE.md · README.md · TASK.md # contexto del proyecto, cómo correrlo y demo, qué falta
├── CASO_SHELL_SAN_RAFAEL.md        # contexto del caso, plan de investigación
├── research_notes/…/               # 01 identidad · 03 vehículos/litros/tiempos · 06 logística/rutas
├── app.py                          # Streamlit (única entrada)
├── verificar.py                    # 100 controles
├── sim/                            # MOTOR (sin Streamlit): datos · config · distribuciones · modelo · estadisticas
│                                   #   traza · runner · red · gnc · escenarios · economia · economia_real · sensibilidad
├── ui/                             # PRESENTACIÓN: tema · animacion · graficos* · datos_ui · textos
├── reports/                        # QA con Playwright + capturas por fase
└── .streamlit/config.toml          # fileWatcherType = "poll" (NO quitar)
```

**Ramas:** `main` (original) · `main-7ss6h3` (Fase 2 heredada) · **`claude/simulator-graphic-orchestrator-wu2xh4` = rama de trabajo** (un commit por fase). **No crear Pull Request** salvo pedido del usuario.

---

## 5. Los números que tenés que saber (valores adoptados)

| Qué | Valor adoptado | Conflicto / confianza |
|---|---|---|
| Surtidores | 6 de doble cara = **12 caras**: A nafta 4 · B diésel 2 · C GNC 6 | grupo |
| Horario | **24 h** | C1 |
| Demanda | **270.000 L/mes** ⇒ 9.000 L/día ⇒ **≈ 252 clientes líquidos/día** (+ GNC 3 %) | **C2/C3 🔴**; estimación, baja-media |
| Perfil horario | picos **07–10 h** y **16–18 h** (3,5 y 3,0 vs. 1,0 de madrugada) | C16 |
| Fin de semana | ×1,30 (normalizado al mes) | C17 |
| Estacionalidad | **neutra** por defecto (hay presets) | C10 |
| Mezcla en litros | Súper 28 · V-Power 19,5 · G2 29,3 · G3 23,2 % | C6, C7 |
| Carga por vehículo | `Triangular(0,2 ; 0,3 ; 1,0) × tanque` (media 0,5·T): auto 47 L, pick-up 80 L, moto 3,7 L, camión 300 L (supuesto) | **C12 🔴** |
| Tiempo en la cara | nafta/diésel `Triangular(2,5,8)` min; GNC `(5,7,12)` | C11 |
| Playeros (noche · mañana · tarde) | **1 · 2 · 2**; 1 caja | **C5 🔴** (ρ_pico = 0,85 con 2) |
| Minimarket | entra el **20 %** | C4 |
| Plazo del camión | `Triangular(24,36,48)` h desde **Dock Sud** (991 km) | Shell Mendoza capital, 2023 |
| GNC en invierno | corte **total** por episodios (2 × 6 días jun–ago), 3 compresores, 30 % migra a Súper | **C8/C9** |
| Economía | margen $100/L, $2.500 por compra, flete fijo $150.000 (**heredados**); playero $1.680.000/mes; francos ×1,4 | C18; ECO-* |

**Resultado de referencia (con esos supuestos):** espera en la hora pico ≈ 3,1 min; margen operativo ≈ −$3,8 M/mes con $100/L (empata con ≈ $116/L).

---

## 6. Unidades y vocabulario

- **Tiempo:** minutos (el día = 1440). **Dinero:** pesos. **Volumen:** litros, **salvo el GNC, que es en m³**. **Nunca** sumes litros con m³ ni los llames "autos".
- **Litros/mes es la entrada de demanda; los clientes por día se derivan** (`ORQUESTADOR §14.2`).
- **Cara** = lado de un surtidor = una posición de carga. **Playero** = quien atiende (servicio atendido).
- **Réplica** = una corrida con otra semilla; se informa **promedio ± IC 95 %**. **Números aleatorios comunes** = misma semilla entre escenarios; la comparación usa la **diferencia pareada**.
- **Dato / estimación / observación / supuesto / heredado**: los cinco tipos del Registro. **Heredado** = del proyecto hipotético, sin fuente.
- **`[RESUMEN]`** = cifra vista sólo en el resumen de un buscador (no verificada). **`OK-orig`** = abierta y leída en el original.

---

## 7. Cómo correr (comandos probados)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt                          # simpy, streamlit>=1.40, plotly>=6, pandas, numpy

python verificar.py                                      # ≈ 2 min; "Todos los controles pasaron (100 en total)"
python -m streamlit run app.py --server.headless true --server.port 8501    # http://localhost:8501
python -m py_compile app.py sim/*.py ui/*.py             # chequeo de sintaxis
```
- Si cambiás la **firma** de un módulo de `sim/` o `ui/`, **reiniciá Streamlit**: recarga `app.py` pero conserva el módulo viejo.
- QA visual: `python reports/qa_fase10_completo.py reports/qa/fase10` (Playwright con el Chrome instalado; **no** descargar navegadores).
- Referencia reproducible: `correr_replica(ParametrosSimulacion.clasico(), semilla=1).espera_pico = 3.609402` (dorado) y `correr_replica(ParametrosSimulacion(), semilla=1).espera_pico = 3.199252` (estación real).

---

## 8. Cómo seguir (lo que falta de verdad)

1. **Relevamiento en la estación** (`ORQUESTADOR §12`, `TASK.md`): demanda por producto, dotación por turno, litros y tiempos de carga, GNC, márgenes y flete. Cada valor entra al Registro como `observacion` (🔵).
2. **Informe del TP** con los números del simulador (las capturas de cada pestaña están en `reports/qa/`).
3. **Deuda técnica** conocida y priorizada en `TASK.md` (anulación de un `Dato` desde la app, botón de verificación, camión consolidado…).

---

## 9. Cómo agregar una variable (proceso)

1. **Registrala** en `sim/datos.py` (`Dato` con valor, unidad, **fuente, tipo, confianza**, alternativas si hay conflicto) y mapeala en `MAPA_PARAMETROS`.
2. Leé su **default desde el Registro** en `sim/config.py` (dataclass `frozen=True`, **tuplas**, no listas/dicts).
3. Usala en `sim/modelo.py` (si es aleatoria, con un **stream nuevo AL FINAL** de `STREAMS`).
4. Mostrala en `app.py` con su **insignia** (`ui/datos_ui.py`).
5. Agregale un **control** en `verificar.py` y corré los 100.
6. Si es `supuesto`/`heredado`/`estimacion`, definí `bajo`/`alto` o alternativas y sumala como **eje** en `sim/sensibilidad.py` (o a `NO_ES_EJE` con el motivo): el control 23 falla si queda sin clasificar.

---

## 10. Qué NO hacer

- ❌ Inventar un número sin pasarlo por el Registro.
- ❌ Usar una cifra "Alta" de un documento compilado como si fuera evidencia.
- ❌ Dividir litros por 30 y llamarlo "autos".
- ❌ Reordenar `STREAMS` o reutilizar un stream (rompe los dorados y los números aleatorios comunes).
- ❌ `import streamlit` o `ui` dentro de `sim/`; `print()` en `sim/`.
- ❌ Base de datos, login, API REST, Docker, plugins, multiprocessing, lavadero.
- ❌ Hex de color fuera de `ui/tema.py`; amarillo como texto sobre blanco; el logo de Shell.
- ❌ Declarar "verificado visualmente" sin haber abierto la app en un navegador.
- ❌ Crear un Pull Request sin que lo pidan.
- ❌ Presentar los pesos como cifras del negocio: son **placeholders** hasta tener márgenes reales.

---

## 11. Preguntas frecuentes

**¿Por qué 270.000 L/mes si la fuente dice 100–150k?** Porque las fuentes débiles convergen ahí (informe regional, promedio nacional de 270–380k, punto de equilibrio de una estación ≈ 315–400k) y 120k sólo se apoya en "San Rafael cayó 30 %". **No pudimos confirmar la cita "CREEBBA 270k"**: por eso es *estimación, confianza baja-media*, con **150k y 400k** como extremos del tornado.

**¿Cuál de dos datos que se contradicen uso?** El de mayor nivel en la jerarquía (`ORQUESTADOR §4.1`); el otro queda como **alternativa** y como eje del tornado. Está resuelto para los 20 conflictos conocidos en `§4.2`; si encontrás uno nuevo, agregalo ahí.

**¿Qué falta de verdad?** Datos **de la propia estación**. Sin relevamiento, todo es estimación y la app lo dice.

**¿Y el relevamiento?** Una visita con el encargado + conteo de un día hábil y uno de fin de semana. Checklist en `ORQUESTADOR §12`.

---
**Última actualización:** 6/10/2026 · **Grupo:** Andino–Assenza · **Próxima revisión:** después del relevamiento en la estación.
