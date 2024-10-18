import socket
import json
import threading
import logging
from typing import Union

from src.utils.config_projects import Project, ProjectRunData, AdbConfig, ProjectRunTask

logging.basicConfig(level=logging.INFO)

class TaskProjectManagerClient:
    def __init__(self, host='localhost', port=11234):
        self.host = host
        self.port = port
        self.sock = socket.create_connection((host, port))
        self.lock = threading.Lock()
        self.listener_thread = threading.Thread(target=self.listen_logs, daemon=True)
        self.listener_thread.start()

    def send_request(self, request: dict):
        with self.lock:
            # Serialize the request to JSON
            message = json.dumps(request)
            # Send the JSON message as bytes
            self.sock.sendall(message.encode('utf-8') + b'\n')

    def listen_logs(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(4096).decode('utf-8')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        response = json.loads(line)
                        if "log" in response:
                            logging.info(response["log"])
                        else:
                            logging.info(response)
            except Exception as e:
                logging.error(f"Error receiving data: {e}")
                break

    def create_tasker_process(self, project: Project):
        print(project)
        request = {
            "action": "create_tasker",
            "project": project.to_json()  # 确保Project对象可以序列化为字典
        }
        self.send_request(request)

    def send_task(self, project: Project, task: Union[str, ProjectRunData]):
        print(task)
        request = {
            "action": "send_task",
            "project_key": f"{project.adb_config.adb_path}:{project.adb_config.adb_address}",
            "task": task.to_json() if isinstance(task, ProjectRunData) else task
        }
        self.send_request(request)

    def terminate_tasker_process(self, project: Project):
        request = {
            "action": "terminate_tasker",
            "project_key": f"{project.adb_config.adb_path}:{project.adb_config.adb_address}"
        }
        self.send_request(request)

    def terminate_all(self):
        request = {
            "action": "terminate_all"
        }
        self.send_request(request)

    def close(self):
        self.sock.close()