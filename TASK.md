# TASK.md — Qué está hecho y qué falta

Leyenda: `[x]` hecho · `[ ]` pendiente. **Versión final de la Fase 10 (6/10/2026).** Reemplaza al plan
anterior, que describía el simulador hipotético (un solo producto, Fase 2 "determinista", etc.).

La especificación y los controles están en `ORQUESTADOR_SIMULADOR.md`; el cierre detallado de cada
fase (qué se hizo, compuerta, resultados y deuda) está en su **§9**.

---

## Lo hecho (fases 0–10 del orquestador, un commit por fase)

### Fase 0 — Corregir la Fase 2 heredada
- [x] Demanda desde **litros/mes ÷ litros medios por cliente** (se acabó "litros = autos"; control N16: 270.000 L/mes ⇒ 270.000 ± 3 %)
- [x] Calendario real con `fecha_inicio` (un solo mapa horizonte → fecha y días), "determinista" → "demanda esperada", calentamiento de 2 días, réplicas e IC se mantienen
- [x] `clasico()` reproduce los **números dorados** (control N1)

### Fase 1 — Registro de datos y tema Shell
- [x] `sim/datos.py`: Registro con valor, unidad, fuente, nivel, tipo, confianza y alternativas; 20 contradicciones (C1–C20); N14 "cero huérfanos"
- [x] `ui/tema.py`: paleta Shell única, plantilla Plotly, CSS; N15 (ningún hex fuera del tema, contraste WCAG)
- [x] Insignias por dato (🟢 dato · 🟡 estimación · 🔵 observación · 🟠 supuesto · ⚪ heredado), pestaña **Datos y fuentes** con filtros y CSV

### Fase 2 — Núcleo del motor real
- [x] 3 zonas de caras (12), 5 productos con "producto primero", playeros por turno, cola finita, GNC sin tanque
- [x] Conservación por grupo y motivo (N2), Little por grupo (N4), playeros ≤ turno y ≤ caras (N5)

### Fase 3 — Animación del playón
- [x] Zonas, playeros, cola que desborda a la avenida, minimarket, tanques por producto, camión en ruta, GNC; saltos (hora pico, quiebre, descarga, corte)

### Fase 4 — Política de reposición por producto
- [x] Barrido de (s, Q) de los 4 tanques a la vez (13 puntos), mejor política por tanque, "Usar las mejores políticas"

### Fase 5 — Red de abastecimiento
- [x] Dijkstra (`heapq`), cortes E1–E4 y sorteados, demora → plazo; pestaña **Red y rutas** (N6: 221,8 km / 399,8 km con RN 143 cortada)

### Fase 6 — GNC
- [x] Episodios de corte total en jun–ago, 3 compresores, migración a Súper o pérdida (`corte_gnc`); pestaña **GNC** con los episodios sombreados (N7, N8)

### Fase 7 — Estaciones del año y escenarios S0–S12
- [x] `correr_estaciones` (ene·abr·jul·oct) y catálogo S0, S2–S12 con números aleatorios comunes y **diferencias pareadas** con IC 95 % (N12)

### Fase 8 — Economía real
- [x] Estado de resultados mensual (ingresos − costos = margen), personal desde la dotación, flete = fijo + $/km, año estimado (ECO-09), decisión en $/mes por escenario y S6; la venta perdida no se resta

### Fase 9 — Sensibilidad
- [x] Tornado: 26 ejes y 56 variantes (cada contradicción con valores alternativos + datos con rango); listado de **todos** los supuesto/heredado/estimación

### Fase 10 — Verificación final y documentación
- [x] `verificar.py` 100/100 · QA visual completo de las 14 pestañas (escritorio y celular) y de la animación en 3 instantes · rendimiento medido
- [x] `CLAUDE.md`, `TASK.md`, `README.md`, `ONBOARDING_PARA_AGENTES.md` reescritos; `FASE2_IMPLEMENTACION.md` y `DATOS_OPERACIONALES…md` corregidos (fe de erratas)
- [x] Criterios D0–D11 con su evidencia (`ORQUESTADOR_SIMULADOR.md` §9, cierre de la Fase 10)

---

## Lo que falta (en orden de impacto)

### Datos de la propia estación (lo único que cambia las conclusiones)
Hoy **todo es estimación o supuesto**. Orden de prioridad (detalle en `ORQUESTADOR §12`):
- [ ] **Demanda real:** litros/mes por producto (última facturación) y conteo de clientes por franja, un día hábil y uno de fin de semana — cierra C2, C3, C7, C16, C17
- [ ] **Dotación por turno** (playeros, cajeros, encargado), horario real de la playa y del shop, ¿autoservicio? — cierra C1, C5, C15
- [ ] **Litros por carga y tiempo en la cara**, cronometrando 5–10 vehículos por producto — cierra C11, C12
- [ ] **GNC:** contrato (firme o interrumpible), compresores, cortes de los últimos inviernos, migración a nafta — cierra C8, C9
- [ ] **Economía:** margen por litro y por compra, flete real por km (el de $150.000 es implausible), sueldos vigentes — cierra C18 y ECO-*
- [ ] **Mix diésel G2/G3** y % de clientes que entran al shop — cierra C4, C6
- [ ] **Estacionalidad real:** ventas mensuales de la Secretaría de Energía — cierra C10

### Para el informe del TP
- [ ] Redactar la conclusión con los números del simulador (`reports/qa/` tiene capturas de cada pestaña)
- [ ] Exportar tablas y gráficos que se quieran pegar en el informe
- [ ] Confirmar con el profesor que acepta el simulador propio en lugar de Simul8/FlexSim

### Deuda técnica conocida (no bloquea la entrega)
- [ ] **Anulación por relevamiento:** poder pisar un `Dato` desde la app o un CSV (⇒ tipo `observacion`) — hoy el Registro se exporta pero no se importa
- [ ] Botón **Verificación** dentro de la app que corra los controles (hoy se corren con `python verificar.py`)
- [ ] Camión **consolidado** (un viaje con varios productos y un solo flete; N2 etapa 2)
- [ ] Quienes ya esperan en la cola del GNC cuando empieza el corte **no migran** (se pierden)
- [ ] Margen por litro **igual para todos los productos** (no distingue Súper de V-Power ni diésel)
- [ ] El tornado es de **un solo mes** y varía **un eje por vez** (sin interacciones)
- [ ] Comparación contra **M/M/c teórico** (control N13, opcional)
- [ ] La app tiene **14 pestañas** (el orquestador proponía ≤ 7 con sub-pestañas); hay que decidir si se agrupan

## Decisiones tomadas
- **No usamos Simul8:** motor propio (pedido del grupo).
- **No escalable a propósito:** sin base de datos, login, API ni Docker. Ver `CLAUDE.md` § Alcance.
- **Unidades:** minutos, pesos, litros (m³ para el GNC). El motor (`sim/`) no depende de Streamlit.
- Resultados con **IC 95 % sobre réplicas**, nunca una sola corrida; comparaciones con **números aleatorios comunes**.
- Un **commit por fase**, en castellano, en la rama `claude/simulator-graphic-orchestrator-wu2xh4`, **sin Pull Request**.
