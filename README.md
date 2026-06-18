# Device/Mobile Installment Management System

An enterprise-grade desktop POS application designed for mobile shops and electronics stores to register customer records, manage device sales transactions, generate installment schedules, track payments, monitor due dates, and export report files. Built with **Python PyQt6** and backed by **Supabase (PostgreSQL)**.

---

## Technical Stack & Architecture
- **GUI Framework:** Python PyQt6
- **Database Backend:** Supabase (Auth, RLS Policies, PostgreSQL)
- **Reporting:** ReportLab (Ledger PDF generation), Pandas (Excel & CSV exports)
- **Data Visualizations:** Matplotlib (KPI charts)
- **Architecture Pattern:** MVVM (Model-View-ViewModel) + Repository Layer Pattern

---

## Getting Started

### 1. Prerequisites
- Python 3.9+
- A Supabase Project (database + authentication)

### 2. Database Schema Setup
Execute the SQL commands inside [database/schema.sql](file:///c:/Users/mujah/OneDrive/Desktop/Installment_Software/database/schema.sql) in your Supabase SQL Editor. This will configure the required tables, check constraints (for CNIC, Phone, and IMEI lengths), indexes, and Row Level Security (RLS) policies.

### 3. Installation
Clone/download this repository to your workspace, navigate to the folder, and run:

```bash
pip install -r requirements.txt
```

### 4. Configuration Environment
Create a `.env` file in the root workspace directory with the following variables:

```ini
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_public_key
```

### 5. Running the Application
Ensure the environment variables are set, and then execute:

```bash
python src/main.py
```

### 6. Executing Unit Tests
Run the automated test suite to verify the logic of calculators and input formats:

```bash
pytest src/tests/
```
