import json

class AdbConfig:
    def __init__(self, adb_path, adb_address):
        self.adb_path = adb_path
        self.adb_address = adb_address

    @staticmethod
    def from_json(data):
        return AdbConfig(
            adb_path=data['adb_path'],
            adb_address=data['adb_address']
        )

    def to_json(self):
        return {
            "adb_path": self.adb_path,
            "adb_address": self.adb_address
        }

class ProjectOption:
    def __init__(self, select=None, input=None):
        self.select = select or {}
        self.input = input or {}

    @staticmethod
    def from_json(data):
        select = {k: v['select'] for k, v in data.items() if 'select' in v}
        input = {k: v['input'] for k, v in data.items() if 'input' in v}
        return ProjectOption(select=select, input=input)

    def to_json(self):
        options = {}
        for k, v in self.select.items():
            options[k] = {"select": v}
        for k, v in self.input.items():
            options[k] = {"input": v}
        return options

class Project:
    def __init__(self, project_name, program_name, adb_config, selected_tasks, option=None):
        self.project_name = project_name
        self.program_name = program_name
        self.adb_config = adb_config
        self.selected_tasks = selected_tasks
        self.option = option or ProjectOption()

    @staticmethod
    def from_json(data):
        return Project(
            project_name=data['project_name'],
            program_name=data['program_name'],
            adb_config=AdbConfig.from_json(data['adb_config']),
            selected_tasks=data['selected_tasks'],
            option=ProjectOption.from_json(data.get('option', {}))
        )

    def to_json(self):
        return {
            "project_name": self.project_name,
            "program_name": self.program_name,
            "adb_config": self.adb_config.to_json(),
            "selected_tasks": self.selected_tasks,
            "option": self.option.to_json()
        }

class ProjectsJson:
    def __init__(self, projects=None):
        self.projects = [Project.from_json(p) for p in projects] if projects else []

    @staticmethod
    def from_json(data):
        return ProjectsJson(
            projects=data.get('projects', [])
        )

    def to_json(self):
        return {
            "projects": [project.to_json() for project in self.projects]
        }

    @staticmethod
    def load_from_file(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return ProjectsJson.from_json(data)

    def save_to_file(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_json(), f, ensure_ascii=False, indent=4)
