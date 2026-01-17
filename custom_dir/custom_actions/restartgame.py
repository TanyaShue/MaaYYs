# -*- coding: UTF-8 -*-
from time import sleep
from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer
from maa.define import Status


@AgentServer.custom_action("ReStartGame")
class ReStartGame(CustomAction):
    cont=0
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:

        if self.cont <5:
            print("即将重启游戏并跳过任务")
            r=context.run_task("关闭阴阳师")
            if r==Status.failed:
                print("关闭游戏失败,检测游戏区服是否正确")
                return False
            sleep(3)
            context.run_task("启动游戏")
            print(f"重启完成,跳过任务")
            self.cont=self.cont+1
            print(f"当前重启次数为:{str(self.cont)}")
            # context.run_task("StopTask")
            # print(f"结束任务链")
            return True
        else:
            context.run_task("StopTask")
            return True
    def stop(self) -> None:
        pass