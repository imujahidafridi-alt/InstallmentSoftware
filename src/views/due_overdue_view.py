from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.viewmodels.installment_viewmodel import InstallmentViewModel
from src.services.cache_service import CacheService
from src.config import ConfigManager

class DueOverdueWorker(QThread):
    sync_finished = pyqtSignal(dict)
    sync_not_needed = pyqtSignal()
    sync_failed = pyqtSignal(str)

    def __init__(self, inst_vm: InstallmentViewModel):
        super().__init__()
        self.inst_vm = inst_vm

    def run(self):
        try:
            changed = CacheService.check_and_update_state("due_overdue", self.inst_vm.inst_repo.db)
            has_cache = CacheService.get("dashboard_tracking") is not None
            if not changed and has_cache:
                print("[Reminders] No database changes detected. Loading reminders from persistent cache.")
                self.sync_not_needed.emit()
                return

            print("[Reminders] Database changes detected. Updating reminders from database...")
            tracking = self.inst_vm.get_due_tracking_lists()
            self.sync_finished.emit(tracking)
        except Exception as e:
            self.sync_failed.emit(str(e))


class DueOverdueView(QWidget):
    def __init__(self):
        super().__init__()
        self.inst_vm = InstallmentViewModel()
        self.cache_tracking = CacheService.get("dashboard_tracking")
        self.sync_worker = None
        self.tracking_data = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Header Title
        header_layout = QHBoxLayout()
        lbl_title = QLabel("Reminders & Payment Schedules")
        lbl_title.setObjectName("lbl_title")
        header_layout.addWidget(lbl_title)
        
        self.lbl_status = QLabel("Up to date")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #10B981; font-weight: bold;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.lbl_status)
        main_layout.addLayout(header_layout)

        # QTabWidget grouping Overdue and Due schedules
        self.tab_widget = QTabWidget()
        
        # --- TAB 1: OVERDUE INSTALLMENTS ---
        self.tab_overdue = QWidget()
        overdue_layout = QVBoxLayout(self.tab_overdue)
        overdue_layout.setContentsMargins(15, 15, 15, 15)
        overdue_layout.setSpacing(15)
        
        # Overdue controls layout (title & combobox filter)
        overdue_ctrl_layout = QHBoxLayout()
        lbl_overdue_desc = QLabel("Track overdue installments to initiate customer recovery.")
        lbl_overdue_desc.setStyleSheet("color: #64748B; font-size: 12px;")
        overdue_ctrl_layout.addWidget(lbl_overdue_desc)
        overdue_ctrl_layout.addStretch()
        
        self.cmb_overdue_filter = QComboBox()
        self.cmb_overdue_filter.addItems(["All Overdue", "1-30 Days", "31-60 Days", "61-90 Days", "90+ Days"])
        self.cmb_overdue_filter.currentIndexChanged.connect(self.update_overdue_table)
        self.cmb_overdue_filter.setFixedWidth(150)
        overdue_ctrl_layout.addWidget(self.cmb_overdue_filter)
        overdue_layout.addLayout(overdue_ctrl_layout)
        
        # Overdue Table
        self.table_overdue = QTableWidget(0, 6)
        self.table_overdue.setHorizontalHeaderLabels(["S.No", "Customer", "Device Details", "Due Date", "Days Overdue", "Outstanding Balance"])
        self.table_overdue.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_overdue.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_overdue.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_overdue.verticalHeader().setVisible(False)
        self.table_overdue.verticalHeader().setDefaultSectionSize(38)
        self.table_overdue.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_overdue.doubleClicked.connect(self.on_overdue_double_clicked)
        overdue_layout.addWidget(self.table_overdue)
        
        # --- TAB 2: DUE SCHEDULES ---
        self.tab_due = QWidget()
        due_layout = QVBoxLayout(self.tab_due)
        due_layout.setContentsMargins(15, 15, 15, 15)
        due_layout.setSpacing(15)
        
        due_ctrl_layout = QHBoxLayout()
        lbl_due_desc = QLabel("Upcoming schedules representing payments expected soon.")
        lbl_due_desc.setStyleSheet("color: #64748B; font-size: 12px;")
        due_ctrl_layout.addWidget(lbl_due_desc)
        due_ctrl_layout.addStretch()
        
        self.cmb_due_filter = QComboBox()
        self.cmb_due_filter.addItems(["Due Today", "Due Tomorrow", "Due This Week", "Due This Month"])
        self.cmb_due_filter.currentIndexChanged.connect(self.update_due_table)
        self.cmb_due_filter.setFixedWidth(150)
        due_ctrl_layout.addWidget(self.cmb_due_filter)
        due_layout.addLayout(due_ctrl_layout)
        
        # Due Table
        self.table_due = QTableWidget(0, 5)
        self.table_due.setHorizontalHeaderLabels(["S.No", "Customer", "Device Details", "Due Date", "Outstanding Balance"])
        self.table_due.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_due.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_due.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_due.verticalHeader().setVisible(False)
        self.table_due.verticalHeader().setDefaultSectionSize(38)
        self.table_due.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_due.doubleClicked.connect(self.on_due_double_clicked)
        due_layout.addWidget(self.table_due)
        
        # Add to Tab Widget
        self.tab_widget.addTab(self.tab_overdue, "Overdue Installments")
        self.tab_widget.addTab(self.tab_due, "Upcoming Due Schedules")
        main_layout.addWidget(self.tab_widget)

        # Bind cache immediately if available
        if self.cache_tracking:
            self.tracking_data = self.cache_tracking
            self.update_due_table()
            self.update_overdue_table()

    def refresh_data(self):
        if self.cache_tracking:
            self.tracking_data = self.cache_tracking
            self.update_due_table()
            self.update_overdue_table()

        if self.sync_worker and self.sync_worker.isRunning():
            return

        self.lbl_status.setText("Updating")
        self.lbl_status.setStyleSheet("color: #F59E0B; font-weight: bold;")

        self.sync_worker = DueOverdueWorker(self.inst_vm)
        self.sync_worker.sync_finished.connect(self.on_sync_success)
        self.sync_worker.sync_not_needed.connect(self.on_sync_not_needed)
        self.sync_worker.sync_failed.connect(self.on_sync_failed)
        self.sync_worker.start()

    def on_sync_success(self, tracking: dict):
        self.lbl_status.setText("Up to date")
        self.lbl_status.setStyleSheet("color: #10B981; font-weight: bold;")
        
        self.cache_tracking = tracking
        CacheService.set("dashboard_tracking", tracking)
        
        self.tracking_data = tracking
        self.update_due_table()
        self.update_overdue_table()

    def on_sync_not_needed(self):
        self.lbl_status.setText("Up to date")
        self.lbl_status.setStyleSheet("color: #10B981; font-weight: bold;")

    def on_sync_failed(self, error_msg: str):
        self.lbl_status.setText("Offline")
        self.lbl_status.setStyleSheet("color: #EF4444; font-weight: bold;")
        print(f"[Reminders] Sync Error: {error_msg}")

    def update_due_table(self):
        if not self.tracking_data:
            return

        filter_type = self.cmb_due_filter.currentText()
        if filter_type == "Due Today":
            data = self.tracking_data.get("due_today", [])
        elif filter_type == "Due Tomorrow":
            data = self.tracking_data.get("due_tomorrow", [])
        elif filter_type == "Due This Week":
            data = self.tracking_data.get("due_this_week", [])
        else:
            data = self.tracking_data.get("due_this_month", [])

        self.table_due.setRowCount(0)
        align_center = Qt.AlignmentFlag.AlignCenter
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        for idx, item in enumerate(data):
            self.table_due.insertRow(idx)

            item_sno = QTableWidgetItem(str(idx + 1))
            item_sno.setTextAlignment(align_center)
            self.table_due.setItem(idx, 0, item_sno)

            item_cust = QTableWidgetItem(item["customer_name"])
            item_cust.setTextAlignment(align_left)
            item_cust.setToolTip(item["customer_name"])
            self.table_due.setItem(idx, 1, item_cust)

            item_dev = QTableWidgetItem(item["device_name"])
            item_dev.setTextAlignment(align_left)
            item_dev.setToolTip(item["device_name"])
            self.table_due.setItem(idx, 2, item_dev)

            item_due = QTableWidgetItem(item["due_date"])
            item_due.setTextAlignment(align_left)
            item_due.setToolTip(item["due_date"])
            self.table_due.setItem(idx, 3, item_due)

            formatted_outstanding = ConfigManager.format_currency(item["outstanding_amount"])
            item_outstanding = QTableWidgetItem(formatted_outstanding)
            item_outstanding.setTextAlignment(align_left)
            item_outstanding.setToolTip(formatted_outstanding)
            self.table_due.setItem(idx, 4, item_outstanding)

    def update_overdue_table(self):
        if not self.tracking_data:
            return

        filter_type = self.cmb_overdue_filter.currentText()
        if filter_type == "1-30 Days":
            data = self.tracking_data.get("overdue_1_30", [])
        elif filter_type == "31-60 Days":
            data = self.tracking_data.get("overdue_31_60", [])
        elif filter_type == "61-90 Days":
            data = self.tracking_data.get("overdue_61_90", [])
        elif filter_type == "90+ Days":
            data = self.tracking_data.get("overdue_90_plus", [])
        else:
            data = (self.tracking_data.get("overdue_1_30", []) + 
                    self.tracking_data.get("overdue_31_60", []) + 
                    self.tracking_data.get("overdue_61_90", []) + 
                    self.tracking_data.get("overdue_90_plus", []))

        self.table_overdue.setRowCount(0)
        align_center = Qt.AlignmentFlag.AlignCenter
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        for idx, item in enumerate(data):
            self.table_overdue.insertRow(idx)

            item_sno = QTableWidgetItem(str(idx + 1))
            item_sno.setTextAlignment(align_center)
            self.table_overdue.setItem(idx, 0, item_sno)

            item_cust = QTableWidgetItem(item["customer_name"])
            item_cust.setTextAlignment(align_left)
            item_cust.setToolTip(item["customer_name"])
            self.table_overdue.setItem(idx, 1, item_cust)

            item_dev = QTableWidgetItem(item["device_name"])
            item_dev.setTextAlignment(align_left)
            item_dev.setToolTip(item["device_name"])
            self.table_overdue.setItem(idx, 2, item_dev)

            item_due = QTableWidgetItem(item["due_date"])
            item_due.setTextAlignment(align_left)
            item_due.setToolTip(item["due_date"])
            self.table_overdue.setItem(idx, 3, item_due)

            days_str = f"{item['days_overdue']} days"
            days_item = QTableWidgetItem(days_str)
            days_item.setTextAlignment(align_left)
            days_item.setForeground(Qt.GlobalColor.red)
            days_item.setToolTip(days_str)
            self.table_overdue.setItem(idx, 4, days_item)

            formatted_outstanding = ConfigManager.format_currency(item["outstanding_amount"])
            item_outstanding = QTableWidgetItem(formatted_outstanding)
            item_outstanding.setTextAlignment(align_left)
            item_outstanding.setToolTip(formatted_outstanding)
            self.table_overdue.setItem(idx, 5, item_outstanding)

    def on_overdue_double_clicked(self, model_index):
        filter_type = self.cmb_overdue_filter.currentText()
        if not self.tracking_data:
            return
        if filter_type == "1-30 Days":
            data = self.tracking_data.get("overdue_1_30", [])
        elif filter_type == "31-60 Days":
            data = self.tracking_data.get("overdue_31_60", [])
        elif filter_type == "61-90 Days":
            data = self.tracking_data.get("overdue_61_90", [])
        elif filter_type == "90+ Days":
            data = self.tracking_data.get("overdue_90_plus", [])
        else:
            data = (self.tracking_data.get("overdue_1_30", []) + 
                    self.tracking_data.get("overdue_31_60", []) + 
                    self.tracking_data.get("overdue_61_90", []) + 
                    self.tracking_data.get("overdue_90_plus", []))
        self.handle_redirect(model_index, data)

    def on_due_double_clicked(self, model_index):
        filter_type = self.cmb_due_filter.currentText()
        if not self.tracking_data:
            return
        if filter_type == "Due Today":
            data = self.tracking_data.get("due_today", [])
        elif filter_type == "Due Tomorrow":
            data = self.tracking_data.get("due_tomorrow", [])
        elif filter_type == "Due This Week":
            data = self.tracking_data.get("due_this_week", [])
        else:
            data = self.tracking_data.get("due_this_month", [])
        self.handle_redirect(model_index, data)

    def handle_redirect(self, model_index, data_list):
        row = model_index.row()
        if row >= len(data_list):
            return
        item = data_list[row]
        sale_id = item.get("sale_id")
        win = self.window()
        if sale_id and win and hasattr(win, "switch_view"):
            if hasattr(win, "view_ledger") and hasattr(win.view_ledger, "select_sale"):
                win.view_ledger.select_sale(sale_id)
            win.switch_view(5)
