"""Eventos aleatorios que alteran la estación (parte 4 del orquestador, §20–23).

Cómo funciona:

1. **Antes de correr** se arma el CALENDARIO de eventos de la corrida: para cada día y cada evento se sortea si
   ocurre (una probabilidad por día, EVT-01…14), y si ocurre, a qué hora, cuánto dura y a quién afecta. Se usa una
   semilla propia (`ParametrosEventos.semilla`) y un stream por evento al final de `STREAMS`, así que:
     · con la misma semilla salen siempre los mismos eventos (se pueden comprobar);
     · prender o apagar un evento no cambia las fechas de los otros (cada uno tiene su stream y se sortean todos
       siempre; después se filtran los prendidos);
     · el resto de la simulación no se toca: con datos reales sigue sin azar.
2. El motor (`sim/modelo.py`) **aplica** el calendario con mecanismos simples: un playero de menos (una reserva en
   el recurso de playeros, como los turnos), una cara o un compresor fuera de servicio, la estación parada (todos
   los playeros reservados), el cobro más lento, etc.
3. Cada evento ocurrido se informa con lo que le hizo a la estación (clientes que se fueron mientras duraba).

Este módulo no importa Streamlit ni `ui/` y no imprime nada.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import NamedTuple

from sim.config import ANO_REFERENCIA, MINUTOS_POR_DIA, ParametrosSimulacion
from sim.datos import valor
from sim.distribuciones import Aleatorio


class TipoEvento(NamedTuple):
    """Un evento del catálogo (§21)."""

    id: str          # "EVT-01"
    nombre: str
    grupo: str       # Personal · Equipos · Precio y abastecimiento · Demanda y seguridad
    efecto: str      # qué le hace a la estación, en una frase


CATALOGO: tuple[TipoEvento, ...] = (
    TipoEvento("EVT-01", "Abandono repentino del turno", "Personal",
               "un playero se va y nadie lo reemplaza hasta el próximo cambio de turno"),
    TipoEvento("EVT-02", "Licencia por accidente (con horas extra)", "Personal",
               "otro playero cubre el turno con horas extra: el servicio no cambia, sube el costo"),
    TipoEvento("EVT-03", "Falta sin aviso", "Personal",
               "un turno entero con un playero menos"),
    TipoEvento("EVT-04", "Licencia sin reemplazo", "Personal",
               "ese turno queda con un playero menos todos los días de la licencia"),
    TipoEvento("EVT-05", "Falla de un surtidor", "Equipos",
               "un surtidor fuera de servicio (sus dos caras) hasta que llega el técnico"),
    TipoEvento("EVT-06", "Falla de un compresor de GNC", "Equipos",
               "un compresor menos"),
    TipoEvento("EVT-07", "Corte de luz", "Equipos",
               "sin surtidores ni compresores: la estación se para"),
    TipoEvento("EVT-08", "Se cae el sistema de cobro", "Equipos",
               "sólo efectivo: cada carga tarda más y la caja del minimarket también"),
    TipoEvento("EVT-09", "Aumento de precio", "Precio y abastecimiento",
               "precio +10 % con el mismo margen por litro; el día anterior la gente se adelanta a cargar"),
    TipoEvento("EVT-10", "Faltante con cupo", "Precio y abastecimiento",
               "cupo de 30 L por cliente; los camiones tardan más y traen la mitad"),
    TipoEvento("EVT-11", "Rotura del camión en la ruta", "Precio y abastecimiento",
               "el camión llega de 12 a 48 h tarde"),
    TipoEvento("EVT-12", "Corte de la avenida", "Demanda y seguridad",
               "llega la mitad de los clientes mientras dura"),
    TipoEvento("EVT-13", "Evento masivo en San Rafael", "Demanda y seguridad",
               "más clientes esos días"),
    TipoEvento("EVT-14", "Asalto", "Demanda y seguridad",
               "la estación se para mientras actúa la policía"),
)
POR_ID = {t.id: t for t in CATALOGO}

#: Mecanismo con el que el motor aplica cada evento (los que tienen calendario).
MECANISMO = {
    "EVT-01": "playero", "EVT-03": "playero", "EVT-04": "playero_diario",
    "EVT-05": "cara", "EVT-06": "compresor", "EVT-07": "parada", "EVT-14": "parada",
    "EVT-08": "cobro",
    "EVT-09": "precio", "EVT-10": "cupo", "EVT-12": "avenida", "EVT-13": "masivo",
}
#: La rotura del camión (EVT-11) no tiene calendario: se sortea en cada viaje, mientras corre la simulación.

#: Turnos de PER-01: (nombre, hora de inicio, hora de fin); la noche termina a las 06 del día siguiente.
TURNOS = (("noche", 22, 30), ("mañana", 6, 14), ("tarde", 14, 22))
#: Cambios de turno (h del día).
CAMBIOS_DE_TURNO = (6, 14, 22)


class Evento(NamedTuple):
    """Un evento del calendario de la corrida."""

    id: str            # "EVT-05"
    inicio: float      # minuto de la corrida
    fin: float         # minuto de la corrida (puede pasar el final)
    objetivo: str      # turno ("noche"), zona ("B"), "" si es toda la estación
    valor: float       # días de la licencia, etc. (según el evento)
    detalle: str       # texto corto para la tabla y el aviso


def probabilidad(id_: str, mes: int = 1) -> float:
    """Probabilidad por día del evento (del Registro); el corte de luz depende de la temporada."""
    if id_ == "EVT-07":
        verano, resto = valor("EVT-07")[:2]
        return verano if mes in (12, 1, 2) else resto
    if id_ in ("EVT-02", "EVT-04"):
        return valor("EVT-02")[0]
    return valor(id_)[0]


def texto_frecuencia(id_: str) -> str:
    """La frecuencia del Registro en palabras ("≈ 1 cada 2 meses")."""
    if id_ == "EVT-04":
        return f"{valor('EVT-04')[0]:.0%} de las licencias"
    if id_ == "EVT-11":
        return f"{valor('EVT-11')[0]:.0%} de los viajes"
    if id_ == "EVT-07":
        verano, resto = valor("EVT-07")[:2]
        return f"≈ {verano * 30:.0f} por mes en verano y ≈ 1 cada {1 / (resto * 30):.0f} meses el resto del año"
    por_mes = probabilidad(id_) * 30
    if por_mes >= 1:
        return f"≈ {por_mes:.0f} por mes"
    if por_mes * 12 < 1.5:
        return "≈ 1 por año"
    return f"≈ 1 cada {1 / por_mes:.0f} meses"


def _dec(x: float) -> str:
    """18,6 (un decimal con coma, como en el resto de la app)."""
    return f"{x:.1f}".replace(".", ",")


def _hora(minutos: float) -> str:
    m = int(round(minutos)) % MINUTOS_POR_DIA
    return f"{m // 60:02d}:{m % 60:02d}"


def _fin_de_turno(t: float) -> float:
    """El próximo cambio de turno después del minuto t."""
    dia = int(t // MINUTOS_POR_DIA)
    for h in (*CAMBIOS_DE_TURNO, 24 + CAMBIOS_DE_TURNO[0]):
        borde = dia * MINUTOS_POR_DIA + h * 60.0
        if borde > t:
            return borde
    return (dia + 1) * MINUTOS_POR_DIA + CAMBIOS_DE_TURNO[0] * 60.0


def _turno_de(t: float) -> str:
    h = (t % MINUTOS_POR_DIA) / 60.0
    if 6 <= h < 14:
        return "mañana"
    if 14 <= h < 22:
        return "tarde"
    return "noche"


def _entre(az: Aleatorio, stream: str, minimo: float, maximo: float) -> float:
    return minimo + az.uniforme(stream) * (maximo - minimo)


def _entero(az: Aleatorio, stream: str, minimo: int, maximo: int) -> int:
    return min(maximo, minimo + int(az.uniforme(stream) * (maximo - minimo + 1)))


def _turno_sorteado(az: Aleatorio, stream: str, p: ParametrosSimulacion) -> tuple[str, int, int]:
    """Un turno, con probabilidad proporcional a sus playeros (le pasa a una persona, no a un turno)."""
    i = az.discreta(tuple(float(n) for n in p.playeros_por_turno), stream)
    return TURNOS[i]


def calendario(p: ParametrosSimulacion) -> tuple[Evento, ...]:
    """Los eventos de la corrida, en orden de inicio (vacío si no hay ninguno prendido)."""
    ev = p.eventos
    if not ev.activos or not p.estacion_real:
        return ()
    az = Aleatorio(ev.semilla)
    inicio = date(ANO_REFERENCIA, *p.fecha_inicio)
    salida: list[Evento] = []
    caras = [(g.id, g.nombre) for g in p.grupos for _ in range(g.caras)]
    for d in range(p.dias):
        fecha = inicio + timedelta(days=d)
        t0 = d * MINUTOS_POR_DIA
        # Se sortean TODOS los eventos todos los días (cada uno con su stream) y después se filtran los
        # prendidos: así prender uno no corre las fechas de los demás.
        for tipo in CATALOGO:
            if tipo.id not in MECANISMO and tipo.id != "EVT-02":
                continue
            if tipo.id == "EVT-04":
                continue                      # sale de las licencias de EVT-02
            stream = f"evento_{tipo.id[-2:]}"
            if not az.bernoulli(min(1.0, probabilidad(tipo.id, fecha.month) * ev.frecuencia), stream):
                continue
            salida.extend(_eventos_del_dia(tipo.id, az, stream, p, t0, caras))
    elegidos = [e for e in salida if e.id in ev.activos]
    return tuple(sorted(elegidos, key=lambda e: (e.inicio, e.id)))


def _eventos_del_dia(id_: str, az: Aleatorio, stream: str, p: ParametrosSimulacion,
                     t0: float, caras: list[tuple[str, str]]) -> list[Evento]:
    """Los detalles de un evento que ocurre el día que arranca en t0."""
    if id_ == "EVT-01":
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        fin = _fin_de_turno(t)
        turno = _turno_de(t)
        return [Evento(id_, t, fin, turno, 0.0,
                       f"un playero del turno {turno} se va a las {_hora(t)}; vuelve a haber dotación completa "
                       f"a las {_hora(fin)}")]
    if id_ == "EVT-03":
        nombre, desde, hasta = _turno_sorteado(az, stream, p)
        return [Evento(id_, t0 + desde * 60.0, t0 + hasta * 60.0, nombre, 0.0,
                       f"el turno {nombre} arranca con un playero menos")]
    if id_ == "EVT-02":
        _, d_min, d_max, _, _ = valor("EVT-02")
        dias = _entero(az, stream, int(d_min), int(d_max))
        nombre, desde, hasta = _turno_sorteado(az, stream, p)
        sin_reemplazo = az.uniforme(stream) < valor("EVT-04")[0]
        id_real = "EVT-04" if sin_reemplazo else "EVT-02"
        texto = (f"un playero del turno {nombre} falta {dias} días: "
                 + ("nadie lo reemplaza, el turno queda corto" if sin_reemplazo
                    else "otro playero lo cubre con horas extra"))
        return [Evento(id_real, t0 + desde * 60.0, t0 + (dias - 1) * MINUTOS_POR_DIA + hasta * 60.0,
                       nombre, float(dias), texto)]
    if id_ == "EVT-05":
        zona, nombre = caras[min(len(caras) - 1, int(az.uniforme(stream) * len(caras)))]
        _, h_min, h_max, _ = valor("EVT-05")
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        horas = _entre(az, stream, h_min, h_max)
        return [Evento(id_, t, t + horas * 60.0, zona, horas,
                       f"se rompe un surtidor de la zona {zona} ({nombre}): sus dos caras quedan fuera de servicio "
                       f"a las {_hora(t)} "
                       f"durante {_dec(horas)} h")]
    if id_ == "EVT-06":
        _, h_min, h_max = valor("EVT-06")
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        horas = _entre(az, stream, h_min, h_max)
        return [Evento(id_, t, t + horas * 60.0, "C", horas,
                       f"un compresor de GNC se rompe a las {_hora(t)} durante {_dec(horas)} h")]
    if id_ in ("EVT-07", "EVT-14"):
        h_min, h_max = valor(id_)[-2:]
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        horas = _entre(az, stream, h_min, h_max)
        que = "corte de luz" if id_ == "EVT-07" else "asalto"
        return [Evento(id_, t, t + horas * 60.0, "", horas,
                       f"{que} a las {_hora(t)}: la estación se para {horas * 60:.0f} min")]
    if id_ == "EVT-08":
        _, h_min, h_max, extra, factor = valor("EVT-08")
        t = t0 + az.uniforme(stream) * MINUTOS_POR_DIA
        horas = _entre(az, stream, h_min, h_max)
        return [Evento(id_, t, t + horas * 60.0, "", horas,
                       f"se cae el cobro con tarjeta a las {_hora(t)} durante {_dec(horas)} h: cada carga tarda "
                       f"{extra:g} min más y la caja × {factor:g}")]
    if id_ == "EVT-09":
        _, aumento, adelanto = valor("EVT-09")
        antes = ("el día anterior llegaron " + f"{100 * adelanto:.0f} % más clientes (se adelantaron a cargar)"
                 if t0 > 0 else "no hay día anterior en el período")
        return [Evento(id_, t0, float(p.duracion), "", aumento,
                       f"nafta y diésel suben {100 * aumento:.0f} % desde hoy, con el mismo margen por litro; {antes}")]
    if id_ == "EVT-10":
        _, d_min, d_max, cupo, fraccion = valor("EVT-10")
        dias = _entero(az, stream, int(d_min), int(d_max))
        return [Evento(id_, t0, t0 + dias * MINUTOS_POR_DIA, "", cupo,
                       f"faltante de combustible durante {dias} días: cupo de {cupo:g} L por cliente; los camiones "
                       f"pedidos tardan el plazo de crisis (INV-09) y traen {100 * fraccion:.0f} %")]
    if id_ == "EVT-12":
        _, h_min, h_max, fraccion, desde, hasta = valor("EVT-12")
        t = t0 + _entre(az, stream, desde, hasta) * 60.0
        horas = _entre(az, stream, h_min, h_max)
        return [Evento(id_, t, t + horas * 60.0, "", fraccion,
                       f"corte de la avenida a las {_hora(t)} durante {_dec(horas)} h: llega el "
                       f"{100 * fraccion:.0f} % de los clientes")]
    if id_ == "EVT-13":
        _, d_min, d_max, aumento = valor("EVT-13")
        dias = _entero(az, stream, int(d_min), int(d_max))
        return [Evento(id_, t0, t0 + dias * MINUTOS_POR_DIA, "", aumento,
                       f"evento masivo en San Rafael durante {dias} día{'s' if dias > 1 else ''}: "
                       f"{100 * aumento:.0f} % más clientes")]
    return []


def aumento_de_llegadas(ev: Evento, d: int) -> float:
    """Cuánto sube (fracción) la cantidad de clientes del día d (0 = el primero) por este evento."""
    dia_inicio = int(ev.inicio // MINUTOS_POR_DIA)
    if ev.id == "EVT-13" and dia_inicio <= d < int(round(ev.fin / MINUTOS_POR_DIA)):
        return ev.valor
    if ev.id == "EVT-09" and dia_inicio == d + 1:
        return valor("EVT-09")[2]                  # el día anterior al aumento la gente se adelanta
    return 0.0


def horas_extra(ev, inicio: date, dias: int) -> tuple[float, float]:
    """(horas al 50 %, horas al 100 %) de una licencia cubierta (EVT-02), dentro del período.

    Un turno de 8 h por cada día de licencia; el domingo va al 100 % y los demás días al 50 % (LCT art. 201;
    el sábado después de las 13 y los feriados se simplifican).
    """
    al_50 = al_100 = 0.0
    primero = int(ev.inicio // MINUTOS_POR_DIA)
    for k in range(int(ev.valor)):
        d = primero + k
        if d >= dias:
            break
        if (inicio + timedelta(days=d)).weekday() == 6:
            al_100 += 8.0
        else:
            al_50 += 8.0
    return al_50, al_100


def costo_de_eventos(eventos, p: ParametrosSimulacion, sueldo_playero_mensual: float) -> float:
    """Pesos que cuestan los eventos en el período: horas extra de las licencias cubiertas y visitas del técnico.

    La venta perdida NO entra acá (es costo de oportunidad y ya está en la venta perdida por motivo).
    """
    valor_hora = sueldo_playero_mensual / valor("EVT-15")
    recargo_50, recargo_100 = valor("EVT-02")[3:5]
    inicio = date(ANO_REFERENCIA, *p.fecha_inicio)
    total = 0.0
    for ev in eventos:
        if ev.id == "EVT-02":
            al_50, al_100 = horas_extra(ev, inicio, p.dias)
            total += valor_hora * (al_50 * (1 + recargo_50) + al_100 * (1 + recargo_100))
        elif ev.id == "EVT-05":
            total += valor("EVT-05")[3]
    return total


class EventoOcurrido(NamedTuple):
    """Un evento con lo que le hizo a la estación (para la tabla "Eventos del período")."""

    id: str
    inicio: float
    fin: float
    objetivo: str
    valor: float
    detalle: str
    perdidos: int      # clientes que se fueron sin cargar mientras duraba
    extra: float = 0.0  # según el evento: clientes de más (9, 13), que no llegaron (12), litros recortados por
                        # el cupo (10), horas de demora del camión (11)
