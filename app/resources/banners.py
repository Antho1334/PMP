"""Clés logiques des bannières officielles."""

from enum import Enum


class Banner(str, Enum):
    """Identifie une bannière sans exposer son emplacement physique."""

    PMP = "pmp"
