import os
import queue
import threading
import logging

import psutil

from custom_actions.auto_battle import AutoBattle
from custom_actions.challenge_dungeon_boss import ChallengeDungeonBoss
from custom_actions.human_touch import HumanTouch
from custom_actions.loop_action import LoopAction
from custom_actions.random_swipe import RandomSwipe
from custom_actions.random_touch import RandomTouch
from custom_actions.switch_soul import SwitchSoul
from custom_actions.task_list import TaskList
from custom_recognition.my_recognizer import MyRecognizer
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
        self.stop_event.set()
        self._terminate_all_subprocesses()
    def _terminate_all_subprocesses(self):
        """使用 psutil 获取并终止所有子进程"""
        current_process = psutil.Process()  # 获取当前主进程
        children = current_process.children(recursive=True)  # 获取所有子进程
        for child in children:
            logging.info(f"Terminating subprocess {child.pid} for {self.project_key}")
            child.terminate()  # 优雅终止子进程
            try:
                child.wait(timeout=2)  # 等待进程终止
            except psutil.TimeoutExpired:
                logging.warning(f"Subprocess {child.pid} did not terminate, forcing kill.")
                child.kill()  # 强制终止子进程
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
