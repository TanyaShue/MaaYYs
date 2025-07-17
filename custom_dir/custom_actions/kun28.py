# -*- coding: UTF-8 -*-
import json
import random
import time

from maa.context import Context
from maa.custom_action import CustomAction

from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("Kun28")
class Kun28(CustomAction):
    def __init__(self):
        super().__init__()
        self.num_tupo = 0

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数
        :param context: 运行上下文
        :return: 是否执行成功。
        """

        print("开始执行自定义动作：Kun28")

        context.run_task("kun289")
        self.num_tupo=self.recognition_tupo_number(context)

        context.run_task("返回庭院")
        if self.num_tupo < 20:
            context.run_task("kun2812")
            self.num_tupo = self.recognition_tupo_number(context)

        for _ in range(100):
            if self.num_tupo >= 20:
                for task in ["返回庭院", "自动结界","返回庭院", "kun2812"]:
                    context.run_task(task)
                    if random.random() < 0.8:
                        number = random.randint(1, 100)  # 80% 概率
                    else:
                        number = random.randint(1, 1000)  # 20% 概率

                    print(f"随机休息: {number} 秒")
                    time.sleep(number)
            else:
                context.run_task("kun281")
            self.num_tupo = self.recognition_tupo_number(context)
        return True

    def recognition_tupo_number(self, context: Context) -> int:
        img = context.tasker.controller.post_screencap().wait().get()

        result=context.run_recognition("kun28_识别突破卷数量",img)
        if result and result.best_result:
            text = result.best_result.text  # 例如 "18/30"
            self.num_tupo = int(text.split("/")[0])
        print(f"识别到的突破卷数量为:{self.num_tupo}")

        return  self.num_tupo

    def stop(self):
        pass