import smbus2 as smbus
import math
import time
import threading
import numpy as np

class MPU6050:
    # MPU6050 Registers and their addresses
    PWR_MGMT_1 = 0x6B
    SMPLRT_DIV = 0x19
    CONFIG = 0x1A
    GYRO_CONFIG = 0x1B
    ACCEL_CONFIG = 0x1C
    INT_ENABLE = 0x38
    ACCEL_XOUT_H = 0x3B
    ACCEL_YOUT_H = 0x3D
    ACCEL_ZOUT_H = 0x3F
    GYRO_XOUT_H = 0x43
    GYRO_YOUT_H = 0x45
    GYRO_ZOUT_H = 0x47
    
    def __init__(self, bus=1, address=0x68):
        self.bus = smbus.SMBus(bus)
        self.address = address
        self.running = False
        self.lock = threading.Lock()
        
        # Sensor data
        self.accel_x = 0
        self.accel_y = 0
        self.accel_z = 0
        self.gyro_x = 0
        self.gyro_y = 0
        self.gyro_z = 0
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        
        # Calibration values
        self.accel_x_offset = 0
        self.accel_y_offset = 0
        self.accel_z_offset = 0
        self.gyro_x_offset = 0
        self.gyro_y_offset = 0
        self.gyro_z_offset = 0
        
        # Initialize the device
        self._initialize()
    
    def _initialize(self):
        """Initialize the MPU6050"""
        # Wake up the MPU6050
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1, 0)
        
        # Configure sample rate
        self.bus.write_byte_data(self.address, self.SMPLRT_DIV, 7)
        
        # Configure the digital low pass filter
        self.bus.write_byte_data(self.address, self.CONFIG, 0)
        
        # Configure gyroscope range (±250°/s)
        self.bus.write_byte_data(self.address, self.GYRO_CONFIG, 0)
        
        # Configure accelerometer range (±2g)
        self.bus.write_byte_data(self.address, self.ACCEL_CONFIG, 0)
        
        # Enable data ready interrupt
        self.bus.write_byte_data(self.address, self.INT_ENABLE, 1)
        
        print("MPU6050 initialized")
    
    def _read_raw_data(self, addr):
        """Read raw 16-bit value from the MPU6050"""
        high = self.bus.read_byte_data(self.address, addr)
        low = self.bus.read_byte_data(self.address, addr + 1)
        
        # Combine high and low for 16-bit value
        value = (high << 8) | low
        
        # Convert to signed value
        if value > 32767:
            value -= 65536
            
        return value
    
    def read_accelerometer(self):
        """Read accelerometer data"""
        with self.lock:
            x = self._read_raw_data(self.ACCEL_XOUT_H)
            y = self._read_raw_data(self.ACCEL_YOUT_H)
            z = self._read_raw_data(self.ACCEL_ZOUT_H)
            
            # Apply calibration offsets
            x -= self.accel_x_offset
            y -= self.accel_y_offset
            z -= self.accel_z_offset
            
            # Convert to g (±2g range)
            x = x / 16384.0
            y = y / 16384.0
            z = z / 16384.0
            
            return (x, y, z)
    
    def read_gyroscope(self):
        """Read gyroscope data"""
        with self.lock:
            x = self._read_raw_data(self.GYRO_XOUT_H)
            y = self._read_raw_data(self.GYRO_YOUT_H)
            z = self._read_raw_data(self.GYRO_ZOUT_H)
            
            # Apply calibration offsets
            x -= self.gyro_x_offset
            y -= self.gyro_y_offset
            z -= self.gyro_z_offset
            
            # Convert to degrees per second (±250°/s range)
            x = x / 131.0
            y = y / 131.0
            z = z / 131.0
            
            return (x, y, z)
    
    def calculate_orientation(self, accel_data, gyro_data, dt):
        """Calculate orientation using complementary filter"""
        # Extract accelerometer data
        accel_x, accel_y, accel_z = accel_data
        
        # Calculate roll and pitch from accelerometer (in degrees)
        accel_roll = math.atan2(accel_y, accel_z) * 180.0 / math.pi
        accel_pitch = math.atan2(-accel_x, math.sqrt(accel_y * accel_y + accel_z * accel_z)) * 180.0 / math.pi
        
        # Extract gyroscope data
        gyro_x, gyro_y, gyro_z = gyro_data
        
        # Complementary filter
        # Combine accelerometer and gyroscope data
        # The filter uses 98% of the gyroscope data and 2% of the accelerometer data
        with self.lock:
            self.roll = 0.98 * (self.roll + gyro_x * dt) + 0.02 * accel_roll
            self.pitch = 0.98 * (self.pitch + gyro_y * dt) + 0.02 * accel_pitch
            self.yaw += gyro_z * dt  # Yaw is calculated only from gyroscope
            
            # Normalize yaw to 0-360 degrees
            self.yaw = self.yaw % 360
            
            return (self.roll, self.pitch, self.yaw)
    
    def calibrate(self, samples=100):
        """Calibrate the sensor by calculating offsets"""
        print("Calibrating MPU6050... Keep the sensor still!")
        
        accel_x_sum = 0
        accel_y_sum = 0
        accel_z_sum = 0
        gyro_x_sum = 0
        gyro_y_sum = 0
        gyro_z_sum = 0
        
        # Collect samples
        for _ in range(samples):
            x = self._read_raw_data(self.ACCEL_XOUT_H)
            y = self._read_raw_data(self.ACCEL_YOUT_H)
            z = self._read_raw_data(self.ACCEL_ZOUT_H)
            
            accel_x_sum += x
            accel_y_sum += y
            accel_z_sum += z
            
            x = self._read_raw_data(self.GYRO_XOUT_H)
            y = self._read_raw_data(self.GYRO_YOUT_H)
            z = self._read_raw_data(self.GYRO_ZOUT_H)
            
            gyro_x_sum += x
            gyro_y_sum += y
            gyro_z_sum += z
            
            time.sleep(0.01)
        
        # Calculate average offsets
        self.accel_x_offset = accel_x_sum / samples
        self.accel_y_offset = accel_y_sum / samples
        self.accel_z_offset = accel_z_sum / samples - 16384  # Remove 1g from z-axis
        self.gyro_x_offset = gyro_x_sum / samples
        self.gyro_y_offset = gyro_y_sum / samples
        self.gyro_z_offset = gyro_z_sum / samples
        
        print("Calibration complete!")
        print(f"Accelerometer offsets: X={self.accel_x_offset}, Y={self.accel_y_offset}, Z={self.accel_z_offset}")
        print(f"Gyroscope offsets: X={self.gyro_x_offset}, Y={self.gyro_y_offset}, Z={self.gyro_z_offset}")
    
    def start(self):
        """Start the IMU processing thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the IMU processing thread"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _process_loop(self):
        """IMU processing loop running in a separate thread"""
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Read sensor data
            accel_data = self.read_accelerometer()
            gyro_data = self.read_gyroscope()
            
            # Update orientation
            self.calculate_orientation(accel_data, gyro_data, dt)
            
            # Store current values
            with self.lock:
                self.accel_x, self.accel_y, self.accel_z = accel_data
                self.gyro_x, self.gyro_y, self.gyro_z = gyro_data
            
            # Sleep to reduce CPU usage
            time.sleep(0.01)
    
    def get_orientation(self):
        """Get the current orientation (roll, pitch, yaw)"""
        with self.lock:
            return (self.roll, self.pitch, self.yaw)
    
    def get_acceleration(self):
        """Get the current acceleration (x, y, z)"""
        with self.lock:
            return (self.accel_x, self.accel_y, self.accel_z)
    
    def get_angular_velocity(self):
        """Get the current angular velocity (x, y, z)"""
        with self.lock:
            return (self.gyro_x, self.gyro_y, self.gyro_z)


# Example usage
if __name__ == "__main__":
    try:
        imu = MPU6050()
        imu.calibrate()
        imu.start()
        
        print("Reading data from MPU6050. Press Ctrl+C to stop.")
        
        while True:
            roll, pitch, yaw = imu.get_orientation()
            accel_x, accel_y, accel_z = imu.get_acceleration()
            
            print(f"Orientation: Roll={roll:.2f}°, Pitch={pitch:.2f}°, Yaw={yaw:.2f}°")
            print(f"Acceleration: X={accel_x:.2f}g, Y={accel_y:.2f}g, Z={accel_z:.2f}g")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        if 'imu' in locals():
            imu.stop() 