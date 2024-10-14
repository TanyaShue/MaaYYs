import logging
import multiprocessing
import threading
import time
from typing import Dict, Union

from maa.controller import AdbController
from maa.resource import Resource
from maa.tasker import Tasker
from maa.toolkit import Toolkit

from src.core.loader import load_custom_actions, action_registry, load_custom_recognizers, recognizer_registry
from src.utils.config_projects import Project, ProjectRunData


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def _get_project_key(p: Project) -> str:
    return f"{p.adb_config.adb_path}:{p.adb_config.adb_address}"


class TaskerProcess:
    """
    单独封装Tasker进程及其队列，方便管理。
    """
    def __init__(self, project_key: str, project: Project):
        self.project_key = project_key
        self.project = project
        self.task_queue = multiprocessing.Queue()
        self.log_queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=self._tasker_process)
        self.process.start()
        logging.info(f"Started Tasker process for {project_key}")

    def _tasker_process(self):
        """
        Tasker进程的具体执行逻辑，运行在独立的子进程中。
        """
        def log_to_queue(message: str):
            self.log_queue.put(message)

        log_to_queue(f"Initializing Tasker for {self.project.adb_config.adb_path}:{self.project.adb_config.adb_address}")
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
            log_to_queue("Failed to init MAA in process.")
            raise RuntimeError("Failed to init MAA in process.")

        log_to_queue(f"Tasker initialized for {self.project_key}")

        # 示例任务执行
        # tasker.post_pipeline("打开游戏").wait()

        # 任务循环

        while True:
            task: Union[str, ProjectRunData] = self.task_queue.get()
            if isinstance(task, str) and task == "TERMINATE":
                log_to_queue(f"Terminating Tasker process for {self.project_key}")
                break

            if isinstance(task, ProjectRunData):
                log_to_queue(f"Executing task {task}")
                for project_run_task in task.project_run_tasks:
                    log_to_queue(f"Executing task {project_run_task.task_name} for {self.project_key}")
                    tasker.post_pipeline(project_run_task.task_entry, project_run_task.pipeline_override).wait()
                    log_to_queue(f"Task {project_run_task.task_name} executed for {self.project_key}")
                # 执行 ProjectRunData 类型的任务
            else:
                log_to_queue(f"Unexpected task type received: {type(task)}")

    def send_task(self, task):
        self.task_queue.put(task)
        logging.info(f"Task {task} sent to Tasker process for {self.project_key}")

    def terminate(self):
        self.task_queue.put("TERMINATE")
        self.process.join()
        logging.info(f"Tasker process {self.project_key} terminated")


@singleton
class TaskProjectManager:
    """
    管理多个Tasker进程，处理任务和进程的启动、终止等。
    """
    def __init__(self):
        self.processes: Dict[str, TaskerProcess] = {}
        self.should_stop_log_thread = False
        self.lock = threading.Lock()

    def create_tasker_process(self, project: Project):
        project_key = _get_project_key(project)
        with self.lock:
            if project_key in self.processes:
                logging.warning(f"Tasker process for {project_key} already exists.")
                return
            tasker_process = TaskerProcess(project_key, project)
            self.processes[project_key] = tasker_process

    def send_task(self, project: Project, task):
        project_key = _get_project_key(project)
        with self.lock:
            if project_key not in self.processes:
                logging.error(f"No Tasker process found for {project_key}.")
                return
            self.processes[project_key].send_task(task)

    def terminate_tasker_process(self, project: Project):
        project_key = _get_project_key(project)
        with self.lock:
            if project_key not in self.processes:
                logging.error(f"No Tasker process found for {project_key}.")
                return
            self.processes[project_key].terminate()
            del self.processes[project_key]

    def force_terminate_all(self):
        """
        强制终止所有Tasker进程，直接调用terminate杀死进程。
        """
        logging.info("Force terminating all Tasker processes...")
        with self.lock:
            for project_key, tasker_process in list(self.processes.items()):
                process = tasker_process.process
                if process.is_alive():
                    logging.warning(f"Force terminating process for {project_key}")
                    process.terminate()  # 强制杀死进程
                    process.join()  # 确保进程被终止
                    logging.info(f"Process {project_key} forcefully terminated.")
            self.processes.clear()
        logging.info("All Tasker processes forcefully terminated.")

    def terminate_all(self):
        logging.info("Terminating all Tasker processes...")
        with self.lock:
            for project_key, tasker_process in list(self.processes.items()):
                # Assuming tasker_process is an instance of TaskerProcess class
                process = tasker_process.process
                task_queue = tasker_process.task_queue

                # Attempt to gracefully terminate the process
                task_queue.put("TERMINATE")
                logging.info(f"Sent terminate signal to Tasker process for {project_key}")

                # Wait for the process to complete
                process.join(timeout=5)  # Wait for a maximum of 5 seconds

                if process.is_alive():
                    logging.warning(
                        f"Tasker process for {project_key} did not terminate gracefully. Forcing termination...")
                    process.terminate()  # Force termination
                    process.join()  # Ensure the process is terminated

                logging.info(f"Tasker process for {project_key} has been terminated.")

            self.processes.clear()  # Clear the process list
        logging.info("All Tasker processes terminated.")

    def monitor_logs(self):
        """
        监控日志队列，输出日志信息。
        """
        with self.lock:
            for project_key, tasker_process in self.processes.items():
                while not tasker_process.log_queue.empty():
                    log_message = tasker_process.log_queue.get()
                    logging.info(f"[{project_key}] {log_message}")


def log_thread(manager: TaskProjectManager):
    """
    日志监控线程，每隔1秒检查所有进程的日志输出。
    """
    logging.info("Log monitoring thread started")
    while not manager.should_stop_log_thread:
        manager.monitor_logs()
        time.sleep(1)
    logging.info("Log monitoring thread terminated")
