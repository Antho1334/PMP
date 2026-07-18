from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DossiersPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Dossiers"))

        self.setLayout(layout)