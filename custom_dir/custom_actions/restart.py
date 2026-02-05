# -*- coding: UTF-8 -*-
from time import sleep

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("ReStart")
class ReStart(CustomAction):
    # 用于记录上一次的任务节点名称
    the_last_entry = None
    # 用于记录同一个任务节点连续出现的次数
    node_count = 0

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        current_entry = argv.task_detail.entry
        print(f"当前任务入口: {current_entry}")
        print("触发timeout")
        return True

    def stop(self) -> None:
        pass