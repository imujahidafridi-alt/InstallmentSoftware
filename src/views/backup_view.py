import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QPushButton, QProgressBar, QCheckBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from src.config import ConfigManager

class BackupView(QWidget):
    def __init__(self):
        super().__init__()
        self.auth_worker = None
        self.upload_worker = None
        self.conn_worker = None
        self.connected_email = None
        self.connected_name = None
        self.connected_photo_bytes = None
        self.is_checking_connection = False
        self.init_ui()

    def init_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Page Title
        lbl_title = QLabel("Backup Center")
        lbl_title.setObjectName("lbl_title")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1E293B;")
        main_layout.addWidget(lbl_title)

        # Card container layout (Horizontal side-by-side cards)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)

        # ─── 1. LOCAL BACKUP CARD ───────────────────────────────────────
        local_card = QFrame()
        local_card.setObjectName("backup_card")
        local_card.setStyleSheet("QFrame#backup_card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }")
        
        local_layout = QVBoxLayout(local_card)
        local_layout.setSpacing(14)
        local_layout.setContentsMargins(24, 24, 24, 24)
        local_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_local_title = QLabel("Local Backup & Recovery")
        lbl_local_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        
        lbl_local_desc = QLabel(
            "Export complete offline database snapshots directly to your local computer.\n\n"
            "This creates a compressed ZIP archive containing individual, structured data sheets "
            "for all customers, device inventories, sales ledgers, installments, and payment logs. "
            "Highly recommended for daily physical offline storage."
        )
        lbl_local_desc.setWordWrap(True)
        lbl_local_desc.setStyleSheet("font-size: 12px; color: #64748B; line-height: 18px;")

        self.btn_local_backup = QPushButton("Create Local Backup (.zip)")
        self.btn_local_backup.setStyleSheet(
            "background-color: #1E293B; color: #FFFFFF; border: none; "
            "font-weight: 600; padding: 10px 16px; border-radius: 6px; font-size: 13px;"
        )
        self.btn_local_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_local_backup.clicked.connect(self.start_local_backup)

        self.lbl_last_local_backup = QLabel("Last Local Backup: Never")
        self.lbl_last_local_backup.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500; margin-top: 2px;")

        local_layout.addWidget(lbl_local_title)
        local_layout.addWidget(lbl_local_desc)
        local_layout.addSpacing(10)
        local_layout.addWidget(self.btn_local_backup)
        local_layout.addWidget(self.lbl_last_local_backup)
        local_layout.addStretch()

        cards_layout.addWidget(local_card, 1)

        # ─── 2. GOOGLE DRIVE BACKUP CARD ───────────────────────────────
        drive_card = QFrame()
        drive_card.setObjectName("backup_card")
        drive_card.setStyleSheet("QFrame#backup_card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }")
        
        drive_layout = QVBoxLayout(drive_card)
        drive_layout.setSpacing(14)
        drive_layout.setContentsMargins(24, 24, 24, 24)
        drive_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_drive_title = QLabel("Google Drive Cloud Backup")
        lbl_drive_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        
        lbl_drive_desc = QLabel(
            "Link your Google Account to automatically sync backups directly to the cloud.\n\n"
            "Once connected, you can upload manual snapshots at the click of a button, "
            "or enable automated daily backup syncs in the background when the application closes. "
            "Files are saved securely in a dedicated folder on your Drive."
        )
        lbl_drive_desc.setWordWrap(True)
        lbl_drive_desc.setStyleSheet("font-size: 12px; color: #64748B; line-height: 18px;")

        # Connection status layout (with status text and profile avatar)
        status_layout = QHBoxLayout()
        status_layout.setSpacing(12)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.lbl_profile_pic = QLabel()
        self.lbl_profile_pic.setFixedSize(36, 36)
        self.lbl_profile_pic.setStyleSheet("border-radius: 18px; background-color: #E2E8F0; border: 1px solid #CBD5E1;")
        self.lbl_profile_pic.setVisible(False)
        
        self.lbl_backup_status = QLabel("Checking connection status...")
        self.lbl_backup_status.setStyleSheet("font-weight: 600; font-size: 12px; color: #475569;")
        
        status_layout.addWidget(self.lbl_profile_pic)
        status_layout.addWidget(self.lbl_backup_status)
        
        # Progress bar
        self.progress_backup = QProgressBar()
        self.progress_backup.setFixedHeight(14)
        self.progress_backup.setTextVisible(True)
        self.progress_backup.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_backup.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background-color: #F8FAFC;
                text-align: center;
                font-size: 10px;
                font-weight: bold;
                color: #1E293B;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 5px;
            }
        """)
        self.progress_backup.setVisible(False)

        # Actions Layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_backup_connect = QPushButton("Connect Google Account")
        self.btn_backup_connect.setStyleSheet(
            "background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; "
            "font-weight: 600; padding: 10px 16px; border-radius: 6px; font-size: 13px;"
        )
        self.btn_backup_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_backup_connect.clicked.connect(self.toggle_google_connection)
        
        self.btn_backup_now = QPushButton("Back Up to Drive")
        self.btn_backup_now.setStyleSheet(
            "background-color: #3B82F6; color: #FFFFFF; border: none; "
            "font-weight: 600; padding: 10px 16px; border-radius: 6px; font-size: 13px;"
        )
        self.btn_backup_now.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_backup_now.clicked.connect(self.start_backup_upload)
        self.btn_backup_now.setEnabled(False)
        
        btn_layout.addWidget(self.btn_backup_connect, 1)
        btn_layout.addWidget(self.btn_backup_now, 1)

        # Auto backup checkbox
        self.chk_auto_backup = QCheckBox("Auto-Backup database to Google Drive on application close")
        self.chk_auto_backup.setStyleSheet("font-size: 11px; color: #475569; margin-top: 4px;")
        self.chk_auto_backup.toggled.connect(self.save_auto_backup_setting)

        # Last backup label
        self.lbl_last_drive_backup = QLabel("Last Cloud Backup: Never")
        self.lbl_last_drive_backup.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500; margin-top: 2px;")

        # Help Info label (shown when client_secrets.json is missing)
        self.lbl_backup_help = QLabel()
        self.lbl_backup_help.setWordWrap(True)
        self.lbl_backup_help.setStyleSheet("font-size: 10px; color: #94A3B8; line-height: 14px; margin-top: 4px;")
        self.lbl_backup_help.setVisible(False)

        drive_layout.addWidget(lbl_drive_title)
        drive_layout.addWidget(lbl_drive_desc)
        drive_layout.addLayout(status_layout)
        drive_layout.addWidget(self.progress_backup)
        drive_layout.addLayout(btn_layout)
        drive_layout.addWidget(self.chk_auto_backup)
        drive_layout.addWidget(self.lbl_last_drive_backup)
        drive_layout.addWidget(self.lbl_backup_help)
        drive_layout.addStretch()

        cards_layout.addWidget(drive_card, 1)

        main_layout.addLayout(cards_layout)
        main_layout.addStretch()

    # ──────────────────────────────────────────────────────────────────
    # Operations & Service Integration
    # ──────────────────────────────────────────────────────────────────

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

    def load_backup_settings(self):
        """Loads auto-backup settings and refreshes connection state."""
        try:
            config = ConfigManager.load_config()
            auto_backup = config.get("auto_backup", False)
            self.chk_auto_backup.setChecked(auto_backup)
            self.update_backup_ui()
        except Exception as e:
            print(f"Error loading backup settings: {e}")

    def update_backup_ui(self):
        """Updates Google Drive connection state & visual handles using cached non-blocking info."""
        try:
            from src.services.backup_service import BackupService
            
            # Update last backup timestamps
            config = ConfigManager.load_config()
            last_local = config.get("last_local_backup", "Never")
            self.lbl_last_local_backup.setText(f"Last Local Backup: {last_local}")
            
            last_drive = config.get("last_drive_backup", "Never")
            self.lbl_last_drive_backup.setText(f"Last Cloud Backup: {last_drive}")
            
            if not BackupService.is_google_configured():
                self.lbl_backup_status.setText("⚠️ Google API is not configured (Client Secrets missing)")
                self.lbl_backup_status.setStyleSheet("font-weight: 600; font-size: 12px; color: #EA580C;")
                self.btn_backup_connect.setEnabled(False)
                self.btn_backup_now.setEnabled(False)
                self.btn_backup_now.setStyleSheet("background-color: #CBD5E1; color: #94A3B8; border: none; font-weight: 600; padding: 10px 16px; border-radius: 6px;")
                self.chk_auto_backup.setEnabled(False)
                self.lbl_profile_pic.setVisible(False)
                
                secrets_path = BackupService.get_client_secrets_path()
                self.lbl_backup_help.setText(
                    f"Administrator Note: To enable cloud backups, place your Google Cloud Console "
                    f"Desktop Credentials file as 'client_secrets.json' in your application folder at:\n{secrets_path}"
                )
                self.lbl_backup_help.setVisible(True)
                return
                
            self.lbl_backup_help.setVisible(False)
            self.chk_auto_backup.setEnabled(True)
            
            if self.is_checking_connection:
                self.lbl_backup_status.setText("Checking connection status...")
                self.lbl_backup_status.setStyleSheet("font-weight: 600; font-size: 12px; color: #2563EB;")
                self.btn_backup_connect.setEnabled(False)
                self.btn_backup_now.setEnabled(False)
                self.btn_backup_now.setStyleSheet("background-color: #CBD5E1; color: #94A3B8; border: none; font-weight: 600; padding: 10px 16px; border-radius: 6px;")
                self.lbl_profile_pic.setVisible(False)
            elif self.connected_email:
                self.lbl_backup_status.setText(f"• Connected:\n  {self.connected_name}\n  ({self.connected_email})")
                self.lbl_backup_status.setStyleSheet("font-weight: 600; font-size: 12px; color: #16A34A; line-height: 16px;")
                self.btn_backup_connect.setText("Disconnect Account")
                self.btn_backup_connect.setEnabled(True)
                self.btn_backup_now.setEnabled(True)
                self.btn_backup_now.setStyleSheet("background-color: #3B82F6; color: #FFFFFF; border: none; font-weight: 600; padding: 10px 16px; border-radius: 6px;")
                
                # Load circular profile photo if available
                if self.connected_photo_bytes:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(self.connected_photo_bytes):
                        circular_pixmap = self.get_circular_pixmap(pixmap)
                        self.lbl_profile_pic.setPixmap(circular_pixmap)
                        self.lbl_profile_pic.setVisible(True)
                    else:
                        self.lbl_profile_pic.setVisible(False)
                else:
                    self.lbl_profile_pic.setVisible(False)
            else:
                self.lbl_backup_status.setText("• Google Drive Disconnected")
                self.lbl_backup_status.setStyleSheet("font-weight: 600; font-size: 12px; color: #64748B;")
                self.btn_backup_connect.setText("Connect Google Account")
                self.btn_backup_connect.setEnabled(True)
                self.btn_backup_now.setEnabled(False)
                self.btn_backup_now.setStyleSheet("background-color: #CBD5E1; color: #94A3B8; border: none; font-weight: 600; padding: 10px 16px; border-radius: 6px;")
                self.lbl_profile_pic.setVisible(False)
        except Exception as e:
            print(f"Error updating backup UI: {e}")

    def toggle_google_connection(self):
        try:
            from src.services.backup_service import BackupService
            
            if self.connected_email:
                # Disconnect
                BackupService.disconnect_google()
                self.connected_email = None
                self.connected_name = None
                self.connected_photo_bytes = None
                self.show_toast("Google Account disconnected successfully.", "info")
                self.update_backup_ui()
            else:
                # Connect
                self.btn_backup_connect.setEnabled(False)
                self.btn_backup_connect.setText("Connecting...")
                self.lbl_backup_status.setText("Please complete authorization in your web browser...")
                self.lbl_backup_status.setStyleSheet("font-weight: 600; font-size: 12px; color: #2563EB;")
                
                from src.views.components.backup_worker import BackupWorker
                self.auth_worker = BackupWorker("authenticate")
                self.auth_worker.finished.connect(self.on_auth_finished)
                self.auth_worker.start()
        except Exception as e:
            self.show_toast(f"Failed to toggle connection: {e}", "error")

    def on_auth_finished(self, success: bool, msg: str):
        self.btn_backup_connect.setEnabled(True)
        if success:
            self.show_toast("Google Account connected successfully.", "success")
            self.refresh_connection_status()
        else:
            self.show_toast(f"Authentication failed: {msg}", "error")
            self.update_backup_ui()

    def start_backup_upload(self):
        self.btn_backup_now.setEnabled(False)
        self.btn_backup_connect.setEnabled(False)
        self.progress_backup.setValue(0)
        self.progress_backup.setVisible(True)
        self.lbl_backup_status.setText("Creating compressed database backup archive...")
        self.lbl_backup_status.setStyleSheet("font-weight: 600; font-size: 12px; color: #2563EB;")
        
        from src.views.components.backup_worker import BackupWorker
        self.upload_worker = BackupWorker("backup")
        self.upload_worker.progress_updated.connect(self.on_backup_progress)
        self.upload_worker.finished.connect(self.on_backup_finished)
        self.upload_worker.start()

    def on_backup_progress(self, val: int):
        self.progress_backup.setValue(val)
        if val < 30:
            self.lbl_backup_status.setText("Creating compressed database backup archive...")
        elif val < 100:
            self.lbl_backup_status.setText("Uploading backup archive to Google Drive...")

    def on_backup_finished(self, success: bool, result: str):
        self.progress_backup.setVisible(False)
        
        if success:
            # Save the backup timestamp in config
            config = ConfigManager.load_config()
            config["last_drive_backup"] = datetime.now().strftime("%Y-%m-%d %I:%M %p")
            ConfigManager.save_config(config)
            
            self.show_toast("Database backup uploaded successfully to Google Drive!", "success")
            try:
                from src.services.audit_log_service import AuditLogService
                AuditLogService().log_action("Uploaded manual database backup to Google Drive")
            except Exception:
                pass
        else:
            self.show_toast(f"Backup upload failed: {result}", "error")
        
        self.update_backup_ui()

    def save_auto_backup_setting(self, checked: bool):
        try:
            config = ConfigManager.load_config()
            config["auto_backup"] = checked
            ConfigManager.save_config(config)
        except Exception as e:
            print(f"Failed to save auto-backup setting: {e}")

    def start_local_backup(self):
        # Open Save File Dialog
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        default_filename = f"EasyQist_Local_Backup_{timestamp}.zip"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Local Database Backup",
            default_filename,
            "ZIP Archives (*.zip)"
        )
        
        if not file_path:
            return
            
        try:
            self.show_toast("Creating local database backup...", "info")
            from src.services.backup_service import BackupService
            
            # Create backup ZIP in temporary folder
            temp_zip, filename = BackupService.create_database_backup()
            
            # Copy it to the user's chosen location
            shutil.copy2(temp_zip, file_path)
            
            # Clean up temp file
            try:
                os.remove(temp_zip)
            except Exception:
                pass
                
            self.show_toast("Local database backup saved successfully!", "success")
            
            # Save the backup timestamp in config
            config = ConfigManager.load_config()
            config["last_local_backup"] = datetime.now().strftime("%Y-%m-%d %I:%M %p")
            ConfigManager.save_config(config)
            self.update_backup_ui()
            
            # Log audit event
            try:
                from src.services.audit_log_service import AuditLogService
                AuditLogService().log_action(f"Created local database backup: {os.path.basename(file_path)}")
            except Exception:
                pass
        except Exception as e:
            self.show_toast(f"Failed to create local backup: {e}", "error")

    # ──────────────────────────────────────────────────────────────────
    # Asynchronous Connection Checking & Profile Photo Drawing
    # ──────────────────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        self.load_backup_settings()
        self.refresh_connection_status()

    def refresh_connection_status(self):
        """Starts a background thread to check Google connection and fetch user details."""
        from src.services.backup_service import BackupService
        if not BackupService.is_google_configured():
            self.connected_email = None
            self.connected_name = None
            self.connected_photo_bytes = None
            self.update_backup_ui()
            return

        if self.is_checking_connection:
            return

        self.is_checking_connection = True
        self.update_backup_ui()

        from src.views.components.backup_worker import BackupWorker
        self.conn_worker = BackupWorker("check_connection")
        self.conn_worker.connection_checked.connect(self.on_connection_checked)
        self.conn_worker.start()

    def on_connection_checked(self, success: bool, email: str, name: str, photo_bytes: bytes):
        self.is_checking_connection = False
        if success and email:
            self.connected_email = email
            self.connected_name = name or "Google User"
            self.connected_photo_bytes = photo_bytes if photo_bytes else None
        else:
            self.connected_email = None
            self.connected_name = None
            self.connected_photo_bytes = None
        self.update_backup_ui()

    def get_circular_pixmap(self, pixmap, size=36):
        """Crops a QPixmap to a perfect anti-aliased circle of the given size."""
        # Scale pixmap
        scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        
        # Create target pixmap
        out_pixmap = QPixmap(size, size)
        out_pixmap.fill(Qt.GlobalColor.transparent)
        
        # Paint circular image
        painter = QPainter(out_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        
        # Draw the scaled pixmap centered
        x = (size - scaled.width()) // 2
        y = (size - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        
        return out_pixmap
