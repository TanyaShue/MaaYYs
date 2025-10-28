# -*- coding: UTF-8 -*-
from time import sleep

from PIL import Image
from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("ReStart")
class ReStart(CustomAction):
    # 用于记录上一次的任务节点名称
    the_last_entry = None
    # 用于记录同一个任务节点连续出现的次数
    node_count = 0

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        current_entry = argv.task_detail.entry
        print(f"当前任务入口: {current_entry}")
        print("触发time_out")

        # 判断当前任务节点是否与上一个相同
        if ReStart.the_last_entry == current_entry:
            ReStart.node_count += 1
            print(f"任务节点 '{current_entry}' 已连续出现 {ReStart.node_count} 次。")
        else:
            # 如果是新的任务节点，则更新记录并重置计数器
            ReStart.the_last_entry = current_entry
            ReStart.node_count = 1
            print(f"任务节点: '{current_entry}'，计数重置为 1。")

        if ReStart.node_count >= 4:
            context.run_task("关闭阴阳师")
            sleep(3)
            print("重启游戏")
            context.run_task("启动游戏")
            return True


        if ReStart.node_count <= 2:
            print("关闭游戏")
            print(f"'{current_entry}' 任务出错")
            context.run_task("返回庭院")
            sleep(3)
            print(f"'开始重新执行{current_entry}' 任务")
            context.run_task(f"{current_entry}")


        # 当同一个任务节点连续出现超过2次时，执行重启操作
        if ReStart.node_count == 3:
            print(f"'{current_entry}' 连续出错次数超过2次，开始执行重启...")

            # 截图用于调试分析
            try:
                img = context.tasker.controller.post_screencap().wait().get()
                # 把 BGR → RGB
                img = img[..., ::-1]
                Image.fromarray(img).save("screencap_error.png")
                print("错误截图已保存: screencap_error.png")
            except Exception as e:
                print(f"截图失败: {e}")

            # 重置计数器，以免重启后立即再次触发
            ReStart.node_count = 0
            ReStart.the_last_entry = None

            # 执行重启流程
            print("关闭游戏")
            context.run_task("关闭阴阳师")
            sleep(3)
            print("重启游戏")
            context.run_task("启动游戏")
            sleep(3)
            # 从该任务的最初入口点开始
            print(f"将从任务入口 '{current_entry}' 重新开始执行。")
            context.run_task(f"{current_entry}")
            return True

        return True

    def stop(self) -> None:
        pass