# Offline Installation Guide

This guide provides step-by-step instructions for installing the AI Smart Car project in an offline environment.

## Prerequisites

Before going offline, you need to download all required packages on a computer with internet access.

## Step 1: Download Required Packages (On a Computer with Internet)

### Windows

1. Open a Command Prompt
2. Navigate to the project directory
3. Run the download script:
   ```
   download_packages.bat
   ```

### Linux/macOS

1. Open a Terminal
2. Navigate to the project directory
3. Make the script executable and run it:
   ```
   chmod +x download_packages.sh
   ./download_packages.sh
   ```

### Python Script (Alternative)

If the batch/shell scripts don't work, you can use the Python script:
```
python download_packages.py
```

This will create an `offline-packages` directory containing all required Python packages.

## Step 2: Transfer Files to Raspberry Pi

Transfer the following to your Raspberry Pi:
- All project files
- The `offline-packages` directory

You can use:
- USB drive
- Direct network transfer (scp, rsync)
- SD card transfer

## Step 3: Install on Raspberry Pi

1. Connect to your Raspberry Pi
2. Navigate to the project directory
3. Run the installation script:

   ```
   chmod +x install.sh
   ./install.sh
   ```

   Or use the Python script:
   ```
   python3 install.py
   ```

4. The script will:
   - Install all required packages from the offline directory
   - Check for required hardware components
   - Provide instructions for starting the application

## Step 4: Start the Application

After installation, start the application:

```
python3 app.py
```

## Step 5: Access the Web Interface

1. Connect your device (phone, tablet, laptop) to the same network as the Raspberry Pi
2. Open a web browser
3. Navigate to `http://<raspberry-pi-ip>:5000`
   - Replace `<raspberry-pi-ip>` with the actual IP address of your Raspberry Pi
   - You can find the IP address by running `hostname -I` on the Raspberry Pi

## Troubleshooting

### Package Installation Issues

If you encounter issues with package installation:
- Make sure all packages were downloaded correctly
- Check if the Raspberry Pi architecture matches the downloaded packages
- Try installing packages individually to identify problematic ones

### Hardware Issues

- Camera not detected: Check USB connection and try different ports
- I2C devices not detected: Enable I2C in `sudo raspi-config`
- Motor control issues: Check wiring and power supply

### Web Interface Issues

- Cannot access web interface: Check network connection and firewall settings
- Video feed not showing: Check camera connection and permissions 