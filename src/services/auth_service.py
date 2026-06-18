from typing import Optional, Dict, Any
from src.db.supabase_client import get_db

class AuthService:
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_db()
        return self._db

    def login(self, email: str, password: str) -> bool:
        """
        Signs in the user with email and password via Supabase Auth.
        """
        try:
            # Clear existing session first to ensure clean state
            self.logout()
            
            response = self.db.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            is_success = response.user is not None
            if is_success:
                from src.services.audit_log_service import AuditLogService
                AuditLogService().log_action("User login successful", email)
            return is_success
        except Exception as e:
            print(f"Auth login error: {e}")
            return False

    def logout(self) -> bool:
        """
        Signs out the current user.
        """
        try:
            self.db.auth.sign_out()
            return True
        except Exception as e:
            print(f"Auth logout error: {e}")
            return False

    def get_current_user(self) -> Optional[Any]:
        """
        Gets the currently authenticated user profile info.
        """
        try:
            response = self.db.auth.get_user()
            return response.user if response else None
        except Exception:
            return None

    def is_authenticated(self) -> bool:
        """
        Checks if a user is currently logged in.
        """
        return self.get_current_user() is not None
