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
"""

from __future__ import annotations

from dataclasses import replace

from sim.config import (
    ESTACIONALIDAD_PROXY,
    MINUTOS_POR_DIA,
    ParametrosSimulacion,
    dias_y_fecha,
)
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
    separador("2. Conservación de clientes")
    ind, _ = simular(p, semilla=11)
    t = ind.c_total
    salidas = t.atendidos_surtidor + t.perdidos_surtidor + t.perdidos_sin_combustible
    en_sistema = t.llegadas - salidas
    controlar(
        0 <= en_sistema <= p.surtidores + 30,
        "Llegadas = atendidos + abandonos + sin combustible + los que quedaron adentro",
        f"{t.llegadas} = {t.atendidos_surtidor} + {t.perdidos_surtidor} + "
        f"{t.perdidos_sin_combustible} + {en_sistema}",
    )
    controlar(
        t.compras_atendidas + t.perdidos_caja <= t.entraron_minimarket,
        "Al minimarket no entra nadie que no haya cargado",
        f"entraron {t.entraron_minimarket}, cobrados {t.compras_atendidas}, "
        f"abandonos {t.perdidos_caja}",
    )

    # ------------------------------------------------------------------ 3
    separador("3. Ley de Little (L = lambda * W) en la cola del surtidor")
    p_largo = replace(p, dias=60, dias_calentamiento=2)
    ind, _ = simular(p_largo, semilla=13)
    periodo = (p_largo.dias - p_largo.dias_calentamiento) * MINUTOS_POR_DIA

    # Tiempo total de espera acumulado por todos los que hicieron cola: los atendidos
    # esperaron lo que registró el colector y los que abandonaron esperaron exactamente
    # su paciencia. Los que se fueron por falta de combustible nunca hicieron cola.
    espera_total = (
        ind.espera_surtidor.suma + ind.c.perdidos_surtidor * p_largo.paciencia_surtidor
    )
    lq_por_little = espera_total / periodo
    lq_medido = ind.cola_surtidor.promedio
    error = abs(lq_medido - lq_por_little) / max(lq_por_little, 1e-9)
    controlar(
        error < 0.05,
        "La cola promedio medida por área coincide con la que predice Little",
        f"medida {lq_medido:.4f} autos | Little {lq_por_little:.4f} autos | "
        f"diferencia {error * 100:.2f} %",
    )

    # ------------------------------------------------------------------ 4
    separador("4. Utilización")
    controlar(
        0.0 <= ind.utilizacion_surtidores <= 1.0,
        "La utilización de los surtidores está entre 0 % y 100 %",
        f"{ind.utilizacion_surtidores * 100:.2f} %",
    )
    trabajo_esperado = ind.c.atendidos_surtidor * p_largo.carga.media
    trabajo_medido = ind.ocupados_surtidores.promedio * periodo
    error_trabajo = abs(trabajo_medido - trabajo_esperado) / trabajo_esperado
    controlar(
        error_trabajo < 0.05,
        "El tiempo de surtidor ocupado coincide con atendidos x tiempo medio de carga",
        f"medido {trabajo_medido:,.0f} min | esperado {trabajo_esperado:,.0f} min | "
        f"diferencia {error_trabajo * 100:.2f} %",
    )

    # ------------------------------------------------------------------ 5
    separador("5. Monotonía (el modelo reacciona como corresponde)")
    escenarios = correr_escenarios(p, replicas=3, semilla_base=1)
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
    separador("6. Monte Carlo: la demanda sorteada respeta la tabla empírica")
    p_muchos = replace(
        p, dias=400, dias_calentamiento=1, modo_demanda="monte_carlo"
    )
    _, traza = correr_replica(p_muchos, semilla=5, con_traza=True)
    sorteos = [d.autos_sorteados for d in traza.dias]
    media_simulada = sum(sorteos) / len(sorteos)
    error_media = abs(media_simulada - p.demanda.media) / p.demanda.media
    controlar(
        error_media < 0.03,
        "La media de la demanda sorteada coincide con la de la tabla",
        f"simulada {media_simulada:.1f} autos/día | tabla {p.demanda.media:.1f} | "
        f"diferencia {error_media * 100:.2f} % ({len(sorteos)} días)",
    )
    peor = 0.0
    for valor, probabilidad in zip(p.demanda.valores, p.demanda.probabilidades):
        observada = sorteos.count(valor) / len(sorteos)
        peor = max(peor, abs(observada - probabilidad))
    controlar(
        peor < 0.05,
        "Cada valor de la tabla sale con la frecuencia que le corresponde",
        f"la mayor diferencia entre probabilidad observada y teórica es {peor * 100:.2f} puntos",
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
    separador("8. Inventario: conservación de litros")
    ind_inv, _ = simular(p, semilla=23)
    t = ind_inv.c_total
    esperado = p.tanque.nivel_inicial + t.litros_recibidos - t.litros_vendidos
    diferencia = abs(ind_inv.nivel_tanque.valor - esperado)
    controlar(
        diferencia < 1.0,
        "Nivel final = nivel inicial + litros recibidos - litros vendidos",
        f"{ind_inv.nivel_tanque.valor:,.1f} L medidos vs {esperado:,.1f} L calculados "
        f"(recibidos {t.litros_recibidos:,.0f} L, vendidos {t.litros_vendidos:,.0f} L)",
    )
    controlar(
        ind_inv.nivel_tanque.minimo >= -1e-6,
        "El tanque nunca queda en negativo",
        f"nivel mínimo alcanzado: {ind_inv.nivel_tanque.minimo:,.1f} L",
    )
    controlar(
        ind_inv.nivel_tanque.maximo <= p.tanque.capacidad + 1e-6,
        "El tanque nunca supera su capacidad",
        f"nivel máximo alcanzado: {ind_inv.nivel_tanque.maximo:,.1f} L de "
        f"{p.tanque.capacidad:,.0f} L",
    )
    controlar(
        0.0 <= ind_inv.nivel_servicio <= 1.0,
        "El nivel de servicio está entre 0 % y 100 %",
        f"{ind_inv.nivel_servicio * 100:.2f} %",
    )

    # ------------------------------------------------------------------ 9
    separador("9. Inventario: la política hace lo que tiene que hacer")
    tacaña, _ = correr_replica(con_politica(p, 4_000, 20_000), semilla=29)
    generosa, _ = correr_replica(con_politica(p, 20_000, 20_000), semilla=29)
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
    chico, _ = correr_replica(con_politica(p, 12_000, 10_000), semilla=29)
    grande, _ = correr_replica(con_politica(p, 12_000, 30_000), semilla=29)
    controlar(
        chico.pedidos_dia > grande.pedidos_dia,
        "Pedir de a poco obliga a pedir más seguido (más fletes)",
        f"pedidos de 10.000 L: {chico.pedidos_dia * 30:.1f} pedidos/mes | "
        f"de 30.000 L: {grande.pedidos_dia * 30:.1f} pedidos/mes",
    )

    # ------------------------------------------------------------------ 10
    separador("10. N1: el caso clásico reproduce los números dorados (§14.1)")
    clasico = ParametrosSimulacion.clasico()
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

    from sim.config import ParametrosEconomicos, ParametrosTanque
    from sim.datos import MAPA_PARAMETROS, REGISTRO as REGISTRO_DATOS

    ids_registro = {d.id for d in REGISTRO_DATOS}
    huerfanos = []
    for clase in (ParametrosSimulacion, ParametrosTanque, ParametrosEconomicos):
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
        "app.py", "ui/graficos.py", "ui/animacion.py", "ui/datos_ui.py",
        "ui/textos.py",
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

    # ------------------------------------------------------------------
    print()
    if _fallas == 0:
        print(f"Todos los controles pasaron ({_total} en total). El motor se comporta como corresponde.")
        return 0
    print(f"{_fallas} control(es) de {_total} fallaron. Revisar antes de sacar conclusiones.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
