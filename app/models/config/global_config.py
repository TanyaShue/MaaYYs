import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Type, Any
from pathlib import Path

from app.models.config.device_config import DevicesConfig
from app.models.config.resource_config import ResourceConfig, Option, SelectOption, BoolOption, InputOption, Task


@dataclass
class RunTimeConfig:
    task_name: str
    task_entry:str
    pipeline_override: Dict[str, Dict[str, Any]] = field(default_factory=dict)

@dataclass
class RunTimeConfigs:
    list: List[RunTimeConfig] = field(default_factory=list)

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

    def save_all_configs(self) -> None:
        """
        保存全局 DevicesConfig 和所有 ResourceConfig 配置到对应的文件中。

        注意：
            每个配置类的 to_json_file 方法会使用记录的 source_file 保存到原路径，
            如果某个配置未记录 source_file，则会抛出异常。
        """
        if self.devices_config is not None:
            self.devices_config.to_json_file()
        else:
            raise ValueError("DevicesConfig 尚未加载，无法保存。")

        for resource_config in self.resource_configs.values():
            resource_config.to_json_file()

    def get_runtime_configs_for_resource(self, resource_name: str) -> RunTimeConfigs:
        """
        获取指定资源中所有任务的 RunTimeConfigs。

        Args:
            resource_name (str): 资源名称

        Returns:
            RunTimeConfigs: 资源中所有任务的运行时配置
        """
        # 获取资源配置
        resource_config = self.get_resource_config(resource_name)
        if resource_config is None:
            raise ValueError(f"Resource '{resource_name}' not found.")

        runtime_configs = []

        # 遍历资源中的每个任务
        for task in resource_config.resource_tasks:
            pipeline_override = self._process_task_options(resource_config, task)

            runtime_config = RunTimeConfig(
                task_name=task.task_name,
                task_entry=task.task_entry,
                pipeline_override=pipeline_override
            )
            runtime_configs.append(runtime_config)

        return RunTimeConfigs(list=runtime_configs)

    def get_runtime_config_for_task(self, resource_name: str, task_name: str) -> Optional[RunTimeConfig]:
        """
        获取特定资源中特定任务的 RunTimeConfig。

        Args:
            resource_name (str): 资源名称
            task_name (str): 任务名称

        Returns:
            Optional[RunTimeConfig]: 任务的运行时配置，若未找到则返回 None
        """
        # 获取资源配置
        resource_config = self.get_resource_config(resource_name)
        if resource_config is None:
            raise ValueError(f"Resource '{resource_name}' not found.")

        # 查找对应的任务
        task = next((t for t in resource_config.resource_tasks if t.task_name == task_name), None)
        if task is None:
            return None

        # 处理任务的 pipeline_override
        pipeline_override = self._process_task_options(resource_config, task)

        return RunTimeConfig(
            task_name=task.task_name,
            task_entry=task.task_entry,
            pipeline_override=pipeline_override
        )

    def _process_task_options(self, resource_config: ResourceConfig, task: Task) -> Dict[str, Any]:
        """
        处理任务的选项，生成 pipeline_override。

        Args:
            resource_config (ResourceConfig): 资源配置
            task (Task): 任务配置

        Returns:
            Dict[str, Any]: 任务的 pipeline_override
        """
        final_pipeline_override = {}
        # print(f"当前------------{task}--------------")

        def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]):
            """递归合并字典"""
            for key, value in dict2.items():
                if isinstance(value, dict) and isinstance(dict1.get(key), dict):
                    merge_dicts(dict1[key], value)
                else:
                    dict1[key] = value

        # 找到当前任务所属的资源在设备配置中的配置
        resource_name = resource_config.resource_name
        device_resources = []

        # 从全局的devices_config中获取当前资源的配置
        if self.devices_config is not None:
            for device in self.devices_config.devices:
                for resource in device.resources:
                    if resource.resource_name == resource_name:
                        device_resources.append(resource)

        # 处理任务的选项
        for option_name in task.option:
            # 查找对应的选项配置
            option = next((opt for opt in resource_config.options if opt.name == option_name), None)
            if option is None:
                continue

            # 查找设备配置中的选项值
            option_value = None
            for device_resource in device_resources:
                option_config = next((opt for opt in device_resource.options if opt.option_name == option_name), None)
                if option_config is not None:
                    option_value = option_config.value
                    break

            # 如果设备配置中没有值，则使用默认值
            if option_value is None:
                option_value = option.default

            # 处理不同类型的选项
            if isinstance(option, SelectOption):
                # 对于select类型，需要找到choice的value
                choice_value = option_value
                # 如果option_value是choice的name，需要转换为value
                choice = next((c for c in option.choices if c.name == option_value), None)
                if choice:
                    choice_value = choice.value

                # 找到对应的 pipeline_override
                choice_override = option.pipeline_override.get(choice_value, {}) if option.pipeline_override else {}
                merge_dicts(final_pipeline_override, choice_override)

            elif isinstance(option, BoolOption):
                # 处理布尔类型选项
                if option_value and option.pipeline_override:
                    processed_override = self._replace_placeholder(option.pipeline_override, str(option_value))
                    merge_dicts(final_pipeline_override, processed_override)

            elif isinstance(option, InputOption):
                # 处理输入类型选项
                if option_value and option.pipeline_override:
                    # 替换占位符
                    processed_override = self._replace_placeholder(option.pipeline_override, str(option_value))
                    merge_dicts(final_pipeline_override, processed_override)

        return final_pipeline_override

    def _replace_placeholder(self, pipeline: Any, value: str) -> Any:
        """
        替换管道中的占位符。

        Args:
            pipeline (Any): 需要替换占位符的字典或其他类型
            value (str): 替换的值

        Returns:
            Any: 替换后的管道
        """
        if isinstance(pipeline, dict):
            return {
                k: (v.replace("{value}", str(value)).replace("{boole}", str(value))
                    if isinstance(v, str) else self._replace_placeholder(v, value))
                for k, v in pipeline.items()
            }
        return pipeline