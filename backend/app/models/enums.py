import enum


class RoleName(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    DESPACHADOR = "DESPACHADOR"
    VENDEDOR = "VENDEDOR"
    CHOFER = "CHOFER"
    CLIENTE = "CLIENTE"


class ShipmentStatus(str, enum.Enum):
    CREADO = "CREADO"
    PENDIENTE = "PENDIENTE"
    PREPARANDO = "PREPARANDO"
    LISTO = "LISTO"
    ASIGNADO = "ASIGNADO"
    SALIDA_BODEGA = "SALIDA_BODEGA"
    EN_RUTA = "EN_RUTA"
    LLEGADA_CLIENTE = "LLEGADA_CLIENTE"
    ENTREGA_EN_PROCESO = "ENTREGA_EN_PROCESO"
    ENTREGADO = "ENTREGADO"
    NO_ENTREGADO = "NO_ENTREGADO"
    INCIDENCIA = "INCIDENCIA"
    REGRESO_BODEGA = "REGRESO_BODEGA"
    LLEGADA_BODEGA = "LLEGADA_BODEGA"
    COMPLETADO = "COMPLETADO"
    CANCELADO = "CANCELADO"


# Fuente de verdad de transiciones válidas (ver docs/states.md).
# El backend NUNCA debe hacer un UPDATE directo de estado sin pasar por esta tabla.
VALID_TRANSITIONS: dict[ShipmentStatus, set[ShipmentStatus]] = {
    ShipmentStatus.CREADO: {ShipmentStatus.PENDIENTE},
    ShipmentStatus.PENDIENTE: {ShipmentStatus.PREPARANDO, ShipmentStatus.CANCELADO},
    ShipmentStatus.PREPARANDO: {ShipmentStatus.LISTO, ShipmentStatus.CANCELADO},
    ShipmentStatus.LISTO: {ShipmentStatus.ASIGNADO, ShipmentStatus.CANCELADO},
    ShipmentStatus.ASIGNADO: {ShipmentStatus.SALIDA_BODEGA, ShipmentStatus.CANCELADO},
    ShipmentStatus.SALIDA_BODEGA: {ShipmentStatus.EN_RUTA},
    ShipmentStatus.EN_RUTA: {ShipmentStatus.LLEGADA_CLIENTE},
    ShipmentStatus.LLEGADA_CLIENTE: {ShipmentStatus.ENTREGA_EN_PROCESO},
    ShipmentStatus.ENTREGA_EN_PROCESO: {
        ShipmentStatus.ENTREGADO,
        ShipmentStatus.NO_ENTREGADO,
        ShipmentStatus.INCIDENCIA,
    },
    ShipmentStatus.NO_ENTREGADO: {ShipmentStatus.INCIDENCIA, ShipmentStatus.REGRESO_BODEGA},
    ShipmentStatus.INCIDENCIA: {ShipmentStatus.EN_RUTA, ShipmentStatus.REGRESO_BODEGA},
    ShipmentStatus.ENTREGADO: {ShipmentStatus.EN_RUTA, ShipmentStatus.REGRESO_BODEGA},
    ShipmentStatus.REGRESO_BODEGA: {ShipmentStatus.LLEGADA_BODEGA},
    ShipmentStatus.LLEGADA_BODEGA: {ShipmentStatus.COMPLETADO},
    ShipmentStatus.COMPLETADO: set(),
    ShipmentStatus.CANCELADO: set(),
}

# Estados desde los cuales se puede cancelar (antes de salir de bodega)
CANCELABLE_STATES = {
    ShipmentStatus.CREADO,
    ShipmentStatus.PENDIENTE,
    ShipmentStatus.PREPARANDO,
    ShipmentStatus.LISTO,
    ShipmentStatus.ASIGNADO,
}


class DriverShiftStatus(str, enum.Enum):
    INICIADA = "INICIADA"
    EN_RUTA = "EN_RUTA"
    REGRESANDO = "REGRESANDO"
    FINALIZADA = "FINALIZADA"


class DeliveryResult(str, enum.Enum):
    ENTREGADO = "ENTREGADO"
    NO_ENTREGADO = "NO_ENTREGADO"


class EvidenceType(str, enum.Enum):
    FIRMA = "FIRMA"
    FOTO = "FOTO"
