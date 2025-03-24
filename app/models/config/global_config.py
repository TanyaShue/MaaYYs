from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any

from app.models.config.device_config import DevicesConfig
from app.models.config.resource_config import ResourceConfig, SelectOption, BoolOption, InputOption, Task


@dataclass
class RunTimeConfig:
    task_name: str
    task_entry: str
    pipeline_override: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class RunTimeConfigs:
    task_list: List[RunTimeConfig] = field(default_factory=list)
    resource_path: str = field(default_factory=Path)  # 当前资源加载时所在的目录路径


class GlobalConfig:
    """
    全局配置管理类，用于管理 DevicesConfig 和多个 ResourceConfig。

    **注意：此类不再是单例类，全局单例实例通过模块末尾的 `global_config` 变量创建。**
    """

    devices_config: Optional[DevicesConfig]
    resource_configs: Dict[str, ResourceConfig]

    def __init__(self):
        """
        初始化 GlobalConfig 实例。
        """
        self.devices_config = None  # 全局 DevicesConfig 初始化为 None
        self.resource_configs = {}  # 存储多个 ResourceConfig，键为 resource_name

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

    def get_device_config(self, device_name):
        """根据设备名称获取设备配置"""
        if not self.devices_config:
            return None

        for device in self.devices_config.devices:
            if device.device_name == device_name:
                return device
        return None

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
        从指定目录及其所有子目录中加载名为 "resource_config.json.json" 的资源配置文件。
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

    def get_runtime_configs_for_resource(self, resource_name: str, device_id: str = None) -> RunTimeConfigs | None:
        """
        获取指定资源中已在DeviceConfig中选择的任务的RunTimeConfigs，
        按照DeviceConfig中的任务顺序排列，
        并将资源所在目录（由 source_file 计算得出）传递到 resource_path 中。

        Args:
            resource_name: 资源名称
            device_id: 设备ID，如果提供，则只返回该设备下的任务

        Returns:
            RunTimeConfigs: 包含任务列表和资源路径的配置对象
        """
        resource_config = self.get_resource_config(resource_name)
        if resource_config is None:
            print(f"Resource '{resource_name}' not found.")
            return None

        # 使用有序字典来收集和保存任务，保持DeviceConfig中的顺序
        from collections import OrderedDict
        ordered_tasks = OrderedDict()

        # 从DeviceConfig中获取指定资源的选定任务
        if self.devices_config is not None:
            for device in self.devices_config.devices:
                # 如果提供了device_id，则只处理指定设备
                if device_id is not None and device.device_name != device_id:
                    continue

                device_has_matching_resource = False
                for device_resource in device.resources:
                    if device_resource.resource_name == resource_name and device_resource.enable:
                        device_has_matching_resource = True
                        # 按照设备资源中的任务顺序添加
                        for task_name in device_resource.selected_tasks:
                            if task_name not in ordered_tasks:
                                ordered_tasks[task_name] = None

                # 如果指定了device_id，且找到了匹配的设备和资源，不需要查找其他设备
                if device_id is not None and device_has_matching_resource:
                    break

        # 为每个已选任务创建RunTimeConfig
        runtime_configs = []

        # 从ResourceConfig中获取任务详细信息并创建RunTimeConfig
        for task_name in ordered_tasks:
            task = next((t for t in resource_config.resource_tasks if t.task_name == task_name), None)
            if task:
                pipeline_override = self._process_task_options(resource_config, task, device_id)  # 传入device_id
                runtime_config = RunTimeConfig(
                    task_name=task.task_name,
                    task_entry=task.task_entry,
                    pipeline_override=pipeline_override
                )
                runtime_configs.append(runtime_config)

        # 通过 source_file（包含文件名）计算出资源加载目录
        resource_path = Path(resource_config.source_file).parent if resource_config.source_file else Path()
        return RunTimeConfigs(task_list=runtime_configs, resource_path=resource_path)

    def get_runtime_config_for_task(self, resource_name: str, task_name: str, device_id: str = None) -> Optional[
        RunTimeConfig]:
        """
        获取特定资源中特定任务的 RunTimeConfig。

        Args:
            resource_name: 资源名称
            task_name: 任务名称
            device_id: 设备ID，如果提供，则只使用该设备的选项值
        """
        resource_config = self.get_resource_config(resource_name)
        if resource_config is None:
            raise ValueError(f"Resource '{resource_name}' not found.")

        task = next((t for t in resource_config.resource_tasks if t.task_name == task_name), None)
        if task is None:
            return None

        pipeline_override = self._process_task_options(resource_config, task, device_id)  # 传入device_id
        return RunTimeConfig(
            task_name=task.task_name,
            task_entry=task.task_entry,
            pipeline_override=pipeline_override
        )

    def _process_task_options(self, resource_config: ResourceConfig, task: Task, device_id: str = None) -> Dict[
        str, Any]:
        """
        处理任务的选项，生成 pipeline_override。

        Args:
            resource_config: 资源配置
            task: 任务配置
            device_id: 设备ID，如果提供，则只使用该设备的选项值
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
                # 如果提供了device_id，则只处理指定设备
                if device_id is not None and device.device_name != device_id:
                    continue

                for resource in device.resources:
                    if resource.resource_name == resource_name:
                        device_resources.append(resource)

        # 后续代码保持不变
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
                    # 对于布尔选项，将值转换为实际布尔值
                    bool_value = self._parse_bool_value(option_value)
                    processed_override = self._replace_placeholder(option.pipeline_override, str(option_value),
                                                                   bool_value)
                    merge_dicts(final_pipeline_override, processed_override)

            elif isinstance(option, InputOption):
                if option_value and option.pipeline_override:
                    processed_override = self._replace_placeholder(option.pipeline_override, str(option_value))
                    merge_dicts(final_pipeline_override, processed_override)

        return final_pipeline_override

    def _parse_bool_value(self, value: Any) -> bool:
        """
        将值解析为布尔类型
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', 'y', '1', 'on')
        return bool(value)

    def _replace_placeholder(self, pipeline: Any, value: str, bool_value: bool = None) -> Any:
        """
        替换管道中的占位符。

        参数:
        pipeline: 要处理的管道配置
        value: 用于替换{value}的字符串值
        bool_value: 用于替换{boole}的布尔值，如果未提供则使用value转换
        """
        if bool_value is None:
            bool_value = self._parse_bool_value(value)

        if isinstance(pipeline, dict):
            result = {}
            for k, v in pipeline.items():
                if isinstance(v, str):
                    if v == "{boole}":
                        # 如果值就是{boole}占位符，直接使用布尔值替换
                        result[k] = bool_value
                    elif "{boole}" in v:
                        # 如果字符串包含{boole}，替换为对应的字符串表示
                        result[k] = v.replace("{boole}", str(bool_value).lower())
                    else:
                        # 仅替换{value}占位符
                        result[k] = v.replace("{value}", value)
                elif isinstance(v, dict):
                    # 递归处理嵌套字典
                    result[k] = self._replace_placeholder(v, value, bool_value)
                elif isinstance(v, list):
                    # 处理列表
                    result[k] = [
                        self._replace_placeholder(item, value, bool_value)
                        if isinstance(item, (dict, list))
                        else (
                            bool_value if item == "{boole}"
                            else (
                                item.replace("{boole}", str(bool_value).lower()).replace("{value}", value)
                                if isinstance(item, str)
                                else item
                            )
                        )
                        for item in v
                    ]
                else:
                    # 其他类型原样保留
                    result[k] = v
            return result
        elif isinstance(pipeline, list):
            # 处理列表
            return [self._replace_placeholder(item, value, bool_value) for item in pipeline]
        # 基本类型直接返回
        return pipeline


# 创建全局单例实例
global_config = GlobalConfig()