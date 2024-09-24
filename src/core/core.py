from maa.context import Context
from maa.resource import Resource
from maa.controller import AdbController
from maa.tasker import Tasker
from maa.toolkit import Toolkit
from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction

from src.config.config_models import TaskProject
import logging


class TaskProjectManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TaskProjectManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.tasker_cache = {}  # 初始化 tasker_cache
        return cls._instance

    # def __init__(self):
    #     # 用于存储 adb_address + adb_port 组合 和 tasker 的映射
    #     self.tasker_cache = {}

    def _get_project_key(self, p: TaskProject) -> str:
        """
        根据 adb_address 和 adb_port 生成唯一的缓存键。
        """
        adb_address = p.adb_config.get("adb_address")
        adb_port = p.adb_config.get("adb_port")
        project_key = f"{adb_address}:{adb_port}"
        print(f"Generated project key: {project_key}")
        return project_key

    def _initialize_tasker(self, p: TaskProject) -> Tasker:
        """
        初始化 Tasker 实例并与资源和控制器绑定。
        """
        user_path = "../assets"
        Toolkit.init_option(user_path)

        resource = Resource()
        res_job = resource.post_path("../assets/resource/base")
        res_job.wait()

        controller = AdbController(
            adb_path=p.adb_config.get("adb_address"),
            address=p.adb_config.get("adb_port")
        )
        controller.post_connection().wait()

        tasker = Tasker()
        tasker.bind(resource, controller)

        if not tasker.inited:
            print("Failed to init MAA.")
            raise RuntimeError("Failed to init MAA.")

        return tasker

    def task_manager_connect(self, p: TaskProject) -> Tasker:
        """
        获取与项目对应的 Tasker，如果缓存中没有则创建并缓存。
        """
        project_key = self._get_project_key(p)

        # 检查缓存
        if project_key in self.tasker_cache:
            print(f"Returning cached Tasker instance for {project_key}")
            return self.tasker_cache[project_key]

        try:
            # 初始化 Tasker 并缓存
            tasker = self._initialize_tasker(p)
            self.tasker_cache[project_key] = tasker
            print(f"Cached new Tasker instance for {project_key}")
            return tasker
        except Exception as e:
            print(f"Error initializing Tasker for {project_key}: {e}")
            raise

    def get_tasker(self, p: TaskProject) -> Tasker:
        """
        通过 adb_address 和 adb_port 获取对应的 Tasker，若不存在则返回 None。
        """
        project_key = self._get_project_key(p)
        print(f"Looking for Tasker instance in cache for {project_key}")
        return self.tasker_cache.get(project_key)
