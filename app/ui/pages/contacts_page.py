from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ContactsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Contacts"))

        self.setLayout(layout)