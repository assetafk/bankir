-- Add first_name and last_name to accounts (idempotent)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'accounts' AND column_name = 'first_name'
  ) THEN
    ALTER TABLE accounts ADD COLUMN first_name VARCHAR(100) NOT NULL DEFAULT '';
  END IF;
END$$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'accounts' AND column_name = 'last_name'
  ) THEN
    ALTER TABLE accounts ADD COLUMN last_name VARCHAR(100) NOT NULL DEFAULT '';
  END IF;
END$$;
