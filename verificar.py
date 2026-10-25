"""Verificación del motor de simulación.

Antes de sacar conclusiones hay que demostrar que el simulador está bien hecho. Este
script corre controles que no dependen de la interfaz y avisa si alguno falla.

    .venv/Scripts/python verificar.py

Los controles cubren las dos partes del modelo:

  COLAS
    1. Reproducibilidad: misma semilla, mismo resultado.
    2. Conservación de clientes: todo el que llega, o carga, o se va, o está adentro.
    3. Ley de Little (L = λ·W): relación que cumple cualquier sistema de colas, sin
       importar las distribuciones. Valida entre sí a los dos colectores estadísticos.
    4. Utilización coherente con el servicio efectivamente entregado.
    5. Monotonía: más autos empeoran la espera, más surtidores la mejoran.

  MONTE CARLO Y DEMANDA
    6. La demanda simulada reproduce la tabla de frecuencias empírica.
    7. Las llegadas siguen el perfil horario cargado.

  INVENTARIO
    8. Conservación de litros: lo que entró menos lo que salió es lo que queda.
    9. El tanque nunca queda negativo ni pasa de su capacidad.
   10. Subir el punto de pedido reduce los quiebres de stock.

  FASE 0 DEL ORQUESTADOR (ORQUESTADOR_SIMULADOR.md §10.2)
   11. N1: el caso clásico reproduce los números dorados de §14.1.
   12. N16: unidades de la demanda (270.000 L/mes ⇒ 270.000 ± 3 % simulados).
   13. N17/N18: calendario real (invierno = jun–ago, julio ≠ enero, día de la
       semana) y normalización del fin de semana (§14.4).

  FASE 1 DEL ORQUESTADOR
   14. N14: cero parámetros huérfanos (todo campo tiene su Dato en el Registro).
   15. N15: tema Shell (ningún hex fuera de ui/tema.py, contraste WCAG ≥ 4,5,
       los 5 colores de PRODUCTO distinguibles).

  FASE 2 DEL ORQUESTADOR (estación real: grupos, producto primero, playeros)
   (N3, la conservación por producto, está dentro del control 8.)
   El modelo REAL es el default de `ParametrosSimulacion()`. Los controles 1–4, 7 y 8
   corren sobre él; los 5, 6 y 9 (monotonía, tabla Monte Carlo absoluta y política de
   tanque único) corren sobre `clasico()`, el caso degenerado de §10.1.
   16. N2: conservación por grupo y por motivo de pérdida (dentro del control 2).
   17. N4: Little por grupo (control 3b).
   18. N5: playeros ≤ turno y ≤ caras (control 4b, con traza).
   19. N9: mezcla de producto en litros ≈ DEM-04 y clientes GNC ≈ 3 %.
   20. N10: media muestral de litros por tipo de vehículo.

  FASE 3 DEL ORQUESTADOR (animación)
   21. Los cuadros de la animación (carriles, cola, camión) coinciden con el motor y el
       HTML del reproductor pesa menos de 3 MB.

  FASE 4 DEL ORQUESTADOR (política por producto)
   22. Grilla válida, monotonía de s (N11), independencia entre tanques y barrido que
       encuentra una política ≤ a la cargada en cada tanque.

   47. Economía: el estado de resultados (ventas − compras − fletes, sueldos y almacenamiento) da el margen
       operativo, y con el margen de equilibrio el resultado es 0.
   49. Fórmulas de colas (M/M/1, M/M/s, costos) y la tabla de errores del pronóstico contra la cátedra;
       la inflación de PRO-05 y los clientes por mes de la corrida.
   48. EVT-05: la falla de un surtidor tacha sus dos caras (pedido de Nico, 14/10/2026).
   46. Valores por defecto de la app: índices de la serie real y la política INV-13, que es la más
       barata de las 14 candidatas en el año completo con datos reales.
   45. §24, G1: la tabla de camiones tiene un camión por pedido y la ruta recorrida se reconstruye
       (desvío o espera).
   41. Parte 3, etapa P4: el punto de pedido por pronóstico (s = D·L + z·σ·√L) a mano, con z = 0
       la demanda del plazo, y la opción del menú lo usa.
   40. Parte 3, etapa P3: con los índices de la serie real el año tiene los mismos litros, repartidos
       por mes según su índice; sin tocar el menú sigue el calendario de temporadas.
   39. Parte 3, etapa P2: métodos de pronóstico contra el práctico (Cable Televisora, Lincoln) y
       elección por RMSE en la serie real de Shell Mendoza.
   38. Parte 4, etapa E3: el menú sin eventos deja la corrida del Registro; con eventos, cada uno es
       un aviso del tablero.
   37. Parte 4, etapa E2: llegadas = base + los de más − los que no llegaron; cupo de 30 L; camiones
       con la mitad y plazo de crisis; roturas de 12–48 h; costo de las horas extra calculado a mano.
   36. Parte 4, etapa E1: eventos de personal y equipos (mismo calendario con la misma semilla,
       prender uno no corre a los otros, cada mecanismo hace lo que dice, conservación de clientes).
   35. Parte 4, etapa E0: el GNC lo carga un playero (autos cargando = playeros ocupados en cada
       cuadro; ρ con los minutos del GNC; el autoservicio queda como alternativa).

   32. Etapa 4: los totales enteros cierran por zona, producto, hora y día, y el tiempo sin
       combustible por tanque es coherente con los días de quiebre.

   31. Etapa 3: capacidad de cola de 3 lugares por cara, la cola no la supera, el tablero graba todos
       los días, litros por producto coherentes con el motor y peso del año completo.

   30. Etapa 2: períodos del menú (días, meses, estaciones, año), cortes de GNC según el
       período, ediciones (demanda, doble pico, GNC, playeros) y precio por litro.

   29. Etapa 1: simulación con datos reales sin azar (mismo resultado con cualquier semilla,
       llegadas y mezcla exactas, camión = plazo medio, GNC con fechas fijas, animación de todos los días).

  FASE 10 DEL ORQUESTADOR (cierre)
   28. N19: clientes líquidos × litros medios por cliente = litros del día, y los litros medios
       por cliente salen de la mezcla y las cargas de cada producto.

  FASE 9 DEL ORQUESTADOR (sensibilidad)
   27. El listado cubre todos los supuesto/heredado/estimación y las 20 contradicciones, la
       cadena de demanda sobrevive a cambiar vehículos o mezcla, el tornado es coherente
       (demanda, playeros, francos), los ejes económicos son lineales y el ranking cambia
       según la métrica.

  FASE 8 DEL ORQUESTADOR (economía real)
   26. Ingresos − costos = margen (y contra un cálculo independiente), la venta perdida no se
       resta, personal desde la dotación (S2/S9), flete = fijo + $/km × km, anualización
       3 × Σ de los 4 meses y margen por litro de equilibrio.

  FASE 7 DEL ORQUESTADOR (estaciones del año y escenarios S0–S12)
   25. N12 con las 4 estaciones (invierno > verano), 4 estaciones × 4 réplicas ≤ 90 s,
       calendario real, litros del mes, quincena normalizada (N18), catálogo S0–S12 con
       cierre de clientes (N2), refuerzo de playeros (N5), N11 con S2, diferencias pareadas,
       crisis de abastecimiento (S7) y cierre nocturno (S10).

  FASE 6 DEL ORQUESTADOR (GNC)
   24. N7 (sin episodios no hay pérdidas; corte total sin migración pierde a todos), N8
       (migrados + perdidos = afectados), N12 (invierno > verano), formas del corte y
       compresores como límite de las cargas simultáneas.

  FASE 5 DEL ORQUESTADOR (red de rutas)
   23. N6 (km y minutos de §5-G), Dijkstra = fuerza bruta, demora por corte, la red sin
       cortes no cambia nada y N11 (cortes, playeros y demanda).

  PARTE 2 DEL ORQUESTADOR (pulido en tandas)
   29. Tanda 3: las causas de los litros no vendidos suman lo que no se vendió; las horas de
       cada quiebre suman el tiempo sin combustible del tanque.
"""

from __future__ import annotations

from dataclasses import replace

from sim.config import (
    ESTACIONALIDAD_PROXY,
    MINUTOS_POR_DIA,
    ParametrosSimulacion,
    dias_y_fecha,
)
from sim.estadisticas import capacidad_total, nivel_inicial_total
from sim.modelo import simular
from sim.runner import con_politica, correr_escenarios, correr_replica

VERDE = "OK  "
ROJO = "FALLA"

_fallas = 0
_total = 0


def controlar(condicion: bool, titulo: str, detalle: str = "") -> None:
    global _fallas, _total
    _total += 1
    if not condicion:
        _fallas += 1
    print(f"  [{VERDE if condicion else ROJO}] {titulo}")
    if detalle:
        print(f"           {detalle}")


def separador(titulo: str) -> None:
    print(f"\n{titulo}")
    print("-" * len(titulo))


def main() -> int:
    p = ParametrosSimulacion()

    # ------------------------------------------------------------------ 1
    separador("1. Reproducibilidad")
    r1, _ = correr_replica(p, semilla=7)
    r2, _ = correr_replica(p, semilla=7)
    r3, _ = correr_replica(p, semilla=8)
    controlar(r1 == r2, "La misma semilla da exactamente el mismo resultado")
    controlar(
        r1 != r3,
        "Semillas distintas dan resultados distintos",
        f"semilla 7: espera {r1.espera_surtidor:.3f} min | "
        f"semilla 8: espera {r3.espera_surtidor:.3f} min",
    )

    # ------------------------------------------------------------------ 2
    separador("2. Conservación de clientes (por estación, por grupo y por motivo: N2)")
    ind, _ = simular(p, semilla=11)
    t = ind.c_total
    perdidos = (
        t.perdidos_surtidor + t.perdidos_sin_combustible + t.perdidos_cola_llena
        + t.perdidos_corte_gnc
    )
    salidas = t.atendidos_surtidor + perdidos
    en_sistema = t.llegadas - salidas
    caras_total = sum(g.caras for g in p.grupos)
    holgura = caras_total + sum(p.capacidad_de(g.id) or 0 for g in p.grupos)
    controlar(
        0 <= en_sistema <= holgura,
        "Llegadas = atendidos + Σ perdidos (por motivo) + los que quedaron adentro",
        f"{t.llegadas} = {t.atendidos_surtidor} + {t.perdidos_surtidor} (espera) + "
        f"{t.perdidos_sin_combustible} (sin combustible) + {t.perdidos_cola_llena} "
        f"(cola llena) + {en_sistema} adentro",
    )
    peor_grupo = ""
    grupos_bien = True
    suma_llegadas = 0
    for g in p.grupos:
        cg = ind.c_grupo_total[g.id]
        suma_llegadas += cg.llegadas
        adentro = cg.llegadas - (
            cg.atendidos + cg.perdidos_espera + cg.perdidos_cola_llena
            + cg.perdidos_sin_combustible + cg.perdidos_corte_gnc
        )
        if not 0 <= adentro <= g.caras + (p.capacidad_de(g.id) or 0):
            grupos_bien = False
            peor_grupo = f"{g.id}: {adentro} adentro"
    controlar(
        grupos_bien and suma_llegadas == t.llegadas,
        "N2: en cada grupo (A, B, C) llegadas = atendidos + perdidos por motivo + adentro",
        "los tres grupos cierran y suman las llegadas de la estación"
        + (f" | falla {peor_grupo}" if peor_grupo else ""),
    )
    suma_producto = sum(ind.c_producto_total[pr].llegadas for pr in ind.c_producto_total)
    controlar(
        suma_producto == t.llegadas,
        "N2: cada cliente que llega tiene exactamente un producto",
        f"Σ llegadas por producto = {suma_producto} | llegadas = {t.llegadas}",
    )
    controlar(
        t.compras_atendidas + t.perdidos_caja <= t.entraron_minimarket <= t.atendidos_surtidor,
        "Al minimarket no entra nadie que no haya cargado",
        f"atendidos {t.atendidos_surtidor}, entraron {t.entraron_minimarket}, "
        f"cobrados {t.compras_atendidas}, abandonos {t.perdidos_caja}",
    )

    # ------------------------------------------------------------------ 3
    separador("3. Ley de Little (L = lambda * W) en la cola de las caras (N4: por grupo)")
    p_largo = replace(p, dias=60, dias_calentamiento=2)
    ind, _ = simular(p_largo, semilla=13)
    periodo = (p_largo.dias - p_largo.dias_calentamiento) * MINUTOS_POR_DIA

    # Tiempo total de espera acumulado por todos los que hicieron cola por una cara: los
    # que llegaron a la cara esperaron lo que registró el colector (`espera_cara`) y los
    # que abandonaron en la cola esperaron exactamente su paciencia. Los que se fueron
    # esperando al playero ya habían tenido cara (están en `espera_cara`), y los que se
    # fueron por falta de combustible o cola llena nunca hicieron cola.
    abandonos_en_cola = ind.c.perdidos_surtidor - ind.c.abandonos_playero
    espera_total = ind.espera_cara.suma + abandonos_en_cola * p_largo.paciencia_surtidor
    lq_por_little = espera_total / periodo
    lq_medido = ind.cola_surtidor.promedio
    error = abs(lq_medido - lq_por_little) / max(lq_por_little, 1e-9)
    controlar(
        error < 0.05,
        "La cola promedio medida por área coincide con la que predice Little",
        f"medida {lq_medido:.4f} autos | Little {lq_por_little:.4f} autos | "
        f"diferencia {error * 100:.2f} %",
    )
    for g in p_largo.grupos:
        cg = ind.c_grupo[g.id]
        espera_g = ind.esperas_cara_grupo[g.id].suma + (
            cg.perdidos_espera - cg.abandonos_playero
        ) * p_largo.paciencia_surtidor
        lq_little = espera_g / periodo
        lq_med = ind.colas_grupo[g.id].promedio
        tolerancia = max(0.05 * lq_little, 0.005)
        controlar(
            abs(lq_med - lq_little) <= tolerancia,
            f"N4: Little en el grupo {g.id} ({g.nombre})",
            f"medida {lq_med:.4f} autos | Little {lq_little:.4f} autos",
        )

    # ------------------------------------------------------------------ 4
    separador("4. Utilización y playeros (N5)")
    controlar(
        0.0 <= ind.utilizacion_surtidores <= 1.0,
        "La utilización de las caras está entre 0 % y 100 %",
        f"{ind.utilizacion_surtidores * 100:.2f} %",
    )
    trabajo_esperado = ind.servicio_suma
    trabajo_medido = ind.ocupados_surtidores.promedio * periodo
    error_trabajo = abs(trabajo_medido - trabajo_esperado) / trabajo_esperado
    controlar(
        error_trabajo < 0.05,
        "El tiempo de cara ocupada coincide con la suma de los tiempos de carga atendidos",
        f"medido {trabajo_medido:,.0f} min | esperado {trabajo_esperado:,.0f} min | "
        f"diferencia {error_trabajo * 100:.2f} %",
    )

    # N5: simultáneos en servicio ≤ playeros del turno y ≤ caras. Se muestrea con la
    # traza (un día entero, un cuadro cada 0,5 min). Cuando baja la dotación, quien ya
    # está en servicio no se expulsa (trampa 13): la capacidad se ajusta al liberarse,
    # así que los primeros minutos después de un borde de turno no cuentan.
    p_traza = replace(p, dias=4, dias_calentamiento=2, dia_animado=3)
    ind_t, traza = simular(p_traza, semilla=19, con_traza=True)
    bordes = [hora * 60.0 for hora, _ in p_traza.turnos]
    margen_borde = 30.0

    def lejos_de_un_borde(minuto: float) -> bool:
        return all(((minuto - b) % MINUTOS_POR_DIA) >= margen_borde for b in bordes)

    sobrepasa = [
        c for c in traza.cuadros
        if lejos_de_un_borde(c.minuto_del_dia) and c.playeros_ocupados > c.playeros_en_turno
    ]
    maximo_playeros = max(c.playeros_ocupados for c in traza.cuadros)
    controlar(
        not sobrepasa and maximo_playeros <= max(p.playeros_por_turno),
        "N5: los playeros en servicio nunca superan los del turno (ni la dotación máxima)",
        f"{len(traza.cuadros):,} cuadros muestreados | máximo simultáneo {maximo_playeros} | "
        f"cuadros en falta: {len(sobrepasa)}",
    )
    caras_ok = all(
        ind_t.ocupados_grupo[g.id].maximo <= g.caras + 1e-9 for g in p.grupos
    )
    controlar(
        caras_ok,
        "N5: nunca hay más autos cargando que caras en cada grupo",
        " · ".join(
            f"{g.id}: máx {ind_t.ocupados_grupo[g.id].maximo:.0f} de {g.caras}"
            for g in p.grupos
        ),
    )
    en_turno = [c.playeros_en_turno for c in traza.cuadros]
    controlar(
        min(en_turno) == min(p.playeros_por_turno) and max(en_turno) == max(p.playeros_por_turno),
        "Los turnos se repiten todos los días (la dotación sube y baja con el reloj)",
        f"playeros en turno observados en el día graficado: {sorted(set(en_turno))}",
    )

    # ------------------------------------------------------------------ 5
    separador("5. Monotonía (el modelo reacciona como corresponde) — caso clásico")
    clasico = ParametrosSimulacion.clasico()
    escenarios = correr_escenarios(clasico, replicas=3, semilla_base=1)
    base, con_surtidor, con_cajero = escenarios[0], escenarios[1], escenarios[2]
    controlar(
        con_surtidor.prom("espera_pico") < base.prom("espera_pico"),
        "Agregar un surtidor reduce la espera de la hora pico",
        f"Base {base.prom('espera_pico'):.2f} min | A {con_surtidor.prom('espera_pico'):.2f} min",
    )
    controlar(
        con_surtidor.prom("util_surtidores") < base.prom("util_surtidores"),
        "Agregar un surtidor baja la utilización de cada uno",
        f"Base {base.prom('util_surtidores') * 100:.1f} % | "
        f"A {con_surtidor.prom('util_surtidores') * 100:.1f} %",
    )
    controlar(
        abs(con_cajero.prom("espera_surtidor") - base.prom("espera_surtidor")) < 1e-9,
        "Agregar un cajero NO cambia nada en los surtidores (números aleatorios comunes)",
        "el minimarket no bloquea al surtidor, así que tiene que dar idéntico",
    )
    controlar(
        con_cajero.prom("espera_caja") < base.prom("espera_caja"),
        "Agregar un cajero sí reduce la espera en la caja",
        f"Base {base.prom('espera_caja'):.2f} min | B {con_cajero.prom('espera_caja'):.2f} min",
    )

    # ------------------------------------------------------------------ 6
    separador("6. Monte Carlo: la demanda sorteada respeta la tabla empírica — caso clásico")
    p_muchos = replace(clasico, dias=400, dias_calentamiento=1)
    _, traza = correr_replica(p_muchos, semilla=5, con_traza=True)
    sorteos = [d.autos_sorteados for d in traza.dias]
    media_simulada = sum(sorteos) / len(sorteos)
    error_media = abs(media_simulada - clasico.demanda.media) / clasico.demanda.media
    controlar(
        error_media < 0.03,
        "La media de la demanda sorteada coincide con la de la tabla",
        f"simulada {media_simulada:.1f} autos/día | tabla {clasico.demanda.media:.1f} | "
        f"diferencia {error_media * 100:.2f} % ({len(sorteos)} días)",
    )
    peor = 0.0
    for valor, probabilidad in zip(clasico.demanda.valores, clasico.demanda.probabilidades):
        observada = sorteos.count(valor) / len(sorteos)
        peor = max(peor, abs(observada - probabilidad))
    controlar(
        peor < 0.05,
        "Cada valor de la tabla sale con la frecuencia que le corresponde",
        f"la mayor diferencia entre probabilidad observada y teórica es {peor * 100:.2f} puntos",
    )

    # En la estación real el Monte Carlo sortea un FACTOR RELATIVO (DEM-07) que multiplica
    # los litros del día derivados de los litros/mes: su media es 1, así que el mes sigue
    # sumando litros_mes.
    p_mc = replace(
        p, modo_demanda="monte_carlo", dias=150, dias_calentamiento=2, fecha_inicio=(1, 1)
    )
    _, traza_mc = correr_replica(p_mc, semilla=5, con_traza=True)
    cocientes = []
    for d in traza_mc.dias:
        esperado = p_mc.litros_del_dia(d.dia) / p_mc.litros_medios_por_cliente / (
            1.0 - p_mc.pct_gnc
        )
        cocientes.append(d.autos_sorteados / esperado)
    media_factor = sum(cocientes) / len(cocientes)
    controlar(
        abs(media_factor - 1.0) < 0.03,
        "Monte Carlo real: el factor relativo sorteado tiene media 1 (conserva los litros)",
        f"media de autos sorteados / autos esperados = {media_factor:.3f} ({len(cocientes)} días)",
    )

    # ------------------------------------------------------------------ 7
    separador("7. Las llegadas siguen el perfil horario")
    ind_perfil, _ = simular(replace(p, dias=90, dias_calentamiento=1), semilla=17)
    llegadas = ind_perfil.por_hora.llegadas
    total = sum(llegadas)
    desvio_maximo = max(
        abs(llegadas[h] / total - p.perfil.fracciones[h]) for h in range(24)
    )
    controlar(
        desvio_maximo < 0.01,
        "La proporción de llegadas de cada hora coincide con el perfil cargado",
        f"mayor desvío: {desvio_maximo * 100:.2f} puntos porcentuales sobre {total:,} autos",
    )
    hora_mas_cargada = llegadas.index(max(llegadas))
    picos = {
        h for h, f in enumerate(p.perfil.factores) if f == p.perfil.factor_maximo
    }
    controlar(
        hora_mas_cargada in picos,
        "La hora con más llegadas es una de las horas pico del perfil",
        f"simulada: {hora_mas_cargada}:00 | horas pico del perfil: {sorted(picos)}",
    )

    # ------------------------------------------------------------------ 8
    separador("8. Inventario: conservación de litros (N3: un tanque por producto líquido)")
    ind_inv, _ = simular(p, semilla=23)
    t = ind_inv.c_total
    inicial = nivel_inicial_total(p)
    capacidad = capacidad_total(p)
    esperado = inicial + t.litros_recibidos - t.litros_vendidos
    diferencia = abs(ind_inv.nivel_tanque.valor - esperado)
    controlar(
        diferencia < 1.0,
        "Nivel final = nivel inicial + litros recibidos - litros vendidos (toda la estación)",
        f"{ind_inv.nivel_tanque.valor:,.1f} L medidos vs {esperado:,.1f} L calculados "
        f"(recibidos {t.litros_recibidos:,.0f} L, vendidos {t.litros_vendidos:,.0f} L)",
    )
    peor_tanque = 0.0
    for inv in p.inventario:
        cp = ind_inv.c_producto_total[inv.producto]
        esperado_p = inv.nivel_inicial + cp.litros_recibidos - cp.litros_vendidos
        peor_tanque = max(peor_tanque, abs(ind_inv.niveles[inv.producto].valor - esperado_p))
    controlar(
        peor_tanque < 1.0,
        "La conservación también cierra en cada tanque por separado",
        f"peor diferencia entre los {len(p.inventario)} tanques: {peor_tanque:.2e} L",
    )
    liquidos_por_producto = sum(
        ind_inv.c_producto_total[inv.producto].litros_vendidos for inv in p.inventario
    )
    gnc = ind_inv.c_producto_total["gnc"]
    m3_por_cliente = gnc.litros_vendidos / max(gnc.atendidos, 1)
    controlar(
        abs(liquidos_por_producto - t.litros_vendidos) < 1e-6
        and abs(m3_por_cliente - 7.0) / 7.0 < 0.05,
        "N3: los m³ del GNC no se mezclan con los litros (≈ 7 m³ por cliente GNC)",
        f"Σ litros de los 4 líquidos = {liquidos_por_producto:,.0f} L = litros vendidos "
        f"de la estación | GNC: {gnc.litros_vendidos:,.0f} m³ en {gnc.atendidos} cargas "
        f"({m3_por_cliente:.2f} m³ c/u)",
    )
    controlar(
        ind_inv.nivel_tanque.minimo >= -1e-6
        and all(s.minimo >= -1e-6 for s in ind_inv.niveles.values()),
        "Ningún tanque queda en negativo",
        f"nivel mínimo de la estación: {ind_inv.nivel_tanque.minimo:,.1f} L",
    )
    controlar(
        ind_inv.nivel_tanque.maximo <= capacidad + 1e-6
        and all(
            ind_inv.niveles[inv.producto].maximo <= inv.capacidad + 1e-6
            for inv in p.inventario
        ),
        "Ningún tanque supera su capacidad",
        f"nivel máximo de la estación: {ind_inv.nivel_tanque.maximo:,.1f} L de "
        f"{capacidad:,.0f} L",
    )
    controlar(
        0.0 <= ind_inv.nivel_servicio <= 1.0,
        "El nivel de servicio está entre 0 % y 100 %",
        f"{ind_inv.nivel_servicio * 100:.2f} %",
    )

    # ------------------------------------------------------------------ 9
    separador("9. Inventario: la política hace lo que tiene que hacer — caso clásico")
    tacaña, _ = correr_replica(con_politica(clasico, 4_000, 20_000), semilla=29)
    generosa, _ = correr_replica(con_politica(clasico, 20_000, 20_000), semilla=29)
    controlar(
        tacaña.porcentaje_dias_quiebre > generosa.porcentaje_dias_quiebre,
        "Con un punto de pedido más alto hay menos días con quiebre de stock",
        f"punto 4.000 L: {tacaña.porcentaje_dias_quiebre:.1f} % de los días | "
        f"punto 20.000 L: {generosa.porcentaje_dias_quiebre:.1f} %",
    )
    controlar(
        generosa.nivel_tanque_promedio > tacaña.nivel_tanque_promedio,
        "Pedir antes deja más combustible inmovilizado (el costo de la seguridad)",
        f"punto 4.000 L: {tacaña.nivel_tanque_promedio:,.0f} L promedio | "
        f"punto 20.000 L: {generosa.nivel_tanque_promedio:,.0f} L",
    )
    chico, _ = correr_replica(con_politica(clasico, 12_000, 10_000), semilla=29)
    grande, _ = correr_replica(con_politica(clasico, 12_000, 30_000), semilla=29)
    controlar(
        chico.pedidos_dia > grande.pedidos_dia,
        "Pedir de a poco obliga a pedir más seguido (más fletes)",
        f"pedidos de 10.000 L: {chico.pedidos_dia * 30:.1f} pedidos/mes | "
        f"de 30.000 L: {grande.pedidos_dia * 30:.1f} pedidos/mes",
    )

    # ------------------------------------------------------------------ 10
    separador("10. N1: el caso clásico reproduce los números dorados (§14.1)")
    # Los dorados se midieron sobre la rama mergeada (5/10/2026) y están en
    # ORQUESTADOR_SIMULADOR.md §14.1. Deben salir idénticos hasta 6 decimales.
    DORADOS_REPLICA = {
        1: {
            "espera_surtidor": 1.3919284647118675,
            "espera_pico": 3.6094022200315035,
            "cola_surtidor": 0.3723630011739665,
            "util_surtidores": 0.43519483111163554,
            "atendidos_dia": 350.8965517241379,
            "perdidos_cola_dia": 4.758620689655173,
            "perdidos_sin_combustible_dia": 12.482758620689655,
            "litros_vendidos_dia": 12333.565057334621,
            "nivel_servicio": 0.9533549473624987,
            "pedidos_dia": 0.6206896551724138,
            "compras_dia": 104.6896551724138,
            "hora_pico": 19,
        },
        2: {
            "espera_surtidor": 1.23730743038923,
            "espera_pico": 3.1924768285024845,
            "cola_surtidor": 0.3149593047004242,
            "util_surtidores": 0.4279340258516126,
            "atendidos_dia": 345.7931034482759,
            "perdidos_cola_dia": 2.4827586206896552,
            "perdidos_sin_combustible_dia": 14.206896551724139,
            "litros_vendidos_dia": 12058.172472897104,
            "nivel_servicio": 0.9539092186615971,
            "pedidos_dia": 0.6206896551724138,
            "compras_dia": 104.6896551724138,
            "hora_pico": 19,
        },
    }
    for semilla, esperados in DORADOS_REPLICA.items():
        r, _ = correr_replica(clasico, semilla=semilla)
        peor = 0.0
        peor_campo = ""
        for campo, esperado in esperados.items():
            diferencia = abs(float(getattr(r, campo)) - float(esperado))
            if diferencia > peor:
                peor, peor_campo = diferencia, campo
        controlar(
            peor < 1e-6,
            f"Réplica con semilla {semilla} idéntica a los dorados (12 campos, |dif| < 1e-6)",
            f"peor diferencia: {peor:.2e} en {peor_campo}",
        )

    DORADOS_ESCENARIO = {
        "Base": (3.2495360377376423, 346.4655172413793, 12140.08982106003),
        "A": (0.8447869320060243, 348.32758620689657, 12207.652175343133),
        "B": (3.2495360377376423, 346.4655172413793, 12140.08982106003),
        "C": (0.8447869320060243, 348.32758620689657, 12207.652175343133),
    }
    escenarios = correr_escenarios(clasico, replicas=4, semilla_base=1)
    peor = 0.0
    peor_detalle = ""
    for r in escenarios:
        for metrica, esperado in zip(
            ("espera_pico", "atendidos_dia", "litros_vendidos_dia"),
            DORADOS_ESCENARIO[r.escenario.nombre],
        ):
            diferencia = abs(r.prom(metrica) - esperado)
            if diferencia > peor:
                peor, peor_detalle = diferencia, f"{r.escenario.nombre}.{metrica}"
    controlar(
        peor < 1e-6,
        "Los 4 escenarios × 4 réplicas reproducen los dorados (B = Base, C = A)",
        f"peor diferencia: {peor:.2e} en {peor_detalle}",
    )

    # ------------------------------------------------------------------ 11
    separador("11. N16: unidades de la demanda (litros, no autos)")
    fecha_enero, dias_enero = dias_y_fecha("mes", mes=1)
    p_esperada = replace(
        p,
        modo_demanda="esperada",
        litros_mes=270_000.0,
        fecha_inicio=fecha_enero,
        dias=dias_enero,
        dias_calentamiento=2,
    )
    litros_totales = []
    for semilla in (101, 102, 103):
        ind, _ = simular(p_esperada, semilla=semilla)
        litros_totales.append(
            ind.c_total.litros_vendidos + ind.c_total.litros_no_vendidos
        )
    promedio = sum(litros_totales) / len(litros_totales)
    controlar(
        abs(promedio - 270_000.0) / 270_000.0 < 0.03,
        "270.000 L/mes -> 270.000 ± 3 % de litros simulados (3 réplicas)",
        f"simulado {promedio:,.0f} L/mes ({' · '.join(f'{v:,.0f}' for v in litros_totales)}) | "
        f"desvío {(promedio - 270_000.0) / 270_000.0 * 100:+.2f} %",
    )

    # ------------------------------------------------------------------ 12
    separador("12. N17/N18: calendario real y normalización del fin de semana")
    fecha_inv, dias_inv = dias_y_fecha("estacion", estacion="invierno")
    p_inv = replace(
        p,
        modo_demanda="esperada",
        fecha_inicio=fecha_inv,
        dias=dias_inv,
        dias_calentamiento=2,
    )
    meses = {p_inv._fecha_del_dia(d)[0] for d in range(1, dias_inv + 1)}
    controlar(
        meses == {6, 7, 8},
        "La estación de invierno simula exactamente junio, julio y agosto",
        f"meses simulados: {sorted(meses)} | arranca el {fecha_inv[1]}/{fecha_inv[0]}",
    )

    litros_por_mes = {}
    for nombre, mes in (("enero", 1), ("julio", 7)):
        fecha_m, dias_m = dias_y_fecha("mes", mes=mes)
        p_m = replace(
            p_esperada,
            estacionalidad=ESTACIONALIDAD_PROXY,
            fecha_inicio=fecha_m,
            dias=dias_m,
        )
        totales = []
        for semilla in (101, 102):
            ind, _ = simular(p_m, semilla=semilla)
            totales.append(
                ind.c_total.litros_vendidos + ind.c_total.litros_no_vendidos
            )
        litros_por_mes[nombre] = sum(totales) / len(totales)
    diferencia_relativa = abs(
        litros_por_mes["julio"] - litros_por_mes["enero"]
    ) / litros_por_mes["enero"]
    controlar(
        diferencia_relativa > 0.01,
        "Con el preset 'proxy turístico', un mes de julio es distinto de un mes de enero",
        f"enero {litros_por_mes['enero']:,.0f} L | julio {litros_por_mes['julio']:,.0f} L | "
        f"diferencia {diferencia_relativa * 100:.1f} %",
    )

    p_cal = replace(p, fecha_inicio=(7, 1))
    controlar(
        p_cal._fecha_del_dia(1) == (7, 2),
        "El 1/7/2026 es miércoles (día de la semana correcto)",
        f"_fecha_del_dia(1) = {p_cal._fecha_del_dia(1)}",
    )
    controlar(
        p_cal._fecha_del_dia(30) == (7, 3),
        "El 30/7/2026 es jueves",
        f"_fecha_del_dia(30) = {p_cal._fecha_del_dia(30)}",
    )

    for factor in (1.30, 1.50):
        p_n = replace(p_esperada, factor_fin_de_semana=factor)
        suma = sum(p_n.litros_del_dia(d) for d in range(1, dias_enero + 1))
        controlar(
            abs(suma - 270_000.0) / 270_000.0 < 1e-9,
            f"El total del mes no cambia al variar el factor de fin de semana (f = {factor:g})",
            f"suma de litros_del_dia = {suma:,.1f} L",
        )

    # ------------------------------------------------------------------ 13
    separador("13. N14: cero parámetros huérfanos")
    from dataclasses import fields

    from sim.config import (
        ParametrosEconomicos,
        ParametrosEventos,
        ParametrosGNC,
        ParametrosRed,
        ParametrosTanque,
    )
    from sim.datos import MAPA_PARAMETROS, REGISTRO as REGISTRO_DATOS

    ids_registro = {d.id for d in REGISTRO_DATOS}
    huerfanos = []
    for clase in (
        ParametrosSimulacion, ParametrosTanque, ParametrosEconomicos, ParametrosRed, ParametrosGNC,
        ParametrosEventos,
    ):
        for campo in fields(clase):
            clave = f"{clase.__name__}.{campo.name}"
            if clave not in MAPA_PARAMETROS or MAPA_PARAMETROS[clave] not in ids_registro:
                huerfanos.append(clave)
    controlar(
        not huerfanos,
        "Todo campo de los parámetros tiene su Dato en el Registro",
        f"{len(MAPA_PARAMETROS)} campos mapeados a Datos"
        + (f" | HUÉRFANOS: {huerfanos}" if huerfanos else ""),
    )

    # ------------------------------------------------------------------ 14
    separador("14. N15: tema (ningún hex fuera de ui/tema.py; contraste; productos)")
    import pathlib
    import re

    from ui.tema import PARES_CONTRASTE, PRODUCTO, contraste as contraste_wcag

    hex_re = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
    # El [theme] de .streamlit/config.toml está exceptuado: sus hex los prescribe el
    # propio §8.1 (regla 5) y son los únicos que puede haber fuera de ui/tema.py.
    archivos_ui = [
        "app.py", "ui/graficos.py", "ui/graficos_red.py", "ui/graficos_gnc.py",
        "ui/graficos_escenarios.py",
        "ui/animacion.py", "ui/datos_ui.py", "ui/textos.py",
    ]
    infractores = []
    for nombre in archivos_ui:
        texto = pathlib.Path(nombre).read_text(encoding="utf-8")
        for coincidencia in hex_re.findall(texto):
            infractores.append(f"{nombre}: {coincidencia}")
    controlar(
        not infractores,
        "Ningún hex hardcodeado fuera de ui/tema.py (salvo el [theme] de config.toml)",
        f"{len(infractores)} hexes sueltos"
        + (f": {infractores[:5]}" if infractores else ""),
    )

    pares_mal = [
        (nombre, contraste_wcag(fondo, frente))
        for nombre, fondo, frente in PARES_CONTRASTE
        if contraste_wcag(fondo, frente) < 4.5
    ]
    controlar(
        not pares_mal,
        "Contraste WCAG >= 4,5 en los pares declarados (§10.3)",
        f"{len(PARES_CONTRASTE)} pares"
        + (f" | fallan: {pares_mal}" if pares_mal else ""),
    )

    def distancia_rgb(h1: str, h2: str) -> float:
        h1, h2 = h1.lstrip("#"), h2.lstrip("#")
        return sum(
            (int(h1[i : i + 2], 16) - int(h2[i : i + 2], 16)) ** 2 for i in (0, 2, 4)
        ) ** 0.5

    colores_producto = list(PRODUCTO.values())
    peor = min(
        distancia_rgb(a, b)
        for i, a in enumerate(colores_producto)
        for b in colores_producto[i + 1 :]
    )
    controlar(
        peor >= 60,
        "Los 5 colores de PRODUCTO son distinguibles entre sí",
        f"menor distancia RGB entre productos: {peor:.0f}",
    )

    # ------------------------------------------------------------------ 15
    separador("15. N9: mezcla de producto (en litros) y clientes GNC")
    p_mix = replace(p, dias=130, dias_calentamiento=2)
    ind_mix, _ = simular(p_mix, semilla=31)
    llegadas_mix = ind_mix.c.llegadas
    # Litros que cada producto PIDIÓ (vendidos + los que pidió quien se fue): así el
    # abandono o el quiebre no sesgan la mezcla que se sortea al llegar.
    pedidos = {
        pr.id: ind_mix.c_producto[pr.id].litros_vendidos
        + ind_mix.c_producto[pr.id].litros_no_vendidos
        for pr in p_mix.productos
        if not pr.es_gnc
    }
    total_pedido = sum(pedidos.values())
    peor_pp = max(
        abs(100.0 * pedidos[pr.id] / total_pedido - 100.0 * pr.pct_litros)
        for pr in p_mix.productos
        if not pr.es_gnc
    )
    controlar(
        llegadas_mix >= 30_000 and peor_pp < 1.5,
        "La mezcla en LITROS simulada coincide con DEM-04 (< 1,5 puntos)",
        f"{llegadas_mix:,} llegadas | "
        + " · ".join(
            f"{pr.nombre} {100.0 * pedidos[pr.id] / total_pedido:.1f} % (DEM-04 {100.0 * pr.pct_litros:.1f})"
            for pr in p_mix.productos
            if not pr.es_gnc
        )
        + f" | peor diferencia {peor_pp:.2f} pp",
    )
    pct_gnc_sim = ind_mix.c_producto["gnc"].llegadas / llegadas_mix
    controlar(
        abs(pct_gnc_sim - p_mix.pct_gnc) < 0.005,
        "Los clientes GNC son ≈ 3 % de las llegadas (DEM-05)",
        f"{100.0 * pct_gnc_sim:.2f} % simulado | {100.0 * p_mix.pct_gnc:.1f} % cargado",
    )

    # ------------------------------------------------------------------ 16
    separador("16. N10: litros por carga según el tipo de vehículo")
    esperados_tipo = {t.id: t.litros.media for t in p_mix.tipos_vehiculo}
    tolerancia_tipo = {"auto": 0.02, "pick_up": 0.02, "moto": 0.04, "camion": 0.04, "auto_gnc": 0.04}
    peor_tipo = 0.0
    detalle_tipo = []
    for tipo, muestras in ind_mix.litros_por_tipo.items():
        error_t = abs(muestras.promedio - esperados_tipo[tipo]) / esperados_tipo[tipo]
        detalle_tipo.append(
            f"{tipo} {muestras.promedio:.2f} (teórica {esperados_tipo[tipo]:.2f}, n={muestras.n:,})"
        )
        peor_tipo = max(peor_tipo, error_t - tolerancia_tipo[tipo])
    controlar(
        peor_tipo <= 0,
        "La media muestral de litros de cada tipo de vehículo coincide con su Triangular",
        " | ".join(detalle_tipo),
    )
    auto_media = ind_mix.litros_por_tipo["auto"].promedio
    pick_media = ind_mix.litros_por_tipo["pick_up"].promedio
    controlar(
        abs(auto_media - 23.5) / 23.5 < 0.02 and abs(pick_media - 40.0) / 40.0 < 0.02,
        "N10: auto ≈ 23,5 L (± 2 %) y pick-up ≈ 40 L (± 2 %)",
        f"auto {auto_media:.2f} L | pick-up {pick_media:.2f} L",
    )

    # ------------------------------------------------------------------ 17
    separador("17. Fase 3: los cuadros de la animación coinciden con el motor")
    p_anim = replace(p, dias=4, dias_calentamiento=2, dia_animado=3)
    _, traza_anim = correr_replica(p_anim, semilla=41, con_traza=True)
    cuadros = traza_anim.cuadros
    incoherentes = 0
    for c in cuadros:
        ocupadas = sum(1 for g in c.grupos for k in g[1] if k >= 0)
        en_cola = sum(g[3] for g in c.grupos)
        esperando_ok = all(
            (k & 1) == 0 or p_anim.grupos[i].requiere_playero
            for i, g in enumerate(c.grupos) for k in g[1] if k >= 0
        )
        cabe = all(len(g[1]) == p_anim.grupos[i].caras for i, g in enumerate(c.grupos))
        if ocupadas != c.surtidores_ocupados or en_cola != c.cola_surtidor or not (esperando_ok and cabe):
            incoherentes += 1
    controlar(
        incoherentes == 0,
        "Caras ocupadas y autos en cola de la foto = los del motor (todos los cuadros)",
        f"{len(cuadros):,} cuadros revisados | incoherentes: {incoherentes}",
    )
    limite_cola = all(
        g[3] <= p_anim.capacidad_de(p_anim.grupos[i].id) for c in cuadros for i, g in enumerate(c.grupos)
    )
    progresos = [t[3] for c in cuadros for t in c.tanques]
    controlar(
        limite_cola and all(-1.0 <= x <= 1.0 for x in progresos),
        "La cola visible respeta la capacidad y el progreso del camión está entre 0 y 1",
        f"cola máxima {max(g[3] for c in cuadros for g in c.grupos)} (capacidad por zona "
        f"{[p_anim.capacidad_de(g.id) for g in p_anim.grupos]})",
    )
    from ui.animacion import reproductor_html
    peso_mb = len(reproductor_html(traza_anim, p_anim, {}, "").encode("utf-8")) / 1e6
    controlar(
        peso_mb < 3.0,
        "El HTML del reproductor pesa menos de 3 MB (un día, un cuadro cada 0,5 min)",
        f"{peso_mb:.2f} MB para {len(cuadros):,} cuadros",
    )

    # ------------------------------------------------------------------ 18
    separador("18. Fase 4: política (s, Q) por producto y barrido")
    from sim.config import ParametrosEconomicos
    from sim.economia import ahorro_por_producto, analizar_politicas_real
    from sim.runner import (
        barrer_politicas_real,
        con_politicas,
        grilla_politicas_real,
        promedio_por_producto,
    )

    grilla = grilla_politicas_real(p)
    capacidades = {i.producto: i.capacidad for i in p.inventario}
    grilla_valida = all(
        0 <= s_ and q_ > 0 and s_ + q_ <= capacidades[prod] + 1e-6
        for punto in grilla for prod, (s_, q_) in punto.items()
    )
    cargada = {i.producto: (i.punto_pedido, i.cantidad_pedido) for i in p.inventario}
    controlar(
        grilla_valida and grilla[0] == cargada and len(grilla) == 13,
        "La grilla tiene 13 puntos, empieza por la política cargada y entra en cada tanque",
        f"{len(grilla)} puntos; el primero = {', '.join(f'{k}: {v[0]:,.0f}/{v[1]:,.0f}' for k, v in cargada.items())}",
    )

    # Monotonía de s: con un punto de pedido más alto el tanque quiebra menos y guarda más
    p_baja = con_politicas(p, {"diesel_g2": (1_500.0, 10_000.0)})
    p_alta = con_politicas(p, {"diesel_g2": (7_000.0, 10_000.0)})
    r_baja, _ = correr_replica(p_baja, semilla=51)
    r_alta, _ = correr_replica(p_alta, semilla=51)
    quiebre_baja = dict(r_baja.dias_quiebre_por_producto)["diesel_g2"]
    quiebre_alta = dict(r_alta.dias_quiebre_por_producto)["diesel_g2"]
    nivel_baja = dict(r_baja.nivel_por_producto)["diesel_g2"]
    nivel_alta = dict(r_alta.nivel_por_producto)["diesel_g2"]
    controlar(
        quiebre_alta < quiebre_baja and nivel_alta > nivel_baja,
        "Subir s en un tanque baja sus días con quiebre y sube su nivel promedio (N11)",
        f"s = 1.500 L: quiebre {quiebre_baja:.1f} % · nivel {nivel_baja:,.0f} L | "
        f"s = 7.000 L: quiebre {quiebre_alta:.1f} % · nivel {nivel_alta:,.0f} L",
    )

    # Independencia: cambiar un tanque no mueve a los otros (cada camión y cada plazo son
    # propios); sólo queda el acople débil por la congestión de las colas.
    otros = ("super", "vpower", "diesel_g3")
    peor = 0.0
    for producto in otros:
        v0 = dict(r_baja.litros_vendidos_por_producto)[producto]
        v1 = dict(r_alta.litros_vendidos_por_producto)[producto]
        peor = max(peor, abs(v1 - v0) / v0)
    pedidos_otros_iguales = all(
        abs(dict(r_baja.pedidos_por_producto)[x] - dict(r_alta.pedidos_por_producto)[x]) <= 2 / 29
        for x in otros
    )
    controlar(
        peor < 0.03 and pedidos_otros_iguales,
        "Cambiar la política del diésel G2 casi no mueve a los otros tres tanques",
        f"mayor cambio en los litros vendidos de los otros: {peor * 100:.2f} %",
    )

    # El barrido (1 réplica por punto) incluye la política cargada y la mejor no la supera
    barrido = barrer_politicas_real(p, replicas=1, semilla_base=61)
    eco = ParametrosEconomicos()
    costos = analizar_politicas_real(barrido, eco, p)
    ahorros = ahorro_por_producto(costos)
    mejores_ok = all(
        min(c.costo_total for c in lista) <= lista[0].costo_total + 1e-6
        for lista in costos.values()
    )
    reconcilia = all(
        abs(c.costo_total - (c.costo_pedidos + c.costo_almacenamiento + c.costo_faltante)) < 1e-6
        for lista in costos.values() for c in lista
    )
    controlar(
        mejores_ok and reconcilia and all(v >= 0 for v in ahorros.values()),
        "El barrido encuentra una política ≤ a la cargada en cada tanque y el costo reconcilia",
        " | ".join(f"{k}: ahorra ${v:,.0f}/mes" for k, v in ahorros.items()),
    )
    controlar(
        sum(ahorros.values()) > 0,
        "Con la política inicial (INV-07) hay algo para mejorar en al menos un tanque",
        f"ahorro total ${sum(ahorros.values()):,.0f} por mes (márgenes y flete placeholder)",
    )

    # ------------------------------------------------------------------ 19
    separador("19. Fase 5: red de rutas (N6) y cortes (N11)")
    from dataclasses import replace as reemplazar
    from itertools import permutations

    from sim.red import camino_mas_corto, demora_por_corte

    red = p.red
    luj = reemplazar(red, origen="LUJAN")
    base_l = camino_mas_corto(luj)
    cort_l = camino_mas_corto(luj, cerrados=(("PAREDITAS", "SANRAFAEL"),))
    controlar(
        abs(base_l.km - 221.8) < 1e-6 and abs(base_l.minutos - 190.1) < 0.05
        and abs(cort_l.km - 399.8) < 1e-6
        and abs((cort_l.km - base_l.km) - 178.0) < 1e-6
        and round(cort_l.minutos - base_l.minutos) == 153,
        "N6: Luján→estación 221,8 km / 190 min; con la RN 143 cortada 399,8 km (+178 km, +153 min)",
        f"{base_l.km} km / {base_l.minutos:.1f} min | cortada: {cort_l.km:.1f} km "
        f"(+{cort_l.km - base_l.km:.1f} km, +{cort_l.minutos - base_l.minutos:.1f} min) por "
        f"{' → '.join(cort_l.ruta)}",
    )
    dock = camino_mas_corto(red)
    dock_l = camino_mas_corto(red, cerrados=(("ALVEAR", "SANRAFAEL"),))
    controlar(
        abs(dock.km - 991.3) < 1e-6 and round(dock.minutos / 60, 1) == 14.2
        and dock.ruta == ("DOCK", "ALVEAR", "SANRAFAEL")
        and abs(dock_l.km - 1279.0) < 1.0 and dock.km < dock_l.km,
        "N6: Dock Sud→estación 991,3 km / 14,2 h por Gral. Alvear, menos que por Luján (≈ 1.279 km)",
        f"{dock.km} km / {dock.minutos / 60:.2f} h | por Luján: {dock_l.km:.1f} km "
        f"(la nota 06 dice 1.279,0: 0,7 km de diferencia por el arco derivado)",
    )

    # Dijkstra contra fuerza bruta: se enumeran todos los caminos simples del grafo
    def fuerza_bruta(r, cerrados):
        cierres = {frozenset(c) for c in cerrados}
        km_arco = {
            frozenset((a.a, a.b)): a.km
            for a in r.arcos
            if frozenset((a.a, a.b)) not in cierres
        }
        nodos = {n for a in r.arcos for n in (a.a, a.b)} - {r.origen, r.destino}
        mejor = float("inf")
        for k in range(len(nodos) + 1):
            for medio in permutations(sorted(nodos), k):
                ruta = (r.origen, *medio, r.destino)
                pares = [frozenset(par) for par in zip(ruta, ruta[1:])]
                if all(x in km_arco for x in pares):
                    mejor = min(mejor, sum(km_arco[x] for x in pares))
        return mejor

    conjuntos_cerrados = (
        (),
        (("PAREDITAS", "SANRAFAEL"),),
        (("ALVEAR", "SANRAFAEL"),),
        (("PAREDITAS", "SANRAFAEL"), ("PAREDITAS", "SOSNEADO"), ("SOSNEADO", "SANRAFAEL")),
        (("SANRAFAEL", "MONTECOMAN"), ("ALVEAR", "SANRAFAEL"), ("SOSNEADO", "SANRAFAEL")),
    )
    casos = [(o, c) for o in ("DOCK", "LUJAN") for c in conjuntos_cerrados]
    discrepancias = [
        (o, c)
        for o, c in casos
        if abs(
            camino_mas_corto(reemplazar(red, origen=o), cerrados=c).km
            - fuerza_bruta(reemplazar(red, origen=o), c)
        ) > 1e-9
    ]
    controlar(
        not discrepancias,
        "Dijkstra coincide con la enumeración de todos los caminos (10 casos, con y sin cortes)",
        f"{len(casos)} combinaciones de origen y arcos cerrados"
        + (f" | discrepan: {discrepancias}" if discrepancias else ""),
    )

    # Un corte que no está en la ruta no demora; si está, demora mín(desvío, duración)
    fuera = demora_por_corte(red, (("PAREDITAS", "SANRAFAEL"),), 360.0)
    dentro = demora_por_corte(luj, (("PAREDITAS", "SANRAFAEL"),), 10_000.0)
    acotada = demora_por_corte(luj, (("PAREDITAS", "SANRAFAEL"),), 60.0)
    aislado = demora_por_corte(
        luj,
        (("PAREDITAS", "SANRAFAEL"), ("LAPAZ", "LUJAN"), ("PAREDITAS", "SOSNEADO")),
        500.0,
    )
    controlar(
        fuera == 0.0 and abs(dentro - (cort_l.minutos - base_l.minutos)) < 1e-9
        and acotada == 60.0 and aislado == 500.0,
        "Corte fuera de la ruta = 0; en la ruta = mín(desvío, duración); sin alternativa = esperar",
        f"Dock Sud + RN 143 oeste: {fuera:.0f} min | Luján: {dentro:.1f} min "
        f"(con 60 min de corte: {acotada:.0f}) | aislado: espera {aislado:.0f} min",
    )

    # La red no cambia nada sin cortes: 'ninguno' y 'aleatorio' fuera de invierno = sin red
    r_sin = correr_replica(reemplazar(p, red=None), semilla=71)[0]
    r_ning = correr_replica(
        reemplazar(p, red=reemplazar(red, escenario_corte="ninguno")), semilla=71
    )[0]
    r_enero = correr_replica(p, semilla=71)[0]
    # (la lista de camiones guarda el origen: sin red queda vacío; el resto de cada camión tiene que coincidir)
    def _sin_origen(r_):
        return reemplazar(r_, camiones=tuple((x.producto, x.t_pedido, x.t_llegada, x.litros) for x in r_.camiones))
    controlar(
        _sin_origen(r_sin) == _sin_origen(r_ning) == _sin_origen(r_enero),
        "Sin cortes (o con cortes sorteados fuera de jun–ago) el resultado es idéntico al de sin red",
        f"plazo {r_sin.plazo_entrega:.4f} h en los tres casos",
    )

    # N11: con cortes el plazo no baja, y los indicadores reaccionan como corresponde
    fecha_jul, dias_jul = dias_y_fecha("mes", mes=7)
    p_jul = reemplazar(p, fecha_inicio=fecha_jul, dias=dias_jul)
    sin_c = correr_replica(
        reemplazar(p_jul, red=reemplazar(luj, escenario_corte="ninguno")), semilla=72
    )[0]
    con_c = correr_replica(
        reemplazar(
            p_jul, red=reemplazar(luj, escenario_corte="aleatorio", prob_corte_viaje=0.5)
        ),
        semilla=72,
    )[0]
    controlar(
        con_c.plazo_entrega > sin_c.plazo_entrega and con_c.viajes_demorados_pct > 0
        and con_c.porcentaje_dias_quiebre >= sin_c.porcentaje_dias_quiebre,
        "N11: con cortes el plazo es mayor y el quiebre no baja",
        f"plazo {sin_c.plazo_entrega:.2f} → {con_c.plazo_entrega:.2f} h | "
        f"{con_c.viajes_demorados_pct:.0f} % de los camiones demorados | quiebre "
        f"{sin_c.porcentaje_dias_quiebre:.1f} → {con_c.porcentaje_dias_quiebre:.1f} %",
    )
    turnos_3 = ((0.0, 3), (6.0, 3), (14.0, 3), (22.0, 3))
    turnos_1 = ((0.0, 1), (6.0, 1), (14.0, 1), (22.0, 1))
    mas_playeros = correr_replica(
        reemplazar(p, playeros_por_turno=(3, 3, 3), turnos=turnos_3), semilla=73
    )[0]
    pocos_playeros = correr_replica(
        reemplazar(p, playeros_por_turno=(1, 1, 1), turnos=turnos_1), semilla=73
    )[0]
    mas_demanda = correr_replica(reemplazar(p, litros_mes=400_000.0), semilla=73)[0]
    base_73 = correr_replica(p, semilla=73)[0]
    controlar(
        mas_playeros.espera_pico < pocos_playeros.espera_pico
        and mas_demanda.espera_pico > base_73.espera_pico,
        "N11: más playeros ⇒ menos espera; más demanda ⇒ más espera",
        f"espera pico: 3 playeros {mas_playeros.espera_pico:.2f} min < 1 playero "
        f"{pocos_playeros.espera_pico:.2f} min | 270.000 L {base_73.espera_pico:.2f} min < "
        f"400.000 L {mas_demanda.espera_pico:.2f} min",
    )

    # ------------------------------------------------------------------ 20
    separador("20. Fase 6: GNC — episodios, compresores y migración (N7, N8, N12)")
    from sim.config import ParametrosGNC

    def ejecutar(g, semilla, base=p_jul):
        return simular(reemplazar(base, gnc=g), semilla=semilla, con_traza=True)

    # N7: sin episodios (o con contrato firme) no hay ninguna pérdida por corte
    ind_0, _ = ejecutar(ParametrosGNC(episodios=0), 81)
    ind_f, _ = ejecutar(ParametrosGNC(contrato="firme", episodios_en_horizonte=True), 81)
    controlar(
        all(
            i.c_total.gnc_afectados == i.c_total.perdidos_corte_gnc
            == i.c_total.migrados_gnc_a_nafta == i.c_total.dias_con_corte_gnc == 0
            for i in (ind_0, ind_f)
        ),
        "N7: sin episodios o con contrato firme, cero afectados, cero pérdidas por corte",
        f"GNC atendido en julio: {ind_0.c_producto_total['gnc'].atendidos} clientes (sin cortes)",
    )

    # N7: corte total y sin migración ⇒ todos los GNC del episodio se pierden
    ind_7, traza_7 = ejecutar(ParametrosGNC(episodios_en_horizonte=True, migracion_a_nafta=0.0), 81)
    c7 = ind_7.c_total
    dias_7 = traza_7.dias
    previo_cortado = [False] + [d.gnc_corte_min >= 1440 for d in dias_7[:-1]]
    atendidos_en_corte = sum(
        d.gnc_atendidos for d, previo in zip(dias_7, previo_cortado)
        if d.gnc_corte_min >= 1440 and previo
    )
    controlar(
        c7.gnc_afectados > 0 and c7.perdidos_corte_gnc == c7.gnc_afectados
        and c7.migrados_gnc_a_nafta == 0 and atendidos_en_corte == 0,
        "N7: corte total sin migración ⇒ todos los clientes GNC del episodio se pierden",
        f"{c7.gnc_afectados} afectados = {c7.perdidos_corte_gnc} perdidos | GNC atendido en "
        f"los días de corte completo: {atendidos_en_corte} | {c7.dias_con_corte_gnc} días con corte",
    )

    # N8: con migración, migrados + perdidos = afectados (y cada zona sigue cerrando)
    ind_8, _ = ejecutar(ParametrosGNC(episodios_en_horizonte=True, migracion_a_nafta=0.5), 81)
    c8 = ind_8.c_total
    cierra = True
    llegadas_grupos = 0
    for gr in p_jul.grupos:
        cg = ind_8.c_grupo_total[gr.id]
        llegadas_grupos += cg.llegadas
        adentro = cg.llegadas - (
            cg.atendidos + cg.perdidos_espera + cg.perdidos_cola_llena
            + cg.perdidos_sin_combustible + cg.perdidos_corte_gnc
        )
        cierra = cierra and 0 <= adentro <= gr.caras + (p_jul.capacidad_de(gr.id) or 0)
    controlar(
        c8.migrados_gnc_a_nafta + c8.perdidos_corte_gnc == c8.gnc_afectados
        and 0.3 < c8.migrados_gnc_a_nafta / c8.gnc_afectados < 0.7
        and cierra and llegadas_grupos == c8.llegadas,
        "N8: migrados + perdidos por el corte = afectados (≈ 50 % migra) y cada zona cierra",
        f"{c8.migrados_gnc_a_nafta} migrados + {c8.perdidos_corte_gnc} perdidos = "
        f"{c8.gnc_afectados} afectados",
    )

    # N12: invierno con episodios ⇒ más migrados que verano
    ind_ene, _ = simular(p, semilla=81)
    controlar(
        c8.migrados_gnc_a_nafta > ind_ene.c_total.migrados_gnc_a_nafta == 0,
        "N12: invierno con episodios ⇒ más migrados a nafta que verano",
        f"julio {c8.migrados_gnc_a_nafta} migrados | enero {ind_ene.c_total.migrados_gnc_a_nafta}",
    )

    # Formas del corte
    _, traza_v = ejecutar(
        ParametrosGNC(episodios_en_horizonte=True, forma="ventana"), 81
    )
    horas_v = [d.gnc_corte_min / 60.0 for d in traza_v.dias if d.gnc_corte_min > 0]
    ind_p, _ = ejecutar(ParametrosGNC(episodios_en_horizonte=True, forma="parcial_50"), 81)
    controlar(
        horas_v and max(horas_v) <= 8.0 + 1e-9 and ind_p.c_total.gnc_afectados == 0
        and ind_p.c_total.dias_con_corte_gnc > 0,
        "La forma 'ventana' corta sólo de 17 a 01 h (≤ 8 h por día) y 'parcial_50' no corta a nadie",
        f"horas de corte por día (ventana): {sorted({round(h) for h in horas_v})} | "
        f"parcial_50: {ind_p.c_total.dias_con_corte_gnc} días con compresores al 50 %, "
        f"{ind_p.c_total.gnc_afectados} afectados",
    )

    # Los compresores, no las caras, limitan las cargas simultáneas de GNC
    p_alto = reemplazar(p, pct_gnc=0.25)
    ind_c1, traza_c1 = simular(
        reemplazar(p_alto, gnc=ParametrosGNC(compresores=1)), semilla=82, con_traza=True
    )
    ind_c6, _ = simular(reemplazar(p_alto, gnc=ParametrosGNC(compresores=6)), semilla=82)
    controlar(
        max(c.compresores_ocupados for c in traza_c1.cuadros) <= 1
        and ind_c1.compresores_ocupados.maximo <= 1
        and ind_c1.esperas_grupo["C"].promedio > ind_c6.esperas_grupo["C"].promedio,
        "Con 1 compresor nunca cargan 2 autos GNC a la vez y la espera sube respecto de 6",
        f"espera en la zona C: 1 compresor {ind_c1.esperas_grupo['C'].promedio:.2f} min > "
        f"6 compresores {ind_c6.esperas_grupo['C'].promedio:.2f} min",
    )

    # ------------------------------------------------------------------ 21
    separador("21. Fase 7: estaciones del año y catálogo S0–S12 (N12, N11, N18)")
    import time

    from sim.config import turnos_con_refuerzo, turnos_de
    from sim.escenarios import (
        HORAS_CERRADO,
        catalogo,
        correr_catalogo,
        correr_estaciones,
        diferencia_pareada,
        es_significativa,
        para_mes,
    )
    from sim.runner import correr_replicas
    from dataclasses import replace as replace_dc

    # N12 + compuerta de tiempo: 4 estaciones × 4 réplicas ≤ 90 s
    forzado = reemplazar(p, gnc=ParametrosGNC(episodios_en_horizonte=True))
    t0 = time.time()
    est = correr_estaciones(forzado, replicas=4)
    segundos = time.time() - t0
    migrados = {r.escenario.id: r.prom("migrados_gnc_dia") for r in est}
    controlar(
        migrados["jul"] > 0 and migrados["ene"] == migrados["abr"] == migrados["oct"] == 0,
        "N12: invierno con episodios ⇒ más migrados a nafta que verano, otoño y primavera",
        " | ".join(f"{k} {v:.2f}" for k, v in migrados.items()) + " migrados por día",
    )
    controlar(
        segundos <= 90.0,
        "4 estaciones × 4 réplicas se corren en ≤ 90 s",
        f"{segundos:.1f} s ({4 * 4} réplicas, {segundos / 16:.2f} s por réplica)",
    )
    controlar(
        [r.parametros.dias for r in est] == [31, 30, 31, 31]
        and [r.parametros.fecha_inicio for r in est] == [(1, 1), (4, 1), (7, 1), (10, 1)],
        "Las estaciones simulan el mes real completo (31·30·31·31 días) desde el 1 de ene·abr·jul·oct",
        f"días {[r.parametros.dias for r in est]}",
    )
    totales = [
        (r.prom("litros_vendidos_dia") + r.prom("litros_no_vendidos_dia")) * r.parametros.dias
        for r in est
    ]
    controlar(
        all(abs(t / p.litros_mes - 1.0) < 0.04 for t in totales),
        "Con estacionalidad neutra cada mes pide los litros del mes (270.000 ± 4 %)",
        " | ".join(f"{t:,.0f} L" for t in totales),
    )

    # N18 con quincena: los litros del mes se conservan y el pico concentra la demanda
    p_n = para_mes(p, 7)
    p_q = reemplazar(p_n, dias_quincena=(16, 17, 18))
    tot_n = sum(p_n.litros_del_dia(d) for d in range(1, p_n.dias + 1))
    tot_q = sum(p_q.litros_del_dia(d) for d in range(1, p_q.dias + 1))
    razon_pico = p_q.litros_del_dia(16) / p_n.litros_del_dia(16)
    controlar(
        abs(tot_q - tot_n) < 1e-6 * tot_n and 1.7 < razon_pico < 2.0
        and p_q.litros_del_dia(5) < p_n.litros_del_dia(5),
        "N18: la quincena conserva los litros del mes y concentra la demanda en sus días",
        f"mes {tot_n:,.0f} L = {tot_q:,.0f} L | día 16: ×{razon_pico:.2f} | día 5: "
        f"×{p_q.litros_del_dia(5) / p_n.litros_del_dia(5):.2f}",
    )

    # El catálogo: identificadores, nombres únicos y cada escenario es una corrida válida
    cat = catalogo(p_n)
    ids = {e.id for e in cat}
    controlar(
        ids == {"S0", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12"}
        and len({e.nombre for e in cat}) == len(cat) and cat[0].id == "S0" and not cat[0].cambios,
        "El catálogo trae S0, S2–S12 con nombres únicos (S1 es la pestaña de estaciones)",
        f"{len(cat)} escenarios: {sorted(ids, key=lambda x: int(x[1:]))}",
    )
    por_nombre = {e.nombre: e for e in cat}

    # Cada escenario cierra el balance de clientes (N2) en un horizonte corto
    corto = reemplazar(p_n, dias=10, dia_animado=3)
    cierran = True
    peor = 0
    for e in catalogo(corto):
        p_e = e.aplicar(corto)
        c = simular(p_e, semilla=85)[0].c_total
        perdidos_e = (
            c.perdidos_surtidor + c.perdidos_sin_combustible + c.perdidos_cola_llena
            + c.perdidos_corte_gnc
        )
        dentro = c.llegadas - c.atendidos_surtidor - perdidos_e
        holgura_e = sum(g.caras + (p_e.capacidad_de(g.id) or 0) for g in p_e.grupos)
        cierran = cierran and 0 <= dentro <= holgura_e
        peor = max(peor, dentro)
    controlar(
        cierran,
        "N2: todos los escenarios del catálogo cierran (llegadas = atendidos + perdidos + adentro)",
        f"{len(catalogo(corto))} escenarios en 10 días; el máximo de clientes adentro al final fue {peor}",
    )

    # S2: el refuerzo y la capacidad del recurso
    controlar(
        turnos_con_refuerzo(p.playeros_por_turno, ((7.0, 10.0, 0), (16.0, 18.0, 0)))
        == turnos_de(p.playeros_por_turno),
        "Un refuerzo de 0 deja los turnos exactamente como están",
    )
    p_s2 = por_nombre["S2 · Playeros en el pico +2"].aplicar(p_n)
    ind_s2, _ = simular(p_s2, semilla=83)
    controlar(
        ind_s2.playeros_en_turno.maximo == max(p.playeros_por_turno) + 2
        and ind_s2.playeros_ocupados.maximo <= p_s2.playeros_maximos
        and p_s2.playeros_maximos == max(p.playeros_por_turno) + 2,
        "N5 con refuerzo: la capacidad sube con el pico y nadie atiende por encima de la dotación",
        f"dotación máxima {ind_s2.playeros_en_turno.maximo:.0f} | ocupados máximo "
        f"{ind_s2.playeros_ocupados.maximo:.0f}",
    )

    # N11 con S2 y diferencias pareadas (números aleatorios comunes)
    nombres_s2 = ("S2 · Playeros en el pico -1", "S2 · Playeros en el pico +1")
    res3 = correr_catalogo(p, 7, replicas=3, nombres=nombres_s2)
    base3, menos, mas = res3
    d_menos = diferencia_pareada(base3, menos, "espera_pico")
    d_mas = diferencia_pareada(base3, mas, "espera_pico")
    d_cero = diferencia_pareada(base3, base3, "espera_pico")
    controlar(
        d_menos.promedio > 0 > d_mas.promedio,
        "N11: un playero menos en el pico sube la espera y uno más la baja",
        f"S2 −1: {d_menos.promedio:+.2f} ± {d_menos.semiamplitud:.2f} min | S2 +1: "
        f"{d_mas.promedio:+.2f} ± {d_mas.semiamplitud:.2f} min (diferencia pareada vs S0)",
    )
    controlar(
        d_cero.promedio == 0.0 and d_cero.semiamplitud == 0.0 and not es_significativa(d_cero)
        and base3.replicas == correr_replicas(p_n, replicas=3),
        "S0 es la corrida de base sin tocar y su diferencia contra sí misma es exactamente 0",
        "las réplicas de S0 coinciden con correr_replicas(mes) sin cambios",
    )

    # S7: durante la crisis los pedidos tardan más; S10: cierre nocturno
    ind_s0, _ = simular(p_n, semilla=84)
    ind_s7, _ = simular(por_nombre["S7 · Crisis de abastecimiento"].aplicar(p_n), semilla=84)
    controlar(
        ind_s7.plazo_entrega.promedio > ind_s0.plazo_entrega.promedio + 1.0
        and ind_s7.plazo_entrega.maximo >= 72.0,
        "S7: los pedidos de la ventana de crisis tardan 72 h o más y el plazo medio sube",
        f"plazo medio {ind_s0.plazo_entrega.promedio:.1f} h → {ind_s7.plazo_entrega.promedio:.1f} h "
        f"| máximo {ind_s7.plazo_entrega.maximo:.1f} h",
    )
    p_s10 = por_nombre["S10 · Cierre nocturno 22–06"].aplicar(p_n)
    cerrado_ok = all(p_s10.perfil.fracciones[h] == 0.0 for h in HORAS_CERRADO)
    lambda_igual = abs(
        p_s10.autos_por_dia * p_s10.perfil.fracciones[8]
        - p_n.autos_por_dia * p_n.perfil.fracciones[8]
    ) < 1e-9
    controlar(
        cerrado_ok and lambda_igual and p_s10.autos_por_dia < p_n.autos_por_dia,
        "S10: de 22 a 06 h no llega nadie y las demás horas siguen igual de cargadas",
        f"clientes por día {p_n.autos_por_dia:.0f} → {p_s10.autos_por_dia:.0f} (la demanda nocturna se pierde)",
    )

    # ------------------------------------------------------------------ 22
    separador("22. Fase 8: economía real (reconciliación, personal, anualización)")
    from sim.config import ParametrosEconomicos
    from sim.economia_real import (
        CAMPOS,
        anualizar,
        conclusiones,
        decision_s6,
        economia_de,
        economia_mensual,
        flete_por_pedido,
        km_por_viaje,
        margen_de_equilibrio_por_litro,
        personas_turno_playeros,
        resumir_economia,
    )

    eco = ParametrosEconomicos()
    p_eco = para_mes(p, 7)
    reps_eco = correr_replicas(p_eco, replicas=3)
    lista_eco = [economia_mensual(r, p_eco, eco) for r in reps_eco]

    # Reconciliación: ingresos − costos = margen, y las partes suman los totales
    def cierra_cuentas(e) -> bool:
        return (
            abs(e.ingreso_total - (e.ingreso_combustible + e.ingreso_gnc + e.ingreso_minimarket)) < 1e-6
            and abs(e.costo_total - (e.flete + e.almacenamiento + e.personal_total + e.costo_eventos)) < 1e-6
            and abs(e.personal_total - (e.personal_playeros + e.personal_cajeros
                                        + e.personal_encargado + e.personal_tienda)) < 1e-6
            and abs(e.margen_operativo - (e.ingreso_total - e.costo_total)) < 1e-6
            and abs(e.ingreso_total - sum(v for _, v in e.ingreso_por_producto)
                    - e.ingreso_minimarket) < 1e-6
        )

    # Cálculo independiente del margen, directo desde la réplica
    r0, e0 = reps_eco[0], lista_eco[0]
    dias_e0 = e0.dias_mes
    margen_directo = (
        sum(v * dias_e0 * (eco.margen_gnc if k == "gnc" else eco.margen_por_litro)
            for k, v in r0.litros_vendidos_por_producto)
        + r0.compras_dia * dias_e0 * eco.margen_compra
        - sum(v for _, v in r0.pedidos_por_producto) * dias_e0 * flete_por_pedido(p_eco, eco)
        - sum(v for _, v in r0.nivel_por_producto) * eco.costo_almacenamiento_litro_mes
        - e0.personal_total
    )
    controlar(
        all(cierra_cuentas(e) for e in lista_eco) and abs(margen_directo - e0.margen_operativo) < 1e-6,
        "Ingresos − costos = margen operativo, y coincide con el cálculo independiente",
        f"margen de julio {e0.margen_operativo:,.0f} $ = {margen_directo:,.0f} $ (3 réplicas, partes suman los totales)",
    )

    # La venta perdida NO se resta: si se triplica el margen del minimarket y se anula la
    # pérdida de una réplica, el margen sólo cambia por el ingreso, no por la venta perdida.
    import dataclasses

    sin_perdida = dataclasses.replace(
        reps_eco[0], perdidos_cola_dia=0.0, perdidos_cola_llena_dia=0.0,
        perdidos_sin_combustible_dia=0.0, perdidos_corte_gnc_dia=0.0, perdidos_caja_dia=0.0,
    )
    e_sin = economia_mensual(sin_perdida, p_eco, eco)
    controlar(
        e_sin.margen_operativo == e0.margen_operativo
        and e_sin.venta_perdida_total < 1e-9 < e0.venta_perdida_total,
        "La venta perdida es costo de oportunidad: anularla no cambia el margen operativo",
        f"venta perdida {e0.venta_perdida_total:,.0f} $ → {e_sin.venta_perdida_total:,.0f} $; "
        f"margen igual ({e0.margen_operativo:,.0f} $)",
    )

    # Personal desde la dotación: 1·2·2 = 5 personas-turno; S2 +1 suma 5 h de 1 playero; S9 resta
    cat_eco = {e.nombre: e for e in catalogo(p_eco)}
    pe_base = personas_turno_playeros(p_eco)
    pe_s2 = personas_turno_playeros(cat_eco["S2 · Playeros en el pico +1"].aplicar(p_eco))
    pe_s9 = personas_turno_playeros(cat_eco["S9 · Autoservicio (−1 playero por turno)"].aplicar(p_eco))
    controlar(
        abs(pe_base - 5.0) < 1e-9 and abs(pe_s2 - (5.0 + 5.0 / 8.0)) < 1e-9 and abs(pe_s9 - 3.0) < 1e-9,
        "El costo de personal sale de la dotación: base 5 personas-turno, S2 +1 suma 5/8, S9 baja a 3",
        f"base {pe_base:g} · S2 +1 {pe_s2:g} · S9 {pe_s9:g}",
    )
    # S9 ahorra personal y la diferencia sale en la conclusión
    res_eco = correr_catalogo(
        p, 7, replicas=3,
        nombres=("S2 · Playeros en el pico +1", "S6 · Stock extra (s × 1,5)",
                 "S9 · Autoservicio (−1 playero por turno)"),
    )
    conc = {c.id: c for c in conclusiones(res_eco, eco)}
    controlar(
        conc["S9"].d_personal.promedio < 0 < conc["S2"].d_personal.promedio
        and conc["S9"].d_venta_perdida.promedio > 0 > conc["S2"].d_venta_perdida.promedio,
        "S9 ahorra personal pero pierde más ventas; S2 +1 cuesta personal y pierde menos ventas",
        f"S9: personal {conc['S9'].d_personal.promedio / 1e6:+.2f} M, venta perdida "
        f"{conc['S9'].d_venta_perdida.promedio / 1e6:+.2f} M | S2 +1: personal "
        f"{conc['S2'].d_personal.promedio / 1e6:+.2f} M, venta perdida "
        f"{conc['S2'].d_venta_perdida.promedio / 1e6:+.2f} M",
    )
    d6 = decision_s6(res_eco, eco)
    controlar(
        d6 is not None and "playero_menos_stock" in d6 and isinstance(d6["mejor"], str),
        "S6 compara el playero extra con el stock extra en $/mes",
        f"{d6['mejor']}" if d6 else "sin datos",
    )

    # Flete = fijo + $/km × km; con $/km > 0 el origen lejano cuesta más que el cercano
    luj_eco = replace_dc(p_eco, red=replace_dc(p_eco.red, origen="LUJAN"))
    eco_km = replace_dc(eco, flete_por_km=100.0)
    controlar(
        flete_por_pedido(p_eco, eco) == eco.costo_pedido
        and flete_por_pedido(p_eco, eco_km) > flete_por_pedido(luj_eco, eco_km) > eco.costo_pedido
        and abs(km_por_viaje(p_eco) - 2 * 991.3) < 2.0,
        "Flete = fijo + $/km × km de ida y vuelta (Dock Sud ≈ 1.982 km; Luján mucho menos)",
        f"Dock Sud {km_por_viaje(p_eco):,.0f} km · Luján {km_por_viaje(luj_eco):,.0f} km",
    )

    # Anualización: 3 × Σ de los 4 meses, réplica a réplica
    est_eco = correr_estaciones(p, replicas=2)
    anual = anualizar(est_eco, eco)
    por_mes = [economia_de(r, eco) for r in est_eco]
    esperado = [3.0 * sum(m[k].margen_operativo for m in por_mes) for k in range(2)]
    controlar(
        abs(anual["margen_operativo"].promedio - sum(esperado) / 2) < 1e-6
        and abs(anual["ingreso_total"].promedio - anual["costo_total"].promedio
                - anual["margen_operativo"].promedio) < 1e-6 < 1.0,
        "El año estimado es 3 × Σ de los 4 meses y también reconcilia (ingresos − costos = margen)",
        f"margen anual {anual['margen_operativo'].promedio / 1e6:,.1f} M $ "
        f"(± {anual['margen_operativo'].semiamplitud / 1e6:,.1f} M, estimación)",
    )
    eq = margen_de_equilibrio_por_litro(lista_eco[0], eco)
    eco_eq = replace_dc(eco, margen_por_litro=eq)
    margen_eq = economia_mensual(reps_eco[0], p_eco, eco_eq).margen_operativo
    controlar(
        abs(margen_eq) < 1.0 and eq > 0,
        "El margen por litro de equilibrio hace el margen operativo igual a 0",
        f"equilibrio ${eq:,.0f}/L (hoy ${eco.margen_por_litro:,.0f}/L) → margen {margen_eq:,.2f} $",
    )

    # ------------------------------------------------------------------ 23
    separador("23. Fase 9: sensibilidad (tornado de los datos inciertos)")
    from sim.datos import CONTRADICCIONES, REGISTRO, por_id
    from sim.sensibilidad import (
        EJES,
        _tanque_de,
        base_de_sensibilidad,
        contradicciones_y_ejes,
        correr_sensibilidad,
        listado_registro,
    )

    # Gate: lista TODOS los supuesto/heredado/estimación y las contradicciones, sin dejar huecos
    listado = listado_registro()
    tipos_lista = [d for d in REGISTRO if d.tipo in ("supuesto", "heredado", "estimacion")]
    sin_clasificar = [f["ID"] for f in listado if "SIN CLASIFICAR" in f["¿Eje del tornado?"]]
    sin_clasificar += [
        f["ID"] for f in contradicciones_y_ejes() if "SIN CLASIFICAR" in f["En el tornado"]
    ]
    con_alternativas = [
        d for d in tipos_lista if d.alternativas or d.bajo is not None or d.alto is not None
    ]
    controlar(
        len(listado) == len(tipos_lista) and not sin_clasificar
        and len(contradicciones_y_ejes()) == len(CONTRADICCIONES)
        and all(por_id(i) for e in EJES for i in e.datos),
        "El listado cubre todos los supuesto/heredado/estimación y las 20 contradicciones",
        f"{len(listado)} datos ({len(con_alternativas)} con alternativas o rango), "
        f"{len(EJES)} ejes, {sum(len(e.variantes) for e in EJES)} variantes, "
        f"sin clasificar: {sin_clasificar or 'ninguno'}",
    )

    # La cadena de demanda no se rompe al cambiar vehículos o mezcla (no repetir B1)
    p_sen = base_de_sensibilidad(p, 7)
    ejes = {e.id: e for e in EJES}
    p_igual, _ = _tanque_de("auto", 47.0)(p_sen, None)
    p_c12, _ = ejes["C12"].variantes[1][1](p_sen, None)
    p_c6, _ = ejes["C6"].variantes[1][1](p_sen, None)
    mix0 = {x.id: x.pct_litros for x in p_sen.productos}
    mix6 = {x.id: x.pct_litros for x in p_c6.productos}
    ind_c12, _ = simular(p_c12, semilla=91)
    pedido_c12 = (
        ind_c12.c.litros_vendidos + ind_c12.c.litros_no_vendidos
    ) / p_c12.dias_medidos
    controlar(
        abs(p_igual.litros_medios_por_cliente - p_sen.litros_medios_por_cliente) < 1e-9
        and abs(p_c12.litros_medios_por_cliente / p_sen.litros_medios_por_cliente - 0.8 / 0.5) < 0.12
        and abs(sum(mix6.values()) - 1.0) < 1e-9
        and abs(mix6["diesel_g2"] + mix6["diesel_g3"] - mix0["diesel_g2"] - mix0["diesel_g3"]) < 1e-9
        and mix6["diesel_g3"] == 0.0
        and abs(pedido_c12 * 31 / p.litros_mes - 1.0) < 0.04,
        "Cambiar vehículos o mezcla rehace los litros por cliente y conserva la demanda en litros",
        f"carga media 0,8 × T: {p_c12.litros_medios_por_cliente:.1f} L/cliente "
        f"(base {p_sen.litros_medios_por_cliente:.1f}) | litros pedidos por día "
        f"{pedido_c12:,.0f} (esperado ≈ {p.litros_mes / 31:,.0f}) | "
        f"mezcla sólo G2: G3 = {mix6['diesel_g3']:.0%}",
    )

    # El tornado corre y sus resultados son coherentes
    t0 = time.time()
    tor = correr_sensibilidad(p, eco, mes=7, replicas=2)
    seg_tornado = time.time() - t0
    por_eje = {e.id: e for e in tor.ejes}

    def delta(eje: str, k: int, campo: str) -> float:
        return getattr(por_eje[eje].variantes[k], campo).promedio

    controlar(
        len(tor.ejes) == len(EJES)
        and delta("C2", 1, "d_margen") > 0 > delta("C2", 0, "d_margen")
        and delta("C2", 1, "d_espera") > 0 > delta("C2", 0, "d_espera")
        and delta("C5", 1, "d_espera") < 0 < delta("C5", 0, "d_espera")
        and delta("ECO-10", 0, "d_margen") > 0 > delta("ECO-10", 1, "d_margen"),
        "Más demanda ⇒ más margen y más espera; más playeros ⇒ menos espera; menos francos ⇒ más margen",
        f"C2 {delta('C2', 0, 'd_margen') / 1e6:+.1f} M / {delta('C2', 1, 'd_margen') / 1e6:+.1f} M · "
        f"C5 espera {delta('C5', 0, 'd_espera'):+.2f} / {delta('C5', 1, 'd_espera'):+.2f} min "
        f"({seg_tornado:.0f} s)",
    )
    controlar(
        all(
            abs(delta(e, 0, "d_margen") + delta(e, 1, "d_margen")) < 1e-6 * abs(delta(e, 1, "d_margen"))
            and delta(e, 0, "d_espera") == delta(e, 1, "d_espera") == 0.0
            for e in ("ECO-01", "ECO-02", "ECO-03", "ECO-07")
        ),
        "Los ejes económicos son lineales (±50 % simétrico) y no mueven ni la espera ni el servicio",
        "ECO-01, ECO-02, ECO-03 y ECO-07 recalculan sobre las réplicas de la base",
    )
    top_margen = [e.id for e in tor.ranking("margen")][:5]
    top_espera = [e.id for e in tor.ranking("espera")][:5]
    top_servicio = [e.id for e in tor.ranking("servicio")][:5]
    controlar(
        len({tuple(top_margen), tuple(top_espera), tuple(top_servicio)}) > 1,
        "El ranking no es constante: cambia según la métrica",
        f"margen {top_margen} | espera {top_espera} | servicio {top_servicio}",
    )

    # ------------------------------------------------------------------ 24
    separador("24. Fase 10: cadena de demanda litros → clientes (N19)")
    from sim.sensibilidad import _armonica

    p_n19 = para_mes(p, 7)
    errores_n19 = [
        abs(
            p_n19.autos_por_dia_fecha(d) * (1.0 - p_n19.pct_gnc) * p_n19.litros_medios_por_cliente
            / p_n19.litros_del_dia(d) - 1.0
        )
        for d in range(1, p_n19.dias + 1)
    ]
    controlar(
        max(errores_n19) < 0.001,
        "N19: clientes líquidos por día × litros medios por cliente = litros del día (±0,1 %)",
        f"error máximo en los {p_n19.dias} días de julio: {max(errores_n19):.2e}",
    )
    controlar(
        abs(_armonica(p.productos) / p.litros_medios_por_cliente - 1.0) < 0.001,
        "Los litros medios por cliente (DEM-11 = 35,7 L) salen de la mezcla y las cargas de cada producto",
        f"1 ÷ Σ(% de litros ÷ carga media) = {_armonica(p.productos):.3f} L contra "
        f"{p.litros_medios_por_cliente} L del Registro",
    )

    # ------------------------------------------------------------------ 25
    separador("25. Rediseño, etapa 1: simulación con datos reales (sin azar)")
    import dataclasses

    p_dr = para_mes(p, 7).datos_reales()
    r_a, _ = correr_replica(p_dr, semilla=1)
    r_b, _ = correr_replica(p_dr, semilla=987)
    controlar(
        r_a == dataclasses.replace(r_b, semilla=r_a.semilla),
        "Sin azar: dos semillas distintas dan EXACTAMENTE el mismo resultado",
        f"espera pico {r_a.espera_pico:.4f} min · nivel de servicio {r_a.nivel_servicio:.4f} (semillas 1 y 987)",
    )

    ind_dr, traza_dr = simular(
        dataclasses.replace(p_dr, dt_traza=15.0), semilla=1, con_traza=True
    )
    c_dr = ind_dr.c
    esperados = sum(int(round(p_dr.autos_por_dia_fecha(d))) for d in range(1, p_dr.dias + 1))
    controlar(
        c_dr.llegadas == esperados and p_dr.dias_calentamiento == 0,
        "Las llegadas son exactas: la suma de los clientes de cada día, sin calentamiento",
        f"{c_dr.llegadas} clientes en {p_dr.dias} días = {esperados} calculados día por día",
    )

    pesos_dr = dict(zip((pr.id for pr in p_dr.productos), p_dr.pesos_llegada()))
    desvio_mezcla = max(
        abs(ind_dr.c_producto[k].llegadas / c_dr.llegadas - w) for k, w in pesos_dr.items()
    )
    controlar(
        desvio_mezcla < 0.003      # los GNC que migran se cuentan como Súper
        and abs(c_dr.compras_atendidas / c_dr.atendidos_surtidor - p_dr.prob_compra) < 0.005,
        "El producto y la compra en el minimarket salen por cuotas exactas (no por sorteo)",
        f"desvío máximo de la mezcla {desvio_mezcla:.5f} · compran "
        f"{c_dr.compras_atendidas / c_dr.atendidos_surtidor:.3f} (esperado {p_dr.prob_compra})",
    )

    dentro = c_dr.llegadas - c_dr.atendidos_surtidor - (
        c_dr.perdidos_surtidor + c_dr.perdidos_sin_combustible + c_dr.perdidos_cola_llena
        + c_dr.perdidos_corte_gnc
    )
    controlar(
        0 <= dentro <= 12 + 3 * 8 and c_dr.viajes_demorados == 0,
        "N2 sin azar: llegadas = atendidos + perdidos + adentro, y no hay cortes de ruta sorteados",
        f"adentro al final: {dentro} · camiones demorados: {c_dr.viajes_demorados}",
    )

    pedidos_ok = (
        len(ind_dr.pedidos) == c_dr.pedidos_emitidos > 0
        and all(abs((x.t_llegada - x.t_pedido) - 36.0 * 60.0) < 1e-6 for x in ind_dr.pedidos)
        and all(i.nivel_inicial == i.capacidad for i in p_dr.inventario)
        and min(x.t_pedido for x in ind_dr.pedidos) > 0
    )
    controlar(
        pedidos_ok,
        "Los tanques arrancan llenos y cada camión tarda exactamente su plazo medio (36 h)",
        f"{len(ind_dr.pedidos)} pedidos; el primero se pidió el día "
        f"{min(x.t_pedido for x in ind_dr.pedidos) / 1440 + 1:.1f}",
    )

    af = c_dr.gnc_afectados
    controlar(
        af > 0 and c_dr.migrados_gnc_a_nafta + c_dr.perdidos_corte_gnc == af
        and abs(c_dr.migrados_gnc_a_nafta / af - p_dr.gnc.migracion_a_nafta) < 0.1
        and simular(para_mes(p, 1).datos_reales(), semilla=5)[0].c.gnc_afectados == 0,
        "GNC sin azar: los episodios caen siempre en las mismas fechas, la migración es una cuota y en enero no hay cortes",
        f"julio: {af} afectados = {c_dr.migrados_gnc_a_nafta} migrados + {c_dr.perdidos_corte_gnc} perdidos",
    )

    controlar(
        len(traza_dr.cuadros) == int(p_dr.duracion // 15.0)
        and traza_dr.cuadros[-1].t >= p_dr.duracion - 15.0,
        "La animación graba TODOS los días (un cuadro cada 15 min)",
        f"{len(traza_dr.cuadros)} cuadros para {p_dr.dias} días",
    )

    # ------------------------------------------------------------------ 26
    separador("26. Rediseño, etapa 2: el período a simular y las ediciones")
    from sim.config import ParametrosEconomicos
    from sim.periodo import (
        TEMPORADAS,
        Edicion,
        anio_completo,
        aplicar_edicion,
        con_periodo,
        cortes_gnc_previstos,
        litros_de_nivel,
        por_dias,
        por_meses,
        por_temporada,
    )

    pd30 = por_dias(30, 1, 15)
    pm = por_meses(1, 3)
    dias_temporadas = {n: por_temporada(n).dias for n in TEMPORADAS}
    controlar(
        pd30.dias == 30 and pd30.fin.isoformat() == "2026-02-13" and pm.dias == 90
        and pm.fin.isoformat() == "2026-03-31"
        and dias_temporadas == {"Verano": 90, "Otoño": 92, "Invierno": 92, "Primavera": 91}
        and sum(dias_temporadas.values()) == 365 and anio_completo().dias == 365
        and por_temporada("Verano").fin.isoformat() == "2027-02-28",
        "Los períodos del menú suman bien: por días, por meses, 4 estaciones (365 días) y el año",
        f"30 días desde el 15/ene → {pd30.fin}; ene–mar {pm.dias} días; estaciones {dias_temporadas}",
    )

    g_def = ParametrosSimulacion().gnc
    controlar(
        por_temporada("Invierno").incluye_invierno and por_dias(180, 1, 1).incluye_invierno
        and anio_completo().incluye_invierno and not por_temporada("Verano").incluye_invierno
        and not pm.incluye_invierno
        and len(cortes_gnc_previstos(anio_completo(), g_def)) == 2
        and cortes_gnc_previstos(por_temporada("Verano"), g_def) == [],
        "Si el período llega al invierno entran los cortes de GNC (2 episodios fijos); en verano no hay",
        f"año: {cortes_gnc_previstos(anio_completo(), g_def)}",
    )

    base_per = ParametrosSimulacion().datos_reales()
    afect = {
        nombre: simular(con_periodo(base_per, per), semilla=1)[0].c.gnc_afectados
        for nombre, per in (("enero a marzo", pm), ("180 días desde enero", por_dias(180, 1, 1)))
    }
    controlar(
        afect["enero a marzo"] == 0 and afect["180 días desde enero"] > 0,
        "Simulado: enero a marzo no tiene clientes de GNC afectados y 180 días desde enero sí",
        str(afect),
    )

    # Ediciones: nivel de demanda, el doble en la hora pico, GNC, playeros y precio
    eco0 = ParametrosEconomicos()
    p_med, _ = aplicar_edicion(base_per, eco0, Edicion())
    p_alta, _ = aplicar_edicion(base_per, eco0, Edicion(nivel_demanda="alta"))
    p_pico, _ = aplicar_edicion(base_per, eco0, Edicion(doble_pico=True))
    pico = [7, 8, 9, 16, 17]
    fuera = [h for h in range(24) if h not in pico]

    def clientes_hora(pp, h):
        return pp.autos_por_dia * pp.perfil.fracciones[h]

    ok_pico = all(
        abs(clientes_hora(p_pico, h) / clientes_hora(p_med, h) - 2.0) < 1e-9 for h in pico
    ) and all(abs(clientes_hora(p_pico, h) / clientes_hora(p_med, h) - 1.0) < 1e-9 for h in fuera)
    controlar(
        not p_med.determinista and p_med.litros_mes == 270_000.0
        and p_alta.litros_mes == litros_de_nivel("alta") == 400_000.0
        and litros_de_nivel("poca") == 150_000.0 and ok_pico,
        "Editar: poca/media/alta salen del Registro (150/270/400 mil L), el doble en el pico duplica "
        "esas horas y deja igual las demás, y la edición usa azar",
        f"clientes por día: media {p_med.autos_por_dia:.0f} · alta {p_alta.autos_por_dia:.0f} · "
        f"alta con doble pico {aplicar_edicion(base_per, eco0, Edicion(nivel_demanda='alta', doble_pico=True))[0].autos_por_dia:.0f}",
    )

    # Precio por litro: subir el Súper $50 sube el margen exactamente $50 por litro vendido
    r_precio, _ = correr_replica(con_periodo(base_per, por_meses(1, 1)), semilla=1)
    p_mes1 = con_periodo(base_per, por_meses(1, 1))
    e_base = economia_mensual(r_precio, p_mes1, eco0)
    e_caro = economia_mensual(
        r_precio, p_mes1, dataclasses.replace(
            eco0, precios=tuple((k, v + 50.0 if k == "super" else v) for k, v in eco0.precios)
        ),
    )
    litros_super = dict(r_precio.litros_vendidos_por_producto)["super"] * e_base.dias_mes
    controlar(
        abs((e_caro.margen_operativo - e_base.margen_operativo) - 50.0 * litros_super) < 1e-6
        and e_caro.ingreso_gnc == e_base.ingreso_gnc,
        "El precio por litro mueve el margen $ por $: Súper +$50 suma 50 × litros vendidos de Súper",
        f"{litros_super:,.0f} L de Súper ⇒ +{50.0 * litros_super:,.0f} $ de margen",
    )

    # ------------------------------------------------------------------ 27
    separador("27. Rediseño, etapa 3: cola de 3 lugares por cara y datos del tablero")
    from sim.periodo import anio_completo as _anio, por_dias as _pdias
    from ui.animacion import MAXIMO_CUADROS, dt_para, reproductor_html as _html

    base_27 = ParametrosSimulacion().datos_reales()
    caps = {g.id: base_27.capacidad_de(g.id) for g in base_27.grupos}
    controlar(
        caps == {"A": 12, "B": 6, "C": 18}
        and ParametrosSimulacion.clasico().capacidad_de("A") is None,
        "Cada cara tiene 3 lugares de cola: A 12 · B 6 · C 18 (el caso clásico no tiene cola finita)",
        str(caps),
    )

    # Con el doble de demanda en el pico y azar, la cola se llena: nunca pasa de su capacidad
    p_cola, _ = aplicar_edicion(
        con_periodo(base_27, _pdias(10, 7, 1)), ParametrosEconomicos(),
        Edicion(nivel_demanda="alta", doble_pico=True),
    )
    ind_cola, traza_cola = simular(
        dataclasses.replace(p_cola, animar_todo=True, dt_traza=12.0), semilla=3, con_traza=True
    )
    max_cola = {
        g.id: max(c.grupos[i][3] for c in traza_cola.cuadros) for i, g in enumerate(p_cola.grupos)
    }
    controlar(
        all(max_cola[g.id] <= caps[g.id] for g in p_cola.grupos)
        and ind_cola.c_total.perdidos_cola_llena > 0,
        "La cola nunca pasa de sus 3 lugares por cara y, con demanda alta, se llena (cola_llena > 0)",
        f"cola máxima {max_cola} · rechazados por cola llena: {ind_cola.c_total.perdidos_cola_llena}",
    )

    # El tablero: todos los días, litros por producto que coinciden con el motor y peso razonable
    p_t = dataclasses.replace(con_periodo(base_27, _pdias(20, 1, 1)), animar_todo=True, dt_traza=12.0)
    ind_t, traza_t = simular(p_t, semilla=1, con_traza=True)
    ult = traza_t.cuadros[-1]
    lit_ok = all(
        0 <= ind_t.c_producto_total[pr.id].litros_vendidos - ult.litros_producto[k]
        <= 0.01 * ind_t.c_producto_total[pr.id].litros_vendidos + 1.0
        for k, pr in enumerate(p_t.productos)
    ) and all(
        b.litros_producto[k] >= a.litros_producto[k] - 1e-9
        for a, b in zip(traza_t.cuadros, traza_t.cuadros[1:]) for k in range(5)
    )
    controlar(
        lit_ok and len(traza_t.cuadros) == int(p_t.duracion // 12.0),
        "El tablero graba los 20 días y los litros por producto de cada cuadro crecen hasta el total del motor",
        f"{len(traza_t.cuadros):,} cuadros · litros del último cuadro: "
        + ", ".join(f"{x:,.0f}" for x in ult.litros_producto),
    )

    p_y = dataclasses.replace(con_periodo(base_27, _anio()), animar_todo=True, dt_traza=dt_para(365))
    _, traza_y = simular(p_y, semilla=1, con_traza=True)
    peso_y = len(_html(traza_y, p_y, {}, "").encode("utf-8")) / 1e6
    controlar(
        dt_para(30) == 12.0 and dt_para(365) == 36.0 and len(traza_y.cuadros) <= MAXIMO_CUADROS
        and peso_y < 8.0,
        "El año completo se anima con un cuadro cada 36 min y el HTML pesa menos de 8 MB",
        f"{len(traza_y.cuadros):,} cuadros · {peso_y:.2f} MB",
    )

    # ------------------------------------------------------------------ 28
    separador("28. Rediseño, etapa 4: totales enteros y tiempo sin combustible por tanque")
    r28, traza28 = correr_replica(
        con_periodo(ParametrosSimulacion().datos_reales(), por_dias(30, 1, 1)), semilla=1, con_traza=True
    )
    t28 = dict(r28.totales)
    perdidos28 = (
        t28["perdidos_espera"] + t28["perdidos_cola_llena"] + t28["perdidos_sin_combustible"]
        + t28["perdidos_corte_gnc"]
    )
    zonas_llegadas = sum(z[1] for z in r28.totales_zona)
    productos_llegadas = sum(x[1] for x in r28.totales_producto)
    controlar(
        0 <= t28["llegadas"] - t28["atendidos"] - perdidos28 <= 60
        and zonas_llegadas == t28["llegadas"] == productos_llegadas
        and sum(x[2] for x in r28.totales_producto) == t28["atendidos"]
        and sum(traza28.llegadas_por_hora) == t28["llegadas"]
        and sum(d.autos_llegados for d in traza28.dias) == t28["llegadas"],
        "Los totales cierran: llegadas = Σ por zona = Σ por producto = Σ por hora = Σ por día",
        f"{t28['llegadas']} llegadas · {t28['atendidos']} atendidos · {perdidos28} perdidos",
    )
    quiebres = dict(r28.dias_quiebre_total)
    vacios = dict(r28.tiempo_sin_stock)
    controlar(
        all(0.0 <= f <= 1.0 for f in vacios.values())
        and all(vacios[pr] == 0 or quiebres[pr] > 0 for pr in vacios)
        and abs(sum(dict(r28.pedidos_total).values()) - r28.pedidos_dia * 30) < 0.5,
        "Un tanque con tiempo sin combustible tuvo días de quiebre; los camiones pedidos cierran",
        "tiempo sin combustible por tanque: "
        + " · ".join(f"{pr} {100 * f:.1f} %" for pr, f in vacios.items())
        + f" | días con quiebre: {quiebres}",
    )

    # ------------------------------------------------------------------ 29
    separador("29. Parte 2, tanda 3: por qué no se vendió y cada quiebre de stock")
    from sim.periodo import Edicion as _Edicion, aplicar_edicion as _aplicar

    p29, _ = _aplicar(
        con_periodo(ParametrosSimulacion().datos_reales(), por_meses(7, 7)), ParametrosEconomicos(),
        _Edicion(doble_pico=True),
    )
    r29, _ = correr_replica(p29, semilla=3)
    causas = {f[0]: f[1:] for f in r29.litros_perdidos_causa}
    liquidos29 = sum(sum(v) for pr, v in causas.items() if pr != "gnc")
    gnc29 = sum(causas["gnc"])
    controlar(
        abs(liquidos29 - r29.litros_no_vendidos_dia * r29.dias_medidos) < 1e-6
        and abs(gnc29 - r29.m3_gnc_perdidos_dia * r29.dias_medidos) < 1e-6
        and all(v >= 0 for f in causas.values() for v in f),
        "Las causas suman exactamente lo que no se vendió (litros y m³ por separado)",
        f"julio con el doble en el pico: {liquidos29:,.0f} L = Σ causas · GNC {gnc29:,.1f} m³",
    )
    vacio29 = dict(r29.tiempo_sin_stock)
    horas29 = r29.dias_medidos * 24
    controlar(
        all(abs(h - vacio29[pr] * horas29) < 0.01 and (n > 0) == (h > 0) and mx <= h + 1e-9
            for pr, n, h, mx in r29.quiebres),
        "Las horas de cada quiebre suman el tiempo sin combustible del tanque",
        " · ".join(f"{pr}: {n} quiebres, {h:.1f} h (el más largo {mx:.1f} h)" for pr, n, h, mx in r29.quiebres),
    )

    # ------------------------------------------------------------------ 30
    separador("30. Parte 2, tanda 4: los ajustes del menú (economía y GNC)")
    from sim.periodo import Ajustes, aplicar_ajustes, gnc_con_ajustes

    p30 = dataclasses.replace(
        con_periodo(ParametrosSimulacion().datos_reales(), por_meses(7, 7)), animar_todo=False
    )
    eco30 = ParametrosEconomicos()
    p30b, eco30b = aplicar_ajustes(p30, eco30, Ajustes(calendario=False, indices_reales=False, politica="cargada"))   # los valores del Registro
    controlar(
        p30b == p30 and correr_replica(p30b, 1)[0] == correr_replica(p30, 1)[0]
        and all(eco30b.margen_de(x) == eco30.margen_de(x) for x in ("super", "diesel_g3", "gnc"))
        and (eco30b.costo_pedido, eco30b.flete_por_km, eco30b.costo_almacenamiento_litro_mes,
             eco30b.sueldo_playero_mensual)
        == (eco30.costo_pedido, eco30.flete_por_km, eco30.costo_almacenamiento_litro_mes,
            eco30.sueldo_playero_mensual),
        "Con los ajustes por defecto todo da exactamente igual que con el Registro",
        "mismos parámetros, misma réplica y mismos márgenes, flete, almacenamiento y sueldo",
    )
    invierno30 = cortes_gnc_previstos(por_temporada("Invierno"), gnc_con_ajustes(p30.gnc, Ajustes(cortes_gnc="todo_invierno")))
    largos = [(b - a).days + 1 for a, b in invierno30]
    _, eco30m = aplicar_ajustes(p30, eco30, Ajustes(margenes=(("super", 120.0),)))
    controlar(
        len(invierno30) == 2 + 2 and sorted(largos) == [6, 6, 6, 10]
        and cortes_gnc_previstos(por_temporada("Invierno"), gnc_con_ajustes(p30.gnc, Ajustes(cortes_gnc="todo_invierno")))
        == invierno30
        and eco30m.margen_de("super") == 120.0 and eco30m.margen_de("vpower") == eco30.margen_por_litro,
        "'Más cortes en todo el invierno' suma 2 cortes y alarga una cuota (sin azar, siempre igual); márgenes por producto",
        " · ".join(f"{a:%d/%m}–{b:%d/%m}" for a, b in invierno30),
    )

    # ------------------------------------------------------------------ 31
    separador("31. Parte 2, tanda 5: calendario de temporadas y perfil del día por fechas")
    from sim.datos import valor as _valor

    p31 = dataclasses.replace(con_periodo(ParametrosSimulacion().datos_reales(), _anio()), animar_todo=False)
    p31n, _ = aplicar_ajustes(p31, eco30, Ajustes(calendario=True, indices_reales=False, politica="cargada",
                                                  factores=(("verano", 1.0), ("vacaciones_invierno", 1.0), ("invierno", 1.0))))
    p31c, _ = aplicar_ajustes(p31, eco30, Ajustes(calendario=True, indices_reales=False, politica="cargada"))
    factores31 = dict(_valor("DEM-14"))
    dias31 = {"verano": 10, "otoño": 100, "invierno": 160, "vacaciones": 190, "invierno tarde": 200}
    razones = {k: p31c.litros_del_dia(d) / p31.litros_del_dia(d) for k, d in dias31.items()}
    controlar(
        all(abs(p31n.litros_del_dia(d) - p31.litros_del_dia(d)) < 1e-9 for d in range(1, 366))
        and ParametrosSimulacion.clasico().calendario_demanda == () and ParametrosSimulacion().calendario_demanda == ()
        and abs(razones["verano"] - factores31["verano"]) < 1e-9 and abs(razones["otoño"] - 1.0) < 1e-9
        and abs(razones["invierno"] - factores31["invierno"]) < 1e-9
        and abs(razones["vacaciones"] - factores31["vacaciones_invierno"]) < 1e-9
        and abs(razones["invierno tarde"] - factores31["invierno"]) < 1e-9,
        "El calendario multiplica cada fecha por su factor; con factores 1 (o apagado) la demanda no cambia",
        " · ".join(f"{k} ×{v:.2f}" for k, v in razones.items())
        + f" · año {sum(p31c.litros_del_dia(d) for d in range(1, 366)) / sum(p31.litros_del_dia(d) for d in range(1, 366)) - 1:+.2%}",
    )
    r31, traza31 = correr_replica(dataclasses.replace(p31c, fecha_inicio=(7, 1), dias=31), semilla=1, con_traza=True)
    controlar(
        sum(map(sum, traza31.llegadas_dia_hora)) == dict(r31.totales)["llegadas"]
        and [sum(h) for h in traza31.llegadas_dia_hora] == [x.autos_llegados for x in traza31.dias]
        and sum(c[1] for dia in traza31.espera_dia_hora for c in dia) == sum(traza31.espera_dia_hora[0][h][1] for h in range(24))
        + sum(c[1] for dia in traza31.espera_dia_hora[1:] for c in dia),
        "El perfil del día por fechas suma igual que el total: Σ (día, hora) = Σ por día = llegadas",
        f"julio con calendario: {dict(r31.totales)['llegadas']} llegadas en {len(traza31.llegadas_dia_hora)} días",
    )

    # ------------------------------------------------------------------ 32
    separador("32. Parte 2, tanda 6: el escenario único (micro simulación de una semana)")
    from sim.periodo import FRANJAS, EscenarioUnico

    eu_hoy = EscenarioUnico(playeros=2, franja=list(FRANJAS)[0], temporada="Otoño", clientela="media")
    p32 = dataclasses.replace(con_periodo(ParametrosSimulacion().datos_reales(), eu_hoy.periodo()), animar_todo=False)
    p32_hoy = eu_hoy.escenario(p32).aplicar(p32)
    p32_mas = EscenarioUnico(playeros=3, franja=list(FRANJAS)[0], temporada="Otoño", clientela="media").escenario(p32).aplicar(p32)
    p32_max = EscenarioUnico(playeros=2, franja="Todo el día", temporada="Otoño", clientela="máxima").escenario(p32).aplicar(p32)
    controlar(
        correr_replica(p32_hoy, 1)[0] == correr_replica(p32, 1)[0]
        and dict(p32_mas.turnos)[7.0] == 3 and dict(p32_mas.turnos)[10.0] == 2
        and p32_max.playeros_por_turno == (2, 2, 2) and p32_max.litros_mes > 400_000
        and eu_hoy.periodo().dias == 7 and eu_hoy.horas() == (7, 8, 9),
        "El escenario único 'como hoy' da lo mismo que la corrida base; los playeros y la clientela cambian lo pedido",
        f"{eu_hoy.periodo().texto} · turnos con 3 en el pico: {p32_mas.turnos} · clientela máxima: "
        f"{p32_max.litros_mes:,.0f} L/mes con el doble en el pico",
    )

    # ------------------------------------------------------------------ 33
    separador("33. Parte 2, tanda 8: rutas alternativas y orígenes alternativos del camión")
    from sim.red import camino_mas_corto as _cmc, rutas_posibles

    rutas33 = rutas_posibles(p30.red)
    controlar(
        rutas33[0].ruta == _cmc(p30.red).ruta and abs(rutas33[0].km - _cmc(p30.red).km) < 1e-9
        and all(a.km <= b.km for a, b in zip(rutas33, rutas33[1:]))
        and len({c.ruta for c in rutas33}) == len(rutas33),
        "La primera de las rutas posibles es la de Dijkstra y están ordenadas de mejor a peor",
        f"{len(rutas33)} rutas desde Dock Sud: " + " · ".join(f"{c.km:,.0f} km" for c in rutas33),
    )
    _, eco33 = None, ParametrosEconomicos()
    corrida33 = {}
    for etiqueta, aj in (("apagado", Ajustes(calendario=False, indices_reales=False, politica="cargada")),
                          ("sin Dock Sud", Ajustes(calendario=False, indices_reales=False, politica="cargada", origenes_no_disponibles=("DOCK",))),
                          ("eventos", Ajustes(calendario=False, indices_reales=False, politica="cargada", eventos_abastecimiento=True))):
        p33, _ = aplicar_ajustes(dataclasses.replace(p30, fecha_inicio=(1, 1), dias=365), eco33, aj)
        ind33, _ = simular(p33, semilla=1)
        corrida33[etiqueta] = (ind33, correr_replica(p33, 1)[0])
    base33 = correr_replica(dataclasses.replace(p30, fecha_inicio=(1, 1), dias=365), 1)[0]
    plazos_arroyo = {round((x.t_llegada - x.t_pedido) / 60.0, 1) for x in corrida33["sin Dock Sud"][0].pedidos}
    esperado_arroyo = round(36.0 * _cmc(p30.red, origen="ARROYO").km / _cmc(p30.red).km, 1)   # misma velocidad media
    ev = corrida33["eventos"][1].pedidos_por_origen
    controlar(
        corrida33["apagado"][1] == base33
        and all(x.origen == "ARROYO" and x.redirigido for x in corrida33["sin Dock Sud"][0].pedidos)
        and plazos_arroyo == {esperado_arroyo}
        and 0 < sum(x[2] for x in ev) <= 0.08 * sum(x[1] for x in ev),
        "Apagado no cambia nada; sin Dock Sud todo sale de Arroyo Seco con su plazo; con eventos se redirige ≈ 1 de cada 20",
        f"plazo desde Arroyo Seco {sorted(plazos_arroyo)} h (esperado {esperado_arroyo}) · año con eventos: {ev}",
    )

    # ------------------------------------------------------------------ 34
    separador("34. Parte 2, tanda 7: los avisos de la animación salen de la traza")
    from datetime import date
    from sim.distribuciones import AleatorioDeterminista
    from sim.gnc import calendario_de_episodios, intervalos_de_corte
    p34 = dataclasses.replace(con_periodo(ParametrosSimulacion().datos_reales(), por_temporada("Invierno")), animar_todo=False)
    ind34, traza34 = simular(p34, semilla=1, con_traza=True)
    ind34b, _ = simular(p34, semilla=1)
    avisos = [e for e in traza34.eventos if e[0] == "pedido"]
    descargas = [e for e in traza34.eventos if e[0] == "descarga"]
    cortes34 = [e for e in traza34.eventos if e[0] == "corte_gnc"]
    s34 = {i.producto: i.punto_pedido / i.capacidad for i in p34.inventario}
    controlar(
        len(avisos) == len(ind34.pedidos) == ind34b.c.pedidos_emitidos
        and all(abs(a[1] - x.t_pedido) < 1e-9 and a[2] == x.producto for a, x in zip(avisos, ind34.pedidos))
        and all(a[3] <= s34[a[2]] + 1e-9 for a in avisos)
        and len(descargas) == sum(1 for x in ind34.pedidos if x.t_llegada <= p34.duracion)
        and [(round(c[1]), round(c[2])) for c in cortes34]
        == [(round(a), round(b)) for a, b in intervalos_de_corte(p34.gnc, calendario_de_episodios(
            p34.gnc, AleatorioDeterminista(1), date(2026, 6, 1), p34.dias), p34.dias)],
        "Cada aviso de 'bajo nivel' es un camión pedido con el tanque en o bajo s; los cortes coinciden con el calendario",
        f"invierno: {len(avisos)} avisos de pedido, {len(descargas)} descargas, {len(cortes34)} cortes de GNC "
        f"(el más bajo: {min(a[3] for a in avisos):.0%} del tanque)",
    )

    # ------------------------------------------------------------------ 35
    separador("35. Parte 4, etapa E0: el GNC lo carga un playero (PER-04)")
    p35 = dataclasses.replace(con_periodo(ParametrosSimulacion().datos_reales(), por_meses(7, 7)), animar_todo=True)
    auto35 = dataclasses.replace(p35, grupos=tuple(
        dataclasses.replace(g, requiere_playero=False) if g.id == "C" else g for g in p35.grupos))
    _, traza35 = simular(p35, semilla=1, con_traza=True)
    # En cada cuadro: autos cargando (con su playero) en las zonas con playero = playeros ocupados
    descuadres = sum(
        1 for c in traza35.cuadros
        if sum(1 for i, g in enumerate(c.grupos) if p35.grupos[i].requiere_playero
               for k in g[1] if k >= 0 and (k & 1) == 0) != c.playeros_ocupados
    )
    gnc_con_playero = sum(
        1 for c in traza35.cuadros for i, g in enumerate(c.grupos)
        if "gnc" in p35.grupos[i].productos for k in g[1] if k >= 0 and (k & 1) == 0
    )
    r35, _ = correr_replica(p35, semilla=1)
    ra35, _ = correr_replica(auto35, semilla=1)
    t35, ta35 = dict(r35.totales), dict(ra35.totales)
    lam = p35.perfil.tasa_maxima(p35.autos_por_dia)
    rho_mano = lam * ((1 - p35.pct_gnc) * p35.media_servicio_liquidos()
                      + p35.pct_gnc * p35.carga_gnc.media) / p35.playeros_maximos
    rho_auto = lam * (1 - p35.pct_gnc) * p35.media_servicio_liquidos() / p35.playeros_maximos
    controlar(
        _valor("PER-04") is True and p35.gnc_con_playero and not auto35.gnc_con_playero
        and descuadres == 0 and gnc_con_playero > 0
        and abs(p35.rho_pico - rho_mano) < 1e-12 and abs(auto35.rho_pico - rho_auto) < 1e-12
        and t35["llegadas"] == ta35["llegadas"] and t35["atendidos"] <= ta35["atendidos"],
        "El GNC usa playero: autos cargando = playeros ocupados en cada cuadro, y ρ cuenta los minutos del GNC",
        f"julio: {len(traza35.cuadros)} cuadros sin descuadre ({gnc_con_playero} cuadros-auto de GNC con playero) · "
        f"ρ pico {auto35.rho_pico:.3f} → {p35.rho_pico:.3f} · atendidos {ta35['atendidos']} (autoservicio) → "
        f"{t35['atendidos']} (con playero)",
    )

    # ------------------------------------------------------------------ 36
    separador("36. Parte 4, etapa E1: eventos de personal y equipos (sorteo y mecanismos)")
    from sim.config import ParametrosEventos
    from sim.eventos import calendario

    E1 = ("EVT-01", "EVT-02", "EVT-03", "EVT-04", "EVT-05", "EVT-06", "EVT-07", "EVT-08", "EVT-14")
    base36 = con_periodo(ParametrosSimulacion().datos_reales(), por_meses(1, 1))
    def con_ev(activos, semilla=1, frecuencia=1.0, p=base36):
        return dataclasses.replace(p, eventos=ParametrosEventos(activos=activos, semilla=semilla, frecuencia=frecuencia))
    cal_todos = calendario(con_ev(E1))
    cal_solo = calendario(con_ev(("EVT-05",)))
    cal_otra = calendario(con_ev(E1, semilla=2))
    r_base, _ = correr_replica(base36, semilla=1)
    r_cero, _ = correr_replica(con_ev(E1, frecuencia=0.0), semilla=1)
    controlar(
        cal_todos == calendario(con_ev(E1)) and cal_todos != cal_otra and len(cal_todos) > 0
        and cal_solo == tuple(e for e in cal_todos if e.id == "EVT-05")
        and calendario(base36) == () and tuple(r_cero.totales) == tuple(r_base.totales),
        "El sorteo de los eventos: misma semilla ⇒ mismo calendario; prender uno no corre a los otros; sin eventos, idéntico",
        f"enero, semilla 1: {len(cal_todos)} eventos ({len(cal_solo)} fallas de surtidor, las mismas solas); "
        f"semilla 2: {len(cal_otra)}",
    )

    # Mecanismos: cada uno en su propia corrida de enero (5 veces más seguido), con la animación de todos los días
    import bisect

    def correr36(activos, frecuencia=5.0):
        p_ = dataclasses.replace(con_ev(activos, frecuencia=frecuencia), animar_todo=True)
        r_, tr_ = correr_replica(p_, semilla=1, con_traza=True)
        return p_, r_, tr_.cuadros, [c.t for c in tr_.cuadros]

    def en(cuadros, tiempos, desde, hasta):
        return cuadros[bisect.bisect_left(tiempos, desde):bisect.bisect_left(tiempos, hasta)]

    def sueltos(eventos):
        return [a for a in eventos if not any(b is not a and a.inicio < b.fin and b.inicio < a.fin for b in eventos)]

    def descuadres(p_, cuadros):
        return sum(1 for c in cuadros if sum(
            1 for k_, g in enumerate(c.grupos) if p_.grupos[k_].requiere_playero
            for k in g[1] if k >= 0 and (k & 1) == 0) != c.playeros_ocupados)

    def turno_base(p_, t):
        h = (t % 1440) / 60.0
        return [n for hora, n in p_.turnos if hora <= h][-1]

    pA, rA, cA, tA = correr36(("EVT-07", "EVT-14"))
    paradas = sueltos(rA.eventos)
    parada_ok = all(c.playeros_en_turno == 0 and c.playeros_ocupados == 0
                    for e in paradas for c in en(cA, tA, e.inicio + 30.0, e.fin))
    pB, rB, cB, tB = correr36(("EVT-01", "EVT-03"))
    playero = sueltos(rB.eventos)
    playero_ok = all(c.playeros_en_turno == max(0, turno_base(pB, c.t) - 1)
                     for e in playero for c in en(cB, tB, e.inicio + 1.0, e.fin)) and all(
        c.playeros_en_turno == turno_base(pB, c.t) for e in playero for c in en(cB, tB, e.fin + 1.0, e.fin + 60.0)
        if not any(o.inicio <= c.t < o.fin for o in rB.eventos)
    )
    pC, rC, cC, tC = correr36(("EVT-05",))
    caras = sueltos(rC.eventos)
    ventanas05 = [(e.inicio, e.fin) for e in rC.eventos]
    cara_ok = all(any(-2 in g[1] for g in c.grupos) for e in caras for c in en(cC, tC, e.inicio + 120.0, e.fin)) \
        and not any(any(-2 in g[1] for g in c.grupos) and not any(a <= c.t < b for a, b in ventanas05) for c in cC)
    pD, rD, cD, tD = correr36(("EVT-06",))
    compresor = sueltos(rD.eventos)
    compresor_ok = all(c.compresores_total == pD.gnc.compresores - 1
                       for e in compresor for c in en(cD, tD, e.inicio + 1.0, e.fin))
    pE, rE, _, _ = correr36(E1, frecuencia=10.0)
    tE = dict(rE.totales)
    perdidosE = tE["perdidos_espera"] + tE["perdidos_cola_llena"] + tE["perdidos_sin_combustible"] + tE["perdidos_corte_gnc"]
    controlar(
        parada_ok and playero_ok and cara_ok and compresor_ok and min(len(paradas), len(playero), len(caras), len(compresor)) > 0
        and descuadres(pA, cA) + descuadres(pB, cB) + descuadres(pC, cC) + descuadres(pD, cD) == 0
        and 0 <= tE["llegadas"] - tE["atendidos"] - perdidosE <= 60
        and tE["atendidos"] < dict(r_base.totales)["atendidos"] and sum(e.perdidos for e in rE.eventos) > 0,
        "Cada mecanismo hace lo que dice: estación parada sin playeros, un playero menos hasta el cambio de turno, "
        "cara tachada y un compresor menos; los clientes se conservan",
        f"enero ×5, cada uno solo y sin superponerse: {len(paradas)} paradas, {len(playero)} de un playero, {len(caras)} "
        f"caras, {len(compresor)} compresores · todos ×10: {len(rE.eventos)} eventos, atendidos "
        f"{dict(r_base.totales)['atendidos']} → {tE['atendidos']}, {sum(e.perdidos for e in rE.eventos)} clientes perdidos "
        f"durante los eventos",
    )

    # ------------------------------------------------------------------ 37
    separador("37. Parte 4, etapa E2: precio, abastecimiento y demanda; costo de los eventos")
    from datetime import date as _date, timedelta as _td
    from sim.economia_real import economia_mensual

    # Llegadas: base + los de más (aumento de precio el día anterior, evento masivo) − los que no llegaron (avenida)
    r37, _ = correr_replica(con_ev(("EVT-09", "EVT-12", "EVT-13"), frecuencia=3.0), semilla=1)
    mas = sum(e.extra for e in r37.eventos if e.id in ("EVT-09", "EVT-13"))
    menos = sum(e.extra for e in r37.eventos if e.id == "EVT-12")
    ids37 = {e.id for e in r37.eventos}
    llegadas_ok = dict(r37.totales)["llegadas"] == dict(r_base.totales)["llegadas"] + mas - menos
    # Faltante con cupo todo el mes: nadie carga más de 30 L; los camiones traen la mitad y tardan el plazo de crisis
    p_cupo = con_ev(("EVT-10",), frecuencia=365.0)
    ind_cupo, _ = simular(p_cupo, semilla=1)
    cupo = _valor("EVT-10")[3]
    liquidos = [pr.id for pr in p_cupo.productos if not pr.es_gnc]
    vendidos = sum(ind_cupo.c_producto[x].litros_vendidos for x in liquidos)
    atendidos_l = sum(ind_cupo.c_producto[x].atendidos for x in liquidos)
    q_por = {i.producto: i.cantidad_pedido for i in p_cupo.inventario}
    cupo_ok = (vendidos <= cupo * atendidos_l + 1e-6 and ind_cupo.pedidos
               and all(abs(x.litros - q_por[x.producto] * _valor("EVT-10")[4]) < 1e-6
                       and x.t_llegada - x.t_pedido >= _valor("INV-09")[0] * 60.0 - 1e-6 for x in ind_cupo.pedidos))
    # Rotura del camión: cada rotura es un pedido que llega entre 12 y 48 h más tarde
    p_rot = con_ev(("EVT-11",), frecuencia=4.0)
    ind_rot, _ = simular(p_rot, semilla=1)
    r_rot, _ = correr_replica(p_rot, semilla=1)
    roturas = [e for e in r_rot.eventos if e.id == "EVT-11"]
    rotura_ok = roturas and all(
        12.0 <= e.extra <= 48.0 and any(abs(x.t_pedido - e.inicio) < 1e-9 and abs(x.t_llegada - e.fin) < 1e-6
                                         for x in ind_rot.pedidos) for e in roturas)
    # Costo: horas extra de las licencias cubiertas, calculadas a mano (8 h por día; domingo 100 %, el resto 50 %)
    eco37 = ParametrosEconomicos()
    p_lic = con_ev(("EVT-02",), frecuencia=20.0)
    r_lic, _ = correr_replica(p_lic, semilla=1)
    horas = [(8.0, (_date(2026, 1, 1) + _td(days=int(e.inicio // 1440) + k)).weekday() == 6)
             for e in r_lic.eventos for k in range(int(e.valor)) if int(e.inicio // 1440) + k < p_lic.dias]
    valor_hora = eco37.sueldo_playero_mensual / _valor("EVT-15")
    a_mano = sum(h * valor_hora * (2.0 if domingo else 1.5) for h, domingo in horas) * 31 / r_lic.dias_medidos
    e_lic = economia_mensual(r_lic, p_lic, eco37)
    costo_ok = (horas and abs(e_lic.costo_eventos - a_mano) < 1e-6
                and abs(e_lic.costo_total - (e_lic.flete + e_lic.almacenamiento + e_lic.personal_total + e_lic.costo_eventos)) < 1e-6
                and tuple(r_lic.totales) == tuple(r_base.totales))
    controlar(
        llegadas_ok and {"EVT-09", "EVT-12", "EVT-13"} <= ids37 and cupo_ok and rotura_ok and costo_ok,
        "Precio, abastecimiento y demanda hacen lo que dicen, y el costo de los eventos es el de las horas extra",
        f"llegadas {dict(r_base.totales)['llegadas']} + {mas:.0f} − {menos:.0f} = {dict(r37.totales)['llegadas']} · cupo: "
        f"{vendidos / max(atendidos_l, 1):.1f} L por carga, {len(ind_cupo.pedidos)} camiones con la mitad · "
        f"{len(roturas)} roturas · {len(horas)} turnos de horas extra = ${e_lic.costo_eventos:,.0f}/mes "
        f"(la licencia cubierta no cambia el servicio)",
    )

    # ------------------------------------------------------------------ 38
    separador("38. Parte 4, etapa E3: del menú a la simulación (eventos aleatorios)")
    from sim.eventos import CATALOGO as CATALOGO_EV, texto_frecuencia
    from sim.periodo import Ajustes, aplicar_ajustes

    base38 = con_periodo(ParametrosSimulacion().datos_reales(), por_meses(1, 1))
    p_sin, _ = aplicar_ajustes(base38, ParametrosEconomicos(), Ajustes())
    todos38 = tuple(t.id for t in CATALOGO_EV)
    p_con, _ = aplicar_ajustes(base38, ParametrosEconomicos(),
                               Ajustes(eventos=todos38, semilla_eventos=7, frecuencia_eventos=5.0))
    r38, tr38 = correr_replica(dataclasses.replace(p_con, animar_todo=True), semilla=1, con_traza=True)
    avisos38 = [e for e in tr38.eventos if e[0] == "evento"]
    controlar(
        p_sin.eventos.activos == () and Ajustes().cambios() == []
        and p_con.eventos == ParametrosEventos(activos=todos38, semilla=7, frecuencia=5.0)
        and len(avisos38) == len(r38.eventos) > 0
        and all(texto_frecuencia(t.id) for t in CATALOGO_EV) and len(CATALOGO_EV) == 14,
        "El menú sin eventos deja la corrida del Registro; con eventos, cada evento ocurrido es un aviso del tablero",
        f"enero, los 14 prendidos ×5 (semilla 7): {len(r38.eventos)} eventos = {len(avisos38)} avisos en la traza",
    )

    # ------------------------------------------------------------------ 39
    separador("39. Parte 3, etapa P2: métodos de pronóstico contra el práctico de la cátedra")
    from sim import pronostico as pron

    cable = [1704, 1712, 1752, 1764, 1805, 1835, 1831, 1866, 1884, 1930, 1919, 1951]
    cable_f = [1702, 1725, 1749, 1772, 1795, 1818, 1841, 1864, 1887, 1910, 1933, 1956]
    e_cable = pron.errores(cable, cable_f)
    a_c, b_c = pron.recta(cable)
    controlar(
        abs(e_cable.mae - 107 / 12) < 1e-9 and abs(e_cable.rmse - 37 / 12 ** 0.5) < 1e-9
        and all(abs(f - (a_c + b_c * t)) <= 0.6 for t, f in enumerate(cable_f))
        and [1650 + 30 * t for t in (12, 13, 14)] == [2010, 2040, 2070],
        "Práctico de Pronóstico (Cable Televisora): MAE, RMSE y la recta de mínimos cuadrados",
        f"MAE = 107/12 = {e_cable.mae:.4f} · RMSE = 37/√12 = {e_cable.rmse:.4f} · la recta de los datos "
        f"(A = {a_c:.1f}, B = {b_c:.2f}) da los pronósticos del práctico redondeados · A=1650, B=30 ⇒ 2010, 2040, 2070",
    )
    aj_pm, ad_pm = pron.promedio_movil([10, 20, 30], 2, 1)
    aj_se, ad_se = pron.suavizado([10, 20, 30], 0.5, 1)
    lincoln = [21, 39, 35, 21, 23, 38, 31, 23, 25, 34, 38, 20, 24, 43, 40, 20]
    i_lin = pron.indices_estacionales(lincoln, [t % 4 for t in range(16)], 4)
    analisis = pron.analizar()
    elegido = min(analisis.ajustes, key=lambda a: a.errores.rmse)
    banda = _valor("PRO-03") * elegido.errores.rmse
    controlar(
        aj_pm == [None, None, 15.0] and ad_pm == [25.0] and aj_se == [None, 10.0, 15.0] and ad_se == [22.5]
        and abs(sum(i_lin) / 4 - 1) < 1e-12 and i_lin[1] > 1 and i_lin[3] < 1
        and abs(sum(analisis.indices) / 12 - 1) < 1e-12 and len(analisis.reales) == 56 and analisis.n_prueba == 12
        and analisis.elegido == elegido.metodo
        and all(abs((h - l) / 2 - banda) < 1e-6 for l, h in analisis.intervalo),
        "Promedio móvil y suavizado a mano; índices estacionales que promedian 1; se elige el de menor RMSE",
        f"Lincoln: índices {', '.join(f'{x:.2f}' for x in i_lin)} · Shell Mendoza (ene-2022 – ago-2026, 12 de prueba): "
        + " · ".join(f"{a.metodo} {a.errores.rmse:,.0f}" for a in analisis.ajustes)
        + f" ⇒ {analisis.elegido} (MAPE {100 * elegido.errores.mape:.1f} %)",
    )

    # ------------------------------------------------------------------ 40
    separador("40. Parte 3, etapa P3: la forma real de la demanda como opción del menú")
    from datetime import date as _d40, timedelta as _t40
    from sim.periodo import anio_completo as _anio40

    base40 = con_periodo(ParametrosSimulacion().datos_reales(), _anio40())
    p_def, _ = aplicar_ajustes(base40, ParametrosEconomicos(), Ajustes())
    p_neu, _ = aplicar_ajustes(base40, ParametrosEconomicos(), Ajustes(calendario=False, indices_reales=False))
    p_real, _ = aplicar_ajustes(base40, ParametrosEconomicos(), Ajustes(calendario=False, indices_reales=True))
    indices40 = pron.analizar().indices

    def litros_mes40(p_, mes):
        return sum(p_.litros_del_dia(d) for d in range(1, 366) if (_d40(2026, 1, 1) + _t40(d - 1)).month == mes)

    total_neu = sum(p_neu.litros_del_dia(d) for d in range(1, 366))
    total_real = sum(p_real.litros_del_dia(d) for d in range(1, 366))
    proporcional = all(abs(litros_mes40(p_real, m) / litros_mes40(p_real, 6) - indices40[m - 1] / indices40[5]) < 1e-9
                       for m in range(1, 13))
    controlar(
        p_def.estacionalidad == p_real.estacionalidad and p_def.calendario_demanda == ()
        and abs(total_real - total_neu) < 1e-6 and proporcional and p_real.calendario_demanda == ()
        and "calendario de temporadas en vez de los índices reales" in Ajustes(indices_reales=False, calendario=True).cambios(),
        "Los índices de la serie real reparten los mismos litros del año, mes a mes según su índice",
        f"año: {total_neu:,.0f} L sin forma = {total_real:,.0f} L con los índices reales · marzo ÷ junio = "
        f"{litros_mes40(p_real, 3) / litros_mes40(p_real, 6):.3f} = {indices40[2] / indices40[5]:.3f} · "
        "sin tocar el menú sigue el calendario de temporadas",
    )

    # ------------------------------------------------------------------ 41
    separador("41. Parte 3, etapa P4: el punto de pedido con el stock de seguridad del pronóstico")
    import math as _m41

    base41 = con_periodo(ParametrosSimulacion().datos_reales(), _anio40())
    calc41 = pron.stock_de_seguridad(base41)
    cero41 = pron.stock_de_seguridad(base41, z=0.0)
    analisis41 = pron.analizar()
    elegido41 = next(a for a in analisis41.ajustes if a.metodo == analisis41.elegido)
    error41 = elegido41.errores.rmse / (sum(analisis41.reales[-12:]) / 12)
    parte41 = {pr.id: pr.pct_litros for pr in base41.productos}
    a_mano = []
    for i in base41.inventario:
        d = base41.litros_mes / 30 * parte41[i.producto]
        largo = i.plazo_entrega.media / 24
        a_mano.append(min(round(d * largo + 1.96 * error41 * d * 30 / _m41.sqrt(30) * _m41.sqrt(largo), -2),
                          i.capacidad - 500))
    p_carg, _ = aplicar_ajustes(base41, ParametrosEconomicos(), Ajustes(politica="cargada"))
    p_pron, _ = aplicar_ajustes(base41, ParametrosEconomicos(), Ajustes(politica="pronostico"))
    r_carg, _ = correr_replica(p_carg, semilla=1)
    r_pron, _ = correr_replica(p_pron, semilla=1)
    t_carg, t_pron = dict(r_carg.totales), dict(r_pron.totales)
    controlar(
        [x.s for x in calc41] == a_mano
        and all(x.s == min(round(x.consumo_dia * x.plazo_dias, -2), i.capacidad - 500)
                for x, i in zip(cero41, base41.inventario))
        and [i.punto_pedido for i in p_pron.inventario] == [x.s for x in calc41]
        and [i.cantidad_pedido for i in p_pron.inventario] == [i.cantidad_pedido for i in base41.inventario]
        and t_pron["perdidos_sin_combustible"] <= t_carg["perdidos_sin_combustible"]
        and t_pron["llegadas"] == t_carg["llegadas"],
        "s = D·L + z·σ_día·√L a mano; con z = 0 queda la demanda del plazo; con la opción del menú la corrida la usa",
        f"error del pronóstico {100 * error41:.2f} % · s (L): " + " · ".join(f"{x.producto} {x.s:,.0f}" for x in calc41)
        + f" · año completo: sin combustible {t_carg['perdidos_sin_combustible']} → {t_pron['perdidos_sin_combustible']}, "
        f"días con quiebre {t_carg['dias_con_quiebre']} → {t_pron['dias_con_quiebre']}, camiones "
        f"{sum(dict(r_carg.pedidos_total).values())} → {sum(dict(r_pron.pedidos_total).values())}",
    )

    # ------------------------------------------------------------------ 45
    separador("45. §24, G1: la tabla de camiones (cada pedido, su ruta y sus km)")
    from sim.config import ParametrosRed
    from sim.red import demora_si_encuentra_el_corte, ruta_del_viaje

    red45 = ParametrosRed()
    km_dock = sum(a.km for a in red45.arcos if {a.a, a.b} in ({"DOCK", "ALVEAR"}, {"ALVEAR", "SANRAFAEL"}))
    base45 = con_periodo(ParametrosSimulacion().datos_reales(), por_meses(1, 1))

    r45, _ = correr_replica(base45, semilla=1)
    d_dock = demora_si_encuentra_el_corte(red45, "E4")
    d_arroyo = demora_si_encuentra_el_corte(dataclasses.replace(red45, origen="ARROYO"), "E4")
    desvio, como_d = ruta_del_viaje(red45, "DOCK", d_dock, "corte E4")
    espera, como_e = ruta_del_viaje(red45, "ARROYO", d_arroyo, "corte E4")
    normal, como_n = ruta_del_viaje(red45, "DOCK", 0.0, "")
    controlar(
        len(r45.camiones) == sum(dict(r45.pedidos_total).values()) > 0
        and all(x.t_pedido >= base45.calentamiento for x in r45.camiones)
        and abs(sum(x.litros for x in r45.camiones) - sum(i.cantidad_pedido for i in base45.inventario
                                                          for x in r45.camiones if x.producto == i.producto)) < 1e-6
        and como_d == "desvío por el corte" and desvio.ruta == ("DOCK", "LUJAN", "PAREDITAS", "SANRAFAEL")
        and como_e == "esperó que reabrieran" and espera.ruta == ("ARROYO", "ALVEAR", "SANRAFAEL")
        and como_n == "ruta óptima" and abs(normal.km - km_dock) < 1e-9,
        "Un camión por pedido (= los pedidos de Indicadores); la ruta recorrida se reconstruye: desvío o espera",
        f"enero: {len(r45.camiones)} camiones · con E4, Dock Sud se desvía ({desvio.km:,.1f} km, +{d_dock / 60:.1f} h) y "
        f"Arroyo Seco espera ({d_arroyo / 60:.0f} h, misma ruta)",
    )

    # ------------------------------------------------------------------ 46
    separador("46. Valores por defecto de la app: índices reales y la política más conveniente (INV-13)")
    from sim.economia import analizar_politicas_real
    from sim.runner import PuntoBarrido, ResultadoBarridoReal, con_politicas, correr_replicas, politica_en_dias

    base46, eco46 = aplicar_ajustes(con_periodo(ParametrosSimulacion().datos_reales(), _anio40()),
                                    ParametrosEconomicos(), Ajustes(politica="cargada"))
    candidatas = grilla_politicas_real(base46) + [pron.politica_por_pronostico(base46)]
    hechos46 = [PuntoBarrido(politicas=pol, replicas=correr_replicas(con_politicas(base46, pol), replicas=1, semilla_base=1))
                for pol in candidatas]
    costos46 = analizar_politicas_real(
        ResultadoBarridoReal(productos=tuple(i.producto for i in base46.inventario), puntos=hechos46), eco46, base46)
    total46 = [sum(lista[k].costo_total for lista in costos46.values()) for k in range(len(candidatas))]
    elegida = politica_en_dias(base46, *_valor("INV-13"))
    k46 = candidatas.index(elegida)
    p_app, _ = aplicar_ajustes(con_periodo(ParametrosSimulacion().datos_reales(), _anio40()),
                               ParametrosEconomicos(), Ajustes())
    controlar(
        total46[k46] == min(total46) and len(candidatas) == 14
        and {i.producto: (i.punto_pedido, i.cantidad_pedido) for i in p_app.inventario} == elegida
        and p_app.estacionalidad == p_real.estacionalidad and p_app.calendario_demanda == ()
        and Ajustes().cambios() == [],
        "La app usa por defecto los índices de la serie real y la política más barata de las 14 en el año",
        f"año con datos reales: INV-13 (s = {_valor('INV-13')[0]:g}, Q = {_valor('INV-13')[1]:g} días) ${total46[k46]:,.0f}/mes · "
        f"pronóstico ${total46[-1]:,.0f} · INV-07 ${total46[0]:,.0f} · la más cara ${max(total46):,.0f}",
    )

    # ------------------------------------------------------------------ 47
    separador("47. Economía: el estado de resultados (ventas − compras − costos) da el margen operativo")
    from sim.economia_real import estado_de_resultados, resultado_con_margen

    r47, _ = correr_replica(p_app, semilla=1)
    e47 = economia_mensual(r47, p_app, eco46)
    renglones47 = estado_de_resultados(r47, p_app, eco46)
    ingresos47 = sum(x.importe for x in renglones47 if x.tipo == "ingreso")
    costos47 = sum(x.importe for x in renglones47 if x.tipo == "costo")
    controlar(
        abs((ingresos47 - costos47) - e47.margen_operativo) < 1e-3
        and all(abs(x.cantidad * x.precio - x.importe) < 1e-3 for x in renglones47 if x.unidad != "mes")
        and all(_valor(i) is not None for x in renglones47 for i in x.datos)
        and abs(resultado_con_margen(e47, eco46, eco46.margen_por_litro) - e47.margen_operativo) < 1e-3
        and abs(resultado_con_margen(e47, eco46, margen_de_equilibrio_por_litro(e47, eco46))) < 1e-3,
        "Ventas al precio del cartel − compras (precio − margen) − fletes, sueldos y almacenamiento = margen "
        "operativo; con el margen de equilibrio el resultado es 0",
        f"enero: {len(renglones47)} renglones · ventas ${ingresos47:,.0f} − costos ${costos47:,.0f} = "
        f"${e47.margen_operativo:,.0f}",
    )

    # ------------------------------------------------------------------ 48
    separador("48. EVT-05: la falla es de un surtidor de doble cara (sus dos caras quedan tachadas)")
    from sim.config import ParametrosEventos as _PE48

    p48 = dataclasses.replace(con_periodo(ParametrosSimulacion().datos_reales(), por_meses(1, 1)), animar_todo=True,
                              eventos=_PE48(activos=("EVT-05",), semilla=1, frecuencia=5.0))
    r48, tr48 = correr_replica(p48, semilla=1, con_traza=True)
    tachados48 = [[k for k, v in enumerate(g[1]) if v == -2] for c in tr48.cuadros for g in c.grupos]
    tachados48 = [x for x in tachados48 if x]
    controlar(
        len(r48.eventos) > 0 and len(tachados48) > 0
        and all(len(x) == 2 and x[0] % 2 == 0 and x[1] == x[0] + 1 for x in tachados48),
        "Cada falla de surtidor tacha las dos caras del mismo surtidor (2k y 2k+1), nunca una sola",
        f"enero ×5: {len(r48.eventos)} fallas · {len(tachados48)} cuadros con un surtidor tachado",
    )

    # ------------------------------------------------------------------ 49
    separador("49. Fórmulas de colas y la tabla de errores del pronóstico, contra la cátedra (23/10/2026)")
    from sim.colas import costo_total, mms
    from sim import pronostico as pr49

    banco = mms(8, 10)
    nacion3, nacion4 = mms(30, 12, 3), mms(30, 12, 4)
    taxi = {s: costo_total(s, 24, 100 / 24, mms(1 / 12, 1 / 21, s).l) for s in (2, 3)}
    controlar(
        abs(banco.wq - 0.4) < 1e-9 and abs(banco.l - 4) < 1e-9 and abs(banco.lq - 3.2) < 1e-9
        and abs(60 * nacion3.wq - 7.02) < 0.01 and abs(60 * nacion4.wq - 1.07) < 0.01
        and round(taxi[2], 2) == 79.11 and round(taxi[3], 2) == 81.24,
        "M/M/1 y M/M/s como en la práctica: banco (Wq = 0,4 h, L = 4), Banco Nación (≈ 7 min con 3 cajeros, ≈ 1 con 4) "
        "y NY Taxi (2 mecánicos $79,11/h < 3 mecánicos $81,24/h)",
        f"Banco Nación: Wq {60 * nacion3.wq:.2f} / {60 * nacion4.wq:.2f} min · NY Taxi {taxi[2]:.2f} vs {taxi[3]:.2f}",
    )
    reales49 = [1704, 1712, 1752, 1764, 1805, 1835, 1831, 1866, 1884, 1930, 1919, 1951]
    pron49 = [1702, 1725, 1749, 1772, 1795, 1818, 1841, 1864, 1887, 1910, 1933, 1956]
    comp49 = pr49.comparar([(2025, m) for m in range(1, 13)], pron49, reales49)
    infl49 = pr49.inflacion_real()
    minimo49, maximo49, _ = _valor("PRO-05")
    anio49, _ = correr_replica(con_periodo(ParametrosSimulacion().datos_reales(), por_meses(1, 3)), semilla=1)
    controlar(
        abs(comp49.mae - 8.92) < 0.01 and abs(comp49.rmse - 10.68) < 0.01
        and abs(comp49.mae - pr49.errores(reales49, pron49).mae) < 1e-9
        and pr49.inflacion_real() == infl49 and all(minimo49 <= i <= maximo49 for i in infl49)
        and abs(pr49.factores_de_precio([0.02, 0.03])[-1] - 1.02 * 1.03) < 1e-12
        and [m for _, m, _, _ in anio49.por_mes] == [1, 2, 3]
        and sum(n for _, _, n, _ in anio49.por_mes) == sum(x.autos_llegados for x in correr_replica(
            con_periodo(ParametrosSimulacion().datos_reales(), por_meses(1, 3)), semilla=1, con_traza=True)[1].dias),
        "Ejercicio 1 del parcial (Cable Televisora): MAE = 8,92 y RMSE = 10,68; la inflación sorteada queda en el rango "
        "de PRO-05 y siempre es la misma; los clientes por mes suman los del día a día",
        f"MAE {comp49.mae:.2f} · MAPE {100 * comp49.mape:.2f} % · RMSE {comp49.rmse:.2f} · inflación "
        + " ".join(f"{100 * i:.1f}" for i in infl49),
    )

    # ------------------------------------------------------------------
    print()
    if _fallas == 0:
        print(f"Todos los controles pasaron ({_total} en total). El motor se comporta como corresponde.")
        return 0
    print(f"{_fallas} control(es) de {_total} fallaron. Revisar antes de sacar conclusiones.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
