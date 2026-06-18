from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from src.viewmodels.customer_viewmodel import CustomerViewModel
from src.services.cache_service import CacheService

class CustomerWorker(QThread):
    sync_finished = pyqtSignal(list)
    sync_not_needed = pyqtSignal()
    sync_failed = pyqtSignal(str)

    def __init__(self, vm: CustomerViewModel, query: str = None):
        super().__init__()
        self.vm = vm
        self.query = query

    def run(self):
        try:
            if self.query is not None:
                print(f"[Customers] Querying search for query: '{self.query}'")
                customers = self.vm.search_customers(self.query)
                self.sync_finished.emit(customers)
            else:
                changed = CacheService.check_and_update_state("customers", self.vm.repo.db)
                has_cache = CacheService.get("customers") is not None
                if not changed and has_cache:
                    print("[Customers] No database changes detected. Loading customer records from persistent cache.")
                    self.sync_not_needed.emit()
                    return

                print("[Customers] Database changes detected. Updating customer records from database...")
                customers = self.vm.get_all_customers()
                self.sync_finished.emit(customers)
        except Exception as e:
            self.sync_failed.emit(str(e))


class CustomerView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = CustomerViewModel()
        self.cache_customers = CacheService.get("customers")
        self.worker = None


        self.active_workers = []
        self.current_search_query = ""
        self.current_edit_customer_id = None
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # -------------------------------------------------------------
        # 1. LEFT SIDE: ADD CUSTOMER FORM
        # -------------------------------------------------------------
        form_card = QFrame()
        form_card.setObjectName("form_card")
        form_card.setFixedWidth(320)
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(10)
        
        self.lbl_form_title = QLabel("Register New Customer")
        self.lbl_form_title.setObjectName("lbl_section_title")
        form_layout.addWidget(self.lbl_form_title)
        
        # Form Fields
        form_layout.addWidget(QLabel("Full Name *"))
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Muhammad Ali")
        form_layout.addWidget(self.txt_name)
        
        form_layout.addWidget(QLabel("Father Name *"))
        self.txt_father_name = QLineEdit()
        self.txt_father_name.setPlaceholderText("e.g. Muhammad Hussain")
        form_layout.addWidget(self.txt_father_name)
        
        form_layout.addWidget(QLabel("Mobile Number *"))
        self.txt_mobile = QLineEdit()
        self.txt_mobile.setPlaceholderText("e.g. 03001234567")
        form_layout.addWidget(self.txt_mobile)
        
        form_layout.addWidget(QLabel("Residential Address"))
        self.txt_address = QTextEdit()
        self.txt_address.setPlaceholderText("Enter complete address...")
        self.txt_address.setMaximumHeight(80)
        form_layout.addWidget(self.txt_address)
        
        form_layout.addWidget(QLabel("Remarks / Notes"))
        self.txt_remarks = QTextEdit()
        self.txt_remarks.setPlaceholderText("Any references or observations...")
        self.txt_remarks.setMaximumHeight(60)
        form_layout.addWidget(self.txt_remarks)

        # Reminders Radio Buttons (On / Off)
        form_layout.addWidget(QLabel("Reminders / Alerts"))
        self.radio_reminders_on = QRadioButton("On")
        self.radio_reminders_off = QRadioButton("Off")
        self.radio_reminders_on.setChecked(True)
        
        self.reminders_group = QButtonGroup(self)
        self.reminders_group.addButton(self.radio_reminders_on)
        self.reminders_group.addButton(self.radio_reminders_off)
        
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_reminders_on)
        radio_layout.addWidget(self.radio_reminders_off)
        form_layout.addLayout(radio_layout)
        
        # Submit & Cancel Button Row
        btn_layout = QHBoxLayout()
        self.btn_submit = QPushButton("Save Customer")
        self.btn_submit.clicked.connect(self.save_customer)
        btn_layout.addWidget(self.btn_submit)
        
        self.btn_cancel_edit = QPushButton("Cancel")
        self.btn_cancel_edit.setObjectName("btn_secondary")
        self.btn_cancel_edit.clicked.connect(self.cancel_edit)
        self.btn_cancel_edit.setVisible(False)
        btn_layout.addWidget(self.btn_cancel_edit)
        form_layout.addLayout(btn_layout)
        
        form_layout.addStretch()
        main_layout.addWidget(form_card)

        # -------------------------------------------------------------
        # 2. RIGHT SIDE: SEARCH AND VIEW CUSTOMERS
        # -------------------------------------------------------------
        list_container = QFrame()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search panel
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search by Name or Mobile...")
        self.txt_search.textChanged.connect(self.search_customers)
        search_layout.addWidget(self.txt_search)
        
        self.btn_refresh = QPushButton("Refresh List")
        self.btn_refresh.setObjectName("btn_secondary")
        self.btn_refresh.clicked.connect(self.load_customers)
        search_layout.addWidget(self.btn_refresh)
        list_layout.addLayout(search_layout)
 
        # Customers table
        self.table_customers = QTableWidget(0, 5)
        self.table_customers.setHorizontalHeaderLabels(["Name", "Father Name", "Mobile", "Address", "Reminders"])
        self.table_customers.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_customers.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_customers.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_customers.doubleClicked.connect(self.on_table_double_clicked)
        list_layout.addWidget(self.table_customers)
        main_layout.addWidget(list_container, 7)


        # Populate cache immediately if available
        if self.cache_customers:
            self.populate_table(self.cache_customers)


    def load_customers(self, *args):
        """Fetches all customer records from VM asynchronously."""
        # 1. Populates cached items instantly if available
        if self.cache_customers:
            self.populate_table(self.cache_customers)

        # 2. Cancel previous worker if running
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        self.txt_search.clear()
        
        # 3. Fire async call to Supabase
        self.worker = CustomerWorker(self.vm)
        self.worker.sync_finished.connect(self.on_load_success)
        self.worker.sync_not_needed.connect(self.on_load_not_needed)
        self.worker.sync_failed.connect(self.on_load_failed)
        self.worker.start()

    def search_customers(self, *args):
        """Fires live searches based on input text asynchronously with debouncing."""
        query = self.txt_search.text().strip()
        self.current_search_query = query
        self.search_timer.stop()
        self.search_timer.start(300)

    def perform_search(self):
        query = self.current_search_query
        worker = CustomerWorker(self.vm, query)
        self.active_workers.append(worker)
        worker.sync_finished.connect(lambda customers: self.on_search_success(customers, query))
        worker.finished.connect(lambda: self.active_workers.remove(worker) if worker in self.active_workers else None)
        worker.start()

    def on_search_success(self, customers, query):
        if query == self.current_search_query:
            self.populate_table(customers)
            if not customers and query:
                self.show_toast(f'No customer record found for "{query}".', "warning")

    def on_load_success(self, customers: list):
        self.cache_customers = customers
        CacheService.set("customers", customers)
        self.populate_table(customers)
        print("[Customers] Customer records updated successfully.")

    def on_load_not_needed(self):
        pass

    def on_load_failed(self, error_msg: str):
        # Silently degrade if network drops, keeping cached logs alive
        print(f"Customer load failed: {error_msg}")

    def populate_table(self, customers):
        self.table_customers.setRowCount(0)
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        for idx, cust in enumerate(customers):
            self.table_customers.insertRow(idx)
            
            item_name = QTableWidgetItem(cust["name"])
            item_father = QTableWidgetItem(cust["father_name"])
            item_mobile = QTableWidgetItem(cust["mobile"])
            item_address = QTableWidgetItem(cust["address"] or "-")
            rem_val = cust.get("reminders_enabled", True)
            item_reminders = QTableWidgetItem("On" if rem_val else "Off")
            
            item_name.setTextAlignment(align_left)
            item_father.setTextAlignment(align_left)
            item_mobile.setTextAlignment(align_left)
            item_address.setTextAlignment(align_left)
            item_reminders.setTextAlignment(align_left)
            
            self.table_customers.setItem(idx, 0, item_name)
            self.table_customers.setItem(idx, 1, item_father)
            self.table_customers.setItem(idx, 2, item_mobile)
            self.table_customers.setItem(idx, 3, item_address)
            self.table_customers.setItem(idx, 4, item_reminders)

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

    def save_customer(self, *args):
        name = self.txt_name.text().strip()
        father = self.txt_father_name.text().strip()
        mobile = self.txt_mobile.text().strip()
        address = self.txt_address.toPlainText().strip()
        remarks = self.txt_remarks.toPlainText().strip()
        reminders_enabled = self.radio_reminders_on.isChecked()
        
        self.btn_submit.setEnabled(False)
        self.btn_submit.setText("Updating..." if self.current_edit_customer_id else "Saving...")
        
        try:
            reminders_status = "On" if reminders_enabled else "Off"
            if self.current_edit_customer_id:
                self.vm.update_customer(self.current_edit_customer_id, name, father, mobile, address, remarks, reminders_enabled)
                self.show_toast(f"Customer details updated successfully. Reminders: {reminders_status}", "success")
            else:
                self.vm.register_customer(name, father, mobile, address, remarks, reminders_enabled)
                self.show_toast(f"Customer registered successfully. Reminders: {reminders_status}", "success")
            
            # Reset Form
            self.cancel_edit()
            
            # Refresh List
            self.load_customers()
        except ValueError as ve:
            self.show_toast(str(ve), "warning")
            self.btn_submit.setEnabled(True)
            self.btn_submit.setText("Update Customer" if self.current_edit_customer_id else "Save Customer")
        except Exception as e:
            self.show_toast(f"Failed to save customer record:\n{e}", "error")
            self.btn_submit.setEnabled(True)
            self.btn_submit.setText("Update Customer" if self.current_edit_customer_id else "Save Customer")

    def cancel_edit(self):
        self.current_edit_customer_id = None
        self.txt_name.clear()
        self.txt_father_name.clear()
        self.txt_mobile.clear()
        self.txt_address.clear()
        self.txt_remarks.clear()
        self.radio_reminders_on.setChecked(True)
        
        self.lbl_form_title.setText("Register New Customer")
        self.btn_submit.setText("Save Customer")
        self.btn_submit.setEnabled(True)
        self.btn_cancel_edit.setVisible(False)

    def on_table_double_clicked(self, model_index):
        row = model_index.row()
        customers = self.cache_customers
        if not customers or row >= len(customers):
            return
            
        cust = customers[row]
        self.current_edit_customer_id = cust["id"]
        
        self.txt_name.setText(cust["name"])
        self.txt_father_name.setText(cust["father_name"])
        self.txt_mobile.setText(cust["mobile"])
        self.txt_address.setPlainText(cust["address"] or "")
        self.txt_remarks.setPlainText(cust["remarks"] or "")
        
        rem_val = cust.get("reminders_enabled", True)
        if rem_val:
            self.radio_reminders_on.setChecked(True)
        else:
            self.radio_reminders_off.setChecked(True)
        
        self.lbl_form_title.setText("Edit Customer Details")
        self.btn_submit.setText("Update Customer")
        self.btn_submit.setEnabled(True)
        self.btn_cancel_edit.setVisible(True)
