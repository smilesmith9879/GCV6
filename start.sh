#!/bin/bash

echo "==================================="
echo "AI Smart Car - Starting Application"
echo "==================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed!"
    exit 1
fi

# Check if app.py exists
if [ ! -f app.py ]; then
    echo "Error: app.py not found!"
    exit 1
fi

# Display IP address
echo "Your Raspberry Pi IP address:"
hostname -I
echo

echo "Starting AI Smart Car application..."
echo "Access the web interface at: http://$(hostname -I | awk '{print $1}'):5000"
echo
echo "Press Ctrl+C to stop the application"
echo

# Start the application
python3 app.py 