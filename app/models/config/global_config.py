import threading
from typing import List, Dict, Optional, Type
from pathlib import Path

from MAAPH.control.config.device_config import DevicesConfig
from MAAPH.control.config.resource_config import ResourceConfig


class GlobalConfig:
    """
    单例类，用于管理全局配置，包括 DevicesConfig 和多个 ResourceConfig。
    """

    _instance: Optional["GlobalConfig"] = None
    _lock: threading.Lock = threading.Lock()

    devices_config: Optional[DevicesConfig]
    resource_configs: Dict[str, ResourceConfig]

    def __new__(cls: Type["GlobalConfig"]) -> "GlobalConfig":
        """确保 GlobalConfig 只有一个实例。"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalConfig, cls).__new__(cls)
                cls._instance.devices_config = None  # 全局 DevicesConfig 初始化为 None
                cls._instance.resource_configs = {}  # 用于存储多个 ResourceConfig，键为 resource_name
        return cls._instance

    def load_devices_config(self, file_path: str) -> None:
        """
        从 JSON 文件中加载全局 DevicesConfig 配置。

        参数：
            file_path: 配置文件的路径。
        """
        self.devices_config = DevicesConfig.from_json_file(file_path)

    def load_resource_config(self, file_path: str) -> None:
        """
        从 JSON 文件中加载单个 ResourceConfig，并存储到全局配置中。

        参数：
            file_path: 配置文件的路径。
        """
        resource_config: ResourceConfig = ResourceConfig.from_json_file(file_path)
        self.resource_configs[resource_config.resource_name] = resource_config

    def get_devices_config(self) -> DevicesConfig:
        """
        获取全局 DevicesConfig 配置。

        返回：
            DevicesConfig 对象。

        异常：
            如果 DevicesConfig 尚未加载，则抛出 ValueError 异常。
        """
        if self.devices_config is None:
            raise ValueError("DevicesConfig 尚未加载。")
        return self.devices_config

    def get_resource_config(self, resource_name: str) -> Optional[ResourceConfig]:
        """
        根据资源名称获取对应的 ResourceConfig 配置。

        参数：
            resource_name: 资源名称。

        返回：
            ResourceConfig 对象，若不存在则返回 None。
        """
        return self.resource_configs.get(resource_name)

    def get_all_resource_configs(self) -> List[ResourceConfig]:
        """
        获取所有加载的 ResourceConfig 配置。

        返回：
            包含所有 ResourceConfig 的列表。
        """
        return list(self.resource_configs.values())

    def load_all_resources_from_directory(self, directory: str) -> None:
        """
        从指定目录及其所有子目录中加载名为 "resource_config.json" 的资源配置文件。

        参数：
            directory: 根目录路径，例如 "../assets/resource"
        """
        path: Path = Path(directory)
        if not path.is_dir():
            raise ValueError(f"{directory} 不是一个有效的目录。")

        # 递归查找所有子目录中的 "resource_config.json" 文件并加载
        for file in path.rglob("resource_config.json"):
            self.load_resource_config(str(file))
