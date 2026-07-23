"""Clés logiques des logos officiels."""

from enum import Enum


class Logo(str, Enum):
    """Identifie un logo sans exposer son emplacement physique."""

    FRENCH_REPUBLIC = "french_republic"
    MUNICIPAL_POLICE = "municipal_police"
    MUNICIPALITY = "municipality"
    PMP = "pmp"
