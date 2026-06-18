from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class MetricCard(QFrame):
    def __init__(self, title: str, value: str = "0"):
        super().__init__()
        self.setObjectName("metric_card")
        self.init_ui(title, value)

    def init_ui(self, title: str, value: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("lbl_metric_title")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setObjectName("lbl_metric_value")
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

    def update_value(self, value: str):
        self.lbl_value.setText(value)
