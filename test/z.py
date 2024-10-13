import unittest

from src.utils.config_programs import *
from src.utils.config_projects import *


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.projects_json_path = '../assets/config/projects.json'
        self.projects = ProjectsJson.load_from_file(self.projects_json_path)  # 直接加载配置类

        self.programs_json_path = '../assets/config/programs.json'
        self.programs = ProgramsJson.load_from_file(self.programs_json_path)  # 直接加载配置类
        for project in self.projects.projects:
            print( project.adb_config.adb_path )
            print(project.adb_config.adb_address)


if __name__ == '__main__':
    unittest.main()