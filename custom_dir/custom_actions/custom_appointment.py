import json
from typing import Union, Set

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


@AgentServer.custom_action("CustomAppointment")
class CustomAppointment(CustomAction):
    Default = {
        "樱饼配方": False,#50体
        "奇怪的痕迹": False,#100体
        "接送弥助": False,#100体
        "伊吹的藤球": False,#100体
        "捡到的宝石": False,#200体
        "以鱼为礼": False,#200体
        "帮忙搬运": False,#200体
        "猫老大": False,#300体
        "寻找耳环": False,#300体
        "弥助的画": False, #300体
    }

    def run(self, context: Context, argv: CustomAction.RunArg) -> Union[CustomAction.RunResult, bool]:
        # 传入参数必须是JSON对象（字典）格式，例如: '{"以鱼为礼":true, "奇怪的痕迹":false}'

        # 1. 解析参数，确定意图要执行的任务
        tasks_to_run_intent = self.Default.copy()
        if argv.custom_action_param:
            try:
                arg = json.loads(argv.custom_action_param)
                # 确保解析后的参数是一个字典
                if isinstance(arg, dict):
                    tasks_to_run_intent.update(arg)
                else:
                    print(f"警告：传入的参数不是有效的字典格式，将被忽略。参数: {argv.custom_action_param}")
            except json.JSONDecodeError:
                print(f"警告：无法解析传入的参数为JSON。参数: {argv.custom_action_param}")
                pass

        # 2. 截图并识别屏幕上实际存在的任务列表
        img = context.tasker.controller.post_screencap().wait().get()
        detail = context.run_recognition("识别当前存在任务列表", img)
        on_screen_tasks: Set[str] = {result.text for result in detail.all_results}
        print(f"识别到的屏幕任务: {on_screen_tasks}")

        # 4. 遍历意图要执行的任务，结合屏幕上的任务进行最终决策
        for task_name, should_run in tasks_to_run_intent.items():
            # 必须同时满足两个条件：
            # 1. should_run为True (即参数指定要运行)
            # 2. task_name 存在于屏幕上识别到的任务列表中
            if should_run and task_name in on_screen_tasks:
                print(f"任务 '{task_name}' 符合执行条件，开始委派...")
                context.run_task(f"式神委派8",{"式神委派8":{"expected":f"{task_name}"}})
                print("任务执行完成")
            elif should_run:
                print(f"式神委派8 '{task_name}'，但未在屏幕上找到。")

        return True

    def stop(self):
        pass