from dataclasses import FrozenInstanceError
from datetime import date, datetime, time

import pytest

from app.models.daily_report import (
    DailyReport,
    DailyReportImportance,
    DailyReportItem,
    DailyReportWarning,
    daily_report_sort_key,
)


REPORT_DATE = date(2026, 7, 21)


def _item(**overrides):
    values = {
        "source": "journal",
        "source_id": "entry-1",
        "report_date": REPORT_DATE,
        "category": "activity",
        "title": "Patrouille",
        "importance": DailyReportImportance.NORMAL,
        "sort_priority": 10,
    }
    values.update(overrides)
    return DailyReportItem(**values)


def test_daily_report_item_is_valid_and_immutable():
    item = _item(event_time=time(8, 30))

    assert item.event_time == time(8, 30)
    with pytest.raises(FrozenInstanceError):
        item.title = "Autre titre"


def test_daily_report_item_accepts_an_absent_event_time():
    assert _item().event_time is None


@pytest.mark.parametrize("field_name", ["source", "source_id", "category", "title"])
@pytest.mark.parametrize("invalid_value", ["", "   "])
def test_daily_report_item_rejects_empty_required_strings(field_name, invalid_value):
    with pytest.raises(ValueError):
        _item(**{field_name: invalid_value})


@pytest.mark.parametrize("report_date", ["2026-07-21", datetime(2026, 7, 21, 8)])
def test_daily_report_item_rejects_invalid_date_types(report_date):
    with pytest.raises(TypeError):
        _item(report_date=report_date)


def test_daily_report_item_rejects_invalid_event_time():
    with pytest.raises(TypeError):
        _item(event_time="08:30")


@pytest.mark.parametrize("priority", [-1, 1.5, True])
def test_daily_report_item_rejects_invalid_priority(priority):
    with pytest.raises((TypeError, ValueError)):
        _item(sort_priority=priority)


def test_daily_report_item_rejects_untyped_importance():
    with pytest.raises(TypeError):
        _item(importance="normal")


def test_sort_key_is_stable_and_places_absent_times_last():
    early = _item(source_id="early", event_time=time(8), title="B")
    late = _item(source_id="late", event_time=time(10), title="A")
    unknown = _item(source_id="unknown", event_time=None, title="A")

    assert sorted([unknown, late, early], key=daily_report_sort_key) == [
        early,
        late,
        unknown,
    ]


def test_sort_key_uses_intrinsic_tie_breakers():
    items = [
        _item(source_id="2", source="z", title="B", category="b"),
        _item(source_id="1", source="a", title="A", category="a"),
    ]

    assert sorted(items, key=daily_report_sort_key) == [items[1], items[0]]


def test_daily_report_can_be_empty_without_being_partial():
    report = DailyReport(REPORT_DATE)

    assert report.items == ()
    assert report.warnings == ()
    assert report.item_count == 0
    assert report.is_partial is False


def test_daily_report_is_partial_when_it_contains_a_warning():
    warning = DailyReportWarning("optional", REPORT_DATE, "Collecte indisponible")
    report = DailyReport(REPORT_DATE, warnings=[warning])

    assert report.warnings == (warning,)
    assert report.is_partial is True


def test_daily_report_rejects_an_item_from_another_date():
    with pytest.raises(ValueError):
        DailyReport(REPORT_DATE, items=[_item(report_date=date(2026, 7, 20))])


def test_daily_report_copies_collections_to_immutable_tuples():
    item = _item()
    source_items = [item]
    report = DailyReport(REPORT_DATE, items=source_items)
    source_items.clear()

    assert report.items == (item,)
    assert report.item_count == 1
    with pytest.raises(FrozenInstanceError):
        report.items = ()


def test_warning_validates_required_fields_and_is_immutable():
    warning = DailyReportWarning("provider", REPORT_DATE, "Incident", "timeout", "Détail")

    with pytest.raises(FrozenInstanceError):
        warning.message = "Autre"
    with pytest.raises(ValueError):
        DailyReportWarning("", REPORT_DATE, "Incident")
    with pytest.raises(ValueError):
        DailyReportWarning("provider", REPORT_DATE, " ")
    with pytest.raises(TypeError):
        DailyReportWarning("provider", datetime(2026, 7, 21, 8), "Incident")
