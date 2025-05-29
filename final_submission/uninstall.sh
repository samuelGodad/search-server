#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Stop and disable service
echo "Stopping and disabling service..."
systemctl stop search-server || true
systemctl disable search-server || true

# Remove systemd service file
echo "Removing systemd service..."
rm -f /etc/systemd/system/search-server.service
systemctl daemon-reload

# Remove installation directory
echo "Removing installation directory..."
rm -rf /opt/search-server

# Remove system user and group
echo "Removing system user and group..."
userdel search-server || true
groupdel search-server || true

# Remove log directory
echo "Removing log directory..."
rm -rf /var/log/search-server

echo "Uninstallation complete!" 