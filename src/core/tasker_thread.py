import os
import queue
import threading
import logging
from src.core.loader import load_custom_actions, action_registry, load_custom_recognizers, recognizer_registry
from src.utils.config_projects import Project, ProjectRunData
from maa.controller import AdbController
from maa.resource import Resource
from maa.tasker import Tasker
from maa.toolkit import Toolkit


class TaskerThread(threading.Thread):
    def __init__(self, project_key: str, project: Project):
        super().__init__()
        self.project_key = project_key
        self.project = project
        self.task_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.tasker = None
        self.controller : AdbController
        self.resource : Resource

    def run(self):
        try:
            self._initialize_resources()
            self._run_task_processing_loop()
        except Exception as e:
            logging.error(f"Error initializing tasker for {self.project_key}: {e}")
        finally:
            self._cleanup()

    def _initialize_resources(self):
        """初始化 Tasker 和相关资源"""
        current_dir = os.getcwd()

        # 初始化工具
        Toolkit.init_option(os.path.join(current_dir, "assets"))

        # 初始化资源和控制器
        self.resource = Resource()
        self.resource.post_path(os.path.join(current_dir, "assets", "resource", "base")).wait()

        self.controller = AdbController(adb_path=self.project.adb_config.adb_path, address=self.project.adb_config.adb_address)
        self.controller.post_connection().wait()

        self.tasker = Tasker()
        self.tasker.bind(self.resource, self.controller)

        # 注册自定义任务
        self._register_custom_modules()

        if not self.tasker.inited:
            raise RuntimeError("Failed to initialize MAA tasker.")

        logging.info(f"Tasker initialized for {self.project_key}")

    def _register_custom_modules(self):
        """注册自定义的 action 和 recognizer"""
        load_custom_actions()
        for action_name, action_instance in action_registry.items():
            self.resource.register_custom_action(action_name, action_instance)

        load_custom_recognizers()
        for recognizer_name, recognizer_instance in recognizer_registry.items():
            self.resource.register_custom_recognition(recognizer_name, recognizer_instance)

    def _run_task_processing_loop(self):
        """任务处理循环"""
        while not self.stop_event.is_set():
            try:
                task = self.task_queue.get(timeout=1)
                self._process_task(task)
            except queue.Empty:
                continue  # 继续等待任务
            except Exception as e:
                logging.error(f"Error processing task for {self.project_key}: {e}")

    def _process_task(self, task):
        """处理任务"""
        if isinstance(task, str):
            self._handle_string_task(task)
        elif isinstance(task, ProjectRunData):
            self._handle_project_run_data_task(task)

    def _handle_string_task(self, task):
        """处理字符串任务"""
        if task == "TERMINATE":
            logging.info(f"Terminating Tasker thread for {self.project_key}")
            self.terminate()  # 设置终止标志
        elif task == "RELOAD_RESOURCES":
            self._reload_resources()
        else:
            logging.warning(f"Unexpected string task received: {task}")

    def _handle_project_run_data_task(self, task):
        """处理 ProjectRunData 任务"""
        logging.info(f"Executing task {task}")
        for project_run_task in task.project_run_tasks:
            logging.info(f"Executing task {project_run_task.task_name} for {self.project_key}")
            self.tasker.post_pipeline(project_run_task.task_entry, project_run_task.pipeline_override)

    def _reload_resources(self):
        """重新加载资源"""
        logging.info(f"Reloading resources for {self.project_key}")
        current_dir = os.getcwd()
        self.resource.post_path(os.path.join(current_dir, "assets", "resource", "base")).wait()
        self.tasker.bind(self.resource, self.controller)
        logging.info(f"Resources reloaded for {self.project_key}")

    def send_task(self, task):
        """发送任务到队列"""
        self.task_queue.put(task)

    def terminate(self):
        """终止线程和清理资源"""
        self.stop_event.set()

    def _cleanup(self):
        """清理资源"""
        logging.info(f"Cleaning up Tasker resources for {self.project_key}")

        if self.tasker:
            try:
                self.tasker.terminate()
            except Exception as e:
                logging.error(f"Error terminating tasker for {self.project_key}: {e}")
        if self.controller:
            try:
                self.controller.__del__()
            except Exception as e:
                logging.error(f"Error terminating controller for {self.project_key}: {e}")
        if self.resource:
            try:
                self.resource.__del__()
            except Exception as e:
                logging.error(f"Error terminating controller for {self.project_key}: {e}")

        logging.info(f"Tasker thread for {self.project_key} has been terminated.")

