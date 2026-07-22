from datetime import date, time

import pytest

from app.models.activity import Activity
from app.models.daily_report import DailyReportImportance
from app.providers.journal_daily_report_provider import JournalDailyReportProvider
from app.services.daily_report_registry import DailyReportRegistry
from app.services.daily_report_service import (
    PROVIDER_COLLECTION_FAILED,
    DailyReportService,
)
from app.services.journal_service import JournalService


REPORT_DATE = date(2026, 7, 22)


def _activity(activity_id=1, **overrides):
    values = {
        "activity_date": REPORT_DATE,
        "activity_time": time(8, 30),
        "category": "  Patrouille de nuit  ",
        "title": "  Controle  place centrale  ",
        "report": "  Compte rendu integral.  ",
        "important": False,
        "folder_id": 42,
        "outlook_id": "outlook-1",
        "id": activity_id,
    }
    values.update(overrides)
    return Activity(**values)


class StubJournalService(JournalService):
    def __init__(self, activities=(), error=None):
        self.activities = activities
        self.error = error
        self.calls = []

    def search_activities_by_date(self, activity_date):
        self.calls.append(activity_date)
        if self.error is not None:
            raise self.error
        return self.activities


def _integrated_service(journal_service):
    provider = JournalDailyReportProvider(journal_service)
    registry = DailyReportRegistry()
    registry.register(provider)
    return DailyReportService(registry)


def test_metadata_identifies_an_optional_journal_provider():
    provider = JournalDailyReportProvider(StubJournalService())

    assert provider.metadata.name == "journal"
    assert provider.metadata.is_essential is False


def test_constructor_accepts_a_journal_service():
    service = StubJournalService()

    provider = JournalDailyReportProvider(service)

    assert provider._journal_service is service


@pytest.mark.parametrize("invalid_service", [None, object(), "journal"])
def test_constructor_rejects_an_invalid_service(invalid_service):
    with pytest.raises(TypeError, match="journal_service"):
        JournalDailyReportProvider(invalid_service)


def test_empty_day_returns_an_empty_tuple_and_calls_service_once():
    service = StubJournalService()

    items = JournalDailyReportProvider(service).collect(REPORT_DATE)

    assert items == ()
    assert isinstance(items, tuple)
    assert service.calls == [REPORT_DATE]


def test_normal_activity_is_mapped_without_transforming_journal_strings():
    activity = _activity()

    item = JournalDailyReportProvider(StubJournalService([activity])).collect(
        REPORT_DATE
    )[0]

    assert item.source == "journal"
    assert item.source_id == "1"
    assert item.report_date == activity.activity_date
    assert item.event_time == activity.activity_time
    assert item.category == activity.category
    assert item.title == activity.title
    assert item.summary == activity.report
    assert item.importance is DailyReportImportance.NORMAL
    assert item.sort_priority == 0
    assert item.location is None
    assert item.folder_reference is None


def test_important_activity_maps_to_important_importance():
    activity = _activity(important=True)

    item = JournalDailyReportProvider(StubJournalService([activity])).collect(
        REPORT_DATE
    )[0]

    assert item.importance is DailyReportImportance.IMPORTANT


def test_empty_report_is_preserved():
    activity = _activity(report="")

    item = JournalDailyReportProvider(StubJournalService([activity])).collect(
        REPORT_DATE
    )[0]

    assert item.summary == ""


def test_very_long_report_is_not_truncated_or_modified():
    report = " Debut  " + ("detail important avec  espaces\n" * 1000) + "  Fin "
    activity = _activity(report=report)

    item = JournalDailyReportProvider(StubJournalService([activity])).collect(
        REPORT_DATE
    )[0]

    assert item.summary == report
    assert len(item.summary) == len(report)


def test_multiple_activities_preserve_the_service_order_without_sorting():
    late = _activity(1, activity_time=time(18), title="Derniere")
    early = _activity(2, activity_time=time(7), title="Premiere")

    items = JournalDailyReportProvider(StubJournalService([late, early])).collect(
        REPORT_DATE
    )

    assert [item.source_id for item in items] == ["1", "2"]
    assert [item.event_time for item in items] == [time(18), time(7)]


def test_collection_does_not_mutate_activities_or_the_source_collection():
    activity = _activity()
    original_values = vars(activity).copy()
    activities = [activity]

    JournalDailyReportProvider(StubJournalService(activities)).collect(REPORT_DATE)

    assert vars(activity) == original_values
    assert activities == [activity]


def test_activity_without_source_id_raises_an_internal_invariant_error():
    provider = JournalDailyReportProvider(StubJournalService([_activity(None)]))

    with pytest.raises(RuntimeError, match="identifiant"):
        provider.collect(REPORT_DATE)


def test_service_exception_is_propagated_unchanged():
    error = RuntimeError("journal indisponible")
    provider = JournalDailyReportProvider(StubJournalService(error=error))

    with pytest.raises(RuntimeError) as captured:
        provider.collect(REPORT_DATE)

    assert captured.value is error


def test_activity_from_another_date_is_not_artificially_corrected():
    actual_date = date(2026, 7, 21)
    activity = _activity(activity_date=actual_date)

    item = JournalDailyReportProvider(StubJournalService([activity])).collect(
        REPORT_DATE
    )[0]

    assert item.report_date == actual_date


def test_complete_chain_generates_journal_items_without_warning():
    normal = _activity(1, activity_time=time(12), title="Midi")
    important = _activity(
        2,
        activity_time=time(8),
        title="Matin",
        important=True,
    )

    report = _integrated_service(StubJournalService([normal, important])).generate(
        REPORT_DATE
    )

    assert report.item_count == 2
    assert report.report_date == REPORT_DATE
    assert [item.source for item in report.items] == ["journal", "journal"]
    assert [item.title for item in report.items] == ["Matin", "Midi"]
    assert report.items[0].importance is DailyReportImportance.IMPORTANT
    assert report.warnings == ()


def test_complete_chain_converts_journal_failure_to_a_partial_report_warning():
    report = _integrated_service(
        StubJournalService(error=RuntimeError("base indisponible"))
    ).generate(REPORT_DATE)

    assert report.items == ()
    assert report.is_partial is True
    assert len(report.warnings) == 1
    assert report.warnings[0].provider_name == "journal"
    assert report.warnings[0].warning_code == PROVIDER_COLLECTION_FAILED
