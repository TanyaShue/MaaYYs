import queue
import socketserver
import threading
import json
import logging
from typing import Dict
from src.core.loader import load_custom_actions, action_registry, load_custom_recognizers, recognizer_registry
from src.utils.config_projects import Project, ProjectRunData
from maa.controller import AdbController
from maa.resource import Resource
from maa.tasker import Tasker
from maa.toolkit import Toolkit

logging.basicConfig(level=logging.INFO)

class TaskerThread(threading.Thread):
    def __init__(self, project_key: str, project: Project):
        super().__init__()
        self.project_key = project_key
        self.project = project
        self.task_queue = queue.Queue()
        self.log_callback = None  # Function to send logs back
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
            self.send_log("Failed to init MAA in thread.")
            return

        self.send_log(f"Tasker initialized for {self.project_key}")

        while not self.stop_event.is_set():
            try:
                print(f"等待任务：{self.project_key}")
                task = self.task_queue.get(timeout=1)
                if isinstance(task, str):
                    self.handle_string_task(task, resource, tasker, controller)
                elif isinstance(task, ProjectRunData):
                    self.handle_project_run_data_task(task, tasker)
                else:
                    self.send_log(f"Unexpected task type received: {type(task)}")
            except queue.Empty:
                continue
            except Exception as e:
                self.send_log(f"Exception occurred: {e}")

    def handle_string_task(self, task, resource, tasker, controller):
        if task == "TERMINATE":
            self.send_log(f"Terminating Tasker thread for {self.project_key}")
            self.stop_event.set()
        elif task == "RELOAD_RESOURCES":
            self.send_log(f"Reloading resources for {self.project_key}")
            resource.post_path("../assets/resource/base").wait()
            tasker.bind(resource, controller)
            self.send_log(f"Resource reloaded for {self.project_key}")
        else:
            self.send_log(f"Unexpected string task received: {task}")

    def handle_project_run_data_task(self, task, tasker):
        self.send_log(f"Executing task {task}")
        for project_run_task in task.project_run_tasks:
            self.send_log(f"Executing task {project_run_task.task_name} for {self.project_key}")
            tasker.post_pipeline(project_run_task.task_entry, project_run_task.pipeline_override).wait()
            self.send_log(f"Task {project_run_task.task_name} executed for {self.project_key}")
            print(f"Task {project_run_task.task_name} executed for {self.project_key}")

    def send_log(self, message: str):
        if self.log_callback:
            self.log_callback(f"[{self.project_key}] {message}")

    def send_task(self, task):
        self.task_queue.put(task)

    def terminate(self):
        self.stop_event.set()
        self.task_queue.put("TERMINATE")
        self.join()


class TaskServiceHandler(socketserver.BaseRequestHandler):
    def handle(self):
        """接收请求并将解析后的请求传递给服务器处理"""
        logging.info(f"Handling connection from {self.client_address}")
        while True:
            try:
                # 接收数据
                data = self.request.recv(1024).strip()  # 使用 recv 接收数据
                if not data:
                    break
                self.process_message(data.decode('utf-8').strip())
            except ConnectionResetError:
                break
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                break

    def process_message(self, msg):
        """解析JSON请求并将其传递给服务器处理"""
        try:
            request = json.loads(msg)  # 解析JSON请求
            print(request)
            response = self.server.handle_task_request(request, self)
            if response:
                self.send_response(response)  # 使用新方法发送响应
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e} for message: {msg}")
            self.send_log(f"Invalid JSON format: {msg}")
        except Exception as e:
            logging.error(f"Error handling request: {e}")
            self.send_log(f"Error handling request: {e}")

    def send_log(self, message: str):
        """发送日志消息到客户端"""
        log_message = json.dumps({"log": message}) + '\n'
        self.request.sendall(log_message.encode('utf-8'))  # 使用 sendall 发送日志

    def send_response(self, response: dict):
        """发送响应消息到客户端"""
        response_message = json.dumps(response) + '\n'
        self.request.sendall(response_message.encode('utf-8'))  # 使用 sendall 发送响应


class TaskServiceServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address):
        logging.info(f"Starting task service on {server_address}")
        super().__init__(server_address, TaskServiceHandler)
        self.taskers: Dict[str, TaskerThread] = {}
        self.lock = threading.Lock()

    def handle_task_request(self, request: dict, handler: TaskServiceHandler):
        """统一处理任务请求"""
        action = request.get("action")
        project_key = request.get("project_key")

        if action in ["create_tasker", "send_task", "terminate_tasker", "terminate_all"]:
            return self.dispatch_task(action, request, handler)
        return {"status": "error", "message": "Unknown action."}

    def dispatch_task(self, action: str, request: dict, handler: TaskServiceHandler):
        """根据动作类型派发任务"""
        project_key = request.get("project_key")
        print("接收到任务请求:", request)
        if action == "create_tasker":
            project_data = request.get("project")
            # 使用 from_json 方法来创建 Project 对象
            project = Project.from_json(project_data)
            print(f"创建Tasker线程: {project}")
            project_key = f"{project.adb_config.adb_path}:{project.adb_config.adb_address}"
            return self.create_tasker(project_key, project, handler)
        elif action == "send_task":
            return self.send_task(project_key, request)
        elif action == "terminate_tasker":
            return self.terminate_tasker(project_key)
        elif action == "terminate_all":
            return self.terminate_all_taskers()

    def create_tasker(self, project_key: str, project: Project, handler: TaskServiceHandler):
        """创建Tasker线程"""
        with self.lock:
            if project_key in self.taskers:
                return {"status": "error", "message": "Tasker already exists."}
            tasker = TaskerThread(project_key, project)
            tasker.log_callback = handler.send_log
            tasker.start()
            self.taskers[project_key] = tasker
        return {"status": "success", "message": f"Tasker {project_key} created."}

    def send_task(self, project_key: str, request: dict):
        """向Tasker发送任务"""
        task_data = request.get("task")
        with self.lock:
            tasker = self.taskers.get(project_key)
            if not tasker:
                return {"status": "error", "message": "Tasker not found."}
            task = ProjectRunData.from_json(task_data) if isinstance(task_data, dict) else task_data
            tasker.send_task(task)
        return {"status": "success", "message": "Task sent."}

    def terminate_tasker(self, project_key: str):
        """终止指定的Tasker"""
        with self.lock:
            tasker = self.taskers.pop(project_key, None)
            if not tasker:
                return {"status": "error", "message": "Tasker not found."}
            tasker.terminate()
        return {"status": "success", "message": f"Tasker {project_key} terminated."}

    def terminate_all_taskers(self):
        """终止所有Tasker"""
        with self.lock:
            for tasker in list(self.taskers.values()):
                tasker.terminate()
            self.taskers.clear()
        return {"status": "success", "message": "All taskers terminated."}


def run_task_service(host='localhost', port=11234):
    """启动任务服务"""
    server = TaskServiceServer((host, port))
    logging.info(f"Task Service started on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_task_service()
