# --- START OF FILE task_list.py ---

# -*- coding: UTF-8 -*-
import json
import time

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer

from custom_dir.until.daily_task_tracker import DailyTaskTracker


@AgentServer.custom_action("TaskList")
class TaskList(CustomAction):
    # 需要每日检查一次的任务列表
    once_a_day = ["领取奖励1_签到", "日常_送友情点", "领取奖励_商店每日奖励", "日常_每日免费一抽"]

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数
                     字典格式: {"task_list": {"A": True, "B": False}, "enable_once_a_day": true}
                     列表格式: {"task_list": ["A", "B", "C"], "enable_once_a_day": false}
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        print("开始执行自定义动作：任务列表")
        json_data = json.loads(argv.custom_action_param)
        task_list = json_data.get("task_list", {})
        on_error = json_data.get("on_error", None)

        # 1. 获取新参数 enable_once_a_day，如果参数未提供，则默认为 True
        enable_once_a_day = json_data.get("enable_once_a_day", True)

        if not task_list:
            print("无效的 task_list")
            return False

        print(f"开始执行任务列表 {task_list}")
        if enable_once_a_day:
            print("每日一次任务检查：已启用")
        else:
            print("每日一次任务检查：已禁用")

        # 2. 在任务开始前，创建一个 DailyTaskTracker 实例
        # 即使禁用检查，创建此对象的开销也很小，代码更整洁
        tracker = DailyTaskTracker()

        # 处理列表格式
        if isinstance(task_list, list):
            for task in task_list:
                # 3. 在执行任务前进行检查，增加 enable_once_a_day 条件
                if enable_once_a_day and task in self.once_a_day:
                    if tracker.has_executed_today(task):
                        # 如果今天已经执行过，则直接跳到下一个任务
                        continue

                print(f"执行任务: {task}")
                if on_error is not None:
                    context.run_task(task, {task:{"on_error":on_error}})
                else:
                    context.run_task(task)
                print(f"任务 {task} 执行完成")

                # 4. 如果任务是每日一次的，执行完后记录，增加 enable_once_a_day 条件
                if enable_once_a_day and task in self.once_a_day:
                    tracker.record_execution(task)

                time.sleep(2)
        # 处理字典格式
        else:
            for task, should_run in task_list.items():
                if should_run:
                    # 3. 在执行任务前进行检查 (同样应用于字典格式)
                    if enable_once_a_day and task in self.once_a_day:
                        if tracker.has_executed_today(task):
                            # 如果今天已经执行过，则直接跳到下一个任务
                            continue

                    print(f"执行任务: {task}")
                    if on_error is not None:
                        context.run_task(task, {task: {"on_error": on_error}})
                    else:
                        context.run_task(task)
                    print(f"任务 {task} 执行完成")

                    # 4. 如果任务是每日一次的，执行完后记录 (同样应用于字典格式)
                    if enable_once_a_day and task in self.once_a_day:
                        tracker.record_execution(task)

                    time.sleep(2)
                else:
                    print(f"跳过任务: {task}（标记为不执行）")

        print("任务列表执行完毕")
        return True

    def stop(self):
        pass