# Banking Service

Production-ready banking service built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker, Redis, and Celery.

## Features

- **Account Management**: Create and manage multi-currency accounts
- **Money Transfers**: Transfer money between accounts with concurrency control (SELECT FOR UPDATE)
- **Transaction History**: View transaction history with filtering and pagination
- **Idempotency**: Prevent duplicate transfers using Redis-based idempotency keys
- **Authentication**: JWT-based authentication and authorization
- **Multi-Currency Support**: Support for multiple currencies (USD, EUR, GBP, etc.)
- **Security**: HTTPS/TLS encryption, security headers, MITM attack protection, and comprehensive XSS protection
- **Anti-Fraud**: Rate limiting, amount limits, transaction frequency checks, IP-based protection
- **Audit Logging**: Comprehensive logging of all operations for compliance and security
- **Soft Delete**: Data retention with soft delete functionality
- **Ledger Logic**: Double-entry bookkeeping for financial accuracy
- **Enhanced Idempotency**: Double request protection with processing flags
- **Failure Handling**: Retry mechanisms, compensation transactions, and error recovery

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Relational database
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration tool
- **Redis**: Caching and idempotency key storage
- **Celery**: Asynchronous task processing
- **Docker**: Containerization and orchestration

### Frontend
- **React**: Modern UI library
- **Webpack**: Module bundler and build tool
- **Babel**: JavaScript compiler
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Axios**: HTTP client for API calls

## Project Structure

```
bankir/
├── backend/                    # Backend application
│   ├── app/                    # Application code
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI application entry point
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # Database connection and session
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── api/                # API routes
│   │   │   └── v1/
│   │   ├── services/           # Business logic
│   │   ├── core/               # Core utilities
│   │   └── tasks/              # Celery tasks
│   ├── alembic/                # Database migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                   # Frontend application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API services
│   │   ├── utils/              # Utility functions
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   ├── package.json
│   ├── webpack.config.js
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

```bash
cp .env.example .env
```

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (generate a strong random key)
- `REDIS_HOST`, `REDIS_PORT`: Redis connection details
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`: Celery broker and result backend

### Docker Setup

1. **Start all services**:
```bash
docker-compose up -d
```

2. **Run database migrations**:
```bash
docker-compose exec app alembic upgrade head
```

Note: The `alembic` command should be run from the backend directory context, or use:
```bash
docker-compose exec app sh -c "cd /app && alembic upgrade head"
```

3. **Access the application**:
- Frontend (HTTPS): https://localhost:3443
- Frontend (HTTP - redirects to HTTPS): http://localhost:3000
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Note**: For HTTPS in development, self-signed certificates are automatically generated. Your browser will show a security warning - this is expected. Click "Advanced" and "Proceed to localhost" to continue.

### Local Development Setup

#### Backend

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run database migrations**:
```bash
alembic upgrade head
```

4. **Start the development server**:
```bash
uvicorn app.main:app --reload
```

5. **Start Celery worker** (in a separate terminal):
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

6. **Start Celery beat** (for scheduled tasks, in another terminal):
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

#### Frontend

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Set up environment variables** (optional):
```bash
cp .env.example .env
# Edit .env if needed (defaults to http://localhost:8000/api/v1)
```

4. **Start development server**:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token
- `GET /api/v1/auth/me` - Get current user information

### Accounts

- `POST /api/v1/accounts` - Create a new account
- `GET /api/v1/accounts` - Get all accounts for current user
- `GET /api/v1/accounts/{account_id}` - Get account by ID

### Transfers

- `POST /api/v1/transfers` - Transfer money between accounts
  - Requires `Idempotency-Key` header to prevent duplicate transfers
  - Includes anti-fraud checks, audit logging, and ledger entries

### Transactions

- `GET /api/v1/transactions` - Get transaction history
  - Query parameters: `account_id`, `status`, `start_date`, `end_date`, `page`, `page_size`

### Admin (Production Monitoring)

- `GET /api/v1/admin/audit-logs` - Get audit logs (admin only)
- `GET /api/v1/admin/ledger/verify/{account_id}` - Verify ledger balance (admin only)
- `GET /api/v1/admin/fraud-stats` - Get fraud detection statistics (admin only)

## Frontend Features

The frontend provides a modern, user-friendly interface for all banking operations:

- **Authentication**: Secure login and registration
- **Dashboard**: Overview of accounts, balances, and recent activity
- **Account Management**: Create and view multi-currency accounts
- **Money Transfers**: Easy-to-use transfer interface with real-time balance updates
- **Transaction History**: Filterable transaction list with pagination
- **Responsive Design**: Works on desktop and mobile devices

## Usage Examples

### Frontend Usage

1. **Register/Login**: Visit http://localhost:3000 and create an account or login
2. **Create Account**: Navigate to Accounts page and create a new account
3. **Transfer Money**: Use the Transfers page to send money between accounts
4. **View History**: Check the Transactions page for complete transaction history

### API Usage Examples

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword123"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 3. Create an Account

```bash
curl -X POST "http://localhost:8000/api/v1/accounts" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "currency": "USD",
    "initial_balance": 1000.00
  }'
```

### 4. Transfer Money

```bash
curl -X POST "http://localhost:8000/api/v1/transfers" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-12345" \
  -d '{
    "from_account_id": 1,
    "to_account_id": 2,
    "amount": 100.00,
    "currency": "USD"
  }'
```

### 5. Get Transaction History

```bash
curl -X GET "http://localhost:8000/api/v1/transactions?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Key Features Implementation

### SELECT FOR UPDATE

The transfer service uses `SELECT FOR UPDATE` to ensure row-level locking during concurrent transfers:

```python
from_account = db.query(Account).with_for_update().filter(
    Account.id == from_account_id,
    Account.user_id == from_user_id
).first()
```

This prevents race conditions when multiple transfers occur simultaneously.

### Idempotency

Idempotency is implemented using Redis. Each transfer request should include an `Idempotency-Key` header. If the same key is used again, the cached response is returned instead of processing a duplicate transfer.

- Key format: `idempotency:{user_id}:{idempotency_key}`
- TTL: 24 hours (configurable via `IDEMPOTENCY_TTL`)

### Multi-Currency Support

The service supports multiple currencies. Supported currencies include:
USD, EUR, GBP, JPY, AUD, CAD, CHF, CNY, INR, RUB, BRL, ZAR, MXN, SGD, HKD, NOK, SEK, DKK, PLN, TRY, NZD, KRW, THB, IDR

## Database Migrations

### Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback migration:
```bash
alembic downgrade -1
```

## Testing

The project structure supports testing. Add tests in a `tests/` directory:

```bash
# Example test structure
tests/
├── test_accounts.py
├── test_transfers.py
└── test_transactions.py
```

## Production Considerations

1. **Security**:
   - Change `SECRET_KEY` to a strong random value
   - Use HTTPS in production
   - Configure CORS appropriately
   - Implement rate limiting

2. **Database**:
   - Use connection pooling (already configured)
   - Set up database backups
   - Monitor database performance

3. **Redis**:
   - Configure Redis persistence
   - Set up Redis replication for high availability

4. **Monitoring**:
   - Add logging and monitoring
   - Set up health checks
   - Monitor Celery tasks

5. **Scaling**:
   - Use load balancer for multiple app instances
   - Scale Celery workers based on load
   - Consider database read replicas

## Health Check

The service includes a health check endpoint:

```bash
curl http://localhost:8000/health
```

## Security

The application includes comprehensive security measures to protect against MITM attacks and other security threats:

- **HTTPS/TLS Encryption**: All communications are encrypted
- **Security Headers**: HSTS, CSP, X-Frame-Options, and more
- **Secure CORS Configuration**: Whitelist-based origin control
- **Request Tracking**: Unique request IDs for all requests
- **SSL/TLS Best Practices**: Strong cipher suites and protocols only

See [SECURITY.md](SECURITY.md) for detailed security documentation and production deployment guidelines.

## License

This project is for demonstration purposes.
