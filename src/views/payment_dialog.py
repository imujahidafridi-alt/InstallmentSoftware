from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDateEdit, QTextEdit, QPushButton, QMessageBox
from PyQt6.QtCore import QDate, Qt

class PaymentDialog(QDialog):
    def __init__(self, parent=None, default_amount: float = 0.0):
        super().__init__(parent)
        self.amount_received = 0.0
        self.payment_date = ""
        self.notes = ""
        self.init_ui(default_amount)

    def init_ui(self, default_amount: float):
        self.setWindowTitle("Record Payment Collection")
        self.resize(350, 280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title/Header
        lbl_header = QLabel("Record Payment Entry")
        lbl_header.setObjectName("lbl_section_title")
        layout.addWidget(lbl_header)

        # Amount Received
        layout.addWidget(QLabel("Amount Received (Rs.) *"))
        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("0.00")
        if default_amount > 0:
            self.txt_amount.setText(f"{default_amount:.2f}")
        layout.addWidget(self.txt_amount)

        # Payment Date
        layout.addWidget(QLabel("Payment Date *"))
        self.txt_date = QDateEdit()
        self.txt_date.setCalendarPopup(True)
        self.txt_date.setDate(QDate.currentDate())
        self.txt_date.setFixedHeight(30)
        layout.addWidget(self.txt_date)

        # Notes
        layout.addWidget(QLabel("Remarks / Transaction Notes"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("e.g. Receipt No, Cash or Bank transfer detail...")
        self.txt_notes.setMaximumHeight(60)
        layout.addWidget(self.txt_notes)

        # Actions Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btn_secondary")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Save Payment")
        self.btn_save.clicked.connect(self.handle_save)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def handle_save(self, *args):
        try:
            amt = float(self.txt_amount.text().strip() or "0")
        except ValueError:
            QMessageBox.warning(self, "Invalid Value", "Please enter a valid numeric payment amount.")
            return

        if amt <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Payment amount must be greater than zero.")
            return

        self.amount_received = amt
        self.payment_date = self.txt_date.date().toPyDate().strftime("%Y-%m-%d")
        self.notes = self.txt_notes.toPlainText().strip()
        
        self.accept()
