// Main JavaScript for AI Smart Car Control

document.addEventListener('DOMContentLoaded', function() {
    // Socket.io connection with reconnection options
    const socket = io({
        reconnection: true,        // 启用自动重连
        reconnectionAttempts: 10,  // 最多尝试重连10次
        reconnectionDelay: 1000,   // 初始重连延迟1秒
        reconnectionDelayMax: 5000, // 最大重连延迟5秒
        timeout: 20000             // 连接超时时间
    });
    
    // Connection status handling
    const connectionStatus = document.getElementById('connection-status');
    let heartbeatTimer = null;
    let lastPongTime = Date.now();
    
    // 实现心跳检测
    function startHeartbeat() {
        // 清除可能存在的旧定时器
        if (heartbeatTimer) {
            clearInterval(heartbeatTimer);
        }
        
        // 设置新的心跳检测
        heartbeatTimer = setInterval(function() {
            // 检查上次pong响应时间，如果超过10秒没有响应，认为连接断开
            if (Date.now() - lastPongTime > 10000) {
                console.log('心跳检测超时，尝试重连...');
                connectionStatus.textContent = 'Reconnecting...';
                connectionStatus.classList.remove('connected');
                socket.disconnect();
                socket.connect(); // 尝试重新连接
            } else {
                // 发送ping心跳
                socket.emit('ping');
            }
        }, 3000); // 每3秒检测一次
    }
    
    socket.on('connect', function() {
        connectionStatus.textContent = 'Connected';
        connectionStatus.classList.add('connected');
        startHeartbeat(); // 连接成功后启动心跳检测
        console.log('已连接到服务器');
    });
    
    socket.on('disconnect', function() {
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.classList.remove('connected');
        if (heartbeatTimer) {
            clearInterval(heartbeatTimer);
        }
        console.log('与服务器的连接已断开');
    });
    
    // 接收服务器的pong响应
    socket.on('pong', function(data) {
        lastPongTime = Date.now();
        console.log('收到服务器心跳响应');
    });
    
    // 连接建立成功的确认
    socket.on('connection_established', function(data) {
        console.log('连接已成功建立，开始心跳检测');
        lastPongTime = Date.now();
    });
    
    // 视频流错误处理
    const videoFeed = document.getElementById('video-feed');
    if (videoFeed) {
        videoFeed.onerror = function() {
            console.error('视频流加载失败，尝试重新加载');
            setTimeout(() => {
                // 尝试重新加载视频流
                videoFeed.src = videoFeed.src;
            }, 2000);
        };
    }
    
    // Status updates
    const speedValue = document.getElementById('speed-value');
    const directionValue = document.getElementById('direction-value');
    const gimbalHValue = document.getElementById('gimbal-h-value');
    const gimbalVValue = document.getElementById('gimbal-v-value');
    
    socket.on('status_update', function(data) {
        speedValue.textContent = data.speed;
        directionValue.textContent = data.direction;
    });
    
    socket.on('gimbal_update', function(data) {
        gimbalHValue.textContent = `${data.horizontal}°`;
        gimbalVValue.textContent = `${data.vertical}°`;
    });
    
    // IMU status handling
    const rollValue = document.getElementById('roll-value');
    const pitchValue = document.getElementById('pitch-value');
    const accelXValue = document.getElementById('accel-x-value');
    const accelYValue = document.getElementById('accel-y-value');
    const accelZValue = document.getElementById('accel-z-value');
    
    function updateIMUStatus(available) {
        const imuContainer = document.querySelector('.imu-data-container');
        if (imuContainer) {
            if (available) {
                imuContainer.classList.add('connected');
                imuContainer.classList.remove('disconnected');
            } else {
                imuContainer.classList.remove('connected');
                imuContainer.classList.add('disconnected');
                
                // Reset IMU values
                rollValue.textContent = "N/A";
                pitchValue.textContent = "N/A";
                accelXValue.textContent = "N/A";
                accelYValue.textContent = "N/A";
                accelZValue.textContent = "N/A";
            }
        }
    }
    
    socket.on('imu_update', function(data) {
        updateIMUStatus(data.available);
        
        if (data.available) {
            rollValue.textContent = `${data.orientation.roll}°`;
            pitchValue.textContent = `${data.orientation.pitch}°`;
            accelXValue.textContent = `${data.acceleration.x} g`;
            accelYValue.textContent = `${data.acceleration.y} g`;
            accelZValue.textContent = `${data.acceleration.z} g`;
        }
    });
    
    // Setup car control joystick
    const carJoystickContainer = document.getElementById('car-joystick');
    if (carJoystickContainer) {
        const carJoystick = nipplejs.create({
            zone: carJoystickContainer,
            mode: 'static',
            position: { left: '50%', top: '50%' },
            color: 'blue',
            size: 120
        });
        
        const carJoystickStatus = document.createElement('div');
        carJoystickStatus.className = 'joystick-status centered';
        carJoystickStatus.textContent = '已回中';
        carJoystickContainer.parentNode.appendChild(carJoystickStatus);
        
        // Handle joystick movement
        carJoystick.on('move', function(evt, data) {
            const x = data.vector.x;
            const y = data.vector.y;
            
            // Update joystick status
            carJoystickStatus.textContent = '活动中';
            carJoystickStatus.classList.remove('centered');
            carJoystickStatus.classList.add('active');
            
            socket.emit('car_control', { x, y });
        });
        
        // Handle joystick end
        carJoystick.on('end', function() {
            socket.emit('car_control', { x: 0, y: 0 });
            
            // Update joystick status
            carJoystickStatus.textContent = '已回中';
            carJoystickStatus.classList.add('centered');
            carJoystickStatus.classList.remove('active');
        });
    }
    
    // Setup gimbal control joystick
    const gimbalJoystickContainer = document.getElementById('gimbal-joystick');
    if (gimbalJoystickContainer) {
        const gimbalJoystick = nipplejs.create({
            zone: gimbalJoystickContainer,
            mode: 'static',
            position: { left: '50%', top: '50%' },
            color: 'green',
            size: 120
        });
        
        const gimbalJoystickStatus = document.createElement('div');
        gimbalJoystickStatus.className = 'joystick-status centered';
        gimbalJoystickStatus.textContent = '已回中';
        gimbalJoystickContainer.parentNode.appendChild(gimbalJoystickStatus);
        
        // Handle joystick movement
        gimbalJoystick.on('move', function(evt, data) {
            const x = data.vector.x;
            const y = data.vector.y;
            
            // Update joystick status
            gimbalJoystickStatus.textContent = '活动中';
            gimbalJoystickStatus.classList.remove('centered');
            gimbalJoystickStatus.classList.add('active');
            
            socket.emit('gimbal_control', { x, y });
        });
        
        // Handle joystick end
        gimbalJoystick.on('end', function() {
            socket.emit('gimbal_control', { x: 0, y: 0 });
            
            // Update joystick status
            gimbalJoystickStatus.textContent = '已回中';
            gimbalJoystickStatus.classList.add('centered');
            gimbalJoystickStatus.classList.remove('active');
        });
    }
    
    // Setup reset button for gimbal
    const resetGimbalBtn = document.getElementById('reset-gimbal-btn');
    if (resetGimbalBtn) {
        resetGimbalBtn.addEventListener('click', function() {
            fetch('/reset_gimbal', {
                method: 'POST'
            }).then(response => response.json())
              .then(data => console.log('Gimbal reset:', data))
              .catch(error => console.error('Error resetting gimbal:', error));
        });
    }
    
    // Setup reset button for map
    const resetMapBtn = document.getElementById('reset-map-btn');
    if (resetMapBtn) {
        resetMapBtn.addEventListener('click', function() {
            fetch('/reset_slam', {
                method: 'POST'
            }).then(response => response.json())
              .then(data => console.log('SLAM reset:', data))
              .catch(error => console.error('Error resetting SLAM:', error));
        });
    }
    
    // Setup fullscreen button
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const container = document.querySelector('.container');
    if (fullscreenBtn && container) {
        fullscreenBtn.addEventListener('click', function() {
            container.classList.toggle('fullscreen-mode');
            
            if (container.classList.contains('fullscreen-mode')) {
                fullscreenBtn.textContent = 'Exit Fullscreen';
            } else {
                fullscreenBtn.textContent = 'Fullscreen';
            }
        });
    }
    
    // Initialize the 3D map
    initMap();
});

// 3D Map functionality
function initMap() {
    const mapContainer = document.getElementById('map-3d');
    if (!mapContainer) return;
    
    // Setup Three.js scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, mapContainer.clientWidth / mapContainer.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    
    renderer.setSize(mapContainer.clientWidth, mapContainer.clientHeight);
    renderer.setClearColor(0x000000, 0.3);
    mapContainer.appendChild(renderer.domElement);
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const pointLight = new THREE.PointLight(0xffffff, 0.8);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);
    
    // Add grid for reference
    const gridHelper = new THREE.GridHelper(20, 20, 0x888888, 0x444444);
    scene.add(gridHelper);
    
    // Car representation
    const carGeometry = new THREE.BoxGeometry(0.5, 0.2, 0.7);
    const carMaterial = new THREE.MeshLambertMaterial({ color: 0x00aaff });
    const car = new THREE.Mesh(carGeometry, carMaterial);
    car.position.y = 0.1;
    scene.add(car);
    
    // Setup camera position
    camera.position.set(5, 5, 5);
    camera.lookAt(car.position);
    
    // Map points
    const pointsGeometry = new THREE.BufferGeometry();
    const pointsMaterial = new THREE.PointsMaterial({ color: 0xffff00, size: 0.1 });
    const points = new THREE.Points(pointsGeometry, pointsMaterial);
    scene.add(points);
    
    // Trajectory
    const trajectoryGeometry = new THREE.BufferGeometry();
    const trajectoryMaterial = new THREE.LineBasicMaterial({ color: 0x00ff00 });
    const trajectory = new THREE.Line(trajectoryGeometry, trajectoryMaterial);
    scene.add(trajectory);
    
    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    
    animate();
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (mapContainer.clientWidth > 0 && mapContainer.clientHeight > 0) {
            camera.aspect = mapContainer.clientWidth / mapContainer.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(mapContainer.clientWidth, mapContainer.clientHeight);
        }
    });
    
    // Update map data periodically
    setInterval(function() {
        fetch('/map_data')
            .then(response => response.json())
            .then(data => updateMapData(data.points, data.trajectory, data.position))
            .catch(error => console.error('Error fetching map data:', error));
    }, 1000);
    
    // Update car orientation from IMU data
    setInterval(function() {
        fetch('/position')
            .then(response => response.json())
            .then(data => updateMapOrientation(data))
            .catch(error => console.error('Error fetching position data:', error));
    }, 200);
}

function updateMapData(points, trajectory, car) {
    const mapContainer = document.getElementById('map-3d');
    if (!mapContainer) return;
    
    const scene = mapContainer.querySelector('canvas')?.['__three_scene'];
    if (!scene) return;
    
    // Update map points
    const pointsObject = scene.children.find(child => child instanceof THREE.Points);
    if (pointsObject && points && points.length > 0) {
        const positions = new Float32Array(points.length * 3);
        
        for (let i = 0; i < points.length; i++) {
            positions[i * 3] = points[i].x;
            positions[i * 3 + 1] = 0;  // Set y to 0 (ground level)
            positions[i * 3 + 2] = points[i].z;
        }
        
        pointsObject.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        pointsObject.geometry.attributes.position.needsUpdate = true;
    }
    
    // Update trajectory
    const trajectoryObject = scene.children.find(child => child instanceof THREE.Line);
    if (trajectoryObject && trajectory && trajectory.length > 0) {
        const positions = new Float32Array(trajectory.length * 3);
        
        for (let i = 0; i < trajectory.length; i++) {
            positions[i * 3] = trajectory[i].x;
            positions[i * 3 + 1] = 0.1;  // Slightly above ground
            positions[i * 3 + 2] = trajectory[i].z;
        }
        
        trajectoryObject.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        trajectoryObject.geometry.attributes.position.needsUpdate = true;
    }
    
    // Update car position
    const carObject = scene.children.find(child => child instanceof THREE.Mesh && child.geometry instanceof THREE.BoxGeometry);
    if (carObject && car) {
        carObject.position.x = car.x;
        carObject.position.z = car.z;
    }
}

function updateMapOrientation(orientation) {
    const mapContainer = document.getElementById('map-3d');
    if (!mapContainer) return;
    
    const scene = mapContainer.querySelector('canvas')?.['__three_scene'];
    if (!scene) return;
    
    // Update car orientation based on IMU data
    const carObject = scene.children.find(child => child instanceof THREE.Mesh && child.geometry instanceof THREE.BoxGeometry);
    if (carObject && orientation) {
        const yaw = orientation.yaw * (Math.PI / 180);  // Convert to radians
        carObject.rotation.y = -yaw;  // Negative to match coordinate system
    }
    
    // Optionally update camera position to follow car
    const camera = mapContainer.querySelector('canvas')?.['__three_camera'];
    if (camera && carObject) {
        const distance = 5;
        const height = 5;
        const angle = carObject.rotation.y - Math.PI / 4;  // Offset for better view
        
        camera.position.x = carObject.position.x + distance * Math.sin(angle);
        camera.position.z = carObject.position.z + distance * Math.cos(angle);
        camera.position.y = height;
        
        camera.lookAt(carObject.position);
    }
} 