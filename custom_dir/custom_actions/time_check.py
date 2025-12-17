# -*- coding: UTF-8 -*-
import json
import datetime
from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("TimeCheck")
class TimeCheck(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg) -> bool:
        """
        自定义动作：检查当前系统时间是否在指定范围内
        :param argv: custom_action_param JSON格式：
                     {
                        "start": "23:00",   // 开始时间 (HH:MM 或 HH:MM:SS)
                        "end": "06:00",     // 结束时间
                        "mode": "in"        // "in" 表示在时间段内返回True，"out" 表示在时间段外返回True
                     }
        :param context: 执行上下文
        :return: 根据 mode 配置，条件满足返回 True，不满足返回 False
        """

        print("开始执行自定义动作：时间范围检查")

        # 1. 参数解析
        try:
            params = json.loads(argv.custom_action_param)
            if not isinstance(params, dict):
                print("参数格式错误：期望 JSON 对象")
                return False

            start_str = params.get("start")
            end_str = params.get("end")
            # mode 默认为 "in" (判断是否在区间内)
            mode = params.get("mode", "in").lower()

            if not start_str or not end_str:
                print("错误：必须提供 start 和 end 时间")
                return False

        except json.JSONDecodeError as e:
            print(f"参数JSON解析失败: {e}")
            return False

        # 2. 时间处理逻辑
        try:
            now_dt = datetime.datetime.now()
            now_time = now_dt.time()

            # 解析输入时间字符串，自动处理 HH:MM 或 HH:MM:SS
            def parse_time(t_str):
                try:
                    return datetime.datetime.strptime(t_str, "%H:%M").time()
                except ValueError:
                    return datetime.datetime.strptime(t_str, "%H:%M:%S").time()

            start_time = parse_time(start_str)
            end_time = parse_time(end_str)

            print(f"当前时间: {now_time.strftime('%H:%M:%S')}")
            print(f"设定范围: {start_time} - {end_time}, 模式: {mode}")

        except ValueError as e:
            print(f"时间格式错误，请使用 HH:MM 或 HH:MM:SS。详细信息: {e}")
            return False

        # 3. 判断逻辑 (核心算法)
        is_in_range = False

        if start_time < end_time:
            # 情况 A: 同一天 (例如 09:00 - 18:00)
            if start_time <= now_time <= end_time:
                is_in_range = True
        else:
            # 情况 B: 跨天 (例如 22:00 - 05:00)
            # 当前时间 >= 开始时间 (23:00)  或者  当前时间 <= 结束时间 (04:00)
            if now_time >= start_time or now_time <= end_time:
                is_in_range = True

        # 4. 根据模式返回结果
        result = False
        if mode == "in":
            # 模式 in: 在范围内返回 True
            result = is_in_range
            desc = "在范围内" if is_in_range else "不在范围内"
        elif mode == "out":
            # 模式 out: 在范围外返回 True
            result = not is_in_range
            desc = "在范围外" if not is_in_range else "在范围内(不满足out模式)"
        else:
            print(f"未知模式 '{mode}'，请使用 'in' 或 'out'")
            return False

        print(f"检查结果: {desc} -> 返回 {result}")
        return result

    def stop(self) -> None:
        pass