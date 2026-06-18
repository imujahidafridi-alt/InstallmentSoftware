from typing import Dict, Any, List, Tuple, Optional
from datetime import date
from src.repositories.sale_repository import SaleRepository

class SaleViewModel:
    def __init__(self):
        self.repo = SaleRepository()

    def calculate_margin(self, selling_price: float, cost_price: float) -> Tuple[float, float]:
        """
        Calculates margin amount and margin percentage.
        Formula: Margin = Selling Price - Cost Price
        Percentage: Margin % = (Margin / Cost Price) * 100
        """
        margin_amt = selling_price - cost_price
        margin_pct = 0.0
        if cost_price > 0:
            margin_pct = (margin_amt / cost_price) * 100
        return round(margin_amt, 2), round(margin_pct, 2)

    def calculate_monthly_installment(self, selling_price: float, down_payment: float, duration: int) -> float:
        """
        Calculates monthly installment amount.
        Formula: (Selling Price - Down Payment) / Duration
        """
        if duration <= 0:
            return 0.0
        remaining_balance = selling_price - down_payment
        if remaining_balance <= 0:
            return 0.0
        return round(remaining_balance / duration, 2)

    def validate_sale_data(
        self,
        customer_id: str,
        device_id: str,
        cost_price: float,
        selling_price: float,
        down_payment: float,
        duration: int,
        start_date: Any
    ) -> Tuple[bool, List[str]]:
        """
        Validates sale fields before committing.
        """
        errors = []
        if not customer_id:
            errors.append("Please select a customer.")
        if not device_id:
            errors.append("Please select a device.")
            
        if cost_price < 0:
            errors.append("Cost Price cannot be negative.")
        if selling_price < cost_price:
            errors.append("Selling Price cannot be less than Cost Price.")
        if down_payment < 0:
            errors.append("Down Payment cannot be negative.")
        if down_payment > selling_price:
            errors.append("Down Payment cannot exceed Selling Price.")
        if duration <= 0:
            errors.append("Installment duration must be at least 1 month.")
        if not start_date:
            errors.append("Installment Start Date is required.")
            
        return len(errors) == 0, errors

    def commit_sale(
        self,
        customer_id: str,
        device_id: str,
        cost_price: float,
        selling_price: float,
        down_payment: float,
        duration: int,
        start_date: Any
    ) -> Dict[str, Any]:
        """
        Validates and commits a sale record with dynamic installment list creation.
        """
        is_valid, errors = self.validate_sale_data(
            customer_id, device_id, cost_price, selling_price, down_payment, duration, start_date
        )
        if not is_valid:
            raise ValueError("\n".join(errors))
            
        sale_data = {
            "customer_id": customer_id,
            "device_id": device_id,
            "cost_price": cost_price,
            "selling_price": selling_price,
            "down_payment": down_payment,
            "installment_months": duration,
            "start_date": start_date
        }
        
        result = self.repo.create_sale_with_installments(sale_data)
        try:
            cust = self.repo.db.table("customers").select("name").eq("id", customer_id).execute().data[0]
            dev = self.repo.db.table("devices").select("brand, model").eq("id", device_id).execute().data[0]
            from src.services.audit_log_service import AuditLogService
            AuditLogService().log_action(f"Created Sale: {cust['name']} purchased {dev['brand']} {dev['model']} (Rs. {selling_price:,.2f})")
        except Exception as log_ex:
            print(f"Failed to log sale creation audit: {log_ex}")
        return result

    def get_all_sales(self) -> List[Dict[str, Any]]:
        """Retrieves list of all sales."""
        return self.repo.get_all_with_details()

    def get_customer_sales(self, customer_id: str) -> List[Dict[str, Any]]:
        """Gets sales for a customer."""
        return self.repo.get_customer_sales(customer_id)
