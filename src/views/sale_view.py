from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit, 
    QComboBox, QPushButton, QDateEdit, QMessageBox, QFormLayout, QGridLayout,
    QCompleter
)
from PyQt6.QtCore import QDate, Qt, QThread, pyqtSignal
from src.viewmodels.sale_viewmodel import SaleViewModel
from src.viewmodels.customer_viewmodel import CustomerViewModel
from src.viewmodels.device_viewmodel import DeviceViewModel
from src.services.cache_service import CacheService

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
            changed_dev = CacheService.check_and_update_state("devices", self.dev_vm.repo.db)
            has_cache = (
                CacheService.get("sale_customers") is not None and
                CacheService.get("sale_devices") is not None
            )
            if not changed_cust and not changed_dev and has_cache:
                print("[Sales Form] No database changes detected. Loading sales dropdowns from persistent cache.")
                self.sync_not_needed.emit()
                return

            print("[Sales Form] Database changes detected. Fetching fresh customers and devices for dropdowns...")
            customers = self.cust_vm.get_all_customers()
            devices = self.dev_vm.get_all_devices()
            self.sync_finished.emit(customers, devices)
        except Exception as e:
            self.sync_failed.emit(str(e))


class SaleView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = SaleViewModel()
        self.cust_vm = CustomerViewModel()
        self.dev_vm = DeviceViewModel()
        
        # Load cache from persistent storage
        self.cache_customers = CacheService.get("sale_customers")
        self.cache_devices = CacheService.get("sale_devices")
        self.worker = None
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Title
        lbl_title = QLabel("Create Installment Sale Transaction")
        lbl_title.setObjectName("lbl_title")
        main_layout.addWidget(lbl_title)

        # Form Wrapper Box
        form_card = QFrame()
        form_card.setObjectName("form_card")
        form_layout = QHBoxLayout(form_card)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(30)

        # -------------------------------------------------------------
        # LEFT COLUMN: INPUTS
        # -------------------------------------------------------------
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Customer selection
        left_layout.addWidget(QLabel("Select Customer *"))
        self.cmb_customer = QComboBox()
        self.cmb_customer.setEditable(True)
        self.cmb_customer.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cmb_customer.setFixedHeight(35)
        if self.cmb_customer.completer():
            self.cmb_customer.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            self.cmb_customer.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        left_layout.addWidget(self.cmb_customer)

        # Device selection
        left_layout.addWidget(QLabel("Select Device *"))
        self.cmb_device = QComboBox()
        self.cmb_device.setEditable(True)
        self.cmb_device.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cmb_device.setFixedHeight(35)
        if self.cmb_device.completer():
            self.cmb_device.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            self.cmb_device.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        left_layout.addWidget(self.cmb_device)

        # Financial Inputs Grid
        fin_grid = QGridLayout()
        fin_grid.setSpacing(10)

        # Cost Price
        fin_grid.addWidget(QLabel("Cost Price (Rs.) *"), 0, 0)
        self.txt_cost_price = QLineEdit()
        self.txt_cost_price.setPlaceholderText("0.00")
        self.txt_cost_price.textChanged.connect(self.update_live_calculators)
        fin_grid.addWidget(self.txt_cost_price, 1, 0)

        # Selling Price
        fin_grid.addWidget(QLabel("Selling Price (Rs.) *"), 0, 1)
        self.txt_selling_price = QLineEdit()
        self.txt_selling_price.setPlaceholderText("0.00")
        self.txt_selling_price.textChanged.connect(self.update_live_calculators)
        fin_grid.addWidget(self.txt_selling_price, 1, 1)

        # Down Payment
        fin_grid.addWidget(QLabel("Down Payment (Rs.) *"), 2, 0)
        self.txt_down_payment = QLineEdit()
        self.txt_down_payment.setPlaceholderText("0.00")
        self.txt_down_payment.textChanged.connect(self.update_live_calculators)
        fin_grid.addWidget(self.txt_down_payment, 3, 0)

        # Duration
        fin_grid.addWidget(QLabel("Duration (Months) *"), 2, 1)
        self.txt_duration = QLineEdit()
        self.txt_duration.setPlaceholderText("e.g. 10")
        self.txt_duration.textChanged.connect(self.update_live_calculators)
        fin_grid.addWidget(self.txt_duration, 3, 1)

        # Start Date
        fin_grid.addWidget(QLabel("Start Date *"), 4, 0)
        self.txt_start_date = QDateEdit()
        self.txt_start_date.setCalendarPopup(True)
        self.txt_start_date.setDate(QDate.currentDate())
        self.txt_start_date.setFixedHeight(30)
        fin_grid.addWidget(self.txt_start_date, 5, 0)

        left_layout.addLayout(fin_grid)
        form_layout.addWidget(left_column, 6)

        # -------------------------------------------------------------
        # RIGHT COLUMN: REALTIME CALCULATOR METRICS
        # -------------------------------------------------------------
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Margin Card Box
        self.margin_box = QFrame()
        self.margin_box.setObjectName("metric_card")
        margin_layout = QVBoxLayout(self.margin_box)
        margin_layout.setContentsMargins(15, 15, 15, 15)
        
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

        # Installment Calculator Card Box
        self.inst_box = QFrame()
        self.inst_box.setObjectName("metric_card")
        inst_layout = QVBoxLayout(self.inst_box)
        inst_layout.setContentsMargins(15, 15, 15, 15)
        
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

        # Commit button
        self.btn_create_sale = QPushButton("Create Sale & Generate Schedule")
        self.btn_create_sale.setFixedHeight(40)
        self.btn_create_sale.clicked.connect(self.create_sale)
        right_layout.addWidget(self.btn_create_sale)

        right_layout.addStretch()
        form_layout.addWidget(right_column, 4)

        main_layout.addWidget(form_card)
        main_layout.addStretch()

    def load_dropdowns_data(self):
        """Loads customer names and devices from VM asynchronously."""
        # 1. Populate from cache immediately if available
        if self.cache_customers and self.cache_devices:
            self.populate_dropdowns(self.cache_customers, self.cache_devices)

        # 2. Prevent concurrent task runs
        if self.worker and self.worker.isRunning():
            return
            
        # 3. Fire async background task
        self.worker = SaleViewWorker(self.cust_vm, self.dev_vm)
        self.worker.sync_finished.connect(self.on_load_success)
        self.worker.sync_not_needed.connect(self.on_load_not_needed)
        self.worker.sync_failed.connect(self.on_load_failed)
        self.worker.start()

    def on_load_success(self, customers: list, devices: list):
        self.cache_customers = customers
        self.cache_devices = devices
        CacheService.set("sale_customers", customers)
        CacheService.set("sale_devices", devices)
        self.populate_dropdowns(customers, devices)
        print("[Sales Form] Sales selection dropdowns updated successfully.")

    def on_load_not_needed(self):
        pass

    def on_load_failed(self, error_msg: str):
        print(f"Sale View sync failed: {error_msg}")

    def populate_dropdowns(self, customers: list, devices: list):
        # Cache active indices
        prev_cust = self.cmb_customer.currentData()
        prev_dev = self.cmb_device.currentData()
        
        self.cmb_customer.clear()
        self.cmb_device.clear()
        
        for cust in customers:
            self.cmb_customer.addItem(f"{cust['name']} ({cust['mobile']})", cust["id"])
            
        for dev in devices:
            self.cmb_device.addItem(f"{dev['name']} ({dev['brand']} {dev['model']})", dev["id"])

        # Restore index choices
        if prev_cust:
            idx = self.cmb_customer.findData(prev_cust)
            if idx >= 0:
                self.cmb_customer.setCurrentIndex(idx)
        if prev_dev:
            idx = self.cmb_device.findData(prev_dev)
            if idx >= 0:
                self.cmb_device.setCurrentIndex(idx)

    def update_live_calculators(self, *args):
        """Monitors inputs and triggers live UI recalculations."""
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

        # Margin calculations
        margin_amt, margin_pct = self.vm.calculate_margin(selling, cost)
        self.lbl_margin_val.setText(f"Rs. {margin_amt:,.2f}")
        self.lbl_margin_pct.setText(f"{margin_pct:,.2f} %")

        # Installment calculations
        inst_amt = self.vm.calculate_monthly_installment(selling, down, duration)
        remaining = max(0.0, selling - down)
        
        self.lbl_inst_val.setText(f"Rs. {inst_amt:,.2f}")
        self.lbl_inst_desc.setText(f"Remaining: Rs. {remaining:,.2f} over {duration} months")

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

    def create_sale(self, *args):
        cust_idx = self.cmb_customer.currentIndex()
        dev_idx = self.cmb_device.currentIndex()
        
        if cust_idx < 0 or dev_idx < 0:
            self.show_toast("Please select a Customer and a Device.", "warning")
            return
            
        customer_id = self.cmb_customer.currentData()
        device_id = self.cmb_device.currentData()
        
        try:
            cost = float(self.txt_cost_price.text().strip() or "0")
            selling = float(self.txt_selling_price.text().strip() or "0")
            down = float(self.txt_down_payment.text().strip() or "0")
            duration = int(self.txt_duration.text().strip() or "0")
        except ValueError:
            self.show_toast("Please make sure cost, selling, down payment and duration contain numeric entries.", "warning")
            return

        start_date = self.txt_start_date.date().toPyDate().strftime("%Y-%m-%d")

        self.btn_create_sale.setEnabled(False)
        self.btn_create_sale.setText("Generating schedule...")

        try:
            self.vm.commit_sale(
                customer_id, device_id, cost, selling, down, duration, start_date
            )
            self.show_toast("The sale has been successfully recorded, and the monthly installment schedule generated.", "success")
            
            # Reset UI
            self.txt_cost_price.clear()
            self.txt_selling_price.clear()
            self.txt_down_payment.clear()
            self.txt_duration.clear()
            self.txt_start_date.setDate(QDate.currentDate())
            self.update_live_calculators()
            
            # Clear caches to enforce update on next activations
            self.cache_customers = None
            self.cache_devices = None
            
        except ValueError as ve:
            self.show_toast(str(ve), "warning")
            self.btn_create_sale.setEnabled(True)
            self.btn_create_sale.setText("Create Sale & Generate Schedule")
        except Exception as e:
            self.show_toast(f"Failed to finalize sale:\n{e}", "error")
            self.btn_create_sale.setEnabled(True)
            self.btn_create_sale.setText("Create Sale & Generate Schedule")
