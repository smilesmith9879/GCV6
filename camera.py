import cv2
import threading
import time
from LOBOROBOT import LOBOROBOT

class Camera:
    def __init__(self, camera_id=0, width=640, height=480, robot=None, jpeg_quality=70):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.camera = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        # JPEG压缩质量（0-100），降低可提高传输速度
        self.jpeg_quality = jpeg_quality
        # 帧率控制
        self.last_frame_time = 0
        self.frame_interval = 1/15  # 目标15fps
        
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
        # 设置更低的帧率以减少CPU使用
        self.camera.set(cv2.CAP_PROP_FPS, 15)
        
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
                time.sleep(0.1)
                continue
            
            # 通过调整大小来减少处理负担
            if self.width > 320:  # 如果原设置分辨率较高，则降低
                frame = cv2.resize(frame, (320, 240))
            
            with self.lock:
                self.frame = frame
            
            # 控制帧率，避免CPU过高负载
            processing_time = time.time() - self.last_frame_time
            if processing_time < self.frame_interval:
                time.sleep(self.frame_interval - processing_time)
            self.last_frame_time = time.time()
    
    def get_frame(self):
        """Get the current frame as JPEG bytes"""
        with self.lock:
            if self.frame is None:
                return None
            
            # 设置JPEG编码参数，降低质量以提高传输速度
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            
            # Encode frame as JPEG with lower quality
            ret, jpeg = cv2.imencode('.jpg', self.frame, encode_params)
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