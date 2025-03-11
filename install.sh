#!/bin/bash

echo "==================================="
echo "AI Smart Car - Offline Installation"
echo "==================================="
echo

# Check if offline-packages directory exists
if [ ! -d offline-packages ]; then
    echo "Error: 'offline-packages' directory not found!"
    echo "Please make sure you've transferred the offline packages to this directory."
    echo "You can create the offline packages using the download_packages.py script on a computer with internet access."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Install packages
echo "Installing packages from offline directory..."
python3 -m pip install --no-index --find-links=offline-packages -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "Error installing packages!"
    exit 1
fi

echo
echo "Packages installed successfully!"

# Check hardware
echo
echo "Checking hardware components..."

# Check for camera
if command -v v4l2-ctl &> /dev/null; then
    v4l2-ctl --list-devices &> /dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Camera detected"
    else
        echo "Warning: Could not detect camera"
    fi
else
    echo "Warning: v4l2-ctl not installed, cannot check camera"
fi

# Check for I2C devices
if command -v i2cdetect &> /dev/null; then
    i2cdetect -y 1 &> /dev/null
    if [ $? -eq 0 ]; then
        echo "✓ I2C bus detected"
    else
        echo "Warning: Could not detect I2C devices"
        echo "Make sure I2C is enabled on your Raspberry Pi (sudo raspi-config)"
    fi
else
    echo "Warning: i2cdetect not installed, cannot check I2C devices"
    echo "Make sure I2C is enabled on your Raspberry Pi (sudo raspi-config)"
fi

echo
echo "Installation complete!"
echo
echo "To start the application, run:"
echo "python3 app.py"
echo
echo "Access the web interface at:"
echo "http://<raspberry-pi-ip>:5000"
echo

read -p "Press Enter to continue..." 