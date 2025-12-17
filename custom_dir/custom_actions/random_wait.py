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
        :param argv: custom_action_param JSON字符串
                     用法1 (范围随机): {"min": 5, "max": 10}  -> 等待 5~10 秒
                     用法2 (固定时间): {"min": 5, "max": 5}   -> 固定等待 5 秒
        :param context: 执行上下文
        :return: 是否执行成功
        """
        print("开始执行自定义动作：随机等待")

        # 默认值
        min_wait = 0.0
        max_wait = 0.0

        # 1. 参数解析
        try:
            param_str = argv.custom_action_param
            if not param_str:
                print("警告：未传入参数，将跳过等待。请在 custom_action_param 中传入如 {\"min\": 2, \"max\": 5}")
                return True

            params = json.loads(param_str)

            # 提取 min 和 max
            # 使用 get 方法提供容错，默认值为 0
            min_wait = float(params.get("min", 0))
            max_wait = float(params.get("max", 0))

        except json.JSONDecodeError as e:
            print(f"参数解析失败，请确保是有效的JSON格式: {e}")
            return False
        except (ValueError, TypeError) as e:
            print(f"参数数值错误，请确保 min/max 是数字: {e}")
            return False

        # 2. 逻辑校验与修正
        if min_wait < 0 or max_wait < 0:
            print("错误：等待时间不能为负数")
            return False

        # 如果用户把 min 和 max 写反了，自动交换
        if min_wait > max_wait:
            print(f"提示：检测到 min({min_wait}) > max({max_wait})，已自动交换范围。")
            min_wait, max_wait = max_wait, min_wait

        # 3. 执行等待
        # 如果 max_wait 为 0 (且 min_wait 也为 0)，则不等待
        if max_wait <= 0:
            print("等待时间范围为 0，跳过等待。")
            return True

        # 生成随机时间
        wait_time = random.uniform(min_wait, max_wait)

        print(f"参数设置: {min_wait} - {max_wait} 秒")
        print(f"实际等待: {wait_time:.2f} 秒...")

        time.sleep(wait_time)

        print("等待结束")
        return True

    def stop(self) -> None:
        """停止逻辑"""
        pass