#!/usr/bin/env python3
"""
Package Downloader for Offline Installation

This script downloads all required packages for offline installation.
Run this script on a computer with internet access before transferring
the project to the Raspberry Pi.
"""

import os
import subprocess
import sys

def main():
    # Create directory for packages
    packages_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'offline-packages')
    os.makedirs(packages_dir, exist_ok=True)
    
    print(f"Downloading packages to: {packages_dir}")
    
    # Get requirements file path
    requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        print("Error: requirements.txt not found!")
        sys.exit(1)
    
    # Download packages
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'download',
            '-d', packages_dir,
            '-r', requirements_file
        ], check=True)
        print("\nPackages downloaded successfully!")
        print(f"Transfer the 'offline-packages' directory along with the project files to your Raspberry Pi.")
        print("\nTo install on the Raspberry Pi, run:")
        print(f"pip install --no-index --find-links=/path/to/offline-packages -r requirements.txt")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading packages: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 