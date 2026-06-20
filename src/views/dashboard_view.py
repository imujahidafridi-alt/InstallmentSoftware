from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QMessageBox,
    QTabWidget, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.views.components.metric_card import MetricCard
from src.views.components.chart_widget import ChartWidget
from src.viewmodels.dashboard_viewmodel import DashboardViewModel
from src.viewmodels.installment_viewmodel import InstallmentViewModel
from src.config import ConfigManager
from datetime import datetime
from src.services.cache_service import CacheService

class DashboardWorker(QThread):
    sync_finished = pyqtSignal(dict, dict)
    sync_not_needed = pyqtSignal()
    sync_failed = pyqtSignal(str)

    def __init__(self, db_vm: DashboardViewModel):
        super().__init__()
        self.db_vm = db_vm

    def run(self):
        try:
            changed = CacheService.check_and_update_state("dashboard", self.db_vm.db)
            has_cache = (
                CacheService.get("dashboard_kpis") is not None and
                CacheService.get("dashboard_charts") is not None
            )
            if not changed and has_cache:
                print("[Dashboard] No database changes detected. Loading dashboard from persistent cache.")
                self.sync_not_needed.emit()
                return

            print("[Dashboard] Database changes detected. Updating dashboard from database...")
            kpis = self.db_vm.get_kpis()
            chart_data = self.db_vm.get_charts_data()
            self.sync_finished.emit(kpis, chart_data)
        except Exception as e:
            self.sync_failed.emit(str(e))


class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.db_vm = DashboardViewModel()
        
        self.cache_kpis = CacheService.get("dashboard_kpis")
        self.cache_chart_data = CacheService.get("dashboard_charts")
        
        self.sync_worker = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Header Title
        header_layout = QHBoxLayout()
        lbl_title = QLabel("Executive Dashboard")
        lbl_title.setObjectName("lbl_title")
        header_layout.addWidget(lbl_title)
        
        self.lbl_status = QLabel("Up to date")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #10B981; font-weight: bold;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.lbl_status)
        main_layout.addLayout(header_layout)

        # Scroll Area for responsive dashboard widgets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_content.setObjectName("scroll_content")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # -------------------------------------------------------------
        # 1. KPI CARDS SECTION (3x3 Grid Layout)
        # -------------------------------------------------------------
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(15)
        
        self.card_cust = MetricCard("TOTAL CUSTOMERS", "0", icon_name="users-card")
        self.card_sold = MetricCard("DEVICES SOLD", "0", icon_name="device-card")
        self.card_active = MetricCard("ACTIVE INSTALLMENTS", "0", icon_name="check-list")
        self.card_completed = MetricCard("COMPLETED INSTALLMENTS", "0", icon_name="check-circle")
        self.card_overdue = MetricCard("OVERDUE INSTALLMENTS", "0", icon_name="overdue-alert")
        self.card_outstanding = MetricCard("OUTSTANDING BALANCE", "Rs. 0.00", icon_name="outstanding")
        self.card_month = MetricCard("COLLECTIONS (THIS MONTH)", "Rs. 0.00", icon_name="collections")
        self.card_profit = MetricCard("MONTHLY PROFIT", "Rs. 0.00", icon_name="profit")
        self.card_revenue = MetricCard("NET REVENUE", "Rs. 0.00", icon_name="revenue")
        
        # Row 0
        kpi_grid.addWidget(self.card_cust, 0, 0)
        kpi_grid.addWidget(self.card_sold, 0, 1)
        kpi_grid.addWidget(self.card_active, 0, 2)
        # Row 1
        kpi_grid.addWidget(self.card_completed, 1, 0)
        kpi_grid.addWidget(self.card_overdue, 1, 1)
        kpi_grid.addWidget(self.card_outstanding, 1, 2)
        # Row 2
        kpi_grid.addWidget(self.card_month, 2, 0)
        kpi_grid.addWidget(self.card_profit, 2, 1)
        kpi_grid.addWidget(self.card_revenue, 2, 2)
        
        scroll_layout.addLayout(kpi_grid)

        # -------------------------------------------------------------
        # 2. CHARTS SECTION (QTabWidget grouping 5 charts)
        # -------------------------------------------------------------
        self.charts_tab = QTabWidget()
        self.charts_tab.setFixedHeight(340)

        self.chart_collections = ChartWidget()
        self.chart_profit = ChartWidget()
        self.chart_outstanding = ChartWidget()
        self.chart_recovery = ChartWidget()
        self.chart_completion = ChartWidget()

        # Helper to wrap charts in styled frames
        def wrap_charts(widgets_list):
            frame = QFrame()
            frame.setObjectName("form_card")
            h_layout = QHBoxLayout(frame)
            h_layout.setContentsMargins(10, 10, 10, 10)
            h_layout.setSpacing(15)
            for w in widgets_list:
                h_layout.addWidget(w)
            return frame

        self.charts_tab.addTab(wrap_charts([self.chart_collections, self.chart_profit]), "Collections & Profit Trends")
        self.charts_tab.addTab(wrap_charts([self.chart_outstanding, self.chart_recovery]), "Balance & Recovery Analysis")
        self.charts_tab.addTab(wrap_charts([self.chart_completion]), "Completion Rate Analysis")

        scroll_layout.addWidget(self.charts_tab)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Bind cache immediately if available
        if self.cache_kpis and self.cache_chart_data:
            self.populate_ui(self.cache_kpis, self.cache_chart_data)

    def refresh_data(self):
        if self.cache_kpis and self.cache_chart_data:
            self.populate_ui(self.cache_kpis, self.cache_chart_data)

        if self.sync_worker and self.sync_worker.isRunning():
            return

        self.lbl_status.setText("Updating")
        self.lbl_status.setStyleSheet("color: #F59E0B; font-weight: bold;")

        self.sync_worker = DashboardWorker(self.db_vm)
        self.sync_worker.sync_finished.connect(self.on_sync_success)
        self.sync_worker.sync_not_needed.connect(self.on_sync_not_needed)
        self.sync_worker.sync_failed.connect(self.on_sync_failed)
        self.sync_worker.start()

    def on_sync_success(self, kpis: dict, chart_data: dict):
        self.lbl_status.setText("Up to date")
        self.lbl_status.setStyleSheet("color: #10B981; font-weight: bold;")
        
        self.cache_kpis = kpis
        self.cache_chart_data = chart_data

        CacheService.set("dashboard_kpis", kpis)
        CacheService.set("dashboard_charts", chart_data)
        
        self.populate_ui(kpis, chart_data)
        print("[Dashboard] Dashboard data updated successfully.")

    def on_sync_not_needed(self):
        self.lbl_status.setText("Up to date")
        self.lbl_status.setStyleSheet("color: #10B981; font-weight: bold;")

    def on_sync_failed(self, error_msg: str):
        self.lbl_status.setText("Offline")
        self.lbl_status.setStyleSheet("color: #EF4444; font-weight: bold;")
        print(f"Silent Sync Error: {error_msg}")

    def populate_ui(self, kpis: dict, chart_data: dict):
        config = ConfigManager.load_config()
        theme = config.get("theme", "light")

        # 1. Update metric cards
        self.card_cust.update_value(f"{kpis['total_customers']}")
        self.card_sold.update_value(f"{kpis['total_devices_sold']}")
        self.card_active.update_value(f"{kpis['total_active_installments']}")
        self.card_completed.update_value(f"{kpis['completed_installments']}")
        self.card_overdue.update_value(f"{kpis['overdue_installments']}")
        self.card_outstanding.update_value(ConfigManager.format_currency(kpis['total_outstanding']))
        self.card_month.update_value(ConfigManager.format_currency(kpis['collections_this_month']))
        self.card_profit.update_value(ConfigManager.format_currency(kpis['total_profit']))
        self.card_revenue.update_value(ConfigManager.format_currency(kpis['net_revenue']))

        # 2. Draw Matplotlib charts
        self.chart_collections.draw_chart(chart_data["labels"], chart_data["collections"], "Monthly Collections (Rs.)", "line", theme)
        self.chart_profit.draw_chart(chart_data["labels"], chart_data["profits"], "Monthly Profit Margin Trend (Rs.)", "line", theme)
        self.chart_outstanding.draw_chart(chart_data["labels"], chart_data["outstanding"], "Outstanding Balance Trend (Rs.)", "bar", theme)
        self.chart_recovery.draw_chart(chart_data["labels"], chart_data["recovery"], "Recovery Performance (%)", "line", theme)
        self.chart_completion.draw_chart(["Completed", "Active"], chart_data["completion"], "Installment Completion Rate", "pie", theme)
