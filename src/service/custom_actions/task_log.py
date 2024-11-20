# -*- coding: UTF-8 -*-
import json
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
        param=json.loads(argv.custom_action_param)
        message=param.get("message","")
        level=param.get("level","INFO")
        task_logger = TaskLogger()
        _handle=context.tasker.controller._handle
        task_logger.log(_handle, f"{message}", level)
        return True

    def stop(self):
        pass