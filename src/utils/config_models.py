import json
from typing import List, Dict, Any

class Task:
    def __init__(self, task_name: str, entry: str = None, parameters: Dict[str, Any] = None):
        self.task_name = task_name
        self.entry = entry
        self.parameters = parameters if parameters else {}

class Program:
    def __init__(self, program_name: str, tasks: List[Task]):
        self.program_name = program_name
        self.tasks = tasks


    def get_entry_by_selected_task(self, selected_task_name: str):
        """
        根据选中的任务名称返回其对应的 entry 值。

        :param selected_task_name: 选中的任务名称
        :return: 对应任务的 entry 值，若找不到返回 None
        """
        for task in self.tasks:
            if task.task_name == selected_task_name:
                return task.entry
        return None

class SelectedTask:
    def __init__(self, task_name: str, is_selected: bool, task_parameters: Dict[str, Any]):
        self.task_name = task_name
        self.is_selected = is_selected
        self.task_parameters = task_parameters




class TaskProject:
    def __init__(self, program_name: str, adb_config: Dict[str, Any], selected_tasks: List[SelectedTask]):
        self.program_name = program_name
        self.adb_config = adb_config
        self.selected_tasks = selected_tasks

    def get_selected_task_by_name(self,selected_task_name:str):
        for task in self.selected_tasks:
            if task.task_name==selected_task_name:
                return task
        return None

    def get_selected_tasks(self):
        return [task for task in self.selected_tasks if task.is_selected]


class Config:
    json_path = None

    def __init__(self, programs: List[Program], task_projects: Dict[str, TaskProject]):
        self.programs = programs
        self.task_projects = task_projects

    def get_program_by_name(self,program_name: str):
        for program in self.programs:
            if program.program_name == program_name:
                return program
        return None

    @classmethod
    def from_json(cls):
        if cls.json_path is None:
            raise ValueError("json_path must be set before calling from_json.")

        with open(cls.json_path, 'r', encoding='utf-8') as f:
            json_str = f.read()

        data = json.loads(json_str)

        programs = [
            Program(
                program_name=prog['program_name'],
                tasks=[Task(task['task_name'], task.get('entry'), task.get('parameters')) for task in prog['tasks']]
            ) for prog in data['programs']
        ]

        task_projects = {
            project_name: TaskProject(
                program_name=project['program_name'],
                adb_config=project['adb_config'],
                selected_tasks=[
                    SelectedTask(
                        task_name=task['task_name'],
                        is_selected=task['is_selected'],
                        task_parameters=task.get('task_parameters', {})
                    ) for task in project['selected_tasks']
                ]
            ) for project_name, project in data['task_projects'].items()
        }

        return cls(programs, task_projects)

    def save_to_json(self):
        if Config.json_path is None:
            raise ValueError("json_path must be set before calling save_to_json.")

        data = {
            "programs": [
                {
                    "program_name": program.program_name,
                    "tasks": [
                        {
                            "task_name": task.task_name,
                            "entry": task.entry,
                            "parameters": task.parameters
                        } for task in program.tasks
                    ]
                } for program in self.programs
            ],
            "task_projects": {
                project_name: {
                    "program_name": project.program_name,
                    "adb_config": project.adb_config,
                    "selected_tasks": [
                        {
                            "task_name": task.task_name,
                            "is_selected": task.is_selected,
                            "task_parameters": task.task_parameters
                        } for task in project.selected_tasks
                    ]
                } for project_name, project in self.task_projects.items()
            }
        }

        with open(Config.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"保存到{Config.json_path}")

