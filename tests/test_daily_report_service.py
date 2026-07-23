from datetime import date, datetime, time

import pytest

from app.models.daily_report import (
    DailyReportImportance,
    DailyReportItem,
    daily_report_sort_key,
)
from app.providers.daily_report_provider import DailyReportProvider, ProviderMetadata
from app.services.daily_report_registry import DailyReportRegistry
from app.services.daily_report_service import (
    INVALID_PROVIDER_NAME,
    PROVIDER_COLLECTION_FAILED,
    DailyReportGenerationError,
    DailyReportService,
)


REPORT_DATE = date(2026, 7, 21)


def _item(source_id="1", **overrides):
    values = {
        "source": "fake",
        "source_id": source_id,
        "report_date": REPORT_DATE,
        "category": "test",
        "title": f"Item {source_id}",
        "importance": DailyReportImportance.NORMAL,
        "sort_priority": 10,
    }
    values.update(overrides)
    return DailyReportItem(**values)


class FakeProvider(DailyReportProvider):
    def __init__(self, name="fake", items=(), is_essential=False, error=None):
        self._metadata = ProviderMetadata(name, is_essential)
        self.items = items
        self.error = error
        self.calls = []

    @property
    def metadata(self):
        return self._metadata

    def collect(self, report_date):
        self.calls.append(report_date)
        if self.error is not None:
            raise self.error
        return self.items


class DynamicMetadataProvider(FakeProvider):
    @property
    def metadata(self):
        return self._metadata


class FailingMetadataProvider(FakeProvider):
    @property
    def metadata(self):
        if getattr(self, "metadata_error", None) is not None:
            raise self.metadata_error
        return self._metadata


def _service(*providers):
    registry = DailyReportRegistry()
    for provider in providers:
        registry.register(provider)
    return DailyReportService(registry)


def test_service_requires_registry():
    with pytest.raises(TypeError):
        DailyReportService(object())


def test_registered_provider_availability_is_read_only_and_tracks_registry():
    registry = DailyReportRegistry()
    service = DailyReportService(registry)

    assert service.has_registered_providers is False

    registry.register(FakeProvider())
    assert service.has_registered_providers is True

    with pytest.raises(AttributeError):
        service.has_registered_providers = False

    registry.clear()
    assert service.has_registered_providers is False


def test_generate_without_provider_returns_complete_empty_report():
    report = _service().generate(REPORT_DATE)

    assert report.report_date == REPORT_DATE
    assert report.items == ()
    assert report.warnings == ()
    assert report.item_count == 0
    assert report.is_partial is False


@pytest.mark.parametrize("invalid_date", [None, "2026-07-21", datetime(2026, 7, 21, 8)])
def test_generate_rejects_invalid_date_before_calling_providers(invalid_date):
    provider = FakeProvider()

    with pytest.raises(TypeError):
        _service(provider).generate(invalid_date)

    assert provider.calls == []


@pytest.mark.parametrize("factory", [list, tuple, lambda items: (item for item in items)])
def test_list_tuple_and_generator_produce_identical_results(factory):
    items = [_item("1"), _item("2")]

    report = _service(FakeProvider(items=factory(items))).generate(REPORT_DATE)

    assert report.items == tuple(sorted(items, key=daily_report_sort_key))


def test_multiple_providers_are_called_once_and_all_items_are_sorted():
    late = _item("late", event_time=time(12), sort_priority=20)
    early = _item("early", event_time=time(8), sort_priority=10)
    first = FakeProvider("first", [late])
    second = FakeProvider("second", [early])

    report = _service(first, second).generate(REPORT_DATE)

    assert report.items == (early, late)
    assert first.calls == [REPORT_DATE]
    assert second.calls == [REPORT_DATE]


def test_empty_provider_returns_complete_empty_report():
    report = _service(FakeProvider(items=[])).generate(REPORT_DATE)

    assert report.item_count == 0
    assert report.is_partial is False


def test_optional_provider_call_failure_becomes_contextual_warning():
    provider = FakeProvider("optional", error=RuntimeError("database unavailable"))

    report = _service(provider).generate(REPORT_DATE)

    warning = report.warnings[0]
    assert warning.provider_name == "optional"
    assert warning.report_date == REPORT_DATE
    assert warning.warning_code == PROVIDER_COLLECTION_FAILED
    assert warning.message == "Provider collection failed."
    assert warning.details == "database unavailable"
    assert report.is_partial is True


def _failing_generator():
    yield _item("partial")
    raise RuntimeError("iteration failed")


def test_optional_generator_failure_is_atomic_and_following_provider_runs():
    failing = FakeProvider("failing", _failing_generator())
    successful_item = _item("successful")
    following = FakeProvider("following", [successful_item])

    report = _service(failing, following).generate(REPORT_DATE)

    assert report.items == (successful_item,)
    assert [warning.provider_name for warning in report.warnings] == ["failing"]
    assert following.calls == [REPORT_DATE]


@pytest.mark.parametrize(
    "items",
    [None, 42, "items", b"items", [object()], [_item(report_date=date(2026, 7, 20))]],
)
def test_optional_provider_contract_violations_become_warnings(items):
    report = _service(FakeProvider("invalid", items)).generate(REPORT_DATE)

    assert report.items == ()
    assert len(report.warnings) == 1


@pytest.mark.parametrize("deferred", [False, True])
def test_essential_failure_is_contextual_and_stops_following_providers(deferred):
    cause = RuntimeError("failed")
    if deferred:
        def items():
            raise cause
            yield
        source = items()
        essential = FakeProvider("essential", source, is_essential=True)
    else:
        essential = FakeProvider("essential", is_essential=True, error=cause)
    following = FakeProvider("following", [_item()])

    with pytest.raises(DailyReportGenerationError) as captured:
        _service(essential, following).generate(REPORT_DATE)

    assert captured.value.provider_name == "essential"
    assert captured.value.report_date == REPORT_DATE
    assert captured.value.__cause__ is cause
    assert following.calls == []


def test_multiple_optional_failures_create_multiple_warnings():
    report = _service(
        FakeProvider("first", error=RuntimeError("first")),
        FakeProvider("second", None),
    ).generate(REPORT_DATE)

    assert [warning.provider_name for warning in report.warnings] == ["first", "second"]
    assert report.item_count == 0
    assert report.is_partial is True


def test_metadata_becoming_invalid_after_registration_is_blocking():
    provider = DynamicMetadataProvider("initial")
    registry = DailyReportRegistry()
    registry.register(provider)
    provider._metadata = "invalid"

    with pytest.raises(DailyReportGenerationError) as captured:
        DailyReportService(registry).generate(REPORT_DATE)

    assert captured.value.provider_name == INVALID_PROVIDER_NAME
    assert captured.value.report_date == REPORT_DATE
    assert isinstance(captured.value.__cause__, TypeError)


def test_metadata_access_failure_after_registration_is_blocking():
    provider = FailingMetadataProvider("initial")
    registry = DailyReportRegistry()
    registry.register(provider)
    provider.metadata_error = RuntimeError("metadata unavailable")

    with pytest.raises(DailyReportGenerationError) as captured:
        DailyReportService(registry).generate(REPORT_DATE)

    assert captured.value.provider_name == INVALID_PROVIDER_NAME
    assert captured.value.report_date == REPORT_DATE
    assert captured.value.__cause__ is provider.metadata_error


def test_source_collection_and_items_are_not_mutated():
    item = _item()
    source = [item]

    report = _service(FakeProvider(items=source)).generate(REPORT_DATE)

    assert source == [item]
    assert report.items == (item,)
    assert report.items[0] is item
