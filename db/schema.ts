import { pgTable, uuid, varchar, text, timestamp, integer, numeric, date, uniqueIndex, boolean } from 'drizzle-orm/pg-core';
import { sql } from 'drizzle-orm';

// 1. CUSTOMERS TABLE
export const customers = pgTable('customers', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  name: varchar('name', { length: 255 }).notNull(),
  fatherName: varchar('father_name', { length: 255 }).notNull(),
  mobile: varchar('mobile', { length: 20 }).notNull(),
  address: text('address'),
  remarks: text('remarks'),
  remindersEnabled: boolean('reminders_enabled').default(true).notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
});

// 2. DEVICES TABLE
export const devices = pgTable('devices', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  name: varchar('name', { length: 255 }).notNull(),
  brand: varchar('brand', { length: 255 }).notNull(),
  model: varchar('model', { length: 255 }).notNull(),
  ram: varchar('ram', { length: 50 }).notNull(),
  rom: varchar('rom', { length: 50 }).notNull(),
  simType: integer('sim_type').notNull(),
  imei1: varchar('imei_1', { length: 15 }).notNull(),
  imei2: varchar('imei_2', { length: 15 }),
  imei3: varchar('imei_3', { length: 15 }),
  imei4: varchar('imei_4', { length: 15 }),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
}, (table) => {
  return {
    imei1Idx: uniqueIndex('idx_devices_imei_1').on(table.imei1),
    imei2Idx: uniqueIndex('idx_devices_imei_2').on(table.imei2),
    imei3Idx: uniqueIndex('idx_devices_imei_3').on(table.imei3),
    imei4Idx: uniqueIndex('idx_devices_imei_4').on(table.imei4),
  };
});

// 3. SALES TABLE
export const sales = pgTable('sales', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  customerId: uuid('customer_id').notNull().references(() => customers.id, { onDelete: 'restrict' }),
  deviceId: uuid('device_id').notNull().references(() => devices.id, { onDelete: 'restrict' }),
  costPrice: numeric('cost_price', { precision: 12, scale: 2 }).notNull(),
  sellingPrice: numeric('selling_price', { precision: 12, scale: 2 }).notNull(),
  downPayment: numeric('down_payment', { precision: 12, scale: 2 }).notNull(),
  installmentMonths: integer('installment_months').notNull(),
  startDate: date('start_date').notNull(),
  margin: numeric('margin', { precision: 12, scale: 2 }), // Handled as generated or client-calculated
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
});

// 4. INSTALLMENTS TABLE
export const installments = pgTable('installments', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  saleId: uuid('sale_id').notNull().references(() => sales.id, { onDelete: 'cascade' }),
  dueDate: date('due_date').notNull(),
  amount: numeric('amount', { precision: 12, scale: 2 }).notNull(),
  status: varchar('status', { length: 50 }).default('Pending').notNull(),
  paidDate: date('paid_date'),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
});

// 5. PAYMENTS TABLE
export const payments = pgTable('payments', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  installmentId: uuid('installment_id').notNull().references(() => installments.id, { onDelete: 'cascade' }),
  amountReceived: numeric('amount_received', { precision: 12, scale: 2 }).notNull(),
  paymentDate: date('payment_date').notNull(),
  notes: text('notes'),
  paymentMethod: varchar('payment_method', { length: 50 }).default('Cash').notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
});

// 6. AUDIT LOGS TABLE
export const auditLogs = pgTable('audit_logs', {
  id: uuid('id').default(sql`gen_random_uuid()`).primaryKey(),
  userEmail: varchar('user_email', { length: 255 }).notNull(),
  action: varchar('action', { length: 500 }).notNull(),
  logDate: date('log_date').default(sql`CURRENT_DATE`).notNull(),
  logTime: varchar('log_time', { length: 20 }).notNull(),
  ipAddress: varchar('ip_address', { length: 50 }).notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
});

