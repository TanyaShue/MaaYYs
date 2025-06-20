import json
import time

# -*- coding: UTF-8 -*-
from maa.context import Context
from maa.custom_action import CustomAction

from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("CountAction")
class CountAction(CustomAction):
    def __init__(self):
        super().__init__()
        self._should_stop = False

    def run(self,
            context: Context,
            argv: CustomAction.RunArg) -> bool:
        """
        执行计数动作，当达到目标计数时执行next任务

        :param context: 运行上下文
        :param argv: 运行参数，包括next_task、count_target和interval
        :return: 是否执行成功
        """
        # 重置停止标志
        self._should_stop = False

        # 读取 custom_param 的参数：{"next_task": "TaskName", "count_target": x, "interval": y, "task_to_count": "TaskToCount"}
        json_data = json.loads(argv.custom_action_param)

        # 获取参数
        next_task = json_data.get("next_task", "")
        count_target = json_data.get("count_target", 1)
        interval = json_data.get("interval", 1.0)  # 默认间隔1秒
        task_to_count = json_data.get("task_to_count", "")

        # 验证参数有效性
        if not next_task or count_target < 1 or not task_to_count:
            print(f"无效的参数: next_task={next_task}, count_target={count_target}, task_to_count={task_to_count}")
            return False

        print(f"开始计数动作: 目标={count_target}, 间隔={interval}秒, 计数任务={task_to_count}, 下一任务={next_task}")

        # 当前计数
        current_count = 0

        # 开始计数循环
        while current_count < count_target and not self._should_stop:
            print(f"当前计数: {current_count}/{count_target}")
            image = context.tasker.controller.post_screencap().wait().get()
            # 执行需要计数的任务
            result = context.run_recognition(task_to_count,image)
            # 检查任务执行结果
            if result and result.best_result:
                current_count += 1
                print(f"任务 {task_to_count} 执行成功，计数增加到 {current_count}")
            else:
                print(f"任务 {task_to_count} 执行失败，计数保持 {current_count}")

            # 如果达到目标计数，退出循环
            if current_count >= count_target:
                break

            # 等待指定的间隔时间
            if not self._should_stop and interval > 0:
                print(f"等待 {interval} 秒...")
                time.sleep(interval)

        # 如果因为达到目标退出循环，则执行next任务
        if current_count >= count_target and not self._should_stop:
            print(f"达到目标计数 {count_target}，执行下一任务: {next_task}")
            next_result = context.run_task(next_task)
            print(f"下一任务 {next_task} 执行结果: {'成功' if next_result else '失败'}")
            return True
        elif self._should_stop:
            print("计数动作被手动停止")
            return False
        else:
            print("计数未达到目标但循环已结束")
            return False

    def stop(self) -> None:
        """停止执行的逻辑"""
        print("收到停止计数的请求")
        self._should_stop = True