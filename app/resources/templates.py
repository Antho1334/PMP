"""Clés logiques des modèles documentaires officiels."""

from enum import Enum


class Template(str, Enum):
    """Identifie un modèle sans exposer son emplacement physique."""

    DAILY_REPORT_WORD = "daily_report_word"
