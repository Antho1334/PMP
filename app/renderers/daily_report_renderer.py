"""Restitution textuelle d'un bilan quotidien."""

from app.models.daily_report import (
    DailyReport,
    DailyReportImportance,
    DailyReportItem,
    DailyReportWarning,
)


_LINE_SEPARATOR = "\n"
_BLOCK_SEPARATOR = "\n\n"
_SECTION_SEPARATOR = "\n\n"
_DOCUMENT_RULE = "=" * 50
_SECTION_RULE = "-" * 50


class DailyReportRenderer:
    """Produit une représentation textuelle déterministe d'un bilan."""

    def render(self, report: DailyReport) -> str:
        """Restitue le rapport sous forme de texte brut."""

        if not isinstance(report, DailyReport):
            raise TypeError("report doit être un DailyReport.")

        sections = (
            self._render_header(report),
            self._render_summary(report),
            self._render_timeline(report),
            self._render_important_items(report),
            self._render_warnings(report),
            self._render_footer(report),
        )
        return _SECTION_SEPARATOR.join(sections)

    def _render_header(self, report: DailyReport) -> str:
        document_title = _BLOCK_SEPARATOR.join(
            ("POSTE MUNICIPAL PERSONNEL", "RAPPORT QUOTIDIEN D'ACTIVITÉ")
        )
        heading = _LINE_SEPARATOR.join(
            (_DOCUMENT_RULE, document_title, _DOCUMENT_RULE)
        )
        content = f"Date : {report.report_date:%d/%m/%Y}"
        return _BLOCK_SEPARATOR.join(
            (heading, self._render_section_title("HEADER"), content)
        )

    def _render_summary(self, report: DailyReport) -> str:
        important_count = sum(
            item.importance is DailyReportImportance.IMPORTANT
            for item in report.items
        )
        lines = (
            f"Nombre d'éléments : {report.item_count}",
            f"Nombre de faits importants : {important_count}",
            f"Nombre d'avertissements : {len(report.warnings)}",
            f"État : {self._render_state(report)}",
        )
        return _BLOCK_SEPARATOR.join(
            (
                self._render_section_title("SYNTHÈSE"),
                _LINE_SEPARATOR.join(lines),
            )
        )

    def _render_timeline(self, report: DailyReport) -> str:
        content = (
            _BLOCK_SEPARATOR.join(self._render_item(item) for item in report.items)
            if report.items
            else "Aucune activité."
        )
        return _BLOCK_SEPARATOR.join(
            (self._render_section_title("CHRONOLOGIE"), content)
        )

    def _render_item(self, item: DailyReportItem) -> str:
        blocks = [
            item.event_time.strftime("%H:%M") if item.event_time else "Sans heure",
            item.category,
            item.title,
        ]
        if item.summary is not None:
            blocks.append(
                _LINE_SEPARATOR.join(("Compte rendu :", item.summary))
            )
        if item.location is not None:
            blocks.append(f"Lieu : {item.location}")
        if item.folder_reference is not None:
            blocks.append(f"Dossier : {item.folder_reference}")
        return _BLOCK_SEPARATOR.join(blocks)

    def _render_important_items(self, report: DailyReport) -> str:
        important_items = tuple(
            item
            for item in report.items
            if item.importance is DailyReportImportance.IMPORTANT
        )
        content = (
            _BLOCK_SEPARATOR.join(
                self._render_item(item) for item in important_items
            )
            if important_items
            else "Aucun fait important."
        )
        return _BLOCK_SEPARATOR.join(
            (self._render_section_title("FAITS IMPORTANTS"), content)
        )

    def _render_warnings(self, report: DailyReport) -> str:
        content = (
            _BLOCK_SEPARATOR.join(
                self._render_warning(warning) for warning in report.warnings
            )
            if report.warnings
            else "Aucun avertissement."
        )
        return _BLOCK_SEPARATOR.join(
            (self._render_section_title("AVERTISSEMENTS"), content)
        )

    def _render_warning(self, warning: DailyReportWarning) -> str:
        lines = [
            f"Provider : {warning.provider_name}",
            f"Message : {warning.message}",
        ]
        if warning.warning_code is not None:
            lines.append(f"Code : {warning.warning_code}")
        if warning.details is not None:
            lines.append(f"Détails : {warning.details}")
        return _LINE_SEPARATOR.join(lines)

    def _render_footer(self, report: DailyReport) -> str:
        content = _LINE_SEPARATOR.join(
            (
                "FIN DU BILAN",
                f"État : {self._render_state(report)}",
                f"Nombre d'avertissements : {len(report.warnings)}",
            )
        )
        return _BLOCK_SEPARATOR.join(
            (self._render_section_title("FOOTER"), content)
        )

    @staticmethod
    def _render_section_title(title: str) -> str:
        return _LINE_SEPARATOR.join((title, _SECTION_RULE))

    @staticmethod
    def _render_state(report: DailyReport) -> str:
        return "partiel" if report.is_partial else "complet"
