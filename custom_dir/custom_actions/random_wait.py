# -*- coding: UTF-8 -*-
import time

from maa.context import Context
from maa.custom_action import CustomAction
import random
from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("RandomWait")
class RandomWait(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        print("开始执行自定义动作：随机等待")
        r = random.random()
        if r < 0.6:
            pass
        else:
            wait = random.uniform(5, 60) if r < 0.9 else random.uniform(60, 300)
            time.sleep(wait)
        return True
    def stop(self) -> None:
        pass
