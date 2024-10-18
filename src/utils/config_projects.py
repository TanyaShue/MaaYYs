import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Union

@dataclass
class AdbConfig:
    adb_path: str
    adb_address: str

    @staticmethod
    def from_json(data: Dict):
        return AdbConfig(
            adb_path=data.get('adb_path', ''),
            adb_address=data.get('adb_address', '')
        )

    def to_json(self):
        return asdict(self)

@dataclass
class Option:
    option_name: str
    option_type: str
    option_value: Union[str, bool, None]

    @staticmethod
    def from_json(option_name: str, data: Dict):
        for key, value in data.items():
            if key in {'select', 'input', 'boole'}:
                return Option(option_name, key, value)
        raise ValueError(f"Unknown option type for {option_name}")

    def to_json(self):
        return {self.option_type: self.option_value}

@dataclass
class ProjectOption:
    options: List[Option] = field(default_factory=list)

    @staticmethod
    def from_json(data: Dict):
        return ProjectOption(
            options=[Option.from_json(name, opt_data) for name, opt_data in data.items()]
        )

    def to_json(self):
        return {opt.option_name: opt.to_json() for opt in self.options}

@dataclass
class ProjectRunTask:
    task_name: str
    task_entry: str
    pipeline_override: Dict = field(default_factory=dict)

    @staticmethod
    def from_json(data: Dict):
        return ProjectRunTask(
            task_name=data['task_name'],
            task_entry=data['task_entry'],
            pipeline_override=data.get('pipeline_override', {})
        )

    def to_json(self):
        return {
            "task_name": self.task_name,
            "task_entry": self.task_entry,
            "pipeline_override": self.pipeline_override
        }

@dataclass
class ProjectRunData:
    project_run_tasks: List[ProjectRunTask]

    @staticmethod
    def from_json(data: Dict):
        return ProjectRunData(
            project_run_tasks=[ProjectRunTask.from_json(task) for task in data['project_run_tasks']]
        )

    def to_json(self):
        return {
            "project_run_tasks": [task.to_json() for task in self.project_run_tasks]
        }

    def __repr__(self):
        return f"ProjectRunData(Tasks: {self.project_run_tasks})"

@dataclass
class Project:
    project_name: str
    program_name: str
    adb_config: AdbConfig
    selected_tasks: List[str]
    option: ProjectOption = field(default_factory=ProjectOption)

    def __init__(self, project_name, program_name, adb_config, selected_tasks, option=None):
        self.project_name = project_name
        self.program_name = program_name
        self.adb_config = adb_config
        self.selected_tasks = selected_tasks
        self.option = option or ProjectOption()
        self.project_run_tasks = None
        self.project_run_option = None

    @staticmethod
    def from_json(data: Dict):
        return Project(
            project_name=data['project_name'],
            program_name=data['program_name'],
            adb_config=AdbConfig.from_json(data['adb_config']),
            selected_tasks=data.get('selected_tasks', []),
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

    # 省略原有的 get_project_run_data 和 get_project_all_run_data 方法
    def get_project_run_data(self, programs_json):
        for program in programs_json.programs:
            if program.program_name == self.program_name:
                project_run_tasks = []
                self.project_run_tasks = program.program_tasks
                self.project_run_option = program.option

                # Iterate over program.program_tasks in order
                for program_task in program.program_tasks:
                    task_name = program_task.task_name
                    if task_name not in self.selected_tasks:
                        continue

                    pipeline_override = self._process_task_option(program_task)

                    project_run_task = ProjectRunTask(
                        task_name=program_task.task_name,
                        task_entry=program_task.task_entry,
                        pipeline_override=pipeline_override
                    )
                    project_run_tasks.append(project_run_task)

                return ProjectRunData(project_run_tasks=project_run_tasks)
        return None

    def get_project_all_run_data(self, programs_json):
        for program in programs_json.programs:
            if program.program_name == self.program_name:
                project_run_tasks = []
                self.project_run_tasks = program.program_tasks
                self.project_run_option = program.option

                # Iterate over program.program_tasks in order
                for program_task in program.program_tasks:
                    task_name = program_task.task_name

                    pipeline_override = self._process_task_option(program_task)

                    project_run_task = ProjectRunTask(
                        task_name=program_task.task_name,
                        task_entry=program_task.task_entry,
                        pipeline_override=pipeline_override
                    )
                    project_run_tasks.append(project_run_task)

                return ProjectRunData(project_run_tasks=project_run_tasks)
        return None
    # 省略原有的 _process_task_option、_get_pipeline_override、_replace_placeholder 和 _replace_boole_value 方法
    def _process_task_option(self, program_task):
        final_pipeline_override = {}

        def merge_dicts(dict1, dict2):
            for key, value in dict2.items():
                if isinstance(value, dict) and isinstance(dict1.get(key), dict):
                    merge_dicts(dict1[key], value)
                else:
                    dict1[key] = value

        for option in program_task.option:
            default_option = self.project_run_option.options.get(option)
            if default_option:
                for selected_option in self.option.options:
                    if selected_option.option_name == option:
                        pipeline_override = self._get_pipeline_override(default_option, selected_option)
                        merge_dicts(final_pipeline_override, pipeline_override)

        return final_pipeline_override

    def _get_pipeline_override(self, default_option, selected_option):
        if selected_option.option_type == 'select':
            return next((item.pipeline_override for item in default_option.select if item.name == selected_option.option_value), {})
        elif selected_option.option_type == 'input':
            return self._replace_placeholder(default_option.input.pipeline_override, selected_option.option_value)
        elif selected_option.option_type == 'boole':
            return self._replace_boole_value(default_option.boole.pipeline_override, selected_option.option_value)
        return {}

    def _replace_placeholder(self, pipeline, value):
        if isinstance(pipeline, dict):
            return {k: (v.replace("{value}", str(value)).replace("{boole}", str(value)) if isinstance(v, str) else self._replace_placeholder(v, value)) for k, v in pipeline.items()}
        return pipeline

    def _replace_boole_value(self, pipeline, value):
        """Recursively find keys in pipeline with value {boole} and replace them with boolean value."""
        if isinstance(pipeline, dict):
            new_pipeline = {}
            for k, v in pipeline.items():
                if v == "{boole}":
                    new_pipeline[k] = value
                elif isinstance(v, dict):
                    new_pipeline[k] = self._replace_boole_value(v, value)
                else:
                    new_pipeline[k] = v
            return new_pipeline
        return pipeline
@dataclass
class ProjectsJson:
    projects: List[Project]

    @staticmethod
    def from_json(data: Dict):
        return ProjectsJson(
            projects=[Project.from_json(p) for p in data.get('projects', [])]
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
