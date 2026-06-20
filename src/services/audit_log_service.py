import socket
import urllib.request
import threading
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from src.repositories.audit_log_repository import AuditLogRepository
from src.services.auth_service import AuthService

class AuditLogService:
    _instance = None
    _cached_ip = None
    _ip_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.repo = AuditLogRepository()
            cls._instance.auth = AuthService()
            cls._instance.start_ip_lookup()
        return cls._instance

    def start_ip_lookup(self):
        """Starts a background daemon thread to lookup public IP once."""
        def fetch_ip():
            ip = "127.0.0.1"
            try:
                with urllib.request.urlopen("https://api.ipify.org", timeout=2.0) as response:
                    ip = response.read().decode('utf-8').strip()
            except Exception:
                try:
                    ip = socket.gethostbyname(socket.gethostname())
                except Exception:
                    pass
            with AuditLogService._ip_lock:
                AuditLogService._cached_ip = ip

        threading.Thread(target=fetch_ip, daemon=True).start()

    @staticmethod
    def get_public_ip() -> str:
        """
        Returns cached public IP instantly or resolves local IP immediately without blocking.
        """
        with AuditLogService._ip_lock:
            if AuditLogService._cached_ip is not None:
                return AuditLogService._cached_ip
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

    def log_action(self, action: str, user_email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Logs an administrative action into the database.
        """
        try:
            if not user_email:
                user = self.auth.get_current_user()
                user_email = user.email if user else "system@asifmobile.com"
                
            ip = self.get_public_ip()
            now = datetime.now()
            log_data = {
                "user_email": user_email,
                "action": action,
                "log_date": date.today().strftime("%Y-%m-%d"),
                "log_time": now.strftime("%H:%M:%S"),
                "ip_address": ip
            }
            return self.repo.create(log_data)
        except Exception as e:
            # Fallback defensively so that logging failures never block core workflows
            print(f"Error writing audit log entry: {e}")
            return None

    def get_logs(self, query: str = None, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Retrieves log history, with filters.
        """
        try:
            return self.repo.search(query, start_date, end_date)
        except Exception as e:
            print(f"Error retrieving audit logs: {e}")
            return []

    def clear_logs(self, user_email: Optional[str] = None) -> bool:
        """
        Deletes all logs and writes a final audit log entry about this deletion.
        """
        try:
            self.repo.clear_all()
            self.log_action("Cleared all audit logs", user_email=user_email)
            return True
        except Exception as e:
            print(f"Error clearing audit logs: {e}")
            return False
