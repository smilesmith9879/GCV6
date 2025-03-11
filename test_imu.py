#!/usr/bin/env python3
"""
MPU6050 Test Script

This script tests the MPU6050 IMU sensor to verify it's working correctly.
Run this script on the Raspberry Pi to check if the sensor is properly connected.
"""

import time
from imu import MPU6050

def main():
    print("MPU6050 Test Script")
    print("===================")
    print("This script tests the MPU6050 IMU sensor.")
    print("Make sure the sensor is connected to the I2C pins of your Raspberry Pi.")
    print()
    
    try:
        # Initialize the MPU6050
        print("Initializing MPU6050...")
        imu = MPU6050()
        print("MPU6050 initialized successfully!")
        
        # Calibrate the sensor
        print("\nCalibrating sensor...")
        print("Keep the sensor still during calibration.")
        imu.calibrate()
        
        # Start the IMU processing thread
        imu.start()
        
        print("\nReading data from MPU6050. Press Ctrl+C to stop.")
        print("------------------------------------------------")
        
        # Read and display data for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            # Get orientation data
            roll, pitch, yaw = imu.get_orientation()
            
            # Get acceleration data
            accel_x, accel_y, accel_z = imu.get_acceleration()
            
            # Get angular velocity data
            gyro_x, gyro_y, gyro_z = imu.get_angular_velocity()
            
            # Print the data
            print(f"\rOrientation: Roll={roll:6.2f}°, Pitch={pitch:6.2f}°, Yaw={yaw:6.2f}° | "
                  f"Accel: X={accel_x:5.2f}g, Y={accel_y:5.2f}g, Z={accel_z:5.2f}g | "
                  f"Gyro: X={gyro_x:6.2f}°/s, Y={gyro_y:6.2f}°/s, Z={gyro_z:6.2f}°/s", end="")
            
            # Sleep to reduce output rate
            time.sleep(0.1)
        
        print("\n\nTest completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure the MPU6050 is properly connected to the I2C pins:")
        print("   - VCC → 3.3V")
        print("   - GND → GND")
        print("   - SCL → GPIO3 (Pin 5)")
        print("   - SDA → GPIO2 (Pin 3)")
        print("2. Check if I2C is enabled on your Raspberry Pi:")
        print("   - Run 'sudo raspi-config' and enable I2C under Interface Options")
        print("3. Check if the I2C device is detected:")
        print("   - Run 'sudo i2cdetect -y 1'")
        print("   - You should see a device at address 0x68 (the MPU6050)")
    finally:
        # Clean up
        if 'imu' in locals():
            imu.stop()

if __name__ == "__main__":
    main() 