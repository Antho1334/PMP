"""Page de consultation du rapport quotidien."""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

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
    ) -> None:
        super().__init__()
        if not isinstance(daily_report_service, DailyReportService):
            raise TypeError("daily_report_service doit être un DailyReportService.")
        if not isinstance(renderer, DailyReportRenderer):
            raise TypeError("renderer doit être un DailyReportRenderer.")

        self._daily_report_service = daily_report_service
        self._renderer = renderer
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
        toolbar.addWidget(self.report_date)

        self.generate_button = QPushButton("Générer le rapport")
        self.generate_button.clicked.connect(self.generate_report)
        toolbar.addWidget(self.generate_button)
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
        self.status_label.setText(
            "Rapport partiel : certains éléments n'ont pas pu être collectés."
            if report.is_partial
            else "Rapport généré."
        )
