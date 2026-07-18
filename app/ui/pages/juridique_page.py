from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class JuridiquePage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Juridique"))

        self.setLayout(layout)