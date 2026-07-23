"""Clés logiques des images institutionnelles."""

from enum import Enum


class Image(str, Enum):
    """Identifie une image institutionnelle sans exposer son emplacement."""

    MUNICIPAL_POLICE_PATCH = "municipal_police_patch"
