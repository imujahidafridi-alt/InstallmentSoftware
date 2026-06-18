from typing import List, Dict, Any, Optional
from src.repositories.base_repository import BaseRepository

class CustomerRepository(BaseRepository):
    def create(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new customer record.
        customer_data should contain: name, father_name, mobile, address, remarks
        """
        response = self.db.table("customers").insert(customer_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create customer record.")

    def update(self, customer_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates an existing customer record.
        """
        response = self.db.table("customers").update(customer_data).eq("id", customer_id).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to update customer record.")

    def get_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a customer by ID.
        """
        response = self.db.table("customers").select("*").eq("id", customer_id).execute()
        return response.data[0] if response.data else None

    def get_all(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Gets all customer records up to limit.
        """
        response = self.db.table("customers").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data or []

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches customers by name or mobile.
        """
        if not query:
            return self.get_all()
        
        # In Supabase/Postgres/Postgrest raw OR filters, the wildcard character is '*'
        or_filter = f"name.ilike.*{query}*,mobile.ilike.*{query}*"
        response = self.db.table("customers").select("*").or_(or_filter).order("name").execute()
        return response.data or []
