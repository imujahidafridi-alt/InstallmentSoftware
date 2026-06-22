import postgres from 'postgres';
import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

dotenv.config({ path: 'c:\\Users\\mujah\\OneDrive\\Desktop\\Installment_Software\\.env' });

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  console.error("Error: DATABASE_URL is missing from environment.");
  process.exit(1);
}

const sql = postgres(connectionString);

async function main() {
  console.log("Reading schema.sql...");
  const schemaPath = "c:\\Users\\mujah\\OneDrive\\Desktop\\Installment_Software\\database\\schema.sql";
  const sqlContent = fs.readFileSync(schemaPath, 'utf8');

  console.log("Executing SQL statements on Supabase...");
  // Use sql.unsafe to execute the multi-statement query content
  await sql.unsafe(sqlContent);
  console.log("RLS policies and schema updates successfully pushed to Supabase!");
}

main().catch(err => {
  console.error("Failed to push schema:", err);
  process.exit(1);
}).finally(() => {
  sql.end();
});
