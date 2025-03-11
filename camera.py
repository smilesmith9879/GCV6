import cv2
import threading
import time
from LOBOROBOT import LOBOROBOT

class Camera:
    def __init__(self, camera_id=0, width=640, height=480,robot=None):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.camera = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        
        # Initialize the robot for gimbal control
        #self.robot = LOBOROBOT()
        # 使用传入的 robot 实例，若未提供则创建新实例
        self.robot = robot if robot is not None else LOBOROBOT()
        
        # Gimbal settings as per project description
        self.horizontal_channel = 9  # PWM9 for horizontal control
        self.vertical_channel = 10   # PWM10 for vertical control
        
        # Initial angles and ranges
        self.horizontal_angle = 80  # Initial angle 80°
        self.vertical_angle = 40    # Initial angle 40°
        self.angle_range = 45       # Range ±45°
        
        # Set initial gimbal position
        self.set_gimbal_position(self.horizontal_angle, self.vertical_angle)
    
    def start(self):
        """Start the camera capture thread"""
        if self.running:
            return
        
        self.camera = cv2.VideoCapture(self.camera_id)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        if not self.camera.isOpened():
            raise RuntimeError("Could not open camera")
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the camera capture thread"""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.camera:
            self.camera.release()
    
    def _capture_loop(self):
        """Camera capture loop running in a separate thread"""
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                continue
            
            with self.lock:
                self.frame = frame
    
    def get_frame(self):
        """Get the current frame as JPEG bytes"""
        with self.lock:
            if self.frame is None:
                return None
            
            # Encode frame as JPEG
            ret, jpeg = cv2.imencode('.jpg', self.frame)
            if not ret:
                return None
            
            return jpeg.tobytes()
    
    def set_gimbal_position(self, horizontal_angle, vertical_angle):
        """Set the gimbal position with angle constraints"""
        # Constrain angles within the allowed range
        h_angle = max(self.horizontal_angle - self.angle_range, 
                      min(self.horizontal_angle + self.angle_range, horizontal_angle))
        v_angle = max(self.vertical_angle - self.angle_range, 
                      min(self.vertical_angle + self.angle_range, vertical_angle))
        
        # Update current angles
        self.horizontal_angle = h_angle
        self.vertical_angle = v_angle
        
        # Set servo angles
        self.robot.set_servo_angle(self.horizontal_channel, h_angle)
        self.robot.set_servo_angle(self.vertical_channel, v_angle)
    
    def move_gimbal(self, horizontal_delta, vertical_delta):
        """Move the gimbal by the specified delta angles"""
        new_h_angle = self.horizontal_angle + horizontal_delta
        new_v_angle = self.vertical_angle + vertical_delta
        self.set_gimbal_position(new_h_angle, new_v_angle)
    
    def reset_gimbal(self):
        """Reset the gimbal to its initial position"""
        self.set_gimbal_position(80, 40)  # Initial angles as per project description 