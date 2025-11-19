# -*- coding: UTF-8 -*-
import json
import random
import time

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("Kun28")
class Kun28(CustomAction):
    def __init__(self):
        super().__init__()
        self.num_tupo = 0  # 突破卷数量 (用于判断是否清票)
        self.num_guiwang = 0  # 鬼王卷数量 (用于判断是否达成目标)

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数
        :param context: 运行上下文
        :return: 是否执行成功。target=鬼王|绘卷
        """

        print("开始执行自定义动作：Kun28")
        json_data = json.loads(argv.custom_action_param)
        group_name = json_data.get('group_name')
        team_name = json_data.get('team_name')
        target = json_data.get('target')

        print(f"当前模式: {target}, 预设队伍: {group_name}-{team_name}")

        # --- 初始准备阶段 ---
        context.run_task("kun289")
        self.recognition_status(context)  # 初始识别

        context.run_task("返回庭院")

        # 如果一开始突破卷就很多，先清一波
        if self.num_tupo < 20:
            context.run_task("kun2812")
            self.recognition_status(context)

        loop_count = 0

        # --- 循环逻辑主体 ---
        while True:
            # 1. 退出条件判断
            if target == "鬼王":
                # 鬼王模式：判断鬼王卷数量
                if self.num_guiwang >= 50:
                    print(f"【鬼王模式】当前鬼王卷数量为 {self.num_guiwang}，已达到目标(50)，任务结束。")
                    break
            else:
                # 绘卷/默认模式：判断循环次数
                if loop_count >= 200:
                    print(f"【绘卷模式】已循环执行 {loop_count} 次，任务结束。")
                    break

            print(f"当前状态 - 循环次数: {loop_count}, 突破卷: {self.num_tupo}, 鬼王卷: {self.num_guiwang}")

            # 2. 行为逻辑判断 (根据突破卷数量决定)
            if self.num_tupo >= 20:
                print("突破卷 >= 20，开始清理结界...")
                # 执行清理结界的任务链
                for task in ["返回庭院", "自动结界", "返回庭院", "kun2812"]:
                    if task == "自动结界":
                        # 动态传入队伍参数
                        context.run_task(task, {"装备突破预设": {
                            "custom_action_param": {
                                "group_name": f"{group_name}",
                                "team_name": f"{team_name}"
                            }
                        }})
                    else:
                        context.run_task(task)

                    # 任务间的随机等待
                    if random.random() < 0.9:
                        number = random.randint(1, 100)  # 90% 概率短等待
                    else:
                        number = random.randint(1, 600)  # 10% 概率长等待

                    print(f"清理结界中随机休息: {number} 秒")
                    time.sleep(number)
            else:
                # 突破卷不足，继续探索/战斗
                print("突破卷 < 20，执行探索任务...")
                context.run_task("kun281")

            # 3. 状态更新
            self.recognition_status(context)
            loop_count += 1

        return True

    def recognition_status(self, context: Context):
        """
        识别并更新突破卷和鬼王卷的数量
        """
        img = context.tasker.controller.post_screencap().wait().get()

        # --- 识别突破卷 ---
        result_tupo = context.run_recognition("kun28_识别突破卷数量", img)
        if result_tupo and result_tupo.best_result:
            try:
                text = result_tupo.best_result.text
                # 假设格式为 "15/30" 或类似，取 "/" 前面的数字
                self.num_tupo = int(text.split("/")[0])
            except Exception as e:
                print(f"解析突破卷数量出错: {e}")

        # --- 识别鬼王卷 ---
        result_guiwang = context.run_recognition("kun28_识别鬼王卷数量", img)
        if result_guiwang and result_guiwang.best_result:
            try:
                text = result_guiwang.best_result.text
                self.num_guiwang = int(text.split("/")[0])
            except Exception as e:
                print(f"解析鬼王卷数量出错: {e}")

        print(f">> 识别结果更新 | 突破卷: {self.num_tupo} | 鬼王卷: {self.num_guiwang}")

    def stop(self):
        pass