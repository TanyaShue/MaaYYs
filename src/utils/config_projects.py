@dataclass
class AdbConfig:
    adb_path: str
    adb_address: str

    def to_dict(self):
        return asdict(self)


@dataclass
class ProjectParameter:
    task_name: str
    name: str
    type: str
    value: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Project:
    project_name: str
    program_name: str
    adb_config: AdbConfig
    selected_tasks: List[str]
    project_parameters: List[ProjectParameter]

    def to_dict(self):
        return {
            "project_name": self.project_name,
            "program_name": self.program_name,
            "adb_config": self.adb_config.to_dict(),
            "selected_tasks": self.selected_tasks,
            "project_parameters": [param.to_dict() for param in self.project_parameters]
        }


@dataclass
class Projects:
    projects: List[Project]

    @staticmethod
    def from_json(data: dict) -> 'Projects':
        projects = [
            Project(
                project_name=project['project_name'],
                program_name=project['program_name'],
                adb_config=AdbConfig(
                    adb_path=project['adb_config']['adb_path'],
                    adb_address=project['adb_config']['adb_address']
                ),
                selected_tasks=project['selected_tasks'],
                project_parameters=[
                    ProjectParameter(
                        task_name=param['task_name'],
                        name=param['name'],
                        type=param['type'],
                        value=param['value']
                    ) for param in project['project_parameters']
                ]
            ) for project in data['projects']
        ]
        return Projects(projects=projects)

    def to_dict(self):
        return {
            "projects": [project.to_dict() for project in self.projects]
        }

    def save_to_json(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)


# 示例：从 JSON 文件读取并保存
# with open('projects.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)
#     projects = Projects.from_json(data)
#
# # 修改后保存回 projects.json
# projects.save_to_json('new_projects.json')
