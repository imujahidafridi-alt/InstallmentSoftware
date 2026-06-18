import re
from typing import Dict, Any, List, Tuple
from src.repositories.customer_repository import CustomerRepository

class CustomerViewModel:
    def __init__(self):
        self.repo = CustomerRepository()

    def validate_customer_data(self, name: str, father_name: str, mobile: str) -> Tuple[bool, List[str]]:
        """
        Validates customer data before database insertion.
        Returns (is_valid, list_of_errors).
        """
        errors = []
        if not name.strip():
            errors.append("Customer Name is required.")
        if not father_name.strip():
            errors.append("Father Name is required.")
            
        # Mobile Regex Validation (03XXXXXXXXX)
        mobile_pattern = r"^03\d{9}$"
        if not re.match(mobile_pattern, mobile.strip()):
            errors.append("Mobile Number must be in format 03XXXXXXXXX (11 digits starting with 03).")
            
        return len(errors) == 0, errors

    def register_customer(self, name: str, father_name: str, mobile: str, address: str, remarks: str, reminders_enabled: bool = True) -> Dict[str, Any]:
        """
        Validates and registers a new customer record.
        """
        is_valid, errors = self.validate_customer_data(name, father_name, mobile)
        if not is_valid:
            raise ValueError("\n".join(errors))
            
        customer_data = {
            "name": name.strip(),
            "father_name": father_name.strip(),
            "mobile": mobile.strip(),
            "address": address.strip() if address else None,
            "remarks": remarks.strip() if remarks else None,
            "reminders_enabled": reminders_enabled
        }
        
        result = self.repo.create(customer_data)
        from src.services.audit_log_service import AuditLogService
        AuditLogService().log_action(f"Created Customer: {result['name']} (Mobile: {result['mobile']})")
        return result

    def update_customer(self, customer_id: str, name: str, father_name: str, mobile: str, address: str, remarks: str, reminders_enabled: bool = True) -> Dict[str, Any]:
        """
        Validates and updates an existing customer record.
        """
        is_valid, errors = self.validate_customer_data(name, father_name, mobile)
        if not is_valid:
            raise ValueError("\n".join(errors))
            
        customer_data = {
            "name": name.strip(),
            "father_name": father_name.strip(),
            "mobile": mobile.strip(),
            "address": address.strip() if address else None,
            "remarks": remarks.strip() if remarks else None,
            "reminders_enabled": reminders_enabled
        }
        
        result = self.repo.update(customer_id, customer_data)
        from src.services.audit_log_service import AuditLogService
        reminders_str = "Reminders Enabled" if reminders_enabled else "Reminders Disabled"
        AuditLogService().log_action(f"Updated Customer: {result['name']} (Mobile: {result['mobile']}) - {reminders_str}")
        return result

    def search_customers(self, query: str) -> List[Dict[str, Any]]:
        """Queries customer data."""
        return self.repo.search(query)

    def get_all_customers(self) -> List[Dict[str, Any]]:
        """Queries all customer records."""
        return self.repo.get_all()
