# -*- coding: UTF-8 -*-
from time import sleep

from PIL import Image
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
        print("触发time_out")
        if current_entry =="寮突":
            print("寮突错误")
            return True
        if current_entry =="组队副本14":
            print("组队副本14")
            return True
        # 判断当前任务节点是否与上一个相同
        if ReStart.the_last_entry == current_entry:
            ReStart.node_count += 1
            print(f"任务节点 '{current_entry}' 已连续出现 {ReStart.node_count} 次。")
        else:
            # 如果是新的任务节点，则更新记录并重置计数器
            ReStart.the_last_entry = current_entry
            ReStart.node_count = 1
            print(f"任务节点: '{current_entry}'，计数重置为 1。")

        if ReStart.node_count >= 2:
            print("任务失败两次即将重启游戏并跳过任务")
            context.run_task("关闭阴阳师")
            sleep(3)
            context.run_task("启动游戏")
            return True


        if ReStart.node_count < 2:
            print("任务失败即将重启游戏")
            context.run_task("关闭阴阳师")
            sleep(3)
            context.run_task("启动游戏")
            print(f"将从任务入口 '{current_entry}' 重新开始执行。")
            context.run_task(f"{current_entry}")

        return True

    def stop(self) -> None:
        pass