from __future__ import annotations

import shutil
import uuid
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import QComboBox,QDateEdit,QDialog,QFileDialog,QFormLayout,QHBoxLayout,QLabel,QLineEdit,QMessageBox,QPushButton,QTextEdit,QTimeEdit,QVBoxLayout

from app.models.abusive_parking_passage import AbusiveParkingPassage


class AbusiveParkingPassageDialog(QDialog):
    def __init__(self, parking_id:int, parent=None):
        super().__init__(parent)
        self.parking_id=parking_id
        self.selected_photo_path=None
        self.passage=None
        self.setWindowTitle("Nouveau passage")
        self.resize(650,600)
        self.build_ui()

    def build_ui(self):
        layout=QVBoxLayout(self)
        form=QFormLayout()
        self.type_input=QComboBox()
        self.type_input.addItems(["Premier constat","Contrôle","Contrôle intermédiaire","Constat final","Autre"])
        self.date_input=QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.time_input=QTimeEdit()
        self.time_input.setDisplayFormat("HH:mm")
        self.time_input.setTime(QTime.currentTime())
        self.address_input=QLineEdit()
        self.latitude_input=QLineEdit()
        self.longitude_input=QLineEdit()
        self.agent_input=QLineEdit()
        self.weather_input=QLineEdit()
        self.observations_input=QTextEdit()
        for l,w in [("Type :",self.type_input),("Date :",self.date_input),("Heure :",self.time_input),("Adresse :",self.address_input),("Latitude :",self.latitude_input),("Longitude :",self.longitude_input),("Agent :",self.agent_input),("Météo :",self.weather_input),("Observations :",self.observations_input)]:
            form.addRow(l,w)
        layout.addLayout(form)
        hl=QHBoxLayout()
        self.photo_label=QLabel("Aucune photo")
        b=QPushButton("Ajouter une photo")
        b.clicked.connect(self.select_photo)
        hl.addWidget(b);hl.addWidget(self.photo_label)
        layout.addLayout(hl)
        bl=QHBoxLayout()
        s=QPushButton("Enregistrer");c=QPushButton("Annuler")
        s.clicked.connect(self.save);c.clicked.connect(self.reject)
        bl.addStretch();bl.addWidget(s);bl.addWidget(c)
        layout.addLayout(bl)

    def select_photo(self):
        fp,_=QFileDialog.getOpenFileName(self,"Choisir une photo","","Images (*.png *.jpg *.jpeg *.bmp)")
        if fp:
            self.selected_photo_path=fp
            self.photo_label.setText(Path(fp).name)

    def save_photo(self):
        if not self.selected_photo_path:
            return ""
        d=Path(__file__).resolve().parents[2]/"data"/"abusive_parking"/"passages"
        d.mkdir(parents=True,exist_ok=True)
        src=Path(self.selected_photo_path)
        dst=d/f"{uuid.uuid4().hex}{src.suffix.lower()}"
        shutil.copy2(src,dst)
        return str(dst)

    def save(self):
        if not self.address_input.text().strip():
            QMessageBox.warning(self,"Adresse","Veuillez renseigner l'adresse du contrôle.")
            return
        qd=self.date_input.date()
        def f(v):
            v=v.strip()
            if not v:return None
            try:return float(v.replace(",","."))
            except:return None
        self.passage=AbusiveParkingPassage(
            parking_id=self.parking_id,
            passage_type=self.type_input.currentText(),
            passage_date=date(qd.year(),qd.month(),qd.day()),
            passage_time=self.time_input.time().toPython(),
            address=self.address_input.text().strip(),
            latitude=f(self.latitude_input.text()),
            longitude=f(self.longitude_input.text()),
            photo_path=self.save_photo(),
            observations=self.observations_input.toPlainText().strip(),
            agent=self.agent_input.text().strip(),
            weather=self.weather_input.text().strip()
        )
        self.accept()

    def get_passage(self):
        return self.passage
