from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.models.daily_report import DailyReportImportance, DailyReportItem
from app.providers.daily_report_provider import DailyReportProvider, ProviderMetadata


class FakeProvider(DailyReportProvider):
    def __init__(self, is_essential=False):
        self._metadata = ProviderMetadata("fake", is_essential)

    @property
    def metadata(self):
        return self._metadata

    def collect(self, report_date):
        return (
            DailyReportItem(
                source="fake",
                source_id="1",
                report_date=report_date,
                category="test",
                title="Élément factice",
                importance=DailyReportImportance.NORMAL,
                sort_priority=0,
            ),
        )


def test_daily_report_provider_is_abstract():
    with pytest.raises(TypeError):
        DailyReportProvider()


@pytest.mark.parametrize("is_essential", [False, True])
def test_fake_provider_exposes_metadata_and_collects_items(is_essential):
    provider = FakeProvider(is_essential)
    report_date = date(2026, 7, 21)

    items = tuple(provider.collect(report_date))

    assert provider.metadata == ProviderMetadata("fake", is_essential)
    assert len(items) == 1
    assert items[0].report_date == report_date


def test_provider_metadata_is_validated_and_immutable():
    metadata = ProviderMetadata("journal", True)

    with pytest.raises(FrozenInstanceError):
        metadata.name = "other"
    with pytest.raises(ValueError):
        ProviderMetadata(" ", False)
    with pytest.raises(TypeError):
        ProviderMetadata("journal", 1)


def test_contract_modules_do_not_import_ui_or_persistence_dependencies():
    from app.models import daily_report
    from app.providers import daily_report_provider

    forbidden_names = {"PySide6", "sqlite3", "Database"}
    assert forbidden_names.isdisjoint(vars(daily_report))
    assert forbidden_names.isdisjoint(vars(daily_report_provider))
