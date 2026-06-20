import re
from typing import Dict, Any, List, Tuple, Optional
from src.repositories.device_repository import DeviceRepository

class DeviceViewModel:
    def __init__(self):
        self.repo = DeviceRepository()

    def validate_device_data(
        self,
        name: str,
        brand: str,
        model: str,
        ram: str,
        rom: str,
        sim_type: int,
        imeis: List[str],
        exclude_device_id: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validates brand, model, ram, rom, and the dynamic IMEIs list.
        Checks for numeric character constraint, length (15 digits),
        duplicates within fields, and duplicates in database.
        """
        errors = []
        if not name.strip():
            errors.append("Device Name is required.")
        if not ram.strip():
            errors.append("RAM is required.")
        if not rom.strip():
            errors.append("ROM is required.")
            
        if not (1 <= sim_type <= 4):
            errors.append("SIM Configuration must be between 1 and 4 SIMs.")

        # Filter the IMEIs list to check only active slots based on sim_type
        active_imeis = [imei.strip() for imei in imeis[:sim_type]]
        
        imei_pattern = r"^\d{15}$"
        seen_imeis = set()
        
        for idx, imei in enumerate(active_imeis, 1):
            if imei:  # Only validate if the user has filled in this IMEI slot
                # Format check
                if not re.match(imei_pattern, imei):
                    errors.append(f"IMEI {idx} ({imei}) must be exactly 15 digits (numeric only).")
                    continue
                
                # Internal duplicates check
                if imei in seen_imeis:
                    errors.append(f"Duplicate IMEI input detected: {imei}")
                seen_imeis.add(imei)
                
                # Database unique constraint check
                if self.repo.check_imei_exists(imei, exclude_device_id):
                    errors.append(f"IMEI {imei} is already registered on another device.")
                    
        return len(errors) == 0, errors

    def register_device(
        self,
        name: str,
        brand: str,
        model: str,
        ram: str,
        rom: str,
        sim_type: int,
        imeis: List[str]
    ) -> Dict[str, Any]:
        """
        Registers a new device in the inventory.
        """
        imeis = list(imeis)
        while len(imeis) < 4:
            imeis.append("")

        # Auto-generate IMEI 1 if left blank to satisfy database constraints
        if not imeis[0].strip():
            import random
            while True:
                val = f"00{random.randint(1000000000000, 9999999999999)}"
                if not self.repo.check_imei_exists(val):
                    imeis[0] = val
                    break

        is_valid, errors = self.validate_device_data(name, brand, model, ram, rom, sim_type, imeis)
        if not is_valid:
            raise ValueError("\n".join(errors))

        device_data = {
            "name": name.strip(),
            "brand": brand.strip() if brand.strip() else "-",
            "model": model.strip() if model.strip() else "-",
            "ram": ram.strip(),
            "rom": rom.strip(),
            "sim_type": sim_type,
            "imei_1": imeis[0].strip(),
            "imei_2": imeis[1].strip() if sim_type >= 2 and len(imeis) > 1 and imeis[1].strip() else None,
            "imei_3": imeis[2].strip() if sim_type >= 3 and len(imeis) > 2 and imeis[2].strip() else None,
            "imei_4": imeis[3].strip() if sim_type >= 4 and len(imeis) > 3 and imeis[3].strip() else None,
        }
        
        result = self.repo.create(device_data)
        from src.services.cache_service import CacheService
        CacheService.clear()
        return result

    def search_devices(self, query: str) -> List[Dict[str, Any]]:
        """Searches device records."""
        return self.repo.search(query)

    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Queries all devices."""
        return self.repo.get_all()

    def get_available_and_sold_devices(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Splits devices into available (unsold) and sold lists."""
        all_devices = self.get_all_devices()
        from src.repositories.sale_repository import SaleRepository
        sale_repo = SaleRepository()
        sales = sale_repo.get_all_with_details()
        sold_ids = {s["device_id"] for s in sales if "device_id" in s}
        
        available = [d for d in all_devices if d["id"] not in sold_ids]
        sold = [d for d in all_devices if d["id"] in sold_ids]
        return available, sold

    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Gets only available (unsold) devices."""
        available, _ = self.get_available_and_sold_devices()
        return available

    def is_device_sold(self, device_id: str) -> bool:
        from src.repositories.sale_repository import SaleRepository
        sale_repo = SaleRepository()
        sales_res = sale_repo.db.table("sales").select("id").eq("device_id", device_id).execute()
        return len(sales_res.data) > 0

    def update_device(
        self,
        device_id: str,
        name: str,
        brand: str,
        model: str,
        ram: str,
        rom: str,
        sim_type: int,
        imeis: List[str]
    ) -> Dict[str, Any]:
        """
        Updates an existing device record if it's not sold.
        """
        if self.is_device_sold(device_id):
            raise ValueError("This device is already sold and cannot be edited.")

        imeis = list(imeis)
        while len(imeis) < 4:
            imeis.append("")

        # Auto-generate IMEI 1 if left blank
        if not imeis[0].strip():
            import random
            while True:
                val = f"00{random.randint(1000000000000, 9999999999999)}"
                if not self.repo.check_imei_exists(val, exclude_device_id=device_id):
                    imeis[0] = val
                    break

        is_valid, errors = self.validate_device_data(name, brand, model, ram, rom, sim_type, imeis, exclude_device_id=device_id)
        if not is_valid:
            raise ValueError("\n".join(errors))

        device_data = {
            "name": name.strip(),
            "brand": brand.strip() if brand.strip() else "-",
            "model": model.strip() if model.strip() else "-",
            "ram": ram.strip(),
            "rom": rom.strip(),
            "sim_type": sim_type,
            "imei_1": imeis[0].strip(),
            "imei_2": imeis[1].strip() if sim_type >= 2 and len(imeis) > 1 and imeis[1].strip() else None,
            "imei_3": imeis[2].strip() if sim_type >= 3 and len(imeis) > 2 and imeis[2].strip() else None,
            "imei_4": imeis[3].strip() if sim_type >= 4 and len(imeis) > 3 and imeis[3].strip() else None,
        }

        result = self.repo.update(device_id, device_data)
        from src.services.cache_service import CacheService
        CacheService.clear()

        from src.services.audit_log_service import AuditLogService
        AuditLogService().log_action(f"Updated Device: {result['brand']} {result['model']} (ID: {device_id})")
        return result

    def delete_device(self, device_id: str) -> bool:
        """
        Deletes a device from the database if it is not sold.
        """
        if self.is_device_sold(device_id):
            raise ValueError("This device is already sold and cannot be deleted.")

        self.repo.delete(device_id)
        from src.services.cache_service import CacheService
        CacheService.clear()

        from src.services.audit_log_service import AuditLogService
        AuditLogService().log_action(f"Deleted Device ID: {device_id}")
        return True
