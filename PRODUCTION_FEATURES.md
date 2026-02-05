# Production Features Documentation

This document details all production-level features implemented in the banking service.

## 1. Anti-Fraud Checks

### Implementation
- **Service**: `backend/app/services/fraud_service.py`
- **Integration**: Automatically called before every transfer

### Checks Performed

#### Amount Limits
- **Maximum per transaction**: $1,000,000
- **Maximum daily per user**: $5,000,000
- **Minimum per transaction**: $0.01

#### Transaction Frequency
- **Hourly limit**: 50 transactions per hour per user
- **Daily limit**: 200 transactions per day per user

#### IP Rate Limiting
- **Limit**: 10 requests per minute per IP address
- **Storage**: Redis with 1-minute TTL

### Response
- **Blocked transfers**: Return 403 Forbidden with reason
- **Audit logging**: All fraud checks are logged
- **Admin monitoring**: Fraud statistics available via admin API

## 2. Audit Logging

### Implementation
- **Model**: `backend/app/models/audit_log.py`
- **Service**: `backend/app/services/audit_service.py`

### Logged Actions
- CREATE, UPDATE, DELETE (accounts, transactions)
- TRANSFER (all money transfers)
- LOGIN, LOGOUT (authentication events)
- FRAUD_CHECK (fraud detection events)
- ACCOUNT_ACCESS (account access events)

### Information Captured
- User ID
- IP Address
- User-Agent
- Request ID (for request tracking)
- Timestamp
- Action details (JSON)
- Status (success, failed, blocked)
- Error messages (if any)

### API Endpoints
- `GET /api/v1/admin/audit-logs` - Query audit logs with filters

## 3. Soft Delete

### Implementation
- **Service**: `backend/app/services/soft_delete.py`
- **Models**: Account, Transaction have `is_deleted` and `deleted_at` fields

### Features
- **Data Retention**: Records are never permanently deleted
- **Automatic Filtering**: All queries automatically exclude soft-deleted records
- **Recovery**: Soft-deleted records can be restored
- **Audit Trail**: Deletion timestamps preserved

### Usage
```python
# Soft delete an account
SoftDeleteService.soft_delete(db, account)

# Restore a soft-deleted account
SoftDeleteService.restore(db, account)

# Query automatically excludes soft-deleted records
accounts = SoftDeleteService.get_active_query(query, Account).all()
```

## 4. Ledger Logic (Double-Entry Bookkeeping)

### Implementation
- **Model**: `backend/app/models/ledger_entry.py`
- **Service**: `backend/app/services/ledger_service.py`

### How It Works
Every transaction creates two ledger entries:
1. **Debit Entry**: Money leaving the source account
2. **Credit Entry**: Money entering the destination account

### Features
- **Balance Tracking**: Records balance before and after each transaction
- **Verification**: Admin endpoint to verify ledger balances match account balances
- **Audit Trail**: Complete financial audit trail
- **Atomicity**: Ledger entries created atomically with transactions

### API Endpoints
- `GET /api/v1/admin/ledger/verify/{account_id}` - Verify ledger balance

## 5. Enhanced Idempotency (Double Request Protection)

### Implementation
- **Service**: `backend/app/services/idempotency.py`
- **Storage**: Redis

### Features
- **Response Caching**: Cached responses for 24 hours
- **Processing Flags**: Prevents duplicate concurrent requests
- **Conflict Detection**: Returns 409 Conflict for duplicate concurrent requests
- **Automatic Cleanup**: Processing flags cleared on completion or error

### Flow
1. Check if idempotency key exists → return cached response
2. Check if request is processing → return 409 Conflict
3. Mark request as processing
4. Execute request
5. Store response
6. Clear processing flag

## 6. Failure Handling

### Implementation
- **Retry Logic**: Automatic retries for transient database errors
- **Transaction Rollback**: Automatic rollback on any failure
- **Balance Restoration**: Account balances restored on failure
- **Error Logging**: All failures logged with full context

### Retry Configuration
- **Max Retries**: 3 attempts
- **Retry Delay**: Exponential backoff (1s, 2s, 3s)
- **Retryable Errors**: OperationalError, IntegrityError
- **Non-Retryable**: Validation errors, business logic errors

### Failure Tracking
- **Transaction Status**: FAILED status for failed transactions
- **Failure Reason**: Stored in `failure_reason` field
- **Retry Count**: Tracked in `retry_count` field
- **Audit Logging**: All failures logged

## 7. Production-Level Atomicity

### Implementation
- **SELECT FOR UPDATE**: Row-level locking
- **Transaction Context**: Context manager for atomic operations
- **Nested Transactions**: Proper handling of nested operations

### Features
- **Row-Level Locking**: Accounts locked during transfer
- **All-or-Nothing**: Either all operations succeed or all rollback
- **Deadlock Prevention**: Ordered locking (from_account, then to_account)
- **Balance Consistency**: Balances always consistent

### Example
```python
with transaction_context(db):
    # All operations are atomic
    from_account.balance -= amount
    to_account.balance += amount
    create_ledger_entries(...)
    create_audit_log(...)
    # If any fails, all rollback
```

## 8. API Endpoints

### Admin Endpoints

#### Audit Logs
```
GET /api/v1/admin/audit-logs
Query Parameters:
  - user_id: Filter by user
  - action: Filter by action type
  - resource_type: Filter by resource type
  - start_date: Start date filter
  - end_date: End date filter
  - page: Page number
  - page_size: Items per page
```

#### Ledger Verification
```
GET /api/v1/admin/ledger/verify/{account_id}
Returns: Verification result with balance comparison
```

#### Fraud Statistics
```
GET /api/v1/admin/fraud-stats
Query Parameters:
  - start_date: Start date filter
  - end_date: End date filter
Returns: Fraud detection statistics
```

## Database Schema

### New Tables

#### audit_logs
- Comprehensive audit trail
- Indexed for fast queries
- JSON details field for flexible data

#### ledger_entries
- Double-entry bookkeeping records
- Composite indexes for performance
- Balance tracking

### Enhanced Tables

#### accounts
- `is_deleted`: Boolean flag
- `deleted_at`: Timestamp

#### transactions
- `is_deleted`: Boolean flag
- `deleted_at`: Timestamp
- `failure_reason`: Text field
- `retry_count`: Integer

## Migration

Run the migration to add production features:

```bash
alembic upgrade head
```

This will create:
- audit_logs table
- ledger_entries table
- Add soft delete fields to accounts and transactions

## Monitoring and Compliance

### What to Monitor
- Fraud detection rate
- Failed transaction rate
- Ledger balance discrepancies
- Audit log volume
- Idempotency key usage

### Compliance
- **Audit Trail**: Complete audit trail for compliance
- **Data Retention**: Soft delete preserves data for compliance
- **Financial Accuracy**: Double-entry ledger ensures accuracy
- **Security**: All operations logged with IP and user agent
