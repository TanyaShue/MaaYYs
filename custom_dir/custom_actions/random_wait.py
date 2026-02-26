# -*- coding: UTF-8 -*-
import time
import json
import random

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("RandomWait")
class RandomWait(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg) -> bool:
        """
        自定义动作：根据传入参数随机等待一段时间
        兼容性：参数值支持 数字(5) 或 字符串("5")
        :param argv: custom_action_param JSON格式
                     {"min": "2", "max": "5"}  -> 支持字符串
                     {"min": 2, "max": 5}      -> 支持数字
        """
        # 定义一个安全的转换函数，处理字符串、None、空值等情况
        def safe_float(value, default=0.0):
            if value is None:
                return default
            try:
                # float() 可以处理 "5", "5.2", 5, 5.2 等情况
                return float(value)
            except (ValueError, TypeError):
                return default

        # 1. 参数解析
        try:
            param_str = argv.custom_action_param
            # 如果参数为空字符串，直接跳过
            if not param_str or not param_str.strip():
                return True

            params = json.loads(param_str)

            # 使用安全转换函数获取数值
            # 即使 JSON 写成 {"min": "5", "max": "10"} 也能正常工作
            min_wait = safe_float(params.get("min"), 0.0)
            max_wait = safe_float(params.get("max"), 0.0)

        except json.JSONDecodeError as e:
            return False

        # 2. 逻辑校验与修正
        if min_wait < 0 or max_wait < 0:
            return False

        # 自动交换大小值（防止用户填反）
        if min_wait > max_wait:
            min_wait, max_wait = max_wait, min_wait

        # 3. 执行等待
        if max_wait <= 0:
            return True

        # 生成随机时间
        wait_time = random.uniform(min_wait, max_wait)

        time.sleep(wait_time)

        return True

    def stop(self) -> None:
        """停止逻辑"""
        pass