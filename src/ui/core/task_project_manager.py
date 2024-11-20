# coding=utf-8
import json
import logging
import threading
import time
from pathlib import WindowsPath

import requests

from urllib3 import Retry
from src.utils.config_projects import Project, ProjectRunData
from src.utils.common import load_config
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Union, Optional, List, Any
from requests.adapters import HTTPAdapter
from abc import ABC, abstractmethod

from src.utils.singleton import singleton

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _get_project_key(p: Project) -> str:
    """使用 adb_config 来唯一标识一个 project，但它不用于服务器通信"""
    return f"{p.adb_config.adb_path}:{p.adb_config.address}"

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class TaskConfig:
    """任务配置数据类"""
    retry_attempts: int = 3
    retry_delay: int = 1
    timeout: int = 300
    keep_alive: bool = True
@dataclass
class AdbDevice:
    name: str
    adb_path: WindowsPath
    address: str
    screencap_methods: int
    input_methods: int
    config: Dict[str, Any]

    def to_dict(self):
        return {
            'name': self.name,
            'adb_path': str(self.adb_path),
            'address': self.address,
            'screencap_methods': str(self.screencap_methods),  # 转换为字符串
            'input_methods': str(self.input_methods),  # 转换为字符串
            'config': self.config
        }

class TaskError(Exception):
    """任务相关异常基类"""
    pass


class TaskCreationError(TaskError):
    """任务创建失败异常"""
    pass


class TaskExecutionError(TaskError):
    """任务执行失败异常"""
    pass


class TaskCommunicationError(TaskError):
    """任务通信失败异常"""
    pass


class TaskMonitor(ABC):
    """任务监控抽象基类"""

    @abstractmethod
    def start_monitoring(self):
        pass

    @abstractmethod
    def stop_monitoring(self):
        pass

    @abstractmethod
    def get_log(self) -> Dict:
        pass

@singleton
class HTTPTaskMonitor(TaskMonitor):
    """基于HTTP的任务监控实现"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.log_queue = {}

    def start_monitoring(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop)
            self._thread.daemon = True
            self._thread.start()

    def stop_monitoring(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def get_log(self) -> Dict:
        url = f"http://{self.host}:{self.port}/api/v1/tasker_all_log"
        try:
            response = requests.get(url)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {}

    def _monitor_loop(self):
        while self._running:
            try:
                # 获取新的日志
                new_log = self.get_log().get("data", {}).get("log", {})
                if new_log:
                    for key, value in new_log.items():
                        if key in self.log_queue:
                            self.log_queue[key].extend(value)  # 追加日志
                        else:
                            self.log_queue[key] = value  # 新增日志
                # print(f"当前日志队列: {self.log_queue}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(1)


@singleton
class TaskProjectManager:
    """任务项目管理器"""

    def __init__(self, config: Optional[TaskConfig] = None):
        """
        初始化任务管理器

        Args:
            config: 任务配置对象,如果为None则使用默认配置
        """
        self.config = config or TaskConfig()
        self.processes: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.session = self._create_http_session()
        self.monitor = HTTPTaskMonitor(
            host=load_config().get("server_host", "localhost"),
            port=load_config().get("server_port", 54345)
        )

    def _create_http_session(self) -> requests.Session:
        """创建具有重试机制的HTTP会话"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def create_tasker_process(self, project: Project) -> bool:
        """
        创建新的Tasker进程

        Args:
            project: 项目配置对象

        Returns:
            bool: 是否成功创建

        Raises:
            TaskCreationError: 创建失败时抛出
        """
        project_key = _get_project_key(project)
        with self.lock:
            if project_key in self.processes:
                logger.warning(f"Tasker process {project_key} already exists.")
                return True

            try:
                response = self._make_request(
                    "create_tasker",
                    {
                        "project_key": project_key,
                        "project": project.to_json()
                    }
                )

                if response.status_code == 200:
                    self.processes[project_key] = {
                        "status": TaskStatus.PENDING,
                        "created_at": time.time(),
                        "project": project
                    }
                    logger.info(f"Successfully created Tasker {project_key}")
                    return True

                raise TaskCreationError(f"Failed to create Tasker: {response.text}")

            except requests.RequestException as e:
                raise TaskCommunicationError(f"Communication error: {e}")

    def send_task(self, project: Project, task: Union[str, ProjectRunData]):
        """
        发送任务到指定的Tasker进程

        Args:
            project: 项目配置对象
            task: 任务数据或任务字符串

        Raises:
            TaskExecutionError: 任务发送失败时抛出
        """
        project_key = _get_project_key(project)

        if project_key not in self.processes:
            raise TaskExecutionError(f"Tasker process {project_key} not found")

        task_data = task.to_json() if isinstance(task, ProjectRunData) else task
        print("send task:", task_data)
        try:
            response = self._make_request(
                "send_task",
                {
                    "project_key": project_key,
                    "task": task_data
                }
            )
            if response.status_code != 200:
                raise TaskExecutionError(f"Failed to send task: {response.text}")

            self.processes[project_key]["status"] = TaskStatus.RUNNING
            logger.info(f"Successfully sent task to {project_key}")

        except requests.RequestException as e:
            raise TaskCommunicationError(f"Communication error: {e}")

    def terminate_tasker_process(self, project: Project):
        """
        终止指定的Tasker进程

        Args:
            project: 项目配置对象

        Raises:
            TaskExecutionError: 终止失败时抛出
        """
        project_key = _get_project_key(project)

        try:
            response = self._make_request(
                "terminate_tasker",
                {"project_key": project_key}
            )

            if response.status_code != 200:
                raise TaskExecutionError(f"Failed to terminate Tasker: {response.text}")

            with self.lock:
                if project_key in self.processes:
                    self.processes[project_key]["status"] = TaskStatus.TERMINATED

            logger.info(f"Successfully terminated Tasker {project_key}")

        except requests.RequestException as e:
            raise TaskCommunicationError(f"Communication error: {e}")

    def get_adb_devices(self) -> list[AdbDevice]:
        """从API获取ADB设备数据"""
        try:

            response = self._make_request(
                "get_all_devices",
                {}
            )
            if response.status_code != 200 :
                raise Exception("API返回错误状态")
            devices_data = response.json().get("data").get("devices")
            if isinstance(devices_data, str):
                devices_data = json.loads(devices_data)
            devices = []
            for device_data in devices_data:
                # 确保将大整数转换为字符串
                device_data['screencap_methods'] = str(device_data['screencap_methods'])
                device_data['input_methods'] = str(device_data['input_methods'])

                device = AdbDevice(
                    name=device_data['name'],
                    adb_path=WindowsPath(device_data['adb_path']),
                    address=device_data['address'],
                    screencap_methods=int(device_data['screencap_methods']),
                    input_methods=int(device_data['input_methods']),
                    config=device_data['config']
                )
                devices.append(device)
            return devices
        except Exception as e:
            print(e)
        except requests.RequestException as e:
            raise TaskCommunicationError(f"Communication error: {e}")

    def _make_request(self, endpoint: str, data: Dict) -> requests.Response:
        """发送HTTP请求的通用方法"""
        url = f"http://{self.monitor.host}:{self.monitor.port}/api/v1/{endpoint}"
        return self.session.post(
            url,
            json={"action": endpoint, **data},
            timeout=self.config.timeout
        )

    def get_process_status(self, project: Project) -> TaskStatus:
        """获取指定进程的状态"""
        project_key = _get_project_key(project)
        return self.processes.get(project_key, {}).get("status", TaskStatus.FAILED)

    def get_all_processes(self) -> List[Dict]:
        """获取所有进程的信息"""
        return [
            {
                "project_key": key,
                "status": info["status"],
                "created_at": info["created_at"],
                "project": info["project"]
            }
            for key, info in self.processes.items()
        ]

    def start_monitoring(self):
        """启动监控"""
        self.monitor.start_monitoring()

    def stop_monitoring(self):
        """停止监控"""
        self.monitor.stop_monitoring()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_monitoring()

    def get_log(self):
        return self.monitor.log_queue


