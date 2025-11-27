# Variables y Notación del MDRP

Este documento define la notación matemática y las variables utilizadas en el proyecto, basándose en la formulación de Reyes et al. (2018) y la adaptación para esta tesis.

## Conjuntos Principales

| Símbolo | Definición | Descripción |
| :---: | :--- | :--- |
| $R$ | Conjunto de Restaurantes | Puntos de recolección fijos en la red. |
| $O$ | Conjunto de Órdenes | Solicitudes de entrega realizadas por los clientes. |
| $C$ | Conjunto de Couriers | Flota de repartidores disponibles (motocicletas/bicicletas). |
| $O^t$ | Órdenes Pendientes | Subconjunto de órdenes conocidas pero aún no entregadas ni comprometidas en el tiempo $t$. |

## Atributos de las Órdenes ($o \in O$)

| Símbolo | Definición | Descripción |
| :---: | :--- | :--- |
| $a_o$ | Placement Time | Tiempo en el que el cliente realiza la orden (arribo de la solicitud). |
| $e_o$ | Ready Time | Tiempo en el que la comida está lista para ser recogida en el restaurante. $e_o \ge a_o$. |
| $r_o$ | Restaurante Origen | El restaurante específico $r \in R$ donde se debe recoger la orden $o$. |
| $\ell_o$ | Ubicación de Entrega | Coordenadas o nodo de la red donde se debe entregar la orden. |
| $s_o$ | Tiempo de Servicio (Entrega) | Tiempo requerido para entregar la orden al cliente (estacionarse, caminar, entregar). |

## Atributos de los Restaurantes ($r \in R$)

| Símbolo | Definición | Descripción |
| :---: | :--- | :--- |
| $\ell_r$ | Ubicación del Restaurante | Coordenadas o nodo de la red donde se ubica el restaurante. |
| $s_r$ | Tiempo de Servicio (Recogida) | Tiempo requerido para recoger una o más órdenes (estacionarse, entrar, recoger). |
| $p_r$ | Tiempo de Preparación | Tiempo variable que transcurre entre $a_o$ y $e_o$. $e_o = a_o + p_r$. |

## Atributos de los Couriers ($c \in C$)

| Símbolo | Definición | Descripción |
| :---: | :--- | :--- |
| $e_c$ | On-time (Inicio de Turno) | Tiempo en el que el courier $c$ inicia su turno y está disponible. |
| $l_c$ | Off-time (Fin de Turno) | Tiempo en el que el courier $c$ termina su turno. |
| $\ell_c$ | On-location | Ubicación inicial del courier al comenzar su turno. |
| $cap_c$ | Capacidad del Courier | Número máximo de órdenes que el courier puede transportar simultáneamente (Restricción operativa de la tesis). |

## Parámetros del Sistema y Políticas

| Símbolo | Definición | Descripción |
| :---: | :--- | :--- |
| $\Delta$ | Horizonte de Reoptimización | Intervalo de tiempo entre ejecuciones del algoritmo de asignación (Rolling Horizon). |
| $\tau$ | Target Click-to-Door | Tiempo objetivo de servicio (SLA) desde $a_o$ hasta la entrega. |
| $\tau_{max}$ | Max Click-to-Door | Tiempo máximo tolerable antes de considerar la orden como fallida o muy tardía. |
| $t$ | Tiempo de Simulación | Instante actual en la simulación de eventos discretos. |
