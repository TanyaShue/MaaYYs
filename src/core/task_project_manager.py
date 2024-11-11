import logging
import threading
import time

import requests
from typing import Dict, Union
from src.utils.config_projects import Project, ProjectRunData
from src.utils.common import load_config


def _get_project_key(p: Project) -> str:
    """使用 adb_config 来唯一标识一个 project，但它不用于服务器通信"""
    return f"{p.adb_config.adb_path}:{p.adb_config.adb_address}"

class TaskProjectManager:
    server_host = load_config().get("server_host", "localhost")
    server_port = load_config().get("server_port", 54345)
    """
    管理与多个运行的Tasker进程的通信。
    """
    def __init__(self):
        self.processes: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def create_tasker_process(self, project: Project) -> bool:
        """
        用于和服务端交互，server_host 和 server_port 是服务器的 HTTP 接口地址，而非 adb_config。
        """
        project_key = _get_project_key(project)
        with self.lock:
            if project_key in self.processes:
                logging.warning(f"Tasker进程 {project_key} 已经存在。")
                return True

            # 存储服务器信息
            self.processes[project_key] = {"server_host": self.server_host, "server_port": self.server_port}
            url = f"http://{self.server_host}:{self.server_port}/create_tasker"
            print(url)
            data = {
                "action": "create_tasker",
                "project_key": project_key,
                "project": project.to_json()  # 发送整个 project 数据供服务器使用
            }

            # 发起HTTP请求来创建Tasker进程
            try:
                response = requests.post(url, json=data)
                if response.status_code == 200:
                    logging.info(f"Tasker {project_key} created successfully.")
                    return True
                elif response.status_code == 500:
                    logging.error(f"Failed to create Tasker {project_key}: {response.text}")
                    return False
            except requests.RequestException as e:
                logging.error(f"Error in creating Tasker: {e}")
                return False

    def send_task(self, project: Project, task: Union[str, ProjectRunData]):
        """
        发送任务到指定的 Tasker 服务端，服务器的 host 和 port 与 adb 无关。
        """
        project_key = _get_project_key(project)
        with self.lock:
            if project_key not in self.processes:
                logging.error(f"未找到 Tasker 进程: {project_key}.")
                return

            url = f"http://{self.server_host}:{self.server_port}/send_task"

            if isinstance(task, ProjectRunData):
                task_data = {
                    'task': task.to_json()
                }
            else:

                task_data = {'task': task}
            data = {
                "action": "send_task",
                "project_key": project_key,
                "task": task_data
            }

            # 发起HTTP请求来发送任务
            try:
                response = requests.post(url, json=data)
                if response.status_code == 200:
                    logging.info(f"Task sent to {project_key} successfully.")
                    logging.info(f"Task: {task}")
                else:
                    logging.error(f"Failed to send task to {project_key}: {response.text}")
            except requests.RequestException as e:
                logging.error(f"Error in sending task: {e}")

    def terminate_tasker_process(self, project: Project):
        """
        终止 Tasker 进程，发送 HTTP 请求给服务器。
        """
        project_key = _get_project_key(project)
        url = f"http://{self.server_host}:{self.server_port}/terminate_tasker"
        data = {
            "action": "terminate_tasker",
            "project_key": project_key
        }

        # 发起HTTP请求来终止Tasker进程
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                logging.info(f"Tasker {project_key} terminated successfully.")
            else:
                logging.error(f"Failed to terminate Tasker {project_key}: {response.text}")
        except requests.RequestException as e:
            logging.error(f"Error in terminating tasker: {e}")

    def monitor_logs(self):
        """
        日志监控部分保持不变，但可以考虑通过服务器提供独立的日志接口。
        """
        pass

def log_thread(manager: TaskProjectManager):
    """
    日志监控线程（假设使用独立的HTTP接口进行日志监控）。
    """
    logging.info("日志监控线程启动")
    while not manager.should_stop_log_thread:
        manager.monitor_logs()
        time.sleep(1)
    logging.info("日志监控线程终止")
