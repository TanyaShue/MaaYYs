# -*- coding: UTF-8 -*-
import json
import random

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer

from custom_dir import print_to_ui


@AgentServer.custom_action("Guess")
class Guess(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg) -> bool:
        """
        自定义动作：根据权重随机选择并执行一个任务
        :param argv: custom_action_param 格式{}
        :param context: 执行上下文
        :return: 是否执行成功
        """

        print("开始执行自定义动作：竞猜")
        img = context.tasker.controller.post_screencap().wait().get()

        result_r = context.run_recognition("识别左侧人数", img)
        count_r = int(
            result_r.best_result.text) if result_r and result_r.best_result and result_r.best_result.text.isdigit() else 0
        print(f"识别左侧人数 {count_r}")

        result_l = context.run_recognition("识别右侧人数", img)
        count_l = int(
            result_l.best_result.text) if result_l and result_l.best_result and result_l.best_result.text.isdigit() else 0
        print(f"识别右侧人数 {count_l}")

        # 找出人数多的那个，没有则默认左边
        if count_r > count_l:
            winner = "左边"
            context.run_task("竞猜7_左边")
        elif count_l > count_r:
            winner = "右边"
            context.run_task("竞猜10_右边")
        else:
            winner = "左边"  # 默认左边
            context.run_task("竞猜7_左边")

        print("竞猜结束")
        print_to_ui(context,f"选择了{winner}")
        return True

    def stop(self) -> None:
        """停止逻辑"""
        pass