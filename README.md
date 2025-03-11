# AI Smart Four-Wheel Drive Car

A comprehensive solution for a Raspberry Pi 5 based four-wheel drive car with enhanced gimbal control, real-time mapping, and web-based remote control.

## Features

- Web-based remote control with virtual joysticks for car and camera gimbal
- Real-time video transmission using WebRTC
- Four-motor control for precise car movement
- AI autonomous navigation with ORB-SLAM3
- Real-time map construction and display
- Camera gimbal control with PWM signals (PWM9 for horizontal, PWM10 for vertical)

## Hardware Requirements

- Raspberry Pi 5
- HUANER USB 160° 4K Camera
- Four-Wheel Drive Chassis
- Servo Gimbal (MG996R + PCA9685)
  - Horizontal Control: PWM9, initial angle 80°, range ±45°
  - Vertical Control: PWM10, initial angle 40°, range ±45°
- MPU6050 IMU Sensor

## Software Requirements

- Ubuntu Server 24.04 LTS
- Python 3.10+

## Offline Installation

This project is designed to work completely offline. For detailed offline installation instructions, see [OFFLINE_INSTALL.md](OFFLINE_INSTALL.md).

### Quick Start

1. **On a computer with internet access:**
   ```bash
   # Windows
   download_packages.bat
   
   # Linux/macOS
   ./download_packages.sh
   ```

2. **Transfer files to Raspberry Pi**

3. **On the Raspberry Pi:**
   ```bash
   ./install.sh
   ./start.sh
   ```

## Usage

### 1. Start the Server

```bash
# Navigate to the project directory
cd /path/to/ai-smart-car

# Start the application
./start.sh
```

### 2. Access the Web Interface

- Connect your device (phone, tablet, laptop) to the same network as the Raspberry Pi
- Open a web browser
- Navigate to `http://<raspberry-pi-ip>:5000`
  - Replace `<raspberry-pi-ip>` with the actual IP address of your Raspberry Pi
  - You can find the IP address by running `hostname -I` on the Raspberry Pi

### 3. Using the Interface

- **Left Joystick**: Controls car movement
  - Forward/Backward: Move joystick up/down
  - Left/Right: Move joystick left/right
  - Speed is proportional to joystick displacement
  - Turning speed is automatically reduced to 50%

- **Right Joystick**: Controls camera gimbal
  - Up/Down: Tilt camera up/down
  - Left/Right: Pan camera left/right
  - Initial position: 80° horizontal, 40° vertical
  - Range: ±45° from initial position

- **Reset Gimbal Button**: Returns the camera to its initial position
- **Reset Map Button**: Clears and restarts the SLAM mapping
- **Fullscreen Button**: Toggles fullscreen mode for better visibility

## Running as a Service

To run the application as a service that starts automatically at boot:

```bash
sudo ./install_service.sh
```

## Project Structure

- `app.py`: Main application entry point and Flask server
- `LOBOROBOT.py`: Car movement control library
- `camera.py`: Camera and gimbal control
- `slam.py`: ORB-SLAM3 integration and map generation
- `static/`: Web interface files
  - `css/`: Stylesheet files
  - `js/`: JavaScript files
    - `lib/`: External libraries (socket.io, nipplejs, three.js)
    - `main.js`: Main client-side application logic
- `templates/`: Flask HTML templates
- `download_packages.py`: Script to download packages for offline installation
- `install.py`: Script to install packages offline
- `start.sh`: Script to start the application
- `smartcar.service`: Systemd service file for automatic startup

## Troubleshooting

### Camera Issues
- If the camera is not detected, check the USB connection
- Try a different USB port
- Verify the camera is supported by running `v4l2-ctl --list-devices`

### Motor Control Issues
- Check the I2C connection to the PCA9685
- Verify I2C is enabled on the Raspberry Pi (`sudo raspi-config`)
- Check motor connections to the PCA9685

### Web Interface Issues
- Ensure you're connected to the same network as the Raspberry Pi
- Check if the server is running (`ps aux | grep app.py`)
- Verify the port is not blocked by a firewall

## MPU6050 IMU Integration

The project uses an MPU6050 IMU (Inertial Measurement Unit) sensor for enhanced navigation and orientation sensing. The IMU provides:

- **Accelerometer data**: Measures linear acceleration in 3 axes (X, Y, Z)
- **Gyroscope data**: Measures angular velocity in 3 axes (X, Y, Z)
- **Orientation calculation**: Provides roll, pitch, and yaw angles

### Hardware Connection

Connect the MPU6050 to the Raspberry Pi's I2C pins:
- VCC → 3.3V
- GND → GND
- SCL → GPIO3 (Pin 5)
- SDA → GPIO2 (Pin 3)
- INT → Not required, but can be connected to any available GPIO pin for interrupt-based readings

### Testing the IMU

A test script is provided to verify the MPU6050 is working correctly:

```bash
python3 test_imu.py
```

This script will:
1. Initialize the MPU6050
2. Calibrate the sensor (keep it still during calibration)
3. Display real-time orientation and acceleration data

### IMU Data in the Web Interface

The web interface displays IMU data in real-time:
- Roll and pitch angles in the status bar
- Acceleration values in the IMU data section

The IMU data is also used to enhance the SLAM system by:
- Improving rotation estimation
- Providing more accurate orientation information
- Enhancing map visualization

## License

This project is licensed under the MIT License - see the LICENSE file for details. 