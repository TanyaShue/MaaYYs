# -*- coding: UTF-8 -*-
from time import sleep

from PIL import Image
from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("ReStart")
class ReStart(CustomAction):
    # 用于记录上一次的入口点
    the_last_entry = None
    # 用于记录同一个入口点连续出现的次数
    entry_count = 0

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        current_entry = argv.task_detail.entry
        print(f"当前任务入口: {current_entry}")

        # 判断当前入口是否与上一个相同
        if ReStart.the_last_entry == current_entry:
            ReStart.entry_count += 1
            print(f"任务 '{current_entry}' 已连续出现 {ReStart.entry_count} 次。")
        else:
            # 如果是新的入口，则更新记录并重置计数器
            ReStart.the_last_entry = current_entry
            ReStart.entry_count = 1
            print(f"任务: '{current_entry}'，计数重置为 1。")

        # 当同一个入口连续出现超过3次时，直接返回True，不再执行后续操作
        if ReStart.entry_count > 3:
            print(f"'{current_entry}' 连续出错次数超过3次，任务终止。")
            return True

        print("计数未超限，开始执行自定义重启动作...")

        img = context.tasker.controller.post_screencap().wait().get()
        # 把 BGR → RGB
        img = img[..., ::-1]

        # 保存图片
        Image.fromarray(img).save("screencap.png")
        print("截图已保存: screencap.png")
        context.get_node_data("关闭阴阳师")

        context.run_task("关闭阴阳师")
        sleep(3)
        context.run_task("启动游戏")
        sleep(3)
        context.run_task(f"{argv.task_detail.entry}")
        return True

    def stop(self) -> None:
        pass