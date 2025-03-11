import time
import threading

class BatteryMonitor:
    """电池监测类，用于监测电池电量"""
    
    def __init__(self, robot=None, update_interval=5):
        """
        初始化电池监测
        
        参数:
        robot -- LOBOROBOT 实例，用于读取ADC数据
        update_interval -- 电量更新间隔（秒）
        """
        self.robot = robot
        self.update_interval = update_interval
        self.running = False
        self.lock = threading.Lock()
        self.battery_level = 100  # 初始电量设为100%
        self.voltage = 0
        
        # 电池阈值设置 (单位: 伏特)
        self.max_voltage = 8.4    # 锂电池满电压约为8.4V (2节锂电池串联)
        self.min_voltage = 6.0    # 锂电池最低电压阈值
        
        # 电量预警阈值
        self.low_battery_threshold = 20  # 低电量警告阈值 (%)
        self.critical_battery_threshold = 10  # 极低电量警告阈值 (%)
        
        # ADC通道设置
        self.adc_channel = 0  # 假设ADC0用于读取电池电压
        
        # 状态
        self.status = "normal"  # normal, low, critical
        
        # 硬件可用性标志
        self.hardware_available = True
        
        # 尝试初始化并检查硬件是否可用
        self._check_hardware_availability()
    
    def _check_hardware_availability(self):
        """检查硬件是否可用"""
        try:
            if self.robot:
                # 尝试读取一次ADC值，检查硬件是否可用
                self.robot.get_adc_value(self.adc_channel)
                self.hardware_available = True
                print("电池监测硬件正常")
            else:
                self.hardware_available = False
                print("警告: 没有可用的机器人控制器，电池监测将使用模拟数据")
        except Exception as e:
            self.hardware_available = False
            print(f"警告: 电池监测硬件不可用 - {e}")
            print("电池监测将使用模拟数据")
    
    def start(self):
        """启动电池监测线程"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        print("电池监测线程已启动")
    
    def stop(self):
        """停止电池监测线程"""
        self.running = False
        if hasattr(self, 'thread') and self.thread:
            self.thread.join()
        print("电池监测线程已停止")
    
    def _monitor_loop(self):
        """电池监测循环，定期更新电池状态"""
        while self.running:
            self._update_battery_level()
            time.sleep(self.update_interval)
    
    def _update_battery_level(self):
        """更新电池电量和状态"""
        try:
            if not self.hardware_available:
                # 硬件不可用时使用模拟数据
                self._simulate_battery_level()
                return
                
            if self.robot:
                try:
                    # 从ADC读取电压值
                    raw_value = self.robot.get_adc_value(self.adc_channel)
                    
                    # 将原始ADC值转换为电压
                    adc_max = 1023  # 10位ADC最大值
                    adc_ref = 3.3   # 参考电压
                    voltage_divider_ratio = 0.25  # 分压比例，根据实际电路调整
                    
                    voltage = (raw_value / adc_max) * adc_ref / voltage_divider_ratio
                    
                    # 计算电池百分比
                    percentage = self._calculate_percentage(voltage)
                    
                    # 更新状态
                    with self.lock:
                        self.voltage = round(voltage, 2)
                        self.battery_level = percentage
                        
                        # 更新电池状态
                        if percentage <= self.critical_battery_threshold:
                            self.status = "critical"
                        elif percentage <= self.low_battery_threshold:
                            self.status = "low"
                        else:
                            self.status = "normal"
                
                except Exception as e:
                    print(f"ADC读取错误: {e}")
                    # 发生错误时，转为模拟模式
                    self.hardware_available = False
                    self._simulate_battery_level()
            
        except Exception as e:
            print(f"电池监测错误: {e}")
            # 错误处理，确保不会因为电池监测错误而影响整个程序
            self._simulate_battery_level()
    
    def _simulate_battery_level(self):
        """模拟电池电量变化（用于硬件不可用时）"""
        with self.lock:
            # 模拟电池缓慢放电，每次更新减少0.1%-0.5%
            discharge_rate = min(0.5, max(0.1, self.battery_level / 500))
            self.battery_level = max(0, self.battery_level - discharge_rate)
            self.voltage = (self.battery_level / 100) * (self.max_voltage - self.min_voltage) + self.min_voltage
            self.voltage = round(self.voltage, 2)
            
            # 更新状态
            if self.battery_level <= self.critical_battery_threshold:
                self.status = "critical"
            elif self.battery_level <= self.low_battery_threshold:
                self.status = "low"
            else:
                self.status = "normal"
    
    def _calculate_percentage(self, voltage):
        """根据电压计算电池百分比"""
        if voltage >= self.max_voltage:
            return 100
        elif voltage <= self.min_voltage:
            return 0
        else:
            # 线性映射电压到百分比
            percentage = ((voltage - self.min_voltage) / 
                         (self.max_voltage - self.min_voltage)) * 100
            return int(percentage)
    
    def get_battery_status(self):
        """获取当前电池状态
        
        返回:
        dict -- 包含电量百分比、电压和状态的字典
        """
        with self.lock:
            return {
                "level": self.battery_level,
                "voltage": self.voltage,
                "status": self.status,
                "hardware_available": self.hardware_available
            }
    
    def is_low_battery(self):
        """检查是否低电量"""
        with self.lock:
            return self.battery_level <= self.low_battery_threshold
    
    def is_critical_battery(self):
        """检查是否极低电量"""
        with self.lock:
            return self.battery_level <= self.critical_battery_threshold
            
    def reset_battery(self, level=100):
        """重置电池电量（用于测试和充电后）"""
        with self.lock:
            self.battery_level = level
            self.voltage = (self.battery_level / 100) * (self.max_voltage - self.min_voltage) + self.min_voltage
            self.status = "normal" 