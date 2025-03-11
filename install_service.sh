#!/bin/bash

echo "==================================="
echo "AI Smart Car - Service Installation"
echo "==================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Get the current directory
CURRENT_DIR=$(pwd)

# Update the service file with the correct path
sed -i "s|/home/pi/ai-smart-car|$CURRENT_DIR|g" smartcar.service

# Copy the service file to systemd directory
cp smartcar.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable the service
systemctl enable smartcar.service

echo
echo "Service installed successfully!"
echo "To start the service now, run:"
echo "sudo systemctl start smartcar.service"
echo
echo "To check the status, run:"
echo "sudo systemctl status smartcar.service"
echo
echo "To view logs, run:"
echo "sudo journalctl -u smartcar.service"
echo

read -p "Do you want to start the service now? (y/n): " START_SERVICE
if [ "$START_SERVICE" = "y" ] || [ "$START_SERVICE" = "Y" ]; then
    systemctl start smartcar.service
    echo "Service started!"
fi 