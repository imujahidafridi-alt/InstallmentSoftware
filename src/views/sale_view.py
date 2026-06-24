from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit,
    QComboBox, QPushButton, QDateEdit, QMessageBox, QGridLayout,
    QListWidget, QListWidgetItem, QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import QDate, Qt, QThread, pyqtSignal, QTimer
from src.viewmodels.sale_viewmodel import SaleViewModel
from src.viewmodels.customer_viewmodel import CustomerViewModel
from src.viewmodels.device_viewmodel import DeviceViewModel
from src.services.cache_service import CacheService
from src.config import ConfigManager
from src.views.components.search_select_widget import SearchSelectWidget



class SaleViewWorker(QThread):
    sync_finished = pyqtSignal(list, list)
    sync_not_needed = pyqtSignal()
    sync_failed = pyqtSignal(str)

    def __init__(self, cust_vm: CustomerViewModel, dev_vm: DeviceViewModel):
        super().__init__()
        self.cust_vm = cust_vm
        self.dev_vm = dev_vm

    def run(self):
        try:
            changed_cust = CacheService.check_and_update_state("customers", self.cust_vm.repo.db)
            changed_dev  = CacheService.check_and_update_state("devices",   self.dev_vm.repo.db)
            changed_sales = CacheService.check_and_update_state("sales",     self.dev_vm.repo.db)
            has_cache = (
                CacheService.get("sale_customers") is not None and
                CacheService.get("sale_devices")   is not None
            )
            if not changed_cust and not changed_dev and not changed_sales and has_cache:
                print("[Sales Form] No database changes detected. Loading sales dropdowns from persistent cache.")
                self.sync_not_needed.emit()
                return

            print("[Sales Form] Database changes detected. Fetching fresh customers and devices for dropdowns...")
            customers = self.cust_vm.get_all_customers()
            devices   = self.dev_vm.get_available_devices()
            self.sync_finished.emit(customers, devices)
        except Exception as e:
            self.sync_failed.emit(str(e))


class SaleCommitWorker(QThread):
    success = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, vm: SaleViewModel, customer_id: str, device_id: str, cost: float, selling: float, down: float, duration: int, start_date: str):
        super().__init__()
        self.vm = vm
        self.customer_id = customer_id
        self.device_id = device_id
        self.cost = cost
        self.selling = selling
        self.down = down
        self.duration = duration
        self.start_date = start_date

    def run(self):
        try:
            res = self.vm.commit_sale(
                self.customer_id, self.device_id, self.cost,
                self.selling, self.down, self.duration, self.start_date
            )
            self.success.emit(res)
        except Exception as e:
            self.failed.emit(str(e))


class CustomerSearchWidget(SearchSelectWidget):
    """
    A styled inline customer-search field utilizing the reusable SearchSelectWidget.
    """
    customer_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(placeholder="Type to search customer…", parent=parent)
        self.item_selected.connect(self.customer_selected.emit)

    def set_customers(self, customers: list):
        self.set_items(customers)

    def filter_items(self, query: str, items: list) -> list:
        if not query:
            return items
        return [
            c for c in items
            if query in c.get("name", "").lower()
            or query in c.get("father_name", "").lower()
            or query in c.get("mobile", "").lower()
            or query in (c.get("address") or "").lower()
        ]

    def format_item(self, cust) -> tuple:
        father  = cust.get("father_name") or "—"
        address = (cust.get("address") or "—")
        if len(address) > 35:
            address = address[:35] + "…"
        phone   = cust.get("mobile", "—")
        display = f"{cust['name']}  /  {father}  /  {address}  /  {phone}"
        
        tooltip = (
            f"Name:    {cust['name']}\n"
            f"Father:  {father}\n"
            f"Address: {cust.get('address') or '—'}\n"
            f"Mobile:  {phone}"
        )
        return display, tooltip, cust["id"]


class DeviceSearchWidget(SearchSelectWidget):
    """
    A styled inline device-search field utilizing the reusable SearchSelectWidget.
    """
    device_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(placeholder="Type to search device by name, model or IMEI…", parent=parent)
        self.item_selected.connect(self.device_selected.emit)

    def set_devices(self, devices: list):
        self.set_items(devices)

    def filter_items(self, query: str, items: list) -> list:
        if not query:
            return items
        return [
            d for d in items
            if query in d.get("name", "").lower()
            or query in d.get("brand", "").lower()
            or query in d.get("model", "").lower()
            or query in d.get("ram", "").lower()
            or query in d.get("rom", "").lower()
            or query in (d.get("imei_1") or "").lower()
            or query in (d.get("imei_2") or "").lower()
        ]

    def format_item(self, dev) -> tuple:
        name = dev.get("name")
        brand = dev.get("brand") or "—"
        model = dev.get("model") or "—"
        ram_rom = f"{dev.get('ram', '—')} / {dev.get('rom', '—')}"
        imei_1 = dev.get("imei_1")
        if imei_1 and imei_1.startswith("00"):
            display_imei_1 = "N/A"
        else:
            display_imei_1 = imei_1 or "N/A"

        imeis = [display_imei_1]
        for i in range(2, 5):
            val = dev.get(f"imei_{i}")
            if val:
                imeis.append(val)
        imei_str = ", ".join(filter(None, imeis))
        display = f"{name}  /  {brand} {model}  /  {ram_rom}  /  IMEI: {display_imei_1}"
        
        tooltip = (
            f"Name:    {name}\n"
            f"Brand/Model:  {brand} {model}\n"
            f"RAM/ROM: {ram_rom}\n"
            f"IMEIs:   {imei_str}"
        )
        return display, tooltip, dev["id"]




# ─────────────────────────────────────────────────────────────────────────────

class SaleView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm       = SaleViewModel()
        self.cust_vm  = CustomerViewModel()
        self.dev_vm   = DeviceViewModel()

        # Load cache from persistent storage
        self.cache_customers = CacheService.get("sale_customers")
        self.cache_devices   = CacheService.get("sale_devices")
        self.worker = None
        self.commit_worker = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Title
        lbl_title = QLabel("Create Installment Sale Transaction")
        lbl_title.setObjectName("lbl_title")
        main_layout.addWidget(lbl_title)

        # Form Wrapper Box
        form_card = QFrame()
        form_card.setObjectName("form_card")
        form_layout = QHBoxLayout(form_card)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(32)

        # ─── LEFT COLUMN ─────────────────────────────────────────────
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Customer search
        left_layout.addWidget(QLabel("Select Customer *"))
        self.cust_search = CustomerSearchWidget()
        left_layout.addWidget(self.cust_search)

        # Device selection (search widget style)
        left_layout.addWidget(QLabel("Select Device *"))
        self.dev_search = DeviceSearchWidget()
        left_layout.addWidget(self.dev_search)

        # Financial Inputs Grid
        fin_grid = QGridLayout()
        fin_grid.setSpacing(12)

        fin_grid.addWidget(QLabel("Cost Price (Rs.) *"), 0, 0)
        self.txt_cost_price = QLineEdit()
        self.txt_cost_price.setPlaceholderText("0.00")
        self.txt_cost_price.textChanged.connect(self.update_live_calculators)
        fin_grid.addWidget(self.txt_cost_price, 1, 0)

        fin_grid.addWidget(QLabel("Selling Price (Rs.) *"), 0, 1)
        self.txt_selling_price = QLineEdit()
        self.txt_selling_price.setPlaceholderText("0.00")
        self.txt_selling_price.textChanged.connect(self.update_live_calculators)
        fin_grid.addWidget(self.txt_selling_price, 1, 1)

        fin_grid.addWidget(QLabel("Down Payment (Rs.) *"), 2, 0)
        self.txt_down_payment = QLineEdit()
        self.txt_down_payment.setPlaceholderText("0.00")
        self.txt_down_payment.textChanged.connect(self.update_live_calculators)
        fin_grid.addWidget(self.txt_down_payment, 3, 0)

        fin_grid.addWidget(QLabel("Duration (Months) *"), 2, 1)
        self.txt_duration = QLineEdit()
        self.txt_duration.setPlaceholderText("e.g. 10")
        self.txt_duration.textChanged.connect(self.update_live_calculators)
        fin_grid.addWidget(self.txt_duration, 3, 1)

        fin_grid.addWidget(QLabel("Start Date *"), 4, 0)
        self.txt_start_date = QDateEdit()
        self.txt_start_date.setCalendarPopup(True)
        self.txt_start_date.setDate(QDate.currentDate())
        self.txt_start_date.setFixedHeight(30)
        fin_grid.addWidget(self.txt_start_date, 5, 0)

        left_layout.addLayout(fin_grid)
        form_layout.addWidget(left_column, 6)

        # ─── RIGHT COLUMN ─────────────────────────────────────────────
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setSpacing(16)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Margin Card
        self.margin_box = QFrame()
        self.margin_box.setObjectName("metric_card")
        margin_layout = QVBoxLayout(self.margin_box)
        margin_layout.setContentsMargins(16, 16, 16, 16)

        lbl_margin_title = QLabel("REAL-TIME PROFIT MARGIN")
        lbl_margin_title.setObjectName("lbl_metric_title")
        self.lbl_margin_val = QLabel("Rs. 0.00")
        self.lbl_margin_val.setObjectName("lbl_metric_value")
        self.lbl_margin_pct = QLabel("0.00 %")
        self.lbl_margin_pct.setObjectName("lbl_metric_title")

        margin_layout.addWidget(lbl_margin_title)
        margin_layout.addWidget(self.lbl_margin_val)
        margin_layout.addWidget(self.lbl_margin_pct)
        right_layout.addWidget(self.margin_box)

        # Installment Card
        self.inst_box = QFrame()
        self.inst_box.setObjectName("metric_card")
        inst_layout = QVBoxLayout(self.inst_box)
        inst_layout.setContentsMargins(16, 16, 16, 16)

        lbl_inst_title = QLabel("ESTIMATED MONTHLY INSTALLMENT")
        lbl_inst_title.setObjectName("lbl_metric_title")
        self.lbl_inst_val = QLabel("Rs. 0.00")
        self.lbl_inst_val.setObjectName("lbl_metric_value")
        self.lbl_inst_desc = QLabel("Remaining: Rs. 0.00")
        self.lbl_inst_desc.setObjectName("lbl_metric_title")

        inst_layout.addWidget(lbl_inst_title)
        inst_layout.addWidget(self.lbl_inst_val)
        inst_layout.addWidget(self.lbl_inst_desc)
        right_layout.addWidget(self.inst_box)

        # Submit button
        self.btn_create_sale = QPushButton("Complete Sale Order")
        self.btn_create_sale.setFixedHeight(40)
        self.btn_create_sale.clicked.connect(self.create_sale)
        right_layout.addWidget(self.btn_create_sale)

        right_layout.addStretch()
        form_layout.addWidget(right_column, 4)

        main_layout.addWidget(form_card)
        main_layout.addStretch()

    # ─────────────────────────────────────────────────────────────────
    # Data loading
    # ─────────────────────────────────────────────────────────────────

    def load_dropdowns_data(self):
        """Loads customer names and devices from VM asynchronously."""
        if self.cache_customers and self.cache_devices:
            self.populate_dropdowns(self.cache_customers, self.cache_devices)

        if self.worker and self.worker.isRunning():
            return

        self.worker = SaleViewWorker(self.cust_vm, self.dev_vm)
        self.worker.sync_finished.connect(self.on_load_success)
        self.worker.sync_not_needed.connect(self.on_load_not_needed)
        self.worker.sync_failed.connect(self.on_load_failed)
        self.worker.start()

    def on_load_success(self, customers: list, devices: list):
        self.cache_customers = customers
        self.cache_devices   = devices
        CacheService.set("sale_customers", customers)
        CacheService.set("sale_devices",   devices)
        self.populate_dropdowns(customers, devices)
        print("[Sales Form] Sales selection dropdowns updated successfully.")

    def on_load_not_needed(self):
        pass

    def on_load_failed(self, error_msg: str):
        print(f"Sale View sync failed: {error_msg}")

    def populate_dropdowns(self, customers: list, devices: list):
        # Feed customers into the search widget
        self.cust_search.set_customers(customers)

        # Feed devices into the search widget
        self.dev_search.set_devices(devices)

    # ─────────────────────────────────────────────────────────────────
    # Live calculators
    # ─────────────────────────────────────────────────────────────────

    def update_live_calculators(self, *args):
        try:
            cost = float(self.txt_cost_price.text().strip() or "0")
        except ValueError:
            cost = 0.0
        try:
            selling = float(self.txt_selling_price.text().strip() or "0")
        except ValueError:
            selling = 0.0
        try:
            down = float(self.txt_down_payment.text().strip() or "0")
        except ValueError:
            down = 0.0
        try:
            duration = int(self.txt_duration.text().strip() or "0")
        except ValueError:
            duration = 0

        margin_amt, margin_pct = self.vm.calculate_margin(selling, cost)
        self.lbl_margin_val.setText(ConfigManager.format_currency(margin_amt))
        self.lbl_margin_pct.setText(f"{margin_pct:,.2f} %")

        inst_amt  = self.vm.calculate_monthly_installment(selling, down, duration)
        remaining = max(0.0, selling - down)
        self.lbl_inst_val.setText(ConfigManager.format_currency(inst_amt))
        self.lbl_inst_desc.setText(f"Remaining: {ConfigManager.format_currency(remaining)} over {duration} months")

    # ─────────────────────────────────────────────────────────────────
    # Toast helper
    # ─────────────────────────────────────────────────────────────────

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

    # ─────────────────────────────────────────────────────────────────
    # Sale submission
    # ─────────────────────────────────────────────────────────────────

    def create_sale(self, *args):
        customer_id = self.cust_search.selected_id()
        device_id   = self.dev_search.selected_id()

        if not customer_id:
            self.show_toast("Please select a Customer from the search suggestions.", "warning")
            return
        if not device_id:
            self.show_toast("Please select a Device from the search suggestions.", "warning")
            return

        try:
            cost     = float(self.txt_cost_price.text().strip()    or "0")
            selling  = float(self.txt_selling_price.text().strip()  or "0")
            down     = float(self.txt_down_payment.text().strip()   or "0")
            duration = int(self.txt_duration.text().strip()         or "0")
        except ValueError:
            self.show_toast(
                "Please make sure cost, selling, down payment and duration contain numeric entries.",
                "warning"
            )
            return

        start_date = self.txt_start_date.date().toPyDate().strftime("%Y-%m-%d")

        # Terminate any running commit worker
        if self.commit_worker and self.commit_worker.isRunning():
            self.commit_worker.terminate()
            self.commit_worker.wait()

        self.btn_create_sale.setEnabled(False)
        self.btn_create_sale.setText("Generating schedule...")

        self.commit_worker = SaleCommitWorker(
            self.vm, customer_id, device_id, cost, selling, down, duration, start_date
        )
        self.commit_worker.success.connect(self.on_sale_success)
        self.commit_worker.failed.connect(self.on_sale_failed)
        self.commit_worker.start()

    def on_sale_success(self, result: dict):
        self.show_toast(
            "The sale has been successfully recorded, and the monthly installment schedule generated.",
            "success"
        )

        # Reset UI
        self.cust_search.clear_selection()
        self.dev_search.clear_selection()
        self.txt_cost_price.clear()
        self.txt_selling_price.clear()
        self.txt_down_payment.clear()
        self.txt_duration.clear()
        self.txt_start_date.setDate(QDate.currentDate())
        self.update_live_calculators()

        # Clear caches to enforce update on next activations
        self.cache_customers = None
        self.cache_devices   = None

        self.btn_create_sale.setEnabled(True)
        self.btn_create_sale.setText("Complete Sale Order")

    def on_sale_failed(self, error_msg: str):
        self.show_toast(f"Failed to finalize sale:\n{error_msg}", "error")
        self.btn_create_sale.setEnabled(True)
        self.btn_create_sale.setText("Complete Sale Order")
