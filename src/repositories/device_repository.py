from typing import List, Dict, Any, Optional
from src.repositories.base_repository import BaseRepository

class DeviceRepository(BaseRepository):
    def create(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new device record.
        """
        response = self.db.table("devices").insert(device_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create device record.")

    def update(self, device_id: str, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates an existing device record.
        """
        response = self.db.table("devices").update(device_data).eq("id", device_id).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to update device record.")

    def get_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a device by ID with nested supplier details.
        """
        response = self.db.table("devices").select("*, suppliers(*)").eq("id", device_id).execute()
        return response.data[0] if response.data else None

    def get_all(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Gets all devices with nested supplier details.
        """
        response = self.db.table("devices").select("*, suppliers(*)").order("created_at", desc=True).limit(limit).execute()
        return response.data or []

    def check_imei_exists(self, imei: str, exclude_device_id: Optional[str] = None) -> bool:
        """
        Checks if an IMEI already exists in the database.
        Allows excluding a specific device ID (useful when updating).
        """
        if not imei:
            return False
        
        # Build query checking all four possible IMEI fields
        or_filter = f"imei_1.eq.{imei},imei_2.eq.{imei},imei_3.eq.{imei},imei_4.eq.{imei}"
        query = self.db.table("devices").select("id").or_(or_filter)
        
        if exclude_device_id:
            query = query.neq("id", exclude_device_id)
            
        response = query.execute()
        return len(response.data) > 0

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches devices by name, brand, model, or any IMEI with nested supplier details.
        """
        if not query:
            return self.get_all()
        
        # In Supabase/Postgres/Postgrest raw OR filters, the wildcard character is '*'
        or_filter = (
            f"name.ilike.*{query}*,brand.ilike.*{query}*,model.ilike.*{query}*,"
            f"imei_1.ilike.*{query}*,imei_2.ilike.*{query}*,imei_3.ilike.*{query}*,imei_4.ilike.*{query}*"
        )
        response = self.db.table("devices").select("*, suppliers(*)").or_(or_filter).order("name").execute()
        return response.data or []

    def delete(self, device_id: str):
        """
        Deletes a device record.
        """
        self.db.table("devices").delete().eq("id", device_id).execute()
