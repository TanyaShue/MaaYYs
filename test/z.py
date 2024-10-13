import unittest
from src.utils.config_programs import *
from src.utils.config_projects import *


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.projects_json_path = '../assets/config/projects.json'
        self.projects = ProjectsJson.load_from_file(self.projects_json_path)  # 加载项目配置类

        self.programs_json_path = '../assets/config/programs.json'
        self.programs = ProgramsJson.load_from_file(self.programs_json_path)  # 加载程序配置类

        for program in self.programs.programs:
            print(f"Program Name: {program.program_name}")
            if program.option:
                # 遍历 program 的所有 option 并打印其 type 和相关参数
                for key, option in program.option.options.items():
                    print(f"Option Key: {key}, Option Type: {option.type}")

                    # 根据 option 的类型打印相应的参数
                    if option.type == 'input' and option.input:
                        print(f"Input Option: name={option.input.name}, default={option.input.default}, "
                              f"pipeline_override={option.input.pipeline_override}")

                    elif option.type == 'select' and option.select:
                        for select_option in option.select:
                            print(f"Select Option: name={select_option.name}, "
                                  f"pipeline_override={select_option.pipeline_override}")

                    elif option.type == 'boole':
                        print(f"Boolean Option: {option.boole}")
                    else:
                        print("Unknown option type or missing attributes.")


if __name__ == '__main__':
    unittest.main()
