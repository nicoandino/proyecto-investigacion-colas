# 11 · Eventos aleatorios que alteran la estación (EVT-00 a EVT-15)

Fecha: 14-oct-2026. Lo usan las etapas E1–E3 de la parte 4 (`sim/eventos.py`).

## 1. Qué son y de dónde salen los números

Nico pidió eventos discretos al azar que cambien el funcionamiento de la estación (§20–21 del orquestador). **No hay
registros de la estación** (ni de ausentismo, ni de fallas, ni de cortes de luz): todas las frecuencias y duraciones
son **supuestos del grupo**, rotulados así en el Registro y editables. Donde hay un dato real que respalde el evento
o su efecto, se usa:

| Evento | Respaldo real | Qué se supone |
|---|---|---|
| EVT-02 Licencia con horas extra | **Ley de Contrato de Trabajo, art. 201**: recargo 50 % en días comunes y 100 % el sábado después de las 13, domingos y feriados | La frecuencia (≈ 1 cada 6 meses) y la duración (3–15 días). Simplificación: 50 % de lunes a sábado y 100 % el domingo (feriados no) |
| EVT-10 Faltante con cupo | Faltante de gasoil de 2022 con cupos por carga; crisis de Mendoza de 2023 (Los Andes, INV-09: plazos de 72–96 h durante 3–4 días) | La frecuencia (≈ 1 por año), el cupo de 30 L (pedido de Nico) y que el camión traiga la mitad |
| EVT-13 Evento masivo | DEM-09: Vendimia +30–50 %, Carnaval +40 % (DATOS §6) | Se usa el **piso** (+30 %) y ≈ 4 por año |
| EVT-15 Valor de la hora | Sueldo del playero (ECO-04, con adicionales) | 200 h por mes (8 h × ≈ 25 días) |
| Los demás (abandono, falta, fallas, luz, cobro, avenida, asalto) | — | Frecuencia y duración del grupo |

## 2. Cómo se sortean

- Cada día y para cada evento se sortea **si ocurre** (probabilidad por día del Registro × el multiplicador de
  frecuencia del menú); si ocurre, se sortea la hora, la duración (uniforme entre el mínimo y el máximo) y a quién le
  pasa (un turno con probabilidad proporcional a sus playeros, una cara entre las 12).
- **Semilla propia** (se muestra): con la misma semilla salen los mismos eventos. **Un stream por evento** al final de
  `STREAMS`, y se sortean todos aunque estén apagados: prender o apagar uno no cambia las fechas de los otros.
- El resto de la simulación **no cambia**: con datos reales sigue sin azar (las llegadas, la mezcla y los tiempos).

## 3. Cómo los aplica el motor

| Mecanismo | Eventos | Cómo |
|---|---|---|
| Un playero menos | EVT-01 (hasta el cambio de turno: 06, 14 o 22 h), EVT-03 (un turno), EVT-04 (ese turno, todos los días de la licencia) | Una reserva con prioridad −1 en el recurso de playeros, igual que los turnos |
| Estación parada | EVT-07 corte de luz, EVT-14 asalto | Se reservan todos los playeros y todos los compresores: los que estaban cargando terminan; los que llegan esperan o se van (paciencia TIE-06) |
| Cara fuera de servicio | EVT-05 | Se reserva una cara de la zona y se dibuja tachada |
| Compresor fuera | EVT-06 | Una reserva en el recurso de compresores |
| Cobro lento | EVT-08 | Cada carga tarda 1 min más y la caja × 1,5 |
| Sin cambio de servicio | EVT-02 | Sólo el costo de las horas extra |

A cada evento se le cuentan los **clientes que se fueron sin cargar mientras duraba** (si dos eventos se superponen,
el cliente se le cuenta a los dos).
