import threading
import multiprocessing
import logging
import time
from typing import Dict, Tuple, List
from maa.resource import Resource
from maa.controller import AdbController
from maa.tasker import Tasker
from maa.toolkit import Toolkit
from src.config.config_models import TaskProject, Task, Program


def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class TaskProjectManager:
    def __init__(self):
        self.processes: Dict[str, Tuple[multiprocessing.Process, multiprocessing.Queue, multiprocessing.Queue]] = {}
        self.should_stop_log_thread = False
        self.lock = threading.Lock()  # 线程锁

    def _get_project_key(self, p: TaskProject) -> str:
        return f"{p.adb_config['adb_address']}:{p.adb_config['adb_port']}"

    def create_tasker_process(self, p: TaskProject):
        project_key = self._get_project_key(p)
        with self.lock:
            if project_key in self.processes:
                logging.warning(f"Tasker process for {project_key} already exists.")
                return

            task_queue = multiprocessing.Queue()
            log_queue = multiprocessing.Queue()
            process = multiprocessing.Process(target=tasker_process, args=(task_queue, log_queue, p))
            process.start()
            self.processes[project_key] = (process, task_queue, log_queue)
            logging.info(f"Started new Tasker process for {project_key}")

    def send_task(self, p: TaskProject,tasks:list[Task]):
        project_key = self._get_project_key(p)
        with self.lock:
            if project_key not in self.processes:
                logging.error(f"No Tasker process found for {project_key}.")
                return
            self.processes[project_key][1].put(tasks)  # 发送任务
            logging.info(f"Task {tasks} sent to Tasker process for {project_key}")

    def terminate_tasker_process(self, p: TaskProject):
        project_key = self._get_project_key(p)
        with self.lock:
            if project_key not in self.processes:
                logging.error(f"No Tasker process found for {project_key}.")
                return
            process, task_queue, _ = self.processes[project_key]
            task_queue.put("TERMINATE")
            process.join()
            del self.processes[project_key]
            logging.info(f"Terminated Tasker process for {project_key}")

    def terminate_all(self):
        self.should_stop_log_thread = True
        logging.info("Terminating all Tasker processes...")
        with self.lock:
            for project_key in list(self.processes.keys()):
                process, input_queue, output_queue = self.processes[project_key]

                # 终止进程
                if process.is_alive():
                    process.terminate()
                    process.join()

                # 关闭队列
                input_queue.close()
                output_queue.close()

                # 取消队列的阻塞等待 (可选)
                input_queue.cancel_join_thread()
                output_queue.cancel_join_thread()

                logging.info(f"已成功终止进程 {process.pid}。")
        logging.info("Terminated all Tasker processes.")

    def monitor_logs(self):
        with self.lock:
            for project_key, (_, _, log_queue) in list(self.processes.items()):
                while not log_queue.empty():
                    log_message = log_queue.get()
                    logging.info(f"[{project_key}] {log_message}")

def tasker_process(task_queue: multiprocessing.Queue, log_queue: multiprocessing.Queue, p: TaskProject):
    def log_to_queue(message: str):
        log_queue.put(message)

    log_to_queue(f"Initializing Tasker for {p.adb_config['adb_address']}:{p.adb_config['adb_port']}")
    Toolkit.init_option("../assets")

    resource = Resource()
    resource.post_path("../assets/resource/base").wait()

    controller = AdbController(adb_path=p.adb_config['adb_address'], address=p.adb_config['adb_port'])
    controller.post_connection().wait()

    tasker = Tasker()
    tasker.bind(resource, controller)

    if not tasker.inited:
        log_to_queue("Failed to init MAA in process.")
        raise RuntimeError("Failed to init MAA in process.")

    log_to_queue(f"成功创建Tasker{tasker}")

    while True:
        try:
            tasks = task_queue.get()
            for task in tasks:
                print(f"{task.task_name}{task.entry}")
            if tasks == "TERMINATE":
                log_to_queue(f"Terminating Tasker process for {p.adb_config['adb_address']}:{p.adb_config['adb_port']}")
                break
            log_to_queue(f"Executing task {tasks} for Tasker {p.adb_config['adb_address']}:{p.adb_config['adb_port']}")
            tasker.execute_task(tasks)
        except Exception as e:
            log_to_queue(f"Error executing task: {e}")

def log_thread(manager: TaskProjectManager):
    logging.info("日志处理线程启动")
    while not manager.should_stop_log_thread:
        manager.monitor_logs()
        time.sleep(1)  # 适当延时，避免CPU过高使用
