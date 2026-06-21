import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.viewmodels.installment_viewmodel import InstallmentViewModel

vm = InstallmentViewModel()
res = vm.get_due_tracking_lists()

print("Due This Week dates:")
for item in res["due_this_week"]:
    print(f"  - {item['customer_name']}: {item['due_date']}")

print("\nNext 7 Days dates:")
for item in res["due_next_7_days"]:
    print(f"  - {item['customer_name']}: {item['due_date']}")
