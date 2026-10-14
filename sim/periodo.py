"""El período a simular y las ediciones del usuario (rediseño v3, etapa 2).

El menú inicial de la app pide **qué período** se simula —por días, por meses, por estación o el
año completo— y la simulación con datos reales corre todo ese período de punta a punta. Este
módulo es la lógica pura de esa elección (sin Streamlit): arma el `Periodo`, dice si incluye el
invierno (y por lo tanto los cortes de GNC) y aplica las **ediciones** opcionales a los parámetros.

Las ediciones son pocas a propósito: playeros, nivel de demanda, el doble de demanda en la hora
pico, el porcentaje de clientes GNC y el precio del litro. Una simulación editada ya no es la de
datos reales: usa azar (Monte Carlo) y la app explica qué se sorteó.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta

from sim.config import (
    ANO_REFERENCIA,
    Escenario,
    ParametrosEconomicos,
    ParametrosGNC,
    ParametrosSimulacion,
    PerfilHorario,
    dias_del_mes,
    turnos_con_refuerzo,
    turnos_de,
)
from sim.datos import valor
from sim.distribuciones import AleatorioDeterminista
from sim.escenarios import PICOS
from sim.gnc import MESES_INVIERNO, calendario_de_episodios, episodios_con_fechas

MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

#: Temporadas del menú (CAL-08): estaciones meteorológicas del hemisferio sur, de mes entero.
#: nombre → (mes en que empieza, cantidad de meses).
TEMPORADAS: dict[str, tuple[int, int]] = {
    nombre: (inicio, meses) for nombre, (inicio, meses) in valor("CAL-08")
}

#: Tope de un período: un año de 365 días.
MAXIMO_DIAS = 365

#: Horas pico de la edición "el doble en la hora pico" (07–10 y 16–18 h, perfil DEM-02).
HORAS_PICO = (7, 8, 9, 16, 17)


# =============================================================================
# El período
# =============================================================================
@dataclass(frozen=True)
class Periodo:
    """Qué se simula: desde qué fecha y cuántos días."""

    tipo: str                       # "dias" · "meses" · "estacion" · "anio"
    titulo: str                     # "Verano", "Enero a marzo", "180 días desde el 1 de enero"…
    fecha_inicio: tuple[int, int]   # (mes, día)
    dias: int

    @property
    def inicio(self) -> date:
        return date(ANO_REFERENCIA, *self.fecha_inicio)

    @property
    def fin(self) -> date:
        return self.inicio + timedelta(days=self.dias - 1)

    @property
    def incluye_invierno(self) -> bool:
        """True si algún día del período cae en jun–ago (entran los cortes de GNC)."""
        return any(
            (self.inicio + timedelta(days=d)).month in MESES_INVIERNO for d in range(self.dias)
        )

    @property
    def texto(self) -> str:
        """'Del 1 de enero al 30 de junio · 181 días'."""
        return (
            f"Del {texto_fecha(self.inicio)} al {texto_fecha(self.fin)} · "
            f"{self.dias} día{'s' if self.dias != 1 else ''}"
        )


def texto_fecha(f: date) -> str:
    """'1 de enero' (con el año sólo si cruza al año siguiente)."""
    extra = f" de {f.year}" if f.year != ANO_REFERENCIA else ""
    return f"{f.day} de {MESES[f.month - 1]}{extra}"


def por_dias(dias: int, mes: int, dia: int) -> Periodo:
    """`dias` días a partir del `dia` de `mes`."""
    dias = max(1, min(int(dias), MAXIMO_DIAS))
    dia = max(1, min(int(dia), dias_del_mes(mes)))
    return Periodo("dias", f"{dias} días desde el {dia} de {MESES[mes - 1]}", (mes, dia), dias)


def por_meses(desde: int, hasta: int) -> Periodo:
    """De enero a marzo, etc.: desde el día 1 de `desde` hasta el último día de `hasta`."""
    if hasta < desde:
        raise ValueError("El mes final tiene que ser igual o posterior al inicial.")
    dias = sum(dias_del_mes(m) for m in range(desde, hasta + 1))
    titulo = MESES[desde - 1].capitalize() if desde == hasta else (
        f"{MESES[desde - 1].capitalize()} a {MESES[hasta - 1]}"
    )
    return Periodo("meses", titulo, (desde, 1), dias)


def por_temporada(nombre: str) -> Periodo:
    """Una estación entera: Verano (dic–feb), Otoño (mar–may), Invierno (jun–ago), Primavera (sep–nov)."""
    inicio, meses = TEMPORADAS[nombre]
    dias = sum(dias_del_mes(((inicio - 1 + k) % 12) + 1) for k in range(meses))
    return Periodo("estacion", nombre, (inicio, 1), dias)


def anio_completo() -> Periodo:
    return Periodo("anio", "Año completo", (1, 1), 365)


def cortes_gnc_previstos(periodo: Periodo, g: ParametrosGNC) -> list[tuple[date, date]]:
    """Fechas de los episodios de corte de GNC que caen en el período (sin azar: fijas)."""
    episodios = calendario_de_episodios(g, AleatorioDeterminista(0), periodo.inicio, periodo.dias)
    return episodios_con_fechas(episodios, periodo.inicio, periodo.dias)


def con_periodo(p: ParametrosSimulacion, periodo: Periodo) -> ParametrosSimulacion:
    """Los mismos parámetros pero simulando `periodo`."""
    return replace(
        p, fecha_inicio=periodo.fecha_inicio, dias=periodo.dias,
        horizonte="anio" if periodo.tipo == "anio" else "mes", dia_animado=1,
    )


# =============================================================================
# Las ediciones
# =============================================================================
#: Los tres niveles de demanda salen del rango del Registro (DEM-01: bajo, adoptado, alto).
NIVELES_DEMANDA = ("poca", "media", "alta")


def litros_de_nivel(nivel: str) -> float:
    """Litros por mes de cada nivel de demanda: poca = DEM-01 bajo, media = adoptado, alta = DEM-01 alto."""
    from sim.datos import por_id

    d = por_id("DEM-01")
    return {"poca": float(d.bajo), "media": float(d.valor), "alta": float(d.alto)}[nivel]


@dataclass(frozen=True)
class Edicion:
    """Lo que el usuario cambió en *Editar simulación*. Los valores en None no se tocan."""

    playeros: tuple[int, int, int] | None = None      # noche · mañana · tarde
    nivel_demanda: str = "media"                      # poca · media · alta
    doble_pico: bool = False                          # el doble de clientes en la hora pico
    pct_gnc: float | None = None                      # 0 a 1
    precios: tuple[tuple[str, float], ...] | None = None
    semilla: int = 1                                  # la edición usa azar: la semilla la repite

    def hay_cambios(self, base: ParametrosSimulacion) -> bool:
        return (
            (self.playeros is not None and self.playeros != base.playeros_por_turno)
            or self.nivel_demanda != "media"
            or self.doble_pico
            or (self.pct_gnc is not None and abs(self.pct_gnc - base.pct_gnc) > 1e-9)
            or (self.precios is not None and self.precios != tuple(valor("ECO-08")))
        )


def aplicar_edicion(
    p: ParametrosSimulacion, eco: ParametrosEconomicos, ed: Edicion
) -> tuple[ParametrosSimulacion, ParametrosEconomicos]:
    """Parámetros y economía de una simulación editada: **con azar** (sin `determinista`)."""
    p = replace(p, determinista=False)
    if ed.playeros is not None:
        p = replace(p, playeros_por_turno=ed.playeros, turnos=turnos_de(ed.playeros))
    litros = litros_de_nivel(ed.nivel_demanda)
    if ed.pct_gnc is not None:
        p = replace(p, pct_gnc=ed.pct_gnc)
    if ed.doble_pico:
        factores = p.perfil.factores
        nuevos = tuple(
            f * valor("DEM-13") if h in HORAS_PICO else f for h, f in enumerate(factores)
        )
        # El perfil se reparte entre las 24 h: para que las horas que no son pico conserven su
        # tasa de llegadas, los litros del mes crecen en proporción al peso que suma el pico.
        litros *= sum(nuevos) / sum(factores)
        p = replace(p, perfil=PerfilHorario(nuevos))
    p = replace(p, litros_mes=litros)
    if ed.precios is not None:
        eco = replace(eco, precios=ed.precios)
    return p, eco


# =============================================================================
# Los ajustes del menú inicial (parte 2, tanda 4)
# =============================================================================
#: Margen de cada producto según el Registro: los líquidos ECO-01 ($/L), el GNC ECO-03 ($/m³). Heredados sin fuente.
MARGENES_REGISTRO: tuple[tuple[str, float], ...] = tuple(
    (pr, float(valor("ECO-03") if pr == "gnc" else valor("ECO-01")))
    for pr in ("super", "vpower", "diesel_g2", "diesel_g3", "gnc")
)

#: Modos de corte de GNC del menú.
CORTES_GNC = ("habituales", "todo_invierno")


@dataclass(frozen=True)
class Ajustes:
    """Lo que se elige en el menú antes de simular. Por defecto, los valores del Registro (y el calendario de
    temporadas prendido, que es la opción por defecto de la app; `calendario=False` deja la demanda del Registro pura).

    La economía (márgenes, flete, almacenamiento, sueldo) no cambia la simulación, sólo la plata. Los cortes de
    GNC y el % de clientes GNC sí cambian la simulación, pero sin azar: sigue siendo determinista.
    """

    margenes: tuple[tuple[str, float], ...] = MARGENES_REGISTRO
    flete_fijo: float = float(valor("ECO-06")[0])
    flete_km: float = float(valor("ECO-06")[1])
    almacenamiento: float = float(valor("ECO-07"))
    sueldo_playero: float = float(valor("ECO-04")[0])
    cortes_gnc: str = "habituales"                    # "habituales" | "todo_invierno"
    pct_gnc: float = float(valor("DEM-05"))
    calendario: bool = True                           # calendario de temporadas (DEM-14): activo en la app
    factores: tuple[tuple[str, float], ...] = tuple(valor("DEM-14"))

    def cambios(self) -> list[str]:
        """Lo que difiere del Registro, en palabras (para el encabezado de los resultados)."""
        base = Ajustes()
        salida = []
        if self.margenes != base.margenes:
            salida.append("márgenes por litro")
        if (self.flete_fijo, self.flete_km) != (base.flete_fijo, base.flete_km):
            salida.append("flete")
        if self.almacenamiento != base.almacenamiento:
            salida.append("costo de almacenamiento")
        if self.sueldo_playero != base.sueldo_playero:
            salida.append("sueldo de los playeros")
        if self.cortes_gnc != base.cortes_gnc:
            salida.append("más cortes de GNC en todo el invierno")
        if abs(self.pct_gnc - base.pct_gnc) > 1e-9:
            salida.append(f"{self.pct_gnc:.0%} de clientes GNC")
        if not self.calendario:
            salida.append("sin calendario de temporadas")
        elif self.factores != base.factores:
            salida.append("factores del calendario de temporadas")
        return salida


def gnc_con_ajustes(g: ParametrosGNC | None, a: Ajustes) -> ParametrosGNC | None:
    """El GNC con el modo de cortes elegido: 'todo el invierno' prende GNC-08/09/10."""
    if g is None or a.cortes_gnc != "todo_invierno":
        return g
    return replace(
        g, cortes_extra=int(valor("GNC-08")), prob_invierno_frio=float(valor("GNC-09")),
        dias_extra_frio=int(valor("GNC-10")),
    )


def aplicar_ajustes(
    p: ParametrosSimulacion, eco: ParametrosEconomicos, a: Ajustes
) -> tuple[ParametrosSimulacion, ParametrosEconomicos]:
    """Parámetros y economía con los ajustes del menú (con los defaults, idénticos a los del Registro)."""
    eco = replace(
        eco, margenes_producto=a.margenes, costo_pedido=a.flete_fijo, flete_por_km=a.flete_km,
        costo_almacenamiento_litro_mes=a.almacenamiento, sueldo_playero_mensual=a.sueldo_playero,
    )
    p = replace(p, gnc=gnc_con_ajustes(p.gnc, a), calendario_demanda=a.factores if a.calendario else ())
    if abs(a.pct_gnc - p.pct_gnc) > 1e-12:
        p = replace(p, pct_gnc=a.pct_gnc)
    return p, eco


# =============================================================================
# El escenario único (parte 2, tanda 6): una micro simulación de una semana
# =============================================================================
#: Franjas horarias que se pueden elegir: los picos son los de S2 (sim/escenarios.py) y el día entero.
FRANJAS: dict[str, tuple[float, float]] = {
    "Pico de la mañana (07–10 h)": PICOS[0],
    "Pico de la tarde (16–18 h)": PICOS[1],
    "Todo el día": (0.0, 24.0),
}
#: Nivel de clientela: poca, media y alta son DEM-01 (bajo, adoptado, alto); máxima = alta y el doble en el pico (DEM-13).
CLIENTELAS = ("poca", "media", "alta", "máxima")
#: Semana representativa de cada temporada (CAL-09): nombre → (mes, día) del lunes en que empieza.
SEMANAS: dict[str, tuple[int, int]] = dict(valor("CAL-09")[0])
DIAS_ESCENARIO: int = int(valor("CAL-09")[1])


@dataclass(frozen=True)
class EscenarioUnico:
    """Lo que se elige para el escenario único: cuántos playeros, en qué franja, temporada y clientela."""

    playeros: int = 2
    franja: str = "Pico de la mañana (07–10 h)"
    temporada: str = "Verano"
    clientela: str = "media"

    @property
    def titulo(self) -> str:
        return (
            f"{self.playeros} playero{'s' if self.playeros != 1 else ''} · {self.franja.lower()} · "
            f"{self.temporada.lower()} · clientela {self.clientela}"
        )

    def horas(self) -> tuple[int, ...]:
        """Las horas enteras del día que caen en la franja."""
        desde, hasta = FRANJAS[self.franja]
        return tuple(range(int(desde), int(hasta)))

    def periodo(self) -> Periodo:
        mes, dia = SEMANAS[self.temporada]
        return Periodo("escenario", f"Semana de {self.temporada.lower()}", (mes, dia), DIAS_ESCENARIO)

    def escenario(self, p: ParametrosSimulacion) -> Escenario:
        """Los cambios sobre `p`, como un `Escenario` declarativo (el mismo objeto que usa el catálogo S0–S12)."""
        cambios: dict[str, object] = {}
        desde, hasta = FRANJAS[self.franja]
        n = max(1, int(self.playeros))
        if (desde, hasta) == (0.0, 24.0):
            cambios["playeros_por_turno"] = (n, n, n)
            cambios["turnos"] = turnos_de((n, n, n))
        else:
            # Los playeros que hay en esa franja según los turnos (PER-01), y el refuerzo (±) que falta hasta n.
            vigente = [m for h, m in turnos_de(p.playeros_por_turno) if h <= desde][-1]
            cambios["turnos"] = turnos_con_refuerzo(p.playeros_por_turno, ((desde, hasta, n - vigente),))
        nivel = "alta" if self.clientela == "máxima" else self.clientela
        litros = litros_de_nivel(nivel)
        if self.clientela == "máxima":
            factores = p.perfil.factores
            nuevos = tuple(f * valor("DEM-13") if h in HORAS_PICO else f for h, f in enumerate(factores))
            litros *= sum(nuevos) / sum(factores)
            cambios["perfil"] = PerfilHorario(nuevos)
        cambios["litros_mes"] = litros
        return Escenario(
            nombre="Escenario único", descripcion=self.titulo, surtidores=p.surtidores, cajas=p.cajas,
            id="EU", pregunta="¿cómo anda la estación en esta situación?", cambios=tuple(cambios.items()),
        )

