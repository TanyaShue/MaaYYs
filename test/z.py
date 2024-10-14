import unittest
from src.utils.config_programs import *
from src.utils.config_projects import *


class MyTestCase(unittest.TestCase):
    def setUp(self):
        # 加载项目和程序配置
        self.projects_json_path = '../assets/config/projects.json'
        self.projects = ProjectsJson.load_from_file(self.projects_json_path)  # 加载项目配置类

        self.programs_json_path = '../assets/config/programs.json'
        self.programs = ProgramsJson.load_from_file(self.programs_json_path)  # 加载程序配置类

    def test_project_run_task_and_options(self):
        # 遍历所有项目，生成项目任务和选项的运行数据
        for project in self.projects.projects:
            print(f"\nProject Name: {project.project_name}, Program Name: {project.program_name}")

            # 获取生成的 ProjectRunData
            project_run_data = project.get_project_run_data(self.programs)

            if project_run_data:
                # 打印任务和其对应的 Pipeline Override
                print("Tasks to Run:")
                for task in project_run_data.project_run_tasks:
                    print(f"  Task Name: {task.task_name}, Task Entry: {task.task_entry}")

                    # 检查并打印每个任务的 Pipeline Override
                    if task.pipeline_override:
                        print(f"    Pipeline Override for {task.task_name}: {task.pipeline_override}")
                    # else:
                        # print(f"    No Pipeline Override for {task.task_name}")
            else:
                print(f"No run data generated for {project.project_name}.")


if __name__ == '__main__':
    unittest.main()
