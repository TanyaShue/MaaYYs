# app/models/resource.py
from app.models.config.resource_config import ResourceConfig, Option, SelectOption, BoolOption, InputOption, Task, \
    Choice
from app.models.config.device_config import Resource as DeviceResource, OptionConfig
from app.models.config.global_config import GlobalConfig


class Resource:
    def __init__(self, resource_config: ResourceConfig, device_resource: DeviceResource = None):
        self.resource_config = resource_config
        self.device_resource = device_resource

        self.name = resource_config.resource_name
        self.version = resource_config.resource_version
        self.author = resource_config.resource_author
        self.description = resource_config.resource_description
        self.icon = resource_config.resource_icon

        # If a device_resource is provided, this resource is associated with a device
        self.enabled = True if device_resource else False

    @property
    def tasks(self):
        return self.resource_config.resource_tasks

    @property
    def options(self):
        return self.resource_config.options

    @property
    def selected_tasks(self):
        if self.device_resource:
            return self.device_resource.selected_tasks
        return []

    @property
    def device_options(self):
        if self.device_resource:
            return self.device_resource.options
        return []

    def get_task_by_name(self, task_name):
        for task in self.tasks:
            if task.task_name == task_name:
                return task
        return None

    def get_option_by_name(self, option_name):
        for option in self.options:
            if option.name == option_name:
                return option
        return None

    def get_device_option_by_name(self, option_name):
        if not self.device_resource:
            return None

        for option in self.device_options:
            if option.option_name == option_name:
                return option
        return None

    @classmethod
    def get_all_resources(cls):
        """Get all resources from global config"""
        global_config = GlobalConfig()
        try:
            resource_configs = global_config.get_all_resource_configs()
            return [cls(resource_config) for resource_config in resource_configs]
        except Exception:
            # If resource configs are not loaded, return sample resources
            return cls.get_sample_resources()

    @classmethod
    def get_device_resources(cls, device_resources):
        """Convert device-specific resources to Resource objects"""
        global_config = GlobalConfig()
        resources = []

        for device_resource in device_resources:
            try:
                # Find the corresponding resource config
                resource_config = global_config.get_resource_config(device_resource.resource_name)
                if resource_config:
                    resources.append(cls(resource_config, device_resource))
            except Exception:
                # Skip if resource config is not found
                pass

        return resources

    @classmethod
    def get_sample_resources(cls):
        """Fallback method for sample resources when no config is available"""
        from app.models.config.resource_config import ResourceConfig, Task, SelectOption, BoolOption, InputOption, \
            Choice

        # Create sample resource configs
        resource1 = ResourceConfig(
            resource_name="战双软件件",
            resource_version="1.0.0",
            resource_author="Maa",
            resource_description="战双帕弥什自动化脚本",
            resource_icon="/icons/apps_icons/R.png",
            resource_tasks=[
                Task(task_name="打开游戏", task_entry="打开游戏", option=["选择区服"]),
                Task(task_name="自动战斗", task_entry="自动战斗", option=["战斗难度", "每日战斗次数"])
            ],
            options=[
                SelectOption(
                    name="战斗难度",
                    type="select",
                    default="普通",
                    choices=[
                        Choice(name="简单", value="简单"),
                        Choice(name="普通", value="普通"),
                        Choice(name="困难", value="困难")
                    ],
                    pipeline_override={}
                ),
                InputOption(
                    name="每日战斗次数",
                    type="input",
                    default="10",
                    pipeline_override={}
                ),
                BoolOption(
                    name="自动使用体力药",
                    type="boole",
                    default=False,
                    pipeline_override={}
                ),
                BoolOption(
                    name="启用自动战斗",
                    type="boole",
                    default=True,
                    pipeline_override={}
                )
            ]
        )

        resource2 = ResourceConfig(
            resource_name="阴阳师",
            resource_version="1.0.0",
            resource_author="Maa",
            resource_description="阴阳师自动化脚本",
            resource_icon="/icons/apps_icons/R.png",
            resource_tasks=[
                Task(task_name="打开游戏", task_entry="打开游戏", option=["选择区服"]),
                Task(task_name="自动御魂", task_entry="自动御魂", option=["副本选择"]),
                Task(task_name="接收礼物", task_entry="接收礼物", option=[]),
                Task(task_name="自动接受邀请", task_entry="自动接受邀请", option=[])
            ],
            options=[
                SelectOption(
                    name="选择区服",
                    type="select",
                    default="官服",
                    choices=[
                        Choice(name="官服", value="官服"),
                        Choice(name="渠道服", value="渠道服")
                    ],
                    pipeline_override={}
                ),
                SelectOption(
                    name="副本选择",
                    type="select",
                    default="御魂",
                    choices=[
                        Choice(name="御魂", value="御魂"),
                        Choice(name="觉醒", value="觉醒"),
                        Choice(name="探索", value="探索")
                    ],
                    pipeline_override={}
                ),
                InputOption(
                    name="运行时间(分钟)",
                    type="input",
                    default="60",
                    pipeline_override={}
                ),
                BoolOption(
                    name="自动接收礼物",
                    type="boole",
                    default=True,
                    pipeline_override={}
                ),
                BoolOption(
                    name="自动接受邀请",
                    type="boole",
                    default=True,
                    pipeline_override={}
                )
            ]
        )

        # Create Resource objects
        return [cls(resource1), cls(resource2)]


# Legacy support for old UI
class ResourceSetting:
    def __init__(self, name, setting_type, value, options=None):
        self.name = name
        self.type = setting_type  # checkbox, combobox, input
        self.value = value
        self.options = options or []


class SettingGroup:
    def __init__(self, name, settings=None):
        self.name = name
        self.settings = settings or []