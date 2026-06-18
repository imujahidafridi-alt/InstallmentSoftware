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
