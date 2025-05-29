#!/bin/bash

# Exit on error
set -e

echo "Setting up SSL certificates..."

# Create certs directory if it doesn't exist
mkdir -p certs
cd certs

# Generate CA private key and certificate
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=Search Server CA"

# Generate server private key and CSR
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=localhost"

# Sign server certificate with CA
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt

# Generate client private key and CSR
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=search_client"

# Sign client certificate with CA
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt

# Clean up CSR files
rm *.csr

# Set proper permissions
chmod 600 *.key
chmod 644 *.crt

echo "SSL certificates generated successfully in the 'certs' directory"
echo "Files are in: certs/"
echo "- ca.key: CA private key"
echo "- ca.crt: CA certificate"
echo "- server.key: Server private key"
echo "- server.crt: Server certificate"
echo "- client.key: Client private key"
echo "- client.crt: Client certificate" 