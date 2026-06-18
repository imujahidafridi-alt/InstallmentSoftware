from typing import List, Dict, Any, Optional
from datetime import date
from src.repositories.base_repository import BaseRepository

class PaymentRepository(BaseRepository):
    def get_payments_for_installment(self, installment_id: str) -> List[Dict[str, Any]]:
        """
        Gets all payment entries for a specific installment.
        """
        response = self.db.table("payments").select("*").eq("installment_id", installment_id).execute()
        return response.data or []

    def get_payments_for_sale(self, sale_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all payments associated with a specific sale ledger by joining via installments.
        """
        # First get the installment IDs for the sale
        inst_response = self.db.table("installments").select("id").eq("sale_id", sale_id).execute()
        if not inst_response.data:
            return []
        
        inst_ids = [inst["id"] for inst in inst_response.data]
        
        response = (
            self.db.table("payments")
            .select("*, installments(due_date, amount, status)")
            .in_("installment_id", inst_ids)
            .order("payment_date", desc=True)
            .execute()
        )
        return response.data or []

    def record_payment_allocation(
        self, 
        sale_id: str, 
        total_amount_received: float, 
        payment_date: str, 
        notes: str,
        payment_method: str = "Cash"
    ) -> List[Dict[str, Any]]:
        """
        Allocates a payment received to the oldest unpaid/partially paid installments.
        Supports:
        - Full Payment: Exactly matches due.
        - Partial Payment: Underpays installment, updates status to 'Partial'.
        - Advance Payment: Overpays current installment, rolls remainder onto subsequent installments.
        
        Returns a list of created payment records.
        """
        amount_remaining = float(total_amount_received)
        if amount_remaining <= 0:
            raise Exception("Payment amount must be greater than zero.")

        # Get all installments for this sale ordered by due_date
        inst_response = (
            self.db.table("installments")
            .select("*")
            .eq("sale_id", sale_id)
            .order("due_date")
            .execute()
        )
        
        if not inst_response.data:
            raise Exception("No installments found for this sale.")
            
        installments = inst_response.data
        unpaid_installments = [inst for inst in installments if inst["status"] != "Paid"]
        
        # If all installments are already paid, apply it to the very last installment as an overpayment
        if not unpaid_installments:
            last_inst = installments[-1]
            payment_record = {
                "installment_id": last_inst["id"],
                "amount_received": amount_remaining,
                "payment_date": payment_date,
                "notes": f"{notes} (Extra payment on fully paid schedule)",
                "payment_method": payment_method
            }
            res = self.db.table("payments").insert(payment_record).execute()
            return res.data or []

        created_payments = []
        
        for inst in unpaid_installments:
            if amount_remaining <= 0:
                break
                
            inst_id = inst["id"]
            inst_amount = float(inst["amount"])
            
            # Find how much has already been paid for this specific installment
            payments_res = self.db.table("payments").select("amount_received").eq("installment_id", inst_id).execute()
            already_paid = sum(float(p["amount_received"]) for p in payments_res.data) if payments_res.data else 0.0
            
            remaining_for_inst = inst_amount - already_paid
            
            if amount_remaining >= remaining_for_inst:
                # We can fully pay off this installment
                payment_record = {
                    "installment_id": inst_id,
                    "amount_received": round(remaining_for_inst, 2),
                    "payment_date": payment_date,
                    "notes": notes if amount_remaining == total_amount_received else f"{notes} (Split allocation)",
                    "payment_method": payment_method
                }
                
                # Insert payment record
                pay_res = self.db.table("payments").insert(payment_record).execute()
                if pay_res.data:
                    created_payments.append(pay_res.data[0])
                
                # Update installment status to Paid
                self.db.table("installments").update({
                    "status": "Paid",
                    "paid_date": payment_date
                }).eq("id", inst_id).execute()
                
                amount_remaining -= remaining_for_inst
            else:
                # Partial payment for this installment
                payment_record = {
                    "installment_id": inst_id,
                    "amount_received": round(amount_remaining, 2),
                    "payment_date": payment_date,
                    "notes": notes,
                    "payment_method": payment_method
                }
                
                pay_res = self.db.table("payments").insert(payment_record).execute()
                if pay_res.data:
                    created_payments.append(pay_res.data[0])
                    
                # Update status to Partial
                self.db.table("installments").update({
                    "status": "Partial"
                }).eq("id", inst_id).execute()
                
                amount_remaining = 0.0
                
        # If there's still cash remaining (Advance payment beyond total outstanding of all installments)
        if amount_remaining > 0:
            # Apply the leftover amount to the last installment
            last_inst = installments[-1]
            payment_record = {
                "installment_id": last_inst["id"],
                "amount_received": round(amount_remaining, 2),
                "payment_date": payment_date,
                "notes": f"{notes} (Excess payment credit)",
                "payment_method": payment_method
            }
            pay_res = self.db.table("payments").insert(payment_record).execute()
            if pay_res.data:
                created_payments.append(pay_res.data[0])
                
        return created_payments
