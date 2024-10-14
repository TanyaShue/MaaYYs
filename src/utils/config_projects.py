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
        self.project_run_tasks = None
        self.project_run_option = None
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

    def get_project_run_data(self, programs_json):
        """
        根据项目和程序配置，生成项目的运行数据，包括每个任务的 pipeline_override。
        """
        for program in programs_json.programs:
            if program.program_name == self.program_name:
                project_run_tasks = []
                self.project_run_tasks=program.program_tasks
                self.project_run_option=program.option

                # 遍历项目中的 selected_tasks
                for task_name in self.selected_tasks:
                    # 查找 Program 中对应的任务
                    program_task = next((task for task in program.program_tasks if task.task_name == task_name), None)
                    if not program_task:
                        print(f"Task {task_name} not found in Program {self.program_name}")
                        continue

                    # 处理选项，生成 pipeline_override
                    pipeline_override = self._process_task_option(program_task)

                    # 创建 ProjectRunTask 并添加到列表
                    project_run_task = ProjectRunTask(
                        task_name=program_task.task_name,
                        task_entry=program_task.task_entry,
                        pipeline_override=pipeline_override
                    )
                    project_run_tasks.append(project_run_task)

                # 返回包含所有 ProjectRunTask 的 ProjectRunData
                return ProjectRunData(project_run_tasks=project_run_tasks)
        return None

    def _process_task_option(self, program_task):
        """
        处理项目选项，覆盖程序中的默认任务设置，生成最终的 pipeline_override。
        """
        pipeline_override = {}
        fin_pipeline_override={}

        # 合并字典的辅助函数
        def merge_dicts(dict1, dict2):
            for key, value in dict2.items():
                if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                    merge_dicts(dict1[key], value)  # 递归合并字典
                else:
                    dict1[key] = value

        # 首先从程序中获取对应的选项
        for option in program_task.option:
            # 从默认值中获取于option对应的完整选项
            if self.project_run_option.options[option]:
                for selected_option in self.option.options:
                    if selected_option.option_name==option:
                        if selected_option.option_type == 'select':
                            for a in self.project_run_option.options[option].select:
                                if a.name==selected_option.option_value:
                                    # 只有在找到选中值时才合并
                                    pipeline_override=a.pipeline_override
                        elif selected_option.option_type == 'input':
                            # 替换输入值中的占位符
                            pipeline_override = self._replace_placeholder(
                                self.project_run_option.options[option].input.pipeline_override,
                                selected_option.option_value
                            )

                        elif selected_option.option_type == 'boole':
                            # 处理布尔选项的占位符替换
                            pipeline_override = self._replace_placeholder(
                                self.project_run_option.options[option].boole.pipeline_override,
                                selected_option.option_value
                            )
                merge_dicts(fin_pipeline_override,pipeline_override)
        return fin_pipeline_override

    def _replace_placeholder(self, pipeline, value):
        """
        递归替换 pipeline 中的占位符 {value} 和 {boole}。
        """
        if isinstance(pipeline, dict):
            for key, val in pipeline.items():
                if isinstance(val, str):
                    # 确保 value 是字符串
                    pipeline[key] = val.replace("{value}", str(value)).replace("{boole}", str(value))
                else:
                    # 如果值本身是字典，递归处理
                    pipeline[key] = self._replace_placeholder(val, value)
        return pipeline

class ProjectRunTask:
    def __init__(self, task_name, task_entry, pipeline_override=None):
        self.task_name = task_name
        self.task_entry = task_entry
        self.pipeline_override = pipeline_override or {}

    def __repr__(self):
        return (f"ProjectRunTask(Name: {self.task_name}, "
                f"Entry: {self.task_entry}, "
                f"Pipeline Override: {self.pipeline_override})")


class ProjectRunData:
    def __init__(self, project_run_tasks):
        self.project_run_tasks = project_run_tasks

    def __repr__(self):
        return f"ProjectRunData(Tasks: {self.project_run_tasks})"

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

