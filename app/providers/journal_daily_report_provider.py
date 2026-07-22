"""Contribution du Journal au bilan quotidien."""

from datetime import date

from app.models.activity import Activity
from app.models.daily_report import DailyReportImportance, DailyReportItem
from app.providers.daily_report_provider import DailyReportProvider, ProviderMetadata
from app.services.journal_service import JournalService


_SOURCE_NAME = "journal"
_JOURNAL_SORT_PRIORITY = 0


class JournalDailyReportProvider(DailyReportProvider):
    """Transforme les activites du Journal en elements de bilan."""

    def __init__(self, journal_service: JournalService) -> None:
        if not isinstance(journal_service, JournalService):
            raise TypeError("journal_service doit etre un JournalService.")
        self._journal_service = journal_service

    @property
    def metadata(self) -> ProviderMetadata:
        """Retourne les metadonnees stables du provider Journal."""

        return ProviderMetadata(name=_SOURCE_NAME, is_essential=False)

    def collect(self, report_date: date) -> tuple[DailyReportItem, ...]:
        """Collecte les activites de la date demandee sans les trier."""

        activities = self._journal_service.search_activities_by_date(report_date)
        return tuple(self._to_daily_report_item(activity) for activity in activities)

    @staticmethod
    def _to_daily_report_item(activity: Activity) -> DailyReportItem:
        if activity.id is None:
            raise RuntimeError("Une activite du Journal collectee doit posseder un identifiant.")

        importance = (
            DailyReportImportance.IMPORTANT
            if activity.important
            else DailyReportImportance.NORMAL
        )
        return DailyReportItem(
            source=_SOURCE_NAME,
            source_id=str(activity.id),
            report_date=activity.activity_date,
            category=activity.category,
            title=activity.title,
            importance=importance,
            sort_priority=_JOURNAL_SORT_PRIORITY,
            event_time=activity.activity_time,
            summary=activity.report,
            location=None,
            folder_reference=None,
        )
