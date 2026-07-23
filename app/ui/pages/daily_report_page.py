"""Page de consultation du rapport quotidien."""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.exporters.daily_report_pdf_exporter import DailyReportPdfExporter
from app.models.daily_report import DailyReport
from app.renderers.daily_report_renderer import DailyReportRenderer
from app.services.daily_report_service import (
    DailyReportGenerationError,
    DailyReportService,
)


class DailyReportPage(QWidget):
    """Orchestre la génération et l'affichage d'un rapport quotidien."""

    def __init__(
        self,
        daily_report_service: DailyReportService,
        renderer: DailyReportRenderer,
        pdf_exporter: DailyReportPdfExporter,
    ) -> None:
        super().__init__()
        if not isinstance(daily_report_service, DailyReportService):
            raise TypeError("daily_report_service doit être un DailyReportService.")
        if not isinstance(renderer, DailyReportRenderer):
            raise TypeError("renderer doit être un DailyReportRenderer.")
        if not isinstance(pdf_exporter, DailyReportPdfExporter):
            raise TypeError("pdf_exporter doit être un DailyReportPdfExporter.")

        self._daily_report_service = daily_report_service
        self._renderer = renderer
        self._pdf_exporter = pdf_exporter
        self._current_report: DailyReport | None = None
        self._build_ui()
        self._update_availability()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Rapport quotidien")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Date :"))

        self.report_date = QDateEdit()
        self.report_date.setCalendarPopup(True)
        self.report_date.setDisplayFormat("dd/MM/yyyy")
        self.report_date.setDate(QDate.currentDate())
        self.report_date.dateChanged.connect(self._invalidate_export)
        toolbar.addWidget(self.report_date)

        self.generate_button = QPushButton("Générer le rapport")
        self.generate_button.clicked.connect(self.generate_report)
        toolbar.addWidget(self.generate_button)

        self.export_pdf_button = QPushButton("Exporter PDF")
        self.export_pdf_button.setEnabled(False)
        self.export_pdf_button.clicked.connect(self.export_pdf)
        toolbar.addWidget(self.export_pdf_button)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Le rapport généré apparaîtra ici.")
        layout.addWidget(self.preview, 1)

    def _update_availability(self) -> None:
        is_available = self._daily_report_service.has_registered_providers
        self.generate_button.setEnabled(is_available)
        if is_available:
            self.status_label.setText("Sélectionnez une date puis générez le rapport.")
        else:
            self.status_label.setText(
                "Aucune source de rapport n'est actuellement disponible."
            )

    def generate_report(self) -> None:
        """Génère, rend puis affiche le rapport pour la date sélectionnée."""

        self._invalidate_export()
        report_date = self.report_date.date().toPython()
        try:
            report = self._daily_report_service.generate(report_date)
        except DailyReportGenerationError as exc:
            self.preview.clear()
            self.status_label.setText(
                f"Impossible de générer le rapport : {exc}"
            )
            return

        rendered_report = self._renderer.render(report)
        self.preview.setPlainText(rendered_report)
        self._current_report = report
        self.export_pdf_button.setEnabled(True)
        self.status_label.setText(
            "Rapport partiel : certains éléments n'ont pas pu être collectés."
            if report.is_partial
            else "Rapport généré."
        )

    def export_pdf(self) -> None:
        """Demande une destination puis exporte le rapport courant en PDF."""

        if self._current_report is None:
            return

        suggested_name = (
            f"rapport_quotidien_{self._current_report.report_date:%Y-%m-%d}.pdf"
        )
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter le rapport quotidien",
            suggested_name,
            "Documents PDF (*.pdf)",
        )
        if not destination:
            return
        if not destination.lower().endswith(".pdf"):
            destination += ".pdf"

        try:
            self._pdf_exporter.export(self._current_report, destination)
        except Exception as exc:
            self.status_label.setText(f"Erreur pendant l'export : {exc}")
            QMessageBox.critical(
                self,
                "Export PDF",
                "Erreur pendant l'export.",
            )
            return

        self.status_label.setText("Export terminé.")
        QMessageBox.information(
            self,
            "Export PDF",
            "Export terminé.",
        )

    def _invalidate_export(self) -> None:
        self._current_report = None
        self.export_pdf_button.setEnabled(False)
