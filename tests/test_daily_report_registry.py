from datetime import date

import pytest

from app.providers.daily_report_provider import DailyReportProvider, ProviderMetadata
from app.services.daily_report_registry import DailyReportRegistry


class FakeProvider(DailyReportProvider):
    def __init__(self, name="fake"):
        self._metadata = ProviderMetadata(name, False)

    @property
    def metadata(self):
        return self._metadata

    def collect(self, report_date: date):
        return ()


class InvalidMetadataProvider(FakeProvider):
    @property
    def metadata(self):
        return "invalid"


def test_registry_is_initially_empty():
    registry = DailyReportRegistry()

    assert registry.providers == ()
    assert registry.provider_count == 0


def test_register_preserves_order_and_returns_none():
    registry = DailyReportRegistry()
    first = FakeProvider("first")
    second = FakeProvider("second")

    result = registry.register(first)
    registry.register(second)

    assert result is None
    assert registry.providers == (first, second)
    assert registry.provider_count == 2


def test_providers_exposes_a_tuple_without_internal_mutation():
    registry = DailyReportRegistry()
    provider = FakeProvider()
    registry.register(provider)

    exposed = registry.providers
    exposed += (FakeProvider("other"),)

    assert isinstance(exposed, tuple)
    assert registry.providers == (provider,)


@pytest.mark.parametrize("provider", [None, object()])
def test_register_rejects_invalid_provider(provider):
    with pytest.raises(TypeError):
        DailyReportRegistry().register(provider)


def test_register_rejects_invalid_metadata():
    with pytest.raises(TypeError):
        DailyReportRegistry().register(InvalidMetadataProvider())


def test_register_rejects_duplicate_name_for_same_or_distinct_instances():
    registry = DailyReportRegistry()
    provider = FakeProvider("duplicate")
    registry.register(provider)

    with pytest.raises(ValueError):
        registry.register(provider)
    with pytest.raises(ValueError):
        registry.register(FakeProvider("duplicate"))


def test_unregister_removes_provider_by_name():
    registry = DailyReportRegistry()
    first = FakeProvider("first")
    second = FakeProvider("second")
    registry.register(first)
    registry.register(second)

    result = registry.unregister("first")

    assert result is None
    assert registry.providers == (second,)


@pytest.mark.parametrize("provider_name", [None, 1])
def test_unregister_rejects_non_string_name(provider_name):
    with pytest.raises(TypeError):
        DailyReportRegistry().unregister(provider_name)


@pytest.mark.parametrize("provider_name", ["", "   "])
def test_unregister_rejects_empty_name(provider_name):
    with pytest.raises(ValueError):
        DailyReportRegistry().unregister(provider_name)


def test_unregister_rejects_absent_provider():
    with pytest.raises(KeyError, match="absent"):
        DailyReportRegistry().unregister("absent")


def test_clear_removes_all_providers_and_is_idempotent():
    registry = DailyReportRegistry()
    registry.register(FakeProvider())

    registry.clear()
    registry.clear()

    assert registry.providers == ()
    assert registry.provider_count == 0
