from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, QSize
from PyQt6.QtGui import QColor

class QNotification(QFrame):
    ACTIVE_NOTIFICATIONS = []
    
    WIDTH = 320
    HEIGHT = 65
    MARGIN = 20
    GAP = 10

    def __init__(self, parent, message: str, type: str = "info", duration: int = 4000):
        """
        Creates a custom toast notification widget.
        
        :param parent: The parent widget (should be MainWindow or a large container)
        :param message: Text message to display
        :param type: Type of notification ("success", "error", "warning", "info")
        :param duration: Auto-close timeout in milliseconds (0 to disable auto-close)
        """
        super().__init__(parent)
        self.message = message
        self.type = type.lower()
        self.duration = duration
        
        self.setFixedWidth(self.WIDTH)
        self.setFixedHeight(self.HEIGHT)
        self.setObjectName("notification_card")
        
        # Determine colors and icon based on status type
        if self.type == "success":
            accent_color = "#10B981"  # Emerald green
            bg_color = "#ECFDF5"      # Light green
            border_color = "#A7F3D0"
            icon = "🟢"
        elif self.type == "error":
            accent_color = "#EF4444"  # Rose red
            bg_color = "#FEF2F2"      # Light red
            border_color = "#FCA5A5"
            icon = "🔴"
        elif self.type == "warning":
            accent_color = "#F59E0B"  # Amber orange
            bg_color = "#FFFBEB"      # Light orange
            border_color = "#FDE68A"
            icon = "🟡"
        else:  # info
            accent_color = "#3B82F6"  # Blue
            bg_color = "#EFF6FF"      # Light blue
            border_color = "#BFDBFE"
            icon = "🔵"

        # Apply curated custom stylesheet to look premium and match light mode
        self.setStyleSheet(f"""
            QFrame#notification_card {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-left: 5px solid {accent_color};
                border-radius: 8px;
            }}
            QLabel#msg_label {{
                color: #1E293B;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
            QLabel#icon_label {{
                font-size: 16px;
                background: transparent;
                border: none;
            }}
            QPushButton#close_btn {{
                background: transparent;
                color: #94A3B8;
                font-size: 18px;
                font-weight: bold;
                border: none;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton#close_btn:hover {{
                color: #475569;
            }}
        """)

        # Layout Setup
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Status Icon
        self.lbl_icon = QLabel(icon)
        self.lbl_icon.setObjectName("icon_label")
        self.lbl_icon.setFixedSize(22, 22)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_icon)
        
        # Message Text
        self.lbl_msg = QLabel(message)
        self.lbl_msg.setObjectName("msg_label")
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.lbl_msg)
        
        # Close Button
        self.btn_close = QPushButton("×")
        self.btn_close.setObjectName("close_btn")
        self.btn_close.setFixedSize(16, 16)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.fade_out)
        layout.addWidget(self.btn_close)

        # Set Opacity Effect for fade animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        # Append to active stack and calculate position
        QNotification.ACTIVE_NOTIFICATIONS.append(self)
        
        self.target_y = self.calculate_target_y()
        self.show()
        
        # Animate Slide-In
        self.slide_in()
        
        # Auto-dismiss timer
        if self.duration > 0:
            self.timer = QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.fade_out)
            self.timer.start(self.duration)
            
    def calculate_target_y(self) -> int:
        """Calculates where this toast should be positioned vertically in the parent window."""
        parent = self.parentWidget()
        if not parent:
            return 0
        
        index = QNotification.ACTIVE_NOTIFICATIONS.index(self)
        # Calculate Y starting from bottom
        return parent.height() - (index + 1) * (self.HEIGHT + self.GAP) - self.MARGIN

    def slide_in(self):
        """Animates the notification sliding in from off-screen (right side)."""
        parent = self.parentWidget()
        if not parent:
            return
            
        start_x = parent.width()
        end_x = parent.width() - self.WIDTH - self.MARGIN
        
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(350)
        self.anim.setStartValue(QPoint(start_x, self.target_y))
        self.anim.setEndValue(QPoint(end_x, self.target_y))
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()

    def fade_out(self):
        """Animates the notification fading out when dismissed."""
        # Stop auto-dismiss timer if running
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
            
        # Disable close button to prevent multiple clicks
        self.btn_close.setEnabled(False)
        
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(self.on_fade_finished)
        self.fade_anim.start()

    def on_fade_finished(self):
        """Handles cleanup after fading out, and shifts remaining active notifications."""
        # Remove from active list
        if self in QNotification.ACTIVE_NOTIFICATIONS:
            QNotification.ACTIVE_NOTIFICATIONS.remove(self)
            
        # Hide and delete self
        self.hide()
        self.deleteLater()
        
        # Trigger reposition of remaining active notifications
        QNotification.reposition_all()

    @classmethod
    def reposition_all(cls):
        """Slide remaining notifications to their new positions when one is closed."""
        for index, notif in enumerate(cls.ACTIVE_NOTIFICATIONS):
            parent = notif.parentWidget()
            if not parent:
                continue
                
            new_y = parent.height() - (index + 1) * (cls.HEIGHT + cls.GAP) - cls.MARGIN
            old_pos = notif.pos()
            
            # If the target position changed, run a slide animation to the new position
            if new_y != notif.target_y:
                notif.target_y = new_y
                notif.shift_anim = QPropertyAnimation(notif, b"pos")
                notif.shift_anim.setDuration(250)
                notif.shift_anim.setStartValue(old_pos)
                notif.shift_anim.setEndValue(QPoint(old_pos.x(), new_y))
                notif.shift_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                notif.shift_anim.start()
