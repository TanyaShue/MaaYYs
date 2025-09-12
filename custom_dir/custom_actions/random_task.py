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
        自定义动作：根据权重随机选择并执行一个任务
        :param argv: custom_action_param 格式：{"任务1":100, "任务2":300, "任务3":600}
                     权重值必须是数字或可转换为数字的字符串。
        :param context: 执行上下文
        :return: 是否执行成功
        """

        print("开始执行自定义动作：随机任务")

        # 1. 参数解析与校验
        try:
            task_weights_map = json.loads(argv.custom_action_param)
            if not isinstance(task_weights_map, dict):
                print(f"参数格式错误：期望一个JSON对象(字典)，但得到了 {type(task_weights_map)}")
                return False
        except json.JSONDecodeError as e:
            print(f"参数JSON解析失败: {e}")
            return False

        if not task_weights_map:
            print("传入的任务列表为空")
            return False

        # 2. 分离任务和权重，并进行严格的类型转换和校验
        tasks = list(task_weights_map.keys())
        weights_raw = list(task_weights_map.values())
        weights = []

        try:
            # 确保所有权重都是有效的非负数
            for w in weights_raw:
                weight = float(w)  # 强制转换为浮点数，兼容整数、浮点数和数字字符串
                if weight < 0:
                    print(f"错误：权重值不能为负数。发现无效权重: {weight}")
                    return False
                weights.append(weight)
        except (ValueError, TypeError) as e:
            # 如果某个值无法转换为float（例如，一个非数字字符串），则捕获异常
            print(f"错误：所有权重值必须是数字。发现无效值: {e}")
            return False

        # 3. 校验权重总和
        if sum(weights) <= 0:
            print("错误：所有任务的权重总和必须大于0。")
            return False

        # 4. 随机选择一个任务
        print(f"任务池: {tasks}")
        print(f"对应权重: {weights}")
        try:
            chosen_task = random.choices(tasks, weights=weights, k=1)[0]
            print(f"随机选择的任务是: {chosen_task}")
        except IndexError:
            # 这是一个备用安全检查，理论上不应该触发，因为前面已经校验过 not task_weights_map
            print("错误：无法从空任务列表中选择任务。")
            return False

        # 5. 执行任务
        try:
            context.run_task(chosen_task)
            print(f"任务 '{chosen_task}' 执行成功。")
            return True
        except Exception as e:
            print(f"执行任务 '{chosen_task}' 失败: {e}")
            return False

    def stop(self) -> None:
        """停止逻辑"""
        pass