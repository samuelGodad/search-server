#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Create system user and group
echo "Creating system user and group..."
useradd -r -s /bin/false search-server || true

# Create installation directory
echo "Creating installation directory..."
mkdir -p /opt/search-server
cp -r . /opt/search-server/
chown -R search-server:search-server /opt/search-server

# Create virtual environment
echo "Setting up Python virtual environment..."
cd /opt/search-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install systemd service
echo "Installing systemd service..."
cp search-server.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable search-server

# Create SSL certificates if needed
if [ ! -d "certs" ]; then
    echo "Creating SSL certificates..."
    mkdir -p certs
    cd certs
    openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes -subj "/CN=localhost"
    chown -R search-server:search-server .
fi

# Set up logging
echo "Setting up logging..."
mkdir -p /var/log/search-server
chown search-server:search-server /var/log/search-server

echo "Installation complete!"
echo "To start the service: sudo systemctl start search-server"
echo "To check status: sudo systemctl status search-server"
echo "To view logs: sudo journalctl -u search-server" 