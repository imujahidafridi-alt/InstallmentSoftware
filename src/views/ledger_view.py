from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QCompleter, QListWidget, QListWidgetItem, QAbstractItemView, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon
from src.viewmodels.installment_viewmodel import InstallmentViewModel
from src.views.payment_dialog import PaymentDialog
from src.views.reschedule_dialog import RescheduleDialog
from datetime import datetime
from src.services.cache_service import CacheService
from src.config import ConfigManager

class LedgerListWorker(QThread):
    sync_finished = pyqtSignal(list)
    sync_not_needed = pyqtSignal()
    sync_failed = pyqtSignal(str)

    def __init__(self, vm: InstallmentViewModel):
        super().__init__()
        self.vm = vm

    def run(self):
        try:
            changed = CacheService.check_and_update_state("sales", self.vm.sale_repo.db)
            has_cache = CacheService.get("ledger_sales_list") is not None
            if not changed and has_cache:
                print("[Ledgers List] No database changes detected. Loading sales list from persistent cache.")
                self.sync_not_needed.emit()
                return

            print("[Ledgers List] Database changes detected. Fetching fresh sales list...")
            sales = self.vm.sale_repo.get_all_with_details()
            self.sync_finished.emit(sales)
        except Exception as e:
            self.sync_failed.emit(str(e))


class LedgerDetailWorker(QThread):
    sync_finished = pyqtSignal(dict)
    sync_not_needed = pyqtSignal()
    sync_failed = pyqtSignal(str)

    def __init__(self, vm: InstallmentViewModel, sale_id: str):
        super().__init__()
        self.vm = vm
        self.sale_id = sale_id

    def run(self):
        try:
            changed = CacheService.check_and_update_state("ledger", self.vm.pay_repo.db)
            cached_details = CacheService.get("ledger_details") or {}
            has_cache = self.sale_id in cached_details
            if not changed and has_cache:
                print(f"[Ledger Detail: {self.sale_id}] No database changes detected. Loading ledger from persistent cache.")
                self.sync_not_needed.emit()
                return

            print(f"[Ledger Detail: {self.sale_id}] Database changes detected. Fetching fresh ledger calculations...")
            data = self.vm.get_ledger_data(self.sale_id)
            self.sync_finished.emit(data)
        except Exception as e:
            self.sync_failed.emit(str(e))


class PaymentRecordWorker(QThread):
    success = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, vm: InstallmentViewModel, sale_id: str, amount: float, date_str: str, notes: str, method: str):
        super().__init__()
        self.vm = vm
        self.sale_id = sale_id
        self.amount = amount
        self.date_str = date_str
        self.notes = notes
        self.method = method

    def run(self):
        try:
            self.vm.record_payment(self.sale_id, self.amount, self.date_str, self.notes, self.method)
            self.success.emit()
        except Exception as e:
            self.failed.emit(str(e))


class RescheduleWorker(QThread):
    success = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, vm: InstallmentViewModel, sale_id: str, new_start_date: str, new_duration: int):
        super().__init__()
        self.vm = vm
        self.sale_id = sale_id
        self.new_start_date = new_start_date
        self.new_duration = new_duration

    def run(self):
        try:
            self.vm.reschedule_installments(self.sale_id, self.new_start_date, self.new_duration)
            self.success.emit()
        except Exception as e:
            self.failed.emit(str(e))


class PdfExportWorker(QThread):
    success = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, vm: InstallmentViewModel, sale_id: str, file_path: str):
        super().__init__()
        self.vm = vm
        self.sale_id = sale_id
        self.file_path = file_path

    def run(self):
        try:
            self.vm.generate_pdf_report(self.sale_id, self.file_path)
            self.success.emit(self.file_path)
        except Exception as e:
            self.failed.emit(str(e))


class LedgerSearchWidget(QWidget):
    """
    A styled inline ledger-search field that shows a light-theme
    popup list. Each suggestion row shows:
        Customer Name  /  Father Name  /  Device  /  Selling Price
    Selecting a row commits the choice and hides the popup.
    """

    ledger_selected = pyqtSignal(str)   # emits sale_id

    _POPUP_ITEM_HEIGHT = 52   # px per row

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sales: list  = []
        self._selected_id: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search input
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Type to search ledger by customer, mobile, device, or IMEI…")
        self.txt_search.setFixedHeight(36)
        self.txt_search.setStyleSheet(
            "QLineEdit {"
            "  background: #FFFFFF;"
            "  border: 1px solid #CBD5E1;"
            "  border-radius: 6px;"
            "  padding: 6px 12px;"
            "  font-size: 13px;"
            "  color: #0F172A;"
            "}"
            "QLineEdit:focus {"
            "  border: 1.5px solid #3B82F6;"
            "}"
        )
        self.txt_search.textChanged.connect(self._on_text_changed)
        self.txt_search.focusOutEvent = self._on_focus_out
        layout.addWidget(self.txt_search)

        # Popup list (hidden by default)
        self.list_popup = QListWidget()
        self.list_popup.setVisible(False)
        self.list_popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_popup.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list_popup.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_popup.setStyleSheet(
            "QListWidget {"
            "  background: #FFFFFF;"
            "  border: 1px solid #CBD5E1;"
            "  border-radius: 6px;"
            "  outline: none;"
            "}"
            "QListWidget::item {"
            "  padding: 8px 12px;"
            "  border-bottom: 1px solid #F1F5F9;"
            "  color: #0F172A;"
            "  font-size: 12px;"
            "}"
            "QListWidget::item:selected, QListWidget::item:hover {"
            "  background: #EFF6FF;"
            "  color: #1D4ED8;"
            "}"
        )
        self.list_popup.itemClicked.connect(self._on_item_clicked)

        # Debounce timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._filter_popup)

    def _on_focus_out(self, event):
        QTimer.singleShot(200, self._hide_popup)
        QLineEdit.focusOutEvent(self.txt_search, event)

    def set_sales(self, sales: list):
        self._sales = sales

    def selected_id(self) -> str:
        return self._selected_id

    def set_selected_id(self, sale_id: str):
        self._selected_id = sale_id
        for sale in self._sales:
            if sale["id"] == sale_id:
                formatted_price = ConfigManager.format_currency(sale['selling_price'])
                display = f"{sale['customers']['name']} - {sale['devices']['brand']} {sale['devices']['model']} ({formatted_price})"
                self.txt_search.blockSignals(True)
                self.txt_search.setText(display)
                self.txt_search.blockSignals(False)
                break

    def clear_selection(self):
        self._selected_id = ""
        self.txt_search.clear()
        self._hide_popup()

    def _on_text_changed(self, text: str):
        self._selected_id = ""
        self._timer.stop()
        self._timer.start(200)

    def _filter_popup(self):
        query = self.txt_search.text().strip().lower()
        self.list_popup.clear()

        if not query:
            self._hide_popup()
            return

        matches = []
        for sale in self._sales:
            cust = sale.get("customers") or {}
            dev = sale.get("devices") or {}
            
            cust_name = cust.get("name", "").lower()
            father_name = cust.get("father_name", "").lower()
            mobile = cust.get("mobile", "").lower()
            brand = dev.get("brand", "").lower()
            model = dev.get("model", "").lower()
            imei_1 = dev.get("imei_1", "").lower() if dev.get("imei_1") else ""
            
            if (query in cust_name or 
                query in father_name or 
                query in mobile or 
                query in brand or 
                query in model or 
                query in imei_1 or 
                query in sale.get("id", "").lower()):
                matches.append(sale)

        if not matches:
            self._hide_popup()
            return

        for sale in matches[:20]:   # cap at 20 suggestions
            cust = sale.get("customers") or {}
            dev = sale.get("devices") or {}
            father = cust.get("father_name") or "—"
            dev_name = f"{dev.get('brand', '')} {dev.get('model', '')}"
            price = ConfigManager.format_currency(sale.get("selling_price", 0))
            display = f"{cust.get('name')}  /  {father}  /  {dev_name}  /  {price}"

            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, sale["id"])
            item.setToolTip(
                f"Customer: {cust.get('name')}\n"
                f"Father:   {father}\n"
                f"Device:   {dev_name}\n"
                f"Price:    {price}"
            )
            self.list_popup.addItem(item)

        win = self.window()
        if win:
            if self.list_popup.parent() != win:
                self.list_popup.setParent(win)
            pos = self.txt_search.mapTo(win, self.txt_search.rect().bottomLeft())
            visible_rows = min(len(matches), 5)
            self.list_popup.setGeometry(
                pos.x(),
                pos.y() + 2,
                self.txt_search.width(),
                visible_rows * self._POPUP_ITEM_HEIGHT
            )
            self.list_popup.raise_()
            self.list_popup.show()

    def _on_item_clicked(self, item: QListWidgetItem):
        sale_id = item.data(Qt.ItemDataRole.UserRole)
        self._selected_id = sale_id
        
        for sale in self._sales:
            if sale["id"] == sale_id:
                formatted_price = ConfigManager.format_currency(sale['selling_price'])
                display = f"{sale['customers']['name']} - {sale['devices']['brand']} {sale['devices']['model']} ({formatted_price})"
                self.txt_search.blockSignals(True)
                self.txt_search.setText(display)
                self.txt_search.blockSignals(False)
                break

        self._hide_popup()
        self.ledger_selected.emit(sale_id)

    def _hide_popup(self):
        self.list_popup.setVisible(False)
        self.list_popup.clear()


class LedgerView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = InstallmentViewModel()
        
        # Load cache from persistent storage
        self.cache_sales_list = CacheService.get("ledger_sales_list")
        self.cache_ledger_details = CacheService.get("ledger_details", {})
        
        self.list_worker = None
        self.detail_worker = None
        self.pending_sale_id = None
        self.payment_worker = None
        self.reschedule_worker = None
        self.pdf_worker = None
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Title / Search section
        search_panel = QFrame()
        search_panel.setObjectName("topnav")
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(10, 10, 10, 10)
        
        search_layout.addWidget(QLabel("Select Active Ledger / Sale:"))
        self.ledg_search = LedgerSearchWidget()
        self.ledg_search.setFixedWidth(380)
        self.ledg_search.ledger_selected.connect(self.load_selected_ledger)
        search_layout.addWidget(self.ledg_search)
        
        self.btn_refresh = QPushButton("Refresh Ledgers")
        self.btn_refresh.setObjectName("btn_secondary")
        self.btn_refresh.clicked.connect(self.load_ledgers_dropdown)
        search_layout.addWidget(self.btn_refresh)
        
        search_layout.addStretch()
        main_layout.addWidget(search_panel)

        # Main Layout splitter
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # -------------------------------------------------------------
        # LEFT COLUMN: LEDGER AND CUSTOMER SUMMARY CARDS
        # -------------------------------------------------------------
        left_col = QVBoxLayout()
        left_col.setSpacing(15)

        # Summary Info Box
        self.summary_box = QFrame()
        self.summary_box.setObjectName("form_card")
        self.summary_box.setFixedWidth(300)
        sum_layout = QVBoxLayout(self.summary_box)
        sum_layout.setSpacing(10)
        
        lbl_sum_title = QLabel("Ledger Balance Sheet")
        lbl_sum_title.setObjectName("lbl_section_title")
        sum_layout.addWidget(lbl_sum_title)

        import os
        def create_metric_row(icon_name, label_widget):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(10)
            
            icon_label = QLabel()
            icon_label.setFixedSize(16, 16)
            
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons", f"{icon_name}.svg")
            if os.path.exists(icon_path):
                icon_label.setPixmap(QIcon(icon_path).pixmap(16, 16))
            
            row_layout.addWidget(icon_label)
            row_layout.addWidget(label_widget)
            row_layout.addStretch()
            return row_widget

        self.lbl_cust_name = QLabel("Customer: -")
        self.lbl_cust_father = QLabel("Father Name: -")
        self.lbl_cust_address = QLabel("Address: -")
        self.lbl_dev_name = QLabel("Device: -")
        self.lbl_selling_price = QLabel("Total Sale Price: Rs. 0.00")
        self.lbl_down_payment = QLabel("Down Payment: Rs. 0.00")
        self.lbl_total_paid = QLabel("Total Payments: Rs. 0.00")
        self.lbl_outstanding = QLabel("Outstanding Balance: Rs. 0.00")
        self.lbl_outstanding.setStyleSheet("font-weight: bold; color: #EF4444;")
        self.lbl_remaining_months = QLabel("Unpaid Months: 0")
        self.lbl_next_due = QLabel("Next Due Date: -")
        
        sum_layout.addWidget(create_metric_row("user", self.lbl_cust_name))
        sum_layout.addWidget(create_metric_row("users", self.lbl_cust_father))
        sum_layout.addWidget(create_metric_row("map-pin", self.lbl_cust_address))
        
        # Spacer line QFrame
        spacer_line = QFrame()
        spacer_line.setFrameShape(QFrame.Shape.HLine)
        spacer_line.setFrameShadow(QFrame.Shadow.Sunken)
        spacer_line.setStyleSheet("background-color: #E2E8F0; max-height: 1px; margin: 5px 0;")
        sum_layout.addWidget(spacer_line)
        
        sum_layout.addWidget(create_metric_row("smartphone", self.lbl_dev_name))
        sum_layout.addWidget(create_metric_row("tag", self.lbl_selling_price))
        sum_layout.addWidget(create_metric_row("credit-card", self.lbl_down_payment))
        sum_layout.addWidget(create_metric_row("coins", self.lbl_total_paid))
        sum_layout.addWidget(create_metric_row("alert-circle", self.lbl_outstanding))
        sum_layout.addWidget(create_metric_row("clock", self.lbl_remaining_months))
        sum_layout.addWidget(create_metric_row("calendar", self.lbl_next_due))
        sum_layout.addStretch()
        
        left_col.addWidget(self.summary_box)

        # Action Buttons Box
        action_box = QFrame()
        action_box.setObjectName("form_card")
        action_box.setFixedWidth(300)
        act_layout = QVBoxLayout(action_box)
        act_layout.setSpacing(10)
        
        self.btn_pay = QPushButton("Collect Installment Payment")
        self.btn_pay.clicked.connect(self.collect_payment)
        self.btn_pay.setEnabled(False)
        
        self.btn_reschedule = QPushButton("Reschedule Remaining Balance")
        self.btn_reschedule.setObjectName("btn_secondary")
        self.btn_reschedule.clicked.connect(self.reschedule_ledger)
        self.btn_reschedule.setEnabled(False)

        self.btn_pdf = QPushButton("Export Customer Ledger (PDF)")
        self.btn_pdf.setObjectName("btn_secondary")
        self.btn_pdf.clicked.connect(self.export_pdf)
        self.btn_pdf.setEnabled(False)
        
        act_layout.addWidget(self.btn_pay)
        act_layout.addWidget(self.btn_reschedule)
        act_layout.addWidget(self.btn_pdf)
        left_col.addWidget(action_box)
        
        content_layout.addLayout(left_col, 3)

        # -------------------------------------------------------------
        # RIGHT COLUMN: REPAYMENT SCHEDULE TABLE
        # -------------------------------------------------------------
        self.table_ledger = QTableWidget(0, 6)
        self.table_ledger.setHorizontalHeaderLabels(["No.", "Due Date", "Amount Due", "Paid Date", "Amount Paid", "Status"])
        self.table_ledger.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_ledger.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_ledger.verticalHeader().setVisible(False)
        self.table_ledger.verticalHeader().setDefaultSectionSize(38)
        self.table_ledger.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        content_layout.addWidget(self.table_ledger, 7)


        main_layout.addLayout(content_layout)

    def load_ledgers_dropdown(self, *args):
        """Syncs all sales transactions from VM to dropdown combobox asynchronously."""
        # 1. Load instantly if cached
        if self.cache_sales_list:
            self.populate_dropdown(self.cache_sales_list)
            
        # 2. Prevent concurrent list loading
        if self.list_worker and self.list_worker.isRunning():
            return
            
        # 3. Fire async worker
        self.list_worker = LedgerListWorker(self.vm)
        self.list_worker.sync_finished.connect(self.on_list_success)
        self.list_worker.sync_not_needed.connect(self.on_list_not_needed)
        self.list_worker.sync_failed.connect(self.on_list_failed)
        self.list_worker.start()

    def on_list_success(self, sales: list):
        self.cache_sales_list = sales
        CacheService.set("ledger_sales_list", sales)
        self.populate_dropdown(sales)
        print("[Ledgers List] Sales ledger list updated successfully.")

    def on_list_not_needed(self):
        pass

    def on_list_failed(self, error_msg: str):
        print(f"[Ledger List] Sync failed: {error_msg}")
        self.show_toast(f"Failed to load ledgers: {error_msg}", "error")

    def select_sale(self, sale_id: str):
        """Sets the active sale ID to be selected."""
        self.pending_sale_id = sale_id
        if self.cache_sales_list:
            exists = any(s["id"] == sale_id for s in self.cache_sales_list)
            if exists:
                self.ledg_search.set_selected_id(sale_id)
                self.pending_sale_id = None
                self.load_selected_ledger()

    def populate_dropdown(self, sales: list):
        self.ledg_search.set_sales(sales)
        
        target_sel = self.pending_sale_id or self.ledg_search.selected_id()
        
        selected_id = None
        if target_sel:
            exists = any(s["id"] == target_sel for s in sales)
            if exists:
                selected_id = target_sel
                self.pending_sale_id = None
                
        # If no target selected, select the first one by default if items exist
        if not selected_id and sales:
            selected_id = sales[0]["id"]
            
        if selected_id:
            self.ledg_search.set_selected_id(selected_id)
            
        self.load_selected_ledger()

    def load_selected_ledger(self, *args):
        """Queries detailed ledger calculations for selection asynchronously."""
        sale_id = self.ledg_search.selected_id()
        if not sale_id:
            # Clear UI metrics
            self.lbl_cust_name.setText("Customer: -")
            self.lbl_cust_father.setText("Father Name: -")
            self.lbl_cust_address.setText("Address: -")
            self.lbl_dev_name.setText("Device: -")
            self.lbl_selling_price.setText("Total Sale Price: Rs. 0.00")
            self.lbl_down_payment.setText("Down Payment: Rs. 0.00")
            self.lbl_total_paid.setText("Total Payments: Rs. 0.00")
            self.lbl_outstanding.setText("Outstanding Balance: Rs. 0.00")
            self.lbl_remaining_months.setText("Unpaid Months: 0")
            self.lbl_next_due.setText("Next Due Date: -")
            self.table_ledger.setRowCount(0)
            self.btn_pay.setEnabled(False)
            self.btn_reschedule.setEnabled(False)
            self.btn_pdf.setEnabled(False)
            return

        # Disable buttons temporarily until data is loaded
        self.btn_pay.setEnabled(False)
        self.btn_reschedule.setEnabled(False)
        self.btn_pdf.setEnabled(False)

        # 1. Populate immediately if detail cache exists
        if sale_id in self.cache_ledger_details:
            self.populate_ledger_details(self.cache_ledger_details[sale_id])

        # 2. Prevent concurrent detail workers
        if self.detail_worker and self.detail_worker.isRunning():
            self.detail_worker.terminate()
            self.detail_worker.wait()
            
        # 3. Fire async details retrieval
        self.detail_worker = LedgerDetailWorker(self.vm, sale_id)
        self.detail_worker.sync_finished.connect(self.on_detail_success)
        self.detail_worker.sync_not_needed.connect(self.on_detail_not_needed)
        self.detail_worker.sync_failed.connect(self.on_detail_failed)
        self.detail_worker.start()

    def on_detail_success(self, data: dict):
        sale_id = data["sale"]["id"]
        self.cache_ledger_details[sale_id] = data
        CacheService.set("ledger_details", self.cache_ledger_details)
        self.populate_ledger_details(data)
        print(f"[Ledger Detail: {sale_id}] Ledger details updated successfully.")

    def on_detail_not_needed(self):
        pass

    def on_detail_failed(self, error_msg: str):
        print(f"[Ledger Detail] Sync failed: {error_msg}")
        self.show_toast(f"Failed to load ledger details: {error_msg}", "error")

    def populate_ledger_details(self, data: dict):
        # Populate KPI metrics
        self.lbl_cust_name.setText(f"Customer: {data['customer']['name']}")
        self.lbl_cust_father.setText(f"Father Name: {data['customer']['father_name']}")
        self.lbl_cust_address.setText(f"Address: {data['customer']['address'] or '-'}")
        self.lbl_dev_name.setText(f"Device: {data['device']['brand']} {data['device']['model']}")
        
        self.lbl_selling_price.setText(f"Total Sale Price: {ConfigManager.format_currency(data['summary']['selling_price'])}")
        self.lbl_down_payment.setText(f"Down Payment: {ConfigManager.format_currency(data['summary']['down_payment'])}")
        self.lbl_total_paid.setText(f"Total Payments: {ConfigManager.format_currency(data['summary']['total_paid'])}")
        self.lbl_outstanding.setText(f"Outstanding Balance: {ConfigManager.format_currency(data['summary']['outstanding'])}")
        self.lbl_remaining_months.setText(f"Unpaid Months: {data['summary']['remaining_installments']}")
        
        next_due_str = "-"
        if data["summary"]["next_due"]:
            next_due_str = datetime.strptime(data["summary"]["next_due"], "%Y-%m-%d").strftime("%d-%b-%Y")
        self.lbl_next_due.setText(f"Next Due Date: {next_due_str}")
        
        # Map repayments table
        installments = data["installments"]
        payments = data["payments"]
        
        # Map payments per installment for display
        payment_map = {}
        for pay in payments:
            inst_id = pay["installment_id"]
            if inst_id not in payment_map:
                payment_map[inst_id] = []
            payment_map[inst_id].append(pay)
            
        self.table_ledger.setRowCount(0)
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        for idx, inst in enumerate(installments):
            self.table_ledger.insertRow(idx)
            
            item_no = QTableWidgetItem(str(idx + 1))
            item_no.setTextAlignment(align_left)
            item_no.setToolTip(str(idx + 1))
            self.table_ledger.setItem(idx, 0, item_no)
            
            due_dt = datetime.strptime(inst["due_date"], "%Y-%m-%d").strftime("%d-%b-%Y")
            item_due = QTableWidgetItem(due_dt)
            item_due.setTextAlignment(align_left)
            item_due.setToolTip(due_dt)
            self.table_ledger.setItem(idx, 1, item_due)
            
            formatted_amt = ConfigManager.format_currency(inst['amount'])
            item_amt = QTableWidgetItem(formatted_amt)
            item_amt.setTextAlignment(align_left)
            item_amt.setToolTip(formatted_amt)
            self.table_ledger.setItem(idx, 2, item_amt)
            
            # Payment info
            inst_pays = payment_map.get(inst["id"], [])
            if inst_pays:
                p_dates = [datetime.strptime(p["payment_date"], "%Y-%m-%d").strftime("%d-%b-%Y") for p in inst_pays]
                p_dates_str = ", ".join(p_dates)
                p_amount = sum(float(p["amount_received"]) for p in inst_pays)
                p_amount_str = ConfigManager.format_currency(p_amount)
            else:
                p_dates_str = "-"
                p_amount_str = ConfigManager.format_currency(0.0)
                
            item_pay_dates = QTableWidgetItem(p_dates_str)
            item_pay_dates.setTextAlignment(align_left)
            item_pay_dates.setToolTip(p_dates_str)
            self.table_ledger.setItem(idx, 3, item_pay_dates)
            
            item_pay_amt = QTableWidgetItem(p_amount_str)
            item_pay_amt.setTextAlignment(align_left)
            item_pay_amt.setToolTip(p_amount_str)
            self.table_ledger.setItem(idx, 4, item_pay_amt)
 
            
            # Status tag coloring
            status = inst["status"]
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(align_left)
            status_item.setToolTip(status)
            if status == "Paid":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == "Partial":
                status_item.setForeground(Qt.GlobalColor.blue)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
                
            self.table_ledger.setItem(idx, 5, status_item)


        # Enable operations buttons
        has_outstanding = data["summary"]["outstanding"] > 0
        self.btn_pay.setEnabled(has_outstanding)
        self.btn_reschedule.setEnabled(has_outstanding)
        self.btn_pdf.setEnabled(True)

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

    def collect_payment(self, *args):
        sale_id = self.ledg_search.selected_id()
        if not sale_id:
            return
            
        if sale_id not in self.cache_ledger_details:
            self.show_toast("Ledger data is still loading. Please wait.", "warning")
            return
            
        # Get next installment amount as a default value recommendation from cache
        try:
            ledger_data = self.cache_ledger_details[sale_id]
            unpaid = [inst for inst in ledger_data["installments"] if inst["status"] != "Paid"]
            default_val = 0.0
            if unpaid:
                if len(unpaid) == 1:
                    default_val = float(ledger_data["summary"]["outstanding"])
                else:
                    inst_id = unpaid[0]["id"]
                    already_paid = sum(float(p["amount_received"]) for p in ledger_data.get("payments", []) if p.get("installment_id") == inst_id)
                    default_val = float(unpaid[0]["amount"]) - already_paid
        except Exception:
            default_val = 0.0

        dialog = PaymentDialog(self, default_val)
        if dialog.exec() == PaymentDialog.DialogCode.Accepted:
            if self.payment_worker and self.payment_worker.isRunning():
                self.payment_worker.terminate()
                self.payment_worker.wait()
                
            self.payment_worker = PaymentRecordWorker(
                self.vm, sale_id, dialog.amount_received, dialog.payment_date, dialog.notes, dialog.payment_method
            )
            self.payment_worker.success.connect(lambda: self.on_payment_success(sale_id))
            self.payment_worker.failed.connect(self.on_payment_failed)
            self.payment_worker.start()

    def on_payment_success(self, sale_id: str):
        self.show_toast("Payment successfully processed and applied to the ledger.", "success")
        # Invalidate cache for this ledger and update persistent store
        if sale_id in self.cache_ledger_details:
            del self.cache_ledger_details[sale_id]
        CacheService.set("ledger_details", self.cache_ledger_details)
        self.load_selected_ledger()

    def on_payment_failed(self, error_msg: str):
        self.show_toast(f"Could not record payment:\n{error_msg}", "error")

    def export_pdf(self, *args):
        sale_id = self.ledg_search.selected_id()
        if not sale_id:
            return
            
        # Select save destination
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Customer Ledger PDF", 
            f"Ledger_{self.ledg_search.txt_search.text().split(' - ')[0].replace(' ', '_')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
            
        if self.pdf_worker and self.pdf_worker.isRunning():
            self.pdf_worker.terminate()
            self.pdf_worker.wait()
            
        self.pdf_worker = PdfExportWorker(self.vm, sale_id, file_path)
        self.pdf_worker.success.connect(self.on_pdf_success)
        self.pdf_worker.failed.connect(self.on_pdf_failed)
        self.pdf_worker.start()

    def on_pdf_success(self, file_path: str):
        self.show_toast(f"PDF Ledger successfully exported to:\n{file_path}", "success")

    def on_pdf_failed(self, error_msg: str):
        self.show_toast(f"Could not compile PDF document:\n{error_msg}", "error")

    def reschedule_ledger(self, *args):
        sale_id = self.ledg_search.selected_id()
        if not sale_id:
            return
            
        if sale_id not in self.cache_ledger_details:
            self.show_toast("Ledger data is still loading. Please wait.", "warning")
            return
            
        try:
            ledger_data = self.cache_ledger_details[sale_id]
            outstanding_bal = ledger_data["summary"]["outstanding"]
        except Exception:
            outstanding_bal = 0.0

        dialog = RescheduleDialog(self, outstanding_bal)
        if dialog.exec() == RescheduleDialog.DialogCode.Accepted:
            if self.reschedule_worker and self.reschedule_worker.isRunning():
                self.reschedule_worker.terminate()
                self.reschedule_worker.wait()
                
            self.reschedule_worker = RescheduleWorker(
                self.vm, sale_id, dialog.new_start_date, dialog.new_duration
            )
            self.reschedule_worker.success.connect(lambda: self.on_reschedule_success(sale_id))
            self.reschedule_worker.failed.connect(self.on_reschedule_failed)
            self.reschedule_worker.start()

    def on_reschedule_success(self, sale_id: str):
        self.show_toast("Installment schedule has been successfully rescheduled.", "success")
        # Invalidate cache for this ledger and update persistent store
        if sale_id in self.cache_ledger_details:
            del self.cache_ledger_details[sale_id]
        CacheService.set("ledger_details", self.cache_ledger_details)
        self.load_selected_ledger()

    def on_reschedule_failed(self, error_msg: str):
        self.show_toast(f"Could not reschedule installments:\n{error_msg}", "error")
