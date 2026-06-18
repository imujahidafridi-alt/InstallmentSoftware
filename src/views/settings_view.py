from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, 
    QComboBox, QPushButton, QMessageBox, QApplication,
    QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.config import ConfigManager

class DatabaseResetWorker(QThread):
    reset_success = pyqtSignal()
    reset_failed = pyqtSignal(str)

    def run(self):
        try:
            from src.db.supabase_client import get_db
            import time
            db = get_db()
            if not db:
                raise Exception("Database client could not be initialized.")
            
            # Delete in order of foreign key dependency
            # 1. Payments
            db.table("payments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            time.sleep(0.5)
            # 2. Installments
            db.table("installments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            time.sleep(0.5)
            # 3. Sales
            db.table("sales").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            time.sleep(0.5)
            # 4. Devices
            db.table("devices").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            time.sleep(0.5)
            # 5. Customers
            db.table("customers").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            time.sleep(0.5)
            # 6. Audit Logs
            db.table("audit_logs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            time.sleep(0.5)
            
            # Clear local persistent cache
            from src.services.cache_service import CacheService
            CacheService.clear()
            
            # Log initial reset event
            from src.services.audit_log_service import AuditLogService
            AuditLogService().log_action("Database wiped and reset completely")
            
            self.reset_success.emit()
        except Exception as e:
            self.reset_failed.emit(str(e))

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.reset_worker = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Title
        lbl_title = QLabel("System Settings")
        lbl_title.setObjectName("lbl_title")
        main_layout.addWidget(lbl_title)

        # Settings Form Card Box
        form_card = QFrame()
        form_card.setObjectName("form_card")
        form_card.setFixedWidth(450)
        
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(20, 20, 20, 20)

        # Shop Name
        form_layout.addWidget(QLabel("Shop / Company Name"))
        self.txt_shop_name = QLineEdit()
        self.txt_shop_name.setPlaceholderText("e.g. Al-Madina Electronics")
        form_layout.addWidget(self.txt_shop_name)

        # Shop Address
        form_layout.addWidget(QLabel("Shop Address"))
        self.txt_shop_address = QLineEdit()
        self.txt_shop_address.setPlaceholderText("e.g. Main Commercial Area, Lahore")
        form_layout.addWidget(self.txt_shop_address)

        # Contact Number
        form_layout.addWidget(QLabel("Contact Phone Number"))
        self.txt_shop_contact = QLineEdit()
        self.txt_shop_contact.setPlaceholderText("e.g. 0300-1234567")
        form_layout.addWidget(self.txt_shop_contact)


        # Save Button
        self.btn_save = QPushButton("Apply and Save Settings")
        self.btn_save.clicked.connect(self.save_settings)
        form_layout.addWidget(self.btn_save)

        main_layout.addWidget(form_card)

        # Danger Zone / Database Management Card
        danger_card = QFrame()
        danger_card.setObjectName("form_card")
        danger_card.setFixedWidth(450)
        danger_card.setStyleSheet("QFrame#form_card { border: 1px solid #FECACA; }")
        
        danger_layout = QVBoxLayout(danger_card)
        danger_layout.setSpacing(10)
        danger_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_danger_title = QLabel("Danger Zone")
        lbl_danger_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #DC2626;")
        danger_layout.addWidget(lbl_danger_title)
        
        lbl_danger_desc = QLabel("Reset the system database completely. This deletes all customers, devices, sales, installments, and payment history.")
        lbl_danger_desc.setWordWrap(True)
        lbl_danger_desc.setStyleSheet("font-size: 11px; color: #64748B; margin-bottom: 5px;")
        danger_layout.addWidget(lbl_danger_desc)
        
        self.btn_reset = QPushButton("Reset System Database")
        self.btn_reset.setObjectName("btn_danger")
        self.btn_reset.clicked.connect(self.reset_database)
        danger_layout.addWidget(self.btn_reset)
        
        main_layout.addWidget(danger_card)
        main_layout.addStretch()

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

    def load_settings(self):
        """Loads and pre-populates existing shop details and active theme settings."""
        try:
            config = ConfigManager.load_config()
            self.txt_shop_name.setText(config.get("shop_name", ""))
            self.txt_shop_address.setText(config.get("shop_address", ""))
            self.txt_shop_contact.setText(config.get("shop_contact", ""))
            

        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self, *args):
        name = self.txt_shop_name.text().strip()
        address = self.txt_shop_address.text().strip()
        contact = self.txt_shop_contact.text().strip()
        theme = "light"

        if not name:
            self.show_toast("Shop Name cannot be empty.", "warning")
            return

        config_data = {
            "theme": theme,
            "shop_name": name,
            "shop_address": address,
            "shop_contact": contact
        }

        try:
            # Save configuration locally
            ConfigManager.save_config(config_data)
            
            # Reapply stylesheet instantly on QApplication instance
            qss = ConfigManager.get_qss(theme)
            app = QApplication.instance()
            if app and qss:
                app.setStyleSheet(qss)
                
            self.show_toast("Configuration settings saved successfully.", "success")
        except Exception as e:
            self.show_toast(f"Could not update configurations: {e}", "error")

    def reset_database(self, *args):
        password, ok = QInputDialog.getText(
            self, 
            "Database Reset Required", 
            "Enter Administrator Password to reset database:",
            QLineEdit.EchoMode.Password
        )
        
        if not ok:
            return
            
        if password != "MUJ@hid.786":
            self.show_toast("Invalid administrator password. Reset aborted.", "error")
            return
            
        confirm = QMessageBox.question(
            self,
            "Confirm Database Reset",
            "WARNING: This will completely wipe all customers, devices, sales, installments, and payment logs.\n\nAre you absolutely sure you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
            
        self.btn_reset.setEnabled(False)
        self.btn_reset.setText("Resetting Database...")
        
        self.reset_worker = DatabaseResetWorker()
        self.reset_worker.reset_success.connect(self.on_reset_success)
        self.reset_worker.reset_failed.connect(self.on_reset_failed)
        self.reset_worker.start()

    def on_reset_success(self):
        self.btn_reset.setEnabled(True)
        self.btn_reset.setText("Reset System Database")
        self.show_toast("Database completely reset and local cache cleared.", "success")

    def on_reset_failed(self, error_msg: str):
        self.btn_reset.setEnabled(True)
        self.btn_reset.setText("Reset System Database")
        self.show_toast(f"Database reset failed: {error_msg}", "error")
