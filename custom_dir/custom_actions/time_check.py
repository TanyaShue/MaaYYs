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
        自定义动作：检查当前系统时间是否在指定范围内（支持时间 + 日期规则）

        该动作用于判断“当前系统时间”是否满足指定的时间区间，
        并可选地结合日期规则（具体日期 / 每月几号 / 每周星期几）进行限制。
        若未提供日期规则，则默认对所有日期生效（完全兼容旧逻辑）。

        :param argv: custom_action_param，JSON 格式字符串，示例：

                     {
                        "start": "23:00",        // 开始时间 (HH:MM 或 HH:MM:SS)
                        "end": "06:00",          // 结束时间 (HH:MM 或 HH:MM:SS)
                        "mode": "in",            // 可选，默认 "in"
                                                  // "in"  : 在时间段内返回 True
                                                  // "out" : 在时间段外返回 True

                        "date_rule": {           // 【可选】日期规则，不传表示不限制日期
                            "type": "week",      // 规则类型，见下方说明
                            "value": [1, 2, 3]   // 规则值
                        }
                     }

        【date_rule.type 支持类型说明】

        - "date"      : 指定某一天
                        value 示例："2025-01-20"

        - "dates"     : 指定多个具体日期
                        value 示例：["2025-01-20", "2025-01-25"]

        - "month_day" : 每月的某几号
                        value 示例：[1, 15, 28]

        - "week"      : 每周星期几（ISO 标准）
                        1=周一 ... 7=周日
                        value 示例：[1, 2, 3, 4, 5]

        - "none" 或 不传 date_rule
                      : 不进行日期限制，任意日期均可

        :param context: 执行上下文（由框架传入）

        :return:
            - 当 mode = "in"  时：
                当前时间 + 日期规则 均满足条件 → 返回 True
                否则 → 返回 False

            - 当 mode = "out" 时：
                当前时间或日期规则不满足 → 返回 True
                否则 → 返回 False
        """

        print("开始执行自定义动作：时间 + 日期范围检查")

        # ========== 1. 参数解析 ==========
        try:
            params = json.loads(argv.custom_action_param)
            if not isinstance(params, dict):
                print("参数格式错误：期望 JSON 对象")
                return False

            start_str = params.get("start")
            end_str = params.get("end")
            mode = params.get("mode", "in").lower()
            date_rule = params.get("date_rule")  # 新增日期规则

            if not start_str or not end_str:
                print("错误：必须提供 start 和 end 时间")
                return False

        except json.JSONDecodeError as e:
            print(f"参数JSON解析失败: {e}")
            return False

        # ========== 2. 当前时间 ==========
        now_dt = datetime.datetime.now()
        now_time = now_dt.time()
        today = now_dt.date()

        # ========== 3. 时间解析 ==========
        try:
            def parse_time(t_str):
                try:
                    return datetime.datetime.strptime(t_str, "%H:%M").time()
                except ValueError:
                    return datetime.datetime.strptime(t_str, "%H:%M:%S").time()

            start_time = parse_time(start_str)
            end_time = parse_time(end_str)

            print(f"当前时间: {now_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"时间范围: {start_time} - {end_time}, 模式: {mode}")

        except ValueError as e:
            print(f"时间格式错误: {e}")
            return False

        # ========== 4. 日期规则判断 ==========
        def check_date_rule(rule) -> bool:
            """不传规则默认 True"""
            if not rule:
                return True

            rule_type = rule.get("type")
            value = rule.get("value")

            if rule_type == "date":
                target = datetime.datetime.strptime(value, "%Y-%m-%d").date()
                return today == target

            elif rule_type == "dates":
                targets = [
                    datetime.datetime.strptime(d, "%Y-%m-%d").date()
                    for d in value
                ]
                return today in targets

            elif rule_type == "month_day":
                # 每月几号
                return today.day in value

            elif rule_type == "week":
                # Monday=1 ... Sunday=7
                return today.isoweekday() in value

            elif rule_type == "none":
                return True

            else:
                print(f"未知 date_rule.type: {rule_type}")
                return False

        date_ok = check_date_rule(date_rule)
        print(f"日期规则检查结果: {date_ok}")

        if not date_ok:
            return False if mode == "in" else True

        # ========== 5. 时间范围判断 ==========
        is_in_range = False

        if start_time < end_time:
            # 同一天
            if start_time <= now_time <= end_time:
                is_in_range = True
        else:
            # 跨天
            if now_time >= start_time or now_time <= end_time:
                is_in_range = True

        # ========== 6. 模式判断 ==========
        if mode == "in":
            result = is_in_range
        elif mode == "out":
            result = not is_in_range
        else:
            print(f"未知模式 '{mode}'")
            return False

        print(f"最终结果: {result}")
        return result

    def stop(self) -> None:
        pass
