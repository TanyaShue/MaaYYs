# -*- coding: UTF-8 -*-
from datetime import datetime

from maa.context import Context

from maa.custom_action import CustomAction

from src.service.tasker import TaskLogger


class TaskLog(CustomAction):


    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数{"task_list": ["A", "B", "C"]}
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        task_logger = TaskLogger()
        print("开始执行自定义动作：任务日志")
        task_logger.log(context.tasker.controller._handle,f"This is a log message , timestamp: {datetime.now()}.", "INFO")
        return True

    def stop(self):
        pass