import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "icons")


class MetricCard(QFrame):
    def __init__(self, title: str, value: str = "0", icon_name: str = None):
        super().__init__()
        self.setObjectName("metric_card")
        self.init_ui(title, value, icon_name)

    def init_ui(self, title: str, value: str, icon_name: str = None):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # --- Top row: icon + title ---
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        if icon_name:
            icon_path = os.path.join(ICONS_DIR, f"{icon_name}.svg")
            lbl_icon = QLabel()
            lbl_icon.setFixedSize(28, 28)
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if os.path.exists(icon_path):
                lbl_icon.setPixmap(QIcon(icon_path).pixmap(22, 22))
            top_row.addWidget(lbl_icon)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("lbl_metric_title")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_title.setWordWrap(True)
        top_row.addWidget(self.lbl_title, 1)

        layout.addLayout(top_row)

        # --- Value row ---
        self.lbl_value = QLabel(value)
        self.lbl_value.setObjectName("lbl_metric_value")
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.lbl_value)

    def update_value(self, value: str):
        self.lbl_value.setText(value)
