// Main JavaScript for AI Smart Car Control

document.addEventListener('DOMContentLoaded', function() {
    // Socket.io connection
    const socket = io();
    
    // Connection status handling
    const connectionStatus = document.getElementById('connection-status');
    
    socket.on('connect', function() {
        connectionStatus.textContent = 'Connected';
        connectionStatus.classList.add('connected');
    });
    
    socket.on('disconnect', function() {
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.classList.remove('connected');
    });
    
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
        gimbalHValue.textContent = Math.round(data.horizontal) + '°';
        gimbalVValue.textContent = Math.round(data.vertical) + '°';
    });
    
    // IMU data elements
    const rollValue = document.getElementById('roll-value');
    const pitchValue = document.getElementById('pitch-value');
    const accelXValue = document.getElementById('accel-x-value');
    const accelYValue = document.getElementById('accel-y-value');
    const accelZValue = document.getElementById('accel-z-value');
    
    // Listen for IMU updates from the server
    socket.on('imu_update', function(data) {
        // Update orientation values
        rollValue.textContent = Math.round(data.orientation.roll) + '°';
        pitchValue.textContent = Math.round(data.orientation.pitch) + '°';
        
        // Update acceleration values
        accelXValue.textContent = data.acceleration.x.toFixed(2) + ' g';
        accelYValue.textContent = data.acceleration.y.toFixed(2) + ' g';
        accelZValue.textContent = data.acceleration.z.toFixed(2) + ' g';
        
        // Use IMU data to enhance the 3D map visualization if needed
        if (mapScene) {
            updateMapOrientation(data.orientation);
        }
    });
    
    // Car joystick
    const carJoystick = nipplejs.create({
        zone: document.getElementById('car-joystick'),
        mode: 'static',
        position: { left: '50%', top: '50%' },
        color: 'blue',
        size: 120
    });
    
    carJoystick.on('move', function(evt, data) {
        const x = data.vector.x;
        const y = -data.vector.y;  // Invert Y axis
        
        socket.emit('car_control', { x: x, y: y });
    });
    
    carJoystick.on('end', function() {
        socket.emit('car_control', { x: 0, y: 0 });
    });
    
    // Gimbal joystick
    const gimbalJoystick = nipplejs.create({
        zone: document.getElementById('gimbal-joystick'),
        mode: 'static',
        position: { left: '50%', top: '50%' },
        color: 'red',
        size: 120
    });
    
    gimbalJoystick.on('move', function(evt, data) {
        const x = data.vector.x;
        const y = -data.vector.y;  // Invert Y axis
        
        socket.emit('gimbal_control', { x: x, y: y });
    });
    
    gimbalJoystick.on('end', function() {
        socket.emit('gimbal_control', { x: 0, y: 0 });
    });
    
    // Reset gimbal button
    document.getElementById('reset-gimbal-btn').addEventListener('click', function() {
        fetch('/reset_gimbal', { method: 'POST' })
            .then(response => response.json())
            .then(data => console.log('Gimbal reset:', data));
    });
    
    // Reset map button
    document.getElementById('reset-map-btn').addEventListener('click', function() {
        fetch('/reset_slam', { method: 'POST' })
            .then(response => response.json())
            .then(data => console.log('Map reset:', data));
    });
    
    // Fullscreen button
    document.getElementById('fullscreen-btn').addEventListener('click', function() {
        const videoContainer = document.querySelector('.video-container');
        
        if (!document.fullscreenElement) {
            videoContainer.requestFullscreen().catch(err => {
                console.error(`Error attempting to enable fullscreen: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    });
    
    // Initialize 3D map
    initMap();
});

// Initialize 3D map with Three.js
function initMap() {
    const container = document.getElementById('map-3d');
    
    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111111);
    
    // Create camera
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 5, 10);
    camera.lookAt(0, 0, 0);
    
    // Create renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);
    
    // Add grid
    const gridHelper = new THREE.GridHelper(20, 20);
    scene.add(gridHelper);
    
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(0, 10, 10);
    scene.add(directionalLight);
    
    // Create car representation
    const carGeometry = new THREE.BoxGeometry(1, 0.5, 2);
    const carMaterial = new THREE.MeshStandardMaterial({ color: 0x00ff00 });
    const car = new THREE.Mesh(carGeometry, carMaterial);
    scene.add(car);
    
    // Points for the map
    const pointsGeometry = new THREE.BufferGeometry();
    const pointsMaterial = new THREE.PointsMaterial({ color: 0xff0000, size: 0.1 });
    const points = new THREE.Points(pointsGeometry, pointsMaterial);
    scene.add(points);
    
    // Trajectory line
    const trajectoryGeometry = new THREE.BufferGeometry();
    const trajectoryMaterial = new THREE.LineBasicMaterial({ color: 0x0000ff });
    const trajectory = new THREE.Line(trajectoryGeometry, trajectoryMaterial);
    scene.add(trajectory);
    
    // Handle window resize
    window.addEventListener('resize', function() {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
    
    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        
        // Update map data
        updateMapData(points, trajectory, car);
        
        // Render scene
        renderer.render(scene, camera);
    }
    
    animate();
}

// Update map data from server
function updateMapData(points, trajectory, car) {
    fetch('/map_data')
        .then(response => response.json())
        .then(data => {
            // Update points
            if (data.points && data.points.length > 0) {
                const positions = new Float32Array(data.points.length * 3);
                
                for (let i = 0; i < data.points.length; i++) {
                    positions[i * 3] = data.points[i][0];
                    positions[i * 3 + 1] = data.points[i][2];  // Y is up in Three.js
                    positions[i * 3 + 2] = data.points[i][1];
                }
                
                points.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
                points.geometry.attributes.position.needsUpdate = true;
            }
            
            // Update trajectory
            if (data.trajectory && data.trajectory.length > 0) {
                const positions = new Float32Array(data.trajectory.length * 3);
                
                for (let i = 0; i < data.trajectory.length; i++) {
                    positions[i * 3] = data.trajectory[i][0];
                    positions[i * 3 + 1] = data.trajectory[i][2];  // Y is up in Three.js
                    positions[i * 3 + 2] = data.trajectory[i][1];
                }
                
                trajectory.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
                trajectory.geometry.attributes.position.needsUpdate = true;
                
                // Update car position to the last trajectory point
                const lastPoint = data.trajectory[data.trajectory.length - 1];
                car.position.set(lastPoint[0], lastPoint[2], lastPoint[1]);
            }
        })
        .catch(error => console.error('Error fetching map data:', error));
    
    // Also update position and orientation
    fetch('/position')
        .then(response => response.json())
        .then(data => {
            if (data.orientation) {
                // Update car rotation based on yaw
                car.rotation.y = data.orientation[2];
            }
        })
        .catch(error => console.error('Error fetching position data:', error));
}

// Function to update the 3D map orientation based on IMU data
function updateMapOrientation(orientation) {
    // This is a placeholder for map orientation updates
    // In a real implementation, this would adjust the camera or scene
    // based on the IMU orientation data
    if (mapControls) {
        // Example: Adjust the camera target based on roll and pitch
        // This would need to be customized based on your specific map implementation
        const rollRad = orientation.roll * Math.PI / 180;
        const pitchRad = orientation.pitch * Math.PI / 180;
        
        // This is just an example - actual implementation would depend on your map setup
        // mapControls.target.y = Math.sin(pitchRad) * 5;
        // mapControls.target.x = Math.sin(rollRad) * 5;
        // mapControls.update();
    }
} 