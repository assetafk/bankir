-- Remove first_name and last_name from accounts
ALTER TABLE accounts DROP COLUMN IF EXISTS first_name;
ALTER TABLE accounts DROP COLUMN IF EXISTS last_name;
