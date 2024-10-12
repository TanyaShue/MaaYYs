import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Union


@dataclass
class Parameter:
    name: str
    type: str
    value: Union[str, Dict[str, str]]

    def to_dict(self):
        return asdict(self)


@dataclass
class Task:
    task_name: str
    task_entry: Union[str, None]
    parameters: List[Parameter]

    def to_dict(self):
        return {
            "task_name": self.task_name,
            "task_entry": self.task_entry,
            "parameters": [param.to_dict() for param in self.parameters]
        }


@dataclass
class Program:
    program_name: str
    program_tasks: List[Task]

    def to_dict(self):
        return {
            "program_name": self.program_name,
            "program_tasks": [task.to_dict() for task in self.program_tasks]
        }


@dataclass
class Programs:
    programs: List[Program]

    @staticmethod
    def from_json(data: dict) -> 'Programs':
        programs = [
            Program(
                program_name=program['program_name'],
                program_tasks=[
                    Task(
                        task_name=task['task_name'],
                        task_entry=task.get('task_entry'),
                        parameters=[
                            Parameter(
                                name=param['name'],
                                type=param['type'],
                                value=param['value']
                            ) for param in task['parameters']
                        ]
                    ) for task in program['program_tasks']
                ]
            ) for program in data['programs']
        ]
        return Programs(programs=programs)

    def to_dict(self):
        return {
            "programs": [program.to_dict() for program in self.programs]
        }

    def save_to_json(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)


# 示例：从 JSON 文件读取并保存
# with open('programs.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)
#     programs = Programs.from_json(data)
#
# # 修改后保存回 programs.json
# programs.save_to_json('new_programs.json')
