from typing import List, Dict, Any, Optional
from src.repositories.base_repository import BaseRepository

class SupplierRepository(BaseRepository):
    def create(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new supplier record.
        supplier_data should contain: name, contact_person, mobile, address, remarks
        """
        response = self.db.table("suppliers").insert(supplier_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create supplier record.")

    def update(self, supplier_id: str, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates an existing supplier record.
        """
        response = self.db.table("suppliers").update(supplier_data).eq("id", supplier_id).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to update supplier record.")

    def get_by_id(self, supplier_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a supplier by ID.
        """
        response = self.db.table("suppliers").select("*").eq("id", supplier_id).execute()
        return response.data[0] if response.data else None

    def get_all(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Gets all supplier records up to limit.
        """
        response = self.db.table("suppliers").select("*").order("name").limit(limit).execute()
        return response.data or []

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches suppliers by name, contact_person, or mobile.
        """
        if not query:
            return self.get_all()
        
        or_filter = f"name.ilike.*{query}*,contact_person.ilike.*{query}*,mobile.ilike.*{query}*"
        response = self.db.table("suppliers").select("*").or_(or_filter).order("name").execute()
        return response.data or []

    def delete(self, supplier_id: str):
        """
        Deletes a supplier record.
        """
        self.db.table("suppliers").delete().eq("id", supplier_id).execute()
