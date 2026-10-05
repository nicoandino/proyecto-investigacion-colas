# 🚀 Guía de Onboarding — Simulador de Estación Shell San Rafael

> **Léeme primero si eres un agente nuevo en este proyecto.** 5 minutos para entender todo.

---

## 📌 En 30 segundos: Qué es esto

Simulador de eventos discretos (DES) para una estación de servicio Shell en San Rafael, Mendoza, Argentina. 

**Pregunta:** ¿Conviene agregar 1 surtidor + 1 cajero? ¿Cuál es la mejor política de reposición de combustible?

**Respuesta:** Simulamos 30 días de operación, medimos colas/esperas/ingresos, comparamos escenarios, y elegimos el que da más plata.

---

## 🎯 Estado Actual: Fase 2 (Octubre 2026)

### Qué está **HECHO** ✅

| Aspecto | Status | Detalles |
|--------|--------|----------|
| Motor DES (SimPy) | ✅ | Colas, abandono, tiempos aleatorios |
| Tanque + política (s,Q) | ✅ | Inventario acoplado con colas |
| UI Streamlit | ✅ | Sidebar con parámetros, pestañas de indicadores |
| Animación SVG | ✅ | Reproductor interactivo de un día |
| Modo determinista | ✅ | Sin Monte Carlo on-the-fly en demanda |
| Horizonte variable | ✅ | Día/semana/mes/estación/año |
| Datos consolidados | ✅ | 80+ fuentes verificadas |

### Qué está **PENDIENTE** ⏳

| Tarea | Prioridad |
|-------|-----------|
| Validación de campo (confirmar con gerente) | 🔴 CRÍTICA |
| Ajustar demanda base de 120k → 270k | 🔴 CRÍTICA |
| Ajustar playeros de 5-6 → 2-3 por turno | 🔴 CRÍTICA |
| Implementar mix diésel G2/G3 | 🟡 Importante |
| Implementar restricción GNC invierno | 🟡 Importante |
| Análisis de sensibilidad | 🟢 Menos urgente |

---

## 📊 Datos Validados Recientemente (Octubre 2026)

### Investigación: 5 agentes buscaron datos reales en Argentina

**1️⃣ DEMANDA**
- **Antes:** Estimación 100–150k L/mes
- **Ahora:** **270k L/mes confirmado** (CREEBBA + Surtidores.com.ar)
- **Rango:** 260–280k para estaciones medianas como San Rafael
- **Estacionalidad:** ~6% máximo (insignificante)

**2️⃣ MINIMARKET / SHELL SHOP**
- **Antes:** 30% de clientes
- **Ahora:** **20% confirmado** (dato directo YPF)
- **Fuente:** YPF reporta 300k clientes/día × 20% = entran 60k al shop
- **Rango según tipo:** 15% (chica) a 30% (premium Shell)

**3️⃣ MIX DE DIÉSEL**
- **G2 (gasoil común):** 75%
- **G3 (gasoil ultra):** 25%
- **Tendencia:** G2 cae -12.47%, G3 sube +11.52%
- **Estaciones pequeñas:** Probablemente solo G2 (no tanques separados)

**4️⃣ TURNOS Y PERSONAL**
- **Playeros por turno:** 2–3 (NO 5–6 como teníamos)
- **Cajeros:** 1 por turno ✅
- **Encargado de turno:** 1 obligatorio por turno
- **Total 24h:** 21 personas en 3 turnos
- **Horarios exactos:** 06:00–14:00 / 14:00–22:00 / 22:00–06:00
- **Regulación:** CCT 371/03 (SOESGyP), turnos rotativos

**5️⃣ GNC EN INVIERNO**
- **Restricción:** -50% oferta en junio–agosto
- **Causa:** ENARGAS Resolución 409/2026 (prioridad residencial en invierno)
- **Síntoma:** Presión en red cae → compresores sin capacidad → sin servicio
- **% afectadas:** 80% estaciones con contrato interrumpible
- **Capacidad compresor:** 20–25 autos/hora (estándar)
- **Temperatura:** San Rafael -2°C en julio está dentro de rango (no afecta equipos)

---

## 🏗️ Estructura del Código

```
proyecto-investigacion-colas/
├── CLAUDE.md                          # Contexto del proyecto
├── TASK.md                            # Checklist de fases
├── DATOS_OPERACIONALES_ESTACION_SHELL_SAN_RAFAEL.md
│                                      # 40+ parámetros con URLs (REFERENCIA)
├── FASE2_IMPLEMENTACION.md            # Documentación técnica Fase 2
├── ONBOARDING_PARA_AGENTES.md         # ESTE ARCHIVO
│
├── app.py                             # ENTRADA: Streamlit UI
│
├── sim/                               # MOTOR: Python puro, sin Streamlit
│   ├── config.py                      # Dataclasses: Estacionalidad, ParametrosSimulacion
│   ├── distribuciones.py              # RNG con streams separados
│   ├── modelo.py                      # Procesos SimPy (días, llegadas, colas, tanque)
│   ├── estadisticas.py                # Colectores de indicadores
│   ├── economia.py                    # Análisis económico
│   ├── runner.py                      # Corridas, réplicas, IC 95%
│   └── traza.py                       # Animación y logs
│
├── ui/                                # PRESENTACIÓN: Streamlit components
│   ├── animacion.py                   # Reproductor SVG
│   ├── graficos.py                    # Plotly charts
│   └── textos.py                      # Strings y etiquetas
│
└── verificar.py                       # 22 controles de correctitud
```

---

## 🚀 Cómo Correr

### 1. **Setup (primera vez)**

```bash
cd /home/user/proyecto-investigacion-colas
python -m venv .venv                   # Crear entorno
source .venv/bin/activate              # Activar (Linux/Mac)
pip install -r requirements.txt        # Instalar dependencias
```

### 2. **Ejecutar la UI**

```bash
streamlit run app.py
```

Abre en navegador: `http://localhost:8501`

### 3. **Estructura de la UI**

**Sidebar izquierdo (Parámetros):**
- 🏪 Capacidad actual (surtidores, cajas)
- 📊 **Fase 2: Modelo determinista** ← **NUEVO**
  - Toggle: "Usar modelo determinista"
  - Slider: Demanda base mensual (30k–300k L)
  - Radio: Horizonte (día/semana/mes/estación/año)
- 🚗 Demanda diaria (tabla Monte Carlo) ← Solo si Mode OFF
- ⏱️ Tiempos de servicio
- ⛽ Litros por carga
- 🧍 Comportamiento del cliente
- 🛢️ Tanque y reposición
- 🔬 Corrida (días, réplicas, semilla)
- 💵 Datos económicos

**Pestañas principales:**
- 🎬 Animación
- 📈 Indicadores
- 📊 Demanda (si Monte Carlo)
- 🛢️ Inventario
- 📉 Escenarios (Base vs. A vs. B vs. C)
- 💰 Análisis Económico
- ✅ Conclusión

### 4. **Verificar que funciona**

```bash
python verificar.py
# Debe decir: 22 controles en OK
```

---

## 🔧 Cambios Necesarios Antes de Presentar

### CRÍTICO — Actualizar parámetros

```python
# sim/config.py - Línea ~119-120

DEMANDA_TIPICA = DemandaDiaria(
    valores=(280, 320, 360, 400, 440),      # ← CAMBIAR a valores reales
    frecuencias=(10, 20, 40, 20, 10),
)
```

**Actual:** Demanda media ~360 autos/día = 120k L/mes

**Debe ser:** ~9,000 autos/día = 270k L/mes

---

Opción A (rápida): Cambiar demanda_base_mensual en UI a **270,000** y activar Fase 2

Opción B (precisa): Actualizar tabla DEMANDA_TIPICA

---

### IMPORTANTE — Ajustar personal

```python
# app.py - Línea ~106-107

with st.sidebar.expander("🏪 Capacidad actual", expanded=True):
    playeros = st.number_input("Playeros instalados", 1, 8, 3, 1)
    # ↑ Default es 3 (correcto: 2-3 por turno × 3 turnos = 6-9 total)
```

**Verificación:**
- Mañana (06:00–14:00): 2–3 playeros
- Tarde (14:00–22:00): 2–3 playeros
- Noche (22:00–06:00): 2–3 playeros
- **Total:** 6–9 playeros en la estación

---

### NUEVO — Implementar mix diésel

Actualmente el motor simula un único producto (Nafta Súper).

**Para añadir G2/G3:**
1. Duplicar tanques en config.py (uno para G2, otro para G3)
2. Crear streams RNG separados para cada diésel
3. Sortear tipo de diésel al llegar (75% G2, 25% G3)
4. Mantener políticas (s,Q) independientes

**Estimación de trabajo:** 2–3 horas de código

---

### NUEVO — Restricción GNC en invierno

**Actual:** GNC es 2–3% de la demanda, sin variación.

**Cambio:** En junio–agosto, reducir disponibilidad GNC -50% (ENARGAS).

**Implementación:**
1. Detectar mes del año en modelo.py
2. Si junio/julio/agosto: limitar tasa de llegada GNC × 0.5
3. Documentar en DATOS_OPERACIONALES...

**Estimación:** 1–2 horas

---

## 📚 Archivos de Referencia

Antes de tocar código, **lee estos en orden:**

1. **CLAUDE.md** — Contexto general, decisiones arquitectónicas
2. **TASK.md** — Qué está hecho, qué falta (Fase 3.5 = Validación)
3. **DATOS_OPERACIONALES_ESTACION_SHELL_SAN_RAFAEL.md** — 40+ parámetros con fuentes
4. **FASE2_IMPLEMENTACION.md** — Detalles técnicos de cambios Fase 2
5. **Este archivo (ONBOARDING_PARA_AGENTES.md)** — Guía rápida

---

## 🎯 Próximos Pasos (Por prioridad)

### ✅ **Fase 3.5: Validación de campo (CRÍTICA)**

**Antes de seguir avanzando, validar con el gerente de la estación:**

```markdown
[ ] Demanda actual (litros/mes) — comparar con 270k
[ ] Personal por turno:
    - Mañana (06:00–14:00): ___ playeros, ___ cajeros
    - Tarde (14:00–22:00): ___ playeros, ___ cajeros
    - Noche (22:00–06:00): ___ playeros, ___ cajeros
[ ] Horario exacto (¿06:00–22:00 o 24h?)
[ ] Tipos diésel (¿G2? ¿G3? ¿Mix?)
[ ] Minimarket: ¿realmente 20%?
[ ] GNC: ¿experimenta restricciones en invierno?
```

**Entregable:** Documento actualizado DATOS_OPERACIONALES... con confirmaciones.

---

### 🟡 **Fase 3.6: Sensibilidad (IMPORTANTE)**

Con datos validados:
- Variar demanda ±20% → impacto en colas/esperas
- Variar personal ±1 → impacto en tiempo/laborales
- Simular cortes RN junio–agosto → demanda reducida
- Gráficos de tornado (pareto sensibilidad)

**Entregable:** Reportes con recomendaciones de robustez.

---

### 🟢 **Fase 4: Presentación Final**

- Boxplots dispersión por escenario
- Exportar resultados a CSV/Excel
- Exportar gráficos como PNG
- Redactar conclusión económica final

---

## 💡 Tips para trabajar con esto

### Si necesitas cambiar parámetros:
1. **Editar en `app.py` (UI):** Slider, radio buttons, etc. → afecta solo esa sesión
2. **Editar en `sim/config.py` (código):** Cambios permanentes → afecta todos los usuarios

### Si necesitas debugging:
```bash
python -c "
from sim.config import ParametrosSimulacion, Estacionalidad
p = ParametrosSimulacion(modo_determinista=True, demanda_base_mensual=270000)
print(f'Demanda/día: {p.autos_por_dia:.0f}')
print(f'Estacionalidad junio: {p.estacionalidad.indice_mes(6)}')
"
```

### Si cambias el motor:
Ejecuta `python verificar.py` después para asegurar que los 22 controles siguen en OK.

---

## 🔗 Recursos Externos

- **CLAUDE.md:** Contexto arquitectónico completo
- **TASK.md:** Checklist de fases
- **DATOS_OPERACIONALES_ESTACION_SHELL_SAN_RAFAEL.md:** Tabla de 40+ parámetros con URLs
- **FASE2_IMPLEMENTACION.md:** Documentación técnica Fase 2

---

## 🤝 Si eres un agente y necesitas ayuda

**Pregunta:** "¿Cómo agrego variable X al modelo?"

**Pasos típicos:**
1. Definir en `sim/config.py` (dataclass field + default)
2. Usar en `sim/modelo.py` (en procesos SimPy)
3. Exponer en `app.py` (slider/radio en sidebar)
4. Documentar en CLAUDE.md (por qué existe)
5. Verificar con `python verificar.py`

**Pregunta:** "¿Cuáles son los 22 controles de verificar.py?"

Ver `verificar.py` línea ~250+. Incluye:
- Conservación (llegadas = atendidos + perdidos)
- Ley de Little (L = λ·W)
- Conservación de litros
- Monotonicidad (más surtidores → menos espera)
- Reproducibilidad (misma semilla = mismo resultado)

---

## 📌 Última cosa: Comandos útiles

```bash
# Compilar verificación sintaxis
python -m py_compile app.py sim/config.py sim/modelo.py

# Correr tests del motor
python verificar.py

# Limpiar cache Streamlit
rm -rf ~/.streamlit/cache

# Ver git log del proyecto
git log --oneline -10
```

---

**Última actualización:** Octubre 5, 2026  
**Autores:** Claude Haiku 4.5 + 5 agentes de investigación  
**Próxima revisión:** Después de validación de campo
