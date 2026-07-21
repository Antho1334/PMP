"""Contrat des sources participant au bilan quotidien."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from app.models.daily_report import DailyReportItem


@dataclass(frozen=True)
class ProviderMetadata:
    """Métadonnées stables nécessaires à la politique d'erreur."""

    name: str
    is_essential: bool

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name doit être une chaîne de caractères.")
        if not self.name.strip():
            raise ValueError("name ne peut pas être vide.")
        if not isinstance(self.is_essential, bool):
            raise TypeError("is_essential doit être un booléen.")


class DailyReportProvider(ABC):
    """Expose un module sous forme d'éléments de bilan quotidien."""

    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Retourne l'identité stable et la criticité du provider."""

    @abstractmethod
    def collect(self, report_date: date) -> Iterable[DailyReportItem]:
        """Transforme les données du module pour la journée demandée."""
