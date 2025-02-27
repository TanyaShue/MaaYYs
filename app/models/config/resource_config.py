import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, ClassVar, Literal


@dataclass
class Choice:
    """Choice option for select type."""
    name: str
    value: str

@dataclass
class Option:
    """Base class for options."""
    name: str
    type: str
    default: Any
    pipeline_override: Dict[str, Dict[str, Any]] = field(default_factory=dict) # PipelineOverride 直接使用 Dict[str, Dict[str, Any]]

@dataclass
class SelectOption(Option):
    """Select option dataclass."""
    type: Literal["select"] = "select"
    default: str = ""
    choices: List[Choice] = field(default_factory=list)

@dataclass
class BoolOption(Option):
    """Boolean option dataclass."""
    type: Literal["boole"] = "boole"
    default: bool = False

@dataclass
class InputOption(Option):
    """Input option dataclass."""
    type: Literal["input"] = "input"
    default: str = ""

@dataclass
class Task:
    """Resource task dataclass."""
    task_name: str
    task_entry: str
    option: List[str] = field(default_factory=list)

@dataclass
class ResourceConfig:
    """Main resource configuration dataclass."""
    resource_name: str
    resource_version: str
    resource_author: str
    resource_description: str
    resource_icon: str
    resource_tasks: List[Task] = field(default_factory=list)
    options: List[Option] = field(default_factory=list)

    @classmethod
    def from_json_file(cls, file_path: str) -> 'ResourceConfig':
        """Load ResourceConfig from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return cls.from_dict(json_data)

    def to_json_file(self, file_path: str, indent=4):
        """Export ResourceConfig to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceConfig':
        """Create ResourceConfig object from a dictionary."""
        tasks_data = data.get('resource_tasks', [])
        options_data = data.get('options', [])

        tasks = [Task(**task_data) for task_data in tasks_data]
        options = []
        for option_data in options_data:
            option_type = option_data.get('type')
            if option_type == 'select':
                choices_data = option_data.get('choices', [])
                choices = [Choice(**choice_data) for choice_data in choices_data]
                # 修正后的代码，避免重复赋值 choices
                options.append(
                    SelectOption(**{k: v for k, v in option_data.items() if k != 'choices'}, choices=choices))
            elif option_type == 'boole':
                options.append(BoolOption(**option_data))
            elif option_type == 'input':
                options.append(InputOption(**option_data))
            else:
                options.append(Option(**option_data))  # Fallback to base Option if type is unknown

        return ResourceConfig(
            resource_name=data.get('resource_name', ''),
            resource_version=data.get('resource_version', ''),
            resource_author=data.get('resource_author', ''),
            resource_description=data.get('resource_description', ''),
            resource_icon=data.get('resource_icon', ''),
            resource_tasks=tasks,
            options=options
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ResourceConfig object to a dictionary."""
        return {
            "resource_name": self.resource_name,
            "resource_version": self.resource_version,
            "resource_author": self.resource_author,
            "resource_description": self.resource_description,
            "resource_icon": self.resource_icon,
            "resource_tasks": [task.__dict__ for task in self.resource_tasks],
            "options": [option_to_dict(option) for option in self.options],
        }

def option_to_dict(option: Option) -> Dict[str, Any]:
    """Helper function to convert Option and its subclasses to dictionary."""
    option_dict = option.__dict__
    if isinstance(option, SelectOption):
        option_dict['choices'] = [choice.__dict__ for choice in option.choices]
    # PipelineOverride 不需要特殊处理，因为它已经是字典了
    return option_dict


# Example Usage:
#
# if __name__ == "__main__":
#     config_json = """
#     {
#       "resource_name": "阴阳师",
#       "resource_version": "1.0.0",
#       "resource_author": "Maa",
#       "resource_description": "阴阳师自动化脚本",
#       "resource_icon": "/icons/apps_icons/R.png",
#       "resource_tasks": [
#         {
#           "task_name": "打开游戏",
#           "task_entry": "打开游戏",
#           "option": [
#             "选择区服"
#           ]
#         },
#         {
#           "task_name": "自动地鬼",
#           "task_entry": "自动地鬼",
#           "option": [
#             "地鬼分组预设",
#             "地鬼队伍预设"
#           ]
#         }
#       ],
#       "options": [
#         {
#           "name": "选择区服",
#           "type": "select",
#           "default": "官服",
#           "choices": [
#             {
#               "name": "官服",
#               "value": "官服"
#             },
#             {
#               "name": "官网下载版",
#               "value": "官网下载版"
#             }
#           ],
#           "pipeline_override": {
#             "官服": {},
#             "官网下载版": {
#               "打开阴阳师": {
#                 "package": "com.netease.onmyoji/.tag0"
#               }
#             }
#           }
#         },
#         {
#           "name": "是否启动自动轮换",
#           "type": "boole",
#           "default": false,
#           "pipeline_override": {
#             "探索_悬赏_自动轮换": {
#               "enabled": "{boole}"
#             }
#           }
#         },
#         {
#           "name": "悬赏封印分组预设",
#           "type": "input",
#           "default": "默认分组",
#           "pipeline_override": {
#             "装备日常清杂预设": {
#               "custom_action_param": {
#                 "group_name": "{value}"
#               }
#             }
#           }
#         }
#       ]
#     }
#     """
#
#     config_dict = json.loads(config_json)
#     config_obj = ResourceConfig.from_dict(config_dict)
#
#     print("Loaded ResourceConfig Object (Simplified and PipelineOverride Simplified Further):")
#     print(config_obj)
#
#     # Example: Accessing task and option data (same as before)
#     print("\nExample Data Access:")
#     for task in config_obj.resource_tasks:
#         print(f"Task Name: {task.task_name}, Entry: {task.task_entry}, Options: {task.option}")
#
#     for option in config_obj.options:
#         print(f"\nOption Name: {option.name}, Type: {option.type}, Default: {option.default}")
#         if isinstance(option, SelectOption):
#             print("  Choices:")
#             for choice in option.choices:
#                 print(f"    - Name: {choice.name}, Value: {choice.value}")
#         if option.pipeline_override:
#              print(f"  Pipeline Override: {option.pipeline_override}")
#
#     # Example: Exporting to JSON (same as before)
#     config_obj.to_json_file("yys_config_dataclass_simplified_pipelineoverride_further_simplified.json")
#     print("\nConfiguration exported to yys_config_dataclass_simplified_pipelineoverride_further_simplified.json")
#
#     # Example: Loading from JSON file (same as before)
#     loaded_config = ResourceConfig.from_json_file("yys_config_dataclass_simplified_pipelineoverride_further_simplified.json")
#     print("\nLoaded from JSON File:")
#     print(loaded_config)