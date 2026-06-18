from typing import List, Dict, Any, Optional
from datetime import date, datetime
from src.repositories.base_repository import BaseRepository

class InstallmentRepository(BaseRepository):
    def get_by_sale_id(self, sale_id: str) -> List[Dict[str, Any]]:
        """
        Gets all installments for a specific sale, ordered by due date.
        """
        response = self.db.table("installments").select("*").eq("sale_id", sale_id).order("due_date").execute()
        return response.data or []

    def get_customer_ledger_installments(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Gets all installments across all sales for a customer, ordered by due date.
        """
        # Query sales first to get their IDs
        sales_response = self.db.table("sales").select("id").eq("customer_id", customer_id).execute()
        if not sales_response.data:
            return []
        
        sale_ids = [s["id"] for s in sales_response.data]
        
        # Query installments for these sales
        response = self.db.table("installments").select("*, sales(devices(name, brand, model))").in_("sale_id", sale_ids).order("due_date").execute()
        return response.data or []

    def get_due_today(self) -> List[Dict[str, Any]]:
        """
        Gets installments due today that are not fully paid.
        """
        today_str = date.today().strftime("%Y-%m-%d")
        response = (
            self.db.table("installments")
            .select("*, sales(cost_price, selling_price, customers(name, mobile), devices(name, brand, model))")
            .eq("due_date", today_str)
            .neq("status", "Paid")
            .order("due_date")
            .execute()
        )
        return response.data or []

    def get_due_within_days(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Gets installments due from tomorrow up to the next N days.
        """
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        
        # Calculate future date
        from datetime import timedelta
        future_date = today + timedelta(days=days)
        future_date_str = future_date.strftime("%Y-%m-%d")
        
        response = (
            self.db.table("installments")
            .select("*, sales(customers(name, mobile), devices(name, brand, model))")
            .gt("due_date", today_str)
            .lte("due_date", future_date_str)
            .neq("status", "Paid")
            .order("due_date")
            .execute()
        )
        return response.data or []

    def get_overdue(self) -> List[Dict[str, Any]]:
        """
        Gets installments that are overdue (due date in past and status is not Paid).
        """
        today_str = date.today().strftime("%Y-%m-%d")
        response = (
            self.db.table("installments")
            .select("*, sales(cost_price, selling_price, customers(name, mobile), devices(name, brand, model))")
            .lt("due_date", today_str)
            .neq("status", "Paid")
            .order("due_date")
            .execute()
        )
        return response.data or []

    def update_status(self, installment_id: str, status: str, paid_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Updates the status and optionally paid date of an installment.
        """
        update_data = {"status": status}
        if paid_date:
            update_data["paid_date"] = paid_date
            
        response = self.db.table("installments").update(update_data).eq("id", installment_id).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to update installment status.")

    def reschedule_schedule(self, sale_id: str, new_start_date: str, duration: int) -> bool:
        """
        Reschedules remaining unpaid and partially paid installments for a sale.
        """
        # Fetch installments ordered by due_date
        inst_res = self.db.table("installments").select("*").eq("sale_id", sale_id).order("due_date").execute()
        installments = inst_res.data or []
        if not installments:
            raise Exception("No installments found for this sale to reschedule.")

        # Calculate outstanding amount to reschedule
        reschedule_amount = 0.0
        
        for inst in installments:
            if inst["status"] == "Paid":
                continue
                
            # Fetch payments received for this installment
            payments_res = self.db.table("payments").select("amount_received").eq("installment_id", inst["id"]).execute()
            paid_amt = sum(float(p["amount_received"]) for p in payments_res.data) if payments_res.data else 0.0
            
            due_amt = float(inst["amount"])
            unpaid_portion = due_amt - paid_amt
            if unpaid_portion > 0:
                reschedule_amount += unpaid_portion
                
            if inst["status"] == "Partial":
                # Convert the partial installment to Paid with amount equal to paid_amt
                self.db.table("installments").update({
                    "amount": paid_amt,
                    "status": "Paid",
                    "paid_date": date.today().strftime("%Y-%m-%d")
                }).eq("id", inst["id"]).execute()
            elif inst["status"] == "Pending":
                # Delete pending installment
                self.db.table("installments").delete().eq("id", inst["id"]).execute()

        if reschedule_amount <= 0:
            return True

        # Calculate N new monthly installments
        monthly_amount = round(reschedule_amount / duration, 2)
        
        # Date helper function
        def add_months(start_date_str: str, months_to_add: int) -> str:
            from datetime import datetime
            dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            month = dt.month - 1 + months_to_add
            year = dt.year + month // 12
            month = month % 12 + 1
            day = min(dt.day, [31,
                29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            return f"{year:04d}-{month:02d}-{day:02d}"

        # Insert new installments
        new_insts = []
        for i in range(duration):
            due_date = add_months(new_start_date, i)
            new_insts.append({
                "sale_id": sale_id,
                "due_date": due_date,
                "amount": monthly_amount,
                "status": "Pending"
            })
            
        self.db.table("installments").insert(new_insts).execute()
        return True

