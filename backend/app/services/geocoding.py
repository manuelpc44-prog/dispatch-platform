"""Capa de abstracción de geocodificación (ver docs/architecture.md sección 6:
mismo patrón Strategy usado para MapProvider/RouteProvider).

IMPORTANTE: este sandbox de desarrollo no tiene acceso de red a un proveedor real
(Nominatim/OpenStreetMap, Google Geocoding, etc. no están en la lista de dominios
permitidos). GeocodingProvider es la interfaz; DevGeocodingProvider es un stub
determinístico solo para desarrollo/tests. La integración real con Nominatim u otro
proveedor queda para cuando se conecte la capa de mapas (Fase 9) — se implementa la
interfaz sin tocar el código que la consume (Customer service, endpoints).
"""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GeocodeResult:
    latitude: float
    longitude: float
    matched_address: str


class GeocodingProvider(ABC):
    @abstractmethod
    def geocode(self, calle: str, numero: str | None, comuna: str, ciudad: str, region: str) -> GeocodeResult:
        raise NotImplementedError


class DevGeocodingProvider(GeocodingProvider):
    """Genera coordenadas determinísticas dentro de un radio de la Región Metropolitana
    a partir de un hash de la dirección, solo para que el flujo de desarrollo/tests
    tenga lat/lng sin depender de un proveedor externo. NO USAR EN PRODUCCIÓN."""

    BASE_LAT = -33.45
    BASE_LNG = -70.65

    def geocode(self, calle: str, numero: str | None, comuna: str, ciudad: str, region: str) -> GeocodeResult:
        address_str = f"{calle} {numero or ''}, {comuna}, {ciudad}, {region}"
        digest = hashlib.sha256(address_str.encode()).hexdigest()
        offset_lat = (int(digest[:8], 16) % 2000 - 1000) / 10000  # +/- 0.1 grados
        offset_lng = (int(digest[8:16], 16) % 2000 - 1000) / 10000
        return GeocodeResult(
            latitude=round(self.BASE_LAT + offset_lat, 6),
            longitude=round(self.BASE_LNG + offset_lng, 6),
            matched_address=address_str.strip(),
        )


def get_geocoding_provider() -> GeocodingProvider:
    # Punto único de cambio de proveedor (Strategy). En producción, condicionar por
    # settings.environment o una variable GEOCODING_PROVIDER.
    return DevGeocodingProvider()
