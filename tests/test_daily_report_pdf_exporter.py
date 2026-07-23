from base64 import b64decode
from datetime import date, time
from pathlib import Path

import pytest
from pypdf import PdfReader

from app.exporters.daily_report_pdf_exporter import DailyReportPdfExporter
from app.models.daily_report import (
    DailyReport,
    DailyReportImportance,
    DailyReportItem,
    DailyReportWarning,
)
from app.resources.catalog import IMAGE_CATALOG
from app.resources.images import Image
from app.resources.resource_manager import ResourceManager


REPORT_DATE = date(2026, 7, 23)
TINY_PNG = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
    "AAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _exporter(resource_root):
    return DailyReportPdfExporter(
        "Commune de test",
        "3.10.1-test",
        ResourceManager(resource_root),
    )


def _pdf_text(path):
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def _item(**overrides):
    values = {
        "source": "journal",
        "source_id": "ACT-42",
        "report_date": REPORT_DATE,
        "category": "Patrouille générale",
        "title": "Contrôle place de la République",
        "importance": DailyReportImportance.IMPORTANT,
        "sort_priority": 10,
        "event_time": time(9, 15),
        "summary": "Vérification effectuée\nSans incident.",
        "location": "Place de la République",
        "folder_reference": "Dossier PM-2026-42",
    }
    values.update(overrides)
    return DailyReportItem(**values)


def test_export_creates_a_non_empty_pdf_with_metadata(tmp_path):
    destination = tmp_path / "rapport.pdf"

    result = _exporter(tmp_path).export(DailyReport(REPORT_DATE), destination)

    assert result == destination
    assert destination.is_file()
    assert destination.stat().st_size > 0
    reader = PdfReader(destination)
    assert reader.metadata.title == "Rapport quotidien"
    assert reader.metadata.author == "PMP"
    assert reader.metadata.subject == "Police Municipale"
    assert reader.metadata.creator == "PMP"


def test_empty_report_keeps_institutional_and_empty_sections(tmp_path):
    destination = tmp_path / "empty.pdf"

    _exporter(tmp_path).export(DailyReport(REPORT_DATE), destination)

    text = _pdf_text(destination)
    assert "POLICE MUNICIPALE DE COMMUNE DE TEST" in text
    assert "RQ-2026-07-23" in text
    assert "Aucune activité." in text
    assert "Aucun fait important." in text
    assert "Aucun avertissement." in text


def test_export_preserves_every_daily_report_value(tmp_path):
    destination = tmp_path / "complete.pdf"
    warning = DailyReportWarning(
        provider_name="journal",
        report_date=REPORT_DATE,
        message="Collecte partielle",
        warning_code="journal_partial",
        details="Une activité indisponible",
    )

    _exporter(tmp_path).export(
        DailyReport(REPORT_DATE, items=(_item(),), warnings=(warning,)),
        destination,
    )

    text = _pdf_text(destination)
    for expected in (
        "09:15",
        "Patrouille générale",
        "Contrôle place de la République",
        "Vérification effectuée",
        "Sans incident.",
        "Place de la République",
        "Dossier PM-2026-42",
        "journal",
        "Collecte partielle",
        "journal_partial",
        "Une activité indisponible",
        "partiel",
    ):
        assert expected in text


def test_important_item_is_present_in_timeline_and_important_section(tmp_path):
    destination = tmp_path / "important.pdf"

    _exporter(tmp_path).export(
        DailyReport(REPORT_DATE, items=(_item(title="Fait signalé"),)),
        destination,
    )

    assert _pdf_text(destination).count("Fait signalé") == 2


def test_missing_patch_does_not_interrupt_generation(tmp_path):
    destination = tmp_path / "without-patch.pdf"

    _exporter(tmp_path).export(DailyReport(REPORT_DATE), destination)

    assert destination.is_file()
    assert "RAPPORT QUOTIDIEN" in _pdf_text(destination)


def test_patch_is_requested_exclusively_through_resource_manager(tmp_path):
    patch = tmp_path / IMAGE_CATALOG[Image.MUNICIPAL_POLICE_PATCH]
    patch.parent.mkdir(parents=True)
    patch.write_bytes(TINY_PNG)

    class RecordingResourceManager(ResourceManager):
        def __init__(self, root):
            super().__init__(root)
            self.requests = []

        def image(self, resource):
            self.requests.append(resource)
            return super().image(resource)

    resources = RecordingResourceManager(tmp_path)
    exporter = DailyReportPdfExporter("Test", "1.0", resources)

    exporter.export(DailyReport(REPORT_DATE), tmp_path / "with-patch.pdf")

    assert resources.requests == [Image.MUNICIPAL_POLICE_PATCH]


def test_disk_write_error_is_propagated_without_partial_file(tmp_path):
    missing_parent = tmp_path / "missing" / "rapport.pdf"

    with pytest.raises(OSError):
        _exporter(tmp_path).export(DailyReport(REPORT_DATE), missing_parent)

    assert not missing_parent.exists()


@pytest.mark.parametrize("invalid_report", [None, object(), "report"])
def test_export_rejects_non_daily_report(invalid_report, tmp_path):
    with pytest.raises(TypeError):
        _exporter(tmp_path).export(invalid_report, tmp_path / "report.pdf")


def test_exporter_has_no_forbidden_architecture_dependencies():
    from app.exporters import daily_report_pdf_exporter

    forbidden_names = {
        "PySide6",
        "Qt",
        "JournalService",
        "DailyReportRegistry",
        "DailyReportProvider",
        "sqlite3",
        "Database",
    }
    assert forbidden_names.isdisjoint(vars(daily_report_pdf_exporter))
    source = Path(daily_report_pdf_exporter.__file__).read_text(encoding="utf-8")
    assert "pm_montady_patch" not in source
