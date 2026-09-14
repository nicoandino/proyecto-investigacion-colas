# Simulador de Estación de Servicio

Simulador de eventos discretos desarrollado para el trabajo práctico de **Investigación Operativa**.

El proyecto modela una estación de servicio completa con un motor propio en Python
basado en SimPy y una interfaz interactiva en Streamlit. Permite analizar, con datos
simulados, decisiones de capacidad e inventario.

## Contenido

- [Qué resuelve](#qué-resuelve)
- [Vistas de la aplicación](#vistas-de-la-aplicación)
- [Iniciar el proyecto desde cero](#iniciar-el-proyecto-desde-cero)
- [Ejecutar y verificar](#ejecutar-y-verificar)
- [Modelo de simulación](#modelo-de-simulación)
- [Escenarios y política de inventario](#escenarios-y-política-de-inventario)
- [Criterio estadístico](#criterio-estadístico)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Tecnologías](#tecnologías)

## Qué resuelve

El modelo integra las tres unidades de la materia en un mismo sistema:

- **Modelos de colas:** red de surtidores y caja del minimarket, con abandono de clientes.
- **Simulación Monte Carlo:** la demanda diaria se genera desde una tabla de frecuencias empírica.
- **Transporte e inventario:** tanque de combustible con política de reposición y entregas aleatorias de un camión cisterna.

Con esto responde dos preguntas de decisión:

1. ¿Conviene incorporar un surtidor y/o un cajero?
2. ¿Qué política de reposición de combustible minimiza el costo mensual?

## Vistas de la aplicación

| Pestaña | Contenido |
| --- | --- |
| 🎬 **Animación** | Operación de un día: llegadas, colas, surtidores, caja y nivel de tanque. |
| 📊 **Indicadores** | Métricas de colas, clientes e inventario, con intervalos de confianza del 95 % y diagnóstico de cuello de botella. |
| 🎲 **Demanda** | Desarrollo paso a paso del método Monte Carlo y registro diario de la demanda simulada. |
| 🛢️ **Inventario** | Evolución del tanque y comparación de políticas de reposición. |
| ⚖️ **Escenarios** | Comparación entre capacidades, con tablas, barras con IC y dispersión por réplica. |
| 💰 **Economía** | Ingresos, costos, beneficio neto y período de repago de cada escenario. |
| 📝 **Conclusión** | Recomendación construida a partir de los resultados simulados. |
| 📖 **Modelo y método** | Supuestos, formulación del modelo y fundamento estadístico. |

Los parámetros —incluida la tabla de frecuencias de demanda— se modifican desde la barra lateral.

## Iniciar el proyecto desde cero

### Requisitos previos

- [Python](https://www.python.org/downloads/) 3.10 o superior.
- `pip`, incluido con las instalaciones actuales de Python.
- Git, solo si todavía hay que clonar el repositorio.

### 1. Obtener el código

Si todavía no tenés el proyecto en tu equipo:

```bash
git clone <URL_DEL_REPOSITORIO>
cd proyecto-investigacion-colas
```

Si ya lo descargaste, abrí una terminal en la carpeta raíz del proyecto.

### 2. Crear y activar el entorno virtual

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Símbolo del sistema)**

```bat
py -m venv .venv
.venv\Scripts\activate.bat
```

**macOS o Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Si PowerShell impide ejecutar el script de activación, usá el Símbolo del sistema o ejecutá:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

### 3. Instalar las dependencias

Con el entorno virtual activado:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Iniciar la aplicación

```bash
streamlit run app.py
```

Abrí la dirección que muestre la terminal, normalmente [http://localhost:8501](http://localhost:8501).

## Ejecutar y verificar

Con el entorno virtual ya creado, alcanza con activar el entorno y ejecutar Streamlit:

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

También se puede ejecutar sin activarlo:

```powershell
.\.venv\Scripts\streamlit run app.py
```

Para comprobar la consistencia del motor de simulación:

```powershell
.\.venv\Scripts\python verificar.py
```

La verificación ejecuta 22 controles: reproducibilidad, conservación de clientes,
ley de Little, utilización, monotonía, demanda empírica, perfil horario, conservación
de litros y comportamiento de la política de reposición. Todos deben finalizar en `OK`.

## Modelo de simulación

```text
Monte Carlo: se sortea la demanda del día desde una tabla empírica
      ↓
Perfil horario: los autos se distribuyen en 24 h
      ↓
[cola] → N surtidores → 30 % → [cola] → M cajas → salida
   ↓        (Triangular)            (Triangular)   ↓
abandono                                       abandono
   ↑
   └── si el tanque está vacío, el auto no ingresa a la cola
              ↑
   TANQUE: política (s, Q) + camión cisterna con plazo de entrega aleatorio
```

- **Entidad:** auto o cliente; atributos: litros a cargar y compra en minimarket.
- **Recursos:** surtidores, cajas y tanque de combustible.
- **Réplica:** un mes completo de operación, equivalente a 30 días.

## Escenarios y política de inventario

### Capacidad

| Escenario | Configuración |
| --- | --- |
| Base | Situación actual: 3 surtidores y 1 caja. |
| A | Base + 1 surtidor. |
| B | Base + 1 cajero. |
| C | Base + 1 surtidor y 1 cajero. |

### Inventario

Se evalúan combinaciones de punto de pedido **(s)** y cantidad a pedir **(Q)**. La
política elegida es la que minimiza el costo total mensual:

> **Costo total = flete de pedidos + almacenamiento + ventas perdidas por faltantes**

## Criterio estadístico

- **Calentamiento:** el transitorio inicial se simula, pero no se incorpora a las métricas.
- **Réplicas independientes:** cada escenario se ejecuta con semillas distintas e informa promedio e intervalo de confianza del 95 % con t de Student.
- **Números aleatorios comunes:** los escenarios usan las mismas semillas para aislar el efecto de la capacidad.
- **Promedios temporales:** cola, utilización y nivel del tanque se calculan como área bajo la curva sobre el tiempo.

## Estructura del proyecto

```text
app.py                 interfaz Streamlit y punto de entrada
verificar.py           controles de correctitud del motor
requirements.txt       dependencias de Python
sim/                   motor de simulación
  config.py            parámetros, perfil horario, demanda, tanque y escenarios
  distribuciones.py    generación aleatoria con streams separados
  modelo.py            procesos SimPy: llegadas, colas, tanque y reposición
  estadisticas.py      colectores de indicadores
  traza.py             animación, serie de tanque y registro Monte Carlo
  runner.py            réplicas, IC, escenarios y barrido de políticas
  economia.py          análisis económico y recomendación
ui/                    componentes de presentación
docs/                  propuesta original del trabajo
```

## Tecnologías

Python · SimPy · Streamlit · Plotly · pandas · NumPy
