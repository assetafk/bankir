-- =============================================================================
-- 001_schema.sql — полная схема БД (users, accounts, transactions, ledger,
--                  audit_logs, transfers, idempotency_keys, outbox_events)
-- =============================================================================

-- Enum types (public schema, idempotent)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON t.typnamespace = n.oid
    WHERE n.nspname = 'public' AND t.typname = 'transactionstatus'
  ) THEN
    CREATE TYPE public.transactionstatus AS ENUM (
      'PENDING', 'COMPLETED', 'FAILED'
    );
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON t.typnamespace = n.oid
    WHERE n.nspname = 'public' AND t.typname = 'ledgerentrytype'
  ) THEN
    CREATE TYPE public.ledgerentrytype AS ENUM ('DEBIT', 'CREDIT');
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON t.typnamespace = n.oid
    WHERE n.nspname = 'public' AND t.typname = 'auditaction'
  ) THEN
    CREATE TYPE public.auditaction AS ENUM (
      'CREATE', 'UPDATE', 'DELETE', 'TRANSFER', 'LOGIN', 'LOGOUT',
      'FRAUD_CHECK', 'ACCOUNT_ACCESS'
    );
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON t.typnamespace = n.oid
    WHERE n.nspname = 'public' AND t.typname = 'transferstatus'
  ) THEN
    CREATE TYPE public.transferstatus AS ENUM (
      'PENDING', 'COMPLETED', 'FAILED'
    );
  END IF;
END$$;

-- -----------------------------------------------------------------------------
-- users
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id   SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);

-- -----------------------------------------------------------------------------
-- accounts
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accounts (
  id         SERIAL PRIMARY KEY,
  user_id    INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  first_name VARCHAR(100) NOT NULL DEFAULT '',
  last_name  VARCHAR(100) NOT NULL DEFAULT '',
  currency   VARCHAR(3) NOT NULL,
  balance    NUMERIC(20, 2) NOT NULL DEFAULT 0,
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_accounts_id ON accounts (id);
CREATE INDEX IF NOT EXISTS ix_accounts_user_id ON accounts (user_id);
CREATE INDEX IF NOT EXISTS ix_accounts_currency ON accounts (currency);
CREATE INDEX IF NOT EXISTS ix_accounts_is_deleted ON accounts (is_deleted);

-- -----------------------------------------------------------------------------
-- transactions (ядро + ledger)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
  id               SERIAL PRIMARY KEY,
  from_account_id  INTEGER REFERENCES accounts (id) ON DELETE SET NULL,
  to_account_id    INTEGER NOT NULL REFERENCES accounts (id) ON DELETE RESTRICT,
  amount           NUMERIC(20, 2) NOT NULL,
  currency         VARCHAR(3) NOT NULL,
  status           public.transactionstatus NOT NULL DEFAULT 'PENDING',
  is_deleted       BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at       TIMESTAMPTZ,
  failure_reason   TEXT,
  retry_count      INTEGER NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_transactions_id ON transactions (id);
CREATE INDEX IF NOT EXISTS ix_transactions_from_account_id ON transactions (from_account_id);
CREATE INDEX IF NOT EXISTS ix_transactions_to_account_id ON transactions (to_account_id);
CREATE INDEX IF NOT EXISTS ix_transactions_status ON transactions (status);
CREATE INDEX IF NOT EXISTS ix_transactions_created_at ON transactions (created_at);
CREATE INDEX IF NOT EXISTS ix_transactions_is_deleted ON transactions (is_deleted);

-- -----------------------------------------------------------------------------
-- ledger_entries (главная бухгалтерская книга)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ledger_entries (
  id             SERIAL PRIMARY KEY,
  transaction_id INTEGER NOT NULL REFERENCES transactions (id) ON DELETE CASCADE,
  account_id     INTEGER NOT NULL REFERENCES accounts (id) ON DELETE RESTRICT,
  entry_type     public.ledgerentrytype NOT NULL,
  amount         NUMERIC(20, 2) NOT NULL,
  currency       VARCHAR(3) NOT NULL,
  balance_before NUMERIC(20, 2) NOT NULL,
  balance_after  NUMERIC(20, 2) NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ledger_entries_id ON ledger_entries (id);
CREATE INDEX IF NOT EXISTS ix_ledger_entries_transaction_id ON ledger_entries (transaction_id);
CREATE INDEX IF NOT EXISTS ix_ledger_entries_account_id ON ledger_entries (account_id);
CREATE INDEX IF NOT EXISTS ix_ledger_entries_entry_type ON ledger_entries (entry_type);
CREATE INDEX IF NOT EXISTS ix_ledger_entries_created_at ON ledger_entries (created_at);
CREATE INDEX IF NOT EXISTS idx_ledger_account_created ON ledger_entries (account_id, created_at);

-- -----------------------------------------------------------------------------
-- audit_logs
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
  id           SERIAL PRIMARY KEY,
  user_id       INTEGER,
  action        public.auditaction NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  resource_id   INTEGER,
  ip_address   VARCHAR(45),
  user_agent   TEXT,
  request_id   VARCHAR(100),
  details      JSONB,
  status       VARCHAR(20) NOT NULL DEFAULT 'success',
  error_message TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_id ON audit_logs (id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_resource_type ON audit_logs (resource_type);
CREATE INDEX IF NOT EXISTS ix_audit_logs_resource_id ON audit_logs (resource_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_request_id ON audit_logs (request_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_status ON audit_logs (status);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);

-- -----------------------------------------------------------------------------
-- transfers (1:1 с transaction)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transfers (
  id               SERIAL PRIMARY KEY,
  transaction_id    INTEGER NOT NULL UNIQUE REFERENCES transactions (id) ON DELETE CASCADE,
  from_account_id   INTEGER NOT NULL REFERENCES accounts (id) ON DELETE RESTRICT,
  to_account_id     INTEGER NOT NULL REFERENCES accounts (id) ON DELETE RESTRICT,
  amount            NUMERIC(20, 2) NOT NULL,
  currency          VARCHAR(3) NOT NULL,
  status            public.transferstatus NOT NULL DEFAULT 'PENDING',
  idempotency_key   VARCHAR(255),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_transfers_id ON transfers (id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_transfers_transaction_id ON transfers (transaction_id);
CREATE INDEX IF NOT EXISTS ix_transfers_from_account_id ON transfers (from_account_id);
CREATE INDEX IF NOT EXISTS ix_transfers_to_account_id ON transfers (to_account_id);
CREATE INDEX IF NOT EXISTS ix_transfers_status ON transfers (status);
CREATE INDEX IF NOT EXISTS ix_transfers_idempotency_key ON transfers (idempotency_key);
CREATE INDEX IF NOT EXISTS ix_transfers_created_at ON transfers (created_at);
CREATE INDEX IF NOT EXISTS ix_transfers_idempotency_from_to
  ON transfers (idempotency_key, from_account_id, to_account_id);

-- -----------------------------------------------------------------------------
-- idempotency_keys
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS idempotency_keys (
  id              SERIAL PRIMARY KEY,
  user_id         INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  idempotency_key VARCHAR(255) NOT NULL,
  request_hash    VARCHAR(64),
  response_body   TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_idempotency_keys_id ON idempotency_keys (id);
CREATE INDEX IF NOT EXISTS ix_idempotency_keys_user_id ON idempotency_keys (user_id);
CREATE INDEX IF NOT EXISTS ix_idempotency_keys_idempotency_key ON idempotency_keys (idempotency_key);
CREATE INDEX IF NOT EXISTS ix_idempotency_keys_expires_at ON idempotency_keys (expires_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_idempotency_user_key ON idempotency_keys (user_id, idempotency_key);

-- -----------------------------------------------------------------------------
-- outbox_events (transactional outbox)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS outbox_events (
  id             SERIAL PRIMARY KEY,
  aggregate_type  VARCHAR(100) NOT NULL,
  aggregate_id    VARCHAR(100) NOT NULL,
  event_type     VARCHAR(100) NOT NULL,
  payload        JSONB,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_outbox_events_id ON outbox_events (id);
CREATE INDEX IF NOT EXISTS ix_outbox_events_aggregate_type ON outbox_events (aggregate_type);
CREATE INDEX IF NOT EXISTS ix_outbox_events_aggregate_id ON outbox_events (aggregate_id);
CREATE INDEX IF NOT EXISTS ix_outbox_events_event_type ON outbox_events (event_type);
CREATE INDEX IF NOT EXISTS ix_outbox_events_created_at ON outbox_events (created_at);
CREATE INDEX IF NOT EXISTS ix_outbox_events_processed_at ON outbox_events (processed_at);
