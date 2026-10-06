"""Generación de números aleatorios con semilla y streams separados.

Dos ideas importantes para que el TP sea defendible:

1. REPRODUCIBILIDAD: toda la aleatoriedad del modelo pasa por acá y depende de una
   semilla explícita. Misma semilla => exactamente el mismo resultado.

2. STREAMS SEPARADOS: cada fuente de azar usa su propio generador independiente. Esto
   permite NÚMEROS ALEATORIOS COMUNES: al comparar escenarios con la misma semilla, los
   autos llegan en los mismos instantes, cargan los mismos litros y el camión tarda lo
   mismo en llegar, en todos los escenarios. La diferencia observada queda explicada por
   la cantidad de surtidores y cajas, no por el azar.
"""

from __future__ import annotations

import random

from sim.config import DemandaDiaria, Triangular

#: Cada fuente de azar del modelo. Los streams NUEVOS se agregan SIEMPRE AL FINAL:
#: reordenar esta tupla cambia las semillas de los anteriores y rompe los números
#: aleatorios comunes y los dorados (trampa 6 del orquestador).
STREAMS = (
    "llegadas",   # instantes de llegada de los autos
    "carga",      # tiempo de carga de combustible
    "compra",     # tiempo de atención en la caja
    "decision",   # si el cliente entra o no al minimarket
    "litros",     # cuántos litros carga cada auto
    "demanda",    # cuántos autos trae cada día (Monte Carlo, tabla empírica)
    "entrega",    # plazo de entrega del camión cisterna
    "producto",   # qué producto carga cada cliente (Fase 2)
    "tipo_vehiculo",  # qué tipo de vehículo es cada cliente (Fase 2)
    # Fase 4: el plazo de cada camión sale de un stream PROPIO por producto. Así, cambiar
    # la política de un producto no corre los sorteos de plazo de los otros (números
    # aleatorios comunes por producto: permite barrer las 4 políticas a la vez).
    "entrega_super",
    "entrega_vpower",
    "entrega_diesel_g2",
    "entrega_diesel_g3",
    # Fase 5: los cortes de ruta, un stream por producto por la misma razón.
    "corte_ruta_super",
    "corte_ruta_vpower",
    "corte_ruta_diesel_g2",
    "corte_ruta_diesel_g3",
    # Fase 6: el calendario de episodios de corte de GNC y la migración a nafta.
    "corte_gnc",
    "migracion",
)

# Números primos grandes para separar las semillas de cada stream y que no queden
# correlacionadas entre sí.
_DESPLAZAMIENTO = 104_729
_MULTIPLICADOR = 7_919


class Aleatorio:
    """Fábrica de variables aleatorias del modelo, con un generador por stream."""

    def __init__(self, semilla: int) -> None:
        self.semilla = int(semilla)
        self._gen: dict[str, random.Random] = {
            nombre: random.Random(self.semilla * _MULTIPLICADOR + i * _DESPLAZAMIENTO)
            for i, nombre in enumerate(STREAMS)
        }

    def _g(self, stream: str) -> random.Random:
        try:
            return self._gen[stream]
        except KeyError:
            raise KeyError(f"Stream desconocido: {stream}. Validos: {STREAMS}") from None

    # --- Variables aleatorias -------------------------------------------------
    def uniforme(self, stream: str) -> float:
        """Número aleatorio uniforme en [0, 1). Es la base de todo lo demás."""
        return self._g(stream).random()

    def exponencial(self, media: float, stream: str) -> float:
        """Exponencial de media dada. Modela el interarribo de un proceso de Poisson."""
        return self._g(stream).expovariate(1.0 / media)

    def triangular(self, t: Triangular, stream: str) -> float:
        """Triangular(mínimo, moda, máximo). Modela tiempos y volúmenes estimados."""
        # Ojo: random.triangular recibe (low, high, mode), en ese orden.
        return self._g(stream).triangular(t.minimo, t.maximo, t.moda)

    def bernoulli(self, p: float, stream: str) -> bool:
        """True con probabilidad p. Modela la decisión de entrar al minimarket."""
        return self._g(stream).random() < p

    def discreta(self, pesos: tuple[float, ...], stream: str) -> int:
        """Índice sorteado por pesos (se normalizan solos). Monte Carlo de 5 pasos:
        frecuencia → probabilidad → acumulada → intervalo → sorteo."""
        u = self._g(stream).random()
        total = sum(pesos)
        acumulado = 0.0
        for i, peso in enumerate(pesos):
            acumulado += peso / total
            if u < acumulado:
                return i
        return len(pesos) - 1

    def discreta_con_numero(self, pesos: tuple[float, ...], stream: str) -> tuple[int, int]:
        """Como `discreta` pero devuelve además el número aleatorio de dos dígitos
        (01 a 100) para poder mostrar la tabla de simulación igual que en el apunte."""
        u = self._g(stream).random()
        numero = int(u * 100) + 1           # 01 a 100; el 100 se muestra como "00"
        total = sum(pesos)
        acumulado = 0.0
        for i, peso in enumerate(pesos):
            acumulado += peso / total
            if u < acumulado:
                return i, numero
        return len(pesos) - 1, numero

    def empirica(self, tabla: DemandaDiaria, stream: str) -> tuple[int, int]:
        """Sortea un valor de una tabla de frecuencias empírica (método Monte Carlo).

        Devuelve el valor sorteado y el número aleatorio de dos dígitos (01 a 100) con el
        que se sorteó, para poder mostrar la tabla de simulación igual que en el apunte.
        """
        u = self._g(stream).random()
        numero = int(u * 100) + 1           # 01 a 100; el 100 se muestra como "00"
        return tabla.sortear(u), numero

    def esperada(self, clientes_por_dia: float) -> tuple[int, int]:
        """Demanda esperada del día, derivada de los litros por mes (sin sorteo).

        El total diario es fijo pero las llegadas siguen siendo Poisson y los tiempos
        aleatorios: por eso se mantienen las réplicas y el calentamiento (B4).

        Args:
            clientes_por_dia: clientes esperados para el día (litros ÷ litros medios)

        Returns:
            Tupla (clientes_redondeados, numero_pseudoaleatorio_50)
        """
        return int(round(clientes_por_dia)), 50
