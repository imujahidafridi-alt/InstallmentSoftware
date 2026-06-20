from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.viewmodels.report_viewmodel import ReportViewModel
from datetime import datetime
from src.services.cache_service import CacheService
from src.config import ConfigManager

class ReportWorker(QThread):
    sync_finished = pyqtSignal(list, dict)
    sync_not_needed = pyqtSignal()
    sync_failed = pyqtSignal(str)

    def __init__(self, vm: ReportViewModel, month: int, year: int):
        super().__init__()
        self.vm = vm
        self.month = month
        self.year = year

    def run(self):
        try:
            changed = CacheService.check_and_update_state("payments", self.vm.db)
            cache_key = f"{self.month}_{self.year}"
            cached_reports = CacheService.get("monthly_reports") or {}
            has_cache = cache_key in cached_reports
            if not changed and has_cache:
                print(f"[Monthly Report: {self.month}/{self.year}] No database changes detected. Loading report from persistent cache.")
                self.sync_not_needed.emit()
                return

            print(f"[Monthly Report: {self.month}/{self.year}] Database changes detected. Compiling report from database...")
            data, summary = self.vm.get_monthly_collections_data(self.month, self.year)
            self.sync_finished.emit(data, summary)
        except Exception as e:
            self.sync_failed.emit(str(e))


class ReportView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = ReportViewModel()
        
        # Load cache from persistent storage
        self.cache_reports = CacheService.get("monthly_reports", {})
        self.worker = None
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Title / Search section
        filter_panel = QFrame()
        filter_panel.setObjectName("topnav")
        filter_layout = QHBoxLayout(filter_panel)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(15)
        
        # Month
        filter_layout.addWidget(QLabel("Month:"))
        self.cmb_month = QComboBox()
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        for idx, m in enumerate(months, 1):
            self.cmb_month.addItem(m, idx)
        # default to current month
        self.cmb_month.setCurrentIndex(datetime.now().month - 1)
        filter_layout.addWidget(self.cmb_month)

        # Year
        filter_layout.addWidget(QLabel("Year:"))
        self.cmb_year = QComboBox()
        curr_year = datetime.now().year
        for y in range(curr_year - 5, curr_year + 5):
            self.cmb_year.addItem(str(y), y)
        self.cmb_year.setCurrentText(str(curr_year))
        filter_layout.addWidget(self.cmb_year)
        
        # Query button
        self.btn_load = QPushButton("Generate Report View")
        self.btn_load.clicked.connect(self.load_report_data)
        filter_layout.addWidget(self.btn_load)
        
        filter_layout.addStretch()
        main_layout.addWidget(filter_panel)

        # -------------------------------------------------------------
        # SUMMARY KPI METRICS PANEL
        # -------------------------------------------------------------
        sum_layout = QHBoxLayout()
        sum_layout.setSpacing(15)
        
        self.lbl_sum_received = QLabel("Collections This Month: Rs. 0.00")
        self.lbl_sum_received.setObjectName("lbl_metric_title")
        self.lbl_sum_received.setStyleSheet("font-weight: bold; font-size: 13px; color: #10B981;")
        
        self.lbl_sum_outstanding = QLabel("System Outstanding: Rs. 0.00")
        self.lbl_sum_outstanding.setObjectName("lbl_metric_title")
        self.lbl_sum_outstanding.setStyleSheet("font-weight: bold; font-size: 13px; color: #EF4444;")
        
        self.lbl_sum_profit = QLabel("Profit Margin: Rs. 0.00")
        self.lbl_sum_profit.setObjectName("lbl_metric_title")
        self.lbl_sum_profit.setStyleSheet("font-weight: bold; font-size: 13px; color: #3B82F6;")
        
        sum_layout.addWidget(self.lbl_sum_received)
        sum_layout.addWidget(self.lbl_sum_outstanding)
        sum_layout.addWidget(self.lbl_sum_profit)
        main_layout.addLayout(sum_layout)

        # Table showing received log
        self.table_collections = QTableWidget(0, 5)
        self.table_collections.setHorizontalHeaderLabels(["S.No", "Customer Name", "Device", "Payment Date", "Amount Received"])
        self.table_collections.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_collections.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_collections.verticalHeader().setVisible(False)
        self.table_collections.verticalHeader().setDefaultSectionSize(38)
        self.table_collections.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.table_collections)



        # -------------------------------------------------------------
        # EXPORTS ACTION PANEL
        # -------------------------------------------------------------
        export_panel = QFrame()
        export_panel.setObjectName("form_card")
        export_layout = QHBoxLayout(export_panel)
        export_layout.setContentsMargins(10, 10, 10, 10)
        export_layout.setSpacing(15)
        
        export_layout.addWidget(QLabel("<b>Export Collection Report:</b>"))
        
        self.btn_pdf = QPushButton("Export to PDF")
        self.btn_pdf.clicked.connect(lambda: self.trigger_export("pdf"))
        self.btn_pdf.setEnabled(False)
        export_layout.addWidget(self.btn_pdf)

        self.btn_excel = QPushButton("Export to Excel")
        self.btn_excel.clicked.connect(lambda: self.trigger_export("excel"))
        self.btn_excel.setEnabled(False)
        export_layout.addWidget(self.btn_excel)

        self.btn_csv = QPushButton("Export to CSV")
        self.btn_csv.clicked.connect(lambda: self.trigger_export("csv"))
        self.btn_csv.setEnabled(False)
        export_layout.addWidget(self.btn_csv)
        
        export_layout.addStretch()
        main_layout.addWidget(export_panel)

    def load_report_data(self, *args):
        """Compiles monthly log collection from VM and fills tables/labels asynchronously."""
        month = self.cmb_month.currentData()
        year = self.cmb_year.currentData()
        
        cache_key = f"{month}_{year}"
        
        # 1. Populate cache immediately if available
        if cache_key in self.cache_reports:
            data, summary = self.cache_reports[cache_key]
            self.populate_report_ui(data, summary)

        # 2. Prevent concurrent runs
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        # 3. Fire async worker
        self.worker = ReportWorker(self.vm, month, year)
        
        def on_success(data, summary):
            self.cache_reports[cache_key] = (data, summary)
            CacheService.set("monthly_reports", self.cache_reports)
            self.populate_report_ui(data, summary)
            print(f"[Monthly Report: {month}/{year}] Report data updated successfully.")

        def on_not_needed():
            pass

        def on_failed(error_msg):
            print(f"Report load failed: {error_msg}")
            
        self.worker.sync_finished.connect(on_success)
        self.worker.sync_not_needed.connect(on_not_needed)
        self.worker.sync_failed.connect(on_failed)
        self.worker.start()

    def populate_report_ui(self, data: list, summary: dict):
        # Fill summary widgets
        self.lbl_sum_received.setText(f"Collections This Month: {ConfigManager.format_currency(summary['total_collection'])}")
        self.lbl_sum_outstanding.setText(f"System Outstanding: {ConfigManager.format_currency(summary['total_outstanding'])}")
        self.lbl_sum_profit.setText(f"Profit Margin: {ConfigManager.format_currency(summary['total_profit'])}")
        
        # Populate list details
        self.table_collections.setRowCount(0)
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        for idx, item in enumerate(data):
            self.table_collections.insertRow(idx)
            
            item_sno = QTableWidgetItem(str(idx + 1))
            item_sno.setTextAlignment(align_left)
            item_sno.setToolTip(str(idx + 1))
            self.table_collections.setItem(idx, 0, item_sno)
            
            item_cust = QTableWidgetItem(item["customer_name"])
            item_cust.setTextAlignment(align_left)
            item_cust.setToolTip(item["customer_name"])
            self.table_collections.setItem(idx, 1, item_cust)
            
            item_dev = QTableWidgetItem(item["device_name"])
            item_dev.setTextAlignment(align_left)
            item_dev.setToolTip(item["device_name"])
            self.table_collections.setItem(idx, 2, item_dev)
            
            pay_dt = datetime.strptime(item["payment_date"], "%Y-%m-%d").strftime("%d-%b-%Y")
            item_pay = QTableWidgetItem(pay_dt)
            item_pay.setTextAlignment(align_left)
            item_pay.setToolTip(pay_dt)
            self.table_collections.setItem(idx, 3, item_pay)
            
            formatted_amount = ConfigManager.format_currency(item['amount_received'])
            item_amount = QTableWidgetItem(formatted_amount)
            item_amount.setTextAlignment(align_left)
            item_amount.setToolTip(formatted_amount)
            self.table_collections.setItem(idx, 4, item_amount)



        # Enable file export actions
        has_records = len(data) > 0
        self.btn_pdf.setEnabled(has_records)
        self.btn_excel.setEnabled(has_records)
        self.btn_csv.setEnabled(has_records)

    def show_toast(self, message: str, type: str = "info"):
        if hasattr(self.window(), 'show_notification'):
            self.window().show_notification(message, type)
        else:
            if type == "error":
                QMessageBox.critical(self, "Error", message)
            elif type == "warning":
                QMessageBox.warning(self, "Warning", message)
            else:
                QMessageBox.information(self, "Info", message)

    def trigger_export(self, fmt: str):
        month = self.cmb_month.currentData()
        year = self.cmb_year.currentData()
        month_name = self.cmb_month.currentText()
        
        # File selector dialog recommendation
        if fmt == "pdf":
            file_filter = "PDF Files (*.pdf)"
            ext = "pdf"
        elif fmt == "excel":
            file_filter = "Excel Files (*.xlsx)"
            ext = "xlsx"
        else:
            file_filter = "CSV Files (*.csv)"
            ext = "csv"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            f"Save Collection Report ({fmt.upper()})", 
            f"Collections_Report_{month_name}_{year}.{ext}",
            file_filter
        )
        
        if not file_path:
            return
            
        try:
            self.vm.export_report(fmt, month, year, file_path)
            self.show_toast(f"Monthly Report successfully compiled and saved to:\n{file_path}", "success")
        except Exception as e:
            self.show_toast(f"Could not export report to {fmt.upper()}:\n{e}", "error")
