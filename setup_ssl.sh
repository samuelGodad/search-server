#!/bin/bash

# Exit on error
set -e

echo "Setting up SSL certificates..."

# Create certs directory
mkdir -p certs
cd certs

# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 \
    -keyout server.key \
    -out server.crt \
    -days 365 \
    -nodes \
    -subj "/CN=localhost" \
    -addext "subjectAltName = DNS:localhost,IP:127.0.0.1"

# Set proper permissions
chmod 600 server.key
chmod 644 server.crt

echo "SSL certificates generated successfully!"
echo "Files are in: certs/"
echo "- server.key: Private key"
echo "- server.crt: Certificate" 