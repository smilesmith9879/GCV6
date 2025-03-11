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
    
    def start(self):
        """启动电池监测线程"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """停止电池监测线程"""
        self.running = False
        if hasattr(self, 'thread') and self.thread:
            self.thread.join()
    
    def _monitor_loop(self):
        """电池监测循环，定期更新电池状态"""
        while self.running:
            self._update_battery_level()
            time.sleep(self.update_interval)
    
    def _update_battery_level(self):
        """更新电池电量和状态"""
        try:
            if self.robot:
                # 从ADC读取电压值 (假设ADC返回的是原始值)
                raw_value = self.robot.get_adc_value(self.adc_channel)
                
                # 将原始ADC值转换为电压 (根据实际硬件参数调整)
                # 假设ADC是10位的，参考电压为3.3V，并且有电压分压器
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
            print(f"电池监测错误: {e}")
    
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
                "status": self.status
            }
    
    def is_low_battery(self):
        """检查是否低电量"""
        with self.lock:
            return self.battery_level <= self.low_battery_threshold
    
    def is_critical_battery(self):
        """检查是否极低电量"""
        with self.lock:
            return self.battery_level <= self.critical_battery_threshold 