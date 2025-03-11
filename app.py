import eventlet
# 初始化eventlet，解决并发问题
eventlet.monkey_patch()
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
from imu import MPU6050  # Import the MPU6050 class
from battery import BatteryMonitor  # Import the BatteryMonitor class



# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smartcar2025'
# 改进SocketIO配置，增加心跳包和超时处理
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', 
                   ping_timeout=10, ping_interval=5,
                   max_http_buffer_size=5*1024*1024)  # 增加缓冲区大小

# Initialize hardware components
robot = LOBOROBOT()
# 降低分辨率到320x240，提高传输性能
camera = Camera(camera_id=0, width=320, height=240, robot=robot, jpeg_quality=60)
slam = SLAM(camera=camera, use_imu=True)  # Enable IMU integration with SLAM
# 初始化电池监测模块
battery_monitor = BatteryMonitor(robot=robot, update_interval=10)

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
        last_frame_time = 0
        frame_interval = 1/10  # 限制最大10fps的输出，减轻网络负担
        
        while True:
            # 控制帧率
            current_time = time.time()
            if current_time - last_frame_time < frame_interval:
                time.sleep(0.01)  # 短暂休眠以减少CPU使用
                continue
                
            frame = camera.get_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                last_frame_time = time.time()
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

@app.route('/imu_data')
def imu_data():
    """Return the current IMU data as JSON"""
    if slam.imu_available:
        try:
            orientation = slam.imu.get_orientation()
            acceleration = slam.imu.get_acceleration()
            angular_velocity = slam.imu.get_angular_velocity()
            
            return jsonify({
                'available': True,
                'orientation': {
                    'roll': orientation[0],
                    'pitch': orientation[1],
                    'yaw': orientation[2]
                },
                'acceleration': {
                    'x': acceleration[0],
                    'y': acceleration[1],
                    'z': acceleration[2]
                },
                'angular_velocity': {
                    'x': angular_velocity[0],
                    'y': angular_velocity[1],
                    'z': angular_velocity[2]
                }
            })
        except Exception as e:
            print(f"Error getting IMU data: {e}")
            slam.imu_available = False
            return jsonify({'available': False, 'error': 'IMU disconnected during operation'})
    else:
        return jsonify({'available': False, 'error': 'IMU not available'})

@app.route('/imu_status')
def imu_status():
    """Return IMU status"""
    return jsonify({
        'available': slam.imu_available
    })

@app.route('/battery_status')
def battery_status():
    """返回电池状态信息的API端点"""
    status = battery_monitor.get_battery_status()
    return jsonify(status)

@app.route('/reset_slam', methods=['POST'])
def reset_slam():
    """Reset SLAM system"""
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

# 保持连接的心跳检测
@socketio.on('ping')
def handle_ping():
    """Handle ping from client to keep connection alive"""
    emit('pong', {'timestamp': time.time()})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('status', {
        'status': 'connected',
        'imu_available': slam.imu_available
    })
    # 发送连接成功消息并设置心跳机制
    emit('connection_established', {'timestamp': time.time()})

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
    
    # 检查是否是回中信号 (0,0)
    if abs(x) < 0.01 and abs(y) < 0.01:
        # 回中信号直接让车停止，不需要反转方向
        robot.t_stop(0)
        current_direction = 'stop'
        current_speed = 0
        
        # 发送状态更新给客户端
        emit('status_update', {
            'speed': current_speed,
            'direction': current_direction
        }, broadcast=True)
        return
    
    # 不是回中信号，则反转控制方向
    x = -x
    y = -y
    
    # Calculate speed (0-30) - 调整速度上限为30
    speed = int(min(30, max(0, abs(y) * 30)))
    
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
    
    # 检查是否是回中信号 (0,0)
    if abs(x) < 0.01 and abs(y) < 0.01:
        # 回中信号意味着停止云台移动，不需要反转方向
        # 不更新云台位置，只发送当前状态
        current_gimbal_h=80
        current_gimbal_v=40
        emit('gimbal_update', {
            'horizontal': current_gimbal_h,
            'vertical': current_gimbal_v
        }, broadcast=True)
        return
    
    # 不是回中信号，则反转云台控制方向
    x = -x
    y = -y
    
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

# Periodically send IMU data to clients
def send_imu_data():
    """Send IMU data periodically"""
    print("IMU data thread started")
    while True:
        if slam.imu_available:
            try:
                # Get orientation data
                orientation = slam.imu.get_orientation()
                acceleration = slam.imu.get_acceleration()
                
                socketio.emit('imu_update', {
                    'available': True,
                    'orientation': {
                        'roll': round(orientation[0], 2),
                        'pitch': round(orientation[1], 2),
                        'yaw': round(orientation[2], 2)
                    },
                    'acceleration': {
                        'x': round(acceleration[0], 2),
                        'y': round(acceleration[1], 2),
                        'z': round(acceleration[2], 2)
                    }
                })
            except Exception as e:
                print(f"Error sending IMU data: {e}")
                slam.imu_available = False
                socketio.emit('imu_update', {
                    'available': False,
                    'error': 'IMU disconnected during operation'
                })
        else:
            # Send IMU not available status
            socketio.emit('imu_update', {
                'available': False
            })
        
        time.sleep(0.2)  # Send 5 times per second

# 添加电池状态更新函数
def send_battery_status():
    """定期发送电池状态到客户端"""
    print("电池状态监测线程已启动")
    while True:
        try:
            status = battery_monitor.get_battery_status()
            socketio.emit('battery_update', status)
            
            # 如果电量极低，发送警告
            if battery_monitor.is_critical_battery():
                socketio.emit('battery_critical', {
                    'message': '电池电量极低，请尽快充电!',
                    'level': status['level']
                })
                
                # 如果电量过低，自动减速以节省电量
                global current_speed
                if current_speed > 15:  # 如果当前速度高于15
                    with control_lock:
                        robot.t_stop(0)  # 暂时停止
                        time.sleep(0.5)
                        # 以较低的速度继续当前方向
                        if current_direction == 'forward':
                            robot.t_up(15, 0)
                        elif current_direction == 'backward':
                            robot.t_down(15, 0)
                        elif current_direction == 'left':
                            robot.turnLeft(8, 0)
                        elif current_direction == 'right':
                            robot.turnRight(8, 0)
                        
                        # 更新速度状态
                        current_speed = 15
                        socketio.emit('status_update', {
                            'speed': current_speed,
                            'direction': current_direction
                        })
        except Exception as e:
            print(f"发送电池状态错误: {e}")
        
        time.sleep(5)  # 每5秒发送一次电池状态

if __name__ == '__main__':
    try:
        # 设置服务器超时
        eventlet.wsgi.server.MAX_HEADER_LINE = 32768
        eventlet.websocket.WebSocketWSGI.max_frame_length = 16 * 1024 * 1024
        
        # 配置日志，减少不必要的输出
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # Start IMU data thread
        imu_thread = threading.Thread(target=send_imu_data)
        imu_thread.daemon = True
        imu_thread.start()
        
        # 启动电池监测
        battery_monitor.start()
        
        # 启动电池状态发送线程
        battery_thread = threading.Thread(target=send_battery_status)
        battery_thread.daemon = True
        battery_thread.start()
        
        # 使用eventlet和优化的性能参数
        print("启动AI智能四驱车服务器，访问 http://localhost:5000")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False,
                    log_output=False,  # 减少日志输出
                    max_size=16 * 1024 * 1024,  # 增加最大数据包大小
                    use_reloader=False)  # 禁用reloader提高稳定性
    except Exception as e:
        print(f"服务器启动错误: {e}")
    finally:
        # Clean up resources
        print("关闭服务器并清理资源...")
        camera.stop()
        slam.stop()
        battery_monitor.stop()  # 停止电池监测
        robot.t_stop(0) 