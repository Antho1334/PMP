"""Moteur transverse d'agrégation du bilan quotidien."""

from collections.abc import Iterable
from datetime import date, datetime

from app.models.daily_report import (
    DailyReport,
    DailyReportItem,
    DailyReportWarning,
    daily_report_sort_key,
)
from app.providers.daily_report_provider import DailyReportProvider, ProviderMetadata
from app.services.daily_report_registry import DailyReportRegistry


INVALID_PROVIDER_NAME = "<invalid provider>"
PROVIDER_COLLECTION_FAILED = "provider_collection_failed"


class DailyReportGenerationError(RuntimeError):
    """Signale l'échec bloquant d'un provider pour une date donnée."""

    def __init__(self, provider_name: str, report_date: date, message: str) -> None:
        self.provider_name = provider_name
        self.report_date = report_date
        super().__init__(message)


class DailyReportService:
    """Collecte, valide et agrège les contributions des providers."""

    def __init__(self, registry: DailyReportRegistry) -> None:
        if not isinstance(registry, DailyReportRegistry):
            raise TypeError("registry doit être un DailyReportRegistry.")
        self._registry = registry

    @property
    def has_registered_providers(self) -> bool:
        """Indique si le moteur dispose d'au moins une source de rapport."""

        return self._registry.provider_count > 0

    def generate(self, report_date: date) -> DailyReport:
        """Construit le rapport agrégé correspondant à la date demandée."""

        if isinstance(report_date, datetime) or not isinstance(report_date, date):
            raise TypeError("report_date doit être une date, sans composante horaire.")

        items: list[DailyReportItem] = []
        warnings: list[DailyReportWarning] = []
        for provider in self._registry.providers:
            try:
                metadata = provider.metadata
            except Exception as exc:
                raise DailyReportGenerationError(
                    INVALID_PROVIDER_NAME,
                    report_date,
                    "Invalid provider metadata.",
                ) from exc
            if not isinstance(metadata, ProviderMetadata):
                error = TypeError("provider.metadata doit être un ProviderMetadata.")
                raise DailyReportGenerationError(
                    INVALID_PROVIDER_NAME,
                    report_date,
                    "Invalid provider metadata.",
                ) from error

            try:
                provider_items = self._collect_provider(provider, report_date)
            except Exception as exc:
                if metadata.is_essential:
                    raise DailyReportGenerationError(
                        metadata.name,
                        report_date,
                        "Provider collection failed.",
                    ) from exc
                warnings.append(
                    DailyReportWarning(
                        provider_name=metadata.name,
                        report_date=report_date,
                        warning_code=PROVIDER_COLLECTION_FAILED,
                        message="Provider collection failed.",
                        details=str(exc) or None,
                    )
                )
            else:
                items.extend(provider_items)

        items.sort(key=daily_report_sort_key)
        return DailyReport(report_date, items=items, warnings=warnings)

    @staticmethod
    def _collect_provider(
        provider: DailyReportProvider, report_date: date
    ) -> list[DailyReportItem]:
        result = provider.collect(report_date)
        if result is None:
            raise TypeError("collect() ne doit pas retourner None.")
        if isinstance(result, (str, bytes)):
            raise TypeError("collect() doit retourner un itérable de DailyReportItem.")
        if not isinstance(result, Iterable):
            raise TypeError("collect() doit retourner un itérable de DailyReportItem.")

        collected: list[DailyReportItem] = []
        for item in result:
            if not isinstance(item, DailyReportItem):
                raise TypeError("collect() doit produire uniquement des DailyReportItem.")
            if item.report_date != report_date:
                raise ValueError("Un item ne correspond pas à la date demandée.")
            collected.append(item)
        return collected
