# TASK.md — Plan de trabajo

Leyenda: `[ ]` pendiente · `[~]` en progreso · `[x]` hecho

Hito **DEMO** = lo que se muestra mañana en clase.
Hito **FINAL** = entrega completa del TP.

---

## Fase 0 — Setup  ✅ DEMO
- [x] Leer la propuesta y extraer requisitos (`docs/propuesta_...docx`)
- [x] Decidir stack: Python 3.14 + SimPy + Streamlit + Plotly
- [x] Crear `.venv` e instalar dependencias
- [x] Escribir `CLAUDE.md` (contexto) y `TASK.md` (este archivo)
- [x] `requirements.txt` y estructura de carpetas
- [x] Copiar la propuesta a `docs/`

## Fase 1 — Motor de simulación (`sim/`)  ✅ DEMO
- [x] `config.py`: dataclasses `ParametrosSimulacion`, `Escenario`, `ParametrosEconomicos`
- [x] `distribuciones.py`: streams con semilla; Exponencial, Triangular, Bernoulli, Uniforme
- [x] `modelo.py`: proceso de llegadas (Poisson)
- [x] `modelo.py`: recurso surtidores con cola FIFO + servicio Triangular
- [x] `modelo.py`: derivación Bernoulli 30% al minimarket
- [x] `modelo.py`: recurso cajas con cola FIFO + servicio
- [x] `modelo.py`: abandono por umbral de paciencia (surtidor y caja)
- [x] `estadisticas.py`: espera promedio por cola (por cliente)
- [x] `estadisticas.py`: longitud de cola promedio en el tiempo (área/tiempo)
- [x] `estadisticas.py`: utilización de surtidores y cajas (área ocupada / capacidad·tiempo)
- [x] `estadisticas.py`: atendidos, perdidos, tiempo en sistema
- [x] `estadisticas.py`: período de calentamiento (reset de indicadores)
- [x] `runner.py`: correr una réplica → `ResultadoReplica`
- [x] `runner.py`: correr R réplicas → promedio + desvío + IC 95% (t de Student)
- [x] `runner.py`: correr los 4 escenarios con números aleatorios comunes
- [x] `traza.py`: log de eventos → cuadros de animación a Δt fijo
- [x] `economia.py`: ingresos, ventas perdidas, costo incremental, beneficio neto, payback
- [x] `verificar.py`: 12 controles de correctitud del motor (ver Fase 5)

## Fase 2 — UI y animación  ✅ DEMO
- [x] `app.py`: layout general, barra lateral de parámetros, pestañas
- [x] Panel de parámetros: N surtidores, M cajas, tasa de llegada, triangulares, % compra,
      paciencia, duración, calentamiento, réplicas, semilla
- [x] `ui/animacion.py`: estado de la estación → SVG (surtidores, autos en cola, minimarket, caja)
- [x] Reproductor de animación: play / pausa / reiniciar, control de velocidad, reloj de simulación
- [x] Contadores en vivo durante la animación (atendidos, perdidos, en cola)
- [x] Pestaña Indicadores: tarjetas con los 4 indicadores obligatorios
- [x] `ui/graficos.py`: serie de tiempo de longitud de cola
- [x] `ui/graficos.py`: barras comparativas entre escenarios
- [x] Pestaña Escenarios: tabla comparativa Base / A / B / C
- [x] Pestaña Economía: cuadro de inversión, beneficio neto y payback
- [x] Pestaña Conclusión: recomendación generada a partir de los números

## Fase 3 — Cierre del TP  ⬜ FINAL
- [ ] Fijar valores concretos definitivos (tasas, tiempos y costos reales/estimados)
      y documentar de dónde salen — la propuesta lo pide como "próximo paso"
- [ ] Boxplot de la dispersión entre réplicas por escenario
- [ ] Análisis de sensibilidad: barrer la tasa de llegada y ver cuándo se cae cada escenario
- [ ] Exportar resultados a CSV / Excel para pegar en el informe
- [ ] Exportar la tabla comparativa y los gráficos como imagen
- [ ] Redactar la conclusión económica final en el informe

## Fase 4 — Presentación  ✅ DEMO (parcial)
- [x] `README.md` con instrucciones de instalación y uso
- [x] Guion de demo: qué mostrar y en qué orden (5 minutos) — está en el README
- [x] Respuestas a las preguntas probables del profesor — están en el README
      (¿por qué exponencial? ¿por qué warm-up? ¿por qué réplicas? ¿por qué triangular?)
- [ ] Hoja resumen con los supuestos del modelo

## Fase 5 — Validación y verificación  ✅ DEMO (parcial)
Todo esto corre con `.venv/Scripts/python verificar.py` — 12 controles, todos en OK.
- [x] Conservación: llegadas = atendidos + perdidos + los que quedaron adentro
- [x] La misma semilla da exactamente el mismo resultado
- [x] **Ley de Little (L = λ·W)**: la longitud de cola medida por área coincide con la que
      predicen las esperas — diferencia del 0,01 %. Valida entre sí a los dos colectores
      estadísticos (el temporal y el por cliente)
- [x] El tiempo de surtidor ocupado coincide con atendidos × tiempo medio de carga
- [x] La utilización nunca supera el 100%
- [x] Monotonía: más llegadas empeoran la espera; más surtidores la mejoran
- [x] Agregar un cajero no altera en nada a los surtidores: prueba de que los números
      aleatorios comunes están funcionando
- [x] Menos paciencia produce más abandonos
- [ ] Comparar contra **M/M/c teórico** (Lq, Wq, ρ): requiere agregar la opción de carga
      exponencial sólo a los fines de validar

## Fase 6 — Demanda realista + Monte Carlo  ✅ HECHO
Reemplaza el bloque de "hora pico" por un mes de operación real.
- [x] `PerfilHorario`: 24 factores de intensidad (pico mañana, valle mediodía, pico tarde)
- [x] `DemandaDiaria`: tabla de frecuencias empírica de autos por día, editable en la app
- [x] Método Monte Carlo del apunte, los 5 pasos: frecuencias → probabilidad → acumulada →
      intervalos de números aleatorios → sorteo. Los intervalos se muestran en pantalla
- [x] Llegadas no homogéneas: Poisson con λ(t) según la hora, exacto por falta de memoria
- [x] La corrida pasa a ser de N días (30 por defecto), con 1 día de calentamiento
- [x] Indicadores por franja horaria: la hora pico ya no se supone, se descubre
- [x] Animación de un día elegido (no del mes entero)
- [x] Pestaña Demanda: tabla de los 5 pasos, registro día por día, perfil y dispersión

## Fase 7 — Inventario de combustible acoplado  ✅ HECHO
Segundo subsistema, acoplado al de colas: el tanque.
- [x] Litros por carga como variable aleatoria (Triangular)
- [x] Tanque con capacidad, nivel inicial y consumo por cada carga
- [x] Política (s, Q) sobre la posición de inventario (existencia + lo que viene en camino)
- [x] Camión cisterna con **plazo de entrega estocástico**
- [x] Quiebre de stock: sin combustible no se atiende a nadie hasta que llega el camión
- [x] Indicadores: nivel de servicio, días con quiebre, litros no vendidos, pedidos,
      nivel promedio y mínimo del tanque, tiempo sin combustible
- [x] Costos de inventario: flete por pedido + almacenamiento + venta perdida
- [x] Pestaña Inventario: gráfico de dientes de sierra del nivel del tanque
- [x] Barrido de políticas: grilla s × Q → costo total mensual, con la mejor destacada
- [x] Botón "Usar esta política" para llevarla a la configuración
- [x] El margen pasa a ser **por litro** (antes era por carga)
- [x] El tanque aparece en la animación, con el punto de pedido y el camión en viaje
- [x] Verificación: conservación de litros (exacta), tanque nunca negativo ni sobre capacidad
- [x] La conclusión compara las DOS decisiones (capacidad vs. reposición) en $/mes

---

## Decisiones tomadas
- **No usamos Simul8**: desarrollamos el simulador propio (pedido del alumno).
- **No escalable a propósito**: sin base de datos, sin API, sin login. Ver `CLAUDE.md` § Alcance.
- Unidad de tiempo **minutos**, moneda **pesos**, en todo el proyecto.
- El motor (`sim/`) no depende de Streamlit: se puede correr sin UI.
- Los resultados se reportan con **IC 95% sobre réplicas**, nunca con una sola corrida.
- **Un solo producto** (nafta súper): varios combustibles multiplican tanques sin cambiar
  la naturaleza del problema.
- **Día completo de 24 h** y corrida de 30 días: la economía sale en $/mes sin extrapolar.
- La animación se dibuja en JavaScript del lado del cliente (ver `CLAUDE.md`).

## Pendiente de definir con el profesor / el grupo
- [ ] Valores reales de costos: ¿cuánto sale instalar un surtidor? ¿sueldo del cajero?
- [ ] Margen de ganancia por carga de combustible y por compra en el minimarket
- [ ] Duración de la hora pico y cuántos días al mes se considera
- [ ] ¿El abandono se modela solo en el surtidor o también en la caja? (hoy: en ambos, configurable)
- [ ] **Confirmar con el profesor que acepta un simulador propio** en lugar de Simul8/FlexSim
- [ ] Datos reales para la tabla de frecuencias de demanda diaria
- [ ] Costo real del flete del camión y del capital inmovilizado en combustible
