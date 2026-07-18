from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DocumentsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Documents"))

        self.setLayout(layout)