from typing import Dict, Any, List
from datetime import date, datetime
from src.repositories.base_repository import BaseRepository

class DashboardViewModel(BaseRepository):
    def get_kpis(self) -> Dict[str, Any]:
        """
        Compiles the primary Executive KPI metrics:
        - Total Customers
        - Total Devices Sold
        - Active Installments (Sales with outstanding balance > 0)
        - Completed Installments (Sales with zero outstanding balance)
        - Overdue Installments (Count of unpaid installments whose due date has passed)
        - Total Outstanding Balance (Sum of outstanding balance on all sales)
        - Monthly Collection (Payments collected + down payments received this month)
        - Monthly Profit (Profit margins of sales registered this month)
        - Net Revenue (Total payments received + all down payments collected all time)
        """
        # 1. Total Customers
        cust_res = self.db.table("customers").select("id", count="exact").execute()
        total_customers = cust_res.count if cust_res.count is not None else 0

        # 2. Total Devices Sold (Total Sales count)
        sales_res = self.db.table("sales").select("id, selling_price, down_payment, margin, cost_price, created_at").execute()
        all_sales = sales_res.data or []
        total_devices_sold = len(all_sales)

        # Fetch all payments to compute outstanding balances
        all_payments_res = self.db.table("payments").select("amount_received, installment_id").execute()
        all_payments = all_payments_res.data or []
        total_payments_received = sum(float(p["amount_received"]) for p in all_payments)

        # Get all installments to map them to sales
        all_inst_res = self.db.table("installments").select("id, sale_id").execute()
        all_insts = all_inst_res.data or []
        inst_to_sale = {inst["id"]: inst["sale_id"] for inst in all_insts}

        # Build map of sale_id to payments
        sale_payments = {}
        for p in all_payments:
            sale_id = inst_to_sale.get(p["installment_id"])
            if sale_id:
                sale_payments[sale_id] = sale_payments.get(sale_id, 0.0) + float(p["amount_received"])

        # Calculate Active vs Completed Installments and Outstanding Balance
        active_installments = 0
        completed_installments = 0
        total_outstanding = 0.0

        for s in all_sales:
            sale_id = s["id"]
            selling_price = float(s["selling_price"])
            down_payment = float(s["down_payment"])
            paid = sale_payments.get(sale_id, 0.0)
            
            outstanding = selling_price - down_payment - paid
            if outstanding > 0.01:
                active_installments += 1
                total_outstanding += outstanding
            else:
                completed_installments += 1

        if total_outstanding < 0:
            total_outstanding = 0.0

        # 5. Overdue Installments count
        today_str = date.today().strftime("%Y-%m-%d")
        overdue_res = (
            self.db.table("installments")
            .select("id", count="exact")
            .lt("due_date", today_str)
            .neq("status", "Paid")
            .execute()
        )
        overdue_count = overdue_res.count if overdue_res.count is not None else 0

        # 6. Monthly collections and profit
        today = date.today()
        start_of_month = date(today.year, today.month, 1).strftime("%Y-%m-%d")
        import calendar
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_of_month = date(today.year, today.month, last_day).strftime("%Y-%m-%d")

        # Collections this month (payments + down payments of new sales)
        down_payments_this_month = sum(
            float(s["down_payment"])
            for s in all_sales
            if start_of_month <= s["created_at"][:10] <= end_of_month
        )

        pay_month_res = (
            self.db.table("payments")
            .select("amount_received")
            .gte("payment_date", start_of_month)
            .lte("payment_date", end_of_month)
            .execute()
        )
        payments_this_month = sum(float(p["amount_received"]) for p in pay_month_res.data) if pay_month_res.data else 0.0
        collections_this_month = payments_this_month + down_payments_this_month

        # Profit this month (margin of sales created this month)
        monthly_profit = sum(
            float(s["margin"])
            for s in all_sales
            if start_of_month <= s["created_at"][:10] <= end_of_month
        )

        # Net Revenue: Sum of all payments received + sum of down payments (Total cash collections)
        total_down_payments = sum(float(s["down_payment"]) for s in all_sales)
        net_revenue = total_payments_received + total_down_payments

        return {
            "total_customers": total_customers,
            "total_devices_sold": total_devices_sold,
            "total_active_installments": active_installments,
            "completed_installments": completed_installments,
            "overdue_installments": overdue_count,
            "total_outstanding": total_outstanding,
            "collections_this_month": collections_this_month,
            "total_profit": monthly_profit,
            "net_revenue": net_revenue
        }

    def get_charts_data(self) -> Dict[str, Any]:
        """
        Retrieves month-wise groupings for the 5 analytics charts:
        - Monthly Collections Trend
        - Monthly Profit Trend
        - Outstanding Balance Analysis
        - Recovery Performance Chart (Collections vs Due)
        - Installment Completion Rate (Completed vs Active)
        """
        # Fetch data
        pay_res = self.db.table("payments").select("payment_date, amount_received").execute()
        payments = pay_res.data or []
        
        sales_res = self.db.table("sales").select("start_date, margin, selling_price, down_payment, created_at").execute()
        sales = sales_res.data or []

        inst_res = self.db.table("installments").select("due_date, amount, status").execute()
        installments = inst_res.data or []

        # Get list of last 6 calendar months
        months_list = []
        today = date.today()
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            months_list.append(datetime(y, m, 1).strftime("%Y-%m"))

        # Map initialization
        collections_map = {m: 0.0 for m in months_list}
        profit_map = {m: 0.0 for m in months_list}
        outstanding_map = {m: 0.0 for m in months_list}
        due_map = {m: 0.0 for m in months_list}
        received_map = {m: 0.0 for m in months_list}

        # 1. Populate collections (including down payments of sales)
        for p in payments:
            try:
                p_month = p["payment_date"][:7]
                if p_month in collections_map:
                    collections_map[p_month] += float(p["amount_received"])
                    received_map[p_month] += float(p["amount_received"])
            except Exception:
                continue

        for s in sales:
            try:
                # Down payments are collected on creation date
                s_month = s["created_at"][:7]
                if s_month in collections_map:
                    collections_map[s_month] += float(s["down_payment"])
            except Exception:
                continue

        # 2. Populate profit trend
        for s in sales:
            try:
                s_month = s["created_at"][:7]
                if s_month in profit_map:
                    profit_map[s_month] += float(s["margin"])
            except Exception:
                continue

        # 3. Populate due map for Recovery Performance
        for inst in installments:
            try:
                inst_month = inst["due_date"][:7]
                if inst_month in due_map:
                    due_map[inst_month] += float(inst["amount"])
            except Exception:
                continue

        # 4. Populate outstanding balances trend (Cumulative outstanding balance over time)
        running_outstanding = 0.0
        first_month_str = months_list[0]
        first_month_date = datetime.strptime(first_month_str + "-01", "%Y-%m-%d").date()
        
        prior_sales_sum = sum(
            float(s["selling_price"]) - float(s["down_payment"]) 
            for s in sales 
            if datetime.strptime(s["created_at"][:10], "%Y-%m-%d").date() < first_month_date
        )
        prior_payments_sum = sum(
            float(p["amount_received"]) 
            for p in payments 
            if datetime.strptime(p["payment_date"], "%Y-%m-%d").date() < first_month_date
        )
        running_outstanding = prior_sales_sum - prior_payments_sum

        for m in months_list:
            m_date = datetime.strptime(m + "-01", "%Y-%m-%d").date()
            import calendar
            last_day = calendar.monthrange(m_date.year, m_date.month)[1]
            end_m_date = date(m_date.year, m_date.month, last_day)

            month_sales = sum(
                float(s["selling_price"]) - float(s["down_payment"]) 
                for s in sales 
                if m_date <= datetime.strptime(s["created_at"][:10], "%Y-%m-%d").date() <= end_m_date
            )
            month_payments = sum(
                float(p["amount_received"]) 
                for p in payments 
                if m_date <= datetime.strptime(p["payment_date"], "%Y-%m-%d").date() <= end_m_date
            )
            running_outstanding += (month_sales - month_payments)
            outstanding_map[m] = max(0.0, running_outstanding)

        # 5. Recovery Performance calculations (collections vs due percentage)
        recovery_performance = []
        for m in months_list:
            due = due_map[m]
            rec = received_map[m]
            pct = (rec / due) * 100 if due > 0 else 0.0
            recovery_performance.append(min(100.0, pct))

        # 6. Installment Completion Rate values
        # Outstanding balance per sale to count completed vs active
        # Build map of sale_id to payments
        sale_payments = {}
        for p in payments:
            # We need to map payments back to installments, which belongs to sales
            pass
        # To make it simple, we can reuse the KPI completed/active values
        kpis = self.get_kpis()
        completion_data = [kpis["completed_installments"], kpis["total_active_installments"]]

        labels = [datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in months_list]
        return {
            "labels": labels,
            "collections": [collections_map[m] for m in months_list],
            "profits": [profit_map[m] for m in months_list],
            "outstanding": [outstanding_map[m] for m in months_list],
            "recovery": recovery_performance,
            "completion": completion_data
        }
