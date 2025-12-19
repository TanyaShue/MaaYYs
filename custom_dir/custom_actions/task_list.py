# -*- coding: UTF-8 -*-
import json
import time

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer

from custom_dir.until.daily_task_tracker import DailyTaskTracker


@AgentServer.custom_action("TaskList")
class TaskList(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数
                     JSON 结构:
                     {
                        "tasks": {
                            "TaskName_A": { "enabled": true, "once_per_day": true },
                            "TaskName_B": { "enabled": true, "once_per_day": false }
                        }
                     }
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        print("开始执行自定义动作：任务列表 (字典版)")

        try:
            json_data = json.loads(argv.custom_action_param)
        except json.JSONDecodeError:
            print("参数 JSON 解析失败")
            return False

        # 获取任务字典，默认为空字典
        task_dict = json_data.get("tasks", {})

        if not task_dict or not isinstance(task_dict, dict):
            print("未检测到有效的 'tasks' 字典配置")
            return False

        tracker = DailyTaskTracker()

        # 遍历字典 (key=任务名, value=配置)
        for task_entry, config in task_dict.items():
            # 防止配置写成 null
            if config is None:
                config = {}

            is_enabled = config.get("enabled", True)
            is_once_per_day = config.get("once_per_day", False)

            # 1. 检查是否启用
            if not is_enabled:
                print(f"[{task_entry}] 配置为禁用，跳过")
                continue

            # 2. 检查每日一次逻辑
            if is_once_per_day:
                if tracker.has_executed_today(task_entry):
                    print(f"[{task_entry}] 今日已执行过，跳过")
                    continue

            # 3. 执行任务
            print(f"开始执行任务: {task_entry}")
            context.run_task(task_entry)
            print(f"任务 {task_entry} 执行完成")

            # 4. 记录执行状态 (仅针对每日一次的任务)
            if is_once_per_day:
                tracker.record_execution(task_entry)

            # 简单休眠
            time.sleep(2)

        print("任务列表执行完毕")
        return True

    def stop(self):
        pass