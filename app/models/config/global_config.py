import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Type, Any
from pathlib import Path

from app.models.config.device_config import DevicesConfig
from app.models.config.resource_config import ResourceConfig, Option, SelectOption, BoolOption, InputOption, Task


@dataclass
class RunTimeConfig:
    task_name: str
    task_entry: str
    pipeline_override: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class RunTimeConfigs:
    list: List[RunTimeConfig] = field(default_factory=list)
    resource_path: Path = field(default_factory=Path)  # 当前资源加载时所在的目录路径


class GlobalConfig:
    """
    单例类，用于管理全局配置，包括 DevicesConfig 和多个 ResourceConfig。
    """

    _instance: Optional["GlobalConfig"] = None
    _lock: threading.Lock = threading.Lock()

    devices_config: Optional[DevicesConfig]
    resource_configs: Dict[str, ResourceConfig]

    def __new__(cls: Type["GlobalConfig"]) -> "GlobalConfig":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalConfig, cls).__new__(cls)
                cls._instance.devices_config = None  # 全局 DevicesConfig 初始化为 None
                cls._instance.resource_configs = {}  # 存储多个 ResourceConfig，键为 resource_name
        return cls._instance

    def load_devices_config(self, file_path: str) -> None:
        """
        从 JSON 文件中加载全局 DevicesConfig 配置。
        """
        self.devices_config = DevicesConfig.from_json_file(file_path)

    def load_resource_config(self, file_path: str) -> None:
        """
        从 JSON 文件中加载单个 ResourceConfig，并存储到全局配置中。

        此处利用 ResourceConfig 中的 source_file 属性记录加载时的文件路径（包含文件名）。
        """
        resource_config: ResourceConfig = ResourceConfig.from_json_file(file_path)
        resource_config.source_file = file_path
        self.resource_configs[resource_config.resource_name] = resource_config

    def get_devices_config(self) -> DevicesConfig:
        """
        获取全局 DevicesConfig 配置。
        """
        if self.devices_config is None:
            raise ValueError("DevicesConfig 尚未加载。")
        return self.devices_config

    def get_resource_config(self, resource_name: str) -> Optional[ResourceConfig]:
        """
        根据资源名称获取对应的 ResourceConfig 配置。
        """
        return self.resource_configs.get(resource_name)

    def get_all_resource_configs(self) -> List[ResourceConfig]:
        """
        获取所有加载的 ResourceConfig 配置。
        """
        return list(self.resource_configs.values())

    def load_all_resources_from_directory(self, directory: str) -> None:
        """
        从指定目录及其所有子目录中加载名为 "resource_config.json" 的资源配置文件。
        """
        path: Path = Path(directory)
        if not path.is_dir():
            raise ValueError(f"{directory} 不是一个有效的目录。")

        for file in path.rglob("resource_config.json"):
            self.load_resource_config(str(file))

    def save_all_configs(self) -> None:
        """
        保存全局 DevicesConfig 和所有 ResourceConfig 配置到对应的文件中。
        """
        if self.devices_config is not None:
            self.devices_config.to_json_file()
        else:
            raise ValueError("DevicesConfig 尚未加载，无法保存。")

        for resource_config in self.resource_configs.values():
            resource_config.to_json_file()

    def get_runtime_configs_for_resource(self, resource_name: str) -> RunTimeConfigs:
        """
        获取指定资源中所有任务的 RunTimeConfigs，并将资源所在目录（由 source_file 计算得出）传递到 resource_path 中。
        """
        resource_config = self.get_resource_config(resource_name)
        if resource_config is None:
            raise ValueError(f"Resource '{resource_name}' not found.")

        runtime_configs = []
        for task in resource_config.resource_tasks:
            pipeline_override = self._process_task_options(resource_config, task)
            runtime_config = RunTimeConfig(
                task_name=task.task_name,
                task_entry=task.task_entry,
                pipeline_override=pipeline_override
            )
            runtime_configs.append(runtime_config)

        # 通过 source_file（包含文件名）计算出资源加载目录
        resource_path = Path(resource_config.source_file).parent if resource_config.source_file else Path()
        return RunTimeConfigs(list=runtime_configs, resource_path=resource_path)

    def get_runtime_config_for_task(self, resource_name: str, task_name: str) -> Optional[RunTimeConfig]:
        """
        获取特定资源中特定任务的 RunTimeConfig。
        """
        resource_config = self.get_resource_config(resource_name)
        if resource_config is None:
            raise ValueError(f"Resource '{resource_name}' not found.")

        task = next((t for t in resource_config.resource_tasks if t.task_name == task_name), None)
        if task is None:
            return None

        pipeline_override = self._process_task_options(resource_config, task)
        return RunTimeConfig(
            task_name=task.task_name,
            task_entry=task.task_entry,
            pipeline_override=pipeline_override
        )

    def _process_task_options(self, resource_config: ResourceConfig, task: Task) -> Dict[str, Any]:
        """
        处理任务的选项，生成 pipeline_override。
        """
        final_pipeline_override = {}

        def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]):
            """递归合并字典"""
            for key, value in dict2.items():
                if isinstance(value, dict) and isinstance(dict1.get(key), dict):
                    merge_dicts(dict1[key], value)
                else:
                    dict1[key] = value

        resource_name = resource_config.resource_name
        device_resources = []

        if self.devices_config is not None:
            for device in self.devices_config.devices:
                for resource in device.resources:
                    if resource.resource_name == resource_name:
                        device_resources.append(resource)

        for option_name in task.option:
            option = next((opt for opt in resource_config.options if opt.name == option_name), None)
            if option is None:
                continue

            option_value = None
            for device_resource in device_resources:
                option_config = next((opt for opt in device_resource.options if opt.option_name == option_name), None)
                if option_config is not None:
                    option_value = option_config.value
                    break

            if option_value is None:
                option_value = option.default

            if isinstance(option, SelectOption):
                choice_value = option_value
                choice = next((c for c in option.choices if c.name == option_value), None)
                if choice:
                    choice_value = choice.value

                choice_override = option.pipeline_override.get(choice_value, {}) if option.pipeline_override else {}
                merge_dicts(final_pipeline_override, choice_override)

            elif isinstance(option, BoolOption):
                if option_value and option.pipeline_override:
                    processed_override = self._replace_placeholder(option.pipeline_override, str(option_value))
                    merge_dicts(final_pipeline_override, processed_override)

            elif isinstance(option, InputOption):
                if option_value and option.pipeline_override:
                    processed_override = self._replace_placeholder(option.pipeline_override, str(option_value))
                    merge_dicts(final_pipeline_override, processed_override)

        return final_pipeline_override

    def _replace_placeholder(self, pipeline: Any, value: str) -> Any:
        """
        替换管道中的占位符。
        """
        if isinstance(pipeline, dict):
            return {
                k: (v.replace("{value}", str(value)).replace("{boole}", str(value))
                    if isinstance(v, str) else self._replace_placeholder(v, value))
                for k, v in pipeline.items()
            }
        return pipeline
