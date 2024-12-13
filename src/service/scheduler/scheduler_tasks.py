# -*- coding: UTF-8 -*-
import logging
import os
from src.service.tasker_service_manager import TaskerServiceManager
from src.utils.config_programs import ProgramsJson
from src.utils.config_projects import ProjectsJson

logger = logging.getLogger(__name__)

# def example_test():
#     """示例测试任务"""
#     logger.info("Executing example test task")


def send_task():
    """定时执行发送任务"""
    resource_path=None
    logger.info("Executing send task task")

    # 从 JSON 文件加载配置
    current_dir = os.getcwd()
    programs_config_path = os.path.join(current_dir, "assets", "config", "programs.json")
    projects_config_path = os.path.join(current_dir, "assets", "config", "projects.json")

    programs = ProgramsJson.load_from_file(programs_config_path)
    projects = ProjectsJson.load_from_file(projects_config_path)

    tasker_service_manager=TaskerServiceManager()

    for project in projects.projects:
        if project.schedule_enabled:
            try:
                for program in programs.programs:
                    if program.program_name==project.program_name:
                        resource_path= program.resource_path
                tasker_service_manager.create_tasker(project.project_name, project,resource_path)

                project_run_data = project.get_project_run_data(programs)

                tasker_service_manager.send_task(project.project_name, project_run_data)
            except Exception as e:
                logger.error(e)
            finally:
                pass
