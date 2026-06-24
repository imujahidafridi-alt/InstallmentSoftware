from PyQt6.QtCore import QThread, pyqtSignal
from src.services.backup_service import BackupService

class BackupWorker(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    connection_checked = pyqtSignal(bool, str, str, bytes)

    def __init__(self, action: str):
        """
        Action can be:
        - "authenticate": Runs Google OAuth 2.0 loopback server
        - "backup": Creates local backup and uploads to Google Drive
        - "check_connection": Fetches Google Account details (email, name, photo)
        """
        super().__init__()
        self.action = action

    def run(self):
        if self.action == "authenticate":
            # Start loopback authentication
            # Set port to 0 to automatically pick a free port
            success, msg = BackupService.authenticate_google()
            self.finished.emit(success, msg)
            
        elif self.action == "check_connection":
            try:
                email, name, photo_bytes = BackupService.get_connected_account_details()
                self.connection_checked.emit(email is not None, email or "", name or "", photo_bytes or b"")
            except Exception:
                self.connection_checked.emit(False, "", "", b"")
            
        elif self.action == "backup":
            try:
                # 1. Create the backup zip locally
                self.progress_updated.emit(10)  # Initial progress
                zip_path, zip_filename = BackupService.create_database_backup()
                self.progress_updated.emit(30)  # Backup created successfully
                
                # 2. Upload to Google Drive with progress callback
                def update_progress(p):
                    # Map upload percentage (0-100) to progress bar range (30-100)
                    mapped_progress = 30 + int(p * 0.7)
                    self.progress_updated.emit(mapped_progress)

                success, result = BackupService.upload_backup_to_drive(
                    zip_path, 
                    zip_filename, 
                    progress_callback=update_progress
                )
                
                if success:
                    self.progress_updated.emit(100)
                    self.finished.emit(True, "Backup successfully uploaded to Google Drive!")
                else:
                    self.finished.emit(False, result)
                    
            except Exception as e:
                self.finished.emit(False, str(e))
