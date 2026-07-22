"""Contrats de données transversaux du bilan quotidien."""

from dataclasses import dataclass
from datetime import date, datetime, time

from enum import Enum


class DailyReportImportance(str, Enum):
    """Niveau d'importance stable d'un élément du bilan."""

    NORMAL = "normal"
    IMPORTANT = "important"
    CRITICAL = "critical"


def _require_non_empty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} doit être une chaîne de caractères.")
    if not value.strip():
        raise ValueError(f"{field_name} ne peut pas être vide.")


def _validate_optional_string(value: object, field_name: str) -> None:
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{field_name} doit être une chaîne de caractères ou None.")


@dataclass(frozen=True)
class DailyReportItem:
    """Contribution immuable d'un module au bilan d'une journée."""

    source: str
    source_id: str
    report_date: date
    category: str
    title: str
    importance: DailyReportImportance
    sort_priority: int
    event_time: time | None = None
    summary: str | None = None
    location: str | None = None
    folder_reference: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("source", "source_id", "category", "title"):
            _require_non_empty_string(getattr(self, field_name), field_name)

        if isinstance(self.report_date, datetime) or not isinstance(self.report_date, date):
            raise TypeError("report_date doit être une date, sans composante horaire.")
        if self.event_time is not None and not isinstance(self.event_time, time):
            raise TypeError("event_time doit être une heure ou None.")
        if not isinstance(self.importance, DailyReportImportance):
            raise TypeError("importance doit être une valeur DailyReportImportance.")
        if isinstance(self.sort_priority, bool) or not isinstance(self.sort_priority, int):
            raise TypeError("sort_priority doit être un entier.")
        if self.sort_priority < 0:
            raise ValueError("sort_priority doit être positif ou nul.")

        for field_name in ("summary", "location", "folder_reference"):
            _validate_optional_string(getattr(self, field_name), field_name)


@dataclass(frozen=True)
class DailyReportWarning:
    """Incident non bloquant rencontré pendant une collecte."""

    provider_name: str
    report_date: date
    message: str
    warning_code: str | None = None
    details: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.provider_name, "provider_name")
        if isinstance(self.report_date, datetime) or not isinstance(self.report_date, date):
            raise TypeError("report_date doit être une date, sans composante horaire.")
        _require_non_empty_string(self.message, "message")
        _validate_optional_string(self.warning_code, "warning_code")
        _validate_optional_string(self.details, "details")


@dataclass(frozen=True)
class DailyReport:
    """Résultat immuable agrégé pour une journée."""

    report_date: date
    items: tuple[DailyReportItem, ...] = ()
    warnings: tuple[DailyReportWarning, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.report_date, datetime) or not isinstance(self.report_date, date):
            raise TypeError("report_date doit être une date, sans composante horaire.")

        try:
            items = tuple(self.items)
        except TypeError as exc:
            raise TypeError("items doit être une collection de DailyReportItem.") from exc
        try:
            warnings = tuple(self.warnings)
        except TypeError as exc:
            raise TypeError("warnings doit être une collection de DailyReportWarning.") from exc

        if not all(isinstance(item, DailyReportItem) for item in items):
            raise TypeError("items doit contenir uniquement des DailyReportItem.")
        if not all(isinstance(warning, DailyReportWarning) for warning in warnings):
            raise TypeError("warnings doit contenir uniquement des DailyReportWarning.")
        if any(item.report_date != self.report_date for item in items):
            raise ValueError("Tous les items doivent correspondre à la date du rapport.")

        object.__setattr__(self, "items", items)
        object.__setattr__(self, "warnings", warnings)

    @property
    def is_partial(self) -> bool:
        """Indique qu'au moins une collecte non essentielle a échoué."""

        return bool(self.warnings)

    @property
    def item_count(self) -> int:
        """Retourne le nombre d'éléments effectivement collectés."""

        return len(self.items)


def daily_report_sort_key(item: DailyReportItem) -> tuple[object, ...]:
    """Construit une clé stable fondée sur les seules données de l'item."""

    if not isinstance(item, DailyReportItem):
        raise TypeError("item doit être un DailyReportItem.")
    return (
        item.sort_priority,
        item.event_time is None,
        item.event_time or time.min,
        item.category,
        item.title,
        item.source,
        item.source_id,
    )
