from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
    QLabel, QLineEdit, QPushButton, QStackedWidget, QMessageBox,
    QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import socket
from src.views.dashboard_view import DashboardView
from src.views.due_overdue_view import DueOverdueView
from src.views.customer_view import CustomerView
from src.views.device_view import DeviceView
from src.views.sale_view import SaleView
from src.views.ledger_view import LedgerView
from src.views.report_view import ReportView
from src.views.settings_view import SettingsView
from src.views.audit_log_view import AuditLogView
from src.views.supplier_view import SupplierView
from src.views.about_view import AboutView
from src.views.backup_view import BackupView
from src.repositories.customer_repository import CustomerRepository
from src.repositories.device_repository import DeviceRepository
from src.repositories.sale_repository import SaleRepository

from src.views.components.q_notification import QNotification

class NetworkCheckWorker(QThread):
    status_changed = pyqtSignal(bool)

    def run(self):
        try:
            socket.setdefaulttimeout(2.0)
            host = socket.gethostbyname("google.com")
            s = socket.create_connection((host, 80), 2.0)
            s.close()
            self.status_changed.emit(True)
        except Exception:
            self.status_changed.emit(False)

class GlobalSearchWorker(QThread):
    finished = pyqtSignal(str)  # Emits matching sale_id if found, else empty string
    failed = pyqtSignal(str)

    def __init__(self, cust_repo: CustomerRepository, dev_repo: DeviceRepository, sale_repo: SaleRepository, query: str):
        super().__init__()
        self.cust_repo = cust_repo
        self.dev_repo = dev_repo
        self.sale_repo = sale_repo
        self.query = query

    def run(self):
        try:
            # 1. Search Customers
            matching_customers = self.cust_repo.search(self.query)
            if matching_customers:
                customer = matching_customers[0]
                sales = self.sale_repo.get_customer_sales(customer["id"])
                if sales:
                    self.finished.emit(sales[0]["id"])
                    return

            # 2. Search Device IMEIs
            matching_devices = self.dev_repo.search(self.query)
            if matching_devices:
                device = matching_devices[0]
                sales_res = self.sale_repo.db.table("sales").select("id").eq("device_id", device["id"]).execute()
                if sales_res.data:
                    self.finished.emit(sales_res.data[0]["id"])
                    return

            # 3. Direct lookup on Sale ID
            if len(self.query) >= 8:
                sales_res = self.sale_repo.db.table("sales").select("id").ilike("id", f"{self.query}%").execute()
                if sales_res.data:
                    self.finished.emit(sales_res.data[0]["id"])
                    return

            self.finished.emit("")
        except Exception as e:
            self.failed.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cust_repo = CustomerRepository()
        self.dev_repo = DeviceRepository()
        self.sale_repo = SaleRepository()
        self.search_worker = None
        self.active_network_worker = None
        self.init_ui()
        
        # Setup Network Status checking Timer
        from PyQt6.QtCore import QTimer
        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self.check_network_status)
        self.network_timer.start(5000) # Check every 5 seconds
        self.check_network_status()

        # Setup Digital Clock Timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000) # Check every second
        self.update_clock() # Update immediately

    def init_ui(self):
        self.setWindowTitle("EasyQist - Device Installment Management System")
        self.resize(1100, 750)

        # Main Central Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. SIDEBAR MENU
        # -------------------------------------------------------------
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(8)

        # App Brand Logo
        from PyQt6.QtGui import QPixmap
        import os

        lbl_brand = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_brand.setPixmap(scaled_pixmap)
            lbl_brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_brand.setStyleSheet("padding: 5px;")
        else:
            lbl_brand.setText("EasyQist")
            lbl_brand.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: #3B82F6;")
            lbl_brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        sidebar_layout.addWidget(lbl_brand)
        sidebar_layout.addSpacing(15)

        # Nav Buttons
        self.nav_buttons = []
        menus = [
            ("Dashboard", 0),
            ("New Sale", 1),
            ("Customers", 2),
            ("Customer Ledgers", 3),
            ("Reminders", 4),
            ("Devices Inventory", 5),
            ("Suppliers", 6),
            ("Financial Reports", 7),
            ("System Settings", 8),
            ("Backup Center", 9),
            ("Audit Logs", 10),
            ("About AMC", 11)

        ]

        for name, index in menus:
            btn = QPushButton(name)
            btn.setObjectName("sidebar_btn")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda checked, idx=index: self.switch_view(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # Default dashboard button checked
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)

        # -------------------------------------------------------------
        # 2. MAIN CONTENT WRAPPER (TOPNAV & STACKED CONTENT)
        # -------------------------------------------------------------
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top Nav Bar
        topnav = QFrame()
        topnav.setObjectName("topnav")
        topnav_layout = QHBoxLayout(topnav)
        topnav_layout.setContentsMargins(15, 10, 15, 10)
        topnav_layout.setSpacing(15)

        # Global Search Box
        self.txt_global_search = QLineEdit()
        self.txt_global_search.setPlaceholderText("Search customer name, mobile, IMEI or Sale ID...")
        self.txt_global_search.setMinimumWidth(300)
        self.txt_global_search.returnPressed.connect(self.perform_global_search)
        topnav_layout.addWidget(self.txt_global_search)

        topnav_layout.addStretch()

        # Digital Clock
        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet("font-weight: bold; color: #475569; padding: 5px; font-size: 12px; margin-right: 10px;")
        topnav_layout.addWidget(self.lbl_clock)

        # Network Status Indicator
        self.lbl_network_status = QLabel("● Checking...")
        self.lbl_network_status.setStyleSheet("font-weight: bold; color: #64748B; padding: 5px;")
        topnav_layout.addWidget(self.lbl_network_status)

        content_layout.addWidget(topnav)

        # QStackedWidget Content Area
        self.stacked_widget = QStackedWidget()
        
        # Instantiate subviews
        self.view_dashboard = DashboardView()
        self.view_sale = SaleView()
        self.view_customer = CustomerView()
        self.view_ledger = LedgerView()
        self.view_due_overdue = DueOverdueView()
        self.view_device = DeviceView()
        self.view_supplier = SupplierView()
        self.view_report = ReportView()
        self.view_settings = SettingsView()
        self.view_backup = BackupView()
        self.view_audit = AuditLogView()
        self.view_about = AboutView()

        # Add to stack
        self.stacked_widget.addWidget(self.view_dashboard)    # Index 0
        self.stacked_widget.addWidget(self.view_sale)          # Index 1
        self.stacked_widget.addWidget(self.view_customer)      # Index 2
        self.stacked_widget.addWidget(self.view_ledger)        # Index 3
        self.stacked_widget.addWidget(self.view_due_overdue)   # Index 4
        self.stacked_widget.addWidget(self.view_device)        # Index 5
        self.stacked_widget.addWidget(self.view_supplier)      # Index 6
        self.stacked_widget.addWidget(self.view_report)        # Index 7
        self.stacked_widget.addWidget(self.view_settings)      # Index 8
        self.stacked_widget.addWidget(self.view_backup)        # Index 9
        self.stacked_widget.addWidget(self.view_audit)         # Index 10
        self.stacked_widget.addWidget(self.view_about)         # Index 11

        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_container)

        # Load initial data
        self.switch_view(0)

    def switch_view(self, index: int):
        """Changes stacking container view and executes lazy metrics loads."""
        self.stacked_widget.setCurrentIndex(index)
        
        # Highlight matching navigation tab
        if index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)
            
        # Refresh screen contents dynamically on activation
        if index == 0:
            self.view_dashboard.refresh_data()
        elif index == 1:
            self.view_sale.load_dropdowns_data()
        elif index == 2:
            self.view_customer.load_customers()
        elif index == 3:
            self.view_ledger.load_ledgers_dropdown()
        elif index == 4:
            self.view_due_overdue.refresh_data()
        elif index == 5:
            self.view_device.load_devices()
        elif index == 6:
            self.view_supplier.load_suppliers()
        elif index == 7:
            self.view_report.load_report_data()
        elif index == 8:
            self.view_settings.load_settings()
        elif index == 9:
            self.view_backup.load_backup_settings()
        elif index == 10:
            self.view_audit.load_audit_logs()


    def perform_global_search(self):
        """
        Global Search Bar logic:
        Searches by Customer Name, Mobile, IMEI, or Sale ID.
        If found, loads the ledger of the matching transaction and redirects.
        """
        query = self.txt_global_search.text().strip()
        if not query:
            return

        if self.search_worker and self.search_worker.isRunning():
            return

        self.txt_global_search.setEnabled(False)
        self.txt_global_search.setPlaceholderText("Searching...")

        self.search_worker = GlobalSearchWorker(self.cust_repo, self.dev_repo, self.sale_repo, query)
        self.search_worker.finished.connect(lambda sale_id: self.on_search_finished(sale_id, query))
        self.search_worker.failed.connect(self.on_search_failed)
        self.search_worker.start()

    def on_search_finished(self, sale_id: str, query: str):
        self.txt_global_search.setEnabled(True)
        self.txt_global_search.setPlaceholderText("Search customer name, mobile, IMEI or Sale ID...")

        if sale_id:
            # Direct them to Customer Ledgers page (index 5) and auto-select this sale
            if hasattr(self.view_ledger, "select_sale"):
                self.view_ledger.select_sale(sale_id)
            self.switch_view(3)
            self.txt_global_search.clear()
            self.show_notification("Installment ledger found successfully.", "success")
        else:
            self.show_notification(f"No ledgers match query: '{query}'", "warning")

    def on_search_failed(self, error_msg: str):
        self.txt_global_search.setEnabled(True)
        self.txt_global_search.setPlaceholderText("Search customer name, mobile, IMEI or Sale ID...")
        self.show_notification(f"Search failed: {error_msg}", "error")

    def check_network_status(self):
        if self.active_network_worker and self.active_network_worker.isRunning():
            return
        self.active_network_worker = NetworkCheckWorker()
        self.active_network_worker.status_changed.connect(self.on_network_status_changed)
        self.active_network_worker.start()

    def on_network_status_changed(self, is_online: bool):
        if is_online:
            self.lbl_network_status.setText("● Online")
            self.lbl_network_status.setStyleSheet("font-weight: bold; color: #10B981; padding: 5px;")
        else:
            self.lbl_network_status.setText("● Offline")
            self.lbl_network_status.setStyleSheet("font-weight: bold; color: #EF4444; padding: 5px;")

    def update_clock(self):
        from PyQt6.QtCore import QDateTime
        self.lbl_clock.setText(QDateTime.currentDateTime().toString("hh:mm:ss AP"))

    def show_notification(self, message: str, type: str = "info", duration: int = 4000):
        """Displays a beautiful non-blocking overlay toast notification."""
        QNotification(self, message, type, duration)

    def closeEvent(self, event):
        """Safely stops and reaps all active background threads to avoid destruction errors."""
        # Check auto backup setting on close
        try:
            from src.config import ConfigManager
            from src.services.backup_service import BackupService
            
            config = ConfigManager.load_config()
            if config.get("auto_backup", False) and BackupService.is_google_configured() and BackupService.get_credentials():
                # Show a beautiful modal dialog to indicate backup is in progress
                from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
                from PyQt6.QtCore import Qt
                
                dialog = QDialog(self)
                dialog.setWindowTitle("Cloud Sync")
                dialog.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
                dialog.setFixedSize(350, 120)
                dialog.setStyleSheet("QDialog { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; }")
                
                dlg_layout = QVBoxLayout(dialog)
                dlg_layout.setContentsMargins(20, 20, 20, 20)
                dlg_layout.setSpacing(10)
                
                lbl_msg = QLabel("Backing up database to Google Drive...")
                lbl_msg.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E293B;")
                dlg_layout.addWidget(lbl_msg)
                
                bar = QProgressBar()
                bar.setFixedHeight(12)
                bar.setTextVisible(False)
                bar.setStyleSheet("""
                    QProgressBar { border: 1px solid #E2E8F0; border-radius: 6px; background-color: #F1F5F9; }
                    QProgressBar::chunk { background-color: #3B82F6; border-radius: 5px; }
                """)
                bar.setRange(0, 100)
                dlg_layout.addWidget(bar)
                
                dialog.show()
                QApplication.processEvents()
                
                lbl_msg.setText("Creating compressed database backup...")
                bar.setValue(15)
                QApplication.processEvents()
                
                zip_path, zip_filename = BackupService.create_database_backup()
                bar.setValue(35)
                lbl_msg.setText("Uploading backup to Google Drive...")
                QApplication.processEvents()
                
                def upload_progress(p):
                    bar.setValue(35 + int(p * 0.65))
                    QApplication.processEvents()
                    
                success, result = BackupService.upload_backup_to_drive(zip_path, zip_filename, progress_callback=upload_progress)
                
                if success:
                    try:
                        from datetime import datetime
                        config = ConfigManager.load_config()
                        config["last_drive_backup"] = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                        ConfigManager.save_config(config)
                    except Exception as e:
                        print(f"Failed to update auto-backup timestamp: {e}")

                    try:
                        from src.services.audit_log_service import AuditLogService
                        AuditLogService().log_action("Uploaded automatic database backup to Google Drive on close")
                    except Exception:
                        pass
                
                dialog.close()
        except Exception as e:
            print(f"Auto-backup on close failed: {e}")

        views = [
            self.view_dashboard, self.view_due_overdue, self.view_customer, self.view_device, 
            self.view_sale, self.view_ledger, self.view_report, self.view_audit, self.view_settings,
            self.view_backup, self.view_about
        ]


        
        # Stop global search worker if running
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()

        # Stop active network checking worker if running
        if self.active_network_worker and self.active_network_worker.isRunning():
            self.active_network_worker.terminate()
            self.active_network_worker.wait()

        # Stop all subview workers
        for view in views:
            if not view:
                continue
            # Check dashboard view workers
            if hasattr(view, "sync_worker") and view.sync_worker and view.sync_worker.isRunning():
                view.sync_worker.terminate()
                view.sync_worker.wait()
            # Check other views having 'worker'
            if hasattr(view, "worker") and view.worker and view.worker.isRunning():
                view.worker.terminate()
                view.worker.wait()
            # Check transactional write/update workers
            if hasattr(view, "commit_worker") and view.commit_worker and view.commit_worker.isRunning():
                view.commit_worker.terminate()
                view.commit_worker.wait()
            if hasattr(view, "save_worker") and view.save_worker and view.save_worker.isRunning():
                view.save_worker.terminate()
                view.save_worker.wait()
            if hasattr(view, "delete_worker") and view.delete_worker and view.delete_worker.isRunning():
                view.delete_worker.terminate()
                view.delete_worker.wait()
            if hasattr(view, "payment_worker") and view.payment_worker and view.payment_worker.isRunning():
                view.payment_worker.terminate()
                view.payment_worker.wait()
            if hasattr(view, "reschedule_worker") and view.reschedule_worker and view.reschedule_worker.isRunning():
                view.reschedule_worker.terminate()
                view.reschedule_worker.wait()
            if hasattr(view, "pdf_worker") and view.pdf_worker and view.pdf_worker.isRunning():
                view.pdf_worker.terminate()
                view.pdf_worker.wait()
            # Check other views having 'clear_worker'
            if hasattr(view, "clear_worker") and view.clear_worker and view.clear_worker.isRunning():
                view.clear_worker.terminate()
                view.clear_worker.wait()
            # Check ledger view list_worker and detail_worker
            if hasattr(view, "list_worker") and view.list_worker and view.list_worker.isRunning():
                view.list_worker.terminate()
                view.list_worker.wait()
            if hasattr(view, "detail_worker") and view.detail_worker and view.detail_worker.isRunning():
                view.detail_worker.terminate()
                view.detail_worker.wait()
            # Check active search workers array (e.g. search workers in customer/device views)
            if hasattr(view, "active_workers") and isinstance(view.active_workers, list):
                for w in list(view.active_workers):
                    if w and w.isRunning():
                        w.terminate()
                        w.wait()
            # Check settings reset worker
            if hasattr(view, "reset_worker") and view.reset_worker and view.reset_worker.isRunning():
                view.reset_worker.terminate()
                view.reset_worker.wait()
            # Check backup view workers
            if hasattr(view, "auth_worker") and view.auth_worker and view.auth_worker.isRunning():
                view.auth_worker.terminate()
                view.auth_worker.wait()
            if hasattr(view, "upload_worker") and view.upload_worker and view.upload_worker.isRunning():
                view.upload_worker.terminate()
                view.upload_worker.wait()
                
        event.accept()

