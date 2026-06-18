-- Enable RLS on all tables
ALTER TABLE "customers" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "devices" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "sales" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "installments" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "payments" ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any, to avoid duplicate errors
DROP POLICY IF EXISTS "allow_all_customers" ON "customers";
DROP POLICY IF EXISTS "allow_all_devices" ON "devices";
DROP POLICY IF EXISTS "allow_all_sales" ON "sales";
DROP POLICY IF EXISTS "allow_all_installments" ON "installments";
DROP POLICY IF EXISTS "allow_all_payments" ON "payments";

-- Create unrestricted policies for public (which includes anon and authenticated)
CREATE POLICY "allow_all_customers" ON "customers" FOR ALL TO public USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_devices" ON "devices" FOR ALL TO public USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_sales" ON "sales" FOR ALL TO public USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_installments" ON "installments" FOR ALL TO public USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_payments" ON "payments" FOR ALL TO public USING (true) WITH CHECK (true);