from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from src.viewmodels.device_viewmodel import DeviceViewModel
from src.services.cache_service import CacheService

class DeviceWorker(QThread):
    sync_finished = pyqtSignal(list)
    sync_not_needed = pyqtSignal()
    sync_failed = pyqtSignal(str)

    def __init__(self, vm: DeviceViewModel, query: str = None):
        super().__init__()
        self.vm = vm
        self.query = query

    def run(self):
        try:
            if self.query is not None:
                print(f"[Devices] Querying search for query: '{self.query}'")
                devices = self.vm.search_devices(self.query)
                self.sync_finished.emit(devices)
            else:
                changed = CacheService.check_and_update_state("devices", self.vm.repo.db)
                has_cache = CacheService.get("devices") is not None
                if not changed and has_cache:
                    print("[Devices] No database changes detected. Loading device inventory from persistent cache.")
                    self.sync_not_needed.emit()
                    return

                print("[Devices] Database changes detected. Updating device inventory from database...")
                devices = self.vm.get_all_devices()
                self.sync_finished.emit(devices)
        except Exception as e:
            self.sync_failed.emit(str(e))


class DeviceView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = DeviceViewModel()
        self.cache_devices = CacheService.get("devices")
        self.worker = None


        self.active_workers = []
        self.current_search_query = ""
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # -------------------------------------------------------------
        # 1. LEFT SIDE: ADD DEVICE FORM
        # -------------------------------------------------------------
        form_card = QFrame()
        form_card.setObjectName("form_card")
        form_card.setFixedWidth(320)
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(8)
        
        lbl_form_title = QLabel("Add New Device")
        lbl_form_title.setObjectName("lbl_section_title")
        form_layout.addWidget(lbl_form_title)
        
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
        
        form_layout.addStretch()
        main_layout.addWidget(form_card)

        # -------------------------------------------------------------
        # 2. RIGHT SIDE: SEARCH AND VIEW INVENTORY
        # -------------------------------------------------------------
        list_container = QFrame()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search by Device Name, Model, IMEI...")
        self.txt_search.textChanged.connect(self.search_devices)
        search_layout.addWidget(self.txt_search)
        
        self.btn_refresh = QPushButton("Refresh Inventory")
        self.btn_refresh.setObjectName("btn_secondary")
        self.btn_refresh.clicked.connect(self.load_devices)
        search_layout.addWidget(self.btn_refresh)
        list_layout.addLayout(search_layout)

        self.table_devices = QTableWidget(0, 5)
        self.table_devices.setHorizontalHeaderLabels(["Device Name", "Brand / Model", "RAM/ROM", "SIM Type", "IMEIs"])
        self.table_devices.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_devices.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        list_layout.addWidget(self.table_devices)
        main_layout.addWidget(list_container, 7)




        # Populate cache immediately if available
        if self.cache_devices:
            self.populate_table(self.cache_devices)


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
            self.populate_table(self.cache_devices)

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
        worker.sync_finished.connect(lambda devices: self.on_search_success(devices, query))
        worker.finished.connect(lambda: self.active_workers.remove(worker) if worker in self.active_workers else None)
        worker.start()

    def on_search_success(self, devices, query):
        if query == self.current_search_query:
            self.populate_table(devices)
            if not devices and query:
                self.show_toast(f'No device records found for "{query}".', "warning")

    def on_load_success(self, devices: list):
        self.cache_devices = devices
        CacheService.set("devices", devices)
        self.populate_table(devices)
        print("[Devices] Device inventory updated successfully.")

    def on_load_not_needed(self):
        pass

    def on_load_failed(self, error_msg: str):
        print(f"Device load failed: {error_msg}")

    def populate_table(self, devices):
        self.table_devices.setRowCount(0)
        align_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        for idx, dev in enumerate(devices):
            self.table_devices.insertRow(idx)
            
            item_name = QTableWidgetItem(dev["name"])
            item_name.setTextAlignment(align_left)
            self.table_devices.setItem(idx, 0, item_name)
            
            item_brand_model = QTableWidgetItem(f"{dev['brand']} / {dev['model']}")
            item_brand_model.setTextAlignment(align_left)
            self.table_devices.setItem(idx, 1, item_brand_model)
            
            item_ram_rom = QTableWidgetItem(f"{dev['ram']} / {dev['rom']}")
            item_ram_rom.setTextAlignment(align_left)
            self.table_devices.setItem(idx, 2, item_ram_rom)
            
            item_sim = QTableWidgetItem(f"{dev['sim_type']} SIM")
            item_sim.setTextAlignment(align_left)
            self.table_devices.setItem(idx, 3, item_sim)
            
            imeis = [dev.get("imei_1")]
            for i in range(2, 5):
                val = dev.get(f"imei_{i}")
                if val:
                    imeis.append(val)
            item_imeis = QTableWidgetItem(", ".join(imeis))
            item_imeis.setTextAlignment(align_left)
            self.table_devices.setItem(idx, 4, item_imeis)


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
        
        self.btn_submit.setEnabled(False)
        self.btn_submit.setText("Saving...")
        
        try:
            self.vm.register_device(name, brand, model, ram, rom, sim_type, imeis)
            self.show_toast("Device saved successfully to inventory.", "success")
            
            # Reset Form fields
            self.txt_name.clear()
            self.txt_brand.clear()
            self.txt_model.clear()
            self.cmb_ram.setCurrentIndex(4)
            self.cmb_rom.setCurrentIndex(3)
            self.radio_2.setChecked(True)
            for _, txt in self.imei_widgets:
                txt.clear()
            self.adjust_imei_fields()
            
            # Refresh Table
            self.load_devices()
        except ValueError as ve:
            self.show_toast(str(ve), "warning")
            self.btn_submit.setEnabled(True)
            self.btn_submit.setText("Save Device")
        except Exception as e:
            self.show_toast(f"Failed to register device:\n{e}", "error")
            self.btn_submit.setEnabled(True)
            self.btn_submit.setText("Save Device")
