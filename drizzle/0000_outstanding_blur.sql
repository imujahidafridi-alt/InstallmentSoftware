CREATE TABLE IF NOT EXISTS "customers" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"name" varchar(255) NOT NULL,
	"father_name" varchar(255) NOT NULL,
	"cnic" varchar(20) NOT NULL,
	"mobile" varchar(20) NOT NULL,
	"address" text,
	"remarks" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "chk_cnic_format" CHECK ("cnic" ~ '^[0-9]{5}-[0-9]{7}-[0-9]{1}$'),
	CONSTRAINT "chk_mobile_format" CHECK ("mobile" ~ '^03[0-9]{9}$')
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "devices" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"name" varchar(255) NOT NULL,
	"brand" varchar(255) NOT NULL,
	"model" varchar(255) NOT NULL,
	"ram" varchar(50) NOT NULL,
	"rom" varchar(50) NOT NULL,
	"sim_type" integer NOT NULL CHECK ("sim_type" BETWEEN 1 AND 4),
	"imei_1" varchar(15) NOT NULL,
	"imei_2" varchar(15),
	"imei_3" varchar(15),
	"imei_4" varchar(15),
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "chk_imei_1_numeric" CHECK ("imei_1" ~ '^[0-9]{15}$'),
	CONSTRAINT "chk_imei_2_numeric" CHECK ("imei_2" IS NULL OR "imei_2" ~ '^[0-9]{15}$'),
	CONSTRAINT "chk_imei_3_numeric" CHECK ("imei_3" IS NULL OR "imei_3" ~ '^[0-9]{15}$'),
	CONSTRAINT "chk_imei_4_numeric" CHECK ("imei_4" IS NULL OR "imei_4" ~ '^[0-9]{15}$')
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "installments" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"sale_id" uuid NOT NULL,
	"due_date" date NOT NULL,
	"amount" numeric(12, 2) NOT NULL,
	"status" varchar(50) DEFAULT 'Pending' NOT NULL,
	"paid_date" date,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "payments" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"installment_id" uuid NOT NULL,
	"amount_received" numeric(12, 2) NOT NULL,
	"payment_date" date NOT NULL,
	"notes" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "sales" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"customer_id" uuid NOT NULL,
	"device_id" uuid NOT NULL,
	"cost_price" numeric(12, 2) NOT NULL CHECK ("cost_price" >= 0),
	"selling_price" numeric(12, 2) NOT NULL CHECK ("selling_price" >= "cost_price"),
	"down_payment" numeric(12, 2) NOT NULL CHECK ("down_payment" >= 0 AND "down_payment" <= "selling_price"),
	"installment_months" integer NOT NULL CHECK ("installment_months" > 0),
	"start_date" date NOT NULL,
	"margin" numeric(12, 2) GENERATED ALWAYS AS ("selling_price" - "cost_price") STORED,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "installments" ADD CONSTRAINT "installments_sale_id_sales_id_fk" FOREIGN KEY ("sale_id") REFERENCES "public"."sales"("id") ON DELETE cascade ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "payments" ADD CONSTRAINT "payments_installment_id_installments_id_fk" FOREIGN KEY ("installment_id") REFERENCES "public"."installments"("id") ON DELETE cascade ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "sales" ADD CONSTRAINT "sales_customer_id_customers_id_fk" FOREIGN KEY ("customer_id") REFERENCES "public"."customers"("id") ON DELETE restrict ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "sales" ADD CONSTRAINT "sales_device_id_devices_id_fk" FOREIGN KEY ("device_id") REFERENCES "public"."devices"("id") ON DELETE restrict ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS "idx_devices_imei_1" ON "devices" ("imei_1");--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS "idx_devices_imei_2" ON "devices" ("imei_2") WHERE "imei_2" IS NOT NULL;--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS "idx_devices_imei_3" ON "devices" ("imei_3") WHERE "imei_3" IS NOT NULL;--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS "idx_devices_imei_4" ON "devices" ("imei_4") WHERE "imei_4" IS NOT NULL;