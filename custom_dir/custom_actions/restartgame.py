# -*- coding: UTF-8 -*-
from time import sleep

from PIL import Image
from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("ReStartGame")
class ReStartGame(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("即将重启游戏并跳过任务")
        context.run_task("关闭阴阳师")
        sleep(3)
        context.run_task("启动游戏")
        print(f"重启完成,跳过任务")
        context.run_action("StopTask")
        return True


    def stop(self) -> None:
        pass