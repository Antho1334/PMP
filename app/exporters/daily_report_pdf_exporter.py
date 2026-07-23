"""Construction du rapport quotidien institutionnel au format PDF."""

from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from os import PathLike
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    CondPageBreak,
    Image as PlatypusImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.daily_report import (
    DailyReport,
    DailyReportImportance,
    DailyReportItem,
    DailyReportWarning,
)
from app.resources.errors import ResourceNotFoundError
from app.resources.images import Image
from app.resources.resource_manager import ResourceManager


_WEEKDAYS = (
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
    "dimanche",
)
_MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


def _paragraph_text(value: object) -> str:
    return escape(str(value)).replace("\n", "<br/>")


class _NumberedCanvas(canvas.Canvas):
    """Canvas réservé aux métadonnées et au pied de page paginé."""

    def __init__(
        self,
        *args,
        footer_lines: tuple[str, ...],
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._footer_lines = footer_lines
        self._page_states: list[dict[str, object]] = []
        self.setTitle("Rapport quotidien")
        self.setAuthor("PMP")
        self.setSubject("Police Municipale")
        self.setCreator("PMP")

    def showPage(self) -> None:
        self._page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        page_count = len(self._page_states)
        for page_number, page_state in enumerate(self._page_states, start=1):
            self.__dict__.update(page_state)
            self._draw_footer(page_number, page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_footer(self, page_number: int, page_count: int) -> None:
        self.saveState()
        self.setStrokeColor(colors.HexColor("#B7B7B7"))
        self.setLineWidth(0.4)
        self.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
        self.setFillColor(colors.HexColor("#555555"))
        self.setFont("Helvetica", 7.5)
        self.drawString(18 * mm, 10.5 * mm, " — ".join(self._footer_lines))
        self.drawRightString(
            A4[0] - 18 * mm,
            10.5 * mm,
            f"Page {page_number} / {page_count}",
        )
        self.restoreState()


class DailyReportPdfExporter:
    """Construit une représentation PDF institutionnelle d'un DailyReport."""

    def __init__(
        self,
        municipality_name: str,
        application_version: str,
        resource_manager: ResourceManager,
    ) -> None:
        if not isinstance(municipality_name, str) or not municipality_name.strip():
            raise ValueError("municipality_name doit être une chaîne non vide.")
        if not isinstance(application_version, str) or not application_version.strip():
            raise ValueError("application_version doit être une chaîne non vide.")
        if not isinstance(resource_manager, ResourceManager):
            raise TypeError("resource_manager doit être un ResourceManager.")

        self._municipality_name = municipality_name.strip()
        self._application_version = application_version.strip()
        self._resource_manager = resource_manager
        self._styles = self._create_styles()

    def export(
        self,
        report: DailyReport,
        destination: str | PathLike[str],
    ) -> Path:
        """Produit le PDF et retourne son chemin de destination."""

        if not isinstance(report, DailyReport):
            raise TypeError("report doit être un DailyReport.")
        if not isinstance(destination, (str, PathLike)):
            raise TypeError("destination doit être un chemin.")

        output_path = Path(destination)
        if not output_path.name:
            raise ValueError("destination doit désigner un fichier.")

        generated_at = datetime.now().astimezone()
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=22 * mm,
            title="Rapport quotidien",
            author="PMP",
            subject="Police Municipale",
            creator="PMP",
        )
        footer_lines = self._build_footer(generated_at)
        document.build(
            self._build_document(report, generated_at),
            canvasmaker=lambda *args, **kwargs: _NumberedCanvas(
                *args,
                footer_lines=footer_lines,
                **kwargs,
            ),
        )
        output_path.write_bytes(buffer.getvalue())
        return output_path

    def _build_document(
        self,
        report: DailyReport,
        generated_at: datetime,
    ) -> list[object]:
        story: list[object] = []
        story.extend(self._build_header(report))
        story.extend(self._build_summary(report, generated_at))
        story.extend(self._build_timeline(report))
        story.extend(self._build_important_items(report))
        story.extend(self._build_warnings(report))
        story.extend(self._build_report_end(report))
        return story

    def _build_header(self, report: DailyReport) -> list[object]:
        elements: list[object] = [
            Paragraph("RÉPUBLIQUE FRANÇAISE", self._styles["republic"]),
            Spacer(1, 3 * mm),
        ]
        patch = self._load_patch()
        if patch is not None:
            elements.extend((patch, Spacer(1, 3 * mm)))
        report_date = report.report_date
        formatted_date = (
            f"{_WEEKDAYS[report_date.weekday()]} {report_date.day} "
            f"{_MONTHS[report_date.month - 1]} {report_date.year}"
        )
        elements.extend(
            (
                Paragraph(
                    f"POLICE MUNICIPALE DE "
                    f"{_paragraph_text(self._municipality_name.upper())}",
                    self._styles["institution"],
                ),
                Spacer(1, 2 * mm),
                Paragraph(
                    "RAPPORT QUOTIDIEN D’ACTIVITÉ",
                    self._styles["document_title"],
                ),
                Spacer(1, 1.5 * mm),
                Paragraph(formatted_date, self._styles["date"]),
                Paragraph(
                    f"Rapport n° : RQ-{report_date:%Y-%m-%d}",
                    self._styles["document_number"],
                ),
                Spacer(1, 6 * mm),
            )
        )
        return elements

    def _build_summary(
        self,
        report: DailyReport,
        generated_at: datetime,
    ) -> list[object]:
        important_count = sum(
            item.importance is DailyReportImportance.IMPORTANT
            for item in report.items
        )
        rows = (
            ("Date du rapport", f"{report.report_date:%d/%m/%Y}"),
            ("Nombre d’activités", str(report.item_count)),
            ("Nombre d’éléments importants", str(important_count)),
            ("Nombre d’avertissements", str(len(report.warnings))),
            ("État", "partiel" if report.is_partial else "complet"),
            ("Généré le", generated_at.strftime("%d/%m/%Y à %H:%M:%S")),
        )
        table = Table(
            [
                [
                    Paragraph(_paragraph_text(label), self._styles["summary_label"]),
                    Paragraph(_paragraph_text(value), self._styles["summary_value"]),
                ]
                for label, value in rows
            ],
            colWidths=(62 * mm, 95 * mm),
            hAlign="CENTER",
        )
        table.setStyle(
            TableStyle(
                (
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F4F4")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#8A8A8A")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D2D2D2")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                )
            )
        )
        return [
            KeepTogether(
                [
                    Paragraph("SYNTHÈSE", self._styles["section"]),
                    table,
                ]
            ),
            Spacer(1, 6 * mm),
        ]

    def _build_timeline(self, report: DailyReport) -> list[object]:
        heading = Paragraph("CHRONOLOGIE", self._styles["section"])
        elements: list[object] = [CondPageBreak(45 * mm)]
        if not report.items:
            elements.append(
                KeepTogether(
                    [
                        heading,
                        Paragraph("Aucune activité.", self._styles["body"]),
                    ]
                )
            )
        else:
            elements.append(
                KeepTogether([heading, self._build_item(report.items[0])])
            )
            elements.append(Spacer(1, 2.5 * mm))
            for item in report.items[1:]:
                elements.extend((self._build_item(item), Spacer(1, 2.5 * mm)))
        elements.append(Spacer(1, 3 * mm))
        return elements

    def _build_important_items(self, report: DailyReport) -> list[object]:
        important_items = tuple(
            item
            for item in report.items
            if item.importance is DailyReportImportance.IMPORTANT
        )
        heading = Paragraph("FAITS IMPORTANTS", self._styles["section"])
        elements: list[object] = [CondPageBreak(55 * mm)]
        if not important_items:
            elements.append(
                KeepTogether(
                    [
                        heading,
                        Paragraph("Aucun fait important.", self._styles["body"]),
                    ]
                )
            )
        else:
            elements.append(
                KeepTogether([heading, self._build_item(important_items[0])])
            )
            elements.append(Spacer(1, 2.5 * mm))
            for item in important_items[1:]:
                elements.extend((self._build_item(item), Spacer(1, 2.5 * mm)))
        elements.append(Spacer(1, 3 * mm))
        return elements

    def _build_warnings(self, report: DailyReport) -> list[object]:
        heading = Paragraph("AVERTISSEMENTS", self._styles["section"])
        elements: list[object] = [CondPageBreak(45 * mm)]
        if not report.warnings:
            elements.append(
                KeepTogether(
                    [
                        heading,
                        Paragraph("Aucun avertissement.", self._styles["body"]),
                    ]
                )
            )
        else:
            elements.append(
                KeepTogether(
                    [heading, self._build_warning(report.warnings[0])]
                )
            )
            elements.append(Spacer(1, 2.5 * mm))
            for warning in report.warnings[1:]:
                elements.extend((self._build_warning(warning), Spacer(1, 2.5 * mm)))
        elements.append(Spacer(1, 3 * mm))
        return elements

    def _build_report_end(self, report: DailyReport) -> list[object]:
        return [
            CondPageBreak(25 * mm),
            KeepTogether(
                [
                    Paragraph("FIN DU BILAN", self._styles["section"]),
                    Paragraph(
                        f"État : {'partiel' if report.is_partial else 'complet'}",
                        self._styles["body"],
                    ),
                    Paragraph(
                        f"Nombre d’avertissements : {len(report.warnings)}",
                        self._styles["body"],
                    ),
                ]
            )
        ]

    def _build_footer(self, generated_at: datetime) -> tuple[str, ...]:
        return (
            "Document généré par PMP",
            f"Version {self._application_version}",
            generated_at.strftime("%d/%m/%Y %H:%M:%S"),
        )

    def _build_item(self, item: DailyReportItem) -> Table:
        blocks: list[object] = [
            Paragraph(
                item.event_time.strftime("%H:%M")
                if item.event_time
                else "Sans heure",
                self._styles["item_time"],
            ),
            Paragraph(_paragraph_text(item.category), self._styles["item_category"]),
            Paragraph(_paragraph_text(item.title), self._styles["item_title"]),
        ]
        if item.summary is not None:
            blocks.append(
                Paragraph(
                    f"<b>Compte rendu :</b><br/>{_paragraph_text(item.summary)}",
                    self._styles["body"],
                )
            )
        if item.location is not None:
            blocks.append(
                Paragraph(
                    f"<b>Lieu :</b> {_paragraph_text(item.location)}",
                    self._styles["body"],
                )
            )
        if item.folder_reference is not None:
            blocks.append(
                Paragraph(
                    f"<b>Dossier :</b> {_paragraph_text(item.folder_reference)}",
                    self._styles["body"],
                )
            )
        important = item.importance is DailyReportImportance.IMPORTANT
        table = Table([[blocks]], colWidths=(157 * mm,))
        table.setStyle(
            TableStyle(
                (
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#EEEEEE" if important else "#FFFFFF"),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7 if important else 0.35,
                        colors.HexColor("#888888" if important else "#C7C7C7"),
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                )
            )
        )
        return table

    def _build_warning(self, warning: DailyReportWarning) -> Table:
        blocks: list[object] = [
            Paragraph(
                f"<b>Provider :</b> {_paragraph_text(warning.provider_name)}",
                self._styles["body"],
            ),
            Paragraph(
                f"<b>Message :</b> {_paragraph_text(warning.message)}",
                self._styles["body"],
            ),
        ]
        if warning.warning_code is not None:
            blocks.append(
                Paragraph(
                    f"<b>Code :</b> {_paragraph_text(warning.warning_code)}",
                    self._styles["body"],
                )
            )
        if warning.details is not None:
            blocks.append(
                Paragraph(
                    f"<b>Détails :</b> {_paragraph_text(warning.details)}",
                    self._styles["body"],
                )
            )
        table = Table([[blocks]], colWidths=(157 * mm,))
        table.setStyle(
            TableStyle(
                (
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F7F7")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                )
            )
        )
        return table

    def _load_patch(self) -> PlatypusImage | None:
        try:
            resource = self._resource_manager.image(
                Image.MUNICIPAL_POLICE_PATCH
            )
            patch = PlatypusImage(str(resource))
        except (ResourceNotFoundError, OSError):
            return None

        maximum_width = 32 * mm
        scale = min(1.0, maximum_width / patch.imageWidth)
        patch.drawWidth = patch.imageWidth * scale
        patch.drawHeight = patch.imageHeight * scale
        patch.hAlign = "CENTER"
        return patch

    @staticmethod
    def _create_styles() -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        body = ParagraphStyle(
            "ReportBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#222222"),
            spaceAfter=2,
        )
        return {
            "body": body,
            "republic": ParagraphStyle(
                "Republic",
                parent=body,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=12,
                spaceAfter=0,
            ),
            "institution": ParagraphStyle(
                "Institution",
                parent=body,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=15,
            ),
            "document_title": ParagraphStyle(
                "DocumentTitle",
                parent=body,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=19,
            ),
            "date": ParagraphStyle(
                "ReportDate",
                parent=body,
                alignment=TA_CENTER,
                fontName="Helvetica",
                fontSize=10,
                leading=13,
            ),
            "document_number": ParagraphStyle(
                "DocumentNumber",
                parent=body,
                alignment=TA_CENTER,
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                textColor=colors.HexColor("#555555"),
            ),
            "section": ParagraphStyle(
                "Section",
                parent=body,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                fontSize=10.5,
                leading=13,
                borderWidth=0,
                borderPadding=(0, 0, 2, 0),
                textColor=colors.HexColor("#202020"),
                spaceAfter=2 * mm,
                keepWithNext=1,
            ),
            "summary_label": ParagraphStyle(
                "SummaryLabel",
                parent=body,
                fontName="Helvetica-Bold",
            ),
            "summary_value": ParagraphStyle(
                "SummaryValue",
                parent=body,
            ),
            "item_time": ParagraphStyle(
                "ItemTime",
                parent=body,
                fontName="Helvetica-Bold",
                fontSize=9.5,
            ),
            "item_category": ParagraphStyle(
                "ItemCategory",
                parent=body,
                fontName="Helvetica-Oblique",
                textColor=colors.HexColor("#555555"),
            ),
            "item_title": ParagraphStyle(
                "ItemTitle",
                parent=body,
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=13,
                spaceAfter=4,
            ),
        }
