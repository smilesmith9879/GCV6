#!/bin/bash

echo "==================================="
echo "AI Smart Car - Package Downloader"
echo "==================================="
echo

echo "This script will download all required packages for offline installation."
echo

# Create directory for packages
mkdir -p offline-packages
echo "Downloading packages to: $(pwd)/offline-packages"
echo

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Download packages
python3 -m pip download -d offline-packages -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "Error downloading packages!"
    exit 1
fi

echo
echo "Packages downloaded successfully!"
echo
echo "Transfer the 'offline-packages' directory along with the project files to your Raspberry Pi."
echo
echo "To install on the Raspberry Pi, run:"
echo "python3 install.py"
echo

read -p "Press Enter to continue..." 