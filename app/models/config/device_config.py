import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class AdbDevice:
    """ADB device configuration dataclass."""
    name: str
    adb_path: str  #  Path 类型改为 str，以匹配 JSON 配置文件中的字符串路径
    address: str
    screencap_methods: int
    input_methods: int
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Resource:
    """Resource configuration within a device."""
    resource_name: str
    selected_tasks: List[str] = field(default_factory=list)
    options: List['OptionConfig'] = field(default_factory=list)  #  使用前向引用

@dataclass
class OptionConfig:
    """Option configuration for a task or resource."""
    option_name: str
    value: Any
    task_name: str = None  #  任务名，可选，用于任务特定的选项

@dataclass
class DeviceConfig:
    """Device configuration dataclass."""
    device_name: str
    adb_config: AdbDevice
    resources: List[Resource] = field(default_factory=list)
    schedule_enabled: bool = False
    schedule_time:list[str] = field(default_factory=list)
    start_command: str = ""

@dataclass
class DevicesConfig:
    """Main devices configuration dataclass, wrapping a list of DeviceConfig."""
    devices: List[DeviceConfig] = field(default_factory=list)

    @classmethod
    def from_json_file(cls, file_path: str) -> 'DevicesConfig':
        """Load DevicesConfig from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return cls.from_dict(json_data)

    def to_json_file(self, file_path: str, indent=4):
        """Export DevicesConfig to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DevicesConfig':
        """Create DevicesConfig object from a dictionary."""
        devices_data = data.get('devices', [])
        device_configs = []
        for device_data in devices_data:
            adb_config_data = device_data.get('adb_config', {})
            adb_config = AdbDevice(**adb_config_data)  # 创建 AdbDevice 对象

            resources_data = device_data.get('resources', [])
            resources = []
            for resource_data in resources_data:
                options_data = resource_data.get('options', [])
                options = [OptionConfig(**option_data) for option_data in options_data]  # 创建 OptionConfig 对象列表
                resources.append(Resource(**{k: v for k, v in resource_data.items() if k != 'options'},
                                          options=options))  # 创建 Resource 对象

            # 修正后的代码，避免重复赋值 adb_config 和 resources
            device_configs.append(
                DeviceConfig(**{k: v for k, v in device_data.items() if k not in ('adb_config', 'resources')},
                             adb_config=adb_config, resources=resources))  # 创建 DeviceConfig 对象

        return DevicesConfig(devices=device_configs)
    def to_dict(self) -> Dict[str, Any]:
        """Convert DevicesConfig object to a dictionary."""
        return {
            "devices": [device_config_to_dict(device) for device in self.devices],
        }

def device_config_to_dict(device: DeviceConfig) -> Dict[str, Any]:
    """Helper function to convert DeviceConfig object to dictionary."""
    device_dict = device.__dict__
    device_dict['adb_config'] = adb_device_to_dict(device.adb_config) # 转换 AdbDevice 对象为字典
    device_dict['resources'] = [resource_to_dict(resource) for resource in device.resources] # 转换 Resource 对象列表为字典列表
    return device_dict

def adb_device_to_dict(adb_device: AdbDevice) -> Dict[str, Any]:
    """Helper function to convert AdbDevice object to dictionary."""
    return adb_device.__dict__

def resource_to_dict(resource: Resource) -> Dict[str, Any]:
    """Helper function to convert Resource object to dictionary."""
    resource_dict = resource.__dict__
    resource_dict['options'] = [option_config_to_dict(option) for option in resource.options] # 转换 OptionConfig 对象列表为字典列表
    return resource_dict

def option_config_to_dict(option: OptionConfig) -> Dict[str, Any]:
    """Helper function to convert OptionConfig object to dictionary."""
    return option.__dict__
