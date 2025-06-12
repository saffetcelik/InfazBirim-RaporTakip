import sys, json, os
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pyautogui, time, win32clipboard, win32con, keyboard
import win32com.client
from PyQt6.QtWidgets import QFileDialog
import subprocess
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, 
                             QCalendarWidget, QSplitter, QFrame, QHeaderView,
                             QDialog, QDialogButtonBox, QFormLayout, QDateTimeEdit,
                             QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QDateTime, QDate, QSize
from PyQt6.QtGui import QColor, QBrush, QPainter, QFont
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
                             QDateEdit, QComboBox, QPushButton, QLabel, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
import json
import os
from datetime import datetime, timedelta


data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'veriler')
os.makedirs(data_dir, exist_ok=True)

class Worker(QObject):
    finished, notify = pyqtSignal(), pyqtSignal(str, str, str)
    def __init__(self, notes): super().__init__(); self.notes = notes
    def run(self):
        while True:
            current_time = datetime.now()
            for note in self.notes:
                reminder_time = datetime.strptime(note['reminder'], "%Y-%m-%d %H:%M")
                if current_time >= reminder_time and not note.get('notified', False):
                    self.notify.emit(note['title'], note['content'], note.get('id', ''))
                    note['notified'] = True
            QThread.msleep(60000)

class EsasNoLineEdit(QLineEdit):
    def __init__(self): super().__init__(); self.textChanged.connect(self.on_text_changed)
    def on_text_changed(self, text):
        if len(text) == 4 and text.isdigit() and '/' not in text:
            self.setText(f"{text}/"); self.setCursorPosition(5)

class EditableTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, editable=True):
        super().__init__(text)
        self.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | (Qt.ItemFlag.ItemIsEditable if editable else Qt.ItemFlag.NoItemFlags))

class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd.MM.yyyy")
        self.setDate(QDate.currentDate())
    def mousePressEvent(self, event):
        self.calendarWidget().setSelectedDate(self.date())
        super().mousePressEvent(event)

class CustomDateTimeEdit(QDateTimeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.setDateTime(QDateTime.currentDateTime())
    def mousePressEvent(self, event):
        self.calendarWidget().setSelectedDate(self.date())
        super().mousePressEvent(event)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hakkında")
        self.setFixedSize(400, 200)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Dosya Takip Sistemi", alignment=Qt.AlignmentFlag.AlignCenter, font=QFont("Arial", 16, QFont.Weight.Bold)))
        layout.addWidget(QLabel("Bu program Adalet Bakanlığı personelleri için\nSaffet Çelik (229301) tarafından hazırlanmıştır.\nKopyalanabilir. Dağıtılabilir.\nMail İletişim: ab229301@adalet.gov.tr\nHaberci:ab229301", alignment=Qt.AlignmentFlag.AlignCenter, font=QFont("Arial", 12)))

class NoteDialog(QDialog):
    def __init__(self, parent=None, note=None):
        super().__init__(parent)
        self.setWindowTitle("Not Ekle/Düzenle")
        self.setFixedSize(400, 400)
        layout = QVBoxLayout(self)
        self.note = note
        self.title_input = QLineEdit(note['title'] if note else "")
        self.content_input = QTextEdit(note['content'] if note else "")
        self.reminder_input = CustomDateTimeEdit()
        if note and note.get('reminder'):
            self.reminder_input.setDateTime(QDateTime.fromString(note['reminder'], "%Y-%m-%d %H:%M"))
        self.tag_input = QLineEdit(', '.join(note['tags']) if note and 'tags' in note else "")
        layout.addWidget(QLabel("Başlık:"))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("İçerik:"))
        layout.addWidget(self.content_input)
        layout.addWidget(QLabel("Hatırlatma Zamanı:"))
        layout.addWidget(self.reminder_input)
        layout.addWidget(QLabel("Etiketler (virgülle ayırın):"))
        layout.addWidget(self.tag_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_note_data(self):
        return {
            'id': self.note['id'] if self.note else datetime.now().strftime("%Y%m%d%H%M%S"),
            'title': self.title_input.text(),
            'content': self.content_input.toPlainText(),
            'reminder': self.reminder_input.dateTime().toString("yyyy-MM-dd HH:mm"),
            'created_at': self.note['created_at'] if self.note else datetime.now().strftime("%Y-%m-%d"),
            'tags': [tag.strip() for tag in self.tag_input.text().split(',') if tag.strip()]
        }

class NotificationSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bildirim Ayarları")
        self.setFixedSize(300, 200)
        layout = QVBoxLayout(self)
        self.enable_notifications = QCheckBox("Bildirimleri Etkinleştir")
        self.notification_sound = QCheckBox("Bildirim Sesi")
        self.notification_popup = QCheckBox("Bildirim Popup'ı")
        layout.addWidget(self.enable_notifications)
        layout.addWidget(self.notification_sound)
        layout.addWidget(self.notification_popup)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self):
        return {
            'enable_notifications': self.enable_notifications.isChecked(),
            'notification_sound': self.notification_sound.isChecked(),
            'notification_popup': self.notification_popup.isChecked()
        }


class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes = []

    def setNotes(self, notes):
        self.notes = notes
        self.updateCells()

    def paintCell(self, painter, rect, date):
        painter.save()

        # Orijinal hücre çizimi
        super().paintCell(painter, rect, date)

        notes_for_day = [note for note in self.notes if note['reminder'].startswith(date.toString("yyyy-MM-dd"))]
        
        if notes_for_day:
            # Şeffaf renklendirme
            if len(notes_for_day) > 1:
                color = QColor(255, 0, 0, 30)  # Şeffaf kırmızı
            else:
                color = QColor(0, 255, 0, 30)  # Şeffaf yeşil
            
            painter.fillRect(rect, color)

            # Not sayısını göster
            painter.setPen(Qt.GlobalColor.black)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(rect.adjusted(0, 0, -2, -2), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, str(len(notes_for_day)))

        painter.restore()


class NotesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes = []
        self.notification_settings = self.load_notification_settings()
        self.load_notes()
        self.init_ui()
        self.notification_thread = QThread()
        self.worker = Worker(self.notes)
        self.worker.moveToThread(self.notification_thread)
        self.notification_thread.started.connect(self.worker.run)
        self.worker.notify.connect(self.show_notification)
        self.notification_thread.start()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="Notlarda ara...")
        self.search_input.textChanged.connect(self.filter_notes)
        search_layout.addWidget(self.search_input)
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("Tüm Etiketler")
        self.tag_filter.currentTextChanged.connect(self.filter_notes)
        search_layout.addWidget(self.tag_filter)
        left_layout.addLayout(search_layout)
        self.notes_table = QTableWidget()
        self.notes_table.setColumnCount(4)
        self.notes_table.setHorizontalHeaderLabels(["Başlık", "Hatırlatma", "Etiketler", "İçerik"])
        self.notes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.notes_table.verticalHeader().setVisible(False)
        self.notes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.notes_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.notes_table.cellClicked.connect(self.show_note_details)
        left_layout.addWidget(self.notes_table)
        self.note_details = QTextEdit()
        self.note_details.setReadOnly(True)
        left_layout.addWidget(self.note_details)
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Not Ekle", clicked=self.add_note)
        self.edit_button = QPushButton("Düzenle", clicked=self.edit_note)
        self.delete_button = QPushButton("Sil", clicked=self.delete_note)
        self.notifications_button = QPushButton("Bildirim Ayarları", clicked=self.show_notification_settings)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.notifications_button)
        left_layout.addLayout(button_layout)
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        self.calendar = CustomCalendarWidget()
        self.calendar.selectionChanged.connect(self.update_calendar_notes)
        right_layout.addWidget(self.calendar)
        bottom_splitter = QSplitter(Qt.Orientation.Vertical)
        self.calendar_notes = QTextEdit()
        self.calendar_notes.setReadOnly(True)
        bottom_splitter.addWidget(self.calendar_notes)
        
        # Ertelenen notlar için yeni widget
        postponed_widget = QWidget()
        postponed_layout = QVBoxLayout(postponed_widget)
        
        # Ertelenen notlar başlığı
        postponed_title = QLabel("Ertelenen Notlar")
        postponed_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        postponed_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        postponed_layout.addWidget(postponed_title)
        
        # Ertelenen notlar tablosu
        self.postponed_notes_table = QTableWidget()
        self.postponed_notes_table.setColumnCount(4)
        self.postponed_notes_table.setHorizontalHeaderLabels(["Başlık", "Hatırlatma", "İçerik", "İşlem"])
        self.postponed_notes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.postponed_notes_table.verticalHeader().setVisible(False)
        postponed_layout.addWidget(self.postponed_notes_table)
        
        bottom_splitter.addWidget(postponed_widget)
        right_layout.addWidget(bottom_splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        main_layout.addWidget(splitter)
        self.update_notes_list()
        self.update_postponed_notes()

    def show_notification_settings(self):
        dialog = NotificationSettingsDialog(self)
        dialog.enable_notifications.setChecked(self.notification_settings.get('enable_notifications', False))
        dialog.notification_sound.setChecked(self.notification_settings.get('notification_sound', False))
        dialog.notification_popup.setChecked(self.notification_settings.get('notification_popup', False))
        if dialog.exec():
            self.notification_settings = dialog.get_settings()
            self.save_notification_settings()

    def load_notification_settings(self):
        try:
            with open(os.path.join("veriler", "notification_settings.json"), "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'enable_notifications': False, 'notification_sound': False, 'notification_popup': False}

    def save_notification_settings(self):
        os.makedirs("veriler", exist_ok=True)
        with open(os.path.join("veriler", "notification_settings.json"), "w") as file:
            json.dump(self.notification_settings, file)

    def load_notes(self):
        try:
            with open(os.path.join("veriler", "notes.json"), "r") as file:
                self.notes = json.load(file)
                for note in self.notes:
                    if 'created_at' not in note:
                        note['created_at'] = datetime.now().strftime("%Y-%m-%d")
                    if 'tags' not in note:
                        note['tags'] = []
                    if 'id' not in note:
                        note['id'] = datetime.now().strftime("%Y%m%d%H%M%S")
        except (FileNotFoundError, json.JSONDecodeError):
            self.notes = []

    def save_notes(self):
        os.makedirs("veriler", exist_ok=True)
        with open(os.path.join("veriler", "notes.json"), "w") as file:
            json.dump(self.notes, file, indent=2)

    def update_notes_list(self):
        self.notes_table.setRowCount(0)
        all_tags = set()
        for note in self.notes:
            row = self.notes_table.rowCount()
            self.notes_table.insertRow(row)
            self.notes_table.setItem(row, 0, QTableWidgetItem(note['title']))
            self.notes_table.setItem(row, 1, QTableWidgetItem(note['reminder']))
            self.notes_table.setItem(row, 2, QTableWidgetItem(', '.join(note['tags'])))
            self.notes_table.setItem(row, 3, QTableWidgetItem(note['content'][:50] + "..."))
            all_tags.update(note['tags'])
        self.tag_filter.clear()
        self.tag_filter.addItem("Tüm Etiketler")
        self.tag_filter.addItems(sorted(all_tags))
        self.calendar.setNotes(self.notes)
        self.update_calendar_notes()

    def show_note_details(self, row, column):
        note = self.notes[row]
        details = f"<h2>{note['title']}</h2>"
        details += f"<p><strong>İçerik:</strong> {note['content']}</p>"
        details += f"<p><strong>Hatırlatma:</strong> {note['reminder']}</p>"
        details += f"<p><strong>Etiketler:</strong> {', '.join(note['tags'])}</p>"
        details += f"<p><strong>Eklenme Tarihi:</strong> {note['created_at']}</p>"
        self.note_details.setHtml(details)

    def add_note(self):
        dialog = NoteDialog(self)
        if dialog.exec():
            new_note = dialog.get_note_data()
            self.notes.append(new_note)
            self.save_notes()
            self.update_notes_list()

    def edit_note(self):
        current_row = self.notes_table.currentRow()
        if current_row >= 0:
            note = self.notes[current_row]
            dialog = NoteDialog(self, note)
            if dialog.exec():
                updated_note = dialog.get_note_data()
                self.notes[current_row] = updated_note
                self.save_notes()
                self.update_notes_list()
                self.show_note_details(current_row, 0)

    def delete_note(self):
        current_row = self.notes_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, 'Notu Sil', 'Bu notu silmek istediğinizden emin misiniz?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                del self.notes[current_row]
                self.save_notes()
                self.update_notes_list()
                self.note_details.clear()

    def update_calendar_notes(self):
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        notes_for_day = [note for note in self.notes if note['reminder'].startswith(selected_date)]
        if notes_for_day:
            notes_text = "<h3>Bu tarih için notlar:</h3>"
            for note in notes_for_day:
                notes_text += f"<h4>{note['title']}</h4>"
                notes_text += f"<p>{note['content'][:100]}...</p>"
                notes_text += f"<p><strong>Etiketler:</strong> {', '.join(note['tags'])}</p>"
                notes_text += "<hr>"
        else:
            notes_text = "<p>Bu tarih için not bulunmamaktadır.</p>"
        self.calendar_notes.setHtml(notes_text)

    def filter_notes(self):
        search_text = self.search_input.text().lower()
        selected_tag = self.tag_filter.currentText()
        for row in range(self.notes_table.rowCount()):
            note = self.notes[row]
            title_match = search_text in note['title'].lower()
            content_match = search_text in note['content'].lower()
            tag_match = selected_tag == "Tüm Etiketler" or selected_tag in note['tags']
            self.notes_table.setRowHidden(row, not ((title_match or content_match) and tag_match))

    def update_postponed_notes(self):
        self.postponed_notes_table.setRowCount(0)
        postponed_notes = [note for note in self.notes if note.get('postponed', False)]
        for note in postponed_notes:
            row = self.postponed_notes_table.rowCount()
            self.postponed_notes_table.insertRow(row)
            self.postponed_notes_table.setItem(row, 0, QTableWidgetItem(note['title']))
            self.postponed_notes_table.setItem(row, 1, QTableWidgetItem(note['reminder']))
            self.postponed_notes_table.setItem(row, 2, QTableWidgetItem(note['content'][:50] + "..."))
            cancel_button = QPushButton("İptal Et")
            cancel_button.clicked.connect(lambda _, n=note: self.cancel_postpone(n))
            self.postponed_notes_table.setCellWidget(row, 3, cancel_button)

    def cancel_postpone(self, note):
        note['postponed'] = False
        self.save_notes()
        self.update_notes_list()
        self.update_postponed_notes()

    def show_notification(self, title, content, note_id):
        if self.notification_settings.get('enable_notifications', False):
            notification = QMessageBox(self)
            notification.setWindowTitle("Hatırlatma")
            notification.setText(f"{title}\n\n{content}")
            notification.setIcon(QMessageBox.Icon.Information)
            notification.addButton("Tamam", QMessageBox.ButtonRole.AcceptRole)
            erteleme_button = notification.addButton("Ertele", QMessageBox.ButtonRole.ActionRole)
            result = notification.exec()
            if notification.clickedButton() == erteleme_button:
                self.show_postpone_options(note_id)

    def show_postpone_options(self, note_id):
        options = ["1 saat sonra", "2 saat sonra", "1 gün sonra", "1 hafta sonra"]
        choice, ok = QInputDialog.getItem(self, "Erteleme Seçenekleri", "Ne zaman hatırlatılsın?", options, 0, False)
        if ok:
            if choice == "1 saat sonra":
                self.postpone_note(note_id, hours=1)
            elif choice == "2 saat sonra":
                self.postpone_note(note_id, hours=2)
            elif choice == "1 gün sonra":
                self.postpone_note(note_id, days=1)
            elif choice == "1 hafta sonra":
                self.postpone_note(note_id, days=7)

    def postpone_note(self, note_id, hours=0, days=0):
        for note in self.notes:
            if note['id'] == note_id:
                new_reminder = datetime.strptime(note['reminder'], "%Y-%m-%d %H:%M") + timedelta(hours=hours, days=days)
                note['reminder'] = new_reminder.strftime("%Y-%m-%d %H:%M")
                note['notified'] = False
                note['postponed'] = True
                self.save_notes()
                self.update_notes_list()
                self.update_postponed_notes()
                break

class NoteDialog(QDialog):
    def __init__(self, parent=None, note=None):
        super().__init__(parent)
        self.setWindowTitle("Not Ekle/Düzenle")
        self.setFixedSize(400, 400)
        layout = QFormLayout(self)

        self.title_input = QLineEdit(note['title'] if note else "")
        self.content_input = QTextEdit(note['content'] if note else "")
        self.reminder_input = QDateTimeEdit(QDateTime.currentDateTime())
        if note and note.get('reminder'):
            self.reminder_input.setDateTime(QDateTime.fromString(note['reminder'], "yyyy-MM-dd HH:mm"))
        self.tag_input = QLineEdit(', '.join(note['tags']) if note and 'tags' in note else "")

        layout.addRow("Başlık:", self.title_input)
        layout.addRow("İçerik:", self.content_input)
        layout.addRow("Hatırlatma:", self.reminder_input)
        layout.addRow("Etiketler (virgülle ayırın):", self.tag_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.note = note

    def get_note_data(self):
        return {
            'id': self.note['id'] if self.note else datetime.now().strftime("%Y%m%d%H%M%S"),
            'title': self.title_input.text(),
            'content': self.content_input.toPlainText(),
            'reminder': self.reminder_input.dateTime().toString("yyyy-MM-dd HH:mm"),
            'created_at': self.note['created_at'] if self.note else datetime.now().strftime("%Y-%m-%d"),
            'tags': [tag.strip() for tag in self.tag_input.text().split(',') if tag.strip()]
        }

class ShortcutDialog(QDialog):
    def __init__(self, parent=None, shortcut=None):
        super().__init__(parent)
        self.setWindowTitle("Kısayol Ekle/Düzenle")
        self.setFixedSize(400, 250)
        layout = QVBoxLayout(self)

        self.key_input = QLineEdit(shortcut['key'] if shortcut else "")
        self.key_input.setPlaceholderText("Kısayol tuşu (örn: F8)")
        layout.addWidget(QLabel("Kısayol Tuşu:"))
        layout.addWidget(self.key_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Metin", "Program"])
        layout.addWidget(QLabel("Kısayol Türü:"))
        layout.addWidget(self.type_combo)

        self.content_input = QTextEdit(shortcut['content'] if shortcut and shortcut['type'] == 'text' else "")
        self.content_input.setPlaceholderText("Metin içeriği")
        self.content_label = QLabel("Metin İçeriği:")
        layout.addWidget(self.content_label)
        layout.addWidget(self.content_input)

        self.program_path_input = QLineEdit(shortcut['content'] if shortcut and shortcut['type'] == 'program' else "")
        self.program_path_input.setPlaceholderText("Program yolu")
        self.program_path_label = QLabel("Program Yolu:")
        layout.addWidget(self.program_path_label)
        layout.addWidget(self.program_path_input)

        self.browse_button = QPushButton("Gözat", clicked=self.browse_program)
        layout.addWidget(self.browse_button)

        self.type_combo.currentTextChanged.connect(self.update_input_visibility)
        
        if shortcut:
            self.type_combo.setCurrentText("Metin" if shortcut['type'] == 'text' else "Program")
        
        self.update_input_visibility()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_input_visibility(self):
        is_text = self.type_combo.currentText() == "Metin"
        self.content_label.setVisible(is_text)
        self.content_input.setVisible(is_text)
        self.program_path_label.setVisible(not is_text)
        self.program_path_input.setVisible(not is_text)
        self.browse_button.setVisible(not is_text)

    def browse_program(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Program Seç", "", "Executable files (*.exe)")
        if file_path:
            self.program_path_input.setText(file_path)

    def get_shortcut_data(self):
        return {
            'key': self.key_input.text(),
            'type': 'text' if self.type_combo.currentText() == "Metin" else 'program',
            'content': self.content_input.toPlainText() if self.type_combo.currentText() == "Metin" else self.program_path_input.text()
        }

class ShortcutsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shortcuts = {}
        self.load_shortcuts()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(4)
        self.shortcuts_table.setHorizontalHeaderLabels(["Kısayol", "Tür", "İçerik", ""])
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.shortcuts_table)
        add_button = QPushButton("Yeni Kısayol Ekle", clicked=self.add_shortcut)
        layout.addWidget(add_button)
        self.update_shortcuts_table()

    def load_shortcuts(self):
        try:
            with open(os.path.join("veriler", "shortcuts.json"), "r") as file:
                old_shortcuts = json.load(file)
                self.shortcuts = {}
                for key, value in old_shortcuts.items():
                    if isinstance(value, str):
                        # Eski format
                        self.shortcuts[key] = {"type": "text", "content": value}
                    elif isinstance(value, dict):
                        # Yeni format
                        self.shortcuts[key] = value
                    else:
                        print(f"Geçersiz kısayol formatı: {key}: {value}")
        except (FileNotFoundError, json.JSONDecodeError):
            self.shortcuts = {"F8": {"type": "text", "content": "Örnek Kısayol: Kısayol tuşuna bastığınızda burada yazılı metni editöre veya metin girişi alanına yazacaktır."}}
        
        # Tüm kısayolları yeni formata dönüştürdükten sonra kaydet
            self.save_shortcuts()

    def save_shortcuts(self):
        os.makedirs("veriler", exist_ok=True)
        with open(os.path.join("veriler", "shortcuts.json"), "w") as file:
            json.dump(self.shortcuts, file, indent=2)

    def update_shortcuts_table(self):
        self.shortcuts_table.setRowCount(0)
        for key, value in self.shortcuts.items():
            row = self.shortcuts_table.rowCount()
            self.shortcuts_table.insertRow(row)
            self.shortcuts_table.setItem(row, 0, QTableWidgetItem(key))
            self.shortcuts_table.setItem(row, 1, QTableWidgetItem("Metin" if value['type'] == 'text' else "Program"))
            self.shortcuts_table.setItem(row, 2, QTableWidgetItem(value['content']))
            delete_button = QPushButton("Sil")
            delete_button.clicked.connect(lambda _, k=key: self.delete_shortcut(k))
            self.shortcuts_table.setCellWidget(row, 3, delete_button)

    def add_shortcut(self):
        dialog = ShortcutDialog(self)
        if dialog.exec():
            shortcut_data = dialog.get_shortcut_data()
            self.shortcuts[shortcut_data['key']] = {
                'type': shortcut_data['type'],
                'content': shortcut_data['content']
            }
            self.save_shortcuts()
            self.update_shortcuts_table()
            keyboard.add_hotkey(shortcut_data['key'], lambda: self.handle_shortcut(shortcut_data['key']))

    def delete_shortcut(self, key):
        del self.shortcuts[key]
        self.save_shortcuts()
        self.update_shortcuts_table()
        keyboard.remove_hotkey(key)

    def handle_shortcut(self, key):
        shortcut = self.shortcuts.get(key)
        if shortcut:
            if isinstance(shortcut, str):
                # Eski format için geriye dönük uyumluluk
                self.paste_text(shortcut)
            elif isinstance(shortcut, dict):
                if shortcut['type'] == 'text':
                    self.paste_text(shortcut['content'])
                else:
                    self.run_program(shortcut['content'])

    def paste_text(self, text):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        pyautogui.hotkey("ctrl", "v")

    def run_program(self, program_path):
        try:
            subprocess.Popen(program_path)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Program çalıştırılırken bir hata oluştu: {e}")



class EsasNoLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.textChanged.connect(self.on_text_changed)
    
    def on_text_changed(self, text):
        if len(text) == 4 and text.isdigit() and '/' not in text:
            self.setText(f"{text}/")
            self.setCursorPosition(5)

class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd.MM.yyyy")
        self.setDate(QDate.currentDate())

class TebligatTakipWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tebligatlar = []
        self.load_tebligatlar()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Arama alanı
        self.search_input = QLineEdit(placeholderText="İlam No ile ara...")
        self.search_input.textChanged.connect(self.search_tebligatlar)
        layout.addWidget(self.search_input)
        
        form_layout = QFormLayout()
        self.ilam_no_input = EsasNoLineEdit()
        self.teblig_tarihi_input = CustomDateEdit()
        self.tur_input = QComboBox()
        self.tur_input.addItems(["Ödeme Emri Hesabı", "Davetname Hesabı"])
        
        for label, widget in [("İlam No:", self.ilam_no_input), 
                              ("Tebliğ Tarihi:", self.teblig_tarihi_input), 
                              ("Tür:", self.tur_input)]:
            form_layout.addRow(label, widget)
        
        ekle_button = QPushButton("Ekle", clicked=self.ekle_tebligat)
        form_layout.addRow("", ekle_button)
        layout.addLayout(form_layout)
        
        tables_layout = QHBoxLayout()
        
        # Ödeme Emirleri için
        odeme_layout = QVBoxLayout()
        odeme_layout.addWidget(QLabel("Ödeme Emirleri"))
        self.odeme_emri_table = self.create_table()
        odeme_layout.addWidget(self.odeme_emri_table)
        tables_layout.addLayout(odeme_layout)
        
        # Davetnameler için
        davetname_layout = QVBoxLayout()
        davetname_layout.addWidget(QLabel("Davetnameler"))
        self.davetname_table = self.create_table()
        davetname_layout.addWidget(self.davetname_table)
        tables_layout.addLayout(davetname_layout)
        
        layout.addLayout(tables_layout)
        
        self.update_tebligatlar_list()

    def create_table(self):
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["İlam No", "Tebliğ Tarihi", "Eklenen Gün", "İşlem Tarihi", ""])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def load_tebligatlar(self):
        try:
            with open(os.path.join("veriler", "tebligatlar.json"), "r") as file:
                self.tebligatlar = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.tebligatlar = []

    def save_tebligatlar(self):
        os.makedirs("veriler", exist_ok=True)
        with open(os.path.join("veriler", "tebligatlar.json"), "w") as file:
            json.dump(self.tebligatlar, file, indent=2)

    def ekle_tebligat(self):
        ilam_no = self.ilam_no_input.text()
        teblig_tarihi = self.teblig_tarihi_input.date().toString("dd.MM.yyyy")
        tur = self.tur_input.currentText()
        
        if not ilam_no:
            QMessageBox.warning(self, "Uyarı", "İlam No boş olamaz.")
            return
        
        eklenen_gun = 31 if tur == "Ödeme Emri Hesabı" else 11
        islem_tarihi = (datetime.strptime(teblig_tarihi, "%d.%m.%Y") + timedelta(days=eklenen_gun)).strftime("%d.%m.%Y")
        
        yeni_tebligat = {
            'ilamNo': ilam_no,
            'tebligTarihi': teblig_tarihi,
            'tur': tur,
            'eklenenGun': eklenen_gun,
            'islemTarihi': islem_tarihi
        }
        
        self.tebligatlar.append(yeni_tebligat)
        self.save_tebligatlar()
        self.update_tebligatlar_list()
        self.temizle_form()

    def temizle_form(self):
        self.ilam_no_input.clear()
        self.teblig_tarihi_input.setDate(QDate.currentDate())
        self.tur_input.setCurrentIndex(0)

    def update_tebligatlar_list(self):
        self.odeme_emri_table.setRowCount(0)
        self.davetname_table.setRowCount(0)
        
        bugun = datetime.now().date()
        gruplar = {
            "Ödeme Emirleri": {"Süresi Dolanlar": [], "Süresi Yaklaşanlar": [], "Normal": []},
            "Davetnameler": {"Süresi Dolanlar": [], "Süresi Yaklaşanlar": [], "Normal": []}
        }
        
        for tebligat in self.tebligatlar:
            islem_tarihi = datetime.strptime(tebligat['islemTarihi'], "%d.%m.%Y").date()
            kalan_gun = (islem_tarihi - bugun).days
            
            if kalan_gun < 0:
                durum = "Süresi Dolanlar"
            elif kalan_gun <= 5:
                durum = "Süresi Yaklaşanlar"
            else:
                durum = "Normal"
            
            tür = "Ödeme Emirleri" if tebligat['tur'] == "Ödeme Emri Hesabı" else "Davetnameler"
            gruplar[tür][durum].append(tebligat)
        
        for tür, table in [("Ödeme Emirleri", self.odeme_emri_table), ("Davetnameler", self.davetname_table)]:
            for durum in ["Süresi Dolanlar", "Süresi Yaklaşanlar", "Normal"]:
                if gruplar[tür][durum]:
                    self.add_group_header(table, durum)
                    for tebligat in sorted(gruplar[tür][durum], key=lambda x: datetime.strptime(x['islemTarihi'], "%d.%m.%Y")):
                        self.add_tebligat_row(table, tebligat, durum)

    def add_group_header(self, table, header):
        row = table.rowCount()
        table.insertRow(row)
        item = QTableWidgetItem(header)
        item.setBackground(QColor(200, 200, 200))
        table.setItem(row, 0, item)
        table.setSpan(row, 0, 1, 5)

    def add_tebligat_row(self, table, tebligat, durum):
        row = table.rowCount()
        table.insertRow(row)
        
        for col, key in enumerate(["ilamNo", "tebligTarihi", "eklenenGun", "islemTarihi"]):
            item = QTableWidgetItem(str(tebligat[key]))
            if durum == "Süresi Dolanlar":
                item.setBackground(QColor(255, 200, 200))  # Kırmızı
            elif durum == "Süresi Yaklaşanlar":
                item.setBackground(QColor(255, 255, 200))  # Sarı
            table.setItem(row, col, item)
        
        delete_button = QPushButton("Sil")
        delete_button.clicked.connect(lambda _, t=tebligat: self.delete_tebligat(t))
        table.setCellWidget(row, 4, delete_button)

    def delete_tebligat(self, tebligat):
        self.tebligatlar.remove(tebligat)
        self.save_tebligatlar()
        self.update_tebligatlar_list()

    def search_tebligatlar(self):
        search_text = self.search_input.text().lower()
        for table in [self.odeme_emri_table, self.davetname_table]:
            for row in range(table.rowCount()):
                ilam_no_item = table.item(row, 0)
                if ilam_no_item:
                    ilam_no = ilam_no_item.text().lower()
                    if search_text in ilam_no:
                        table.setRowHidden(row, False)
                    else:
                        table.setRowHidden(row, True)
                else:
                    table.setRowHidden(row, False)  # Grup başlıklarını göster

class PhoneBookWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.contacts = []
        self.load_contacts()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.search_input = QLineEdit(placeholderText="Ara...")
        self.search_input.textChanged.connect(self.filter_contacts)
        layout.addWidget(self.search_input)
        
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(4)
        self.contacts_table.setHorizontalHeaderLabels(["İsim", "Kategori", "Telefon", "E-posta"])
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.contacts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.contacts_table.itemClicked.connect(self.show_contact_details)
        layout.addWidget(self.contacts_table)
        
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Ekle", clicked=self.add_contact)
        self.edit_button = QPushButton("Düzenle", clicked=self.edit_contact)
        self.delete_button = QPushButton("Sil", clicked=self.delete_contact)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        
        self.contact_details = QTextEdit(readOnly=True)
        layout.addWidget(self.contact_details)
        
        self.update_contacts_list()

    def load_contacts(self):
        try:
            with open(os.path.join("veriler", "contacts.json"), "r") as file:
                self.contacts = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.contacts = []

    def save_contacts(self):
        os.makedirs("veriler", exist_ok=True)
        with open(os.path.join("veriler", "contacts.json"), "w") as file:
            json.dump(self.contacts, file, indent=2)

    def update_contacts_list(self):
        self.contacts_table.setRowCount(0)
        for contact in self.contacts:
            row = self.contacts_table.rowCount()
            self.contacts_table.insertRow(row)
            self.contacts_table.setItem(row, 0, QTableWidgetItem(contact['name']))
            self.contacts_table.setItem(row, 1, QTableWidgetItem(contact['category']))
            self.contacts_table.setItem(row, 2, QTableWidgetItem(contact['phones'][0] if contact['phones'] else ""))
            self.contacts_table.setItem(row, 3, QTableWidgetItem(contact['emails'][0] if contact['emails'] else ""))

    def add_contact(self):
        dialog = ContactDialog(self)
        if dialog.exec():
            new_contact = dialog.get_contact_data()
            self.contacts.append(new_contact)
            self.save_contacts()
            self.update_contacts_list()

    def edit_contact(self):
        current_row = self.contacts_table.currentRow()

    def edit_contact(self):
        current_row = self.contacts_table.currentRow()
        if current_row >= 0:
            contact = self.contacts[current_row]
            dialog = ContactDialog(self, contact)
            if dialog.exec():
                updated_contact = dialog.get_contact_data()
                self.contacts[current_row] = updated_contact
                self.save_contacts()
                self.update_contacts_list()
                self.show_contact_details()

    def delete_contact(self):
        current_row = self.contacts_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, 'Kişiyi Sil', 'Bu kişiyi silmek istediğinizden emin misiniz?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                del self.contacts[current_row]
                self.save_contacts()
                self.update_contacts_list()
                self.contact_details.clear()

    def show_contact_details(self):
        current_row = self.contacts_table.currentRow()
        if current_row >= 0:
            contact = self.contacts[current_row]
            details = f"İsim: {contact['name']}\n"
            details += f"Kategori: {contact['category']}\n\n"
            details += "Telefonlar:\n" + "\n".join(contact['phones']) + "\n\n"
            details += "E-postalar:\n" + "\n".join(contact['emails'])
            self.contact_details.setText(details)

    def filter_contacts(self):
        search_text = self.search_input.text().lower()
        for row in range(self.contacts_table.rowCount()):
            match = False
            for col in range(self.contacts_table.columnCount()):
                item = self.contacts_table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.contacts_table.setRowHidden(row, not match)

class ContactDialog(QDialog):
    def __init__(self, parent=None, contact=None):
        super().__init__(parent)
        self.setWindowTitle("Kişi Ekle/Düzenle")
        self.setFixedSize(400, 300)
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit(contact['name'] if contact else "")
        self.category_input = QComboBox()
        self.category_input.addItems(["İş", "Aile", "Arkadaşlar", "Diğer"])
        if contact:
            self.category_input.setCurrentText(contact['category'])
        
        self.phone_inputs = []
        self.email_inputs = []
        
        layout.addRow("İsim:", self.name_input)
        layout.addRow("Kategori:", self.category_input)
        
        for i in range(3):
            phone_input = QLineEdit()
            email_input = QLineEdit()
            if contact and i < len(contact['phones']):
                phone_input.setText(contact['phones'][i])
            if contact and i < len(contact['emails']):
                email_input.setText(contact['emails'][i])
            layout.addRow(f"Telefon {i+1}:", phone_input)
            layout.addRow(f"E-posta {i+1}:", email_input)
            self.phone_inputs.append(phone_input)
            self.email_inputs.append(email_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_contact_data(self):
        return {
            'name': self.name_input.text(),
            'category': self.category_input.currentText(),
            'phones': [phone.text() for phone in self.phone_inputs if phone.text()],
            'emails': [email.text() for email in self.email_inputs if email.text()]
        }


class DosyaTakipSistemi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A.K.K - Not - Oto Tuş Sistemi V1")
        self.setGeometry(100, 100, 1800, 700)
        self.dosyalar = []
        self.json_file = os.path.join("veriler", "dosyalar.json")
        self.gecmis_file = os.path.join("veriler", "gecmis.json")
        self.load_data()
        self.load_gecmis()
        self.init_ui()
        self.create_menu()
        self.set_styles()
        self.guncelle_tablo()
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")))
        self.calendar.paintCell = self.paintCell
        for key in self.shortcuts_widget.shortcuts.keys():
            keyboard.add_hotkey(key, lambda k=key: self.shortcuts_widget.handle_shortcut(k))

        # Tray icon oluşturma
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.windowIcon())
        self.tray_icon.setToolTip("A.K.K Sistemi")
        self.create_tray_menu()
        self.tray_icon.show()
        # Tray icon'a çift tıklama olayını bağlama
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_program()

    def show_program(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("A.K.K Sistemi", "Program halen simge modunda çalışıyor.", QSystemTrayIcon.MessageIcon.Information, 2000)

    def create_tray_menu(self):
        menu = QMenu()
        open_action = menu.addAction("Aç")
        open_action.triggered.connect(self.show)
        quit_action = menu.addAction("Çıkış")
        quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_icon.setContextMenu(menu)

    def create_menu(self):
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu('Yardım')
        help_menu.addAction('Hakkında', lambda: AboutDialog(self).exec())

    def init_ui(self):
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)
        
        # Dosya Takip sekmesi
        dosya_takip_widget = QWidget()
        dosya_takip_layout = QVBoxLayout(dosya_takip_widget)
        self.search_input = QLineEdit(placeholderText="İlam No ile ara...")
        self.search_input.textChanged.connect(self.search_table)
        dosya_takip_layout.addWidget(self.search_input)
        
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        form_group = QGroupBox("Dosya Bilgileri")
        form_layout = QFormLayout()
        self.esas_no_input = EsasNoLineEdit()
        self.rapor_baslangic_tarihi_input = CustomDateEdit()
        self.son_rapor_tarihi_input = CustomDateEdit()
        self.rapor_yil_input = QSpinBox(minimum=5, maximum=100)
        self.rapor_ay_input = QSpinBox(minimum=3, maximum=12)
        self.notlar_input = QLineEdit()
        
        yil_button_layout = QHBoxLayout()
        yil_button_layout.addWidget(self.rapor_yil_input)
        for yil in [5, 10]:
            btn = QPushButton(str(yil))
            btn.clicked.connect(lambda _, y=yil: self.rapor_yil_input.setValue(y))
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn.setMinimumWidth(30)
            yil_button_layout.addWidget(btn)
        
        ay_button_layout = QHBoxLayout()
        ay_button_layout.addWidget(self.rapor_ay_input)
        for ay in [3, 6]:
            btn = QPushButton(str(ay))
            btn.clicked.connect(lambda _, a=ay: self.rapor_ay_input.setValue(a))
            btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            btn.setMaximumWidth(btn.sizeHint().width()//2)
            ay_button_layout.addWidget(btn)
        
        for label, widget in [
            ("İlam No:", self.esas_no_input),
            ("Rapor Başlangıç Tarihi:", self.rapor_baslangic_tarihi_input),
            ("Son Rapor Tarihi:", self.son_rapor_tarihi_input),
            ("Rapor Yıl:", yil_button_layout),
            ("Rapor Ay:", ay_button_layout),
            ("Notlar:", self.notlar_input)
        ]:
            form_layout.addRow(label, widget)
        
        button_layout = QHBoxLayout()
        for button_text, func in [("Ekle", self.ekle_dosya), ("Seçili Dosyayı Sil", self.sil_dosya), ("Geçmişi Görüntüle", self.show_gecmis)]:
            button = QPushButton(button_text, clicked=func)
            button_layout.addWidget(button)
        form_layout.addRow("", button_layout)
        
        form_group.setLayout(form_layout)
        left_layout.addWidget(form_group)
        
        right_layout = QVBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("QCalendarWidget{border:none;}")
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setGridVisible(False)
        self.calendar.selectionChanged.connect(self.update_calendar_details)
        right_layout.addWidget(self.calendar)
        
        self.calendar_details = QTableWidget()
        self.calendar_details.setColumnCount(2)
        self.calendar_details.setHorizontalHeaderLabels(["Özellik", "Değer"])
        self.calendar_details.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.calendar_details.verticalHeader().setVisible(False)
        self.calendar_details.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 5px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
            }
        """)
        right_layout.addWidget(self.calendar_details)
        
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        
        dosya_takip_layout.addLayout(main_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels(["İlam No", "Son Rapor Tarihi", "Rapor Yıl", "Rapor Ay", "Kalan Gün", "Yeniden Yazı Tarihi", "Geciken Süre", "Durum", "Notlar", "Rapor Bşlm. Tarihi", "Rapor Bitiş Tarihi"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemChanged.connect(self.on_cell_changed)
        dosya_takip_layout.addWidget(self.table)
        
        self.central_widget.addTab(dosya_takip_widget, "A.K.K")
        
        # Diğer sekmeler
        self.tebligat_takip_widget = TebligatTakipWidget(self)
        self.central_widget.addTab(self.tebligat_takip_widget, "Tebligat Takibi")
        
        self.notes_widget = NotesWidget(self)
        self.central_widget.addTab(self.notes_widget, "Notlar")
        
        self.shortcuts_widget = ShortcutsWidget(self)
        self.central_widget.addTab(self.shortcuts_widget, "Kısayollarım")
        
        self.phone_book_widget = PhoneBookWidget(self)
        self.central_widget.addTab(self.phone_book_widget, "Telefon Rehberi")

    def set_styles(self):
        self.setStyleSheet("""
            QMainWindow{background-color:#f0f0f0;}
            QTabWidget::pane{border:1px solid #d7d7d7;background-color:#f5f5f5;}
            QTabBar::tab{background-color:#e0e0e0;padding:8px 20px;margin-right:2px;}
            QTabBar::tab:selected{background-color:#f5f5f5;border-bottom:2px solid #4a90e2;}
            QGroupBox{font-size:16px;font-weight:bold;border:2px solid #d7d7d7;border-radius:6px;margin-top:10px;}
            QLabel{font-size:14px;color:#333;}
            QLineEdit,QDateEdit,QSpinBox,QDateTimeEdit{font-size:14px;padding:5px;border:1px solid #ccc;border-radius:4px;}
            QPushButton{font-size:14px;background-color:#4a90e2;color:white;border:none;padding:8px 15px;border-radius:4px;}
            QPushButton:hover{background-color:#357ae8;}
            QTableWidget{font-size:14px;border:1px solid #d7d7d7;}
            QHeaderView::section{background-color:#e0e0e0;font-size:14px;font-weight:bold;padding:5px;border:none;}
            QListWidget{font-size:14px;border:1px solid #d7d7d7;border-radius:4px;}
            QTextEdit{font-size:14px;border:1px solid #d7d7d7;border-radius:4px;}
        """)

    def load_data(self):
        try:
            os.makedirs("veriler", exist_ok=True)
            with open(self.json_file, 'r') as file:
                self.dosyalar = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.dosyalar = []

    def save_data(self):
        try:
            os.makedirs("veriler", exist_ok=True)
            with open(self.json_file, 'w') as file:
                json.dump(self.dosyalar, file, indent=2)
        except Exception as e:
            print(f"Veri kaydedilirken hata oluştu: {e}")
            QMessageBox.warning(self, "Hata", "Veriler kaydedilirken bir hata oluştu.")

    def load_gecmis(self):
        try:
            os.makedirs("veriler", exist_ok=True)
            with open(self.gecmis_file, 'r') as file:
                self.gecmis = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.gecmis = {}

    def save_gecmis(self):
        try:
            os.makedirs("veriler", exist_ok=True)
            with open(self.gecmis_file, 'w') as file:
                json.dump(self.gecmis, file, indent=2)
        except Exception as e:
            print(f"Geçmiş kaydedilirken hata oluştu: {e}")
            QMessageBox.warning(self, "Hata", "Geçmiş kaydedilirken bir hata oluştu.")

    def ekle_dosya(self):
        esas_no = self.esas_no_input.text()
        if not esas_no:
            QMessageBox.warning(self, "Uyarı", "Esas No boş olamaz.")
            return
        yeni_dosya = {
            'esasNo': esas_no,
            'raporBaslangicTarihi': self.rapor_baslangic_tarihi_input.date().toString("dd.MM.yyyy"),
            'sonRaporTarihi': self.son_rapor_tarihi_input.date().toString("dd.MM.yyyy"),
            'raporYil': self.rapor_yil_input.value(),
            'raporAy': self.rapor_ay_input.value(),
            'notlar': self.notlar_input.text()
        }
        self.dosyalar.append(yeni_dosya)
        self.add_to_gecmis(esas_no, "Yeni dosya eklendi", yeni_dosya)
        self.save_data()
        self.guncelle_tablo()
        self.temizle_form()
        self.calendar.updateCells()

    def sil_dosya(self):
        secili_satirlar = self.table.selectedItems()
        if not secili_satirlar:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek için bir dosya seçin.")
            return
        secili_satir = secili_satirlar[0].row()
        esas_no = self.table.item(secili_satir, 0).text()
        cevap = QMessageBox.question(self, "Dosya Silme", f"{esas_no} numaralı dosyayı silmek istediğinizden emin misiniz?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if cevap == QMessageBox.StandardButton.Yes:
            silinen_dosya = next((dosya for dosya in self.dosyalar if dosya['esasNo'] == esas_no), None)
            if silinen_dosya:
                self.add_to_gecmis(esas_no, "Dosya silindi", silinen_dosya)
            self.dosyalar = [dosya for dosya in self.dosyalar if dosya['esasNo'] != esas_no]
            self.save_data()
            self.guncelle_tablo()
            self.calendar.updateCells()

    def guncelle_tablo(self):
        self.table.itemChanged.disconnect(self.on_cell_changed)
        self.table.setRowCount(0)
        bugun = date.today()
        dosya_gruplari = {'Süresi Dolanlar': [], 'Süresi Yaklaşanlar': [], 'Normal Dosyalar': []}
        for dosya in self.dosyalar:
            try:
                rapor_baslangic_tarihi = datetime.strptime(dosya['raporBaslangicTarihi'], "%d.%m.%Y").date()
                son_rapor_tarihi = datetime.strptime(dosya['sonRaporTarihi'], "%d.%m.%Y").date()
                yeniden_rapor_tarihi = son_rapor_tarihi + relativedelta(months=dosya['raporAy'])
                rapor_bitis_tarihi = rapor_baslangic_tarihi + relativedelta(years=dosya['raporYil'])
                kalan_gun = (yeniden_rapor_tarihi - bugun).days
                geciken_sure = max(0, (bugun - yeniden_rapor_tarihi).days)
                dosya.update({
                    'kalanGun': kalan_gun,
                    'yenidenRaporTarihi': yeniden_rapor_tarihi.strftime("%d.%m.%Y"),
                    'gecikenSure': geciken_sure,
                    'raporBitisTarihi': rapor_bitis_tarihi.strftime("%d.%m.%Y"),
                    'durum': 'Süresi Dolmuş' if geciken_sure > 0 else ('Yaklaşıyor' if kalan_gun <= 10 else 'Normal')
                })
                if geciken_sure > 0:
                    dosya_gruplari['Süresi Dolanlar'].append(dosya)
                elif kalan_gun <= 10:
                    dosya_gruplari['Süresi Yaklaşanlar'].append(dosya)
                else:
                    dosya_gruplari['Normal Dosyalar'].append(dosya)
            except Exception as e:
                print(f"Hata: {e}. Dosya: {dosya}")
                dosya_gruplari['Normal Dosyalar'].append(dosya)
        for baslik, grup in dosya_gruplari.items():
            if grup:
                self.ekle_grup_baslik(baslik)
                [self.ekle_dosya_satiri(dosya) for dosya in sorted(grup, key=lambda x: x.get('kalanGun', 0))]
        self.table.itemChanged.connect(self.on_cell_changed)
        self.calendar.updateCells()

    def ekle_grup_baslik(self, baslik):
        row = self.table.rowCount()
        self.table.insertRow(row)
        baslik_item = EditableTableWidgetItem(baslik, editable=False)
        baslik_item.setBackground(QBrush(QColor(200, 200, 200)))
        self.table.setItem(row, 0, baslik_item)
        self.table.setSpan(row, 0, 1, self.table.columnCount())

    def ekle_dosya_satiri(self, dosya):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, (key, editable) in enumerate([('esasNo', True), ('sonRaporTarihi', True), ('raporYil', True), ('raporAy', True), ('kalanGun', False), ('yenidenRaporTarihi', False), ('gecikenSure', False), ('durum', False), ('notlar', True), ('raporBaslangicTarihi', True), ('raporBitisTarihi', False)]):
            self.table.setItem(row, col, EditableTableWidgetItem(str(dosya.get(key, '')), editable))
        renk = {'Süresi Dolmuş': QColor(255, 200, 200), 'Yaklaşıyor': QColor(255, 255, 200), 'Normal': QColor(255, 255, 255)}.get(dosya.get('durum', 'Normal'), QColor(255, 255, 255))
        [self.table.item(row, col).setBackground(QBrush(renk)) for col in range(self.table.columnCount())]

    def on_cell_changed(self, item):
        if item.column() in [0, 1, 2, 3, 8, 9]:
            row = item.row()
            esas_no = self.table.item(row, 0).text()
            for dosya in self.dosyalar:
                if dosya['esasNo'] == esas_no:
                    try:
                        old_value = dosya.get(self.get_column_key(item.column()), "")
                        new_value = item.text()
                        if old_value != new_value:
                            self.update_dosya(dosya, item.column(), new_value)
                            self.add_to_gecmis(esas_no, f"{self.get_column_name(item.column())} değiştirildi", {self.get_column_name(item.column()): f"{old_value} -> {new_value}"})
                    except ValueError:
                        QMessageBox.warning(self, "Hata", "Geçersiz veri girişi. Lütfen doğru format kullanın.")
                        self.guncelle_tablo()
                        return
            self.save_data()
            self.guncelle_tablo()
            self.calendar.updateCells()

    def get_column_key(self, column):
        return ['esasNo', 'sonRaporTarihi', 'raporYil', 'raporAy', 'kalanGun', 'yenidenRaporTarihi', 'gecikenSure', 'durum', 'notlar', 'raporBaslangicTarihi', 'raporBitisTarihi'][column]

    def get_column_name(self, column):
        return ["İlam No", "Son Rapor Tarihi", "Rapor Yıl", "Rapor Ay", "Kalan Gün", "Yeniden Yazı Tarihi", "Geciken Süre", "Durum", "Notlar", "Rapor Bşlm. Tarihi", "Rapor Bitiş Tarihi"][column]

    def update_dosya(self, dosya, column, new_value):
        key = self.get_column_key(column)
        if key in ['raporYil', 'raporAy']:
            dosya[key] = int(new_value)
        elif key in ['sonRaporTarihi', 'raporBaslangicTarihi']:
            datetime.strptime(new_value, "%d.%m.%Y")
            dosya[key] = new_value
        else:
            dosya[key] = new_value

    def temizle_form(self):
        self.esas_no_input.clear()
        self.rapor_baslangic_tarihi_input.setDate(QDate.currentDate())
        self.son_rapor_tarihi_input.setDate(QDate.currentDate())
        self.rapor_yil_input.setValue(5)
        self.rapor_ay_input.setValue(3)
        self.notlar_input.clear()

    def search_table(self):
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and search_text in item.text().lower():
                self.table.setRowHidden(row, False)
                if search_text == item.text().lower():
                    self.table.scrollToItem(item)
            else:
                self.table.setRowHidden(row, True)

    def add_to_gecmis(self, esas_no, action, details):
        if esas_no not in self.gecmis:
            self.gecmis[esas_no] = []
        self.gecmis[esas_no].append({
            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "islem": action,
            "detaylar": details
        })
        self.save_gecmis()

    def show_gecmis(self):
        secili_satirlar = self.table.selectedItems()
        if not secili_satirlar:
            QMessageBox.warning(self, "Uyarı", "Lütfen geçmişini görüntülemek için bir dosya seçin.")
            return
        secili_satir = secili_satirlar[0].row()
        esas_no = self.table.item(secili_satir, 0).text()
        if esas_no not in self.gecmis:
            QMessageBox.information(self, "Bilgi", f"{esas_no} numaralı dosya için geçmiş kaydı bulunamadı.")
            return
        gecmis_dialog = QDialog(self)
        gecmis_dialog.setWindowTitle(f"{esas_no} Numaralı Dosya Geçmişi")
        gecmis_dialog.setGeometry(200, 200, 600, 400)
        layout = QVBoxLayout()
        gecmis_table = QTableWidget()
        gecmis_table.setColumnCount(3)
        gecmis_table.setHorizontalHeaderLabels(["Tarih", "İşlem", "Detaylar"])
        gecmis_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for kayit in self.gecmis[esas_no]:
            row = gecmis_table.rowCount()
            gecmis_table.insertRow(row)
            gecmis_table.setItem(row, 0, QTableWidgetItem(kayit["tarih"]))
            gecmis_table.setItem(row, 1, QTableWidgetItem(kayit["islem"]))
            gecmis_table.setItem(row, 2, QTableWidgetItem(str(kayit["detaylar"])))
        layout.addWidget(gecmis_table)
        kapat_button = QPushButton("Kapat")
        kapat_button.clicked.connect(gecmis_dialog.close)
        layout.addWidget(kapat_button)
        gecmis_dialog.setLayout(layout)
        gecmis_dialog.exec()

    def update_calendar_details(self):
        selected_date = self.calendar.selectedDate()
        self.calendar_details.setRowCount(0)  # Mevcut satırları temizle
        
        for dosya in self.dosyalar:
            yeniden_yazim_tarihi = QDate.fromString(dosya['yenidenRaporTarihi'], "dd.MM.yyyy")
            if selected_date == yeniden_yazim_tarihi:
                self.add_detail_row("İlam No", dosya['esasNo'])
                self.add_detail_row("Yeniden Yazım Tarihi", dosya['yenidenRaporTarihi'])
                self.add_detail_row("Kalan Gün", str(dosya['kalanGun']))
                self.add_detail_row("Notlar", dosya['notlar'])
                self.add_detail_row("", "--------------------")  # Ayırıcı çizgi
        
        if self.calendar_details.rowCount() == 0:
            self.add_detail_row("Bilgi", "Bu tarihte yeniden yazım yapılacak dosya bulunmamaktadır.")

    def add_detail_row(self, key, value):
        row = self.calendar_details.rowCount()
        self.calendar_details.insertRow(row)
        self.calendar_details.setItem(row, 0, QTableWidgetItem(key))
        self.calendar_details.setItem(row, 1, QTableWidgetItem(value))

        # Ayırıcı çizgi için özel stil
        if key == "":
            for col in range(2):
                item = self.calendar_details.item(row, col)
                item.setBackground(QColor(200, 200, 200))

    def paintCell(self, painter, rect, date):
        QCalendarWidget.paintCell(self.calendar, painter, rect, date)
        painter.save()
        date_str = date.toString("dd.MM.yyyy")
        dosyalar_for_day = [dosya for dosya in self.dosyalar if dosya['yenidenRaporTarihi'] == date_str]
        if dosyalar_for_day:
            kalan_gun = min(int(dosya['kalanGun']) for dosya in dosyalar_for_day)
            if kalan_gun <= 1:
                color = QColor(255, 0, 0, 100)
            elif kalan_gun <= 10:
                color = QColor(255, 255, 0, 100)
            else:
                color = QColor(144, 238, 144, 100)
            painter.fillRect(rect, color)
            painter.setPen(Qt.GlobalColor.black)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(rect.topRight() - QPoint(15, -5), str(len(dosyalar_for_day)))
        painter.restore()

    def show_notification(self, title, content, note_id):
        notification = QMessageBox(self)
        notification.setWindowTitle("Hatırlatma")
        notification.setText(f"{title}\n\n{content}")
        notification.setIcon(QMessageBox.Icon.Information)
        notification.addButton("Tamam", QMessageBox.ButtonRole.AcceptRole)
        erteleme_button = notification.addButton("1 Gün Sonra Hatırlat", QMessageBox.ButtonRole.ActionRole)
        hafta_button = notification.addButton("1 Hafta Sonra Hatırlat", QMessageBox.ButtonRole.ActionRole)
        result = notification.exec()
        if notification.clickedButton() == erteleme_button:
            self.erteleme_hatirlatma(note_id, 1)
        elif notification.clickedButton() == hafta_button:
            self.erteleme_hatirlatma(note_id, 7)

    def erteleme_hatirlatma(self, note_id, days):
        for note in self.notes_widget.notes:
            if note['id'] == note_id:
                new_reminder = datetime.strptime(note['reminder'], "%Y-%m-%d %H:%M") + timedelta(days=days)
                note['reminder'] = new_reminder.strftime("%Y-%m-%d %H:%M")
                note['notified'] = False
                self.notes_widget.save_notes()
                self.notes_widget.update_notes_list()
                break

    def execute_shortcut(self, key):
        shortcut = self.shortcuts_widget.shortcuts.get(key)
        if shortcut:
            if shortcut['type'] == 'text':
                self.paste_text(shortcut['content'])
                QMessageBox.information(self, "Kısayol Uygulandı", f"{key} kısayolu panoya kopyalandı. Ctrl+V ile yapıştırabilirsiniz.")
            else:
                self.shortcuts_widget.run_program(shortcut['content'])
                QMessageBox.information(self, "Program Çalıştırıldı", f"{key} kısayolu ile {shortcut['content']} programı çalıştırıldı.")

    def paste_text(self, text):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        pyautogui.hotkey("ctrl", "v")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F8:
            self.execute_shortcut("F8")
        elif event.key() == Qt.Key.Key_F7:
            self.execute_shortcut("F7")
        super().keyPressEvent(event)

class EsasNoLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.textChanged.connect(self.on_text_changed)
    
    def on_text_changed(self, text):
        if len(text) == 4 and text.isdigit() and '/' not in text:
            self.setText(f"{text}/")
            self.setCursorPosition(5)

class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd.MM.yyyy")
        self.setDate(QDate.currentDate())

class EditableTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, editable=True):
        super().__init__(text)
        self.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | (Qt.ItemFlag.ItemIsEditable if editable else Qt.ItemFlag.NoItemFlags))

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hakkında")
        self.setFixedSize(400, 200)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("A.K.K Sistemi", alignment=Qt.AlignmentFlag.AlignCenter, font=QFont("Arial", 16, QFont.Weight.Bold)))
        layout.addWidget(QLabel("Bu program Adalet Bakanlığı personelleri için\nSaffet Çelik (229301) tarafından hazırlanmıştır.\nKopyalanabilir. Dağıtılabilir.\nMail İletişim: iletisim@saffetcelik.com.tr\n", alignment=Qt.AlignmentFlag.AlignCenter, font=QFont("Arial", 12)))

