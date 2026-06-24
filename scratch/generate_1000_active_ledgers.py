import os
import sys
import random
from datetime import datetime, timedelta

# Add workspace root to sys.path to allow imports from src
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(workspace_root)

from src.db.supabase_client import get_db
from src.services.cache_service import CacheService

def generate_1000_active_ledgers():
    print("Connecting to Supabase Database...")
    db = get_db()
    if not db:
        print("Error: Database client could not be initialized.")
        return

    print("Connection established. Starting generation of 1000 active ledgers...")

    # =========================================================================
    # 1. GENERATE MOCK SUPPLIERS (10 suppliers)
    # =========================================================================
    print("\nGenerating 10 mock suppliers...")
    supplier_names = [
        "Al-Rehman Mobile Wholesalers", "Pak Telecom Distributors", "Karakoram Mobile Zone",
        "Peshawar Communications", "Sufi & Sons Electronics", "United Mobile Distribution",
        "Airlink Communication Ltd", "Patriot Mobiles", "Apex Distributors", "Indus Mobile Traders"
    ]
    contact_persons = ["Sajid Khan", "Kamran Ahmed", "Yousaf Ali", "Babar Rizvi", "Zeeshan Shah"]
    
    suppliers_to_insert = []
    for name in supplier_names:
        mobile = f"03{random.randint(100000000, 999999999)}"
        suppliers_to_insert.append({
            "name": name,
            "contact_person": random.choice(contact_persons),
            "mobile": mobile,
            "address": f"Shop #{random.randint(10, 150)}, Mobile Market, Lahore/Peshawar",
            "remarks": "Wholesale supplier for smart devices."
        })
    
    res = db.table("suppliers").insert(suppliers_to_insert).execute()
    inserted_suppliers = res.data
    print(f"Successfully inserted {len(inserted_suppliers)} suppliers.")

    # =========================================================================
    # 2. GENERATE 1000 CUSTOMERS
    # =========================================================================
    print("\nGenerating 1000 mock customers...")
    first_names = [
        "Muhammad", "Ahmad", "Ali", "Zeeshan", "Hamza", "Usman", "Bilal", "Umer", 
        "Asif", "Sajid", "Yasir", "Faisal", "Tariq", "Imran", "Kamran", "Naveed", 
        "Zafar", "Arsalan", "Waqas", "Babar", "Farhan", "Adnan", "Junaid", "Nabeel",
        "Sohail", "Rizwan", "Abid", "Zahid", "Noman", "Kashif", "Sufyan", "Talha"
    ]
    last_names = [
        "Khan", "Ahmed", "Ali", "Hussain", "Shah", "Butt", "Mughal", "Sheikh", 
        "Raza", "Mahmood", "Iqbal", "Siddiqui", "Gill", "Malik", "Dar", "Abbasi",
        "Afridi", "Khattak", "Shinwari", "Gujjar", "Chaudhry", "Bajwa", "Jan"
    ]
    father_names = [
        "Muhammad Ali", "Muhammad Hussain", "Ahmad Khan", "Zafar Iqbal", 
        "Tariq Mahmood", "Imran Shah", "Sajid Raza", "Kamran Malik",
        "Liaquat Ali", "Javed Iqbal", "Tariq Mehmood", "Sohail Akhtar",
        "Gul Khan", "Mirza Beg", "Naseeruddin", "Akram Chaudhry"
    ]
    cities = [
        "Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", 
        "Multan", "Gujranwala", "Sialkot", "Peshawar", "Quetta", "Mardan"
    ]
    streets = [
        "Street 1", "Street 2", "Main Bazar", "Commercial Area", "Sector G-11", 
        "Model Town", "Gulberg III", "DHA Phase 5", "Johar Town", "Bahria Town", "Samanabad"
    ]

    customers_to_insert = []
    for i in range(1000):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        father_name = random.choice(father_names)
        mobile = f"03{random.randint(100000000, 999999999)}"
        address = f"House {random.randint(1, 450)}, {random.choice(streets)}, {random.choice(cities)}"
        customers_to_insert.append({
            "name": name,
            "father_name": father_name,
            "mobile": mobile,
            "address": address,
            "remarks": f"Performance testing active customer #{i+1}."
        })

    inserted_customers = []
    batch_size = 100
    for j in range(0, len(customers_to_insert), batch_size):
        batch = customers_to_insert[j:j+batch_size]
        res = db.table("customers").insert(batch).execute()
        inserted_customers.extend(res.data)
        print(f"Inserted customers: {len(inserted_customers)}/1000", end="\r")
    print(f"\nSuccessfully inserted {len(inserted_customers)} customers.")

    # =========================================================================
    # 3. GENERATE 1000 DEVICES
    # =========================================================================
    print("\nGenerating 1000 mock devices...")
    device_brands = [
        ("Apple", "iPhone 15 Pro Max", ["256 GB", "512 GB"], ["8 GB"]),
        ("Apple", "iPhone 14 Pro", ["128 GB", "256 GB"], ["6 GB"]),
        ("Samsung", "Galaxy S24 Ultra", ["256 GB", "512 GB"], ["12 GB"]),
        ("Samsung", "Galaxy A55", ["128 GB", "256 GB"], ["8 GB"]),
        ("Xiaomi", "Redmi Note 13 Pro", ["256 GB"], ["8 GB", "12 GB"]),
        ("Realme", "12 Pro+", ["256 GB"], ["8 GB"]),
        ("Vivo", "V30 Pro", ["256 GB"], ["12 GB"]),
        ("Infinix", "Note 40 Pro", ["256 GB"], ["8 GB"])
    ]

    used_imeis = set()
    def get_unique_imei():
        while True:
            # Generate a 15-digit unique numeric string matching validation rules
            imei = f"86{random.randint(1000000000000, 9999999999999)}"
            if imei not in used_imeis:
                used_imeis.add(imei)
                return imei

    devices_to_insert = []
    for i in range(1000):
        brand, model, rom_options, ram_options = random.choice(device_brands)
        name = f"{brand} {model}"
        rom = random.choice(rom_options)
        ram = random.choice(ram_options)
        sim_type = random.choice([1, 2])
        supplier = random.choice(inserted_suppliers)

        device_data = {
            "name": name,
            "brand": brand,
            "model": model,
            "ram": ram,
            "rom": rom,
            "sim_type": sim_type,
            "imei_1": get_unique_imei(),
            "supplier_id": supplier["id"]
        }
        if sim_type == 2:
            device_data["imei_2"] = get_unique_imei()

        devices_to_insert.append(device_data)

    inserted_devices = []
    for j in range(0, len(devices_to_insert), batch_size):
        batch = devices_to_insert[j:j+batch_size]
        res = db.table("devices").insert(batch).execute()
        inserted_devices.extend(res.data)
        print(f"Inserted devices: {len(inserted_devices)}/1000", end="\r")
    print(f"\nSuccessfully inserted {len(inserted_devices)} devices.")

    # =========================================================================
    # 4. GENERATE 1000 SALES (Each customer gets a unique device)
    # =========================================================================
    print("\nGenerating 1000 sales...")
    sales_to_insert = []
    
    # We want active ledgers, so we simulate sales that started 1 to 4 months ago
    # with a 6-month or 12-month installment plan.
    for i in range(1000):
        customer = inserted_customers[i]
        device = inserted_devices[i]
        
        cost_price = random.randint(30000, 120000)
        profit = random.randint(10000, 30000)
        selling_price = cost_price + profit
        down_payment = int(selling_price * random.choice([0.15, 0.20, 0.25, 0.30]))
        
        installment_months = random.choice([6, 12])
        # Start date between 30 and 120 days ago (so they have 1-4 paid installments)
        days_ago = random.randint(30, 120)
        start_date = datetime.now() - timedelta(days=days_ago)
        
        sales_to_insert.append({
            "customer_id": customer["id"],
            "device_id": device["id"],
            "cost_price": cost_price,
            "selling_price": selling_price,
            "down_payment": down_payment,
            "installment_months": installment_months,
            "start_date": start_date.strftime("%Y-%m-%d")
        })

    inserted_sales = []
    for j in range(0, len(sales_to_insert), batch_size):
        batch = sales_to_insert[j:j+batch_size]
        res = db.table("sales").insert(batch).execute()
        inserted_sales.extend(res.data)
        print(f"Inserted sales: {len(inserted_sales)}/1000", end="\r")
    print(f"\nSuccessfully inserted {len(inserted_sales)} sales.")

    # =========================================================================
    # 5. GENERATE INSTALLMENTS & PAYMENTS
    # =========================================================================
    print("\nGenerating installment schedules and payments for active ledgers...")
    installments_to_insert = []
    
    # Pre-calculate installments to insert in batches
    # We will keep track of which installments are marked "Paid" to insert payments afterwards.
    sales_installment_data = [] # To temporarily map installments back to their monthly indexes
    
    for sale in inserted_sales:
        selling_price = float(sale["selling_price"])
        down_payment = float(sale["down_payment"])
        installment_months = int(sale["installment_months"])
        start_date = datetime.strptime(sale["start_date"], "%Y-%m-%d")
        
        remaining_balance = selling_price - down_payment
        monthly_amount = int(remaining_balance / installment_months)
        
        for m in range(1, installment_months + 1):
            due_date = start_date + timedelta(days=m * 30)
            
            # Since these are active healthy ledgers:
            # Installments whose due_date is in the past are marked "Paid"
            # Installments whose due_date is in the future are marked "Pending"
            is_past = due_date < datetime.now()
            status = "Paid" if is_past else "Pending"
            paid_date_str = (due_date - timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d") if is_past else None
            
            installments_to_insert.append({
                "sale_id": sale["id"],
                "due_date": due_date.strftime("%Y-%m-%d"),
                "amount": monthly_amount,
                "status": status,
                "paid_date": paid_date_str
            })

    print(f"Total installments calculated: {len(installments_to_insert)}")
    print("Inserting installments in batches...")
    inserted_installments = []
    inst_batch_size = 500
    for j in range(0, len(installments_to_insert), inst_batch_size):
        batch = installments_to_insert[j:j+inst_batch_size]
        res = db.table("installments").insert(batch).execute()
        inserted_installments.extend(res.data)
        print(f"Inserted installments: {len(inserted_installments)}/{len(installments_to_insert)}", end="\r")
    print(f"\nSuccessfully inserted {len(inserted_installments)} installments.")

    # Now generate payments for the installments that were inserted as "Paid"
    print("\nGenerating payments for paid installments...")
    payments_to_insert = []
    for inst in inserted_installments:
        if inst["status"] == "Paid":
            payments_to_insert.append({
                "installment_id": inst["id"],
                "amount_received": inst["amount"],
                "payment_date": inst["paid_date"],
                "payment_method": "Cash",
                "notes": "Monthly installment payment received."
            })
            
    print(f"Total payments calculated: {len(payments_to_insert)}")
    print("Inserting payments in batches...")
    inserted_payments = []
    for j in range(0, len(payments_to_insert), inst_batch_size):
        batch = payments_to_insert[j:j+inst_batch_size]
        res = db.table("payments").insert(batch).execute()
        inserted_payments.extend(res.data)
        print(f"Inserted payments: {len(inserted_payments)}/{len(payments_to_insert)}", end="\r")
    print(f"\nSuccessfully inserted {len(inserted_payments)} payments.")

    # =========================================================================
    # 6. CLEAR CACHE & DONE
    # =========================================================================
    print("\nClearing local persistent cache to trigger full sync upon next app launch...")
    CacheService.clear()

    print("\n" + "="*50)
    print("MOCK DATA GENERATION SUCCESSFUL")
    print("="*50)
    print(f"Total Suppliers Created:   {len(inserted_suppliers)}")
    print(f"Total Customers Created:   {len(inserted_customers)}")
    print(f"Total Devices Created:     {len(inserted_devices)}")
    print(f"Total Sales Ledgers:       {len(inserted_sales)}")
    print(f"Total Installment Records: {len(inserted_installments)}")
    print(f"Total Payment Transactions: {len(inserted_payments)}")
    print("="*50)
    print("You can now verify the database size in your Supabase dashboard under: Project Settings -> Database.")
    print("="*50)

if __name__ == "__main__":
    generate_1000_active_ledgers()
