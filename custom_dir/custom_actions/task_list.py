# -*- coding: UTF-8 -*-
import json
import time

from maa.context import Context
from maa.custom_action import CustomAction

try:
    from app.models.logging.log_manager import log_manager
    use_default_logging = False
except ImportError:
    import logging
    use_default_logging = True

class TaskList(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数{"task_list": {"A": True, "B": False, "C": True}}
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        if use_default_logging:
            logger = logging.getLogger("TaskList")
        else:
            logger = log_manager.get_context_logger(context)
        logger.debug("开始执行自定义动作：任务列表")
        json_data = json.loads(argv.custom_action_param)
        # task_logger = TaskLogger()
        task_dict = json_data.get("task_list", {})

        if not task_dict:
            logger.debug("无效的 task_list")
            return False

        logger.debug(f"开始执行任务列表 {task_dict}")

        for task, should_run in task_dict.items():
            if should_run:
                logger.debug(f"执行任务: {task}")
                # task_logger.log(context.tasker.controller._handle, f"执行任务: {task}", "INFO")
                context.run_task(task)
                # task_logger.log(context.tasker.controller._handle, f"任务: {task} 执行完成", "INFO")
                logger.debug(f"任务 {task} 执行完成")
                time.sleep(2)
            else:
                logger.debug(f"跳过任务: {task}（标记为不执行）")
        return True

    def stop(self):
        pass