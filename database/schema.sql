-- Database Schema for Device/Mobile Installment Management System

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================================
-- 1. CUSTOMERS TABLE
-- =========================================================================
-- Ensure clean migration by dropping cnic column, index, and check constraint if they exist
ALTER TABLE customers DROP COLUMN IF EXISTS cnic CASCADE;
DROP INDEX IF EXISTS idx_customers_cnic;

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    father_name VARCHAR(255) NOT NULL,
    mobile VARCHAR(20) NOT NULL,
    address TEXT,
    remarks TEXT,
    reminders_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    
    -- Format validation rules
    CONSTRAINT chk_mobile_format CHECK (mobile ~ '^03[0-9]{9}$')
);

-- Indexes for fast searching
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
CREATE INDEX IF NOT EXISTS idx_customers_mobile ON customers(mobile);


-- =========================================================================
-- 2. DEVICES TABLE
-- =========================================================================
CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    ram VARCHAR(50) NOT NULL,
    rom VARCHAR(50) NOT NULL,
    sim_type INTEGER NOT NULL CHECK (sim_type BETWEEN 1 AND 4),
    imei_1 VARCHAR(15) NOT NULL,
    imei_2 VARCHAR(15),
    imei_3 VARCHAR(15),
    imei_4 VARCHAR(15),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,

    -- IMEI validations: exactly 15 digits numeric
    CONSTRAINT chk_imei_1_numeric CHECK (imei_1 ~ '^[0-9]{15}$'),
    CONSTRAINT chk_imei_2_numeric CHECK (imei_2 IS NULL OR imei_2 ~ '^[0-9]{15}$'),
    CONSTRAINT chk_imei_3_numeric CHECK (imei_3 IS NULL OR imei_3 ~ '^[0-9]{15}$'),
    CONSTRAINT chk_imei_4_numeric CHECK (imei_4 IS NULL OR imei_4 ~ '^[0-9]{15}$')
);

-- Ensure all IMEIs are unique globally
CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_imei_1 ON devices(imei_1);
CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_imei_2 ON devices(imei_2) WHERE imei_2 IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_imei_3 ON devices(imei_3) WHERE imei_3 IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_imei_4 ON devices(imei_4) WHERE imei_4 IS NOT NULL;


-- =========================================================================
-- 3. SALES TABLE
-- =========================================================================
CREATE TABLE IF NOT EXISTS sales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE RESTRICT,
    cost_price NUMERIC(12, 2) NOT NULL CHECK (cost_price >= 0),
    selling_price NUMERIC(12, 2) NOT NULL CHECK (selling_price >= cost_price),
    down_payment NUMERIC(12, 2) NOT NULL CHECK (down_payment >= 0 AND down_payment <= selling_price),
    installment_months INTEGER NOT NULL CHECK (installment_months > 0),
    start_date DATE NOT NULL,
    margin NUMERIC(12, 2) GENERATED ALWAYS AS (selling_price - cost_price) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for sale queries
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_device ON sales(device_id);


-- =========================================================================
-- 4. INSTALLMENTS TABLE
-- =========================================================================
CREATE TABLE IF NOT EXISTS installments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id UUID NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    due_date DATE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    status VARCHAR(50) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Paid', 'Partial')),
    paid_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for quick schedules
CREATE INDEX IF NOT EXISTS idx_installments_sale ON installments(sale_id);
CREATE INDEX IF NOT EXISTS idx_installments_due_date ON installments(due_date);
CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status);


-- =========================================================================
-- 5. PAYMENTS TABLE
-- =========================================================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installment_id UUID NOT NULL REFERENCES installments(id) ON DELETE CASCADE,
    amount_received NUMERIC(12, 2) NOT NULL CHECK (amount_received > 0),
    payment_date DATE NOT NULL,
    notes TEXT,
    payment_method VARCHAR(50) NOT NULL DEFAULT 'Cash',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for payment queries
CREATE INDEX IF NOT EXISTS idx_payments_installment ON payments(installment_id);


-- =========================================================================
-- 6. SECURITY & ROW LEVEL SECURITY (RLS) POLICIES
-- =========================================================================
-- Enable Row Level Security on all tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE installments ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Create basic RLS policies for authenticated and anonymous users
-- (Assumes store operators have full access)
DROP POLICY IF EXISTS "Allow full access for authenticated users to customers" ON customers;
CREATE POLICY "Allow full access for authenticated users to customers"
    ON customers FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow full access for authenticated users to devices" ON devices;
CREATE POLICY "Allow full access for authenticated users to devices"
    ON devices FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow full access for authenticated users to sales" ON sales;
CREATE POLICY "Allow full access for authenticated users to sales"
    ON sales FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow full access for authenticated users to installments" ON installments;
CREATE POLICY "Allow full access for authenticated users to installments"
    ON installments FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow full access for authenticated users to payments" ON payments;
CREATE POLICY "Allow full access for authenticated users to payments"
    ON payments FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);


-- =========================================================================
-- 7. AUDIT LOGS TABLE
-- =========================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email VARCHAR(255) NOT NULL,
    action VARCHAR(500) NOT NULL,
    log_date DATE NOT NULL DEFAULT CURRENT_DATE,
    log_time VARCHAR(20) NOT NULL,
    ip_address VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow full access for authenticated users to audit_logs" ON audit_logs;
CREATE POLICY "Allow full access for authenticated users to audit_logs"
    ON audit_logs FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

