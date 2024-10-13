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

class Option:
    def __init__(self, option_name, option_type, option_value):
        self.option_name = option_name  # 选项名称
        self.option_type = option_type  # 选项类型 (select, input, boole)
        self.option_value = option_value  # 选项值

    @staticmethod
    def from_json(option_name, data):
        # 根据 data 判断 option 的类型并初始化
        if 'select' in data:
            return Option(option_name, 'select', data['select'])
        elif 'input' in data:
            return Option(option_name, 'input', data['input'])
        elif 'boole' in data:
            return Option(option_name, 'boole', data['boole'])
        else:
            raise ValueError(f"Unknown option type for {option_name}")

    def to_json(self):
        return {self.option_type: self.option_value}


class ProjectOption:
    def __init__(self, options=None):
        self.options = options or []  # 选项列表

    @staticmethod
    def from_json(data):
        options = []
        for option_name, option_data in data.items():
            option = Option.from_json(option_name, option_data)
            options.append(option)
        return ProjectOption(options=options)

    def to_json(self):
        result = {}
        for option in self.options:
            result[option.option_name] = option.to_json()
        return result


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

