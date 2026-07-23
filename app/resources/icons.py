"""Clés logiques des icônes officielles."""

from enum import Enum


class Icon(str, Enum):
    """Identifie une icône sans exposer son emplacement physique."""

    PATROL = "patrol"
    PARKING = "parking"
    TRAFFIC = "traffic"
    URBAN_PLANNING = "urban_planning"
    INTERVENTION = "intervention"
    IMPOUND = "impound"
    ADMINISTRATIVE_POLICE = "administrative_police"
    JUDICIAL_POLICE = "judicial_police"
    WARNING = "warning"
    IMPORTANT = "important"
    INFORMATION = "information"
