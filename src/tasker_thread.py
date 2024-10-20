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

    def run(self):
        Toolkit.init_option("../assets")
        resource = Resource()
        resource.post_path("../assets/resource/base").wait()

        controller = AdbController(adb_path=self.project.adb_config.adb_path, address=self.project.adb_config.adb_address)
        controller.post_connection().wait()

        tasker = Tasker()
        tasker.bind(resource, controller)

        # 注册自定义任务
        load_custom_actions("../src/custom_actions")
        for action_name, action_instance in action_registry.items():
            resource.register_custom_action(action_name, action_instance)

        load_custom_recognizers("../src/custom_recognition")
        for recognizer_name, recognizer_instance in recognizer_registry.items():
            resource.register_custom_recognition(recognizer_name, recognizer_instance)

        if not tasker.inited:
            logging.error("Failed to init MAA in thread.")
            return

        logging.info(f"Tasker initialized for {self.project_key}")

        while not self.stop_event.is_set():
            try:

                task = self.task_queue.get(timeout=1)
                if isinstance(task, str):
                    self.handle_string_task(task, resource, tasker, controller)
                elif isinstance(task, ProjectRunData):
                    self.handle_project_run_data_task(task, tasker)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Exception occurred: {e}")

    def handle_string_task(self, task, resource, tasker, controller):
        if task == "TERMINATE":
            logging.info(f"Terminating Tasker thread for {self.project_key}")
            self.stop_event.set()
        elif task == "RELOAD_RESOURCES":
            logging.info(f"Reloading resources for {self.project_key}")
            resource.post_path("../assets/resource/base").wait()
            tasker.bind(resource, controller)
            logging.info(f"Resource reloaded for {self.project_key}")
        else:
            logging.warning(f"Unexpected string task received: {task}")

    def handle_project_run_data_task(self, task, tasker):
        logging.info(f"Executing task {task}")
        for project_run_task in task.project_run_tasks:
            logging.info(f"Executing task {project_run_task.task_name} for {self.project_key}")
            tasker.post_pipeline(project_run_task.task_entry, project_run_task.pipeline_override).wait()

    def send_task(self, task):
        self.task_queue.put(task)

    def terminate(self):
        self.stop_event.set()
