from dataclasses import FrozenInstanceError
from datetime import date, time

import pytest

from app.models.daily_report import (
    DailyReport,
    DailyReportImportance,
    DailyReportItem,
    DailyReportWarning,
)
from app.renderers.daily_report_renderer import DailyReportRenderer


REPORT_DATE = date(2026, 7, 23)


def _item(source_id="1", **overrides):
    values = {
        "source": "journal",
        "source_id": source_id,
        "report_date": REPORT_DATE,
        "category": "Patrouille",
        "title": "Centre-ville",
        "importance": DailyReportImportance.NORMAL,
        "sort_priority": 0,
        "event_time": time(8, 15),
    }
    values.update(overrides)
    return DailyReportItem(**values)


def _warning(**overrides):
    values = {
        "provider_name": "journal",
        "report_date": REPORT_DATE,
        "message": "Collecte indisponible.",
    }
    values.update(overrides)
    return DailyReportWarning(**values)


def test_render_rejects_a_non_daily_report():
    with pytest.raises(TypeError, match="DailyReport"):
        DailyReportRenderer().render(object())


def test_empty_report_has_the_complete_stable_structure():
    rendered = DailyReportRenderer().render(DailyReport(REPORT_DATE))

    assert rendered == (
        "==================================================\n"
        "POSTE MUNICIPAL PERSONNEL\n\n"
        "RAPPORT QUOTIDIEN D'ACTIVITÉ\n"
        "==================================================\n\n"
        "HEADER\n"
        "--------------------------------------------------\n\n"
        "Date : 23/07/2026\n\n"
        "SYNTHÈSE\n"
        "--------------------------------------------------\n\n"
        "Nombre d'éléments : 0\n"
        "Nombre de faits importants : 0\n"
        "Nombre d'avertissements : 0\n"
        "État : complet\n\n"
        "CHRONOLOGIE\n"
        "--------------------------------------------------\n\n"
        "Aucune activité.\n\n"
        "FAITS IMPORTANTS\n"
        "--------------------------------------------------\n\n"
        "Aucun fait important.\n\n"
        "AVERTISSEMENTS\n"
        "--------------------------------------------------\n\n"
        "Aucun avertissement.\n\n"
        "FOOTER\n"
        "--------------------------------------------------\n\n"
        "FIN DU BILAN\n"
        "État : complet\n"
        "Nombre d'avertissements : 0"
    )


def test_empty_partial_report_displays_warning_and_partial_state():
    report = DailyReport(REPORT_DATE, warnings=(_warning(),))

    rendered = DailyReportRenderer().render(report)

    assert "Nombre d'avertissements : 1" in rendered
    assert rendered.count("État : partiel") == 2
    assert "Provider : journal\nMessage : Collecte indisponible." in rendered


def test_single_item_text_contract():
    report = DailyReport(
        REPORT_DATE,
        items=(_item(summary="Compte rendu original."),),
    )

    rendered = DailyReportRenderer().render(report)

    expected_block = (
        "08:15\n\n"
        "Patrouille\n\n"
        "Centre-ville\n\n"
        "Compte rendu :\n"
        "Compte rendu original."
    )
    assert expected_block in rendered
    assert "Source :" not in rendered
    assert "source_id" not in rendered


def test_multiple_items_remain_in_report_order_without_calling_sorted(monkeypatch):
    first = _item("1", event_time=time(18), title="Premier fourni")
    second = _item("2", event_time=time(7), title="Second fourni")
    report = DailyReport(REPORT_DATE, items=(first, second))

    def forbidden_sorted(*args, **kwargs):
        raise AssertionError("Le renderer ne doit pas appeler sorted().")

    monkeypatch.setattr("builtins.sorted", forbidden_sorted)
    rendered = DailyReportRenderer().render(report)
    timeline = rendered.split("FAITS IMPORTANTS", maxsplit=1)[0]

    assert timeline.index("Premier fourni") < timeline.index("Second fourni")


def test_only_important_items_appear_in_important_section():
    normal = _item("normal", title="Élément normal")
    important = _item(
        "important",
        title="Élément important",
        importance=DailyReportImportance.IMPORTANT,
    )
    critical = _item(
        "critical",
        title="Élément critique",
        importance=DailyReportImportance.CRITICAL,
    )
    report = DailyReport(REPORT_DATE, items=(normal, important, critical))

    rendered = DailyReportRenderer().render(report)
    important_section = rendered.split("FAITS IMPORTANTS", maxsplit=1)[1].split(
        "AVERTISSEMENTS", maxsplit=1
    )[0]

    assert "Élément important" in important_section
    assert "Élément normal" not in important_section
    assert "Élément critique" not in important_section
    assert "Nombre de faits importants : 1" in rendered


def test_important_section_reuses_the_exact_item_rendering():
    item = _item(
        importance=DailyReportImportance.IMPORTANT,
        summary="Texte important",
        location="Place centrale",
    )
    renderer = DailyReportRenderer()

    rendered = renderer.render(DailyReport(REPORT_DATE, items=(item,)))

    assert rendered.count(renderer._render_item(item)) == 2


def test_item_without_time_displays_without_time():
    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, items=(_item(event_time=None),))
    )

    assert "Sans heure\n\nPatrouille" in rendered


def test_none_summary_omits_the_report_heading():
    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, items=(_item(summary=None),))
    )

    assert "Compte rendu :" not in rendered


def test_empty_summary_preserves_an_empty_report_section():
    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, items=(_item(summary=""),))
    )

    assert "Compte rendu :\n\n\nFAITS IMPORTANTS" in rendered


def test_very_long_summary_is_not_truncated():
    summary = "Début " + ("contenu très long\n" * 2000) + "Fin"

    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, items=(_item(summary=summary),))
    )

    assert summary in rendered


def test_strings_preserve_spaces_double_spaces_and_line_breaks():
    category = "  Police  administrative  "
    title = "  Titre  original  "
    summary = "  Ligne  une  \n\n Ligne deux  "
    item = _item(category=category, title=title, summary=summary)

    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, items=(item,))
    )

    assert category in rendered
    assert title in rendered
    assert summary in rendered


def test_optional_location_and_folder_are_rendered_when_present():
    item = _item(location="  Place  centrale  ", folder_reference="  D-42  ")

    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, items=(item,))
    )

    assert "Lieu :   Place  centrale  " in rendered
    assert "Dossier :   D-42  " in rendered


def test_optional_location_and_folder_are_omitted_when_absent():
    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, items=(_item(),))
    )

    assert "Lieu :" not in rendered
    assert "Dossier :" not in rendered


def test_minimal_warning_omits_optional_fields():
    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, warnings=(_warning(),))
    )

    assert "Provider : journal\nMessage : Collecte indisponible." in rendered
    assert "Code :" not in rendered
    assert "Détails :" not in rendered


def test_complete_warning_preserves_all_fields():
    warning = _warning(
        provider_name="  journal  ",
        message="  Échec  technique.  ",
        warning_code="  db_error  ",
        details="  Détail\nsur deux lignes  ",
    )

    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, warnings=(warning,))
    )

    assert "Provider :   journal  " in rendered
    assert "Message :   Échec  technique.  " in rendered
    assert "Code :   db_error  " in rendered
    assert "Détails :   Détail\nsur deux lignes  " in rendered


def test_multiple_warnings_preserve_their_order():
    first = _warning(provider_name="first", message="Premier")
    second = _warning(provider_name="second", message="Second")

    rendered = DailyReportRenderer().render(
        DailyReport(REPORT_DATE, warnings=(first, second))
    )

    assert rendered.index("Provider : first") < rendered.index("Provider : second")


def test_two_successive_renders_are_identical_and_renderer_is_stateless():
    renderer = DailyReportRenderer()
    report = DailyReport(REPORT_DATE, items=(_item(summary="Stable"),))

    first = renderer.render(report)
    second = renderer.render(report)

    assert first == second
    assert vars(renderer) == {}


def test_render_does_not_mutate_report_items_or_warnings():
    item = _item(summary="Original")
    warning = _warning()
    report = DailyReport(REPORT_DATE, items=(item,), warnings=(warning,))
    original_report_values = vars(report).copy()
    original_item_values = vars(item).copy()
    original_warning_values = vars(warning).copy()

    DailyReportRenderer().render(report)

    assert vars(report) == original_report_values
    assert vars(item) == original_item_values
    assert vars(warning) == original_warning_values
    with pytest.raises(FrozenInstanceError):
        item.title = "Modifié"


def test_renderer_module_has_no_forbidden_dependencies():
    from app.renderers import daily_report_renderer

    forbidden_names = {
        "PySide6",
        "sqlite3",
        "JournalService",
        "DailyReportService",
        "DailyReportRegistry",
        "DailyReportProvider",
    }
    assert forbidden_names.isdisjoint(vars(daily_report_renderer))
