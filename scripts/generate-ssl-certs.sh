#!/bin/bash

# Script to generate self-signed SSL certificates for development
# For production, use certificates from a trusted CA (Let's Encrypt, etc.)

set -e

CERT_DIR="ssl"
FRONTEND_SSL_DIR="../frontend/ssl"

echo "Generating SSL certificates for development..."

# Create directories
mkdir -p "$CERT_DIR"
mkdir -p "$FRONTEND_SSL_DIR"

# Generate private key
openssl genrsa -out "$CERT_DIR/key.pem" 2048

# Generate certificate signing request
openssl req -new -key "$CERT_DIR/key.pem" -out "$CERT_DIR/csr.pem" \
    -subj "/C=US/ST=State/L=City/O=Banking Service/CN=localhost"

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in "$CERT_DIR/csr.pem" -signkey "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -extensions v3_req \
    -extfile <(
        echo "[v3_req]"
        echo "subjectAltName=@alt_names"
        echo "[alt_names]"
        echo "DNS.1=localhost"
        echo "DNS.2=*.localhost"
        echo "IP.1=127.0.0.1"
        echo "IP.2=::1"
    )

# Copy certificates to frontend directory
cp "$CERT_DIR/cert.pem" "$FRONTEND_SSL_DIR/cert.pem"
cp "$CERT_DIR/key.pem" "$FRONTEND_SSL_DIR/key.pem"

echo "SSL certificates generated successfully!"
echo "Certificates are in: $CERT_DIR and $FRONTEND_SSL_DIR"
echo ""
echo "WARNING: These are self-signed certificates for development only."
echo "For production, use certificates from a trusted CA (Let's Encrypt, etc.)"
