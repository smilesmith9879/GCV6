import os
import time
import json
import threading
from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import numpy as np

from LOBOROBOT import LOBOROBOT
from camera import Camera
from slam import SLAM

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smartcar2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize hardware components
robot = LOBOROBOT()
camera = Camera(camera_id=0, width=640, height=480)
slam = SLAM(camera=camera)

# Global variables for control
control_lock = threading.Lock()
current_speed = 0
current_direction = 'stop'
current_gimbal_h = 80  # Initial horizontal angle
current_gimbal_v = 40  # Initial vertical angle

# Ensure data directory exists
os.makedirs('static/data', exist_ok=True)

# Start camera and SLAM
camera.start()
slam.start()

@app.route('/')
def index():
    """Render the main control page"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    def generate():
        while True:
            frame = camera.get_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.1)
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/map_data')
def map_data():
    """Return the current map data as JSON"""
    return jsonify(slam.get_map_data())

@app.route('/position')
def position():
    """Return the current position and orientation as JSON"""
    return jsonify(slam.get_position())

@app.route('/reset_slam', methods=['POST'])
def reset_slam():
    """Reset the SLAM system"""
    slam.reset()
    return jsonify({'status': 'success'})

@app.route('/reset_gimbal', methods=['POST'])
def reset_gimbal():
    """Reset the camera gimbal to its initial position"""
    global current_gimbal_h, current_gimbal_v
    camera.reset_gimbal()
    current_gimbal_h = 80
    current_gimbal_v = 40
    return jsonify({'status': 'success'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')
    # Stop the car when client disconnects
    with control_lock:
        robot.t_stop(0)

@socketio.on('car_control')
def handle_car_control(data):
    """Handle car movement control from joystick"""
    global current_speed, current_direction
    
    # Extract joystick data
    x = data.get('x', 0)  # -1 (left) to 1 (right)
    y = data.get('y', 0)  # -1 (down) to 1 (up)
    
    # Calculate speed (0-100)
    speed = int(min(100, max(0, abs(y) * 100)))
    
    # Determine direction and movement
    with control_lock:
        current_speed = speed
        
        # Stop if joystick is centered (with small deadzone)
        if abs(x) < 0.1 and abs(y) < 0.1:
            robot.t_stop(0)
            current_direction = 'stop'
        
        # Forward/backward movement
        elif abs(y) > abs(x):
            if y > 0:  # Forward
                robot.t_up(speed, 0)
                current_direction = 'forward'
            else:  # Backward
                robot.t_down(speed, 0)
                current_direction = 'backward'
        
        # Left/right movement
        else:
            # Reduce speed for turning as per project requirements
            turn_speed = int(speed * 0.5)
            
            if x > 0:  # Right
                robot.turnRight(turn_speed, 0)
                current_direction = 'right'
            else:  # Left
                robot.turnLeft(turn_speed, 0)
                current_direction = 'left'
    
    # Send status update to clients
    emit('status_update', {
        'speed': current_speed,
        'direction': current_direction
    }, broadcast=True)

@socketio.on('gimbal_control')
def handle_gimbal_control(data):
    """Handle camera gimbal control from joystick"""
    global current_gimbal_h, current_gimbal_v
    
    # Extract joystick data
    x = data.get('x', 0)  # -1 (left) to 1 (right)
    y = data.get('y', 0)  # -1 (down) to 1 (up)
    
    # Calculate angle changes (scale factor determines sensitivity)
    h_delta = x * 2  # Scale factor for horizontal movement
    v_delta = -y * 2  # Scale factor for vertical movement (inverted)
    
    # Update gimbal position
    with control_lock:
        current_gimbal_h += h_delta
        current_gimbal_v += v_delta
        camera.set_gimbal_position(current_gimbal_h, current_gimbal_v)
    
    # Send status update to clients
    emit('gimbal_update', {
        'horizontal': current_gimbal_h,
        'vertical': current_gimbal_v
    }, broadcast=True)

if __name__ == '__main__':
    try:
        # Use eventlet for better performance with WebSocket
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    finally:
        # Clean up resources
        camera.stop()
        slam.stop()
        robot.t_stop(0) 