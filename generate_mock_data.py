import os
import sys
import random
from datetime import datetime, timedelta

# Add the workspace root to sys.path so we can import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.supabase_client import get_db

def clear_database(db):
    print("Wiping existing database tables in order of dependency...")
    try:
        import time
        # Delete in reverse order of foreign key relationships
        db.table("payments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        time.sleep(0.5)
        db.table("installments").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        time.sleep(0.5)
        db.table("sales").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        time.sleep(0.5)
        db.table("devices").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        time.sleep(0.5)
        db.table("customers").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("Existing database tables wiped successfully.")
    except Exception as e:
        print(f"Error wiping database: {e}")
        sys.exit(1)

def generate_mock_dataset():
    print("Connecting to Supabase Database...")
    db = get_db()
    if not db:
        print("Error: Database client could not be initialized.")
        return

    # Clear database to prevent duplicate keys or foreign key violations
    clear_database(db)

    # =========================================================================
    # 1. GENERATE 100 CUSTOMERS
    # =========================================================================
    first_names = [
        "Muhammad", "Ahmad", "Ali", "Zeeshan", "Hamza", "Usman", "Bilal", "Umer", 
        "Asif", "Sajid", "Yasir", "Faisal", "Tariq", "Imran", "Kamran", "Naveed", 
        "Zafar", "Arsalan", "Waqas", "Babar", "Farhan", "Adnan", "Junaid", "Nabeel"
    ]
    last_names = [
        "Khan", "Ahmed", "Ali", "Hussain", "Shah", "Butt", "Mughal", "Sheikh", 
        "Raza", "Mahmood", "Iqbal", "Siddiqui", "Gill", "Malik", "Dar", "Abbasi"
    ]
    father_names = [
        "Muhammad Ali", "Muhammad Hussain", "Ahmad Khan", "Zafar Iqbal", 
        "Tariq Mahmood", "Imran Shah", "Sajid Raza", "Kamran Malik",
        "Liaquat Ali", "Javed Iqbal", "Tariq Mehmood", "Sohail Akhtar"
    ]
    cities = [
        "Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", 
        "Multan", "Gujranwala", "Sialkot", "Peshawar", "Quetta"
    ]
    streets = [
        "Street 1", "Street 2", "Main Bazar", "Commercial Area", "Sector G-11", 
        "Model Town", "Gulberg III", "DHA Phase 5", "Johar Town", "Bahria Town"
    ]

    print("Generating 100 mock customer records...")
    customers_to_insert = []
    
    for i in range(100):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        father_name = random.choice(father_names)
        # Match constraints: ^03[0-9]{9}$
        mobile = f"03{random.randint(100000000, 999999999)}"
        address = f"House {random.randint(1, 350)}, {random.choice(streets)}, {random.choice(cities)}"
        
        customers_to_insert.append({
            "name": name,
            "father_name": father_name,
            "mobile": mobile,
            "address": address,
            "remarks": f"System performance mock customer #{i+1}."
        })

    inserted_customers = []
    # Insert in batches of 20
    batch_size = 20
    for j in range(0, len(customers_to_insert), batch_size):
        batch = customers_to_insert[j:j+batch_size]
        res = db.table("customers").insert(batch).execute()
        inserted_customers.extend(res.data)
    print(f"Successfully inserted {len(inserted_customers)} customers.")

    # =========================================================================
    # 2. GENERATE 30 DEVICES
    # =========================================================================
    device_brands = [
        ("Apple", "iPhone 15 Pro Max", ["256 GB", "512 GB", "1 TB"], ["8 GB"]),
        ("Apple", "iPhone 14 Pro", ["128 GB", "256 GB"], ["6 GB"]),
        ("Samsung", "Galaxy S24 Ultra", ["256 GB", "512 GB"], ["12 GB", "16 GB"]),
        ("Samsung", "Galaxy A55", ["128 GB", "256 GB"], ["8 GB"]),
        ("Xiaomi", "Redmi Note 13 Pro", ["256 GB", "512 GB"], ["8 GB", "12 GB"]),
        ("Realme", "12 Pro+", ["256 GB", "512 GB"], ["8 GB", "12 GB"]),
        ("Vivo", "V30 Pro", ["256 GB"], ["12 GB"]),
        ("Infinix", "Note 40 Pro", ["256 GB"], ["8 GB", "12 GB"])
    ]

    used_imeis = set()
    def get_unique_imei():
        while True:
            # Match constraints: ^[0-9]{15}$
            imei = f"86{random.randint(1000000000000, 9999999999999)}"
            if imei not in used_imeis:
                used_imeis.add(imei)
                return imei

    print("Generating 30 mock devices...")
    devices_to_insert = []
    for i in range(30):
        brand, model, rom_options, ram_options = random.choice(device_brands)
        name = f"{brand} {model}"
        rom = random.choice(rom_options)
        ram = random.choice(ram_options)
        sim_type = random.randint(1, 2)  # 1 for Single SIM, 2 for Dual SIM
        
        device_data = {
            "name": name,
            "brand": brand,
            "model": model,
            "ram": ram,
            "rom": rom,
            "sim_type": sim_type,
            "imei_1": get_unique_imei()
        }
        if sim_type == 2:
            device_data["imei_2"] = get_unique_imei()

        devices_to_insert.append(device_data)

    inserted_devices = []
    for j in range(0, len(devices_to_insert), batch_size):
        batch = devices_to_insert[j:j+batch_size]
        res = db.table("devices").insert(batch).execute()
        inserted_devices.extend(res.data)
    print(f"Successfully inserted {len(inserted_devices)} devices.")

    # =========================================================================
    # 3. GENERATE 50 SALES & ACTIVE LEDGERS
    # =========================================================================
    print("Generating 50 sales, schedules, and collections history...")
    
    # We want a mix of sales:
    # - Completely paid (past sales, all installments paid)
    # - Ongoing healthy (past installments paid, future pending)
    # - Ongoing overdue (past installments unpaid)
    
    for i in range(50):
        customer = random.choice(inserted_customers)
        device = random.choice(inserted_devices)
        
        cost_price = random.randint(25000, 110000)
        profit = random.randint(10000, 25000)
        selling_price = cost_price + profit
        down_payment = int(selling_price * random.choice([0.15, 0.20, 0.25, 0.30]))
        
        installment_months = random.choice([3, 6, 9, 12])
        
        # Decide start date between 10 days and 240 days ago
        days_ago = random.randint(10, 240)
        start_date = datetime.now() - timedelta(days=days_ago)
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        sale_data = {
            "customer_id": customer["id"],
            "device_id": device["id"],
            "cost_price": cost_price,
            "selling_price": selling_price,
            "down_payment": down_payment,
            "installment_months": installment_months,
            "start_date": start_date_str
        }
        
        sale_res = db.table("sales").insert(sale_data).execute()
        sale = sale_res.data[0]
        
        # Calculate monthly installment amounts
        remaining_balance = selling_price - down_payment
        monthly_amount = int(remaining_balance / installment_months)
        
        installments_batch = []
        for m in range(1, installment_months + 1):
            due_date = start_date + timedelta(days=m * 30)
            
            # Determine installment status based on current date
            status = "Pending"
            paid_date_str = None
            
            if due_date < datetime.now():
                # Past due installment:
                # 70% chance paid on-time or early
                # 20% chance paid late
                # 10% chance overdue (still pending)
                roll = random.random()
                if roll < 0.70:
                    status = "Paid"
                    paid_date = due_date - timedelta(days=random.randint(0, 5))
                    paid_date_str = paid_date.strftime("%Y-%m-%d")
                elif roll < 0.90:
                    status = "Paid"
                    paid_date = due_date + timedelta(days=random.randint(1, 8))
                    paid_date_str = paid_date.strftime("%Y-%m-%d")
                else:
                    status = "Pending"
                    paid_date_str = None
            else:
                # Future installment
                status = "Pending"
                paid_date_str = None
                
            installments_batch.append({
                "sale_id": sale["id"],
                "due_date": due_date.strftime("%Y-%m-%d"),
                "amount": monthly_amount,
                "status": status,
                "paid_date": paid_date_str
            })
            
        inst_res = db.table("installments").insert(installments_batch).execute()
        inserted_insts = inst_res.data
        
        # Insert payments for paid installments
        payments_batch = []
        for inst in inserted_insts:
            if inst["status"] == "Paid":
                payments_batch.append({
                    "installment_id": inst["id"],
                    "amount_received": inst["amount"],
                    "payment_date": inst["paid_date"],
                    "notes": f"Inst. #{inserted_insts.index(inst) + 1} payment received."
                })
                
        if payments_batch:
            db.table("payments").insert(payments_batch).execute()

    # Clear caches to force UI sync
    from src.services.cache_service import CacheService
    CacheService.clear()
    
    print("\nDatabase fully populated with:")
    print("* 100 Customers")
    print("* 30 Devices")
    print("* 50 Sales Ledgers (with full installments schedules & payments)")
    print("* All local persistent caches cleared.")

if __name__ == "__main__":
    generate_mock_dataset()
