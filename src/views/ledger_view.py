from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.viewmodels.installment_viewmodel import InstallmentViewModel
from src.views.payment_dialog import PaymentDialog
from src.views.reschedule_dialog import RescheduleDialog
from datetime import datetime
from src.services.cache_service import CacheService

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
            changed = CacheService.check_and_update_state("payments", self.vm.pay_repo.db)
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


class LedgerView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = InstallmentViewModel()
        
        # Load cache from persistent storage
        self.cache_sales_list = CacheService.get("ledger_sales_list")
        self.cache_ledger_details = CacheService.get("ledger_details", {})
        
        self.list_worker = None
        self.detail_worker = None
        
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
        self.cmb_sales = QComboBox()
        self.cmb_sales.setFixedWidth(350)
        self.cmb_sales.currentIndexChanged.connect(self.load_selected_ledger)
        search_layout.addWidget(self.cmb_sales)
        
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

        self.lbl_cust_name = QLabel("Customer: -")
        self.lbl_dev_name = QLabel("Device: -")
        self.lbl_selling_price = QLabel("Total Sale Price: Rs. 0.00")
        self.lbl_down_payment = QLabel("Down Payment: Rs. 0.00")
        self.lbl_total_paid = QLabel("Total Payments: Rs. 0.00")
        self.lbl_outstanding = QLabel("Outstanding Balance: Rs. 0.00")
        self.lbl_outstanding.setStyleSheet("font-weight: bold; color: #EF4444;")
        self.lbl_remaining_months = QLabel("Unpaid Months: 0")
        self.lbl_next_due = QLabel("Next Due Date: -")
        
        sum_layout.addWidget(self.lbl_cust_name)
        sum_layout.addWidget(QFrame()) # spacer line
        sum_layout.addWidget(self.lbl_dev_name)
        sum_layout.addWidget(self.lbl_selling_price)
        sum_layout.addWidget(self.lbl_down_payment)
        sum_layout.addWidget(self.lbl_total_paid)
        sum_layout.addWidget(self.lbl_outstanding)
        sum_layout.addWidget(self.lbl_remaining_months)
        sum_layout.addWidget(self.lbl_next_due)
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
        self.list_worker.start()

    def on_list_success(self, sales: list):
        self.cache_sales_list = sales
        CacheService.set("ledger_sales_list", sales)
        self.populate_dropdown(sales)
        print("[Ledgers List] Sales ledger list updated successfully.")

    def on_list_not_needed(self):
        pass

    def populate_dropdown(self, sales: list):
        prev_sel = self.cmb_sales.currentData()
        
        # Block signals temporarily to prevent load loops during populate
        self.cmb_sales.blockSignals(True)
        self.cmb_sales.clear()
        
        for sale in sales:
            label = f"{sale['customers']['name']} - {sale['devices']['brand']} {sale['devices']['model']} (Rs. {float(sale['selling_price']):,.0f})"
            self.cmb_sales.addItem(label, sale["id"])
            
        if prev_sel:
            idx = self.cmb_sales.findData(prev_sel)
            if idx >= 0:
                self.cmb_sales.setCurrentIndex(idx)
                
        self.cmb_sales.blockSignals(False)

    def load_selected_ledger(self, *args):
        """Queries detailed ledger calculations for selection asynchronously."""
        sale_id = self.cmb_sales.currentData()
        if not sale_id:
            # Clear UI metrics
            self.lbl_cust_name.setText("Customer: -")
            self.lbl_dev_name.setText("Device: -")
            self.lbl_selling_price.setText("Total Sale Price: Rs. 0.00")
            self.lbl_down_payment.setText("Down Payment: Rs. 0.00")
            self.lbl_total_paid.setText("Total Payments: Rs. 0.00")
            self.lbl_outstanding.setText("Outstanding Balance: Rs. 0.00")
            self.lbl_remaining_months.setText("Unpaid Months: 0")
            self.lbl_next_due.setText("Next Due Date: -")
            self.table_ledger.setRowCount(0)
            self.btn_pay.setEnabled(False)
            self.btn_pdf.setEnabled(False)
            return

        # 1. Populate immediately if detail cache exists
        if sale_id in self.cache_ledger_details:
            self.populate_ledger_details(self.cache_ledger_details[sale_id])

        # 2. Prevent concurrent detail workers
        if self.detail_worker and self.detail_worker.isRunning():
            self.detail_worker.terminate()
            
        # 3. Fire async details retrieval
        self.detail_worker = LedgerDetailWorker(self.vm, sale_id)
        self.detail_worker.sync_finished.connect(self.on_detail_success)
        self.detail_worker.sync_not_needed.connect(self.on_detail_not_needed)
        self.detail_worker.start()

    def on_detail_success(self, data: dict):
        sale_id = data["sale"]["id"]
        self.cache_ledger_details[sale_id] = data
        CacheService.set("ledger_details", self.cache_ledger_details)
        self.populate_ledger_details(data)
        print(f"[Ledger Detail: {sale_id}] Ledger details updated successfully.")

    def on_detail_not_needed(self):
        pass

    def populate_ledger_details(self, data: dict):
        # Populate KPI metrics
        self.lbl_cust_name.setText(f"Customer: {data['customer']['name']}")
        self.lbl_dev_name.setText(f"Device: {data['device']['brand']} {data['device']['model']}")
        
        self.lbl_selling_price.setText(f"Total Sale Price: Rs. {data['summary']['selling_price']:,.2f}")
        self.lbl_down_payment.setText(f"Down Payment: Rs. {data['summary']['down_payment']:,.2f}")
        self.lbl_total_paid.setText(f"Total Payments: Rs. {data['summary']['total_paid']:,.2f}")
        self.lbl_outstanding.setText(f"Outstanding Balance: Rs. {data['summary']['outstanding']:,.2f}")
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
            self.table_ledger.setItem(idx, 0, item_no)
            
            due_dt = datetime.strptime(inst["due_date"], "%Y-%m-%d").strftime("%d-%b-%Y")
            item_due = QTableWidgetItem(due_dt)
            item_due.setTextAlignment(align_left)
            self.table_ledger.setItem(idx, 1, item_due)
            
            item_amt = QTableWidgetItem(f"Rs. {float(inst['amount']):,.2f}")
            item_amt.setTextAlignment(align_left)
            self.table_ledger.setItem(idx, 2, item_amt)
            
            # Payment info
            inst_pays = payment_map.get(inst["id"], [])
            if inst_pays:
                p_dates = [datetime.strptime(p["payment_date"], "%Y-%m-%d").strftime("%d-%b-%Y") for p in inst_pays]
                p_dates_str = ", ".join(p_dates)
                p_amount = sum(float(p["amount_received"]) for p in inst_pays)
                p_amount_str = f"Rs. {p_amount:,.2f}"
            else:
                p_dates_str = "-"
                p_amount_str = "Rs. 0.00"
                
            item_pay_dates = QTableWidgetItem(p_dates_str)
            item_pay_dates.setTextAlignment(align_left)
            self.table_ledger.setItem(idx, 3, item_pay_dates)
            
            item_pay_amt = QTableWidgetItem(p_amount_str)
            item_pay_amt.setTextAlignment(align_left)
            self.table_ledger.setItem(idx, 4, item_pay_amt)

            
            # Status tag coloring
            status = inst["status"]
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(align_left)
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
        sale_id = self.cmb_sales.currentData()
        if not sale_id:
            return
            
        # Get next installment amount as a default value recommendation from cache
        try:
            if sale_id in self.cache_ledger_details:
                ledger_data = self.cache_ledger_details[sale_id]
            else:
                ledger_data = self.vm.get_ledger_data(sale_id)
            unpaid = [inst for inst in ledger_data["installments"] if inst["status"] != "Paid"]
            default_val = 0.0
            if unpaid:
                inst_id = unpaid[0]["id"]
                already_paid = sum(float(p["amount_received"]) for p in ledger_data.get("payments", []) if p.get("installment_id") == inst_id)
                default_val = float(unpaid[0]["amount"]) - already_paid
        except Exception:
            default_val = 0.0

        dialog = PaymentDialog(self, default_val)
        if dialog.exec() == PaymentDialog.DialogCode.Accepted:
            try:
                self.vm.record_payment(
                    sale_id, 
                    dialog.amount_received, 
                    dialog.payment_date, 
                    dialog.notes
                )
                self.show_toast("Payment successfully processed and applied to the ledger.", "success")
                
                # Invalidate cache for this ledger and update persistent store
                if sale_id in self.cache_ledger_details:
                    del self.cache_ledger_details[sale_id]
                CacheService.set("ledger_details", self.cache_ledger_details)
                self.load_selected_ledger()
            except Exception as e:
                self.show_toast(f"Could not record payment:\n{e}", "error")

    def export_pdf(self, *args):
        sale_id = self.cmb_sales.currentData()
        if not sale_id:
            return
            
        # Select save destination
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Customer Ledger PDF", 
            f"Ledger_{self.cmb_sales.currentText().split(' - ')[0].replace(' ', '_')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
            
        try:
            self.vm.generate_pdf_report(sale_id, file_path)
            self.show_toast(f"PDF Ledger successfully exported to:\n{file_path}", "success")
        except Exception as e:
            self.show_toast(f"Could not compile PDF document:\n{e}", "error")

    def reschedule_ledger(self, *args):
        sale_id = self.cmb_sales.currentData()
        if not sale_id:
            return
            
        try:
            if sale_id in self.cache_ledger_details:
                ledger_data = self.cache_ledger_details[sale_id]
            else:
                ledger_data = self.vm.get_ledger_data(sale_id)
            outstanding_bal = ledger_data["summary"]["outstanding"]
        except Exception:
            outstanding_bal = 0.0

        dialog = RescheduleDialog(self, outstanding_bal)
        if dialog.exec() == RescheduleDialog.DialogCode.Accepted:
            try:
                self.vm.reschedule_installments(
                    sale_id,
                    dialog.new_start_date,
                    dialog.new_duration
                )
                self.show_toast("Installment schedule has been successfully rescheduled.", "success")
                
                # Invalidate cache for this ledger and update persistent store
                if sale_id in self.cache_ledger_details:
                    del self.cache_ledger_details[sale_id]
                CacheService.set("ledger_details", self.cache_ledger_details)
                self.load_selected_ledger()
            except Exception as e:
                self.show_toast(f"Could not reschedule installments:\n{e}", "error")
