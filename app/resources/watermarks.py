"""Clés logiques des filigranes officiels."""

from enum import Enum


class Watermark(str, Enum):
    """Identifie un filigrane sans exposer son emplacement physique."""

    PMP = "pmp"
