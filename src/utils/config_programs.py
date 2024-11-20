import json

class InputOption:
    def __init__(self, name, default, pipeline_override=None):
        self.name = name
        self.default = default
        self.pipeline_override = pipeline_override or {}

    @staticmethod
    def from_json(data):
        return InputOption(
            name=data['name'],
            default=data['default'],
            pipeline_override=data.get('pipeline_override', {})
        )

    def to_json(self):
        return {
            "name": self.name,
            "default": self.default,
            "pipeline_override": self.pipeline_override
        }

class SelectOption:
    def __init__(self, name, pipeline_override=None):
        self.name = name
        self.pipeline_override = pipeline_override or {}

    @staticmethod
    def from_json(data):
        return SelectOption(
            name=data['name'],
            pipeline_override=data.get('pipeline_override', {})
        )

    def to_json(self):
        return {
            "name": self.name,
            "pipeline_override": self.pipeline_override
        }

class BooleOption:
    def __init__(self, default=False, pipeline_override=None):
        self.default = default
        self.pipeline_override = pipeline_override or {}

    @staticmethod
    def from_json(data):
        return BooleOption(
            default=data.get('default', False),
            pipeline_override=data.get('pipeline_override', {})
        )

    def to_json(self):
        return {
            "default": self.default,
            "pipeline_override": self.pipeline_override
        }




class TaskOption:
    def __init__(self, option_type=None, select=None, input=None, boole=None):
        self.type = option_type
        self.select = [SelectOption.from_json(s) for s in select] if select else []
        self.input = InputOption.from_json(input) if input else None
        self.boole = BooleOption.from_json(boole) if boole else None

    @staticmethod
    def from_json(data):
        if 'select' in data:
            return TaskOption(
                option_type='select',
                select=data.get('select', [])
            )
        elif 'input' in data:
            return TaskOption(
                option_type='input',
                input=data.get('input')
            )
        elif 'boole' in data:
            return TaskOption(
                option_type='boole',
                boole=data.get('boole')
            )
        return TaskOption()

    def to_json(self):
        if self.type == 'select':
            return {
                "select": [s.to_json() for s in self.select],
                "type": self.type
            }
        elif self.type == 'input':
            return {
                "input": self.input.to_json() if self.input else None,
                "type": self.type
            }
        elif self.type == 'boole':
            return {
                "boole": self.boole.to_json() if self.boole else None,
                "type": self.type
            }
        return {}

class Task:
    def __init__(self, task_name, task_entry=None, option=None):
        self.task_name = task_name
        self.task_entry = task_entry
        self.option = option or []

    @staticmethod
    def from_json(data):
        return Task(
            task_name=data['task_name'],
            task_entry=data.get('task_entry'),
            option=data.get('option', [])
        )

    def to_json(self):
        return {
            "task_name": self.task_name,
            "task_entry": self.task_entry,
            "option": self.option
        }


class ProgramOption:
    def __init__(self, options=None):
        self.options = {key: TaskOption.from_json(value) for key, value in options.items()} if options else {}

    @staticmethod
    def from_json(data):
        return ProgramOption(
            options=data
        )

    def to_json(self):
        return {key: value.to_json() for key, value in self.options.items()}

class Program:
    def __init__(self, program_name, program_icon,program_tasks=None, option=None):
        self.program_name = program_name
        self.program_icon=program_icon
        self.program_tasks = [Task.from_json(t) for t in program_tasks] if program_tasks else []
        self.option = ProgramOption.from_json(option) if option else None

    @staticmethod
    def from_json(data):
        return Program(
            program_name=data['program_name'],
            program_icon=data['program_icon'],
            program_tasks=data.get('program_tasks', []),
            option=data.get('option')
        )

    def to_json(self):
        return {
            "program_name": self.program_name,
            "program_icon": self.program_icon,
            "program_tasks": [task.to_json() for task in self.program_tasks],
            "option": self.option.to_json() if self.option else None
        }

    # 通过名字获取任务
    def get_task_by_name(self, task_name):
        for task in self.program_tasks:
            if task.task_name == task_name:
                return task
        return None

class ProgramsJson:
    def __init__(self, programs=None):
        self.programs = [Program.from_json(p) for p in programs] if programs else []

    @staticmethod
    def from_json(data):
        return ProgramsJson(
            programs=data.get('programs', [])
        )

    def to_json(self):
        return {
            "programs": [program.to_json() for program in self.programs]
        }
    # 通过名字获取程序
    def get_program_by_name(self, program_name):
        for program in self.programs:
            if program.program_name == program_name:
                return program
        return None

    @staticmethod
    def load_from_file(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return ProgramsJson.from_json(data)

    def save_to_file(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_json(), f, ensure_ascii=False, indent=4)
