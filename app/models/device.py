# app/models/device.py
class Device:
    def __init__(self, name, device_type, status, last_start=None):
        self.name = name
        self.device_type = device_type
        self.status = status
        self.last_start = last_start or "2025-02-26 11:45:14"
        self.start_count = 42  # Default value

    @classmethod
    def get_sample_devices(cls):
        return [
            cls("雷电模拟器-阴阳师1", "模拟器", "运行正常"),
            cls("夜神模拟器-战双", "模拟器", "运行正常"),
            cls("雷电模拟器-原神", "模拟器", "检测到异常"),
            cls("MuMu模拟器-明日方舟", "模拟器", "运行正常"),
            cls("BlueStacks-FGO", "模拟器", "运行正常"),
            cls("雷电模拟器-碧蓝航线", "模拟器", "检测到异常")
        ]