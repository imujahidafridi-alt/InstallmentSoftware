from typing import List, Dict, Any, Tuple
from datetime import datetime, date
import calendar
from src.repositories.base_repository import BaseRepository
from src.services.report_service import ReportService

class ReportViewModel(BaseRepository):
    def get_monthly_collections_data(self, month: int, year: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Retrieves payment logs and compile aggregates for a specific Month & Year.
        """
        start_of_month = date(year, month, 1).strftime("%Y-%m-%d")
        last_day = calendar.monthrange(year, month)[1]
        end_of_month = date(year, month, last_day).strftime("%Y-%m-%d")
        
        response = (
            self.db.table("payments")
            .select("*, installments(*, sales(*, customers(*), devices(*)))")
            .gte("payment_date", start_of_month)
            .lte("payment_date", end_of_month)
            .order("payment_date")
            .execute()
        )
        
        raw_payments = response.data or []
        processed_data = []
        total_collection = 0.0
        total_profit = 0.0
        
        for p in raw_payments:
            try:
                amt = float(p["amount_received"])
                total_collection += amt
                
                inst = p["installments"]
                sale = inst["sales"]
                cust = sale["customers"]
                dev = sale["devices"]
                
                # Pro-rate profit margin for this installment payment
                # Formula: (Installment Paid Amount / Total Selling Price) * Margin
                selling_price = float(sale["selling_price"])
                margin = float(sale["margin"])
                pro_rated_profit = 0.0
                if selling_price > 0:
                    pro_rated_profit = (amt / selling_price) * margin
                total_profit += pro_rated_profit
                
                processed_data.append({
                    "payment_date": p["payment_date"],
                    "amount_received": amt,
                    "notes": p["notes"],
                    "customer_name": cust["name"],
                    "device_name": dev["name"],
                    "sale_id": sale["id"]
                })
            except Exception as e:
                print(f"Error compiling row: {e}")
                continue
                
        # Calculate system-wide outstanding balance
        # For simplicity, we get current total outstanding balance
        all_sales_res = self.db.table("sales").select("selling_price, down_payment").execute()
        all_sales = all_sales_res.data or []
        total_finance = sum(float(s["selling_price"]) - float(s["down_payment"]) for s in all_sales)
        
        all_pay_res = self.db.table("payments").select("amount_received").execute()
        total_pay = sum(float(p["amount_received"]) for p in all_pay_res.data) if all_pay_res.data else 0.0
        
        outstanding_bal = max(0.0, total_finance - total_pay)
        
        summary = {
            "total_collection": round(total_collection, 2),
            "total_outstanding": round(outstanding_bal, 2),
            "total_profit": round(total_profit, 2)
        }
        
        return processed_data, summary

    def export_report(self, format_type: str, month: int, year: int, output_path: str) -> str:
        """
        Exports the compiled monthly collections report in PDF, Excel, or CSV format.
        """
        data, summary = self.get_monthly_collections_data(month, year)
        
        fmt = format_type.lower()
        if fmt == "pdf":
            return ReportService.generate_monthly_collection_pdf(month, year, data, summary, output_path)
        elif fmt == "excel":
            return ReportService.generate_monthly_collection_excel(month, year, data, summary, output_path)
        elif fmt == "csv":
            return ReportService.generate_monthly_collection_csv(month, year, data, summary, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
