from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from src.services.audit_log_service import AuditLogService

class AuditLogWorker(QThread):
    logs_fetched = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, service: AuditLogService, query: str = None, start_date: str = None, end_date: str = None):
        super().__init__()
        self.service = service
        self.query = query
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        try:
            logs = self.service.get_logs(self.query, self.start_date, self.end_date)
            self.logs_fetched.emit(logs)
        except Exception as e:
            self.failed.emit(str(e))

class AuditLogView(QWidget):
    def __init__(self):
        super().__init__()
        self.service = AuditLogService()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Title
        lbl_title = QLabel("Audit & Activity Logs")
        lbl_title.setObjectName("lbl_title")
        main_layout.addWidget(lbl_title)

        # Filter panel top
        filter_panel = QFrame()
        filter_panel.setObjectName("topnav")
        filter_layout = QHBoxLayout(filter_panel)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(10)

        # Search box
        filter_layout.addWidget(QLabel("Search Actions/Users:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter email or action details...")
        self.txt_search.setMinimumWidth(220)
        filter_layout.addWidget(self.txt_search)

        # Date Range selectors
        filter_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        # Default date_from to start of month
        today = QDate.currentDate()
        self.date_from.setDate(QDate(today.year(), today.month(), 1))
        filter_layout.addWidget(self.date_from)

        filter_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(today)
        filter_layout.addWidget(self.date_to)

        self.btn_filter = QPushButton("Apply Filters")
        self.btn_filter.clicked.connect(self.load_audit_logs)
        filter_layout.addWidget(self.btn_filter)

        self.btn_reset_filters = QPushButton("Reset")
        self.btn_reset_filters.setObjectName("btn_secondary")
        self.btn_reset_filters.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.btn_reset_filters)

        filter_layout.addStretch()
        main_layout.addWidget(filter_panel)

        # Audit Logs Table
        self.table_logs = QTableWidget(0, 5)
        self.table_logs.setHorizontalHeaderLabels(["User", "Action performed", "Date", "Time", "IP Address"])
        self.table_logs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_logs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Give action details maximum width
        self.table_logs.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_logs.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_logs.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table_logs)

    def reset_filters(self, *args):
        self.txt_search.clear()
        today = QDate.currentDate()
        self.date_from.setDate(QDate(today.year(), today.month(), 1))
        self.date_to.setDate(today)
        self.load_audit_logs()

    def load_audit_logs(self, *args):
        query = self.txt_search.text().strip()
        from_str = self.date_from.date().toString("yyyy-MM-dd")
        to_str = self.date_to.date().toString("yyyy-MM-dd")

        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        self.worker = AuditLogWorker(self.service, query, from_str, to_str)
        self.worker.logs_fetched.connect(self.populate_table)
        self.worker.failed.connect(self.on_fetch_failed)
        self.worker.start()

    def populate_table(self, logs: list):
        self.table_logs.setRowCount(0)
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        for idx, log in enumerate(logs):
            self.table_logs.insertRow(idx)

            user_item = QTableWidgetItem(log["user_email"])
            action_item = QTableWidgetItem(log["action"])
            date_item = QTableWidgetItem(log["log_date"])
            time_item = QTableWidgetItem(log["log_time"])
            ip_item = QTableWidgetItem(log["ip_address"])

            user_item.setTextAlignment(align_left)
            action_item.setTextAlignment(align_left)
            date_item.setTextAlignment(align_left)
            time_item.setTextAlignment(align_left)
            ip_item.setTextAlignment(align_left)

            self.table_logs.setItem(idx, 0, user_item)
            self.table_logs.setItem(idx, 1, action_item)
            self.table_logs.setItem(idx, 2, date_item)
            self.table_logs.setItem(idx, 3, time_item)
            self.table_logs.setItem(idx, 4, ip_item)

    def on_fetch_failed(self, error: str):
        if hasattr(self.window(), 'show_notification'):
            self.window().show_notification(f"Failed to load audit logs: {error}", "error")
        else:
            QMessageBox.critical(self, "Error", f"Failed to load audit logs:\n{error}")
