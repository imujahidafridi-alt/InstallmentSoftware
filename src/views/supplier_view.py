from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QTabWidget, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from src.viewmodels.supplier_viewmodel import SupplierViewModel
from src.viewmodels.device_viewmodel import DeviceViewModel
from src.services.cache_service import CacheService

class SupplierWorker(QThread):
    sync_finished = pyqtSignal(list)
    sync_not_needed = pyqtSignal()
    sync_failed = pyqtSignal(str)

    def __init__(self, vm: SupplierViewModel, query: str = None):
        super().__init__()
        self.vm = vm
        self.query = query

    def run(self):
        try:
            if self.query is not None:
                print(f"[Suppliers] Querying search for query: '{self.query}'")
                suppliers = self.vm.search_suppliers(self.query)
                self.sync_finished.emit(suppliers)
            else:
                changed = CacheService.check_and_update_state("suppliers", self.vm.repo.db)
                has_cache = CacheService.get("suppliers") is not None
                if not changed and has_cache:
                    print("[Suppliers] No database changes detected. Loading supplier records from persistent cache.")
                    self.sync_not_needed.emit()
                    return

                print("[Suppliers] Database changes detected. Updating supplier records from database...")
                suppliers = self.vm.get_all_suppliers()
                self.sync_finished.emit(suppliers)
        except Exception as e:
            self.sync_failed.emit(str(e))


class SupplierSaveWorker(QThread):
    success = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, vm: SupplierViewModel, supplier_id: Optional[str], name: str, contact_person: str, mobile: str, address: str, remarks: str):
        super().__init__()
        self.vm = vm
        self.supplier_id = supplier_id
        self.name = name
        self.contact_person = contact_person
        self.mobile = mobile
        self.address = address
        self.remarks = remarks

    def run(self):
        try:
            if self.supplier_id:
                self.vm.update_supplier(
                    self.supplier_id, self.name, self.contact_person, self.mobile,
                    self.address, self.remarks
                )
                self.success.emit("Supplier details updated successfully.")
            else:
                self.vm.register_supplier(
                    self.name, self.contact_person, self.mobile,
                    self.address, self.remarks
                )
                self.success.emit("Supplier registered successfully.")
        except Exception as e:
            self.failed.emit(str(e))


class SupplierDeleteWorker(QThread):
    success = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, vm: SupplierViewModel, supplier_id: str):
        super().__init__()
        self.vm = vm
        self.supplier_id = supplier_id

    def run(self):
        try:
            self.vm.delete_supplier(self.supplier_id)
            self.success.emit()
        except Exception as e:
            self.failed.emit(str(e))


class ImeiLookupWorker(QThread):
    finished = pyqtSignal(dict, bool)  # device dict, is_sold bool
    not_found = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, device_vm: DeviceViewModel, imei: str):
        super().__init__()
        self.device_vm = device_vm
        self.imei = imei

    def run(self):
        try:
            # Search devices matching this IMEI
            devices = self.device_vm.search_devices(self.imei)
            matched_device = None
            for d in devices:
                if (d.get("imei_1") == self.imei or 
                    d.get("imei_2") == self.imei or 
                    d.get("imei_3") == self.imei or 
                    d.get("imei_4") == self.imei):
                    matched_device = d
                    break
            
            # Fallback if query returns a specific device
            if not matched_device and devices:
                matched_device = devices[0]

            if matched_device:
                is_sold = self.device_vm.is_device_sold(matched_device["id"])
                self.finished.emit(matched_device, is_sold)
            else:
                self.not_found.emit(self.imei)
        except Exception as e:
            self.failed.emit(str(e))


class SupplierView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = SupplierViewModel()
        self.device_vm = DeviceViewModel()
        self.cache_suppliers = CacheService.get("suppliers")
        
        self.active_workers = []
        self.worker = None
        self.save_worker = None
        self.delete_worker = None
        self.lookup_worker = None
        
        self.current_search_query = ""
        self.current_edit_supplier_id = None
        self.displayed_suppliers = []
        
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Title / Header Section
        header_layout = QHBoxLayout()
        lbl_title = QLabel("Suppliers & Device IMEI Lookup")
        lbl_title.setObjectName("lbl_title")
        header_layout.addWidget(lbl_title)
        
        self.lbl_status = QLabel("Up to date")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #10B981; font-weight: bold;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.lbl_status)
        main_layout.addLayout(header_layout)

        # QTabWidget grouping Lookup and Directory
        self.tab_widget = QTabWidget()
        
        # --- TAB 1: IMEI LOOKUP ---
        self.tab_lookup = QWidget()
        self.setup_lookup_tab()
        self.tab_widget.addTab(self.tab_lookup, "IMEI Supplier Lookup")
        
        # --- TAB 2: SUPPLIER DIRECTORY ---
        self.tab_directory = QWidget()
        self.setup_directory_tab()
        self.tab_widget.addTab(self.tab_directory, "Supplier Directory")
        
        main_layout.addWidget(self.tab_widget)

        # Initial populate from cache if exists
        if self.cache_suppliers:
            self.populate_table(self.cache_suppliers)

    def setup_lookup_tab(self):
        layout = QVBoxLayout(self.tab_lookup)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Description
        lbl_desc = QLabel("Enter or scan a device IMEI to retrieve the supplier from whom it was purchased.")
        lbl_desc.setStyleSheet("color: #64748B; font-size: 12px;")
        layout.addWidget(lbl_desc)

        # Search box QFrame
        search_card = QFrame()
        search_card.setObjectName("form_card")
        search_card_layout = QHBoxLayout(search_card)
        search_card_layout.setContentsMargins(16, 12, 16, 12)
        search_card_layout.setSpacing(12)
        
        lbl_imei_prompt = QLabel("Scan/Enter IMEI:")
        lbl_imei_prompt.setStyleSheet("font-weight: bold;")
        search_card_layout.addWidget(lbl_imei_prompt)
        
        self.txt_lookup_imei = QLineEdit()
        self.txt_lookup_imei.setPlaceholderText("Enter 15-digit IMEI number...")
        self.txt_lookup_imei.setMaxLength(15)
        self.txt_lookup_imei.setFixedHeight(35)
        self.txt_lookup_imei.returnPressed.connect(self.lookup_imei)
        search_card_layout.addWidget(self.txt_lookup_imei)
        
        self.btn_lookup = QPushButton("Lookup Supplier")
        self.btn_lookup.setFixedHeight(35)
        self.btn_lookup.clicked.connect(self.lookup_imei)
        search_card_layout.addWidget(self.btn_lookup)
        
        layout.addWidget(search_card)

        # Result Frame
        self.result_card = QFrame()
        self.result_card.setObjectName("form_card")
        self.result_card_layout = QVBoxLayout(self.result_card)
        self.result_card_layout.setContentsMargins(20, 20, 20, 20)
        self.result_card_layout.setSpacing(16)
        
        # Result label initial placeholder
        self.lbl_placeholder = QLabel("Scan or enter an IMEI number in the field above to search device and supplier details.")
        self.lbl_placeholder.setStyleSheet("color: #94A3B8; font-size: 14px;")
        self.lbl_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_card_layout.addWidget(self.lbl_placeholder)
        
        # Grid details layout (will show/hide based on result)
        self.details_widget = QWidget()
        self.details_grid = QGridLayout(self.details_widget)
        self.details_grid.setSpacing(12)
        self.details_grid.setContentsMargins(0, 0, 0, 0)
        
        # Device details card
        self.lbl_dev_title = QLabel("Device Details")
        self.lbl_dev_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #1E293B; border-bottom: 2px solid #E2E8F0; padding-bottom: 4px;")
        self.details_grid.addWidget(self.lbl_dev_title, 0, 0, 1, 2)
        
        self.lbl_dev_name_tag = QLabel("Device Name:")
        self.lbl_dev_name_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_dev_name = QLabel("-")
        self.lbl_dev_name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_grid.addWidget(self.lbl_dev_name_tag, 1, 0)
        self.details_grid.addWidget(self.lbl_dev_name, 1, 1)

        self.lbl_brand_model_tag = QLabel("Brand / Model:")
        self.lbl_brand_model_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_brand_model = QLabel("-")
        self.lbl_brand_model.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_grid.addWidget(self.lbl_brand_model_tag, 2, 0)
        self.details_grid.addWidget(self.lbl_brand_model, 2, 1)

        self.lbl_specs_tag = QLabel("RAM / ROM:")
        self.lbl_specs_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_specs = QLabel("-")
        self.lbl_specs.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_grid.addWidget(self.lbl_specs_tag, 3, 0)
        self.details_grid.addWidget(self.lbl_specs, 3, 1)

        self.lbl_sims_tag = QLabel("SIM Type / slots:")
        self.lbl_sims_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_sims = QLabel("-")
        self.details_grid.addWidget(self.lbl_sims_tag, 4, 0)
        self.details_grid.addWidget(self.lbl_sims, 4, 1)

        self.lbl_sale_status_tag = QLabel("Inventory Status:")
        self.lbl_sale_status_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_sale_status = QLabel("-")
        self.lbl_sale_status.setStyleSheet("font-weight: bold;")
        self.details_grid.addWidget(self.lbl_sale_status_tag, 5, 0)
        self.details_grid.addWidget(self.lbl_sale_status, 5, 1)
        
        # Supplier details card
        self.lbl_supp_title = QLabel("Supplier Information")
        self.lbl_supp_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #1E293B; border-bottom: 2px solid #E2E8F0; padding-bottom: 4px;")
        self.details_grid.addWidget(self.lbl_supp_title, 0, 2, 1, 2)
        
        self.lbl_supp_name_tag = QLabel("Supplier Name:")
        self.lbl_supp_name_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_supp_name = QLabel("-")
        self.lbl_supp_name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_grid.addWidget(self.lbl_supp_name_tag, 1, 2)
        self.details_grid.addWidget(self.lbl_supp_name, 1, 3)

        self.lbl_supp_contact_tag = QLabel("Contact Person:")
        self.lbl_supp_contact_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_supp_contact = QLabel("-")
        self.lbl_supp_contact.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_grid.addWidget(self.lbl_supp_contact_tag, 2, 2)
        self.details_grid.addWidget(self.lbl_supp_contact, 2, 3)

        self.lbl_supp_mobile_tag = QLabel("Mobile Number:")
        self.lbl_supp_mobile_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_supp_mobile = QLabel("-")
        self.lbl_supp_mobile.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details_grid.addWidget(self.lbl_supp_mobile_tag, 3, 2)
        self.details_grid.addWidget(self.lbl_supp_mobile, 3, 3)

        self.lbl_supp_address_tag = QLabel("Supplier Address:")
        self.lbl_supp_address_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_supp_address = QLabel("-")
        self.lbl_supp_address.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_supp_address.setWordWrap(True)
        self.details_grid.addWidget(self.lbl_supp_address_tag, 4, 2)
        self.details_grid.addWidget(self.lbl_supp_address, 4, 3)

        self.lbl_supp_remarks_tag = QLabel("Remarks:")
        self.lbl_supp_remarks_tag.setStyleSheet("color: #64748B; font-weight: bold;")
        self.lbl_supp_remarks = QLabel("-")
        self.lbl_supp_remarks.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_supp_remarks.setWordWrap(True)
        self.details_grid.addWidget(self.lbl_supp_remarks_tag, 5, 2)
        self.details_grid.addWidget(self.lbl_supp_remarks, 5, 3)

        # Set column stretch to divide into 2 columns equally
        self.details_grid.setColumnStretch(1, 1)
        self.details_grid.setColumnStretch(3, 1)

        self.details_widget.setVisible(False)
        self.result_card_layout.addWidget(self.details_widget)
        layout.addWidget(self.result_card)
        layout.addStretch()

    def setup_directory_tab(self):
        layout = QHBoxLayout(self.tab_directory)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ----------------- LEFT SIDE: CRUD FORM -----------------
        form_card = QFrame()
        form_card.setObjectName("form_card")
        form_card.setFixedWidth(320)
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(8)

        self.lbl_form_title = QLabel("Add New Supplier")
        self.lbl_form_title.setObjectName("lbl_section_title")
        form_layout.addWidget(self.lbl_form_title)

        form_layout.addWidget(QLabel("Supplier Name *"))
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Khalid Electronics")
        form_layout.addWidget(self.txt_name)

        form_layout.addWidget(QLabel("Contact Person"))
        self.txt_contact_person = QLineEdit()
        self.txt_contact_person.setPlaceholderText("e.g. Muhammad Khalid")
        form_layout.addWidget(self.txt_contact_person)

        form_layout.addWidget(QLabel("Mobile Number *"))
        self.txt_mobile = QLineEdit()
        self.txt_mobile.setPlaceholderText("e.g. 03001234567")
        self.txt_mobile.setMaxLength(11)
        form_layout.addWidget(self.txt_mobile)

        form_layout.addWidget(QLabel("Address"))
        self.txt_address = QTextEdit()
        self.txt_address.setPlaceholderText("Supplier business address details...")
        self.txt_address.setMaximumHeight(80)
        form_layout.addWidget(self.txt_address)

        form_layout.addWidget(QLabel("Remarks"))
        self.txt_remarks = QTextEdit()
        self.txt_remarks.setPlaceholderText("Other details, bank accounts, terms...")
        self.txt_remarks.setMaximumHeight(80)
        form_layout.addWidget(self.txt_remarks)

        # Submit Button
        self.btn_submit = QPushButton("Save Supplier")
        self.btn_submit.clicked.connect(self.save_supplier)
        form_layout.addWidget(self.btn_submit)

        # Cancel Edit Button
        self.btn_cancel_edit = QPushButton("Cancel Edit")
        self.btn_cancel_edit.setObjectName("btn_secondary")
        self.btn_cancel_edit.clicked.connect(self.cancel_edit)
        self.btn_cancel_edit.setVisible(False)
        form_layout.addWidget(self.btn_cancel_edit)

        # Delete Button
        self.btn_delete = QPushButton("Delete Supplier")
        self.btn_delete.setObjectName("btn_danger")
        self.btn_delete.setStyleSheet("background-color: #EF4444; color: white;")
        self.btn_delete.clicked.connect(self.delete_supplier)
        self.btn_delete.setVisible(False)
        form_layout.addWidget(self.btn_delete)

        form_layout.addStretch()
        layout.addWidget(form_card)

        # ----------------- RIGHT SIDE: LIST TABLE -----------------
        list_container = QFrame()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)

        # Search controls
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search by Name, Contact Person, Mobile...")
        self.txt_search.textChanged.connect(self.search_suppliers)
        search_layout.addWidget(self.txt_search)

        self.btn_refresh = QPushButton("Refresh List")
        self.btn_refresh.setObjectName("btn_secondary")
        self.btn_refresh.clicked.connect(self.load_suppliers)
        search_layout.addWidget(self.btn_refresh)
        list_layout.addLayout(search_layout)

        # Table
        self.table_suppliers = QTableWidget(0, 5)
        self.table_suppliers.setHorizontalHeaderLabels(["S.No", "Supplier Name", "Contact Person", "Mobile", "Address"])
        self.table_suppliers.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_suppliers.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_suppliers.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_suppliers.verticalHeader().setVisible(False)
        self.table_suppliers.verticalHeader().setDefaultSectionSize(38)
        self.table_suppliers.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_suppliers.setSortingEnabled(False)
        self.table_suppliers.doubleClicked.connect(self.on_table_double_clicked)
        list_layout.addWidget(self.table_suppliers)

        layout.addWidget(list_container, 7)

    # -----------------------------------------------------------------
    # IMEI LOOKUP FUNCTIONALITY
    # -----------------------------------------------------------------
    def lookup_imei(self):
        imei = self.txt_lookup_imei.text().strip()
        if not imei:
            self.show_toast("Please enter an IMEI number to lookup.", "warning")
            return
        
        if len(imei) != 15 or not imei.isdigit():
            self.show_toast("IMEI must be exactly 15 numeric digits.", "warning")
            return

        self.btn_lookup.setEnabled(False)
        self.btn_lookup.setText("Searching...")
        
        if self.lookup_worker and self.lookup_worker.isRunning():
            self.lookup_worker.terminate()
            self.lookup_worker.wait()

        self.lookup_worker = ImeiLookupWorker(self.device_vm, imei)
        self.lookup_worker.finished.connect(self.on_lookup_success)
        self.lookup_worker.not_found.connect(self.on_lookup_not_found)
        self.lookup_worker.failed.connect(self.on_lookup_failed)
        self.lookup_worker.start()

    def on_lookup_success(self, device: dict, is_sold: bool):
        self.btn_lookup.setEnabled(True)
        self.btn_lookup.setText("Lookup Supplier")
        
        self.lbl_placeholder.setVisible(False)
        self.details_widget.setVisible(True)

        # Update Device details
        self.lbl_dev_name.setText(device.get("name", "-"))
        self.lbl_brand_model.setText(f"{device.get('brand', '-')} / {device.get('model', '-')}")
        self.lbl_specs.setText(f"{device.get('ram', '-')} / {device.get('rom', '-')}")
        self.lbl_sims.setText(f"{device.get('sim_type', 1)} SIM slots")

        if is_sold:
            self.lbl_sale_status.setText("Sold (Out of Inventory)")
            self.lbl_sale_status.setStyleSheet("font-weight: bold; color: #EF4444;")
        else:
            self.lbl_sale_status.setText("Available (In Inventory)")
            self.lbl_sale_status.setStyleSheet("font-weight: bold; color: #10B981;")

        # Update Supplier details
        supplier = device.get("suppliers")
        if supplier:
            self.lbl_supp_name.setText(supplier.get("name", "-"))
            self.lbl_supp_contact.setText(supplier.get("contact_person") or "N/A")
            self.lbl_supp_mobile.setText(supplier.get("mobile", "-"))
            self.lbl_supp_address.setText(supplier.get("address") or "N/A")
            self.lbl_supp_remarks.setText(supplier.get("remarks") or "N/A")
        else:
            self.lbl_supp_name.setText("None Linked")
            self.lbl_supp_contact.setText("N/A")
            self.lbl_supp_mobile.setText("N/A")
            self.lbl_supp_address.setText("N/A")
            self.lbl_supp_remarks.setText("This device was registered without linking to a supplier.")

    def on_lookup_not_found(self, imei: str):
        self.btn_lookup.setEnabled(True)
        self.btn_lookup.setText("Lookup Supplier")
        
        self.details_widget.setVisible(False)
        self.lbl_placeholder.setVisible(True)
        self.lbl_placeholder.setText(f"No device registered with IMEI '{imei}' found in the system.")
        self.lbl_placeholder.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: bold;")
        self.show_toast(f"No registered device found for IMEI '{imei}'.", "warning")

    def on_lookup_failed(self, error_msg: str):
        self.btn_lookup.setEnabled(True)
        self.btn_lookup.setText("Lookup Supplier")
        self.show_toast(f"An error occurred during lookup:\n{error_msg}", "error")

    # -----------------------------------------------------------------
    # CRUD SUPPLIER FUNCTIONALITY
    # -----------------------------------------------------------------
    def load_suppliers(self, *args):
        """Fetches all suppliers asynchronously."""
        if self.cache_suppliers:
            self.populate_table(self.cache_suppliers)

        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        self.txt_search.clear()
        self.lbl_status.setText("Checking database...")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #64748B;")

        self.worker = SupplierWorker(self.vm)
        self.worker.sync_finished.connect(self.on_load_success)
        self.worker.sync_not_needed.connect(self.on_load_not_needed)
        self.worker.sync_failed.connect(self.on_load_failed)
        self.worker.start()

    def on_load_success(self, suppliers: list):
        self.cache_suppliers = suppliers
        CacheService.set("suppliers", suppliers)
        if not self.current_search_query:
            self.populate_table(suppliers)
        self.lbl_status.setText("Up to date")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #10B981; font-weight: bold;")

    def on_load_not_needed(self):
        self.lbl_status.setText("Up to date (Cache)")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #10B981; font-weight: bold;")

    def on_load_failed(self, error_msg: str):
        self.lbl_status.setText("Sync offline")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #EF4444; font-weight: bold;")
        print(f"Supplier load failed: {error_msg}")

    def search_suppliers(self, *args):
        query = self.txt_search.text().strip()
        self.current_search_query = query
        self.search_timer.stop()
        self.search_timer.start(300)

    def perform_search(self):
        query = self.current_search_query
        worker = SupplierWorker(self.vm, query)
        self.active_workers.append(worker)
        worker.sync_finished.connect(lambda suppliers: self.on_search_success(suppliers, query))
        worker.finished.connect(lambda: self.active_workers.remove(worker) if worker in self.active_workers else None)
        worker.start()

    def on_search_success(self, suppliers: list, query: str):
        if query == self.current_search_query:
            self.populate_table(suppliers)

    def populate_table(self, suppliers: list):
        self.displayed_suppliers = []
        self.table_suppliers.setRowCount(0)

        if not suppliers:
            from src.views.components.q_placeholder import show_empty_table_message
            if self.current_search_query:
                show_empty_table_message(self.table_suppliers, f"No matching suppliers found for '{self.current_search_query}'.")
            else:
                show_empty_table_message(self.table_suppliers, "No registered suppliers.\nAdd a supplier using the form on the left.")
            return

        row_idx = 0
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        align_center = Qt.AlignmentFlag.AlignCenter

        for supplier in suppliers:
            self.displayed_suppliers.append(supplier)
            self.table_suppliers.insertRow(row_idx)

            # S.No
            item_sno = QTableWidgetItem(str(row_idx + 1))
            item_sno.setTextAlignment(align_center)
            self.table_suppliers.setItem(row_idx, 0, item_sno)

            # Supplier Name
            item_name = QTableWidgetItem(supplier["name"])
            item_name.setTextAlignment(align_left)
            self.table_suppliers.setItem(row_idx, 1, item_name)

            # Contact Person
            item_contact = QTableWidgetItem(supplier.get("contact_person") or "-")
            item_contact.setTextAlignment(align_left)
            self.table_suppliers.setItem(row_idx, 2, item_contact)

            # Mobile
            item_mobile = QTableWidgetItem(supplier["mobile"])
            item_mobile.setTextAlignment(align_left)
            self.table_suppliers.setItem(row_idx, 3, item_mobile)

            # Address
            item_addr = QTableWidgetItem(supplier.get("address") or "-")
            item_addr.setTextAlignment(align_left)
            item_addr.setToolTip(supplier.get("address") or "")
            self.table_suppliers.setItem(row_idx, 4, item_addr)

            row_idx += 1

    def save_supplier(self):
        name = self.txt_name.text().strip()
        contact = self.txt_contact_person.text().strip()
        mobile = self.txt_mobile.text().strip()
        address = self.txt_address.toPlainText().strip()
        remarks = self.txt_remarks.toPlainText().strip()

        if not name:
            self.show_toast("Supplier Name is required.", "warning")
            return
        if not mobile:
            self.show_toast("Mobile Number is required.", "warning")
            return

        if self.save_worker and self.save_worker.isRunning():
            self.save_worker.terminate()
            self.save_worker.wait()

        self.btn_submit.setEnabled(False)
        self.btn_submit.setText("Saving...")

        self.save_worker = SupplierSaveWorker(
            self.vm, self.current_edit_supplier_id, name, contact, mobile, address, remarks
        )
        self.save_worker.success.connect(self.on_save_success)
        self.save_worker.failed.connect(self.on_save_failed)
        self.save_worker.start()

    def on_save_success(self, message: str):
        self.show_toast(message, "success")
        self.cancel_edit()
        self.load_suppliers()

    def on_save_failed(self, error_msg: str):
        if "must be in format" in error_msg.lower() or "required" in error_msg.lower():
            self.show_toast(error_msg, "warning")
        else:
            self.show_toast(f"Failed to register/update supplier:\n{error_msg}", "error")
        self.btn_submit.setEnabled(True)
        self.btn_submit.setText("Update Supplier" if self.current_edit_supplier_id else "Save Supplier")

    def cancel_edit(self):
        self.current_edit_supplier_id = None
        self.txt_name.clear()
        self.txt_contact_person.clear()
        self.txt_mobile.clear()
        self.txt_address.clear()
        self.txt_remarks.clear()

        self.lbl_form_title.setText("Add New Supplier")
        self.btn_submit.setText("Save Supplier")
        self.btn_submit.setEnabled(True)
        self.btn_cancel_edit.setVisible(False)
        self.btn_delete.setVisible(False)

    def on_table_double_clicked(self, model_index):
        row = model_index.row()
        sno_item = self.table_suppliers.item(row, 0)
        if sno_item is None:
            return
        try:
            supplier_idx = int(sno_item.text()) - 1
        except ValueError:
            return

        suppliers = self.displayed_suppliers
        if not suppliers or supplier_idx >= len(suppliers):
            return

        supplier = suppliers[supplier_idx]
        self.current_edit_supplier_id = supplier["id"]

        self.txt_name.setText(supplier["name"])
        self.txt_contact_person.setText(supplier.get("contact_person") or "")
        self.txt_mobile.setText(supplier["mobile"])
        self.txt_address.setPlainText(supplier.get("address") or "")
        self.txt_remarks.setPlainText(supplier.get("remarks") or "")

        self.lbl_form_title.setText("Edit Supplier Details")
        self.btn_submit.setText("Update Supplier")
        self.btn_submit.setEnabled(True)
        self.btn_cancel_edit.setVisible(True)
        self.btn_delete.setVisible(True)

    def delete_supplier(self):
        if not self.current_edit_supplier_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete Supplier",
            "Are you sure you want to delete this supplier record? All linked devices will lose their supplier association.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.delete_worker and self.delete_worker.isRunning():
            self.delete_worker.terminate()
            self.delete_worker.wait()

        self.btn_delete.setEnabled(False)

        self.delete_worker = SupplierDeleteWorker(self.vm, self.current_edit_supplier_id)
        self.delete_worker.success.connect(self.on_delete_success)
        self.delete_worker.failed.connect(self.on_delete_failed)
        self.delete_worker.start()

    def on_delete_success(self):
        self.show_toast("Supplier deleted successfully.", "success")
        self.btn_delete.setEnabled(True)
        self.cancel_edit()
        self.load_suppliers()

    def on_delete_failed(self, error_msg: str):
        self.show_toast(f"Failed to delete supplier:\n{error_msg}", "error")
        self.btn_delete.setEnabled(True)

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
