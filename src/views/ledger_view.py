import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QCompleter, QListWidget, QListWidgetItem, QAbstractItemView, QLineEdit, QToolButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QBuffer, QByteArray, QSize, QRect
from PyQt6.QtGui import QIcon, QPainter, QPageSize
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter, QPrintPreviewWidget
from PyQt6.QtPdf import QPdfDocument
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

    ledger_selected = pyqtSignal(str)   # emits sale_id or ""

    _POPUP_ITEM_HEIGHT = 52   # px per row

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sales: list  = []
        self._selected_id: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setFixedHeight(36)

        # Search input
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍  Type to search ledger by customer, mobile, device, or IMEI…")
        self.txt_search.setFixedHeight(36)
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.setStyleSheet(
            "QLineEdit {"
            "  background: #FFFFFF;"
            "  border: 1px solid #CBD5E1;"
            "  border-top-left-radius: 6px;"
            "  border-bottom-left-radius: 6px;"
            "  border-top-right-radius: 0px;"
            "  border-bottom-right-radius: 0px;"
            "  padding: 6px 12px;"
            "  font-size: 13px;"
            "  color: #0F172A;"
            "}"
            "QLineEdit:focus {"
            "  border: 1.5px solid #3B82F6;"
            "  border-right: none;"
            "}"
        )
        self.txt_search.textChanged.connect(self._on_text_changed)
        self.txt_search.focusOutEvent = self._on_focus_out
        self.txt_search.mousePressEvent = self._on_mouse_press
        layout.addWidget(self.txt_search)

        # Dropdown arrow button
        self.btn_dropdown = QToolButton()
        self.btn_dropdown.setText("▼")
        self.btn_dropdown.setFixedHeight(36)
        self.btn_dropdown.setFixedWidth(30)
        self.btn_dropdown.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_dropdown.setStyleSheet(
            "QToolButton {"
            "  background: #F1F5F9;"
            "  border: 1px solid #CBD5E1;"
            "  border-left: none;"
            "  border-top-right-radius: 6px;"
            "  border-bottom-right-radius: 6px;"
            "  color: #475569;"
            "  font-size: 10px;"
            "}"
            "QToolButton:hover {"
            "  background: #E2E8F0;"
            "}"
        )
        self.btn_dropdown.clicked.connect(self._toggle_popup)
        layout.addWidget(self.btn_dropdown)

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

    def _toggle_popup(self):
        if self.list_popup.isVisible():
            self._hide_popup()
        else:
            self.txt_search.setFocus()
            self._filter_popup()

    def _on_mouse_press(self, event):
        QLineEdit.mousePressEvent(self.txt_search, event)
        if not self.list_popup.isVisible():
            self._filter_popup()

    def _on_focus_out(self, event):
        # Prevent auto-hide if dropdown button is clicked (let toggle handler do the work)
        if self.btn_dropdown.underMouse():
            QLineEdit.focusOutEvent(self.txt_search, event)
            return
        QTimer.singleShot(200, self._hide_popup)
        QLineEdit.focusOutEvent(self.txt_search, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_popup_geometry()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._update_popup_geometry()

    def _update_popup_geometry(self):
        if not self.list_popup.isVisible():
            return
        win = self.window()
        if win:
            if self.list_popup.parent() != win:
                self.list_popup.setParent(win)
            pos = self.txt_search.mapTo(win, self.txt_search.rect().bottomLeft())
            visible_rows = min(max(self.list_popup.count(), 1), 5)
            self.list_popup.setGeometry(
                pos.x(),
                pos.y() + 2,
                self.width(),
                visible_rows * self._POPUP_ITEM_HEIGHT
            )
            self.list_popup.raise_()

    def set_sales(self, sales: list):
        self._sales = sales

    def selected_id(self) -> str:
        return self._selected_id

    def set_selected_id(self, sale_id: str):
        self._selected_id = sale_id
        for sale in self._sales:
            if sale["id"] == sale_id:
                formatted_price = ConfigManager.format_currency(sale['selling_price'])
                father = sale['customers'].get('father_name') or '—'
                display = f"{sale['customers']['name']} | {father} | {sale['devices']['brand']} {sale['devices']['model']} ({formatted_price})"
                self.txt_search.blockSignals(True)
                self.txt_search.setText(display)
                self.txt_search.blockSignals(False)
                break

    def clear_selection(self):
        self._selected_id = ""
        self.txt_search.clear()
        self._hide_popup()

    def _on_text_changed(self, text: str):
        if not text:
            self._selected_id = ""
            self.ledger_selected.emit("")
        self._timer.stop()
        self._timer.start(200)

    def _filter_popup(self):
        query = self.txt_search.text().strip().lower()
        self.list_popup.clear()

        # Empty or active sale format is considered "no query" to list all
        is_empty_or_selected = not query or self._selected_id
        
        matches = []
        if is_empty_or_selected:
            matches = self._sales[:10]
        else:
            for sale in self._sales:
                cust = sale.get("customers") or {}
                dev = sale.get("devices") or {}
                
                cust_name = cust.get("name", "").lower()
                father_name = cust.get("father_name", "").lower()
                mobile = cust.get("mobile", "").lower()
                address = cust.get("address", "").lower() if cust.get("address") else ""
                brand = dev.get("brand", "").lower()
                model = dev.get("model", "").lower()
                imei_1 = dev.get("imei_1", "").lower() if dev.get("imei_1") else ""
                
                if (query in cust_name or 
                    query in father_name or 
                    query in mobile or 
                    query in address or
                    query in brand or 
                    query in model or 
                    query in imei_1 or 
                    query in sale.get("id", "").lower()):
                    matches.append(sale)

        if not matches:
            item = QListWidgetItem("No matching ledgers found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_popup.addItem(item)
        else:
            for sale in matches[:20]:
                cust = sale.get("customers") or {}
                dev = sale.get("devices") or {}
                father = cust.get("father_name") or "—"
                address = cust.get("address") or "—"
                mobile = cust.get("mobile") or "—"
                
                display = f"{cust.get('name')}  |  {father}  |  {address}  |  {mobile}"

                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, sale["id"])
                item.setToolTip(
                    f"Customer: {cust.get('name')}\n"
                    f"Father:   {father}\n"
                    f"Address:  {address}\n"
                    f"Mobile:   {mobile}"
                )
                self.list_popup.addItem(item)

        win = self.window()
        if win and self.list_popup.parent() != win:
            self.list_popup.setParent(win)
        self.list_popup.show()
        self._update_popup_geometry()

    def _on_item_clicked(self, item: QListWidgetItem):
        sale_id = item.data(Qt.ItemDataRole.UserRole)
        if not sale_id:
            return
            
        self._selected_id = sale_id
        
        for sale in self._sales:
            if sale["id"] == sale_id:
                formatted_price = ConfigManager.format_currency(sale['selling_price'])
                father = sale['customers'].get('father_name') or '—'
                display = f"{sale['customers']['name']} | {father} | {sale['devices']['brand']} {sale['devices']['model']} ({formatted_price})"
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
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Title / Search section
        search_panel = QFrame()
        search_panel.setObjectName("topnav")
        search_panel.setFixedHeight(60)
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(12, 12, 12, 12)
        
        search_layout.addWidget(QLabel("Select Active Ledger / Sale:"))
        self.ledg_search = LedgerSearchWidget()
        self.ledg_search.setFixedWidth(550)
        self.ledg_search.ledger_selected.connect(self.load_selected_ledger)
        search_layout.addWidget(self.ledg_search)
        
        self.btn_refresh = QPushButton("Refresh Ledgers")
        self.btn_refresh.setObjectName("btn_secondary")
        self.btn_refresh.setFixedHeight(36)
        self.btn_refresh.setIconSize(QSize(16, 16))
        icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
        self.btn_refresh.setIcon(QIcon(os.path.join(icons_dir, "refresh.svg")))
        self.btn_refresh.clicked.connect(self.load_ledgers_dropdown)
        search_layout.addWidget(self.btn_refresh)
        
        search_layout.addStretch()
        main_layout.addWidget(search_panel)

        # Main Layout splitter
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # -------------------------------------------------------------
        # LEFT COLUMN: LEDGER AND CUSTOMER SUMMARY CARDS
        # -------------------------------------------------------------
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # Summary Info Box
        self.summary_box = QFrame()
        self.summary_box.setObjectName("form_card")
        self.summary_box.setFixedWidth(300)
        sum_layout = QVBoxLayout(self.summary_box)
        sum_layout.setSpacing(12)
        
        lbl_sum_title = QLabel("Ledger Balance Sheet")
        lbl_sum_title.setObjectName("lbl_section_title")
        sum_layout.addWidget(lbl_sum_title)

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
        self.lbl_selling_date = QLabel("Selling Date: -")
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
        sum_layout.addWidget(create_metric_row("calendar", self.lbl_selling_date))
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
        act_layout.setSpacing(12)
        
        self.btn_pay = QPushButton("Collect Installment Payment")
        self.btn_pay.clicked.connect(self.collect_payment)
        self.btn_pay.setEnabled(False)
        
        self.btn_reschedule = QPushButton("Reschedule Remaining Balance")
        self.btn_reschedule.clicked.connect(self.reschedule_ledger)
        self.btn_reschedule.setEnabled(False)

        self.btn_pdf = QPushButton("Export Customer Ledger (PDF)")
        self.btn_pdf.clicked.connect(self.export_pdf)
        self.btn_pdf.setEnabled(False)

        self.btn_print = QPushButton("Preview Ledger")
        self.btn_print.clicked.connect(self.print_ledger)
        self.btn_print.setEnabled(False)

        button_style_template = (
            "QPushButton {{"
            "  background-color: {bg_color};"
            "  color: #FFFFFF;"
            "  text-align: left;"
            "  padding-left: 20px;"
            "  font-weight: bold;"
            "  border-radius: 6px;"
            "  height: 32px;"
            "  border: none;"
            "}}"
            "QPushButton:hover {{"
            "  background-color: {hover_color};"
            "}}"
            "QPushButton:pressed {{"
            "  background-color: {pressed_color};"
            "}}"
            "QPushButton:disabled {{"
            "  background-color: #E2E8F0;"
            "  color: #94A3B8;"
            "}}"
        )

        self.btn_pay.setStyleSheet(button_style_template.format(
            bg_color="#10B981", hover_color="#059669", pressed_color="#047857"
        ))
        self.btn_reschedule.setStyleSheet(button_style_template.format(
            bg_color="#6366F1", hover_color="#4F46E5", pressed_color="#3730A3"
        ))
        self.btn_pdf.setStyleSheet(button_style_template.format(
            bg_color="#0EA5E9", hover_color="#0284C7", pressed_color="#0369A1"
        ))
        self.btn_print.setStyleSheet(button_style_template.format(
            bg_color="#8B5CF6", hover_color="#7C3AED", pressed_color="#6D28D9"
        ))

        # Set white icons to render clearly inside colored buttons
        icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
        self.btn_pay.setIcon(QIcon(os.path.join(icons_dir, "coins_white.svg")))
        self.btn_reschedule.setIcon(QIcon(os.path.join(icons_dir, "calendar_white.svg")))
        self.btn_pdf.setIcon(QIcon(os.path.join(icons_dir, "checklist_white.svg")))
        self.btn_print.setIcon(QIcon(os.path.join(icons_dir, "eye_white.svg")))

        # Set standard icon sizes to fit neatly inside 32px height buttons
        icon_size = QSize(16, 16)
        self.btn_pay.setIconSize(icon_size)
        self.btn_reschedule.setIconSize(icon_size)
        self.btn_pdf.setIconSize(icon_size)
        self.btn_print.setIconSize(icon_size)

        act_layout.addWidget(self.btn_pay)
        act_layout.addWidget(self.btn_reschedule)
        act_layout.addWidget(self.btn_pdf)
        act_layout.addWidget(self.btn_print)
        left_col.addWidget(action_box)
        
        content_layout.addLayout(left_col, 3)

        # -------------------------------------------------------------
        # RIGHT COLUMN: REPAYMENT SCHEDULE TABLE
        # -------------------------------------------------------------
        self.table_ledger = QTableWidget(0, 6)
        self.table_ledger.setHorizontalHeaderLabels(["No.", "Due Date", "Amount Due", "Paid Date", "Amount Paid", "Status"])
        self.table_ledger.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_ledger.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Right align financial column headers
        hdr_amt_due = self.table_ledger.horizontalHeaderItem(2)
        if hdr_amt_due:
            hdr_amt_due.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hdr_amt_paid = self.table_ledger.horizontalHeaderItem(4)
        if hdr_amt_paid:
            hdr_amt_paid.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
        self.table_ledger.verticalHeader().setVisible(False)
        self.table_ledger.verticalHeader().setDefaultSectionSize(38)
        self.table_ledger.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_ledger.setSortingEnabled(False)
        
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
            self.lbl_selling_date.setText("Selling Date: -")
            self.lbl_selling_price.setText("Total Sale Price: Rs. 0.00")
            self.lbl_down_payment.setText("Down Payment: Rs. 0.00")
            self.lbl_total_paid.setText("Total Payments: Rs. 0.00")
            self.lbl_outstanding.setText("Outstanding Balance: Rs. 0.00")
            self.lbl_remaining_months.setText("Unpaid Months: 0")
            self.lbl_next_due.setText("Next Due Date: -")
            
            # Show guidelines empty state on table
            from src.views.components.q_placeholder import show_empty_table_message
            show_empty_table_message(self.table_ledger, "Please search and select a customer ledger using the search bar above\nto view their payment schedule.")
            
            self.btn_pay.setEnabled(False)
            self.btn_reschedule.setEnabled(False)
            self.btn_pdf.setEnabled(False)
            self.btn_print.setEnabled(False)
            return

        # Disable buttons temporarily until data is loaded
        self.btn_pay.setEnabled(False)
        self.btn_reschedule.setEnabled(False)
        self.btn_pdf.setEnabled(False)
        self.btn_print.setEnabled(False)

        # 1. Populate immediately if detail cache exists
        if sale_id in self.cache_ledger_details:
            self.populate_ledger_details(self.cache_ledger_details[sale_id])

        # 2. Prevent concurrent detail workers
        if self.detail_worker and self.detail_worker.isRunning():
            if self.detail_worker.sale_id == sale_id:
                return
            try:
                self.detail_worker.sync_finished.disconnect()
                self.detail_worker.sync_not_needed.disconnect()
                self.detail_worker.sync_failed.disconnect()
            except TypeError:
                pass
            
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
        
        selling_date_str = "-"
        if data["sale"].get("start_date"):
            try:
                selling_date_str = datetime.strptime(data["sale"]["start_date"], "%Y-%m-%d").strftime("%d-%b-%Y")
            except Exception:
                selling_date_str = str(data["sale"]["start_date"])
        self.lbl_selling_date.setText(f"Selling Date: {selling_date_str}")
        
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
        installments = sorted(data["installments"], key=lambda x: x["due_date"])
        payments = data["payments"]
        
        self.table_ledger.setSortingEnabled(False)
        self.table_ledger.setRowCount(0)
        
        if not installments:
            from src.views.components.q_placeholder import show_empty_table_message
            show_empty_table_message(self.table_ledger, "No installment schedules generated for this ledger.")
            return

        # Map payments per installment for display
        payment_map = {}
        for pay in payments:
            inst_id = pay["installment_id"]
            if inst_id not in payment_map:
                payment_map[inst_id] = []
            payment_map[inst_id].append(pay)
            
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        align_right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        for idx, inst in enumerate(installments):
            self.table_ledger.insertRow(idx)
            
            item_no = QTableWidgetItem()
            item_no.setData(Qt.ItemDataRole.EditRole, idx + 1)
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
            item_amt.setTextAlignment(align_right)
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
            item_pay_amt.setTextAlignment(align_right)
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
        self.table_ledger.setSortingEnabled(False)


        # Enable operations buttons
        has_outstanding = data["summary"]["outstanding"] > 0
        self.btn_pay.setEnabled(has_outstanding)
        self.btn_reschedule.setEnabled(has_outstanding)
        self.btn_pdf.setEnabled(True)
        self.btn_print.setEnabled(True)

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
        raw_text = self.ledg_search.txt_search.text()
        parts = [p.strip() for p in raw_text.split('|') if p.strip()]
        
        if parts:
            cust_name = parts[0].replace(' ', '_')
            if len(parts) > 1 and parts[1] != '—':
                father_name = parts[1].replace(' ', '_')
                default_filename = f"Ledger_{cust_name}_{father_name}.pdf"
            else:
                default_filename = f"Ledger_{cust_name}.pdf"
        else:
            default_filename = "Ledger_Report.pdf"
            
        # Remove any invalid OS filename characters
        for char in '<>:"/\\|?*':
            default_filename = default_filename.replace(char, '')

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Customer Ledger PDF", 
            default_filename,
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

    def print_ledger(self, *args):
        sale_id = self.ledg_search.selected_id()
        if not sale_id:
            return
            
        import tempfile
        # Create a temp file path in the OS temp directory
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            file_path = temp_file.name
            temp_file.close() # Close so background thread can write to it on Windows
        except Exception as e:
            self.show_toast(f"Failed to create temporary file:\n{str(e)}", "error")
            return
            
        if self.pdf_worker and self.pdf_worker.isRunning():
            self.pdf_worker.terminate()
            self.pdf_worker.wait()
            
        self.pdf_worker = PdfExportWorker(self.vm, sale_id, file_path)
        self.pdf_worker.success.connect(self.on_print_success)
        self.pdf_worker.failed.connect(self.on_pdf_failed)
        self.pdf_worker.start()

    def on_pdf_success(self, file_path: str):
        self.show_toast(f"PDF Ledger successfully exported to:\n{file_path}", "success")

    def on_print_success(self, file_path: str):
        try:
            # Read all bytes from the temporary file
            with open(file_path, "rb") as f:
                pdf_data = f.read()
            
            # Immediately delete the temporary file
            try:
                os.unlink(file_path)
            except Exception as ex:
                print(f"Failed to delete temp file {file_path}: {ex}")
                
            # Launch in-memory preview & print dialog
            self.show_print_preview(pdf_data)
        except Exception as e:
            self.show_toast(f"Could not load PDF file for preview:\n{str(e)}", "error")

    def show_print_preview(self, pdf_data: bytes):
        # Load PDF in-memory and keep references alive on self during exec
        self._preview_pdf_doc = QPdfDocument(None)
        self._preview_buffer = QBuffer()
        self._preview_buffer.setData(QByteArray(pdf_data))
        self._preview_buffer.open(QBuffer.OpenModeFlag.ReadOnly)
        
        self._preview_pdf_doc.load(self._preview_buffer)
        if self._preview_pdf_doc.status() != QPdfDocument.Status.Ready:
            self.show_toast("Failed to parse PDF document for printing preview.", "error")
            self._preview_pdf_doc = None
            self._preview_buffer = None
            return
            
        # Create print preview dialog
        preview = QPrintPreviewDialog(self)
        preview.setWindowTitle("Print Preview - Customer Ledger")
        
        # Apply specific stylesheet override to restore toolbar widget proportions and colors
        preview.setStyleSheet("""
            QPrintPreviewDialog {
                background-color: #F8FAFC;
            }
            QPrintPreviewDialog QToolBar {
                background-color: #1E293B;
                border-bottom: 1px solid #0F172A;
                spacing: 4px;
                padding: 4px;
            }
            QPrintPreviewDialog QLabel {
                color: #F8FAFC;
                font-weight: bold;
                font-size: 12px;
                padding: 0 4px;
            }
            QPrintPreviewDialog QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 24px 2px 6px;
                color: #0F172A;
                min-width: 85px;
                height: 24px;
                font-size: 12px;
            }
            QPrintPreviewDialog QComboBox::drop-down {
                border: none;
                width: 20px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }
            QPrintPreviewDialog QComboBox::down-arrow {
                border-top: 5px solid #475569;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                width: 0;
                height: 0;
                margin-right: 6px;
            }
            QPrintPreviewDialog QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 6px;
                color: #0F172A;
                height: 24px;
                font-size: 12px;
            }
            QPrintPreviewDialog QToolButton {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px;
                background-color: transparent;
            }
            QPrintPreviewDialog QToolButton:hover {
                background-color: #334155;
            }
            QPrintPreviewDialog QToolButton:pressed, QPrintPreviewDialog QToolButton:checked {
                background-color: #2563EB;
            }
        """)
        
        # Configure printer settings
        printer = preview.printer()
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
        
        # Auto-zoom to perfect width for readability
        preview_widget = preview.findChild(QPrintPreviewWidget)
        if preview_widget:
            preview_widget.setZoomMode(QPrintPreviewWidget.ZoomMode.FitToWidth)
            
        # Define paint callback
        def paint_pdf(p_target: QPrinter):
            painter = QPainter(p_target)
            if not painter.isActive():
                return
                
            page_count = self._preview_pdf_doc.pageCount()
            for page_idx in range(page_count):
                if page_idx > 0:
                    p_target.newPage()
                    
                # PDF page size in points (1 pt = 1/72 inch)
                pdf_page_size = self._preview_pdf_doc.pagePointSize(page_idx)
                
                # Render page at 300 DPI for crystal clear text (independent of screen resolution)
                target_dpi = 300
                render_w = int(pdf_page_size.width() * target_dpi / 72.0)
                render_h = int(pdf_page_size.height() * target_dpi / 72.0)
                
                image = self._preview_pdf_doc.render(page_idx, QSize(render_w, render_h))
                
                # Get printable area dimensions in pixels at current resolution
                page_rect = p_target.pageLayout().paintRectPixels(p_target.resolution())
                
                # Fit aspect ratio
                scale_x = page_rect.width() / pdf_page_size.width()
                scale_y = page_rect.height() / pdf_page_size.height()
                scale = min(scale_x, scale_y)
                
                paint_w = int(pdf_page_size.width() * scale)
                paint_h = int(pdf_page_size.height() * scale)
                
                # Center the page image
                x_offset = page_rect.left() + (page_rect.width() - paint_w) // 2
                y_offset = page_rect.top() + (page_rect.height() - paint_h) // 2
                
                # Draw high-resolution image scaled down to the target display rect
                painter.drawImage(QRect(x_offset, y_offset, paint_w, paint_h), image)
                
            painter.end()
            
        preview.paintRequested.connect(paint_pdf)
        preview.exec()
        
        # Clean up references after execution finishes
        self._preview_pdf_doc = None
        self._preview_buffer = None

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
