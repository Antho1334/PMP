"""Clés logiques des polices officielles."""

from enum import Enum


class Font(str, Enum):
    """Identifie une police sans exposer son emplacement physique."""

    DEFAULT = "default"
