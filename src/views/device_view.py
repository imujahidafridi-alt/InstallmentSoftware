from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QRadioButton, QButtonGroup, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from src.viewmodels.device_viewmodel import DeviceViewModel
from src.services.cache_service import CacheService

class DeviceWorker(QThread):
    sync_finished = pyqtSignal(list, list, list)
    sync_not_needed = pyqtSignal(list)
    sync_failed = pyqtSignal(str)

    def __init__(self, vm: DeviceViewModel, query: str = None):
        super().__init__()
        self.vm = vm
        self.query = query

    def run(self):
        try:
            from src.repositories.sale_repository import SaleRepository
            from src.viewmodels.supplier_viewmodel import SupplierViewModel
            sale_repo = SaleRepository()
            supplier_vm = SupplierViewModel()
            suppliers = supplier_vm.get_all_suppliers()
            
            if self.query is not None:
                print(f"[Devices] Querying search for query: '{self.query}'")
                devices = self.vm.search_devices(self.query)
                sales = sale_repo.get_all_with_details()
                self.sync_finished.emit(devices, sales, suppliers)
            else:
                changed_dev = CacheService.check_and_update_state("devices", self.vm.repo.db)
                changed_sales = CacheService.check_and_update_state("sales", self.vm.repo.db)
                has_cache = (
                    CacheService.get("devices") is not None and
                    CacheService.get("device_sales") is not None
                )
                if not changed_dev and not changed_sales and has_cache:
                    print("[Devices] No database changes detected. Loading device inventory from persistent cache.")
                    self.sync_not_needed.emit(suppliers)
                    return

                print("[Devices] Database changes detected. Updating device inventory from database...")
                devices = self.vm.get_all_devices()
                sales = sale_repo.get_all_with_details()
                self.sync_finished.emit(devices, sales, suppliers)
        except Exception as e:
            self.sync_failed.emit(str(e))


class DeviceSaveWorker(QThread):
    success = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, vm: DeviceViewModel, device_id: Optional[str], name: str, brand: str, model: str, ram: str, rom: str, sim_type: int, imeis: list, supplier_id: Optional[str] = None):
        super().__init__()
        self.vm = vm
        self.device_id = device_id
        self.name = name
        self.brand = brand
        self.model = model
        self.ram = ram
        self.rom = rom
        self.sim_type = sim_type
        self.imeis = imeis
        self.supplier_id = supplier_id

    def run(self):
        try:
            if self.device_id:
                self.vm.update_device(
                    self.device_id, self.name, self.brand, self.model,
                    self.ram, self.rom, self.sim_type, self.imeis, self.supplier_id
                )
                self.success.emit("Device details updated successfully.")
            else:
                self.vm.register_device(
                    self.name, self.brand, self.model,
                    self.ram, self.rom, self.sim_type, self.imeis, self.supplier_id
                )
                self.success.emit("Device saved successfully to inventory.")
        except Exception as e:
            self.failed.emit(str(e))


class DeviceDeleteWorker(QThread):
    success = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, vm: DeviceViewModel, device_id: str):
        super().__init__()
        self.vm = vm
        self.device_id = device_id

    def run(self):
        try:
            self.vm.delete_device(self.device_id)
            self.success.emit()
        except Exception as e:
            self.failed.emit(str(e))


class DeviceView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = DeviceViewModel()
        self.cache_devices = CacheService.get("devices")
        self.cache_sales = CacheService.get("device_sales")
        self.worker = None
        self.save_worker = None
        self.delete_worker = None


        self.active_workers = []
        self.current_search_query = ""
        self.current_edit_device_id = None
        self.displayed_devices = []
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # -------------------------------------------------------------
        # 1. LEFT SIDE: ADD DEVICE FORM
        # -------------------------------------------------------------
        form_card = QFrame()
        form_card.setObjectName("form_card")
        form_card.setFixedWidth(320)
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(8)
        
        self.lbl_form_title = QLabel("Add New Device")
        self.lbl_form_title.setObjectName("lbl_section_title")
        form_layout.addWidget(self.lbl_form_title)
        
        # General Fields
        form_layout.addWidget(QLabel("Device Name *"))
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Galaxy S24 Ultra")
        form_layout.addWidget(self.txt_name)
        
        form_layout.addWidget(QLabel("Brand"))
        self.txt_brand = QLineEdit()
        self.txt_brand.setPlaceholderText("e.g. Samsung")
        form_layout.addWidget(self.txt_brand)
        
        form_layout.addWidget(QLabel("Model"))
        self.txt_model = QLineEdit()
        self.txt_model.setPlaceholderText("e.g. SM-S928B")
        form_layout.addWidget(self.txt_model)
        
        # RAM & ROM Dropdowns
        ram_rom_layout = QHBoxLayout()
        
        # RAM
        ram_box = QVBoxLayout()
        ram_box.addWidget(QLabel("RAM *"))
        self.cmb_ram = QComboBox()
        self.cmb_ram.addItems(["2 GB", "3 GB", "4 GB", "6 GB", "8 GB", "12 GB", "16 GB", "24 GB"])
        self.cmb_ram.setCurrentIndex(4) # default 8 GB
        ram_box.addWidget(self.cmb_ram)
        ram_rom_layout.addLayout(ram_box)
        
        # ROM
        rom_box = QVBoxLayout()
        rom_box.addWidget(QLabel("ROM *"))
        self.cmb_rom = QComboBox()
        self.cmb_rom.addItems(["32 GB", "64 GB", "128 GB", "256 GB", "512 GB", "1 TB"])
        self.cmb_rom.setCurrentIndex(3) # default 256 GB
        rom_box.addWidget(self.cmb_rom)
        ram_rom_layout.addLayout(rom_box)
        
        form_layout.addLayout(ram_rom_layout)

        # Supplier Selection
        form_layout.addWidget(QLabel("Supplier"))
        self.cmb_supplier = QComboBox()
        self.cmb_supplier.addItem("No Supplier (None)", None)
        form_layout.addWidget(self.cmb_supplier)
        
        # SIM Configuration Buttons
        form_layout.addWidget(QLabel("SIM Slots Configuration"))
        sim_layout = QHBoxLayout()
        
        self.radio_1 = QRadioButton("1 SIM")
        self.radio_2 = QRadioButton("2 SIMs")
        self.radio_3 = QRadioButton("3 SIMs")
        self.radio_4 = QRadioButton("4 SIMs")
        
        self.sim_group = QButtonGroup()
        self.sim_group.addButton(self.radio_1, 1)
        self.sim_group.addButton(self.radio_2, 2)
        self.sim_group.addButton(self.radio_3, 3)
        self.sim_group.addButton(self.radio_4, 4)
        
        sim_layout.addWidget(self.radio_1)
        sim_layout.addWidget(self.radio_2)
        sim_layout.addWidget(self.radio_3)
        sim_layout.addWidget(self.radio_4)
        
        # Default Dual SIM
        self.radio_2.setChecked(True)
        form_layout.addLayout(sim_layout)
        
        # Listen for toggle changes
        self.sim_group.buttonToggled.connect(self.adjust_imei_fields)

        # Dynamic IMEI Fields
        self.imei_widgets = []
        for i in range(1, 5):
            lbl = QLabel(f"IMEI {i}")
            txt = QLineEdit()
            txt.setPlaceholderText("Exactly 15 numeric digits")
            txt.setMaxLength(15)
            
            form_layout.addWidget(lbl)
            form_layout.addWidget(txt)
            self.imei_widgets.append((lbl, txt))
            
        # Initial Toggle state
        self.adjust_imei_fields()

        # Submit Button
        self.btn_submit = QPushButton("Save Device")
        self.btn_submit.clicked.connect(self.save_device)
        form_layout.addWidget(self.btn_submit)

        # Cancel Edit Button
        self.btn_cancel_edit = QPushButton("Cancel Edit")
        self.btn_cancel_edit.setObjectName("btn_secondary")
        self.btn_cancel_edit.clicked.connect(self.cancel_edit)
        self.btn_cancel_edit.setVisible(False)
        form_layout.addWidget(self.btn_cancel_edit)

        # Delete Device Button
        self.btn_delete = QPushButton("Delete Device")
        self.btn_delete.setObjectName("btn_danger")
        self.btn_delete.clicked.connect(self.delete_device)
        self.btn_delete.setVisible(False)
        form_layout.addWidget(self.btn_delete)
        
        form_layout.addStretch()
        main_layout.addWidget(form_card)

        # -------------------------------------------------------------
        # 2. RIGHT SIDE: SEARCH AND VIEW INVENTORY
        # -------------------------------------------------------------
        list_container = QFrame()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        # Available / Sold Tab-style buttons
        self.btn_show_available = QPushButton("Available Devices")
        self.btn_show_available.setCheckable(True)
        self.btn_show_available.setChecked(True)
        self.btn_show_available.setFixedHeight(36)
        self.btn_show_available.setMinimumWidth(170)
        self.btn_show_available.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.btn_show_sold = QPushButton("Sold Devices")
        self.btn_show_sold.setCheckable(True)
        self.btn_show_sold.setChecked(False)
        self.btn_show_sold.setFixedHeight(36)
        self.btn_show_sold.setMinimumWidth(130)
        self.btn_show_sold.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        tab_qss = (
            "QPushButton {"
            "  background-color: #F8FAFC;"
            "  color: #64748B;"
            "  font-size: 13px;"
            "  font-weight: normal;"
            "  border: none;"
            "  border-bottom: 2px solid transparent;"
            "  border-top-left-radius: 6px;"
            "  border-top-right-radius: 6px;"
            "  border-bottom-left-radius: 0px;"
            "  border-bottom-right-radius: 0px;"
            "  padding: 8px 16px;"
            "}"
            "QPushButton:hover {"
            "  color: #0F172A;"
            "  background-color: #F1F5F9;"
            "}"
            "QPushButton:checked {"
            "  background-color: #FFFFFF;"
            "  color: #0F172A;"
            "  font-weight: normal;"
            "  border-bottom: 2px solid #3B82F6;"
            "}"
        )
        self.btn_show_available.setStyleSheet(tab_qss)
        self.btn_show_sold.setStyleSheet(tab_qss)

        self.toggle_group = QButtonGroup(self)
        self.toggle_group.addButton(self.btn_show_available)
        self.toggle_group.addButton(self.btn_show_sold)
        self.toggle_group.buttonToggled.connect(self.on_filter_toggle_changed)

        # Add tabs to the left of the search box
        search_layout.addWidget(self.btn_show_available)
        search_layout.addWidget(self.btn_show_sold)
        
        # Add a small spacing spacer between tabs and search input
        search_layout.addSpacing(12)

        # Search input
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search by Device Name, Model, IMEI...")
        self.txt_search.textChanged.connect(self.search_devices)
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
        search_layout.addWidget(self.txt_search, 1)

        # Refresh button
        self.btn_refresh = QPushButton("Refresh Inventory")
        self.btn_refresh.setObjectName("btn_secondary")
        self.btn_refresh.setFixedHeight(36)
        self.btn_refresh.clicked.connect(self.load_devices)
        search_layout.addWidget(self.btn_refresh)
        
        list_layout.addLayout(search_layout)
 
        self.table_devices = QTableWidget(0, 6)
        self.table_devices.setHorizontalHeaderLabels(["S.No", "Device Name", "Brand / Model", "RAM/ROM", "SIM Type", "IMEIs"])
        self.table_devices.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_devices.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_devices.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table_devices.verticalHeader().setVisible(False)
        self.table_devices.verticalHeader().setDefaultSectionSize(38)
        self.table_devices.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_devices.setSortingEnabled(False)
        list_layout.addWidget(self.table_devices)
        self.table_devices.doubleClicked.connect(self.on_table_double_clicked)
        main_layout.addWidget(list_container, 7)




        # Populate cache immediately if available
        if self.cache_devices:
            self.populate_table(self.cache_devices, self.cache_sales or [])


    def adjust_imei_fields(self):
        """Hides/shows IMEI fields depending on SIM slots radio selection."""
        sim_count = self.sim_group.checkedId()
        for idx, (lbl, txt) in enumerate(self.imei_widgets, 1):
            should_show = (idx <= sim_count)
            lbl.setVisible(should_show)
            txt.setVisible(should_show)

    def load_devices(self, *args):
        """Fetches all device logs and populates table asynchronously."""
        # 1. Populate cache immediately if available
        if self.cache_devices:
            self.populate_table(self.cache_devices, self.cache_sales or [])

        # 2. Terminate running worker
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        self.txt_search.clear()
        
        # 3. Fire async background task
        self.worker = DeviceWorker(self.vm)
        self.worker.sync_finished.connect(self.on_load_success)
        self.worker.sync_not_needed.connect(self.on_load_not_needed)
        self.worker.sync_failed.connect(self.on_load_failed)
        self.worker.start()

    def search_devices(self, *args):
        """Performs live search queries asynchronously with debouncing."""
        query = self.txt_search.text().strip()
        self.current_search_query = query
        self.search_timer.stop()
        self.search_timer.start(300)

    def perform_search(self):
        query = self.current_search_query
        worker = DeviceWorker(self.vm, query)
        self.active_workers.append(worker)
        worker.sync_finished.connect(lambda devices, sales, suppliers: self.on_search_success(devices, sales, suppliers, query))
        worker.finished.connect(lambda: self.active_workers.remove(worker) if worker in self.active_workers else None)
        worker.start()

    def on_search_success(self, devices, sales, suppliers, query):
        if query == self.current_search_query:
            self.populate_suppliers_combo(suppliers)
            self.populate_table(devices, sales)
            if not devices and query:
                self.show_toast(f'No device records found for "{query}".', "warning")

    def populate_suppliers_combo(self, suppliers: list):
        """Populates the supplier combo box while keeping selected value if possible."""
        current_sel = self.cmb_supplier.currentData()
        self.cmb_supplier.clear()
        self.cmb_supplier.addItem("No Supplier (None)", None)
        for s in suppliers:
            self.cmb_supplier.addItem(s["name"], s["id"])
        if current_sel:
            idx = self.cmb_supplier.findData(current_sel)
            if idx >= 0:
                self.cmb_supplier.setCurrentIndex(idx)

    def on_load_success(self, devices: list, sales: list, suppliers: list):
        self.cache_devices = devices
        self.cache_sales   = sales
        CacheService.set("devices", devices)
        CacheService.set("device_sales", sales)
        self.populate_suppliers_combo(suppliers)
        # Only repopulate if no search is active — prevents race condition
        if not self.current_search_query:
            self.populate_table(devices, sales)
        print("[Devices] Device inventory updated successfully.")

    def on_load_not_needed(self, suppliers: list):
        self.populate_suppliers_combo(suppliers)

    def on_load_failed(self, error_msg: str):
        print(f"Device load failed: {error_msg}")

    def on_filter_toggle_changed(self, button, checked):
        if checked:
            devices_to_show = getattr(self, "last_fetched_devices", None) or self.cache_devices
            if devices_to_show:
                self.populate_table(devices_to_show, self.cache_sales or [])

    def populate_table(self, devices, sales):
        self.last_fetched_devices = devices
        self.displayed_devices = []
        self.table_devices.setSortingEnabled(False)
        self.table_devices.setRowCount(0)
        
        sold_ids = {s["device_id"] for s in sales if "device_id" in s}

        show_only_sold = self.btn_show_sold.isChecked()
        
        filtered_devices = []
        for dev in devices:
            is_sold = dev["id"] in sold_ids
            if show_only_sold != is_sold:
                continue
            filtered_devices.append(dev)

        if not filtered_devices:
            from src.views.components.q_placeholder import show_empty_table_message
            if self.current_search_query:
                show_empty_table_message(self.table_devices, f"No matching devices found for '{self.current_search_query}'.\nTry searching for another device name, model, or IMEI.")
            elif show_only_sold:
                show_empty_table_message(self.table_devices, "No sold devices found in the system log.")
            else:
                show_empty_table_message(self.table_devices, "No devices available in inventory.\nRegister a device using the form on the left.")
            return

        align_center = Qt.AlignmentFlag.AlignCenter
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        row_idx = 0
        for dev in filtered_devices:
            self.displayed_devices.append(dev)
            self.table_devices.insertRow(row_idx)

            item_sno = QTableWidgetItem(str(row_idx + 1))
            item_sno.setTextAlignment(align_center)
            self.table_devices.setItem(row_idx, 0, item_sno)

            item_name = QTableWidgetItem(dev["name"])
            item_name.setTextAlignment(align_left)
            item_name.setToolTip(dev["name"])
            self.table_devices.setItem(row_idx, 1, item_name)

            brand_model = f"{dev['brand']} / {dev['model']}"
            item_brand_model = QTableWidgetItem(brand_model)
            item_brand_model.setTextAlignment(align_left)
            item_brand_model.setToolTip(brand_model)
            self.table_devices.setItem(row_idx, 2, item_brand_model)

            ram_rom = f"{dev['ram']} / {dev['rom']}"
            item_ram_rom = QTableWidgetItem(ram_rom)
            item_ram_rom.setTextAlignment(align_left)
            item_ram_rom.setToolTip(ram_rom)
            self.table_devices.setItem(row_idx, 3, item_ram_rom)

            sim = f"{dev['sim_type']} SIM"
            item_sim = QTableWidgetItem(sim)
            item_sim.setTextAlignment(align_left)
            item_sim.setToolTip(sim)
            self.table_devices.setItem(row_idx, 4, item_sim)

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
            item_imeis = QTableWidgetItem(imei_str)
            item_imeis.setTextAlignment(align_left)
            item_imeis.setToolTip(imei_str)
            self.table_devices.setItem(row_idx, 5, item_imeis)
            
            row_idx += 1
        self.table_devices.setSortingEnabled(False)


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

    def save_device(self, *args):
        name = self.txt_name.text().strip()
        brand = self.txt_brand.text().strip()
        model = self.txt_model.text().strip()
        ram = self.cmb_ram.currentText()
        rom = self.cmb_rom.currentText()
        sim_type = self.sim_group.checkedId()
        
        # Read all IMEI fields
        imeis = [txt.text().strip() for _, txt in self.imei_widgets]

        if self.save_worker and self.save_worker.isRunning():
            self.save_worker.terminate()
            self.save_worker.wait()
        
        self.btn_submit.setEnabled(False)
        self.btn_submit.setText("Updating..." if self.current_edit_device_id else "Saving...")
        
        supplier_id = self.cmb_supplier.currentData()
        self.save_worker = DeviceSaveWorker(
            self.vm, self.current_edit_device_id, name, brand, model, ram, rom, sim_type, imeis, supplier_id
        )
        self.save_worker.success.connect(self.on_save_success)
        self.save_worker.failed.connect(self.on_save_failed)
        self.save_worker.start()

    def on_save_success(self, message: str):
        self.show_toast(message, "success")
        self.cancel_edit()
        self.load_devices()

    def on_save_failed(self, error_msg: str):
        if "required" in error_msg.lower() or "must be" in error_msg.lower() or "duplicate" in error_msg.lower() or "already registered" in error_msg.lower():
            self.show_toast(error_msg, "warning")
        else:
            self.show_toast(f"Failed to register/update device:\n{error_msg}", "error")
        self.btn_submit.setEnabled(True)
        self.btn_submit.setText("Update Device" if self.current_edit_device_id else "Save Device")

    def cancel_edit(self):
        self.current_edit_device_id = None
        self.txt_name.clear()
        self.txt_brand.clear()
        self.txt_model.clear()
        self.cmb_ram.setCurrentIndex(4) # default 8 GB
        self.cmb_rom.setCurrentIndex(3) # default 256 GB
        self.radio_2.setChecked(True)
        self.cmb_supplier.setCurrentIndex(0) # default None
        for _, txt in self.imei_widgets:
            txt.clear()
        self.adjust_imei_fields()
        
        self.lbl_form_title.setText("Add New Device")
        self.btn_submit.setText("Save Device")
        self.btn_submit.setEnabled(True)
        self.btn_cancel_edit.setVisible(False)
        self.btn_delete.setVisible(False)

    def on_table_double_clicked(self, model_index):
        row = model_index.row()
        sno_item = self.table_devices.item(row, 0)
        if sno_item is None:
            return
        try:
            # S.no is 1-based, convert to 0-based index in displayed_devices
            dev_index = int(sno_item.text()) - 1
        except ValueError:
            return

        devices = self.displayed_devices
        if not devices or dev_index >= len(devices):
            return

        dev = devices[dev_index]
        
        # Check if the device is already sold. If yes, warn the user and block editing/deletion
        sold_ids = {s["device_id"] for s in (self.cache_sales or []) if "device_id" in s}
        if dev["id"] in sold_ids:
            self.show_toast("This device is already sold and cannot be edited or deleted.", "warning")
            return

        self.current_edit_device_id = dev["id"]

        self.txt_name.setText(dev["name"])
        self.txt_brand.setText(dev["brand"] if dev["brand"] != "-" else "")
        self.txt_model.setText(dev["model"] if dev["model"] != "-" else "")

        # Set Supplier Combo
        supplier_id = dev.get("supplier_id")
        idx = self.cmb_supplier.findData(supplier_id)
        if idx >= 0:
            self.cmb_supplier.setCurrentIndex(idx)
        else:
            self.cmb_supplier.setCurrentIndex(0)

        # Set RAM Combo
        ram_index = self.cmb_ram.findText(dev["ram"])
        if ram_index >= 0:
            self.cmb_ram.setCurrentIndex(ram_index)

        # Set ROM Combo
        rom_index = self.cmb_rom.findText(dev["rom"])
        if rom_index >= 0:
            self.cmb_rom.setCurrentIndex(rom_index)

        # Set SIM radio group
        sim_val = dev["sim_type"]
        if sim_val == 1:
            self.radio_1.setChecked(True)
        elif sim_val == 2:
            self.radio_2.setChecked(True)
        elif sim_val == 3:
            self.radio_3.setChecked(True)
        elif sim_val == 4:
            self.radio_4.setChecked(True)

        self.adjust_imei_fields()

        # Set IMEI text fields
        # If the IMEI was auto-generated (starts with "00"), we clear it in the edit form so they can type one!
        for idx in range(1, 5):
            imei_val = dev.get(f"imei_{idx}")
            txt_widget = self.imei_widgets[idx - 1][1]
            if imei_val:
                if idx == 1 and imei_val.startswith("00"):
                    txt_widget.clear()
                else:
                    txt_widget.setText(imei_val)
            else:
                txt_widget.clear()

        self.lbl_form_title.setText("Edit Device Details")
        self.btn_submit.setText("Update Device")
        self.btn_submit.setEnabled(True)
        self.btn_cancel_edit.setVisible(True)
        self.btn_delete.setVisible(True)

    def delete_device(self):
        if not self.current_edit_device_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete Device",
            "Are you sure you want to delete this device record from inventory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.delete_worker and self.delete_worker.isRunning():
            self.delete_worker.terminate()
            self.delete_worker.wait()

        self.btn_delete.setEnabled(False)

        self.delete_worker = DeviceDeleteWorker(self.vm, self.current_edit_device_id)
        self.delete_worker.success.connect(self.on_delete_success)
        self.delete_worker.failed.connect(self.on_delete_failed)
        self.delete_worker.start()

    def on_delete_success(self):
        self.show_toast("Device deleted successfully from inventory.", "success")
        self.btn_delete.setEnabled(True)
        self.cancel_edit()
        self.load_devices()

    def on_delete_failed(self, error_msg: str):
        if "already sold" in error_msg.lower() or "cannot be deleted" in error_msg.lower():
            self.show_toast(error_msg, "warning")
        else:
            self.show_toast(f"Failed to delete device:\n{error_msg}", "error")
        self.btn_delete.setEnabled(True)
