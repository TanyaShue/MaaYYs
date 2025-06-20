# -*- coding: UTF-8 -*-
from maa.context import Context
from maa.custom_action import CustomAction
import random
import json
from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("RandomSwipe")
class RandomSwipe(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        """
        执行滑动操作，从 custom_param 中获取起始和结束区域，生成随机点并执行滑动。

        :param argv:
        :param context: 运行上下文，提供 swipe 方法。
        :return: 滑动是否成功。
        """

        print("开始执行自定义动作: 随机滑动")

        try:
            params = json.loads(argv.custom_action_param)

            # 随机生成start点
            start_x = random.randint(params["start_roi"][0], params["start_roi"][0] + params["start_roi"][2])
            start_y = random.randint(params["start_roi"][1], params["start_roi"][1] + params["start_roi"][3])

            # 随机生成end点
            end_x = random.randint(params["end_roi"][0], params["end_roi"][0] + params["end_roi"][2])
            end_y = random.randint(params["end_roi"][1], params["end_roi"][1] + params["end_roi"][3])

            duration = params.get("delay", 200)
            
            context.tasker.controller.post_swipe(start_x, start_y, end_x, end_y, duration)
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Swipe action failed: {e}")
            return False
        
    
    def stop(self) -> None:
        pass
