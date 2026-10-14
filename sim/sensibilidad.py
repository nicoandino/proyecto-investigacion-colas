"""Sensibilidad: el tornado de los datos inciertos (Fase 9, ORQUESTADOR §7.8).

Para cada eje (una contradicción C1–C19 del §4.2 o un dato con rango/alternativas en el
Registro) se corre la estación con cada extremo, **dejando todo lo demás en la base y con las
mismas semillas** (números aleatorios comunes). Se informa el cambio, réplica a réplica, de:

  · el **margen operativo mensual** (pesos),
  · la **espera en la hora pico** (minutos) y
  · el **nivel de servicio** (puntos de %).

Los ejes puramente económicos (márgenes, sueldos, flete) no necesitan volver a simular: se
recalculan sobre las réplicas de la base. **Los extremos salen del Registro** (`bajo`/`alto` o las
`alternativas` de cada `Dato`); donde el Registro no tenía rango se agregó uno rotulado "de
prueba" (ECO-01/02/03/06/07/10) y los presets de carga (VEH-07).

`listado_registro` enumera TODOS los datos supuesto/heredado/estimación con sus alternativas y
dice cuáles son eje y por qué los demás no (control del gate de la Fase 9).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from sim.config import (
    ESTACIONALIDAD_LEVE,
    ESTACIONALIDAD_PROXY,
    _TIPOS_MATRIZ,
    ParametrosEconomicos,
    ParametrosSimulacion,
    PerfilHorario,
    Triangular,
    turnos_de,
)
from sim.datos import CONTRADICCIONES, REGISTRO, por_id, valor
from sim.economia_real import economia_mensual
from sim.escenarios import cambios_cierre_nocturno, para_mes
from sim.runner import Resumen, correr_replicas, resumen_de

Aplicar = Callable[[ParametrosSimulacion, ParametrosEconomicos], tuple[ParametrosSimulacion, ParametrosEconomicos]]


# =============================================================================
# Lectura de extremos del Registro
# =============================================================================
def _alt(id_: str, prefijo: str):
    """Valor de la alternativa del Registro cuyo nombre empieza con `prefijo`."""
    for nombre, v, _ in por_id(id_).alternativas:
        if nombre.startswith(prefijo):
            return v
    raise KeyError(f"{id_} no tiene la alternativa '{prefijo}'")


def _bajo(id_: str) -> float:
    return por_id(id_).bajo


def _alto(id_: str) -> float:
    return por_id(id_).alto


def _num(x: float) -> str:
    """Número para una etiqueta: 150.000, 0,15, 2,4."""
    if abs(x) >= 1000:
        return f"{x:,.0f}".replace(",", ".")
    return f"{x:g}".replace(".", ",")


# =============================================================================
# Cadena de demanda: si cambian los vehículos o la mezcla, cambian los litros por cliente
# =============================================================================
def _armonica(productos) -> float:
    """Litros medios por cliente líquido = 1 ÷ Σ (% de litros ÷ carga media) (§14.2)."""
    return 1.0 / sum(pr.pct_litros / pr.carga_media for pr in productos if not pr.es_gnc)


def _recalcular(
    p: ParametrosSimulacion, tipos=None, mezcla: dict[str, float] | None = None
) -> ParametrosSimulacion:
    """Rehace la carga media por producto y los litros por cliente tras cambiar vehículos o mezcla.

    Sin esto, cambiar el tanque de un vehículo cambiaría los litros pero no la cantidad de
    clientes que hacen falta para vender los litros del mes (se repetiría el error B1).
    """
    tipos = tipos or p.tipos_vehiculo
    por_tipo = {t.id: t for t in tipos}
    matriz = dict(p.matriz_tipos)
    nuevos = []
    for pr in p.productos:
        if pr.es_gnc:
            nuevos.append(pr)
            continue
        media = sum(w * por_tipo[t].litros.media for t, w in zip(_TIPOS_MATRIZ, matriz[pr.id]))
        pct = mezcla[pr.id] if mezcla else pr.pct_litros
        nuevos.append(replace(pr, carga_media=media, pct_litros=pct))
    escala = _armonica(nuevos) / _armonica(p.productos)
    return replace(
        p, tipos_vehiculo=tuple(tipos), productos=tuple(nuevos),
        litros_medios_por_cliente=p.litros_medios_por_cliente * escala,
    )


def _preset_carga(preset: str) -> Aplicar:
    a, m, b = dict(valor("VEH-07"))[preset]

    def aplicar(p, eco):
        tipos = tuple(
            t if t.es_gnc else replace(
                t, litros=Triangular(a * t.tanque, m * t.tanque, b * t.tanque)
            )
            for t in p.tipos_vehiculo
        )
        return _recalcular(p, tipos=tipos), eco

    return aplicar


def _tanque_de(id_tipo: str, litros: float) -> Aplicar:
    def aplicar(p, eco):
        tipos = tuple(
            replace(t, tanque=litros,
                    litros=Triangular(0.20 * litros, 0.30 * litros, 1.00 * litros))
            if t.id == id_tipo else t
            for t in p.tipos_vehiculo
        )
        return _recalcular(p, tipos=tipos), eco

    return aplicar


def _mezcla_diesel(parte_g2: float) -> Aplicar:
    def aplicar(p, eco):
        pct = {pr.id: pr.pct_litros for pr in p.productos}
        diesel = pct["diesel_g2"] + pct["diesel_g3"]
        pct["diesel_g2"], pct["diesel_g3"] = diesel * parte_g2, diesel * (1.0 - parte_g2)
        return _recalcular(p, mezcla=pct), eco

    return aplicar


# =============================================================================
# Los ejes
# =============================================================================
@dataclass(frozen=True)
class _Eje:
    id: str                      # "C2"
    nombre: str
    conflicto: str               # "C2" ("" si no es una contradicción)
    datos: tuple[str, ...]       # ids del Registro que cubre
    variantes: tuple[tuple[str, Aplicar], ...]
    solo_economia: bool = False  # no hace falta volver a simular
    nota: str = ""
    rango_de_prueba: bool = False  # los extremos son de prueba (no es dato del Registro)


def _p(**cambios) -> Aplicar:
    """Cambia campos de `ParametrosSimulacion`."""
    return lambda p, eco: (replace(p, **cambios), eco)


def _e(**cambios) -> Aplicar:
    """Cambia campos de `ParametrosEconomicos`."""
    return lambda p, eco: (p, replace(eco, **cambios))


def _gnc(**cambios) -> Aplicar:
    return lambda p, eco: (replace(p, gnc=replace(p.gnc, **cambios)), eco)


def _red(**cambios) -> Aplicar:
    return lambda p, eco: (replace(p, red=replace(p.red, **cambios)), eco)


def _menos_uno(p, eco):
    n = tuple(max(1, x - 1) for x in p.playeros_por_turno)
    return replace(p, playeros_por_turno=n, turnos=turnos_de(n)), eco


def _mas_playeros(p, eco):
    n = tuple(_alt("PER-01", "2"))
    return replace(p, playeros_por_turno=n, turnos=turnos_de(n)), eco


def _capacidad_tanques(capacidad: float) -> Aplicar:
    def aplicar(p, eco):
        nuevos = []
        for i in p.inventario:
            s = min(i.punto_pedido, capacidad)
            nuevos.append(replace(
                i, capacidad=capacidad,
                nivel_inicial=capacidad * i.nivel_inicial / i.capacidad,
                punto_pedido=s, cantidad_pedido=min(i.cantidad_pedido, capacidad - s),
            ))
        return replace(p, inventario=tuple(nuevos)), eco

    return aplicar


def _cierre_nocturno(p, eco):
    return replace(p, **cambios_cierre_nocturno(p)), eco


def _gnc_retiene_playero(p, eco):
    grupos = tuple(replace(g, requiere_playero=True) if g.id == "C" else g for g in p.grupos)
    return replace(p, grupos=grupos), eco


def _construir_ejes() -> tuple[_Eje, ...]:
    d_quin = valor("DEM-12")
    return (
        _Eje("C1", "Horario de la playa", "C1", ("EST-06",),
             (("cierre nocturno 22–06", _cierre_nocturno),),
             nota="la base es 24 h; la alternativa pierde la demanda nocturna"),
        _Eje("C2", "Demanda mensual", "C2", ("DEM-01",),
             ((f"{_num(_bajo('DEM-01'))} L/mes", _p(litros_mes=_bajo("DEM-01"))),
              (f"{_num(_alto('DEM-01'))} L/mes", _p(litros_mes=_alto("DEM-01"))))),
        _Eje("C4", "Entrada al minimarket", "C4", ("DEM-08",),
             ((f"{_bajo('DEM-08'):.0%}", _p(prob_compra=_bajo("DEM-08"))),
              (f"{_alto('DEM-08'):.0%}", _p(prob_compra=_alto("DEM-08"))))),
        _Eje("C5", "Personal (playeros por turno)", "C5", ("PER-01", "PER-02", "PER-03"),
             (("−1 por turno (autoservicio, C15)", _menos_uno),
              ("2 · 3 · 3 (ONBOARDING)", _mas_playeros))),
        _Eje("C6", "Mix diésel G2/G3", "C6", ("SUR-03", "DEM-04"),
             (("G2/G3 = 75/25", _mezcla_diesel(_alt("DEM-04", "G2/G3"))),
              ("sólo G2 (100/0)", _mezcla_diesel(_alt("DEM-04", "sólo G2"))))),
        _Eje("C8", "Clientes GNC (6 caras vs. ≈ 3 %)", "C8", ("DEM-05",),
             ((f"{_alt('DEM-05', '11'):.0%} de las llegadas", _p(pct_gnc=_alt("DEM-05", "11"))),
              (f"{_alto('DEM-05'):.0%} de las llegadas", _p(pct_gnc=_alto("DEM-05"))))),
        _Eje("C9", "GNC en invierno", "C9",
             ("GNC-01", "GNC-02", "GNC-04", "GNC-06", "SUR-06", "PER-04"),
             (("contrato firme (sin cortes)", _gnc(contrato="firme")),
              (f"{_alto('GNC-02')} episodios de {_alto('GNC-06')} días, migración "
               f"{_bajo('GNC-04'):.0%}",
               _gnc(episodios=_alto("GNC-02"), dias_por_episodio=_alto("GNC-06"),
                    migracion_a_nafta=_bajo("GNC-04"))),
              (f"{_alt('SUR-06', '2')} compresores", _gnc(compresores=_alt("SUR-06", "2"))),
              ("el GNC retiene playero", _gnc_retiene_playero)),
             nota="la base fuerza los episodios de corte adentro del mes (si no, el azar los deja afuera)"),
        _Eje("C10", "Estacionalidad", "C10", ("DEM-06",),
             (("leve ±6 %", _p(estacionalidad=ESTACIONALIDAD_LEVE)),
              ("proxy turístico", _p(estacionalidad=ESTACIONALIDAD_PROXY)))),
        _Eje("C11", "Tiempo de servicio", "C11", ("TIE-02", "TIE-04", "TIE-05"),
             (("nafta (2,4 · 3,7 · 5,0) min", _p(carga=Triangular(*_alt("TIE-02", "nota")))),
              ("GNC (10 · 15 · 30) min", _p(carga_gnc=Triangular(*_alt("TIE-04", "nota")))),
              ("caja (1,5 · 3 · 6) min", _p(compra=Triangular(*_alt("TIE-05", "heredado")))))),
        _Eje("C12", "Litros por carga", "C12", ("VEH-07",),
             (("media 0,3 × tanque", _preset_carga("bajo")),
              ("media 0,8 × tanque", _preset_carga("alto"))),
             nota="los litros del mes no cambian: cambia cuántos clientes hacen falta"),
        _Eje("C13", "Tanques de vehículos", "C13", ("VEH-01", "VEH-03", "VEH-04"),
             ((f"auto {_num(_bajo('VEH-01'))} L", _tanque_de("auto", _bajo("VEH-01"))),
              (f"auto {_num(_alto('VEH-01'))} L", _tanque_de("auto", _alto("VEH-01"))),
              (f"camión {_num(_bajo('VEH-04'))} L", _tanque_de("camion", _bajo("VEH-04"))),
              (f"camión {_num(_alto('VEH-04'))} L", _tanque_de("camion", _alto("VEH-04"))),
              (f"moto {_num(_bajo('VEH-03'))} L", _tanque_de("moto", _bajo("VEH-03"))),
              (f"moto {_num(_alto('VEH-03'))} L", _tanque_de("moto", _alto("VEH-03"))))),
        _Eje("C16", "Perfil horario", "C16", ("DEM-02",),
             (("perfil heredado (picos 08 y 19 h)",
               _p(perfil=PerfilHorario(tuple(_alt("DEM-02", "heredado"))))),)),
        _Eje("C17", "Fin de semana y quincena", "C17", ("DEM-03", "DEM-12"),
             ((f"fin de semana ×{_num(_bajo('DEM-03'))}", _p(factor_fin_de_semana=_bajo("DEM-03"))),
              (f"fin de semana ×{_num(_alto('DEM-03'))}", _p(factor_fin_de_semana=_alto("DEM-03"))),
              (f"quincena ×{_num(d_quin[0])} (días {', '.join(map(str, d_quin[1]))})",
               _p(factor_quincena=d_quin[0], dias_quincena=tuple(d_quin[1]))))),
        _Eje("C18", "Salarios", "C18", ("ECO-04", "ECO-04C"),
             (("sueldos básicos, sin adicionales",
               _e(sueldo_playero_mensual=_alt("ECO-04", "básicos")[0],
                  sueldo_cajero_mensual=_alt("ECO-04", "básicos")[1],
                  sueldo_encargado_mensual=_alt("ECO-04", "básicos")[2])),
              (f"cajero heredado ${_num(_alt('ECO-04C', 'heredado'))}",
               _e(sueldo_cajero_mensual=_alt("ECO-04C", "heredado")))),
             solo_economia=True),
        # --- Ejes sin contradicción numerada pero con rango en el Registro --------------------
        _Eje("PER-05", "Capacidad de la cola por zona", "", ("PER-05",),
             ((f"{_bajo('PER-05')} autos por zona", _p(capacidad_cola=_bajo("PER-05"), cola_por_cara=None)),
              (f"{_alto('PER-05')} autos por zona", _p(capacidad_cola=_alto("PER-05"), cola_por_cara=None)))),
        _Eje("PER-06", "Disciplina de cola", "", ("PER-06",),
             (("una fila por cara", _p(disciplina_cola="por_cara")),)),
        _Eje("TIE-06", "Paciencia en la cola del surtidor", "", ("TIE-06",),
             ((f"{_num(_bajo('TIE-06'))} min", _p(paciencia_surtidor=_bajo("TIE-06"))),
              (f"{_num(_alto('TIE-06'))} min", _p(paciencia_surtidor=_alto("TIE-06"))))),
        _Eje("INV-03", "Capacidad de cada tanque", "", ("INV-03",),
             ((f"{_num(_bajo('INV-03'))} L", _capacidad_tanques(_bajo("INV-03"))),
              (f"{_num(_alto('INV-03'))} L", _capacidad_tanques(_alto("INV-03"))))),
        _Eje("INV-05", "Origen del camión", "", ("INV-05",),
             (("Luján de Cuyo", _red(origen="LUJAN")),)),
        _Eje("RED-13", "Probabilidad de corte de ruta por viaje", "", ("RED-13",),
             ((f"{_bajo('RED-13'):.0%}", _red(prob_corte_viaje=_bajo("RED-13"))),
              (f"{_alto('RED-13'):.0%}", _red(prob_corte_viaje=_alto("RED-13"))))),
        # --- Economía (no vuelve a simular) ----------------------------------------------------
        _Eje("ECO-01", "Margen por litro", "", ("ECO-01",),
             ((f"${_num(_bajo('ECO-01'))}/L", _e(margen_por_litro=_bajo("ECO-01"))),
              (f"${_num(_alto('ECO-01'))}/L", _e(margen_por_litro=_alto("ECO-01")))),
             solo_economia=True, nota="rango de prueba, no es dato", rango_de_prueba=True),
        _Eje("ECO-02", "Margen por compra en el minimarket", "", ("ECO-02",),
             ((f"${_num(_bajo('ECO-02'))}", _e(margen_compra=_bajo("ECO-02"))),
              (f"${_num(_alto('ECO-02'))}", _e(margen_compra=_alto("ECO-02")))),
             solo_economia=True, nota="rango de prueba, no es dato", rango_de_prueba=True),
        _Eje("ECO-03", "Margen por m³ de GNC", "", ("ECO-03",),
             ((f"${_num(_bajo('ECO-03'))}/m³", _e(margen_gnc=_bajo("ECO-03"))),
              (f"${_num(_alto('ECO-03'))}/m³", _e(margen_gnc=_alto("ECO-03")))),
             solo_economia=True, nota="rango de prueba, no es dato", rango_de_prueba=True),
        _Eje("ECO-06", "Flete fijo por viaje", "", ("ECO-06",),
             ((f"${_num(_bajo('ECO-06'))}", _e(costo_pedido=_bajo("ECO-06"))),
              (f"${_num(_alto('ECO-06'))}", _e(costo_pedido=_alto("ECO-06")))),
             solo_economia=True, nota="rango de prueba; $150.000 es implausible para ≈ 1.000 km",
             rango_de_prueba=True),
        _Eje("ECO-07", "Costo de almacenamiento", "", ("ECO-07",),
             ((f"${_num(_bajo('ECO-07'))}/L-mes", _e(costo_almacenamiento_litro_mes=_bajo("ECO-07"))),
              (f"${_num(_alto('ECO-07'))}/L-mes", _e(costo_almacenamiento_litro_mes=_alto("ECO-07")))),
             solo_economia=True, nota="rango de prueba, no es dato", rango_de_prueba=True),
        _Eje("ECO-10", "Cobertura de francos del personal", "", ("ECO-10",),
             ((f"{_num(_bajo('ECO-10'))} personas por puesto", _e(cobertura_francos=_bajo("ECO-10"))),
              (f"{_num(_alto('ECO-10'))} personas por puesto", _e(cobertura_francos=_alto("ECO-10")))),
             solo_economia=True, rango_de_prueba=True),
    )


EJES: tuple[_Eje, ...] = _construir_ejes()


# =============================================================================
# Resultados
# =============================================================================
@dataclass(frozen=True)
class ResultadoVariante:
    etiqueta: str
    margen: Resumen              # margen operativo mensual de la variante (pesos)
    d_margen: Resumen            # variante − base, réplica a réplica
    d_espera: Resumen            # Δ espera en la hora pico (min)
    d_servicio: Resumen          # Δ nivel de servicio (0 a 1)


@dataclass(frozen=True)
class ResultadoEje:
    id: str
    nombre: str
    conflicto: str
    datos: tuple[str, ...]
    nota: str
    solo_economia: bool
    variantes: tuple[ResultadoVariante, ...]
    rango_de_prueba: bool = False

    def oscilacion(self, metrica: str) -> float:
        """Cuánto mueve el eje la métrica: el mayor |Δ| de sus extremos."""
        return max(abs(getattr(v, f"d_{metrica}").promedio) for v in self.variantes)


@dataclass(frozen=True)
class ResultadoSensibilidad:
    mes: int
    replicas: int
    base_margen: Resumen
    base_espera: Resumen
    base_servicio: Resumen
    ejes: tuple[ResultadoEje, ...]

    def ranking(self, metrica: str = "margen") -> list[ResultadoEje]:
        """Los ejes ordenados del que más mueve la métrica al que menos."""
        return sorted(self.ejes, key=lambda e: e.oscilacion(metrica), reverse=True)


def base_de_sensibilidad(p: ParametrosSimulacion, mes: int) -> ParametrosSimulacion:
    """La base del tornado: el mes real completo y, con GNC, los episodios de corte adentro.

    Sin forzar los episodios, el azar los deja fuera de la mayoría de las réplicas y el eje C9
    no se vería. Es la misma herramienta de análisis que usa la pestaña GNC.
    """
    base = para_mes(p, mes)
    if base.gnc is not None:
        base = replace(base, gnc=replace(base.gnc, episodios_en_horizonte=True))
    return base


def correr_sensibilidad(
    p: ParametrosSimulacion,
    eco: ParametrosEconomicos,
    mes: int = 7,
    replicas: int = 2,
    semilla_base: int = 1,
    ids: tuple[str, ...] | None = None,
) -> ResultadoSensibilidad:
    """Corre el tornado: la base y cada extremo de cada eje, con las mismas semillas."""
    if not p.estacion_real:
        raise ValueError("La sensibilidad es del caso real.")
    p_base = base_de_sensibilidad(p, mes)
    reps_base = correr_replicas(p_base, replicas=replicas, semilla_base=semilla_base)
    econ_base = [economia_mensual(r, p_base, eco) for r in reps_base]

    ejes = []
    for eje in EJES:
        if ids is not None and eje.id not in ids:
            continue
        variantes = []
        for etiqueta, aplicar in eje.variantes:
            p_v, eco_v = aplicar(p_base, eco)
            reps_v = reps_base if eje.solo_economia else correr_replicas(
                p_v, replicas=replicas, semilla_base=semilla_base
            )
            econ_v = [economia_mensual(r, p_v, eco_v) for r in reps_v]
            variantes.append(
                ResultadoVariante(
                    etiqueta=etiqueta,
                    margen=resumen_de([e.margen_operativo for e in econ_v]),
                    d_margen=resumen_de(
                        [v.margen_operativo - b.margen_operativo for b, v in zip(econ_base, econ_v)]
                    ),
                    d_espera=resumen_de(
                        [v.espera_pico - b.espera_pico for b, v in zip(reps_base, reps_v)]
                    ),
                    d_servicio=resumen_de(
                        [v.nivel_servicio - b.nivel_servicio for b, v in zip(reps_base, reps_v)]
                    ),
                )
            )
        ejes.append(
            ResultadoEje(
                id=eje.id, nombre=eje.nombre, conflicto=eje.conflicto, datos=eje.datos,
                nota=eje.nota, solo_economia=eje.solo_economia, variantes=tuple(variantes),
                rango_de_prueba=eje.rango_de_prueba,
            )
        )
    return ResultadoSensibilidad(
        mes=mes,
        replicas=replicas,
        base_margen=resumen_de([e.margen_operativo for e in econ_base]),
        base_espera=resumen_de([r.espera_pico for r in reps_base]),
        base_servicio=resumen_de([r.nivel_servicio for r in reps_base]),
        ejes=tuple(ejes),
    )


# =============================================================================
# Listado completo (gate de la Fase 9)
# =============================================================================
#: Datos con rango o alternativas que NO son eje, y por qué (cada motivo es verificable).
NO_ES_EJE: dict[str, str] = {
    "MOD-01": "es el caso clásico (otro modelo), no un valor incierto: se elige en la barra lateral",
    "PER-07": "reemplaza a PER-05: la cola es de 3 lugares por cara (el eje PER-05 sigue variando la capacidad por zona)",
    "MOD-02": "elige entre la simulación con datos reales (sin azar) y la que tiene azar: no es un valor",
    "INV-12": "condición de arranque de la simulación con datos reales (tanques llenos); el modo con azar usa INV-10",
    "DEM-00": "cambia el tratamiento del azar de la demanda (esperada vs. Monte Carlo), no un valor",
    "INV-02": "informativo: el modelo pide la Q de la política (s, Q), no la capacidad del camión",
    "INV-09": "sólo vale dentro del escenario S7 (crisis de abastecimiento): la base no tiene crisis",
    "INV-11": "sólo vale dentro del escenario S7 (crisis de abastecimiento): la base no tiene crisis",
    "RED-01": "114 vs. 114,8 km: 0,8 km sobre 222; el plazo base es INV-01 y no cambia",
    "RED-12": "son los escenarios de corte S4 (pestaña Escenarios), no un valor",
    "GNC-03": "las formas del corte son el escenario S3 (pestaña Escenarios)",
    "GNC-07": "herramienta de análisis (forzar el corte adentro): la base del tornado ya la usa",
    "GNC-08": "opción del menú ('más cortes en todo el invierno'), apagada en la base; la cantidad de cortes "
              "ya es el eje GNC-02",
    "GNC-09": "sólo vale con la opción 'más cortes en todo el invierno'; la duración del corte ya es el eje GNC-06",
    "GNC-10": "sólo vale con la opción 'más cortes en todo el invierno'; la duración del corte ya es el eje GNC-06",
}

#: Contradicciones del §4.2 que no son eje y por qué.
CONTRADICCION_SIN_EJE: dict[str, str] = {
    "C3": "corrección de unidades (litros ≠ autos), no un valor incierto: la cadena §14.2 es la regla",
    "C7": "la mezcla se evalúa con C6 (G2/G3) y C8 (% de clientes GNC)",
    "C14": "el lavadero y otros servicios no se modelan (fuera de alcance)",
    "C15": "es la variante −1 playero por turno del eje C5",
    "C19": "los precios no entran al modelo: el margen es un valor por litro (eje ECO-01)",
    "C20": "datos de la sociedad propietaria: no afectan la operación",
}


def listado_registro() -> list[dict[str, str]]:
    """TODOS los datos supuesto/heredado/estimación con sus alternativas y su eje (o por qué no)."""
    cubiertos: dict[str, str] = {}
    for eje in EJES:
        for d in eje.datos:
            cubiertos.setdefault(d, eje.id)
    filas = []
    for d in REGISTRO:
        if d.tipo not in ("supuesto", "heredado", "estimacion"):
            continue
        tiene_rango = bool(d.alternativas) or d.bajo is not None or d.alto is not None
        if d.id in cubiertos:
            eje = f"sí · eje {cubiertos[d.id]}"
        elif d.id in NO_ES_EJE:
            eje = f"no · {NO_ES_EJE[d.id]}"
        elif tiene_rango:
            eje = "SIN CLASIFICAR"
        else:
            eje = "no · el Registro no trae rango ni alternativa para variarlo"
        alternativas = " · ".join(
            f"{n}" + (f" = {v}" if v is not None else "") for n, v, _ in d.alternativas
        )
        if d.bajo is not None or d.alto is not None:
            alternativas = (alternativas + " · " if alternativas else "") + f"rango {d.bajo}–{d.alto}"
        filas.append({
            "ID": d.id, "Dato": d.nombre, "Tipo": d.tipo, "Contradicción": d.conflicto,
            "Alternativas / rango": alternativas, "¿Eje del tornado?": eje,
        })
    return filas


def contradicciones_y_ejes() -> list[dict[str, str]]:
    """Cada contradicción C1–C20 con el eje que la cubre (o por qué no tiene)."""
    por_conflicto = {e.conflicto: e for e in EJES if e.conflicto}
    filas = []
    for c in CONTRADICCIONES:
        if c.id in por_conflicto:
            e = por_conflicto[c.id]
            estado = f"eje {e.id}: " + " · ".join(et for et, _ in e.variantes)
        else:
            estado = "sin eje: " + CONTRADICCION_SIN_EJE.get(c.id, "SIN CLASIFICAR")
        filas.append({"ID": c.id, "Tema": c.tema, "Impacto": c.impacto, "En el tornado": estado})
    return filas
