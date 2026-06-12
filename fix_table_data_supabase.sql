-- FIX definitivo per column reports.table_data does not exist
ALTER TABLE reports ADD COLUMN IF NOT EXISTS table_data JSONB;

-- (Opzionale) Verifica che la colonna sia stata aggiunta
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name='reports' AND column_name='table_data';