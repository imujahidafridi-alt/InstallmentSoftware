from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timedelta
from src.repositories.installment_repository import InstallmentRepository
from src.repositories.payment_repository import PaymentRepository
from src.repositories.customer_repository import CustomerRepository
from src.repositories.device_repository import DeviceRepository
from src.repositories.sale_repository import SaleRepository
from src.services.report_service import ReportService

class InstallmentViewModel:
    def __init__(self):
        self.inst_repo = InstallmentRepository()
        self.pay_repo = PaymentRepository()
        self.cust_repo = CustomerRepository()
        self.dev_repo = DeviceRepository()
        self.sale_repo = SaleRepository()

    def get_ledger_data(self, sale_id: str) -> Dict[str, Any]:
        """
        Gathers complete summary and transactional entries for a specific sale ledger.
        """
        sale = self.sale_repo.get_by_id(sale_id)
        if not sale:
            raise ValueError("Sale record not found.")

        installments = self.inst_repo.get_by_sale_id(sale_id)
        payments = self.pay_repo.get_payments_for_sale(sale_id)
        
        # Calculate summary parameters
        selling_price = float(sale["selling_price"])
        down_payment = float(sale["down_payment"])
        cost_price = float(sale["cost_price"])
        
        # Total amount paid (excluding down payment)
        total_paid = sum(float(p["amount_received"]) for p in payments)
        outstanding = selling_price - down_payment - total_paid
        if outstanding < 0.01:
            outstanding = 0.0
            
        remaining_installments = sum(1 for inst in installments if inst["status"] != "Paid")
        
        next_due = None
        unpaid = [inst for inst in installments if inst["status"] != "Paid"]
        if unpaid:
            next_due = unpaid[0]["due_date"]

        return {
            "sale": sale,
            "customer": sale["customers"],
            "device": sale["devices"],
            "installments": installments,
            "payments": payments,
            "summary": {
                "selling_price": selling_price,
                "down_payment": down_payment,
                "outstanding": outstanding,
                "total_paid": total_paid,
                "cost_price": cost_price,
                "margin": selling_price - cost_price,
                "remaining_installments": remaining_installments,
                "next_due": next_due
            }
        }

    def get_customer_all_installments(self, customer_id: str) -> List[Dict[str, Any]]:
        """Gets ledger installments for a customer."""
        return self.inst_repo.get_customer_ledger_installments(customer_id)

    def record_payment(
        self, 
        sale_id: str, 
        amount: float, 
        payment_date: str, 
        notes: str,
        payment_method: str = "Cash"
    ) -> List[Dict[str, Any]]:
        """
        Processes payment collection and propagates changes.
        """
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        result = self.pay_repo.record_payment_allocation(sale_id, amount, payment_date, notes, payment_method)
        
        from src.services.cache_service import CacheService
        CacheService.clear()
        
        try:
            sale = self.sale_repo.get_by_id(sale_id)
            customer_name = sale["customers"]["name"]
            device_name = f"{sale['devices']['brand']} {sale['devices']['model']}"
            from src.services.audit_log_service import AuditLogService
            AuditLogService().log_action(f"Collected Payment ({payment_method}): Rs. {amount:,.2f} from {customer_name} for {device_name}")
        except Exception as log_ex:
            print(f"Failed to log payment audit: {log_ex}")
        return result

    def get_due_tracking_lists(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Queries and categorizes all outstanding (unpaid/partially paid) installments.
        """
        unpaid_res = (
            self.inst_repo.db.table("installments")
            .select("*, sales(cost_price, selling_price, customers(id, name, mobile, reminders_enabled), devices(name, brand, model))")
            .neq("status", "Paid")
            .order("due_date")
            .execute()
        )
        unpaid_installments = unpaid_res.data or []

        # Optimization: Fetch payments for all unpaid installments in a single query
        unpaid_ids = [inst["id"] for inst in unpaid_installments]
        payments_map = {}
        if unpaid_ids:
            payments_res = self.pay_repo.db.table("payments").select("installment_id, amount_received").in_("installment_id", unpaid_ids).execute()
            for p in (payments_res.data or []):
                inst_id = p["installment_id"]
                payments_map[inst_id] = payments_map.get(inst_id, 0.0) + float(p["amount_received"])

        # Categorize
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Determine calendar week range (Monday to Sunday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Determine rolling 7-day range (including today)
        end_of_next_7_days = today + timedelta(days=6)
        
        # Determine calendar month range
        start_of_month = date(today.year, today.month, 1)
        import calendar
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_of_month = date(today.year, today.month, last_day)

        due_today = []
        due_tomorrow = []
        due_this_week = []
        due_next_7_days = []
        due_this_month = []
        
        overdue_1_30 = []
        overdue_31_60 = []
        overdue_61_90 = []
        overdue_90_plus = []

        for inst in unpaid_installments:
            # Check reminders toggle
            try:
                reminders_enabled = inst["sales"]["customers"].get("reminders_enabled", True)
                if not reminders_enabled:
                    continue
            except Exception:
                pass

            try:
                due_dt = datetime.strptime(inst["due_date"], "%Y-%m-%d").date()
            except Exception:
                continue

            inst_id = inst["id"]
            due_amount = float(inst["amount"])
            paid_amount = payments_map.get(inst_id, 0.0)
            outstanding_amount = due_amount - paid_amount
            
            if outstanding_amount <= 0.01:
                continue

            item = {
                "id": inst_id,
                "sale_id": inst["sale_id"],
                "customer_name": inst["sales"]["customers"]["name"],
                "mobile": inst["sales"]["customers"]["mobile"],
                "device_name": inst["sales"]["devices"]["name"],
                "due_date": inst["due_date"],
                "due_amount": due_amount,
                "outstanding_amount": outstanding_amount
            }

            if due_dt < today:
                days_overdue = (today - due_dt).days
                item["days_overdue"] = days_overdue
                
                if 1 <= days_overdue <= 30:
                    overdue_1_30.append(item)
                elif 31 <= days_overdue <= 60:
                    overdue_31_60.append(item)
                elif 61 <= days_overdue <= 90:
                    overdue_61_90.append(item)
                else:
                    overdue_90_plus.append(item)
            else:
                if due_dt == today:
                    due_today.append(item)
                if due_dt == tomorrow:
                    due_tomorrow.append(item)
                if start_of_week <= due_dt <= end_of_week:
                    due_this_week.append(item)
                if due_dt <= end_of_next_7_days:
                    due_next_7_days.append(item)
                if start_of_month <= due_dt <= end_of_month:
                    due_this_month.append(item)

        return {
            "due_today": due_today,
            "due_tomorrow": due_tomorrow,
            "due_this_week": due_this_week,
            "due_next_7_days": due_next_7_days,
            "due_this_month": due_this_month,
            "overdue_1_30": overdue_1_30,
            "overdue_31_60": overdue_31_60,
            "overdue_61_90": overdue_61_90,
            "overdue_90_plus": overdue_90_plus
        }

    def generate_pdf_report(self, sale_id: str, output_path: str, shop_details: Optional[Dict[str, str]] = None) -> str:
        """
        Exports an individual customer ledger PDF.
        """
        data = self.get_ledger_data(sale_id)
        return ReportService.generate_ledger_pdf(
            customer=data["customer"],
            device=data["device"],
            sale=data["sale"],
            installments=data["installments"],
            payments=data["payments"],
            output_path=output_path,
            shop_details=shop_details
        )

    def reschedule_installments(self, sale_id: str, new_start_date: str, duration: int) -> bool:
        """
        Triggers rescheduling of unpaid/partially paid installments for a sale,
        and logs the action to the audit logs.
        """
        if duration <= 0:
            raise ValueError("Reschedule duration must be at least 1 month.")
            
        success = self.inst_repo.reschedule_schedule(sale_id, new_start_date, duration)
        if success:
            from src.services.cache_service import CacheService
            CacheService.clear()
            
            try:
                sale = self.sale_repo.get_by_id(sale_id)
                customer_name = sale["customers"]["name"]
                device_name = f"{sale['devices']['brand']} {sale['devices']['model']}"
                from src.services.audit_log_service import AuditLogService
                AuditLogService().log_action(f"Rescheduled Installments: {customer_name} for {device_name} over {duration} months starting {new_start_date}")
            except Exception as log_ex:
                print(f"Failed to log rescheduling audit: {log_ex}")
        return success

