-- =============================================================================
-- 001_schema_down.sql — откат схемы (порядок обратный созданию)
-- =============================================================================

DROP TABLE IF EXISTS outbox_events;
DROP TABLE IF EXISTS idempotency_keys;
DROP TABLE IF EXISTS transfers;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS ledger_entries;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS users;

DROP TYPE IF EXISTS public.transferstatus;
DROP TYPE IF EXISTS public.auditaction;
DROP TYPE IF EXISTS public.ledgerentrytype;
DROP TYPE IF EXISTS public.transactionstatus;
