# app/models/device.py
from app.models.config.device_config import DeviceConfig
from app.models.config.global_config import GlobalConfig


class Device:
    def __init__(self, device_config: DeviceConfig):
        self.device_config = device_config
        self.name = device_config.device_name
        self.device_type = device_config.adb_config.name
        self.status = "运行正常"  # Default status, could be updated dynamically
        self.last_start = "2025-02-26 11:45:14"  # Default value
        self.start_count = 42  # Default value

    @property
    def adb_config(self):
        return self.device_config.adb_config

    @property
    def resources(self):
        return self.device_config.resources

    @property
    def schedule_enabled(self):
        return self.device_config.schedule_enabled

    @property
    def start_command(self):
        return self.device_config.start_command

    @classmethod
    def get_all_devices(cls):
        """Get all devices from global config"""
        global_config = GlobalConfig()
        try:
            devices_config = global_config.get_devices_config()
            return [cls(device_config) for device_config in devices_config.devices]
        except ValueError:
            # If devices config is not loaded, return sample devices
            return cls.get_sample_devices()

    @classmethod
    def get_sample_devices(cls):
        """Fallback method for sample devices when no config is available"""
        # Create dummy DeviceConfig objects
        from app.models.config.device_config import DeviceConfig, AdbDevice, Resource

        sample_devices = []

        # Create dummy configs similar to the example in device_config.py
        device1 = DeviceConfig(
            device_name="雷电模拟器-阴阳师1",
            adb_config=AdbDevice(
                name="LDPlayer",
                adb_path="D:\\leidian\\LDPlayer9\\adb.exe",
                address="127.0.0.1:5555",
                screencap_methods=18446744073709551559,
                input_methods=18446744073709551607,
                config={}
            ),
            resources=[],
            schedule_enabled=True,
            start_command="D:\\leidian\\LDPlayer9\\dnplayer.exe index=0"
        )

        device2 = DeviceConfig(
            device_name="夜神模拟器-战双",
            adb_config=AdbDevice(
                name="夜神模拟器",
                adb_path="C:\\Android\\adb.exe",
                address="emulator-5554",
                screencap_methods=18446744073709551559,
                input_methods=18446744073709551607,
                config={}
            ),
            resources=[],
            schedule_enabled=False,
            start_command=""
        )

        device3 = DeviceConfig(
            device_name="雷电模拟器-原神",
            adb_config=AdbDevice(
                name="LDPlayer",
                adb_path="D:\\leidian\\LDPlayer9\\adb.exe",
                address="127.0.0.1:5556",
                screencap_methods=18446744073709551559,
                input_methods=18446744073709551607,
                config={}
            ),
            resources=[],
            schedule_enabled=True,
            start_command=""
        )

        device4 = DeviceConfig(
            device_name="MuMu模拟器-明日方舟",
            adb_config=AdbDevice(
                name="MuMu",
                adb_path="D:\\MuMu\\adb.exe",
                address="127.0.0.1:7555",
                screencap_methods=18446744073709551559,
                input_methods=18446744073709551607,
                config={}
            ),
            resources=[],
            schedule_enabled=True,
            start_command=""
        )

        device5 = DeviceConfig(
            device_name="BlueStacks-FGO",
            adb_config=AdbDevice(
                name="BlueStacks",
                adb_path="C:\\Program Files\\BlueStacks\\adb.exe",
                address="127.0.0.1:5555",
                screencap_methods=18446744073709551559,
                input_methods=18446744073709551607,
                config={}
            ),
            resources=[],
            schedule_enabled=False,
            start_command=""
        )

        device6 = DeviceConfig(
            device_name="雷电模拟器-碧蓝航线",
            adb_config=AdbDevice(
                name="LDPlayer",
                adb_path="D:\\leidian\\LDPlayer9\\adb.exe",
                address="127.0.0.1:5557",
                screencap_methods=18446744073709551559,
                input_methods=18446744073709551607,
                config={}
            ),
            resources=[],
            schedule_enabled=False,
            start_command=""
        )

        # Create Device objects from configs
        devices = [device1, device2, device3, device4, device5, device6]
        sample_devices = [cls(device) for device in devices]

        # Set some special statuses
        sample_devices[2].status = "检测到异常"
        sample_devices[5].status = "检测到异常"

        return sample_devices