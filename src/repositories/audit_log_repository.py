from typing import List, Dict, Any
from src.repositories.base_repository import BaseRepository

class AuditLogRepository(BaseRepository):
    def create(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts a new audit log record.
        log_data should contain: user_email, action, log_date, log_time, ip_address
        """
        response = self.db.table("audit_logs").insert(log_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to insert audit log record.")

    def get_all(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Gets all audit logs, ordered by created_at desc.
        """
        response = self.db.table("audit_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data or []

    def search(self, query: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Searches and filters audit logs by keyword or date range.
        """
        db_query = self.db.table("audit_logs").select("*")
        if query:
            db_query = db_query.or_(f"user_email.ilike.*{query}*,action.ilike.*{query}*")
        if start_date:
            db_query = db_query.gte("log_date", start_date)
        if end_date:
            db_query = db_query.lte("log_date", end_date)
        
        response = db_query.order("created_at", desc=True).execute()
        return response.data or []

    def clear_all(self):
        """
        Deletes all audit logs safely by targeting non-matching dummy UUID.
        """
        self.db.table("audit_logs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
