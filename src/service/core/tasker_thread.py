import os
import queue
import threading
import logging

from src.service.tasker import TaskLogger
from src.service.custom_actions.task_log import TaskLog
from src.service.custom_actions.bounty_monster_recognition import BountyMonsterRecognition
from src.service.custom_actions.auto_battle import AutoBattle
from src.service.custom_actions.challenge_dungeon_boss import ChallengeDungeonBoss
from src.service.custom_actions.human_touch import HumanTouch
from src.service.custom_actions.loop_action import LoopAction
from src.service.custom_actions.random_swipe import RandomSwipe
from src.service.custom_actions.random_touch import RandomTouch
from src.service.custom_actions.switch_soul import SwitchSoul
from src.service.custom_actions.task_list import TaskList
from src.service.custom_recognition.my_recognizer import MyRecognizer

from src.utils.config_projects import Project, ProjectRunData
from maa.controller import AdbController
from maa.resource import Resource
from maa.tasker import Tasker
from maa.toolkit import Toolkit

# TaskerThread implementation
class TaskerThread(threading.Thread):
    def __init__(self, project_key: str, project: Project):
        super().__init__()
        self.project_key = project_key
        self.project = project
        self.task_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.tasker = None
        self.controller = None
        self.resource = None
        self.command_thread = None

    def run(self):
        try:
            # 开启控制线程
            self.command_thread = threading.Thread(target=self._run_task_processing_loop, args=(self.command_queue, ))
            self.command_thread.start()
            # self._initialize_resources()
            # 开启主线程任务
            self._run_task_processing_loop(self.task_queue)
        except Exception as e:
            logging.error(f"Error initializing tasker for {self.project_key}: {e}")
        finally:
            self._cleanup()

    def _initialize_resources(self,resource_path) ->Tasker:
        current_dir = os.getcwd()
        Toolkit.init_option(os.path.join(current_dir, "assets"))
        if resource_path is None:
            resource_path=os.path.join(current_dir, "assets", "resource","yys_base")
        self.resource = Resource()
        print(os.path.join(current_dir, "assets", resource_path))
        self.resource.post_path(os.path.join(current_dir, "assets", resource_path)).wait()
        self.controller = AdbController(adb_path=self.project.adb_config.adb_path, address=self.project.adb_config.address)
        self.controller.post_connection().wait()

        self.tasker = Tasker()
        self.tasker.bind(self.resource, self.controller)
        self._register_custom_modules()

        if not self.tasker.inited:
            raise RuntimeError("Failed to initialize MAA tasker.")
        logging.info(f"Tasker initialized for {self.project_key}")
        return self.controller._handle

    def _register_custom_modules(self):
        # 注册自定义的 action ： AutoBattle, ChallengeDungeonBoss,
        # HumanTouch,LoopAction,RandomSwipe,RandomTouch,SwitchSoul,TaskList,BountyMonsterRecognition,TaskLog
        self.resource.register_custom_action("AutoBattle", AutoBattle())
        self.resource.register_custom_action("ChallengeDungeonBoss",ChallengeDungeonBoss())
        self.resource.register_custom_action("HumanTouch",HumanTouch())
        self.resource.register_custom_action("LoopAction",LoopAction())
        self.resource.register_custom_action("RandomSwipe",RandomSwipe())
        self.resource.register_custom_action("RandomTouch",RandomTouch())
        self.resource.register_custom_action("SwitchSoul",SwitchSoul())
        self.resource.register_custom_action("TaskList",TaskList())
        self.resource.register_custom_action("BountyMonsterRecognition",BountyMonsterRecognition())
        self.resource.register_custom_action("TaskLog",TaskLog())

        # 注册自定义的 recognizer:MyRecognizer
        self.resource.register_custom_recognition("MyRecognizer", MyRecognizer())

    def _run_task_processing_loop(self, task_queue):
        while not self.stop_event.is_set():
            try:
                task = task_queue.get(timeout=1)
                self._process_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error processing task for {self.project_key}: {e}")

    def _process_task(self, task):
        task_logger = TaskLogger()
        if isinstance(task, str):

            if task == "TERMINATE":
                self.terminate()
            elif task == "STOP":
                logging.info(f"Stopping Tasker {self.project_key}")
                self.tasker.post_stop()
                logging.info(f"Tasker {self.project_key} posted stop")
            else:
                logging.warning(f"Unexpected task: {task}")
        elif isinstance(task, ProjectRunData):
            for project_run_task in task.project_run_tasks:
                logging.info(f"Executing {project_run_task.task_name} for {self.project_key}")
                task_logger.log(self.controller._handle, f"开始执行任务: {project_run_task.task_name}")
                self.tasker.post_pipeline(project_run_task.task_entry, project_run_task.pipeline_override).wait()
                task_logger.log(self.controller._handle, f"任务: {project_run_task.task_name} 执行完成")
                logging.info(f"Task {project_run_task.task_name} Executed for {self.project_key}")

    def send_task(self, task):
        """将任务添加到队列"""
        if isinstance(task, str):
            self.command_queue.put(task)
        else:
            self.task_queue.put(task)

    def terminate(self):
        """终止线程和所有子进程"""
        logging.info(f"Terminating Tasker {self.project_key}...")

        self.stop_event.set()  # 停止事件
        self.task_queue.queue.clear()  # 清空任务队列，防止残留任务导致内存泄漏

        # 清理控制线程
        self.command_queue.queue.clear()
        self.command_thread.join()
        self._cleanup()


    def _cleanup(self):
        logging.info(f"Cleaning up resources for {self.project_key}")
        try:
            if self.tasker:
                self.tasker.post_stop()
                self.tasker.__del__()
            if self.controller:
                self.controller.__del__()
            if self.resource:
                self.resource.__del__()
        except Exception as e:
            logging.error(f"Error during cleanup for {self.project_key}: {e}")
        logging.info(f"Tasker thread for {self.project_key} has been terminated.")


