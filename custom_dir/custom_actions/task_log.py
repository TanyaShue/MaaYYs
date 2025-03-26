# -*- coding: UTF-8 -*-
import json
from datetime import datetime

from maa import resource
from maa.context import Context

from maa.custom_action import CustomAction


class TaskLog(CustomAction):


    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        param=json.loads(argv.custom_action_param)
        message=param.get("message","")
        level=param.get("level","INFO")
        # task_logger = TaskLogger()
        _handle=context.tasker.controller._handle
        # task_logger.log(_handle, f"{message}", level)
        return True

    def stop(self):
        pass