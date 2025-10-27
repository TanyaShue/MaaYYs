import json
import time

# -*- coding: UTF-8 -*-
from maa.context import Context
from maa.custom_action import CustomAction


from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("LoopAction")
class LoopAction(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数, 包括action_list和loop_times
        :param context: 运行上下文
        :return: 是否执行成功
        """

        # 读取 custom_param 的参数：{"action_list": ["A", "B", "C"], "loop_times": x}
        json_data = json.loads(argv.custom_action_param)
        # 获取动作列表和循环次数
        action_list = json_data.get("action_list", [])
        loop_times = json_data.get("loop_times", 1)
        on_error= json_data.get("on_error", None)
        if not action_list or loop_times < 1:
            print("无效的action_list或loop_times")
            return False

        print(f"开始执行动作列表 {action_list}，循环 {loop_times} 次")

        for i in range(loop_times):
            print(f"第 {i + 1} 次循环开始")

            for action in action_list:
                action_time_name = f"第{i + 1}次{action}任务"
                print(f"执行动作: {action_time_name}")

                if on_error is not None:
                    context.run_task(action_time_name, {action_time_name:{"next":action,"timeout":1000,"on_error":on_error}})
                else:
                    context.run_task(action_time_name, {action_time_name:{"next":action,"timeout":1000}})

                time.sleep(0.5)  # 可根据需求设置不同的延迟

            print(f"第 {i + 1} 次循环结束")

        return True


    def stop(self) -> None:
        """停止执行的逻辑"""
        pass