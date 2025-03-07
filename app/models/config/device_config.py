import json
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class AdbDevice:
    """ADB device configuration dataclass."""
    name: str
    adb_path: str  # 路径使用 str 类型，匹配 JSON 中的字符串路径
    address: str
    screencap_methods: int
    input_methods: int
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Resource:
    """Resource configuration within a device."""
    resource_name: str
    enable: bool = False  # 添加默认值，防止 JSON 中缺失时出错
    selected_tasks: List[str] = field(default_factory=list)
    options: List['OptionConfig'] = field(default_factory=list)  # 使用前向引用


@dataclass
class OptionConfig:
    """Option configuration for a task or resource."""
    option_name: str
    value: Any
    # task_name: str = None  # 任务名，可选，用于任务特定的选项


@dataclass
class DeviceConfig:
    """Device configuration dataclass."""
    device_name: str
    adb_config: AdbDevice
    resources: List[Resource] = field(default_factory=list)
    schedule_enabled: bool = False
    schedule_time: List[str] = field(default_factory=list)
    start_command: str = ""


@dataclass
class DevicesConfig:
    """Main devices configuration dataclass, wrapping a task_list of DeviceConfig."""
    devices: List[DeviceConfig] = field(default_factory=list)
    source_file: str = ""  # 用于记录加载的文件路径，但不保存到输出 JSON 中

    @classmethod
    def from_json_file(cls, file_path: str) -> 'DevicesConfig':
        """从 JSON 文件加载 DevicesConfig 并记录来源文件路径。"""
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        config = cls.from_dict(json_data)
        config.source_file = file_path  # 记录来源文件路径
        return config

    def to_json_file(self, file_path: str = None, indent=4):
        """将 DevicesConfig 导出为 JSON 文件。

        如果未传入 file_path，则使用记录的 source_file 进行保存。
        注意：输出的 JSON 文件中不包含 source_file 属性。
        """
        if file_path is None:
            if not self.source_file:
                raise ValueError("未提供保存路径且未记录原始文件路径。")
            file_path = self.source_file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DevicesConfig':
        """从字典创建 DevicesConfig 对象。"""
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
                # 传入除 options 以外的键，若 JSON 中没有 enable 键则使用默认值 False
                resources.append(Resource(**{k: v for k, v in resource_data.items() if k != 'options'},
                                          options=options))
            device_configs.append(
                DeviceConfig(**{k: v for k, v in device_data.items() if k not in ('adb_config', 'resources')},
                             adb_config=adb_config, resources=resources)
            )
        return DevicesConfig(devices=device_configs)

    def to_dict(self) -> Dict[str, Any]:
        """将 DevicesConfig 对象转换为字典，不包含 source_file 属性。"""
        return {
            "devices": [device_config_to_dict(device) for device in self.devices],
        }


def device_config_to_dict(device: DeviceConfig) -> Dict[str, Any]:
    """辅助函数，将 DeviceConfig 对象转换为字典。"""
    device_dict = device.__dict__.copy()
    device_dict['adb_config'] = adb_device_to_dict(device.adb_config)
    device_dict['resources'] = [resource_to_dict(resource) for resource in device.resources]
    return device_dict


def adb_device_to_dict(adb_device: AdbDevice) -> Dict[str, Any]:
    """辅助函数，将 AdbDevice 对象转换为字典。"""
    return adb_device.__dict__


def resource_to_dict(resource: Resource) -> Dict[str, Any]:
    """辅助函数，将 Resource 对象转换为字典。"""
    resource_dict = resource.__dict__.copy()
    resource_dict['options'] = [option_config_to_dict(option) for option in resource.options]
    return resource_dict


def option_config_to_dict(option: OptionConfig) -> Dict[str, Any]:
    """辅助函数，将 OptionConfig 对象转换为字典。"""
    return option.__dict__
