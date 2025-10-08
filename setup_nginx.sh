#!/usr/bin/env zsh

# Define base NGINX directory
NGINX_DIR="/usr/local/etc/nginx"
SSL_DIR="$NGINX_DIR/ssl"

# Clear default nginx setup
rm -r "$NGINX_DIR"

# Setup directories
mkdir -p "$SSL_DIR"

# Copy configuration
cp ./nginx.conf "$NGINX_DIR/nginx.conf"

# Copy certificate and private key
cp ./localhost+2.pem "$SSL_DIR/localhost+2.pem"
cp ./localhost+2-key.pem "$SSL_DIR/localhost+2-key.pem"

chown -R root:wheel "$SSL_DIR"              # Change owner of certificates directory to the root
chmod 644 "$SSL_DIR"/localhost+2.pem        # Certificates are public -> everyone can read
chmod 600 "$SSL_DIR"/localhost+2-key.pem    # Private key only accessible by root

# Reload nginx with new configuration
nginx -s reload

echo "NGINX Configuration Done"
exit
