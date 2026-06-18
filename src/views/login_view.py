from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt, QThread
from src.services.auth_service import AuthService

class LoginWorker(QThread):
    finished = pyqtSignal(bool)
    failed = pyqtSignal(str)

    def __init__(self, auth_service: AuthService, email: str, password: str):
        super().__init__()
        self.auth_service = auth_service
        self.email = email
        self.password = password

    def run(self):
        try:
            success = self.auth_service.login(self.email, self.password)
            self.finished.emit(success)
        except Exception as e:
            self.failed.emit(str(e))

class LoginView(QWidget):
    login_success = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.setObjectName("login_window")
        self.setWindowTitle("Sign In - Asif Mobile Center")
        self.resize(460, 650)
        self.setMinimumSize(450, 630)
        self.setMaximumSize(520, 750)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(35, 25, 35, 25)
        main_layout.setSpacing(15)

        # =============================================================
        # 1. APPLICATION HEADER LOGO/TITLE
        # =============================================================
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.setSpacing(4)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        from PyQt6.QtGui import QPixmap
        import os

        lbl_app_logo = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_app_logo.setPixmap(scaled_pixmap)
        else:
            lbl_app_logo.setText("📱")
            lbl_app_logo.setStyleSheet("font-size: 36px; margin-bottom: 5px;")
        lbl_app_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(lbl_app_logo)

        lbl_app_title = QLabel("Asif Mobile Center")
        lbl_app_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0F172A;")
        lbl_app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(lbl_app_title)

        lbl_app_subtitle = QLabel("Buy · Sell · Repair · Accessories")
        lbl_app_subtitle.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500;")
        lbl_app_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(lbl_app_subtitle)

        main_layout.addWidget(header_widget)

        # =============================================================
        # 2. SECURE LOGIN CARD
        # =============================================================
        card = QFrame()
        card.setObjectName("form_card")
        card.setStyleSheet("QFrame#form_card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(12)
        
        lbl_card_title = QLabel("Sign In")
        lbl_card_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-bottom: 4px;")
        lbl_card_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(lbl_card_title)
        
        # Email Input
        lbl_email_hdr = QLabel("Email Address")
        lbl_email_hdr.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Enter your email address")
        self.txt_email.setFixedHeight(35)
        self.txt_email.setStyleSheet("QLineEdit { border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 10px; color: #0F172A; } QLineEdit:focus { border: 1px solid #3B82F6; }")
        card_layout.addWidget(lbl_email_hdr)
        card_layout.addWidget(self.txt_email)
        
        # Password Input
        lbl_pwd_hdr = QLabel("Password")
        lbl_pwd_hdr.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Enter your password")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setFixedHeight(35)
        self.txt_password.setStyleSheet("QLineEdit { border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 10px; color: #0F172A; } QLineEdit:focus { border: 1px solid #3B82F6; }")
        card_layout.addWidget(lbl_pwd_hdr)
        card_layout.addWidget(self.txt_password)
        
        # Login Button
        self.btn_login = QPushButton("Sign In")
        self.btn_login.setFixedHeight(38)
        self.btn_login.setStyleSheet("QPushButton { background-color: #2563EB; color: #FFFFFF; font-weight: bold; border-radius: 6px; font-size: 12px; } QPushButton:hover { background-color: #1D4ED8; } QPushButton:pressed { background-color: #1E40AF; }")
        self.btn_login.clicked.connect(self.handle_login)
        card_layout.addWidget(self.btn_login)
        
        main_layout.addWidget(card)

        # =============================================================
        # 3. FOOTER SECURITY / SYSTEM STATS
        # =============================================================
        footer_widget = QWidget()
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 5, 0, 0)
        footer_layout.setSpacing(4)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_sec_warning = QLabel("🔒 Staff Access Only")
        lbl_sec_warning.setStyleSheet("font-size: 10px; font-weight: 600; color: #EF4444;")
        lbl_sec_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(lbl_sec_warning)

        lbl_cloud_sync = QLabel("✔ Secure Cloud Sync Active")
        lbl_cloud_sync.setStyleSheet("font-size: 10px; color: #10B981; font-weight: 500;")
        lbl_cloud_sync.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(lbl_cloud_sync)

        lbl_version = QLabel("Version 1.0.0")
        lbl_version.setStyleSheet("font-size: 9px; color: #94A3B8;")
        lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(lbl_version)

        main_layout.addWidget(footer_widget)

    def handle_login(self, *args):
        email = self.txt_email.text().strip()
        password = self.txt_password.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Required Input", "Please enter both Email and Password.")
            return
            
        self.btn_login.setEnabled(False)
        self.btn_login.setText("Signing In...")
        
        self.worker = LoginWorker(self.auth_service, email, password)
        self.worker.finished.connect(self.on_login_finished)
        self.worker.failed.connect(self.on_login_failed)
        self.worker.start()

    def on_login_finished(self, success: bool):
        self.btn_login.setEnabled(True)
        self.btn_login.setText("Sign In")
        if success:
            self.login_success.emit()
        else:
            QMessageBox.critical(
                self, 
                "Login Failed", 
                "Incorrect email or password. Please try again."
            )

    def on_login_failed(self, error_msg: str):
        self.btn_login.setEnabled(True)
        self.btn_login.setText("Sign In")
        QMessageBox.critical(
            self, 
            "Connection Error", 
            "Could not connect to the server. Please check your internet connection."
        )
