# -*- coding: UTF-8 -*-
import json
import random

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("RandomTask")
class RandomTask(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg) -> bool:
        """
        自定义动作：随机任务
        :param argv: custom_action_param 格式：{"任务1":100,"任务2":300,"任务3":600}
        :param context: 执行上下文
        :return: 是否执行成功
        """

        print("开始执行自定义动作：随机任务")

        try:
            json_data = json.loads(argv.custom_action_param)
        except Exception as e:
            print(f"参数解析失败: {e}")
            return False

        if not json_data:
            print("传入参数为空")
            return False

        # 分离任务和权重
        tasks = list(json_data.keys())
        weights = list(json_data.values())

        # 随机选择一个任务
        chosen_task = random.choices(tasks, weights=weights, k=1)[0]
        print(f"随机选择的任务是: {chosen_task}")

        # 执行任务
        try:
            context.run_task(chosen_task)
            return True
        except Exception as e:
            print(f"执行任务失败: {e}")
            return False

    def stop(self) -> None:
        """停止逻辑"""
        pass
