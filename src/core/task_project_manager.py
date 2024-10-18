import socket
import json
import logging
import threading
import time
from typing import Dict, Union
from src.utils.config_projects import Project, ProjectRunData


def _get_project_key(p: Project) -> str:
    return f"{p.adb_config.adb_path}:{p.adb_config.adb_address}"


class TaskProjectManager:
    """
    管理与多个运行为独立服务的Tasker进程的通信。
    """
    def __init__(self):
        self.processes: Dict[str, Dict] = {}
        self.should_stop_log_thread = False
        self.lock = threading.Lock()

    def create_tasker_process(self, project: Project, host='localhost', port=9000):
        project_key = _get_project_key(project)
        with self.lock:
            if project_key in self.processes:
                logging.warning(f"Tasker进程 {project_key} 已经存在。")
                return

            # 存储服务器信息
            self.processes[project_key] = {"host": host, "port": port}

    def send_task(self, project: Project, task: Union[str, ProjectRunData]):
        project_key = _get_project_key(project)
        with self.lock:
            if project_key not in self.processes:
                logging.error(f"未找到 Tasker 进程: {project_key}.")
                return

            host = self.processes[project_key]['host']
            port = self.processes[project_key]['port']

            # 创建一个客户端Socket连接到TaskerProcess
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                if isinstance(task, str):
                    task_data = {'type': task}
                else:
                    task_data = {
                        'type': 'EXECUTE_TASK',
                        'task': task.__dict__
                    }
                s.sendall(json.dumps(task_data).encode())
                s.close()

    def terminate_tasker_process(self, project: Project):
        self.send_task(project, 'TERMINATE')

    def monitor_logs(self):
        """
        日志监控（这里的socket日志监控暂未实现）。
        可以为日志监控实现一个独立的Socket。
        """
        pass


def log_thread(manager: TaskProjectManager):
    """
    日志监控线程（假设使用独立的socket进行日志监控）。
    """
    logging.info("日志监控线程启动")
    while not manager.should_stop_log_thread:
        manager.monitor_logs()
        time.sleep(1)
    logging.info("日志监控线程终止")
