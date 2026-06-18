from typing import List, Dict, Any, Optional
from datetime import datetime, date
import calendar
from src.repositories.base_repository import BaseRepository

def add_months(sourcedate: date, months: int) -> date:
    """Safely adds calendar months to a date, wrapping month-end properly."""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

class SaleRepository(BaseRepository):
    def create_sale_with_installments(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a sale record and generates its corresponding installments schedule.
        sale_data contains: customer_id, device_id, cost_price, selling_price, down_payment, 
        installment_months, start_date (as string YYYY-MM-DD or date object)
        """
        # Convert start_date if it's a string
        start_date_str = sale_data["start_date"]
        if isinstance(start_date_str, str):
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = start_date_str
            start_date_str = start_date.strftime("%Y-%m-%d")

        # Insert sale
        db_sale_data = {
            "customer_id": sale_data["customer_id"],
            "device_id": sale_data["device_id"],
            "cost_price": float(sale_data["cost_price"]),
            "selling_price": float(sale_data["selling_price"]),
            "down_payment": float(sale_data["down_payment"]),
            "installment_months": int(sale_data["installment_months"]),
            "start_date": start_date_str
        }
        
        response = self.db.table("sales").insert(db_sale_data).execute()
        if not response.data:
            raise Exception("Failed to insert sale record.")
        
        inserted_sale = response.data[0]
        sale_id = inserted_sale["id"]
        
        # Calculate installments
        remaining_balance = float(sale_data["selling_price"]) - float(sale_data["down_payment"])
        duration = int(sale_data["installment_months"])
        
        if remaining_balance > 0 and duration > 0:
            monthly_amount = remaining_balance / duration
            
            # Generate installment list
            installments_to_insert = []
            for i in range(1, duration + 1):
                due_date = add_months(start_date, i)
                installments_to_insert.append({
                    "sale_id": sale_id,
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "amount": round(monthly_amount, 2),
                    "status": "Pending"
                })
                
            # Batch insert installments
            inst_response = self.db.table("installments").insert(installments_to_insert).execute()
            if not inst_response.data:
                # Rollback sale (since client-side, we should clean up to keep DB consistent)
                self.db.table("sales").delete().eq("id", sale_id).execute()
                raise Exception("Failed to generate installment schedule. Sale transaction cancelled.")
        
        return inserted_sale

    def get_by_id(self, sale_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a sale by ID with nested customer and device details.
        """
        response = self.db.table("sales").select("*, customers(*), devices(*)").eq("id", sale_id).execute()
        return response.data[0] if response.data else None

    def get_all_with_details(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Gets all sales with customer and device details.
        """
        response = self.db.table("sales").select("*, customers(name, cnic, mobile), devices(name, brand, model)").order("created_at", desc=True).limit(limit).execute()
        return response.data or []

    def get_customer_sales(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all sales made to a specific customer.
        """
        response = self.db.table("sales").select("*, devices(*)").eq("customer_id", customer_id).order("start_date", desc=True).execute()
        return response.data or []
