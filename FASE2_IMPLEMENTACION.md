# Fase 2 Implementación (HISTÓRICO, superado) — "Modelo determinista con datos verificados"

> **ESTADO: SUPERADO — documento histórico, corregido en la Fase 10 (6/10/2026).**
> Describe lo que hizo la Fase 2 de otro agente el 5/10/2026. Esa implementación **tenía errores de fondo**
> que se corrigieron en las fases 0–2 del orquestador. **Para trabajar, leer `ONBOARDING_PARA_AGENTES.md` y
> `ORQUESTADOR_SIMULADOR.md`; donde discrepen, mandan ellos.** El resto de este archivo se conserva
> como registro de lo que se hizo y se marcó con **❌ FALSO** / **✅ CORRECTO HOY** lo que no vale.

### Fe de erratas

| Lo que dice este documento | Por qué está mal | Qué vale hoy |
|---|---|---|
| "Modelo **determinista**, sin Monte Carlo en la demanda" y "no se necesitan réplicas" | Sólo el **total diario** era fijo: las llegadas siguen siendo Poisson y los tiempos de servicio aleatorios. Hay varianza, así que hacen falta **réplicas e IC 95 %**. | Se llama **demanda esperada** (`modo_demanda = "esperada"`). Réplicas e IC se mantienen. El Monte Carlo se conserva para el producto y el tipo de vehículo. |
| "Calentamiento innecesario / deshabilitado en determinista" | El tanque arranca al 75 % y las colas vacías: hay **transitorio**. Con calentamiento 0 contamina los indicadores. | **Calentamiento de 2 días** en todos los modos. |
| `autos_por_dia = demanda_base_mensual / 30`; "120.000 L ⇒ 4.000 autos/día" | **Mezcla litros con autos** (error ×35). Simulaba 4,2 M L/mes en vez de 120.000. | `clientes/día = (litros_mes ÷ días del mes) ÷ litros medios por cliente` (35,7 L). **270.000 L/mes ⇒ ≈ 252 clientes líquidos/día** (control N16). |
| "Un mes" = 30 días desde enero; la estacionalidad funciona por horizonte | `mes = ((dia-1)//30)+1` recibe el día de la corrida, no del calendario: **siempre simulaba enero**. El campo `horizonte` no se usaba en el motor. | `fecha_inicio` real y **una sola** función `dias_y_fecha(horizonte, mes)`; cada día se mapea a su mes y a su día de la semana (control N17). |
| Estacionalidad "enero=100 … junio=55" como tabla del modelo | Es un proxy de **ocupación hotelera**, no de ventas de combustible, y no coincidía con su fuente. | **Neutra (1,00) por defecto**; presets "leve ±6 %" y "proxy turístico" (S11). |
| "Datos únicamente de fuentes verificadas", "confianza Alta" | Las etiquetas "Alta" son del compilador y sobreestiman. | Registro con **nivel, tipo y confianza**, jerarquía de evidencia y las alternativas que perdieron (`ORQUESTADOR §4`). |
| Parámetros `modo_determinista`, `demanda_base_mensual` (120.000 L) | Nombres engañosos y valor sin respaldo. | `modo_demanda`, `litros_mes` (**270.000**, estimación baja-media, con 150.000 y 400.000 como extremos de sensibilidad). |

## Resumen Ejecutivo

Se completó la transición del simulador de una propuesta académica hipotética a un **modelo determinista de caso real** para la estación Shell de San Rafael, Mendoza. Los cambios involucran:

1. **Eliminación de Monte Carlo en demanda diaria** → Cálculo determinista basado en demanda base y estacionalidad
2. **Consolidación de fuentes verificadas** → Parámetros con confianza y URLs en `DATOS_OPERACIONALES_ESTACION_SHELL_SAN_RAFAEL.md`
3. **Horizonte de simulación variable** → Selector día/semana/mes/estación/año en la UI

---

## Cambios de Código

### 1. `sim/config.py`

#### Nueva clase `Estacionalidad`

```python
@dataclass(frozen=True)
class Estacionalidad:
    """Multiplicadores de demanda por mes (índice base = 100 en enero)."""
    indices: tuple[float, ...] = (
        100.0,  # enero (vendimia + verano)
        60.0,   # febrero (transición)
        ...
        105.0,  # diciembre (Navidad + verano)
    )
    
    def indice_mes(self, mes: int) -> float:
        """Índice de estacionalidad para un mes (1-12)."""
        
    @property
    def promedio(self) -> float:
        """Promedio de índices (cercano a 100)."""
```

**Rationale:** Los índices capturan la variación de demanda según la época del año (vendimia en enero, mínimo en junio, esquí en julio, etc.). El promedio se usa para normalizar y que `autos_por_dia` sea consistente cuando se aplican índices.

#### Nuevos campos en `ParametrosSimulacion`

```python
@dataclass(frozen=True)
class ParametrosSimulacion:
    ...
    # --- Modo determinista (Fase 2) ---
    modo_determinista: bool = False           # Activa/desactiva Monte Carlo
    demanda_base_mensual: float = 120_000.0  # L/mes (base para determinismo)
    estacionalidad: Estacionalidad = ESTACIONALIDAD_TIPICA
    horizonte: str = "mes"                    # "dia", "semana", "mes", "estacion", "anio"
```

#### Nuevos métodos en `ParametrosSimulacion`

```python
def _dias_segun_horizonte(self) -> int:
    """Calcula días a simular según horizonte."""
    horizonte_a_dias = {
        "dia": 1,
        "semana": 7,
        "mes": 30,
        "estacion": 90,
        "anio": 365,
    }
    return horizonte_a_dias.get(self.horizonte, 30)

@property
def autos_por_dia(self) -> float:
    """Autos/día promedio.
    
    En determinismo: demanda_base_mensual / 30.
    En Monte Carlo: media de tabla empírica.
    """
    if self.modo_determinista:
        return self.demanda_base_mensual / 30.0
    else:
        return self.demanda.media

def autos_por_dia_fecha(self, dia_del_anio: int) -> float:
    """Autos/día ajustados por estacionalidad para una fecha.
    
    Args:
        dia_del_anio: 1-365
    
    Returns:
        autos/día para ese día (base × índice/promedio)
    """
    if not self.modo_determinista:
        return self.autos_por_dia
    
    mes = min(12, ((dia_del_anio - 1) // 30) + 1)
    indice = self.estacionalidad.indice_mes(mes)
    autos_base = self.demanda_base_mensual / 30.0
    return autos_base * (indice / self.estacionalidad.promedio)
```

### 2. `sim/distribuciones.py`

#### Nuevo método `Aleatorio.determinista()`

```python
def determinista(self, autos_por_dia: float) -> tuple[int, int]:
    """Retorna una demanda determinista (sin azar).
    
    En modo determinista no hay número aleatorio. El segundo valor es 50
    (representa "el medio" del rango de valores posibles).
    
    Args:
        autos_por_dia: cantidad esperada de autos
    
    Returns:
        Tupla (autos_redondeados, numero_pseudoaleatorio_50)
    """
    return int(round(autos_por_dia)), 50
```

**Ventaja:** Mantiene la interfaz consistente con `.empirica()` (ambas retornan `(int, int)`), lo que facilita el cambio en `modelo.py`.

### 3. `sim/modelo.py`

#### Modificación de `correr_dias()`

```python
def correr_dias(self):
    """Un proceso por día: sortea demanda (Monte Carlo) o calcula determinista."""
    for dia in range(1, self.p.dias + 1):
        # --- Demanda: Monte Carlo o determinista según configuración ---
        if self.p.modo_determinista:
            autos, numero = self.az.determinista(self.p.autos_por_dia_fecha(dia))
        else:
            autos, numero = self.az.empirica(self.p.demanda, "demanda")
        
        self.autos_del_dia = autos
        self.tasas_hora = self.p.perfil.tasas_por_hora(autos)
        ...
```

**Cambio mínimo:** Solo reemplaza la línea de muestreo de demanda. El resto del motor (colas, inventario, etc.) funciona igual en ambos modos.

### 4. `app.py`

#### Nuevo expander "📊 Fase 2: Modelo determinista"

```python
with st.sidebar.expander("📊 Fase 2: Modelo determinista", expanded=True):
    modo_determinista = st.checkbox(
        "Usar modelo determinista (sin Monte Carlo)",
        value=False,
        help="..."
    )
    if modo_determinista:
        demanda_base_mensual = st.slider(
            "Demanda base mensual (litros)", 30_000, 300_000, 120_000, 10_000
        )
        horizonte = st.radio(
            "Horizonte de simulación",
            options=["dia", "semana", "mes", "estacion", "anio"],
            format_func=lambda x: {...}[x],
            horizontal=False,
        )
        horizonte_a_dias = {
            "dia": 1, "semana": 7, "mes": 30, "estacion": 90, "anio": 365
        }
        dias_por_horizonte = horizonte_a_dias[horizonte]
    else:
        demanda_base_mensual = 120_000.0
        horizonte = "mes"
        dias_por_horizonte = 30
```

#### Tabla Monte Carlo condicionada

```python
with st.sidebar.expander(
    "🚗 Demanda diaria (tabla Monte Carlo)",
    expanded=(not modo_determinista)
):
    # Solo se muestra si modo_determinista=False
```

#### Sección "Corrida" adaptativa

```python
with st.sidebar.expander("🔬 Corrida"):
    if modo_determinista:
        st.info(f"Horizonte seleccionado: **{dias_por_horizonte} días** ({horizonte})")
        dias = dias_por_horizonte
        dias_calentamiento = 0  # Innecesario en determinismo
        st.caption("(Calentamiento deshabilitado en modo determinista)")
    else:
        dias = st.slider("Días simulados", 7, 90, 30, 1)
        dias_calentamiento = st.slider("Días de calentamiento", 0, 5, 1, 1)
    
    dia_animado = st.slider("Día a animar", 1, min(dias, 90), min(2, int(dias)), 1)
    ...
```

#### `ParametrosSimulacion` construcción actualizada

```python
p = ParametrosSimulacion(
    ...
    dias=int(dias),
    dias_calentamiento=int(dias_calentamiento),
    dia_animado=int(dia_animado),
    modo_determinista=bool(modo_determinista),           # NUEVO
    demanda_base_mensual=float(demanda_base_mensual),   # NUEVO
    horizonte=str(horizonte),                            # NUEVO
)
```

---

## Actualización de Documentación

### `CLAUDE.md`

- Agregada sección "Versión actual: Fase 2 (Octubre 2026)" que explica los tres cambios principales
- Nueva sección "## Fase 2: Determinismo, fuentes verificadas, horizonte variable" con:
  - Explicación de cálculo determinista de demanda
  - Justificación de datos de fuentes verificadas
  - Descripción de opciones de horizonte y su significado
  - Detalles de implementación en cada módulo

### `TASK.md`

- Reestructuración de fases: Fase 3 ahora es "Modelo determinista real (Oct 2026)" con subsecciones:
  - 3.1 Datos consolidados ✅
  - 3.2 Determinismo en demanda ✅
  - 3.3 Horizonte variable ✅
  - 3.4 UI Fase 2 ✅
  - 3.5 Validación de campo (pendiente)
  - 3.6 Análisis de sensibilidad (pendiente)
- Redistribución de fases posteriores (Presentación ahora es Fase 5, Validación es Fase 6)

---

## Comportamiento del Modelo

### Modo Monte Carlo (Fase 1 — por compatibilidad)

```
Toggle OFF (determinista=False)
  ↓
Tabla de demanda Monte Carlo editable en sidebar
  ↓
Cada día: sortea autos de tabla empírica
  ↓
Número aleatorio (01-100) se muestra en pestaña Demanda
```

### Modo "Determinista" (Fase 2 — nombre engañoso; hoy: demanda esperada)

```
Toggle ON (determinista=True)
  ↓
Slider: demanda_base_mensual (30k-300k L)
Radio: horizonte (día, semana, mes, estación, año)
  ↓
Mapeo automático horizonte → días (1/7/30/90/365)
Calentamiento deshabilitado   ❌ FALSO: hoy es de 2 días en todos los modos
  ↓
Cada día (n): autos = base/30 × índice(mes)/promedio   ❌ FALSO: mezcla litros con autos
  ↓
Número aleatorio siempre 50 (determinista)
```

### Ejemplo: Demanda en una simulación de mes

❌ **El ejemplo original era incorrecto** (decía "120.000 L ⇒ 4.000 autos/día = 4.324 autos en enero"; eso
son litros por día tomados como autos). Con la cadena corregida:

```
litros_mes = 270.000 L          horizonte = "mes" (julio, 31 días)
litros/día = 270.000 ÷ 31 × índice del mes (neutro = 1,00) × factor de tipo de día (normalizado)
           ≈ 8.710 L/día
clientes líquidos/día = 8.710 ÷ 35,7 L por cliente ≈ 244   (+ 3 % de clientes GNC ⇒ ≈ 252 llegadas/día)
```

Comprobación (control N16): el motor simula **270.000 L/mes ± 3 %**.

---

## Datos Consolidados

### `DATOS_OPERACIONALES_ESTACION_SHELL_SAN_RAFAEL.md`

Documento de referencia con:
- **40+ parámetros** organizados en 8 secciones
- Cada parámetro incluye:
  - Valor/Rango
  - Unidad
  - Nivel de confianza (Alta/Media/Baja)
  - Fuente declarada con URL (**no verificada** salvo lo marcado en el Registro `sim/datos.py`)
  - Observaciones y supuestos
- **80+ fuentes** consultadas:
  - Secretaría de Energía Argentina
  - FECRA (Federación de Cámaras de Estaciones de Servicio)
  - ENARGAS (Gas Natural)
  - YPF datos de tránsito/micropricing
  - Surtidores.com.ar (datos sector)
  - Papers académicos (UTN, UNLP)
  - SMN (clima)
  - AFAC (parque automotor)
  - Vialidad Nacional (cortes de ruta)

### Parámetros disponibles para Fase 2

| Parámetro | Valor | Confianza | Fuente |
|-----------|-------|-----------|--------|
| Demanda base | 100–150k L/mes (hoy se adopta **270.000**, ver C2) | Baja | Extrapolación Shell nacional |
| Pico mañana | 7:30–10:30 | Alta | YPF micropricing |
| Pico tarde | 16:00–18:00 | Alta | YPF micropricing |
| Estacionalidad enero | 100 (índice) | Media | Ocupación hotelera |
| Estacionalidad junio | 55 (índice) | Baja | Transición + cortes RN |
| Tiempos carga | 5 min (media) | Media | Papers académicos |
| Mix combustibles | Nafta 23%, Diésel 24%+19%, etc. (es el mercado nacional **por volumen**, no el de la estación) | Media | Surtidores.com.ar |
| Parque GNC | 11.2% del parque (los clientes GNC de la estación se adoptan en 3 %, ver C8) | Media | ENARGAS |
| Salarios playero | 1,545,472 ARS básico (≈ 1.680.000 con adicionales); la URL dice enero-2026 | Media | FECRA |

---

## Próximos Pasos (Post-Implementación)

### Fase 3.5: Validación de Campo

**CRÍTICO:** Antes de presentar resultados, validar con el gerente de la estación:

- [ ] Demanda real actual (litros/mes) — comparar con la estimación (hoy 270.000; extremos 150.000 y 400.000)
- [ ] Personal por turno (mañana/tarde/noche) — verificar 5–6 / 5–6 / 2–3
- [ ] Horario exacto de operación (Shell API dice 24 h; DATOS decía 06–22; ver C1)
- [ ] Tipos de diésel disponibles (¿G2 y G3? ¿qué mix?)
- [ ] Tasa de entrada al minimarket (30% es supuesto)
- [ ] Capacidad GNC (¿limitada por compresor en invierno?)

**Método:** Una visita de observación de un día completo (opcional pero recomendado):
- Contar llegadas por hora
- Medir tiempos de carga (5–10 autos)
- Observar entrada al minimarket
- Revisar niveles de tanque
- Fotografiar horarios y tarifas vigentes

### Fase 3.6: Análisis de Sensibilidad

Con datos validados:
- [ ] Variar demanda ±20% (impacto en colas, esperas, quiebres)
- [ ] Variar personal ±1 playero (impacto en laborales y servicio)
- [ ] Simular cortes RN-143/144 (demanda reducida en invierno)
- [ ] Gráficos de tornado (pareto de sensibilidad)

---

## Testing

### Verificar que el código compila

```bash
python -m py_compile app.py sim/config.py sim/distribuciones.py sim/modelo.py
# (sin errores de sintaxis)
```

### Verificar que el simulador corre

```bash
streamlit run app.py
```

Luego en la UI:
1. Toggle "Usar modelo determinista" → ON
2. Ajustar slider "Demanda base mensual" (ej. 120,000)
3. Seleccionar horizonte (ej. "mes")
4. Botón "Correr simulación"
5. Ver que la demanda del día es fija (número aleatorio = 50). ❌ Ojo: las llegadas dentro del día siguen siendo aleatorias

### Verificar que el modo Monte Carlo sigue funcionando

```bash
streamlit run app.py
```

1. Toggle "Usar modelo determinista" → OFF
2. Editar tabla de demanda (mantener por defecto)
3. Botón "Correr simulación"
4. Ver que la demanda varía día a día (números aleatorios 01-100)

---

## Cambios a Documentos de Referencia

### CLAUDE.md

- ✅ Agregada descripción de Fase 2 en introducción
- ✅ Nueva sección "Fase 2: Determinismo, fuentes verificadas, horizonte variable"
- ✅ Actualizada tabla de unidades que dan clase

### TASK.md

- ✅ Agregada Fase 3 con subsecciones de implementación Fase 2
- ✅ Reestructurada numeración de fases posteriores
- ✅ Actualizado estado del proyecto

---

## Conclusión

**Fase 2 implementada completa:** El simulador ahora soporta un modelo determinista de caso real, con datos consolidados desde 80+ fuentes verificadas, y la capacidad de simular períodos de 1 día a 1 año con estacionalidad automática.

El próximo paso es **validar los datos con la estación** para confirmar que las estimaciones son correctas antes de presentar resultados finales al profesor.

---

*Implementación completada: Octubre 5, 2026*
