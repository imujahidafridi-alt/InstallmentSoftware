import socket
import urllib.request
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from src.repositories.audit_log_repository import AuditLogRepository
from src.services.auth_service import AuthService

class AuditLogService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.repo = AuditLogRepository()
            cls._instance.auth = AuthService()
        return cls._instance

    @staticmethod
    def get_public_ip() -> str:
        """
        Fetches public IP from api.ipify.org with fallback to local machine IP.
        """
        try:
            # Attempt to fetch public IP
            with urllib.request.urlopen("https://api.ipify.org", timeout=2.0) as response:
                return response.read().decode('utf-8').strip()
        except Exception:
            try:
                # Fallback to local network IP
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
