import cv2
import numpy as np
import threading
import time
import os
import json
from imu import MPU6050  # Import the MPU6050 class

class SLAM:
    def __init__(self, camera=None, use_imu=True):
        self.camera = camera
        self.running = False
        self.lock = threading.Lock()
        self.map_data = {
            'points': [],
            'trajectory': []
        }
        self.current_position = [0, 0, 0]  # x, y, z
        self.current_orientation = [0, 0, 0]  # roll, pitch, yaw
        
        # Path to save map data
        self.map_file = 'static/data/map_data.json'
        os.makedirs(os.path.dirname(self.map_file), exist_ok=True)
        
        # Initialize ORB feature detector (as a simplified stand-in for ORB-SLAM3)
        self.orb = cv2.ORB_create()
        self.prev_frame = None
        self.prev_kp = None
        self.prev_des = None
        
        # For trajectory tracking
        self.trajectory = []
        
        # Initialize IMU if available
        self.use_imu = use_imu
        self.imu = None
        if self.use_imu:
            try:
                self.imu = MPU6050()
                print("IMU initialized successfully")
            except Exception as e:
                print(f"Failed to initialize IMU: {e}")
                self.use_imu = False
    
    def start(self):
        """Start the SLAM processing thread"""
        if self.running:
            return
        
        if self.camera is None:
            raise ValueError("Camera must be set before starting SLAM")
        
        # Start IMU if available
        if self.use_imu and self.imu:
            try:
                print("Calibrating IMU...")
                self.imu.calibrate()
                self.imu.start()
                print("IMU started successfully")
            except Exception as e:
                print(f"Failed to start IMU: {e}")
                self.use_imu = False
        
        self.running = True
        self.thread = threading.Thread(target=self._process_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the SLAM processing thread"""
        self.running = False
        if self.thread:
            self.thread.join()
        
        # Stop IMU if it was started
        if self.use_imu and self.imu:
            self.imu.stop()
        
        # Save the final map data
        self._save_map_data()
    
    def _process_loop(self):
        """SLAM processing loop running in a separate thread"""
        while self.running:
            # Get the current frame from the camera
            with self.camera.lock:
                if self.camera.frame is None:
                    time.sleep(0.01)
                    continue
                
                frame = self.camera.frame.copy()
            
            # Process the frame with ORB-SLAM (simplified version)
            self._process_frame(frame)
            
            # Update orientation from IMU if available
            if self.use_imu and self.imu:
                roll, pitch, yaw = self.imu.get_orientation()
                with self.lock:
                    self.current_orientation = [roll, pitch, yaw]
            
            # Sleep to reduce CPU usage
            time.sleep(0.05)
    
    def _process_frame(self, frame):
        """Process a frame with ORB features (simplified SLAM)"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect ORB features
        kp, des = self.orb.detectAndCompute(gray, None)
        
        if self.prev_frame is not None and self.prev_kp is not None and self.prev_des is not None:
            # Match features
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(self.prev_des, des)
            
            # Sort matches by distance
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Use top matches to estimate motion
            if len(matches) > 10:
                # Extract matched keypoints
                prev_pts = np.float32([self.prev_kp[m.queryIdx].pt for m in matches[:10]])
                curr_pts = np.float32([kp[m.trainIdx].pt for m in matches[:10]])
                
                # Estimate rigid transformation
                if len(prev_pts) >= 4 and len(curr_pts) >= 4:
                    # This is a simplified motion estimation
                    # In a real ORB-SLAM3 implementation, this would be much more sophisticated
                    M, _ = cv2.estimateAffinePartial2D(prev_pts, curr_pts)
                    
                    if M is not None:
                        # Extract translation
                        dx = M[0, 2]
                        dy = M[1, 2]
                        
                        # Extract rotation (simplified)
                        da = np.arctan2(M[1, 0], M[0, 0])
                        
                        # Get IMU data if available
                        imu_orientation = None
                        if self.use_imu and self.imu:
                            imu_orientation = self.imu.get_orientation()
                        
                        # Update position (simplified)
                        with self.lock:
                            # If IMU is available, use it to improve motion estimation
                            if imu_orientation:
                                roll, pitch, yaw = imu_orientation
                                
                                # Use IMU yaw to improve rotation estimation
                                # This is a simplified fusion - a real implementation would use a Kalman filter
                                da = 0.7 * da + 0.3 * (np.radians(yaw) - np.radians(self.current_orientation[2]))
                                
                                # Update orientation
                                self.current_orientation = [roll, pitch, np.degrees(np.radians(self.current_orientation[2]) + da)]
                            else:
                                # Without IMU, just use visual estimation
                                self.current_orientation[2] += np.degrees(da)
                            
                            # Calculate movement in world coordinates based on current orientation
                            angle_rad = np.radians(self.current_orientation[2])
                            dx_world = dx * np.cos(angle_rad) - dy * np.sin(angle_rad)
                            dy_world = dx * np.sin(angle_rad) + dy * np.cos(angle_rad)
                            
                            # Scale factor (adjust based on your environment)
                            scale = 0.01
                            
                            self.current_position[0] += dx_world * scale
                            self.current_position[1] += dy_world * scale
                            
                            # Add to trajectory
                            self.trajectory.append(self.current_position.copy())
                            
                            # Update map data
                            self.map_data['trajectory'] = self.trajectory
                            
                            # Add some random 3D points (in a real system, these would be actual 3D points)
                            if len(self.map_data['points']) < 1000 and np.random.random() < 0.1:
                                for _ in range(5):
                                    point = [
                                        self.current_position[0] + np.random.normal(0, 0.5),
                                        self.current_position[1] + np.random.normal(0, 0.5),
                                        np.random.normal(0, 0.2)
                                    ]
                                    self.map_data['points'].append(point)
        
        # Save current frame and keypoints for next iteration
        self.prev_frame = gray
        self.prev_kp = kp
        self.prev_des = des
        
        # Periodically save map data
        if np.random.random() < 0.05:  # Save roughly every 20 frames
            self._save_map_data()
    
    def _save_map_data(self):
        """Save the current map data to a JSON file"""
        with self.lock:
            # Convert numpy arrays to lists for JSON serialization
            data = {
                'points': [[float(x), float(y), float(z)] for x, y, z in self.map_data['points']],
                'trajectory': [[float(x), float(y), float(z)] for x, y, z in self.map_data['trajectory']]
            }
            
            with open(self.map_file, 'w') as f:
                json.dump(data, f)
    
    def get_position(self):
        """Get the current position and orientation"""
        with self.lock:
            return {
                'position': self.current_position.copy(),
                'orientation': self.current_orientation.copy()
            }
    
    def get_map_data(self):
        """Get the current map data"""
        with self.lock:
            return self.map_data.copy()
    
    def reset(self):
        """Reset the SLAM system"""
        with self.lock:
            self.map_data = {
                'points': [],
                'trajectory': []
            }
            self.current_position = [0, 0, 0]
            self.current_orientation = [0, 0, 0]
            self.trajectory = []
            self.prev_frame = None
            self.prev_kp = None
            self.prev_des = None
            
            # Reset IMU yaw if available
            if self.use_imu and self.imu:
                # We can't reset the IMU's internal values directly,
                # but we can note the current values and apply an offset
                _, _, yaw = self.imu.get_orientation()
                self.imu_yaw_offset = yaw  # Store the current yaw as an offset 