import os
import queue
import threading
import logging

import psutil

from src.custom_actions.auto_battle import AutoBattle
from src.custom_actions.challenge_dungeon_boss import ChallengeDungeonBoss
from src.custom_actions.human_touch import HumanTouch
from src.custom_actions.loop_action import LoopAction
from src.custom_actions.random_swipe import RandomSwipe
from src.custom_actions.random_touch import RandomTouch
from src.custom_actions.switch_soul import SwitchSoul
from src.custom_actions.task_list import TaskList
from src.custom_recognition.my_recognizer import MyRecognizer
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
        self.controller = None
        self.resource = None

    def run(self):
        try:
            self._initialize_resources()
            self._run_task_processing_loop()
        except Exception as e:
            logging.error(f"Error initializing tasker for {self.project_key}: {e}")
        finally:
            self._cleanup()

    def _initialize_resources(self):
        current_dir = os.getcwd()
        Toolkit.init_option(os.path.join(current_dir, "assets"))

        self.resource = Resource()
        self.resource.post_path(os.path.join(current_dir, "assets", "resource", "base")).wait()

        self.controller = AdbController(adb_path=self.project.adb_config.adb_path, address=self.project.adb_config.adb_address)
        self.controller.post_connection().wait()

        self.tasker = Tasker()
        self.tasker.bind(self.resource, self.controller)
        self._register_custom_modules()

        if not self.tasker.inited:
            raise RuntimeError("Failed to initialize MAA tasker.")

        logging.info(f"Tasker initialized for {self.project_key}")

    def _register_custom_modules(self):
        # 注册自定义的 action ： AutoBattle, ChallengeDungeonBoss, HumanTouch,LoopAction,RandomSwipe,RandomTouch,SwitchSoul,TaskList
        self.resource.register_custom_action("AutoBattle", AutoBattle())
        self.resource.register_custom_action("ChallengeDungeonBoss",ChallengeDungeonBoss())
        self.resource.register_custom_action("HumanTouch",HumanTouch())
        self.resource.register_custom_action("LoopAction",LoopAction())
        self.resource.register_custom_action("RandomSwipe",RandomSwipe())
        self.resource.register_custom_action("RandomTouch",RandomTouch())
        self.resource.register_custom_action("SwitchSoul",SwitchSoul())
        self.resource.register_custom_action("TaskList",TaskList())
        # 注册自定义的 recognizer:MyRecognizer
        self.resource.register_custom_recognition("MyRecognizer", MyRecognizer())

    def _run_task_processing_loop(self):
        while not self.stop_event.is_set():
            try:
                task = self.task_queue.get(timeout=1)
                self._process_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error processing task for {self.project_key}: {e}")

    def _process_task(self, task):
        if isinstance(task, str):
            if task == "TERMINATE":
                self.terminate()
            else:
                logging.warning(f"Unexpected task: {task}")
        elif isinstance(task, ProjectRunData):
            for project_run_task in task.project_run_tasks:
                logging.info(f"Executing {project_run_task.task_name} for {self.project_key}")
                self.tasker.post_pipeline(project_run_task.task_entry, project_run_task.pipeline_override).wait()
                logging.info(f"任务执行完毕")

    def send_task(self, task):
        """将任务添加到队列"""
        self.task_queue.put(task)

    def terminate(self):
        """终止线程和所有子进程"""
        logging.info(f"Terminating Tasker {self.project_key}...")

        # 停止 tasker 的自定义逻辑
        self.tasker.post_stop()

        # 强行终止 adb.exe 进程
        _terminate_adb_processes()

        # 清理其他资源
        self._cleanup()

        # 触发终止事件
        self.stop_event.set()




    def _cleanup(self):
        logging.info(f"Cleaning up resources for {self.project_key}")
        try:
            if self.tasker:
                self.tasker.terminate()
            if self.controller:
                self.controller.__del__()
            if self.resource:
                self.resource.__del__()
        except Exception as e:
            logging.error(f"Error during cleanup for {self.project_key}: {e}")
        logging.info(f"Tasker thread for {self.project_key} has been terminated.")
def _terminate_adb_processes():
    """查找并终止所有名为 adb.exe 的进程"""
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == 'adb.exe':
            try:
                logging.info(f"Terminating adb.exe process [PID: {process.info['pid']}]...")
                process.terminate()
                process.wait(timeout=5)  # 等待最多5秒终止
            except psutil.NoSuchProcess:
                logging.warning(f"Process [PID: {process.info['pid']}] already terminated.")
            except psutil.TimeoutExpired:
                logging.warning(f"Process [PID: {process.info['pid']}] did not terminate, killing it...")
                process.kill()  # 强制杀死进程
            except Exception as e:
                logging.error(f"Failed to terminate process [PID: {process.info['pid']}]: {e}")