"""Résultat transverse d'une recherche de géocodage."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GeocodingResult:
    """Adresse géocodée, indépendante de la carte et des modules métier."""

    label: str
    latitude: float
    longitude: float
    score: Optional[float] = None
    postcode: str = ""
    city: str = ""
    result_type: str = ""
    provider_id: str = ""
    context: str = ""
