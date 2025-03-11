#!/usr/bin/env python3
"""
Offline Installation Script for AI Smart Car

This script helps with the offline installation process on the Raspberry Pi.
It checks for the presence of the offline packages and installs them.
"""

import os
import subprocess
import sys

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 10):
        print("Warning: This project is designed for Python 3.10 or newer.")
        print(f"Current Python version: {sys.version}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

def check_offline_packages():
    """Check if offline packages directory exists"""
    packages_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'offline-packages')
    if not os.path.exists(packages_dir):
        print("Error: 'offline-packages' directory not found!")
        print("Please make sure you've transferred the offline packages to this directory.")
        print("You can create the offline packages using the download_packages.py script on a computer with internet access.")
        sys.exit(1)
    return packages_dir

def install_packages(packages_dir):
    """Install packages from the offline directory"""
    requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        print("Error: requirements.txt not found!")
        sys.exit(1)
    
    print("Installing packages from offline directory...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            '--no-index',
            '--find-links', packages_dir,
            '-r', requirements_file
        ], check=True)
        print("\nPackages installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def check_hardware():
    """Check for required hardware components"""
    try:
        # Check for camera
        subprocess.run(['v4l2-ctl', '--list-devices'], check=True, capture_output=True)
        print("✓ Camera detected")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Could not detect camera or v4l2-ctl not installed")
    
    try:
        # Check for I2C devices (PCA9685)
        subprocess.run(['i2cdetect', '-y', '1'], check=True, capture_output=True)
        print("✓ I2C bus detected")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Could not detect I2C devices or i2cdetect not installed")
        print("Make sure I2C is enabled on your Raspberry Pi (sudo raspi-config)")

def main():
    print("=" * 60)
    print("AI Smart Car - Offline Installation")
    print("=" * 60)
    
    # Check Python version
    check_python_version()
    
    # Check for offline packages
    packages_dir = check_offline_packages()
    
    # Install packages
    install_packages(packages_dir)
    
    # Check hardware
    print("\nChecking hardware components...")
    check_hardware()
    
    print("\nInstallation complete!")
    print("\nTo start the application, run:")
    print("python app.py")
    print("\nAccess the web interface at:")
    print("http://<raspberry-pi-ip>:5000")

if __name__ == "__main__":
    main() 