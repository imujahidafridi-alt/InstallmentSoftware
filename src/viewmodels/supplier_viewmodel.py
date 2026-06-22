import re
from typing import Dict, Any, List, Tuple
from src.repositories.supplier_repository import SupplierRepository
from src.services.cache_service import CacheService
from src.services.audit_log_service import AuditLogService

class SupplierViewModel:
    def __init__(self):
        self.repo = SupplierRepository()

    def validate_supplier_data(self, name: str, mobile: str) -> Tuple[bool, List[str]]:
        """
        Validates supplier data before database insertion.
        Returns (is_valid, list_of_errors).
        """
        errors = []
        if not name.strip():
            errors.append("Supplier Name is required.")
            
        # Mobile Regex Validation (03XXXXXXXXX or any 11 digits starting with 03)
        mobile_pattern = r"^03\d{9}$"
        if not re.match(mobile_pattern, mobile.strip()):
            errors.append("Mobile Number must be in format 03XXXXXXXXX (11 digits starting with 03).")
            
        return len(errors) == 0, errors

    def register_supplier(self, name: str, contact_person: str, mobile: str, address: str, remarks: str) -> Dict[str, Any]:
        """
        Validates and registers a new supplier record.
        """
        is_valid, errors = self.validate_supplier_data(name, mobile)
        if not is_valid:
            raise ValueError("\n".join(errors))
            
        supplier_data = {
            "name": name.strip(),
            "contact_person": contact_person.strip() if contact_person else None,
            "mobile": mobile.strip(),
            "address": address.strip() if address else None,
            "remarks": remarks.strip() if remarks else None
        }
        
        result = self.repo.create(supplier_data)
        CacheService.clear()
        
        try:
            AuditLogService().log_action(f"Created Supplier: {result['name']} (Mobile: {result['mobile']})")
        except Exception as e:
            print(f"Audit log failed: {e}")
            
        return result

    def update_supplier(self, supplier_id: str, name: str, contact_person: str, mobile: str, address: str, remarks: str) -> Dict[str, Any]:
        """
        Validates and updates an existing supplier record.
        """
        is_valid, errors = self.validate_supplier_data(name, mobile)
        if not is_valid:
            raise ValueError("\n".join(errors))
            
        supplier_data = {
            "name": name.strip(),
            "contact_person": contact_person.strip() if contact_person else None,
            "mobile": mobile.strip(),
            "address": address.strip() if address else None,
            "remarks": remarks.strip() if remarks else None
        }
        
        result = self.repo.update(supplier_id, supplier_data)
        CacheService.clear()
        
        try:
            AuditLogService().log_action(f"Updated Supplier: {result['name']} (ID: {supplier_id})")
        except Exception as e:
            print(f"Audit log failed: {e}")
            
        return result

    def get_all_suppliers(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieves all suppliers.
        """
        return self.repo.get_all(limit)

    def search_suppliers(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches suppliers by name, contact, or mobile.
        """
        return self.repo.search(query)

    def delete_supplier(self, supplier_id: str):
        """
        Deletes a supplier by ID.
        """
        supplier = self.repo.get_by_id(supplier_id)
        supplier_name = supplier["name"] if supplier else supplier_id
        
        self.repo.delete(supplier_id)
        CacheService.clear()
        
        try:
            AuditLogService().log_action(f"Deleted Supplier: {supplier_name} (ID: {supplier_id})")
        except Exception as e:
            print(f"Audit log failed: {e}")
