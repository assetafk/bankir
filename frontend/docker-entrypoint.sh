#!/bin/sh
set -e

# Mounted volume may be read-only; use writable dir for generated certs
USER_SSL="/etc/nginx/ssl"
GEN_SSL="/var/lib/nginx/ssl"
SSL_CONF="/var/lib/nginx/ssl.conf"

if [ -f "$USER_SSL/cert.pem" ] && [ -f "$USER_SSL/key.pem" ]; then
  echo "HTTPS required: using certificates from $USER_SSL"
  printf 'ssl_certificate %s/cert.pem;\nssl_certificate_key %s/key.pem;\n' \
    "$USER_SSL" "$USER_SSL" > "$SSL_CONF"
else
  echo "HTTPS required: generating self-signed certificate in $GEN_SSL"
  mkdir -p "$GEN_SSL"
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$GEN_SSL/key.pem" \
    -out "$GEN_SSL/cert.pem" \
    -subj "/C=US/ST=State/L=City/O=Banking Service/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1"
  printf 'ssl_certificate %s/cert.pem;\nssl_certificate_key %s/key.pem;\n' \
    "$GEN_SSL" "$GEN_SSL" > "$SSL_CONF"
fi

exec nginx -g "daemon off;"
