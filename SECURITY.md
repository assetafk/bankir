# Security Documentation

This document outlines the security measures implemented to protect against various attacks, including Man-in-the-Middle (MITM) attacks and Cross-Site Scripting (XSS) attacks.

## Security Features

### 1. HTTPS/TLS Encryption

All communications are encrypted using TLS 1.2 and TLS 1.3:

- **Frontend**: Nginx serves content over HTTPS (port 443)
- **Backend API**: All API calls are made over HTTPS
- **HTTP to HTTPS Redirect**: All HTTP traffic is automatically redirected to HTTPS

### 2. Security Headers

The application implements multiple security headers:

- **Strict-Transport-Security (HSTS)**: Forces browsers to use HTTPS for 1 year
- **Content-Security-Policy (CSP)**: Strict CSP prevents XSS attacks by:
  - Blocking inline scripts (`'unsafe-inline'` removed from script-src)
  - Blocking `eval()` and similar functions (`'unsafe-eval'` removed)
  - Only allowing scripts from same origin
  - Blocking object/embed tags
- **X-Frame-Options**: Prevents clickjacking attacks
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-XSS-Protection**: Enables browser XSS protection
- **Referrer-Policy**: Controls referrer information
- **Permissions-Policy**: Restricts browser features

### 2.1. XSS Protection

Comprehensive XSS protection is implemented at multiple layers:

#### Input Sanitization
- **Automatic Sanitization**: All user inputs are automatically sanitized
- **HTML Escaping**: Special characters are HTML-escaped
- **Tag Removal**: All HTML tags are stripped from user input
- **Pattern Detection**: Dangerous patterns (JavaScript, event handlers) are detected and blocked
- **Pydantic Validators**: Schema-level validation prevents XSS in all API inputs

#### Output Encoding
- **JSON Encoding**: All output is properly encoded for JSON context
- **HTML Encoding**: HTML entities are properly escaped
- **Context-Aware Encoding**: Encoding is applied based on output context

#### Middleware Protection
- **XSS Detection Middleware**: Validates all request data (query params, headers, body)
- **Pattern Matching**: Detects common XSS attack patterns
- **Automatic Blocking**: Blocks requests containing XSS patterns

#### Schema Validation
- **Email Sanitization**: Email addresses are validated and sanitized
- **String Field Sanitization**: All string fields are sanitized with length limits
- **Currency Code Validation**: Currency codes are validated and sanitized
- **Idempotency Key Validation**: Idempotency keys are sanitized

### 3. CORS Configuration

Cross-Origin Resource Sharing is configured with:

- Whitelist of allowed origins (no wildcards in production)
- Specific allowed methods (GET, POST, PUT, DELETE, OPTIONS)
- Specific allowed headers
- Credentials support with secure origins only
- Preflight request caching (1 hour)

### 4. SSL/TLS Configuration

- **Protocols**: Only TLS 1.2 and TLS 1.3 are allowed
- **Cipher Suites**: Strong, modern cipher suites only
- **OCSP Stapling**: Enabled for certificate validation
- **Session Management**: Secure session handling

### 5. Request Tracking

- Unique Request ID for each request
- Request ID included in response headers for debugging and tracking

## Production Deployment

### SSL Certificates

For production, use certificates from a trusted Certificate Authority:

1. **Let's Encrypt** (Recommended for free certificates):
   ```bash
   certbot certonly --standalone -d yourdomain.com
   ```

2. **Commercial CA**: Purchase certificates from trusted providers

3. **Update nginx.conf**: Point to your production certificates:
   ```nginx
   ssl_certificate /etc/nginx/ssl/fullchain.pem;
   ssl_certificate_key /etc/nginx/ssl/privkey.pem;
   ```

### Environment Variables

Set the following in production:

```bash
# Force HTTPS redirects
FORCE_HTTPS=true

# Set allowed origins (comma-separated)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Security Checklist

- [ ] Use production SSL certificates from trusted CA
- [ ] Set `FORCE_HTTPS=true` in production
- [ ] Configure `ALLOWED_ORIGINS` with your production domains
- [ ] Use strong `SECRET_KEY` (generate with: `openssl rand -hex 32`)
- [ ] Enable database encryption at rest
- [ ] Use secure password hashing (already implemented with bcrypt)
- [ ] Implement rate limiting (consider adding)
- [ ] Set up monitoring and alerting
- [ ] Regular security audits
- [ ] Keep dependencies updated

## Development

For development, self-signed certificates are generated automatically. To generate manually:

```bash
cd scripts
chmod +x generate-ssl-certs.sh
./generate-ssl-certs.sh
```

**Note**: Browsers will show a warning for self-signed certificates. This is expected in development.

## Additional Security Recommendations

1. **Rate Limiting**: Consider adding rate limiting middleware
2. **IP Whitelisting**: For admin endpoints
3. **Two-Factor Authentication**: For sensitive operations
4. **Audit Logging**: Log all security-relevant events
5. **Regular Updates**: Keep all dependencies updated
6. **Security Headers Testing**: Use tools like securityheaders.com
7. **Penetration Testing**: Regular security assessments

## Monitoring

Monitor for:

- Failed authentication attempts
- Unusual request patterns
- SSL certificate expiration
- Security header compliance
- CORS violations

## Production Features

### Anti-Fraud System

The application includes comprehensive anti-fraud checks:

- **Amount Limits**: 
  - Maximum per transaction: $1,000,000
  - Maximum daily per user: $5,000,000
  - Minimum per transaction: $0.01
- **Transaction Frequency Limits**:
  - Maximum 50 transactions per hour per user
  - Maximum 200 transactions per day per user
- **IP Rate Limiting**: 10 requests per minute per IP address
- **Automatic Blocking**: Suspicious transactions are automatically blocked and logged

### Audit Logging

All operations are logged for compliance and security:

- **Logged Actions**: Create, Update, Delete, Transfer, Login, Logout, Fraud Checks
- **Information Captured**: User ID, IP address, User-Agent, Request ID, Timestamps
- **Status Tracking**: Success, Failed, Blocked
- **Query Interface**: Admin endpoints for viewing audit logs

### Soft Delete

Data is never permanently deleted:

- **Accounts**: Soft-deleted with `is_deleted` flag and `deleted_at` timestamp
- **Transactions**: Soft-deleted with failure reasons preserved
- **Recovery**: Soft-deleted records can be restored
- **Queries**: Active queries automatically exclude soft-deleted records

### Double-Entry Ledger

Financial accuracy guaranteed with double-entry bookkeeping:

- **Every Transaction**: Creates two ledger entries (debit and credit)
- **Balance Tracking**: Tracks balance before and after each transaction
- **Verification**: Admin endpoint to verify ledger balances match account balances
- **Audit Trail**: Complete financial audit trail

### Enhanced Idempotency

Double request protection:

- **Processing Flags**: Prevents duplicate concurrent requests
- **Response Caching**: Cached responses for 24 hours
- **Conflict Detection**: Returns 409 Conflict for duplicate concurrent requests
- **Automatic Cleanup**: Processing flags cleared on completion or error

### Failure Handling

Production-grade error handling:

- **Retry Logic**: Automatic retries for transient database errors (up to 3 attempts)
- **Exponential Backoff**: Increasing delay between retries
- **Transaction Rollback**: Automatic rollback on any failure
- **Balance Restoration**: Account balances restored on failure
- **Error Logging**: All failures logged with full context
- **Compensation**: Failed transactions marked with failure reasons

### Atomicity

Production-level transaction atomicity:

- **SELECT FOR UPDATE**: Row-level locking prevents race conditions
- **Transaction Context**: All-or-nothing transaction execution
- **Nested Transactions**: Proper handling of nested operations
- **Deadlock Prevention**: Ordered locking to prevent deadlocks

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly.
