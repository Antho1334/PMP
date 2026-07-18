from pathlib import Path

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter


class JournalPdfService:
    """
    Service responsable de l'export PDF du Journal PMP.
    """

    def export(self, activities, file_path):
        """
        Exporte une liste d'activités dans un fichier PDF.
        """

        if not activities:
            raise ValueError(
                "Aucune activité à exporter."
            )

        # Création du dossier parent si nécessaire
        Path(file_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ------------------------------------------------------
        # Construction du document HTML
        # ------------------------------------------------------

        html = """
        <html>
        <head>
        <meta charset="utf-8">

        <style>

        body {
            font-family: Arial;
            font-size: 11pt;
        }

        h1 {
            text-align: center;
            font-size: 20pt;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th {
            background-color: #dddddd;
            font-weight: bold;
            padding: 6px;
            border: 1px solid #888888;
        }

        td {
            padding: 6px;
            border: 1px solid #aaaaaa;
            vertical-align: top;
        }

        .important {
            font-weight: bold;
        }

        </style>

        </head>

        <body>

        <h1>Journal quotidien PMP</h1>

        <table>

        <tr>
            <th>Date</th>
            <th>Heure</th>
            <th>Catégorie</th>
            <th>Objet</th>
            <th>Compte-rendu</th>
            <th>Important</th>
        </tr>
        """

        # ------------------------------------------------------
        # Ajout des activités
        # ------------------------------------------------------

        for activity in activities:

            important = (
                "OUI"
                if activity.important
                else ""
            )

            html += f"""
            <tr>
                <td>
                    {activity.activity_date.strftime("%d/%m/%Y")}
                </td>

                <td>
                    {activity.activity_time.strftime("%H:%M")}
                </td>

                <td>
                    {activity.category}
                </td>

                <td>
                    {activity.title}
                </td>

                <td>
                    {activity.report}
                </td>

                <td class="important">
                    {important}
                </td>
            </tr>
            """

        html += """
        </table>

        </body>
        </html>
        """

        # ------------------------------------------------------
        # Création du document Qt
        # ------------------------------------------------------

        document = QTextDocument()

        document.setHtml(
            html
        )

        # ------------------------------------------------------
        # Configuration du PDF
        # ------------------------------------------------------

        printer = QPrinter(
            QPrinter.HighResolution
        )

        printer.setOutputFormat(
            QPrinter.PdfFormat
        )

        printer.setOutputFileName(
            str(file_path)
        )

        # ------------------------------------------------------
        # Génération du PDF
        # ------------------------------------------------------

        document.print_(
            printer
        )