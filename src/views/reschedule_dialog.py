from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit, QPushButton, QMessageBox
from PyQt6.QtCore import QDate, Qt
from src.config import ConfigManager

class RescheduleDialog(QDialog):
    def __init__(self, parent=None, remaining_balance: float = 0.0):
        super().__init__(parent)
        self.new_start_date = ""
        self.new_duration = 1
        self.init_ui(remaining_balance)

    def init_ui(self, remaining_balance: float):
        self.setWindowTitle("Reschedule Installment Plan")
        self.resize(350, 220)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title/Header
        lbl_header = QLabel("Reschedule Remaining Balance")
        lbl_header.setObjectName("lbl_section_title")
        layout.addWidget(lbl_header)

        # Show Balance to Reschedule
        formatted_balance = ConfigManager.format_currency(remaining_balance)
        lbl_balance = QLabel(f"Reschedule Balance: {formatted_balance}")
        lbl_balance.setStyleSheet("font-weight: bold; color: #DC2626;")
        layout.addWidget(lbl_balance)

        # New Start Date
        layout.addWidget(QLabel("New Start Date *"))
        self.txt_date = QDateEdit()
        self.txt_date.setCalendarPopup(True)
        # Default to current date or next month
        self.txt_date.setDate(QDate.currentDate().addMonths(1))
        self.txt_date.setFixedHeight(30)
        layout.addWidget(self.txt_date)

        # New Duration (Months)
        layout.addWidget(QLabel("New Duration (Months) *"))
        self.cmb_duration = QComboBox()
        self.cmb_duration.setFixedHeight(30)
        for m in range(1, 25):
            self.cmb_duration.addItem(f"{m} Month(s)", m)
        # Default to 6 months
        self.cmb_duration.setCurrentIndex(5)
        layout.addWidget(self.cmb_duration)

        # Actions Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btn_secondary")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Apply Reschedule")
        self.btn_save.clicked.connect(self.handle_save)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def handle_save(self, *args):
        self.new_start_date = self.txt_date.date().toPyDate().strftime("%Y-%m-%d")
        self.new_duration = self.cmb_duration.currentData()
        self.accept()
