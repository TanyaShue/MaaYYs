import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Literal, Optional

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
    pipeline_override: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # PipelineOverride 直接使用 Dict[str, Dict[str, Any]]

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
    resource_update_service:str
    resource_icon: str
    resource_tasks: List[Task] = field(default_factory=list)
    options: List[Option] = field(default_factory=list)
    source_file: str = ""  # 用于记录加载的文件路径，但不保存到输出 JSON 中

    @classmethod
    def from_json_file(cls, file_path: str) -> 'ResourceConfig':
        """Load ResourceConfig from a JSON file and record the source file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        config = cls.from_dict(json_data)
        config.source_file = file_path  # 记录来源文件路径
        return config

    def to_json_file(self, file_path: Optional[str] = None, indent=4):
        """Export ResourceConfig to a JSON file.

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
                # 排除 choices 字段，避免重复赋值
                options.append(
                    SelectOption(**{k: v for k, v in option_data.items() if k != 'choices'}, choices=choices)
                )
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
            resource_update_service=data.get('resource_update_service', ''),
            resource_description=data.get('resource_description', ''),
            resource_icon=data.get('resource_icon', ''),
            resource_tasks=tasks,
            options=options
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ResourceConfig object to a dictionary, excluding source_file."""
        return {
            "resource_name": self.resource_name,
            "resource_version": self.resource_version,
            "resource_author": self.resource_author,
            "resource_update_service": self.resource_update_service,
            "resource_description": self.resource_description,
            "resource_icon": self.resource_icon,
            "resource_tasks": [task.__dict__ for task in self.resource_tasks],
            "options": [option_to_dict(option) for option in self.options],
        }

def option_to_dict(option: Option) -> Dict[str, Any]:
    """Helper function to convert Option and its subclasses to dictionary."""
    option_dict = option.__dict__.copy()
    if isinstance(option, SelectOption):
        option_dict['choices'] = [choice.__dict__ for choice in option.choices]
    return option_dict
