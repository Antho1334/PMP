from datetime import date

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

from app.models.daily_report import DailyReport
from app.providers.daily_report_provider import DailyReportProvider, ProviderMetadata
from app.renderers.daily_report_renderer import DailyReportRenderer
from app.services.daily_report_registry import DailyReportRegistry
from app.services.daily_report_service import DailyReportService
from app.ui.pages.daily_report_page import DailyReportPage


class EmptyProvider(DailyReportProvider):
    @property
    def metadata(self):
        return ProviderMetadata("empty", False)

    def collect(self, report_date):
        return ()


class RecordingService(DailyReportService):
    def __init__(self, registry):
        super().__init__(registry)
        self.requested_dates = []

    def generate(self, report_date):
        self.requested_dates.append(report_date)
        return super().generate(report_date)


class RecordingRenderer(DailyReportRenderer):
    def __init__(self):
        self.reports = []

    def render(self, report):
        self.reports.append(report)
        return "rapport rendu"


@pytest.fixture(scope="module", autouse=True)
def application():
    return QApplication.instance() or QApplication([])


def test_page_disables_generation_when_engine_has_no_provider():
    page = DailyReportPage(
        DailyReportService(DailyReportRegistry()),
        DailyReportRenderer(),
    )

    assert page.generate_button.isEnabled() is False
    assert page.preview.isReadOnly() is True
    assert "Aucune source" in page.status_label.text()


def test_page_orchestrates_service_renderer_and_display():
    registry = DailyReportRegistry()
    registry.register(EmptyProvider())
    service = RecordingService(registry)
    renderer = RecordingRenderer()
    page = DailyReportPage(service, renderer)
    requested_date = date(2026, 7, 23)
    page.report_date.setDate(QDate(2026, 7, 23))

    page.generate_report()

    assert service.requested_dates == [requested_date]
    assert renderer.reports == [DailyReport(requested_date)]
    assert page.preview.toPlainText() == "rapport rendu"
    assert page.status_label.text() == "Rapport généré."
