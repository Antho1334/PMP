from PySide6.QtWidgets import QListWidget


class Menu(QListWidget):

    def __init__(self, page_manager):
        super().__init__()

        self.page_manager = page_manager

        self.setFixedWidth(230)

        self.addItems([
            "🏠 Accueil",
            "📅 Journal",
            "📂 Dossiers",
            "☑ Actions",
            "🚗 Stationnement abusif",
            "📄 Arrêtés",
            "⚖ Juridique",
            "👥 Contacts",
            "📊 Tableau de bord",
            "⚙ Paramètres",
            "🗺️ Cartographie opérationnelle",
            "📋 Rapport quotidien",
        ])

        self.currentRowChanged.connect(
            self.change_page
        )

        self.setCurrentRow(0)

    def change_page(self, index):
        self.page_manager.setCurrentIndex(
            index
        )
