from maa.context import Context
from maa.resource import Resource
from maa.controller import AdbController
from maa.tasker import Tasker
from maa.toolkit import Toolkit
from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction

from src.config.config_models import TaskProject



class TaskProjectManager:
    def __init__(self):
        # 用于存储 adb_address + adb_port 组合 和 tasker 的映射
        self.tasker_cache = {}

    def _get_project_key(self, p: TaskProject):
        """
        根据 adb_address 和 adb_port 生成唯一的缓存键。
        """
        adb_address = p.adb_config.get("adb_address")
        adb_port = p.adb_config.get("adb_port")
        project_key = f"{adb_address}:{adb_port}"
        print(f"Generated project key: {project_key}")  # 增加调试日志
        return project_key

    def task_manager_connect(self, p: TaskProject):
        # 生成唯一的缓存键
        project_key = self._get_project_key(p)

        if project_key in self.tasker_cache:
            # 如果已经有该 adb_address + adb_port 对应的 tasker，直接返回
            print(f"---- Returning cached Tasker instance for {project_key} ----")
            return self.tasker_cache[project_key]

        user_path = "../assets"
        Toolkit.init_option(user_path)

        print(p.adb_config.get("adb_address"), p.adb_config.get("adb_port"))
        resource = Resource()
        res_job = resource.post_path("../assets/resource/base")
        res_job.wait()

        if not p:
            print("No ADB device found.")

        controller = AdbController(
            adb_path=p.adb_config.get("adb_address"),
            address=p.adb_config.get("adb_port")
        )
        controller.post_connection().wait()
        tasker = Tasker()
        tasker.bind(resource, controller)

        if not tasker.inited:
            print("Failed to init MAA.")
            exit()

        # 缓存 tasker 实例
        self.tasker_cache[project_key] = tasker
        print(f"---- Cached new Tasker instance for {project_key} ----")

        return tasker

    def get_tasker(self, p: TaskProject):
        """
        通过 project 的 adb_address 和 adb_port 获取对应的 Tasker，
        如果不存在则返回 None。
        """
        project_key = self._get_project_key(p)
        print(f"Looking for Tasker instance in cache for {project_key}")  # 增加调试日志
        return self.tasker_cache.get(project_key, None)




