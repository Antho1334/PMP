from datetime import date

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

from app.models.daily_report import DailyReport
from app.exporters.daily_report_pdf_exporter import DailyReportPdfExporter
from app.providers.daily_report_provider import DailyReportProvider, ProviderMetadata
from app.renderers.daily_report_renderer import DailyReportRenderer
from app.services.daily_report_registry import DailyReportRegistry
from app.services.daily_report_service import DailyReportService
from app.ui.pages.daily_report_page import DailyReportPage
from app.resources.resource_manager import ResourceManager


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


class RecordingPdfExporter(DailyReportPdfExporter):
    def __init__(self):
        super().__init__("Montady", "test", ResourceManager())
        self.calls = []
        self.error = None

    def export(self, report, destination):
        self.calls.append((report, destination))
        if self.error is not None:
            raise self.error
        return destination


@pytest.fixture(scope="module", autouse=True)
def application():
    return QApplication.instance() or QApplication([])


def test_page_disables_generation_when_engine_has_no_provider():
    page = DailyReportPage(
        DailyReportService(DailyReportRegistry()),
        DailyReportRenderer(),
        RecordingPdfExporter(),
    )

    assert page.generate_button.isEnabled() is False
    assert page.preview.isReadOnly() is True
    assert "Aucune source" in page.status_label.text()


def test_page_orchestrates_service_renderer_and_display():
    registry = DailyReportRegistry()
    registry.register(EmptyProvider())
    service = RecordingService(registry)
    renderer = RecordingRenderer()
    exporter = RecordingPdfExporter()
    page = DailyReportPage(service, renderer, exporter)
    requested_date = date(2026, 7, 23)
    page.report_date.setDate(QDate(2026, 7, 23))

    page.generate_report()

    assert service.requested_dates == [requested_date]
    assert renderer.reports == [DailyReport(requested_date)]
    assert page.preview.toPlainText() == "rapport rendu"
    assert page.status_label.text() == "Rapport généré."
    assert page.export_pdf_button.isEnabled() is True


def test_pdf_button_is_disabled_initially_and_after_date_change():
    registry = DailyReportRegistry()
    registry.register(EmptyProvider())
    page = DailyReportPage(
        DailyReportService(registry),
        DailyReportRenderer(),
        RecordingPdfExporter(),
    )

    assert page.export_pdf_button.isEnabled() is False

    page.generate_report()
    assert page.export_pdf_button.isEnabled() is True

    page.report_date.setDate(page.report_date.date().addDays(1))
    assert page.export_pdf_button.isEnabled() is False


def test_pdf_export_calls_exporter_once_and_reports_success(monkeypatch):
    registry = DailyReportRegistry()
    registry.register(EmptyProvider())
    exporter = RecordingPdfExporter()
    page = DailyReportPage(
        DailyReportService(registry),
        DailyReportRenderer(),
        exporter,
    )
    page.generate_report()
    monkeypatch.setattr(
        "app.ui.pages.daily_report_page.QFileDialog.getSaveFileName",
        lambda *args: ("C:/exports/report", "Documents PDF (*.pdf)"),
    )
    messages = []
    monkeypatch.setattr(
        "app.ui.pages.daily_report_page.QMessageBox.information",
        lambda *args: messages.append(args[-1]),
    )

    page.export_pdf()

    assert exporter.calls == [(page._current_report, "C:/exports/report.pdf")]
    assert page.status_label.text() == "Export terminé."
    assert messages == ["Export terminé."]


def test_pdf_export_error_is_caught_and_reported(monkeypatch):
    registry = DailyReportRegistry()
    registry.register(EmptyProvider())
    exporter = RecordingPdfExporter()
    exporter.error = OSError("disque indisponible")
    page = DailyReportPage(
        DailyReportService(registry),
        DailyReportRenderer(),
        exporter,
    )
    page.generate_report()
    monkeypatch.setattr(
        "app.ui.pages.daily_report_page.QFileDialog.getSaveFileName",
        lambda *args: ("C:/exports/report.pdf", "Documents PDF (*.pdf)"),
    )
    messages = []
    monkeypatch.setattr(
        "app.ui.pages.daily_report_page.QMessageBox.critical",
        lambda *args: messages.append(args[-1]),
    )

    page.export_pdf()

    assert len(exporter.calls) == 1
    assert page.status_label.text() == (
        "Erreur pendant l'export : disque indisponible"
    )
    assert messages == ["Erreur pendant l'export."]
