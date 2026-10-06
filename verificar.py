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

  FASE 6 DEL ORQUESTADOR (GNC)
   24. N7 (sin episodios no hay pérdidas; corte total sin migración pierde a todos), N8
       (migrados + perdidos = afectados), N12 (invierno > verano), formas del corte y
       compresores como límite de las cargas simultáneas.

  FASE 5 DEL ORQUESTADOR (red de rutas)
   23. N6 (km y minutos de §5-G), Dijkstra = fuerza bruta, demora por corte, la red sin
       cortes no cambia nada y N11 (cortes, playeros y demanda).
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
    holgura = caras_total + len(p.grupos) * (p.capacidad_cola or 0)
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
        if not 0 <= adentro <= g.caras + (p.capacidad_cola or 0):
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
        ParametrosGNC,
        ParametrosRed,
        ParametrosTanque,
    )
    from sim.datos import MAPA_PARAMETROS, REGISTRO as REGISTRO_DATOS

    ids_registro = {d.id for d in REGISTRO_DATOS}
    huerfanos = []
    for clase in (
        ParametrosSimulacion, ParametrosTanque, ParametrosEconomicos, ParametrosRed, ParametrosGNC,
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
        g[3] <= p_anim.capacidad_cola for c in cuadros for g in c.grupos
    )
    progresos = [t[3] for c in cuadros for t in c.tanques]
    controlar(
        limite_cola and all(-1.0 <= x <= 1.0 for x in progresos),
        "La cola visible respeta la capacidad y el progreso del camión está entre 0 y 1",
        f"cola máxima {max(g[3] for c in cuadros for g in c.grupos)} de {p_anim.capacidad_cola}",
    )
    from ui.animacion import reproductor_html
    peso_mb = len(reproductor_html(traza_anim, p_anim, 3, "").encode("utf-8")) / 1e6
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
    controlar(
        r_sin == r_ning == r_enero,
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
        cierra = cierra and 0 <= adentro <= gr.caras + (p_jul.capacidad_cola or 0)
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

    # ------------------------------------------------------------------
    print()
    if _fallas == 0:
        print(f"Todos los controles pasaron ({_total} en total). El motor se comporta como corresponde.")
        return 0
    print(f"{_fallas} control(es) de {_total} fallaron. Revisar antes de sacar conclusiones.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
